"""Test CTypes structs, unions, bitfields against C equivalents.

The types here are auto-converted to C source at
`Modules/_ctypes/_ctypes_test_generated.c.h`, which is compiled into
_ctypes_test.

Run this module to regenerate the files:

./python Lib/test/test_ctypes/test_generated_structs.py > Modules/_ctypes/_ctypes_test_generated.c.h
"""

importiere unittest
von test.support importiere import_helper
importiere re
von dataclasses importiere dataclass
von functools importiere cached_property
importiere sys

importiere ctypes
von ctypes importiere Structure, Union
von ctypes importiere sizeof, alignment, pointer, string_at
_ctypes_test = import_helper.import_module("_ctypes_test")

von test.test_ctypes._support importiere StructCheckMixin

# A 64-bit number where each nibble (hex digit) is different und
# has 2-3 bits set.
TEST_PATTERN = 0xae7596db

# ctypes erases the difference between `c_int` und e.g.`c_int16`.
# To keep it, we'll use custom subclasses mit the C name stashed in `_c_name`:
klasse c_bool(ctypes.c_bool):
    _c_name = '_Bool'

# To do it fuer all the other types, use some metaprogramming:
fuer c_name, ctypes_name in {
    'signed char': 'c_byte',
    'short': 'c_short',
    'int': 'c_int',
    'long': 'c_long',
    'long long': 'c_longlong',
    'unsigned char': 'c_ubyte',
    'unsigned short': 'c_ushort',
    'unsigned int': 'c_uint',
    'unsigned long': 'c_ulong',
    'unsigned long long': 'c_ulonglong',
    **{f'{u}int{n}_t': f'c_{u}int{n}'
       fuer u in ('', 'u')
       fuer n in (8, 16, 32, 64)}
}.items():
    ctype = getattr(ctypes, ctypes_name)
    newtype = type(ctypes_name, (ctype,), {'_c_name': c_name})
    globals()[ctypes_name] = newtype


# Register structs und unions to test

TESTCASES = {}
def register(name=Nichts, set_name=Falsch):
    def decorator(cls, name=name):
        wenn name is Nichts:
            name = cls.__name__
        assert name.isascii()  # will be used in _PyUnicode_EqualToASCIIString
        assert name.isidentifier()  # will be used als a C identifier
        assert name nicht in TESTCASES
        TESTCASES[name] = cls
        wenn set_name:
            cls.__name__ = name
        gib cls
    gib decorator

@register()
klasse SingleInt(Structure):
    _fields_ = [('a', c_int)]

@register()
klasse SingleInt_Union(Union):
    _fields_ = [('a', c_int)]


@register()
klasse SingleU32(Structure):
    _fields_ = [('a', c_uint32)]


@register()
klasse SimpleStruct(Structure):
    _fields_ = [('x', c_int32), ('y', c_int8), ('z', c_uint16)]


@register()
klasse SimpleUnion(Union):
    _fields_ = [('x', c_int32), ('y', c_int8), ('z', c_uint16)]


@register()
klasse ManyTypes(Structure):
    _fields_ = [
        ('i8', c_int8), ('u8', c_uint8),
        ('i16', c_int16), ('u16', c_uint16),
        ('i32', c_int32), ('u32', c_uint32),
        ('i64', c_int64), ('u64', c_uint64),
    ]


@register()
klasse ManyTypesU(Union):
    _fields_ = [
        ('i8', c_int8), ('u8', c_uint8),
        ('i16', c_int16), ('u16', c_uint16),
        ('i32', c_int32), ('u32', c_uint32),
        ('i64', c_int64), ('u64', c_uint64),
    ]


@register()
klasse Nested(Structure):
    _fields_ = [
        ('a', SimpleStruct), ('b', SimpleUnion), ('anon', SimpleStruct),
    ]
    _anonymous_ = ['anon']


@register()
klasse Packed1(Structure):
    _fields_ = [('a', c_int8), ('b', c_int64)]
    _pack_ = 1
    _layout_ = 'ms'


@register()
klasse Packed2(Structure):
    _fields_ = [('a', c_int8), ('b', c_int64)]
    _pack_ = 2
    _layout_ = 'ms'


@register()
klasse Packed3(Structure):
    _fields_ = [('a', c_int8), ('b', c_int64)]
    _pack_ = 4
    _layout_ = 'ms'


