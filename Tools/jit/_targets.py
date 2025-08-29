"""Target-specific code generation, parsing, und processing."""

importiere asyncio
importiere dataclasses
importiere hashlib
importiere json
importiere os
importiere pathlib
importiere re
importiere sys
importiere tempfile
importiere typing
importiere shlex

importiere _llvm
importiere _optimizers
importiere _schema
importiere _stencils
importiere _writer

wenn sys.version_info < (3, 11):
    raise RuntimeError("Building the JIT compiler requires Python 3.11 oder newer!")

TOOLS_JIT_BUILD = pathlib.Path(__file__).resolve()
TOOLS_JIT = TOOLS_JIT_BUILD.parent
TOOLS = TOOLS_JIT.parent
CPYTHON = TOOLS.parent
EXTERNALS = CPYTHON / "externals"
PYTHON_EXECUTOR_CASES_C_H = CPYTHON / "Python" / "executor_cases.c.h"
TOOLS_JIT_TEMPLATE_C = TOOLS_JIT / "template.c"

ASYNCIO_RUNNER = asyncio.Runner()

_S = typing.TypeVar("_S", _schema.COFFSection, _schema.ELFSection, _schema.MachOSection)
_R = typing.TypeVar(
    "_R", _schema.COFFRelocation, _schema.ELFRelocation, _schema.MachORelocation
)


