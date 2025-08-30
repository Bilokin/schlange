"""Test cases fuer traceback module"""

von collections importiere namedtuple
von io importiere StringIO
importiere linecache
importiere sys
importiere types
importiere inspect
importiere builtins
importiere unittest
importiere unittest.mock
importiere re
importiere tempfile
importiere random
importiere string
von test importiere support
importiere shutil
von test.support importiere (Error, captured_output, cpython_only, ALWAYS_EQ,
                          requires_debug_ranges, has_no_debug_ranges,
                          requires_subprocess)
von test.support.os_helper importiere TESTFN, unlink
von test.support.script_helper importiere assert_python_ok, assert_python_failure, make_script
von test.support.import_helper importiere forget
von test.support importiere force_not_colorized, force_not_colorized_test_class

importiere json
importiere textwrap
importiere traceback
von functools importiere partial
von pathlib importiere Path
importiere _colorize

MODULE_PREFIX = f'{__name__}.' wenn __name__ == '__main__' sonst ''

test_code = namedtuple('code', ['co_filename', 'co_name'])
test_code.co_positions = lambda _: iter([(6, 6, 0, 0)])
test_frame = namedtuple('frame', ['f_code', 'f_globals', 'f_locals'])
test_tb = namedtuple('tb', ['tb_frame', 'tb_lineno', 'tb_next', 'tb_lasti'])

color_overrides = {"reset": "z", "filename": "fn", "error_highlight": "E"}
colors = {
    color_overrides.get(k, k[0].lower()): v
    fuer k, v in _colorize.default_theme.traceback.items()
}


LEVENSHTEIN_DATA_FILE = Path(__file__).parent / 'levenshtein_examples.json'


