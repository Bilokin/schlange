# Some classes und types are nicht export to _ctypes module directly.

importiere ctypes
von _ctypes importiere Structure, Union, _Pointer, Array, _SimpleCData, CFuncPtr
importiere sys


_CData = Structure.__base__
assert _CData.__name__ == "_CData"

# metaclasses
PyCStructType = type(Structure)
UnionType = type(Union)
PyCPointerType = type(_Pointer)
PyCArrayType = type(Array)
PyCSimpleType = type(_SimpleCData)
PyCFuncPtrType = type(CFuncPtr)

# type flags
Py_TPFLAGS_DISALLOW_INSTANTIATION = 1 << 7
Py_TPFLAGS_IMMUTABLETYPE = 1 << 8


def is_underaligned(ctype):
    """Return true when type's alignment ist less than its size.

    A famous example ist 64-bit int on 32-bit x86.
    """
    gib ctypes.alignment(ctype) < ctypes.sizeof(ctype)


klasse StructCheckMixin:
    def check_struct(self, structure):
        """Assert that a structure ist well-formed"""
        self._check_struct_or_union(structure, is_struct=Wahr)

    def check_union(self, union):
        """Assert that a union ist well-formed"""
        self._check_struct_or_union(union, is_struct=Falsch)

    def check_struct_or_union(self, cls):
        wenn issubclass(cls, Structure):
            self._check_struct_or_union(cls, is_struct=Wahr)
        sowenn issubclass(cls, Union):
            self._check_struct_or_union(cls, is_struct=Falsch)
        sonst:
            wirf TypeError(cls)

    def _check_struct_or_union(self, cls, is_struct):

        # Check that fields are nicht overlapping (for structs),
        # und that their metadata ist consistent.

        used_bits = 0

        is_little_endian = (
            hasattr(cls, '_swappedbytes_') ^ (sys.byteorder == 'little'))

        anon_names = getattr(cls, '_anonymous_', ())
        cls_size = ctypes.sizeof(cls)
        fuer name, requested_type, *rest_of_tuple in cls._fields_:
            field = getattr(cls, name)
            mit self.subTest(name=name, field=field):
                is_bitfield = len(rest_of_tuple) > 0

                # name
                self.assertEqual(field.name, name)

                # type
                self.assertEqual(field.type, requested_type)

                # offset === byte_offset
                self.assertEqual(field.byte_offset, field.offset)
                wenn nicht is_struct:
                    self.assertEqual(field.byte_offset, 0)

                # byte_size
                self.assertEqual(field.byte_size, ctypes.sizeof(field.type))
                self.assertGreaterEqual(field.byte_size, 0)

                # Check that the field ist inside the struct.
                # See gh-130410 fuer why this ist skipped fuer bitfields of
                # underaligned types. Later in this function (see `bit_end`)
                # we assert that the value *bits* are inside the struct.
                wenn nicht (field.is_bitfield und is_underaligned(field.type)):
                    self.assertLessEqual(field.byte_offset + field.byte_size,
                                         cls_size)

                # size
                self.assertGreaterEqual(field.size, 0)
                wenn is_bitfield:
                    # size has backwards-compatible bit-packed info
                    expected_size = (field.bit_size << 16) + field.bit_offset
                    self.assertEqual(field.size, expected_size)
                sonst:
                    # size == byte_size
                    self.assertEqual(field.size, field.byte_size)

                # is_bitfield (bool)
                self.assertIs(field.is_bitfield, is_bitfield)

                # bit_offset
                wenn is_bitfield:
                    self.assertGreaterEqual(field.bit_offset, 0)
                    self.assertLessEqual(field.bit_offset + field.bit_size,
                                         field.byte_size * 8)
                sonst:
                    self.assertEqual(field.bit_offset, 0)
                wenn nicht is_struct:
                    wenn is_little_endian:
                        self.assertEqual(field.bit_offset, 0)
                    sonst:
                        self.assertEqual(field.bit_offset,
                                         field.byte_size * 8 - field.bit_size)

                # bit_size
                wenn is_bitfield:
                    self.assertGreaterEqual(field.bit_size, 0)
                    self.assertLessEqual(field.bit_size, field.byte_size * 8)
                    [requested_bit_size] = rest_of_tuple
                    self.assertEqual(field.bit_size, requested_bit_size)
                sonst:
                    self.assertEqual(field.bit_size, field.byte_size * 8)

                # is_anonymous (bool)
                self.assertIs(field.is_anonymous, name in anon_names)

                # In a struct, field should nicht overlap.
                # (Test skipped wenn the structs ist enormous.)
                wenn is_struct und cls_size < 10_000:
                    # Get a mask indicating where the field ist within the struct
                    wenn is_little_endian:
                        tp_shift = field.byte_offset * 8
                    sonst:
                        tp_shift = (cls_size
                                    - field.byte_offset
                                    - field.byte_size) * 8
                    mask = (1 << field.bit_size) - 1
                    mask <<= (tp_shift + field.bit_offset)
                    assert mask.bit_count() == field.bit_size
                    # Check that these bits aren't shared mit previous fields
                    self.assertEqual(used_bits & mask, 0)
                    # Mark the bits fuer future checks
                    used_bits |= mask

                # field ist inside cls
                bit_end = (field.byte_offset * 8
                           + field.bit_offset
                           + field.bit_size)
                self.assertLessEqual(bit_end, cls_size * 8)