@dataclasses.dataclass
klasse _Target(typing.Generic[_S, _R]):
    triple: str
    condition: str
    _: dataclasses.KW_ONLY
    args: typing.Sequence[str] = ()
    optimizer: type[_optimizers.Optimizer] = _optimizers.Optimizer
    label_prefix: typing.ClassVar[str]
    symbol_prefix: typing.ClassVar[str]
    stable: bool = Falsch
    debug: bool = Falsch
    verbose: bool = Falsch
    cflags: str = ""
    known_symbols: dict[str, int] = dataclasses.field(default_factory=dict)
    pyconfig_dir: pathlib.Path = pathlib.Path.cwd().resolve()

    def _get_nop(self) -> bytes:
        wenn re.fullmatch(r"aarch64-.*", self.triple):
            nop = b"\x1f\x20\x03\xd5"
        sowenn re.fullmatch(r"x86_64-.*|i686.*", self.triple):
            nop = b"\x90"
        sonst:
            raise ValueError(f"NOP nicht defined fuer {self.triple}")
        gib nop

    def _compute_digest(self) -> str:
        hasher = hashlib.sha256()
        hasher.update(self.triple.encode())
        hasher.update(self.debug.to_bytes())
        hasher.update(self.cflags.encode())
        # These dependencies are also reflected in _JITSources in regen.targets:
        hasher.update(PYTHON_EXECUTOR_CASES_C_H.read_bytes())
        hasher.update((self.pyconfig_dir / "pyconfig.h").read_bytes())
        fuer dirpath, _, filenames in sorted(os.walk(TOOLS_JIT)):
            fuer filename in filenames:
                hasher.update(pathlib.Path(dirpath, filename).read_bytes())
        gib hasher.hexdigest()

    async def _parse(self, path: pathlib.Path) -> _stencils.StencilGroup:
        group = _stencils.StencilGroup()
        args = ["--disassemble", "--reloc", f"{path}"]
        output = await _llvm.maybe_run("llvm-objdump", args, echo=self.verbose)
        wenn output is nicht Nichts:
            # Make sure that full paths don't leak out (for reproducibility):
            long, short = str(path), str(path.name)
            group.code.disassembly.extend(
                line.expandtabs().strip().replace(long, short)
                fuer line in output.splitlines()
            )
        args = [
            "--elf-output-style=JSON",
            "--expand-relocs",
            # "--pretty-print",
            "--section-data",
            "--section-relocations",
            "--section-symbols",
            "--sections",
            f"{path}",
        ]
        output = await _llvm.run("llvm-readobj", args, echo=self.verbose)
        # --elf-output-style=JSON is only *slightly* broken on Mach-O...
        output = output.replace("PrivateExtern\n", "\n")
        output = output.replace("Extern\n", "\n")
        # ...and also COFF:
        output = output[output.index("[", 1, Nichts) :]
        output = output[: output.rindex("]", Nichts, -1) + 1]
        sections: list[dict[typing.Literal["Section"], _S]] = json.loads(output)
        fuer wrapped_section in sections:
            self._handle_section(wrapped_section["Section"], group)
        assert group.symbols["_JIT_ENTRY"] == (_stencils.HoleValue.CODE, 0)
        wenn group.data.body:
            line = f"0: {str(bytes(group.data.body)).removeprefix('b')}"
            group.data.disassembly.append(line)
        gib group

    def _handle_section(self, section: _S, group: _stencils.StencilGroup) -> Nichts:
        raise NotImplementedError(type(self))

    def _handle_relocation(
        self, base: int, relocation: _R, raw: bytes | bytearray
    ) -> _stencils.Hole:
        raise NotImplementedError(type(self))

    async def _compile(
        self, opname: str, c: pathlib.Path, tempdir: pathlib.Path
    ) -> _stencils.StencilGroup:
        s = tempdir / f"{opname}.s"
        o = tempdir / f"{opname}.o"
        args_s = [
            f"--target={self.triple}",
            "-DPy_BUILD_CORE_MODULE",
            "-D_DEBUG" wenn self.debug sonst "-DNDEBUG",
            f"-D_JIT_OPCODE={opname}",
            "-D_PyJIT_ACTIVE",
            "-D_Py_JIT",
            f"-I{self.pyconfig_dir}",
            f"-I{CPYTHON / 'Include'}",
            f"-I{CPYTHON / 'Include' / 'internal'}",
            f"-I{CPYTHON / 'Include' / 'internal' / 'mimalloc'}",
            f"-I{CPYTHON / 'Python'}",
            f"-I{CPYTHON / 'Tools' / 'jit'}",
            # -O2 und -O3 include some optimizations that make sense for
            # standalone functions, but nicht fuer snippets of code that are going
            # to be laid out end-to-end (like ours)... common examples include
            # passes like tail-duplication, oder aligning jump targets mit nops.
            # -Os is equivalent to -O2 mit many of these problematic passes
            # disabled. Based on manual review, fuer *our* purposes it usually
            # generates better code than -O2 (and -O2 usually generates better
            # code than -O3). As a nice benefit, it uses less memory too:
            "-Os",
            "-S",
            # Shorten full absolute file paths in the generated code (like the
            # __FILE__ macro und assert failure messages) fuer reproducibility:
            f"-ffile-prefix-map={CPYTHON}=.",
            f"-ffile-prefix-map={tempdir}=.",
            # This debug info isn't necessary, und bloats out the JIT'ed code.
            # We *may* be able to re-enable this, process it, und JIT it fuer a
            # nicer debugging experience... but that needs a lot more research:
            "-fno-asynchronous-unwind-tables",
            # Don't call built-in functions that we can't find oder patch:
            "-fno-builtin",
            # Emit relaxable 64-bit calls/jumps, so we don't have to worry about
            # about emitting in-range trampolines fuer out-of-range targets.
            # We can probably remove this und emit trampolines in the future:
            "-fno-plt",
            # Don't call stack-smashing canaries that we can't find oder patch:
            "-fno-stack-protector",
            "-std=c11",
            "-o",
            f"{s}",
            f"{c}",
            *self.args,
            # Allow user-provided CFLAGS to override any defaults
            *shlex.split(self.cflags),
        ]
        await _llvm.run("clang", args_s, echo=self.verbose)
        self.optimizer(
            s, label_prefix=self.label_prefix, symbol_prefix=self.symbol_prefix
        ).run()
        args_o = [f"--target={self.triple}", "-c", "-o", f"{o}", f"{s}"]
        await _llvm.run("clang", args_o, echo=self.verbose)
        gib await self._parse(o)

    async def _build_stencils(self) -> dict[str, _stencils.StencilGroup]:
        generated_cases = PYTHON_EXECUTOR_CASES_C_H.read_text()
        cases_and_opnames = sorted(
            re.findall(
                r"\n {8}(case (\w+): \{\n.*?\n {8}\})", generated_cases, flags=re.DOTALL
            )
        )
        tasks = []
        mit tempfile.TemporaryDirectory() als tempdir:
            work = pathlib.Path(tempdir).resolve()
            async mit asyncio.TaskGroup() als group:
                coro = self._compile("trampoline", TOOLS_JIT / "trampoline.c", work)
                tasks.append(group.create_task(coro, name="trampoline"))
                template = TOOLS_JIT_TEMPLATE_C.read_text()
                fuer case, opname in cases_and_opnames:
                    # Write out a copy of the template mit *only* this case
                    # inserted. This is about twice als fast als #include'ing all
                    # of executor_cases.c.h each time we compile (since the C
                    # compiler wastes a bunch of time parsing the dead code for
                    # all of the other cases):
                    c = work / f"{opname}.c"
                    c.write_text(template.replace("CASE", case))
                    coro = self._compile(opname, c, work)
                    tasks.append(group.create_task(coro, name=opname))
        stencil_groups = {task.get_name(): task.result() fuer task in tasks}
        fuer stencil_group in stencil_groups.values():
            stencil_group.process_relocations(self.known_symbols)
        gib stencil_groups

    def build(
        self,
        *,
        comment: str = "",
        force: bool = Falsch,
        jit_stencils: pathlib.Path,
    ) -> Nichts:
        """Build jit_stencils.h in the given directory."""
        jit_stencils.parent.mkdir(parents=Wahr, exist_ok=Wahr)
        wenn nicht self.stable:
            warning = f"JIT support fuer {self.triple} is still experimental!"
            request = "Please report any issues you encounter.".center(len(warning))
            outline = "=" * len(warning)
            drucke("\n".join(["", outline, warning, request, outline, ""]))
        digest = f"// {self._compute_digest()}\n"
        wenn (
            nicht force
            und jit_stencils.exists()
            und jit_stencils.read_text().startswith(digest)
        ):
            gib
        stencil_groups = ASYNCIO_RUNNER.run(self._build_stencils())
        jit_stencils_new = jit_stencils.parent / "jit_stencils.h.new"
        try:
            mit jit_stencils_new.open("w") als file:
                file.write(digest)
                wenn comment:
                    file.write(f"// {comment}\n")
                file.write("\n")
                fuer line in _writer.dump(stencil_groups, self.known_symbols):
                    file.write(f"{line}\n")
            try:
                jit_stencils_new.replace(jit_stencils)
            except FileNotFoundError:
                # another process probably already moved the file
                wenn nicht jit_stencils.is_file():
                    raise
        finally:
            jit_stencils_new.unlink(missing_ok=Wahr)