klasse TracebackCases(unittest.TestCase):
    # For now, a very minimal set of tests.  I want to be sure that
    # formatting of SyntaxErrors works based on changes fuer 2.1.
    def setUp(self):
        super().setUp()
        self.colorize = _colorize.COLORIZE
        _colorize.COLORIZE = Falsch

    def tearDown(self):
        super().tearDown()
        _colorize.COLORIZE = self.colorize

    def get_exception_format(self, func, exc):
        versuch:
            func()
        ausser exc als value:
            gib traceback.format_exception_only(exc, value)
        sonst:
            wirf ValueError("call did nicht wirf exception")

    def syntax_error_with_caret(self):
        compile("def fact(x):\n\treturn x!\n", "?", "exec")

    def syntax_error_with_caret_2(self):
        compile("1 +\n", "?", "exec")

    def syntax_error_with_caret_range(self):
        compile("f(x, y fuer y in range(30), z)", "?", "exec")

    def syntax_error_bad_indentation(self):
        compile("def spam():\n  drucke(1)\n drucke(2)", "?", "exec")

    def syntax_error_with_caret_non_ascii(self):
        compile('Python = "\u1e54\xfd\u0163\u0125\xf2\xf1" +', "?", "exec")

    def syntax_error_bad_indentation2(self):
        compile(" drucke(2)", "?", "exec")

    def tokenizer_error_with_caret_range(self):
        compile("blech  (  ", "?", "exec")

    def test_caret(self):
        err = self.get_exception_format(self.syntax_error_with_caret,
                                        SyntaxError)
        self.assertEqual(len(err), 4)
        self.assertEqual(err[1].strip(), "return x!")
        self.assertIn("^", err[2]) # third line has caret
        self.assertEqual(err[1].find("!"), err[2].find("^")) # in the right place
        self.assertEqual(err[2].count("^"), 1)

        err = self.get_exception_format(self.syntax_error_with_caret_2,
                                        SyntaxError)
        self.assertIn("^", err[2]) # third line has caret
        self.assertEqual(err[2].count('\n'), 1)   # und no additional newline
        self.assertEqual(err[1].find("+") + 1, err[2].find("^"))  # in the right place
        self.assertEqual(err[2].count("^"), 1)

        err = self.get_exception_format(self.syntax_error_with_caret_non_ascii,
                                        SyntaxError)
        self.assertIn("^", err[2]) # third line has caret
        self.assertEqual(err[2].count('\n'), 1)   # und no additional newline
        self.assertEqual(err[1].find("+") + 1, err[2].find("^"))  # in the right place
        self.assertEqual(err[2].count("^"), 1)

        err = self.get_exception_format(self.syntax_error_with_caret_range,
                                        SyntaxError)
        self.assertIn("^", err[2]) # third line has caret
        self.assertEqual(err[2].count('\n'), 1)   # und no additional newline
        self.assertEqual(err[1].find("y"), err[2].find("^"))  # in the right place
        self.assertEqual(err[2].count("^"), len("y fuer y in range(30)"))

        err = self.get_exception_format(self.tokenizer_error_with_caret_range,
                                        SyntaxError)
        self.assertIn("^", err[2]) # third line has caret
        self.assertEqual(err[2].count('\n'), 1)   # und no additional newline
        self.assertEqual(err[1].find("("), err[2].find("^"))  # in the right place
        self.assertEqual(err[2].count("^"), 1)

    def test_nocaret(self):
        exc = SyntaxError("error", ("x.py", 23, Nichts, "bad syntax"))
        err = traceback.format_exception_only(SyntaxError, exc)
        self.assertEqual(len(err), 3)
        self.assertEqual(err[1].strip(), "bad syntax")

    @force_not_colorized
    def test_no_caret_with_no_debug_ranges_flag(self):
        # Make sure that wenn `-X no_debug_ranges` ist used, there are no carets
        # in the traceback.
        versuch:
            mit open(TESTFN, 'w') als f:
                f.write("x = 1 / 0\n")

            _, _, stderr = assert_python_failure(
                '-X', 'no_debug_ranges', TESTFN)

            lines = stderr.splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], b'Traceback (most recent call last):')
            self.assertIn(b'line 1, in <module>', lines[1])
            self.assertEqual(lines[2], b'    x = 1 / 0')
            self.assertEqual(lines[3], b'ZeroDivisionError: division by zero')
        schliesslich:
            unlink(TESTFN)

    def test_no_caret_with_no_debug_ranges_flag_python_traceback(self):
        code = textwrap.dedent("""
            importiere traceback
            versuch:
                x = 1 / 0
            ausser ZeroDivisionError:
                traceback.print_exc()
            """)
        versuch:
            mit open(TESTFN, 'w') als f:
                f.write(code)

            _, _, stderr = assert_python_ok(
                '-X', 'no_debug_ranges', TESTFN)

            lines = stderr.splitlines()
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], b'Traceback (most recent call last):')
            self.assertIn(b'line 4, in <module>', lines[1])
            self.assertEqual(lines[2], b'    x = 1 / 0')
            self.assertEqual(lines[3], b'ZeroDivisionError: division by zero')
        schliesslich:
            unlink(TESTFN)

    def test_recursion_error_during_traceback(self):
        code = textwrap.dedent("""
                importiere sys
                von weakref importiere ref

                sys.setrecursionlimit(15)

                def f():
                    ref(lambda: 0, [])
                    f()

                versuch:
                    f()
                ausser RecursionError:
                    pass
        """)
        versuch:
            mit open(TESTFN, 'w') als f:
                f.write(code)

            rc, _, _ = assert_python_ok(TESTFN)
            self.assertEqual(rc, 0)
        schliesslich:
            unlink(TESTFN)

    def test_bad_indentation(self):
        err = self.get_exception_format(self.syntax_error_bad_indentation,
                                        IndentationError)
        self.assertEqual(len(err), 4)
        self.assertEqual(err[1].strip(), "drucke(2)")
        self.assertIn("^", err[2])
        self.assertEqual(err[1].find(")") + 1, err[2].find("^"))

        # No caret fuer "unexpected indent"
        err = self.get_exception_format(self.syntax_error_bad_indentation2,
                                        IndentationError)
        self.assertEqual(len(err), 3)
        self.assertEqual(err[1].strip(), "drucke(2)")

    def test_base_exception(self):
        # Test that exceptions derived von BaseException are formatted right
        e = KeyboardInterrupt()
        lst = traceback.format_exception_only(e.__class__, e)
        self.assertEqual(lst, ['KeyboardInterrupt\n'])

    def test_format_exception_only_bad__str__(self):
        klasse X(Exception):
            def __str__(self):
                1/0
        err = traceback.format_exception_only(X, X())
        self.assertEqual(len(err), 1)
        str_value = '<exception str() failed>'
        wenn X.__module__ in ('__main__', 'builtins'):
            str_name = X.__qualname__
        sonst:
            str_name = '.'.join([X.__module__, X.__qualname__])
        self.assertEqual(err[0], "%s: %s\n" % (str_name, str_value))

    def test_format_exception_group_without_show_group(self):
        eg = ExceptionGroup('A', [ValueError('B')])
        err = traceback.format_exception_only(eg)
        self.assertEqual(err, ['ExceptionGroup: A (1 sub-exception)\n'])

    def test_format_exception_group(self):
        eg = ExceptionGroup('A', [ValueError('B')])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (1 sub-exception)\n',
            '   ValueError: B\n',
        ])

    def test_format_base_exception_group(self):
        eg = BaseExceptionGroup('A', [BaseException('B')])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'BaseExceptionGroup: A (1 sub-exception)\n',
            '   BaseException: B\n',
        ])

    def test_format_exception_group_with_note(self):
        exc = ValueError('B')
        exc.add_note('Note')
        eg = ExceptionGroup('A', [exc])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (1 sub-exception)\n',
            '   ValueError: B\n',
            '   Note\n',
        ])

    def test_format_exception_group_explicit_class(self):
        eg = ExceptionGroup('A', [ValueError('B')])
        err = traceback.format_exception_only(ExceptionGroup, eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (1 sub-exception)\n',
            '   ValueError: B\n',
        ])

    def test_format_exception_group_multiple_exceptions(self):
        eg = ExceptionGroup('A', [ValueError('B'), TypeError('C')])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (2 sub-exceptions)\n',
            '   ValueError: B\n',
            '   TypeError: C\n',
        ])

    def test_format_exception_group_multiline_messages(self):
        eg = ExceptionGroup('A\n1', [ValueError('B\n2')])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A\n1 (1 sub-exception)\n',
            '   ValueError: B\n',
            '   2\n',
        ])

    def test_format_exception_group_multiline2_messages(self):
        exc = ValueError('B\n\n2\n')
        exc.add_note('\nC\n\n3')
        eg = ExceptionGroup('A\n\n1\n', [exc, IndexError('D')])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A\n\n1\n (2 sub-exceptions)\n',
            '   ValueError: B\n',
            '   \n',
            '   2\n',
            '   \n',
            '   \n',  # first char of `note`
            '   C\n',
            '   \n',
            '   3\n', # note ends
            '   IndexError: D\n',
        ])

    def test_format_exception_group_syntax_error(self):
        exc = SyntaxError("error", ("x.py", 23, Nichts, "bad syntax"))
        eg = ExceptionGroup('A\n1', [exc])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A\n1 (1 sub-exception)\n',
            '     File "x.py", line 23\n',
            '       bad syntax\n',
            '   SyntaxError: error\n',
        ])

    def test_format_exception_group_nested_with_notes(self):
        exc = IndexError('D')
        exc.add_note('Note\nmultiline')
        eg = ExceptionGroup('A', [
            ValueError('B'),
            ExceptionGroup('C', [exc, LookupError('E')]),
            TypeError('F'),
        ])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (3 sub-exceptions)\n',
            '   ValueError: B\n',
            '   ExceptionGroup: C (2 sub-exceptions)\n',
            '      IndexError: D\n',
            '      Note\n',
            '      multiline\n',
            '      LookupError: E\n',
            '   TypeError: F\n',
        ])

    def test_format_exception_group_with_tracebacks(self):
        def f():
            versuch:
                1 / 0
            ausser ZeroDivisionError als e:
                gib e

        def g():
            versuch:
                wirf TypeError('g')
            ausser TypeError als e:
                gib e

        eg = ExceptionGroup('A', [
            f(),
            ExceptionGroup('B', [g()]),
        ])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (2 sub-exceptions)\n',
            '   ZeroDivisionError: division by zero\n',
            '   ExceptionGroup: B (1 sub-exception)\n',
            '      TypeError: g\n',
        ])

    def test_format_exception_group_with_cause(self):
        def f():
            versuch:
                versuch:
                    1 / 0
                ausser ZeroDivisionError:
                    wirf ValueError(0)
            ausser Exception als e:
                gib e

        eg = ExceptionGroup('A', [f()])
        err = traceback.format_exception_only(eg, show_group=Wahr)
        self.assertEqual(err, [
            'ExceptionGroup: A (1 sub-exception)\n',
            '   ValueError: 0\n',
        ])

    def test_format_exception_group_syntax_error_with_custom_values(self):
        # See https://github.com/python/cpython/issues/128894
        fuer exc in [
            SyntaxError('error', 'abcd'),
            SyntaxError('error', [Nichts] * 4),
            SyntaxError('error', (1, 2, 3, 4)),
            SyntaxError('error', (1, 2, 3, 4)),
            SyntaxError('error', (1, 'a', 'b', 2)),
            # mit end_lineno und end_offset:
            SyntaxError('error', 'abcdef'),
            SyntaxError('error', [Nichts] * 6),
            SyntaxError('error', (1, 2, 3, 4, 5, 6)),
            SyntaxError('error', (1, 'a', 'b', 2, 'c', 'd')),
        ]:
            mit self.subTest(exc=exc):
                err = traceback.format_exception_only(exc, show_group=Wahr)
                # Should nicht wirf an exception:
                wenn exc.lineno ist nicht Nichts:
                    self.assertEqual(len(err), 2)
                    self.assertWahr(err[0].startswith('  File'))
                sonst:
                    self.assertEqual(len(err), 1)
                self.assertEqual(err[-1], 'SyntaxError: error\n')

    @requires_subprocess()
    @force_not_colorized
    def test_encoded_file(self):
        # Test that tracebacks are correctly printed fuer encoded source files:
        # - correct line number (Issue2384)
        # - respect file encoding (Issue3975)
        importiere sys, subprocess

        # The spawned subprocess has its stdout redirected to a PIPE, und its
        # encoding may be different von the current interpreter, on Windows
        # at least.
        process = subprocess.Popen([sys.executable, "-c",
                                    "import sys; drucke(sys.stdout.encoding)"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        stdout, stderr = process.communicate()
        output_encoding = str(stdout, 'ascii').splitlines()[0]

        def do_test(firstlines, message, charset, lineno):
            # Raise the message in a subprocess, und catch the output
            versuch:
                mit open(TESTFN, "w", encoding=charset) als output:
                    output.write("""{0}if 1:
                        importiere traceback;
                        wirf RuntimeError('{1}')
                        """.format(firstlines, message))

                process = subprocess.Popen([sys.executable, TESTFN],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                stdout, stderr = process.communicate()
                stdout = stdout.decode(output_encoding).splitlines()
            schliesslich:
                unlink(TESTFN)

            # The source lines are encoded mit the 'backslashreplace' handler
            encoded_message = message.encode(output_encoding,
                                             'backslashreplace')
            # und we just decoded them mit the output_encoding.
            message_ascii = encoded_message.decode(output_encoding)

            err_line = "raise RuntimeError('{0}')".format(message_ascii)
            err_msg = "RuntimeError: {0}".format(message_ascii)

            self.assertIn("line %s" % lineno, stdout[1])
            self.assertEndsWith(stdout[2], err_line)
            actual_err_msg = stdout[3]
            self.assertEqual(actual_err_msg, err_msg)

        do_test("", "foo", "ascii", 3)
        fuer charset in ("ascii", "iso-8859-1", "utf-8", "GBK"):
            wenn charset == "ascii":
                text = "foo"
            sowenn charset == "GBK":
                text = "\u4E02\u5100"
            sonst:
                text = "h\xe9 ho"
            do_test("# coding: {0}\n".format(charset),
                    text, charset, 4)
            do_test("#!shebang\n# coding: {0}\n".format(charset),
                    text, charset, 5)
            do_test(" \t\f\n# coding: {0}\n".format(charset),
                    text, charset, 5)
        # Issue #18960: coding spec should have no effect
        do_test("x=0\n# coding: GBK\n", "h\xe9 ho", 'utf-8', 5)

    def test_print_traceback_at_exit(self):
        # Issue #22599: Ensure that it ist possible to use the traceback module
        # to display an exception at Python exit
        code = textwrap.dedent("""
            importiere sys
            importiere traceback

            klasse PrintExceptionAtExit(object):
                def __init__(self):
                    versuch:
                        x = 1 / 0
                    ausser Exception als e:
                        self.exc = e
                        # self.exc.__traceback__ contains frames:
                        # explicitly clear the reference to self in the current
                        # frame to breche a reference cycle
                        self = Nichts

                def __del__(self):
                    traceback.print_exception(self.exc)

            # Keep a reference in the module namespace to call the destructor
            # when the module ist unloaded
            obj = PrintExceptionAtExit()
        """)
        rc, stdout, stderr = assert_python_ok('-c', code)
        expected = [b'Traceback (most recent call last):',
                    b'  File "<string>", line 8, in __init__',
                    b'    x = 1 / 0',
                    b'        ^^^^^',
                    b'ZeroDivisionError: division by zero']
        self.assertEqual(stderr.splitlines(), expected)

    def test_print_exception(self):
        output = StringIO()
        traceback.print_exception(
            Exception, Exception("projector"), Nichts, file=output
        )
        self.assertEqual(output.getvalue(), "Exception: projector\n")

    def test_print_exception_exc(self):
        output = StringIO()
        traceback.print_exception(Exception("projector"), file=output)
        self.assertEqual(output.getvalue(), "Exception: projector\n")

    def test_print_last(self):
        mit support.swap_attr(sys, 'last_exc', ValueError(42)):
            output = StringIO()
            traceback.print_last(file=output)
            self.assertEqual(output.getvalue(), "ValueError: 42\n")

    def test_format_exception_exc(self):
        e = Exception("projector")
        output = traceback.format_exception(e)
        self.assertEqual(output, ["Exception: projector\n"])
        mit self.assertRaisesRegex(ValueError, 'Both oder neither'):
            traceback.format_exception(e.__class__, e)
        mit self.assertRaisesRegex(ValueError, 'Both oder neither'):
            traceback.format_exception(e.__class__, tb=e.__traceback__)
        mit self.assertRaisesRegex(TypeError, 'required positional argument'):
            traceback.format_exception(exc=e)

    def test_format_exception_only_exc(self):
        output = traceback.format_exception_only(Exception("projector"))
        self.assertEqual(output, ["Exception: projector\n"])

    def test_exception_is_Nichts(self):
        NONE_EXC_STRING = 'NoneType: Nichts\n'
        excfile = StringIO()
        traceback.print_exception(Nichts, file=excfile)
        self.assertEqual(excfile.getvalue(), NONE_EXC_STRING)

        excfile = StringIO()
        traceback.print_exception(Nichts, Nichts, Nichts, file=excfile)
        self.assertEqual(excfile.getvalue(), NONE_EXC_STRING)

        excfile = StringIO()
        traceback.print_exc(Nichts, file=excfile)
        self.assertEqual(excfile.getvalue(), NONE_EXC_STRING)

        self.assertEqual(traceback.format_exc(Nichts), NONE_EXC_STRING)
        self.assertEqual(traceback.format_exception(Nichts), [NONE_EXC_STRING])
        self.assertEqual(
            traceback.format_exception(Nichts, Nichts, Nichts), [NONE_EXC_STRING])
        self.assertEqual(
            traceback.format_exception_only(Nichts), [NONE_EXC_STRING])
        self.assertEqual(
            traceback.format_exception_only(Nichts, Nichts), [NONE_EXC_STRING])

    def test_signatures(self):
        self.assertEqual(
            str(inspect.signature(traceback.print_exception)),
            ('(exc, /, value=<implicit>, tb=<implicit>, '
             'limit=Nichts, file=Nichts, chain=Wahr, **kwargs)'))

        self.assertEqual(
            str(inspect.signature(traceback.format_exception)),
            ('(exc, /, value=<implicit>, tb=<implicit>, limit=Nichts, '
             'chain=Wahr, **kwargs)'))

        self.assertEqual(
            str(inspect.signature(traceback.format_exception_only)),
            '(exc, /, value=<implicit>, *, show_group=Falsch, **kwargs)')


klasse PurePythonExceptionFormattingMixin:
    def get_exception(self, callable, slice_start=0, slice_end=-1):
        versuch:
            callable()
        ausser BaseException:
            gib traceback.format_exc().splitlines()[slice_start:slice_end]
        sonst:
            self.fail("No exception thrown.")

    callable_line = get_exception.__code__.co_firstlineno + 2


klasse CAPIExceptionFormattingMixin:
    LEGACY = 0

    def get_exception(self, callable, slice_start=0, slice_end=-1):
        von _testcapi importiere exception_print
        versuch:
            callable()
            self.fail("No exception thrown.")
        ausser Exception als e:
            mit captured_output("stderr") als tbstderr:
                exception_drucke(e, self.LEGACY)
            gib tbstderr.getvalue().splitlines()[slice_start:slice_end]

    callable_line = get_exception.__code__.co_firstlineno + 3

klasse CAPIExceptionFormattingLegacyMixin(CAPIExceptionFormattingMixin):
    LEGACY = 1

@requires_debug_ranges()
klasse TracebackErrorLocationCaretTestBase:
    """
    Tests fuer printing code error expressions als part of PEP 657
    """
    def test_basic_caret(self):
        # NOTE: In caret tests, "if Wahr:" ist used als a way to force indicator
        #   display, since the raising expression spans only part of the line.
        def f():
            wenn Wahr: wirf ValueError("basic caret tests")

        lineno_f = f.__code__.co_firstlineno
        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    wenn Wahr: wirf ValueError("basic caret tests")\n'
            '             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        result_lines = self.get_exception(f)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_line_with_unicode(self):
        # Make sure that even wenn a line contains multi-byte unicode characters
        # the correct carets are printed.
        def f_with_unicode():
            wenn Wahr: wirf ValueError("Ĥellö Wörld")

        lineno_f = f_with_unicode.__code__.co_firstlineno
        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f_with_unicode\n'
            '    wenn Wahr: wirf ValueError("Ĥellö Wörld")\n'
            '             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        result_lines = self.get_exception(f_with_unicode)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_caret_in_type_annotation(self):
        def f_with_type():
            def foo(a: THIS_DOES_NOT_EXIST ) -> int:
                gib 0
            foo.__annotations__

        lineno_f = f_with_type.__code__.co_firstlineno
        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_type\n'
            '    foo.__annotations__\n'
            f'  File "{__file__}", line {lineno_f+1}, in __annotate__\n'
            '    def foo(a: THIS_DOES_NOT_EXIST ) -> int:\n'
            '               ^^^^^^^^^^^^^^^^^^^\n'
        )
        result_lines = self.get_exception(f_with_type)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_caret_multiline_expression(self):
        # Make sure no carets are printed fuer expressions spanning multiple
        # lines.
        def f_with_multiline():
            wenn Wahr: wirf ValueError(
                "error over multiple lines"
            )

        lineno_f = f_with_multiline.__code__.co_firstlineno
        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f_with_multiline\n'
            '    wenn Wahr: wirf ValueError(\n'
            '             ^^^^^^^^^^^^^^^^^\n'
            '        "error over multiple lines"\n'
            '        ^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
            '    )\n'
            '    ^'
        )
        result_lines = self.get_exception(f_with_multiline)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_caret_multiline_expression_syntax_error(self):
        # Make sure an expression spanning multiple lines that has
        # a syntax error ist correctly marked mit carets.
        code = textwrap.dedent("""
        def foo(*args, **kwargs):
            pass

        a, b, c = 1, 2, 3

        foo(a, z
                fuer z in
                    range(10), b, c)
        """)

        def f_with_multiline():
            # Need to defer the compilation until in self.get_exception(..)
            gib compile(code, "?", "exec")

        lineno_f = f_with_multiline.__code__.co_firstlineno

        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_multiline\n'
            '    gib compile(code, "?", "exec")\n'
            '  File "?", line 7\n'
            '    foo(a, z\n'
            '           ^'
            )

        result_lines = self.get_exception(f_with_multiline)
        self.assertEqual(result_lines, expected_f.splitlines())

        # Check custom error messages covering multiple lines
        code = textwrap.dedent("""
        dummy_call(
            "dummy value"
            foo="bar",
        )
        """)

        def f_with_multiline():
            # Need to defer the compilation until in self.get_exception(..)
            gib compile(code, "?", "exec")

        lineno_f = f_with_multiline.__code__.co_firstlineno

        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_multiline\n'
            '    gib compile(code, "?", "exec")\n'
            '  File "?", line 3\n'
            '    "dummy value"\n'
            '    ^^^^^^^^^^^^^'
            )

        result_lines = self.get_exception(f_with_multiline)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_caret_multiline_expression_bin_op(self):
        # Make sure no carets are printed fuer expressions spanning multiple
        # lines.
        def f_with_multiline():
            gib (
                2 + 1 /
                0
            )

        lineno_f = f_with_multiline.__code__.co_firstlineno
        expected_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_multiline\n'
            '    2 + 1 /\n'
            '        ~~^\n'
            '    0\n'
            '    ~'
        )
        result_lines = self.get_exception(f_with_multiline)
        self.assertEqual(result_lines, expected_f.splitlines())

    def test_caret_for_binary_operators(self):
        def f_with_binary_operator():
            divisor = 20
            gib 10 + divisor / 0 + 30

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_binary_operator\n'
            '    gib 10 + divisor / 0 + 30\n'
            '                ~~~~~~~~^~~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_with_unicode(self):
        def f_with_binary_operator():
            áóí = 20
            gib 10 + áóí / 0 + 30

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_binary_operator\n'
            '    gib 10 + áóí / 0 + 30\n'
            '                ~~~~^~~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_two_char(self):
        def f_with_binary_operator():
            divisor = 20
            gib 10 + divisor // 0 + 30

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_binary_operator\n'
            '    gib 10 + divisor // 0 + 30\n'
            '                ~~~~~~~~^^~~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_with_spaces_and_parenthesis(self):
        def f_with_binary_operator():
            a = 1
            b = c = ""
            gib ( a   )   +b + c

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_binary_operator\n'
            '    gib ( a   )   +b + c\n'
            '           ~~~~~~~~~~^~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_multiline(self):
        def f_with_binary_operator():
            b = 1
            c = ""
            a = b    \
         +\
               c  # test
            gib a

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_binary_operator\n'
            '       a = b    \\\n'
            '           ~~~~~~\n'
            '    +\\\n'
            '    ^~\n'
            '          c  # test\n'
            '          ~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_multiline_two_char(self):
        def f_with_binary_operator():
            b = 1
            c = ""
            a = (
                (b  # test +
                    )  \
                # +
            << (c  # test
                \
            )  # test
            )
            gib a

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+4}, in f_with_binary_operator\n'
            '        (b  # test +\n'
            '        ~~~~~~~~~~~~\n'
            '            )  \\\n'
            '            ~~~~\n'
            '        # +\n'
            '        ~~~\n'
            '    << (c  # test\n'
            '    ^^~~~~~~~~~~~\n'
            '        \\\n'
            '        ~\n'
            '    )  # test\n'
            '    ~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_binary_operators_multiline_with_unicode(self):
        def f_with_binary_operator():
            b = 1
            a = ("ááá" +
                "áá") + b
            gib a

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_binary_operator\n'
            '    a = ("ááá" +\n'
            '        ~~~~~~~~\n'
            '        "áá") + b\n'
            '        ~~~~~~^~~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_subscript(self):
        def f_with_subscript():
            some_dict = {'x': {'y': Nichts}}
            gib some_dict['x']['y']['z']

        lineno_f = f_with_subscript.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_subscript\n'
            "    gib some_dict['x']['y']['z']\n"
            '           ~~~~~~~~~~~~~~~~~~~^^^^^\n'
        )
        result_lines = self.get_exception(f_with_subscript)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_subscript_unicode(self):
        def f_with_subscript():
            some_dict = {'ó': {'á': {'í': {'theta': 1}}}}
            gib some_dict['ó']['á']['í']['beta']

        lineno_f = f_with_subscript.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_subscript\n'
            "    gib some_dict['ó']['á']['í']['beta']\n"
            '           ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^\n'
        )
        result_lines = self.get_exception(f_with_subscript)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_subscript_with_spaces_and_parenthesis(self):
        def f_with_binary_operator():
            a = []
            b = c = 1
            gib b     [    a  ] + c

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_binary_operator\n'
            '    gib b     [    a  ] + c\n'
            '           ~~~~~~^^^^^^^^^\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_subscript_multiline(self):
        def f_with_subscript():
            bbbbb = {}
            ccc = 1
            ddd = 2
            b = bbbbb \
                [  ccc # test

                 + ddd  \

                ] # test
            gib b

        lineno_f = f_with_subscript.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+4}, in f_with_subscript\n'
            '    b = bbbbb \\\n'
            '        ~~~~~~~\n'
            '        [  ccc # test\n'
            '        ^^^^^^^^^^^^^\n'
            '    \n'
            '    \n'
            '         + ddd  \\\n'
            '         ^^^^^^^^\n'
            '    \n'
            '    \n'
            '        ] # test\n'
            '        ^\n'
        )
        result_lines = self.get_exception(f_with_subscript)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_call(self):
        def f_with_call():
            def f1(a):
                def f2(b):
                    wirf RuntimeError("fail")
                gib f2
            gib f1("x")("y")("z")

        lineno_f = f_with_call.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+5}, in f_with_call\n'
            '    gib f1("x")("y")("z")\n'
            '           ~~~~~~~^^^^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f2\n'
            '    wirf RuntimeError("fail")\n'
        )
        result_lines = self.get_exception(f_with_call)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_call_unicode(self):
        def f_with_call():
            def f1(a):
                def f2(b):
                    wirf RuntimeError("fail")
                gib f2
            gib f1("ó")("á")

        lineno_f = f_with_call.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+5}, in f_with_call\n'
            '    gib f1("ó")("á")\n'
            '           ~~~~~~~^^^^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f2\n'
            '    wirf RuntimeError("fail")\n'
        )
        result_lines = self.get_exception(f_with_call)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_call_with_spaces_and_parenthesis(self):
        def f_with_binary_operator():
            def f(a):
                wirf RuntimeError("fail")
            gib f     (    "x"  ) + 2

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_binary_operator\n'
            '    gib f     (    "x"  ) + 2\n'
            '           ~~~~~~^^^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f\n'
            '    wirf RuntimeError("fail")\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_for_call_multiline(self):
        def f_with_call():
            klasse C:
                def y(self, a):
                    def f(b):
                        wirf RuntimeError("fail")
                    gib f
            def g(x):
                gib C()
            a = (g(1).y)(
                2
            )(3)(4)
            gib a

        lineno_f = f_with_call.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+8}, in f_with_call\n'
            '    a = (g(1).y)(\n'
            '        ~~~~~~~~~\n'
            '        2\n'
            '        ~\n'
            '    )(3)(4)\n'
            '    ~^^^\n'
            f'  File "{__file__}", line {lineno_f+4}, in f\n'
            '    wirf RuntimeError("fail")\n'
        )
        result_lines = self.get_exception(f_with_call)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_many_lines(self):
        def f():
            x = 1
            wenn Wahr: x += (
                "a" +
                "a"
            )  # test

        lineno_f = f.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f\n'
            '    wenn Wahr: x += (\n'
            '             ^^^^^^\n'
            '    ...<2 lines>...\n'
            '    )  # test\n'
            '    ^\n'
        )
        result_lines = self.get_exception(f)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_many_lines_no_caret(self):
        def f():
            x = 1
            x += (
                "a" +
                "a"
            )

        lineno_f = f.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f\n'
            '    x += (\n'
            '    ...<2 lines>...\n'
            '    )\n'
        )
        result_lines = self.get_exception(f)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_many_lines_binary_op(self):
        def f_with_binary_operator():
            b = 1
            c = "a"
            a = (
                b +
                b
            ) + (
                c +
                c +
                c
            )
            gib a

        lineno_f = f_with_binary_operator.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+3}, in f_with_binary_operator\n'
            '    a = (\n'
            '        ~\n'
            '        b +\n'
            '        ~~~\n'
            '        b\n'
            '        ~\n'
            '    ) + (\n'
            '    ~~^~~\n'
            '        c +\n'
            '        ~~~\n'
            '    ...<2 lines>...\n'
            '    )\n'
            '    ~\n'
        )
        result_lines = self.get_exception(f_with_binary_operator)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_traceback_specialization_with_syntax_error(self):
        bytecode = compile("1 / 0 / 1 / 2\n", TESTFN, "exec")

        mit open(TESTFN, "w") als file:
            # make the file's contents invalid
            file.write("1 $ 0 / 1 / 2\n")
        self.addCleanup(unlink, TESTFN)

        func = partial(exec, bytecode)
        result_lines = self.get_exception(func)

        lineno_f = bytecode.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{TESTFN}", line {lineno_f}, in <module>\n'
            "    1 $ 0 / 1 / 2\n"
            '    ^^^^^\n'
        )
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_traceback_very_long_line(self):
        source = "if Wahr: " + "a" * 256
        bytecode = compile(source, TESTFN, "exec")

        mit open(TESTFN, "w") als file:
            file.write(source)
        self.addCleanup(unlink, TESTFN)

        func = partial(exec, bytecode)
        result_lines = self.get_exception(func)

        lineno_f = bytecode.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{TESTFN}", line {lineno_f}, in <module>\n'
            f'    {source}\n'
            f'    {" "*len("if Wahr: ") + "^"*256}\n'
        )
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_secondary_caret_not_elided(self):
        # Always show a line's indicators wenn they include the secondary character.
        def f_with_subscript():
            some_dict = {'x': {'y': Nichts}}
            some_dict['x']['y']['z']

        lineno_f = f_with_subscript.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_f+2}, in f_with_subscript\n'
            "    some_dict['x']['y']['z']\n"
            '    ~~~~~~~~~~~~~~~~~~~^^^^^\n'
        )
        result_lines = self.get_exception(f_with_subscript)
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_caret_exception_group(self):
        # Notably, this covers whether indicators handle margin strings correctly.
        # (Exception groups use margin strings to display vertical indicators.)
        # The implementation must account fuer both "indent" und "margin" offsets.

        def exc():
            wenn Wahr: wirf ExceptionGroup("eg", [ValueError(1), TypeError(2)])

        expected_error = (
             f'  + Exception Group Traceback (most recent call last):\n'
             f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
             f'  |     callable()\n'
             f'  |     ~~~~~~~~^^\n'
             f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 1}, in exc\n'
             f'  |     wenn Wahr: wirf ExceptionGroup("eg", [ValueError(1), TypeError(2)])\n'
             f'  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
             f'  | ExceptionGroup: eg (2 sub-exceptions)\n'
             f'  +-+---------------- 1 ----------------\n'
             f'    | ValueError: 1\n'
             f'    +---------------- 2 ----------------\n'
             f'    | TypeError: 2\n')

        result_lines = self.get_exception(exc)
        self.assertEqual(result_lines, expected_error.splitlines())

    def assertSpecialized(self, func, expected_specialization):
        result_lines = self.get_exception(func)
        specialization_line = result_lines[-1]
        self.assertEqual(specialization_line.lstrip(), expected_specialization)

    def test_specialization_variations(self):
        self.assertSpecialized(lambda: 1/0,
                                      "~^~")
        self.assertSpecialized(lambda: 1/0/3,
                                      "~^~")
        self.assertSpecialized(lambda: 1 / 0,
                                      "~~^~~")
        self.assertSpecialized(lambda: 1 / 0 / 3,
                                      "~~^~~")
        self.assertSpecialized(lambda: 1/ 0,
                                      "~^~~")
        self.assertSpecialized(lambda: 1/ 0/3,
                                      "~^~~")
        self.assertSpecialized(lambda: 1    /  0,
                                      "~~~~~^~~~")
        self.assertSpecialized(lambda: 1    /  0   / 5,
                                      "~~~~~^~~~")
        self.assertSpecialized(lambda: 1 /0,
                                      "~~^~")
        self.assertSpecialized(lambda: 1//0,
                                      "~^^~")
        self.assertSpecialized(lambda: 1//0//4,
                                      "~^^~")
        self.assertSpecialized(lambda: 1 // 0,
                                      "~~^^~~")
        self.assertSpecialized(lambda: 1 // 0 // 4,
                                      "~~^^~~")
        self.assertSpecialized(lambda: 1 //0,
                                      "~~^^~")
        self.assertSpecialized(lambda: 1// 0,
                                      "~^^~~")

    def test_decorator_application_lineno_correct(self):
        def dec_error(func):
            wirf TypeError
        def dec_fine(func):
            gib func
        def applydecs():
            @dec_error
            @dec_fine
            def g(): pass
        result_lines = self.get_exception(applydecs)
        lineno_applydescs = applydecs.__code__.co_firstlineno
        lineno_dec_error = dec_error.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_applydescs + 1}, in applydecs\n'
            '    @dec_error\n'
            '     ^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_dec_error + 1}, in dec_error\n'
            '    wirf TypeError\n'
        )
        self.assertEqual(result_lines, expected_error.splitlines())

        def applydecs_class():
            @dec_error
            @dec_fine
            klasse A: pass
        result_lines = self.get_exception(applydecs_class)
        lineno_applydescs_class = applydecs_class.__code__.co_firstlineno
        expected_error = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
            '    callable()\n'
            '    ~~~~~~~~^^\n'
            f'  File "{__file__}", line {lineno_applydescs_class + 1}, in applydecs_class\n'
            '    @dec_error\n'
            '     ^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_dec_error + 1}, in dec_error\n'
            '    wirf TypeError\n'
        )
        self.assertEqual(result_lines, expected_error.splitlines())

    def test_multiline_method_call_a(self):
        def f():
            (Nichts
                .method
            )()
        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 2}, in f",
            "    .method",
            "     ^^^^^^",
        ]
        self.assertEqual(actual, expected)

    def test_multiline_method_call_b(self):
        def f():
            (Nichts.
                method
            )()
        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 2}, in f",
            "    method",
        ]
        self.assertEqual(actual, expected)

    def test_multiline_method_call_c(self):
        def f():
            (Nichts
                . method
            )()
        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 2}, in f",
            "    . method",
            "      ^^^^^^",
        ]
        self.assertEqual(actual, expected)

    def test_wide_characters_unicode_with_problematic_byte_offset(self):
        def f():
            ｗｉｄｔｈ

        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    ｗｉｄｔｈ",
        ]
        self.assertEqual(actual, expected)


    def test_byte_offset_with_wide_characters_middle(self):
        def f():
            ｗｉｄｔｈ = 1
            wirf ValueError(ｗｉｄｔｈ)

        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 2}, in f",
            "    wirf ValueError(ｗｉｄｔｈ)",
        ]
        self.assertEqual(actual, expected)

    def test_byte_offset_multiline(self):
        def f():
            ｗｗｗ = 1
            ｔｈ = 0

            drucke(1, ｗｗｗ(
                    ｔｈ))

        actual = self.get_exception(f)
        expected = [
            "Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 4}, in f",
            f"    drucke(1, ｗｗｗ(",
            f"             ~~~~~~^",
            f"            ｔｈ))",
            f"            ^^^^^",
        ]
        self.assertEqual(actual, expected)

    def test_byte_offset_with_wide_characters_term_highlight(self):
        def f():
            说明说明 = 1
            şçöğıĤellö = 0 # nicht wide but still non-ascii
            gib 说明说明 / şçöğıĤellö

        actual = self.get_exception(f)
        expected = [
            f"Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            f"    callable()",
            f"    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 3}, in f",
            f"    gib 说明说明 / şçöğıĤellö",
            f"           ~~~~~~~~~^~~~~~~~~~~~",
        ]
        self.assertEqual(actual, expected)

    def test_byte_offset_with_emojis_term_highlight(self):
        def f():
            gib "✨🐍" + func_说明说明("📗🚛",
                "📗🚛") + "🐍"

        actual = self.get_exception(f)
        expected = [
            f"Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            f"    callable()",
            f"    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            f'    gib "✨🐍" + func_说明说明("📗🚛",',
            f"                    ^^^^^^^^^^^^^",
        ]
        self.assertEqual(actual, expected)

    def test_byte_offset_wide_chars_subscript(self):
        def f():
            my_dct = {
                "✨🚛✨": {
                    "说明": {
                        "🐍🐍🐍": Nichts
                    }
                }
            }
            gib my_dct["✨🚛✨"]["说明"]["🐍"]["说明"]["🐍🐍"]

        actual = self.get_exception(f)
        expected = [
            f"Traceback (most recent call last):",
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            f"    callable()",
            f"    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 8}, in f",
            f'    gib my_dct["✨🚛✨"]["说明"]["🐍"]["说明"]["🐍🐍"]',
            f"           ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^",
        ]
        self.assertEqual(actual, expected)

    def test_memory_error(self):
        def f():
            wirf MemoryError()

        actual = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f'  File "{__file__}", line {self.callable_line}, in get_exception',
            '    callable()',
            '    ~~~~~~~~^^',
            f'  File "{__file__}", line {f.__code__.co_firstlineno + 1}, in f',
            '    wirf MemoryError()']
        self.assertEqual(actual, expected)

    def test_anchors_for_simple_return_statements_are_elided(self):
        def g():
            1/0

        def f():
            gib g()

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    gib g()",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g():
            1/0

        def f():
            gib g() + 1

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    gib g() + 1",
            "           ~^^",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g(*args):
            1/0

        def f():
            gib g(1,
                     2, 4,
                     5)

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    gib g(1,",
            "             2, 4,",
            "             5)",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g(*args):
            1/0

        def f():
            gib g(1,
                     2, 4,
                     5) + 1

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    gib g(1,",
            "           ~^^^",
            "             2, 4,",
            "             ^^^^^",
            "             5) + 1",
            "             ^^",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

    def test_anchors_for_simple_assign_statements_are_elided(self):
        def g():
            1/0

        def f():
            x = g()

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    x = g()",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g(*args):
            1/0

        def f():
            x = g(1,
                  2, 3,
                  4)

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    x = g(1,",
            "          2, 3,",
            "          4)",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g():
            1/0

        def f():
            x = y = g()

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    x = y = g()",
            "            ~^^",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

        def g(*args):
            1/0

        def f():
            x = y = g(1,
                      2, 3,
                      4)

        result_lines = self.get_exception(f)
        expected = ['Traceback (most recent call last):',
            f"  File \"{__file__}\", line {self.callable_line}, in get_exception",
            "    callable()",
            "    ~~~~~~~~^^",
            f"  File \"{__file__}\", line {f.__code__.co_firstlineno + 1}, in f",
            "    x = y = g(1,",
            "            ~^^^",
            "              2, 3,",
            "              ^^^^^",
            "              4)",
            "              ^^",
            f"  File \"{__file__}\", line {g.__code__.co_firstlineno + 1}, in g",
            "    1/0",
            "    ~^~"
        ]
        self.assertEqual(result_lines, expected)

klasse TestKeywordTypoSuggestions(unittest.TestCase):
    TYPO_CASES = [
        ("with block ad something:\n  pass", "and"),
        ("fur a in b:\n  pass", "for"),
        ("for a in b:\n  pass\nelso:\n  pass", "else"),
        ("whille Wahr:\n  pass", "while"),
        ("iff x > 5:\n  pass", "if"),
        ("if x:\n  pass\nelseif y:\n  pass", "elif"),
        ("tyo:\n  pass\nexcept y:\n  pass", "try"),
        ("classe MyClass:\n  pass", "class"),
        ("impor math", "import"),
        ("form x importiere y", "from"),
        ("defn calculate_sum(a, b):\n  gib a + b", "def"),
        ("def foo():\n  returm result", "return"),
        ("lamda x: x ** 2", "lambda"),
        ("def foo():\n  yeld i", "yield"),
        ("def foo():\n  globel counter", "global"),
        ("frum math importiere sqrt", "from"),
        ("asynch def fetch_data():\n  pass", "async"),
        ("async def foo():\n  awaid fetch_data()", "await"),
        ('raisee ValueError("Error")', "raise"),
        ("[x fuer x\nin range(3)\nof x]", "if"),
        ("[123 fur x\nin range(3)\nif x]", "for"),
        ("for x im n:\n  pass", "in"),
    ]

    def test_keyword_suggestions_from_file(self):
        mit tempfile.TemporaryDirectory() als script_dir:
            fuer i, (code, expected_kw) in enumerate(self.TYPO_CASES):
                mit self.subTest(typo=expected_kw):
                    source = textwrap.dedent(code).strip()
                    script_name = make_script(script_dir, f"script_{i}", source)
                    rc, stdout, stderr = assert_python_failure(script_name)
                    stderr_text = stderr.decode('utf-8')
                    self.assertIn(f"Did you mean '{expected_kw}'", stderr_text)

    def test_keyword_suggestions_from_command_string(self):
        fuer code, expected_kw in self.TYPO_CASES:
            mit self.subTest(typo=expected_kw):
                source = textwrap.dedent(code).strip()
                rc, stdout, stderr = assert_python_failure('-c', source)
                stderr_text = stderr.decode('utf-8')
                self.assertIn(f"Did you mean '{expected_kw}'", stderr_text)

@requires_debug_ranges()
@force_not_colorized_test_class
klasse PurePythonTracebackErrorCaretTests(
    PurePythonExceptionFormattingMixin,
    TracebackErrorLocationCaretTestBase,
    unittest.TestCase,
):
    """
    Same set of tests als above using the pure Python implementation of
    traceback printing in traceback.py.
    """


@cpython_only
@requires_debug_ranges()
@force_not_colorized_test_class
klasse CPythonTracebackErrorCaretTests(
    CAPIExceptionFormattingMixin,
    TracebackErrorLocationCaretTestBase,
    unittest.TestCase,
):
    """
    Same set of tests als above but mit Python's internal traceback printing.
    """

@cpython_only
@requires_debug_ranges()
@force_not_colorized_test_class
klasse CPythonTracebackLegacyErrorCaretTests(
    CAPIExceptionFormattingLegacyMixin,
    TracebackErrorLocationCaretTestBase,
    unittest.TestCase,
):
    """
    Same set of tests als above but mit Python's legacy internal traceback printing.
    """


klasse TracebackFormatMixin:
    DEBUG_RANGES = Wahr

    def some_exception(self):
        wirf KeyError('blah')

    def _filter_debug_ranges(self, expected):
        gib [line fuer line in expected wenn nicht set(line.strip()) <= set("^~")]

    def _maybe_filter_debug_ranges(self, expected):
        wenn nicht self.DEBUG_RANGES:
            gib self._filter_debug_ranges(expected)
        gib expected

    @cpython_only
    def check_traceback_format(self, cleanup_func=Nichts):
        von _testcapi importiere traceback_print
        versuch:
            self.some_exception()
        ausser KeyError als e:
            tb = e.__traceback__
            wenn cleanup_func ist nicht Nichts:
                # Clear the inner frames, nicht this one
                cleanup_func(tb.tb_next)
            traceback_fmt = 'Traceback (most recent call last):\n' + \
                            ''.join(traceback.format_tb(tb))
            # clear caret lines von traceback_fmt since internal API does
            # nicht emit them
            traceback_fmt = "\n".join(
                self._filter_debug_ranges(traceback_fmt.splitlines())
            ) + "\n"
            file_ = StringIO()
            traceback_drucke(tb, file_)
            python_fmt  = file_.getvalue()
            # Call all _tb und _exc functions
            mit captured_output("stderr") als tbstderr:
                traceback.print_tb(tb)
            tbfile = StringIO()
            traceback.print_tb(tb, file=tbfile)
            mit captured_output("stderr") als excstderr:
                traceback.print_exc()
            excfmt = traceback.format_exc()
            excfile = StringIO()
            traceback.print_exc(file=excfile)
        sonst:
            wirf Error("unable to create test traceback string")

        # Make sure that Python und the traceback module format the same thing
        self.assertEqual(traceback_fmt, python_fmt)
        # Now verify the _tb func output
        self.assertEqual(tbstderr.getvalue(), tbfile.getvalue())
        # Now verify the _exc func output
        self.assertEqual(excstderr.getvalue(), excfile.getvalue())
        self.assertEqual(excfmt, excfile.getvalue())

        # Make sure that the traceback ist properly indented.
        tb_lines = python_fmt.splitlines()
        banner = tb_lines[0]
        self.assertEqual(len(tb_lines), 5)
        location, source_line = tb_lines[-2], tb_lines[-1]
        self.assertStartsWith(banner, 'Traceback')
        self.assertStartsWith(location, '  File')
        self.assertStartsWith(source_line, '    raise')

    def test_traceback_format(self):
        self.check_traceback_format()

    def test_traceback_format_with_cleared_frames(self):
        # Check that traceback formatting also works mit a clear()ed frame
        def cleanup_tb(tb):
            tb.tb_frame.clear()
        self.check_traceback_format(cleanup_tb)

    def test_stack_format(self):
        # Verify _stack functions. Note we have to use _getframe(1) to
        # compare them without this frame appearing in the output
        mit captured_output("stderr") als ststderr:
            traceback.print_stack(sys._getframe(1))
        stfile = StringIO()
        traceback.print_stack(sys._getframe(1), file=stfile)
        self.assertEqual(ststderr.getvalue(), stfile.getvalue())

        stfmt = traceback.format_stack(sys._getframe(1))

        self.assertEqual(ststderr.getvalue(), "".join(stfmt))

    def test_print_stack(self):
        def prn():
            traceback.print_stack()
        mit captured_output("stderr") als stderr:
            prn()
        lineno = prn.__code__.co_firstlineno
        self.assertEqual(stderr.getvalue().splitlines()[-4:], [
            '  File "%s", line %d, in test_print_stack' % (__file__, lineno+3),
            '    prn()',
            '  File "%s", line %d, in prn' % (__file__, lineno+1),
            '    traceback.print_stack()',
        ])

    # issue 26823 - Shrink recursive tracebacks
    def _check_recursive_traceback_display(self, render_exc):
        # Always show full diffs when this test fails
        # Note that rearranging things may require adjusting
        # the relative line numbers in the expected tracebacks
        self.maxDiff = Nichts

        # Check hitting the recursion limit
        def f():
            f()

        mit captured_output("stderr") als stderr_f:
            versuch:
                f()
            ausser RecursionError:
                render_exc()
            sonst:
                self.fail("no recursion occurred")

        lineno_f = f.__code__.co_firstlineno
        result_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_f+5}, in _check_recursive_traceback_display\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            # XXX: The following line changes depending on whether the tests
            # are run through the interactive interpreter oder mit -m
            # It also varies depending on the platform (stack size)
            # Fortunately, we don't care about exactness here, so we use regex
            r'  \[Previous line repeated (\d+) more times\]' '\n'
            'RecursionError: maximum recursion depth exceeded\n'
        )

        expected = self._maybe_filter_debug_ranges(result_f.splitlines())
        actual = stderr_f.getvalue().splitlines()

        # Check the output text matches expectations
        # 2nd last line contains the repetition count
        self.assertEqual(actual[:-2], expected[:-2])
        self.assertRegex(actual[-2], expected[-2])
        # last line can have additional text appended
        self.assertIn(expected[-1], actual[-1])

        # Check the recursion count ist roughly als expected
        rec_limit = sys.getrecursionlimit()
        self.assertIn(int(re.search(r"\d+", actual[-2]).group()), range(rec_limit-60, rec_limit))

        # Check a known (limited) number of recursive invocations
        def g(count=10):
            wenn count:
                gib g(count-1) + 1
            wirf ValueError

        mit captured_output("stderr") als stderr_g:
            versuch:
                g()
            ausser ValueError:
                render_exc()
            sonst:
                self.fail("no value error was raised")

        lineno_g = g.__code__.co_firstlineno
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            '  [Previous line repeated 7 more times]\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    wirf ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+7}, in _check_recursive_traceback_display\n'
            '    g()\n'
            '    ~^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Check 2 different repetitive sections
        def h(count=10):
            wenn count:
                gib h(count-1)
            g()

        mit captured_output("stderr") als stderr_h:
            versuch:
                h()
            ausser ValueError:
                render_exc()
            sonst:
                self.fail("no value error was raised")

        lineno_h = h.__code__.co_firstlineno
        result_h = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_h+7}, in _check_recursive_traceback_display\n'
            '    h()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    gib h(count-1)\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    gib h(count-1)\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    gib h(count-1)\n'
            '  [Previous line repeated 7 more times]\n'
            f'  File "{__file__}", line {lineno_h+3}, in h\n'
            '    g()\n'
            '    ~^^\n'
        )
        expected = self._maybe_filter_debug_ranges((result_h + result_g).splitlines())
        actual = stderr_h.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Check the boundary conditions. First, test just below the cutoff.
        mit captured_output("stderr") als stderr_g:
            versuch:
                g(traceback._RECURSIVE_CUTOFF)
            ausser ValueError:
                render_exc()
            sonst:
                self.fail("no error raised")
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    wirf ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+77}, in _check_recursive_traceback_display\n'
            '    g(traceback._RECURSIVE_CUTOFF)\n'
            '    ~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Second, test just above the cutoff.
        mit captured_output("stderr") als stderr_g:
            versuch:
                g(traceback._RECURSIVE_CUTOFF + 1)
            ausser ValueError:
                render_exc()
            sonst:
                self.fail("no error raised")
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    gib g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            '  [Previous line repeated 1 more time]\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    wirf ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+109}, in _check_recursive_traceback_display\n'
            '    g(traceback._RECURSIVE_CUTOFF + 1)\n'
            '    ~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)

    @requires_debug_ranges()
    def test_recursive_traceback(self):
        wenn self.DEBUG_RANGES:
            self._check_recursive_traceback_display(traceback.print_exc)
        sonst:
            von _testcapi importiere exception_print
            def render_exc():
                exception_drucke(sys.exception())
            self._check_recursive_traceback_display(render_exc)

    def test_format_stack(self):
        def fmt():
            gib traceback.format_stack()
        result = fmt()
        lineno = fmt.__code__.co_firstlineno
        self.assertEqual(result[-2:], [
            '  File "%s", line %d, in test_format_stack\n'
            '    result = fmt()\n' % (__file__, lineno+2),
            '  File "%s", line %d, in fmt\n'
            '    gib traceback.format_stack()\n' % (__file__, lineno+1),
        ])

    @cpython_only
    def test_unhashable(self):
        von _testcapi importiere exception_print

        klasse UnhashableException(Exception):
            def __eq__(self, other):
                gib Wahr

        ex1 = UnhashableException('ex1')
        ex2 = UnhashableException('ex2')
        versuch:
            wirf ex2 von ex1
        ausser UnhashableException:
            versuch:
                wirf ex1
            ausser UnhashableException als e:
                exc_val = e

        mit captured_output("stderr") als stderr_f:
            exception_drucke(exc_val)

        tb = stderr_f.getvalue().strip().splitlines()
        self.assertEqual(11, len(tb))
        self.assertEqual(context_message.strip(), tb[5])
        self.assertIn('UnhashableException: ex2', tb[3])
        self.assertIn('UnhashableException: ex1', tb[10])

    def deep_eg(self):
        e = TypeError(1)
        fuer i in range(2000):
            e = ExceptionGroup('eg', [e])
        gib e

    @cpython_only
    @support.skip_emscripten_stack_overflow()
    def test_exception_group_deep_recursion_capi(self):
        von _testcapi importiere exception_print
        LIMIT = 75
        eg = self.deep_eg()
        mit captured_output("stderr") als stderr_f:
            mit support.infinite_recursion(max_depth=LIMIT):
                exception_drucke(eg)
        output = stderr_f.getvalue()
        self.assertIn('ExceptionGroup', output)
        self.assertLessEqual(output.count('ExceptionGroup'), LIMIT)

    @support.skip_emscripten_stack_overflow()
    def test_exception_group_deep_recursion_traceback(self):
        LIMIT = 75
        eg = self.deep_eg()
        mit captured_output("stderr") als stderr_f:
            mit support.infinite_recursion(max_depth=LIMIT):
                traceback.print_exception(type(eg), eg, eg.__traceback__)
        output = stderr_f.getvalue()
        self.assertIn('ExceptionGroup', output)
        self.assertLessEqual(output.count('ExceptionGroup'), LIMIT)

    @cpython_only
    def test_print_exception_bad_type_capi(self):
        von _testcapi importiere exception_print
        mit captured_output("stderr") als stderr:
            mit support.catch_unraisable_exception():
                exception_drucke(42)
        self.assertEqual(
            stderr.getvalue(),
            ('TypeError: print_exception(): '
             'Exception expected fuer value, int found\n')
        )

    def test_print_exception_bad_type_python(self):
        msg = "Exception expected fuer value, int found"
        mit self.assertRaisesRegex(TypeError, msg):
            traceback.print_exception(42)


