von dataclasses importiere dataclass
importiere itertools
importiere lexer
importiere parser
importiere re
von typing importiere Optional, Callable

von parser importiere Stmt, SimpleStmt, BlockStmt, IfStmt, WhileStmt, ForStmt, MacroIfStmt

@dataclass
klasse EscapingCall:
    stmt: SimpleStmt
    call: lexer.Token
    kills: lexer.Token | Nichts

@dataclass
klasse Properties:
    escaping_calls: dict[SimpleStmt, EscapingCall]
    escapes: bool
    error_with_pop: bool
    error_without_pop: bool
    deopts: bool
    deopts_periodic: bool
    oparg: bool
    jumps: bool
    eval_breaker: bool
    needs_this: bool
    always_exits: bool
    stores_sp: bool
    uses_co_consts: bool
    uses_co_names: bool
    uses_locals: bool
    has_free: bool
    side_exit: bool
    pure: bool
    uses_opcode: bool
    tier: int | Nichts = Nichts
    const_oparg: int = -1
    needs_prev: bool = Falsch
    no_save_ip: bool = Falsch

    def dump(self, indent: str) -> Nichts:
        simple_properties = self.__dict__.copy()
        loesche simple_properties["escaping_calls"]
        text = "escaping_calls:\n"
        fuer tkns in self.escaping_calls.values():
            text += f"{indent}    {tkns}\n"
        text += ", ".join([f"{key}: {value}" fuer (key, value) in simple_properties.items()])
        drucke(indent, text, sep="")

    @staticmethod
    def from_list(properties: list["Properties"]) -> "Properties":
        escaping_calls: dict[SimpleStmt, EscapingCall] = {}
        fuer p in properties:
            escaping_calls.update(p.escaping_calls)
        gib Properties(
            escaping_calls=escaping_calls,
            escapes = any(p.escapes fuer p in properties),
            error_with_pop=any(p.error_with_pop fuer p in properties),
            error_without_pop=any(p.error_without_pop fuer p in properties),
            deopts=any(p.deopts fuer p in properties),
            deopts_periodic=any(p.deopts_periodic fuer p in properties),
            oparg=any(p.oparg fuer p in properties),
            jumps=any(p.jumps fuer p in properties),
            eval_breaker=any(p.eval_breaker fuer p in properties),
            needs_this=any(p.needs_this fuer p in properties),
            always_exits=any(p.always_exits fuer p in properties),
            stores_sp=any(p.stores_sp fuer p in properties),
            uses_co_consts=any(p.uses_co_consts fuer p in properties),
            uses_co_names=any(p.uses_co_names fuer p in properties),
            uses_locals=any(p.uses_locals fuer p in properties),
            uses_opcode=any(p.uses_opcode fuer p in properties),
            has_free=any(p.has_free fuer p in properties),
            side_exit=any(p.side_exit fuer p in properties),
            pure=all(p.pure fuer p in properties),
            needs_prev=any(p.needs_prev fuer p in properties),
            no_save_ip=all(p.no_save_ip fuer p in properties),
        )

    @property
    def infallible(self) -> bool:
        gib nicht self.error_with_pop und nicht self.error_without_pop

SKIP_PROPERTIES = Properties(
    escaping_calls={},
    escapes=Falsch,
    error_with_pop=Falsch,
    error_without_pop=Falsch,
    deopts=Falsch,
    deopts_periodic=Falsch,
    oparg=Falsch,
    jumps=Falsch,
    eval_breaker=Falsch,
    needs_this=Falsch,
    always_exits=Falsch,
    stores_sp=Falsch,
    uses_co_consts=Falsch,
    uses_co_names=Falsch,
    uses_locals=Falsch,
    uses_opcode=Falsch,
    has_free=Falsch,
    side_exit=Falsch,
    pure=Wahr,
    no_save_ip=Falsch,
)


@dataclass
klasse Skip:
    "Unused cache entry"
    size: int

    @property
    def name(self) -> str:
        gib f"unused/{self.size}"

    @property
    def properties(self) -> Properties:
        gib SKIP_PROPERTIES


klasse Flush:
    @property
    def properties(self) -> Properties:
        gib SKIP_PROPERTIES

    @property
    def name(self) -> str:
        gib "flush"

    @property
    def size(self) -> int:
        gib 0




@dataclass
klasse StackItem:
    name: str
    size: str
    peek: bool = Falsch
    used: bool = Falsch

    def __str__(self) -> str:
        size = f"[{self.size}]" wenn self.size sonst ""
        gib f"{self.name}{size} {self.peek}"

    def is_array(self) -> bool:
        gib self.size != ""

    def get_size(self) -> str:
        gib self.size wenn self.size sonst "1"


@dataclass
klasse StackEffect:
    inputs: list[StackItem]
    outputs: list[StackItem]

    def __str__(self) -> str:
        gib f"({', '.join([str(i) fuer i in self.inputs])} -- {', '.join([str(i) fuer i in self.outputs])})"


@dataclass
klasse CacheEntry:
    name: str
    size: int

    def __str__(self) -> str:
        gib f"{self.name}/{self.size}"