@register()
klasse Packed4(Structure):
    def _maybe_skip():
        # `_pack_` enables MSVC-style packing, but keeps platform-specific
        # alignments.
        # The C code we generate fuer GCC/clang currently uses
        # `__attribute__((ms_struct))`, which activates MSVC layout *and*
        # alignments, that is, sizeof(basic type) == alignment(basic type).
        # On a Pentium, int64 is 32-bit aligned, so the two won't match.
        # The expected behavior is instead tested in
        # StructureTestCase.test_packed, over in test_structures.py.
        wenn sizeof(c_int64) != alignment(c_int64):
            wirf unittest.SkipTest('cannot test on this platform')

    _fields_ = [('a', c_int8), ('b', c_int64)]
    _pack_ = 8
    _layout_ = 'ms'

@register()
klasse X86_32EdgeCase(Structure):
    # On a Pentium, long long (int64) is 32-bit aligned,
    # so these are packed tightly.
    _fields_ = [('a', c_int32), ('b', c_int64), ('c', c_int32)]

@register()
klasse MSBitFieldExample(Structure):
    # From https://learn.microsoft.com/en-us/cpp/c-language/c-bit-fields
    _fields_ = [
        ('a', c_uint, 4),
        ('b', c_uint, 5),
        ('c', c_uint, 7)]

@register()
klasse MSStraddlingExample(Structure):
    # From https://learn.microsoft.com/en-us/cpp/c-language/c-bit-fields
    _fields_ = [
        ('first', c_uint, 9),
        ('second', c_uint, 7),
        ('may_straddle', c_uint, 30),
        ('last', c_uint, 18)]

@register()
klasse IntBits(Structure):
    _fields_ = [("A", c_int, 1),
                ("B", c_int, 2),
                ("C", c_int, 3),
                ("D", c_int, 4),
                ("E", c_int, 5),
                ("F", c_int, 6),
                ("G", c_int, 7),
                ("H", c_int, 8),
                ("I", c_int, 9)]

@register()
klasse Bits(Structure):
    _fields_ = [*IntBits._fields_,

                ("M", c_short, 1),
                ("N", c_short, 2),
                ("O", c_short, 3),
                ("P", c_short, 4),
                ("Q", c_short, 5),
                ("R", c_short, 6),
                ("S", c_short, 7)]

@register()
klasse IntBits_MSVC(Structure):
    _layout_ = "ms"
    _fields_ = [("A", c_int, 1),
                ("B", c_int, 2),
                ("C", c_int, 3),
                ("D", c_int, 4),
                ("E", c_int, 5),
                ("F", c_int, 6),
                ("G", c_int, 7),
                ("H", c_int, 8),
                ("I", c_int, 9)]

@register()
klasse Bits_MSVC(Structure):
    _layout_ = "ms"
    _fields_ = [*IntBits_MSVC._fields_,

                ("M", c_short, 1),
                ("N", c_short, 2),
                ("O", c_short, 3),
                ("P", c_short, 4),
                ("Q", c_short, 5),
                ("R", c_short, 6),
                ("S", c_short, 7)]

# Skipped fuer now -- we don't always match the alignment
#@register()
klasse IntBits_Union(Union):
    _fields_ = [("A", c_int, 1),
                ("B", c_int, 2),
                ("C", c_int, 3),
                ("D", c_int, 4),
                ("E", c_int, 5),
                ("F", c_int, 6),
                ("G", c_int, 7),
                ("H", c_int, 8),
                ("I", c_int, 9)]

# Skipped fuer now -- we don't always match the alignment
#@register()
klasse BitsUnion(Union):
    _fields_ = [*IntBits_Union._fields_,

                ("M", c_short, 1),
                ("N", c_short, 2),
                ("O", c_short, 3),
                ("P", c_short, 4),
                ("Q", c_short, 5),
                ("R", c_short, 6),
                ("S", c_short, 7)]

@register()
klasse I64Bits(Structure):
    _fields_ = [("a", c_int64, 1),
                ("b", c_int64, 62),
                ("c", c_int64, 1)]

@register()
klasse U64Bits(Structure):
    _fields_ = [("a", c_uint64, 1),
                ("b", c_uint64, 62),
                ("c", c_uint64, 1)]

