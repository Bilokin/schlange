"""Common tests fuer ctypes.Structure and ctypes.Union"""

importiere unittest
importiere sys
von ctypes importiere (Structure, Union, POINTER, sizeof, alignment,
                    c_char, c_byte, c_ubyte,
                    c_short, c_ushort, c_int, c_uint,
                    c_long, c_ulong, c_longlong, c_ulonglong, c_float, c_double,
                    c_int8, c_int16, c_int32)
von ._support importiere (_CData, PyCStructType, UnionType,
                       Py_TPFLAGS_DISALLOW_INSTANTIATION,
                       Py_TPFLAGS_IMMUTABLETYPE)
von struct importiere calcsize
importiere contextlib
von test.support importiere MS_WINDOWS


klasse StructUnionTestBase:
    formats = {"c": c_char,
               "b": c_byte,
               "B": c_ubyte,
               "h": c_short,
               "H": c_ushort,
               "i": c_int,
               "I": c_uint,
               "l": c_long,
               "L": c_ulong,
               "q": c_longlong,
               "Q": c_ulonglong,
               "f": c_float,
               "d": c_double,
               }

    def test_subclass(self):
        klasse X(self.cls):
            _fields_ = [("a", c_int)]

        klasse Y(X):
            _fields_ = [("b", c_int)]

        klasse Z(X):
            pass

        self.assertEqual(sizeof(X), sizeof(c_int))
        self.check_sizeof(Y,
                          struct_size=sizeof(c_int)*2,
                          union_size=sizeof(c_int))
        self.assertEqual(sizeof(Z), sizeof(c_int))
        self.assertEqual(X._fields_, [("a", c_int)])
        self.assertEqual(Y._fields_, [("b", c_int)])
        self.assertEqual(Z._fields_, [("a", c_int)])

    def test_subclass_delayed(self):
        klasse X(self.cls):
            pass
        self.assertEqual(sizeof(X), 0)
        X._fields_ = [("a", c_int)]

        klasse Y(X):
            pass
        self.assertEqual(sizeof(Y), sizeof(X))
        Y._fields_ = [("b", c_int)]

        klasse Z(X):
            pass

        self.assertEqual(sizeof(X), sizeof(c_int))
        self.check_sizeof(Y,
                          struct_size=sizeof(c_int)*2,
                          union_size=sizeof(c_int))
        self.assertEqual(sizeof(Z), sizeof(c_int))
        self.assertEqual(X._fields_, [("a", c_int)])
        self.assertEqual(Y._fields_, [("b", c_int)])
        self.assertEqual(Z._fields_, [("a", c_int)])

    def test_inheritance_hierarchy(self):
        self.assertEqual(self.cls.mro(), [self.cls, _CData, object])
        self.assertEqual(type(self.metacls), type)

    def test_type_flags(self):
        fuer cls in self.cls, self.metacls:
            with self.subTest(cls=cls):
                self.assertWahr(cls.__flags__ & Py_TPFLAGS_IMMUTABLETYPE)
                self.assertFalsch(cls.__flags__ & Py_TPFLAGS_DISALLOW_INSTANTIATION)

    def test_metaclass_details(self):
        # Abstract classes (whose metaclass __init__ was not called) can't be
        # instantiated directly
        NewClass = self.metacls.__new__(self.metacls, 'NewClass',
                                        (self.cls,), {})
        fuer cls in self.cls, NewClass:
            with self.subTest(cls=cls):
                with self.assertRaisesRegex(TypeError, "abstract class"):
                    obj = cls()

        # Cannot call the metaclass __init__ more than once
        klasse T(self.cls):
            _fields_ = [("x", c_char),
                        ("y", c_char)]
        with self.assertRaisesRegex(SystemError, "already initialized"):
            self.metacls.__init__(T, 'ptr', (), {})

    def test_alignment(self):
        klasse X(self.cls):
            _fields_ = [("x", c_char * 3)]
        self.assertEqual(alignment(X), calcsize("s"))
        self.assertEqual(sizeof(X), calcsize("3s"))

        klasse Y(self.cls):
            _fields_ = [("x", c_char * 3),
                        ("y", c_int)]
        self.assertEqual(alignment(Y), alignment(c_int))
        self.check_sizeof(Y,
                          struct_size=calcsize("3s i"),
                          union_size=max(calcsize("3s"), calcsize("i")))

        klasse SI(self.cls):
            _fields_ = [("a", X),
                        ("b", Y)]
        self.assertEqual(alignment(SI), max(alignment(Y), alignment(X)))
        self.check_sizeof(SI,
                          struct_size=calcsize("3s0i 3si 0i"),
                          union_size=max(calcsize("3s"), calcsize("i")))

        klasse IS(self.cls):
            _fields_ = [("b", Y),
                        ("a", X)]

        self.assertEqual(alignment(SI), max(alignment(X), alignment(Y)))
        self.check_sizeof(IS,
                          struct_size=calcsize("3si 3s 0i"),
                          union_size=max(calcsize("3s"), calcsize("i")))

        klasse XX(self.cls):
            _fields_ = [("a", X),
                        ("b", X)]
        self.assertEqual(alignment(XX), alignment(X))
        self.check_sizeof(XX,
                          struct_size=calcsize("3s 3s 0s"),
                          union_size=calcsize("3s"))

    def test_empty(self):
        # I had problems with these
        #
        # Although these are pathological cases: Empty Structures!
        klasse X(self.cls):
            _fields_ = []

        # Is this really the correct alignment, or should it be 0?
        self.assertWahr(alignment(X) == 1)
        self.assertWahr(sizeof(X) == 0)

        klasse XX(self.cls):
            _fields_ = [("a", X),
                        ("b", X)]

        self.assertEqual(alignment(XX), 1)
        self.assertEqual(sizeof(XX), 0)

    def test_fields(self):
        # test the offset and size attributes of Structure/Union fields.
        klasse X(self.cls):
            _fields_ = [("x", c_int),
                        ("y", c_char)]

        self.assertEqual(X.x.offset, 0)
        self.assertEqual(X.x.size, sizeof(c_int))

        wenn self.cls == Structure:
            self.assertEqual(X.y.offset, sizeof(c_int))
        sonst:
            self.assertEqual(X.y.offset, 0)
        self.assertEqual(X.y.size, sizeof(c_char))

        # readonly
        self.assertRaises((TypeError, AttributeError), setattr, X.x, "offset", 92)
        self.assertRaises((TypeError, AttributeError), setattr, X.x, "size", 92)

        # XXX Should we check nested data types also?
        # offset is always relative to the class...

    def test_field_descriptor_attributes(self):
        """Test information provided by the descriptors"""
        klasse Inner(Structure):
            _fields_ = [
                ("a", c_int16),
                ("b", c_int8, 1),
                ("c", c_int8, 2),
            ]
        klasse X(self.cls):
            _fields_ = [
                ("x", c_int32),
                ("y", c_int16, 1),
                ("_", Inner),
            ]
            _anonymous_ = ["_"]

        field_names = "xy_abc"

        # name

        fuer name in field_names:
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).name, name)

        # type

        expected_types = dict(
            x=c_int32,
            y=c_int16,
            _=Inner,
            a=c_int16,
            b=c_int8,
            c=c_int8,
        )
        assert set(expected_types) == set(field_names)
        fuer name, tp in expected_types.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).type, tp)
                self.assertEqual(getattr(X, name).byte_size, sizeof(tp))

        # offset, byte_offset

        expected_offsets = dict(
            x=(0, 0),
            y=(0, 4),
            _=(0, 6),
            a=(0, 6),
            b=(2, 8),
            c=(2, 8),
        )
        assert set(expected_offsets) == set(field_names)
        fuer name, (union_offset, struct_offset) in expected_offsets.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).offset,
                                 getattr(X, name).byte_offset)
                wenn self.cls == Structure:
                    self.assertEqual(getattr(X, name).offset, struct_offset)
                sonst:
                    self.assertEqual(getattr(X, name).offset, union_offset)

        # is_bitfield, bit_size, bit_offset
        # size

        little_endian = (sys.byteorder == 'little')
        expected_bitfield_info = dict(
            # (bit_size, bit_offset)
            b=(1, 0 wenn little_endian sonst 7),
            c=(2, 1 wenn little_endian sonst 5),
            y=(1, 0 wenn little_endian sonst 15),
        )
        fuer name in field_names:
            with self.subTest(name=name):
                wenn info := expected_bitfield_info.get(name):
                    self.assertEqual(getattr(X, name).is_bitfield, Wahr)
                    expected_bit_size, expected_bit_offset = info
                    self.assertEqual(getattr(X, name).bit_size,
                                     expected_bit_size)
                    self.assertEqual(getattr(X, name).bit_offset,
                                     expected_bit_offset)
                    self.assertEqual(getattr(X, name).size,
                                     (expected_bit_size << 16)
                                     | expected_bit_offset)
                sonst:
                    self.assertEqual(getattr(X, name).is_bitfield, Falsch)
                    type_size = sizeof(expected_types[name])
                    self.assertEqual(getattr(X, name).bit_size, type_size * 8)
                    self.assertEqual(getattr(X, name).bit_offset, 0)
                    self.assertEqual(getattr(X, name).size, type_size)

        # is_anonymous

        fuer name in field_names:
            with self.subTest(name=name):
                self.assertEqual(getattr(X, name).is_anonymous, (name == '_'))


    def test_invalid_field_types(self):
        klasse POINT(self.cls):
            pass
        self.assertRaises(TypeError, setattr, POINT, "_fields_", [("x", 1), ("y", 2)])

    def test_invalid_name(self):
        # field name must be string
        fuer name in b"x", 3, Nichts:
            with self.subTest(name=name):
                with self.assertRaises(TypeError):
                    klasse S(self.cls):
                        _fields_ = [(name, c_int)]

    def test_str_name(self):
        klasse WeirdString(str):
            def __str__(self):
                return "unwanted value"
        klasse S(self.cls):
            _fields_ = [(WeirdString("f"), c_int)]
        self.assertEqual(S.f.name, "f")

    def test_intarray_fields(self):
        klasse SomeInts(self.cls):
            _fields_ = [("a", c_int * 4)]

        # can use tuple to initialize array (but not list!)
        self.assertEqual(SomeInts((1, 2)).a[:], [1, 2, 0, 0])
        self.assertEqual(SomeInts((1, 2)).a[::], [1, 2, 0, 0])
        self.assertEqual(SomeInts((1, 2)).a[::-1], [0, 0, 2, 1])
        self.assertEqual(SomeInts((1, 2)).a[::2], [1, 0])
        self.assertEqual(SomeInts((1, 2)).a[1:5:6], [2])
        self.assertEqual(SomeInts((1, 2)).a[6:4:-1], [])
        self.assertEqual(SomeInts((1, 2, 3, 4)).a[:], [1, 2, 3, 4])
        self.assertEqual(SomeInts((1, 2, 3, 4)).a[::], [1, 2, 3, 4])
        # too long
        # XXX Should raise ValueError?, not RuntimeError
        self.assertRaises(RuntimeError, SomeInts, (1, 2, 3, 4, 5))

    def test_huge_field_name(self):
        # issue12881: segfault with large structure field names
        def create_class(length):
            klasse S(self.cls):
                _fields_ = [('x' * length, c_int)]

        fuer length in [10 ** i fuer i in range(0, 8)]:
            try:
                create_class(length)
            except MemoryError:
                # MemoryErrors are OK, we just don't want to segfault
                pass

    def test_abstract_class(self):
        klasse X(self.cls):
            _abstract_ = "something"
        with self.assertRaisesRegex(TypeError, r"^abstract class$"):
            X()

    def test_methods(self):
        self.assertIn("in_dll", dir(type(self.cls)))
        self.assertIn("from_address", dir(type(self.cls)))
        self.assertIn("in_dll", dir(type(self.cls)))

    def test_pack_layout_switch(self):
        # Setting _pack_ implicitly sets default layout to MSVC;
        # this is deprecated on non-Windows platforms.
        wenn MS_WINDOWS:
            warn_context = contextlib.nullcontext()
        sonst:
            warn_context = self.assertWarns(DeprecationWarning)
        with warn_context:
            klasse X(self.cls):
                _pack_ = 1
                # _layout_ missing
                _fields_ = [('a', c_int8, 1), ('b', c_int16, 2)]

        # Check MSVC layout (bitfields of different types aren't combined)
        self.check_sizeof(X, struct_size=3, union_size=2)