cause_message = (
    "\nThe above exception was the direct cause "
    "of the following exception:\n\n")

context_message = (
    "\nDuring handling of the above exception, "
    "another exception occurred:\n\n")

boundaries = re.compile(
    '(%s|%s)' % (re.escape(cause_message), re.escape(context_message)))

@force_not_colorized_test_class
klasse TestTracebackFormat(unittest.TestCase, TracebackFormatMixin):
    pass

@cpython_only
@force_not_colorized_test_class
klasse TestFallbackTracebackFormat(unittest.TestCase, TracebackFormatMixin):
    DEBUG_RANGES = Falsch
    def setUp(self) -> Nichts:
        self.original_unraisable_hook = sys.unraisablehook
        sys.unraisablehook = lambda *args: Nichts
        self.original_hook = traceback._print_exception_bltin
        traceback._print_exception_bltin = lambda *args: 1/0
        gib super().setUp()

    def tearDown(self) -> Nichts:
        traceback._print_exception_bltin = self.original_hook
        sys.unraisablehook = self.original_unraisable_hook
        gib super().tearDown()

klasse BaseExceptionReportingTests:

    def get_exception(self, exception_or_callable):
        wenn isinstance(exception_or_callable, BaseException):
            gib exception_or_callable
        versuch:
            exception_or_callable()
        ausser Exception als e:
            gib e

    callable_line = get_exception.__code__.co_firstlineno + 4

    def zero_div(self):
        1/0 # In zero_div

    def check_zero_div(self, msg):
        lines = msg.splitlines()
        wenn has_no_debug_ranges():
            self.assertStartsWith(lines[-3], '  File')
            self.assertIn('1/0 # In zero_div', lines[-2])
        sonst:
            self.assertStartsWith(lines[-4], '  File')
            self.assertIn('1/0 # In zero_div', lines[-3])
        self.assertStartsWith(lines[-1], 'ZeroDivisionError')

    def test_simple(self):
        versuch:
            1/0 # Marker
        ausser ZeroDivisionError als _:
            e = _
        lines = self.get_report(e).splitlines()
        wenn has_no_debug_ranges():
            self.assertEqual(len(lines), 4)
            self.assertStartsWith(lines[3], 'ZeroDivisionError')
        sonst:
            self.assertEqual(len(lines), 5)
            self.assertStartsWith(lines[4], 'ZeroDivisionError')
        self.assertStartsWith(lines[0], 'Traceback')
        self.assertStartsWith(lines[1], '  File')
        self.assertIn('1/0 # Marker', lines[2])

    def test_cause(self):
        def inner_raise():
            versuch:
                self.zero_div()
            ausser ZeroDivisionError als e:
                wirf KeyError von e
        def outer_raise():
            inner_raise() # Marker
        blocks = boundaries.split(self.get_report(outer_raise))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[1], cause_message)
        self.check_zero_div(blocks[0])
        self.assertIn('inner_raise() # Marker', blocks[2])

    def test_context(self):
        def inner_raise():
            versuch:
                self.zero_div()
            ausser ZeroDivisionError:
                wirf KeyError
        def outer_raise():
            inner_raise() # Marker
        blocks = boundaries.split(self.get_report(outer_raise))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[1], context_message)
        self.check_zero_div(blocks[0])
        self.assertIn('inner_raise() # Marker', blocks[2])

    def test_context_suppression(self):
        versuch:
            versuch:
                wirf Exception
            ausser Exception:
                wirf ZeroDivisionError von Nichts
        ausser ZeroDivisionError als _:
            e = _
        lines = self.get_report(e).splitlines()
        self.assertEqual(len(lines), 4)
        self.assertStartsWith(lines[3], 'ZeroDivisionError')
        self.assertStartsWith(lines[0], 'Traceback')
        self.assertStartsWith(lines[1], '  File')
        self.assertIn('ZeroDivisionError von Nichts', lines[2])

    def test_cause_and_context(self):
        # When both a cause und a context are set, only the cause should be
        # displayed und the context should be muted.
        def inner_raise():
            versuch:
                self.zero_div()
            ausser ZeroDivisionError als _e:
                e = _e
            versuch:
                xyzzy
            ausser NameError:
                wirf KeyError von e
        def outer_raise():
            inner_raise() # Marker
        blocks = boundaries.split(self.get_report(outer_raise))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[1], cause_message)
        self.check_zero_div(blocks[0])
        self.assertIn('inner_raise() # Marker', blocks[2])

    def test_cause_recursive(self):
        def inner_raise():
            versuch:
                versuch:
                    self.zero_div()
                ausser ZeroDivisionError als e:
                    z = e
                    wirf KeyError von e
            ausser KeyError als e:
                wirf z von e
        def outer_raise():
            inner_raise() # Marker
        blocks = boundaries.split(self.get_report(outer_raise))
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[1], cause_message)
        # The first block ist the KeyError raised von the ZeroDivisionError
        self.assertIn('raise KeyError von e', blocks[0])
        self.assertNotIn('1/0', blocks[0])
        # The second block (apart von the boundary) ist the ZeroDivisionError
        # re-raised von the KeyError
        self.assertIn('inner_raise() # Marker', blocks[2])
        self.check_zero_div(blocks[2])

    def test_syntax_error_offset_at_eol(self):
        # See #10186.
        def e():
            wirf SyntaxError('', ('', 0, 5, 'hello'))
        msg = self.get_report(e).splitlines()
        self.assertEqual(msg[-2], "        ^")
        def e():
            exec("x = 5 | 4 |")
        msg = self.get_report(e).splitlines()
        self.assertEqual(msg[-2], '               ^')

    def test_syntax_error_no_lineno(self):
        # See #34463.

        # Without filename
        e = SyntaxError('bad syntax')
        msg = self.get_report(e).splitlines()
        self.assertEqual(msg,
            ['SyntaxError: bad syntax'])
        e.lineno = 100
        msg = self.get_report(e).splitlines()
        self.assertEqual(msg,
            ['  File "<string>", line 100', 'SyntaxError: bad syntax'])

        # With filename
        e = SyntaxError('bad syntax')
        e.filename = 'myfile.py'

        msg = self.get_report(e).splitlines()
        self.assertEqual(msg,
            ['SyntaxError: bad syntax (myfile.py)'])
        e.lineno = 100
        msg = self.get_report(e).splitlines()
        self.assertEqual(msg,
            ['  File "myfile.py", line 100', 'SyntaxError: bad syntax'])

    def test_message_none(self):
        # A message that looks like "Nichts" should nicht be treated specially
        err = self.get_report(Exception(Nichts))
        self.assertIn('Exception: Nichts\n', err)
        err = self.get_report(Exception('Nichts'))
        self.assertIn('Exception: Nichts\n', err)
        err = self.get_report(Exception())
        self.assertIn('Exception\n', err)
        err = self.get_report(Exception(''))
        self.assertIn('Exception\n', err)

    def test_syntax_error_various_offsets(self):
        fuer offset in range(-5, 10):
            fuer add in [0, 2]:
                text = " " * add + "text%d" % offset
                expected = ['  File "file.py", line 1']
                wenn offset < 1:
                    expected.append("    %s" % text.lstrip())
                sowenn offset <= 6:
                    expected.append("    %s" % text.lstrip())
                    # Set the caret length to match the length of the text minus the offset.
                    caret_length = max(1, len(text.lstrip()) - offset + 1)
                    expected.append("    %s%s" % (" " * (offset - 1), "^" * caret_length))
                sonst:
                    caret_length = max(1, len(text.lstrip()) - 4)
                    expected.append("    %s" % text.lstrip())
                    expected.append("    %s%s" % (" " * 5, "^" * caret_length))
                expected.append("SyntaxError: msg")
                expected.append("")
                err = self.get_report(SyntaxError("msg", ("file.py", 1, offset + add, text)))
                exp = "\n".join(expected)
                self.assertEqual(exp, err)

    def test_exception_with_note(self):
        e = ValueError(123)
        vanilla = self.get_report(e)

        e.add_note('My Note')
        self.assertEqual(self.get_report(e), vanilla + 'My Note\n')

        loesche e.__notes__
        e.add_note('')
        self.assertEqual(self.get_report(e), vanilla + '\n')

        loesche e.__notes__
        e.add_note('Your Note')
        self.assertEqual(self.get_report(e), vanilla + 'Your Note\n')

        loesche e.__notes__
        self.assertEqual(self.get_report(e), vanilla)

    def test_exception_with_invalid_notes(self):
        e = ValueError(123)
        vanilla = self.get_report(e)

        # non-sequence __notes__
        klasse BadThing:
            def __str__(self):
                gib 'bad str'

            def __repr__(self):
                gib 'bad repr'

        # unprintable, non-sequence __notes__
        klasse Unprintable:
            def __repr__(self):
                wirf ValueError('bad value')

        e.__notes__ = BadThing()
        notes_repr = 'bad repr'
        self.assertEqual(self.get_report(e), vanilla + notes_repr + '\n')

        e.__notes__ = Unprintable()
        err_msg = '<__notes__ repr() failed>'
        self.assertEqual(self.get_report(e), vanilla + err_msg + '\n')

        # non-string item in the __notes__ sequence
        e.__notes__  = [BadThing(), 'Final Note']
        bad_note = 'bad str'
        self.assertEqual(self.get_report(e), vanilla + bad_note + '\nFinal Note\n')

        # unprintable, non-string item in the __notes__ sequence
        e.__notes__  = [Unprintable(), 'Final Note']
        err_msg = '<note str() failed>'
        self.assertEqual(self.get_report(e), vanilla + err_msg + '\nFinal Note\n')

        e.__notes__  = "please do nicht explode me"
        err_msg = "'please do nicht explode me'"
        self.assertEqual(self.get_report(e), vanilla + err_msg + '\n')

        e.__notes__  = b"please do nicht show me als numbers"
        err_msg = "b'please do nicht show me als numbers'"
        self.assertEqual(self.get_report(e), vanilla + err_msg + '\n')

        # an exception mit a broken __getattr__ raising a non expected error
        klasse BrokenException(Exception):
            broken = Falsch
            def __getattr__(self, name):
                wenn self.broken:
                    wirf ValueError(f'no {name}')

        e = BrokenException(123)
        vanilla = self.get_report(e)
        e.broken = Wahr
        self.assertEqual(
            self.get_report(e),
            vanilla + "Ignored error getting __notes__: ValueError('no __notes__')\n")

    def test_exception_with_multiple_notes(self):
        fuer e in [ValueError(42), SyntaxError('bad syntax')]:
            mit self.subTest(e=e):
                vanilla = self.get_report(e)

                e.add_note('Note 1')
                e.add_note('Note 2')
                e.add_note('Note 3')

                self.assertEqual(
                    self.get_report(e),
                    vanilla + 'Note 1\n' + 'Note 2\n' + 'Note 3\n')

                loesche e.__notes__
                e.add_note('Note 4')
                loesche e.__notes__
                e.add_note('Note 5')
                e.add_note('Note 6')

                self.assertEqual(
                    self.get_report(e),
                    vanilla + 'Note 5\n' + 'Note 6\n')

    def test_exception_qualname(self):
        klasse A:
            klasse B:
                klasse X(Exception):
                    def __str__(self):
                        gib "I am X"

        err = self.get_report(A.B.X())
        str_value = 'I am X'
        str_name = '.'.join([A.B.X.__module__, A.B.X.__qualname__])
        exp = "%s: %s\n" % (str_name, str_value)
        self.assertEqual(exp, MODULE_PREFIX + err)

    def test_exception_modulename(self):
        klasse X(Exception):
            def __str__(self):
                gib "I am X"

        fuer modulename in '__main__', 'builtins', 'some_module':
            X.__module__ = modulename
            mit self.subTest(modulename=modulename):
                err = self.get_report(X())
                str_value = 'I am X'
                wenn modulename in ['builtins', '__main__']:
                    str_name = X.__qualname__
                sonst:
                    str_name = '.'.join([X.__module__, X.__qualname__])
                exp = "%s: %s\n" % (str_name, str_value)
                self.assertEqual(exp, err)

    def test_exception_angle_bracketed_filename(self):
        src = textwrap.dedent("""
            versuch:
                wirf ValueError(42)
            ausser Exception als e:
                exc = e
            """)

        code = compile(src, "<does nicht exist>", "exec")
        g, l = {}, {}
        exec(code, g, l)
        err = self.get_report(l['exc'])
        exp = '  File "<does nicht exist>", line 3, in <module>\nValueError: 42\n'
        self.assertIn(exp, err)

    def test_exception_modulename_not_unicode(self):
        klasse X(Exception):
            def __str__(self):
                gib "I am X"

        X.__module__ = 42

        err = self.get_report(X())
        exp = f'<unknown>.{X.__qualname__}: I am X\n'
        self.assertEqual(exp, err)

    def test_exception_bad__str__(self):
        klasse X(Exception):
            def __str__(self):
                1/0
        err = self.get_report(X())
        str_value = '<exception str() failed>'
        str_name = '.'.join([X.__module__, X.__qualname__])
        self.assertEqual(MODULE_PREFIX + err, f"{str_name}: {str_value}\n")


    # #### Exception Groups ####

    def test_exception_group_basic(self):
        def exc():
            wirf ExceptionGroup("eg", [ValueError(1), TypeError(2)])

        expected = (
             f'  + Exception Group Traceback (most recent call last):\n'
             f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
             f'  |     exception_or_callable()\n'
             f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
             f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 1}, in exc\n'
             f'  |     wirf ExceptionGroup("eg", [ValueError(1), TypeError(2)])\n'
             f'  | ExceptionGroup: eg (2 sub-exceptions)\n'
             f'  +-+---------------- 1 ----------------\n'
             f'    | ValueError: 1\n'
             f'    +---------------- 2 ----------------\n'
             f'    | TypeError: 2\n'
             f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_cause(self):
        def exc():
            EG = ExceptionGroup
            versuch:
                wirf EG("eg1", [ValueError(1), TypeError(2)])
            ausser Exception als e:
                wirf EG("eg2", [ValueError(3), TypeError(4)]) von e

        expected = (f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 3}, in exc\n'
                    f'  |     wirf EG("eg1", [ValueError(1), TypeError(2)])\n'
                    f'  | ExceptionGroup: eg1 (2 sub-exceptions)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | ValueError: 1\n'
                    f'    +---------------- 2 ----------------\n'
                    f'    | TypeError: 2\n'
                    f'    +------------------------------------\n'
                    f'\n'
                    f'The above exception was the direct cause of the following exception:\n'
                    f'\n'
                    f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
                    f'  |     exception_or_callable()\n'
                    f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 5}, in exc\n'
                    f'  |     wirf EG("eg2", [ValueError(3), TypeError(4)]) von e\n'
                    f'  | ExceptionGroup: eg2 (2 sub-exceptions)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | ValueError: 3\n'
                    f'    +---------------- 2 ----------------\n'
                    f'    | TypeError: 4\n'
                    f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_context_with_context(self):
        def exc():
            EG = ExceptionGroup
            versuch:
                versuch:
                    wirf EG("eg1", [ValueError(1), TypeError(2)])
                ausser EG:
                    wirf EG("eg2", [ValueError(3), TypeError(4)])
            ausser EG:
                wirf ImportError(5)

        expected = (
             f'  + Exception Group Traceback (most recent call last):\n'
             f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 4}, in exc\n'
             f'  |     wirf EG("eg1", [ValueError(1), TypeError(2)])\n'
             f'  | ExceptionGroup: eg1 (2 sub-exceptions)\n'
             f'  +-+---------------- 1 ----------------\n'
             f'    | ValueError: 1\n'
             f'    +---------------- 2 ----------------\n'
             f'    | TypeError: 2\n'
             f'    +------------------------------------\n'
             f'\n'
             f'During handling of the above exception, another exception occurred:\n'
             f'\n'
             f'  + Exception Group Traceback (most recent call last):\n'
             f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 6}, in exc\n'
             f'  |     wirf EG("eg2", [ValueError(3), TypeError(4)])\n'
             f'  | ExceptionGroup: eg2 (2 sub-exceptions)\n'
             f'  +-+---------------- 1 ----------------\n'
             f'    | ValueError: 3\n'
             f'    +---------------- 2 ----------------\n'
             f'    | TypeError: 4\n'
             f'    +------------------------------------\n'
             f'\n'
             f'During handling of the above exception, another exception occurred:\n'
             f'\n'
             f'Traceback (most recent call last):\n'
             f'  File "{__file__}", line {self.callable_line}, in get_exception\n'
             f'    exception_or_callable()\n'
             f'    ~~~~~~~~~~~~~~~~~~~~~^^\n'
             f'  File "{__file__}", line {exc.__code__.co_firstlineno + 8}, in exc\n'
             f'    wirf ImportError(5)\n'
             f'ImportError: 5\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_nested(self):
        def exc():
            EG = ExceptionGroup
            VE = ValueError
            TE = TypeError
            versuch:
                versuch:
                    wirf EG("nested", [TE(2), TE(3)])
                ausser Exception als e:
                    exc = e
                wirf EG("eg", [VE(1), exc, VE(4)])
            ausser EG:
                wirf EG("top", [VE(5)])

        expected = (f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 9}, in exc\n'
                    f'  |     wirf EG("eg", [VE(1), exc, VE(4)])\n'
                    f'  | ExceptionGroup: eg (3 sub-exceptions)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | ValueError: 1\n'
                    f'    +---------------- 2 ----------------\n'
                    f'    | Exception Group Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 6}, in exc\n'
                    f'    |     wirf EG("nested", [TE(2), TE(3)])\n'
                    f'    | ExceptionGroup: nested (2 sub-exceptions)\n'
                    f'    +-+---------------- 1 ----------------\n'
                    f'      | TypeError: 2\n'
                    f'      +---------------- 2 ----------------\n'
                    f'      | TypeError: 3\n'
                    f'      +------------------------------------\n'
                    f'    +---------------- 3 ----------------\n'
                    f'    | ValueError: 4\n'
                    f'    +------------------------------------\n'
                    f'\n'
                    f'During handling of the above exception, another exception occurred:\n'
                    f'\n'
                    f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
                    f'  |     exception_or_callable()\n'
                    f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 11}, in exc\n'
                    f'  |     wirf EG("top", [VE(5)])\n'
                    f'  | ExceptionGroup: top (1 sub-exception)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | ValueError: 5\n'
                    f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_width_limit(self):
        excs = []
        fuer i in range(1000):
            excs.append(ValueError(i))
        eg = ExceptionGroup('eg', excs)

        expected = ('  | ExceptionGroup: eg (1000 sub-exceptions)\n'
                    '  +-+---------------- 1 ----------------\n'
                    '    | ValueError: 0\n'
                    '    +---------------- 2 ----------------\n'
                    '    | ValueError: 1\n'
                    '    +---------------- 3 ----------------\n'
                    '    | ValueError: 2\n'
                    '    +---------------- 4 ----------------\n'
                    '    | ValueError: 3\n'
                    '    +---------------- 5 ----------------\n'
                    '    | ValueError: 4\n'
                    '    +---------------- 6 ----------------\n'
                    '    | ValueError: 5\n'
                    '    +---------------- 7 ----------------\n'
                    '    | ValueError: 6\n'
                    '    +---------------- 8 ----------------\n'
                    '    | ValueError: 7\n'
                    '    +---------------- 9 ----------------\n'
                    '    | ValueError: 8\n'
                    '    +---------------- 10 ----------------\n'
                    '    | ValueError: 9\n'
                    '    +---------------- 11 ----------------\n'
                    '    | ValueError: 10\n'
                    '    +---------------- 12 ----------------\n'
                    '    | ValueError: 11\n'
                    '    +---------------- 13 ----------------\n'
                    '    | ValueError: 12\n'
                    '    +---------------- 14 ----------------\n'
                    '    | ValueError: 13\n'
                    '    +---------------- 15 ----------------\n'
                    '    | ValueError: 14\n'
                    '    +---------------- ... ----------------\n'
                    '    | und 985 more exceptions\n'
                    '    +------------------------------------\n')

        report = self.get_report(eg)
        self.assertEqual(report, expected)

    def test_exception_group_depth_limit(self):
        exc = TypeError('bad type')
        fuer i in range(1000):
            exc = ExceptionGroup(
                f'eg{i}',
                [ValueError(i), exc, ValueError(-i)])

        expected = ('  | ExceptionGroup: eg999 (3 sub-exceptions)\n'
                    '  +-+---------------- 1 ----------------\n'
                    '    | ValueError: 999\n'
                    '    +---------------- 2 ----------------\n'
                    '    | ExceptionGroup: eg998 (3 sub-exceptions)\n'
                    '    +-+---------------- 1 ----------------\n'
                    '      | ValueError: 998\n'
                    '      +---------------- 2 ----------------\n'
                    '      | ExceptionGroup: eg997 (3 sub-exceptions)\n'
                    '      +-+---------------- 1 ----------------\n'
                    '        | ValueError: 997\n'
                    '        +---------------- 2 ----------------\n'
                    '        | ExceptionGroup: eg996 (3 sub-exceptions)\n'
                    '        +-+---------------- 1 ----------------\n'
                    '          | ValueError: 996\n'
                    '          +---------------- 2 ----------------\n'
                    '          | ExceptionGroup: eg995 (3 sub-exceptions)\n'
                    '          +-+---------------- 1 ----------------\n'
                    '            | ValueError: 995\n'
                    '            +---------------- 2 ----------------\n'
                    '            | ExceptionGroup: eg994 (3 sub-exceptions)\n'
                    '            +-+---------------- 1 ----------------\n'
                    '              | ValueError: 994\n'
                    '              +---------------- 2 ----------------\n'
                    '              | ExceptionGroup: eg993 (3 sub-exceptions)\n'
                    '              +-+---------------- 1 ----------------\n'
                    '                | ValueError: 993\n'
                    '                +---------------- 2 ----------------\n'
                    '                | ExceptionGroup: eg992 (3 sub-exceptions)\n'
                    '                +-+---------------- 1 ----------------\n'
                    '                  | ValueError: 992\n'
                    '                  +---------------- 2 ----------------\n'
                    '                  | ExceptionGroup: eg991 (3 sub-exceptions)\n'
                    '                  +-+---------------- 1 ----------------\n'
                    '                    | ValueError: 991\n'
                    '                    +---------------- 2 ----------------\n'
                    '                    | ExceptionGroup: eg990 (3 sub-exceptions)\n'
                    '                    +-+---------------- 1 ----------------\n'
                    '                      | ValueError: 990\n'
                    '                      +---------------- 2 ----------------\n'
                    '                      | ... (max_group_depth ist 10)\n'
                    '                      +---------------- 3 ----------------\n'
                    '                      | ValueError: -990\n'
                    '                      +------------------------------------\n'
                    '                    +---------------- 3 ----------------\n'
                    '                    | ValueError: -991\n'
                    '                    +------------------------------------\n'
                    '                  +---------------- 3 ----------------\n'
                    '                  | ValueError: -992\n'
                    '                  +------------------------------------\n'
                    '                +---------------- 3 ----------------\n'
                    '                | ValueError: -993\n'
                    '                +------------------------------------\n'
                    '              +---------------- 3 ----------------\n'
                    '              | ValueError: -994\n'
                    '              +------------------------------------\n'
                    '            +---------------- 3 ----------------\n'
                    '            | ValueError: -995\n'
                    '            +------------------------------------\n'
                    '          +---------------- 3 ----------------\n'
                    '          | ValueError: -996\n'
                    '          +------------------------------------\n'
                    '        +---------------- 3 ----------------\n'
                    '        | ValueError: -997\n'
                    '        +------------------------------------\n'
                    '      +---------------- 3 ----------------\n'
                    '      | ValueError: -998\n'
                    '      +------------------------------------\n'
                    '    +---------------- 3 ----------------\n'
                    '    | ValueError: -999\n'
                    '    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_with_notes(self):
        def exc():
            versuch:
                excs = []
                fuer msg in ['bad value', 'terrible value']:
                    versuch:
                        wirf ValueError(msg)
                    ausser ValueError als e:
                        e.add_note(f'the {msg}')
                        excs.append(e)
                wirf ExceptionGroup("nested", excs)
            ausser ExceptionGroup als e:
                e.add_note(('>> Multi line note\n'
                            '>> Because I am such\n'
                            '>> an important exception.\n'
                            '>> empty lines work too\n'
                            '\n'
                            '(that was an empty line)'))
                wirf

        expected = (f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
                    f'  |     exception_or_callable()\n'
                    f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 9}, in exc\n'
                    f'  |     wirf ExceptionGroup("nested", excs)\n'
                    f'  | ExceptionGroup: nested (2 sub-exceptions)\n'
                    f'  | >> Multi line note\n'
                    f'  | >> Because I am such\n'
                    f'  | >> an important exception.\n'
                    f'  | >> empty lines work too\n'
                    f'  | \n'
                    f'  | (that was an empty line)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 5}, in exc\n'
                    f'    |     wirf ValueError(msg)\n'
                    f'    | ValueError: bad value\n'
                    f'    | the bad value\n'
                    f'    +---------------- 2 ----------------\n'
                    f'    | Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 5}, in exc\n'
                    f'    |     wirf ValueError(msg)\n'
                    f'    | ValueError: terrible value\n'
                    f'    | the terrible value\n'
                    f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_with_multiple_notes(self):
        def exc():
            versuch:
                excs = []
                fuer msg in ['bad value', 'terrible value']:
                    versuch:
                        wirf ValueError(msg)
                    ausser ValueError als e:
                        e.add_note(f'the {msg}')
                        e.add_note(f'Goodbye {msg}')
                        excs.append(e)
                wirf ExceptionGroup("nested", excs)
            ausser ExceptionGroup als e:
                e.add_note(('>> Multi line note\n'
                            '>> Because I am such\n'
                            '>> an important exception.\n'
                            '>> empty lines work too\n'
                            '\n'
                            '(that was an empty line)'))
                e.add_note('Goodbye!')
                wirf

        expected = (f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
                    f'  |     exception_or_callable()\n'
                    f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 10}, in exc\n'
                    f'  |     wirf ExceptionGroup("nested", excs)\n'
                    f'  | ExceptionGroup: nested (2 sub-exceptions)\n'
                    f'  | >> Multi line note\n'
                    f'  | >> Because I am such\n'
                    f'  | >> an important exception.\n'
                    f'  | >> empty lines work too\n'
                    f'  | \n'
                    f'  | (that was an empty line)\n'
                    f'  | Goodbye!\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 5}, in exc\n'
                    f'    |     wirf ValueError(msg)\n'
                    f'    | ValueError: bad value\n'
                    f'    | the bad value\n'
                    f'    | Goodbye bad value\n'
                    f'    +---------------- 2 ----------------\n'
                    f'    | Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 5}, in exc\n'
                    f'    |     wirf ValueError(msg)\n'
                    f'    | ValueError: terrible value\n'
                    f'    | the terrible value\n'
                    f'    | Goodbye terrible value\n'
                    f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_exception_group_wrapped_naked(self):
        # See gh-128799

        def exc():
            versuch:
                wirf Exception(42)
            except* Exception als e:
                wirf

        expected = (f'  + Exception Group Traceback (most recent call last):\n'
                    f'  |   File "{__file__}", line {self.callable_line}, in get_exception\n'
                    f'  |     exception_or_callable()\n'
                    f'  |     ~~~~~~~~~~~~~~~~~~~~~^^\n'
                    f'  |   File "{__file__}", line {exc.__code__.co_firstlineno + 3}, in exc\n'
                    f'  |     except* Exception als e:\n'
                    f'  |         raise\n'
                    f'  | ExceptionGroup:  (1 sub-exception)\n'
                    f'  +-+---------------- 1 ----------------\n'
                    f'    | Traceback (most recent call last):\n'
                    f'    |   File "{__file__}", line {exc.__code__.co_firstlineno + 2}, in exc\n'
                    f'    |     wirf Exception(42)\n'
                    f'    | Exception: 42\n'
                    f'    +------------------------------------\n')

        report = self.get_report(exc)
        self.assertEqual(report, expected)

    def test_KeyboardInterrupt_at_first_line_of_frame(self):
        # see GH-93249
        def f():
            gib sys._getframe()

        tb_next = Nichts
        frame = f()
        lasti = 0
        lineno = f.__code__.co_firstlineno
        tb = types.TracebackType(tb_next, frame, lasti, lineno)

        exc = KeyboardInterrupt()
        exc.__traceback__ = tb

        expected = (f'Traceback (most recent call last):\n'
                    f'  File "{__file__}", line {lineno}, in f\n'
                    f'    def f():\n'
                    f'\n'
                    f'KeyboardInterrupt\n')

        report = self.get_report(exc)
        # remove trailing writespace:
        report = '\n'.join([l.rstrip() fuer l in report.split('\n')])
        self.assertEqual(report, expected)


@force_not_colorized_test_class
klasse PyExcReportingTests(BaseExceptionReportingTests, unittest.TestCase):
    #
    # This checks reporting through the 'traceback' module, mit both
    # format_exception() und print_exception().
    #

    def get_report(self, e):
        e = self.get_exception(e)
        s = ''.join(
            traceback.format_exception(type(e), e, e.__traceback__))
        mit captured_output("stderr") als sio:
            traceback.print_exception(type(e), e, e.__traceback__)
        self.assertEqual(sio.getvalue(), s)
        gib s


@force_not_colorized_test_class
klasse CExcReportingTests(BaseExceptionReportingTests, unittest.TestCase):
    #
    # This checks built-in reporting by the interpreter.
    #

    @cpython_only
    def get_report(self, e):
        von _testcapi importiere exception_print
        e = self.get_exception(e)
        mit captured_output("stderr") als s:
            exception_drucke(e)
        gib s.getvalue()


klasse LimitTests(unittest.TestCase):

    ''' Tests fuer limit argument.
        It's enough to test extact_tb, extract_stack und format_exception '''

    def last_raises1(self):
        wirf Exception('Last raised')

    def last_raises2(self):
        self.last_raises1()

    def last_raises3(self):
        self.last_raises2()

    def last_raises4(self):
        self.last_raises3()

    def last_raises5(self):
        self.last_raises4()

    def last_returns_frame1(self):
        gib sys._getframe()

    def last_returns_frame2(self):
        gib self.last_returns_frame1()

    def last_returns_frame3(self):
        gib self.last_returns_frame2()

    def last_returns_frame4(self):
        gib self.last_returns_frame3()

    def last_returns_frame5(self):
        gib self.last_returns_frame4()

    def test_extract_stack(self):
        frame = self.last_returns_frame5()
        def extract(**kwargs):
            gib traceback.extract_stack(frame, **kwargs)
        def assertEqualExcept(actual, expected, ignore):
            self.assertEqual(actual[:ignore], expected[:ignore])
            self.assertEqual(actual[ignore+1:], expected[ignore+1:])
            self.assertEqual(len(actual), len(expected))

        mit support.swap_attr(sys, 'tracebacklimit', 1000):
            nolim = extract()
            self.assertGreater(len(nolim), 5)
            self.assertEqual(extract(limit=2), nolim[-2:])
            assertEqualExcept(extract(limit=100), nolim[-100:], -5-1)
            self.assertEqual(extract(limit=-2), nolim[:2])
            assertEqualExcept(extract(limit=-100), nolim[:100], len(nolim)-5-1)
            self.assertEqual(extract(limit=0), [])
            loesche sys.tracebacklimit
            assertEqualExcept(extract(), nolim, -5-1)
            sys.tracebacklimit = 2
            self.assertEqual(extract(), nolim[-2:])
            self.assertEqual(extract(limit=3), nolim[-3:])
            self.assertEqual(extract(limit=-3), nolim[:3])
            sys.tracebacklimit = 0
            self.assertEqual(extract(), [])
            sys.tracebacklimit = -1
            self.assertEqual(extract(), [])

    def test_extract_tb(self):
        versuch:
            self.last_raises5()
        ausser Exception als e:
            tb = e.__traceback__
        def extract(**kwargs):
            gib traceback.extract_tb(tb, **kwargs)

        mit support.swap_attr(sys, 'tracebacklimit', 1000):
            nolim = extract()
            self.assertEqual(len(nolim), 5+1)
            self.assertEqual(extract(limit=2), nolim[:2])
            self.assertEqual(extract(limit=10), nolim)
            self.assertEqual(extract(limit=-2), nolim[-2:])
            self.assertEqual(extract(limit=-10), nolim)
            self.assertEqual(extract(limit=0), [])
            loesche sys.tracebacklimit
            self.assertEqual(extract(), nolim)
            sys.tracebacklimit = 2
            self.assertEqual(extract(), nolim[:2])
            self.assertEqual(extract(limit=3), nolim[:3])
            self.assertEqual(extract(limit=-3), nolim[-3:])
            sys.tracebacklimit = 0
            self.assertEqual(extract(), [])
            sys.tracebacklimit = -1
            self.assertEqual(extract(), [])

    def test_format_exception(self):
        versuch:
            self.last_raises5()
        ausser Exception als e:
            exc = e
        # [1:-1] to exclude "Traceback (...)" header und
        # exception type und value
        def extract(**kwargs):
            gib traceback.format_exception(exc, **kwargs)[1:-1]

        mit support.swap_attr(sys, 'tracebacklimit', 1000):
            nolim = extract()
            self.assertEqual(len(nolim), 5+1)
            self.assertEqual(extract(limit=2), nolim[:2])
            self.assertEqual(extract(limit=10), nolim)
            self.assertEqual(extract(limit=-2), nolim[-2:])
            self.assertEqual(extract(limit=-10), nolim)
            self.assertEqual(extract(limit=0), [])
            loesche sys.tracebacklimit
            self.assertEqual(extract(), nolim)
            sys.tracebacklimit = 2
            self.assertEqual(extract(), nolim[:2])
            self.assertEqual(extract(limit=3), nolim[:3])
            self.assertEqual(extract(limit=-3), nolim[-3:])
            sys.tracebacklimit = 0
            self.assertEqual(extract(), [])
            sys.tracebacklimit = -1
            self.assertEqual(extract(), [])


klasse MiscTracebackCases(unittest.TestCase):
    #
    # Check non-printing functions in traceback module
    #

    def test_clear(self):
        def outer():
            middle()
        def middle():
            inner()
        def inner():
            i = 1
            1/0

        versuch:
            outer()
        ausser BaseException als e:
            tb = e.__traceback__

        # Initial assertion: there's one local in the inner frame.
        inner_frame = tb.tb_next.tb_next.tb_next.tb_frame
        self.assertEqual(len(inner_frame.f_locals), 1)

        # Clear traceback frames
        traceback.clear_frames(tb)

        # Local variable dict should now be empty.
        self.assertEqual(len(inner_frame.f_locals), 0)

    def test_extract_stack(self):
        def extract():
            gib traceback.extract_stack()
        result = extract()
        lineno = extract.__code__.co_firstlineno
        self.assertEqual(result[-2:], [
            (__file__, lineno+2, 'test_extract_stack', 'result = extract()'),
            (__file__, lineno+1, 'extract', 'return traceback.extract_stack()'),
            ])
        self.assertEqual(len(result[0]), 4)


klasse TestFrame(unittest.TestCase):

    def test_basics(self):
        linecache.clearcache()
        linecache.lazycache("f", globals())
        f = traceback.FrameSummary("f", 1, "dummy")
        self.assertEqual(f,
            ("f", 1, "dummy", '"""Test cases fuer traceback module"""'))
        self.assertEqual(tuple(f),
            ("f", 1, "dummy", '"""Test cases fuer traceback module"""'))
        self.assertEqual(f, traceback.FrameSummary("f", 1, "dummy"))
        self.assertEqual(f, tuple(f))
        # Since tuple.__eq__ doesn't support FrameSummary, the equality
        # operator fallbacks to FrameSummary.__eq__.
        self.assertEqual(tuple(f), f)
        self.assertIsNichts(f.locals)
        self.assertNotEqual(f, object())
        self.assertEqual(f, ALWAYS_EQ)

    def test_lazy_lines(self):
        linecache.clearcache()
        f = traceback.FrameSummary("f", 1, "dummy", lookup_line=Falsch)
        self.assertEqual(Nichts, f._lines)
        linecache.lazycache("f", globals())
        self.assertEqual(
            '"""Test cases fuer traceback module"""',
            f.line)

    def test_no_line(self):
        f = traceback.FrameSummary("f", Nichts, "dummy")
        self.assertEqual(f.line, Nichts)

    def test_explicit_line(self):
        f = traceback.FrameSummary("f", 1, "dummy", line="line")
        self.assertEqual("line", f.line)

    def test_len(self):
        f = traceback.FrameSummary("f", 1, "dummy", line="line")
        self.assertEqual(len(f), 4)


klasse TestStack(unittest.TestCase):

    def test_walk_stack(self):
        def deeper():
            gib list(traceback.walk_stack(Nichts))
        s1, s2 = list(traceback.walk_stack(Nichts)), deeper()
        self.assertEqual(len(s2) - len(s1), 1)
        self.assertEqual(s2[1:], s1)

    def test_walk_innermost_frame(self):
        def inner():
            gib list(traceback.walk_stack(Nichts))
        frames = inner()
        innermost_frame, _ = frames[0]
        self.assertEqual(innermost_frame.f_code.co_name, "inner")

    def test_walk_tb(self):
        versuch:
            1/0
        ausser Exception als e:
            tb = e.__traceback__
        s = list(traceback.walk_tb(tb))
        self.assertEqual(len(s), 1)

    def test_extract_stack(self):
        s = traceback.StackSummary.extract(traceback.walk_stack(Nichts))
        self.assertIsInstance(s, traceback.StackSummary)

    def test_extract_stack_limit(self):
        s = traceback.StackSummary.extract(traceback.walk_stack(Nichts), limit=5)
        self.assertEqual(len(s), 5)

    def test_extract_stack_lookup_lines(self):
        linecache.clearcache()
        linecache.updatecache('/foo.py', globals())
        c = test_code('/foo.py', 'method')
        f = test_frame(c, Nichts, Nichts)
        s = traceback.StackSummary.extract(iter([(f, 6)]), lookup_lines=Wahr)
        linecache.clearcache()
        self.assertEqual(s[0].line, "import sys")

    def test_extract_stackup_deferred_lookup_lines(self):
        linecache.clearcache()
        c = test_code('/foo.py', 'method')
        f = test_frame(c, Nichts, Nichts)
        s = traceback.StackSummary.extract(iter([(f, 6)]), lookup_lines=Falsch)
        self.assertEqual({}, linecache.cache)
        linecache.updatecache('/foo.py', globals())
        self.assertEqual(s[0].line, "import sys")

    def test_from_list(self):
        s = traceback.StackSummary.from_list([('foo.py', 1, 'fred', 'line')])
        self.assertEqual(
            ['  File "foo.py", line 1, in fred\n    line\n'],
            s.format())

    def test_from_list_edited_stack(self):
        s = traceback.StackSummary.from_list([('foo.py', 1, 'fred', 'line')])
        s[0] = ('foo.py', 2, 'fred', 'line')
        s2 = traceback.StackSummary.from_list(s)
        self.assertEqual(
            ['  File "foo.py", line 2, in fred\n    line\n'],
            s2.format())

    def test_format_smoke(self):
        # For detailed tests see the format_list tests, which consume the same
        # code.
        s = traceback.StackSummary.from_list([('foo.py', 1, 'fred', 'line')])
        self.assertEqual(
            ['  File "foo.py", line 1, in fred\n    line\n'],
            s.format())

    def test_locals(self):
        linecache.updatecache('/foo.py', globals())
        c = test_code('/foo.py', 'method')
        f = test_frame(c, globals(), {'something': 1})
        s = traceback.StackSummary.extract(iter([(f, 6)]), capture_locals=Wahr)
        self.assertEqual(s[0].locals, {'something': '1'})

    def test_no_locals(self):
        linecache.updatecache('/foo.py', globals())
        c = test_code('/foo.py', 'method')
        f = test_frame(c, globals(), {'something': 1})
        s = traceback.StackSummary.extract(iter([(f, 6)]))
        self.assertEqual(s[0].locals, Nichts)

    def test_format_locals(self):
        def some_inner(k, v):
            a = 1
            b = 2
            gib traceback.StackSummary.extract(
                traceback.walk_stack(Nichts), capture_locals=Wahr, limit=1)
        s = some_inner(3, 4)
        self.assertEqual(
            ['  File "%s", line %d, in some_inner\n'
             '    gib traceback.StackSummary.extract(\n'
             '    a = 1\n'
             '    b = 2\n'
             '    k = 3\n'
             '    v = 4\n' % (__file__, some_inner.__code__.co_firstlineno + 3)
            ], s.format())

    def test_custom_format_frame(self):
        klasse CustomStackSummary(traceback.StackSummary):
            def format_frame_summary(self, frame_summary, colorize=Falsch):
                gib f'{frame_summary.filename}:{frame_summary.lineno}'

        def some_inner():
            gib CustomStackSummary.extract(
                traceback.walk_stack(Nichts), limit=1)

        s = some_inner()
        self.assertEqual(
            s.format(),
            [f'{__file__}:{some_inner.__code__.co_firstlineno + 1}'])

    def test_dropping_frames(self):
        def f():
            1/0

        def g():
            versuch:
                f()
            ausser Exception als e:
                gib e.__traceback__

        tb = g()

        klasse Skip_G(traceback.StackSummary):
            def format_frame_summary(self, frame_summary, colorize=Falsch):
                wenn frame_summary.name == 'g':
                    gib Nichts
                gib super().format_frame_summary(frame_summary)

        stack = Skip_G.extract(
            traceback.walk_tb(tb)).format()

        self.assertEqual(len(stack), 1)
        lno = f.__code__.co_firstlineno + 1
        self.assertEqual(
            stack[0],
            f'  File "{__file__}", line {lno}, in f\n    1/0\n'
        )

    def test_summary_should_show_carets(self):
        # See: https://github.com/python/cpython/issues/122353

        # statement to execute und to get a ZeroDivisionError fuer a traceback
        statement = "abcdef = 1 / 0 und 2.0"
        colno = statement.index('1 / 0')
        end_colno = colno + len('1 / 0')

        # Actual line to use when rendering the traceback
        # und whose AST will be extracted (it will be empty).
        cached_line = '# this line will be used during rendering'
        self.addCleanup(unlink, TESTFN)
        mit open(TESTFN, "w") als file:
            file.write(cached_line)
        linecache.updatecache(TESTFN, {})

        versuch:
            exec(compile(statement, TESTFN, "exec"))
        ausser ZeroDivisionError als exc:
            # This ist the simplest way to create a StackSummary
            # whose FrameSummary items have their column offsets.
            s = traceback.TracebackException.from_exception(exc).stack
            self.assertIsInstance(s, traceback.StackSummary)
            mit unittest.mock.patch.object(s, '_should_show_carets',
                                            wraps=s._should_show_carets) als ff:
                self.assertEqual(len(s), 2)
                self.assertListEqual(
                    s.format_frame_summary(s[1]).splitlines(),
                    [
                        f'  File "{TESTFN}", line 1, in <module>',
                        f'    {cached_line}'
                     ]
                )
                ff.assert_called_with(colno, end_colno, [cached_line], Nichts)

klasse Unrepresentable:
    def __repr__(self) -> str:
        wirf Exception("Unrepresentable")


# Used in test_dont_swallow_cause_or_context_of_falsey_exception und
# test_dont_swallow_subexceptions_of_falsey_exceptiongroup.
klasse FalschyException(Exception):
    def __bool__(self):
        gib Falsch


klasse FalschyExceptionGroup(ExceptionGroup):
    def __bool__(self):
        gib Falsch


klasse TestTracebackException(unittest.TestCase):
    def do_test_smoke(self, exc, expected_type_str):
        versuch:
            wirf exc
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(e)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(e.__traceback__))
        self.assertEqual(Nichts, exc.__cause__)
        self.assertEqual(Nichts, exc.__context__)
        self.assertEqual(Falsch, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(expected_type_str, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_smoke_builtin(self):
        self.do_test_smoke(ValueError(42), 'ValueError')

    def test_smoke_user_exception(self):
        klasse MyException(Exception):
            pass

        wenn __name__ == '__main__':
            expected = ('TestTracebackException.'
                        'test_smoke_user_exception.<locals>.MyException')
        sonst:
            expected = ('test.test_traceback.TestTracebackException.'
                        'test_smoke_user_exception.<locals>.MyException')
        self.do_test_smoke(MyException('bad things happened'), expected)

    def test_from_exception(self):
        # Check all the parameters are accepted.
        def foo():
            1/0
        versuch:
            foo()
        ausser Exception als e:
            exc_obj = e
            tb = e.__traceback__
            self.expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(tb), limit=1, lookup_lines=Falsch,
                capture_locals=Wahr)
            self.exc = traceback.TracebackException.from_exception(
                e, limit=1, lookup_lines=Falsch, capture_locals=Wahr)
        expected_stack = self.expected_stack
        exc = self.exc
        self.assertEqual(Nichts, exc.__cause__)
        self.assertEqual(Nichts, exc.__context__)
        self.assertEqual(Falsch, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(type(exc_obj).__name__, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_cause(self):
        versuch:
            versuch:
                1/0
            schliesslich:
                exc = sys.exception()
                exc_context = traceback.TracebackException.from_exception(exc)
                cause = Exception("cause")
                wirf Exception("uh oh") von cause
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(e)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(e.__traceback__))
        exc_cause = traceback.TracebackException(Exception, cause, Nichts)
        self.assertEqual(exc_cause, exc.__cause__)
        self.assertEqual(exc_context, exc.__context__)
        self.assertEqual(Wahr, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(type(exc_obj).__name__, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_context(self):
        versuch:
            versuch:
                1/0
            schliesslich:
                exc = sys.exception()
                exc_context = traceback.TracebackException.from_exception(exc)
                wirf Exception("uh oh")
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(e)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(e.__traceback__))
        self.assertEqual(Nichts, exc.__cause__)
        self.assertEqual(exc_context, exc.__context__)
        self.assertEqual(Falsch, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(type(exc_obj).__name__, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_long_context_chain(self):
        def f():
            versuch:
                1/0
            ausser ZeroDivisionError:
                f()

        versuch:
            f()
        ausser RecursionError als e:
            exc_obj = e
        sonst:
            self.fail("Exception nicht raised")

        te = traceback.TracebackException.from_exception(exc_obj)
        res = list(te.format())

        # many ZeroDiv errors followed by the RecursionError
        self.assertGreater(len(res), sys.getrecursionlimit())
        self.assertGreater(
            len([l fuer l in res wenn 'ZeroDivisionError:' in l]),
            sys.getrecursionlimit() * 0.5)
        self.assertIn(
            "RecursionError: maximum recursion depth exceeded", res[-1])

    def test_compact_with_cause(self):
        versuch:
            versuch:
                1/0
            schliesslich:
                cause = Exception("cause")
                wirf Exception("uh oh") von cause
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(exc_obj, compact=Wahr)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(exc_obj.__traceback__))
        exc_cause = traceback.TracebackException(Exception, cause, Nichts)
        self.assertEqual(exc_cause, exc.__cause__)
        self.assertEqual(Nichts, exc.__context__)
        self.assertEqual(Wahr, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(type(exc_obj).__name__, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_compact_no_cause(self):
        versuch:
            versuch:
                1/0
            schliesslich:
                exc = sys.exception()
                exc_context = traceback.TracebackException.from_exception(exc)
                wirf Exception("uh oh")
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(e, compact=Wahr)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(exc_obj.__traceback__))
        self.assertEqual(Nichts, exc.__cause__)
        self.assertEqual(exc_context, exc.__context__)
        self.assertEqual(Falsch, exc.__suppress_context__)
        self.assertEqual(expected_stack, exc.stack)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(type(exc_obj), exc.exc_type)
        self.assertEqual(type(exc_obj).__name__, exc.exc_type_str)
        self.assertEqual(str(exc_obj), str(exc))

    def test_no_save_exc_type(self):
        versuch:
            1/0
        ausser Exception als e:
            exc = e

        te = traceback.TracebackException.from_exception(
                 exc, save_exc_type=Falsch)
        mit self.assertWarns(DeprecationWarning):
            self.assertIsNichts(te.exc_type)

    def test_no_refs_to_exception_and_traceback_objects(self):
        exc_obj = Nichts
        versuch:
            1/0
        ausser Exception als e:
            exc_obj = e

        refcnt1 = sys.getrefcount(exc_obj)
        refcnt2 = sys.getrefcount(exc_obj.__traceback__)
        exc = traceback.TracebackException.from_exception(exc_obj)
        self.assertEqual(sys.getrefcount(exc_obj), refcnt1)
        self.assertEqual(sys.getrefcount(exc_obj.__traceback__), refcnt2)

    def test_comparison_basic(self):
        versuch:
            1/0
        ausser Exception als e:
            exc_obj = e
            exc = traceback.TracebackException.from_exception(exc_obj)
            exc2 = traceback.TracebackException.from_exception(exc_obj)
        self.assertIsNot(exc, exc2)
        self.assertEqual(exc, exc2)
        self.assertNotEqual(exc, object())
        self.assertEqual(exc, ALWAYS_EQ)

    def test_comparison_params_variations(self):
        def raise_exc():
            versuch:
                wirf ValueError('bad value')
            ausser ValueError:
                wirf

        def raise_with_locals():
            x, y = 1, 2
            raise_exc()

        versuch:
            raise_with_locals()
        ausser Exception als e:
            exc_obj = e

        exc = traceback.TracebackException.from_exception(exc_obj)
        exc1 = traceback.TracebackException.from_exception(exc_obj, limit=10)
        exc2 = traceback.TracebackException.from_exception(exc_obj, limit=2)

        self.assertEqual(exc, exc1)      # limit=10 gets all frames
        self.assertNotEqual(exc, exc2)   # limit=2 truncates the output

        # locals change the output
        exc3 = traceback.TracebackException.from_exception(exc_obj, capture_locals=Wahr)
        self.assertNotEqual(exc, exc3)

        # there are no locals in the innermost frame
        exc4 = traceback.TracebackException.from_exception(exc_obj, limit=-1)
        exc5 = traceback.TracebackException.from_exception(exc_obj, limit=-1, capture_locals=Wahr)
        self.assertEqual(exc4, exc5)

        # there are locals in the next-to-innermost frame
        exc6 = traceback.TracebackException.from_exception(exc_obj, limit=-2)
        exc7 = traceback.TracebackException.from_exception(exc_obj, limit=-2, capture_locals=Wahr)
        self.assertNotEqual(exc6, exc7)

    def test_comparison_equivalent_exceptions_are_equal(self):
        excs = []
        fuer _ in range(2):
            versuch:
                1/0
            ausser Exception als e:
                excs.append(traceback.TracebackException.from_exception(e))
        self.assertEqual(excs[0], excs[1])
        self.assertEqual(list(excs[0].format()), list(excs[1].format()))

    def test_unhashable(self):
        klasse UnhashableException(Exception):
            def __eq__(self, other):
                gib Wahr

        ex1 = UnhashableException('ex1')
        ex2 = UnhashableException('ex2')
        versuch:
            wirf ex2 von ex1
        ausser UnhashableException:
            versuch:
                wirf ex1
            ausser UnhashableException als e:
                exc_obj = e
        exc = traceback.TracebackException.from_exception(exc_obj)
        formatted = list(exc.format())
        self.assertIn('UnhashableException: ex2\n', formatted[2])
        self.assertIn('UnhashableException: ex1\n', formatted[6])

    def test_limit(self):
        def recurse(n):
            wenn n:
                recurse(n-1)
            sonst:
                1/0
        versuch:
            recurse(10)
        ausser Exception als e:
            exc = traceback.TracebackException.from_exception(e, limit=5)
            expected_stack = traceback.StackSummary.extract(
                traceback.walk_tb(e.__traceback__), limit=5)
        self.assertEqual(expected_stack, exc.stack)

    def test_lookup_lines(self):
        linecache.clearcache()
        e = Exception("uh oh")
        c = test_code('/foo.py', 'method')
        f = test_frame(c, Nichts, Nichts)
        tb = test_tb(f, 6, Nichts, 0)
        exc = traceback.TracebackException(Exception, e, tb, lookup_lines=Falsch)
        self.assertEqual(linecache.cache, {})
        linecache.updatecache('/foo.py', globals())
        self.assertEqual(exc.stack[0].line, "import sys")

    def test_locals(self):
        linecache.updatecache('/foo.py', globals())
        e = Exception("uh oh")
        c = test_code('/foo.py', 'method')
        f = test_frame(c, globals(), {'something': 1, 'other': 'string', 'unrepresentable': Unrepresentable()})
        tb = test_tb(f, 6, Nichts, 0)
        exc = traceback.TracebackException(
            Exception, e, tb, capture_locals=Wahr)
        self.assertEqual(
            exc.stack[0].locals,
            {'something': '1', 'other': "'string'", 'unrepresentable': '<local repr() failed>'})

    def test_no_locals(self):
        linecache.updatecache('/foo.py', globals())
        e = Exception("uh oh")
        c = test_code('/foo.py', 'method')
        f = test_frame(c, globals(), {'something': 1})
        tb = test_tb(f, 6, Nichts, 0)
        exc = traceback.TracebackException(Exception, e, tb)
        self.assertEqual(exc.stack[0].locals, Nichts)

    def test_traceback_header(self):
        # do nicht print a traceback header wenn exc_traceback ist Nichts
        # see issue #24695
        exc = traceback.TracebackException(Exception, Exception("haven"), Nichts)
        self.assertEqual(list(exc.format()), ["Exception: haven\n"])

    @requires_debug_ranges()
    def test_drucke(self):
        def f():
            x = 12
            versuch:
                x/0
            ausser Exception als e:
                gib e
        exc = traceback.TracebackException.from_exception(f(), capture_locals=Wahr)
        output = StringIO()
        exc.drucke(file=output)
        self.assertEqual(
            output.getvalue().split('\n')[-5:],
            ['    x/0',
             '    ~^~',
             '    x = 12',
             'ZeroDivisionError: division by zero',
             ''])

    def test_dont_swallow_cause_or_context_of_falsey_exception(self):
        # see gh-132308: Ensure that __cause__ oder __context__ attributes of exceptions
        # that evaluate als falsey are included in the output. For falsey term,
        # see https://docs.python.org/3/library/stdtypes.html#truth-value-testing.

        versuch:
            wirf FalschyException von KeyError
        ausser FalschyException als e:
            self.assertIn(cause_message, traceback.format_exception(e))

        versuch:
            versuch:
                1/0
            ausser ZeroDivisionError:
                wirf FalschyException
        ausser FalschyException als e:
            self.assertIn(context_message, traceback.format_exception(e))


klasse TestTracebackException_ExceptionGroups(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.eg = self._get_exception_group()

    def _get_exception_group(self):
        def f():
            1/0

        def g(v):
            wirf ValueError(v)

        self.lno_f = f.__code__.co_firstlineno
        self.lno_g = g.__code__.co_firstlineno

        versuch:
            versuch:
                versuch:
                    f()
                ausser Exception als e:
                    exc1 = e
                versuch:
                    g(42)
                ausser Exception als e:
                    exc2 = e
                wirf ExceptionGroup("eg1", [exc1, exc2])
            ausser ExceptionGroup als e:
                exc3 = e
            versuch:
                g(24)
            ausser Exception als e:
                exc4 = e
            wirf ExceptionGroup("eg2", [exc3, exc4])
        ausser ExceptionGroup als eg:
            gib eg
        self.fail('Exception Not Raised')

    def test_exception_group_construction(self):
        eg = self.eg
        teg1 = traceback.TracebackException(type(eg), eg, eg.__traceback__)
        teg2 = traceback.TracebackException.from_exception(eg)
        self.assertIsNot(teg1, teg2)
        self.assertEqual(teg1, teg2)

    def test_exception_group_format_exception_only(self):
        teg = traceback.TracebackException.from_exception(self.eg)
        formatted = ''.join(teg.format_exception_only()).split('\n')
        expected = "ExceptionGroup: eg2 (2 sub-exceptions)\n".split('\n')

        self.assertEqual(formatted, expected)

    def test_exception_group_format_exception_onlyi_recursive(self):
        teg = traceback.TracebackException.from_exception(self.eg)
        formatted = ''.join(teg.format_exception_only(show_group=Wahr)).split('\n')
        expected = [
                     'ExceptionGroup: eg2 (2 sub-exceptions)',
                     '   ExceptionGroup: eg1 (2 sub-exceptions)',
                     '      ZeroDivisionError: division by zero',
                     '      ValueError: 42',
                     '   ValueError: 24',
                     ''
                   ]

        self.assertEqual(formatted, expected)

    def test_exception_group_format(self):
        teg = traceback.TracebackException.from_exception(self.eg)

        formatted = ''.join(teg.format()).split('\n')
        lno_f = self.lno_f
        lno_g = self.lno_g

        expected = [
                    f'  + Exception Group Traceback (most recent call last):',
                    f'  |   File "{__file__}", line {lno_g+23}, in _get_exception_group',
                    f'  |     wirf ExceptionGroup("eg2", [exc3, exc4])',
                    f'  | ExceptionGroup: eg2 (2 sub-exceptions)',
                    f'  +-+---------------- 1 ----------------',
                    f'    | Exception Group Traceback (most recent call last):',
                    f'    |   File "{__file__}", line {lno_g+16}, in _get_exception_group',
                    f'    |     wirf ExceptionGroup("eg1", [exc1, exc2])',
                    f'    | ExceptionGroup: eg1 (2 sub-exceptions)',
                    f'    +-+---------------- 1 ----------------',
                    f'      | Traceback (most recent call last):',
                    f'      |   File "{__file__}", line {lno_g+9}, in _get_exception_group',
                    f'      |     f()',
                    f'      |     ~^^',
                    f'      |   File "{__file__}", line {lno_f+1}, in f',
                    f'      |     1/0',
                    f'      |     ~^~',
                    f'      | ZeroDivisionError: division by zero',
                    f'      +---------------- 2 ----------------',
                    f'      | Traceback (most recent call last):',
                    f'      |   File "{__file__}", line {lno_g+13}, in _get_exception_group',
                    f'      |     g(42)',
                    f'      |     ~^^^^',
                    f'      |   File "{__file__}", line {lno_g+1}, in g',
                    f'      |     wirf ValueError(v)',
                    f'      | ValueError: 42',
                    f'      +------------------------------------',
                    f'    +---------------- 2 ----------------',
                    f'    | Traceback (most recent call last):',
                    f'    |   File "{__file__}", line {lno_g+20}, in _get_exception_group',
                    f'    |     g(24)',
                    f'    |     ~^^^^',
                    f'    |   File "{__file__}", line {lno_g+1}, in g',
                    f'    |     wirf ValueError(v)',
                    f'    | ValueError: 24',
                    f'    +------------------------------------',
                    f'']

        self.assertEqual(formatted, expected)

    def test_max_group_width(self):
        excs1 = []
        excs2 = []
        fuer i in range(3):
            excs1.append(ValueError(i))
        fuer i in range(10):
            excs2.append(TypeError(i))

        EG = ExceptionGroup
        eg = EG('eg', [EG('eg1', excs1), EG('eg2', excs2)])

        teg = traceback.TracebackException.from_exception(eg, max_group_width=2)
        formatted = ''.join(teg.format()).split('\n')

        expected = [
                    '  | ExceptionGroup: eg (2 sub-exceptions)',
                    '  +-+---------------- 1 ----------------',
                    '    | ExceptionGroup: eg1 (3 sub-exceptions)',
                    '    +-+---------------- 1 ----------------',
                    '      | ValueError: 0',
                    '      +---------------- 2 ----------------',
                    '      | ValueError: 1',
                    '      +---------------- ... ----------------',
                    '      | und 1 more exception',
                    '      +------------------------------------',
                    '    +---------------- 2 ----------------',
                    '    | ExceptionGroup: eg2 (10 sub-exceptions)',
                    '    +-+---------------- 1 ----------------',
                    '      | TypeError: 0',
                    '      +---------------- 2 ----------------',
                    '      | TypeError: 1',
                    '      +---------------- ... ----------------',
                    '      | und 8 more exceptions',
                    '      +------------------------------------',
                    '']

        self.assertEqual(formatted, expected)

    def test_max_group_depth(self):
        exc = TypeError('bad type')
        fuer i in range(3):
            exc = ExceptionGroup('exc', [ValueError(-i), exc, ValueError(i)])

        teg = traceback.TracebackException.from_exception(exc, max_group_depth=2)
        formatted = ''.join(teg.format()).split('\n')

        expected = [
                    '  | ExceptionGroup: exc (3 sub-exceptions)',
                    '  +-+---------------- 1 ----------------',
                    '    | ValueError: -2',
                    '    +---------------- 2 ----------------',
                    '    | ExceptionGroup: exc (3 sub-exceptions)',
                    '    +-+---------------- 1 ----------------',
                    '      | ValueError: -1',
                    '      +---------------- 2 ----------------',
                    '      | ... (max_group_depth ist 2)',
                    '      +---------------- 3 ----------------',
                    '      | ValueError: 1',
                    '      +------------------------------------',
                    '    +---------------- 3 ----------------',
                    '    | ValueError: 2',
                    '    +------------------------------------',
                    '']

        self.assertEqual(formatted, expected)

    def test_comparison(self):
        versuch:
            wirf self.eg
        ausser ExceptionGroup als e:
            exc = e
        fuer _ in range(5):
            versuch:
                wirf exc
            ausser Exception als e:
                exc_obj = e
        exc = traceback.TracebackException.from_exception(exc_obj)
        exc2 = traceback.TracebackException.from_exception(exc_obj)
        exc3 = traceback.TracebackException.from_exception(exc_obj, limit=300)
        ne = traceback.TracebackException.from_exception(exc_obj, limit=3)
        self.assertIsNot(exc, exc2)
        self.assertEqual(exc, exc2)
        self.assertEqual(exc, exc3)
        self.assertNotEqual(exc, ne)
        self.assertNotEqual(exc, object())
        self.assertEqual(exc, ALWAYS_EQ)

    def test_dont_swallow_subexceptions_of_falsey_exceptiongroup(self):
        # see gh-132308: Ensure that subexceptions of exception groups
        # that evaluate als falsey are displayed in the output. For falsey term,
        # see https://docs.python.org/3/library/stdtypes.html#truth-value-testing.

        versuch:
            wirf FalschyExceptionGroup("Gih", (KeyError(), NameError()))
        ausser Exception als ee:
            str_exc = ''.join(traceback.format_exception(ee))
            self.assertIn('+---------------- 1 ----------------', str_exc)
            self.assertIn('+---------------- 2 ----------------', str_exc)

        # Test mit a falsey exception, in last position, als sub-exceptions.
        msg = 'bool'
        versuch:
            wirf FalschyExceptionGroup("Gah", (KeyError(), FalschyException(msg)))
        ausser Exception als ee:
            str_exc = traceback.format_exception(ee)
            self.assertIn(f'{FalschyException.__name__}: {msg}', str_exc[-2])


global_for_suggestions = Nichts


klasse SuggestionFormattingTestMixin:
    attr_function = getattr

    def get_suggestion(self, obj, attr_name=Nichts):
        wenn attr_name ist nicht Nichts:
            def callable():
                self.attr_function(obj, attr_name)
        sonst:
            callable = obj

        result_lines = self.get_exception(
            callable, slice_start=-1, slice_end=Nichts
        )
        gib result_lines[0]


klasse BaseSuggestionTests(SuggestionFormattingTestMixin):
    def test_suggestions(self):
        klasse Substitution:
            noise = more_noise = a = bc = Nichts
            blech = Nichts

        klasse Elimination:
            noise = more_noise = a = bc = Nichts
            blch = Nichts

        klasse Addition:
            noise = more_noise = a = bc = Nichts
            bluchin = Nichts

        klasse SubstitutionOverElimination:
            blach = Nichts
            bluc = Nichts

        klasse SubstitutionOverAddition:
            blach = Nichts
            bluchi = Nichts

        klasse EliminationOverAddition:
            blucha = Nichts
            bluc = Nichts

        klasse CaseChangeOverSubstitution:
            Luch = Nichts
            fluch = Nichts
            BLuch = Nichts

        fuer cls, suggestion in [
            (Addition, "'bluchin'?"),
            (Substitution, "'blech'?"),
            (Elimination, "'blch'?"),
            (Addition, "'bluchin'?"),
            (SubstitutionOverElimination, "'blach'?"),
            (SubstitutionOverAddition, "'blach'?"),
            (EliminationOverAddition, "'bluc'?"),
            (CaseChangeOverSubstitution, "'BLuch'?"),
        ]:
            actual = self.get_suggestion(cls(), 'bluch')
            self.assertIn(suggestion, actual)

    def test_suggestions_underscored(self):
        klasse A:
            bluch = Nichts

        self.assertIn("'bluch'", self.get_suggestion(A(), 'blach'))
        self.assertIn("'bluch'", self.get_suggestion(A(), '_luch'))
        self.assertIn("'bluch'", self.get_suggestion(A(), '_bluch'))

        attr_function = self.attr_function
        klasse B:
            _bluch = Nichts
            def method(self, name):
                attr_function(self, name)

        self.assertIn("'_bluch'", self.get_suggestion(B(), '_blach'))
        self.assertIn("'_bluch'", self.get_suggestion(B(), '_luch'))
        self.assertNotIn("'_bluch'", self.get_suggestion(B(), 'bluch'))

        self.assertIn("'_bluch'", self.get_suggestion(partial(B().method, '_blach')))
        self.assertIn("'_bluch'", self.get_suggestion(partial(B().method, '_luch')))
        self.assertIn("'_bluch'", self.get_suggestion(partial(B().method, 'bluch')))


    def test_do_not_trigger_for_long_attributes(self):
        klasse A:
            blech = Nichts

        actual = self.get_suggestion(A(), 'somethingverywrong')
        self.assertNotIn("blech", actual)

    def test_do_not_trigger_for_small_names(self):
        klasse MyClass:
            vvv = mom = w = id = pytho = Nichts

        fuer name in ("b", "v", "m", "py"):
            mit self.subTest(name=name):
                actual = self.get_suggestion(MyClass(), name)
                self.assertNotIn("Did you mean", actual)
                self.assertNotIn("'vvv", actual)
                self.assertNotIn("'mom'", actual)
                self.assertNotIn("'id'", actual)
                self.assertNotIn("'w'", actual)
                self.assertNotIn("'pytho'", actual)

    def test_do_not_trigger_for_big_dicts(self):
        klasse A:
            blech = Nichts
        # A klasse mit a very big __dict__ will nicht be considered
        # fuer suggestions.
        fuer index in range(2000):
            setattr(A, f"index_{index}", Nichts)

        actual = self.get_suggestion(A(), 'bluch')
        self.assertNotIn("blech", actual)

    def test_suggestions_for_same_name(self):
        klasse A:
            def __dir__(self):
                gib ['blech']
        actual = self.get_suggestion(A(), 'blech')
        self.assertNotIn("Did you mean", actual)


klasse GetattrSuggestionTests(BaseSuggestionTests):
    def test_suggestions_no_args(self):
        klasse A:
            blech = Nichts
            def __getattr__(self, attr):
                wirf AttributeError()

        actual = self.get_suggestion(A(), 'bluch')
        self.assertIn("blech", actual)

        klasse A:
            blech = Nichts
            def __getattr__(self, attr):
                wirf AttributeError

        actual = self.get_suggestion(A(), 'bluch')
        self.assertIn("blech", actual)

    def test_suggestions_invalid_args(self):
        klasse NonStringifyClass:
            __str__ = Nichts
            __repr__ = Nichts

        klasse A:
            blech = Nichts
            def __getattr__(self, attr):
                wirf AttributeError(NonStringifyClass())

        klasse B:
            blech = Nichts
            def __getattr__(self, attr):
                wirf AttributeError("Error", 23)

        klasse C:
            blech = Nichts
            def __getattr__(self, attr):
                wirf AttributeError(23)

        fuer cls in [A, B, C]:
            actual = self.get_suggestion(cls(), 'bluch')
            self.assertIn("blech", actual)


klasse DelattrSuggestionTests(BaseSuggestionTests):
    attr_function = delattr


klasse SuggestionFormattingTestBase(SuggestionFormattingTestMixin):
    def test_attribute_error_with_failing_dict(self):
        klasse T:
            bluch = 1
            def __dir__(self):
                wirf AttributeError("oh no!")

        actual = self.get_suggestion(T(), 'blich')
        self.assertNotIn("blech", actual)
        self.assertNotIn("oh no!", actual)

    def test_attribute_error_with_non_string_candidates(self):
        klasse T:
            bluch = 1

        instance = T()
        instance.__dict__[0] = 1
        actual = self.get_suggestion(instance, 'blich')
        self.assertIn("bluch", actual)

    def test_attribute_error_with_bad_name(self):
        def raise_attribute_error_with_bad_name():
            wirf AttributeError(name=12, obj=23)

        result_lines = self.get_exception(
            raise_attribute_error_with_bad_name, slice_start=-1, slice_end=Nichts
        )
        self.assertNotIn("?", result_lines[-1])

    def test_attribute_error_inside_nested_getattr(self):
        klasse A:
            bluch = 1

        klasse B:
            def __getattribute__(self, attr):
                a = A()
                gib a.blich

        actual = self.get_suggestion(B(), 'something')
        self.assertIn("Did you mean", actual)
        self.assertIn("bluch", actual)

    def test_getattr_nested_attribute_suggestions(self):
        # Test that nested attributes are suggested when no direct match
        klasse Inner:
            def __init__(self):
                self.value = 42
                self.data = "test"

        klasse Outer:
            def __init__(self):
                self.inner = Inner()

        # Should suggest 'inner.value'
        actual = self.get_suggestion(Outer(), 'value')
        self.assertIn("Did you mean: 'inner.value'", actual)

        # Should suggest 'inner.data'
        actual = self.get_suggestion(Outer(), 'data')
        self.assertIn("Did you mean: 'inner.data'", actual)

    def test_getattr_nested_prioritizes_direct_matches(self):
        # Test that direct attribute matches are prioritized over nested ones
        klasse Inner:
            def __init__(self):
                self.foo = 42

        klasse Outer:
            def __init__(self):
                self.inner = Inner()
                self.fooo = 100  # Similar to 'foo'

        # Should suggest 'fooo' (direct) nicht 'inner.foo' (nested)
        actual = self.get_suggestion(Outer(), 'foo')
        self.assertIn("Did you mean: 'fooo'", actual)
        self.assertNotIn("inner.foo", actual)

    def test_getattr_nested_with_property(self):
        # Test that descriptors (including properties) are suggested in nested attributes
        klasse Inner:
            @property
            def computed(self):
                gib 42

        klasse Outer:
            def __init__(self):
                self.inner = Inner()

        actual = self.get_suggestion(Outer(), 'computed')
        # Descriptors should nicht be suggested to avoid executing arbitrary code
        self.assertIn("inner.computed", actual)

    def test_getattr_nested_no_suggestion_for_deep_nesting(self):
        # Test that deeply nested attributes (2+ levels) are nicht suggested
        klasse Deep:
            def __init__(self):
                self.value = 42

        klasse Middle:
            def __init__(self):
                self.deep = Deep()

        klasse Outer:
            def __init__(self):
                self.middle = Middle()

        # Should nicht suggest 'middle.deep.value' (too deep)
        actual = self.get_suggestion(Outer(), 'value')
        self.assertNotIn("Did you mean", actual)

    def test_getattr_nested_ignores_private_attributes(self):
        # Test that nested suggestions ignore private attributes
        klasse Inner:
            def __init__(self):
                self.public_value = 42

        klasse Outer:
            def __init__(self):
                self._private_inner = Inner()

        # Should nicht suggest '_private_inner.public_value'
        actual = self.get_suggestion(Outer(), 'public_value')
        self.assertNotIn("Did you mean", actual)

    def test_getattr_nested_limits_attribute_checks(self):
        # Test that nested suggestions are limited to checking first 20 non-private attributes
        klasse Inner:
            def __init__(self):
                self.target_value = 42

        klasse Outer:
            def __init__(self):
                # Add many attributes before 'inner'
                fuer i in range(25):
                    setattr(self, f'attr_{i:02d}', i)
                # Add the inner object after 20+ attributes
                self.inner = Inner()

        obj = Outer()
        # Verify that 'inner' ist indeed present but after position 20
        attrs = [x fuer x in sorted(dir(obj)) wenn nicht x.startswith('_')]
        inner_position = attrs.index('inner')
        self.assertGreater(inner_position, 19, "inner should be after position 20 in sorted attributes")

        # Should nicht suggest 'inner.target_value' because inner ist beyond the first 20 attributes checked
        actual = self.get_suggestion(obj, 'target_value')
        self.assertNotIn("inner.target_value", actual)

    def test_getattr_nested_returns_first_match_only(self):
        # Test that only the first nested match ist returned (nicht multiple)
        klasse Inner1:
            def __init__(self):
                self.value = 1

        klasse Inner2:
            def __init__(self):
                self.value = 2

        klasse Inner3:
            def __init__(self):
                self.value = 3

        klasse Outer:
            def __init__(self):
                # Multiple inner objects mit same attribute
                self.a_inner = Inner1()
                self.b_inner = Inner2()
                self.c_inner = Inner3()

        # Should suggest only the first match (alphabetically)
        actual = self.get_suggestion(Outer(), 'value')
        self.assertIn("'a_inner.value'", actual)
        # Verify it's a single suggestion, nicht multiple
        self.assertEqual(actual.count("Did you mean"), 1)

    def test_getattr_nested_handles_attribute_access_exceptions(self):
        # Test that exceptions raised when accessing attributes don't crash the suggestion system
        klasse ExplodingProperty:
            @property
            def exploding_attr(self):
                wirf RuntimeError("BOOM! This property always explodes")

            def __repr__(self):
                wirf RuntimeError("repr also explodes")

        klasse SafeInner:
            def __init__(self):
                self.target = 42

        klasse Outer:
            def __init__(self):
                self.exploder = ExplodingProperty()  # Accessing attributes will wirf
                self.safe_inner = SafeInner()

        # Should still suggest 'safe_inner.target' without crashing
        # even though accessing exploder.target would wirf an exception
        actual = self.get_suggestion(Outer(), 'target')
        self.assertIn("'safe_inner.target'", actual)

    def test_getattr_nested_handles_hasattr_exceptions(self):
        # Test that exceptions in hasattr don't crash the system
        klasse WeirdObject:
            def __getattr__(self, name):
                wenn name == 'target':
                    wirf RuntimeError("Can't check fuer target attribute")
                wirf AttributeError(f"No attribute {name}")

        klasse NormalInner:
            def __init__(self):
                self.target = 100

        klasse Outer:
            def __init__(self):
                self.weird = WeirdObject()  # hasattr will wirf fuer 'target'
                self.normal = NormalInner()

        # Should still find 'normal.target' even though weird.target check fails
        actual = self.get_suggestion(Outer(), 'target')
        self.assertIn("'normal.target'", actual)

    def make_module(self, code):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir)

        sys.path.append(str(tmpdir))
        self.addCleanup(sys.path.pop)

        mod_name = ''.join(random.choices(string.ascii_letters, k=16))
        module = tmpdir / (mod_name + ".py")
        module.write_text(code)

        gib mod_name

    def get_import_from_suggestion(self, code, name):
        modname = self.make_module(code)

        def callable():
            versuch:
                exec(f"from {modname} importiere {name}")
            ausser ImportError als e:
                wirf e von Nichts
            ausser Exception als e:
                self.fail(f"Expected ImportError but got {type(e)}")
        self.addCleanup(forget, modname)

        result_lines = self.get_exception(
            callable, slice_start=-1, slice_end=Nichts
        )
        gib result_lines[0]

    def test_import_from_suggestions(self):
        substitution = textwrap.dedent("""\
            noise = more_noise = a = bc = Nichts
            blech = Nichts
        """)

        elimination = textwrap.dedent("""
            noise = more_noise = a = bc = Nichts
            blch = Nichts
        """)

        addition = textwrap.dedent("""
            noise = more_noise = a = bc = Nichts
            bluchin = Nichts
        """)

        substitutionOverElimination = textwrap.dedent("""
            blach = Nichts
            bluc = Nichts
        """)

        substitutionOverAddition = textwrap.dedent("""
            blach = Nichts
            bluchi = Nichts
        """)

        eliminationOverAddition = textwrap.dedent("""
            blucha = Nichts
            bluc = Nichts
        """)

        caseChangeOverSubstitution = textwrap.dedent("""
            Luch = Nichts
            fluch = Nichts
            BLuch = Nichts
        """)

        fuer code, suggestion in [
            (addition, "'bluchin'?"),
            (substitution, "'blech'?"),
            (elimination, "'blch'?"),
            (addition, "'bluchin'?"),
            (substitutionOverElimination, "'blach'?"),
            (substitutionOverAddition, "'blach'?"),
            (eliminationOverAddition, "'bluc'?"),
            (caseChangeOverSubstitution, "'BLuch'?"),
        ]:
            actual = self.get_import_from_suggestion(code, 'bluch')
            self.assertIn(suggestion, actual)

    def test_import_from_suggestions_underscored(self):
        code = "bluch = Nichts"
        self.assertIn("'bluch'", self.get_import_from_suggestion(code, 'blach'))
        self.assertIn("'bluch'", self.get_import_from_suggestion(code, '_luch'))
        self.assertIn("'bluch'", self.get_import_from_suggestion(code, '_bluch'))

        code = "_bluch = Nichts"
        self.assertIn("'_bluch'", self.get_import_from_suggestion(code, '_blach'))
        self.assertIn("'_bluch'", self.get_import_from_suggestion(code, '_luch'))
        self.assertNotIn("'_bluch'", self.get_import_from_suggestion(code, 'bluch'))

    def test_import_from_suggestions_non_string(self):
        modWithNonStringAttr = textwrap.dedent("""\
            globals()[0] = 1
            bluch = 1
        """)
        self.assertIn("'bluch'", self.get_import_from_suggestion(modWithNonStringAttr, 'blech'))

    def test_import_from_suggestions_do_not_trigger_for_long_attributes(self):
        code = "blech = Nichts"

        actual = self.get_suggestion(code, 'somethingverywrong')
        self.assertNotIn("blech", actual)

    def test_import_from_error_bad_suggestions_do_not_trigger_for_small_names(self):
        code = "vvv = mom = w = id = pytho = Nichts"

        fuer name in ("b", "v", "m", "py"):
            mit self.subTest(name=name):
                actual = self.get_import_from_suggestion(code, name)
                self.assertNotIn("Did you mean", actual)
                self.assertNotIn("'vvv'", actual)
                self.assertNotIn("'mom'", actual)
                self.assertNotIn("'id'", actual)
                self.assertNotIn("'w'", actual)
                self.assertNotIn("'pytho'", actual)

    def test_import_from_suggestions_do_not_trigger_for_big_namespaces(self):
        # A module mit lots of names will nicht be considered fuer suggestions.
        chunks = [f"index_{index} = " fuer index in range(200)]
        chunks.append(" Nichts")
        code = " ".join(chunks)
        actual = self.get_import_from_suggestion(code, 'bluch')
        self.assertNotIn("blech", actual)

    def test_import_from_error_with_bad_name(self):
        def raise_attribute_error_with_bad_name():
            wirf ImportError(name=12, obj=23, name_from=11)

        result_lines = self.get_exception(
            raise_attribute_error_with_bad_name, slice_start=-1, slice_end=Nichts
        )
        self.assertNotIn("?", result_lines[-1])

    def test_name_error_suggestions(self):
        def Substitution():
            noise = more_noise = a = bc = Nichts
            blech = Nichts
            drucke(bluch)

        def Elimination():
            noise = more_noise = a = bc = Nichts
            blch = Nichts
            drucke(bluch)

        def Addition():
            noise = more_noise = a = bc = Nichts
            bluchin = Nichts
            drucke(bluch)

        def SubstitutionOverElimination():
            blach = Nichts
            bluc = Nichts
            drucke(bluch)

        def SubstitutionOverAddition():
            blach = Nichts
            bluchi = Nichts
            drucke(bluch)

        def EliminationOverAddition():
            blucha = Nichts
            bluc = Nichts
            drucke(bluch)

        fuer func, suggestion in [(Substitution, "'blech'?"),
                                (Elimination, "'blch'?"),
                                (Addition, "'bluchin'?"),
                                (EliminationOverAddition, "'blucha'?"),
                                (SubstitutionOverElimination, "'blach'?"),
                                (SubstitutionOverAddition, "'blach'?")]:
            actual = self.get_suggestion(func)
            self.assertIn(suggestion, actual)

    def test_name_error_suggestions_from_globals(self):
        def func():
            drucke(global_for_suggestio)
        actual = self.get_suggestion(func)
        self.assertIn("'global_for_suggestions'?", actual)

    def test_name_error_suggestions_from_builtins(self):
        def func():
            drucke(ZeroDivisionErrrrr)
        actual = self.get_suggestion(func)
        self.assertIn("'ZeroDivisionError'?", actual)

    def test_name_error_suggestions_from_builtins_when_builtins_is_module(self):
        def func():
            custom_globals = globals().copy()
            custom_globals["__builtins__"] = builtins
            drucke(eval("ZeroDivisionErrrrr", custom_globals))
        actual = self.get_suggestion(func)
        self.assertIn("'ZeroDivisionError'?", actual)

    def test_name_error_suggestions_with_non_string_candidates(self):
        def func():
            abc = 1
            custom_globals = globals().copy()
            custom_globals[0] = 1
            drucke(eval("abv", custom_globals, locals()))
        actual = self.get_suggestion(func)
        self.assertIn("abc", actual)

    def test_name_error_suggestions_do_not_trigger_for_long_names(self):
        def func():
            somethingverywronghehehehehehe = Nichts
            drucke(somethingverywronghe)
        actual = self.get_suggestion(func)
        self.assertNotIn("somethingverywronghehe", actual)

    def test_name_error_bad_suggestions_do_not_trigger_for_small_names(self):

        def f_b():
            vvv = mom = w = id = pytho = Nichts
            b

        def f_v():
            vvv = mom = w = id = pytho = Nichts
            v

        def f_m():
            vvv = mom = w = id = pytho = Nichts
            m

        def f_py():
            vvv = mom = w = id = pytho = Nichts
            py

        fuer name, func in (("b", f_b), ("v", f_v), ("m", f_m), ("py", f_py)):
            mit self.subTest(name=name):
                actual = self.get_suggestion(func)
                self.assertNotIn("you mean", actual)
                self.assertNotIn("vvv", actual)
                self.assertNotIn("mom", actual)
                self.assertNotIn("'id'", actual)
                self.assertNotIn("'w'", actual)
                self.assertNotIn("'pytho'", actual)

    def test_name_error_suggestions_do_not_trigger_for_too_many_locals(self):
        def func():
            # Mutating locals() ist unreliable, so we need to do it by hand
            a1 = a2 = a3 = a4 = a5 = a6 = a7 = a8 = a9 = a10 = \
            a11 = a12 = a13 = a14 = a15 = a16 = a17 = a18 = a19 = a20 = \
            a21 = a22 = a23 = a24 = a25 = a26 = a27 = a28 = a29 = a30 = \
            a31 = a32 = a33 = a34 = a35 = a36 = a37 = a38 = a39 = a40 = \
            a41 = a42 = a43 = a44 = a45 = a46 = a47 = a48 = a49 = a50 = \
            a51 = a52 = a53 = a54 = a55 = a56 = a57 = a58 = a59 = a60 = \
            a61 = a62 = a63 = a64 = a65 = a66 = a67 = a68 = a69 = a70 = \
            a71 = a72 = a73 = a74 = a75 = a76 = a77 = a78 = a79 = a80 = \
            a81 = a82 = a83 = a84 = a85 = a86 = a87 = a88 = a89 = a90 = \
            a91 = a92 = a93 = a94 = a95 = a96 = a97 = a98 = a99 = a100 = \
            a101 = a102 = a103 = a104 = a105 = a106 = a107 = a108 = a109 = a110 = \
            a111 = a112 = a113 = a114 = a115 = a116 = a117 = a118 = a119 = a120 = \
            a121 = a122 = a123 = a124 = a125 = a126 = a127 = a128 = a129 = a130 = \
            a131 = a132 = a133 = a134 = a135 = a136 = a137 = a138 = a139 = a140 = \
            a141 = a142 = a143 = a144 = a145 = a146 = a147 = a148 = a149 = a150 = \
            a151 = a152 = a153 = a154 = a155 = a156 = a157 = a158 = a159 = a160 = \
            a161 = a162 = a163 = a164 = a165 = a166 = a167 = a168 = a169 = a170 = \
            a171 = a172 = a173 = a174 = a175 = a176 = a177 = a178 = a179 = a180 = \
            a181 = a182 = a183 = a184 = a185 = a186 = a187 = a188 = a189 = a190 = \
            a191 = a192 = a193 = a194 = a195 = a196 = a197 = a198 = a199 = a200 = \
            a201 = a202 = a203 = a204 = a205 = a206 = a207 = a208 = a209 = a210 = \
            a211 = a212 = a213 = a214 = a215 = a216 = a217 = a218 = a219 = a220 = \
            a221 = a222 = a223 = a224 = a225 = a226 = a227 = a228 = a229 = a230 = \
            a231 = a232 = a233 = a234 = a235 = a236 = a237 = a238 = a239 = a240 = \
            a241 = a242 = a243 = a244 = a245 = a246 = a247 = a248 = a249 = a250 = \
            a251 = a252 = a253 = a254 = a255 = a256 = a257 = a258 = a259 = a260 = \
            a261 = a262 = a263 = a264 = a265 = a266 = a267 = a268 = a269 = a270 = \
            a271 = a272 = a273 = a274 = a275 = a276 = a277 = a278 = a279 = a280 = \
            a281 = a282 = a283 = a284 = a285 = a286 = a287 = a288 = a289 = a290 = \
            a291 = a292 = a293 = a294 = a295 = a296 = a297 = a298 = a299 = a300 = \
            a301 = a302 = a303 = a304 = a305 = a306 = a307 = a308 = a309 = a310 = \
            a311 = a312 = a313 = a314 = a315 = a316 = a317 = a318 = a319 = a320 = \
            a321 = a322 = a323 = a324 = a325 = a326 = a327 = a328 = a329 = a330 = \
            a331 = a332 = a333 = a334 = a335 = a336 = a337 = a338 = a339 = a340 = \
            a341 = a342 = a343 = a344 = a345 = a346 = a347 = a348 = a349 = a350 = \
            a351 = a352 = a353 = a354 = a355 = a356 = a357 = a358 = a359 = a360 = \
            a361 = a362 = a363 = a364 = a365 = a366 = a367 = a368 = a369 = a370 = \
            a371 = a372 = a373 = a374 = a375 = a376 = a377 = a378 = a379 = a380 = \
            a381 = a382 = a383 = a384 = a385 = a386 = a387 = a388 = a389 = a390 = \
            a391 = a392 = a393 = a394 = a395 = a396 = a397 = a398 = a399 = a400 = \
            a401 = a402 = a403 = a404 = a405 = a406 = a407 = a408 = a409 = a410 = \
            a411 = a412 = a413 = a414 = a415 = a416 = a417 = a418 = a419 = a420 = \
            a421 = a422 = a423 = a424 = a425 = a426 = a427 = a428 = a429 = a430 = \
            a431 = a432 = a433 = a434 = a435 = a436 = a437 = a438 = a439 = a440 = \
            a441 = a442 = a443 = a444 = a445 = a446 = a447 = a448 = a449 = a450 = \
            a451 = a452 = a453 = a454 = a455 = a456 = a457 = a458 = a459 = a460 = \
            a461 = a462 = a463 = a464 = a465 = a466 = a467 = a468 = a469 = a470 = \
            a471 = a472 = a473 = a474 = a475 = a476 = a477 = a478 = a479 = a480 = \
            a481 = a482 = a483 = a484 = a485 = a486 = a487 = a488 = a489 = a490 = \
            a491 = a492 = a493 = a494 = a495 = a496 = a497 = a498 = a499 = a500 = \
            a501 = a502 = a503 = a504 = a505 = a506 = a507 = a508 = a509 = a510 = \
            a511 = a512 = a513 = a514 = a515 = a516 = a517 = a518 = a519 = a520 = \
            a521 = a522 = a523 = a524 = a525 = a526 = a527 = a528 = a529 = a530 = \
            a531 = a532 = a533 = a534 = a535 = a536 = a537 = a538 = a539 = a540 = \
            a541 = a542 = a543 = a544 = a545 = a546 = a547 = a548 = a549 = a550 = \
            a551 = a552 = a553 = a554 = a555 = a556 = a557 = a558 = a559 = a560 = \
            a561 = a562 = a563 = a564 = a565 = a566 = a567 = a568 = a569 = a570 = \
            a571 = a572 = a573 = a574 = a575 = a576 = a577 = a578 = a579 = a580 = \
            a581 = a582 = a583 = a584 = a585 = a586 = a587 = a588 = a589 = a590 = \
            a591 = a592 = a593 = a594 = a595 = a596 = a597 = a598 = a599 = a600 = \
            a601 = a602 = a603 = a604 = a605 = a606 = a607 = a608 = a609 = a610 = \
            a611 = a612 = a613 = a614 = a615 = a616 = a617 = a618 = a619 = a620 = \
            a621 = a622 = a623 = a624 = a625 = a626 = a627 = a628 = a629 = a630 = \
            a631 = a632 = a633 = a634 = a635 = a636 = a637 = a638 = a639 = a640 = \
            a641 = a642 = a643 = a644 = a645 = a646 = a647 = a648 = a649 = a650 = \
            a651 = a652 = a653 = a654 = a655 = a656 = a657 = a658 = a659 = a660 = \
            a661 = a662 = a663 = a664 = a665 = a666 = a667 = a668 = a669 = a670 = \
            a671 = a672 = a673 = a674 = a675 = a676 = a677 = a678 = a679 = a680 = \
            a681 = a682 = a683 = a684 = a685 = a686 = a687 = a688 = a689 = a690 = \
            a691 = a692 = a693 = a694 = a695 = a696 = a697 = a698 = a699 = a700 = \
            a701 = a702 = a703 = a704 = a705 = a706 = a707 = a708 = a709 = a710 = \
            a711 = a712 = a713 = a714 = a715 = a716 = a717 = a718 = a719 = a720 = \
            a721 = a722 = a723 = a724 = a725 = a726 = a727 = a728 = a729 = a730 = \
            a731 = a732 = a733 = a734 = a735 = a736 = a737 = a738 = a739 = a740 = \
            a741 = a742 = a743 = a744 = a745 = a746 = a747 = a748 = a749 = a750 = \
            a751 = a752 = a753 = a754 = a755 = a756 = a757 = a758 = a759 = a760 = \
            a761 = a762 = a763 = a764 = a765 = a766 = a767 = a768 = a769 = a770 = \
            a771 = a772 = a773 = a774 = a775 = a776 = a777 = a778 = a779 = a780 = \
            a781 = a782 = a783 = a784 = a785 = a786 = a787 = a788 = a789 = a790 = \
            a791 = a792 = a793 = a794 = a795 = a796 = a797 = a798 = a799 = a800 \
                = Nichts
            drucke(a0)

        actual = self.get_suggestion(func)
        self.assertNotRegex(actual, r"NameError.*a1")

    def test_name_error_with_custom_exceptions(self):
        def func():
            blech = Nichts
            wirf NameError()

        actual = self.get_suggestion(func)
        self.assertNotIn("blech", actual)

        def func():
            blech = Nichts
            wirf NameError

        actual = self.get_suggestion(func)
        self.assertNotIn("blech", actual)

    def test_name_error_with_instance(self):
        klasse A:
            def __init__(self):
                self.blech = Nichts
            def foo(self):
                blich = 1
                x = blech

        instance = A()
        actual = self.get_suggestion(instance.foo)
        self.assertIn("self.blech", actual)

    def test_unbound_local_error_with_instance(self):
        klasse A:
            def __init__(self):
                self.blech = Nichts
            def foo(self):
                blich = 1
                x = blech
                blech = 1

        instance = A()
        actual = self.get_suggestion(instance.foo)
        self.assertNotIn("self.blech", actual)

    def test_unbound_local_error_with_side_effect(self):
        # gh-132385
        klasse A:
            def __getattr__(self, key):
                wenn key == 'foo':
                    wirf AttributeError('foo')
                wenn key == 'spam':
                    wirf ValueError('spam')

            def bar(self):
                foo
            def baz(self):
                spam

        suggestion = self.get_suggestion(A().bar)
        self.assertNotIn('self.', suggestion)
        self.assertIn("'foo'", suggestion)

        suggestion = self.get_suggestion(A().baz)
        self.assertNotIn('self.', suggestion)
        self.assertIn("'spam'", suggestion)

    def test_unbound_local_error_does_not_match(self):
        def func():
            something = 3
            drucke(somethong)
            somethong = 3

        actual = self.get_suggestion(func)
        self.assertNotIn("something", actual)

    def test_name_error_for_stdlib_modules(self):
        def func():
            stream = io.StringIO()

        actual = self.get_suggestion(func)
        self.assertIn("forget to importiere 'io'", actual)

    def test_name_error_for_private_stdlib_modules(self):
        def func():
            stream = _io.StringIO()

        actual = self.get_suggestion(func)
        self.assertIn("forget to importiere '_io'", actual)



klasse PurePythonSuggestionFormattingTests(
    PurePythonExceptionFormattingMixin,
    SuggestionFormattingTestBase,
    unittest.TestCase,
):
    """
    Same set of tests als above using the pure Python implementation of
    traceback printing in traceback.py.
    """


@cpython_only
klasse CPythonSuggestionFormattingTests(
    CAPIExceptionFormattingMixin,
    SuggestionFormattingTestBase,
    unittest.TestCase,
):
    """
    Same set of tests als above but mit Python's internal traceback printing.
    """


klasse PurePythonGetattrSuggestionFormattingTests(
    PurePythonExceptionFormattingMixin,
    GetattrSuggestionTests,
    unittest.TestCase,
):
    """
    Same set of tests (for attribute access) als above using the pure Python
    implementation of traceback printing in traceback.py.
    """


klasse PurePythonDelattrSuggestionFormattingTests(
    PurePythonExceptionFormattingMixin,
    DelattrSuggestionTests,
    unittest.TestCase,
):
    """
    Same set of tests (for attribute deletion) als above using the pure Python
    implementation of traceback printing in traceback.py.
    """


@cpython_only
klasse CPythonGetattrSuggestionFormattingTests(
    CAPIExceptionFormattingMixin,
    GetattrSuggestionTests,
    unittest.TestCase,
):
    """
    Same set of tests (for attribute access) als above but mit Python's
    internal traceback printing.
    """


@cpython_only
klasse CPythonDelattrSuggestionFormattingTests(
    CAPIExceptionFormattingMixin,
    DelattrSuggestionTests,
    unittest.TestCase,
):
    """
    Same set of tests (for attribute deletion) als above but mit Python's
    internal traceback printing.
    """

klasse MiscTest(unittest.TestCase):

    def test_all(self):
        expected = set()
        fuer name in dir(traceback):
            wenn name.startswith('_'):
                weiter
            module_object = getattr(traceback, name)
            wenn getattr(module_object, '__module__', Nichts) == 'traceback':
                expected.add(name)
        self.assertCountEqual(traceback.__all__, expected)

    def test_levenshtein_distance(self):
        # copied von _testinternalcapi.test_edit_cost
        # to also exercise the Python implementation

        def CHECK(a, b, expected):
            actual = traceback._levenshtein_distance(a, b, 4044)
            self.assertEqual(actual, expected)

        CHECK("", "", 0)
        CHECK("", "a", 2)
        CHECK("a", "A", 1)
        CHECK("Apple", "Aple", 2)
        CHECK("Banana", "B@n@n@", 6)
        CHECK("Cherry", "Cherry!", 2)
        CHECK("---0---", "------", 2)
        CHECK("abc", "y", 6)
        CHECK("aa", "bb", 4)
        CHECK("aaaaa", "AAAAA", 5)
        CHECK("wxyz", "wXyZ", 2)
        CHECK("wxyz", "wXyZ123", 8)
        CHECK("Python", "Java", 12)
        CHECK("Java", "C#", 8)
        CHECK("AbstractFoobarManager", "abstract_foobar_manager", 3+2*2)
        CHECK("CPython", "PyPy", 10)
        CHECK("CPython", "pypy", 11)
        CHECK("AttributeError", "AttributeErrop", 2)
        CHECK("AttributeError", "AttributeErrorTests", 10)
        CHECK("ABA", "AAB", 4)

    @support.requires_resource('cpu')
    def test_levenshtein_distance_short_circuit(self):
        wenn nicht LEVENSHTEIN_DATA_FILE.is_file():
            self.fail(
                f"{LEVENSHTEIN_DATA_FILE} ist missing."
                f" Run `make regen-test-levenshtein`"
            )

        mit LEVENSHTEIN_DATA_FILE.open("r") als f:
            examples = json.load(f)
        fuer a, b, expected in examples:
            res1 = traceback._levenshtein_distance(a, b, 1000)
            self.assertEqual(res1, expected, msg=(a, b))

            fuer threshold in [expected, expected + 1, expected + 2]:
                # big enough thresholds shouldn't change the result
                res2 = traceback._levenshtein_distance(a, b, threshold)
                self.assertEqual(res2, expected, msg=(a, b, threshold))

            fuer threshold in range(expected):
                # fuer small thresholds, the only piece of information
                # we receive ist "strings nicht close enough".
                res3 = traceback._levenshtein_distance(a, b, threshold)
                self.assertGreater(res3, threshold, msg=(a, b, threshold))

    @cpython_only
    def test_suggestions_extension(self):
        # Check that the C extension ist available
        importiere _suggestions

        self.assertEqual(
            _suggestions._generate_suggestions(
                ["hello", "world"],
                "hell"
            ),
            "hello"
        )
        self.assertEqual(
            _suggestions._generate_suggestions(
                ["hovercraft"],
                "eels"
            ),
            Nichts
        )

        # gh-131936: _generate_suggestions() doesn't accept list subclasses
        klasse MyList(list):
            pass

        mit self.assertRaises(TypeError):
            _suggestions._generate_suggestions(MyList(), "")

    def test_no_site_package_flavour(self):
        code = """import boo"""
        _, _, stderr = assert_python_failure('-S', '-c', code)

        self.assertIn(
            (b"Site initialization ist disabled, did you forget to "
                b"add the site-packages directory to sys.path?"), stderr
        )

        code = """
            importiere sys
            sys.stdlib_module_names = sys.stdlib_module_names + ("boo",)
            importiere boo
        """
        _, _, stderr = assert_python_failure('-S', '-c', code)

        self.assertNotIn(
            (b"Site initialization ist disabled, did you forget to "
                b"add the site-packages directory to sys.path?"), stderr
        )


klasse TestColorizedTraceback(unittest.TestCase):
    maxDiff = Nichts

    def test_colorized_traceback(self):
        def foo(*args):
            x = {'a':{'b': Nichts}}
            y = x['a']['b']['c']

        def baz2(*args):
            gib (lambda *args: foo(*args))(1,2,3,4)

        def baz1(*args):
            gib baz2(1,2,3,4)

        def bar():
            gib baz1(1,
                    2,3
                    ,4)
        versuch:
            bar()
        ausser Exception als e:
            exc = traceback.TracebackException.from_exception(
                e, capture_locals=Wahr
            )
        lines = "".join(exc.format(colorize=Wahr))
        red = colors["e"]
        boldr = colors["E"]
        reset = colors["z"]
        self.assertIn("y = " + red + "x['a']['b']" + reset + boldr + "['c']" + reset, lines)
        self.assertIn("return " + red + "(lambda *args: foo(*args))" + reset + boldr + "(1,2,3,4)" + reset, lines)
        self.assertIn("return (lambda *args: " + red + "foo" + reset + boldr + "(*args)" + reset + ")(1,2,3,4)", lines)
        self.assertIn("return baz2(1,2,3,4)", lines)
        self.assertIn("return baz1(1,\n            2,3\n            ,4)", lines)
        self.assertIn(red + "bar" + reset + boldr + "()" + reset, lines)

    def test_colorized_syntax_error(self):
        versuch:
            compile("a $ b", "<string>", "exec")
        ausser SyntaxError als e:
            exc = traceback.TracebackException.from_exception(
                e, capture_locals=Wahr
            )
        actual = "".join(exc.format(colorize=Wahr))
        def expected(t, m, fn, l, f, E, e, z):
            gib "".join(
                [
                    f'  File {fn}"<string>"{z}, line {l}1{z}\n',
                    f'    a {E}${z} b\n',
                    f'      {E}^{z}\n',
                    f'{t}SyntaxError{z}: {m}invalid syntax{z}\n'
                ]
            )
        self.assertIn(expected(**colors), actual)

    def test_colorized_traceback_is_the_default(self):
        def foo():
            1/0

        von _testcapi importiere exception_print
        versuch:
            foo()
            self.fail("No exception thrown.")
        ausser Exception als e:
            mit captured_output("stderr") als tbstderr:
                mit unittest.mock.patch('_colorize.can_colorize', return_value=Wahr):
                    exception_drucke(e)
            actual = tbstderr.getvalue().splitlines()

        lno_foo = foo.__code__.co_firstlineno
        def expected(t, m, fn, l, f, E, e, z):
            gib [
                'Traceback (most recent call last):',
                f'  File {fn}"{__file__}"{z}, '
                f'line {l}{lno_foo+5}{z}, in {f}test_colorized_traceback_is_the_default{z}',
                f'    {e}foo{z}{E}(){z}',
                f'    {e}~~~{z}{E}^^{z}',
                f'  File {fn}"{__file__}"{z}, '
                f'line {l}{lno_foo+1}{z}, in {f}foo{z}',
                f'    {e}1{z}{E}/{z}{e}0{z}',
                f'    {e}~{z}{E}^{z}{e}~{z}',
                f'{t}ZeroDivisionError{z}: {m}division by zero{z}',
            ]
        self.assertEqual(actual, expected(**colors))

    def test_colorized_traceback_from_exception_group(self):
        def foo():
            exceptions = []
            versuch:
                1 / 0
            ausser ZeroDivisionError als inner_exc:
                exceptions.append(inner_exc)
            wirf ExceptionGroup("test", exceptions)

        versuch:
            foo()
        ausser Exception als e:
            exc = traceback.TracebackException.from_exception(
                e, capture_locals=Wahr
            )

        lno_foo = foo.__code__.co_firstlineno
        actual = "".join(exc.format(colorize=Wahr)).splitlines()
        def expected(t, m, fn, l, f, E, e, z):
            gib [
                f"  + Exception Group Traceback (most recent call last):",
                f'  |   File {fn}"{__file__}"{z}, line {l}{lno_foo+9}{z}, in {f}test_colorized_traceback_from_exception_group{z}',
                f'  |     {e}foo{z}{E}(){z}',
                f'  |     {e}~~~{z}{E}^^{z}',
                f"  |     e = ExceptionGroup('test', [ZeroDivisionError('division by zero')])",
                f"  |     foo = {foo}",
                f'  |     self = <{__name__}.TestColorizedTraceback testMethod=test_colorized_traceback_from_exception_group>',
                f'  |   File {fn}"{__file__}"{z}, line {l}{lno_foo+6}{z}, in {f}foo{z}',
                f'  |     wirf ExceptionGroup("test", exceptions)',
                f"  |     exceptions = [ZeroDivisionError('division by zero')]",
                f'  | {t}ExceptionGroup{z}: {m}test (1 sub-exception){z}',
                f'  +-+---------------- 1 ----------------',
                f'    | Traceback (most recent call last):',
                f'    |   File {fn}"{__file__}"{z}, line {l}{lno_foo+3}{z}, in {f}foo{z}',
                f'    |     {e}1 {z}{E}/{z}{e} 0{z}',
                f'    |     {e}~~{z}{E}^{z}{e}~~{z}',
                f"    |     exceptions = [ZeroDivisionError('division by zero')]",
                f'    | {t}ZeroDivisionError{z}: {m}division by zero{z}',
                f'    +------------------------------------',
        ]
        self.assertEqual(actual, expected(**colors))

wenn __name__ == "__main__":
    unittest.main()
