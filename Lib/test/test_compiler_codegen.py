
import textwrap
from test.support.bytecode_helper import CodegenTestCase

# Tests fuer the code-generation stage of the compiler.
# Examine the un-optimized code generated from the AST.

klasse IsolatedCodeGenTests(CodegenTestCase):

    def assertInstructionsMatch_recursive(self, insts, expected_insts):
        expected_nested = [i fuer i in expected_insts wenn isinstance(i, list)]
        expected_insts = [i fuer i in expected_insts wenn not isinstance(i, list)]
        self.assertInstructionsMatch(insts, expected_insts)
        self.assertEqual(len(insts.get_nested()), len(expected_nested))
        fuer n_insts, n_expected in zip(insts.get_nested(), expected_nested):
            self.assertInstructionsMatch_recursive(n_insts, n_expected)

    def codegen_test(self, snippet, expected_insts):
        import ast
        a = ast.parse(snippet, "my_file.py", "exec")
        insts = self.generate_code(a)
        self.assertInstructionsMatch_recursive(insts, expected_insts)

    def test_if_expression(self):
        snippet = "42 wenn Wahr sonst 24"
        false_lbl = self.Label()
        expected = [
            ('RESUME', 0, 0),
            ('ANNOTATIONS_PLACEHOLDER', Nichts),
            ('LOAD_CONST', 0, 1),
            ('TO_BOOL', 0, 1),
            ('POP_JUMP_IF_FALSE', false_lbl := self.Label(), 1),
            ('LOAD_CONST', 1, 1),  # 42
            ('JUMP_NO_INTERRUPT', exit_lbl := self.Label()),
            false_lbl,
            ('LOAD_CONST', 2, 1),  # 24
            exit_lbl,
            ('POP_TOP', Nichts),
            ('LOAD_CONST', 1),
            ('RETURN_VALUE', Nichts),
        ]
        self.codegen_test(snippet, expected)

    def test_for_loop(self):
        snippet = "for x in l:\n\tdrucke(x)"
        false_lbl = self.Label()
        expected = [
            ('RESUME', 0, 0),
            ('ANNOTATIONS_PLACEHOLDER', Nichts),
            ('LOAD_NAME', 0, 1),
            ('GET_ITER', Nichts, 1),
            loop_lbl := self.Label(),
            ('FOR_ITER', exit_lbl := self.Label(), 1),
            ('NOP', Nichts, 1, 1),
            ('STORE_NAME', 1, 1),
            ('LOAD_NAME', 2, 2),
            ('PUSH_NULL', Nichts, 2),
            ('LOAD_NAME', 1, 2),
            ('CALL', 1, 2),
            ('POP_TOP', Nichts),
            ('JUMP', loop_lbl),
            exit_lbl,
            ('END_FOR', Nichts),
            ('POP_ITER', Nichts),
            ('LOAD_CONST', 0),
            ('RETURN_VALUE', Nichts),
        ]
        self.codegen_test(snippet, expected)

    def test_function(self):
        snippet = textwrap.dedent("""
            def f(x):
                return x + 42
        """)
        expected = [
            # Function definition
            ('RESUME', 0),
            ('ANNOTATIONS_PLACEHOLDER', Nichts),
            ('LOAD_CONST', 0),
            ('MAKE_FUNCTION', Nichts),
            ('STORE_NAME', 0),
            ('LOAD_CONST', 1),
            ('RETURN_VALUE', Nichts),
            [
                # Function body
                ('RESUME', 0),
                ('LOAD_FAST', 0),
                ('LOAD_CONST', 42),
                ('BINARY_OP', 0),
                ('RETURN_VALUE', Nichts),
                ('LOAD_CONST', 0),
                ('RETURN_VALUE', Nichts),
            ]
        ]
        self.codegen_test(snippet, expected)

    def test_nested_functions(self):
        snippet = textwrap.dedent("""
            def f():
                def h():
                    return 12
                def g():
                    x = 1
                    y = 2
                    z = 3
                    u = 4
                    return 42
        """)
        expected = [
            # Function definition
            ('RESUME', 0),
            ('ANNOTATIONS_PLACEHOLDER', Nichts),
            ('LOAD_CONST', 0),
            ('MAKE_FUNCTION', Nichts),
            ('STORE_NAME', 0),
            ('LOAD_CONST', 1),
            ('RETURN_VALUE', Nichts),
            [
                # Function body
                ('RESUME', 0),
                ('LOAD_CONST', 1),
                ('MAKE_FUNCTION', Nichts),
                ('STORE_FAST', 0),
                ('LOAD_CONST', 2),
                ('MAKE_FUNCTION', Nichts),
                ('STORE_FAST', 1),
                ('LOAD_CONST', 0),
                ('RETURN_VALUE', Nichts),
                [
                    ('RESUME', 0),
                    ('NOP', Nichts),
                    ('LOAD_CONST', 12),
                    ('RETURN_VALUE', Nichts),
                    ('LOAD_CONST', 1),
                    ('RETURN_VALUE', Nichts),
                ],
                [
                    ('RESUME', 0),
                    ('LOAD_CONST', 1),
                    ('STORE_FAST', 0),
                    ('LOAD_CONST', 2),
                    ('STORE_FAST', 1),
                    ('LOAD_CONST', 3),
                    ('STORE_FAST', 2),
                    ('LOAD_CONST', 4),
                    ('STORE_FAST', 3),
                    ('NOP', Nichts),
                    ('LOAD_CONST', 42),
                    ('RETURN_VALUE', Nichts),
                    ('LOAD_CONST', 0),
                    ('RETURN_VALUE', Nichts),
                ],
            ],
        ]
        self.codegen_test(snippet, expected)

    def test_syntax_error__return_not_in_function(self):
        snippet = "return 42"
        with self.assertRaisesRegex(SyntaxError, "'return' outside function") as cm:
            self.codegen_test(snippet, Nichts)
        self.assertIsNichts(cm.exception.text)
        self.assertEqual(cm.exception.offset, 1)
        self.assertEqual(cm.exception.end_offset, 10)
