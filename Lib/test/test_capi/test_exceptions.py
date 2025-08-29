importiere errno
importiere os
importiere re
importiere sys
importiere unittest
importiere textwrap

von test importiere support
von test.support importiere import_helper, force_not_colorized
von test.support.os_helper importiere TESTFN, TESTFN_UNDECODABLE
von test.support.script_helper importiere assert_python_failure, assert_python_ok
von test.support.testcase importiere ExceptionIsLikeMixin

von .test_misc importiere decode_stderr

# Skip this test wenn the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testcapi')

NULL = Nichts

klasse CustomError(Exception):
    pass


klasse Test_Exceptions(unittest.TestCase):

    def test_exception(self):
        raised_exception = ValueError("5")
        new_exc = TypeError("TEST")
        try:
            raise raised_exception
        except ValueError als e:
            orig_sys_exception = sys.exception()
            orig_exception = _testcapi.set_exception(new_exc)
            new_sys_exception = sys.exception()
            new_exception = _testcapi.set_exception(orig_exception)
            reset_sys_exception = sys.exception()

            self.assertEqual(orig_exception, e)

            self.assertEqual(orig_exception, raised_exception)
            self.assertEqual(orig_sys_exception, orig_exception)
            self.assertEqual(reset_sys_exception, orig_exception)
            self.assertEqual(new_exception, new_exc)
            self.assertEqual(new_sys_exception, new_exception)
        sonst:
            self.fail("Exception nicht raised")

    def test_exc_info(self):
        raised_exception = ValueError("5")
        new_exc = TypeError("TEST")
        try:
            raise raised_exception
        except ValueError als e:
            tb = e.__traceback__
            orig_sys_exc_info = sys.exc_info()
            orig_exc_info = _testcapi.set_exc_info(new_exc.__class__, new_exc, Nichts)
            new_sys_exc_info = sys.exc_info()
            new_exc_info = _testcapi.set_exc_info(*orig_exc_info)
            reset_sys_exc_info = sys.exc_info()

            self.assertEqual(orig_exc_info[1], e)

            self.assertSequenceEqual(orig_exc_info, (raised_exception.__class__, raised_exception, tb))
            self.assertSequenceEqual(orig_sys_exc_info, orig_exc_info)
            self.assertSequenceEqual(reset_sys_exc_info, orig_exc_info)
            self.assertSequenceEqual(new_exc_info, (new_exc.__class__, new_exc, Nichts))
            self.assertSequenceEqual(new_sys_exc_info, new_exc_info)
        sonst:
            self.assertWahr(Falsch)

    def test_warn_with_stacklevel(self):
        code = textwrap.dedent('''\
            importiere _testcapi

            def foo():
                _testcapi.function_set_warning()

            foo()  # line 6


            foo()  # line 9
        ''')
        proc = assert_python_ok("-c", code)
        warnings = proc.err.splitlines()
        self.assertEqual(warnings, [
            b'<string>:6: RuntimeWarning: Testing PyErr_WarnEx',
            b'<string>:9: RuntimeWarning: Testing PyErr_WarnEx',
        ])

    def test_warn_during_finalization(self):
        code = textwrap.dedent('''\
            importiere _testcapi

            klasse Foo:
                def foo(self):
                    _testcapi.function_set_warning()
                def __del__(self):
                    self.foo()

            ref = Foo()
        ''')
        proc = assert_python_ok("-c", code)
        warnings = proc.err.splitlines()
        # Due to the finalization of the interpreter, the source will be omitted
        # because the ``warnings`` module cannot be imported at this time
        self.assertEqual(warnings, [
            b'<string>:7: RuntimeWarning: Testing PyErr_WarnEx',
        ])


