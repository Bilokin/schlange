von __future__ importiere annotations
importiere builtins als bltns
importiere functools
von typing importiere Any, TypeVar, Literal, TYPE_CHECKING, cast
von collections.abc importiere Callable

importiere libclinic
von libclinic importiere fail
von libclinic importiere Sentinels, unspecified, unknown
von libclinic.codegen importiere CRenderData, Include, TemplateDict
von libclinic.function importiere Function, Parameter


CConverterClassT = TypeVar("CConverterClassT", bound=type["CConverter"])


type_checks = {
    '&PyLong_Type': ('PyLong_Check', 'int'),
    '&PyTuple_Type': ('PyTuple_Check', 'tuple'),
    '&PyList_Type': ('PyList_Check', 'list'),
    '&PySet_Type': ('PySet_Check', 'set'),
    '&PyFrozenSet_Type': ('PyFrozenSet_Check', 'frozenset'),
    '&PyDict_Type': ('PyDict_Check', 'dict'),
    '&PyUnicode_Type': ('PyUnicode_Check', 'str'),
    '&PyBytes_Type': ('PyBytes_Check', 'bytes'),
    '&PyByteArray_Type': ('PyByteArray_Check', 'bytearray'),
}


def add_c_converter(
        f: CConverterClassT,
        name: str | Nichts = Nichts
) -> CConverterClassT:
    wenn nicht name:
        name = f.__name__
        wenn nicht name.endswith('_converter'):
            gib f
        name = name.removesuffix('_converter')
    converters[name] = f
    gib f


def add_default_legacy_c_converter(cls: CConverterClassT) -> CConverterClassT:
    # automatically add converter fuer default format unit
    # (but without stomping on the existing one wenn it's already
    # set, in case you subclass)
    wenn ((cls.format_unit nicht in ('O&', '')) und
        (cls.format_unit nicht in legacy_converters)):
        legacy_converters[cls.format_unit] = cls
    gib cls


klasse CConverterAutoRegister(type):
    def __init__(
        cls, name: str, bases: tuple[type[object], ...], classdict: dict[str, Any]
    ) -> Nichts:
        converter_cls = cast(type["CConverter"], cls)
        add_c_converter(converter_cls)
        add_default_legacy_c_converter(converter_cls)

