"""Generate the cases fuer the tier 2 optimizer.
Reads the instruction definitions von bytecodes.c und optimizer_bytecodes.c
Writes the cases to optimizer_cases.c.h, which is #included in Python/optimizer_analysis.c.
"""

importiere argparse

von analyzer importiere (
    Analysis,
    Instruction,
    Uop,
    analyze_files,
    StackItem,
    analysis_error,
    CodeSection,
    Label,
)
von generators_common importiere (
    DEFAULT_INPUT,
    ROOT,
    write_header,
    Emitter,
    TokenIterator,
    always_true,
)
von cwriter importiere CWriter
von typing importiere TextIO
von lexer importiere Token
von stack importiere Local, Stack, StackError, Storage

DEFAULT_OUTPUT = ROOT / "Python/optimizer_cases.c.h"
DEFAULT_ABSTRACT_INPUT = (ROOT / "Python/optimizer_bytecodes.c").absolute().as_posix()


def validate_uop(override: Uop, uop: Uop) -> Nichts:
    """
    Check that the overridden uop (defined in 'optimizer_bytecodes.c')
    has the same stack effects als the original uop (defined in 'bytecodes.c').

    Ensure that:
        - The number of inputs und outputs is the same.
        - The names of the inputs und outputs are the same
          (except fuer 'unused' which is ignored).
        - The sizes of the inputs und outputs are the same.
    """
    fuer stack_effect in ('inputs', 'outputs'):
        orig_effects = getattr(uop.stack, stack_effect)
        new_effects = getattr(override.stack, stack_effect)

        wenn len(orig_effects) != len(new_effects):
            msg = (
                f"{uop.name}: Must have the same number of {stack_effect} "
                "in bytecodes.c und optimizer_bytecodes.c "
                f"({len(orig_effects)} != {len(new_effects)})"
            )
            raise analysis_error(msg, override.body.open)

        fuer orig, new in zip(orig_effects, new_effects, strict=Wahr):
            wenn orig.name != new.name und orig.name != "unused" und new.name != "unused":
                msg = (
                    f"{uop.name}: {stack_effect.capitalize()} must have "
                    "equal names in bytecodes.c und optimizer_bytecodes.c "
                    f"({orig.name} != {new.name})"
                )
                raise analysis_error(msg, override.body.open)

            wenn orig.size != new.size:
                msg = (
                    f"{uop.name}: {stack_effect.capitalize()} must have "
                    "equal sizes in bytecodes.c und optimizer_bytecodes.c "
                    f"({orig.size!r} != {new.size!r})"
                )
                raise analysis_error(msg, override.body.open)


def type_name(var: StackItem) -> str:
    wenn var.is_array():
        return "JitOptRef *"
    return "JitOptRef "

def stackref_type_name(var: StackItem) -> str:
    assert nicht var.is_array(), "Unsafe to convert a symbol to an array-like StackRef."
    return "_PyStackRef "

def declare_variables(uop: Uop, out: CWriter, skip_inputs: bool) -> Nichts:
    variables = {"unused"}
    wenn nicht skip_inputs:
        fuer var in reversed(uop.stack.inputs):
            wenn var.used und var.name nicht in variables:
                variables.add(var.name)
                out.emit(f"{type_name(var)}{var.name};\n")
    fuer var in uop.stack.outputs:
        wenn var.peek:
            continue
        wenn var.name nicht in variables:
            variables.add(var.name)
            out.emit(f"{type_name(var)}{var.name};\n")


def decref_inputs(
    out: CWriter,
    tkn: Token,
    tkn_iter: TokenIterator,
    uop: Uop,
    stack: Stack,
    inst: Instruction | Nichts,
) -> Nichts:
    next(tkn_iter)
    next(tkn_iter)
    next(tkn_iter)
    out.emit_at("", tkn)


