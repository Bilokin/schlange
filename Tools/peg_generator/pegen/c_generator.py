importiere ast
importiere os.path
importiere re
von dataclasses importiere dataclass, field
von enum importiere Enum
von typing importiere IO, Any, Callable, Dict, List, Optional, Set, Text, Tuple

von pegen importiere grammar
von pegen.grammar importiere (
    Alt,
    Cut,
    Forced,
    Gather,
    GrammarVisitor,
    Group,
    Leaf,
    Lookahead,
    NamedItem,
    NameLeaf,
    NegativeLookahead,
    Opt,
    PositiveLookahead,
    Repeat0,
    Repeat1,
    Rhs,
    Rule,
    StringLeaf,
)
von pegen.parser_generator importiere ParserGenerator

EXTENSION_PREFIX = """\
#include "pegen.h"

#if defined(Py_DEBUG) && defined(Py_BUILD_CORE)
#  define D(x) wenn (p->debug) { x; }
#else
#  define D(x)
#endif

#ifdef __wasi__
#  ifdef Py_DEBUG
#    define MAXSTACK 1000
#  else
#    define MAXSTACK 4000
#  endif
#else
#  define MAXSTACK 6000
#endif

"""


EXTENSION_SUFFIX = """
void *
_PyPegen_parse(Parser *p)
{
    // Initialize keywords
    p->keywords = reserved_keywords;
    p->n_keyword_lists = n_keyword_lists;
    p->soft_keywords = soft_keywords;

    gib start_rule(p);
}
"""


klasse NodeTypes(Enum):
    NAME_TOKEN = 0
    NUMBER_TOKEN = 1
    STRING_TOKEN = 2
    GENERIC_TOKEN = 3
    KEYWORD = 4
    SOFT_KEYWORD = 5
    CUT_OPERATOR = 6
    F_STRING_CHUNK = 7


BASE_NODETYPES = {
    "NAME": NodeTypes.NAME_TOKEN,
    "NUMBER": NodeTypes.NUMBER_TOKEN,
    "STRING": NodeTypes.STRING_TOKEN,
    "SOFT_KEYWORD": NodeTypes.SOFT_KEYWORD,
}


@dataclass
klasse FunctionCall:
    function: str
    arguments: List[Any] = field(default_factory=list)
    assigned_variable: Optional[str] = Nichts
    assigned_variable_type: Optional[str] = Nichts
    return_type: Optional[str] = Nichts
    nodetype: Optional[NodeTypes] = Nichts
    force_true: bool = Falsch
    comment: Optional[str] = Nichts

    def __str__(self) -> str:
        parts = []
        parts.append(self.function)
        wenn self.arguments:
            parts.append(f"({', '.join(map(str, self.arguments))})")
        wenn self.force_true:
            parts.append(", !p->error_indicator")
        wenn self.assigned_variable:
            wenn self.assigned_variable_type:
                parts = [
                    "(",
                    self.assigned_variable,
                    " = ",
                    "(",
                    self.assigned_variable_type,
                    ")",
                    *parts,
                    ")",
                ]
            sonst:
                parts = ["(", self.assigned_variable, " = ", *parts, ")"]
        wenn self.comment:
            parts.append(f"  // {self.comment}")
        gib "".join(parts)