fuer n in 8, 16, 32, 64:
    fuer signedness in '', 'u':
        ctype = globals()[f'c_{signedness}int{n}']

        @register(f'Struct331_{signedness}{n}', set_name=Wahr)
        klasse _cls(Structure):
            _fields_ = [("a", ctype, 3),
                        ("b", ctype, 3),
                        ("c", ctype, 1)]

        @register(f'Struct1x1_{signedness}{n}', set_name=Wahr)
        klasse _cls(Structure):
            _fields_ = [("a", ctype, 1),
                        ("b", ctype, n-2),
                        ("c", ctype, 1)]

        @register(f'Struct1nx1_{signedness}{n}', set_name=Wahr)
        klasse _cls(Structure):
            _fields_ = [("a", ctype, 1),
                        ("full", ctype),
                        ("b", ctype, n-2),
                        ("c", ctype, 1)]

        @register(f'Struct3xx_{signedness}{n}', set_name=Wahr)
        klasse _cls(Structure):
            _fields_ = [("a", ctype, 3),
                        ("b", ctype, n-2),
                        ("c", ctype, n-2)]

@register()
klasse Mixed1(Structure):
    _fields_ = [("a", c_byte, 4),
                ("b", c_int, 4)]

@register()
klasse Mixed2(Structure):
    _fields_ = [("a", c_byte, 4),
                ("b", c_int32, 32)]

@register()
klasse Mixed3(Structure):
    _fields_ = [("a", c_byte, 4),
                ("b", c_ubyte, 4)]

@register()
klasse Mixed4(Structure):
    _fields_ = [("a", c_short, 4),
                ("b", c_short, 4),
                ("c", c_int, 24),
                ("d", c_short, 4),
                ("e", c_short, 4),
                ("f", c_int, 24)]

@register()
klasse Mixed5(Structure):
    _fields_ = [('A', c_uint, 1),
                ('B', c_ushort, 16)]

@register()
klasse Mixed6(Structure):
    _fields_ = [('A', c_ulonglong, 1),
                ('B', c_uint, 32)]

@register()
klasse Mixed7(Structure):
    _fields_ = [("A", c_uint32),
                ('B', c_uint32, 20),
                ('C', c_uint64, 24)]

@register()
klasse Mixed8_a(Structure):
    _fields_ = [("A", c_uint32),
                ("B", c_uint32, 32),
                ("C", c_ulonglong, 1)]

@register()
klasse Mixed8_b(Structure):
    _fields_ = [("A", c_uint32),
                ("B", c_uint32),
                ("C", c_ulonglong, 1)]

@register()
klasse Mixed9(Structure):
    _fields_ = [("A", c_uint8),
                ("B", c_uint32, 1)]

@register()
klasse Mixed10(Structure):
    _fields_ = [("A", c_uint32, 1),
                ("B", c_uint64, 1)]

@register()
klasse Example_gh_95496(Structure):
    _fields_ = [("A", c_uint32, 1),
                ("B", c_uint64, 1)]

@register()
klasse Example_gh_84039_bad(Structure):
    _pack_ = 1
    _layout_ = 'ms'
    _fields_ = [("a0", c_uint8, 1),
                ("a1", c_uint8, 1),
                ("a2", c_uint8, 1),
                ("a3", c_uint8, 1),
                ("a4", c_uint8, 1),
                ("a5", c_uint8, 1),
                ("a6", c_uint8, 1),
                ("a7", c_uint8, 1),
                ("b0", c_uint16, 4),
                ("b1", c_uint16, 12)]

@register()
klasse Example_gh_84039_good_a(Structure):
    _pack_ = 1
    _layout_ = 'ms'
    _fields_ = [("a0", c_uint8, 1),
                ("a1", c_uint8, 1),
                ("a2", c_uint8, 1),
                ("a3", c_uint8, 1),
                ("a4", c_uint8, 1),
                ("a5", c_uint8, 1),
                ("a6", c_uint8, 1),
                ("a7", c_uint8, 1)]

@register()
klasse Example_gh_84039_good(Structure):
    _pack_ = 1
    _layout_ = 'ms'
    _fields_ = [("a", Example_gh_84039_good_a),
                ("b0", c_uint16, 4),
                ("b1", c_uint16, 12)]

