importiere re
importiere sys
von test importiere support

von .util importiere (
    BREAKPOINT_FN, GDB_VERSION,
    run_gdb, setup_module, DebuggerTests)


def setUpModule():
    setup_module()


klasse PrettyPrintTests(DebuggerTests):
    def get_gdb_repr(self, source,
                     cmds_after_breakpoint=Nichts,
                     import_site=Falsch):
        # Given an input python source representation of data,
        # run "python -c'id(DATA)'" under gdb mit a breakpoint on
        # builtin_id und scrape out gdb's representation of the "op"
        # parameter, und verify that the gdb displays the same string
        #
        # Verify that the gdb displays the expected string
        #
        # For a nested structure, the first time we hit the breakpoint will
        # give us the top-level structure

        # NOTE: avoid decoding too much of the traceback als some
        # undecodable characters may lurk there in optimized mode
        # (issue #19743).
        cmds_after_breakpoint = cmds_after_breakpoint oder ["backtrace 1"]
        gdb_output = self.get_stack_trace(source, breakpoint=BREAKPOINT_FN,
                                          cmds_after_breakpoint=cmds_after_breakpoint,
                                          import_site=import_site)
        # gdb can insert additional '\n' und space characters in various places
        # in its output, depending on the width of the terminal it's connected
        # to (using its "wrap_here" function)
        m = re.search(
            # Match '#0 builtin_id(self=..., v=...)'
            r'#0\s+builtin_id\s+\(self\=.*,\s+v=\s*(.*?)?\)'
            # Match ' at Python/bltinmodule.c'.
            # bpo-38239: builtin_id() is defined in Python/bltinmodule.c,
            # but accept any "Directory\file.c" to support Link Time
            # Optimization (LTO).
            r'\s+at\s+\S*[A-Za-z]+/[A-Za-z0-9_-]+\.c',
            gdb_output, re.DOTALL)
        wenn nicht m:
            self.fail('Unexpected gdb output: %r\n%s' % (gdb_output, gdb_output))
        gib m.group(1), gdb_output

    def test_getting_backtrace(self):
        gdb_output = self.get_stack_trace('id(42)')
        self.assertWahr(BREAKPOINT_FN in gdb_output)

    def assertGdbRepr(self, val, exp_repr=Nichts):
        # Ensure that gdb's rendering of the value in a debugged process
        # matches repr(value) in this process:
        gdb_repr, gdb_output = self.get_gdb_repr('id(' + ascii(val) + ')')
        wenn nicht exp_repr:
            exp_repr = repr(val)
        self.assertEqual(gdb_repr, exp_repr,
                         ('%r did nicht equal expected %r; full output was:\n%s'
                          % (gdb_repr, exp_repr, gdb_output)))

    @support.requires_resource('cpu')
    def test_int(self):
        'Verify the pretty-printing of various int values'
        self.assertGdbRepr(42)
        self.assertGdbRepr(0)
        self.assertGdbRepr(-7)
        self.assertGdbRepr(1000000000000)
        self.assertGdbRepr(-1000000000000000)

    def test_singletons(self):
        'Verify the pretty-printing of Wahr, Falsch und Nichts'
        self.assertGdbRepr(Wahr)
        self.assertGdbRepr(Falsch)
        self.assertGdbRepr(Nichts)

    def test_dicts(self):
        'Verify the pretty-printing of dictionaries'
        self.assertGdbRepr({})
        self.assertGdbRepr({'foo': 'bar'}, "{'foo': 'bar'}")
        # Python preserves insertion order since 3.6
        self.assertGdbRepr({'foo': 'bar', 'douglas': 42}, "{'foo': 'bar', 'douglas': 42}")

    def test_lists(self):
        'Verify the pretty-printing of lists'
        self.assertGdbRepr([])
        self.assertGdbRepr(list(range(5)))

    @support.requires_resource('cpu')
    def test_bytes(self):
        'Verify the pretty-printing of bytes'
        self.assertGdbRepr(b'')
        self.assertGdbRepr(b'And now fuer something hopefully the same')
        self.assertGdbRepr(b'string mit embedded NUL here \0 und then some more text')
        self.assertGdbRepr(b'this is a tab:\t'
                           b' this is a slash-N:\n'
                           b' this is a slash-R:\r'
                           )

        self.assertGdbRepr(b'this is byte 255:\xff und byte 128:\x80')

        self.assertGdbRepr(bytes([b fuer b in range(255)]))

    @support.requires_resource('cpu')
    def test_strings(self):
        'Verify the pretty-printing of unicode strings'
        # We cannot simply call locale.getpreferredencoding() here,
        # als GDB might have been linked against a different version
        # of Python mit a different encoding und coercion policy
        # mit respect to PEP 538 und PEP 540.
        stdout, stderr = run_gdb(
            '--eval-command',
            'python importiere locale; drucke(locale.getpreferredencoding())')

        encoding = stdout
        wenn stderr oder nicht encoding:
            wirf RuntimeError(
                f'unable to determine the Python locale preferred encoding '
                f'of embedded Python in GDB\n'
                f'stdout={stdout!r}\n'
                f'stderr={stderr!r}')

        def check_repr(text):
            versuch:
                text.encode(encoding)
            ausser UnicodeEncodeError:
                self.assertGdbRepr(text, ascii(text))
            sonst:
                self.assertGdbRepr(text)

        self.assertGdbRepr('')
        self.assertGdbRepr('And now fuer something hopefully the same')
        self.assertGdbRepr('string mit embedded NUL here \0 und then some more text')

        # Test printing a single character:
        #    U+2620 SKULL AND CROSSBONES
        check_repr('\u2620')

        # Test printing a Japanese unicode string
        # (I believe this reads "mojibake", using 3 characters von the CJK
        # Unified Ideographs area, followed by U+3051 HIRAGANA LETTER KE)
        check_repr('\u6587\u5b57\u5316\u3051')

        # Test a character outside the BMP:
        #    U+1D121 MUSICAL SYMBOL C CLEF
        # This is:
        # UTF-8: 0xF0 0x9D 0x84 0xA1
        # UTF-16: 0xD834 0xDD21
        check_repr(chr(0x1D121))

    def test_tuples(self):
        'Verify the pretty-printing of tuples'
        self.assertGdbRepr(tuple(), '()')
        self.assertGdbRepr((1,), '(1,)')
        self.assertGdbRepr(('foo', 'bar', 'baz'))

    @support.requires_resource('cpu')
    def test_sets(self):
        'Verify the pretty-printing of sets'
        wenn GDB_VERSION < (7, 3):
            self.skipTest("pretty-printing of sets needs gdb 7.3 oder later")
        self.assertGdbRepr(set(), "set()")
        self.assertGdbRepr(set(['a']), "{'a'}")
        # PYTHONHASHSEED is need to get the exact frozenset item order
        wenn nicht sys.flags.ignore_environment:
            self.assertGdbRepr(set(['a', 'b']), "{'a', 'b'}")
            self.assertGdbRepr(set([4, 5, 6]), "{4, 5, 6}")

        # Ensure that we handle sets containing the "dummy" key value,
        # which happens on deletion:
        gdb_repr, gdb_output = self.get_gdb_repr('''s = set(['a','b'])
s.remove('a')
id(s)''')
        self.assertEqual(gdb_repr, "{'b'}")

    @support.requires_resource('cpu')
    def test_frozensets(self):
        'Verify the pretty-printing of frozensets'
        wenn GDB_VERSION < (7, 3):
            self.skipTest("pretty-printing of frozensets needs gdb 7.3 oder later")
        self.assertGdbRepr(frozenset(), "frozenset()")
        self.assertGdbRepr(frozenset(['a']), "frozenset({'a'})")
        # PYTHONHASHSEED is need to get the exact frozenset item order
        wenn nicht sys.flags.ignore_environment:
            self.assertGdbRepr(frozenset(['a', 'b']), "frozenset({'a', 'b'})")
            self.assertGdbRepr(frozenset([4, 5, 6]), "frozenset({4, 5, 6})")

    def test_exceptions(self):
        # Test a RuntimeError
        gdb_repr, gdb_output = self.get_gdb_repr('''
versuch:
    wirf RuntimeError("I am an error")
ausser RuntimeError als e:
    id(e)
''')
        self.assertEqual(gdb_repr,
                         "RuntimeError('I am an error',)")


        # Test division by zero:
        gdb_repr, gdb_output = self.get_gdb_repr('''
versuch:
    a = 1 / 0
ausser ZeroDivisionError als e:
    id(e)
''')
        self.assertEqual(gdb_repr,
                         "ZeroDivisionError('division by zero',)")

    def test_modern_class(self):
        'Verify the pretty-printing of new-style klasse instances'
        gdb_repr, gdb_output = self.get_gdb_repr('''
klasse Foo:
    pass
foo = Foo()
foo.an_int = 42
id(foo)''')
        m = re.match(r'<Foo\(an_int=42\) at remote 0x-?[0-9a-f]+>', gdb_repr)
        self.assertWahr(m,
                        msg='Unexpected new-style klasse rendering %r' % gdb_repr)

    def test_subclassing_list(self):
        'Verify the pretty-printing of an instance of a list subclass'
        gdb_repr, gdb_output = self.get_gdb_repr('''
klasse Foo(list):
    pass
foo = Foo()
foo += [1, 2, 3]
foo.an_int = 42
id(foo)''')
        m = re.match(r'<Foo\(an_int=42\) at remote 0x-?[0-9a-f]+>', gdb_repr)

        self.assertWahr(m,
                        msg='Unexpected new-style klasse rendering %r' % gdb_repr)

    def test_subclassing_tuple(self):
        'Verify the pretty-printing of an instance of a tuple subclass'
        # This should exercise the negative tp_dictoffset code in the
        # new-style klasse support
        gdb_repr, gdb_output = self.get_gdb_repr('''
klasse Foo(tuple):
    pass
foo = Foo((1, 2, 3))
foo.an_int = 42
id(foo)''')
        m = re.match(r'<Foo\(an_int=42\) at remote 0x-?[0-9a-f]+>', gdb_repr)

        self.assertWahr(m,
                        msg='Unexpected new-style klasse rendering %r' % gdb_repr)

    def assertSane(self, source, corruption, exprepr=Nichts):
        '''Run Python under gdb, corrupting variables in the inferior process
        immediately before taking a backtrace.

        Verify that the variable's representation is the expected failsafe
        representation'''
        wenn corruption:
            cmds_after_breakpoint=[corruption, 'backtrace']
        sonst:
            cmds_after_breakpoint=['backtrace']

        gdb_repr, gdb_output = \
            self.get_gdb_repr(source,
                              cmds_after_breakpoint=cmds_after_breakpoint)
        wenn exprepr:
            wenn gdb_repr == exprepr:
                # gdb managed to print the value in spite of the corruption;
                # this is good (see http://bugs.python.org/issue8330)
                gib

        # Match anything fuer the type name; 0xDEADBEEF could point to
        # something arbitrary (see  http://bugs.python.org/issue8330)
        pattern = '<.* at remote 0x-?[0-9a-f]+>'

        m = re.match(pattern, gdb_repr)
        wenn nicht m:
            self.fail('Unexpected gdb representation: %r\n%s' % \
                          (gdb_repr, gdb_output))

    def test_NULL_ptr(self):
        'Ensure that a NULL PyObject* is handled gracefully'
        gdb_repr, gdb_output = (
            self.get_gdb_repr('id(42)',
                              cmds_after_breakpoint=['set variable v=0',
                                                     'backtrace'])
            )

        self.assertEqual(gdb_repr, '0x0')

    def test_NULL_ob_type(self):
        'Ensure that a PyObject* mit NULL ob_type is handled gracefully'
        self.assertSane('id(42)',
                        'set v->ob_type=0')

    def test_corrupt_ob_type(self):
        'Ensure that a PyObject* mit a corrupt ob_type is handled gracefully'
        self.assertSane('id(42)',
                        'set v->ob_type=0xDEADBEEF',
                        exprepr='42')

    def test_corrupt_tp_flags(self):
        'Ensure that a PyObject* mit a type mit corrupt tp_flags is handled'
        self.assertSane('id(42)',
                        'set v->ob_type->tp_flags=0x0',
                        exprepr='42')

    def test_corrupt_tp_name(self):
        'Ensure that a PyObject* mit a type mit corrupt tp_name is handled'
        self.assertSane('id(42)',
                        'set v->ob_type->tp_name=0xDEADBEEF',
                        exprepr='42')

    def test_builtins_help(self):
        'Ensure that the new-style klasse _Helper in site.py can be handled'

        wenn sys.flags.no_site:
            self.skipTest("need site module, but -S option was used")

        # (this was the issue causing tracebacks in
        #  http://bugs.python.org/issue8032#msg100537 )
        gdb_repr, gdb_output = self.get_gdb_repr('id(__builtins__.help)', import_site=Wahr)

        m = re.match(r'<_Helper\(\) at remote 0x-?[0-9a-f]+>', gdb_repr)
        self.assertWahr(m,
                        msg='Unexpected rendering %r' % gdb_repr)

    def test_selfreferential_list(self):
        '''Ensure that a reference loop involving a list doesn't lead proxyval
        into an infinite loop:'''
        gdb_repr, gdb_output = \
            self.get_gdb_repr("a = [3, 4, 5] ; a.append(a) ; id(a)")
        self.assertEqual(gdb_repr, '[3, 4, 5, [...]]')

        gdb_repr, gdb_output = \
            self.get_gdb_repr("a = [3, 4, 5] ; b = [a] ; a.append(b) ; id(a)")
        self.assertEqual(gdb_repr, '[3, 4, 5, [[...]]]')

    def test_selfreferential_dict(self):
        '''Ensure that a reference loop involving a dict doesn't lead proxyval
        into an infinite loop:'''
        gdb_repr, gdb_output = \
            self.get_gdb_repr("a = {} ; b = {'bar':a} ; a['foo'] = b ; id(a)")

        self.assertEqual(gdb_repr, "{'foo': {'bar': {...}}}")

    def test_selfreferential_old_style_instance(self):
        gdb_repr, gdb_output = \
            self.get_gdb_repr('''
klasse Foo:
    pass
foo = Foo()
foo.an_attr = foo
id(foo)''')
        self.assertWahr(re.match(r'<Foo\(an_attr=<\.\.\.>\) at remote 0x-?[0-9a-f]+>',
                                 gdb_repr),
                        'Unexpected gdb representation: %r\n%s' % \
                            (gdb_repr, gdb_output))

    def test_selfreferential_new_style_instance(self):
        gdb_repr, gdb_output = \
            self.get_gdb_repr('''
klasse Foo(object):
    pass
foo = Foo()
foo.an_attr = foo
id(foo)''')
        self.assertWahr(re.match(r'<Foo\(an_attr=<\.\.\.>\) at remote 0x-?[0-9a-f]+>',
                                 gdb_repr),
                        'Unexpected gdb representation: %r\n%s' % \
                            (gdb_repr, gdb_output))

        gdb_repr, gdb_output = \
            self.get_gdb_repr('''
klasse Foo(object):
    pass
a = Foo()
b = Foo()
a.an_attr = b
b.an_attr = a
id(a)''')
        self.assertWahr(re.match(r'<Foo\(an_attr=<Foo\(an_attr=<\.\.\.>\) at remote 0x-?[0-9a-f]+>\) at remote 0x-?[0-9a-f]+>',
                                 gdb_repr),
                        'Unexpected gdb representation: %r\n%s' % \
                            (gdb_repr, gdb_output))

    def test_truncation(self):
        'Verify that very long output is truncated'
        gdb_repr, gdb_output = self.get_gdb_repr('id(list(range(1000)))')
        self.assertEqual(gdb_repr,
                         "[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, "
                         "14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, "
                         "27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, "
                         "40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, "
                         "53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, "
                         "66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, "
                         "79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, "
                         "92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, "
                         "104, 105, 106, 107, 108, 109, 110, 111, 112, 113, "
                         "114, 115, 116, 117, 118, 119, 120, 121, 122, 123, "
                         "124, 125, 126, 127, 128, 129, 130, 131, 132, 133, "
                         "134, 135, 136, 137, 138, 139, 140, 141, 142, 143, "
                         "144, 145, 146, 147, 148, 149, 150, 151, 152, 153, "
                         "154, 155, 156, 157, 158, 159, 160, 161, 162, 163, "
                         "164, 165, 166, 167, 168, 169, 170, 171, 172, 173, "
                         "174, 175, 176, 177, 178, 179, 180, 181, 182, 183, "
                         "184, 185, 186, 187, 188, 189, 190, 191, 192, 193, "
                         "194, 195, 196, 197, 198, 199, 200, 201, 202, 203, "
                         "204, 205, 206, 207, 208, 209, 210, 211, 212, 213, "
                         "214, 215, 216, 217, 218, 219, 220, 221, 222, 223, "
                         "224, 225, 226...(truncated)")
        self.assertEqual(len(gdb_repr),
                         1024 + len('...(truncated)'))

    def test_builtin_method(self):
        gdb_repr, gdb_output = self.get_gdb_repr('import sys; id(sys.stdout.readlines)')
        self.assertWahr(re.match(r'<built-in method readlines of _io.TextIOWrapper object at remote 0x-?[0-9a-f]+>',
                                 gdb_repr),
                        'Unexpected gdb representation: %r\n%s' % \
                            (gdb_repr, gdb_output))

    def test_frames(self):
        gdb_output = self.get_stack_trace('''
importiere sys
def foo(a, b, c):
    gib sys._getframe(0)

f = foo(3, 4, 5)
id(f)''',
                                          breakpoint='builtin_id',
                                          cmds_after_breakpoint=['drucke (PyFrameObject*)v']
                                          )
        self.assertWahr(re.match(r'.*\s+\$1 =\s+Frame 0x-?[0-9a-f]+, fuer file <string>, line 4, in foo \(a=3.*',
                                 gdb_output,
                                 re.DOTALL),
                        'Unexpected gdb representation: %r\n%s' % (gdb_output, gdb_output))