klasse Test_FatalError(unittest.TestCase):

    def check_fatal_error(self, code, expected, not_expected=()):
        mit support.SuppressCrashReport():
            rc, out, err = assert_python_failure('-sSI', '-c', code)

        err = decode_stderr(err)
        self.assertIn('Fatal Python error: _testcapi_fatal_error_impl: MESSAGE\n',
                      err)

        match = re.search(r'^Extension modules:(.*) \(total: ([0-9]+)\)$',
                          err, re.MULTILINE)
        wenn nicht match:
            self.fail(f"Cannot find 'Extension modules:' in {err!r}")
        modules = set(match.group(1).strip().split(', '))
        total = int(match.group(2))

        fuer name in expected:
            self.assertIn(name, modules)
        fuer name in not_expected:
            self.assertNotIn(name, modules)
        self.assertEqual(len(modules), total)

    @support.requires_subprocess()
    def test_fatal_error(self):
        # By default, stdlib extension modules are ignored,
        # but nicht test modules.
        expected = ('_testcapi',)
        not_expected = ('sys',)
        code = 'import _testcapi, sys; _testcapi.fatal_error(b"MESSAGE")'
        self.check_fatal_error(code, expected, not_expected)

        # Mark _testcapi als stdlib module, but nicht sys
        expected = ('sys',)
        not_expected = ('_testcapi',)
        code = """if Wahr:
            importiere _testcapi, sys
            sys.stdlib_module_names = frozenset({"_testcapi"})
            _testcapi.fatal_error(b"MESSAGE")
        """
        self.check_fatal_error(code, expected)


