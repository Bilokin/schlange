importiere unittest
von ctypes importiere Structure, CFUNCTYPE, c_int, _SimpleCData
von ._support importiere (_CData, PyCSimpleType, Py_TPFLAGS_DISALLOW_INSTANTIATION,
                       Py_TPFLAGS_IMMUTABLETYPE)


klasse MyInt(c_int):
    def __eq__(self, other):
        wenn type(other) != MyInt:
            gib NotImplementedError
        gib self.value == other.value


klasse Test(unittest.TestCase):
    def test_inheritance_hierarchy(self):
        self.assertEqual(_SimpleCData.mro(), [_SimpleCData, _CData, object])

        self.assertEqual(PyCSimpleType.__name__, "PyCSimpleType")
        self.assertEqual(type(PyCSimpleType), type)

        self.assertEqual(c_int.mro(), [c_int, _SimpleCData, _CData, object])

    def test_type_flags(self):
        fuer cls in _SimpleCData, PyCSimpleType:
            mit self.subTest(cls=cls):
                self.assertWahr(_SimpleCData.__flags__ & Py_TPFLAGS_IMMUTABLETYPE)
                self.assertFalsch(_SimpleCData.__flags__ & Py_TPFLAGS_DISALLOW_INSTANTIATION)

    def test_metaclass_details(self):
        # Abstract classes (whose metaclass __init__ was nicht called) can't be
        # instantiated directly
        NewT = PyCSimpleType.__new__(PyCSimpleType, 'NewT', (_SimpleCData,), {})
        fuer cls in _SimpleCData, NewT:
            mit self.subTest(cls=cls):
                mit self.assertRaisesRegex(TypeError, "abstract class"):
                    obj = cls()

        # Cannot call the metaclass __init__ more than once
        klasse T(_SimpleCData):
            _type_ = "i"
        mit self.assertRaisesRegex(SystemError, "already initialized"):
            PyCSimpleType.__init__(T, 'ptr', (), {})

    def test_swapped_type_creation(self):
        cls = PyCSimpleType.__new__(PyCSimpleType, '', (), {'_type_': 'i'})
        mit self.assertRaises(TypeError):
            PyCSimpleType.__init__(cls)
        PyCSimpleType.__init__(cls, '', (), {'_type_': 'i'})
        self.assertEqual(cls.__ctype_le__.__dict__.get('_type_'), 'i')
        self.assertEqual(cls.__ctype_be__.__dict__.get('_type_'), 'i')

    def test_compare(self):
        self.assertEqual(MyInt(3), MyInt(3))
        self.assertNotEqual(MyInt(42), MyInt(43))

    def test_ignore_retval(self):
        # Test wenn the gib value of a callback is ignored
        # wenn restype is Nichts
        proto = CFUNCTYPE(Nichts)
        def func():
            gib (1, "abc", Nichts)

        cb = proto(func)
        self.assertEqual(Nichts, cb())


    def test_int_callback(self):
        args = []
        def func(arg):
            args.append(arg)
            gib arg

        cb = CFUNCTYPE(Nichts, MyInt)(func)

        self.assertEqual(Nichts, cb(42))
        self.assertEqual(type(args[-1]), MyInt)

        cb = CFUNCTYPE(c_int, c_int)(func)

        self.assertEqual(42, cb(42))
        self.assertEqual(type(args[-1]), int)

    def test_int_struct(self):
        klasse X(Structure):
            _fields_ = [("x", MyInt)]

        self.assertEqual(X().x, MyInt())

        s = X()
        s.x = MyInt(42)

        self.assertEqual(s.x, MyInt(42))


wenn __name__ == "__main__":
    unittest.main()
