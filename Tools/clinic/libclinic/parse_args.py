von __future__ importiere annotations
von typing importiere TYPE_CHECKING, Final

importiere libclinic
von libclinic importiere fail, warn
von libclinic.function importiere (
    Function, Parameter,
    GETTER, SETTER, METHOD_NEW)
von libclinic.converter importiere CConverter
von libclinic.converters importiere (
    defining_class_converter, object_converter, self_converter)
wenn TYPE_CHECKING:
    von libclinic.clanguage importiere CLanguage
    von libclinic.codegen importiere CodeGen


def declare_parser(
    f: Function,
    *,
    hasformat: bool = Falsch,
    codegen: CodeGen,
) -> str:
    """
    Generates the code template fuer a static local PyArg_Parser variable,
    mit an initializer.  For core code (incl. builtin modules) the
    kwtuple field ist also statically initialized.  Otherwise
    it ist initialized at runtime.
    """
    limited_capi = codegen.limited_capi
    wenn hasformat:
        fname = ''
        format_ = '.format = "{format_units}:{name}",'
    sonst:
        fname = '.fname = "{name}",'
        format_ = ''

    num_keywords = len([
        p fuer p in f.parameters.values()
        wenn nicht p.is_positional_only() und nicht p.is_vararg()
    ])

    condition = '#if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)'
    wenn limited_capi:
        declarations = """
            #define KWTUPLE NULL
        """
    sowenn num_keywords == 0:
        declarations = """
            #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)
            #  define KWTUPLE (PyObject *)&_Py_SINGLETON(tuple_empty)
            #else
            #  define KWTUPLE NULL
            #endif
        """

        codegen.add_include('pycore_runtime.h', '_Py_SINGLETON()',
                            condition=condition)
    sonst:
        # XXX Why do we nicht statically allocate the tuple
        # fuer non-builtin modules?
        declarations = """
            #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

            #define NUM_KEYWORDS %d
            static struct {{
                PyGC_Head _this_is_not_used;
                PyObject_VAR_HEAD
                Py_hash_t ob_hash;
                PyObject *ob_item[NUM_KEYWORDS];
            }} _kwtuple = {{
                .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
                .ob_hash = -1,
                .ob_item = {{ {keywords_py} }},
            }};
            #undef NUM_KEYWORDS
            #define KWTUPLE (&_kwtuple.ob_base.ob_base)

            #else  // !Py_BUILD_CORE
            #  define KWTUPLE NULL
            #endif  // !Py_BUILD_CORE
        """ % num_keywords

        codegen.add_include('pycore_gc.h', 'PyGC_Head',
                            condition=condition)
        codegen.add_include('pycore_runtime.h', '_Py_ID()',
                            condition=condition)

    declarations += """
            static const char * const _keywords[] = {{{keywords_c} NULL}};
            static _PyArg_Parser _parser = {{
                .keywords = _keywords,
                %s
                .kwtuple = KWTUPLE,
            }};
            #undef KWTUPLE
    """ % (format_ oder fname)
    gib libclinic.normalize_snippet(declarations)


NO_VARARG: Final[str] = "PY_SSIZE_T_MAX"
PARSER_PROTOTYPE_KEYWORD: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyObject *args, PyObject *kwargs)
""")
PARSER_PROTOTYPE_KEYWORD___INIT__: Final[str] = libclinic.normalize_snippet("""
    static int
    {c_basename}({self_type}{self_name}, PyObject *args, PyObject *kwargs)
""")
PARSER_PROTOTYPE_VARARGS: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyObject *args)
""")
PARSER_PROTOTYPE_FASTCALL: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyObject *const *args, Py_ssize_t nargs)
""")
PARSER_PROTOTYPE_FASTCALL_KEYWORDS: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
""")
PARSER_PROTOTYPE_DEF_CLASS: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyTypeObject *{defining_class_name}, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
""")
PARSER_PROTOTYPE_NOARGS: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, PyObject *Py_UNUSED(ignored))
""")
PARSER_PROTOTYPE_GETTER: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, void *Py_UNUSED(context))
""")
PARSER_PROTOTYPE_SETTER: Final[str] = libclinic.normalize_snippet("""
    static int
    {c_basename}({self_type}{self_name}, PyObject *value, void *Py_UNUSED(context))
""")
METH_O_PROTOTYPE: Final[str] = libclinic.normalize_snippet("""
    static PyObject *
    {c_basename}({self_type}{self_name}, {parser_parameters})