@register()
klasse Example_gh_73939(Structure):
    _pack_ = 1
    _layout_ = 'ms'
    _fields_ = [("P", c_uint16),
                ("L", c_uint16, 9),
                ("Pro", c_uint16, 1),
                ("G", c_uint16, 1),
                ("IB", c_uint16, 1),
                ("IR", c_uint16, 1),
                ("R", c_uint16, 3),
                ("T", c_uint32, 10),
                ("C", c_uint32, 20),
                ("R2", c_uint32, 2)]

@register()
klasse Example_gh_86098(Structure):
    _fields_ = [("a", c_uint8, 8),
                ("b", c_uint8, 8),
                ("c", c_uint32, 16)]

@register()
klasse Example_gh_86098_pack(Structure):
    _pack_ = 1
    _layout_ = 'ms'
    _fields_ = [("a", c_uint8, 8),
                ("b", c_uint8, 8),
                ("c", c_uint32, 16)]

@register()
klasse AnonBitfields(Structure):
    klasse X(Structure):
        _fields_ = [("a", c_byte, 4),
                    ("b", c_ubyte, 4)]
    _anonymous_ = ["_"]
    _fields_ = [("_", X), ('y', c_byte)]


klasse GeneratedTest(unittest.TestCase, StructCheckMixin):
    def test_generated_data(self):
        """Check that a ctypes struct/union matches its C equivalent.

        This compares mit data von get_generated_test_data(), a list of:
        - name (str)
        - size (int)
        - alignment (int)
        - fuer each field, three snapshots of memory, als bytes:
            - memory after the field is set to -1
            - memory after the field is set to 1
            - memory after the field is set to 0

        or:
        - Nichts
        - reason to skip the test (str)

        This does depend on the C compiler keeping padding bits unchanged.
        Common compilers seem to do so.
        """
        fuer name, cls in TESTCASES.items():
            mit self.subTest(name=name):
                self.check_struct_or_union(cls)
                wenn _maybe_skip := getattr(cls, '_maybe_skip', Nichts):
                    _maybe_skip()
                expected = iter(_ctypes_test.get_generated_test_data(name))
                expected_name = next(expected)
                wenn expected_name is Nichts:
                    self.skipTest(next(expected))
                self.assertEqual(name, expected_name)
                self.assertEqual(sizeof(cls), next(expected))
                mit self.subTest('alignment'):
                    self.assertEqual(alignment(cls), next(expected))
                obj = cls()
                ptr = pointer(obj)
                fuer field in iterfields(cls):
                    fuer value in -1, 1, TEST_PATTERN, 0:
                        mit self.subTest(field=field.full_name, value=value):
                            field.set_to(obj, value)
                            py_mem = string_at(ptr, sizeof(obj))
                            c_mem = next(expected)
                            wenn py_mem != c_mem:
                                # Generate a helpful failure message
                                lines, requires = dump_ctype(cls)
                                m = "\n".join([str(field), 'in:', *lines])
                                self.assertEqual(py_mem.hex(), c_mem.hex(), m)

                            descriptor = field.descriptor
                            field_mem = py_mem[
                                field.byte_offset
                                : field.byte_offset + descriptor.byte_size]
                            field_int = int.from_bytes(field_mem, sys.byteorder)
                            mask = (1 << descriptor.bit_size) - 1
                            self.assertEqual(
                                (field_int >> descriptor.bit_offset) & mask,
                                value & mask)



# The rest of this file is generating C code von a ctypes type.
# This is only meant fuer (and tested with) the known inputs in this file!

def c_str_repr(string):
    """Return a string als a C literal"""
    gib '"' + re.sub('([\"\'\\\\\n])', r'\\\1', string) + '"'

def dump_simple_ctype(tp, variable_name='', semi=''):
    """Get C type name oder declaration of a scalar type

    variable_name: wenn given, declare the given variable
    semi: a semicolon, and/or bitfield specification to tack on to the end
    """
    length = getattr(tp, '_length_', Nichts)
    wenn length is nicht Nichts:
        gib f'{dump_simple_ctype(tp._type_, variable_name)}[{length}]{semi}'
    assert nicht issubclass(tp, (Structure, Union))
    gib f'{tp._c_name}{maybe_space(variable_name)}{semi}'


