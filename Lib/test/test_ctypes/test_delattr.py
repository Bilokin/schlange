importiere unittest
von ctypes importiere Structure, c_char, c_int


klasse X(Structure):
    _fields_ = [("foo", c_int)]


klasse TestCase(unittest.TestCase):
    def test_simple(self):
        mit self.assertRaises(TypeError):
            loesche c_int(42).value

    def test_chararray(self):
        chararray = (c_char * 5)()
        mit self.assertRaises(TypeError):
            loesche chararray.value

    def test_struct(self):
        struct = X()
        mit self.assertRaises(TypeError):
            loesche struct.foo


wenn __name__ == "__main__":
    unittest.main()