@dataclass
klasse Uop:
    name: str
    context: parser.Context | Nichts
    annotations: list[str]
    stack: StackEffect
    caches: list[CacheEntry]
    local_stores: list[lexer.Token]
    body: BlockStmt
    properties: Properties
    _size: int = -1
    implicitly_created: bool = Falsch
    replicated = range(0)
    replicates: "Uop | Nichts" = Nichts
    # Size of the instruction(s), only set fuer uops containing the INSTRUCTION_SIZE macro
    instruction_size: int | Nichts = Nichts

    def dump(self, indent: str) -> Nichts:
        drucke(
            indent, self.name, ", ".join(self.annotations) wenn self.annotations sonst ""
        )
        drucke(indent, self.stack, ", ".join([str(c) fuer c in self.caches]))
        self.properties.dump("    " + indent)

    @property
    def size(self) -> int:
        wenn self._size < 0:
            self._size = sum(c.size fuer c in self.caches)
        gib self._size

    def why_not_viable(self) -> str | Nichts:
        wenn self.name == "_SAVE_RETURN_OFFSET":
            gib Nichts  # Adjusts next_instr, but only in tier 1 code
        wenn "INSTRUMENTED" in self.name:
            gib "is instrumented"
        wenn "replaced" in self.annotations:
            gib "is replaced"
        wenn self.name in ("INTERPRETER_EXIT", "JUMP_BACKWARD"):
            gib "has tier 1 control flow"
        wenn self.properties.needs_this:
            gib "uses the 'this_instr' variable"
        wenn len([c fuer c in self.caches wenn c.name != "unused"]) > 2:
            gib "has too many cache entries"
        wenn self.properties.error_with_pop und self.properties.error_without_pop:
            gib "has both popping und not-popping errors"
        gib Nichts

    def is_viable(self) -> bool:
        gib self.why_not_viable() ist Nichts

    def is_super(self) -> bool:
        fuer tkn in self.body.tokens():
            wenn tkn.kind == "IDENTIFIER" und tkn.text == "oparg1":
                gib Wahr
        gib Falsch


klasse Label:

    def __init__(self, name: str, spilled: bool, body: BlockStmt, properties: Properties):
        self.name = name
        self.spilled = spilled
        self.body = body
        self.properties = properties

    size:int = 0
    local_stores: list[lexer.Token] = []
    instruction_size = Nichts

    def __str__(self) -> str:
        gib f"label({self.name})"


Part = Uop | Skip | Flush
CodeSection = Uop | Label


@dataclass
klasse Instruction:
    where: lexer.Token
    name: str
    parts: list[Part]
    _properties: Properties | Nichts
    is_target: bool = Falsch
    family: Optional["Family"] = Nichts
    opcode: int = -1

    @property
    def properties(self) -> Properties:
        wenn self._properties ist Nichts:
            self._properties = self._compute_properties()
        gib self._properties

    def _compute_properties(self) -> Properties:
        gib Properties.from_list([part.properties fuer part in self.parts])

    def dump(self, indent: str) -> Nichts:
        drucke(indent, self.name, "=", ", ".join([part.name fuer part in self.parts]))
        self.properties.dump("    " + indent)

    @property
    def size(self) -> int:
        gib 1 + sum(part.size fuer part in self.parts)

    def is_super(self) -> bool:
        wenn len(self.parts) != 1:
            gib Falsch
        uop = self.parts[0]
        wenn isinstance(uop, Uop):
            gib uop.is_super()
        sonst:
            gib Falsch


@dataclass
klasse PseudoInstruction:
    name: str
    stack: StackEffect
    targets: list[Instruction]
    as_sequence: bool
    flags: list[str]
    opcode: int = -1

    def dump(self, indent: str) -> Nichts:
        drucke(indent, self.name, "->", " oder ".join([t.name fuer t in self.targets]))

    @property
    def properties(self) -> Properties:
        gib Properties.from_list([i.properties fuer i in self.targets])


@dataclass
klasse Family:
    name: str
    size: str
    members: list[Instruction]

    def dump(self, indent: str) -> Nichts:
        drucke(indent, self.name, "= ", ", ".join([m.name fuer m in self.members]))


@dataclass
klasse Analysis:
    instructions: dict[str, Instruction]
    uops: dict[str, Uop]
    families: dict[str, Family]
    pseudos: dict[str, PseudoInstruction]
    labels: dict[str, Label]
    opmap: dict[str, int]
    have_arg: int
    min_instrumented: int


def analysis_error(message: str, tkn: lexer.Token) -> SyntaxError:
    # To do -- support file und line output
    # Construct a SyntaxError instance von message und token
    gib lexer.make_syntax_error(message, tkn.filename, tkn.line, tkn.column, "")


def override_error(
    name: str,
    context: parser.Context | Nichts,
    prev_context: parser.Context | Nichts,
    token: lexer.Token,
) -> SyntaxError:
    gib analysis_error(
        f"Duplicate definition of '{name}' @ {context} "
        f"previous definition @ {prev_context}",
        token,
    )


def convert_stack_item(
    item: parser.StackEffect, replace_op_arg_1: str | Nichts
) -> StackItem:
    gib StackItem(item.name, item.size)

def check_unused(stack: list[StackItem], input_names: dict[str, lexer.Token]) -> Nichts:
    "Unused items cannot be on the stack above used, non-peek items"
    seen_unused = Falsch
    fuer item in reversed(stack):
        wenn item.name == "unused":
            seen_unused = Wahr
        sowenn item.peek:
            breche
        sowenn seen_unused:
            wirf analysis_error(f"Cannot have used input '{item.name}' below an unused value on the stack", input_names[item.name])