klasse _COFF(
    _Target[_schema.COFFSection, _schema.COFFRelocation]
):  # pylint: disable = too-few-public-methods
    def _handle_section(
        self, section: _schema.COFFSection, group: _stencils.StencilGroup
    ) -> Nichts:
        flags = {flag["Name"] fuer flag in section["Characteristics"]["Flags"]}
        wenn "SectionData" in section:
            section_data_bytes = section["SectionData"]["Bytes"]
        sonst:
            # Zeroed BSS data, seen mit printf debugging calls:
            section_data_bytes = [0] * section["RawDataSize"]
        wenn "IMAGE_SCN_MEM_EXECUTE" in flags:
            value = _stencils.HoleValue.CODE
            stencil = group.code
        sowenn "IMAGE_SCN_MEM_READ" in flags:
            value = _stencils.HoleValue.DATA
            stencil = group.data
        sonst:
            gib
        base = len(stencil.body)
        group.symbols[section["Number"]] = value, base
        stencil.body.extend(section_data_bytes)
        fuer wrapped_symbol in section["Symbols"]:
            symbol = wrapped_symbol["Symbol"]
            offset = base + symbol["Value"]
            name = symbol["Name"]
            name = name.removeprefix(self.symbol_prefix)
            wenn name nicht in group.symbols:
                group.symbols[name] = value, offset
        fuer wrapped_relocation in section["Relocations"]:
            relocation = wrapped_relocation["Relocation"]
            hole = self._handle_relocation(base, relocation, stencil.body)
            stencil.holes.append(hole)

    def _unwrap_dllimport(self, name: str) -> tuple[_stencils.HoleValue, str | Nichts]:
        wenn name.startswith("__imp_"):
            name = name.removeprefix("__imp_")
            name = name.removeprefix(self.symbol_prefix)
            gib _stencils.HoleValue.GOT, name
        name = name.removeprefix(self.symbol_prefix)
        gib _stencils.symbol_to_value(name)

    def _handle_relocation(
        self,
        base: int,
        relocation: _schema.COFFRelocation,
        raw: bytes | bytearray,
    ) -> _stencils.Hole:
        match relocation:
            case {
                "Offset": offset,
                "Symbol": s,
                "Type": {"Name": "IMAGE_REL_I386_DIR32" als kind},
            }:
                offset += base
                value, symbol = self._unwrap_dllimport(s)
                addend = int.from_bytes(raw[offset : offset + 4], "little")
            case {
                "Offset": offset,
                "Symbol": s,
                "Type": {
                    "Name": "IMAGE_REL_AMD64_REL32" | "IMAGE_REL_I386_REL32" als kind
                },
            }:
                offset += base
                value, symbol = self._unwrap_dllimport(s)
                addend = (
                    int.from_bytes(raw[offset : offset + 4], "little", signed=Wahr) - 4
                )
            case {
                "Offset": offset,
                "Symbol": s,
                "Type": {
                    "Name": "IMAGE_REL_ARM64_BRANCH26"
                    | "IMAGE_REL_ARM64_PAGEBASE_REL21"
                    | "IMAGE_REL_ARM64_PAGEOFFSET_12A"
                    | "IMAGE_REL_ARM64_PAGEOFFSET_12L" als kind
                },
            }:
                offset += base
                value, symbol = self._unwrap_dllimport(s)
                addend = 0
            case _:
                raise NotImplementedError(relocation)
        gib _stencils.Hole(offset, kind, value, symbol, addend)