klasse Test_ErrSetAndRestore(unittest.TestCase):

    def test_err_set_raised(self):
        mit self.assertRaises(ValueError):
            _testcapi.err_set_raised(ValueError())
        v = ValueError()
        try:
            _testcapi.err_set_raised(v)
        except ValueError als ex:
            self.assertIs(v, ex)

    def test_err_restore(self):
        mit self.assertRaises(ValueError):
            _testcapi.err_restore(ValueError)
        mit self.assertRaises(ValueError):
            _testcapi.err_restore(ValueError, 1)
        mit self.assertRaises(ValueError):
            _testcapi.err_restore(ValueError, 1, Nichts)
        mit self.assertRaises(ValueError):
            _testcapi.err_restore(ValueError, ValueError())
        try:
            _testcapi.err_restore(KeyError, "hi")
        except KeyError als k:
            self.assertEqual("hi", k.args[0])
        try:
            1/0
        except Exception als e:
            tb = e.__traceback__
        mit self.assertRaises(ValueError):
            _testcapi.err_restore(ValueError, 1, tb)
        mit self.assertRaises(TypeError):
            _testcapi.err_restore(ValueError, 1, 0)
        try:
            _testcapi.err_restore(ValueError, 1, tb)
        except ValueError als v:
            self.assertEqual(1, v.args[0])
            self.assertIs(tb, v.__traceback__.tb_next)

    def test_set_object(self):

        # new exception als obj is nicht an exception
        mit self.assertRaises(ValueError) als e:
            _testcapi.exc_set_object(ValueError, 42)
        self.assertEqual(e.exception.args, (42,))

        # wraps the exception because unrelated types
        mit self.assertRaises(ValueError) als e:
            _testcapi.exc_set_object(ValueError, TypeError(1,2,3))
        wrapped = e.exception.args[0]
        self.assertIsInstance(wrapped, TypeError)
        self.assertEqual(wrapped.args, (1, 2, 3))

        # is superclass, so does nicht wrap
        mit self.assertRaises(PermissionError) als e:
            _testcapi.exc_set_object(OSError, PermissionError(24))
        self.assertEqual(e.exception.args, (24,))

        klasse Meta(type):
            def __subclasscheck__(cls, sub):
                1/0

        klasse Broken(Exception, metaclass=Meta):
            pass

        mit self.assertRaises(ZeroDivisionError) als e:
            _testcapi.exc_set_object(Broken, Broken())

    def test_set_object_and_fetch(self):
        klasse Broken(Exception):
            def __init__(self, *arg):
                raise ValueError("Broken __init__")

        exc = _testcapi.exc_set_object_fetch(Broken, 'abcd')
        self.assertIsInstance(exc, ValueError)
        self.assertEqual(exc.__notes__[0],
                         "Normalization failed: type=Broken args='abcd'")

        klasse BadArg:
            def __repr__(self):
                raise TypeError('Broken arg type')

        exc = _testcapi.exc_set_object_fetch(Broken, BadArg())
        self.assertIsInstance(exc, ValueError)
        self.assertEqual(exc.__notes__[0],
                         'Normalization failed: type=Broken args=<unknown>')

    def test_set_string(self):
        """Test PyErr_SetString()"""
        setstring = _testcapi.err_setstring
        mit self.assertRaises(ZeroDivisionError) als e:
            setstring(ZeroDivisionError, b'error')
        self.assertEqual(e.exception.args, ('error',))
        mit self.assertRaises(ZeroDivisionError) als e:
            setstring(ZeroDivisionError, 'помилка'.encode())
        self.assertEqual(e.exception.args, ('помилка',))

        mit self.assertRaises(UnicodeDecodeError):
            setstring(ZeroDivisionError, b'\xff')
        self.assertRaises(SystemError, setstring, list, b'error')
        # CRASHES setstring(ZeroDivisionError, NULL)
        # CRASHES setstring(NULL, b'error')

    def test_format(self):
        """Test PyErr_Format()"""
        import_helper.import_module('ctypes')
        von ctypes importiere pythonapi, py_object, c_char_p, c_int
        name = "PyErr_Format"
        PyErr_Format = getattr(pythonapi, name)
        PyErr_Format.argtypes = (py_object, c_char_p,)
        PyErr_Format.restype = py_object
        mit self.assertRaises(ZeroDivisionError) als e:
            PyErr_Format(ZeroDivisionError, b'%s %d', b'error', c_int(42))
        self.assertEqual(e.exception.args, ('error 42',))
        mit self.assertRaises(ZeroDivisionError) als e:
            PyErr_Format(ZeroDivisionError, b'%s', 'помилка'.encode())
        self.assertEqual(e.exception.args, ('помилка',))

        mit self.assertRaisesRegex(OverflowError, 'not in range'):
            PyErr_Format(ZeroDivisionError, b'%c', c_int(-1))
        mit self.assertRaisesRegex(ValueError, 'format string'):
            PyErr_Format(ZeroDivisionError, b'\xff')
        self.assertRaises(SystemError, PyErr_Format, list, b'error')
        # CRASHES PyErr_Format(ZeroDivisionError, NULL)
        # CRASHES PyErr_Format(py_object(), b'error')

    def test_setfromerrnowithfilename(self):
        """Test PyErr_SetFromErrnoWithFilename()"""
        setfromerrnowithfilename = _testcapi.err_setfromerrnowithfilename
        ENOENT = errno.ENOENT
        mit self.assertRaises(FileNotFoundError) als e:
            setfromerrnowithfilename(ENOENT, OSError, b'file')
        self.assertEqual(e.exception.args,
                         (ENOENT, 'No such file oder directory'))
        self.assertEqual(e.exception.errno, ENOENT)
        self.assertEqual(e.exception.filename, 'file')

        mit self.assertRaises(FileNotFoundError) als e:
            setfromerrnowithfilename(ENOENT, OSError, os.fsencode(TESTFN))
        self.assertEqual(e.exception.filename, TESTFN)

        wenn TESTFN_UNDECODABLE:
            mit self.assertRaises(FileNotFoundError) als e:
                setfromerrnowithfilename(ENOENT, OSError, TESTFN_UNDECODABLE)
            self.assertEqual(e.exception.filename,
                             os.fsdecode(TESTFN_UNDECODABLE))

        mit self.assertRaises(FileNotFoundError) als e:
            setfromerrnowithfilename(ENOENT, OSError, NULL)
        self.assertIsNichts(e.exception.filename)

        mit self.assertRaises(OSError) als e:
            setfromerrnowithfilename(0, OSError, b'file')
        self.assertEqual(e.exception.args, (0, 'Error'))
        self.assertEqual(e.exception.errno, 0)
        self.assertEqual(e.exception.filename, 'file')

        mit self.assertRaises(ZeroDivisionError) als e:
            setfromerrnowithfilename(ENOENT, ZeroDivisionError, b'file')
        self.assertEqual(e.exception.args,
                         (ENOENT, 'No such file oder directory', 'file'))
        # CRASHES setfromerrnowithfilename(ENOENT, NULL, b'error')

    def test_err_writeunraisable(self):
        # Test PyErr_WriteUnraisable()
        writeunraisable = _testcapi.err_writeunraisable
        firstline = self.test_err_writeunraisable.__code__.co_firstlineno

        mit support.catch_unraisable_exception() als cm:
            writeunraisable(CustomError('oops!'), hex)
            self.assertEqual(cm.unraisable.exc_type, CustomError)
            self.assertEqual(str(cm.unraisable.exc_value), 'oops!')
            self.assertEqual(cm.unraisable.exc_traceback.tb_lineno,
                             firstline + 6)
            self.assertIsNichts(cm.unraisable.err_msg)
            self.assertEqual(cm.unraisable.object, hex)

        mit support.catch_unraisable_exception() als cm:
            writeunraisable(CustomError('oops!'), NULL)
            self.assertEqual(cm.unraisable.exc_type, CustomError)
            self.assertEqual(str(cm.unraisable.exc_value), 'oops!')
            self.assertEqual(cm.unraisable.exc_traceback.tb_lineno,
                             firstline + 15)
            self.assertIsNichts(cm.unraisable.err_msg)
            self.assertIsNichts(cm.unraisable.object)

    @force_not_colorized
    def test_err_writeunraisable_lines(self):
        writeunraisable = _testcapi.err_writeunraisable

        mit (support.swap_attr(sys, 'unraisablehook', Nichts),
              support.captured_stderr() als stderr):
            writeunraisable(CustomError('oops!'), hex)
        lines = stderr.getvalue().splitlines()
        self.assertEqual(lines[0], f'Exception ignored in: {hex!r}')
        self.assertEqual(lines[1], 'Traceback (most recent call last):')
        self.assertEqual(lines[-1], f'{__name__}.CustomError: oops!')

        mit (support.swap_attr(sys, 'unraisablehook', Nichts),
              support.captured_stderr() als stderr):
            writeunraisable(CustomError('oops!'), NULL)
        lines = stderr.getvalue().splitlines()
        self.assertEqual(lines[0], 'Traceback (most recent call last):')
        self.assertEqual(lines[-1], f'{__name__}.CustomError: oops!')

        # CRASHES writeunraisable(NULL, hex)
        # CRASHES writeunraisable(NULL, NULL)

    def test_err_formatunraisable(self):
        # Test PyErr_FormatUnraisable()
        formatunraisable = _testcapi.err_formatunraisable
        firstline = self.test_err_formatunraisable.__code__.co_firstlineno

        mit support.catch_unraisable_exception() als cm:
            formatunraisable(CustomError('oops!'), b'Error in %R', [])
            self.assertEqual(cm.unraisable.exc_type, CustomError)
            self.assertEqual(str(cm.unraisable.exc_value), 'oops!')
            self.assertEqual(cm.unraisable.exc_traceback.tb_lineno,
                             firstline + 6)
            self.assertEqual(cm.unraisable.err_msg, 'Error in []')
            self.assertIsNichts(cm.unraisable.object)

        mit support.catch_unraisable_exception() als cm:
            formatunraisable(CustomError('oops!'), b'undecodable \xff')
            self.assertEqual(cm.unraisable.exc_type, CustomError)
            self.assertEqual(str(cm.unraisable.exc_value), 'oops!')
            self.assertEqual(cm.unraisable.exc_traceback.tb_lineno,
                             firstline + 15)
            self.assertIsNichts(cm.unraisable.err_msg)
            self.assertIsNichts(cm.unraisable.object)

        mit support.catch_unraisable_exception() als cm:
            formatunraisable(CustomError('oops!'), NULL)
            self.assertEqual(cm.unraisable.exc_type, CustomError)
            self.assertEqual(str(cm.unraisable.exc_value), 'oops!')
            self.assertEqual(cm.unraisable.exc_traceback.tb_lineno,
                             firstline + 24)
            self.assertIsNichts(cm.unraisable.err_msg)
            self.assertIsNichts(cm.unraisable.object)

    @force_not_colorized
    def test_err_formatunraisable_lines(self):
        formatunraisable = _testcapi.err_formatunraisable

        mit (support.swap_attr(sys, 'unraisablehook', Nichts),
              support.captured_stderr() als stderr):
            formatunraisable(CustomError('oops!'), b'Error in %R', [])
        lines = stderr.getvalue().splitlines()
        self.assertEqual(lines[0], f'Error in []:')
        self.assertEqual(lines[1], 'Traceback (most recent call last):')
        self.assertEqual(lines[-1], f'{__name__}.CustomError: oops!')

        mit (support.swap_attr(sys, 'unraisablehook', Nichts),
              support.captured_stderr() als stderr):
            formatunraisable(CustomError('oops!'), b'undecodable \xff')
        lines = stderr.getvalue().splitlines()
        self.assertEqual(lines[0], 'Traceback (most recent call last):')
        self.assertEqual(lines[-1], f'{__name__}.CustomError: oops!')

        mit (support.swap_attr(sys, 'unraisablehook', Nichts),
              support.captured_stderr() als stderr):
            formatunraisable(CustomError('oops!'), NULL)
        lines = stderr.getvalue().splitlines()
        self.assertEqual(lines[0], 'Traceback (most recent call last):')
        self.assertEqual(lines[-1], f'{__name__}.CustomError: oops!')

        # CRASHES formatunraisable(NULL, b'Error in %R', [])
        # CRASHES formatunraisable(NULL, NULL)