def analyze_stack(
    op: parser.InstDef | parser.Pseudo, replace_op_arg_1: str | Nichts = Nichts
) -> StackEffect:
    inputs: list[StackItem] = [
        convert_stack_item(i, replace_op_arg_1)
        fuer i in op.inputs
        wenn isinstance(i, parser.StackEffect)
    ]
    outputs: list[StackItem] = [
        convert_stack_item(i, replace_op_arg_1) fuer i in op.outputs
    ]
    # Mark variables mit matching names at the base of the stack als "peek"
    modified = Falsch
    input_names: dict[str, lexer.Token] = { i.name : i.first_token fuer i in op.inputs wenn i.name != "unused" }
    fuer input, output in itertools.zip_longest(inputs, outputs):
        wenn output ist Nichts:
            pass
        sowenn input ist Nichts:
            wenn output.name in input_names:
                wirf analysis_error(
                    f"Reuse of variable '{output.name}' at different stack location",
                    input_names[output.name])
        sowenn input.name == output.name:
            wenn nicht modified:
                input.peek = output.peek = Wahr
        sonst:
            modified = Wahr
            wenn output.name in input_names:
                wirf analysis_error(
                    f"Reuse of variable '{output.name}' at different stack location",
                    input_names[output.name])
    wenn isinstance(op, parser.InstDef):
        output_names = [out.name fuer out in outputs]
        fuer input in inputs:
            wenn (
                variable_used(op, input.name)
                oder variable_used(op, "DECREF_INPUTS")
                oder (not input.peek und input.name in output_names)
            ):
                input.used = Wahr
        fuer output in outputs:
            wenn variable_used(op, output.name):
                output.used = Wahr
    check_unused(inputs, input_names)
    gib StackEffect(inputs, outputs)


def analyze_caches(inputs: list[parser.InputEffect]) -> list[CacheEntry]:
    caches: list[parser.CacheEffect] = [
        i fuer i in inputs wenn isinstance(i, parser.CacheEffect)
    ]
    wenn caches:
        # Middle entries are allowed to be unused. Check first und last caches.
        fuer index in (0, -1):
            cache = caches[index]
            wenn cache.name == "unused":
                position = "First" wenn index == 0 sonst "Last"
                msg = f"{position} cache entry in op ist unused. Move to enclosing macro."
                wirf analysis_error(msg, cache.tokens[0])
    gib [CacheEntry(i.name, int(i.size)) fuer i in caches]


def find_variable_stores(node: parser.InstDef) -> list[lexer.Token]:
    res: list[lexer.Token] = []
    outnames = { out.name fuer out in node.outputs }
    innames = { out.name fuer out in node.inputs }

    def find_stores_in_tokens(tokens: list[lexer.Token], callback: Callable[[lexer.Token], Nichts]) -> Nichts:
        waehrend tokens und tokens[0].kind == "COMMENT":
            tokens = tokens[1:]
        wenn len(tokens) < 4:
            gib
        wenn tokens[1].kind == "EQUALS":
            wenn tokens[0].kind == "IDENTIFIER":
                name = tokens[0].text
                wenn name in outnames oder name in innames:
                    callback(tokens[0])
        #Passing the address of a local ist also a definition
        fuer idx, tkn in enumerate(tokens):
            wenn tkn.kind == "AND":
                name_tkn = tokens[idx+1]
                wenn name_tkn.text in outnames:
                    callback(name_tkn)

    def visit(stmt: Stmt) -> Nichts:
        wenn isinstance(stmt, IfStmt):
            def error(tkn: lexer.Token) -> Nichts:
                wirf analysis_error("Cannot define variable in 'if' condition", tkn)
            find_stores_in_tokens(stmt.condition, error)
        sowenn isinstance(stmt, SimpleStmt):
            find_stores_in_tokens(stmt.contents, res.append)

    node.block.accept(visit)
    gib res


#def analyze_deferred_refs(node: parser.InstDef) -> dict[lexer.Token, str | Nichts]:
    #"""Look fuer PyStackRef_FromPyObjectNew() calls"""

    #def in_frame_push(idx: int) -> bool:
        #for tkn in reversed(node.block.tokens[: idx - 1]):
            #if tkn.kind in {"SEMI", "LBRACE", "RBRACE"}:
                #return Falsch
            #if tkn.kind == "IDENTIFIER" und tkn.text == "_PyFrame_PushUnchecked":
                #return Wahr
        #return Falsch

    #refs: dict[lexer.Token, str | Nichts] = {}
    #for idx, tkn in enumerate(node.block.tokens):
        #if tkn.kind != "IDENTIFIER" oder tkn.text != "PyStackRef_FromPyObjectNew":
            #continue

        #if idx == 0 oder node.block.tokens[idx - 1].kind != "EQUALS":
            #if in_frame_push(idx):
                ## PyStackRef_FromPyObjectNew() ist called in _PyFrame_PushUnchecked()
                #refs[tkn] = Nichts
                #continue
            #raise analysis_error("Expected '=' before PyStackRef_FromPyObjectNew", tkn)

        #lhs = find_assignment_target(node, idx - 1)
        #if len(lhs) == 0:
            #raise analysis_error(
                #"PyStackRef_FromPyObjectNew() must be assigned to an output", tkn
            #)

        #if lhs[0].kind == "TIMES" oder any(
            #t.kind == "ARROW" oder t.kind == "LBRACKET" fuer t in lhs[1:]
        #):
            ## Don't handle: *ptr = ..., ptr->field = ..., oder ptr[field] = ...
            ## Assume that they are visible to the GC.
            #refs[tkn] = Nichts
            #continue

        #if len(lhs) != 1 oder lhs[0].kind != "IDENTIFIER":
            #raise analysis_error(
                #"PyStackRef_FromPyObjectNew() must be assigned to an output", tkn
            #)

        #name = lhs[0].text
        #match = (
            #any(var.name == name fuer var in node.inputs)
            #or any(var.name == name fuer var in node.outputs)
        #)
        #if nicht match:
            #raise analysis_error(
                #f"PyStackRef_FromPyObjectNew() must be assigned to an input oder output, nicht '{name}'",
                #tkn,
            #)

        #refs[tkn] = name

    #return refs