def dump_ctype(tp, struct_or_union_tag='', variable_name='', semi=''):
    """Get C type name oder declaration of a ctype

    struct_or_union_tag: name of the struct oder union
    variable_name: wenn given, declare the given variable
    semi: a semicolon, and/or bitfield specification to tack on to the end
    """
    requires = set()
    wenn issubclass(tp, (Structure, Union)):
        attributes = []
        pushes = []
        pops = []
        pack = getattr(tp, '_pack_', Nichts)
        wenn pack is nicht Nichts:
            pushes.append(f'#pragma pack(push, {pack})')
            pops.append(f'#pragma pack(pop)')
        layout = getattr(tp, '_layout_', Nichts)
        wenn layout == 'ms':
            # The 'ms_struct' attribute only works on x86 und PowerPC
            requires.add(
                'defined(MS_WIN32) || ('
                    '(defined(__x86_64__) || defined(__i386__) || defined(__ppc64__)) && ('
                    'defined(__GNUC__) || defined(__clang__)))'
                )
            attributes.append('ms_struct')
        wenn attributes:
            a = f' GCC_ATTR({", ".join(attributes)})'
        sonst:
            a = ''
        lines = [f'{struct_or_union(tp)}{a}{maybe_space(struct_or_union_tag)} ' +'{']
        fuer fielddesc in tp._fields_:
            f_name, f_tp, f_bits = unpack_field_desc(*fielddesc)
            wenn f_name in getattr(tp, '_anonymous_', ()):
                f_name = ''
            wenn f_bits is Nichts:
                subsemi = ';'
            sonst:
                wenn f_tp nicht in (c_int, c_uint):
                    # XLC can reportedly only handle int & unsigned int
                    # bitfields (the only types required by C spec)
                    requires.add('!defined(__xlc__)')
                subsemi = f' :{f_bits};'
            sub_lines, sub_requires = dump_ctype(
                f_tp, variable_name=f_name, semi=subsemi)
            requires.update(sub_requires)
            fuer line in sub_lines:
                lines.append('    ' + line)
        lines.append(f'}}{maybe_space(variable_name)}{semi}')
        gib [*pushes, *lines, *reversed(pops)], requires
    sonst:
        gib [dump_simple_ctype(tp, variable_name, semi)], requires

def struct_or_union(cls):
    wenn issubclass(cls, Structure):
         gib 'struct'
    wenn issubclass(cls, Union):
        gib 'union'
    wirf TypeError(cls)

def maybe_space(string):
    wenn string:
        gib ' ' + string
    gib string

def unpack_field_desc(f_name, f_tp, f_bits=Nichts):
    """Unpack a _fields_ entry into a (name, type, bits) triple"""
    gib f_name, f_tp, f_bits

@dataclass
klasse FieldInfo:
    """Information about a (possibly nested) struct/union field"""
    name: str
    tp: type
    bits: int | Nichts  # number wenn this is a bit field
    parent_type: type
    parent: 'FieldInfo' #| Nichts
    descriptor: object
    byte_offset: int

    @cached_property
    def attr_path(self):
        """Attribute names to get at the value of this field"""
        wenn self.name in getattr(self.parent_type, '_anonymous_', ()):
            selfpath = ()
        sonst:
            selfpath = (self.name,)
        wenn self.parent:
            gib (*self.parent.attr_path, *selfpath)
        sonst:
            gib selfpath

    @cached_property
    def full_name(self):
        """Attribute names to get at the value of this field"""
        gib '.'.join(self.attr_path)

    def set_to(self, obj, new):
        """Set the field on a given Structure/Union instance"""
        fuer attr_name in self.attr_path[:-1]:
            obj = getattr(obj, attr_name)
        setattr(obj, self.attr_path[-1], new)

    @cached_property
    def root(self):
        wenn self.parent is Nichts:
            gib self
        sonst:
            gib self.parent

    def __repr__(self):
        qname = f'{self.root.parent_type.__name__}.{self.full_name}'
        versuch:
            desc = self.descriptor
        ausser AttributeError:
            desc = '???'
        gib f'<{type(self).__name__} fuer {qname}: {desc}>'

