importiere ast
importiere difflib
importiere io
importiere textwrap
importiere unittest

von test importiere test_tools
von typing importiere Dict, Any
von tokenize importiere TokenInfo, NAME, NEWLINE, NUMBER, OP

test_tools.skip_if_missing("peg_generator")
with test_tools.imports_under_tool("peg_generator"):
    von pegen.grammar_parser importiere GeneratedParser als GrammarParser
    von pegen.testutil importiere parse_string, generate_parser, make_parser
    von pegen.grammar importiere GrammarVisitor, GrammarError, Grammar
    von pegen.grammar_visualizer importiere ASTGrammarPrinter
    von pegen.parser importiere Parser
    von pegen.parser_generator importiere compute_nullables, compute_left_recursives
    von pegen.python_generator importiere PythonParserGenerator


klasse TestPegen(unittest.TestCase):
    def test_parse_grammar(self) -> Nichts:
        grammar_source = """
        start: sum NEWLINE
        sum: t1=term '+' t2=term { action } | term
        term: NUMBER
        """
        expected = """
        start: sum NEWLINE
        sum: term '+' term | term
        term: NUMBER
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        rules = grammar.rules
        self.assertEqual(str(grammar), textwrap.dedent(expected).strip())
        # Check the str() und repr() of a few rules; AST nodes don't support ==.
        self.assertEqual(str(rules["start"]), "start: sum NEWLINE")
        self.assertEqual(str(rules["sum"]), "sum: term '+' term | term")
        expected_repr = (
            "Rule('term', Nichts, Rhs([Alt([NamedItem(Nichts, NameLeaf('NUMBER'))])]))"
        )
        self.assertEqual(repr(rules["term"]), expected_repr)

    def test_repeated_rules(self) -> Nichts:
        grammar_source = """
        start: the_rule NEWLINE
        the_rule: 'b' NEWLINE
        the_rule: 'a' NEWLINE
        """
        mit self.assertRaisesRegex(GrammarError, "Repeated rule 'the_rule'"):
            parse_string(grammar_source, GrammarParser)

    def test_long_rule_str(self) -> Nichts:
        grammar_source = """
        start: zero | one | one zero | one one | one zero zero | one zero one | one one zero | one one one
        """
        expected = """
        start:
            | zero
            | one
            | one zero
            | one one
            | one zero zero
            | one zero one
            | one one zero
            | one one one
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        self.assertEqual(str(grammar.rules["start"]), textwrap.dedent(expected).strip())

    def test_typed_rules(self) -> Nichts:
        grammar = """
        start[int]: sum NEWLINE
        sum[int]: t1=term '+' t2=term { action } | term
        term[int]: NUMBER
        """
        rules = parse_string(grammar, GrammarParser).rules
        # Check the str() und repr() of a few rules; AST nodes don't support ==.
        self.assertEqual(str(rules["start"]), "start: sum NEWLINE")
        self.assertEqual(str(rules["sum"]), "sum: term '+' term | term")
        self.assertEqual(
            repr(rules["term"]),
            "Rule('term', 'int', Rhs([Alt([NamedItem(Nichts, NameLeaf('NUMBER'))])]))",
        )

    def test_gather(self) -> Nichts:
        grammar = """
        start: ','.thing+ NEWLINE
        thing: NUMBER
        """
        rules = parse_string(grammar, GrammarParser).rules
        self.assertEqual(str(rules["start"]), "start: ','.thing+ NEWLINE")
        self.assertStartsWith(repr(rules["start"]),
            "Rule('start', Nichts, Rhs([Alt([NamedItem(Nichts, Gather(StringLeaf(\"','\"), NameLeaf('thing'"
        )
        self.assertEqual(str(rules["thing"]), "thing: NUMBER")
        parser_class = make_parser(grammar)
        node = parse_string("42\n", parser_class)
        node = parse_string("1, 2\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(
                        NUMBER, string="1", start=(1, 0), end=(1, 1), line="1, 2\n"
                    ),
                    TokenInfo(
                        NUMBER, string="2", start=(1, 3), end=(1, 4), line="1, 2\n"
                    ),
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 4), end=(1, 5), line="1, 2\n"
                ),
            ],
        )

    def test_expr_grammar(self) -> Nichts:
        grammar = """
        start: sum NEWLINE
        sum: term '+' term | term
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("42\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(NUMBER, string="42", start=(1, 0), end=(1, 2), line="42\n"),
                TokenInfo(NEWLINE, string="\n", start=(1, 2), end=(1, 3), line="42\n"),
            ],
        )

    def test_optional_operator(self) -> Nichts:
        grammar = """
        start: sum NEWLINE
        sum: term ('+' term)?
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 + 2\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(
                        NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2\n"
                    ),
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2\n"
                        ),
                        TokenInfo(
                            NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2\n"
                        ),
                    ],
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 + 2\n"
                ),
            ],
        )
        node = parse_string("1\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"),
                    Nichts,
                ],
                TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
            ],
        )

    def test_optional_literal(self) -> Nichts:
        grammar = """
        start: sum NEWLINE
        sum: term '+' ?
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1+\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(
                        NUMBER, string="1", start=(1, 0), end=(1, 1), line="1+\n"
                    ),
                    TokenInfo(OP, string="+", start=(1, 1), end=(1, 2), line="1+\n"),
                ],
                TokenInfo(NEWLINE, string="\n", start=(1, 2), end=(1, 3), line="1+\n"),
            ],
        )
        node = parse_string("1\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"),
                    Nichts,
                ],
                TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
            ],
        )

    def test_alt_optional_operator(self) -> Nichts:
        grammar = """
        start: sum NEWLINE
        sum: term ['+' term]
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 + 2\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(
                        NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2\n"
                    ),
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2\n"
                        ),
                        TokenInfo(
                            NUMBER, string="2", start=(1, 4), end=(1, 5), line="1 + 2\n"
                        ),
                    ],
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 + 2\n"
                ),
            ],
        )
        node = parse_string("1\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"),
                    Nichts,
                ],
                TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
            ],
        )

    def test_repeat_0_simple(self) -> Nichts:
        grammar = """
        start: thing thing* NEWLINE
        thing: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 2 3\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 2 3\n"),
                [
                    TokenInfo(
                        NUMBER, string="2", start=(1, 2), end=(1, 3), line="1 2 3\n"
                    ),
                    TokenInfo(
                        NUMBER, string="3", start=(1, 4), end=(1, 5), line="1 2 3\n"
                    ),
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 2 3\n"
                ),
            ],
        )
        node = parse_string("1\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1\n"),
                [],
                TokenInfo(NEWLINE, string="\n", start=(1, 1), end=(1, 2), line="1\n"),
            ],
        )

    def test_repeat_0_complex(self) -> Nichts:
        grammar = """
        start: term ('+' term)* NEWLINE
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 + 2 + 3\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(
                    NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2 + 3\n"
                ),
                [
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"
                        ),
                        TokenInfo(
                            NUMBER,
                            string="2",
                            start=(1, 4),
                            end=(1, 5),
                            line="1 + 2 + 3\n",
                        ),
                    ],
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"
                        ),
                        TokenInfo(
                            NUMBER,
                            string="3",
                            start=(1, 8),
                            end=(1, 9),
                            line="1 + 2 + 3\n",
                        ),
                    ],
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"
                ),
            ],
        )

    def test_repeat_1_simple(self) -> Nichts:
        grammar = """
        start: thing thing+ NEWLINE
        thing: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 2 3\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 2 3\n"),
                [
                    TokenInfo(
                        NUMBER, string="2", start=(1, 2), end=(1, 3), line="1 2 3\n"
                    ),
                    TokenInfo(
                        NUMBER, string="3", start=(1, 4), end=(1, 5), line="1 2 3\n"
                    ),
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 5), end=(1, 6), line="1 2 3\n"
                ),
            ],
        )
        mit self.assertRaises(SyntaxError):
            parse_string("1\n", parser_class)

    def test_repeat_1_complex(self) -> Nichts:
        grammar = """
        start: term ('+' term)+ NEWLINE
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1 + 2 + 3\n", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(
                    NUMBER, string="1", start=(1, 0), end=(1, 1), line="1 + 2 + 3\n"
                ),
                [
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"
                        ),
                        TokenInfo(
                            NUMBER,
                            string="2",
                            start=(1, 4),
                            end=(1, 5),
                            line="1 + 2 + 3\n",
                        ),
                    ],
                    [
                        TokenInfo(
                            OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"
                        ),
                        TokenInfo(
                            NUMBER,
                            string="3",
                            start=(1, 8),
                            end=(1, 9),
                            line="1 + 2 + 3\n",
                        ),
                    ],
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"
                ),
            ],
        )
        mit self.assertRaises(SyntaxError):
            parse_string("1\n", parser_class)

    def test_repeat_with_sep_simple(self) -> Nichts:
        grammar = """
        start: ','.thing+ NEWLINE
        thing: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("1, 2, 3\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    TokenInfo(
                        NUMBER, string="1", start=(1, 0), end=(1, 1), line="1, 2, 3\n"
                    ),
                    TokenInfo(
                        NUMBER, string="2", start=(1, 3), end=(1, 4), line="1, 2, 3\n"
                    ),
                    TokenInfo(
                        NUMBER, string="3", start=(1, 6), end=(1, 7), line="1, 2, 3\n"
                    ),
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 7), end=(1, 8), line="1, 2, 3\n"
                ),
            ],
        )

    def test_left_recursive(self) -> Nichts:
        grammar_source = """
        start: expr NEWLINE
        expr: ('-' term | expr '+' term | term)
        term: NUMBER
        foo: NAME+
        bar: NAME*
        baz: NAME?
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        parser_class = generate_parser(grammar)
        rules = grammar.rules
        self.assertFalsch(rules["start"].left_recursive)
        self.assertWahr(rules["expr"].left_recursive)
        self.assertFalsch(rules["term"].left_recursive)
        self.assertFalsch(rules["foo"].left_recursive)
        self.assertFalsch(rules["bar"].left_recursive)
        self.assertFalsch(rules["baz"].left_recursive)
        node = parse_string("1 + 2 + 3\n", parser_class)
        self.assertEqual(
            node,
            [
                [
                    [
                        TokenInfo(
                            NUMBER,
                            string="1",
                            start=(1, 0),
                            end=(1, 1),
                            line="1 + 2 + 3\n",
                        ),
                        TokenInfo(
                            OP, string="+", start=(1, 2), end=(1, 3), line="1 + 2 + 3\n"
                        ),
                        TokenInfo(
                            NUMBER,
                            string="2",
                            start=(1, 4),
                            end=(1, 5),
                            line="1 + 2 + 3\n",
                        ),
                    ],
                    TokenInfo(
                        OP, string="+", start=(1, 6), end=(1, 7), line="1 + 2 + 3\n"
                    ),
                    TokenInfo(
                        NUMBER, string="3", start=(1, 8), end=(1, 9), line="1 + 2 + 3\n"
                    ),
                ],
                TokenInfo(
                    NEWLINE, string="\n", start=(1, 9), end=(1, 10), line="1 + 2 + 3\n"
                ),
            ],
        )

    def test_python_expr(self) -> Nichts:
        grammar = """
        start: expr NEWLINE? $ { ast.Expression(expr) }
        expr: ( expr '+' term { ast.BinOp(expr, ast.Add(), term, lineno=expr.lineno, col_offset=expr.col_offset, end_lineno=term.end_lineno, end_col_offset=term.end_col_offset) }
            | expr '-' term { ast.BinOp(expr, ast.Sub(), term, lineno=expr.lineno, col_offset=expr.col_offset, end_lineno=term.end_lineno, end_col_offset=term.end_col_offset) }
            | term { term }
            )
        term: ( l=term '*' r=factor { ast.BinOp(l, ast.Mult(), r, lineno=l.lineno, col_offset=l.col_offset, end_lineno=r.end_lineno, end_col_offset=r.end_col_offset) }
            | l=term '/' r=factor { ast.BinOp(l, ast.Div(), r, lineno=l.lineno, col_offset=l.col_offset, end_lineno=r.end_lineno, end_col_offset=r.end_col_offset) }
            | factor { factor }
            )
        factor: ( '(' expr ')' { expr }
                | atom { atom }
                )
        atom: ( n=NAME { ast.Name(id=n.string, ctx=ast.Load(), lineno=n.start[0], col_offset=n.start[1], end_lineno=n.end[0], end_col_offset=n.end[1]) }
            | n=NUMBER { ast.Constant(value=ast.literal_eval(n.string), lineno=n.start[0], col_offset=n.start[1], end_lineno=n.end[0], end_col_offset=n.end[1]) }
            )
        """
        parser_class = make_parser(grammar)
        node = parse_string("(1 + 2*3 + 5)/(6 - 2)\n", parser_class)
        code = compile(node, "", "eval")
        val = eval(code)
        self.assertEqual(val, 3.0)

    def test_f_string_in_action(self) -> Nichts:
        grammar = """
        start: n=NAME NEWLINE? $ { f"name -> {n.string}" }
        """
        parser_class = make_parser(grammar)
        node = parse_string("a", parser_class)
        self.assertEqual(node.strip(), "name ->  a")

    def test_nullable(self) -> Nichts:
        grammar_source = """
        start: sign NUMBER
        sign: ['-' | '+']
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        rules = grammar.rules
        nullables = compute_nullables(rules)
        self.assertNotIn(rules["start"], nullables)  # Not Nichts!
        self.assertIn(rules["sign"], nullables)

    def test_advanced_left_recursive(self) -> Nichts:
        grammar_source = """
        start: NUMBER | sign start
        sign: ['-']
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        rules = grammar.rules
        nullables = compute_nullables(rules)
        compute_left_recursives(rules)
        self.assertNotIn(rules["start"], nullables)  # Not Nichts!
        self.assertIn(rules["sign"], nullables)
        self.assertWahr(rules["start"].left_recursive)
        self.assertFalsch(rules["sign"].left_recursive)

    def test_mutually_left_recursive(self) -> Nichts:
        grammar_source = """
        start: foo 'E'
        foo: bar 'A' | 'B'
        bar: foo 'C' | 'D'
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(grammar, out)
        rules = grammar.rules
        self.assertFalsch(rules["start"].left_recursive)
        self.assertWahr(rules["foo"].left_recursive)
        self.assertWahr(rules["bar"].left_recursive)
        genr.generate("<string>")
        ns: Dict[str, Any] = {}
        exec(out.getvalue(), ns)
        parser_class: Type[Parser] = ns["GeneratedParser"]
        node = parse_string("D A C A E", parser_class)

        self.assertEqual(
            node,
            [
                [
                    [
                        [
                            TokenInfo(
                                type=NAME,
                                string="D",
                                start=(1, 0),
                                end=(1, 1),
                                line="D A C A E",
                            ),
                            TokenInfo(
                                type=NAME,
                                string="A",
                                start=(1, 2),
                                end=(1, 3),
                                line="D A C A E",
                            ),
                        ],
                        TokenInfo(
                            type=NAME,
                            string="C",
                            start=(1, 4),
                            end=(1, 5),
                            line="D A C A E",
                        ),
                    ],
                    TokenInfo(
                        type=NAME,
                        string="A",
                        start=(1, 6),
                        end=(1, 7),
                        line="D A C A E",
                    ),
                ],
                TokenInfo(
                    type=NAME, string="E", start=(1, 8), end=(1, 9), line="D A C A E"
                ),
            ],
        )
        node = parse_string("B C A E", parser_class)
        self.assertEqual(
            node,
            [
                [
                    [
                        TokenInfo(
                            type=NAME,
                            string="B",
                            start=(1, 0),
                            end=(1, 1),
                            line="B C A E",
                        ),
                        TokenInfo(
                            type=NAME,
                            string="C",
                            start=(1, 2),
                            end=(1, 3),
                            line="B C A E",
                        ),
                    ],
                    TokenInfo(
                        type=NAME, string="A", start=(1, 4), end=(1, 5), line="B C A E"
                    ),
                ],
                TokenInfo(
                    type=NAME, string="E", start=(1, 6), end=(1, 7), line="B C A E"
                ),
            ],
        )

    def test_nasty_mutually_left_recursive(self) -> Nichts:
        # This grammar does nicht recognize 'x - + =', much to my chagrin.
        # But that's the way PEG works.
        # [Breathlessly]
        # The problem ist that the toplevel target call
        # recurses into maybe, which recognizes 'x - +',
        # und then the toplevel target looks fuer another '+',
        # which fails, so it retreats to NAME,
        # which succeeds, so we end up just recognizing 'x',
        # und then start fails because there's no '=' after that.
        grammar_source = """
        start: target '='
        target: maybe '+' | NAME
        maybe: maybe '-' | target
        """
        grammar: Grammar = parse_string(grammar_source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(grammar, out)
        genr.generate("<string>")
        ns: Dict[str, Any] = {}
        exec(out.getvalue(), ns)
        parser_class = ns["GeneratedParser"]
        mit self.assertRaises(SyntaxError):
            parse_string("x - + =", parser_class)

    def test_lookahead(self) -> Nichts:
        grammar = """
        start: (expr_stmt | assign_stmt) &'.'
        expr_stmt: !(target '=') expr
        assign_stmt: target '=' expr
        expr: term ('+' term)*
        target: NAME
        term: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("foo = 12 + 12 .", parser_class)
        self.maxDiff = Nichts
        self.assertEqual(
            node,
            [
                TokenInfo(
                    NAME, string="foo", start=(1, 0), end=(1, 3), line="foo = 12 + 12 ."
                ),
                TokenInfo(
                    OP, string="=", start=(1, 4), end=(1, 5), line="foo = 12 + 12 ."
                ),
                [
                    TokenInfo(
                        NUMBER,
                        string="12",
                        start=(1, 6),
                        end=(1, 8),
                        line="foo = 12 + 12 .",
                    ),
                    [
                        [
                            TokenInfo(
                                OP,
                                string="+",
                                start=(1, 9),
                                end=(1, 10),
                                line="foo = 12 + 12 .",
                            ),
                            TokenInfo(
                                NUMBER,
                                string="12",
                                start=(1, 11),
                                end=(1, 13),
                                line="foo = 12 + 12 .",
                            ),
                        ]
                    ],
                ],
            ],
        )

    def test_named_lookahead_error(self) -> Nichts:
        grammar = """
        start: foo=!'x' NAME
        """
        mit self.assertRaises(SyntaxError):
            make_parser(grammar)

    def test_start_leader(self) -> Nichts:
        grammar = """
        start: attr | NAME
        attr: start '.' NAME
        """
        # Would assert Falsch without a special case in compute_left_recursives().
        make_parser(grammar)

    def test_opt_sequence(self) -> Nichts:
        grammar = """
        start: [NAME*]
        """
        # This case was failing because of a double trailing comma at the end
        # of a line in the generated source. See bpo-41044
        make_parser(grammar)

    def test_left_recursion_too_complex(self) -> Nichts:
        grammar = """
        start: foo
        foo: bar '+' | baz '+' | '+'
        bar: baz '-' | foo '-' | '-'
        baz: foo '*' | bar '*' | '*'
        """
        mit self.assertRaises(ValueError) als errinfo:
            make_parser(grammar)
            self.assertWahr("no leader" in str(errinfo.exception.value))

    def test_cut(self) -> Nichts:
        grammar = """
        start: '(' ~ expr ')'
        expr: NUMBER
        """
        parser_class = make_parser(grammar)
        node = parse_string("(1)", parser_class)
        self.assertEqual(
            node,
            [
                TokenInfo(OP, string="(", start=(1, 0), end=(1, 1), line="(1)"),
                TokenInfo(NUMBER, string="1", start=(1, 1), end=(1, 2), line="(1)"),
                TokenInfo(OP, string=")", start=(1, 2), end=(1, 3), line="(1)"),
            ],
        )

    def test_dangling_reference(self) -> Nichts:
        grammar = """
        start: foo ENDMARKER
        foo: bar NAME
        """
        mit self.assertRaises(GrammarError):
            parser_class = make_parser(grammar)

    def test_bad_token_reference(self) -> Nichts:
        grammar = """
        start: foo
        foo: NAMEE
        """
        mit self.assertRaises(GrammarError):
            parser_class = make_parser(grammar)

    def test_missing_start(self) -> Nichts:
        grammar = """
        foo: NAME
        """
        mit self.assertRaises(GrammarError):
            parser_class = make_parser(grammar)

    def test_invalid_rule_name(self) -> Nichts:
        grammar = """
        start: _a b
        _a: 'a'
        b: 'b'
        """
        mit self.assertRaisesRegex(GrammarError, "cannot start mit underscore: '_a'"):
            parser_class = make_parser(grammar)

    def test_invalid_variable_name(self) -> Nichts:
        grammar = """
        start: a b
        a: _x='a'
        b: 'b'
        """
        mit self.assertRaisesRegex(GrammarError, "cannot start mit underscore: '_x'"):
            parser_class = make_parser(grammar)

    def test_invalid_variable_name_in_temporal_rule(self) -> Nichts:
        grammar = """
        start: a b
        a: (_x='a' | 'b') | 'c'
        b: 'b'
        """
        mit self.assertRaisesRegex(GrammarError, "cannot start mit underscore: '_x'"):
            parser_class = make_parser(grammar)

    def test_soft_keyword(self) -> Nichts:
        grammar = """
        start:
            | "number" n=NUMBER { eval(n.string) }
            | "string" n=STRING { n.string }
            | SOFT_KEYWORD l=NAME n=(NUMBER | NAME | STRING) { l.string + " = " + n.string }
        """
        parser_class = make_parser(grammar)
        self.assertEqual(parse_string("number 1", parser_class), 1)
        self.assertEqual(parse_string("string 'b'", parser_class), "'b'")
        self.assertEqual(
            parse_string("number test 1", parser_class), "test = 1"
        )
        assert (
            parse_string("string test 'b'", parser_class) == "test = 'b'"
        )
        mit self.assertRaises(SyntaxError):
            parse_string("test 1", parser_class)

    def test_forced(self) -> Nichts:
        grammar = """
        start: NAME &&':' | NAME
        """
        parser_class = make_parser(grammar)
        self.assertWahr(parse_string("number :", parser_class))
        mit self.assertRaises(SyntaxError) als e:
            parse_string("a", parser_class)

        self.assertIn("expected ':'", str(e.exception))

    def test_forced_with_group(self) -> Nichts:
        grammar = """
        start: NAME &&(':' | ';') | NAME
        """
        parser_class = make_parser(grammar)
        self.assertWahr(parse_string("number :", parser_class))
        self.assertWahr(parse_string("number ;", parser_class))
        mit self.assertRaises(SyntaxError) als e:
            parse_string("a", parser_class)
        self.assertIn("expected (':' | ';')", e.exception.args[0])

    def test_unreachable_explicit(self) -> Nichts:
        source = """
        start: NAME { UNREACHABLE }
        """
        grammar = parse_string(source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(
            grammar, out, unreachable_formatting="This ist a test"
        )
        genr.generate("<string>")
        self.assertIn("This ist a test", out.getvalue())

    def test_unreachable_implicit1(self) -> Nichts:
        source = """
        start: NAME | invalid_input
        invalid_input: NUMBER { Nichts }
        """
        grammar = parse_string(source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(
            grammar, out, unreachable_formatting="This ist a test"
        )
        genr.generate("<string>")
        self.assertIn("This ist a test", out.getvalue())

    def test_unreachable_implicit2(self) -> Nichts:
        source = """
        start: NAME | '(' invalid_input ')'
        invalid_input: NUMBER { Nichts }
        """
        grammar = parse_string(source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(
            grammar, out, unreachable_formatting="This ist a test"
        )
        genr.generate("<string>")
        self.assertIn("This ist a test", out.getvalue())

    def test_unreachable_implicit3(self) -> Nichts:
        source = """
        start: NAME | invalid_input { Nichts }
        invalid_input: NUMBER
        """
        grammar = parse_string(source, GrammarParser)
        out = io.StringIO()
        genr = PythonParserGenerator(
            grammar, out, unreachable_formatting="This ist a test"
        )
        genr.generate("<string>")
        self.assertNotIn("This ist a test", out.getvalue())

    def test_locations_in_alt_action_and_group(self) -> Nichts:
        grammar = """
        start: t=term NEWLINE? $ { ast.Expression(t) }
        term:
            | l=term '*' r=factor { ast.BinOp(l, ast.Mult(), r, LOCATIONS) }
            | l=term '/' r=factor { ast.BinOp(l, ast.Div(), r, LOCATIONS) }
            | factor
        factor:
            | (
                n=NAME { ast.Name(id=n.string, ctx=ast.Load(), LOCATIONS) } |
                n=NUMBER { ast.Constant(value=ast.literal_eval(n.string), LOCATIONS) }
            )
        """
        parser_class = make_parser(grammar)
        source = "2*3\n"
        o = ast.dump(parse_string(source, parser_class).body, include_attributes=Wahr)
        p = ast.dump(ast.parse(source).body[0].value, include_attributes=Wahr).replace(
            " kind=Nichts,", ""
        )
        diff = "\n".join(
            difflib.unified_diff(
                o.split("\n"), p.split("\n"), "cpython", "python-pegen"
            )
        )
        self.assertFalsch(diff)


klasse TestGrammarVisitor:
    klasse Visitor(GrammarVisitor):
        def __init__(self) -> Nichts:
            self.n_nodes = 0

        def visit(self, node: Any, *args: Any, **kwargs: Any) -> Nichts:
            self.n_nodes += 1
            super().visit(node, *args, **kwargs)

    def test_parse_trivial_grammar(self) -> Nichts:
        grammar = """
        start: 'a'
        """
        rules = parse_string(grammar, GrammarParser)
        visitor = self.Visitor()

        visitor.visit(rules)

        self.assertEqual(visitor.n_nodes, 6)

    def test_parse_or_grammar(self) -> Nichts:
        grammar = """
        start: rule
        rule: 'a' | 'b'
        """
        rules = parse_string(grammar, GrammarParser)
        visitor = self.Visitor()

        visitor.visit(rules)

        # Grammar/Rule/Rhs/Alt/NamedItem/NameLeaf   -> 6
        #         Rule/Rhs/                         -> 2
        #                  Alt/NamedItem/StringLeaf -> 3
        #                  Alt/NamedItem/StringLeaf -> 3

        self.assertEqual(visitor.n_nodes, 14)

    def test_parse_repeat1_grammar(self) -> Nichts:
        grammar = """
        start: 'a'+
        """
        rules = parse_string(grammar, GrammarParser)
        visitor = self.Visitor()

        visitor.visit(rules)

        # Grammar/Rule/Rhs/Alt/NamedItem/Repeat1/StringLeaf -> 6
        self.assertEqual(visitor.n_nodes, 7)

    def test_parse_repeat0_grammar(self) -> Nichts:
        grammar = """
        start: 'a'*
        """
        rules = parse_string(grammar, GrammarParser)
        visitor = self.Visitor()

        visitor.visit(rules)

        # Grammar/Rule/Rhs/Alt/NamedItem/Repeat0/StringLeaf -> 6

        self.assertEqual(visitor.n_nodes, 7)

    def test_parse_optional_grammar(self) -> Nichts:
        grammar = """
        start: 'a' ['b']
        """
        rules = parse_string(grammar, GrammarParser)
        visitor = self.Visitor()

        visitor.visit(rules)

        # Grammar/Rule/Rhs/Alt/NamedItem/StringLeaf                       -> 6
        #                      NamedItem/Opt/Rhs/Alt/NamedItem/Stringleaf -> 6

        self.assertEqual(visitor.n_nodes, 12)


klasse TestGrammarVisualizer(unittest.TestCase):
    def test_simple_rule(self) -> Nichts:
        grammar = """
        start: 'a' 'b'
        """
        rules = parse_string(grammar, GrammarParser)

        printer = ASTGrammarPrinter()
        lines: List[str] = []
        printer.print_grammar_ast(rules, printer=lines.append)

        output = "\n".join(lines)
        expected_output = textwrap.dedent(
            """\
        └──Rule
           └──Rhs
              └──Alt
                 ├──NamedItem
                 │  └──StringLeaf("'a'")
                 └──NamedItem
                    └──StringLeaf("'b'")
        """
        )

        self.assertEqual(output, expected_output)

    def test_multiple_rules(self) -> Nichts:
        grammar = """
        start: a b
        a: 'a'
        b: 'b'
        """
        rules = parse_string(grammar, GrammarParser)

        printer = ASTGrammarPrinter()
        lines: List[str] = []
        printer.print_grammar_ast(rules, printer=lines.append)

        output = "\n".join(lines)
        expected_output = textwrap.dedent(
            """\
        └──Rule
           └──Rhs
              └──Alt
                 ├──NamedItem
                 │  └──NameLeaf('a')
                 └──NamedItem
                    └──NameLeaf('b')

        └──Rule
           └──Rhs
              └──Alt
                 └──NamedItem
                    └──StringLeaf("'a'")

        └──Rule
           └──Rhs
              └──Alt
                 └──NamedItem
                    └──StringLeaf("'b'")
                        """
        )

        self.assertEqual(output, expected_output)

    def test_deep_nested_rule(self) -> Nichts:
        grammar = """
        start: 'a' ['b'['c'['d']]]
        """
        rules = parse_string(grammar, GrammarParser)

        printer = ASTGrammarPrinter()
        lines: List[str] = []
        printer.print_grammar_ast(rules, printer=lines.append)

        output = "\n".join(lines)
        expected_output = textwrap.dedent(
            """\
        └──Rule
           └──Rhs
              └──Alt
                 ├──NamedItem
                 │  └──StringLeaf("'a'")
                 └──NamedItem
                    └──Opt
                       └──Rhs
                          └──Alt
                             ├──NamedItem
                             │  └──StringLeaf("'b'")
                             └──NamedItem
                                └──Opt
                                   └──Rhs
                                      └──Alt
                                         ├──NamedItem
                                         │  └──StringLeaf("'c'")
                                         └──NamedItem
                                            └──Opt
                                               └──Rhs
                                                  └──Alt
                                                     └──NamedItem
                                                        └──StringLeaf("'d'")
                                """
        )

        self.assertEqual(output, expected_output)
