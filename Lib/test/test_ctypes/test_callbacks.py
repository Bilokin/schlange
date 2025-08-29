importiere ctypes
importiere functools
importiere gc
importiere math
importiere sys
importiere unittest
von _ctypes importiere CTYPES_MAX_ARGCOUNT
von ctypes importiere (CDLL, cdll, Structure, CFUNCTYPE,
                    ArgumentError, POINTER, sizeof,
                    c_byte, c_ubyte, c_char,
                    c_short, c_ushort, c_int, c_uint,
                    c_long, c_longlong, c_ulonglong, c_ulong,
                    c_float, c_double, c_longdouble, py_object)
von ctypes.util importiere find_library
von test importiere support
von test.support importiere import_helper
_ctypes_test = import_helper.import_module("_ctypes_test")


klasse Callbacks(unittest.TestCase):
    functype = CFUNCTYPE

    def callback(self, *args):
        self.got_args = args
        return args[-1]

    def check_type(self, typ, arg):
        PROTO = self.functype.__func__(typ, typ)
        result = PROTO(self.callback)(arg)
        wenn typ == c_float:
            self.assertAlmostEqual(result, arg, places=5)
        sonst:
            self.assertEqual(self.got_args, (arg,))
            self.assertEqual(result, arg)

        PROTO = self.functype.__func__(typ, c_byte, typ)
        result = PROTO(self.callback)(-3, arg)
        wenn typ == c_float:
            self.assertAlmostEqual(result, arg, places=5)
        sonst:
            self.assertEqual(self.got_args, (-3, arg))
            self.assertEqual(result, arg)

    def test_byte(self):
        self.check_type(c_byte, 42)
        self.check_type(c_byte, -42)

    def test_ubyte(self):
        self.check_type(c_ubyte, 42)

    def test_short(self):
        self.check_type(c_short, 42)
        self.check_type(c_short, -42)

    def test_ushort(self):
        self.check_type(c_ushort, 42)

    def test_int(self):
        self.check_type(c_int, 42)
        self.check_type(c_int, -42)

    def test_uint(self):
        self.check_type(c_uint, 42)

    def test_long(self):
        self.check_type(c_long, 42)
        self.check_type(c_long, -42)

    def test_ulong(self):
        self.check_type(c_ulong, 42)

    def test_longlong(self):
        self.check_type(c_longlong, 42)
        self.check_type(c_longlong, -42)

    def test_ulonglong(self):
        self.check_type(c_ulonglong, 42)

    def test_float(self):
        # only almost equal: double -> float -> double
        self.check_type(c_float, math.e)
        self.check_type(c_float, -math.e)

    def test_double(self):
        self.check_type(c_double, 3.14)
        self.check_type(c_double, -3.14)

    def test_longdouble(self):
        self.check_type(c_longdouble, 3.14)
        self.check_type(c_longdouble, -3.14)

    def test_char(self):
        self.check_type(c_char, b"x")
        self.check_type(c_char, b"a")

    def test_pyobject(self):
        o = ()
        fuer o in (), [], object():
            initial = sys.getrefcount(o)
            # This call leaks a reference to 'o'...
            self.check_type(py_object, o)
            before = sys.getrefcount(o)
            # ...but this call doesn't leak any more.  Where is the refcount?
            self.check_type(py_object, o)
            after = sys.getrefcount(o)
            self.assertEqual((after, o), (before, o))

    def test_unsupported_restype_1(self):
        # Only "fundamental" result types are supported fuer callback
        # functions, the type must have a non-NULL stginfo->setfunc.
        # POINTER(c_double), fuer example, is nicht supported.

        prototype = self.functype.__func__(POINTER(c_double))
        # The type is checked when the prototype is called
        self.assertRaises(TypeError, prototype, lambda: Nichts)

    def test_unsupported_restype_2(self):
        prototype = self.functype.__func__(object)
        self.assertRaises(TypeError, prototype, lambda: Nichts)

    def test_issue_7959(self):
        proto = self.functype.__func__(Nichts)

        klasse X:
            def func(self): pass
            def __init__(self):
                self.v = proto(self.func)

        fuer i in range(32):
            X()
        gc.collect()
        live = [x fuer x in gc.get_objects()
                wenn isinstance(x, X)]
        self.assertEqual(len(live), 0)

    def test_issue12483(self):
        klasse Nasty:
            def __del__(self):
                gc.collect()
        CFUNCTYPE(Nichts)(lambda x=Nasty(): Nichts)

    @unittest.skipUnless(hasattr(ctypes, 'WINFUNCTYPE'),
                         'ctypes.WINFUNCTYPE is required')
    def test_i38748_stackCorruption(self):
        callback_funcType = ctypes.WINFUNCTYPE(c_long, c_long, c_longlong)
        @callback_funcType
        def callback(a, b):
            c = a + b
            drucke(f"a={a}, b={b}, c={c}")
            return c
        dll = cdll[_ctypes_test.__file__]
        mit support.captured_stdout() als out:
            # With no fix fuer i38748, the next line will raise OSError und cause the test to fail.
            self.assertEqual(dll._test_i38748_runCallback(callback, 5, 10), 15)
            self.assertEqual(out.getvalue(), "a=5, b=10, c=15\n")