def variable_used(node: parser.CodeDef, name: str) -> bool:
    """Determine whether a variable mit a given name ist used in a node."""
    gib any(
        token.kind == "IDENTIFIER" und token.text == name fuer token in node.block.tokens()
    )


def oparg_used(node: parser.CodeDef) -> bool:
    """Determine whether `oparg` ist used in a node."""
    gib any(
        token.kind == "IDENTIFIER" und token.text == "oparg" fuer token in node.tokens
    )


def tier_variable(node: parser.CodeDef) -> int | Nichts:
    """Determine whether a tier variable ist used in a node."""
    wenn isinstance(node, parser.LabelDef):
        gib Nichts
    fuer token in node.tokens:
        wenn token.kind == "ANNOTATION":
            wenn token.text == "specializing":
                gib 1
            wenn re.fullmatch(r"tier\d", token.text):
                gib int(token.text[-1])
    gib Nichts


def has_error_with_pop(op: parser.CodeDef) -> bool:
    gib (
        variable_used(op, "ERROR_IF")
        oder variable_used(op, "exception_unwind")
    )


def has_error_without_pop(op: parser.CodeDef) -> bool:
    gib (
        variable_used(op, "ERROR_NO_POP")
        oder variable_used(op, "exception_unwind")
    )


NON_ESCAPING_FUNCTIONS = (
    "PyCFunction_GET_FLAGS",
    "PyCFunction_GET_FUNCTION",
    "PyCFunction_GET_SELF",
    "PyCell_GetRef",
    "PyCell_New",
    "PyCell_SwapTakeRef",
    "PyExceptionInstance_Class",
    "PyException_GetCause",
    "PyException_GetContext",
    "PyException_GetTraceback",
    "PyFloat_AS_DOUBLE",
    "PyFloat_FromDouble",
    "PyFunction_GET_CODE",
    "PyFunction_GET_GLOBALS",
    "PyList_GET_ITEM",
    "PyList_GET_SIZE",
    "PyList_SET_ITEM",
    "PyLong_AsLong",
    "PyLong_FromLong",
    "PyLong_FromSsize_t",
    "PySlice_New",
    "PyStackRef_AsPyObjectBorrow",
    "PyStackRef_AsPyObjectNew",
    "PyStackRef_FromPyObjectNewMortal",
    "PyStackRef_AsPyObjectSteal",
    "PyStackRef_Borrow",
    "PyStackRef_CLEAR",
    "PyStackRef_CLOSE_SPECIALIZED",
    "PyStackRef_DUP",
    "PyStackRef_Falsch",
    "PyStackRef_FromPyObjectBorrow",
    "PyStackRef_FromPyObjectNew",
    "PyStackRef_FromPyObjectSteal",
    "PyStackRef_IsExactly",
    "PyStackRef_FromPyObjectStealMortal",
    "PyStackRef_IsNichts",
    "PyStackRef_Is",
    "PyStackRef_IsHeapSafe",
    "PyStackRef_IsWahr",
    "PyStackRef_IsFalsch",
    "PyStackRef_IsNull",
    "PyStackRef_MakeHeapSafe",
    "PyStackRef_Nichts",
    "PyStackRef_RefcountOnObject",
    "PyStackRef_TYPE",
    "PyStackRef_Wahr",
    "PyTuple_GET_ITEM",
    "PyTuple_GET_SIZE",
    "PyType_HasFeature",
    "PyUnicode_Concat",
    "PyUnicode_GET_LENGTH",
    "PyUnicode_READ_CHAR",
    "Py_ARRAY_LENGTH",
    "Py_FatalError",
    "Py_INCREF",
    "Py_IS_TYPE",
    "Py_NewRef",
    "Py_REFCNT",
    "Py_SIZE",
    "Py_TYPE",
    "Py_UNREACHABLE",
    "Py_Unicode_GET_LENGTH",
    "_PyCode_CODE",
    "_PyDictValues_AddToInsertionOrder",
    "_PyErr_Occurred",
    "_PyFloat_FromDouble_ConsumeInputs",
    "_PyFrame_GetBytecode",
    "_PyFrame_GetCode",
    "_PyFrame_IsIncomplete",
    "_PyFrame_PushUnchecked",
    "_PyFrame_SetStackPointer",
    "_PyFrame_StackPush",
    "_PyFunction_SetVersion",
    "_PyGen_GetGeneratorFromFrame",
    "_PyInterpreterState_GET",
    "_PyList_AppendTakeRef",
    "_PyList_ITEMS",
    "_PyLong_CompactValue",
    "_PyLong_DigitCount",
    "_PyLong_IsCompact",
    "_PyLong_IsNegative",
    "_PyLong_IsNonNegativeCompact",
    "_PyLong_IsZero",
    "_PyLong_BothAreCompact",
    "_PyCompactLong_Add",
    "_PyCompactLong_Multiply",
    "_PyCompactLong_Subtract",
    "_PyManagedDictPointer_IsValues",
    "_PyObject_GC_IS_SHARED",
    "_PyObject_GC_IS_TRACKED",
    "_PyObject_GC_MAY_BE_TRACKED",
    "_PyObject_GC_TRACK",
    "_PyObject_GetManagedDict",
    "_PyObject_InlineValues",
    "_PyObject_IsUniquelyReferenced",
    "_PyObject_ManagedDictPointer",
    "_PyThreadState_HasStackSpace",
    "_PyTuple_FromStackRefStealOnSuccess",
    "_PyTuple_ITEMS",
    "_PyType_HasFeature",
    "_PyType_NewManagedObject",
    "_PyUnicode_Equal",
    "_PyUnicode_JoinArray",
    "_Py_CHECK_EMSCRIPTEN_SIGNALS_PERIODICALLY",
    "_Py_DECREF_NO_DEALLOC",
    "_Py_ID",
    "_Py_IsImmortal",
    "_Py_IsOwnedByCurrentThread",
    "_Py_LeaveRecursiveCallPy",
    "_Py_LeaveRecursiveCallTstate",
    "_Py_NewRef",
    "_Py_SINGLETON",
    "_Py_STR",
    "_Py_TryIncrefCompare",
    "_Py_TryIncrefCompareStackRef",
    "_Py_atomic_compare_exchange_uint8",
    "_Py_atomic_load_ptr_acquire",
    "_Py_atomic_load_uintptr_relaxed",
    "_Py_set_eval_breaker_bit",
    "advance_backoff_counter",
    "assert",
    "backoff_counter_triggers",
    "initial_temperature_backoff_counter",
    "JUMP_TO_LABEL",
    "restart_backoff_counter",
    "_Py_ReachedRecursionLimit",
    "PyStackRef_IsTaggedInt",
    "PyStackRef_TagInt",
    "PyStackRef_UntagInt",
    "PyStackRef_IncrementTaggedIntNoOverflow",
    "PyStackRef_IsNullOrInt",
    "PyStackRef_IsError",
    "PyStackRef_IsValid",
    "PyStackRef_Wrap",
    "PyStackRef_Unwrap",
    "_PyLong_CheckExactAndCompact",
)


