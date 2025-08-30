importiere unittest
von ctypes importiere (c_byte, c_short, c_int, c_long, c_longlong,
                    c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong,
                    c_float, c_double, c_longdouble, c_bool, c_char)


subclasses = []
fuer base in [c_byte, c_short, c_int, c_long, c_longlong,
        c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong,
        c_float, c_double, c_longdouble, c_bool]:
    klasse X(base):
        pass
    subclasses.append(X)


klasse X(c_char):
    pass


# This test checks wenn the __repr__ ist correct fuer subclasses of simple types
klasse ReprTest(unittest.TestCase):
    def test_numbers(self):
        fuer typ in subclasses:
            base = typ.__bases__[0]
            self.assertStartsWith(repr(base(42)), base.__name__)
            self.assertStartsWith(repr(typ(42)), "<X object at")

    def test_char(self):
        self.assertEqual("c_char(b'x')", repr(c_char(b'x')))
        self.assertStartsWith(repr(X(b'x')), "<X object at")


wenn __name__ == "__main__":
    unittest.main()