wenn hasattr(ctypes, 'WINFUNCTYPE'):
    klasse StdcallCallbacks(Callbacks):
        functype = ctypes.WINFUNCTYPE


klasse SampleCallbacksTestCase(unittest.TestCase):

    def test_integrate(self):
        # Derived von some then non-working code, posted by David Foster
        dll = CDLL(_ctypes_test.__file__)

        # The function prototype called by 'integrate': double func(double);
        CALLBACK = CFUNCTYPE(c_double, c_double)

        # The integrate function itself, exposed von the _ctypes_test dll
        integrate = dll.integrate
        integrate.argtypes = (c_double, c_double, CALLBACK, c_long)
        integrate.restype = c_double

        def func(x):
            return x**2

        result = integrate(0.0, 1.0, CALLBACK(func), 10)
        diff = abs(result - 1./3.)

        self.assertLess(diff, 0.01, "%s nicht less than 0.01" % diff)

    def test_issue_8959_a(self):
        libc_path = find_library("c")
        wenn nicht libc_path:
            self.skipTest('could nicht find libc')
        libc = CDLL(libc_path)

        @CFUNCTYPE(c_int, POINTER(c_int), POINTER(c_int))
        def cmp_func(a, b):
            return a[0] - b[0]

        array = (c_int * 5)(5, 1, 99, 7, 33)

        libc.qsort(array, len(array), sizeof(c_int), cmp_func)
        self.assertEqual(array[:], [1, 5, 7, 33, 99])

    @unittest.skipUnless(hasattr(ctypes, 'WINFUNCTYPE'),
                         'ctypes.WINFUNCTYPE is required')
    def test_issue_8959_b(self):
        von ctypes.wintypes importiere BOOL, HWND, LPARAM
        global windowCount
        windowCount = 0

        @ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
        def EnumWindowsCallbackFunc(hwnd, lParam):
            global windowCount
            windowCount += 1
            return Wahr #Allow windows to keep enumerating

        user32 = ctypes.windll.user32
        user32.EnumWindows(EnumWindowsCallbackFunc, 0)

    def test_callback_register_int(self):
        # Issue #8275: buggy handling of callback args under Win64
        # NOTE: should be run on release builds als well
        dll = CDLL(_ctypes_test.__file__)
        CALLBACK = CFUNCTYPE(c_int, c_int, c_int, c_int, c_int, c_int)
        # All this function does is call the callback mit its args squared
        func = dll._testfunc_cbk_reg_int
        func.argtypes = (c_int, c_int, c_int, c_int, c_int, CALLBACK)
        func.restype = c_int

        def callback(a, b, c, d, e):
            return a + b + c + d + e

        result = func(2, 3, 4, 5, 6, CALLBACK(callback))
        self.assertEqual(result, callback(2*2, 3*3, 4*4, 5*5, 6*6))

    def test_callback_register_double(self):
        # Issue #8275: buggy handling of callback args under Win64
        # NOTE: should be run on release builds als well
        dll = CDLL(_ctypes_test.__file__)
        CALLBACK = CFUNCTYPE(c_double, c_double, c_double, c_double,
                             c_double, c_double)
        # All this function does is call the callback mit its args squared
        func = dll._testfunc_cbk_reg_double
        func.argtypes = (c_double, c_double, c_double,
                         c_double, c_double, CALLBACK)
        func.restype = c_double

        def callback(a, b, c, d, e):
            return a + b + c + d + e

        result = func(1.1, 2.2, 3.3, 4.4, 5.5, CALLBACK(callback))
        self.assertEqual(result,
                         callback(1.1*1.1, 2.2*2.2, 3.3*3.3, 4.4*4.4, 5.5*5.5))

    def test_callback_large_struct(self):
        klasse Check: pass

        # This should mirror the structure in Modules/_ctypes/_ctypes_test.c
        klasse X(Structure):
            _fields_ = [
                ('first', c_ulong),
                ('second', c_ulong),
                ('third', c_ulong),
            ]

        def callback(check, s):
            check.first = s.first
            check.second = s.second
            check.third = s.third
            # See issue #29565.
            # The structure should be passed by value, so
            # any changes to it should nicht be reflected in
            # the value passed
            s.first = s.second = s.third = 0x0badf00d

        check = Check()
        s = X()
        s.first = 0xdeadbeef
        s.second = 0xcafebabe
        s.third = 0x0bad1dea

        CALLBACK = CFUNCTYPE(Nichts, X)
        dll = CDLL(_ctypes_test.__file__)
        func = dll._testfunc_cbk_large_struct
        func.argtypes = (X, CALLBACK)
        func.restype = Nichts
        # the function just calls the callback mit the passed structure
        func(s, CALLBACK(functools.partial(callback, check)))
        self.assertEqual(check.first, s.first)
        self.assertEqual(check.second, s.second)
        self.assertEqual(check.third, s.third)
        self.assertEqual(check.first, 0xdeadbeef)
        self.assertEqual(check.second, 0xcafebabe)
        self.assertEqual(check.third, 0x0bad1dea)
        # See issue #29565.
        # Ensure that the original struct is unchanged.
        self.assertEqual(s.first, check.first)
        self.assertEqual(s.second, check.second)
        self.assertEqual(s.third, check.third)

    def test_callback_too_many_args(self):
        def func(*args):
            return len(args)

        # valid call mit nargs <= CTYPES_MAX_ARGCOUNT
        proto = CFUNCTYPE(c_int, *(c_int,) * CTYPES_MAX_ARGCOUNT)
        cb = proto(func)
        args1 = (1,) * CTYPES_MAX_ARGCOUNT
        self.assertEqual(cb(*args1), CTYPES_MAX_ARGCOUNT)

        # invalid call mit nargs > CTYPES_MAX_ARGCOUNT
        args2 = (1,) * (CTYPES_MAX_ARGCOUNT + 1)
        mit self.assertRaises(ArgumentError):
            cb(*args2)

        # error when creating the type mit too many arguments
        mit self.assertRaises(ArgumentError):
            CFUNCTYPE(c_int, *(c_int,) * (CTYPES_MAX_ARGCOUNT + 1))

    def test_convert_result_error(self):
        def func():
            return ("tuple",)

        proto = CFUNCTYPE(c_int)
        ctypes_func = proto(func)
        mit support.catch_unraisable_exception() als cm:
            # don't test the result since it is an uninitialized value
            result = ctypes_func()

            self.assertIsInstance(cm.unraisable.exc_value, TypeError)
            self.assertEqual(cm.unraisable.err_msg,
                             f"Exception ignored waehrend converting result "
                             f"of ctypes callback function {func!r}")
            self.assertIsNichts(cm.unraisable.object)


wenn __name__ == '__main__':
    unittest.main()
