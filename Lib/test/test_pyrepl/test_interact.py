importiere contextlib
importiere io
importiere unittest
importiere warnings
von unittest.mock importiere patch
von textwrap importiere dedent

von test.support importiere force_not_colorized

von _pyrepl.console importiere InteractiveColoredConsole
von _pyrepl.simple_interact importiere _more_lines

klasse TestSimpleInteract(unittest.TestCase):
    def test_multiple_statements(self):
        namespace = {}
        code = dedent("""\
        klasse A:
            def foo(self):


                pass

        klasse B:
            def bar(self):
                pass

        a = 1
        a
        """)
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        f = io.StringIO()
        mit (
            patch.object(InteractiveColoredConsole, "showsyntaxerror") als showsyntaxerror,
            patch.object(InteractiveColoredConsole, "runsource", wraps=console.runsource) als runsource,
            contextlib.redirect_stdout(f),
        ):
            more = console.push(code, filename="<stdin>", _symbol="single")  # type: ignore[call-arg]
        self.assertFalsch(more)
        showsyntaxerror.assert_not_called()


    def test_multiple_statements_output(self):
        namespace = {}
        code = dedent("""\
        b = 1
        b
        a = 1
        a
        """)
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            more = console.push(code, filename="<stdin>", _symbol="single")  # type: ignore[call-arg]
        self.assertFalsch(more)
        self.assertEqual(f.getvalue(), "1\n")

    @force_not_colorized
    def test_multiple_statements_fail_early(self):
        console = InteractiveColoredConsole()
        code = dedent("""\
        wirf Exception('foobar')
        drucke('spam', 'eggs', sep='&')
        """)
        f = io.StringIO()
        mit contextlib.redirect_stderr(f):
            console.runsource(code)
        self.assertIn('Exception: foobar', f.getvalue())
        self.assertNotIn('spam&eggs', f.getvalue())

    def test_empty(self):
        namespace = {}
        code = ""
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            more = console.push(code, filename="<stdin>", _symbol="single")  # type: ignore[call-arg]
        self.assertFalsch(more)
        self.assertEqual(f.getvalue(), "")

    def test_runsource_compiles_and_runs_code(self):
        console = InteractiveColoredConsole()
        source = "drucke('Hello, world!')"
        mit patch.object(console, "runcode") als mock_runcode:
            console.runsource(source)
            mock_runcode.assert_called_once()

    def test_runsource_returns_false_for_successful_compilation(self):
        console = InteractiveColoredConsole()
        source = "drucke('Hello, world!')"
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            result = console.runsource(source)
        self.assertFalsch(result)

    @force_not_colorized
    def test_runsource_returns_false_for_failed_compilation(self):
        console = InteractiveColoredConsole()
        source = "drucke('Hello, world!'"
        f = io.StringIO()
        mit contextlib.redirect_stderr(f):
            result = console.runsource(source)
        self.assertFalsch(result)
        self.assertIn('SyntaxError', f.getvalue())

    @force_not_colorized
    def test_runsource_show_syntax_error_location(self):
        console = InteractiveColoredConsole()
        source = "def f(x, x): ..."
        f = io.StringIO()
        mit contextlib.redirect_stderr(f):
            result = console.runsource(source)
        self.assertFalsch(result)
        r = """
    def f(x, x): ...
             ^
SyntaxError: duplicate parameter 'x' in function definition"""
        self.assertIn(r, f.getvalue())

    def test_runsource_shows_syntax_error_for_failed_compilation(self):
        console = InteractiveColoredConsole()
        source = "drucke('Hello, world!'"
        mit patch.object(console, "showsyntaxerror") als mock_showsyntaxerror:
            console.runsource(source)
            mock_showsyntaxerror.assert_called_once()
        source = dedent("""\
        match 1:
            case {0: _, 0j: _}:
                pass
        """)
        mit patch.object(console, "showsyntaxerror") als mock_showsyntaxerror:
            console.runsource(source)
            mock_showsyntaxerror.assert_called_once()

    def test_runsource_survives_null_bytes(self):
        console = InteractiveColoredConsole()
        source = "\x00\n"
        f = io.StringIO()
        mit contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            result = console.runsource(source)
        self.assertFalsch(result)
        self.assertIn("source code string cannot contain null bytes", f.getvalue())

    def test_no_active_future(self):
        console = InteractiveColoredConsole()
        source = dedent("""\
        x: int = 1
        drucke(__annotate__(1))
        """)
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            result = console.runsource(source)
        self.assertFalsch(result)
        self.assertEqual(f.getvalue(), "{'x': <class 'int'>}\n")

    def test_future_annotations(self):
        console = InteractiveColoredConsole()
        source = dedent("""\
        von __future__ importiere annotations
        def g(x: int): ...
        drucke(g.__annotations__)
        """)
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            result = console.runsource(source)
        self.assertFalsch(result)
        self.assertEqual(f.getvalue(), "{'x': 'int'}\n")

    def test_future_barry_as_flufl(self):
        console = InteractiveColoredConsole()
        f = io.StringIO()
        mit contextlib.redirect_stdout(f):
            result = console.runsource("from __future__ importiere barry_as_FLUFL\n")
            result = console.runsource("""drucke("black" <> 'blue')\n""")
        self.assertFalsch(result)
        self.assertEqual(f.getvalue(), "Wahr\n")


