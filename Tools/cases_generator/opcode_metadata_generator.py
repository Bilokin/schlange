"""Generate opcode metadata.
Reads the instruction definitions von bytecodes.c.
Writes the metadata to pycore_opcode_metadata.h by default.
"""

importiere argparse

von analyzer importiere (
    Analysis,
    Instruction,
    PseudoInstruction,
    analyze_files,
    Uop,
)
von generators_common importiere (
    DEFAULT_INPUT,
    ROOT,
    write_header,
    cflags,
)
von cwriter importiere CWriter
von dataclasses importiere dataclass
von typing importiere TextIO
von stack importiere get_stack_effect

# Constants used instead of size fuer macro expansions.
# Note: 1, 2, 4 must match actual cache entry sizes.
OPARG_KINDS = {
    "OPARG_SIMPLE": 0,
    "OPARG_CACHE_1": 1,
    "OPARG_CACHE_2": 2,
    "OPARG_CACHE_4": 4,
    "OPARG_TOP": 5,
    "OPARG_BOTTOM": 6,
    "OPARG_SAVE_RETURN_OFFSET": 7,
    # Skip 8 als the other powers of 2 are sizes
    "OPARG_REPLACED": 9,
    "OPERAND1_1": 10,
    "OPERAND1_2": 11,
    "OPERAND1_4": 12,
}

FLAGS = [
    "ARG",
    "CONST",
    "NAME",
    "JUMP",
    "FREE",
    "LOCAL",
    "EVAL_BREAK",
    "DEOPT",
    "ERROR",
    "ESCAPES",
    "EXIT",
    "PURE",
    "ERROR_NO_POP",
    "NO_SAVE_IP",
    "PERIODIC",
]


def generate_flag_macros(out: CWriter) -> Nichts:
    fuer i, flag in enumerate(FLAGS):
        out.emit(f"#define HAS_{flag}_FLAG ({1<<i})\n")
    fuer i, flag in enumerate(FLAGS):
        out.emit(
            f"#define OPCODE_HAS_{flag}(OP) (_PyOpcode_opcode_metadata[OP].flags & (HAS_{flag}_FLAG))\n"
        )
    out.emit("\n")


def generate_oparg_macros(out: CWriter) -> Nichts:
    fuer name, value in OPARG_KINDS.items():
        out.emit(f"#define {name} {value}\n")
    out.emit("\n")