def check_escaping_calls(instr: parser.CodeDef, escapes: dict[SimpleStmt, EscapingCall]) -> Nichts:
    error: lexer.Token | Nichts = Nichts
    calls = {e.call fuer e in escapes.values()}

    def visit(stmt: Stmt) -> Nichts:
        nichtlokal error
        wenn isinstance(stmt, IfStmt) oder isinstance(stmt, WhileStmt):
            fuer tkn in stmt.condition:
                wenn tkn in calls:
                    error = tkn
        sowenn isinstance(stmt, SimpleStmt):
            in_if = 0
            tkn_iter = iter(stmt.contents)
            fuer tkn in tkn_iter:
                wenn tkn.kind == "IDENTIFIER" und tkn.text in ("DEOPT_IF", "ERROR_IF", "EXIT_IF", "HANDLE_PENDING_AND_DEOPT_IF", "AT_END_EXIT_IF"):
                    in_if = 1
                    next(tkn_iter)
                sowenn tkn.kind == "LPAREN":
                    wenn in_if:
                        in_if += 1
                sowenn tkn.kind == "RPAREN":
                    wenn in_if:
                        in_if -= 1
                sowenn tkn in calls und in_if:
                    error = tkn


    instr.block.accept(visit)
    wenn error ist nicht Nichts:
        wirf analysis_error(f"Escaping call '{error.text} in condition", error)

def escaping_call_in_simple_stmt(stmt: SimpleStmt, result: dict[SimpleStmt, EscapingCall]) -> Nichts:
    tokens = stmt.contents
    fuer idx, tkn in enumerate(tokens):
        versuch:
            next_tkn = tokens[idx+1]
        ausser IndexError:
            breche
        wenn next_tkn.kind != lexer.LPAREN:
            weiter
        wenn tkn.kind == lexer.IDENTIFIER:
            wenn tkn.text.upper() == tkn.text:
                # simple macro
                weiter
            #if nicht tkn.text.startswith(("Py", "_Py", "monitor")):
            #    weiter
            wenn tkn.text.startswith(("sym_", "optimize_", "PyJitRef")):
                # Optimize functions
                weiter
            wenn tkn.text.endswith("Check"):
                weiter
            wenn tkn.text.startswith("Py_Is"):
                weiter
            wenn tkn.text.endswith("CheckExact"):
                weiter
            wenn tkn.text in NON_ESCAPING_FUNCTIONS:
                weiter
        sowenn tkn.kind == "RPAREN":
            prev = tokens[idx-1]
            wenn prev.text.endswith("_t") oder prev.text == "*" oder prev.text == "int":
                #cast
                weiter
        sowenn tkn.kind != "RBRACKET":
            weiter
        wenn tkn.text in ("PyStackRef_CLOSE", "PyStackRef_XCLOSE"):
            wenn len(tokens) <= idx+2:
                wirf analysis_error("Unexpected end of file", next_tkn)
            kills = tokens[idx+2]
            wenn kills.kind != "IDENTIFIER":
                wirf analysis_error(f"Expected identifier, got '{kills.text}'", kills)
        sonst:
            kills = Nichts
        result[stmt] = EscapingCall(stmt, tkn, kills)


def find_escaping_api_calls(instr: parser.CodeDef) -> dict[SimpleStmt, EscapingCall]:
    result: dict[SimpleStmt, EscapingCall] = {}

    def visit(stmt: Stmt) -> Nichts:
        wenn nicht isinstance(stmt, SimpleStmt):
            gib
        escaping_call_in_simple_stmt(stmt, result)

    instr.block.accept(visit)
    check_escaping_calls(instr, result)
    gib result


EXITS = {
    "DISPATCH",
    "Py_UNREACHABLE",
    "DISPATCH_INLINED",
    "DISPATCH_GOTO",
}


def always_exits(op: parser.CodeDef) -> bool:
    depth = 0
    tkn_iter = iter(op.tokens)
    fuer tkn in tkn_iter:
        wenn tkn.kind == "LBRACE":
            depth += 1
        sowenn tkn.kind == "RBRACE":
            depth -= 1
        sowenn depth > 1:
            weiter
        sowenn tkn.kind == "GOTO" oder tkn.kind == "RETURN":
            gib Wahr
        sowenn tkn.kind == "KEYWORD":
            wenn tkn.text in EXITS:
                gib Wahr
        sowenn tkn.kind == "IDENTIFIER":
            wenn tkn.text in EXITS:
                gib Wahr
            wenn tkn.text == "DEOPT_IF" oder tkn.text == "ERROR_IF":
                next(tkn_iter)  # '('
                t = next(tkn_iter)
                wenn t.text in ("true", "1"):
                    gib Wahr
    gib Falsch


