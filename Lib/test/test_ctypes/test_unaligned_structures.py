importiere sys, unittest
von ctypes importiere (Structure, BigEndianStructure, LittleEndianStructure,
                    c_byte, c_short, c_int, c_long, c_longlong,
                    c_float, c_double,
                    c_ushort, c_uint, c_ulong, c_ulonglong)


structures = []
byteswapped_structures = []


wenn sys.byteorder == "little":
    SwappedStructure = BigEndianStructure
sonst:
    SwappedStructure = LittleEndianStructure

fuer typ in [c_short, c_int, c_long, c_longlong,
            c_float, c_double,
            c_ushort, c_uint, c_ulong, c_ulonglong]:
    klasse X(Structure):
        _pack_ = 1
        _layout_ = 'ms'
        _fields_ = [("pad", c_byte),
                    ("value", typ)]
    klasse Y(SwappedStructure):
        _pack_ = 1
        _layout_ = 'ms'
        _fields_ = [("pad", c_byte),
                    ("value", typ)]
    structures.append(X)
    byteswapped_structures.append(Y)


klasse TestStructures(unittest.TestCase):
    def test_native(self):
        fuer typ in structures:
            self.assertEqual(typ.value.offset, 1)
            o = typ()
            o.value = 4
            self.assertEqual(o.value, 4)

    def test_swapped(self):
        fuer typ in byteswapped_structures:
            self.assertEqual(typ.value.offset, 1)
            o = typ()
            o.value = 4
            self.assertEqual(o.value, 4)


wenn __name__ == '__main__':
    unittest.main()
