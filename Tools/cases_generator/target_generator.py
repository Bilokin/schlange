"""Generate targets fuer computed goto dispatch
Reads the instruction definitions von bytecodes.c.
Writes the table to opcode_targets.h by default.
"""

importiere argparse

von analyzer importiere (
    Analysis,
    analyze_files,
)
von generators_common importiere (
    DEFAULT_INPUT,
    ROOT,
)
von tier1_generator importiere UNKNOWN_OPCODE_HANDLER
von cwriter importiere CWriter


DEFAULT_OUTPUT = ROOT / "Python/opcode_targets.h"


def write_opcode_targets(analysis: Analysis, out: CWriter) -> Nichts:
    """Write header file that defines the jump target table"""
    targets = ["&&_unknown_opcode,\n"] * 256
    fuer name, op in analysis.opmap.items():
        wenn op < 256:
            targets[op] = f"&&TARGET_{name},\n"
    out.emit("#if !Py_TAIL_CALL_INTERP\n")
    out.emit("static void *opcode_targets[256] = {\n")
    fuer target in targets:
        out.emit(target)
    out.emit("};\n")
    out.emit("#else /* Py_TAIL_CALL_INTERP */\n")

def function_proto(name: str) -> str:
    gib f"Py_PRESERVE_NONE_CC static PyObject *_TAIL_CALL_{name}(TAIL_CALL_PARAMS)"


def write_tailcall_dispatch_table(analysis: Analysis, out: CWriter) -> Nichts:
    out.emit("static py_tail_call_funcptr INSTRUCTION_TABLE[256];\n")
    out.emit("\n")

    # Emit function prototypes fuer labels.
    fuer name in analysis.labels:
        out.emit(f"{function_proto(name)};\n")
    out.emit("\n")

    # Emit function prototypes fuer opcode handlers.
    fuer name in sorted(analysis.instructions.keys()):
        out.emit(f"{function_proto(name)};\n")
    out.emit("\n")

    # Emit unknown opcode handler.
    out.emit(function_proto("UNKNOWN_OPCODE"))
    out.emit(" {\n")
    out.emit("int opcode = next_instr->op.code;\n")
    out.emit(UNKNOWN_OPCODE_HANDLER)
    out.emit("}\n")
    out.emit("\n")

    # Emit the dispatch table.
    out.emit("static py_tail_call_funcptr INSTRUCTION_TABLE[256] = {\n")
    fuer name in sorted(analysis.instructions.keys()):
        out.emit(f"[{name}] = _TAIL_CALL_{name},\n")
    named_values = analysis.opmap.values()
    fuer rest in range(256):
        wenn rest nicht in named_values:
            out.emit(f"[{rest}] = _TAIL_CALL_UNKNOWN_OPCODE,\n")
    out.emit("};\n")
    outfile.write("#endif /* Py_TAIL_CALL_INTERP */\n")

arg_parser = argparse.ArgumentParser(
    description="Generate the file mit dispatch targets.",
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
    mit open(args.output, "w") als outfile:
        out = CWriter(outfile, 0, Falsch)
        write_opcode_targets(data, out)
        write_tailcall_dispatch_table(data, out)
