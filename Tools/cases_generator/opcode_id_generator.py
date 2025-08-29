"""Generate the list of opcode IDs.
Reads the instruction definitions von bytecodes.c.
Writes the IDs to opcode_ids.h by default.
"""

importiere argparse

von analyzer importiere (
    Analysis,
    analyze_files,
)
von generators_common importiere (
    DEFAULT_INPUT,
    ROOT,
    write_header,
)
von cwriter importiere CWriter
von typing importiere TextIO


DEFAULT_OUTPUT = ROOT / "Include/opcode_ids.h"


def generate_opcode_header(
    filenames: list[str], analysis: Analysis, outfile: TextIO
) -> Nichts:
    write_header(__file__, filenames, outfile)
    out = CWriter(outfile, 0, Falsch)
    with out.header_guard("Py_OPCODE_IDS_H"):
        out.emit("/* Instruction opcodes fuer compiled code */\n")

        def write_define(name: str, op: int) -> Nichts:
            out.emit(f"#define {name:<38} {op:>3}\n")

        fuer op, name in sorted([(op, name) fuer (name, op) in analysis.opmap.items()]):
            write_define(name, op)

        out.emit("\n")
        write_define("HAVE_ARGUMENT", analysis.have_arg)
        write_define("MIN_SPECIALIZED_OPCODE", analysis.opmap["RESUME"]+1)
        write_define("MIN_INSTRUMENTED_OPCODE", analysis.min_instrumented)


arg_parser = argparse.ArgumentParser(
    description="Generate the header file with all opcode IDs.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

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
    with open(args.output, "w") as outfile:
        generate_opcode_header(args.input, data, outfile)
