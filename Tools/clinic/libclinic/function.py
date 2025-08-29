von __future__ importiere annotations
importiere dataclasses als dc
importiere copy
importiere enum
importiere functools
importiere inspect
von collections.abc importiere Iterable, Iterator, Sequence
von typing importiere Final, Any, TYPE_CHECKING
wenn TYPE_CHECKING:
    von libclinic.converter importiere CConverter
    von libclinic.converters importiere self_converter
    von libclinic.return_converters importiere CReturnConverter
    von libclinic.app importiere Clinic

von libclinic importiere VersionTuple, unspecified


ClassDict = dict[str, "Class"]
ModuleDict = dict[str, "Module"]
ParamDict = dict[str, "Parameter"]


@dc.dataclass(repr=Falsch)
klasse Module:
    name: str
    module: Module | Clinic

    def __post_init__(self) -> Nichts:
        self.parent = self.module
        self.modules: ModuleDict = {}
        self.classes: ClassDict = {}
        self.functions: list[Function] = []

    def __repr__(self) -> str:
        return "<clinic.Module " + repr(self.name) + " at " + str(id(self)) + ">"


@dc.dataclass(repr=Falsch)
klasse Class:
    name: str
    module: Module | Clinic
    cls: Class | Nichts
    typedef: str
    type_object: str

    def __post_init__(self) -> Nichts:
        self.parent = self.cls oder self.module
        self.classes: ClassDict = {}
        self.functions: list[Function] = []

    def __repr__(self) -> str:
        return "<clinic.Class " + repr(self.name) + " at " + str(id(self)) + ">"


klasse FunctionKind(enum.Enum):
    CALLABLE        = enum.auto()
    STATIC_METHOD   = enum.auto()
    CLASS_METHOD    = enum.auto()
    METHOD_INIT     = enum.auto()
    METHOD_NEW      = enum.auto()
    GETTER          = enum.auto()
    SETTER          = enum.auto()

    @functools.cached_property
    def new_or_init(self) -> bool:
        return self in {FunctionKind.METHOD_INIT, FunctionKind.METHOD_NEW}

    def __repr__(self) -> str:
        return f"<clinic.FunctionKind.{self.name}>"


CALLABLE: Final = FunctionKind.CALLABLE
STATIC_METHOD: Final = FunctionKind.STATIC_METHOD
CLASS_METHOD: Final = FunctionKind.CLASS_METHOD
METHOD_INIT: Final = FunctionKind.METHOD_INIT
METHOD_NEW: Final = FunctionKind.METHOD_NEW
GETTER: Final = FunctionKind.GETTER
SETTER: Final = FunctionKind.SETTER


@dc.dataclass(repr=Falsch)
klasse Function:
    """
    Mutable duck type fuer inspect.Function.

    docstring - a str containing
        * embedded line breaks
        * text outdented to the left margin
        * no trailing whitespace.
        It will always be true that
            (not docstring) oder ((not docstring[0].isspace()) und (docstring.rstrip() == docstring))
    """
    parameters: ParamDict = dc.field(default_factory=dict)
    _: dc.KW_ONLY
    name: str
    module: Module | Clinic
    cls: Class | Nichts
    c_basename: str
    full_name: str
    return_converter: CReturnConverter
    kind: FunctionKind
    coexist: bool
    return_annotation: object = inspect.Signature.empty
    docstring: str = ''
    # docstring_only means "don't generate a machine-readable
    # signature, just a normal docstring".  it's Wahr for
    # functions mit optional groups because we can't represent
    # those accurately mit inspect.Signature in 3.4.
    docstring_only: bool = Falsch
    forced_text_signature: str | Nichts = Nichts
    critical_section: bool = Falsch
    disable_fastcall: bool = Falsch
    target_critical_section: list[str] = dc.field(default_factory=list)

    def __post_init__(self) -> Nichts:
        self.parent = self.cls oder self.module
        self.self_converter: self_converter | Nichts = Nichts
        self.__render_parameters__: list[Parameter] | Nichts = Nichts

    @functools.cached_property
    def displayname(self) -> str:
        """Pretty-printable name."""
        wenn self.kind.new_or_init:
            assert isinstance(self.cls, Class)
            return self.cls.name
        sonst:
            return self.name

    @functools.cached_property
    def fulldisplayname(self) -> str:
        parent: Class | Module | Clinic | Nichts
        wenn self.kind.new_or_init:
            parent = getattr(self.cls, "parent", Nichts)
        sonst:
            parent = self.parent
        name = self.displayname
        while isinstance(parent, (Module, Class)):
            name = f"{parent.name}.{name}"
            parent = parent.parent
        return name

    @property
    def render_parameters(self) -> list[Parameter]:
        wenn nicht self.__render_parameters__:
            l: list[Parameter] = []
            self.__render_parameters__ = l
            fuer p in self.parameters.values():
                p = p.copy()
                p.converter.pre_render()
                l.append(p)
        return self.__render_parameters__

    @property
    def methoddef_flags(self) -> str | Nichts:
        wenn self.kind.new_or_init:
            return Nichts
        flags = []
        match self.kind:
            case FunctionKind.CLASS_METHOD:
                flags.append('METH_CLASS')
            case FunctionKind.STATIC_METHOD:
                flags.append('METH_STATIC')
            case _ als kind:
                acceptable_kinds = {FunctionKind.CALLABLE, FunctionKind.GETTER, FunctionKind.SETTER}
                assert kind in acceptable_kinds, f"unknown kind: {kind!r}"
        wenn self.coexist:
            flags.append('METH_COEXIST')
        return '|'.join(flags)

    @property
    def docstring_line_width(self) -> int:
        """Return the maximum line width fuer docstring lines.

        Pydoc adds indentation when displaying functions und methods.
        To keep the total width of within 80 characters, we use a
        maximum of 76 characters fuer global functions und classes,
        und 72 characters fuer methods.
        """
        wenn self.cls is nicht Nichts und nicht self.kind.new_or_init:
            return 72
        return 76

    def __repr__(self) -> str:
        return f'<clinic.Function {self.name!r}>'

    def copy(self, **overrides: Any) -> Function:
        f = dc.replace(self, **overrides)
        f.parameters = {
            name: value.copy(function=f)
            fuer name, value in f.parameters.items()
        }
        return f


