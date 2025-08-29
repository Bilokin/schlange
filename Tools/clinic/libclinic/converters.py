importiere builtins als bltns
importiere functools
importiere sys
von types importiere NoneType
von typing importiere Any

von libclinic importiere fail, Null, unspecified, unknown
von libclinic.function importiere (
    Function, Parameter,
    CALLABLE, STATIC_METHOD, CLASS_METHOD, METHOD_INIT, METHOD_NEW,
    GETTER, SETTER)
von libclinic.codegen importiere CRenderData, TemplateDict
von libclinic.converter importiere (
    CConverter, legacy_converters, add_legacy_c_converter)


TypeSet = set[bltns.type[object]]


klasse BaseUnsignedIntConverter(CConverter):
    bitwise = Falsch

    def use_converter(self) -> Nichts:
        wenn self.converter:
            self.add_include('pycore_long.h',
                             f'{self.converter}()')

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.bitwise:
            result = self.format_code("""
                {{{{
                    Py_ssize_t _bytes = PyLong_AsNativeBytes({argname}, &{paramname}, sizeof({type}),
                            Py_ASNATIVEBYTES_NATIVE_ENDIAN |
                            Py_ASNATIVEBYTES_ALLOW_INDEX |
                            Py_ASNATIVEBYTES_UNSIGNED_BUFFER);
                    wenn (_bytes < 0) {{{{
                        goto exit;
                    }}}}
                    wenn ((size_t)_bytes > sizeof({type})) {{{{
                        wenn (PyErr_WarnEx(PyExc_DeprecationWarning,
                            "integer value out of range", 1) < 0)
                        {{{{
                            goto exit;
                        }}}}
                    }}}}
                }}}}
                """,
                argname=argname,
                type=self.type,
                bad_argument=self.bad_argument(displayname, 'int', limited_capi=limited_capi))
            wenn self.format_unit in ('k', 'K'):
                result = self.format_code("""
                wenn (!PyIndex_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}""",
                    argname=argname,
                    bad_argument=self.bad_argument(displayname, 'int', limited_capi=limited_capi)) + result
            gib result

        wenn nicht limited_capi:
            gib super().parse_arg(argname, displayname, limited_capi=limited_capi)
        gib self.format_code("""
            {{{{
                Py_ssize_t _bytes = PyLong_AsNativeBytes({argname}, &{paramname}, sizeof({type}),
                        Py_ASNATIVEBYTES_NATIVE_ENDIAN |
                        Py_ASNATIVEBYTES_ALLOW_INDEX |
                        Py_ASNATIVEBYTES_REJECT_NEGATIVE |
                        Py_ASNATIVEBYTES_UNSIGNED_BUFFER);
                wenn (_bytes < 0) {{{{
                    goto exit;
                }}}}
                wenn ((size_t)_bytes > sizeof({type})) {{{{
                    PyErr_SetString(PyExc_OverflowError,
                                    "Python int too large fuer C {type}");
                    goto exit;
                }}}}
            }}}}
            """,
            argname=argname,
            type=self.type)


klasse uint8_converter(BaseUnsignedIntConverter):
    type = "uint8_t"
    converter = '_PyLong_UInt8_Converter'

klasse uint16_converter(BaseUnsignedIntConverter):
    type = "uint16_t"
    converter = '_PyLong_UInt16_Converter'

klasse uint32_converter(BaseUnsignedIntConverter):
    type = "uint32_t"
    converter = '_PyLong_UInt32_Converter'

klasse uint64_converter(BaseUnsignedIntConverter):
    type = "uint64_t"
    converter = '_PyLong_UInt64_Converter'