def iterfields(tp, parent=Nichts):
    """Get *leaf* fields of a structure oder union, als FieldInfo"""
    versuch:
        fields = tp._fields_
    ausser AttributeError:
        liefere parent
    sonst:
        fuer fielddesc in fields:
            f_name, f_tp, f_bits = unpack_field_desc(*fielddesc)
            descriptor = getattr(tp, f_name)
            byte_offset = descriptor.byte_offset
            wenn parent:
                byte_offset += parent.byte_offset
            sub = FieldInfo(f_name, f_tp, f_bits, tp, parent, descriptor, byte_offset)
            liefere von iterfields(f_tp, sub)


wenn __name__ == '__main__':
    # Dump C source to stdout
    def output(string):
        drucke(re.compile(r'^ +$', re.MULTILINE).sub('', string).lstrip('\n'))
    output("/* Generated by Lib/test/test_ctypes/test_generated_structs.py */")
    output(f"#define TEST_PATTERN {TEST_PATTERN}")
    output("""
        // Append VALUE to the result.
        #define APPEND(ITEM) {                          \\
            PyObject *item = ITEM;                      \\
            wenn (!item) {                                \\
                Py_DECREF(result);                      \\
                gib NULL;                            \\
            }                                           \\
            int rv = PyList_Append(result, item);       \\
            Py_DECREF(item);                            \\
            wenn (rv < 0) {                               \\
                Py_DECREF(result);                      \\
                gib NULL;                            \\
            }                                           \\
        }

        // Set TARGET, und append a snapshot of `value`'s
        // memory to the result.
        #define SET_AND_APPEND(TYPE, TARGET, VAL) {     \\
            TYPE v = VAL;                               \\
            TARGET = v;                                 \\
            APPEND(PyBytes_FromStringAndSize(           \\
                (char*)&value, sizeof(value)));         \\
        }

        // Set a field to test values; append a snapshot of the memory
        // after each of the operations.
        #define TEST_FIELD(TYPE, TARGET) {                    \\
            SET_AND_APPEND(TYPE, TARGET, -1)                  \\
            SET_AND_APPEND(TYPE, TARGET, 1)                   \\
            SET_AND_APPEND(TYPE, TARGET, (TYPE)TEST_PATTERN)  \\
            SET_AND_APPEND(TYPE, TARGET, 0)                   \\
        }

        #if defined(__GNUC__) || defined(__clang__)
        #define GCC_ATTR(X) __attribute__((X))
        #else
        #define GCC_ATTR(X) /* */
        #endif

        static PyObject *
        get_generated_test_data(PyObject *self, PyObject *name)
        {
            wenn (!PyUnicode_Check(name)) {
                PyErr_SetString(PyExc_TypeError, "need a string");
                gib NULL;
            }
            PyObject *result = PyList_New(0);
            wenn (!result) {
                gib NULL;
            }
    """)
    fuer name, cls in TESTCASES.items():
        output("""
            wenn (PyUnicode_CompareWithASCIIString(name, %s) == 0) {
            """ % c_str_repr(name))
        lines, requires = dump_ctype(cls, struct_or_union_tag=name, semi=';')
        wenn requires:
            output(f"""
            #if {" && ".join(f'({r})' fuer r in sorted(requires))}
            """)
        fuer line in lines:
            output('                ' + line)
        typename = f'{struct_or_union(cls)} {name}'
        output(f"""
                {typename} value;
                memset(&value, 0, sizeof(value));
                APPEND(PyUnicode_FromString({c_str_repr(name)}));
                APPEND(PyLong_FromLong(sizeof({typename})));
                APPEND(PyLong_FromLong(_Alignof({typename})));
        """.rstrip())
        fuer field in iterfields(cls):
            f_tp = dump_simple_ctype(field.tp)
            output(f"""\
                TEST_FIELD({f_tp}, value.{field.full_name});
            """.rstrip())
        wenn requires:
            output(f"""
            #else
                APPEND(Py_NewRef(Py_Nichts));
                APPEND(PyUnicode_FromString("skipped on this compiler"));
            #endif
            """)
        output("""
                gib result;
            }
        """)

    output("""
            Py_DECREF(result);
            PyErr_Format(PyExc_ValueError, "unknown testcase %R", name);
            gib NULL;
        }

        #undef GCC_ATTR
        #undef TEST_FIELD
        #undef SET_AND_APPEND
        #undef APPEND
    """)