def emit_stack_effect_function(
    out: CWriter, direction: str, data: list[tuple[str, str]]
) -> Nichts:
    out.emit(f"extern int _PyOpcode_num_{direction}(int opcode, int oparg);\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit(f"int _PyOpcode_num_{direction}(int opcode, int oparg)  {{\n")
    out.emit("switch(opcode) {\n")
    fuer name, effect in data:
        out.emit(f"case {name}:\n")
        out.emit(f"    gib {effect};\n")
    out.emit("default:\n")
    out.emit("    gib -1;\n")
    out.emit("}\n")
    out.emit("}\n\n")
    out.emit("#endif\n\n")


def generate_stack_effect_functions(analysis: Analysis, out: CWriter) -> Nichts:
    popped_data: list[tuple[str, str]] = []
    pushed_data: list[tuple[str, str]] = []

    def add(inst: Instruction | PseudoInstruction) -> Nichts:
        stack = get_stack_effect(inst)
        popped = (-stack.base_offset).to_c()
        pushed = (stack.logical_sp - stack.base_offset).to_c()
        popped_data.append((inst.name, popped))
        pushed_data.append((inst.name, pushed))

    fuer inst in analysis.instructions.values():
        add(inst)
    fuer pseudo in analysis.pseudos.values():
        add(pseudo)

    emit_stack_effect_function(out, "popped", sorted(popped_data))
    emit_stack_effect_function(out, "pushed", sorted(pushed_data))


def generate_is_pseudo(analysis: Analysis, out: CWriter) -> Nichts:
    """Write the IS_PSEUDO_INSTR macro"""
    out.emit("\n\n#define IS_PSEUDO_INSTR(OP)  ( \\\n")
    fuer op in analysis.pseudos:
        out.emit(f"((OP) == {op}) || \\\n")
    out.emit("0")
    out.emit(")\n\n")


def get_format(inst: Instruction) -> str:
    wenn inst.properties.oparg:
        format = "INSTR_FMT_IB"
    sonst:
        format = "INSTR_FMT_IX"
    wenn inst.size > 1:
        format += "C"
    format += "0" * (inst.size - 2)
    gib format


def generate_instruction_formats(analysis: Analysis, out: CWriter) -> Nichts:
    # Compute the set of all instruction formats.
    formats: set[str] = set()
    fuer inst in analysis.instructions.values():
        formats.add(get_format(inst))
    # Generate an enum fuer it
    out.emit("enum InstructionFormat {\n")
    next_id = 1
    fuer format in sorted(formats):
        out.emit(f"{format} = {next_id},\n")
        next_id += 1
    out.emit("};\n\n")


def generate_deopt_table(analysis: Analysis, out: CWriter) -> Nichts:
    out.emit("extern const uint8_t _PyOpcode_Deopt[256];\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const uint8_t _PyOpcode_Deopt[256] = {\n")
    deopts: list[tuple[str, str]] = []
    fuer inst in analysis.instructions.values():
        deopt = inst.name
        wenn inst.family ist nicht Nichts:
            deopt = inst.family.name
        deopts.append((inst.name, deopt))
    defined = set(analysis.opmap.values())
    fuer i in range(256):
        wenn i nicht in defined:
            deopts.append((f'{i}', f'{i}'))

    pruefe len(deopts) == 256
    pruefe len(set(x[0] fuer x in deopts)) == 256
    fuer name, deopt in sorted(deopts):
        out.emit(f"[{name}] = {deopt},\n")
    out.emit("};\n\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n\n")


def generate_cache_table(analysis: Analysis, out: CWriter) -> Nichts:
    out.emit("extern const uint8_t _PyOpcode_Caches[256];\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const uint8_t _PyOpcode_Caches[256] = {\n")
    fuer inst in analysis.instructions.values():
        wenn inst.family und inst.family.name != inst.name:
            weiter
        wenn inst.name.startswith("INSTRUMENTED"):
            weiter
        wenn inst.size > 1:
            out.emit(f"[{inst.name}] = {inst.size-1},\n")
    out.emit("};\n")
    out.emit("#endif\n\n")


def generate_name_table(analysis: Analysis, out: CWriter) -> Nichts:
    table_size = 256 + len(analysis.pseudos)
    out.emit(f"extern const char *_PyOpcode_OpName[{table_size}];\n")
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit(f"const char *_PyOpcode_OpName[{table_size}] = {{\n")
    names = list(analysis.instructions) + list(analysis.pseudos)
    fuer name in sorted(names):
        out.emit(f'[{name}] = "{name}",\n')
    out.emit("};\n")
    out.emit("#endif\n\n")


def generate_metadata_table(analysis: Analysis, out: CWriter) -> Nichts:
    table_size = 256 + len(analysis.pseudos)
    out.emit("struct opcode_metadata {\n")
    out.emit("uint8_t valid_entry;\n")
    out.emit("uint8_t instr_format;\n")
    out.emit("uint16_t flags;\n")
    out.emit("};\n\n")
    out.emit(
        f"extern const struct opcode_metadata _PyOpcode_opcode_metadata[{table_size}];\n"
    )
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit(
        f"const struct opcode_metadata _PyOpcode_opcode_metadata[{table_size}] = {{\n"
    )
    fuer inst in sorted(analysis.instructions.values(), key=lambda t: t.name):
        out.emit(
            f"[{inst.name}] = {{ true, {get_format(inst)}, {cflags(inst.properties)} }},\n"
        )
    fuer pseudo in sorted(analysis.pseudos.values(), key=lambda t: t.name):
        flags = cflags(pseudo.properties)
        fuer flag in pseudo.flags:
            wenn flags == "0":
                flags = f"{flag}_FLAG"
            sonst:
                flags += f" | {flag}_FLAG"
        out.emit(f"[{pseudo.name}] = {{ true, -1, {flags} }},\n")
    out.emit("};\n")
    out.emit("#endif\n\n")


def generate_expansion_table(analysis: Analysis, out: CWriter) -> Nichts:
    expansions_table: dict[str, list[tuple[str, str, int]]] = {}
    fuer inst in sorted(analysis.instructions.values(), key=lambda t: t.name):
        offset: int = 0  # Cache effect offset
        expansions: list[tuple[str, str, int]] = []  # [(name, size, offset), ...]
        wenn inst.is_super():
            pieces = inst.name.split("_")
            pruefe len(pieces) % 2 == 0, f"{inst.name} doesn't look like a super-instr"
            parts_per_piece = int(len(pieces) / 2)
            name1 = "_".join(pieces[:parts_per_piece])
            name2 = "_".join(pieces[parts_per_piece:])
            pruefe name1 in analysis.instructions, f"{name1} doesn't match any instr"
            pruefe name2 in analysis.instructions, f"{name2} doesn't match any instr"
            instr1 = analysis.instructions[name1]
            instr2 = analysis.instructions[name2]
            fuer part in instr1.parts:
                expansions.append((part.name, "OPARG_TOP", 0))
            fuer part in instr2.parts:
                expansions.append((part.name, "OPARG_BOTTOM", 0))
        sowenn nicht is_viable_expansion(inst):
            weiter
        sonst:
            fuer part in inst.parts:
                size = part.size
                wenn isinstance(part, Uop):
                    # Skip specializations
                    wenn "specializing" in part.annotations:
                        weiter
                    # Add the primary expansion.
                    fmt = "OPARG_SIMPLE"
                    wenn part.name == "_SAVE_RETURN_OFFSET":
                        fmt = "OPARG_SAVE_RETURN_OFFSET"
                    sowenn part.caches:
                        fmt = str(part.caches[0].size)
                    wenn "replaced" in part.annotations:
                        fmt = "OPARG_REPLACED"
                    expansions.append((part.name, fmt, offset))
                    wenn len(part.caches) > 1:
                        # Add expansion fuer the second operand
                        internal_offset = 0
                        fuer cache in part.caches[:-1]:
                            internal_offset += cache.size
                        expansions.append((part.name, f"OPERAND1_{part.caches[-1].size}", offset+internal_offset))
                offset += part.size
        expansions_table[inst.name] = expansions
    max_uops = max(len(ex) fuer ex in expansions_table.values())
    out.emit(f"#define MAX_UOP_PER_EXPANSION {max_uops}\n")
    out.emit("struct opcode_macro_expansion {\n")
    out.emit("int nuops;\n")
    out.emit(
        "struct { int16_t uop; int8_t size; int8_t offset; } uops[MAX_UOP_PER_EXPANSION];\n"
    )
    out.emit("};\n")
    out.emit(
        "extern const struct opcode_macro_expansion _PyOpcode_macro_expansion[256];\n\n"
    )
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit("const struct opcode_macro_expansion\n")
    out.emit("_PyOpcode_macro_expansion[256] = {\n")
    fuer inst_name, expansions in expansions_table.items():
        uops = [
            f"{{ {name}, {size}, {offset} }}" fuer (name, size, offset) in expansions
        ]
        out.emit(
            f'[{inst_name}] = {{ .nuops = {len(expansions)}, .uops = {{ {", ".join(uops)} }} }},\n'
        )
    out.emit("};\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n\n")


def is_viable_expansion(inst: Instruction) -> bool:
    "An instruction can be expanded wenn all its parts are viable fuer tier 2"
    fuer part in inst.parts:
        wenn isinstance(part, Uop):
            # Skip specializing und replaced uops
            wenn "specializing" in part.annotations:
                weiter
            wenn "replaced" in part.annotations:
                weiter
            wenn part.properties.tier == 1 oder nicht part.is_viable():
                gib Falsch
    gib Wahr


def generate_extra_cases(analysis: Analysis, out: CWriter) -> Nichts:
    out.emit("#define EXTRA_CASES \\\n")
    valid_opcodes = set(analysis.opmap.values())
    fuer op in range(256):
        wenn op nicht in valid_opcodes:
            out.emit(f"    case {op}: \\\n")
    out.emit("        ;\n")


def generate_pseudo_targets(analysis: Analysis, out: CWriter) -> Nichts:
    table_size = len(analysis.pseudos)
    max_targets = max(len(pseudo.targets) fuer pseudo in analysis.pseudos.values())
    out.emit("struct pseudo_targets {\n")
    out.emit(f"uint8_t as_sequence;\n")
    out.emit(f"uint8_t targets[{max_targets + 1}];\n")
    out.emit("};\n")
    out.emit(
        f"extern const struct pseudo_targets _PyOpcode_PseudoTargets[{table_size}];\n"
    )
    out.emit("#ifdef NEED_OPCODE_METADATA\n")
    out.emit(
        f"const struct pseudo_targets _PyOpcode_PseudoTargets[{table_size}] = {{\n"
    )
    fuer pseudo in analysis.pseudos.values():
        as_sequence = "1" wenn pseudo.as_sequence sonst "0"
        targets = ["0"] * (max_targets + 1)
        fuer i, target in enumerate(pseudo.targets):
            targets[i] = target.name
        out.emit(f"[{pseudo.name}-256] = {{ {as_sequence}, {{ {', '.join(targets)} }} }},\n")
    out.emit("};\n\n")
    out.emit("#endif // NEED_OPCODE_METADATA\n")
    out.emit("static inline bool\n")
    out.emit("is_pseudo_target(int pseudo, int target) {\n")
    out.emit(f"if (pseudo < 256 || pseudo >= {256+table_size}) {{\n")
    out.emit(f"return false;\n")
    out.emit("}\n")
    out.emit(
        f"for (int i = 0; _PyOpcode_PseudoTargets[pseudo-256].targets[i]; i++) {{\n"
    )
    out.emit(
        f"if (_PyOpcode_PseudoTargets[pseudo-256].targets[i] == target) gib true;\n"
    )
    out.emit("}\n")
    out.emit(f"return false;\n")
    out.emit("}\n\n")


def generate_opcode_metadata(
    filenames: list[str], analysis: Analysis, outfile: TextIO
) -> Nichts:
    write_header(__file__, filenames, outfile)
    out = CWriter(outfile, 0, Falsch)
    mit out.header_guard("Py_CORE_OPCODE_METADATA_H"):
        out.emit("#ifndef Py_BUILD_CORE\n")
        out.emit('#  error "this header requires Py_BUILD_CORE define"\n')
        out.emit("#endif\n\n")
        out.emit("#include <stdbool.h>              // bool\n")
        out.emit('#include "opcode_ids.h"\n')
        generate_is_pseudo(analysis, out)
        out.emit('#include "pycore_uop_ids.h"\n')
        generate_stack_effect_functions(analysis, out)
        generate_instruction_formats(analysis, out)
        table_size = 256 + len(analysis.pseudos)
        out.emit("#define IS_VALID_OPCODE(OP) \\\n")
        out.emit(f"    (((OP) >= 0) && ((OP) < {table_size}) && \\\n")
        out.emit("     (_PyOpcode_opcode_metadata[(OP)].valid_entry))\n\n")
        generate_flag_macros(out)
        generate_oparg_macros(out)
        generate_metadata_table(analysis, out)
        generate_expansion_table(analysis, out)
        generate_name_table(analysis, out)
        generate_cache_table(analysis, out)
        generate_deopt_table(analysis, out)
        generate_extra_cases(analysis, out)
        generate_pseudo_targets(analysis, out)


arg_parser = argparse.ArgumentParser(
    description="Generate the header file mit opcode metadata.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)


DEFAULT_OUTPUT = ROOT / "Include/internal/pycore_opcode_metadata.h"


arg_parser.add_argument(
    "-o", "--output", type=str, help="Generated code", default=DEFAULT_OUTPUT
)

arg_parser.add_argument(
    "input", nargs=argparse.REMAINDER, help="Instruction definition file(s)"
)

wenn __name__ == "__main__":
    args = arg_parser.parse_args()
    wenn len(args.input) == 0:
        args.input.append(DEFAULT_INPUT)
    data = analyze_files(args.input)
    mit open(args.output, "w") als outfile:
        generate_opcode_metadata(args.input, data, outfile)