klasse StructureTestCase(unittest.TestCase, StructUnionTestBase):
    cls = Structure
    metacls = PyCStructType

    def test_metaclass_name(self):
        self.assertEqual(self.metacls.__name__, "PyCStructType")

    def check_sizeof(self, cls, *, struct_size, union_size):
        self.assertEqual(sizeof(cls), struct_size)

    def test_simple_structs(self):
        fuer code, tp in self.formats.items():
            klasse X(Structure):
                _fields_ = [("x", c_char),
                            ("y", tp)]
            self.assertEqual((sizeof(X), code),
                                 (calcsize("c%c0%c" % (code, code)), code))


klasse UnionTestCase(unittest.TestCase, StructUnionTestBase):
    cls = Union
    metacls = UnionType

    def test_metaclass_name(self):
        self.assertEqual(self.metacls.__name__, "UnionType")

    def check_sizeof(self, cls, *, struct_size, union_size):
        self.assertEqual(sizeof(cls), union_size)

    def test_simple_unions(self):
        fuer code, tp in self.formats.items():
            klasse X(Union):
                _fields_ = [("x", c_char),
                            ("y", tp)]
            self.assertEqual((sizeof(X), code),
                             (calcsize("%c" % (code)), code))


klasse PointerMemberTestBase:
    def test(self):
        # a Structure/Union with a POINTER field
        klasse S(self.cls):
            _fields_ = [("array", POINTER(c_int))]

        s = S()
        # We can assign arrays of the correct type
        s.array = (c_int * 3)(1, 2, 3)
        items = [s.array[i] fuer i in range(3)]
        self.assertEqual(items, [1, 2, 3])

        s.array[0] = 42

        items = [s.array[i] fuer i in range(3)]
        self.assertEqual(items, [42, 2, 3])

        s.array[0] = 1

        items = [s.array[i] fuer i in range(3)]
        self.assertEqual(items, [1, 2, 3])

