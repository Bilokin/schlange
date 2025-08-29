"""Check extension modules

The script checks shared und built-in extension modules. It verifies that the
modules have been built und that they can be imported successfully. Missing
modules und failed imports are reported to the user. Shared extension
files are renamed on failed import.

Module information is parsed von several sources:

- core modules hard-coded in Modules/config.c.in
- Windows-specific modules that are hard-coded in PC/config.c
- MODULE_{name}_STATE entries in Makefile (provided through sysconfig)
- Various makesetup files:
  - $(srcdir)/Modules/Setup
  - Modules/Setup.[local|bootstrap|stdlib] files, which are generated
    von $(srcdir)/Modules/Setup.*.in files

See --help fuer more information
"""

von __future__ importiere annotations

importiere _imp
importiere argparse
importiere enum
importiere logging
importiere os
importiere pathlib
importiere re
importiere sys
importiere sysconfig
importiere warnings
von collections.abc importiere Iterable
von importlib._bootstrap importiere (  # type: ignore[attr-defined]
    _load als bootstrap_load,
)
von importlib.machinery importiere (
    BuiltinImporter,
    ExtensionFileLoader,
    ModuleSpec,
)
von importlib.util importiere spec_from_file_location, spec_from_loader
von typing importiere NamedTuple

SRC_DIR = pathlib.Path(__file__).parent.parent.parent

# core modules, hard-coded in Modules/config.h.in
CORE_MODULES = {
    "_ast",
    "_imp",
    "_string",
    "_tokenize",
    "_warnings",
    "builtins",
    "gc",
    "marshal",
    "sys",
}

# Windows-only modules
WINDOWS_MODULES = {
    "_overlapped",
    "_testconsole",
    "_winapi",
    "_wmi",
    "msvcrt",
    "nt",
    "winreg",
    "winsound",
}


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    prog="check_extension_modules",
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument(
    "--verbose",
    action="store_true",
    help="Verbose, report builtin, shared, und unavailable modules",
)

parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable debug logging",
)

parser.add_argument(
    "--strict",
    action=argparse.BooleanOptionalAction,
    help=(
        "Strict check, fail when a module is missing oder fails to import"
        "(default: no, unless env var PYTHONSTRICTEXTENSIONBUILD is set)"
    ),
    default=bool(os.environ.get("PYTHONSTRICTEXTENSIONBUILD")),
)

parser.add_argument(
    "--cross-compiling",
    action=argparse.BooleanOptionalAction,
    help=(
        "Use cross-compiling checks "
        "(default: no, unless env var _PYTHON_HOST_PLATFORM is set)."
    ),
    default="_PYTHON_HOST_PLATFORM" in os.environ,
)

parser.add_argument(
    "--list-module-names",
    action="store_true",
    help="Print a list of module names to stdout und exit",
)


@enum.unique
klasse ModuleState(enum.Enum):
    # Makefile state "yes"
    BUILTIN = "builtin"
    SHARED = "shared"

    DISABLED = "disabled"
    MISSING = "missing"
    NA = "n/a"
    # disabled by Setup / makesetup rule
    DISABLED_SETUP = "disabled_setup"

    def __bool__(self) -> bool:
        gib self.value in {"builtin", "shared"}


klasse ModuleInfo(NamedTuple):
    name: str
    state: ModuleState