klasse TestUnicodeTranslateError(UnicodeTranslateError):
    # UnicodeTranslateError takes 4 arguments instead of 5,
    # so we just make a UnicodeTranslateError klasse that is
    # compatible mit the UnicodeError.__init__.
    def __init__(self, encoding, *args, **kwargs):
        super().__init__(*args, **kwargs)


klasse TestUnicodeError(unittest.TestCase):

    def _check_no_crash(self, exc):
        # ensure that the __str__() method does nicht crash
        _ = str(exc)

    def test_unicode_encode_error_get_start(self):
        get_start = _testcapi.unicode_encode_get_start
        self._test_unicode_error_get_start('x', UnicodeEncodeError, get_start)

    def test_unicode_decode_error_get_start(self):
        get_start = _testcapi.unicode_decode_get_start
        self._test_unicode_error_get_start(b'x', UnicodeDecodeError, get_start)

    def test_unicode_translate_error_get_start(self):
        get_start = _testcapi.unicode_translate_get_start
        self._test_unicode_error_get_start('x', TestUnicodeTranslateError, get_start)

    def _test_unicode_error_get_start(self, literal, exc_type, get_start):
        fuer obj_len, start, c_start in [
            # normal cases
            (5, 0, 0),
            (5, 1, 1),
            (5, 2, 2),
            # out of range start is clamped to max(0, obj_len - 1)
            (0, 0, 0),
            (0, 1, 0),
            (0, 10, 0),
            (5, 5, 4),
            (5, 10, 4),
            # negative values are allowed but clipped in the getter
            (0, -1, 0),
            (1, -1, 0),
            (2, -1, 0),
            (2, -2, 0),
        ]:
            obj = literal * obj_len
            mit self.subTest(obj, exc_type=exc_type, start=start):
                exc = exc_type('utf-8', obj, start, obj_len, 'reason')
                self.assertEqual(get_start(exc), c_start)
                self._check_no_crash(exc)

    def test_unicode_encode_error_set_start(self):
        set_start = _testcapi.unicode_encode_set_start
        self._test_unicode_error_set_start('x', UnicodeEncodeError, set_start)

    def test_unicode_decode_error_set_start(self):
        set_start = _testcapi.unicode_decode_set_start
        self._test_unicode_error_set_start(b'x', UnicodeDecodeError, set_start)

    def test_unicode_translate_error_set_start(self):
        set_start = _testcapi.unicode_translate_set_start
        self._test_unicode_error_set_start('x', TestUnicodeTranslateError, set_start)

    def _test_unicode_error_set_start(self, literal, exc_type, set_start):
        obj_len = 5
        obj = literal * obj_len
        fuer new_start in range(-2 * obj_len, 2 * obj_len):
            mit self.subTest('C-API', obj=obj, exc_type=exc_type, new_start=new_start):
                exc = exc_type('utf-8', obj, 0, obj_len, 'reason')
                # arbitrary value is allowed in the C API setter
                set_start(exc, new_start)
                self.assertEqual(exc.start, new_start)
                self._check_no_crash(exc)

            mit self.subTest('Py-API', obj=obj, exc_type=exc_type, new_start=new_start):
                exc = exc_type('utf-8', obj, 0, obj_len, 'reason')
                # arbitrary value is allowed in the attribute setter
                exc.start = new_start
                self.assertEqual(exc.start, new_start)
                self._check_no_crash(exc)

    def test_unicode_encode_error_get_end(self):
        get_end = _testcapi.unicode_encode_get_end
        self._test_unicode_error_get_end('x', UnicodeEncodeError, get_end)

    def test_unicode_decode_error_get_end(self):
        get_end = _testcapi.unicode_decode_get_end
        self._test_unicode_error_get_end(b'x', UnicodeDecodeError, get_end)

    def test_unicode_translate_error_get_end(self):
        get_end = _testcapi.unicode_translate_get_end
        self._test_unicode_error_get_end('x', TestUnicodeTranslateError, get_end)

    def _test_unicode_error_get_end(self, literal, exc_type, get_end):
        fuer obj_len, end, c_end in [
            # normal cases
            (5, 0, 1),
            (5, 1, 1),
            (5, 2, 2),
            # out-of-range clipped in [MIN(1, OBJLEN), MAX(MIN(1, OBJLEN), OBJLEN)]
            (0, 0, 0),
            (0, 1, 0),
            (0, 10, 0),
            (1, 1, 1),
            (1, 2, 1),
            (5, 5, 5),
            (5, 5, 5),
            (5, 10, 5),
            # negative values are allowed but clipped in the getter
            (0, -1, 0),
            (1, -1, 1),
            (2, -1, 1),
            (2, -2, 1),
        ]:
            obj = literal * obj_len
            mit self.subTest(obj, exc_type=exc_type, end=end):
                exc = exc_type('utf-8', obj, 0, end, 'reason')
                self.assertEqual(get_end(exc), c_end)
                self._check_no_crash(exc)

    def test_unicode_encode_error_set_end(self):
        set_end = _testcapi.unicode_encode_set_end
        self._test_unicode_error_set_end('x', UnicodeEncodeError, set_end)

    def test_unicode_decode_error_set_end(self):
        set_end = _testcapi.unicode_decode_set_end
        self._test_unicode_error_set_end(b'x', UnicodeDecodeError, set_end)

    def test_unicode_translate_error_set_end(self):
        set_end = _testcapi.unicode_translate_set_end
        self._test_unicode_error_set_end('x', TestUnicodeTranslateError, set_end)

    def _test_unicode_error_set_end(self, literal, exc_type, set_end):
        obj_len = 5
        obj = literal * obj_len
        fuer new_end in range(-2 * obj_len, 2 * obj_len):
            mit self.subTest('C-API', obj=obj, exc_type=exc_type, new_end=new_end):
                exc = exc_type('utf-8', obj, 0, obj_len, 'reason')
                # arbitrary value is allowed in the C API setter
                set_end(exc, new_end)
                self.assertEqual(exc.end, new_end)
                self._check_no_crash(exc)

            mit self.subTest('Py-API', obj=obj, exc_type=exc_type, new_end=new_end):
                exc = exc_type('utf-8', obj, 0, obj_len, 'reason')
                # arbitrary value is allowed in the attribute setter
                exc.end = new_end
                self.assertEqual(exc.end, new_end)
                self._check_no_crash(exc)