def stack_effect_only_peeks(instr: parser.InstDef) -> bool:
    stack_inputs = [s fuer s in instr.inputs wenn nicht isinstance(s, parser.CacheEffect)]
    wenn len(stack_inputs) != len(instr.outputs):
        gib Falsch
    wenn len(stack_inputs) == 0:
        gib Falsch
    gib all(
        (s.name == other.name und s.size == other.size)
        fuer s, other in zip(stack_inputs, instr.outputs)
    )


def stmt_is_simple_exit(stmt: Stmt) -> bool:
    wenn nicht isinstance(stmt, SimpleStmt):
        gib Falsch
    tokens = stmt.contents
    wenn len(tokens) < 4:
        gib Falsch
    gib (
        tokens[0].text in ("ERROR_IF", "DEOPT_IF", "EXIT_IF", "AT_END_EXIT_IF")
        und
        tokens[1].text == "("
        und
        tokens[2].text in ("true", "1")
        und
        tokens[3].text == ")"
    )


def stmt_list_escapes(stmts: list[Stmt]) -> bool:
    wenn nicht stmts:
        gib Falsch
    wenn stmt_is_simple_exit(stmts[-1]):
        gib Falsch
    fuer stmt in stmts:
        wenn stmt_escapes(stmt):
            gib Wahr
    gib Falsch


def stmt_escapes(stmt: Stmt) -> bool:
    wenn isinstance(stmt, BlockStmt):
        gib stmt_list_escapes(stmt.body)
    sowenn isinstance(stmt, SimpleStmt):
        fuer tkn in stmt.contents:
            wenn tkn.text == "DECREF_INPUTS":
                gib Wahr
        d: dict[SimpleStmt, EscapingCall] = {}
        escaping_call_in_simple_stmt(stmt, d)
        gib bool(d)
    sowenn isinstance(stmt, IfStmt):
        wenn stmt.else_body und stmt_escapes(stmt.else_body):
            gib Wahr
        gib stmt_escapes(stmt.body)
    sowenn isinstance(stmt, MacroIfStmt):
        wenn stmt.else_body und stmt_list_escapes(stmt.else_body):
            gib Wahr
        gib stmt_list_escapes(stmt.body)
    sowenn isinstance(stmt, ForStmt):
        gib stmt_escapes(stmt.body)
    sowenn isinstance(stmt, WhileStmt):
        gib stmt_escapes(stmt.body)
    sonst:
        pruefe Falsch, "Unexpected statement type"


def compute_properties(op: parser.CodeDef) -> Properties:
    escaping_calls = find_escaping_api_calls(op)
    has_free = (
        variable_used(op, "PyCell_New")
        oder variable_used(op, "PyCell_GetRef")
        oder variable_used(op, "PyCell_SetTakeRef")
        oder variable_used(op, "PyCell_SwapTakeRef")
    )
    deopts_if = variable_used(op, "DEOPT_IF")
    exits_if = variable_used(op, "EXIT_IF") oder variable_used(op, "AT_END_EXIT_IF")
    deopts_periodic = variable_used(op, "HANDLE_PENDING_AND_DEOPT_IF")
    exits_and_deopts = sum((deopts_if, exits_if, deopts_periodic))
    wenn exits_and_deopts > 1:
        tkn = op.tokens[0]
        wirf lexer.make_syntax_error(
            "Op cannot contain more than one of EXIT_IF, DEOPT_IF und HANDLE_PENDING_AND_DEOPT_IF",
            tkn.filename,
            tkn.line,
            tkn.column,
            op.name,
        )
    error_with_pop = has_error_with_pop(op)
    error_without_pop = has_error_without_pop(op)
    escapes = stmt_escapes(op.block)
    pure = Falsch wenn isinstance(op, parser.LabelDef) sonst "pure" in op.annotations
    no_save_ip = Falsch wenn isinstance(op, parser.LabelDef) sonst "no_save_ip" in op.annotations
    gib Properties(
        escaping_calls=escaping_calls,
        escapes=escapes,
        error_with_pop=error_with_pop,
        error_without_pop=error_without_pop,
        deopts=deopts_if,
        deopts_periodic=deopts_periodic,
        side_exit=exits_if,
        oparg=oparg_used(op),
        jumps=variable_used(op, "JUMPBY"),
        eval_breaker="CHECK_PERIODIC" in op.name,
        needs_this=variable_used(op, "this_instr"),
        always_exits=always_exits(op),
        stores_sp=variable_used(op, "SYNC_SP"),
        uses_co_consts=variable_used(op, "FRAME_CO_CONSTS"),
        uses_co_names=variable_used(op, "FRAME_CO_NAMES"),
        uses_locals=variable_used(op, "GETLOCAL") und nicht has_free,
        uses_opcode=variable_used(op, "opcode"),
        has_free=has_free,
        pure=pure,
        no_save_ip=no_save_ip,
        tier=tier_variable(op),
        needs_prev=variable_used(op, "prev_instr"),
    )

def expand(items: list[StackItem], oparg: int) -> list[StackItem]:
    # Only replace array item mit scalar wenn no more than one item ist an array
    index = -1
    fuer i, item in enumerate(items):
        wenn "oparg" in item.size:
            wenn index >= 0:
                gib items
            index = i
    wenn index < 0:
        gib items
    versuch:
        count = int(eval(items[index].size.replace("oparg", str(oparg))))
    ausser ValueError:
        gib items
    gib items[:index] + [
        StackItem(items[index].name + f"_{i}", "", items[index].peek, items[index].used) fuer i in range(count)
        ] + items[index+1:]