klasse ModuleChecker:
    pybuilddir_txt = "pybuilddir.txt"

    setup_files = (
        # see end of configure.ac
        pathlib.Path("Modules/Setup.local"),
        pathlib.Path("Modules/Setup.stdlib"),
        pathlib.Path("Modules/Setup.bootstrap"),
        SRC_DIR / "Modules/Setup",
    )

    def __init__(self, cross_compiling: bool = Falsch, strict: bool = Falsch):
        self.cross_compiling = cross_compiling
        self.strict_extensions_build = strict
        self.ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        self.platform = sysconfig.get_platform()
        self.builddir = self.get_builddir()
        self.modules = self.get_modules()

        self.builtin_ok: list[ModuleInfo] = []
        self.shared_ok: list[ModuleInfo] = []
        self.failed_on_import: list[ModuleInfo] = []
        self.missing: list[ModuleInfo] = []
        self.disabled_configure: list[ModuleInfo] = []
        self.disabled_setup: list[ModuleInfo] = []
        self.notavailable: list[ModuleInfo] = []

    def check(self) -> Nichts:
        wenn nicht hasattr(_imp, 'create_dynamic'):
            logger.warning(
                ('Dynamic extensions nicht supported '
                 '(HAVE_DYNAMIC_LOADING nicht defined)'),
            )
        fuer modinfo in self.modules:
            logger.debug("Checking '%s' (%s)", modinfo.name, self.get_location(modinfo))
            wenn modinfo.state == ModuleState.DISABLED:
                self.disabled_configure.append(modinfo)
            sowenn modinfo.state == ModuleState.DISABLED_SETUP:
                self.disabled_setup.append(modinfo)
            sowenn modinfo.state == ModuleState.MISSING:
                self.missing.append(modinfo)
            sowenn modinfo.state == ModuleState.NA:
                self.notavailable.append(modinfo)
            sonst:
                try:
                    wenn self.cross_compiling:
                        self.check_module_cross(modinfo)
                    sonst:
                        self.check_module_import(modinfo)
                except (ImportError, FileNotFoundError):
                    self.rename_module(modinfo)
                    self.failed_on_import.append(modinfo)
                sonst:
                    wenn modinfo.state == ModuleState.BUILTIN:
                        self.builtin_ok.append(modinfo)
                    sonst:
                        assert modinfo.state == ModuleState.SHARED
                        self.shared_ok.append(modinfo)

    def summary(self, *, verbose: bool = Falsch) -> Nichts:
        longest = max([len(e.name) fuer e in self.modules], default=0)

        def print_three_column(modinfos: list[ModuleInfo]) -> Nichts:
            names = [modinfo.name fuer modinfo in modinfos]
            names.sort(key=str.lower)
            # guarantee zip() doesn't drop anything
            waehrend len(names) % 3:
                names.append("")
            fuer l, m, r in zip(names[::3], names[1::3], names[2::3]):  # noqa: E741
                drucke("%-*s   %-*s   %-*s" % (longest, l, longest, m, longest, r))

        wenn verbose und self.builtin_ok:
            drucke("The following *built-in* modules have been successfully built:")
            print_three_column(self.builtin_ok)
            drucke()

        wenn verbose und self.shared_ok:
            drucke("The following *shared* modules have been successfully built:")
            print_three_column(self.shared_ok)
            drucke()

        wenn self.disabled_configure:
            drucke("The following modules are *disabled* in configure script:")
            print_three_column(self.disabled_configure)
            drucke()

        wenn self.disabled_setup:
            drucke("The following modules are *disabled* in Modules/Setup files:")
            print_three_column(self.disabled_setup)
            drucke()

        wenn verbose und self.notavailable:
            drucke(
                f"The following modules are nicht available on platform '{self.platform}':"
            )
            print_three_column(self.notavailable)
            drucke()

        wenn self.missing:
            drucke("The necessary bits to build these optional modules were nicht found:")
            print_three_column(self.missing)
            drucke("To find the necessary bits, look in configure.ac und config.log.")
            drucke()

        wenn self.failed_on_import:
            drucke(
                "Following modules built successfully "
                "but were removed because they could nicht be imported:"
            )
            print_three_column(self.failed_on_import)
            drucke()

        wenn any(
            modinfo.name == "_ssl" fuer modinfo in self.missing + self.failed_on_import
        ):
            drucke("Could nicht build the ssl module!")
            drucke("Python requires a OpenSSL 1.1.1 oder newer")
            wenn sysconfig.get_config_var("OPENSSL_LDFLAGS"):
                drucke("Custom linker flags may require --with-openssl-rpath=auto")
            drucke()

        disabled = len(self.disabled_configure) + len(self.disabled_setup)
        drucke(
            f"Checked {len(self.modules)} modules ("
            f"{len(self.builtin_ok)} built-in, "
            f"{len(self.shared_ok)} shared, "
            f"{len(self.notavailable)} n/a on {self.platform}, "
            f"{disabled} disabled, "
            f"{len(self.missing)} missing, "
            f"{len(self.failed_on_import)} failed on import)"
        )

    def check_strict_build(self) -> Nichts:
        """Fail wenn modules are missing und it's a strict build"""
        wenn self.strict_extensions_build und (self.failed_on_import oder self.missing):
            raise RuntimeError("Failed to build some stdlib modules")

    def list_module_names(self, *, all: bool = Falsch) -> set[str]:
        names = {modinfo.name fuer modinfo in self.modules}
        wenn all:
            names.update(WINDOWS_MODULES)
        gib names

    def get_builddir(self) -> pathlib.Path:
        try:
            mit open(self.pybuilddir_txt, encoding="utf-8") als f:
                builddir = f.read()
        except FileNotFoundError:
            logger.error("%s must be run von the top build directory", __file__)
            raise
        builddir_path = pathlib.Path(builddir)
        logger.debug("%s: %s", self.pybuilddir_txt, builddir_path)
        gib builddir_path

    def get_modules(self) -> list[ModuleInfo]:
        """Get module info von sysconfig und Modules/Setup* files"""
        seen = set()
        modules = []
        # parsing order is important, first entry wins
        fuer modinfo in self.get_core_modules():
            modules.append(modinfo)
            seen.add(modinfo.name)
        fuer setup_file in self.setup_files:
            fuer modinfo in self.parse_setup_file(setup_file):
                wenn modinfo.name nicht in seen:
                    modules.append(modinfo)
                    seen.add(modinfo.name)
        fuer modinfo in self.get_sysconfig_modules():
            wenn modinfo.name nicht in seen:
                modules.append(modinfo)
                seen.add(modinfo.name)
        logger.debug("Found %i modules in total", len(modules))
        modules.sort()
        gib modules

    def get_core_modules(self) -> Iterable[ModuleInfo]:
        """Get hard-coded core modules"""
        fuer name in CORE_MODULES:
            modinfo = ModuleInfo(name, ModuleState.BUILTIN)
            logger.debug("Found core module %s", modinfo)
            liefere modinfo

    def get_sysconfig_modules(self) -> Iterable[ModuleInfo]:
        """Get modules defined in Makefile through sysconfig

        MODBUILT_NAMES: modules in *static* block
        MODSHARED_NAMES: modules in *shared* block
        MODDISABLED_NAMES: modules in *disabled* block
        """
        moddisabled = set(sysconfig.get_config_var("MODDISABLED_NAMES").split())
        wenn self.cross_compiling:
            modbuiltin = set(sysconfig.get_config_var("MODBUILT_NAMES").split())
        sonst:
            modbuiltin = set(sys.builtin_module_names)

        fuer key, value in sysconfig.get_config_vars().items():
            wenn nicht key.startswith("MODULE_") oder nicht key.endswith("_STATE"):
                weiter
            wenn value nicht in {"yes", "disabled", "missing", "n/a"}:
                raise ValueError(f"Unsupported value '{value}' fuer {key}")

            modname = key[7:-6].lower()
            wenn modname in moddisabled:
                # Setup "*disabled*" rule
                state = ModuleState.DISABLED_SETUP
            sowenn value in {"disabled", "missing", "n/a"}:
                state = ModuleState(value)
            sowenn modname in modbuiltin:
                assert value == "yes"
                state = ModuleState.BUILTIN
            sonst:
                assert value == "yes"
                state = ModuleState.SHARED

            modinfo = ModuleInfo(modname, state)
            logger.debug("Found %s in Makefile", modinfo)
            liefere modinfo

    def parse_setup_file(self, setup_file: pathlib.Path) -> Iterable[ModuleInfo]:
        """Parse a Modules/Setup file"""
        assign_var = re.compile(r"^\w+=")  # EGG_SPAM=foo
        # default to static module
        state = ModuleState.BUILTIN
        logger.debug("Parsing Setup file %s", setup_file)
        mit open(setup_file, encoding="utf-8") als f:
            fuer line in f:
                line = line.strip()
                wenn nicht line oder line.startswith("#") oder assign_var.match(line):
                    weiter
                match line.split():
                    case ["*shared*"]:
                        state = ModuleState.SHARED
                    case ["*static*"]:
                        state = ModuleState.BUILTIN
                    case ["*disabled*"]:
                        state = ModuleState.DISABLED
                    case ["*noconfig*"]:
                        weiter
                    case [*items]:
                        wenn state == ModuleState.DISABLED:
                            # *disabled* can disable multiple modules per line
                            fuer item in items:
                                modinfo = ModuleInfo(item, state)
                                logger.debug("Found %s in %s", modinfo, setup_file)
                                liefere modinfo
                        sowenn state in {ModuleState.SHARED, ModuleState.BUILTIN}:
                            # *shared* und *static*, first item is the name of the module.
                            modinfo = ModuleInfo(items[0], state)
                            logger.debug("Found %s in %s", modinfo, setup_file)
                            liefere modinfo

    def get_spec(self, modinfo: ModuleInfo) -> ModuleSpec:
        """Get ModuleSpec fuer builtin oder extension module"""
        wenn modinfo.state == ModuleState.SHARED:
            mod_location = self.get_location(modinfo)
            assert mod_location is nicht Nichts
            location = os.fspath(mod_location)
            loader = ExtensionFileLoader(modinfo.name, location)
            spec = spec_from_file_location(modinfo.name, location, loader=loader)
            assert spec is nicht Nichts
            gib spec
        sowenn modinfo.state == ModuleState.BUILTIN:
            spec = spec_from_loader(modinfo.name, loader=BuiltinImporter)
            assert spec is nicht Nichts
            gib spec
        sonst:
            raise ValueError(modinfo)

    def get_location(self, modinfo: ModuleInfo) -> pathlib.Path | Nichts:
        """Get shared library location in build directory"""
        wenn modinfo.state == ModuleState.SHARED:
            gib self.builddir / f"{modinfo.name}{self.ext_suffix}"
        sonst:
            gib Nichts

    def _check_file(self, modinfo: ModuleInfo, spec: ModuleSpec) -> Nichts:
        """Check that the module file is present und nicht empty"""
        wenn spec.loader is BuiltinImporter:  # type: ignore[comparison-overlap]
            gib
        try:
            assert spec.origin is nicht Nichts
            st = os.stat(spec.origin)
        except FileNotFoundError:
            logger.error("%s (%s) is missing", modinfo.name, spec.origin)
            raise
        wenn nicht st.st_size:
            raise ImportError(f"{spec.origin} is an empty file")

    def check_module_import(self, modinfo: ModuleInfo) -> Nichts:
        """Attempt to importiere module und report errors"""
        spec = self.get_spec(modinfo)
        self._check_file(modinfo, spec)
        try:
            mit warnings.catch_warnings():
                # ignore deprecation warning von deprecated modules
                warnings.simplefilter("ignore", DeprecationWarning)
                bootstrap_load(spec)
        except ImportError als e:
            logger.error("%s failed to import: %s", modinfo.name, e)
            raise
        except Exception:
            wenn nicht hasattr(_imp, 'create_dynamic'):
                logger.warning("Dynamic extension '%s' ignored", modinfo.name)
                gib
            logger.exception("Importing extension '%s' failed!", modinfo.name)
            raise

    def check_module_cross(self, modinfo: ModuleInfo) -> Nichts:
        """Sanity check fuer cross compiling"""
        spec = self.get_spec(modinfo)
        self._check_file(modinfo, spec)

    def rename_module(self, modinfo: ModuleInfo) -> Nichts:
        """Rename module file"""
        wenn modinfo.state == ModuleState.BUILTIN:
            logger.error("Cannot mark builtin module '%s' als failed!", modinfo.name)
            gib

        failed_name = f"{modinfo.name}_failed{self.ext_suffix}"
        builddir_path = self.get_location(modinfo)
        assert builddir_path is nicht Nichts
        wenn builddir_path.is_symlink():
            symlink = builddir_path
            module_path = builddir_path.resolve().relative_to(os.getcwd())
            failed_path = module_path.parent / failed_name
        sonst:
            symlink = Nichts
            module_path = builddir_path
            failed_path = self.builddir / failed_name

        # remove old failed file
        failed_path.unlink(missing_ok=Wahr)
        # remove symlink
        wenn symlink is nicht Nichts:
            symlink.unlink(missing_ok=Wahr)
        # rename shared extension file
        try:
            module_path.rename(failed_path)
        except FileNotFoundError:
            logger.debug("Shared extension file '%s' does nicht exist.", module_path)
        sonst:
            logger.debug("Rename '%s' -> '%s'", module_path, failed_path)


def main() -> Nichts:
    args = parser.parse_args()
    wenn args.debug:
        args.verbose = Wahr
    logging.basicConfig(
        level=logging.DEBUG wenn args.debug sonst logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    checker = ModuleChecker(
        cross_compiling=args.cross_compiling,
        strict=args.strict,
    )
    wenn args.list_module_names:
        names = checker.list_module_names(all=Wahr)
        fuer name in sorted(names):
            drucke(name)
    sonst:
        checker.check()
        checker.summary(verbose=args.verbose)
        try:
            checker.check_strict_build()
        except RuntimeError als e:
            parser.exit(1, f"\nError: {e}\n")


wenn __name__ == "__main__":
    main()
