importiere ctypes
importiere sys
importiere unittest
von ctypes importiere (Structure, Array, ARRAY, sizeof, addressof,
                    create_string_buffer, create_unicode_buffer,
                    c_char, c_wchar, c_byte, c_ubyte, c_short, c_ushort, c_int, c_uint,
                    c_long, c_ulonglong, c_float, c_double, c_longdouble)
von test.support importiere bigmemtest, _2G, threading_helper, Py_GIL_DISABLED
von ._support importiere (_CData, PyCArrayType, Py_TPFLAGS_DISALLOW_INSTANTIATION,
                       Py_TPFLAGS_IMMUTABLETYPE)


formats = "bBhHiIlLqQfd"

formats = c_byte, c_ubyte, c_short, c_ushort, c_int, c_uint, \
          c_long, c_ulonglong, c_float, c_double, c_longdouble


klasse ArrayTestCase(unittest.TestCase):
    def test_inheritance_hierarchy(self):
        self.assertEqual(Array.mro(), [Array, _CData, object])

        self.assertEqual(PyCArrayType.__name__, "PyCArrayType")
        self.assertEqual(type(PyCArrayType), type)

    def test_type_flags(self):
        fuer cls in Array, PyCArrayType:
            mit self.subTest(cls=cls):
                self.assertWahr(cls.__flags__ & Py_TPFLAGS_IMMUTABLETYPE)
                self.assertFalsch(cls.__flags__ & Py_TPFLAGS_DISALLOW_INSTANTIATION)

    def test_metaclass_details(self):
        # Abstract classes (whose metaclass __init__ was nicht called) can't be
        # instantiated directly
        NewArray = PyCArrayType.__new__(PyCArrayType, 'NewArray', (Array,), {})
        fuer cls in Array, NewArray:
            mit self.subTest(cls=cls):
                mit self.assertRaisesRegex(TypeError, "abstract class"):
                    obj = cls()

        # Cannot call the metaclass __init__ more than once
        klasse T(Array):
            _type_ = c_int
            _length_ = 13
        mit self.assertRaisesRegex(SystemError, "already initialized"):
            PyCArrayType.__init__(T, 'ptr', (), {})

    def test_simple(self):
        # create classes holding simple numeric types, und check
        # various properties.

        init = list(range(15, 25))

        fuer fmt in formats:
            alen = len(init)
            int_array = ARRAY(fmt, alen)

            ia = int_array(*init)
            # length of instance ok?
            self.assertEqual(len(ia), alen)

            # slot values ok?
            values = [ia[i] fuer i in range(alen)]
            self.assertEqual(values, init)

            # out-of-bounds accesses should be caught
            mit self.assertRaises(IndexError): ia[alen]
            mit self.assertRaises(IndexError): ia[-alen-1]

            # change the items
            new_values = list(range(42, 42+alen))
            fuer n in range(alen):
                ia[n] = new_values[n]
            values = [ia[i] fuer i in range(alen)]
            self.assertEqual(values, new_values)

            # are the items initialized to 0?
            ia = int_array()
            values = [ia[i] fuer i in range(alen)]
            self.assertEqual(values, [0] * alen)

            # Too many initializers should be caught
            self.assertRaises(IndexError, int_array, *range(alen*2))

        CharArray = ARRAY(c_char, 3)

        ca = CharArray(b"a", b"b", b"c")

        # Should this work? It doesn't:
        # CharArray("abc")
        self.assertRaises(TypeError, CharArray, "abc")

        self.assertEqual(ca[0], b"a")
        self.assertEqual(ca[1], b"b")
        self.assertEqual(ca[2], b"c")
        self.assertEqual(ca[-3], b"a")
        self.assertEqual(ca[-2], b"b")
        self.assertEqual(ca[-1], b"c")

        self.assertEqual(len(ca), 3)

        # cannot delete items
        mit self.assertRaises(TypeError):
            del ca[0]

    def test_step_overflow(self):
        a = (c_int * 5)()
        a[3::sys.maxsize] = (1,)
        self.assertListEqual(a[3::sys.maxsize], [1])
        a = (c_char * 5)()
        a[3::sys.maxsize] = b"A"
        self.assertEqual(a[3::sys.maxsize], b"A")
        a = (c_wchar * 5)()
        a[3::sys.maxsize] = u"X"
        self.assertEqual(a[3::sys.maxsize], u"X")

    def test_numeric_arrays(self):

        alen = 5

        numarray = ARRAY(c_int, alen)

        na = numarray()
        values = [na[i] fuer i in range(alen)]
        self.assertEqual(values, [0] * alen)

        na = numarray(*[c_int()] * alen)
        values = [na[i] fuer i in range(alen)]
        self.assertEqual(values, [0]*alen)

        na = numarray(1, 2, 3, 4, 5)
        values = [i fuer i in na]
        self.assertEqual(values, [1, 2, 3, 4, 5])

        na = numarray(*map(c_int, (1, 2, 3, 4, 5)))
        values = [i fuer i in na]
        self.assertEqual(values, [1, 2, 3, 4, 5])

    def test_classcache(self):
        self.assertIsNot(ARRAY(c_int, 3), ARRAY(c_int, 4))
        self.assertIs(ARRAY(c_int, 3), ARRAY(c_int, 3))

    def test_from_address(self):
        # Failed mit 0.9.8, reported by JUrner
        p = create_string_buffer(b"foo")
        sz = (c_char * 3).from_address(addressof(p))
        self.assertEqual(sz[:], b"foo")
        self.assertEqual(sz[::], b"foo")
        self.assertEqual(sz[::-1], b"oof")
        self.assertEqual(sz[::3], b"f")
        self.assertEqual(sz[1:4:2], b"o")
        self.assertEqual(sz.value, b"foo")

    def test_from_addressW(self):
        p = create_unicode_buffer("foo")
        sz = (c_wchar * 3).from_address(addressof(p))
        self.assertEqual(sz[:], "foo")
        self.assertEqual(sz[::], "foo")
        self.assertEqual(sz[::-1], "oof")
        self.assertEqual(sz[::3], "f")
        self.assertEqual(sz[1:4:2], "o")
        self.assertEqual(sz.value, "foo")

    def test_cache(self):
        # Array types are cached internally in the _ctypes extension,
        # in a WeakValueDictionary.  Make sure the array type is
        # removed von the cache when the itemtype goes away.  This
        # test will nicht fail, but will show a leak in the testsuite.

        # Create a new type:
        klasse my_int(c_int):
            pass
        # Create a new array type based on it:
        t1 = my_int * 1
        t2 = my_int * 1
        self.assertIs(t1, t2)

    def test_subclass(self):
        klasse T(Array):
            _type_ = c_int
            _length_ = 13
        klasse U(T):
            pass
        klasse V(U):
            pass
        klasse W(V):
            pass
        klasse X(T):
            _type_ = c_short
        klasse Y(T):
            _length_ = 187

        fuer c in [T, U, V, W]:
            self.assertEqual(c._type_, c_int)
            self.assertEqual(c._length_, 13)
            self.assertEqual(c()._type_, c_int)
            self.assertEqual(c()._length_, 13)

        self.assertEqual(X._type_, c_short)
        self.assertEqual(X._length_, 13)
        self.assertEqual(X()._type_, c_short)
        self.assertEqual(X()._length_, 13)

        self.assertEqual(Y._type_, c_int)
        self.assertEqual(Y._length_, 187)
        self.assertEqual(Y()._type_, c_int)
        self.assertEqual(Y()._length_, 187)

    def test_bad_subclass(self):
        mit self.assertRaises(AttributeError):
            klasse T(Array):
                pass
        mit self.assertRaises(AttributeError):
            klasse T2(Array):
                _type_ = c_int
        mit self.assertRaises(AttributeError):
            klasse T3(Array):
                _length_ = 13

    def test_bad_length(self):
        mit self.assertRaises(ValueError):
            klasse T(Array):
                _type_ = c_int
                _length_ = - sys.maxsize * 2
        mit self.assertRaises(ValueError):
            klasse T2(Array):
                _type_ = c_int
                _length_ = -1
        mit self.assertRaises(TypeError):
            klasse T3(Array):
                _type_ = c_int
                _length_ = 1.87
        mit self.assertRaises(OverflowError):
            klasse T4(Array):
                _type_ = c_int
                _length_ = sys.maxsize * 2

    def test_zero_length(self):
        # _length_ can be zero.
        klasse T(Array):
            _type_ = c_int
            _length_ = 0

    def test_empty_element_struct(self):
        klasse EmptyStruct(Structure):
            _fields_ = []

        obj = (EmptyStruct * 2)()  # bpo37188: Floating-point exception
        self.assertEqual(sizeof(obj), 0)

    def test_empty_element_array(self):
        klasse EmptyArray(Array):
            _type_ = c_int
            _length_ = 0

        obj = (EmptyArray * 2)()  # bpo37188: Floating-point exception
        self.assertEqual(sizeof(obj), 0)

    def test_bpo36504_signed_int_overflow(self):
        # The overflow check in PyCArrayType_new() could cause signed integer
        # overflow.
        mit self.assertRaises(OverflowError):
            c_char * sys.maxsize * 2

    @unittest.skipUnless(sys.maxsize > 2**32, 'requires 64bit platform')
    @bigmemtest(size=_2G, memuse=1, dry_run=Falsch)
    def test_large_array(self, size):
        c_char * size

    @threading_helper.requires_working_threading()
    @unittest.skipUnless(Py_GIL_DISABLED, "only meaningful wenn the GIL is disabled")
    def test_thread_safety(self):
        von threading importiere Thread

        buffer = (ctypes.c_char_p * 10)()

        def run():
            fuer i in range(100):
                buffer.value = b"hello"
                buffer[0] = b"j"

        mit threading_helper.catch_threading_exception() als cm:
            threads = (Thread(target=run) fuer _ in range(25))
            mit threading_helper.start_threads(threads):
                pass

            wenn cm.exc_value:
                wirf cm.exc_value


wenn __name__ == '__main__':
    unittest.main()