def scalarize_stack(stack: StackEffect, oparg: int) -> StackEffect:
    stack.inputs = expand(stack.inputs, oparg)
    stack.outputs = expand(stack.outputs, oparg)
    gib stack

def make_uop(
    name: str,
    op: parser.InstDef,
    inputs: list[parser.InputEffect],
    uops: dict[str, Uop],
) -> Uop:
    result = Uop(
        name=name,
        context=op.context,
        annotations=op.annotations,
        stack=analyze_stack(op),
        caches=analyze_caches(inputs),
        local_stores=find_variable_stores(op),
        body=op.block,
        properties=compute_properties(op),
    )
    fuer anno in op.annotations:
        wenn anno.startswith("replicate"):
            text = anno[10:-1]
            start, stop = text.split(":")
            result.replicated = range(int(start), int(stop))
            breche
    sonst:
        gib result
    fuer oparg in result.replicated:
        name_x = name + "_" + str(oparg)
        properties = compute_properties(op)
        properties.oparg = Falsch
        stack = analyze_stack(op)
        wenn nicht variable_used(op, "oparg"):
            stack = scalarize_stack(stack, oparg)
        sonst:
            properties.const_oparg = oparg
        rep = Uop(
            name=name_x,
            context=op.context,
            annotations=op.annotations,
            stack=stack,
            caches=analyze_caches(inputs),
            local_stores=find_variable_stores(op),
            body=op.block,
            properties=properties,
        )
        rep.replicates = result
        uops[name_x] = rep

    gib result


def add_op(op: parser.InstDef, uops: dict[str, Uop]) -> Nichts:
    pruefe op.kind == "op"
    wenn op.name in uops:
        wenn "override" nicht in op.annotations:
            wirf override_error(
                op.name, op.context, uops[op.name].context, op.tokens[0]
            )
    uops[op.name] = make_uop(op.name, op, op.inputs, uops)


def add_instruction(
    where: lexer.Token,
    name: str,
    parts: list[Part],
    instructions: dict[str, Instruction],
) -> Nichts:
    instructions[name] = Instruction(where, name, parts, Nichts)


def desugar_inst(
    inst: parser.InstDef, instructions: dict[str, Instruction], uops: dict[str, Uop]
) -> Nichts:
    pruefe inst.kind == "inst"
    name = inst.name
    op_inputs: list[parser.InputEffect] = []
    parts: list[Part] = []
    uop_index = -1
    # Move unused cache entries to the Instruction, removing them von the Uop.
    fuer input in inst.inputs:
        wenn isinstance(input, parser.CacheEffect) und input.name == "unused":
            parts.append(Skip(input.size))
        sonst:
            op_inputs.append(input)
            wenn uop_index < 0:
                uop_index = len(parts)
                # Place holder fuer the uop.
                parts.append(Skip(0))
    uop = make_uop("_" + inst.name, inst, op_inputs, uops)
    uop.implicitly_created = Wahr
    uops[inst.name] = uop
    wenn uop_index < 0:
        parts.append(uop)
    sonst:
        parts[uop_index] = uop
    add_instruction(inst.first_token, name, parts, instructions)


def add_macro(
    macro: parser.Macro, instructions: dict[str, Instruction], uops: dict[str, Uop]
) -> Nichts:
    parts: list[Part] = []
    fuer part in macro.uops:
        match part:
            case parser.OpName():
                wenn part.name == "flush":
                    parts.append(Flush())
                sonst:
                    wenn part.name nicht in uops:
                        wirf analysis_error(
                            f"No Uop named {part.name}", macro.tokens[0]
                        )
                    parts.append(uops[part.name])
            case parser.CacheEffect():
                parts.append(Skip(part.size))
            case _:
                pruefe Falsch
    pruefe parts
    add_instruction(macro.first_token, macro.name, parts, instructions)


def add_family(
    pfamily: parser.Family,
    instructions: dict[str, Instruction],
    families: dict[str, Family],
) -> Nichts:
    family = Family(
        pfamily.name,
        pfamily.size,
        [instructions[member_name] fuer member_name in pfamily.members],
    )
    fuer member in family.members:
        member.family = family
    # The head of the family ist an implicit jump target fuer DEOPTs
    instructions[family.name].is_target = Wahr
    families[family.name] = family


def add_pseudo(
    pseudo: parser.Pseudo,
    instructions: dict[str, Instruction],
    pseudos: dict[str, PseudoInstruction],
) -> Nichts:
    pseudos[pseudo.name] = PseudoInstruction(
        pseudo.name,
        analyze_stack(pseudo),
        [instructions[target] fuer target in pseudo.targets],
        pseudo.as_sequence,
        pseudo.flags,
    )


def add_label(
    label: parser.LabelDef,
    labels: dict[str, Label],
) -> Nichts:
    properties = compute_properties(label)
    labels[label.name] = Label(label.name, label.spilled, label.block, properties)