klasse CCallMakerVisitor(GrammarVisitor):
    def __init__(
        self,
        parser_generator: ParserGenerator,
        exact_tokens: Dict[str, int],
        non_exact_tokens: Set[str],
    ):
        self.gen = parser_generator
        self.exact_tokens = exact_tokens
        self.non_exact_tokens = non_exact_tokens
        self.cache: Dict[str, str] = {}
        self.cleanup_statements: List[str] = []

    def keyword_helper(self, keyword: str) -> FunctionCall:
        gib FunctionCall(
            assigned_variable="_keyword",
            function="_PyPegen_expect_token",
            arguments=["p", self.gen.keywords[keyword]],
            return_type="Token *",
            nodetype=NodeTypes.KEYWORD,
            comment=f"token='{keyword}'",
        )

    def soft_keyword_helper(self, value: str) -> FunctionCall:
        gib FunctionCall(
            assigned_variable="_keyword",
            function="_PyPegen_expect_soft_keyword",
            arguments=["p", value],
            return_type="expr_ty",
            nodetype=NodeTypes.SOFT_KEYWORD,
            comment=f"soft_keyword='{value}'",
        )

    def visit_NameLeaf(self, node: NameLeaf) -> FunctionCall:
        name = node.value
        wenn name in self.non_exact_tokens:
            wenn name in BASE_NODETYPES:
                gib FunctionCall(
                    assigned_variable=f"{name.lower()}_var",
                    function=f"_PyPegen_{name.lower()}_token",
                    arguments=["p"],
                    nodetype=BASE_NODETYPES[name],
                    return_type="expr_ty",
                    comment=name,
                )
            gib FunctionCall(
                assigned_variable=f"{name.lower()}_var",
                function=f"_PyPegen_expect_token",
                arguments=["p", name],
                nodetype=NodeTypes.GENERIC_TOKEN,
                return_type="Token *",
                comment=f"token='{name}'",
            )

        type = Nichts
        rule = self.gen.all_rules.get(name.lower())
        wenn rule is nicht Nichts:
            type = "asdl_seq *" wenn rule.is_loop() oder rule.is_gather() sonst rule.type

        gib FunctionCall(
            assigned_variable=f"{name}_var",
            function=f"{name}_rule",
            arguments=["p"],
            return_type=type,
            comment=f"{node}",
        )

    def visit_StringLeaf(self, node: StringLeaf) -> FunctionCall:
        val = ast.literal_eval(node.value)
        wenn re.match(r"[a-zA-Z_]\w*\Z", val):  # This is a keyword
            wenn node.value.endswith("'"):
                gib self.keyword_helper(val)
            sonst:
                gib self.soft_keyword_helper(node.value)
        sonst:
            assert val in self.exact_tokens, f"{node.value} is nicht a known literal"
            type = self.exact_tokens[val]
            gib FunctionCall(
                assigned_variable="_literal",
                function=f"_PyPegen_expect_token",
                arguments=["p", type],
                nodetype=NodeTypes.GENERIC_TOKEN,
                return_type="Token *",
                comment=f"token='{val}'",
            )

    def visit_NamedItem(self, node: NamedItem) -> FunctionCall:
        call = self.generate_call(node.item)
        wenn node.name:
            call.assigned_variable = node.name
        wenn node.type:
            call.assigned_variable_type = node.type
        gib call

    def assert_no_undefined_behavior(
        self, call: FunctionCall, wrapper: str, expected_rtype: str | Nichts,
    ) -> Nichts:
        wenn call.return_type != expected_rtype:
            wirf RuntimeError(
                f"{call.function} gib type is incompatible mit {wrapper}: "
                f"expect: {expected_rtype}, actual: {call.return_type}"
            )

    def lookahead_call_helper(self, node: Lookahead, positive: int) -> FunctionCall:
        call = self.generate_call(node.node)
        comment = Nichts
        wenn call.nodetype is NodeTypes.NAME_TOKEN:
            function = "_PyPegen_lookahead_for_expr"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        sowenn call.nodetype is NodeTypes.STRING_TOKEN:
            # _PyPegen_string_token() returns 'void *' instead of 'Token *';
            # in addition, the overall function call would gib 'expr_ty'.
            assert call.function == "_PyPegen_string_token"
            function = "_PyPegen_lookahead"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        sowenn call.nodetype == NodeTypes.SOFT_KEYWORD:
            function = "_PyPegen_lookahead_with_string"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        sowenn call.nodetype in {NodeTypes.GENERIC_TOKEN, NodeTypes.KEYWORD}:
            function = "_PyPegen_lookahead_with_int"
            self.assert_no_undefined_behavior(call, function, "Token *")
            comment = f"token={node.node}"
        sowenn call.return_type == "expr_ty":
            function = "_PyPegen_lookahead_for_expr"
        sowenn call.return_type == "stmt_ty":
            function = "_PyPegen_lookahead_for_stmt"
        sonst:
            function = "_PyPegen_lookahead"
            self.assert_no_undefined_behavior(call, function, Nichts)
        gib FunctionCall(
            function=function,
            arguments=[positive, call.function, *call.arguments],
            return_type="int",
            comment=comment,
        )

    def visit_PositiveLookahead(self, node: PositiveLookahead) -> FunctionCall:
        gib self.lookahead_call_helper(node, 1)

    def visit_NegativeLookahead(self, node: NegativeLookahead) -> FunctionCall:
        gib self.lookahead_call_helper(node, 0)

    def visit_Forced(self, node: Forced) -> FunctionCall:
        call = self.generate_call(node.node)
        wenn isinstance(node.node, Leaf):
            assert isinstance(node.node, Leaf)
            val = ast.literal_eval(node.node.value)
            assert val in self.exact_tokens, f"{node.node.value} is nicht a known literal"
            type = self.exact_tokens[val]
            gib FunctionCall(
                assigned_variable="_literal",
                function=f"_PyPegen_expect_forced_token",
                arguments=["p", type, f'"{val}"'],
                nodetype=NodeTypes.GENERIC_TOKEN,
                return_type="Token *",
                comment=f"forced_token='{val}'",
            )
        wenn isinstance(node.node, Group):
            call = self.visit(node.node.rhs)
            call.assigned_variable = Nichts
            call.comment = Nichts
            gib FunctionCall(
                assigned_variable="_literal",
                function=f"_PyPegen_expect_forced_result",
                arguments=["p", str(call), f'"{node.node.rhs!s}"'],
                return_type="void *",
                comment=f"forced_token=({node.node.rhs!s})",
            )
        sonst:
            wirf NotImplementedError(f"Forced tokens don't work mit {node.node} nodes")

    def visit_Opt(self, node: Opt) -> FunctionCall:
        call = self.generate_call(node.node)
        gib FunctionCall(
            assigned_variable="_opt_var",
            function=call.function,
            arguments=call.arguments,
            force_true=Wahr,
            comment=f"{node}",
        )

    def _generate_artificial_rule_call(
        self,
        node: Any,
        prefix: str,
        rule_generation_func: Callable[[], str],
        return_type: Optional[str] = Nichts,
    ) -> FunctionCall:
        node_str = f"{node}"
        key = f"{prefix}_{node_str}"
        wenn key in self.cache:
            name = self.cache[key]
        sonst:
            name = rule_generation_func()
            self.cache[key] = name

        gib FunctionCall(
            assigned_variable=f"{name}_var",
            function=f"{name}_rule",
            arguments=["p"],
            return_type=return_type,
            comment=node_str,
        )

    def visit_Rhs(self, node: Rhs) -> FunctionCall:
        wenn node.can_be_inlined:
            gib self.generate_call(node.alts[0].items[0])

        gib self._generate_artificial_rule_call(
            node,
            "rhs",
            lambda: self.gen.artificial_rule_from_rhs(node),
        )

    def visit_Repeat0(self, node: Repeat0) -> FunctionCall:
        gib self._generate_artificial_rule_call(
            node,
            "repeat0",
            lambda: self.gen.artificial_rule_from_repeat(node.node, is_repeat1=Falsch),
            "asdl_seq *",
        )

    def visit_Repeat1(self, node: Repeat1) -> FunctionCall:
        gib self._generate_artificial_rule_call(
            node,
            "repeat1",
            lambda: self.gen.artificial_rule_from_repeat(node.node, is_repeat1=Wahr),
            "asdl_seq *",
        )

    def visit_Gather(self, node: Gather) -> FunctionCall:
        gib self._generate_artificial_rule_call(
            node,
            "gather",
            lambda: self.gen.artificial_rule_from_gather(node),
            "asdl_seq *",
        )

    def visit_Group(self, node: Group) -> FunctionCall:
        gib self.generate_call(node.rhs)

    def visit_Cut(self, node: Cut) -> FunctionCall:
        gib FunctionCall(
            assigned_variable="_cut_var",
            return_type="int",
            function="1",
            nodetype=NodeTypes.CUT_OPERATOR,
        )

    def generate_call(self, node: Any) -> FunctionCall:
        gib super().visit(node)