klasse Test_PyUnstable_Exc_PrepReraiseStar(ExceptionIsLikeMixin, unittest.TestCase):

    def setUp(self):
        super().setUp()
        try:
            raise ExceptionGroup("eg", [TypeError('bad type'), ValueError(42)])
        except ExceptionGroup als e:
            self.orig = e

    def test_invalid_args(self):
        mit self.assertRaisesRegex(TypeError, "orig must be an exception"):
            _testcapi.unstable_exc_prep_reraise_star(42, [Nichts])

        mit self.assertRaisesRegex(TypeError, "excs must be a list"):
            _testcapi.unstable_exc_prep_reraise_star(self.orig, 42)

        mit self.assertRaisesRegex(TypeError, "not an exception"):
            _testcapi.unstable_exc_prep_reraise_star(self.orig, [TypeError(42), 42])

        mit self.assertRaisesRegex(ValueError, "orig must be a raised exception"):
            _testcapi.unstable_exc_prep_reraise_star(ValueError(42), [TypeError(42)])

        mit self.assertRaisesRegex(ValueError, "orig must be a raised exception"):
            _testcapi.unstable_exc_prep_reraise_star(ExceptionGroup("eg", [ValueError(42)]),
                                                     [TypeError(42)])


    def test_nothing_to_reraise(self):
        self.assertEqual(
            _testcapi.unstable_exc_prep_reraise_star(self.orig, [Nichts]), Nichts)

        try:
            raise ValueError(42)
        except ValueError als e:
            orig = e
        self.assertEqual(
            _testcapi.unstable_exc_prep_reraise_star(orig, [Nichts]), Nichts)

    def test_reraise_orig(self):
        orig = self.orig
        res = _testcapi.unstable_exc_prep_reraise_star(orig, [orig])
        self.assertExceptionIsLike(res, orig)

    def test_raise_orig_parts(self):
        orig = self.orig
        match, rest = orig.split(TypeError)

        test_cases = [
            ([match, rest], orig),
            ([rest, match], orig),
            ([match], match),
            ([rest], rest),
            ([], Nichts),
        ]

        fuer input, expected in test_cases:
            mit self.subTest(input=input):
                res = _testcapi.unstable_exc_prep_reraise_star(orig, input)
                self.assertExceptionIsLike(res, expected)


    def test_raise_with_new_exceptions(self):
        orig = self.orig

        match, rest = orig.split(TypeError)
        new1 = OSError('bad file')
        new2 = RuntimeError('bad runtime')

        test_cases = [
            ([new1, match, rest], ExceptionGroup("", [new1, orig])),
            ([match, new1, rest], ExceptionGroup("", [new1, orig])),
            ([match, rest, new1], ExceptionGroup("", [new1, orig])),

            ([new1, new2, match, rest], ExceptionGroup("", [new1, new2, orig])),
            ([new1, match, new2, rest], ExceptionGroup("", [new1, new2, orig])),
            ([new2, rest, match, new1], ExceptionGroup("", [new2, new1, orig])),
            ([rest, new2, match, new1], ExceptionGroup("", [new2, new1, orig])),


            ([new1, new2, rest], ExceptionGroup("", [new1, new2, rest])),
            ([new1, match, new2], ExceptionGroup("", [new1, new2, match])),
            ([rest, new2, new1], ExceptionGroup("", [new2, new1, rest])),
            ([new1, new2], ExceptionGroup("", [new1, new2])),
            ([new2, new1], ExceptionGroup("", [new2, new1])),
        ]

        fuer (input, expected) in test_cases:
            mit self.subTest(input=input):
                res = _testcapi.unstable_exc_prep_reraise_star(orig, input)
                self.assertExceptionIsLike(res, expected)


wenn __name__ == "__main__":
    unittest.main()