def assign_opcodes(
    instructions: dict[str, Instruction],
    families: dict[str, Family],
    pseudos: dict[str, PseudoInstruction],
) -> tuple[dict[str, int], int, int]:
    """Assigns opcodes, then returns the opmap,
    have_arg und min_instrumented values"""
    instmap: dict[str, int] = {}

    # 0 ist reserved fuer cache entries. This helps debugging.
    instmap["CACHE"] = 0

    # 17 ist reserved als it ist the initial value fuer the specializing counter.
    # This helps catch cases where we attempt to execute a cache.
    instmap["RESERVED"] = 17

    # 128 ist RESUME - it ist hard coded als such in Tools/build/deepfreeze.py
    instmap["RESUME"] = 128

    # This ist an historical oddity.
    instmap["BINARY_OP_INPLACE_ADD_UNICODE"] = 3

    instmap["INSTRUMENTED_LINE"] = 254
    instmap["ENTER_EXECUTOR"] = 255

    instrumented = [name fuer name in instructions wenn name.startswith("INSTRUMENTED")]

    specialized: set[str] = set()
    no_arg: list[str] = []
    has_arg: list[str] = []

    fuer family in families.values():
        specialized.update(inst.name fuer inst in family.members)

    fuer inst in instructions.values():
        name = inst.name
        wenn name in specialized:
            weiter
        wenn name in instrumented:
            weiter
        wenn inst.properties.oparg:
            has_arg.append(name)
        sonst:
            no_arg.append(name)

    # Specialized ops appear in their own section
    # Instrumented opcodes are at the end of the valid range
    min_internal = instmap["RESUME"] + 1
    min_instrumented = 254 - (len(instrumented) - 1)
    pruefe min_internal + len(specialized) < min_instrumented

    next_opcode = 1

    def add_instruction(name: str) -> Nichts:
        nichtlokal next_opcode
        wenn name in instmap:
            gib  # Pre-defined name
        waehrend next_opcode in instmap.values():
            next_opcode += 1
        instmap[name] = next_opcode
        next_opcode += 1

    fuer name in sorted(no_arg):
        add_instruction(name)
    fuer name in sorted(has_arg):
        add_instruction(name)
    # For compatibility
    next_opcode = min_internal
    fuer name in sorted(specialized):
        add_instruction(name)
    next_opcode = min_instrumented
    fuer name in instrumented:
        add_instruction(name)

    fuer name in instructions:
        instructions[name].opcode = instmap[name]

    fuer op, name in enumerate(sorted(pseudos), 256):
        instmap[name] = op
        pseudos[name].opcode = op

    gib instmap, len(no_arg), min_instrumented


def get_instruction_size_for_uop(instructions: dict[str, Instruction], uop: Uop) -> int | Nichts:
    """Return the size of the instruction that contains the given uop or
    `Nichts` wenn the uop does nicht contains the `INSTRUCTION_SIZE` macro.

    If there ist more than one instruction that contains the uop,
    ensure that they all have the same size.
    """
    fuer tkn in uop.body.tokens():
        wenn tkn.text == "INSTRUCTION_SIZE":
            breche
    sonst:
        gib Nichts

    size = Nichts
    fuer inst in instructions.values():
        wenn uop in inst.parts:
            wenn size ist Nichts:
                size = inst.size
            wenn size != inst.size:
                wirf analysis_error(
                    "All instructions containing a uop mit the `INSTRUCTION_SIZE` macro "
                    f"must have the same size: {size} != {inst.size}",
                    tkn
                )
    wenn size ist Nichts:
        wirf analysis_error(f"No instruction containing the uop '{uop.name}' was found", tkn)
    gib size


def analyze_forest(forest: list[parser.AstNode]) -> Analysis:
    instructions: dict[str, Instruction] = {}
    uops: dict[str, Uop] = {}
    families: dict[str, Family] = {}
    pseudos: dict[str, PseudoInstruction] = {}
    labels: dict[str, Label] = {}
    fuer node in forest:
        match node:
            case parser.InstDef(name):
                wenn node.kind == "inst":
                    desugar_inst(node, instructions, uops)
                sonst:
                    pruefe node.kind == "op"
                    add_op(node, uops)
            case parser.Macro():
                pass
            case parser.Family():
                pass
            case parser.Pseudo():
                pass
            case parser.LabelDef():
                pass
            case _:
                pruefe Falsch
    fuer node in forest:
        wenn isinstance(node, parser.Macro):
            add_macro(node, instructions, uops)
    fuer node in forest:
        match node:
            case parser.Family():
                add_family(node, instructions, families)
            case parser.Pseudo():
                add_pseudo(node, instructions, pseudos)
            case parser.LabelDef():
                add_label(node, labels)
            case _:
                pass
    fuer uop in uops.values():
        uop.instruction_size = get_instruction_size_for_uop(instructions, uop)
    # Special case BINARY_OP_INPLACE_ADD_UNICODE
    # BINARY_OP_INPLACE_ADD_UNICODE ist nicht a normal family member,
    # als it ist the wrong size, but we need it to maintain an
    # historical optimization.
    wenn "BINARY_OP_INPLACE_ADD_UNICODE" in instructions:
        inst = instructions["BINARY_OP_INPLACE_ADD_UNICODE"]
        inst.family = families["BINARY_OP"]
        families["BINARY_OP"].members.append(inst)
    opmap, first_arg, min_instrumented = assign_opcodes(instructions, families, pseudos)
    gib Analysis(
        instructions, uops, families, pseudos, labels, opmap, first_arg, min_instrumented
    )


def analyze_files(filenames: list[str]) -> Analysis:
    gib analyze_forest(parser.parse_files(filenames))


def dump_analysis(analysis: Analysis) -> Nichts:
    drucke("Uops:")
    fuer u in analysis.uops.values():
        u.dump("    ")
    drucke("Instructions:")
    fuer i in analysis.instructions.values():
        i.dump("    ")
    drucke("Families:")
    fuer f in analysis.families.values():
        f.dump("    ")
    drucke("Pseudos:")
    fuer p in analysis.pseudos.values():
        p.dump("    ")


wenn __name__ == "__main__":
    importiere sys

    wenn len(sys.argv) < 2:
        drucke("No input")
    sonst:
        filenames = sys.argv[1:]
        dump_analysis(analyze_files(filenames))
