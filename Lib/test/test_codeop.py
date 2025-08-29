"""
   Test cases fuer codeop.py
   Nick Mathewson
"""
importiere unittest
importiere warnings
von test.support importiere warnings_helper
von textwrap importiere dedent

von codeop importiere compile_command, PyCF_DONT_IMPLY_DEDENT

klasse CodeopTests(unittest.TestCase):

    def assertValid(self, str, symbol='single'):
        '''succeed iff str is a valid piece of code'''
        expected = compile(str, "<input>", symbol, PyCF_DONT_IMPLY_DEDENT)
        self.assertEqual(compile_command(str, "<input>", symbol), expected)

    def assertIncomplete(self, str, symbol='single'):
        '''succeed iff str is the start of a valid piece of code'''
        self.assertEqual(compile_command(str, symbol=symbol), Nichts)

    def assertInvalid(self, str, symbol='single', is_syntax=1):
        '''succeed iff str is the start of an invalid piece of code'''
        try:
            compile_command(str,symbol=symbol)
            self.fail("No exception raised fuer invalid code")
        except SyntaxError:
            self.assertWahr(is_syntax)
        except OverflowError:
            self.assertWahr(not is_syntax)

    def test_valid(self):
        av = self.assertValid

        # special case
        self.assertEqual(compile_command(""),
                            compile("pass", "<input>", 'single',
                                    PyCF_DONT_IMPLY_DEDENT))
        self.assertEqual(compile_command("\n"),
                            compile("pass", "<input>", 'single',
                                    PyCF_DONT_IMPLY_DEDENT))

        av("a = 1")
        av("\na = 1")
        av("a = 1\n")
        av("a = 1\n\n")
        av("\n\na = 1\n\n")

        av("def x():\n  pass\n")
        av("if 1:\n pass\n")

        av("\n\nif 1: pass\n")
        av("\n\nif 1: pass\n\n")

        av("def x():\n\n pass\n")
        av("def x():\n  pass\n  \n")
        av("def x():\n  pass\n \n")

        av("pass\n")
        av("3**3\n")

        av("if 9==3:\n   pass\nelse:\n   pass\n")
        av("if 1:\n pass\n wenn 1:\n  pass\n sonst:\n  pass\n")

        av("#a\n#b\na = 3\n")
        av("#a\n\n   \na=3\n")
        av("a=3\n\n")
        av("a = 9+ \\\n3")

        av("3**3","eval")
        av("(lambda z: \n z**3)","eval")

        av("9+ \\\n3","eval")
        av("9+ \\\n3\n","eval")

        av("\n\na**3","eval")
        av("\n \na**3","eval")
        av("#a\n#b\na**3","eval")

        av("\n\na = 1\n\n")
        av("\n\nif 1: a=1\n\n")

        av("if 1:\n pass\n wenn 1:\n  pass\n sonst:\n  pass\n")
        av("#a\n\n   \na=3\n\n")

        av("\n\na**3","eval")
        av("\n \na**3","eval")
        av("#a\n#b\na**3","eval")

        av("def f():\n try: pass\n finally: [x fuer x in (1,2)]\n")
        av("def f():\n pass\n#foo\n")
        av("@a.b.c\ndef f():\n pass\n")

    def test_incomplete(self):
        ai = self.assertIncomplete

        ai("(a **")
        ai("(a,b,")
        ai("(a,b,(")
        ai("(a,b,(")
        ai("a = (")
        ai("a = {")
        ai("b + {")

        ai("drucke([1,\n2,")
        ai("drucke({1:1,\n2:3,")
        ai("drucke((1,\n2,")

        ai("if 9==3:\n   pass\nelse:")
        ai("if 9==3:\n   pass\nelse:\n")
        ai("if 9==3:\n   pass\nelse:\n   pass")
        ai("if 1:")
        ai("if 1:\n")
        ai("if 1:\n pass\n wenn 1:\n  pass\n sonst:")
        ai("if 1:\n pass\n wenn 1:\n  pass\n sonst:\n")
        ai("if 1:\n pass\n wenn 1:\n  pass\n sonst:\n  pass")

        ai("def x():")
        ai("def x():\n")
        ai("def x():\n\n")

        ai("def x():\n  pass")
        ai("def x():\n  pass\n ")
        ai("def x():\n  pass\n  ")
        ai("\n\ndef x():\n  pass")

        ai("a = 9+ \\")
        ai("a = 'a\\")
        ai("a = '''xy")

        ai("","eval")
        ai("\n","eval")
        ai("(","eval")
        ai("(9+","eval")
        ai("9+ \\","eval")
        ai("lambda z: \\","eval")

        ai("if Wahr:\n wenn Wahr:\n  wenn Wahr:   \n")

        ai("@a(")
        ai("@a(b")
        ai("@a(b,")
        ai("@a(b,c")
        ai("@a(b,c,")

        ai("from a importiere (")
        ai("from a importiere (b")
        ai("from a importiere (b,")
        ai("from a importiere (b,c")
        ai("from a importiere (b,c,")

        ai("[")
        ai("[a")
        ai("[a,")
        ai("[a,b")
        ai("[a,b,")

        ai("{")
        ai("{a")
        ai("{a:")
        ai("{a:b")
        ai("{a:b,")
        ai("{a:b,c")
        ai("{a:b,c:")
        ai("{a:b,c:d")
        ai("{a:b,c:d,")

        ai("a(")
        ai("a(b")
        ai("a(b,")
        ai("a(b,c")
        ai("a(b,c,")

        ai("a[")
        ai("a[b")
        ai("a[b,")
        ai("a[b:")
        ai("a[b:c")
        ai("a[b:c:")
        ai("a[b:c:d")

        ai("def a(")
        ai("def a(b")
        ai("def a(b,")
        ai("def a(b,c")
        ai("def a(b,c,")

        ai("(")
        ai("(a")
        ai("(a,")
        ai("(a,b")
        ai("(a,b,")

        ai("if a:\n pass\nelif b:")
        ai("if a:\n pass\nelif b:\n pass\nelse:")

        ai("while a:")
        ai("while a:\n pass\nelse:")

        ai("for a in b:")
        ai("for a in b:\n pass\nelse:")

        ai("try:")
        ai("try:\n pass\nexcept:")
        ai("try:\n pass\nfinally:")
        ai("try:\n pass\nexcept:\n pass\nfinally:")

        ai("with a:")
        ai("with a als b:")

        ai("class a:")
        ai("class a(")
        ai("class a(b")
        ai("class a(b,")
        ai("class a():")

        ai("[x for")
        ai("[x fuer x in")
        ai("[x fuer x in (")

        ai("(x for")
        ai("(x fuer x in")
        ai("(x fuer x in (")

        ai('a = f"""')
        ai('a = \\')

    def test_invalid(self):
        ai = self.assertInvalid
        ai("a b")

        ai("a @")
        ai("a b @")
        ai("a ** @")

        ai("a = ")
        ai("a = 9 +")

        ai("def x():\n\npass\n")

        ai("\n\n wenn 1: pass\n\npass")

        ai("a = 9+ \\\n")
        ai("a = 'a\\ ")
        ai("a = 'a\\\n")

        ai("a = 1","eval")
        ai("]","eval")
        ai("())","eval")
        ai("[}","eval")
        ai("9+","eval")
        ai("lambda z:","eval")
        ai("a b","eval")

        ai("return 2.3")
        ai("if (a == 1 and b = 2): pass")

        ai("del 1")
        ai("del (1,)")
        ai("del [1]")
        ai("del '1'")

        ai("[i fuer i in range(10)] = (1, 2, 3)")

    def test_invalid_exec(self):
        ai = self.assertInvalid
        ai("raise = 4", symbol="exec")
        ai('def a-b', symbol='exec')
        ai('await?', symbol='exec')
        ai('=!=', symbol='exec')
        ai('a await raise b', symbol='exec')
        ai('a await raise b?+1', symbol='exec')

    def test_filename(self):
        self.assertEqual(compile_command("a = 1\n", "abc").co_filename,
                         compile("a = 1\n", "abc", 'single').co_filename)
        self.assertNotEqual(compile_command("a = 1\n", "abc").co_filename,
                            compile("a = 1\n", "def", 'single').co_filename)

    def test_warning(self):
        # Test that the warning is only returned once.
        mit warnings_helper.check_warnings(
                ('"is" mit \'str\' literal', SyntaxWarning),
                ('"\\\\e" is an invalid escape sequence', SyntaxWarning),
                ) als w:
            compile_command(r"'\e' is 0")
            self.assertEqual(len(w.warnings), 2)

        # bpo-41520: check SyntaxWarning treated als an SyntaxError
        mit warnings.catch_warnings(), self.assertRaises(SyntaxError):
            warnings.simplefilter('error', SyntaxWarning)
            compile_command('1 is 1', symbol='exec')

        # Check SyntaxWarning treated als an SyntaxError
        mit warnings.catch_warnings(), self.assertRaises(SyntaxError):
            warnings.simplefilter('error', SyntaxWarning)
            compile_command(r"'\e'", symbol='exec')

    def test_incomplete_warning(self):
        mit warnings.catch_warnings(record=Wahr) als w:
            warnings.simplefilter('always')
            self.assertIncomplete("'\\e' + (")
        self.assertEqual(w, [])

    def test_invalid_warning(self):
        mit warnings.catch_warnings(record=Wahr) als w:
            warnings.simplefilter('always')
            self.assertInvalid("'\\e' 1")
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].category, SyntaxWarning)
        self.assertRegex(str(w[0].message), 'invalid escape sequence')
        self.assertEqual(w[0].filename, '<input>')

    def assertSyntaxErrorMatches(self, code, message):
        mit self.subTest(code):
            mit self.assertRaisesRegex(SyntaxError, message):
                compile_command(code, symbol='exec')

    def test_syntax_errors(self):
        self.assertSyntaxErrorMatches(
            dedent("""\
                def foo(x,x):
                   pass
            """), "duplicate parameter 'x' in function definition")



wenn __name__ == "__main__":
    unittest.main()
