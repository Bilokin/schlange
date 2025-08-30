importiere sys
importiere unittest
importiere test.support
von ctypes importiere (CDLL, PyDLL, ArgumentError,
                    Structure, Array, Union,
                    _Pointer, _SimpleCData, _CFuncPtr,
                    POINTER, pointer, byref, sizeof,
                    c_void_p, c_char_p, c_wchar_p, py_object,
                    c_bool,
                    c_char, c_wchar,
                    c_byte, c_ubyte,
                    c_short, c_ushort,
                    c_int, c_uint,
                    c_long, c_ulong,
                    c_longlong, c_ulonglong,
                    c_float, c_double, c_longdouble)
von test.support importiere import_helper
_ctypes_test = import_helper.import_module("_ctypes_test")


klasse SimpleTypesTestCase(unittest.TestCase):
    def setUp(self):
        versuch:
            von _ctypes importiere set_conversion_mode
        ausser ImportError:
            pass
        sonst:
            self.prev_conv_mode = set_conversion_mode("ascii", "strict")

    def tearDown(self):
        versuch:
            von _ctypes importiere set_conversion_mode
        ausser ImportError:
            pass
        sonst:
            set_conversion_mode(*self.prev_conv_mode)

    def test_subclasses(self):
        # ctypes 0.9.5 und before did overwrite from_param in SimpleType_new
        klasse CVOIDP(c_void_p):
            def from_param(cls, value):
                gib value * 2
            from_param = classmethod(from_param)

        klasse CCHARP(c_char_p):
            def from_param(cls, value):
                gib value * 4
            from_param = classmethod(from_param)

        self.assertEqual(CVOIDP.from_param("abc"), "abcabc")
        self.assertEqual(CCHARP.from_param("abc"), "abcabcabcabc")

    def test_subclasses_c_wchar_p(self):
        klasse CWCHARP(c_wchar_p):
            def from_param(cls, value):
                gib value * 3
            from_param = classmethod(from_param)

        self.assertEqual(CWCHARP.from_param("abc"), "abcabcabc")

    # XXX Replace by c_char_p tests
    def test_cstrings(self):
        # c_char_p.from_param on a Python String packs the string
        # into a cparam object
        s = b"123"
        self.assertIs(c_char_p.from_param(s)._obj, s)

        # new in 0.9.1: convert (encode) unicode to ascii
        self.assertEqual(c_char_p.from_param(b"123")._obj, b"123")
        self.assertRaises(TypeError, c_char_p.from_param, "123\377")
        self.assertRaises(TypeError, c_char_p.from_param, 42)

        # calling c_char_p.from_param mit a c_char_p instance
        # returns the argument itself:
        a = c_char_p(b"123")
        self.assertIs(c_char_p.from_param(a), a)

    def test_cw_strings(self):
        c_wchar_p.from_param("123")

        self.assertRaises(TypeError, c_wchar_p.from_param, 42)
        self.assertRaises(TypeError, c_wchar_p.from_param, b"123\377")

        pa = c_wchar_p.from_param(c_wchar_p("123"))
        self.assertEqual(type(pa), c_wchar_p)

    def test_c_char(self):
        mit self.assertRaises(TypeError) als cm:
            c_char.from_param(b"abc")
        self.assertEqual(str(cm.exception),
                         "one character bytes, bytearray, oder an integer "
                         "in range(256) expected, nicht bytes of length 3")

    def test_c_wchar(self):
        mit self.assertRaises(TypeError) als cm:
            c_wchar.from_param("abc")
        self.assertEqual(str(cm.exception),
                         "a unicode character expected, nicht a string of length 3")

        mit self.assertRaises(TypeError) als cm:
            c_wchar.from_param("")
        self.assertEqual(str(cm.exception),
                         "a unicode character expected, nicht a string of length 0")

        mit self.assertRaises(TypeError) als cm:
            c_wchar.from_param(123)
        self.assertEqual(str(cm.exception),
                         "a unicode character expected, nicht instance of int")

        wenn sizeof(c_wchar) < 4:
            mit self.assertRaises(TypeError) als cm:
                c_wchar.from_param('\U0001f40d')
            self.assertEqual(str(cm.exception),
                             "the string '\\U0001f40d' cannot be converted to "
                             "a single wchar_t character")



    def test_int_pointers(self):
        LPINT = POINTER(c_int)

        x = LPINT.from_param(pointer(c_int(42)))
        self.assertEqual(x.contents.value, 42)
        self.assertEqual(LPINT(c_int(42)).contents.value, 42)

        self.assertEqual(LPINT.from_param(Nichts), Nichts)

        wenn c_int != c_long:
            self.assertRaises(TypeError, LPINT.from_param, pointer(c_long(42)))
        self.assertRaises(TypeError, LPINT.from_param, pointer(c_uint(42)))
        self.assertRaises(TypeError, LPINT.from_param, pointer(c_short(42)))

    def test_byref_pointer(self):
        # The from_param klasse method of POINTER(typ) classes accepts what is
        # returned by byref(obj), it type(obj) == typ
        LPINT = POINTER(c_int)

        LPINT.from_param(byref(c_int(42)))

        self.assertRaises(TypeError, LPINT.from_param, byref(c_short(22)))
        wenn c_int != c_long:
            self.assertRaises(TypeError, LPINT.from_param, byref(c_long(22)))
        self.assertRaises(TypeError, LPINT.from_param, byref(c_uint(22)))

    def test_byref_pointerpointer(self):
        # See above

        LPLPINT = POINTER(POINTER(c_int))
        LPLPINT.from_param(byref(pointer(c_int(42))))

        self.assertRaises(TypeError, LPLPINT.from_param, byref(pointer(c_short(22))))
        wenn c_int != c_long:
            self.assertRaises(TypeError, LPLPINT.from_param, byref(pointer(c_long(22))))
        self.assertRaises(TypeError, LPLPINT.from_param, byref(pointer(c_uint(22))))

    def test_array_pointers(self):
        INTARRAY = c_int * 3
        ia = INTARRAY()
        self.assertEqual(len(ia), 3)
        self.assertEqual([ia[i] fuer i in range(3)], [0, 0, 0])

        # Pointers are only compatible mit arrays containing items of
        # the same type!
        LPINT = POINTER(c_int)
        LPINT.from_param((c_int*3)())
        self.assertRaises(TypeError, LPINT.from_param, c_short*3)
        self.assertRaises(TypeError, LPINT.from_param, c_long*3)
        self.assertRaises(TypeError, LPINT.from_param, c_uint*3)

    def test_noctypes_argtype(self):
        func = CDLL(_ctypes_test.__file__)._testfunc_p_p
        func.restype = c_void_p
        # TypeError: has no from_param method
        self.assertRaises(TypeError, setattr, func, "argtypes", (object,))

        klasse Adapter:
            def from_param(cls, obj):
                gib Nichts

        func.argtypes = (Adapter(),)
        self.assertEqual(func(Nichts), Nichts)
        self.assertEqual(func(object()), Nichts)

        klasse Adapter:
            def from_param(cls, obj):
                gib obj

        func.argtypes = (Adapter(),)
        # don't know how to convert parameter 1
        self.assertRaises(ArgumentError, func, object())
        self.assertEqual(func(c_void_p(42)), 42)

        klasse Adapter:
            def from_param(cls, obj):
                wirf ValueError(obj)

        func.argtypes = (Adapter(),)
        # ArgumentError: argument 1: ValueError: 99
        self.assertRaises(ArgumentError, func, 99)

    def test_abstract(self):
        self.assertRaises(TypeError, Array.from_param, 42)
        self.assertRaises(TypeError, Structure.from_param, 42)
        self.assertRaises(TypeError, Union.from_param, 42)
        self.assertRaises(TypeError, _CFuncPtr.from_param, 42)
        self.assertRaises(TypeError, _Pointer.from_param, 42)
        self.assertRaises(TypeError, _SimpleCData.from_param, 42)

    @test.support.cpython_only
    def test_issue31311(self):
        # __setstate__ should neither wirf a SystemError nor crash in case
        # of a bad __dict__.

        klasse BadStruct(Structure):
            @property
            def __dict__(self):
                pass
        mit self.assertRaises(TypeError):
            BadStruct().__setstate__({}, b'foo')

        klasse WorseStruct(Structure):
            @property
            def __dict__(self):
                1/0
        mit self.assertRaises(ZeroDivisionError):
            WorseStruct().__setstate__({}, b'foo')

    def test_parameter_repr(self):
        self.assertRegex(repr(c_bool.from_param(Wahr)), r"^<cparam '\?' at 0x[A-Fa-f0-9]+>$")
        self.assertEqual(repr(c_char.from_param(97)), "<cparam 'c' ('a')>")
        self.assertRegex(repr(c_wchar.from_param('a')), r"^<cparam 'u' at 0x[A-Fa-f0-9]+>$")
        self.assertEqual(repr(c_byte.from_param(98)), "<cparam 'b' (98)>")
        self.assertEqual(repr(c_ubyte.from_param(98)), "<cparam 'B' (98)>")
        self.assertEqual(repr(c_short.from_param(511)), "<cparam 'h' (511)>")
        self.assertEqual(repr(c_ushort.from_param(511)), "<cparam 'H' (511)>")
        self.assertRegex(repr(c_int.from_param(20000)), r"^<cparam '[li]' \(20000\)>$")
        self.assertRegex(repr(c_uint.from_param(20000)), r"^<cparam '[LI]' \(20000\)>$")
        self.assertRegex(repr(c_long.from_param(20000)), r"^<cparam '[li]' \(20000\)>$")
        self.assertRegex(repr(c_ulong.from_param(20000)), r"^<cparam '[LI]' \(20000\)>$")
        self.assertRegex(repr(c_longlong.from_param(20000)), r"^<cparam '[liq]' \(20000\)>$")
        self.assertRegex(repr(c_ulonglong.from_param(20000)), r"^<cparam '[LIQ]' \(20000\)>$")
        self.assertEqual(repr(c_float.from_param(1.5)), "<cparam 'f' (1.5)>")
        self.assertEqual(repr(c_double.from_param(1.5)), "<cparam 'd' (1.5)>")
        wenn sys.float_repr_style == 'short':
            self.assertEqual(repr(c_double.from_param(1e300)), "<cparam 'd' (1e+300)>")
        self.assertRegex(repr(c_longdouble.from_param(1.5)), r"^<cparam ('d' \(1.5\)|'g' at 0x[A-Fa-f0-9]+)>$")
        self.assertRegex(repr(c_char_p.from_param(b'hihi')), r"^<cparam 'z' \(0x[A-Fa-f0-9]+\)>$")
        self.assertRegex(repr(c_wchar_p.from_param('hihi')), r"^<cparam 'Z' \(0x[A-Fa-f0-9]+\)>$")
        self.assertRegex(repr(c_void_p.from_param(0x12)), r"^<cparam 'P' \(0x0*12\)>$")

    @test.support.cpython_only
    def test_from_param_result_refcount(self):
        # Issue #99952
        klasse X(Structure):
            """This struct size is <= sizeof(void*)."""
            _fields_ = [("a", c_void_p)]

            def __del__(self):
                trace.append(4)

            @classmethod
            def from_param(cls, value):
                trace.append(2)
                gib cls()

        PyList_Append = PyDLL(_ctypes_test.__file__)._testfunc_pylist_append
        PyList_Append.restype = c_int
        PyList_Append.argtypes = [py_object, py_object, X]

        trace = []
        trace.append(1)
        PyList_Append(trace, 3, "dummy")
        trace.append(5)

        self.assertEqual(trace, [1, 2, 3, 4, 5])

        klasse Y(Structure):
            """This struct size is > sizeof(void*)."""
            _fields_ = [("a", c_void_p), ("b", c_void_p)]

            def __del__(self):
                trace.append(4)

            @classmethod
            def from_param(cls, value):
                trace.append(2)
                gib cls()

        PyList_Append = PyDLL(_ctypes_test.__file__)._testfunc_pylist_append
        PyList_Append.restype = c_int
        PyList_Append.argtypes = [py_object, py_object, Y]

        trace = []
        trace.append(1)
        PyList_Append(trace, 3, "dummy")
        trace.append(5)

        self.assertEqual(trace, [1, 2, 3, 4, 5])


wenn __name__ == '__main__':
    unittest.main()