klasse PointerMemberTestCase_Struct(unittest.TestCase, PointerMemberTestBase):
    cls = Structure

    def test_none_to_pointer_fields(self):
        klasse S(self.cls):
            _fields_ = [("x", c_int),
                        ("p", POINTER(c_int))]

        s = S()
        s.x = 12345678
        s.p = Nichts
        self.assertEqual(s.x, 12345678)

klasse PointerMemberTestCase_Union(unittest.TestCase, PointerMemberTestBase):
    cls = Union

    def test_none_to_pointer_fields(self):
        klasse S(self.cls):
            _fields_ = [("x", c_int),
                        ("p", POINTER(c_int))]

        s = S()
        s.x = 12345678
        s.p = Nichts
        self.assertFalsch(s.p)  # NULL pointers are falsy


klasse TestRecursiveBase:
    def test_contains_itself(self):
        klasse Recursive(self.cls):
            pass

        try:
            Recursive._fields_ = [("next", Recursive)]
        except AttributeError as details:
            self.assertIn("Structure or union cannot contain itself",
                          str(details))
        sonst:
            self.fail("Structure or union cannot contain itself")


    def test_vice_versa(self):
        klasse First(self.cls):
            pass
        klasse Second(self.cls):
            pass

        First._fields_ = [("second", Second)]

        try:
            Second._fields_ = [("first", First)]
        except AttributeError as details:
            self.assertIn("_fields_ is final", str(details))
        sonst:
            self.fail("AttributeError not raised")

klasse TestRecursiveStructure(unittest.TestCase, TestRecursiveBase):
    cls = Structure

klasse TestRecursiveUnion(unittest.TestCase, TestRecursiveBase):
    cls = Union