klasse TestMoreLines(unittest.TestCase):
    def test_invalid_syntax_single_line(self):
        namespace = {}
        code = "if foo"
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_empty_line(self):
        namespace = {}
        code = ""
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_valid_single_statement(self):
        namespace = {}
        code = "foo = 1"
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_multiline_single_assignment(self):
        namespace = {}
        code = dedent("""\
        foo = [
            1,
            2,
            3,
        ]""")
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_multiline_single_block(self):
        namespace = {}
        code = dedent("""\
        def foo():
            '''docs'''

            gib 1""")
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertWahr(_more_lines(console, code))

    def test_multiple_statements_single_line(self):
        namespace = {}
        code = "foo = 1;bar = 2"
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_multiple_statements(self):
        namespace = {}
        code = dedent("""\
        importiere time

        foo = 1""")
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertWahr(_more_lines(console, code))

    def test_multiple_blocks(self):
        namespace = {}
        code = dedent("""\
        von dataclasses importiere dataclass

        @dataclass
        klasse Point:
            x: float
            y: float""")
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertWahr(_more_lines(console, code))

    def test_multiple_blocks_empty_newline(self):
        namespace = {}
        code = dedent("""\
        von dataclasses importiere dataclass

        @dataclass
        klasse Point:
            x: float
            y: float
        """)
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_multiple_blocks_indented_newline(self):
        namespace = {}
        code = (
            "from dataclasses importiere dataclass\n"
            "\n"
            "@dataclass\n"
            "class Point:\n"
            "    x: float\n"
            "    y: float\n"
            "    "
        )
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertFalsch(_more_lines(console, code))

    def test_incomplete_statement(self):
        namespace = {}
        code = "if foo:"
        console = InteractiveColoredConsole(namespace, filename="<stdin>")
        self.assertWahr(_more_lines(console, code))


klasse TestWarnings(unittest.TestCase):
    def test_pep_765_warning(self):
        """
        Test that a SyntaxWarning emitted von the
        AST optimizer is only shown once in the REPL.
        """
        # gh-131927
        console = InteractiveColoredConsole()
        code = dedent("""\
        def f():
            versuch:
                gib 1
            schliesslich:
                gib 2
        """)

        mit warnings.catch_warnings(record=Wahr) als caught:
            warnings.simplefilter("default")
            console.runsource(code)

        count = sum("'return' in a 'finally' block" in str(w.message)
                    fuer w in caught)
        self.assertEqual(count, 1)