klasse CParserGenerator(ParserGenerator, GrammarVisitor):
    def __init__(
        self,
        grammar: grammar.Grammar,
        tokens: Dict[int, str],
        exact_tokens: Dict[str, int],
        non_exact_tokens: Set[str],
        file: Optional[IO[Text]],
        debug: bool = Falsch,
        skip_actions: bool = Falsch,
    ):
        super().__init__(grammar, set(tokens.values()), file)
        self.callmakervisitor: CCallMakerVisitor = CCallMakerVisitor(
            self, exact_tokens, non_exact_tokens
        )
        self._varname_counter = 0
        self.debug = debug
        self.skip_actions = skip_actions
        self.cleanup_statements: List[str] = []

    def add_level(self) -> Nichts:
        self.drucke("if (p->level++ == MAXSTACK || _Py_ReachedRecursionLimitWithMargin(PyThreadState_Get(), 1)) {")
        mit self.indent():
            self.drucke("_Pypegen_stack_overflow(p);")
        self.drucke("}")

    def remove_level(self) -> Nichts:
        self.drucke("p->level--;")

    def add_return(self, ret_val: str) -> Nichts:
        fuer stmt in self.cleanup_statements:
            self.drucke(stmt)
        self.remove_level()
        self.drucke(f"return {ret_val};")

    def unique_varname(self, name: str = "tmpvar") -> str:
        new_var = name + "_" + str(self._varname_counter)
        self._varname_counter += 1
        gib new_var

    def call_with_errorcheck_return(self, call_text: str, returnval: str) -> Nichts:
        error_var = self.unique_varname()
        self.drucke(f"int {error_var} = {call_text};")
        self.drucke(f"if ({error_var}) {{")
        mit self.indent():
            self.add_return(returnval)
        self.drucke("}")

    def call_with_errorcheck_goto(self, call_text: str, goto_target: str) -> Nichts:
        error_var = self.unique_varname()
        self.drucke(f"int {error_var} = {call_text};")
        self.drucke(f"if ({error_var}) {{")
        mit self.indent():
            self.drucke(f"goto {goto_target};")
        self.drucke(f"}}")

    def out_of_memory_return(
        self,
        expr: str,
        cleanup_code: Optional[str] = Nichts,
    ) -> Nichts:
        self.drucke(f"if ({expr}) {{")
        mit self.indent():
            wenn cleanup_code is nicht Nichts:
                self.drucke(cleanup_code)
            self.drucke("p->error_indicator = 1;")
            self.drucke("PyErr_NoMemory();")
            self.add_return("NULL")
        self.drucke(f"}}")

    def out_of_memory_goto(self, expr: str, goto_target: str) -> Nichts:
        self.drucke(f"if ({expr}) {{")
        mit self.indent():
            self.drucke("PyErr_NoMemory();")
            self.drucke(f"goto {goto_target};")
        self.drucke(f"}}")

    def generate(self, filename: str) -> Nichts:
        self.collect_rules()
        basename = os.path.basename(filename)
        self.drucke(f"// @generated by pegen von {basename}")
        header = self.grammar.metas.get("header", EXTENSION_PREFIX)
        wenn header:
            self.drucke(header.rstrip("\n"))
        subheader = self.grammar.metas.get("subheader", "")
        wenn subheader:
            self.drucke(subheader)
        self._setup_keywords()
        self._setup_soft_keywords()
        fuer i, (rulename, rule) in enumerate(self.all_rules.items(), 1000):
            comment = "  // Left-recursive" wenn rule.left_recursive sonst ""
            self.drucke(f"#define {rulename}_type {i}{comment}")
        self.drucke()
        fuer rulename, rule in self.all_rules.items():
            wenn rule.is_loop() oder rule.is_gather():
                type = "asdl_seq *"
            sowenn rule.type:
                type = rule.type + " "
            sonst:
                type = "void *"
            self.drucke(f"static {type}{rulename}_rule(Parser *p);")
        self.drucke()
        fuer rulename, rule in list(self.all_rules.items()):
            self.drucke()
            wenn rule.left_recursive:
                self.drucke("// Left-recursive")
            self.visit(rule)
        wenn self.skip_actions:
            mode = 0
        sonst:
            mode = int(self.rules["start"].type == "mod_ty") wenn "start" in self.rules sonst 1
            wenn mode == 1 und self.grammar.metas.get("bytecode"):
                mode += 1
        modulename = self.grammar.metas.get("modulename", "parse")
        trailer = self.grammar.metas.get("trailer", EXTENSION_SUFFIX)
        wenn trailer:
            self.drucke(trailer.rstrip("\n") % dict(mode=mode, modulename=modulename))

    def _group_keywords_by_length(self) -> Dict[int, List[Tuple[str, int]]]:
        groups: Dict[int, List[Tuple[str, int]]] = {}
        fuer keyword_str, keyword_type in self.keywords.items():
            length = len(keyword_str)
            wenn length in groups:
                groups[length].append((keyword_str, keyword_type))
            sonst:
                groups[length] = [(keyword_str, keyword_type)]
        gib groups

    def _setup_keywords(self) -> Nichts:
        n_keyword_lists = (
            len(max(self.keywords.keys(), key=len)) + 1 wenn len(self.keywords) > 0 sonst 0
        )
        self.drucke(f"static const int n_keyword_lists = {n_keyword_lists};")
        groups = self._group_keywords_by_length()
        self.drucke("static KeywordToken *reserved_keywords[] = {")
        mit self.indent():
            num_groups = max(groups) + 1 wenn groups sonst 1
            fuer keywords_length in range(num_groups):
                wenn keywords_length nicht in groups.keys():
                    self.drucke("(KeywordToken[]) {{NULL, -1}},")
                sonst:
                    self.drucke("(KeywordToken[]) {")
                    mit self.indent():
                        fuer keyword_str, keyword_type in groups[keywords_length]:
                            self.drucke(f'{{"{keyword_str}", {keyword_type}}},')
                        self.drucke("{NULL, -1},")
                    self.drucke("},")
        self.drucke("};")

    def _setup_soft_keywords(self) -> Nichts:
        soft_keywords = sorted(self.soft_keywords)
        self.drucke("static char *soft_keywords[] = {")
        mit self.indent():
            fuer keyword in soft_keywords:
                self.drucke(f'"{keyword}",')
            self.drucke("NULL,")
        self.drucke("};")

    def _set_up_token_start_metadata_extraction(self) -> Nichts:
        self.drucke("if (p->mark == p->fill && _PyPegen_fill_token(p) < 0) {")
        mit self.indent():
            self.drucke("p->error_indicator = 1;")
            self.add_return("NULL")
        self.drucke("}")
        self.drucke("int _start_lineno = p->tokens[_mark]->lineno;")
        self.drucke("UNUSED(_start_lineno); // Only used by EXTRA macro")
        self.drucke("int _start_col_offset = p->tokens[_mark]->col_offset;")
        self.drucke("UNUSED(_start_col_offset); // Only used by EXTRA macro")

    def _set_up_token_end_metadata_extraction(self) -> Nichts:
        self.drucke("Token *_token = _PyPegen_get_last_nonnwhitespace_token(p);")
        self.drucke("if (_token == NULL) {")
        mit self.indent():
            self.add_return("NULL")
        self.drucke("}")
        self.drucke("int _end_lineno = _token->end_lineno;")
        self.drucke("UNUSED(_end_lineno); // Only used by EXTRA macro")
        self.drucke("int _end_col_offset = _token->end_col_offset;")
        self.drucke("UNUSED(_end_col_offset); // Only used by EXTRA macro")

    def _check_for_errors(self) -> Nichts:
        self.drucke("if (p->error_indicator) {")
        mit self.indent():
            self.add_return("NULL")
        self.drucke("}")

    def _set_up_rule_memoization(self, node: Rule, result_type: str) -> Nichts:
        self.drucke("{")
        mit self.indent():
            self.add_level()
            self.drucke(f"{result_type} _res = NULL;")
            self.drucke(f"if (_PyPegen_is_memoized(p, {node.name}_type, &_res)) {{")
            mit self.indent():
                self.add_return("_res")
            self.drucke("}")
            self.drucke("int _mark = p->mark;")
            self.drucke("int _resmark = p->mark;")
            self.drucke("while (1) {")
            mit self.indent():
                self.call_with_errorcheck_return(
                    f"_PyPegen_update_memo(p, _mark, {node.name}_type, _res)", "_res"
                )
                self.drucke("p->mark = _mark;")
                self.drucke(f"void *_raw = {node.name}_raw(p);")
                self.drucke("if (p->error_indicator) {")
                mit self.indent():
                    self.add_return("NULL")
                self.drucke("}")
                self.drucke("if (_raw == NULL || p->mark <= _resmark)")
                mit self.indent():
                    self.drucke("break;")
                self.drucke(f"_resmark = p->mark;")
                self.drucke("_res = _raw;")
            self.drucke("}")
            self.drucke(f"p->mark = _resmark;")
            self.add_return("_res")
        self.drucke("}")
        self.drucke(f"static {result_type}")
        self.drucke(f"{node.name}_raw(Parser *p)")

    def _should_memoize(self, node: Rule) -> bool:
        gib node.memo und nicht node.left_recursive

    def _handle_default_rule_body(self, node: Rule, rhs: Rhs, result_type: str) -> Nichts:
        memoize = self._should_memoize(node)

        mit self.indent():
            self.add_level()
            self._check_for_errors()
            self.drucke(f"{result_type} _res = NULL;")
            wenn memoize:
                self.drucke(f"if (_PyPegen_is_memoized(p, {node.name}_type, &_res)) {{")
                mit self.indent():
                    self.add_return("_res")
                self.drucke("}")
            self.drucke("int _mark = p->mark;")
            wenn any(alt.action und "EXTRA" in alt.action fuer alt in rhs.alts):
                self._set_up_token_start_metadata_extraction()
            self.visit(
                rhs,
                is_loop=Falsch,
                is_gather=node.is_gather(),
                rulename=node.name,
            )
            wenn self.debug:
                self.drucke(f'D(fprintf(stderr, "Fail at %d: {node.name}\\n", p->mark));')
            self.drucke("_res = NULL;")
        self.drucke("  done:")
        mit self.indent():
            wenn memoize:
                self.drucke(f"_PyPegen_insert_memo(p, _mark, {node.name}_type, _res);")
            self.add_return("_res")

    def _handle_loop_rule_body(self, node: Rule, rhs: Rhs) -> Nichts:
        memoize = self._should_memoize(node)
        is_repeat1 = node.name.startswith("_loop1")

        mit self.indent():
            self.add_level()
            self._check_for_errors()
            self.drucke("void *_res = NULL;")
            wenn memoize:
                self.drucke(f"if (_PyPegen_is_memoized(p, {node.name}_type, &_res)) {{")
                mit self.indent():
                    self.add_return("_res")
                self.drucke("}")
            self.drucke("int _mark = p->mark;")
            wenn memoize:
                self.drucke("int _start_mark = p->mark;")
            self.drucke("void **_children = PyMem_Malloc(sizeof(void *));")
            self.out_of_memory_return(f"!_children")
            self.drucke("Py_ssize_t _children_capacity = 1;")
            self.drucke("Py_ssize_t _n = 0;")
            wenn any(alt.action und "EXTRA" in alt.action fuer alt in rhs.alts):
                self._set_up_token_start_metadata_extraction()
            self.visit(
                rhs,
                is_loop=Wahr,
                is_gather=node.is_gather(),
                rulename=node.name,
            )
            wenn is_repeat1:
                self.drucke("if (_n == 0 || p->error_indicator) {")
                mit self.indent():
                    self.drucke("PyMem_Free(_children);")
                    self.add_return("NULL")
                self.drucke("}")
            self.drucke("asdl_seq *_seq = (asdl_seq*)_Py_asdl_generic_seq_new(_n, p->arena);")
            self.out_of_memory_return(f"!_seq", cleanup_code="PyMem_Free(_children);")
            self.drucke("for (Py_ssize_t i = 0; i < _n; i++) asdl_seq_SET_UNTYPED(_seq, i, _children[i]);")
            self.drucke("PyMem_Free(_children);")
            wenn memoize und node.name:
                self.drucke(f"_PyPegen_insert_memo(p, _start_mark, {node.name}_type, _seq);")
            self.add_return("_seq")

    def visit_Rule(self, node: Rule) -> Nichts:
        is_loop = node.is_loop()
        is_gather = node.is_gather()
        rhs = node.flatten()
        wenn is_loop oder is_gather:
            result_type = "asdl_seq *"
        sowenn node.type:
            result_type = node.type
        sonst:
            result_type = "void *"

        fuer line in str(node).splitlines():
            self.drucke(f"// {line}")
        wenn node.left_recursive und node.leader:
            self.drucke(f"static {result_type} {node.name}_raw(Parser *);")

        self.drucke(f"static {result_type}")
        self.drucke(f"{node.name}_rule(Parser *p)")

        wenn node.left_recursive und node.leader:
            self._set_up_rule_memoization(node, result_type)

        self.drucke("{")

        wenn node.name.endswith("without_invalid"):
            mit self.indent():
                self.drucke("int _prev_call_invalid = p->call_invalid_rules;")
                self.drucke("p->call_invalid_rules = 0;")
                self.cleanup_statements.append("p->call_invalid_rules = _prev_call_invalid;")

        wenn is_loop:
            self._handle_loop_rule_body(node, rhs)
        sonst:
            self._handle_default_rule_body(node, rhs, result_type)

        wenn node.name.endswith("without_invalid"):
            self.cleanup_statements.pop()

        self.drucke("}")

    def visit_NamedItem(self, node: NamedItem) -> Nichts:
        call = self.callmakervisitor.generate_call(node)
        wenn call.assigned_variable:
            call.assigned_variable = self.dedupe(call.assigned_variable)
        self.drucke(call)

    def visit_Rhs(
        self, node: Rhs, is_loop: bool, is_gather: bool, rulename: Optional[str]
    ) -> Nichts:
        wenn is_loop:
            assert len(node.alts) == 1
        fuer alt in node.alts:
            self.visit(alt, is_loop=is_loop, is_gather=is_gather, rulename=rulename)

    def join_conditions(self, keyword: str, node: Any) -> Nichts:
        self.drucke(f"{keyword} (")
        mit self.indent():
            first = Wahr
            fuer item in node.items:
                wenn first:
                    first = Falsch
                sonst:
                    self.drucke("&&")
                self.visit(item)
        self.drucke(")")

    def emit_action(self, node: Alt, cleanup_code: Optional[str] = Nichts) -> Nichts:
        self.drucke(f"_res = {node.action};")

        self.drucke("if (_res == NULL && PyErr_Occurred()) {")
        mit self.indent():
            self.drucke("p->error_indicator = 1;")
            wenn cleanup_code:
                self.drucke(cleanup_code)
            self.add_return("NULL")
        self.drucke("}")

        wenn self.debug:
            self.drucke(
                f'D(fprintf(stderr, "Hit mit action [%d-%d]: %s\\n", _mark, p->mark, "{node}"));'
            )

    def emit_default_action(self, is_gather: bool, node: Alt) -> Nichts:
        wenn len(self.local_variable_names) > 1:
            wenn is_gather:
                assert len(self.local_variable_names) == 2
                self.drucke(
                    f"_res = _PyPegen_seq_insert_in_front(p, "
                    f"{self.local_variable_names[0]}, {self.local_variable_names[1]});"
                )
            sonst:
                wenn self.debug:
                    self.drucke(
                        f'D(fprintf(stderr, "Hit without action [%d:%d]: %s\\n", _mark, p->mark, "{node}"));'
                    )
                self.drucke(
                    f"_res = _PyPegen_dummy_name(p, {', '.join(self.local_variable_names)});"
                )
        sonst:
            wenn self.debug:
                self.drucke(
                    f'D(fprintf(stderr, "Hit mit default action [%d:%d]: %s\\n", _mark, p->mark, "{node}"));'
                )
            self.drucke(f"_res = {self.local_variable_names[0]};")

    def emit_dummy_action(self) -> Nichts:
        self.drucke("_res = _PyPegen_dummy_name(p);")

    def handle_alt_normal(self, node: Alt, is_gather: bool, rulename: Optional[str]) -> Nichts:
        self.join_conditions(keyword="if", node=node)
        self.drucke("{")
        # We have parsed successfully all the conditions fuer the option.
        mit self.indent():
            node_str = str(node).replace('"', '\\"')
            self.drucke(
                f'D(fprintf(stderr, "%*c+ {rulename}[%d-%d]: %s succeeded!\\n", p->level, \' \', _mark, p->mark, "{node_str}"));'
            )
            # Prepare to emit the rule action und do so
            wenn node.action und "EXTRA" in node.action:
                self._set_up_token_end_metadata_extraction()
            wenn self.skip_actions:
                self.emit_dummy_action()
            sowenn node.action:
                self.emit_action(node)
            sonst:
                self.emit_default_action(is_gather, node)

            # As the current option has parsed correctly, do nicht weiter mit the rest.
            self.drucke(f"goto done;")
        self.drucke("}")

    def handle_alt_loop(self, node: Alt, is_gather: bool, rulename: Optional[str]) -> Nichts:
        # Condition of the main body of the alternative
        self.join_conditions(keyword="while", node=node)
        self.drucke("{")
        # We have parsed successfully one item!
        mit self.indent():
            # Prepare to emit the rule action und do so
            wenn node.action und "EXTRA" in node.action:
                self._set_up_token_end_metadata_extraction()
            wenn self.skip_actions:
                self.emit_dummy_action()
            sowenn node.action:
                self.emit_action(node, cleanup_code="PyMem_Free(_children);")
            sonst:
                self.emit_default_action(is_gather, node)

            # Add the result of rule to the temporary buffer of children. This buffer
            # will populate later an asdl_seq mit all elements to return.
            self.drucke("if (_n == _children_capacity) {")
            mit self.indent():
                self.drucke("_children_capacity *= 2;")
                self.drucke(
                    "void **_new_children = PyMem_Realloc(_children, _children_capacity*sizeof(void *));"
                )
                self.out_of_memory_return(f"!_new_children", cleanup_code="PyMem_Free(_children);")
                self.drucke("_children = _new_children;")
            self.drucke("}")
            self.drucke("_children[_n++] = _res;")
            self.drucke("_mark = p->mark;")
        self.drucke("}")

    def visit_Alt(
        self, node: Alt, is_loop: bool, is_gather: bool, rulename: Optional[str]
    ) -> Nichts:
        wenn len(node.items) == 1 und str(node.items[0]).startswith("invalid_"):
            self.drucke(f"if (p->call_invalid_rules) {{ // {node}")
        sonst:
            self.drucke(f"{{ // {node}")
        mit self.indent():
            self._check_for_errors()
            node_str = str(node).replace('"', '\\"')
            self.drucke(
                f'D(fprintf(stderr, "%*c> {rulename}[%d-%d]: %s\\n", p->level, \' \', _mark, p->mark, "{node_str}"));'
            )
            # Prepare variable declarations fuer the alternative
            vars = self.collect_vars(node)
            fuer v, var_type in sorted(item fuer item in vars.items() wenn item[0] is nicht Nichts):
                wenn nicht var_type:
                    var_type = "void *"
                sonst:
                    var_type += " "
                wenn v == "_cut_var":
                    v += " = 0"  # cut_var must be initialized
                self.drucke(f"{var_type}{v};")
                wenn v und v.startswith("_opt_var"):
                    self.drucke(f"UNUSED({v}); // Silence compiler warnings")

            mit self.local_variable_context():
                wenn is_loop:
                    self.handle_alt_loop(node, is_gather, rulename)
                sonst:
                    self.handle_alt_normal(node, is_gather, rulename)

            self.drucke("p->mark = _mark;")
            node_str = str(node).replace('"', '\\"')
            self.drucke(
                f"D(fprintf(stderr, \"%*c%s {rulename}[%d-%d]: %s failed!\\n\", p->level, ' ',\n"
                f'                  p->error_indicator ? "ERROR!" : "-", _mark, p->mark, "{node_str}"));'
            )
            wenn "_cut_var" in vars:
                self.drucke("if (_cut_var) {")
                mit self.indent():
                    self.add_return("NULL")
                self.drucke("}")
        self.drucke("}")

    def collect_vars(self, node: Alt) -> Dict[Optional[str], Optional[str]]:
        types = {}
        mit self.local_variable_context():
            fuer item in node.items:
                name, type = self.add_var(item)
                types[name] = type
        gib types

    def add_var(self, node: NamedItem) -> Tuple[Optional[str], Optional[str]]:
        call = self.callmakervisitor.generate_call(node.item)
        name = node.name wenn node.name sonst call.assigned_variable
        wenn name is nicht Nichts:
            name = self.dedupe(name)
        return_type = call.return_type wenn node.type is Nichts sonst node.type
        gib name, return_type