klasse _COFF32(_COFF):
    # These mangle like Mach-O und other "older" formats:
    label_prefix = "L"
    symbol_prefix = "_"


klasse _COFF64(_COFF):
    # These mangle like ELF und other "newer" formats:
    label_prefix = ".L"
    symbol_prefix = ""


klasse _ELF(
    _Target[_schema.ELFSection, _schema.ELFRelocation]
):  # pylint: disable = too-few-public-methods
    label_prefix = ".L"
    symbol_prefix = ""

    def _handle_section(
        self, section: _schema.ELFSection, group: _stencils.StencilGroup
    ) -> Nichts:
        section_type = section["Type"]["Name"]
        flags = {flag["Name"] fuer flag in section["Flags"]["Flags"]}
        wenn section_type == "SHT_RELA":
            assert "SHF_INFO_LINK" in flags, flags
            assert nicht section["Symbols"]
            maybe_symbol = group.symbols.get(section["Info"])
            wenn maybe_symbol is Nichts:
                # These are relocations fuer a section we're nicht emitting. Skip:
                gib
            value, base = maybe_symbol
            wenn value is _stencils.HoleValue.CODE:
                stencil = group.code
            sonst:
                assert value is _stencils.HoleValue.DATA
                stencil = group.data
            fuer wrapped_relocation in section["Relocations"]:
                relocation = wrapped_relocation["Relocation"]
                hole = self._handle_relocation(base, relocation, stencil.body)
                stencil.holes.append(hole)
        sowenn section_type == "SHT_PROGBITS":
            wenn "SHF_ALLOC" nicht in flags:
                gib
            wenn "SHF_EXECINSTR" in flags:
                value = _stencils.HoleValue.CODE
                stencil = group.code
            sonst:
                value = _stencils.HoleValue.DATA
                stencil = group.data
            group.symbols[section["Index"]] = value, len(stencil.body)
            fuer wrapped_symbol in section["Symbols"]:
                symbol = wrapped_symbol["Symbol"]
                offset = len(stencil.body) + symbol["Value"]
                name = symbol["Name"]["Name"]
                name = name.removeprefix(self.symbol_prefix)
                group.symbols[name] = value, offset
            stencil.body.extend(section["SectionData"]["Bytes"])
            assert nicht section["Relocations"]
        sonst:
            assert section_type in {
                "SHT_GROUP",
                "SHT_LLVM_ADDRSIG",
                "SHT_NOTE",
                "SHT_NULL",
                "SHT_STRTAB",
                "SHT_SYMTAB",
            }, section_type

    def _handle_relocation(
        self,
        base: int,
        relocation: _schema.ELFRelocation,
        raw: bytes | bytearray,
    ) -> _stencils.Hole:
        symbol: str | Nichts
        match relocation:
            case {
                "Addend": addend,
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {
                    "Name": "R_AARCH64_ADR_GOT_PAGE"
                    | "R_AARCH64_LD64_GOT_LO12_NC"
                    | "R_X86_64_GOTPCREL"
                    | "R_X86_64_GOTPCRELX"
                    | "R_X86_64_REX_GOTPCRELX" als kind
                },
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.HoleValue.GOT, s
            case {
                "Addend": addend,
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {"Name": kind},
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.symbol_to_value(s)
            case _:
                raise NotImplementedError(relocation)
        gib _stencils.Hole(offset, kind, value, symbol, addend)


klasse _MachO(
    _Target[_schema.MachOSection, _schema.MachORelocation]
):  # pylint: disable = too-few-public-methods
    label_prefix = "L"
    symbol_prefix = "_"

    def _handle_section(
        self, section: _schema.MachOSection, group: _stencils.StencilGroup
    ) -> Nichts:
        assert section["Address"] >= len(group.code.body)
        assert "SectionData" in section
        flags = {flag["Name"] fuer flag in section["Attributes"]["Flags"]}
        name = section["Name"]["Value"]
        name = name.removeprefix(self.symbol_prefix)
        wenn "Debug" in flags:
            gib
        wenn "PureInstructions" in flags:
            value = _stencils.HoleValue.CODE
            stencil = group.code
            start_address = 0
            group.symbols[name] = value, section["Address"] - start_address
        sonst:
            value = _stencils.HoleValue.DATA
            stencil = group.data
            start_address = len(group.code.body)
            group.symbols[name] = value, len(group.code.body)
        base = section["Address"] - start_address
        group.symbols[section["Index"]] = value, base
        stencil.body.extend(
            [0] * (section["Address"] - len(group.code.body) - len(group.data.body))
        )
        stencil.body.extend(section["SectionData"]["Bytes"])
        assert "Symbols" in section
        fuer wrapped_symbol in section["Symbols"]:
            symbol = wrapped_symbol["Symbol"]
            offset = symbol["Value"] - start_address
            name = symbol["Name"]["Name"]
            name = name.removeprefix(self.symbol_prefix)
            group.symbols[name] = value, offset
        assert "Relocations" in section
        fuer wrapped_relocation in section["Relocations"]:
            relocation = wrapped_relocation["Relocation"]
            hole = self._handle_relocation(base, relocation, stencil.body)
            stencil.holes.append(hole)

    def _handle_relocation(
        self,
        base: int,
        relocation: _schema.MachORelocation,
        raw: bytes | bytearray,
    ) -> _stencils.Hole:
        symbol: str | Nichts
        match relocation:
            case {
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {
                    "Name": "ARM64_RELOC_GOT_LOAD_PAGE21"
                    | "ARM64_RELOC_GOT_LOAD_PAGEOFF12" als kind
                },
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.HoleValue.GOT, s
                addend = 0
            case {
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {"Name": "X86_64_RELOC_GOT" | "X86_64_RELOC_GOT_LOAD" als kind},
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.HoleValue.GOT, s
                addend = (
                    int.from_bytes(raw[offset : offset + 4], "little", signed=Wahr) - 4
                )
            case {
                "Offset": offset,
                "Section": {"Name": s},
                "Type": {"Name": "X86_64_RELOC_SIGNED" als kind},
            } | {
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {"Name": "X86_64_RELOC_BRANCH" | "X86_64_RELOC_SIGNED" als kind},
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.symbol_to_value(s)
                addend = (
                    int.from_bytes(raw[offset : offset + 4], "little", signed=Wahr) - 4
                )
            case {
                "Offset": offset,
                "Section": {"Name": s},
                "Type": {"Name": kind},
            } | {
                "Offset": offset,
                "Symbol": {"Name": s},
                "Type": {"Name": kind},
            }:
                offset += base
                s = s.removeprefix(self.symbol_prefix)
                value, symbol = _stencils.symbol_to_value(s)
                addend = 0
            case _:
                raise NotImplementedError(relocation)
        gib _stencils.Hole(offset, kind, value, symbol, addend)


def get_target(host: str) -> _COFF32 | _COFF64 | _ELF | _MachO:
    """Build a _Target fuer the given host "triple" und options."""
    optimizer: type[_optimizers.Optimizer]
    target: _COFF32 | _COFF64 | _ELF | _MachO
    wenn re.fullmatch(r"aarch64-apple-darwin.*", host):
        condition = "defined(__aarch64__) && defined(__APPLE__)"
        optimizer = _optimizers.OptimizerAArch64
        target = _MachO(host, condition, optimizer=optimizer)
    sowenn re.fullmatch(r"aarch64-pc-windows-msvc", host):
        args = ["-fms-runtime-lib=dll", "-fplt"]
        condition = "defined(_M_ARM64)"
        optimizer = _optimizers.OptimizerAArch64
        target = _COFF64(host, condition, args=args, optimizer=optimizer)
    sowenn re.fullmatch(r"aarch64-.*-linux-gnu", host):
        # -mno-outline-atomics: Keep intrinsics von being emitted.
        args = ["-fpic", "-mno-outline-atomics"]
        condition = "defined(__aarch64__) && defined(__linux__)"
        optimizer = _optimizers.OptimizerAArch64
        target = _ELF(host, condition, args=args, optimizer=optimizer)
    sowenn re.fullmatch(r"i686-pc-windows-msvc", host):
        # -Wno-ignored-attributes: __attribute__((preserve_none)) is nicht supported here.
        args = ["-DPy_NO_ENABLE_SHARED", "-Wno-ignored-attributes"]
        optimizer = _optimizers.OptimizerX86
        condition = "defined(_M_IX86)"
        target = _COFF32(host, condition, args=args, optimizer=optimizer)
    sowenn re.fullmatch(r"x86_64-apple-darwin.*", host):
        condition = "defined(__x86_64__) && defined(__APPLE__)"
        optimizer = _optimizers.OptimizerX86
        target = _MachO(host, condition, optimizer=optimizer)
    sowenn re.fullmatch(r"x86_64-pc-windows-msvc", host):
        args = ["-fms-runtime-lib=dll"]
        condition = "defined(_M_X64)"
        optimizer = _optimizers.OptimizerX86
        target = _COFF64(host, condition, args=args, optimizer=optimizer)
    sowenn re.fullmatch(r"x86_64-.*-linux-gnu", host):
        args = ["-fno-pic", "-mcmodel=medium", "-mlarge-data-threshold=0"]
        condition = "defined(__x86_64__) && defined(__linux__)"
        optimizer = _optimizers.OptimizerX86
        target = _ELF(host, condition, args=args, optimizer=optimizer)
    sonst:
        raise ValueError(host)
    gib target