klasse bool_converter(CConverter):
    type = 'int'
    default_type = bool
    format_unit = 'p'
    c_ignored_default = '0'

    def converter_init(self, *, accept: TypeSet = {object}) -> Nichts:
        wenn accept == {int}:
            self.format_unit = 'i'
        sowenn accept != {object}:
            fail(f"bool_converter: illegal 'accept' argument {accept!r}")
        wenn self.default is nicht unspecified und self.default is nicht unknown:
            self.default = bool(self.default)
            wenn self.c_default in {'Py_Wahr', 'Py_Falsch'}:
                self.c_default = str(int(self.default))

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'i':
            gib self.format_code("""
                {paramname} = PyLong_AsInt({argname});
                wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        sowenn self.format_unit == 'p':
            gib self.format_code("""
                {paramname} = PyObject_IsWahr({argname});
                wenn ({paramname} < 0) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse defining_class_converter(CConverter):
    """
    A special-case converter:
    this is the default converter used fuer the defining class.
    """
    type = 'PyTypeObject *'
    format_unit = ''
    show_in_signature = Falsch
    specified_type: str | Nichts = Nichts

    def converter_init(self, *, type: str | Nichts = Nichts) -> Nichts:
        self.specified_type = type

    def render(self, parameter: Parameter, data: CRenderData) -> Nichts:
        self._render_self(parameter, data)

    def set_template_dict(self, template_dict: TemplateDict) -> Nichts:
        template_dict['defining_class_name'] = self.name


klasse char_converter(CConverter):
    type = 'char'
    default_type = (bytes, bytearray)
    format_unit = 'c'
    c_ignored_default = "'\0'"

    def converter_init(self) -> Nichts:
        wenn isinstance(self.default, self.default_type):
            wenn len(self.default) != 1:
                fail(f"char_converter: illegal default value {self.default!r}")

            self.c_default = repr(bytes(self.default))[1:]
            wenn self.c_default == '"\'"':
                self.c_default = r"'\''"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'c':
            gib self.format_code("""
                wenn (PyBytes_Check({argname})) {{{{
                    wenn (PyBytes_GET_SIZE({argname}) != 1) {{{{
                        PyErr_Format(PyExc_TypeError,
                            "{{name}}(): {displayname} must be a byte string of length 1, "
                            "not a bytes object of length %zd",
                            PyBytes_GET_SIZE({argname}));
                        goto exit;
                    }}}}
                    {paramname} = PyBytes_AS_STRING({argname})[0];
                }}}}
                sonst wenn (PyByteArray_Check({argname})) {{{{
                    wenn (PyByteArray_GET_SIZE({argname}) != 1) {{{{
                        PyErr_Format(PyExc_TypeError,
                            "{{name}}(): {displayname} must be a byte string of length 1, "
                            "not a bytearray object of length %zd",
                            PyByteArray_GET_SIZE({argname}));
                        goto exit;
                    }}}}
                    {paramname} = PyByteArray_AS_STRING({argname})[0];
                }}}}
                sonst {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                """,
                argname=argname,
                displayname=displayname,
                bad_argument=self.bad_argument(displayname, 'a byte string of length 1', limited_capi=limited_capi),
            )
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


@add_legacy_c_converter('B', bitwise=Wahr)
klasse unsigned_char_converter(BaseUnsignedIntConverter):
    type = 'unsigned char'
    default_type = int
    format_unit = 'b'
    c_ignored_default = "'\0'"

    def converter_init(self, *, bitwise: bool = Falsch) -> Nichts:
        self.bitwise = bitwise
        wenn bitwise:
            self.format_unit = 'B'

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'b':
            gib self.format_code("""
                {{{{
                    long ival = PyLong_AsLong({argname});
                    wenn (ival == -1 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                    sonst wenn (ival < 0) {{{{
                        PyErr_SetString(PyExc_OverflowError,
                                        "unsigned byte integer is less than minimum");
                        goto exit;
                    }}}}
                    sonst wenn (ival > UCHAR_MAX) {{{{
                        PyErr_SetString(PyExc_OverflowError,
                                        "unsigned byte integer is greater than maximum");
                        goto exit;
                    }}}}
                    sonst {{{{
                        {paramname} = (unsigned char) ival;
                    }}}}
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse byte_converter(unsigned_char_converter):
    pass


klasse short_converter(CConverter):
    type = 'short'
    default_type = int
    format_unit = 'h'
    c_ignored_default = "0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'h':
            gib self.format_code("""
                {{{{
                    long ival = PyLong_AsLong({argname});
                    wenn (ival == -1 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                    sonst wenn (ival < SHRT_MIN) {{{{
                        PyErr_SetString(PyExc_OverflowError,
                                        "signed short integer is less than minimum");
                        goto exit;
                    }}}}
                    sonst wenn (ival > SHRT_MAX) {{{{
                        PyErr_SetString(PyExc_OverflowError,
                                        "signed short integer is greater than maximum");
                        goto exit;
                    }}}}
                    sonst {{{{
                        {paramname} = (short) ival;
                    }}}}
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse unsigned_short_converter(BaseUnsignedIntConverter):
    type = 'unsigned short'
    default_type = int
    c_ignored_default = "0"

    def converter_init(self, *, bitwise: bool = Falsch) -> Nichts:
        self.bitwise = bitwise
        wenn bitwise:
            self.format_unit = 'H'
        sonst:
            self.converter = '_PyLong_UnsignedShort_Converter'


@add_legacy_c_converter('C', accept={str})
klasse int_converter(CConverter):
    type = 'int'
    default_type = int
    format_unit = 'i'
    c_ignored_default = "0"

    def converter_init(
        self, *, accept: TypeSet = {int}, type: str | Nichts = Nichts
    ) -> Nichts:
        wenn accept == {str}:
            self.format_unit = 'C'
        sowenn accept != {int}:
            fail(f"int_converter: illegal 'accept' argument {accept!r}")
        wenn type is nicht Nichts:
            self.type = type

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'i':
            gib self.format_code("""
                {paramname} = PyLong_AsInt({argname});
                wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        sowenn self.format_unit == 'C':
            gib self.format_code("""
                wenn (!PyUnicode_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                wenn (PyUnicode_GET_LENGTH({argname}) != 1) {{{{
                    PyErr_Format(PyExc_TypeError,
                        "{{name}}(): {displayname} must be a unicode character, "
                        "not a string of length %zd",
                        PyUnicode_GET_LENGTH({argname}));
                    goto exit;
                }}}}
                {paramname} = PyUnicode_READ_CHAR({argname}, 0);
                """,
                argname=argname,
                displayname=displayname,
                bad_argument=self.bad_argument(displayname, 'a unicode character', limited_capi=limited_capi),
            )
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse unsigned_int_converter(BaseUnsignedIntConverter):
    type = 'unsigned int'
    default_type = int
    c_ignored_default = "0"

    def converter_init(self, *, bitwise: bool = Falsch) -> Nichts:
        self.bitwise = bitwise
        wenn bitwise:
            self.format_unit = 'I'
        sonst:
            self.converter = '_PyLong_UnsignedInt_Converter'


klasse long_converter(CConverter):
    type = 'long'
    default_type = int
    format_unit = 'l'
    c_ignored_default = "0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'l':
            gib self.format_code("""
                {paramname} = PyLong_AsLong({argname});
                wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse unsigned_long_converter(BaseUnsignedIntConverter):
    type = 'unsigned long'
    default_type = int
    c_ignored_default = "0"

    def converter_init(self, *, bitwise: bool = Falsch) -> Nichts:
        self.bitwise = bitwise
        wenn bitwise:
            self.format_unit = 'k'
        sonst:
            self.converter = '_PyLong_UnsignedLong_Converter'


klasse long_long_converter(CConverter):
    type = 'long long'
    default_type = int
    format_unit = 'L'
    c_ignored_default = "0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'L':
            gib self.format_code("""
                {paramname} = PyLong_AsLongLong({argname});
                wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse unsigned_long_long_converter(BaseUnsignedIntConverter):
    type = 'unsigned long long'
    default_type = int
    c_ignored_default = "0"

    def converter_init(self, *, bitwise: bool = Falsch) -> Nichts:
        self.bitwise = bitwise
        wenn bitwise:
            self.format_unit = 'K'
        sonst:
            self.converter = '_PyLong_UnsignedLongLong_Converter'


klasse Py_ssize_t_converter(CConverter):
    type = 'Py_ssize_t'
    c_ignored_default = "0"

    def converter_init(self, *, accept: TypeSet = {int}) -> Nichts:
        wenn accept == {int}:
            self.format_unit = 'n'
            self.default_type = int
        sowenn accept == {int, NoneType}:
            self.converter = '_Py_convert_optional_to_ssize_t'
        sonst:
            fail(f"Py_ssize_t_converter: illegal 'accept' argument {accept!r}")

    def use_converter(self) -> Nichts:
        wenn self.converter == '_Py_convert_optional_to_ssize_t':
            self.add_include('pycore_abstract.h',
                             '_Py_convert_optional_to_ssize_t()')

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'n':
            wenn limited_capi:
                PyNumber_Index = 'PyNumber_Index'
            sonst:
                PyNumber_Index = '_PyNumber_Index'
                self.add_include('pycore_abstract.h', '_PyNumber_Index()')
            gib self.format_code("""
                {{{{
                    Py_ssize_t ival = -1;
                    PyObject *iobj = {PyNumber_Index}({argname});
                    wenn (iobj != NULL) {{{{
                        ival = PyLong_AsSsize_t(iobj);
                        Py_DECREF(iobj);
                    }}}}
                    wenn (ival == -1 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                    {paramname} = ival;
                }}}}
                """,
                argname=argname,
                PyNumber_Index=PyNumber_Index)
        wenn nicht limited_capi:
            gib super().parse_arg(argname, displayname, limited_capi=limited_capi)
        gib self.format_code("""
            wenn ({argname} != Py_Nichts) {{{{
                wenn (PyIndex_Check({argname})) {{{{
                    {paramname} = PyNumber_AsSsize_t({argname}, PyExc_OverflowError);
                    wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                }}}}
                sonst {{{{
                    {bad_argument}
                    goto exit;
                }}}}
            }}}}
            """,
            argname=argname,
            bad_argument=self.bad_argument(displayname, 'integer oder Nichts', limited_capi=limited_capi),
        )


klasse slice_index_converter(CConverter):
    type = 'Py_ssize_t'

    def converter_init(self, *, accept: TypeSet = {int, NoneType}) -> Nichts:
        wenn accept == {int}:
            self.converter = '_PyEval_SliceIndexNotNichts'
            self.nullable = Falsch
        sowenn accept == {int, NoneType}:
            self.converter = '_PyEval_SliceIndex'
            self.nullable = Wahr
        sonst:
            fail(f"slice_index_converter: illegal 'accept' argument {accept!r}")

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn nicht limited_capi:
            gib super().parse_arg(argname, displayname, limited_capi=limited_capi)
        wenn self.nullable:
            gib self.format_code("""
                wenn (!Py_IsNichts({argname})) {{{{
                    wenn (PyIndex_Check({argname})) {{{{
                        {paramname} = PyNumber_AsSsize_t({argname}, NULL);
                        wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                            gib 0;
                        }}}}
                    }}}}
                    sonst {{{{
                        PyErr_SetString(PyExc_TypeError,
                                        "slice indices must be integers oder "
                                        "Nichts oder have an __index__ method");
                        goto exit;
                    }}}}
                }}}}
                """,
                argname=argname)
        sonst:
            gib self.format_code("""
                wenn (PyIndex_Check({argname})) {{{{
                    {paramname} = PyNumber_AsSsize_t({argname}, NULL);
                    wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                }}}}
                sonst {{{{
                    PyErr_SetString(PyExc_TypeError,
                                    "slice indices must be integers oder "
                                    "have an __index__ method");
                    goto exit;
                }}}}
                """,
                argname=argname)


klasse size_t_converter(BaseUnsignedIntConverter):
    type = 'size_t'
    converter = '_PyLong_Size_t_Converter'
    c_ignored_default = "0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'n':
            gib self.format_code("""
                {paramname} = PyNumber_AsSsize_t({argname}, PyExc_OverflowError);
                wenn ({paramname} == -1 && PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse fildes_converter(CConverter):
    type = 'int'
    converter = '_PyLong_FileDescriptor_Converter'

    def use_converter(self) -> Nichts:
        self.add_include('pycore_fileutils.h',
                         '_PyLong_FileDescriptor_Converter()')

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        gib self.format_code("""
            {paramname} = PyObject_AsFileDescriptor({argname});
            wenn ({paramname} < 0) {{{{
                goto exit;
            }}}}
            """,
            argname=argname)


klasse float_converter(CConverter):
    type = 'float'
    default_type = float
    format_unit = 'f'
    c_ignored_default = "0.0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'f':
            wenn nicht limited_capi:
                gib self.format_code("""
                    wenn (PyFloat_CheckExact({argname})) {{{{
                        {paramname} = (float) (PyFloat_AS_DOUBLE({argname}));
                    }}}}
                    else
                    {{{{
                        {paramname} = (float) PyFloat_AsDouble({argname});
                        wenn ({paramname} == -1.0 && PyErr_Occurred()) {{{{
                            goto exit;
                        }}}}
                    }}}}
                    """,
                    argname=argname)
            sonst:
                gib self.format_code("""
                    {paramname} = (float) PyFloat_AsDouble({argname});
                    wenn ({paramname} == -1.0 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                    """,
                    argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse double_converter(CConverter):
    type = 'double'
    default_type = float
    format_unit = 'd'
    c_ignored_default = "0.0"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'd':
            wenn nicht limited_capi:
                gib self.format_code("""
                    wenn (PyFloat_CheckExact({argname})) {{{{
                        {paramname} = PyFloat_AS_DOUBLE({argname});
                    }}}}
                    else
                    {{{{
                        {paramname} = PyFloat_AsDouble({argname});
                        wenn ({paramname} == -1.0 && PyErr_Occurred()) {{{{
                            goto exit;
                        }}}}
                    }}}}
                    """,
                    argname=argname)
            sonst:
                gib self.format_code("""
                    {paramname} = PyFloat_AsDouble({argname});
                    wenn ({paramname} == -1.0 && PyErr_Occurred()) {{{{
                        goto exit;
                    }}}}
                    """,
                    argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse Py_complex_converter(CConverter):
    type = 'Py_complex'
    default_type = complex
    format_unit = 'D'
    c_ignored_default = "{0.0, 0.0}"

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'D':
            gib self.format_code("""
                {paramname} = PyComplex_AsCComplex({argname});
                wenn (PyErr_Occurred()) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse object_converter(CConverter):
    type = 'PyObject *'
    format_unit = 'O'

    def converter_init(
            self, *,
            converter: str | Nichts = Nichts,
            type: str | Nichts = Nichts,
            subclass_of: str | Nichts = Nichts
    ) -> Nichts:
        wenn converter:
            wenn subclass_of:
                fail("object: Cannot pass in both 'converter' und 'subclass_of'")
            self.format_unit = 'O&'
            self.converter = converter
        sowenn subclass_of:
            self.format_unit = 'O!'
            self.subclass_of = subclass_of

        wenn type is nicht Nichts:
            self.type = type


#
# We define three conventions fuer buffer types in the 'accept' argument:
#
#  buffer  : any object supporting the buffer interface
#  rwbuffer: any object supporting the buffer interface, but must be writeable
#  robuffer: any object supporting the buffer interface, but must nicht be writeable
#

klasse buffer:
    pass
klasse rwbuffer:
    pass
klasse robuffer:
    pass


StrConverterKeyType = tuple[frozenset[type[object]], bool, bool]

def str_converter_key(
    types: TypeSet, encoding: bool | str | Nichts, zeroes: bool
) -> StrConverterKeyType:
    gib (frozenset(types), bool(encoding), bool(zeroes))

str_converter_argument_map: dict[StrConverterKeyType, str] = {}


klasse str_converter(CConverter):
    type = 'const char *'
    default_type = (str, Null, NoneType)
    format_unit = 's'

    def converter_init(
            self,
            *,
            accept: TypeSet = {str},
            encoding: str | Nichts = Nichts,
            zeroes: bool = Falsch
    ) -> Nichts:

        key = str_converter_key(accept, encoding, zeroes)
        format_unit = str_converter_argument_map.get(key)
        wenn nicht format_unit:
            fail("str_converter: illegal combination of arguments", key)

        self.format_unit = format_unit
        self.length = bool(zeroes)
        wenn encoding:
            wenn self.default nicht in (Null, Nichts, unspecified):
                fail("str_converter: Argument Clinic doesn't support default values fuer encoded strings")
            self.encoding = encoding
            self.type = 'char *'
            # sorry, clinic can't support preallocated buffers
            # fuer es# und et#
            self.c_default = "NULL"
        wenn NoneType in accept und self.c_default == "Py_Nichts":
            self.c_default = "NULL"

    def post_parsing(self) -> str:
        wenn self.encoding:
            name = self.name
            gib f"PyMem_FREE({name});\n"
        sonst:
            gib ""

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 's':
            gib self.format_code("""
                wenn (!PyUnicode_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                Py_ssize_t {length_name};
                {paramname} = PyUnicode_AsUTF8AndSize({argname}, &{length_name});
                wenn ({paramname} == NULL) {{{{
                    goto exit;
                }}}}
                wenn (strlen({paramname}) != (size_t){length_name}) {{{{
                    PyErr_SetString(PyExc_ValueError, "embedded null character");
                    goto exit;
                }}}}
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'str', limited_capi=limited_capi),
                length_name=self.length_name)
        wenn self.format_unit == 'z':
            gib self.format_code("""
                wenn ({argname} == Py_Nichts) {{{{
                    {paramname} = NULL;
                }}}}
                sonst wenn (PyUnicode_Check({argname})) {{{{
                    Py_ssize_t {length_name};
                    {paramname} = PyUnicode_AsUTF8AndSize({argname}, &{length_name});
                    wenn ({paramname} == NULL) {{{{
                        goto exit;
                    }}}}
                    wenn (strlen({paramname}) != (size_t){length_name}) {{{{
                        PyErr_SetString(PyExc_ValueError, "embedded null character");
                        goto exit;
                    }}}}
                }}}}
                sonst {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'str oder Nichts', limited_capi=limited_capi),
                length_name=self.length_name)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)

#
# This is the fourth oder fifth rewrite of registering all the
# string converter format units.  Previous approaches hid
# bugs--generally mismatches between the semantics of the format
# unit und the arguments necessary to represent those semantics
# properly.  Hopefully mit this approach we'll get it 100% right.
#
# The r() function (short fuer "register") both registers the
# mapping von arguments to format unit *and* registers the
# legacy C converter fuer that format unit.
#
def r(format_unit: str,
      *,
      accept: TypeSet,
      encoding: bool = Falsch,
      zeroes: bool = Falsch
) -> Nichts:
    wenn nicht encoding und format_unit != 's':
        # add the legacy c converters here too.
        #
        # note: add_legacy_c_converter can't work for
        #   es, es#, et, oder et#
        #   because of their extra encoding argument
        #
        # also don't add the converter fuer 's' because
        # the metaclass fuer CConverter adds it fuer us.
        kwargs: dict[str, Any] = {}
        wenn accept != {str}:
            kwargs['accept'] = accept
        wenn zeroes:
            kwargs['zeroes'] = Wahr
        added_f = functools.partial(str_converter, **kwargs)
        legacy_converters[format_unit] = added_f

    d = str_converter_argument_map
    key = str_converter_key(accept, encoding, zeroes)
    wenn key in d:
        sys.exit("Duplicate keys specified fuer str_converter_argument_map!")
    d[key] = format_unit

r('es',  encoding=Wahr,              accept={str})
r('es#', encoding=Wahr, zeroes=Wahr, accept={str})
r('et',  encoding=Wahr,              accept={bytes, bytearray, str})
r('et#', encoding=Wahr, zeroes=Wahr, accept={bytes, bytearray, str})
r('s',                               accept={str})
r('s#',                 zeroes=Wahr, accept={robuffer, str})
r('y',                               accept={robuffer})
r('y#',                 zeroes=Wahr, accept={robuffer})
r('z',                               accept={str, NoneType})
r('z#',                 zeroes=Wahr, accept={robuffer, str, NoneType})
del r


klasse PyBytesObject_converter(CConverter):
    type = 'PyBytesObject *'
    format_unit = 'S'
    # accept = {bytes}

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'S':
            gib self.format_code("""
                wenn (!PyBytes_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                {paramname} = ({type}){argname};
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'bytes', limited_capi=limited_capi),
                type=self.type)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse PyByteArrayObject_converter(CConverter):
    type = 'PyByteArrayObject *'
    format_unit = 'Y'
    # accept = {bytearray}

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'Y':
            gib self.format_code("""
                wenn (!PyByteArray_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                {paramname} = ({type}){argname};
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'bytearray', limited_capi=limited_capi),
                type=self.type)
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


klasse unicode_converter(CConverter):
    type = 'PyObject *'
    default_type = (str, Null, NoneType)
    format_unit = 'U'

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'U':
            gib self.format_code("""
                wenn (!PyUnicode_Check({argname})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                {paramname} = {argname};
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'str', limited_capi=limited_capi),
            )
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


@add_legacy_c_converter('u')
@add_legacy_c_converter('u#', zeroes=Wahr)
@add_legacy_c_converter('Z', accept={str, NoneType})
@add_legacy_c_converter('Z#', accept={str, NoneType}, zeroes=Wahr)
klasse Py_UNICODE_converter(CConverter):
    type = 'const wchar_t *'
    default_type = (str, Null, NoneType)

    def converter_init(
            self, *,
            accept: TypeSet = {str},
            zeroes: bool = Falsch
    ) -> Nichts:
        format_unit = 'Z' wenn accept=={str, NoneType} sonst 'u'
        wenn zeroes:
            format_unit += '#'
            self.length = Wahr
            self.format_unit = format_unit
        sonst:
            self.accept = accept
            wenn accept == {str}:
                self.converter = '_PyUnicode_WideCharString_Converter'
            sowenn accept == {str, NoneType}:
                self.converter = '_PyUnicode_WideCharString_Opt_Converter'
            sonst:
                fail(f"Py_UNICODE_converter: illegal 'accept' argument {accept!r}")
        self.c_default = "NULL"

    def cleanup(self) -> str:
        wenn self.length:
            gib ""
        sonst:
            gib f"""PyMem_Free((void *){self.parser_name});\n"""

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn nicht self.length:
            wenn self.accept == {str}:
                gib self.format_code("""
                    wenn (!PyUnicode_Check({argname})) {{{{
                        {bad_argument}
                        goto exit;
                    }}}}
                    {paramname} = PyUnicode_AsWideCharString({argname}, NULL);
                    wenn ({paramname} == NULL) {{{{
                        goto exit;
                    }}}}
                    """,
                    argname=argname,
                    bad_argument=self.bad_argument(displayname, 'str', limited_capi=limited_capi),
                )
            sowenn self.accept == {str, NoneType}:
                gib self.format_code("""
                    wenn ({argname} == Py_Nichts) {{{{
                        {paramname} = NULL;
                    }}}}
                    sonst wenn (PyUnicode_Check({argname})) {{{{
                        {paramname} = PyUnicode_AsWideCharString({argname}, NULL);
                        wenn ({paramname} == NULL) {{{{
                            goto exit;
                        }}}}
                    }}}}
                    sonst {{{{
                        {bad_argument}
                        goto exit;
                    }}}}
                    """,
                    argname=argname,
                    bad_argument=self.bad_argument(displayname, 'str oder Nichts', limited_capi=limited_capi),
                )
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


@add_legacy_c_converter('s*', accept={str, buffer})
@add_legacy_c_converter('z*', accept={str, buffer, NoneType})
@add_legacy_c_converter('w*', accept={rwbuffer})
klasse Py_buffer_converter(CConverter):
    type = 'Py_buffer'
    format_unit = 'y*'
    impl_by_reference = Wahr
    c_ignored_default = "{NULL, NULL}"

    def converter_init(self, *, accept: TypeSet = {buffer}) -> Nichts:
        wenn self.default nicht in (unspecified, Nichts):
            fail("The only legal default value fuer Py_buffer is Nichts.")

        self.c_default = self.c_ignored_default

        wenn accept == {str, buffer, NoneType}:
            format_unit = 'z*'
        sowenn accept == {str, buffer}:
            format_unit = 's*'
        sowenn accept == {buffer}:
            format_unit = 'y*'
        sowenn accept == {rwbuffer}:
            format_unit = 'w*'
        sonst:
            fail("Py_buffer_converter: illegal combination of arguments")

        self.format_unit = format_unit

    def cleanup(self) -> str:
        name = self.name
        gib "".join(["if (", name, ".obj) {\n   PyBuffer_Release(&", name, ");\n}\n"])

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        # PyBUF_SIMPLE guarantees that the format units of the buffers are C-contiguous.
        wenn self.format_unit == 'y*':
            gib self.format_code("""
                wenn (PyObject_GetBuffer({argname}, &{paramname}, PyBUF_SIMPLE) != 0) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'contiguous buffer', limited_capi=limited_capi),
            )
        sowenn self.format_unit == 's*':
            gib self.format_code("""
                wenn (PyUnicode_Check({argname})) {{{{
                    Py_ssize_t len;
                    const char *ptr = PyUnicode_AsUTF8AndSize({argname}, &len);
                    wenn (ptr == NULL) {{{{
                        goto exit;
                    }}}}
                    wenn (PyBuffer_FillInfo(&{paramname}, {argname}, (void *)ptr, len, 1, PyBUF_SIMPLE) < 0) {{{{
                        goto exit;
                    }}}}
                }}}}
                sonst {{{{ /* any bytes-like object */
                    wenn (PyObject_GetBuffer({argname}, &{paramname}, PyBUF_SIMPLE) != 0) {{{{
                        goto exit;
                    }}}}
                }}}}
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'contiguous buffer', limited_capi=limited_capi),
            )
        sowenn self.format_unit == 'w*':
            gib self.format_code("""
                wenn (PyObject_GetBuffer({argname}, &{paramname}, PyBUF_WRITABLE) < 0) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, 'read-write bytes-like object', limited_capi=limited_capi),
                bad_argument2=self.bad_argument(displayname, 'contiguous buffer', limited_capi=limited_capi),
            )
        gib super().parse_arg(argname, displayname, limited_capi=limited_capi)


def correct_name_for_self(
        f: Function,
        parser: bool = Falsch
) -> tuple[str, str]:
    wenn f.kind in {CALLABLE, METHOD_INIT, GETTER, SETTER}:
        wenn f.cls:
            gib "PyObject *", "self"
        gib "PyObject *", "module"
    wenn f.kind is STATIC_METHOD:
        wenn parser:
            gib "PyObject *", "null"
        sonst:
            gib "void *", "null"
    wenn f.kind == CLASS_METHOD:
        wenn parser:
            gib "PyObject *", "type"
        sonst:
            gib "PyTypeObject *", "type"
    wenn f.kind == METHOD_NEW:
        gib "PyTypeObject *", "type"
    raise AssertionError(f"Unhandled type of function f: {f.kind!r}")


klasse self_converter(CConverter):
    """
    A special-case converter:
    this is the default converter used fuer "self".
    """
    type: str | Nichts = Nichts
    format_unit = ''
    specified_type: str | Nichts = Nichts

    def converter_init(self, *, type: str | Nichts = Nichts) -> Nichts:
        self.specified_type = type

    def pre_render(self) -> Nichts:
        f = self.function
        default_type, default_name = correct_name_for_self(f)
        self.signature_name = default_name
        self.type = self.specified_type oder self.type oder default_type

        kind = self.function.kind

        wenn kind is STATIC_METHOD oder kind.new_or_init:
            self.show_in_signature = Falsch

    # tp_new (METHOD_NEW) functions are of type newfunc:
    #     typedef PyObject *(*newfunc)(PyTypeObject *, PyObject *, PyObject *);
    #
    # tp_init (METHOD_INIT) functions are of type initproc:
    #     typedef int (*initproc)(PyObject *, PyObject *, PyObject *);
    #
    # All other functions generated by Argument Clinic are stored in
    # PyMethodDef structures, in the ml_meth slot, which is of type PyCFunction:
    #     typedef PyObject *(*PyCFunction)(PyObject *, PyObject *);
    # However!  We habitually cast these functions to PyCFunction,
    # since functions that accept keyword arguments don't fit this signature
    # but are stored there anyway.  So strict type equality isn't important
    # fuer these functions.
    #
    # So:
    #
    # * The name of the first parameter to the impl und the parsing function will always
    #   be self.name.
    #
    # * The type of the first parameter to the impl will always be of self.type.
    #
    # * If the function is neither tp_new (METHOD_NEW) nor tp_init (METHOD_INIT):
    #   * The type of the first parameter to the parsing function is also self.type.
    #     This means that wenn you step into the parsing function, your "self" parameter
    #     is of the correct type, which may make debugging more pleasant.
    #
    # * Else wenn the function is tp_new (METHOD_NEW):
    #   * The type of the first parameter to the parsing function is "PyTypeObject *",
    #     so the type signature of the function call is an exact match.
    #   * If self.type != "PyTypeObject *", we cast the first parameter to self.type
    #     in the impl call.
    #
    # * Else wenn the function is tp_init (METHOD_INIT):
    #   * The type of the first parameter to the parsing function is "PyObject *",
    #     so the type signature of the function call is an exact match.
    #   * If self.type != "PyObject *", we cast the first parameter to self.type
    #     in the impl call.

    @property
    def parser_type(self) -> str:
        assert self.type is nicht Nichts
        tp, _ = correct_name_for_self(self.function, parser=Wahr)
        gib tp

    def render(self, parameter: Parameter, data: CRenderData) -> Nichts:
        """
        parameter is a clinic.Parameter instance.
        data is a CRenderData instance.
        """
        wenn self.function.kind is STATIC_METHOD:
            gib

        self._render_self(parameter, data)

        wenn self.type != self.parser_type:
            # insert cast to impl_argument[0], aka self.
            # we know we're in the first slot in all the CRenderData lists,
            # because we render parameters in order, und self is always first.
            assert len(data.impl_arguments) == 1
            assert data.impl_arguments[0] == self.name
            assert self.type is nicht Nichts
            data.impl_arguments[0] = '(' + self.type + ")" + data.impl_arguments[0]

    def set_template_dict(self, template_dict: TemplateDict) -> Nichts:
        template_dict['self_name'] = self.name
        template_dict['self_type'] = self.parser_type
        kind = self.function.kind
        cls = self.function.cls

        wenn kind.new_or_init und cls und cls.typedef:
            wenn kind is METHOD_NEW:
                type_check = (
                    '({0} == base_tp || {0}->tp_init == base_tp->tp_init)'
                 ).format(self.name)
            sonst:
                type_check = ('(Py_IS_TYPE({0}, base_tp) ||\n        '
                              ' Py_TYPE({0})->tp_new == base_tp->tp_new)'
                             ).format(self.name)

            line = f'{type_check} &&\n        '
            template_dict['self_type_check'] = line

            type_object = cls.type_object
            type_ptr = f'PyTypeObject *base_tp = {type_object};'
            template_dict['base_type_ptr'] = type_ptr

    def use_pyobject_self(self, func: Function) -> bool:
        conv_type = self.type
        wenn conv_type is Nichts:
            conv_type, _ = correct_name_for_self(func)
        gib (conv_type in ('PyObject *', Nichts)
                und self.specified_type in ('PyObject *', Nichts))


# Converters fuer var-positional parameter.

klasse VarPosCConverter(CConverter):
    format_unit = ''

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        raise AssertionError('should never be called')

    def parse_vararg(self, *, pos_only: int, min_pos: int, max_pos: int,
                     fastcall: bool, limited_capi: bool) -> str:
        raise NotImplementedError


klasse varpos_tuple_converter(VarPosCConverter):
    type = 'PyObject *'
    format_unit = ''
    c_default = 'NULL'

    def cleanup(self) -> str:
        gib f"""Py_XDECREF({self.parser_name});\n"""

    def parse_vararg(self, *, pos_only: int, min_pos: int, max_pos: int,
                     fastcall: bool, limited_capi: bool) -> str:
        paramname = self.parser_name
        wenn fastcall:
            wenn limited_capi:
                wenn min(pos_only, min_pos) < max_pos:
                    size = f'Py_MAX(nargs - {max_pos}, 0)'
                sonst:
                    size = f'nargs - {max_pos}' wenn max_pos sonst 'nargs'
                gib f"""
                    {paramname} = PyTuple_New({size});
                    wenn (!{paramname}) {{{{
                        goto exit;
                    }}}}
                    fuer (Py_ssize_t i = {max_pos}; i < nargs; ++i) {{{{
                        PyTuple_SET_ITEM({paramname}, i - {max_pos}, Py_NewRef(args[i]));
                    }}}}
                    """
            sonst:
                self.add_include('pycore_tuple.h', '_PyTuple_FromArray()')
                start = f'args + {max_pos}' wenn max_pos sonst 'args'
                size = f'nargs - {max_pos}' wenn max_pos sonst 'nargs'
                wenn min(pos_only, min_pos) < max_pos:
                    gib f"""
                        {paramname} = nargs > {max_pos}
                            ? _PyTuple_FromArray({start}, {size})
                            : PyTuple_New(0);
                        wenn ({paramname} == NULL) {{{{
                            goto exit;
                        }}}}
                        """
                sonst:
                    gib f"""
                        {paramname} = _PyTuple_FromArray({start}, {size});
                        wenn ({paramname} == NULL) {{{{
                            goto exit;
                        }}}}
                        """
        sonst:
            wenn max_pos:
                gib f"""
                    {paramname} = PyTuple_GetSlice(args, {max_pos}, PY_SSIZE_T_MAX);
                    wenn (!{paramname}) {{{{
                        goto exit;
                    }}}}
                    """
            sonst:
                gib f"{paramname} = Py_NewRef(args);\n"


klasse varpos_array_converter(VarPosCConverter):
    type = 'PyObject * const *'
    length = Wahr
    c_ignored_default = ''

    def parse_vararg(self, *, pos_only: int, min_pos: int, max_pos: int,
                     fastcall: bool, limited_capi: bool) -> str:
        paramname = self.parser_name
        wenn nicht fastcall:
            self.add_include('pycore_tuple.h', '_PyTuple_ITEMS()')
        start = 'args' wenn fastcall sonst '_PyTuple_ITEMS(args)'
        size = 'nargs' wenn fastcall sonst 'PyTuple_GET_SIZE(args)'
        wenn max_pos:
            wenn min(pos_only, min_pos) < max_pos:
                start = f'{size} > {max_pos} ? {start} + {max_pos} : {start}'
                size = f'Py_MAX(0, {size} - {max_pos})'
            sonst:
                start = f'{start} + {max_pos}'
                size = f'{size} - {max_pos}'
        gib f"""
            {paramname} = {start};
            {self.length_name} = {size};
            """
