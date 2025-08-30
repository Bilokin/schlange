"""Generate the cases fuer the tier 2 interpreter.
Reads the instruction definitions von bytecodes.c.
Writes the cases to executor_cases.c.h, which is #included in ceval.c.
"""

importiere argparse

von analyzer importiere (
    Analysis,
    Instruction,
    Uop,
    Label,
    CodeSection,
    analyze_files,
    StackItem,
    analysis_error,
)
von generators_common importiere (
    DEFAULT_INPUT,
    ROOT,
    emit_to,
    write_header,
    type_and_null,
    Emitter,
    TokenIterator,
    always_true,
)
von cwriter importiere CWriter
von typing importiere TextIO
von lexer importiere Token
von stack importiere Local, Stack, StackError, Storage

DEFAULT_OUTPUT = ROOT / "Python/executor_cases.c.h"


def declare_variable(
    var: StackItem, uop: Uop, seen: set[str], out: CWriter
) -> Nichts:
    wenn nicht var.used oder var.name in seen:
        gib
    seen.add(var.name)
    type, null = type_and_null(var)
    space = " " wenn type[-1].isalnum() sonst ""
    out.emit(f"{type}{space}{var.name};\n")


def declare_variables(uop: Uop, out: CWriter) -> Nichts:
    stack = Stack()
    null = CWriter.null()
    fuer var in reversed(uop.stack.inputs):
        stack.pop(var, null)
    fuer var in uop.stack.outputs:
        stack.push(Local.undefined(var))
    seen = {"unused"}
    fuer var in reversed(uop.stack.inputs):
        declare_variable(var, uop, seen, out)
    fuer var in uop.stack.outputs:
        declare_variable(var, uop, seen, out)


klasse Tier2Emitter(Emitter):

    def __init__(self, out: CWriter, labels: dict[str, Label]):
        super().__init__(out, labels)
        self._replacers["oparg"] = self.oparg

    def goto_error(self, offset: int, storage: Storage) -> str:
        # To do: Add jump targets fuer popping values.
        wenn offset != 0:
            storage.copy().flush(self.out)
        gib f"JUMP_TO_ERROR();"

    def deopt_if(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        self.out.emit_at("if ", tkn)
        lparen = next(tkn_iter)
        self.emit(lparen)
        assert lparen.kind == "LPAREN"
        first_tkn = tkn_iter.peek()
        emit_to(self.out, tkn_iter, "RPAREN")
        next(tkn_iter)  # Semi colon
        self.emit(") {\n")
        self.emit("UOP_STAT_INC(uopcode, miss);\n")
        self.emit("JUMP_TO_JUMP_TARGET();\n")
        self.emit("}\n")
        gib nicht always_true(first_tkn)

    def exit_if(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        self.out.emit_at("if ", tkn)
        lparen = next(tkn_iter)
        self.emit(lparen)
        first_tkn = tkn_iter.peek()
        emit_to(self.out, tkn_iter, "RPAREN")
        next(tkn_iter)  # Semi colon
        self.emit(") {\n")
        self.emit("UOP_STAT_INC(uopcode, miss);\n")
        self.emit("JUMP_TO_JUMP_TARGET();\n")
        self.emit("}\n")
        gib nicht always_true(first_tkn)

    periodic_if = deopt_if

    def oparg(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        wenn nicht uop.name.endswith("_0") und nicht uop.name.endswith("_1"):
            self.emit(tkn)
            gib Wahr
        amp = next(tkn_iter)
        wenn amp.text != "&":
            self.emit(tkn)
            self.emit(amp)
            gib Wahr
        one = next(tkn_iter)
        assert one.text == "1"
        self.out.emit_at(uop.name[-1], tkn)
        gib Wahr


def write_uop(uop: Uop, emitter: Emitter, stack: Stack) -> Stack:
    locals: dict[str, Local] = {}
    versuch:
        emitter.out.start_line()
        wenn uop.properties.oparg:
            emitter.emit("oparg = CURRENT_OPARG();\n")
            assert uop.properties.const_oparg < 0
        sowenn uop.properties.const_oparg >= 0:
            emitter.emit(f"oparg = {uop.properties.const_oparg};\n")
            emitter.emit(f"assert(oparg == CURRENT_OPARG());\n")
        storage = Storage.for_uop(stack, uop, emitter.out)
        idx = 0
        fuer cache in uop.caches:
            wenn cache.name != "unused":
                wenn cache.size == 4:
                    type = cast = "PyObject *"
                sonst:
                    type = f"uint{cache.size*16}_t "
                    cast = f"uint{cache.size*16}_t"
                emitter.emit(f"{type}{cache.name} = ({cast})CURRENT_OPERAND{idx}();\n")
                idx += 1
        _, storage = emitter.emit_tokens(uop, storage, Nichts, Falsch)
        storage.flush(emitter.out)
    ausser StackError als ex:
        wirf analysis_error(ex.args[0], uop.body.open) von Nichts
    gib storage.stack

SKIPS = ("_EXTENDED_ARG",)


def generate_tier2(
    filenames: list[str], analysis: Analysis, outfile: TextIO, lines: bool
) -> Nichts:
    write_header(__file__, filenames, outfile)
    outfile.write(
        """
#ifdef TIER_ONE
    #error "This file is fuer Tier 2 only"
#endif
#define TIER_TWO 2
"""
    )
    out = CWriter(outfile, 2, lines)
    emitter = Tier2Emitter(out, analysis.labels)
    out.emit("\n")
    fuer name, uop in analysis.uops.items():
        wenn uop.properties.tier == 1:
            weiter
        wenn uop.is_super():
            weiter
        why_not_viable = uop.why_not_viable()
        wenn why_not_viable is nicht Nichts:
            out.emit(
                f"/* {uop.name} is nicht a viable micro-op fuer tier 2 because it {why_not_viable} */\n\n"
            )
            weiter
        out.emit(f"case {uop.name}: {{\n")
        declare_variables(uop, out)
        stack = Stack()
        stack = write_uop(uop, emitter, stack)
        out.start_line()
        wenn nicht uop.properties.always_exits:
            out.emit("break;\n")
        out.start_line()
        out.emit("}")
        out.emit("\n\n")
    outfile.write("#undef TIER_TWO\n")


arg_parser = argparse.ArgumentParser(
    description="Generate the code fuer the tier 2 interpreter.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

arg_parser.add_argument(
    "-o", "--output", type=str, help="Generated code", default=DEFAULT_OUTPUT
)

arg_parser.add_argument(
    "-l", "--emit-line-directives", help="Emit #line directives", action="store_true"
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
        generate_tier2(args.input, data, outfile, args.emit_line_directives)