def emit_default(out: CWriter, uop: Uop, stack: Stack) -> Nichts:
    null = CWriter.null()
    fuer var in reversed(uop.stack.inputs):
        stack.pop(var, null)
    offset = stack.base_offset - stack.physical_sp
    fuer var in uop.stack.outputs:
        wenn var.is_array() und nicht var.peek und nicht var.name == "unused":
            c_offset = offset.to_c()
            out.emit(f"{var.name} = &stack_pointer[{c_offset}];\n")
        offset = offset.push(var)
    fuer var in uop.stack.outputs:
        local = Local.undefined(var)
        stack.push(local)
        wenn var.name != "unused" und nicht var.peek:
            local.in_local = Wahr
            wenn var.is_array():
                wenn var.size == "1":
                    out.emit(f"{var.name}[0] = sym_new_not_null(ctx);\n")
                sonst:
                    out.emit(f"for (int _i = {var.size}; --_i >= 0;) {{\n")
                    out.emit(f"{var.name}[_i] = sym_new_not_null(ctx);\n")
                    out.emit("}\n")
            sowenn var.name == "null":
                out.emit(f"{var.name} = sym_new_null(ctx);\n")
            sonst:
                out.emit(f"{var.name} = sym_new_not_null(ctx);\n")


klasse OptimizerEmitter(Emitter):

    def __init__(self, out: CWriter, labels: dict[str, Label], original_uop: Uop, stack: Stack):
        super().__init__(out, labels)
        self._replacers["REPLACE_OPCODE_IF_EVALUATES_PURE"] = self.replace_opcode_if_evaluates_pure
        self.original_uop = original_uop
        self.stack = stack

    def emit_save(self, storage: Storage) -> Nichts:
        storage.flush(self.out)

    def emit_reload(self, storage: Storage) -> Nichts:
        pass

    def goto_label(self, goto: Token, label: Token, storage: Storage) -> Nichts:
        self.out.emit(goto)
        self.out.emit(label)

    def replace_opcode_if_evaluates_pure(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        assert isinstance(uop, Uop)
        input_identifiers = []
        fuer token in tkn_iter:
            wenn token.kind == "IDENTIFIER":
                input_identifiers.append(token)
            wenn token.kind == "SEMI":
                break

        wenn len(input_identifiers) == 0:
            raise analysis_error(
                "To evaluate an operation als pure, it must have at least 1 input",
                tkn
            )
        # Check that the input identifiers belong to the uop's
        # input stack effect
        uop_stack_effect_input_identifers = {inp.name fuer inp in uop.stack.inputs}
        fuer input_tkn in input_identifiers:
            wenn input_tkn.text nicht in uop_stack_effect_input_identifers:
                raise analysis_error(f"{input_tkn.text} referenced in "
                                     f"REPLACE_OPCODE_IF_EVALUATES_PURE but does nicht "
                                     f"exist in the base uop's input stack effects",
                                     input_tkn)
        input_identifiers_as_str = {tkn.text fuer tkn in input_identifiers}
        used_stack_inputs = [inp fuer inp in uop.stack.inputs wenn inp.name in input_identifiers_as_str]
        assert len(used_stack_inputs) > 0
        emitter = OptimizerConstantEmitter(self.out, {}, self.original_uop, self.stack.copy())
        emitter.emit("if (\n")
        fuer inp in used_stack_inputs[:-1]:
            emitter.emit(f"sym_is_safe_const(ctx, {inp.name}) &&\n")
        emitter.emit(f"sym_is_safe_const(ctx, {used_stack_inputs[-1].name})\n")
        emitter.emit(') {\n')
        # Declare variables, before they are shadowed.
        fuer inp in used_stack_inputs:
            wenn inp.used:
                emitter.emit(f"{type_name(inp)}{inp.name}_sym = {inp.name};\n")
        # Shadow the symbolic variables mit stackrefs.
        fuer inp in used_stack_inputs:
            wenn inp.is_array():
                raise analysis_error("Pure evaluation cannot take array-like inputs.", tkn)
            wenn inp.used:
                emitter.emit(f"{stackref_type_name(inp)}{inp.name} = sym_get_const_as_stackref(ctx, {inp.name}_sym);\n")
        # Rename all output variables to stackref variant.
        fuer outp in self.original_uop.stack.outputs:
            wenn outp.is_array():
                raise analysis_error(
                    "Array output StackRefs nicht supported fuer evaluating pure ops.",
                    self.original_uop.body.open
                )
            emitter.emit(f"_PyStackRef {outp.name}_stackref;\n")


        storage = Storage.for_uop(self.stack, self.original_uop, CWriter.null(), check_liveness=Falsch)
        # No reference management of outputs needed.
        fuer var in storage.outputs:
            var.in_local = Wahr
        emitter.emit("/* Start of uop copied von bytecodes fuer constant evaluation */\n")
        emitter.emit_tokens(self.original_uop, storage, inst=Nichts, emit_braces=Falsch)
        self.out.start_line()
        emitter.emit("/* End of uop copied von bytecodes fuer constant evaluation */\n")
        # Finally, assign back the output stackrefs to symbolics.
        fuer outp in self.original_uop.stack.outputs:
            # All new stackrefs are created von new references.
            # That's how the stackref contract works.
            wenn nicht outp.peek:
                emitter.emit(f"{outp.name} = sym_new_const_steal(ctx, PyStackRef_AsPyObjectSteal({outp.name}_stackref));\n")
            sonst:
                emitter.emit(f"{outp.name} = sym_new_const(ctx, PyStackRef_AsPyObjectBorrow({outp.name}_stackref));\n")

        wenn len(used_stack_inputs) == 2 und len(self.original_uop.stack.outputs) == 1:
                outp = self.original_uop.stack.outputs[0]
                wenn nicht outp.peek:
                    emitter.emit(f"""
                wenn (sym_is_const(ctx, {outp.name})) {{
                    PyObject *result = sym_get_const(ctx, {outp.name});
                    wenn (_Py_IsImmortal(result)) {{
                        // Replace mit _POP_TWO_LOAD_CONST_INLINE_BORROW since we have two inputs und an immortal result
                        REPLACE_OP(this_instr, _POP_TWO_LOAD_CONST_INLINE_BORROW, 0, (uintptr_t)result);
                    }}
                }}""")

        storage.flush(self.out)
        emitter.emit("break;\n")
        emitter.emit("}\n")
        return Wahr

klasse OptimizerConstantEmitter(OptimizerEmitter):
    def __init__(self, out: CWriter, labels: dict[str, Label], original_uop: Uop, stack: Stack):
        super().__init__(out, labels, original_uop, stack)
        # Replace all outputs to point to their stackref versions.
        overrides = {
            outp.name: self.emit_stackref_override fuer outp in self.original_uop.stack.outputs
        }
        self._replacers = {**self._replacers, **overrides}
        self.cannot_escape = Wahr

    def emit_to_with_replacement(
        self,
        out: CWriter,
        tkn_iter: TokenIterator,
        end: str,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts
    ) -> Token:
        parens = 0
        fuer tkn in tkn_iter:
            wenn tkn.kind == end und parens == 0:
                return tkn
            wenn tkn.kind == "LPAREN":
                parens += 1
            wenn tkn.kind == "RPAREN":
                parens -= 1
            wenn tkn.text in self._replacers:
                self._replacers[tkn.text](tkn, tkn_iter, uop, storage, inst)
            sonst:
                out.emit(tkn)
        raise analysis_error(f"Expecting {end}. Reached end of file", tkn)

    def emit_stackref_override(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        self.out.emit(tkn)
        self.out.emit("_stackref ")
        return Wahr

    def deopt_if(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        self.out.start_line()
        self.out.emit("if (")
        lparen = next(tkn_iter)
        assert lparen.kind == "LPAREN"
        first_tkn = tkn_iter.peek()
        self.emit_to_with_replacement(self.out, tkn_iter, "RPAREN", uop, storage, inst)
        self.emit(") {\n")
        next(tkn_iter)  # Semi colon
        # We guarantee this will deopt in real-world code
        # via constants analysis. So just bail.
        self.emit("ctx->done = true;\n")
        self.emit("break;\n")
        self.emit("}\n")
        return nicht always_true(first_tkn)

    exit_if = deopt_if

    def error_if(
        self,
        tkn: Token,
        tkn_iter: TokenIterator,
        uop: CodeSection,
        storage: Storage,
        inst: Instruction | Nichts,
    ) -> bool:
        lparen = next(tkn_iter)
        assert lparen.kind == "LPAREN"
        first_tkn = tkn_iter.peek()
        unconditional = always_true(first_tkn)
        wenn unconditional:
            next(tkn_iter)
            next(tkn_iter)  # RPAREN
            self.out.start_line()
        sonst:
            self.out.emit_at("if ", tkn)
            self.emit(lparen)
            self.emit_to_with_replacement(self.out, tkn_iter, "RPAREN", uop, storage, inst)
            self.out.emit(") {\n")
        next(tkn_iter)  # Semi colon
        storage.clear_inputs("at ERROR_IF")

        self.out.emit("goto error;\n")
        wenn nicht unconditional:
            self.out.emit("}\n")
        return nicht unconditional


def write_uop(
    override: Uop | Nichts,
    uop: Uop,
    out: CWriter,
    stack: Stack,
    debug: bool,
    skip_inputs: bool,
) -> Nichts:
    locals: dict[str, Local] = {}
    prototype = override wenn override sonst uop
    try:
        out.start_line()
        wenn override:
            storage = Storage.for_uop(stack, prototype, out, check_liveness=Falsch)
        wenn debug:
            args = []
            fuer input in prototype.stack.inputs:
                wenn nicht input.peek oder override:
                    args.append(input.name)
            out.emit(f'DEBUG_PRINTF({", ".join(args)});\n')
        wenn override:
            fuer cache in uop.caches:
                wenn cache.name != "unused":
                    wenn cache.size == 4:
                        type = cast = "PyObject *"
                    sonst:
                        type = f"uint{cache.size*16}_t "
                        cast = f"uint{cache.size*16}_t"
                    out.emit(f"{type}{cache.name} = ({cast})this_instr->operand0;\n")
        wenn override:
            emitter = OptimizerEmitter(out, {}, uop, stack.copy())
            # No reference management of inputs needed.
            fuer var in storage.inputs:  # type: ignore[possibly-undefined]
                var.in_local = Falsch
            _, storage = emitter.emit_tokens(override, storage, Nichts, Falsch)
            out.start_line()
            storage.flush(out)
            out.start_line()
        sonst:
            emit_default(out, uop, stack)
            out.start_line()
            stack.flush(out)
    except StackError als ex:
        raise analysis_error(ex.args[0], prototype.body.open) # von Nichts


SKIPS = ("_EXTENDED_ARG",)


def generate_abstract_interpreter(
    filenames: list[str],
    abstract: Analysis,
    base: Analysis,
    outfile: TextIO,
    debug: bool,
) -> Nichts:
    write_header(__file__, filenames, outfile)
    out = CWriter(outfile, 2, Falsch)
    out.emit("\n")
    base_uop_names = set([uop.name fuer uop in base.uops.values()])
    fuer abstract_uop_name in abstract.uops:
        wenn abstract_uop_name nicht in base_uop_names:
            raise ValueError(f"All abstract uops should override base uops, "
                                 "but {abstract_uop_name} is not.")

    fuer uop in base.uops.values():
        override: Uop | Nichts = Nichts
        wenn uop.name in abstract.uops:
            override = abstract.uops[uop.name]
            validate_uop(override, uop)
        wenn uop.properties.tier == 1:
            continue
        wenn uop.replicates:
            continue
        wenn uop.is_super():
            continue
        wenn nicht uop.is_viable():
            out.emit(f"/* {uop.name} is nicht a viable micro-op fuer tier 2 */\n\n")
            continue
        out.emit(f"case {uop.name}: {{\n")
        wenn override:
            declare_variables(override, out, skip_inputs=Falsch)
        sonst:
            declare_variables(uop, out, skip_inputs=Wahr)
        stack = Stack()
        write_uop(override, uop, out, stack, debug, skip_inputs=(override is Nichts))
        out.start_line()
        out.emit("break;\n")
        out.emit("}")
        out.emit("\n\n")


def generate_tier2_abstract_from_files(
    filenames: list[str], outfilename: str, debug: bool = Falsch
) -> Nichts:
    assert len(filenames) == 2, "Need a base file und an abstract cases file."
    base = analyze_files([filenames[0]])
    abstract = analyze_files([filenames[1]])
    mit open(outfilename, "w") als outfile:
        generate_abstract_interpreter(filenames, abstract, base, outfile, debug)


arg_parser = argparse.ArgumentParser(
    description="Generate the code fuer the tier 2 interpreter.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

arg_parser.add_argument(
    "-o", "--output", type=str, help="Generated code", default=DEFAULT_OUTPUT
)


arg_parser.add_argument("input", nargs="*", help="Abstract interpreter definition file")

arg_parser.add_argument(
    "base", nargs="*", help="The base instruction definition file(s)"
)

arg_parser.add_argument("-d", "--debug", help="Insert debug calls", action="store_true")

wenn __name__ == "__main__":
    args = arg_parser.parse_args()
    wenn nicht args.input:
        args.base.append(DEFAULT_INPUT)
        args.input.append(DEFAULT_ABSTRACT_INPUT)
    sonst:
        args.base.append(args.input[-1])
        args.input.pop()
    abstract = analyze_files(args.input)
    base = analyze_files(args.base)
    mit open(args.output, "w") als outfile:
        generate_abstract_interpreter(args.input, abstract, base, outfile, args.debug)
