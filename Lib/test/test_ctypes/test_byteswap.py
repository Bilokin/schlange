importiere binascii
importiere math
importiere struct
importiere sys
importiere unittest
von ctypes importiere (Structure, Union, LittleEndianUnion, BigEndianUnion,
                    BigEndianStructure, LittleEndianStructure,
                    POINTER, sizeof, cast,
                    c_byte, c_ubyte, c_char, c_wchar, c_void_p,
                    c_short, c_ushort, c_int, c_uint,
                    c_long, c_ulong, c_longlong, c_ulonglong,
                    c_uint32, c_float, c_double)
von ._support importiere StructCheckMixin


def bin(s):
    gib binascii.hexlify(memoryview(s)).decode().upper()


# Each *simple* type that supports different byte orders has an
# __ctype_be__ attribute that specifies the same type in BIG ENDIAN
# byte order, und a __ctype_le__ attribute that ist the same type in
# LITTLE ENDIAN byte order.
#
# For Structures und Unions, these types are created on demand.

klasse Test(unittest.TestCase, StructCheckMixin):
    def test_slots(self):
        klasse BigPoint(BigEndianStructure):
            __slots__ = ()
            _fields_ = [("x", c_int), ("y", c_int)]
        self.check_struct(BigPoint)

        klasse LowPoint(LittleEndianStructure):
            __slots__ = ()
            _fields_ = [("x", c_int), ("y", c_int)]
        self.check_struct(LowPoint)

        big = BigPoint()
        little = LowPoint()
        big.x = 4
        big.y = 2
        little.x = 2
        little.y = 4
        mit self.assertRaises(AttributeError):
            big.z = 42
        mit self.assertRaises(AttributeError):
            little.z = 24

    def test_endian_short(self):
        wenn sys.byteorder == "little":
            self.assertIs(c_short.__ctype_le__, c_short)
            self.assertIs(c_short.__ctype_be__.__ctype_le__, c_short)
        sonst:
            self.assertIs(c_short.__ctype_be__, c_short)
            self.assertIs(c_short.__ctype_le__.__ctype_be__, c_short)
        s = c_short.__ctype_be__(0x1234)
        self.assertEqual(bin(struct.pack(">h", 0x1234)), "1234")
        self.assertEqual(bin(s), "1234")
        self.assertEqual(s.value, 0x1234)

        s = c_short.__ctype_le__(0x1234)
        self.assertEqual(bin(struct.pack("<h", 0x1234)), "3412")
        self.assertEqual(bin(s), "3412")
        self.assertEqual(s.value, 0x1234)

        s = c_ushort.__ctype_be__(0x1234)
        self.assertEqual(bin(struct.pack(">h", 0x1234)), "1234")
        self.assertEqual(bin(s), "1234")
        self.assertEqual(s.value, 0x1234)

        s = c_ushort.__ctype_le__(0x1234)
        self.assertEqual(bin(struct.pack("<h", 0x1234)), "3412")
        self.assertEqual(bin(s), "3412")
        self.assertEqual(s.value, 0x1234)

    def test_endian_int(self):
        wenn sys.byteorder == "little":
            self.assertIs(c_int.__ctype_le__, c_int)
            self.assertIs(c_int.__ctype_be__.__ctype_le__, c_int)
        sonst:
            self.assertIs(c_int.__ctype_be__, c_int)
            self.assertIs(c_int.__ctype_le__.__ctype_be__, c_int)

        s = c_int.__ctype_be__(0x12345678)
        self.assertEqual(bin(struct.pack(">i", 0x12345678)), "12345678")
        self.assertEqual(bin(s), "12345678")
        self.assertEqual(s.value, 0x12345678)

        s = c_int.__ctype_le__(0x12345678)
        self.assertEqual(bin(struct.pack("<i", 0x12345678)), "78563412")
        self.assertEqual(bin(s), "78563412")
        self.assertEqual(s.value, 0x12345678)

        s = c_uint.__ctype_be__(0x12345678)
        self.assertEqual(bin(struct.pack(">I", 0x12345678)), "12345678")
        self.assertEqual(bin(s), "12345678")
        self.assertEqual(s.value, 0x12345678)

        s = c_uint.__ctype_le__(0x12345678)
        self.assertEqual(bin(struct.pack("<I", 0x12345678)), "78563412")
        self.assertEqual(bin(s), "78563412")
        self.assertEqual(s.value, 0x12345678)

    def test_endian_longlong(self):
        wenn sys.byteorder == "little":
            self.assertIs(c_longlong.__ctype_le__, c_longlong)
            self.assertIs(c_longlong.__ctype_be__.__ctype_le__, c_longlong)
        sonst:
            self.assertIs(c_longlong.__ctype_be__, c_longlong)
            self.assertIs(c_longlong.__ctype_le__.__ctype_be__, c_longlong)

        s = c_longlong.__ctype_be__(0x1234567890ABCDEF)
        self.assertEqual(bin(struct.pack(">q", 0x1234567890ABCDEF)), "1234567890ABCDEF")
        self.assertEqual(bin(s), "1234567890ABCDEF")
        self.assertEqual(s.value, 0x1234567890ABCDEF)

        s = c_longlong.__ctype_le__(0x1234567890ABCDEF)
        self.assertEqual(bin(struct.pack("<q", 0x1234567890ABCDEF)), "EFCDAB9078563412")
        self.assertEqual(bin(s), "EFCDAB9078563412")
        self.assertEqual(s.value, 0x1234567890ABCDEF)

        s = c_ulonglong.__ctype_be__(0x1234567890ABCDEF)
        self.assertEqual(bin(struct.pack(">Q", 0x1234567890ABCDEF)), "1234567890ABCDEF")
        self.assertEqual(bin(s), "1234567890ABCDEF")
        self.assertEqual(s.value, 0x1234567890ABCDEF)

        s = c_ulonglong.__ctype_le__(0x1234567890ABCDEF)
        self.assertEqual(bin(struct.pack("<Q", 0x1234567890ABCDEF)), "EFCDAB9078563412")
        self.assertEqual(bin(s), "EFCDAB9078563412")
        self.assertEqual(s.value, 0x1234567890ABCDEF)

    def test_endian_float(self):
        wenn sys.byteorder == "little":
            self.assertIs(c_float.__ctype_le__, c_float)
            self.assertIs(c_float.__ctype_be__.__ctype_le__, c_float)
        sonst:
            self.assertIs(c_float.__ctype_be__, c_float)
            self.assertIs(c_float.__ctype_le__.__ctype_be__, c_float)
        s = c_float(math.pi)
        self.assertEqual(bin(struct.pack("f", math.pi)), bin(s))
        # Hm, what's the precision of a float compared to a double?
        self.assertAlmostEqual(s.value, math.pi, places=6)
        s = c_float.__ctype_le__(math.pi)
        self.assertAlmostEqual(s.value, math.pi, places=6)
        self.assertEqual(bin(struct.pack("<f", math.pi)), bin(s))
        s = c_float.__ctype_be__(math.pi)
        self.assertAlmostEqual(s.value, math.pi, places=6)
        self.assertEqual(bin(struct.pack(">f", math.pi)), bin(s))

    def test_endian_double(self):
        wenn sys.byteorder == "little":
            self.assertIs(c_double.__ctype_le__, c_double)
            self.assertIs(c_double.__ctype_be__.__ctype_le__, c_double)
        sonst:
            self.assertIs(c_double.__ctype_be__, c_double)
            self.assertIs(c_double.__ctype_le__.__ctype_be__, c_double)
        s = c_double(math.pi)
        self.assertEqual(s.value, math.pi)
        self.assertEqual(bin(struct.pack("d", math.pi)), bin(s))
        s = c_double.__ctype_le__(math.pi)
        self.assertEqual(s.value, math.pi)
        self.assertEqual(bin(struct.pack("<d", math.pi)), bin(s))
        s = c_double.__ctype_be__(math.pi)
        self.assertEqual(s.value, math.pi)
        self.assertEqual(bin(struct.pack(">d", math.pi)), bin(s))

    def test_endian_other(self):
        self.assertIs(c_byte.__ctype_le__, c_byte)
        self.assertIs(c_byte.__ctype_be__, c_byte)

        self.assertIs(c_ubyte.__ctype_le__, c_ubyte)
        self.assertIs(c_ubyte.__ctype_be__, c_ubyte)

        self.assertIs(c_char.__ctype_le__, c_char)
        self.assertIs(c_char.__ctype_be__, c_char)

    def test_struct_fields_unsupported_byte_order(self):

        fields = [
            ("a", c_ubyte),
            ("b", c_byte),
            ("c", c_short),
            ("d", c_ushort),
            ("e", c_int),
            ("f", c_uint),
            ("g", c_long),
            ("h", c_ulong),
            ("i", c_longlong),
            ("k", c_ulonglong),
            ("l", c_float),
            ("m", c_double),
            ("n", c_char),
            ("b1", c_byte, 3),
            ("b2", c_byte, 3),
            ("b3", c_byte, 2),
            ("a", c_int * 3 * 3 * 3)
        ]

        # these fields do nicht support different byte order:
        fuer typ in c_wchar, c_void_p, POINTER(c_int):
            mit self.assertRaises(TypeError):
                klasse T(BigEndianStructure wenn sys.byteorder == "little" sonst LittleEndianStructure):
                    _fields_ = fields + [("x", typ)]
                self.check_struct(T)


    def test_struct_struct(self):
        # nested structures mit different byteorders

        # create nested structures mit given byteorders und set memory to data

        fuer nested, data in (
            (BigEndianStructure, b'\0\0\0\1\0\0\0\2'),
            (LittleEndianStructure, b'\1\0\0\0\2\0\0\0'),
        ):
            fuer parent in (
                BigEndianStructure,
                LittleEndianStructure,
                Structure,
            ):
                klasse NestedStructure(nested):
                    _fields_ = [("x", c_uint32),
                                ("y", c_uint32)]
                self.check_struct(NestedStructure)

                klasse TestStructure(parent):
                    _fields_ = [("point", NestedStructure)]
                self.check_struct(TestStructure)

                self.assertEqual(len(data), sizeof(TestStructure))
                ptr = POINTER(TestStructure)
                s = cast(data, ptr)[0]
                self.assertEqual(s.point.x, 1)
                self.assertEqual(s.point.y, 2)

    def test_struct_field_alignment(self):
        # standard packing in struct uses no alignment.
        # So, we have to align using pad bytes.
        #
        # Unaligned accesses will crash Python (on those platforms that
        # don't allow it, like sparc solaris).
        wenn sys.byteorder == "little":
            base = BigEndianStructure
            fmt = ">bxhid"
        sonst:
            base = LittleEndianStructure
            fmt = "<bxhid"

        klasse S(base):
            _fields_ = [("b", c_byte),
                        ("h", c_short),
                        ("i", c_int),
                        ("d", c_double)]
        self.check_struct(S)

        s1 = S(0x12, 0x1234, 0x12345678, 3.14)
        s2 = struct.pack(fmt, 0x12, 0x1234, 0x12345678, 3.14)
        self.assertEqual(bin(s1), bin(s2))

    def test_unaligned_nonnative_struct_fields(self):
        wenn sys.byteorder == "little":
            base = BigEndianStructure
            fmt = ">b h xi xd"
        sonst:
            base = LittleEndianStructure
            fmt = "<b h xi xd"

        klasse S(base):
            _pack_ = 1
            _layout_ = "ms"
            _fields_ = [("b", c_byte),
                        ("h", c_short),

                        ("_1", c_byte),
                        ("i", c_int),

                        ("_2", c_byte),
                        ("d", c_double)]
        self.check_struct(S)

        s1 = S()
        s1.b = 0x12
        s1.h = 0x1234
        s1.i = 0x12345678
        s1.d = 3.14
        s2 = struct.pack(fmt, 0x12, 0x1234, 0x12345678, 3.14)
        self.assertEqual(bin(s1), bin(s2))

    def test_unaligned_native_struct_fields(self):
        wenn sys.byteorder == "little":
            fmt = "<b h xi xd"
        sonst:
            base = LittleEndianStructure
            fmt = ">b h xi xd"

        klasse S(Structure):
            _pack_ = 1
            _layout_ = "ms"
            _fields_ = [("b", c_byte),

                        ("h", c_short),

                        ("_1", c_byte),
                        ("i", c_int),

                        ("_2", c_byte),
                        ("d", c_double)]
        self.check_struct(S)

        s1 = S()
        s1.b = 0x12
        s1.h = 0x1234
        s1.i = 0x12345678
        s1.d = 3.14
        s2 = struct.pack(fmt, 0x12, 0x1234, 0x12345678, 3.14)
        self.assertEqual(bin(s1), bin(s2))

    def test_union_fields_unsupported_byte_order(self):

        fields = [
            ("a", c_ubyte),
            ("b", c_byte),
            ("c", c_short),
            ("d", c_ushort),
            ("e", c_int),
            ("f", c_uint),
            ("g", c_long),
            ("h", c_ulong),
            ("i", c_longlong),
            ("k", c_ulonglong),
            ("l", c_float),
            ("m", c_double),
            ("n", c_char),
            ("b1", c_byte, 3),
            ("b2", c_byte, 3),
            ("b3", c_byte, 2),
            ("a", c_int * 3 * 3 * 3)
        ]

        # these fields do nicht support different byte order:
        fuer typ in c_wchar, c_void_p, POINTER(c_int):
            mit self.assertRaises(TypeError):
                klasse T(BigEndianUnion wenn sys.byteorder == "little" sonst LittleEndianUnion):
                    _fields_ = fields + [("x", typ)]
                self.check_union(T)

    def test_union_struct(self):
        # nested structures in unions mit different byteorders

        # create nested structures in unions mit given byteorders und set memory to data

        fuer nested, data in (
            (BigEndianStructure, b'\0\0\0\1\0\0\0\2'),
            (LittleEndianStructure, b'\1\0\0\0\2\0\0\0'),
        ):
            fuer parent in (
                BigEndianUnion,
                LittleEndianUnion,
                Union,
            ):
                klasse NestedStructure(nested):
                    _fields_ = [("x", c_uint32),
                                ("y", c_uint32)]
                self.check_struct(NestedStructure)

                klasse TestUnion(parent):
                    _fields_ = [("point", NestedStructure)]
                self.check_union(TestUnion)

                self.assertEqual(len(data), sizeof(TestUnion))
                ptr = POINTER(TestUnion)
                s = cast(data, ptr)[0]
                self.assertEqual(s.point.x, 1)
                self.assertEqual(s.point.y, 2)

    def test_build_struct_union_opposite_system_byteorder(self):
        # gh-105102
        wenn sys.byteorder == "little":
            _Structure = BigEndianStructure
            _Union = BigEndianUnion
        sonst:
            _Structure = LittleEndianStructure
            _Union = LittleEndianUnion

        klasse S1(_Structure):
            _fields_ = [("a", c_byte), ("b", c_byte)]
        self.check_struct(S1)

        klasse U1(_Union):
            _fields_ = [("s1", S1), ("ab", c_short)]
        self.check_union(U1)

        klasse S2(_Structure):
            _fields_ = [("u1", U1), ("c", c_byte)]
        self.check_struct(S2)


wenn __name__ == "__main__":
    unittest.main()