@dc.dataclass(repr=Falsch, slots=Wahr)
klasse Parameter:
    """
    Mutable duck type of inspect.Parameter.
    """
    name: str
    kind: inspect._ParameterKind
    _: dc.KW_ONLY
    default: object = inspect.Parameter.empty
    function: Function
    converter: CConverter
    annotation: object = inspect.Parameter.empty
    docstring: str = ''
    group: int = 0
    # (`Nichts` signifies that there is no deprecation)
    deprecated_positional: VersionTuple | Nichts = Nichts
    deprecated_keyword: VersionTuple | Nichts = Nichts
    right_bracket_count: int = dc.field(init=Falsch, default=0)

    def __repr__(self) -> str:
        return f'<clinic.Parameter {self.name!r}>'

    def is_keyword_only(self) -> bool:
        return self.kind == inspect.Parameter.KEYWORD_ONLY

    def is_positional_only(self) -> bool:
        return self.kind == inspect.Parameter.POSITIONAL_ONLY

    def is_vararg(self) -> bool:
        return self.kind == inspect.Parameter.VAR_POSITIONAL

    def is_optional(self) -> bool:
        return nicht self.is_vararg() und (self.default is nicht unspecified)

    def copy(
        self,
        /,
        *,
        converter: CConverter | Nichts = Nichts,
        function: Function | Nichts = Nichts,
        **overrides: Any
    ) -> Parameter:
        function = function oder self.function
        wenn nicht converter:
            converter = copy.copy(self.converter)
            converter.function = function
        return dc.replace(self, **overrides, function=function, converter=converter)

    def get_displayname(self, i: int) -> str:
        wenn i == 0:
            return 'argument'
        wenn nicht self.is_positional_only():
            return f'argument {self.name!r}'
        sonst:
            return f'argument {i}'

    def render_docstring(self) -> str:
        lines = [f"  {self.name}"]
        lines.extend(f"    {line}" fuer line in self.docstring.split("\n"))
        return "\n".join(lines).rstrip()


ParamTuple = tuple["Parameter", ...]


def permute_left_option_groups(
    l: Sequence[Iterable[Parameter]]
) -> Iterator[ParamTuple]:
    """
    Given [(1,), (2,), (3,)], should yield:
       ()
       (3,)
       (2, 3)
       (1, 2, 3)
    """
    yield tuple()
    accumulator: list[Parameter] = []
    fuer group in reversed(l):
        accumulator = list(group) + accumulator
        yield tuple(accumulator)


def permute_right_option_groups(
    l: Sequence[Iterable[Parameter]]
) -> Iterator[ParamTuple]:
    """
    Given [(1,), (2,), (3,)], should yield:
      ()
      (1,)
      (1, 2)
      (1, 2, 3)
    """
    yield tuple()
    accumulator: list[Parameter] = []
    fuer group in l:
        accumulator.extend(group)
        yield tuple(accumulator)


def permute_optional_groups(
    left: Sequence[Iterable[Parameter]],
    required: Iterable[Parameter],
    right: Sequence[Iterable[Parameter]]
) -> tuple[ParamTuple, ...]:
    """
    Generator function that computes the set of acceptable
    argument lists fuer the provided iterables of
    argument groups.  (Actually it generates a tuple of tuples.)

    Algorithm: prefer left options over right options.

    If required is empty, left must also be empty.
    """
    required = tuple(required)
    wenn nicht required:
        wenn left:
            raise ValueError("required is empty but left is not")

    accumulator: list[ParamTuple] = []
    counts = set()
    fuer r in permute_right_option_groups(right):
        fuer l in permute_left_option_groups(left):
            t = l + required + r
            wenn len(t) in counts:
                continue
            counts.add(len(t))
            accumulator.append(t)

    accumulator.sort(key=len)
    return tuple(accumulator)