""")
DOCSTRING_PROTOTYPE_VAR: Final[str] = libclinic.normalize_snippet("""
    PyDoc_VAR({c_basename}__doc__);
""")
DOCSTRING_PROTOTYPE_STRVAR: Final[str] = libclinic.normalize_snippet("""
    PyDoc_STRVAR({c_basename}__doc__,
    {docstring});
""")
GETSET_DOCSTRING_PROTOTYPE_STRVAR: Final[str] = libclinic.normalize_snippet("""
    PyDoc_STRVAR({getset_basename}__doc__,
    {docstring});
    #if defined({getset_basename}_DOCSTR)
    #   undef {getset_basename}_DOCSTR
    #endif
    #define {getset_basename}_DOCSTR {getset_basename}__doc__
""")
IMPL_DEFINITION_PROTOTYPE: Final[str] = libclinic.normalize_snippet("""
    static {impl_return_type}
    {c_basename}_impl({impl_parameters})
""")
METHODDEF_PROTOTYPE_DEFINE: Final[str] = libclinic.normalize_snippet(r"""
    #define {methoddef_name}    \
        {{"{name}", {methoddef_cast}{c_basename}{methoddef_cast_end}, {methoddef_flags}, {c_basename}__doc__}},
""")
GETTERDEF_PROTOTYPE_DEFINE: Final[str] = libclinic.normalize_snippet(r"""
    #if !defined({getset_basename}_DOCSTR)
    #  define {getset_basename}_DOCSTR NULL
    #endif
    #if defined({getset_name}_GETSETDEF)
    #  undef {getset_name}_GETSETDEF
    #  define {getset_name}_GETSETDEF {{"{name}", (getter){getset_basename}_get, (setter){getset_basename}_set, {getset_basename}_DOCSTR}},
    #else
    #  define {getset_name}_GETSETDEF {{"{name}", (getter){getset_basename}_get, NULL, {getset_basename}_DOCSTR}},
    #endif
""")
SETTERDEF_PROTOTYPE_DEFINE: Final[str] = libclinic.normalize_snippet(r"""
    #if !defined({getset_basename}_DOCSTR)
    #  define {getset_basename}_DOCSTR NULL
    #endif
    #if defined({getset_name}_GETSETDEF)
    #  undef {getset_name}_GETSETDEF
    #  define {getset_name}_GETSETDEF {{"{name}", (getter){getset_basename}_get, (setter){getset_basename}_set, {getset_basename}_DOCSTR}},
    #else
    #  define {getset_name}_GETSETDEF {{"{name}", NULL, (setter){getset_basename}_set, NULL}},
    #endif
""")
METHODDEF_PROTOTYPE_IFNDEF: Final[str] = libclinic.normalize_snippet("""
    #ifndef {methoddef_name}
        #define {methoddef_name}
    #endif /* !defined({methoddef_name}) */