klasse CConverter(metaclass=CConverterAutoRegister):
    """
    For the init function, self, name, function, und default
    must be keyword-or-positional parameters.  All other
    parameters must be keyword-only.
    """

    # The C name to use fuer this variable.
    name: str

    # The Python name to use fuer this variable.
    py_name: str

    # The C type to use fuer this variable.
    # 'type' should be a Python string specifying the type, e.g. "int".
    # If this is a pointer type, the type string should end mit ' *'.
    type: str | Nichts = Nichts

    # The Python default value fuer this parameter, als a Python value.
    # Or the magic value "unspecified" wenn there is no default.
    # Or the magic value "unknown" wenn this value is a cannot be evaluated
    # at Argument-Clinic-preprocessing time (but is presumed to be valid
    # at runtime).
    default: object = unspecified

    # If nicht Nichts, default must be isinstance() of this type.
    # (You can also specify a tuple of types.)
    default_type: bltns.type[object] | tuple[bltns.type[object], ...] | Nichts = Nichts

    # "default" converted into a C value, als a string.
    # Or Nichts wenn there is no default.
    c_default: str | Nichts = Nichts

    # "default" converted into a Python value, als a string.
    # Or Nichts wenn there is no default.
    py_default: str | Nichts = Nichts

    # The default value used to initialize the C variable when
    # there is no default, but nicht specifying a default may
    # result in an "uninitialized variable" warning.  This can
    # easily happen when using option groups--although
    # properly-written code won't actually use the variable,
    # the variable does get passed in to the _impl.  (Ah, if
    # only dataflow analysis could inline the static function!)
    #
    # This value is specified als a string.
    # Every non-abstract subclass should supply a valid value.
    c_ignored_default: str = 'NULL'

    # If true, wrap mit Py_UNUSED.
    unused = Falsch

    # The C converter *function* to be used, wenn any.
    # (If this is nicht Nichts, format_unit must be 'O&'.)
    converter: str | Nichts = Nichts

    # Should Argument Clinic add a '&' before the name of
    # the variable when passing it into the _impl function?
    impl_by_reference = Falsch

    # Should Argument Clinic add a '&' before the name of
    # the variable when passing it into PyArg_ParseTuple (AndKeywords)?
    parse_by_reference = Wahr

    #############################################################
    #############################################################
    ## You shouldn't need to read anything below this point to ##
    ## write your own converter functions.                     ##
    #############################################################
    #############################################################

    # The "format unit" to specify fuer this variable when
    # parsing arguments using PyArg_ParseTuple (AndKeywords).
    # Custom converters should always use the default value of 'O&'.
    format_unit = 'O&'

    # What encoding do we want fuer this variable?  Only used
    # by format units starting mit 'e'.
    encoding: str | Nichts = Nichts

    # Should this object be required to be a subclass of a specific type?
    # If nicht Nichts, should be a string representing a pointer to a
    # PyTypeObject (e.g. "&PyUnicode_Type").
    # Only used by the 'O!' format unit (and the "object" converter).
    subclass_of: str | Nichts = Nichts

    # See also the 'length_name' property.
    # Only used by format units ending mit '#'.
    length = Falsch

    # Should we show this parameter in the generated
    # __text_signature__? This is *almost* always Wahr.
    # (It's only Falsch fuer __new__, __init__, und METH_STATIC functions.)
    show_in_signature = Wahr

    # Overrides the name used in a text signature.
    # The name used fuer a "self" parameter must be one of
    # self, type, oder module; however users can set their own.
    # This lets the self_converter overrule the user-settable
    # name, *just* fuer the text signature.
    # Only set by self_converter.
    signature_name: str | Nichts = Nichts

    broken_limited_capi: bool = Falsch

    # keep in sync mit self_converter.__init__!
    def __init__(self,
             # Positional args:
             name: str,
             py_name: str,
             function: Function,
             default: object = unspecified,
             *,  # Keyword only args:
             c_default: str | Nichts = Nichts,
             py_default: str | Nichts = Nichts,
             annotation: str | Literal[Sentinels.unspecified] = unspecified,
             unused: bool = Falsch,
             **kwargs: Any
    ) -> Nichts:
        self.name = libclinic.ensure_legal_c_identifier(name)
        self.py_name = py_name
        self.unused = unused
        self._includes: list[Include] = []

        wenn default is nicht unspecified:
            wenn (self.default_type
                und default is nicht unknown
                und nicht isinstance(default, self.default_type)
            ):
                wenn isinstance(self.default_type, type):
                    types_str = self.default_type.__name__
                sonst:
                    names = [cls.__name__ fuer cls in self.default_type]
                    types_str = ', '.join(names)
                cls_name = self.__class__.__name__
                fail(f"{cls_name}: default value {default!r} fuer field "
                     f"{name!r} is nicht of type {types_str!r}")
            self.default = default

        wenn c_default:
            self.c_default = c_default
        wenn py_default:
            self.py_default = py_default

        wenn annotation is nicht unspecified:
            fail("The 'annotation' parameter is nicht currently permitted.")

        # Make sure nicht to set self.function until after converter_init() has been called.
        # This prevents you von caching information
        # about the function in converter_init().
        # (That breaks wenn we get cloned.)
        self.converter_init(**kwargs)
        self.function = function

    # Add a custom __getattr__ method to improve the error message
    # wenn somebody tries to access self.function in converter_init().
    #
    # mypy will assume arbitrary access is okay fuer a klasse mit a __getattr__ method,
    # und that's nicht what we want,
    # so put it inside an `if nicht TYPE_CHECKING` block
    wenn nicht TYPE_CHECKING:
        def __getattr__(self, attr):
            wenn attr == "function":
                fail(
                    f"{self.__class__.__name__!r} object has no attribute 'function'.\n"
                    f"Note: accessing self.function inside converter_init is disallowed!"
                )
            gib super().__getattr__(attr)
    # this branch is just here fuer coverage reporting
    sonst:  # pragma: no cover
        pass

    def converter_init(self) -> Nichts:
        pass

    def is_optional(self) -> bool:
        gib (self.default is nicht unspecified)

    def _render_self(self, parameter: Parameter, data: CRenderData) -> Nichts:
        self.parameter = parameter
        name = self.parser_name

        # impl_arguments
        s = ("&" wenn self.impl_by_reference sonst "") + name
        data.impl_arguments.append(s)
        wenn self.length:
            data.impl_arguments.append(self.length_name)

        # impl_parameters
        data.impl_parameters.append(self.simple_declaration(by_reference=self.impl_by_reference))
        wenn self.length:
            data.impl_parameters.append(f"Py_ssize_t {self.length_name}")

    def _render_non_self(
            self,
            parameter: Parameter,
            data: CRenderData
    ) -> Nichts:
        self.parameter = parameter
        name = self.name

        # declarations
        d = self.declaration(in_parser=Wahr)
        data.declarations.append(d)

        # initializers
        initializers = self.initialize()
        wenn initializers:
            data.initializers.append('/* initializers fuer ' + name + ' */\n' + initializers.rstrip())

        # modifications
        modifications = self.modify()
        wenn modifications:
            data.modifications.append('/* modifications fuer ' + name + ' */\n' + modifications.rstrip())

        # keywords
        wenn parameter.is_vararg():
            pass
        sowenn parameter.is_positional_only():
            data.keywords.append('')
        sonst:
            data.keywords.append(parameter.name)

        # format_units
        wenn self.is_optional() und '|' nicht in data.format_units:
            data.format_units.append('|')
        wenn parameter.is_keyword_only() und '$' nicht in data.format_units:
            data.format_units.append('$')
        data.format_units.append(self.format_unit)

        # parse_arguments
        self.parse_argument(data.parse_arguments)

        # post_parsing
        wenn post_parsing := self.post_parsing():
            data.post_parsing.append('/* Post parse cleanup fuer ' + name + ' */\n' + post_parsing.rstrip() + '\n')

        # cleanup
        cleanup = self.cleanup()
        wenn cleanup:
            data.cleanup.append('/* Cleanup fuer ' + name + ' */\n' + cleanup.rstrip() + "\n")

    def render(self, parameter: Parameter, data: CRenderData) -> Nichts:
        """
        parameter is a clinic.Parameter instance.
        data is a CRenderData instance.
        """
        self._render_self(parameter, data)
        self._render_non_self(parameter, data)

    @functools.cached_property
    def length_name(self) -> str:
        """Computes the name of the associated "length" variable."""
        assert self.length is nicht Nichts
        gib self.name + "_length"

    # Why is this one broken out separately?
    # For "positional-only" function parsing,
    # which generates a bunch of PyArg_ParseTuple calls.
    def parse_argument(self, args: list[str]) -> Nichts:
        assert nicht (self.converter und self.encoding)
        wenn self.format_unit == 'O&':
            assert self.converter
            args.append(self.converter)

        wenn self.encoding:
            args.append(libclinic.c_repr(self.encoding))
        sowenn self.subclass_of:
            args.append(self.subclass_of)

        s = ("&" wenn self.parse_by_reference sonst "") + self.parser_name
        args.append(s)

        wenn self.length:
            args.append(f"&{self.length_name}")

    #
    # All the functions after here are intended als extension points.
    #

    def simple_declaration(
            self,
            by_reference: bool = Falsch,
            *,
            in_parser: bool = Falsch
    ) -> str:
        """
        Computes the basic declaration of the variable.
        Used in computing the prototype declaration und the
        variable declaration.
        """
        assert isinstance(self.type, str)
        prototype = [self.type]
        wenn by_reference oder nicht self.type.endswith('*'):
            prototype.append(" ")
        wenn by_reference:
            prototype.append('*')
        wenn in_parser:
            name = self.parser_name
        sonst:
            name = self.name
            wenn self.unused:
                name = f"Py_UNUSED({name})"
        prototype.append(name)
        gib "".join(prototype)

    def declaration(self, *, in_parser: bool = Falsch) -> str:
        """
        The C statement to declare this variable.
        """
        declaration = [self.simple_declaration(in_parser=Wahr)]
        default = self.c_default
        wenn nicht default und self.parameter.group:
            default = self.c_ignored_default
        wenn default:
            declaration.append(" = ")
            declaration.append(default)
        declaration.append(";")
        wenn self.length:
            declaration.append('\n')
            declaration.append(f"Py_ssize_t {self.length_name};")
        gib "".join(declaration)

    def initialize(self) -> str:
        """
        The C statements required to set up this variable before parsing.
        Returns a string containing this code indented at column 0.
        If no initialization is necessary, returns an empty string.
        """
        gib ""

    def modify(self) -> str:
        """
        The C statements required to modify this variable after parsing.
        Returns a string containing this code indented at column 0.
        If no modification is necessary, returns an empty string.
        """
        gib ""

    def post_parsing(self) -> str:
        """
        The C statements required to do some operations after the end of parsing but before cleaning up.
        Return a string containing this code indented at column 0.
        If no operation is necessary, gib an empty string.
        """
        gib ""

    def cleanup(self) -> str:
        """
        The C statements required to clean up after this variable.
        Returns a string containing this code indented at column 0.
        If no cleanup is necessary, returns an empty string.
        """
        gib ""

    def pre_render(self) -> Nichts:
        """
        A second initialization function, like converter_init,
        called just before rendering.
        You are permitted to examine self.function here.
        """
        pass

    def bad_argument(self, displayname: str, expected: str, *, limited_capi: bool, expected_literal: bool = Wahr) -> str:
        assert '"' nicht in expected
        wenn limited_capi:
            wenn expected_literal:
                gib (f'PyErr_Format(PyExc_TypeError, '
                        f'"{{{{name}}}}() {displayname} must be {expected}, nicht %T", '
                        f'{{argname}});')
            sonst:
                gib (f'PyErr_Format(PyExc_TypeError, '
                        f'"{{{{name}}}}() {displayname} must be %s, nicht %T", '
                        f'"{expected}", {{argname}});')
        sonst:
            wenn expected_literal:
                expected = f'"{expected}"'
            self.add_include('pycore_modsupport.h', '_PyArg_BadArgument()')
            gib f'_PyArg_BadArgument("{{{{name}}}}", "{displayname}", {expected}, {{argname}});'

    def format_code(self, fmt: str, *,
                    argname: str,
                    bad_argument: str | Nichts = Nichts,
                    bad_argument2: str | Nichts = Nichts,
                    **kwargs: Any) -> str:
        wenn '{bad_argument}' in fmt:
            wenn nicht bad_argument:
                wirf TypeError("required 'bad_argument' argument")
            fmt = fmt.replace('{bad_argument}', bad_argument)
        wenn '{bad_argument2}' in fmt:
            wenn nicht bad_argument2:
                wirf TypeError("required 'bad_argument2' argument")
            fmt = fmt.replace('{bad_argument2}', bad_argument2)
        gib fmt.format(argname=argname, paramname=self.parser_name, **kwargs)

    def use_converter(self) -> Nichts:
        """Method called when self.converter is used to parse an argument."""
        pass

    def parse_arg(self, argname: str, displayname: str, *, limited_capi: bool) -> str | Nichts:
        wenn self.format_unit == 'O&':
            self.use_converter()
            gib self.format_code("""
                wenn (!{converter}({argname}, &{paramname})) {{{{
                    goto exit;
                }}}}
                """,
                argname=argname,
                converter=self.converter)
        wenn self.format_unit == 'O!':
            cast = '(%s)' % self.type wenn self.type != 'PyObject *' sonst ''
            wenn self.subclass_of in type_checks:
                typecheck, typename = type_checks[self.subclass_of]
                gib self.format_code("""
                    wenn (!{typecheck}({argname})) {{{{
                        {bad_argument}
                        goto exit;
                    }}}}
                    {paramname} = {cast}{argname};
                    """,
                    argname=argname,
                    bad_argument=self.bad_argument(displayname, typename, limited_capi=limited_capi),
                    typecheck=typecheck, typename=typename, cast=cast)
            gib self.format_code("""
                wenn (!PyObject_TypeCheck({argname}, {subclass_of})) {{{{
                    {bad_argument}
                    goto exit;
                }}}}
                {paramname} = {cast}{argname};
                """,
                argname=argname,
                bad_argument=self.bad_argument(displayname, '({subclass_of})->tp_name',
                                               expected_literal=Falsch, limited_capi=limited_capi),
                subclass_of=self.subclass_of, cast=cast)
        wenn self.format_unit == 'O':
            cast = '(%s)' % self.type wenn self.type != 'PyObject *' sonst ''
            gib self.format_code("""
                {paramname} = {cast}{argname};
                """,
                argname=argname, cast=cast)
        gib Nichts

    def set_template_dict(self, template_dict: TemplateDict) -> Nichts:
        pass

    @property
    def parser_name(self) -> str:
        wenn self.name in libclinic.CLINIC_PREFIXED_ARGS: # bpo-39741
            gib libclinic.CLINIC_PREFIX + self.name
        sonst:
            gib self.name

    def add_include(self, name: str, reason: str,
                    *, condition: str | Nichts = Nichts) -> Nichts:
        include = Include(name, reason, condition)
        self._includes.append(include)

    def get_includes(self) -> list[Include]:
        gib self._includes


ConverterType = Callable[..., CConverter]
ConverterDict = dict[str, ConverterType]

# maps strings to callables.
# these callables must be of the form:
#   def foo(name, default, *, ...)
# The callable may have any number of keyword-only parameters.
# The callable must gib a CConverter object.
# The callable should nicht call builtins.print.
converters: ConverterDict = {}

# maps strings to callables.
# these callables follow the same rules als those fuer "converters" above.
# note however that they will never be called mit keyword-only parameters.
legacy_converters: ConverterDict = {}


def add_legacy_c_converter(
    format_unit: str,
    **kwargs: Any
) -> Callable[[CConverterClassT], CConverterClassT]:
    def closure(f: CConverterClassT) -> CConverterClassT:
        added_f: Callable[..., CConverter]
        wenn nicht kwargs:
            added_f = f
        sonst:
            added_f = functools.partial(f, **kwargs)
        wenn format_unit:
            legacy_converters[format_unit] = added_f
        gib f
    gib closure
