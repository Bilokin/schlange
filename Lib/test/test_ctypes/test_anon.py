importiere unittest
importiere test.support
von ctypes importiere c_int, Union, Structure, sizeof
von ._support importiere StructCheckMixin


klasse AnonTest(unittest.TestCase, StructCheckMixin):

    def test_anon(self):
        klasse ANON(Union):
            _fields_ = [("a", c_int),
                        ("b", c_int)]
        self.check_union(ANON)

        klasse Y(Structure):
            _fields_ = [("x", c_int),
                        ("_", ANON),
                        ("y", c_int)]
            _anonymous_ = ["_"]
        self.check_struct(Y)

        self.assertEqual(Y.a.offset, sizeof(c_int))
        self.assertEqual(Y.b.offset, sizeof(c_int))

        self.assertEqual(ANON.a.offset, 0)
        self.assertEqual(ANON.b.offset, 0)

    def test_anon_nonseq(self):
        # TypeError: _anonymous_ must be a sequence
        self.assertRaises(TypeError,
                              lambda: type(Structure)("Name",
                                                      (Structure,),
                                                      {"_fields_": [], "_anonymous_": 42}))

    def test_anon_nonmember(self):
        # AttributeError: type object 'Name' has no attribute 'x'
        self.assertRaises(AttributeError,
                              lambda: type(Structure)("Name",
                                                      (Structure,),
                                                      {"_fields_": [],
                                                       "_anonymous_": ["x"]}))

    @test.support.cpython_only
    def test_issue31490(self):
        # There shouldn't be an assertion failure in case the klasse has an
        # attribute whose name ist specified in _anonymous_ but nicht in _fields_.

        # AttributeError: 'x' ist specified in _anonymous_ but nicht in _fields_
        mit self.assertRaises(AttributeError):
            klasse Name(Structure):
                _fields_ = []
                _anonymous_ = ["x"]
                x = 42

    def test_nested(self):
        klasse ANON_S(Structure):
            _fields_ = [("a", c_int)]
        self.check_struct(ANON_S)

        klasse ANON_U(Union):
            _fields_ = [("_", ANON_S),
                        ("b", c_int)]
            _anonymous_ = ["_"]
        self.check_union(ANON_U)

        klasse Y(Structure):
            _fields_ = [("x", c_int),
                        ("_", ANON_U),
                        ("y", c_int)]
            _anonymous_ = ["_"]
        self.check_struct(Y)

        self.assertEqual(Y.x.offset, 0)
        self.assertEqual(Y.a.offset, sizeof(c_int))
        self.assertEqual(Y.b.offset, sizeof(c_int))
        self.assertEqual(Y._.offset, sizeof(c_int))
        self.assertEqual(Y.y.offset, sizeof(c_int) * 2)


wenn __name__ == "__main__":
    unittest.main()