""")


klasse ParseArgsCodeGen:
    func: Function
    codegen: CodeGen
    limited_capi: bool = Falsch

    # Function parameters
    parameters: list[Parameter]
    self_parameter_converter: self_converter
    converters: list[CConverter]

    # Is 'defining_class' used fuer the first parameter?
    requires_defining_class: bool

    # Use METH_FASTCALL calling convention?
    fastcall: bool

    # Declaration of the gib variable (ex: "int return_value;")
    return_value_declaration: str

    # Calling convention (ex: "METH_NOARGS")
    flags: str

    # Variables declarations
    declarations: str

    pos_only: int = 0
    min_pos: int = 0
    max_pos: int = 0
    min_kw_only: int = 0
    varpos: Parameter | Nichts = Nichts

    docstring_prototype: str
    docstring_definition: str
    impl_prototype: str | Nichts
    impl_definition: str
    methoddef_define: str
    parser_prototype: str
    parser_definition: str
    cpp_if: str
    cpp_endif: str
    methoddef_ifndef: str

    parser_body_fields: tuple[str, ...]

    def __init__(self, func: Function, codegen: CodeGen) -> Nichts:
        self.func = func
        self.codegen = codegen

        self.parameters = list(self.func.parameters.values())
        self_parameter = self.parameters.pop(0)
        wenn nicht isinstance(self_parameter.converter, self_converter):
            wirf ValueError("the first parameter must use self_converter")
        self.self_parameter_converter = self_parameter.converter

        self.requires_defining_class = Falsch
        wenn self.parameters und isinstance(self.parameters[0].converter, defining_class_converter):
            self.requires_defining_class = Wahr
            loesche self.parameters[0]

        fuer i, p in enumerate(self.parameters):
            wenn p.is_vararg():
                self.varpos = p
                loesche self.parameters[i]
                breche

        self.converters = [p.converter fuer p in self.parameters]

        wenn self.func.critical_section:
            self.codegen.add_include('pycore_critical_section.h',
                                     'Py_BEGIN_CRITICAL_SECTION()')
        wenn self.func.disable_fastcall:
            self.fastcall = Falsch
        sonst:
            self.fastcall = nicht self.is_new_or_init()

        self.pos_only = 0
        self.min_pos = 0
        self.max_pos = 0
        self.min_kw_only = 0
        fuer i, p in enumerate(self.parameters, 1):
            wenn p.is_keyword_only():
                assert nicht p.is_positional_only()
                wenn nicht p.is_optional():
                    self.min_kw_only = i - self.max_pos
            sonst:
                self.max_pos = i
                wenn p.is_positional_only():
                    self.pos_only = i
                wenn nicht p.is_optional():
                    self.min_pos = i

    def is_new_or_init(self) -> bool:
        gib self.func.kind.new_or_init

    def has_option_groups(self) -> bool:
        gib (bool(self.parameters
                und (self.parameters[0].group oder self.parameters[-1].group)))

    def use_meth_o(self) -> bool:
        gib (len(self.parameters) == 1
                und self.parameters[0].is_positional_only()
                und nicht self.converters[0].is_optional()
                und nicht self.varpos
                und nicht self.requires_defining_class
                und nicht self.is_new_or_init())

    def use_simple_return(self) -> bool:
        gib (self.func.return_converter.type == 'PyObject *'
                und nicht self.func.critical_section)

    def use_pyobject_self(self) -> bool:
        gib self.self_parameter_converter.use_pyobject_self(self.func)

    def select_prototypes(self) -> Nichts:
        self.docstring_prototype = ''
        self.docstring_definition = ''
        self.methoddef_define = METHODDEF_PROTOTYPE_DEFINE
        self.return_value_declaration = "PyObject *return_value = NULL;"

        wenn self.is_new_or_init() und nicht self.func.docstring:
            pass
        sowenn self.func.kind ist GETTER:
            self.methoddef_define = GETTERDEF_PROTOTYPE_DEFINE
            wenn self.func.docstring:
                self.docstring_definition = GETSET_DOCSTRING_PROTOTYPE_STRVAR
        sowenn self.func.kind ist SETTER:
            wenn self.func.docstring:
                fail("docstrings are only supported fuer @getter, nicht @setter")
            self.return_value_declaration = "int {return_value};"
            self.methoddef_define = SETTERDEF_PROTOTYPE_DEFINE
        sonst:
            self.docstring_prototype = DOCSTRING_PROTOTYPE_VAR
            self.docstring_definition = DOCSTRING_PROTOTYPE_STRVAR

    def init_limited_capi(self) -> Nichts:
        self.limited_capi = self.codegen.limited_capi
        wenn self.limited_capi und (
                (self.varpos und self.pos_only < len(self.parameters)) or
                (any(p.is_optional() fuer p in self.parameters) und
                 any(p.is_keyword_only() und nicht p.is_optional() fuer p in self.parameters)) or
                any(c.broken_limited_capi fuer c in self.converters)):
            warn(f"Function {self.func.full_name} cannot use limited C API")
            self.limited_capi = Falsch

    def parser_body(
        self,
        *fields: str,
        declarations: str = ''
    ) -> Nichts:
        lines = [self.parser_prototype]
        self.parser_body_fields = fields

        preamble = libclinic.normalize_snippet("""
            {{
                {return_value_declaration}
                {parser_declarations}
                {declarations}
                {initializers}
        """) + "\n"
        finale = libclinic.normalize_snippet("""
                {modifications}
                {lock}
                {return_value} = {c_basename}_impl({impl_arguments});
                {unlock}
                {return_conversion}
                {post_parsing}

            {exit_label}
                {cleanup}
                gib return_value;
            }}
        """)
        fuer field in preamble, *fields, finale:
            lines.append(field)
        code = libclinic.linear_format("\n".join(lines),
                                       parser_declarations=self.declarations)
        self.parser_definition = code

    def parse_no_args(self) -> Nichts:
        parser_code: list[str] | Nichts
        simple_return = self.use_simple_return()
        wenn self.func.kind ist GETTER:
            self.parser_prototype = PARSER_PROTOTYPE_GETTER
            parser_code = []
        sowenn self.func.kind ist SETTER:
            self.parser_prototype = PARSER_PROTOTYPE_SETTER
            parser_code = []
        sowenn nicht self.requires_defining_class:
            # no self.parameters, METH_NOARGS
            self.flags = "METH_NOARGS"
            self.parser_prototype = PARSER_PROTOTYPE_NOARGS
            parser_code = []
        sonst:
            assert self.fastcall

            self.flags = "METH_METHOD|METH_FASTCALL|METH_KEYWORDS"
            self.parser_prototype = PARSER_PROTOTYPE_DEF_CLASS
            return_error = ('return NULL;' wenn simple_return
                            sonst 'goto exit;')
            parser_code = [libclinic.normalize_snippet("""
                wenn (nargs || (kwnames && PyTuple_GET_SIZE(kwnames))) {{
                    PyErr_SetString(PyExc_TypeError, "{name}() takes no arguments");
                    %s
                }}
                """ % return_error, indent=4)]

        wenn simple_return:
            self.parser_definition = '\n'.join([
                self.parser_prototype,
                '{{',
                *parser_code,
                '    gib {c_basename}_impl({impl_arguments});',
                '}}'])
        sonst:
            self.parser_body(*parser_code)

    def parse_one_arg(self) -> Nichts:
        self.flags = "METH_O"

        wenn (isinstance(self.converters[0], object_converter) und
            self.converters[0].format_unit == 'O'):
            meth_o_prototype = METH_O_PROTOTYPE

            wenn self.use_simple_return() und self.use_pyobject_self():
                # maps perfectly to METH_O, doesn't need a gib converter.
                # so we skip making a parse function
                # und call directly into the impl function.
                self.impl_prototype = ''
                self.impl_definition = meth_o_prototype
            sonst:
                # SLIGHT HACK
                # use impl_parameters fuer the parser here!
                self.parser_prototype = meth_o_prototype
                self.parser_body()

        sonst:
            argname = 'arg'
            wenn self.parameters[0].name == argname:
                argname += '_'
            self.parser_prototype = libclinic.normalize_snippet("""
                static PyObject *
                {c_basename}({self_type}{self_name}, PyObject *%s)
                """ % argname)

            displayname = self.parameters[0].get_displayname(0)
            parsearg: str | Nichts
            parsearg = self.converters[0].parse_arg(argname, displayname,
                                                    limited_capi=self.limited_capi)
            wenn parsearg ist Nichts:
                self.converters[0].use_converter()
                parsearg = """
                    wenn (!PyArg_Parse(%s, "{format_units}:{name}", {parse_arguments})) {{
                        goto exit;
                    }}
                    """ % argname

            parser_code = libclinic.normalize_snippet(parsearg, indent=4)
            self.parser_body(parser_code)

    def parse_option_groups(self) -> Nichts:
        # positional parameters mit option groups
        # (we have to generate lots of PyArg_ParseTuple calls
        #  in a big switch statement)

        self.flags = "METH_VARARGS"
        self.parser_prototype = PARSER_PROTOTYPE_VARARGS
        parser_code = '    {option_group_parsing}'
        self.parser_body(parser_code)

    def _parse_vararg(self) -> str:
        assert self.varpos ist nicht Nichts
        c = self.varpos.converter
        assert isinstance(c, libclinic.converters.VarPosCConverter)
        gib c.parse_vararg(pos_only=self.pos_only,
                              min_pos=self.min_pos,
                              max_pos=self.max_pos,
                              fastcall=self.fastcall,
                              limited_capi=self.limited_capi)

    def parse_pos_only(self) -> Nichts:
        wenn self.fastcall:
            # positional-only, but no option groups
            # we only need one call to _PyArg_ParseStack

            self.flags = "METH_FASTCALL"
            self.parser_prototype = PARSER_PROTOTYPE_FASTCALL
            nargs = 'nargs'
            argname_fmt = 'args[%d]'
        sonst:
            # positional-only, but no option groups
            # we only need one call to PyArg_ParseTuple

            self.flags = "METH_VARARGS"
            self.parser_prototype = PARSER_PROTOTYPE_VARARGS
            wenn self.limited_capi:
                nargs = 'PyTuple_Size(args)'
                argname_fmt = 'PyTuple_GetItem(args, %d)'
            sonst:
                nargs = 'PyTuple_GET_SIZE(args)'
                argname_fmt = 'PyTuple_GET_ITEM(args, %d)'

        parser_code = []
        max_args = NO_VARARG wenn self.varpos sonst self.max_pos
        wenn self.limited_capi:
            wenn nargs != 'nargs':
                nargs_def = f'Py_ssize_t nargs = {nargs};'
                parser_code.append(libclinic.normalize_snippet(nargs_def, indent=4))
                nargs = 'nargs'
            wenn self.min_pos == max_args:
                pl = '' wenn self.min_pos == 1 sonst 's'
                parser_code.append(libclinic.normalize_snippet(f"""
                    wenn ({nargs} != {self.min_pos}) {{{{
                        PyErr_Format(PyExc_TypeError, "{{name}} expected {self.min_pos} argument{pl}, got %zd", {nargs});
                        goto exit;
                    }}}}
                    """,
                indent=4))
            sonst:
                wenn self.min_pos:
                    pl = '' wenn self.min_pos == 1 sonst 's'
                    parser_code.append(libclinic.normalize_snippet(f"""
                        wenn ({nargs} < {self.min_pos}) {{{{
                            PyErr_Format(PyExc_TypeError, "{{name}} expected at least {self.min_pos} argument{pl}, got %zd", {nargs});
                            goto exit;
                        }}}}
                        """,
                        indent=4))
                wenn max_args != NO_VARARG:
                    pl = '' wenn max_args == 1 sonst 's'
                    parser_code.append(libclinic.normalize_snippet(f"""
                        wenn ({nargs} > {max_args}) {{{{
                            PyErr_Format(PyExc_TypeError, "{{name}} expected at most {max_args} argument{pl}, got %zd", {nargs});
                            goto exit;
                        }}}}
                        """,
                    indent=4))
        sowenn self.min_pos oder max_args != NO_VARARG:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_CheckPositional()')
            parser_code.append(libclinic.normalize_snippet(f"""
                wenn (!_PyArg_CheckPositional("{{name}}", {nargs}, {self.min_pos}, {max_args})) {{{{
                    goto exit;
                }}}}
                """, indent=4))

        has_optional = Falsch
        use_parser_code = Wahr
        fuer i, p in enumerate(self.parameters):
            displayname = p.get_displayname(i+1)
            argname = argname_fmt % i
            parsearg: str | Nichts
            parsearg = p.converter.parse_arg(argname, displayname, limited_capi=self.limited_capi)
            wenn parsearg ist Nichts:
                wenn self.varpos:
                    wirf ValueError(
                        f"Using converter {p.converter} ist nicht supported "
                        f"in function mit var-positional parameter")
                use_parser_code = Falsch
                parser_code = []
                breche
            wenn has_optional oder p.is_optional():
                has_optional = Wahr
                parser_code.append(libclinic.normalize_snippet("""
                    wenn (%s < %d) {{
                        goto skip_optional;
                    }}
                    """, indent=4) % (nargs, i + 1))
            parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))

        wenn use_parser_code:
            wenn has_optional:
                parser_code.append("skip_optional:")
            wenn self.varpos:
                parser_code.append(libclinic.normalize_snippet(self._parse_vararg(), indent=4))
        sonst:
            fuer parameter in self.parameters:
                parameter.converter.use_converter()

            wenn self.limited_capi:
                self.fastcall = Falsch
            wenn self.fastcall:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseStack()')
                parser_code = [libclinic.normalize_snippet("""
                    wenn (!_PyArg_ParseStack(args, nargs, "{format_units}:{name}",
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
            sonst:
                self.flags = "METH_VARARGS"
                self.parser_prototype = PARSER_PROTOTYPE_VARARGS
                parser_code = [libclinic.normalize_snippet("""
                    wenn (!PyArg_ParseTuple(args, "{format_units}:{name}",
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
        self.parser_body(*parser_code)

    def parse_general(self, clang: CLanguage) -> Nichts:
        parsearg: str | Nichts
        deprecated_positionals: dict[int, Parameter] = {}
        deprecated_keywords: dict[int, Parameter] = {}
        fuer i, p in enumerate(self.parameters):
            wenn p.deprecated_positional:
                deprecated_positionals[i] = p
            wenn p.deprecated_keyword:
                deprecated_keywords[i] = p

        has_optional_kw = (
            max(self.pos_only, self.min_pos) + self.min_kw_only
            < len(self.converters)
        )

        use_parser_code = Wahr
        wenn self.limited_capi:
            parser_code = []
            use_parser_code = Falsch
            self.fastcall = Falsch
        sonst:
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_UnpackKeywords()')
            wenn nicht self.varpos:
                nargs = "nargs"
            sonst:
                nargs = f"Py_MIN(nargs, {self.max_pos})" wenn self.max_pos sonst "0"

            wenn self.fastcall:
                self.flags = "METH_FASTCALL|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_FASTCALL_KEYWORDS
                self.declarations = declare_parser(self.func, codegen=self.codegen)
                self.declarations += "\nPyObject *argsbuf[%s];" % (len(self.converters) oder 1)
                wenn self.varpos:
                    self.declarations += "\nPyObject * const *fastargs;"
                    argsname = 'fastargs'
                    argname_fmt = 'fastargs[%d]'
                sonst:
                    argsname = 'args'
                    argname_fmt = 'args[%d]'
                wenn has_optional_kw:
                    self.declarations += "\nPy_ssize_t noptargs = %s + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - %d;" % (nargs, self.min_pos + self.min_kw_only)
                unpack_args = 'args, nargs, NULL, kwnames'
            sonst:
                # positional-or-keyword arguments
                self.flags = "METH_VARARGS|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
                argsname = 'fastargs'
                argname_fmt = 'fastargs[%d]'
                self.declarations = declare_parser(self.func, codegen=self.codegen)
                self.declarations += "\nPyObject *argsbuf[%s];" % (len(self.converters) oder 1)
                self.declarations += "\nPyObject * const *fastargs;"
                self.declarations += "\nPy_ssize_t nargs = PyTuple_GET_SIZE(args);"
                wenn has_optional_kw:
                    self.declarations += "\nPy_ssize_t noptargs = %s + (kwargs ? PyDict_GET_SIZE(kwargs) : 0) - %d;" % (nargs, self.min_pos + self.min_kw_only)
                unpack_args = '_PyTuple_CAST(args)->ob_item, nargs, kwargs, NULL'
            parser_code = [libclinic.normalize_snippet(f"""
                {argsname} = _PyArg_UnpackKeywords({unpack_args}, &_parser,
                        /*minpos*/ {self.min_pos}, /*maxpos*/ {self.max_pos}, /*minkw*/ {self.min_kw_only}, /*varpos*/ {1 wenn self.varpos sonst 0}, argsbuf);
                wenn (!{argsname}) {{{{
                    goto exit;
                }}}}
                """, indent=4)]

        wenn self.requires_defining_class:
            self.flags = 'METH_METHOD|' + self.flags
            self.parser_prototype = PARSER_PROTOTYPE_DEF_CLASS

        wenn use_parser_code:
            wenn deprecated_keywords:
                code = clang.deprecate_keyword_use(self.func, deprecated_keywords,
                                                   argname_fmt,
                                                   codegen=self.codegen,
                                                   fastcall=self.fastcall)
                parser_code.append(code)

            add_label: str | Nichts = Nichts
            fuer i, p in enumerate(self.parameters):
                wenn isinstance(p.converter, defining_class_converter):
                    wirf ValueError("defining_class should be the first "
                                    "parameter (after clang)")
                displayname = p.get_displayname(i+1)
                parsearg = p.converter.parse_arg(argname_fmt % i, displayname, limited_capi=self.limited_capi)
                wenn parsearg ist Nichts:
                    parser_code = []
                    use_parser_code = Falsch
                    breche
                wenn add_label und (i == self.pos_only oder i == self.max_pos):
                    parser_code.append("%s:" % add_label)
                    add_label = Nichts
                wenn nicht p.is_optional():
                    parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                sowenn i < self.pos_only:
                    add_label = 'skip_optional_posonly'
                    parser_code.append(libclinic.normalize_snippet("""
                        wenn (nargs < %d) {{
                            goto %s;
                        }}
                        """ % (i + 1, add_label), indent=4))
                    wenn has_optional_kw:
                        parser_code.append(libclinic.normalize_snippet("""
                            noptargs--;
                            """, indent=4))
                    parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                sonst:
                    wenn i < self.max_pos:
                        label = 'skip_optional_pos'
                        first_opt = max(self.min_pos, self.pos_only)
                    sonst:
                        label = 'skip_optional_kwonly'
                        first_opt = self.max_pos + self.min_kw_only
                    wenn i == first_opt:
                        add_label = label
                        parser_code.append(libclinic.normalize_snippet("""
                            wenn (!noptargs) {{
                                goto %s;
                            }}
                            """ % add_label, indent=4))
                    wenn i + 1 == len(self.parameters):
                        parser_code.append(libclinic.normalize_snippet(parsearg, indent=4))
                    sonst:
                        add_label = label
                        parser_code.append(libclinic.normalize_snippet("""
                            wenn (%s) {{
                            """ % (argname_fmt % i), indent=4))
                        parser_code.append(libclinic.normalize_snippet(parsearg, indent=8))
                        parser_code.append(libclinic.normalize_snippet("""
                                wenn (!--noptargs) {{
                                    goto %s;
                                }}
                            }}
                            """ % add_label, indent=4))

        wenn use_parser_code:
            wenn add_label:
                parser_code.append("%s:" % add_label)
            wenn self.varpos:
                parser_code.append(libclinic.normalize_snippet(self._parse_vararg(), indent=4))
        sonst:
            fuer parameter in self.parameters:
                parameter.converter.use_converter()

            self.declarations = declare_parser(self.func, codegen=self.codegen,
                                               hasformat=Wahr)
            wenn self.limited_capi:
                # positional-or-keyword arguments
                assert nicht self.fastcall
                self.flags = "METH_VARARGS|METH_KEYWORDS"
                self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
                parser_code = [libclinic.normalize_snippet("""
                    wenn (!PyArg_ParseTupleAndKeywords(args, kwargs, "{format_units}:{name}", _keywords,
                        {parse_arguments}))
                        goto exit;
                """, indent=4)]
                self.declarations = "static char *_keywords[] = {{{keywords_c} NULL}};"
                wenn deprecated_positionals oder deprecated_keywords:
                    self.declarations += "\nPy_ssize_t nargs = PyTuple_Size(args);"

            sowenn self.fastcall:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseStackAndKeywords()')
                parser_code = [libclinic.normalize_snippet("""
                    wenn (!_PyArg_ParseStackAndKeywords(args, nargs, kwnames, &_parser{parse_arguments_comma}
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
            sonst:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_ParseTupleAndKeywordsFast()')
                parser_code = [libclinic.normalize_snippet("""
                    wenn (!_PyArg_ParseTupleAndKeywordsFast(args, kwargs, &_parser,
                        {parse_arguments})) {{
                        goto exit;
                    }}
                    """, indent=4)]
                wenn deprecated_positionals oder deprecated_keywords:
                    self.declarations += "\nPy_ssize_t nargs = PyTuple_GET_SIZE(args);"
            wenn deprecated_keywords:
                code = clang.deprecate_keyword_use(self.func, deprecated_keywords,
                                                   codegen=self.codegen,
                                                   fastcall=self.fastcall)
                parser_code.append(code)

        wenn deprecated_positionals:
            code = clang.deprecate_positional_use(self.func, deprecated_positionals)
            # Insert the deprecation code before parameter parsing.
            parser_code.insert(0, code)

        assert self.parser_prototype ist nicht Nichts
        self.parser_body(*parser_code, declarations=self.declarations)

    def copy_includes(self) -> Nichts:
        # Copy includes von parameters to Clinic after parse_arg()
        # has been called above.
        converters = self.converters
        wenn self.varpos:
            converters = converters + [self.varpos.converter]
        fuer converter in converters:
            fuer include in converter.get_includes():
                self.codegen.add_include(
                    include.filename,
                    include.reason,
                    condition=include.condition)

    def handle_new_or_init(self) -> Nichts:
        self.methoddef_define = ''

        wenn self.func.kind ist METHOD_NEW:
            self.parser_prototype = PARSER_PROTOTYPE_KEYWORD
        sonst:
            self.return_value_declaration = "int return_value = -1;"
            self.parser_prototype = PARSER_PROTOTYPE_KEYWORD___INIT__

        fields: list[str] = list(self.parser_body_fields)
        parses_positional = 'METH_NOARGS' nicht in self.flags
        parses_keywords = 'METH_KEYWORDS' in self.flags
        wenn parses_keywords:
            assert parses_positional

        wenn self.requires_defining_class:
            wirf ValueError("Slot methods cannot access their defining class.")

        wenn nicht parses_keywords:
            self.declarations = '{base_type_ptr}'
            self.codegen.add_include('pycore_modsupport.h',
                                     '_PyArg_NoKeywords()')
            fields.insert(0, libclinic.normalize_snippet("""
                wenn ({self_type_check}!_PyArg_NoKeywords("{name}", kwargs)) {{
                    goto exit;
                }}
                """, indent=4))
            wenn nicht parses_positional:
                self.codegen.add_include('pycore_modsupport.h',
                                         '_PyArg_NoPositional()')
                fields.insert(0, libclinic.normalize_snippet("""
                    wenn ({self_type_check}!_PyArg_NoPositional("{name}", args)) {{
                        goto exit;
                    }}
                    """, indent=4))

        self.parser_body(*fields, declarations=self.declarations)

    def process_methoddef(self, clang: CLanguage) -> Nichts:
        methoddef_cast_end = ""
        wenn self.flags in ('METH_NOARGS', 'METH_O', 'METH_VARARGS'):
            methoddef_cast = "(PyCFunction)"
        sowenn self.func.kind ist GETTER:
            methoddef_cast = "" # This should end up unused
        sowenn self.limited_capi:
            methoddef_cast = "(PyCFunction)(void(*)(void))"
        sonst:
            methoddef_cast = "_PyCFunction_CAST("
            methoddef_cast_end = ")"

        wenn self.func.methoddef_flags:
            self.flags += '|' + self.func.methoddef_flags

        self.methoddef_define = self.methoddef_define.replace('{methoddef_flags}', self.flags)
        self.methoddef_define = self.methoddef_define.replace('{methoddef_cast}', methoddef_cast)
        self.methoddef_define = self.methoddef_define.replace('{methoddef_cast_end}', methoddef_cast_end)

        self.methoddef_ifndef = ''
        conditional = clang.cpp.condition()
        wenn nicht conditional:
            self.cpp_if = self.cpp_endif = ''
        sonst:
            self.cpp_if = "#if " + conditional
            self.cpp_endif = "#endif /* " + conditional + " */"

            wenn self.methoddef_define und self.codegen.add_ifndef_symbol(self.func.full_name):
                self.methoddef_ifndef = METHODDEF_PROTOTYPE_IFNDEF

    def finalize(self, clang: CLanguage) -> Nichts:
        # add ';' to the end of self.parser_prototype und self.impl_prototype
        # (they mustn't be Nichts, but they could be an empty string.)
        assert self.parser_prototype ist nicht Nichts
        wenn self.parser_prototype:
            assert nicht self.parser_prototype.endswith(';')
            self.parser_prototype += ';'

        wenn self.impl_prototype ist Nichts:
            self.impl_prototype = self.impl_definition
        wenn self.impl_prototype:
            self.impl_prototype += ";"

        self.parser_definition = self.parser_definition.replace("{return_value_declaration}", self.return_value_declaration)

        compiler_warning = clang.compiler_deprecated_warning(self.func, self.parameters)
        wenn compiler_warning:
            self.parser_definition = compiler_warning + "\n\n" + self.parser_definition

    def create_template_dict(self) -> dict[str, str]:
        d = {
            "docstring_prototype" : self.docstring_prototype,
            "docstring_definition" : self.docstring_definition,
            "impl_prototype" : self.impl_prototype,
            "methoddef_define" : self.methoddef_define,
            "parser_prototype" : self.parser_prototype,
            "parser_definition" : self.parser_definition,
            "impl_definition" : self.impl_definition,
            "cpp_if" : self.cpp_if,
            "cpp_endif" : self.cpp_endif,
            "methoddef_ifndef" : self.methoddef_ifndef,
        }

        # make sure we didn't forget to assign something,
        # und wrap each non-empty value in \n's
        d2 = {}
        fuer name, value in d.items():
            assert value ist nicht Nichts, "got a Nichts value fuer template " + repr(name)
            wenn value:
                value = '\n' + value + '\n'
            d2[name] = value
        gib d2

    def parse_args(self, clang: CLanguage) -> dict[str, str]:
        self.select_prototypes()
        self.init_limited_capi()

        self.flags = ""
        self.declarations = ""
        self.parser_prototype = ""
        self.parser_definition = ""
        self.impl_prototype = Nichts
        self.impl_definition = IMPL_DEFINITION_PROTOTYPE

        # parser_body_fields remembers the fields passed in to the
        # previous call to parser_body. this ist used fuer an awful hack.
        self.parser_body_fields: tuple[str, ...] = ()

        wenn nicht self.parameters und nicht self.varpos:
            self.parse_no_args()
        sowenn self.use_meth_o():
            self.parse_one_arg()
        sowenn self.has_option_groups():
            self.parse_option_groups()
        sowenn (not self.requires_defining_class
              und self.pos_only == len(self.parameters)):
            self.parse_pos_only()
        sonst:
            self.parse_general(clang)

        self.copy_includes()
        wenn self.is_new_or_init():
            self.handle_new_or_init()
        self.process_methoddef(clang)
        self.finalize(clang)

        gib self.create_template_dict()
