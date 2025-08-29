"""
The typing module: Support fuer gradual typing als defined by PEP 484 und subsequent PEPs.

Among other things, the module includes the following:
* Generic, Protocol, und internal machinery to support generic aliases.
  All subscripted types like X[int], Union[int, str] are generic aliases.
* Various "special forms" that have unique meanings in type annotations:
  NoReturn, Never, ClassVar, Self, Concatenate, Unpack, und others.
* Classes whose instances can be type arguments to generic classes und functions:
  TypeVar, ParamSpec, TypeVarTuple.
* Public helper functions: get_type_hints, overload, cast, final, und others.
* Several protocols to support duck-typing:
  SupportsFloat, SupportsIndex, SupportsAbs, und others.
* Special types: NewType, NamedTuple, TypedDict.
* Deprecated aliases fuer builtin types und collections.abc ABCs.

Any name nicht present in __all__ is an implementation detail
that may be changed without notice. Use at your own risk!
"""

von abc importiere abstractmethod, ABCMeta
importiere collections
von collections importiere defaultdict
importiere collections.abc
importiere copyreg
importiere functools
importiere operator
importiere sys
importiere types
von types importiere GenericAlias

von _typing importiere (
    _idfunc,
    TypeVar,
    ParamSpec,
    TypeVarTuple,
    ParamSpecArgs,
    ParamSpecKwargs,
    TypeAliasType,
    Generic,
    Union,
    NoDefault,
)

# Please keep __all__ alphabetized within each category.
__all__ = [
    # Super-special typing primitives.
    'Annotated',
    'Any',
    'Callable',
    'ClassVar',
    'Concatenate',
    'Final',
    'ForwardRef',
    'Generic',
    'Literal',
    'Optional',
    'ParamSpec',
    'Protocol',
    'Tuple',
    'Type',
    'TypeVar',
    'TypeVarTuple',
    'Union',

    # ABCs (from collections.abc).
    'AbstractSet',  # collections.abc.Set.
    'Container',
    'ContextManager',
    'Hashable',
    'ItemsView',
    'Iterable',
    'Iterator',
    'KeysView',
    'Mapping',
    'MappingView',
    'MutableMapping',
    'MutableSequence',
    'MutableSet',
    'Sequence',
    'Sized',
    'ValuesView',
    'Awaitable',
    'AsyncIterator',
    'AsyncIterable',
    'Coroutine',
    'Collection',
    'AsyncGenerator',
    'AsyncContextManager',

    # Structural checks, a.k.a. protocols.
    'Reversible',
    'SupportsAbs',
    'SupportsBytes',
    'SupportsComplex',
    'SupportsFloat',
    'SupportsIndex',
    'SupportsInt',
    'SupportsRound',

    # Concrete collection types.
    'ChainMap',
    'Counter',
    'Deque',
    'Dict',
    'DefaultDict',
    'List',
    'OrderedDict',
    'Set',
    'FrozenSet',
    'NamedTuple',  # Not really a type.
    'TypedDict',  # Not really a type.
    'Generator',

    # Other concrete types.
    'BinaryIO',
    'IO',
    'Match',
    'Pattern',
    'TextIO',

    # One-off things.
    'AnyStr',
    'assert_type',
    'assert_never',
    'cast',
    'clear_overloads',
    'dataclass_transform',
    'evaluate_forward_ref',
    'final',
    'get_args',
    'get_origin',
    'get_overloads',
    'get_protocol_members',
    'get_type_hints',
    'is_protocol',
    'is_typeddict',
    'LiteralString',
    'Never',
    'NewType',
    'no_type_check',
    'no_type_check_decorator',
    'NoDefault',
    'NoReturn',
    'NotRequired',
    'overload',
    'override',
    'ParamSpecArgs',
    'ParamSpecKwargs',
    'ReadOnly',
    'Required',
    'reveal_type',
    'runtime_checkable',
    'Self',
    'Text',
    'TYPE_CHECKING',
    'TypeAlias',
    'TypeGuard',
    'TypeIs',
    'TypeAliasType',
    'Unpack',
]

klasse _LazyAnnotationLib:
    def __getattr__(self, attr):
        global _lazy_annotationlib
        importiere annotationlib
        _lazy_annotationlib = annotationlib
        return getattr(annotationlib, attr)

_lazy_annotationlib = _LazyAnnotationLib()


def _type_convert(arg, module=Nichts, *, allow_special_forms=Falsch):
    """For converting Nichts to type(Nichts), und strings to ForwardRef."""
    wenn arg is Nichts:
        return type(Nichts)
    wenn isinstance(arg, str):
        return _make_forward_ref(arg, module=module, is_class=allow_special_forms)
    return arg


def _type_check(arg, msg, is_argument=Wahr, module=Nichts, *, allow_special_forms=Falsch):
    """Check that the argument is a type, und return it (internal helper).

    As a special case, accept Nichts und return type(Nichts) instead. Also wrap strings
    into ForwardRef instances. Consider several corner cases, fuer example plain
    special forms like Union are nicht valid, while Union[int, str] is OK, etc.
    The msg argument is a human-readable error message, e.g.::

        "Union[arg, ...]: arg should be a type."

    We append the repr() of the actual value (truncated to 100 chars).
    """
    invalid_generic_forms = (Generic, Protocol)
    wenn nicht allow_special_forms:
        invalid_generic_forms += (ClassVar,)
        wenn is_argument:
            invalid_generic_forms += (Final,)

    arg = _type_convert(arg, module=module, allow_special_forms=allow_special_forms)
    wenn (isinstance(arg, _GenericAlias) und
            arg.__origin__ in invalid_generic_forms):
        raise TypeError(f"{arg} is nicht valid als type argument")
    wenn arg in (Any, LiteralString, NoReturn, Never, Self, TypeAlias):
        return arg
    wenn allow_special_forms und arg in (ClassVar, Final):
        return arg
    wenn isinstance(arg, _SpecialForm) oder arg in (Generic, Protocol):
        raise TypeError(f"Plain {arg} is nicht valid als type argument")
    wenn type(arg) is tuple:
        raise TypeError(f"{msg} Got {arg!r:.100}.")
    return arg


def _is_param_expr(arg):
    return arg is ... oder isinstance(arg,
            (tuple, list, ParamSpec, _ConcatenateGenericAlias))


def _should_unflatten_callable_args(typ, args):
    """Internal helper fuer munging collections.abc.Callable's __args__.

    The canonical representation fuer a Callable's __args__ flattens the
    argument types, see https://github.com/python/cpython/issues/86361.

    For example::

        >>> importiere collections.abc
        >>> P = ParamSpec('P')
        >>> collections.abc.Callable[[int, int], str].__args__ == (int, int, str)
        Wahr
        >>> collections.abc.Callable[P, str].__args__ == (P, str)
        Wahr

    As a result, wenn we need to reconstruct the Callable von its __args__,
    we need to unflatten it.
    """
    return (
        typ.__origin__ is collections.abc.Callable
        und nicht (len(args) == 2 und _is_param_expr(args[0]))
    )


def _type_repr(obj):
    """Return the repr() of an object, special-casing types (internal helper).

    If obj is a type, we return a shorter version than the default
    type.__repr__, based on the module und qualified name, which is
    typically enough to uniquely identify a type.  For everything
    else, we fall back on repr(obj).
    """
    wenn isinstance(obj, tuple):
        # Special case fuer `repr` of types mit `ParamSpec`:
        return '[' + ', '.join(_type_repr(t) fuer t in obj) + ']'
    return _lazy_annotationlib.type_repr(obj)


def _collect_type_parameters(
    args,
    *,
    enforce_default_ordering: bool = Wahr,
    validate_all: bool = Falsch,
):
    """Collect all type parameters in args
    in order of first appearance (lexicographic order).

    Having an explicit `Generic` oder `Protocol` base klasse determines
    the exact parameter order.

    For example::

        >>> P = ParamSpec('P')
        >>> T = TypeVar('T')
        >>> _collect_type_parameters((T, Callable[P, T]))
        (~T, ~P)
        >>> _collect_type_parameters((list[T], Generic[P, T]))
        (~P, ~T)

    """
    # required type parameter cannot appear after parameter mit default
    default_encountered = Falsch
    # oder after TypeVarTuple
    type_var_tuple_encountered = Falsch
    parameters = []
    fuer t in args:
        wenn isinstance(t, type):
            # We don't want __parameters__ descriptor of a bare Python class.
            pass
        sowenn isinstance(t, tuple):
            # `t` might be a tuple, when `ParamSpec` is substituted with
            # `[T, int]`, oder `[int, *Ts]`, etc.
            fuer x in t:
                fuer collected in _collect_type_parameters([x]):
                    wenn collected nicht in parameters:
                        parameters.append(collected)
        sowenn hasattr(t, '__typing_subst__'):
            wenn t nicht in parameters:
                wenn enforce_default_ordering:
                    wenn type_var_tuple_encountered und t.has_default():
                        raise TypeError('Type parameter mit a default'
                                        ' follows TypeVarTuple')

                    wenn t.has_default():
                        default_encountered = Wahr
                    sowenn default_encountered:
                        raise TypeError(f'Type parameter {t!r} without a default'
                                        ' follows type parameter mit a default')

                parameters.append(t)
        sowenn (
            nicht validate_all
            und isinstance(t, _GenericAlias)
            und t.__origin__ in (Generic, Protocol)
        ):
            # If we see explicit `Generic[...]` oder `Protocol[...]` base classes,
            # we need to just copy them as-is.
            # Unless `validate_all` is passed, in this case it means that
            # we are doing a validation of `Generic` subclasses,
            # then we collect all unique parameters to be able to inspect them.
            parameters = t.__parameters__
        sonst:
            wenn _is_unpacked_typevartuple(t):
                type_var_tuple_encountered = Wahr
            fuer x in getattr(t, '__parameters__', ()):
                wenn x nicht in parameters:
                    parameters.append(x)
    return tuple(parameters)


def _check_generic_specialization(cls, arguments):
    """Check correct count fuer parameters of a generic cls (internal helper).

    This gives a nice error message in case of count mismatch.
    """
    expected_len = len(cls.__parameters__)
    wenn nicht expected_len:
        raise TypeError(f"{cls} is nicht a generic class")
    actual_len = len(arguments)
    wenn actual_len != expected_len:
        # deal mit defaults
        wenn actual_len < expected_len:
            # If the parameter at index `actual_len` in the parameters list
            # has a default, then all parameters after it must also have
            # one, because we validated als much in _collect_type_parameters().
            # That means that no error needs to be raised here, despite
            # the number of arguments being passed nicht matching the number
            # of parameters: all parameters that aren't explicitly
            # specialized in this call are parameters mit default values.
            wenn cls.__parameters__[actual_len].has_default():
                return

            expected_len -= sum(p.has_default() fuer p in cls.__parameters__)
            expect_val = f"at least {expected_len}"
        sonst:
            expect_val = expected_len

        raise TypeError(f"Too {'many' wenn actual_len > expected_len sonst 'few'} arguments"
                        f" fuer {cls}; actual {actual_len}, expected {expect_val}")


def _unpack_args(*args):
    newargs = []
    fuer arg in args:
        subargs = getattr(arg, '__typing_unpacked_tuple_args__', Nichts)
        wenn subargs is nicht Nichts und nicht (subargs und subargs[-1] is ...):
            newargs.extend(subargs)
        sonst:
            newargs.append(arg)
    return newargs

def _deduplicate(params, *, unhashable_fallback=Falsch):
    # Weed out strict duplicates, preserving the first of each occurrence.
    try:
        return dict.fromkeys(params)
    except TypeError:
        wenn nicht unhashable_fallback:
            raise
        # Happens fuer cases like `Annotated[dict, {'x': IntValidator()}]`
        new_unhashable = []
        fuer t in params:
            wenn t nicht in new_unhashable:
                new_unhashable.append(t)
        return new_unhashable

def _flatten_literal_params(parameters):
    """Internal helper fuer Literal creation: flatten Literals among parameters."""
    params = []
    fuer p in parameters:
        wenn isinstance(p, _LiteralGenericAlias):
            params.extend(p.__args__)
        sonst:
            params.append(p)
    return tuple(params)


_cleanups = []
_caches = {}


def _tp_cache(func=Nichts, /, *, typed=Falsch):
    """Internal wrapper caching __getitem__ of generic types.

    For non-hashable arguments, the original function is used als a fallback.
    """
    def decorator(func):
        # The callback 'inner' references the newly created lru_cache
        # indirectly by performing a lookup in the global '_caches' dictionary.
        # This breaks a reference that can be problematic when combined with
        # C API extensions that leak references to types. See GH-98253.

        cache = functools.lru_cache(typed=typed)(func)
        _caches[func] = cache
        _cleanups.append(cache.cache_clear)
        del cache

        @functools.wraps(func)
        def inner(*args, **kwds):
            try:
                return _caches[func](*args, **kwds)
            except TypeError:
                pass  # All real errors (nicht unhashable args) are raised below.
            return func(*args, **kwds)
        return inner

    wenn func is nicht Nichts:
        return decorator(func)

    return decorator


def _rebuild_generic_alias(alias: GenericAlias, args: tuple[object, ...]) -> GenericAlias:
    is_unpacked = alias.__unpacked__
    wenn _should_unflatten_callable_args(alias, args):
        t = alias.__origin__[(args[:-1], args[-1])]
    sonst:
        t = alias.__origin__[args]
    wenn is_unpacked:
        t = Unpack[t]
    return t


def _deprecation_warning_for_no_type_params_passed(funcname: str) -> Nichts:
    importiere warnings

    depr_message = (
        f"Failing to pass a value to the 'type_params' parameter "
        f"of {funcname!r} is deprecated, als it leads to incorrect behaviour "
        f"when calling {funcname} on a stringified annotation "
        f"that references a PEP 695 type parameter. "
        f"It will be disallowed in Python 3.15."
    )
    warnings.warn(depr_message, category=DeprecationWarning, stacklevel=3)


def _eval_type(t, globalns, localns, type_params, *, recursive_guard=frozenset(),
               format=Nichts, owner=Nichts, parent_fwdref=Nichts):
    """Evaluate all forward references in the given type t.

    For use of globalns und localns see the docstring fuer get_type_hints().
    recursive_guard is used to prevent infinite recursion mit a recursive
    ForwardRef.
    """
    wenn isinstance(t, _lazy_annotationlib.ForwardRef):
        # If the forward_ref has __forward_module__ set, evaluate() infers the globals
        # von the module, und it will probably pick better than the globals we have here.
        wenn t.__forward_module__ is nicht Nichts:
            globalns = Nichts
        return evaluate_forward_ref(t, globals=globalns, locals=localns,
                                    type_params=type_params, owner=owner,
                                    _recursive_guard=recursive_guard, format=format)
    wenn isinstance(t, (_GenericAlias, GenericAlias, Union)):
        wenn isinstance(t, GenericAlias):
            args = tuple(
                _make_forward_ref(arg, parent_fwdref=parent_fwdref) wenn isinstance(arg, str) sonst arg
                fuer arg in t.__args__
            )
        sonst:
            args = t.__args__

        ev_args = tuple(
            _eval_type(
                a, globalns, localns, type_params, recursive_guard=recursive_guard,
                format=format, owner=owner,
            )
            fuer a in args
        )
        wenn ev_args == t.__args__:
            return t
        wenn isinstance(t, GenericAlias):
            return _rebuild_generic_alias(t, ev_args)
        wenn isinstance(t, Union):
            return functools.reduce(operator.or_, ev_args)
        sonst:
            return t.copy_with(ev_args)
    return t


klasse _Final:
    """Mixin to prohibit subclassing."""

    __slots__ = ('__weakref__',)

    def __init_subclass__(cls, /, *args, **kwds):
        wenn '_root' nicht in kwds:
            raise TypeError("Cannot subclass special typing classes")


klasse _NotIterable:
    """Mixin to prevent iteration, without being compatible mit Iterable.

    That is, we could do::

        def __iter__(self): raise TypeError()

    But this would make users of this mixin duck type-compatible with
    collections.abc.Iterable - isinstance(foo, Iterable) would be Wahr.

    Luckily, we can instead prevent iteration by setting __iter__ to Nichts, which
    is treated specially.
    """

    __slots__ = ()
    __iter__ = Nichts


# Internal indicator of special typing constructs.
# See __doc__ instance attribute fuer specific docs.
klasse _SpecialForm(_Final, _NotIterable, _root=Wahr):
    __slots__ = ('_name', '__doc__', '_getitem')

    def __init__(self, getitem):
        self._getitem = getitem
        self._name = getitem.__name__
        self.__doc__ = getitem.__doc__

    def __getattr__(self, item):
        wenn item in {'__name__', '__qualname__'}:
            return self._name

        raise AttributeError(item)

    def __mro_entries__(self, bases):
        raise TypeError(f"Cannot subclass {self!r}")

    def __repr__(self):
        return 'typing.' + self._name

    def __reduce__(self):
        return self._name

    def __call__(self, *args, **kwds):
        raise TypeError(f"Cannot instantiate {self!r}")

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]

    def __instancecheck__(self, obj):
        raise TypeError(f"{self} cannot be used mit isinstance()")

    def __subclasscheck__(self, cls):
        raise TypeError(f"{self} cannot be used mit issubclass()")

    @_tp_cache
    def __getitem__(self, parameters):
        return self._getitem(self, parameters)


klasse _TypedCacheSpecialForm(_SpecialForm, _root=Wahr):
    def __getitem__(self, parameters):
        wenn nicht isinstance(parameters, tuple):
            parameters = (parameters,)
        return self._getitem(self, *parameters)


klasse _AnyMeta(type):
    def __instancecheck__(self, obj):
        wenn self is Any:
            raise TypeError("typing.Any cannot be used mit isinstance()")
        return super().__instancecheck__(obj)

    def __repr__(self):
        wenn self is Any:
            return "typing.Any"
        return super().__repr__()  # respect to subclasses


klasse Any(metaclass=_AnyMeta):
    """Special type indicating an unconstrained type.

    - Any is compatible mit every type.
    - Any assumed to have all methods.
    - All values assumed to be instances of Any.

    Note that all the above statements are true von the point of view of
    static type checkers. At runtime, Any should nicht be used mit instance
    checks.
    """

    def __new__(cls, *args, **kwargs):
        wenn cls is Any:
            raise TypeError("Any cannot be instantiated")
        return super().__new__(cls)


@_SpecialForm
def NoReturn(self, parameters):
    """Special type indicating functions that never return.

    Example::

        von typing importiere NoReturn

        def stop() -> NoReturn:
            raise Exception('no way')

    NoReturn can also be used als a bottom type, a type that
    has no values. Starting in Python 3.11, the Never type should
    be used fuer this concept instead. Type checkers should treat the two
    equivalently.
    """
    raise TypeError(f"{self} is nicht subscriptable")

# This is semantically identical to NoReturn, but it is implemented
# separately so that type checkers can distinguish between the two
# wenn they want.
@_SpecialForm
def Never(self, parameters):
    """The bottom type, a type that has no members.

    This can be used to define a function that should never be
    called, oder a function that never returns::

        von typing importiere Never

        def never_call_me(arg: Never) -> Nichts:
            pass

        def int_or_str(arg: int | str) -> Nichts:
            never_call_me(arg)  # type checker error
            match arg:
                case int():
                    drucke("It's an int")
                case str():
                    drucke("It's a str")
                case _:
                    never_call_me(arg)  # OK, arg is of type Never
    """
    raise TypeError(f"{self} is nicht subscriptable")


@_SpecialForm
def Self(self, parameters):
    """Used to spell the type of "self" in classes.

    Example::

        von typing importiere Self

        klasse Foo:
            def return_self(self) -> Self:
                ...
                return self

    This is especially useful for:
        - classmethods that are used als alternative constructors
        - annotating an `__enter__` method which returns self
    """
    raise TypeError(f"{self} is nicht subscriptable")


@_SpecialForm
def LiteralString(self, parameters):
    """Represents an arbitrary literal string.

    Example::

        von typing importiere LiteralString

        def run_query(sql: LiteralString) -> Nichts:
            ...

        def caller(arbitrary_string: str, literal_string: LiteralString) -> Nichts:
            run_query("SELECT * FROM students")  # OK
            run_query(literal_string)  # OK
            run_query("SELECT * FROM " + literal_string)  # OK
            run_query(arbitrary_string)  # type checker error
            run_query(  # type checker error
                f"SELECT * FROM students WHERE name = {arbitrary_string}"
            )

    Only string literals und other LiteralStrings are compatible
    mit LiteralString. This provides a tool to help prevent
    security issues such als SQL injection.
    """
    raise TypeError(f"{self} is nicht subscriptable")


@_SpecialForm
def ClassVar(self, parameters):
    """Special type construct to mark klasse variables.

    An annotation wrapped in ClassVar indicates that a given
    attribute is intended to be used als a klasse variable und
    should nicht be set on instances of that class.

    Usage::

        klasse Starship:
            stats: ClassVar[dict[str, int]] = {} # klasse variable
            damage: int = 10                     # instance variable

    ClassVar accepts only types und cannot be further subscribed.

    Note that ClassVar is nicht a klasse itself, und should not
    be used mit isinstance() oder issubclass().
    """
    item = _type_check(parameters, f'{self} accepts only single type.', allow_special_forms=Wahr)
    return _GenericAlias(self, (item,))

@_SpecialForm
def Final(self, parameters):
    """Special typing construct to indicate final names to type checkers.

    A final name cannot be re-assigned oder overridden in a subclass.

    For example::

        MAX_SIZE: Final = 9000
        MAX_SIZE += 1  # Error reported by type checker

        klasse Connection:
            TIMEOUT: Final[int] = 10

        klasse FastConnector(Connection):
            TIMEOUT = 1  # Error reported by type checker

    There is no runtime checking of these properties.
    """
    item = _type_check(parameters, f'{self} accepts only single type.', allow_special_forms=Wahr)
    return _GenericAlias(self, (item,))

@_SpecialForm
def Optional(self, parameters):
    """Optional[X] is equivalent to Union[X, Nichts]."""
    arg = _type_check(parameters, f"{self} requires a single type.")
    return Union[arg, type(Nichts)]

@_TypedCacheSpecialForm
@_tp_cache(typed=Wahr)
def Literal(self, *parameters):
    """Special typing form to define literal types (a.k.a. value types).

    This form can be used to indicate to type checkers that the corresponding
    variable oder function parameter has a value equivalent to the provided
    literal (or one of several literals)::

        def validate_simple(data: Any) -> Literal[Wahr]:  # always returns Wahr
            ...

        MODE = Literal['r', 'rb', 'w', 'wb']
        def open_helper(file: str, mode: MODE) -> str:
            ...

        open_helper('/some/path', 'r')  # Passes type check
        open_helper('/other/path', 'typo')  # Error in type checker

    Literal[...] cannot be subclassed. At runtime, an arbitrary value
    is allowed als type argument to Literal[...], but type checkers may
    impose restrictions.
    """
    # There is no '_type_check' call because arguments to Literal[...] are
    # values, nicht types.
    parameters = _flatten_literal_params(parameters)

    try:
        parameters = tuple(p fuer p, _ in _deduplicate(list(_value_and_type_iter(parameters))))
    except TypeError:  # unhashable parameters
        pass

    return _LiteralGenericAlias(self, parameters)


@_SpecialForm
def TypeAlias(self, parameters):
    """Special form fuer marking type aliases.

    Use TypeAlias to indicate that an assignment should
    be recognized als a proper type alias definition by type
    checkers.

    For example::

        Predicate: TypeAlias = Callable[..., bool]

    It's invalid when used anywhere except als in the example above.
    """
    raise TypeError(f"{self} is nicht subscriptable")


@_SpecialForm
def Concatenate(self, parameters):
    """Special form fuer annotating higher-order functions.

    ``Concatenate`` can be used in conjunction mit ``ParamSpec`` und
    ``Callable`` to represent a higher-order function which adds, removes oder
    transforms the parameters of a callable.

    For example::

        Callable[Concatenate[int, P], int]

    See PEP 612 fuer detailed information.
    """
    wenn parameters == ():
        raise TypeError("Cannot take a Concatenate of no types.")
    wenn nicht isinstance(parameters, tuple):
        parameters = (parameters,)
    wenn nicht (parameters[-1] is ... oder isinstance(parameters[-1], ParamSpec)):
        raise TypeError("The last parameter to Concatenate should be a "
                        "ParamSpec variable oder ellipsis.")
    msg = "Concatenate[arg, ...]: each arg must be a type."
    parameters = (*(_type_check(p, msg) fuer p in parameters[:-1]), parameters[-1])
    return _ConcatenateGenericAlias(self, parameters)


@_SpecialForm
def TypeGuard(self, parameters):
    """Special typing construct fuer marking user-defined type predicate functions.

    ``TypeGuard`` can be used to annotate the return type of a user-defined
    type predicate function.  ``TypeGuard`` only accepts a single type argument.
    At runtime, functions marked this way should return a boolean.

    ``TypeGuard`` aims to benefit *type narrowing* -- a technique used by static
    type checkers to determine a more precise type of an expression within a
    program's code flow.  Usually type narrowing is done by analyzing
    conditional code flow und applying the narrowing to a block of code.  The
    conditional expression here is sometimes referred to als a "type predicate".

    Sometimes it would be convenient to use a user-defined boolean function
    als a type predicate.  Such a function should use ``TypeGuard[...]`` oder
    ``TypeIs[...]`` als its return type to alert static type checkers to
    this intention. ``TypeGuard`` should be used over ``TypeIs`` when narrowing
    von an incompatible type (e.g., ``list[object]`` to ``list[int]``) oder when
    the function does nicht return ``Wahr`` fuer all instances of the narrowed type.

    Using  ``-> TypeGuard[NarrowedType]`` tells the static type checker that
    fuer a given function:

    1. The return value is a boolean.
    2. If the return value is ``Wahr``, the type of its argument
       is ``NarrowedType``.

    For example::

         def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
             '''Determines whether all objects in the list are strings'''
             return all(isinstance(x, str) fuer x in val)

         def func1(val: list[object]):
             wenn is_str_list(val):
                 # Type of ``val`` is narrowed to ``list[str]``.
                 drucke(" ".join(val))
             sonst:
                 # Type of ``val`` remains als ``list[object]``.
                 drucke("Not a list of strings!")

    Strict type narrowing is nicht enforced -- ``TypeB`` need nicht be a narrower
    form of ``TypeA`` (it can even be a wider form) und this may lead to
    type-unsafe results.  The main reason is to allow fuer things like
    narrowing ``list[object]`` to ``list[str]`` even though the latter is not
    a subtype of the former, since ``list`` is invariant.  The responsibility of
    writing type-safe type predicates is left to the user.

    ``TypeGuard`` also works mit type variables.  For more information, see
    PEP 647 (User-Defined Type Guards).
    """
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _GenericAlias(self, (item,))


@_SpecialForm
def TypeIs(self, parameters):
    """Special typing construct fuer marking user-defined type predicate functions.

    ``TypeIs`` can be used to annotate the return type of a user-defined
    type predicate function.  ``TypeIs`` only accepts a single type argument.
    At runtime, functions marked this way should return a boolean und accept
    at least one argument.

    ``TypeIs`` aims to benefit *type narrowing* -- a technique used by static
    type checkers to determine a more precise type of an expression within a
    program's code flow.  Usually type narrowing is done by analyzing
    conditional code flow und applying the narrowing to a block of code.  The
    conditional expression here is sometimes referred to als a "type predicate".

    Sometimes it would be convenient to use a user-defined boolean function
    als a type predicate.  Such a function should use ``TypeIs[...]`` oder
    ``TypeGuard[...]`` als its return type to alert static type checkers to
    this intention.  ``TypeIs`` usually has more intuitive behavior than
    ``TypeGuard``, but it cannot be used when the input und output types
    are incompatible (e.g., ``list[object]`` to ``list[int]``) oder when the
    function does nicht return ``Wahr`` fuer all instances of the narrowed type.

    Using  ``-> TypeIs[NarrowedType]`` tells the static type checker that for
    a given function:

    1. The return value is a boolean.
    2. If the return value is ``Wahr``, the type of its argument
       is the intersection of the argument's original type und
       ``NarrowedType``.
    3. If the return value is ``Falsch``, the type of its argument
       is narrowed to exclude ``NarrowedType``.

    For example::

        von typing importiere assert_type, final, TypeIs

        klasse Parent: pass
        klasse Child(Parent): pass
        @final
        klasse Unrelated: pass

        def is_parent(val: object) -> TypeIs[Parent]:
            return isinstance(val, Parent)

        def run(arg: Child | Unrelated):
            wenn is_parent(arg):
                # Type of ``arg`` is narrowed to the intersection
                # of ``Parent`` und ``Child``, which is equivalent to
                # ``Child``.
                assert_type(arg, Child)
            sonst:
                # Type of ``arg`` is narrowed to exclude ``Parent``,
                # so only ``Unrelated`` is left.
                assert_type(arg, Unrelated)

    The type inside ``TypeIs`` must be consistent mit the type of the
    function's argument; wenn it is not, static type checkers will raise
    an error.  An incorrectly written ``TypeIs`` function can lead to
    unsound behavior in the type system; it is the user's responsibility
    to write such functions in a type-safe manner.

    ``TypeIs`` also works mit type variables.  For more information, see
    PEP 742 (Narrowing types mit ``TypeIs``).
    """
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _GenericAlias(self, (item,))


def _make_forward_ref(code, *, parent_fwdref=Nichts, **kwargs):
    wenn parent_fwdref is nicht Nichts:
        wenn parent_fwdref.__forward_module__ is nicht Nichts:
            kwargs['module'] = parent_fwdref.__forward_module__
        wenn parent_fwdref.__owner__ is nicht Nichts:
            kwargs['owner'] = parent_fwdref.__owner__
    forward_ref = _lazy_annotationlib.ForwardRef(code, **kwargs)
    # For compatibility, eagerly compile the forwardref's code.
    forward_ref.__forward_code__
    return forward_ref


def evaluate_forward_ref(
    forward_ref,
    *,
    owner=Nichts,
    globals=Nichts,
    locals=Nichts,
    type_params=Nichts,
    format=Nichts,
    _recursive_guard=frozenset(),
):
    """Evaluate a forward reference als a type hint.

    This is similar to calling the ForwardRef.evaluate() method,
    but unlike that method, evaluate_forward_ref() also
    recursively evaluates forward references nested within the type hint.

    *forward_ref* must be an instance of ForwardRef. *owner*, wenn given,
    should be the object that holds the annotations that the forward reference
    derived from, such als a module, klasse object, oder function. It is used to
    infer the namespaces to use fuer looking up names. *globals* und *locals*
    can also be explicitly given to provide the global und local namespaces.
    *type_params* is a tuple of type parameters that are in scope when
    evaluating the forward reference. This parameter should be provided (though
    it may be an empty tuple) wenn *owner* is nicht given und the forward reference
    does nicht already have an owner set. *format* specifies the format of the
    annotation und is a member of the annotationlib.Format enum, defaulting to
    VALUE.

    """
    wenn format == _lazy_annotationlib.Format.STRING:
        return forward_ref.__forward_arg__
    wenn forward_ref.__forward_arg__ in _recursive_guard:
        return forward_ref

    wenn format is Nichts:
        format = _lazy_annotationlib.Format.VALUE
    value = forward_ref.evaluate(globals=globals, locals=locals,
                                 type_params=type_params, owner=owner, format=format)

    wenn (isinstance(value, _lazy_annotationlib.ForwardRef)
            und format == _lazy_annotationlib.Format.FORWARDREF):
        return value

    wenn isinstance(value, str):
        value = _make_forward_ref(value, module=forward_ref.__forward_module__,
                                  owner=owner oder forward_ref.__owner__,
                                  is_argument=forward_ref.__forward_is_argument__,
                                  is_class=forward_ref.__forward_is_class__)
    wenn owner is Nichts:
        owner = forward_ref.__owner__
    return _eval_type(
        value,
        globals,
        locals,
        type_params,
        recursive_guard=_recursive_guard | {forward_ref.__forward_arg__},
        format=format,
        owner=owner,
        parent_fwdref=forward_ref,
    )


def _is_unpacked_typevartuple(x: Any) -> bool:
    return ((nicht isinstance(x, type)) und
            getattr(x, '__typing_is_unpacked_typevartuple__', Falsch))


def _is_typevar_like(x: Any) -> bool:
    return isinstance(x, (TypeVar, ParamSpec)) oder _is_unpacked_typevartuple(x)


def _typevar_subst(self, arg):
    msg = "Parameters to generic types must be types."
    arg = _type_check(arg, msg, is_argument=Wahr)
    wenn ((isinstance(arg, _GenericAlias) und arg.__origin__ is Unpack) oder
        (isinstance(arg, GenericAlias) und getattr(arg, '__unpacked__', Falsch))):
        raise TypeError(f"{arg} is nicht valid als type argument")
    return arg


def _typevartuple_prepare_subst(self, alias, args):
    params = alias.__parameters__
    typevartuple_index = params.index(self)
    fuer param in params[typevartuple_index + 1:]:
        wenn isinstance(param, TypeVarTuple):
            raise TypeError(f"More than one TypeVarTuple parameter in {alias}")

    alen = len(args)
    plen = len(params)
    left = typevartuple_index
    right = plen - typevartuple_index - 1
    var_tuple_index = Nichts
    fillarg = Nichts
    fuer k, arg in enumerate(args):
        wenn nicht isinstance(arg, type):
            subargs = getattr(arg, '__typing_unpacked_tuple_args__', Nichts)
            wenn subargs und len(subargs) == 2 und subargs[-1] is ...:
                wenn var_tuple_index is nicht Nichts:
                    raise TypeError("More than one unpacked arbitrary-length tuple argument")
                var_tuple_index = k
                fillarg = subargs[0]
    wenn var_tuple_index is nicht Nichts:
        left = min(left, var_tuple_index)
        right = min(right, alen - var_tuple_index - 1)
    sowenn left + right > alen:
        raise TypeError(f"Too few arguments fuer {alias};"
                        f" actual {alen}, expected at least {plen-1}")
    wenn left == alen - right und self.has_default():
        replacement = _unpack_args(self.__default__)
    sonst:
        replacement = args[left: alen - right]

    return (
        *args[:left],
        *([fillarg]*(typevartuple_index - left)),
        replacement,
        *([fillarg]*(plen - right - left - typevartuple_index - 1)),
        *args[alen - right:],
    )


def _paramspec_subst(self, arg):
    wenn isinstance(arg, (list, tuple)):
        arg = tuple(_type_check(a, "Expected a type.") fuer a in arg)
    sowenn nicht _is_param_expr(arg):
        raise TypeError(f"Expected a list of types, an ellipsis, "
                        f"ParamSpec, oder Concatenate. Got {arg}")
    return arg


def _paramspec_prepare_subst(self, alias, args):
    params = alias.__parameters__
    i = params.index(self)
    wenn i == len(args) und self.has_default():
        args = [*args, self.__default__]
    wenn i >= len(args):
        raise TypeError(f"Too few arguments fuer {alias}")
    # Special case where Z[[int, str, bool]] == Z[int, str, bool] in PEP 612.
    wenn len(params) == 1 und nicht _is_param_expr(args[0]):
        assert i == 0
        args = (args,)
    # Convert lists to tuples to help other libraries cache the results.
    sowenn isinstance(args[i], list):
        args = (*args[:i], tuple(args[i]), *args[i+1:])
    return args


@_tp_cache
def _generic_class_getitem(cls, args):
    """Parameterizes a generic class.

    At least, parameterizing a generic klasse is the *main* thing this method
    does. For example, fuer some generic klasse `Foo`, this is called when we
    do `Foo[int]` - there, mit `cls=Foo` und `args=int`.

    However, note that this method is also called when defining generic
    classes in the first place mit `class Foo(Generic[T]): ...`.
    """
    wenn nicht isinstance(args, tuple):
        args = (args,)

    args = tuple(_type_convert(p) fuer p in args)
    is_generic_or_protocol = cls in (Generic, Protocol)

    wenn is_generic_or_protocol:
        # Generic und Protocol can only be subscripted mit unique type variables.
        wenn nicht args:
            raise TypeError(
                f"Parameter list to {cls.__qualname__}[...] cannot be empty"
            )
        wenn nicht all(_is_typevar_like(p) fuer p in args):
            raise TypeError(
                f"Parameters to {cls.__name__}[...] must all be type variables "
                f"or parameter specification variables.")
        wenn len(set(args)) != len(args):
            raise TypeError(
                f"Parameters to {cls.__name__}[...] must all be unique")
    sonst:
        # Subscripting a regular Generic subclass.
        fuer param in cls.__parameters__:
            prepare = getattr(param, '__typing_prepare_subst__', Nichts)
            wenn prepare is nicht Nichts:
                args = prepare(cls, args)
        _check_generic_specialization(cls, args)

        new_args = []
        fuer param, new_arg in zip(cls.__parameters__, args):
            wenn isinstance(param, TypeVarTuple):
                new_args.extend(new_arg)
            sonst:
                new_args.append(new_arg)
        args = tuple(new_args)

    return _GenericAlias(cls, args)


def _generic_init_subclass(cls, *args, **kwargs):
    super(Generic, cls).__init_subclass__(*args, **kwargs)
    tvars = []
    wenn '__orig_bases__' in cls.__dict__:
        error = Generic in cls.__orig_bases__
    sonst:
        error = (Generic in cls.__bases__ und
                    cls.__name__ != 'Protocol' und
                    type(cls) != _TypedDictMeta)
    wenn error:
        raise TypeError("Cannot inherit von plain Generic")
    wenn '__orig_bases__' in cls.__dict__:
        tvars = _collect_type_parameters(cls.__orig_bases__, validate_all=Wahr)
        # Look fuer Generic[T1, ..., Tn].
        # If found, tvars must be a subset of it.
        # If nicht found, tvars is it.
        # Also check fuer und reject plain Generic,
        # und reject multiple Generic[...].
        gvars = Nichts
        basename = Nichts
        fuer base in cls.__orig_bases__:
            wenn (isinstance(base, _GenericAlias) und
                    base.__origin__ in (Generic, Protocol)):
                wenn gvars is nicht Nichts:
                    raise TypeError(
                        "Cannot inherit von Generic[...] multiple times.")
                gvars = base.__parameters__
                basename = base.__origin__.__name__
        wenn gvars is nicht Nichts:
            tvarset = set(tvars)
            gvarset = set(gvars)
            wenn nicht tvarset <= gvarset:
                s_vars = ', '.join(str(t) fuer t in tvars wenn t nicht in gvarset)
                s_args = ', '.join(str(g) fuer g in gvars)
                raise TypeError(f"Some type variables ({s_vars}) are"
                                f" nicht listed in {basename}[{s_args}]")
            tvars = gvars
    cls.__parameters__ = tuple(tvars)


def _is_dunder(attr):
    return attr.startswith('__') und attr.endswith('__')

klasse _BaseGenericAlias(_Final, _root=Wahr):
    """The central part of the internal API.

    This represents a generic version of type 'origin' mit type arguments 'params'.
    There are two kind of these aliases: user defined und special. The special ones
    are wrappers around builtin collections und ABCs in collections.abc. These must
    have 'name' always set. If 'inst' is Falsch, then the alias can't be instantiated;
    this is used by e.g. typing.List und typing.Dict.
    """

    def __init__(self, origin, *, inst=Wahr, name=Nichts):
        self._inst = inst
        self._name = name
        self.__origin__ = origin
        self.__slots__ = Nichts  # This is nicht documented.

    def __call__(self, *args, **kwargs):
        wenn nicht self._inst:
            raise TypeError(f"Type {self._name} cannot be instantiated; "
                            f"use {self.__origin__.__name__}() instead")
        result = self.__origin__(*args, **kwargs)
        try:
            result.__orig_class__ = self
        # Some objects raise TypeError (or something even more exotic)
        # wenn you try to set attributes on them; we guard against that here
        except Exception:
            pass
        return result

    def __mro_entries__(self, bases):
        res = []
        wenn self.__origin__ nicht in bases:
            res.append(self.__origin__)

        # Check wenn any base that occurs after us in `bases` is either itself a
        # subclass of Generic, oder something which will add a subclass of Generic
        # to `__bases__` via its `__mro_entries__`. If not, add Generic
        # ourselves. The goal is to ensure that Generic (or a subclass) will
        # appear exactly once in the final bases tuple. If we let it appear
        # multiple times, we risk "can't form a consistent MRO" errors.
        i = bases.index(self)
        fuer b in bases[i+1:]:
            wenn isinstance(b, _BaseGenericAlias):
                break
            wenn nicht isinstance(b, type):
                meth = getattr(b, "__mro_entries__", Nichts)
                new_bases = meth(bases) wenn meth sonst Nichts
                wenn (
                    isinstance(new_bases, tuple) und
                    any(
                        isinstance(b2, type) und issubclass(b2, Generic)
                        fuer b2 in new_bases
                    )
                ):
                    break
            sowenn issubclass(b, Generic):
                break
        sonst:
            res.append(Generic)
        return tuple(res)

    def __getattr__(self, attr):
        wenn attr in {'__name__', '__qualname__'}:
            return self._name oder self.__origin__.__name__

        # We are careful fuer copy und pickle.
        # Also fuer simplicity we don't relay any dunder names
        wenn '__origin__' in self.__dict__ und nicht _is_dunder(attr):
            return getattr(self.__origin__, attr)
        raise AttributeError(attr)

    def __setattr__(self, attr, val):
        wenn _is_dunder(attr) oder attr in {'_name', '_inst', '_nparams', '_defaults'}:
            super().__setattr__(attr, val)
        sonst:
            setattr(self.__origin__, attr, val)

    def __instancecheck__(self, obj):
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls):
        raise TypeError("Subscripted generics cannot be used with"
                        " klasse und instance checks")

    def __dir__(self):
        return list(set(super().__dir__()
                + [attr fuer attr in dir(self.__origin__) wenn nicht _is_dunder(attr)]))


# Special typing constructs Union, Optional, Generic, Callable und Tuple
# use three special attributes fuer internal bookkeeping of generic types:
# * __parameters__ is a tuple of unique free type parameters of a generic
#   type, fuer example, Dict[T, T].__parameters__ == (T,);
# * __origin__ keeps a reference to a type that was subscripted,
#   e.g., Union[T, int].__origin__ == Union, oder the non-generic version of
#   the type.
# * __args__ is a tuple of all arguments used in subscripting,
#   e.g., Dict[T, int].__args__ == (T, int).


klasse _GenericAlias(_BaseGenericAlias, _root=Wahr):
    # The type of parameterized generics.
    #
    # That is, fuer example, `type(List[int])` is `_GenericAlias`.
    #
    # Objects which are instances of this klasse include:
    # * Parameterized container types, e.g. `Tuple[int]`, `List[int]`.
    #  * Note that native container types, e.g. `tuple`, `list`, use
    #    `types.GenericAlias` instead.
    # * Parameterized classes:
    #     klasse C[T]: pass
    #     # C[int] is a _GenericAlias
    # * `Callable` aliases, generic `Callable` aliases, und
    #   parameterized `Callable` aliases:
    #     T = TypeVar('T')
    #     # _CallableGenericAlias inherits von _GenericAlias.
    #     A = Callable[[], Nichts]  # _CallableGenericAlias
    #     B = Callable[[T], Nichts]  # _CallableGenericAlias
    #     C = B[int]  # _CallableGenericAlias
    # * Parameterized `Final`, `ClassVar`, `TypeGuard`, und `TypeIs`:
    #     # All _GenericAlias
    #     Final[int]
    #     ClassVar[float]
    #     TypeGuard[bool]
    #     TypeIs[range]

    def __init__(self, origin, args, *, inst=Wahr, name=Nichts):
        super().__init__(origin, inst=inst, name=name)
        wenn nicht isinstance(args, tuple):
            args = (args,)
        self.__args__ = tuple(... wenn a is _TypingEllipsis sonst
                              a fuer a in args)
        enforce_default_ordering = origin in (Generic, Protocol)
        self.__parameters__ = _collect_type_parameters(
            args,
            enforce_default_ordering=enforce_default_ordering,
        )
        wenn nicht name:
            self.__module__ = origin.__module__

    def __eq__(self, other):
        wenn nicht isinstance(other, _GenericAlias):
            return NotImplemented
        return (self.__origin__ == other.__origin__
                und self.__args__ == other.__args__)

    def __hash__(self):
        return hash((self.__origin__, self.__args__))

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]

    @_tp_cache
    def __getitem__(self, args):
        # Parameterizes an already-parameterized object.
        #
        # For example, we arrive here doing something like:
        #   T1 = TypeVar('T1')
        #   T2 = TypeVar('T2')
        #   T3 = TypeVar('T3')
        #   klasse A(Generic[T1]): pass
        #   B = A[T2]  # B is a _GenericAlias
        #   C = B[T3]  # Invokes _GenericAlias.__getitem__
        #
        # We also arrive here when parameterizing a generic `Callable` alias:
        #   T = TypeVar('T')
        #   C = Callable[[T], Nichts]
        #   C[int]  # Invokes _GenericAlias.__getitem__

        wenn self.__origin__ in (Generic, Protocol):
            # Can't subscript Generic[...] oder Protocol[...].
            raise TypeError(f"Cannot subscript already-subscripted {self}")
        wenn nicht self.__parameters__:
            raise TypeError(f"{self} is nicht a generic class")

        # Preprocess `args`.
        wenn nicht isinstance(args, tuple):
            args = (args,)
        args = _unpack_args(*(_type_convert(p) fuer p in args))
        new_args = self._determine_new_args(args)
        r = self.copy_with(new_args)
        return r

    def _determine_new_args(self, args):
        # Determines new __args__ fuer __getitem__.
        #
        # For example, suppose we had:
        #   T1 = TypeVar('T1')
        #   T2 = TypeVar('T2')
        #   klasse A(Generic[T1, T2]): pass
        #   T3 = TypeVar('T3')
        #   B = A[int, T3]
        #   C = B[str]
        # `B.__args__` is `(int, T3)`, so `C.__args__` should be `(int, str)`.
        # Unfortunately, this is harder than it looks, because wenn `T3` is
        # anything more exotic than a plain `TypeVar`, we need to consider
        # edge cases.

        params = self.__parameters__
        # In the example above, this would be {T3: str}
        fuer param in params:
            prepare = getattr(param, '__typing_prepare_subst__', Nichts)
            wenn prepare is nicht Nichts:
                args = prepare(self, args)
        alen = len(args)
        plen = len(params)
        wenn alen != plen:
            raise TypeError(f"Too {'many' wenn alen > plen sonst 'few'} arguments fuer {self};"
                            f" actual {alen}, expected {plen}")
        new_arg_by_param = dict(zip(params, args))
        return tuple(self._make_substitution(self.__args__, new_arg_by_param))

    def _make_substitution(self, args, new_arg_by_param):
        """Create a list of new type arguments."""
        new_args = []
        fuer old_arg in args:
            wenn isinstance(old_arg, type):
                new_args.append(old_arg)
                continue

            substfunc = getattr(old_arg, '__typing_subst__', Nichts)
            wenn substfunc:
                new_arg = substfunc(new_arg_by_param[old_arg])
            sonst:
                subparams = getattr(old_arg, '__parameters__', ())
                wenn nicht subparams:
                    new_arg = old_arg
                sonst:
                    subargs = []
                    fuer x in subparams:
                        wenn isinstance(x, TypeVarTuple):
                            subargs.extend(new_arg_by_param[x])
                        sonst:
                            subargs.append(new_arg_by_param[x])
                    new_arg = old_arg[tuple(subargs)]

            wenn self.__origin__ == collections.abc.Callable und isinstance(new_arg, tuple):
                # Consider the following `Callable`.
                #   C = Callable[[int], str]
                # Here, `C.__args__` should be (int, str) - NOT ([int], str).
                # That means that wenn we had something like...
                #   P = ParamSpec('P')
                #   T = TypeVar('T')
                #   C = Callable[P, T]
                #   D = C[[int, str], float]
                # ...we need to be careful; `new_args` should end up as
                # `(int, str, float)` rather than `([int, str], float)`.
                new_args.extend(new_arg)
            sowenn _is_unpacked_typevartuple(old_arg):
                # Consider the following `_GenericAlias`, `B`:
                #   klasse A(Generic[*Ts]): ...
                #   B = A[T, *Ts]
                # If we then do:
                #   B[float, int, str]
                # The `new_arg` corresponding to `T` will be `float`, und the
                # `new_arg` corresponding to `*Ts` will be `(int, str)`. We
                # should join all these types together in a flat list
                # `(float, int, str)` - so again, we should `extend`.
                new_args.extend(new_arg)
            sowenn isinstance(old_arg, tuple):
                # Corner case:
                #    P = ParamSpec('P')
                #    T = TypeVar('T')
                #    klasse Base(Generic[P]): ...
                # Can be substituted like this:
                #    X = Base[[int, T]]
                # In this case, `old_arg` will be a tuple:
                new_args.append(
                    tuple(self._make_substitution(old_arg, new_arg_by_param)),
                )
            sonst:
                new_args.append(new_arg)
        return new_args

    def copy_with(self, args):
        return self.__class__(self.__origin__, args, name=self._name, inst=self._inst)

    def __repr__(self):
        wenn self._name:
            name = 'typing.' + self._name
        sonst:
            name = _type_repr(self.__origin__)
        wenn self.__args__:
            args = ", ".join([_type_repr(a) fuer a in self.__args__])
        sonst:
            # To ensure the repr is eval-able.
            args = "()"
        return f'{name}[{args}]'

    def __reduce__(self):
        wenn self._name:
            origin = globals()[self._name]
        sonst:
            origin = self.__origin__
        args = tuple(self.__args__)
        wenn len(args) == 1 und nicht isinstance(args[0], tuple):
            args, = args
        return operator.getitem, (origin, args)

    def __mro_entries__(self, bases):
        wenn isinstance(self.__origin__, _SpecialForm):
            raise TypeError(f"Cannot subclass {self!r}")

        wenn self._name:  # generic version of an ABC oder built-in class
            return super().__mro_entries__(bases)
        wenn self.__origin__ is Generic:
            wenn Protocol in bases:
                return ()
            i = bases.index(self)
            fuer b in bases[i+1:]:
                wenn isinstance(b, _BaseGenericAlias) und b is nicht self:
                    return ()
        return (self.__origin__,)

    def __iter__(self):
        yield Unpack[self]


# _nparams is the number of accepted parameters, e.g. 0 fuer Hashable,
# 1 fuer List und 2 fuer Dict.  It may be -1 wenn variable number of
# parameters are accepted (needs custom __getitem__).

klasse _SpecialGenericAlias(_NotIterable, _BaseGenericAlias, _root=Wahr):
    def __init__(self, origin, nparams, *, inst=Wahr, name=Nichts, defaults=()):
        wenn name is Nichts:
            name = origin.__name__
        super().__init__(origin, inst=inst, name=name)
        self._nparams = nparams
        self._defaults = defaults
        wenn origin.__module__ == 'builtins':
            self.__doc__ = f'A generic version of {origin.__qualname__}.'
        sonst:
            self.__doc__ = f'A generic version of {origin.__module__}.{origin.__qualname__}.'

    @_tp_cache
    def __getitem__(self, params):
        wenn nicht isinstance(params, tuple):
            params = (params,)
        msg = "Parameters to generic types must be types."
        params = tuple(_type_check(p, msg) fuer p in params)
        wenn (self._defaults
            und len(params) < self._nparams
            und len(params) + len(self._defaults) >= self._nparams
        ):
            params = (*params, *self._defaults[len(params) - self._nparams:])
        actual_len = len(params)

        wenn actual_len != self._nparams:
            wenn self._defaults:
                expected = f"at least {self._nparams - len(self._defaults)}"
            sonst:
                expected = str(self._nparams)
            wenn nicht self._nparams:
                raise TypeError(f"{self} is nicht a generic class")
            raise TypeError(f"Too {'many' wenn actual_len > self._nparams sonst 'few'} arguments fuer {self};"
                            f" actual {actual_len}, expected {expected}")
        return self.copy_with(params)

    def copy_with(self, params):
        return _GenericAlias(self.__origin__, params,
                             name=self._name, inst=self._inst)

    def __repr__(self):
        return 'typing.' + self._name

    def __subclasscheck__(self, cls):
        wenn isinstance(cls, _SpecialGenericAlias):
            return issubclass(cls.__origin__, self.__origin__)
        wenn nicht isinstance(cls, _GenericAlias):
            return issubclass(cls, self.__origin__)
        return super().__subclasscheck__(cls)

    def __reduce__(self):
        return self._name

    def __or__(self, right):
        return Union[self, right]

    def __ror__(self, left):
        return Union[left, self]


klasse _CallableGenericAlias(_NotIterable, _GenericAlias, _root=Wahr):
    def __repr__(self):
        assert self._name == 'Callable'
        args = self.__args__
        wenn len(args) == 2 und _is_param_expr(args[0]):
            return super().__repr__()
        return (f'typing.Callable'
                f'[[{", ".join([_type_repr(a) fuer a in args[:-1]])}], '
                f'{_type_repr(args[-1])}]')

    def __reduce__(self):
        args = self.__args__
        wenn nicht (len(args) == 2 und _is_param_expr(args[0])):
            args = list(args[:-1]), args[-1]
        return operator.getitem, (Callable, args)


klasse _CallableType(_SpecialGenericAlias, _root=Wahr):
    def copy_with(self, params):
        return _CallableGenericAlias(self.__origin__, params,
                                     name=self._name, inst=self._inst)

    def __getitem__(self, params):
        wenn nicht isinstance(params, tuple) oder len(params) != 2:
            raise TypeError("Callable must be used als "
                            "Callable[[arg, ...], result].")
        args, result = params
        # This relaxes what args can be on purpose to allow things like
        # PEP 612 ParamSpec.  Responsibility fuer whether a user is using
        # Callable[...] properly is deferred to static type checkers.
        wenn isinstance(args, list):
            params = (tuple(args), result)
        sonst:
            params = (args, result)
        return self.__getitem_inner__(params)

    @_tp_cache
    def __getitem_inner__(self, params):
        args, result = params
        msg = "Callable[args, result]: result must be a type."
        result = _type_check(result, msg)
        wenn args is Ellipsis:
            return self.copy_with((_TypingEllipsis, result))
        wenn nicht isinstance(args, tuple):
            args = (args,)
        args = tuple(_type_convert(arg) fuer arg in args)
        params = args + (result,)
        return self.copy_with(params)


klasse _TupleType(_SpecialGenericAlias, _root=Wahr):
    @_tp_cache
    def __getitem__(self, params):
        wenn nicht isinstance(params, tuple):
            params = (params,)
        wenn len(params) >= 2 und params[-1] is ...:
            msg = "Tuple[t, ...]: t must be a type."
            params = tuple(_type_check(p, msg) fuer p in params[:-1])
            return self.copy_with((*params, _TypingEllipsis))
        msg = "Tuple[t0, t1, ...]: each t must be a type."
        params = tuple(_type_check(p, msg) fuer p in params)
        return self.copy_with(params)


klasse _UnionGenericAliasMeta(type):
    def __instancecheck__(self, inst: object) -> bool:
        importiere warnings
        warnings._deprecated("_UnionGenericAlias", remove=(3, 17))
        return isinstance(inst, Union)

    def __subclasscheck__(self, inst: type) -> bool:
        importiere warnings
        warnings._deprecated("_UnionGenericAlias", remove=(3, 17))
        return issubclass(inst, Union)

    def __eq__(self, other):
        importiere warnings
        warnings._deprecated("_UnionGenericAlias", remove=(3, 17))
        wenn other is _UnionGenericAlias oder other is Union:
            return Wahr
        return NotImplemented

    def __hash__(self):
        return hash(Union)


klasse _UnionGenericAlias(metaclass=_UnionGenericAliasMeta):
    """Compatibility hack.

    A klasse named _UnionGenericAlias used to be used to implement
    typing.Union. This klasse exists to serve als a shim to preserve
    the meaning of some code that used to use _UnionGenericAlias
    directly.

    """
    def __new__(cls, self_cls, parameters, /, *, name=Nichts):
        importiere warnings
        warnings._deprecated("_UnionGenericAlias", remove=(3, 17))
        return Union[parameters]


def _value_and_type_iter(parameters):
    return ((p, type(p)) fuer p in parameters)


klasse _LiteralGenericAlias(_GenericAlias, _root=Wahr):
    def __eq__(self, other):
        wenn nicht isinstance(other, _LiteralGenericAlias):
            return NotImplemented

        return set(_value_and_type_iter(self.__args__)) == set(_value_and_type_iter(other.__args__))

    def __hash__(self):
        return hash(frozenset(_value_and_type_iter(self.__args__)))


klasse _ConcatenateGenericAlias(_GenericAlias, _root=Wahr):
    def copy_with(self, params):
        wenn isinstance(params[-1], (list, tuple)):
            return (*params[:-1], *params[-1])
        wenn isinstance(params[-1], _ConcatenateGenericAlias):
            params = (*params[:-1], *params[-1].__args__)
        return super().copy_with(params)


@_SpecialForm
def Unpack(self, parameters):
    """Type unpack operator.

    The type unpack operator takes the child types von some container type,
    such als `tuple[int, str]` oder a `TypeVarTuple`, und 'pulls them out'.

    For example::

        # For some generic klasse `Foo`:
        Foo[Unpack[tuple[int, str]]]  # Equivalent to Foo[int, str]

        Ts = TypeVarTuple('Ts')
        # Specifies that `Bar` is generic in an arbitrary number of types.
        # (Think of `Ts` als a tuple of an arbitrary number of individual
        #  `TypeVar`s, which the `Unpack` is 'pulling out' directly into the
        #  `Generic[]`.)
        klasse Bar(Generic[Unpack[Ts]]): ...
        Bar[int]  # Valid
        Bar[int, str]  # Also valid

    From Python 3.11, this can also be done using the `*` operator::

        Foo[*tuple[int, str]]
        klasse Bar(Generic[*Ts]): ...

    And von Python 3.12, it can be done using built-in syntax fuer generics::

        Foo[*tuple[int, str]]
        klasse Bar[*Ts]: ...

    The operator can also be used along mit a `TypedDict` to annotate
    `**kwargs` in a function signature::

        klasse Movie(TypedDict):
            name: str
            year: int

        # This function expects two keyword arguments - *name* of type `str` und
        # *year* of type `int`.
        def foo(**kwargs: Unpack[Movie]): ...

    Note that there is only some runtime checking of this operator. Not
    everything the runtime allows may be accepted by static type checkers.

    For more information, see PEPs 646 und 692.
    """
    item = _type_check(parameters, f'{self} accepts only single type.')
    return _UnpackGenericAlias(origin=self, args=(item,))


klasse _UnpackGenericAlias(_GenericAlias, _root=Wahr):
    def __repr__(self):
        # `Unpack` only takes one argument, so __args__ should contain only
        # a single item.
        return f'typing.Unpack[{_type_repr(self.__args__[0])}]'

    def __getitem__(self, args):
        wenn self.__typing_is_unpacked_typevartuple__:
            return args
        return super().__getitem__(args)

    @property
    def __typing_unpacked_tuple_args__(self):
        assert self.__origin__ is Unpack
        assert len(self.__args__) == 1
        arg, = self.__args__
        wenn isinstance(arg, (_GenericAlias, types.GenericAlias)):
            wenn arg.__origin__ is nicht tuple:
                raise TypeError("Unpack[...] must be used mit a tuple type")
            return arg.__args__
        return Nichts

    @property
    def __typing_is_unpacked_typevartuple__(self):
        assert self.__origin__ is Unpack
        assert len(self.__args__) == 1
        return isinstance(self.__args__[0], TypeVarTuple)


klasse _TypingEllipsis:
    """Internal placeholder fuer ... (ellipsis)."""


_TYPING_INTERNALS = frozenset({
    '__parameters__', '__orig_bases__',  '__orig_class__',
    '_is_protocol', '_is_runtime_protocol', '__protocol_attrs__',
    '__non_callable_proto_members__', '__type_params__',
})

_SPECIAL_NAMES = frozenset({
    '__abstractmethods__', '__annotations__', '__dict__', '__doc__',
    '__init__', '__module__', '__new__', '__slots__',
    '__subclasshook__', '__weakref__', '__class_getitem__',
    '__match_args__', '__static_attributes__', '__firstlineno__',
    '__annotate__', '__annotate_func__', '__annotations_cache__',
})

# These special attributes will be nicht collected als protocol members.
EXCLUDED_ATTRIBUTES = _TYPING_INTERNALS | _SPECIAL_NAMES | {'_MutableMapping__marker'}


def _get_protocol_attrs(cls):
    """Collect protocol members von a protocol klasse objects.

    This includes names actually defined in the klasse dictionary, als well
    als names that appear in annotations. Special names (above) are skipped.
    """
    attrs = set()
    fuer base in cls.__mro__[:-1]:  # without object
        wenn base.__name__ in {'Protocol', 'Generic'}:
            continue
        try:
            annotations = base.__annotations__
        except Exception:
            # Only go through annotationlib to handle deferred annotations wenn we need to
            annotations = _lazy_annotationlib.get_annotations(
                base, format=_lazy_annotationlib.Format.FORWARDREF
            )
        fuer attr in (*base.__dict__, *annotations):
            wenn nicht attr.startswith('_abc_') und attr nicht in EXCLUDED_ATTRIBUTES:
                attrs.add(attr)
    return attrs


def _no_init_or_replace_init(self, *args, **kwargs):
    cls = type(self)

    wenn cls._is_protocol:
        raise TypeError('Protocols cannot be instantiated')

    # Already using a custom `__init__`. No need to calculate correct
    # `__init__` to call. This can lead to RecursionError. See bpo-45121.
    wenn cls.__init__ is nicht _no_init_or_replace_init:
        return

    # Initially, `__init__` of a protocol subclass is set to `_no_init_or_replace_init`.
    # The first instantiation of the subclass will call `_no_init_or_replace_init` which
    # searches fuer a proper new `__init__` in the MRO. The new `__init__`
    # replaces the subclass' old `__init__` (ie `_no_init_or_replace_init`). Subsequent
    # instantiation of the protocol subclass will thus use the new
    # `__init__` und no longer call `_no_init_or_replace_init`.
    fuer base in cls.__mro__:
        init = base.__dict__.get('__init__', _no_init_or_replace_init)
        wenn init is nicht _no_init_or_replace_init:
            cls.__init__ = init
            break
    sonst:
        # should nicht happen
        cls.__init__ = object.__init__

    cls.__init__(self, *args, **kwargs)


def _caller(depth=1, default='__main__'):
    try:
        return sys._getframemodulename(depth + 1) oder default
    except AttributeError:  # For platforms without _getframemodulename()
        pass
    try:
        return sys._getframe(depth + 1).f_globals.get('__name__', default)
    except (AttributeError, ValueError):  # For platforms without _getframe()
        pass
    return Nichts

def _allow_reckless_class_checks(depth=2):
    """Allow instance und klasse checks fuer special stdlib modules.

    The abc und functools modules indiscriminately call isinstance() und
    issubclass() on the whole MRO of a user class, which may contain protocols.
    """
    # gh-136047: When `_abc` module is nicht available, `_py_abc` is required to
    # allow `_py_abc.ABCMeta` fallback.
    return _caller(depth) in {'abc', '_py_abc', 'functools', Nichts}


_PROTO_ALLOWLIST = {
    'collections.abc': [
        'Callable', 'Awaitable', 'Iterable', 'Iterator', 'AsyncIterable',
        'AsyncIterator', 'Hashable', 'Sized', 'Container', 'Collection',
        'Reversible', 'Buffer',
    ],
    'contextlib': ['AbstractContextManager', 'AbstractAsyncContextManager'],
    'io': ['Reader', 'Writer'],
    'os': ['PathLike'],
}


@functools.cache
def _lazy_load_getattr_static():
    # Import getattr_static lazily so als nicht to slow down the importiere of typing.py
    # Cache the result so we don't slow down _ProtocolMeta.__instancecheck__ unnecessarily
    von inspect importiere getattr_static
    return getattr_static


_cleanups.append(_lazy_load_getattr_static.cache_clear)

def _pickle_psargs(psargs):
    return ParamSpecArgs, (psargs.__origin__,)

copyreg.pickle(ParamSpecArgs, _pickle_psargs)

def _pickle_pskwargs(pskwargs):
    return ParamSpecKwargs, (pskwargs.__origin__,)

copyreg.pickle(ParamSpecKwargs, _pickle_pskwargs)

del _pickle_psargs, _pickle_pskwargs


# Preload these once, als globals, als a micro-optimisation.
# This makes a significant difference to the time it takes
# to do `isinstance()`/`issubclass()` checks
# against runtime-checkable protocols mit only one callable member.
_abc_instancecheck = ABCMeta.__instancecheck__
_abc_subclasscheck = ABCMeta.__subclasscheck__


def _type_check_issubclass_arg_1(arg):
    """Raise TypeError wenn `arg` is nicht an instance of `type`
    in `issubclass(arg, <protocol>)`.

    In most cases, this is verified by type.__subclasscheck__.
    Checking it again unnecessarily would slow down issubclass() checks,
    so, we don't perform this check unless we absolutely have to.

    For various error paths, however,
    we want to ensure that *this* error message is shown to the user
    where relevant, rather than a typing.py-specific error message.
    """
    wenn nicht isinstance(arg, type):
        # Same error message als fuer issubclass(1, int).
        raise TypeError('issubclass() arg 1 must be a class')


klasse _ProtocolMeta(ABCMeta):
    # This metaclass is somewhat unfortunate,
    # but is necessary fuer several reasons...
    def __new__(mcls, name, bases, namespace, /, **kwargs):
        wenn name == "Protocol" und bases == (Generic,):
            pass
        sowenn Protocol in bases:
            fuer base in bases:
                wenn nicht (
                    base in {object, Generic}
                    oder base.__name__ in _PROTO_ALLOWLIST.get(base.__module__, [])
                    oder (
                        issubclass(base, Generic)
                        und getattr(base, "_is_protocol", Falsch)
                    )
                ):
                    raise TypeError(
                        f"Protocols can only inherit von other protocols, "
                        f"got {base!r}"
                    )
        return super().__new__(mcls, name, bases, namespace, **kwargs)

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        wenn getattr(cls, "_is_protocol", Falsch):
            cls.__protocol_attrs__ = _get_protocol_attrs(cls)

    def __subclasscheck__(cls, other):
        wenn cls is Protocol:
            return type.__subclasscheck__(cls, other)
        wenn (
            getattr(cls, '_is_protocol', Falsch)
            und nicht _allow_reckless_class_checks()
        ):
            wenn nicht getattr(cls, '_is_runtime_protocol', Falsch):
                _type_check_issubclass_arg_1(other)
                raise TypeError(
                    "Instance und klasse checks can only be used mit "
                    "@runtime_checkable protocols"
                )
            wenn (
                # this attribute is set by @runtime_checkable:
                cls.__non_callable_proto_members__
                und cls.__dict__.get("__subclasshook__") is _proto_hook
            ):
                _type_check_issubclass_arg_1(other)
                non_method_attrs = sorted(cls.__non_callable_proto_members__)
                raise TypeError(
                    "Protocols mit non-method members don't support issubclass()."
                    f" Non-method members: {str(non_method_attrs)[1:-1]}."
                )
        return _abc_subclasscheck(cls, other)

    def __instancecheck__(cls, instance):
        # We need this method fuer situations where attributes are
        # assigned in __init__.
        wenn cls is Protocol:
            return type.__instancecheck__(cls, instance)
        wenn nicht getattr(cls, "_is_protocol", Falsch):
            # i.e., it's a concrete subclass of a protocol
            return _abc_instancecheck(cls, instance)

        wenn (
            nicht getattr(cls, '_is_runtime_protocol', Falsch) und
            nicht _allow_reckless_class_checks()
        ):
            raise TypeError("Instance und klasse checks can only be used with"
                            " @runtime_checkable protocols")

        wenn _abc_instancecheck(cls, instance):
            return Wahr

        getattr_static = _lazy_load_getattr_static()
        fuer attr in cls.__protocol_attrs__:
            try:
                val = getattr_static(instance, attr)
            except AttributeError:
                break
            # this attribute is set by @runtime_checkable:
            wenn val is Nichts und attr nicht in cls.__non_callable_proto_members__:
                break
        sonst:
            return Wahr

        return Falsch


@classmethod
def _proto_hook(cls, other):
    wenn nicht cls.__dict__.get('_is_protocol', Falsch):
        return NotImplemented

    fuer attr in cls.__protocol_attrs__:
        fuer base in other.__mro__:
            # Check wenn the members appears in the klasse dictionary...
            wenn attr in base.__dict__:
                wenn base.__dict__[attr] is Nichts:
                    return NotImplemented
                break

            # ...or in annotations, wenn it is a sub-protocol.
            wenn issubclass(other, Generic) und getattr(other, "_is_protocol", Falsch):
                # We avoid the slower path through annotationlib here because in most
                # cases it should be unnecessary.
                try:
                    annos = base.__annotations__
                except Exception:
                    annos = _lazy_annotationlib.get_annotations(
                        base, format=_lazy_annotationlib.Format.FORWARDREF
                    )
                wenn attr in annos:
                    break
        sonst:
            return NotImplemented
    return Wahr


klasse Protocol(Generic, metaclass=_ProtocolMeta):
    """Base klasse fuer protocol classes.

    Protocol classes are defined as::

        klasse Proto(Protocol):
            def meth(self) -> int:
                ...

    Such classes are primarily used mit static type checkers that recognize
    structural subtyping (static duck-typing).

    For example::

        klasse C:
            def meth(self) -> int:
                return 0

        def func(x: Proto) -> int:
            return x.meth()

        func(C())  # Passes static type check

    See PEP 544 fuer details. Protocol classes decorated with
    @typing.runtime_checkable act als simple-minded runtime protocols that check
    only the presence of given attributes, ignoring their type signatures.
    Protocol classes can be generic, they are defined as::

        klasse GenProto[T](Protocol):
            def meth(self) -> T:
                ...
    """

    __slots__ = ()
    _is_protocol = Wahr
    _is_runtime_protocol = Falsch

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        # Determine wenn this is a protocol oder a concrete subclass.
        wenn nicht cls.__dict__.get('_is_protocol', Falsch):
            cls._is_protocol = any(b is Protocol fuer b in cls.__bases__)

        # Set (or override) the protocol subclass hook.
        wenn '__subclasshook__' nicht in cls.__dict__:
            cls.__subclasshook__ = _proto_hook

        # Prohibit instantiation fuer protocol classes
        wenn cls._is_protocol und cls.__init__ is Protocol.__init__:
            cls.__init__ = _no_init_or_replace_init


klasse _AnnotatedAlias(_NotIterable, _GenericAlias, _root=Wahr):
    """Runtime representation of an annotated type.

    At its core 'Annotated[t, dec1, dec2, ...]' is an alias fuer the type 't'
    mit extra metadata. The alias behaves like a normal typing alias.
    Instantiating is the same als instantiating the underlying type; binding
    it to types is also the same.

    The metadata itself is stored in a '__metadata__' attribute als a tuple.
    """

    def __init__(self, origin, metadata):
        wenn isinstance(origin, _AnnotatedAlias):
            metadata = origin.__metadata__ + metadata
            origin = origin.__origin__
        super().__init__(origin, origin, name='Annotated')
        self.__metadata__ = metadata

    def copy_with(self, params):
        assert len(params) == 1
        new_type = params[0]
        return _AnnotatedAlias(new_type, self.__metadata__)

    def __repr__(self):
        return "typing.Annotated[{}, {}]".format(
            _type_repr(self.__origin__),
            ", ".join(repr(a) fuer a in self.__metadata__)
        )

    def __reduce__(self):
        return operator.getitem, (
            Annotated, (self.__origin__,) + self.__metadata__
        )

    def __eq__(self, other):
        wenn nicht isinstance(other, _AnnotatedAlias):
            return NotImplemented
        return (self.__origin__ == other.__origin__
                und self.__metadata__ == other.__metadata__)

    def __hash__(self):
        return hash((self.__origin__, self.__metadata__))

    def __getattr__(self, attr):
        wenn attr in {'__name__', '__qualname__'}:
            return 'Annotated'
        return super().__getattr__(attr)

    def __mro_entries__(self, bases):
        return (self.__origin__,)


@_TypedCacheSpecialForm
@_tp_cache(typed=Wahr)
def Annotated(self, *params):
    """Add context-specific metadata to a type.

    Example: Annotated[int, runtime_check.Unsigned] indicates to the
    hypothetical runtime_check module that this type is an unsigned int.
    Every other consumer of this type can ignore this metadata und treat
    this type als int.

    The first argument to Annotated must be a valid type.

    Details:

    - It's an error to call `Annotated` mit less than two arguments.
    - Access the metadata via the ``__metadata__`` attribute::

        assert Annotated[int, '$'].__metadata__ == ('$',)

    - Nested Annotated types are flattened::

        assert Annotated[Annotated[T, Ann1, Ann2], Ann3] == Annotated[T, Ann1, Ann2, Ann3]

    - Instantiating an annotated type is equivalent to instantiating the
    underlying type::

        assert Annotated[C, Ann1](5) == C(5)

    - Annotated can be used als a generic type alias::

        type Optimized[T] = Annotated[T, runtime.Optimize()]
        # type checker will treat Optimized[int]
        # als equivalent to Annotated[int, runtime.Optimize()]

        type OptimizedList[T] = Annotated[list[T], runtime.Optimize()]
        # type checker will treat OptimizedList[int]
        # als equivalent to Annotated[list[int], runtime.Optimize()]

    - Annotated cannot be used mit an unpacked TypeVarTuple::

        type Variadic[*Ts] = Annotated[*Ts, Ann1]  # NOT valid

      This would be equivalent to::

        Annotated[T1, T2, T3, ..., Ann1]

      where T1, T2 etc. are TypeVars, which would be invalid, because
      only one type should be passed to Annotated.
    """
    wenn len(params) < 2:
        raise TypeError("Annotated[...] should be used "
                        "with at least two arguments (a type und an "
                        "annotation).")
    wenn _is_unpacked_typevartuple(params[0]):
        raise TypeError("Annotated[...] should nicht be used mit an "
                        "unpacked TypeVarTuple")
    msg = "Annotated[t, ...]: t must be a type."
    origin = _type_check(params[0], msg, allow_special_forms=Wahr)
    metadata = tuple(params[1:])
    return _AnnotatedAlias(origin, metadata)


def runtime_checkable(cls):
    """Mark a protocol klasse als a runtime protocol.

    Such protocol can be used mit isinstance() und issubclass().
    Raise TypeError wenn applied to a non-protocol class.
    This allows a simple-minded structural check very similar to
    one trick ponies in collections.abc such als Iterable.

    For example::

        @runtime_checkable
        klasse Closable(Protocol):
            def close(self): ...

        assert isinstance(open('/some/file'), Closable)

    Warning: this will check only the presence of the required methods,
    nicht their type signatures!
    """
    wenn nicht issubclass(cls, Generic) oder nicht getattr(cls, '_is_protocol', Falsch):
        raise TypeError('@runtime_checkable can be only applied to protocol classes,'
                        ' got %r' % cls)
    cls._is_runtime_protocol = Wahr
    # PEP 544 prohibits using issubclass()
    # mit protocols that have non-method members.
    # See gh-113320 fuer why we compute this attribute here,
    # rather than in `_ProtocolMeta.__init__`
    cls.__non_callable_proto_members__ = set()
    fuer attr in cls.__protocol_attrs__:
        try:
            is_callable = callable(getattr(cls, attr, Nichts))
        except Exception als e:
            raise TypeError(
                f"Failed to determine whether protocol member {attr!r} "
                "is a method member"
            ) von e
        sonst:
            wenn nicht is_callable:
                cls.__non_callable_proto_members__.add(attr)
    return cls


def cast(typ, val):
    """Cast a value to a type.

    This returns the value unchanged.  To the type checker this
    signals that the return value has the designated type, but at
    runtime we intentionally don't check anything (we want this
    to be als fast als possible).
    """
    return val


def assert_type(val, typ, /):
    """Ask a static type checker to confirm that the value is of the given type.

    At runtime this does nothing: it returns the first argument unchanged mit no
    checks oder side effects, no matter the actual type of the argument.

    When a static type checker encounters a call to assert_type(), it
    emits an error wenn the value is nicht of the specified type::

        def greet(name: str) -> Nichts:
            assert_type(name, str)  # OK
            assert_type(name, int)  # type checker error
    """
    return val


def get_type_hints(obj, globalns=Nichts, localns=Nichts, include_extras=Falsch,
                   *, format=Nichts):
    """Return type hints fuer an object.

    This is often the same als obj.__annotations__, but it handles
    forward references encoded als string literals und recursively replaces all
    'Annotated[T, ...]' mit 'T' (unless 'include_extras=Wahr').

    The argument may be a module, class, method, oder function. The annotations
    are returned als a dictionary. For classes, annotations include also
    inherited members.

    TypeError is raised wenn the argument is nicht of a type that can contain
    annotations, und an empty dictionary is returned wenn no annotations are
    present.

    BEWARE -- the behavior of globalns und localns is counterintuitive
    (unless you are familiar mit how eval() und exec() work).  The
    search order is locals first, then globals.

    - If no dict arguments are passed, an attempt is made to use the
      globals von obj (or the respective module's globals fuer classes),
      und these are also used als the locals.  If the object does nicht appear
      to have globals, an empty dictionary is used.  For classes, the search
      order is globals first then locals.

    - If one dict argument is passed, it is used fuer both globals und
      locals.

    - If two dict arguments are passed, they specify globals und
      locals, respectively.
    """
    wenn getattr(obj, '__no_type_check__', Nichts):
        return {}
    Format = _lazy_annotationlib.Format
    wenn format is Nichts:
        format = Format.VALUE
    # Classes require a special treatment.
    wenn isinstance(obj, type):
        hints = {}
        fuer base in reversed(obj.__mro__):
            ann = _lazy_annotationlib.get_annotations(base, format=format)
            wenn format == Format.STRING:
                hints.update(ann)
                continue
            wenn globalns is Nichts:
                base_globals = getattr(sys.modules.get(base.__module__, Nichts), '__dict__', {})
            sonst:
                base_globals = globalns
            base_locals = dict(vars(base)) wenn localns is Nichts sonst localns
            wenn localns is Nichts und globalns is Nichts:
                # This is surprising, but required.  Before Python 3.10,
                # get_type_hints only evaluated the globalns of
                # a class.  To maintain backwards compatibility, we reverse
                # the globalns und localns order so that eval() looks into
                # *base_globals* first rather than *base_locals*.
                # This only affects ForwardRefs.
                base_globals, base_locals = base_locals, base_globals
            type_params = base.__type_params__
            base_globals, base_locals = _add_type_params_to_scope(
                type_params, base_globals, base_locals, Wahr)
            fuer name, value in ann.items():
                wenn isinstance(value, str):
                    value = _make_forward_ref(value, is_argument=Falsch, is_class=Wahr)
                value = _eval_type(value, base_globals, base_locals, (),
                                   format=format, owner=obj)
                wenn value is Nichts:
                    value = type(Nichts)
                hints[name] = value
        wenn include_extras oder format == Format.STRING:
            return hints
        sonst:
            return {k: _strip_annotations(t) fuer k, t in hints.items()}

    hints = _lazy_annotationlib.get_annotations(obj, format=format)
    wenn (
        nicht hints
        und nicht isinstance(obj, types.ModuleType)
        und nicht callable(obj)
        und nicht hasattr(obj, '__annotations__')
        und nicht hasattr(obj, '__annotate__')
    ):
        raise TypeError(f"{obj!r} is nicht a module, class, oder callable.")
    wenn format == Format.STRING:
        return hints

    wenn globalns is Nichts:
        wenn isinstance(obj, types.ModuleType):
            globalns = obj.__dict__
        sonst:
            nsobj = obj
            # Find globalns fuer the unwrapped object.
            while hasattr(nsobj, '__wrapped__'):
                nsobj = nsobj.__wrapped__
            globalns = getattr(nsobj, '__globals__', {})
        wenn localns is Nichts:
            localns = globalns
    sowenn localns is Nichts:
        localns = globalns
    type_params = getattr(obj, "__type_params__", ())
    globalns, localns = _add_type_params_to_scope(type_params, globalns, localns, Falsch)
    fuer name, value in hints.items():
        wenn isinstance(value, str):
            # class-level forward refs were handled above, this must be either
            # a module-level annotation oder a function argument annotation
            value = _make_forward_ref(
                value,
                is_argument=nicht isinstance(obj, types.ModuleType),
                is_class=Falsch,
            )
        value = _eval_type(value, globalns, localns, (), format=format, owner=obj)
        wenn value is Nichts:
            value = type(Nichts)
        hints[name] = value
    return hints wenn include_extras sonst {k: _strip_annotations(t) fuer k, t in hints.items()}


# Add type parameters to the globals und locals scope. This is needed for
# compatibility.
def _add_type_params_to_scope(type_params, globalns, localns, is_class):
    wenn nicht type_params:
        return globalns, localns
    globalns = dict(globalns)
    localns = dict(localns)
    fuer param in type_params:
        wenn nicht is_class oder param.__name__ nicht in globalns:
            globalns[param.__name__] = param
            localns.pop(param.__name__, Nichts)
    return globalns, localns


def _strip_annotations(t):
    """Strip the annotations von a given type."""
    wenn isinstance(t, _AnnotatedAlias):
        return _strip_annotations(t.__origin__)
    wenn hasattr(t, "__origin__") und t.__origin__ in (Required, NotRequired, ReadOnly):
        return _strip_annotations(t.__args__[0])
    wenn isinstance(t, _GenericAlias):
        stripped_args = tuple(_strip_annotations(a) fuer a in t.__args__)
        wenn stripped_args == t.__args__:
            return t
        return t.copy_with(stripped_args)
    wenn isinstance(t, GenericAlias):
        stripped_args = tuple(_strip_annotations(a) fuer a in t.__args__)
        wenn stripped_args == t.__args__:
            return t
        return _rebuild_generic_alias(t, stripped_args)
    wenn isinstance(t, Union):
        stripped_args = tuple(_strip_annotations(a) fuer a in t.__args__)
        wenn stripped_args == t.__args__:
            return t
        return functools.reduce(operator.or_, stripped_args)

    return t


def get_origin(tp):
    """Get the unsubscripted version of a type.

    This supports generic types, Callable, Tuple, Union, Literal, Final, ClassVar,
    Annotated, und others. Return Nichts fuer unsupported types.

    Examples::

        >>> P = ParamSpec('P')
        >>> assert get_origin(Literal[42]) is Literal
        >>> assert get_origin(int) is Nichts
        >>> assert get_origin(ClassVar[int]) is ClassVar
        >>> assert get_origin(Generic) is Generic
        >>> assert get_origin(Generic[T]) is Generic
        >>> assert get_origin(Union[T, int]) is Union
        >>> assert get_origin(List[Tuple[T, T]][int]) is list
        >>> assert get_origin(P.args) is P
    """
    wenn isinstance(tp, _AnnotatedAlias):
        return Annotated
    wenn isinstance(tp, (_BaseGenericAlias, GenericAlias,
                       ParamSpecArgs, ParamSpecKwargs)):
        return tp.__origin__
    wenn tp is Generic:
        return Generic
    wenn isinstance(tp, Union):
        return Union
    return Nichts


def get_args(tp):
    """Get type arguments mit all substitutions performed.

    For unions, basic simplifications used by Union constructor are performed.

    Examples::

        >>> T = TypeVar('T')
        >>> assert get_args(Dict[str, int]) == (str, int)
        >>> assert get_args(int) == ()
        >>> assert get_args(Union[int, Union[T, int], str][int]) == (int, str)
        >>> assert get_args(Union[int, Tuple[T, int]][str]) == (int, Tuple[str, int])
        >>> assert get_args(Callable[[], T][int]) == ([], int)
    """
    wenn isinstance(tp, _AnnotatedAlias):
        return (tp.__origin__,) + tp.__metadata__
    wenn isinstance(tp, (_GenericAlias, GenericAlias)):
        res = tp.__args__
        wenn _should_unflatten_callable_args(tp, res):
            res = (list(res[:-1]), res[-1])
        return res
    wenn isinstance(tp, Union):
        return tp.__args__
    return ()


def is_typeddict(tp):
    """Check wenn an annotation is a TypedDict class.

    For example::

        >>> von typing importiere TypedDict
        >>> klasse Film(TypedDict):
        ...     title: str
        ...     year: int
        ...
        >>> is_typeddict(Film)
        Wahr
        >>> is_typeddict(dict)
        Falsch
    """
    return isinstance(tp, _TypedDictMeta)


_ASSERT_NEVER_REPR_MAX_LENGTH = 100


def assert_never(arg: Never, /) -> Never:
    """Statically assert that a line of code is unreachable.

    Example::

        def int_or_str(arg: int | str) -> Nichts:
            match arg:
                case int():
                    drucke("It's an int")
                case str():
                    drucke("It's a str")
                case _:
                    assert_never(arg)

    If a type checker finds that a call to assert_never() is
    reachable, it will emit an error.

    At runtime, this throws an exception when called.
    """
    value = repr(arg)
    wenn len(value) > _ASSERT_NEVER_REPR_MAX_LENGTH:
        value = value[:_ASSERT_NEVER_REPR_MAX_LENGTH] + '...'
    raise AssertionError(f"Expected code to be unreachable, but got: {value}")


def no_type_check(arg):
    """Decorator to indicate that annotations are nicht type hints.

    The argument must be a klasse oder function; wenn it is a class, it
    applies recursively to all methods und classes defined in that class
    (but nicht to methods defined in its superclasses oder subclasses).

    This mutates the function(s) oder class(es) in place.
    """
    wenn isinstance(arg, type):
        fuer key in dir(arg):
            obj = getattr(arg, key)
            wenn (
                nicht hasattr(obj, '__qualname__')
                oder obj.__qualname__ != f'{arg.__qualname__}.{obj.__name__}'
                oder getattr(obj, '__module__', Nichts) != arg.__module__
            ):
                # We only modify objects that are defined in this type directly.
                # If classes / methods are nested in multiple layers,
                # we will modify them when processing their direct holders.
                continue
            # Instance, class, und static methods:
            wenn isinstance(obj, types.FunctionType):
                obj.__no_type_check__ = Wahr
            wenn isinstance(obj, types.MethodType):
                obj.__func__.__no_type_check__ = Wahr
            # Nested types:
            wenn isinstance(obj, type):
                no_type_check(obj)
    try:
        arg.__no_type_check__ = Wahr
    except TypeError:  # built-in classes
        pass
    return arg


def no_type_check_decorator(decorator):
    """Decorator to give another decorator the @no_type_check effect.

    This wraps the decorator mit something that wraps the decorated
    function in @no_type_check.
    """
    importiere warnings
    warnings._deprecated("typing.no_type_check_decorator", remove=(3, 15))
    @functools.wraps(decorator)
    def wrapped_decorator(*args, **kwds):
        func = decorator(*args, **kwds)
        func = no_type_check(func)
        return func

    return wrapped_decorator


def _overload_dummy(*args, **kwds):
    """Helper fuer @overload to raise when called."""
    raise NotImplementedError(
        "You should nicht call an overloaded function. "
        "A series of @overload-decorated functions "
        "outside a stub module should always be followed "
        "by an implementation that is nicht @overload-ed.")


# {module: {qualname: {firstlineno: func}}}
_overload_registry = defaultdict(functools.partial(defaultdict, dict))


def overload(func):
    """Decorator fuer overloaded functions/methods.

    In a stub file, place two oder more stub definitions fuer the same
    function in a row, each decorated mit @overload.

    For example::

        @overload
        def utf8(value: Nichts) -> Nichts: ...
        @overload
        def utf8(value: bytes) -> bytes: ...
        @overload
        def utf8(value: str) -> bytes: ...

    In a non-stub file (i.e. a regular .py file), do the same but
    follow it mit an implementation.  The implementation should *not*
    be decorated mit @overload::

        @overload
        def utf8(value: Nichts) -> Nichts: ...
        @overload
        def utf8(value: bytes) -> bytes: ...
        @overload
        def utf8(value: str) -> bytes: ...
        def utf8(value):
            ...  # implementation goes here

    The overloads fuer a function can be retrieved at runtime using the
    get_overloads() function.
    """
    # classmethod und staticmethod
    f = getattr(func, "__func__", func)
    try:
        _overload_registry[f.__module__][f.__qualname__][f.__code__.co_firstlineno] = func
    except AttributeError:
        # Not a normal function; ignore.
        pass
    return _overload_dummy


def get_overloads(func):
    """Return all defined overloads fuer *func* als a sequence."""
    # classmethod und staticmethod
    f = getattr(func, "__func__", func)
    wenn f.__module__ nicht in _overload_registry:
        return []
    mod_dict = _overload_registry[f.__module__]
    wenn f.__qualname__ nicht in mod_dict:
        return []
    return list(mod_dict[f.__qualname__].values())


def clear_overloads():
    """Clear all overloads in the registry."""
    _overload_registry.clear()


def final(f):
    """Decorator to indicate final methods und final classes.

    Use this decorator to indicate to type checkers that the decorated
    method cannot be overridden, und decorated klasse cannot be subclassed.

    For example::

        klasse Base:
            @final
            def done(self) -> Nichts:
                ...
        klasse Sub(Base):
            def done(self) -> Nichts:  # Error reported by type checker
                ...

        @final
        klasse Leaf:
            ...
        klasse Other(Leaf):  # Error reported by type checker
            ...

    There is no runtime checking of these properties. The decorator
    attempts to set the ``__final__`` attribute to ``Wahr`` on the decorated
    object to allow runtime introspection.
    """
    try:
        f.__final__ = Wahr
    except (AttributeError, TypeError):
        # Skip the attribute silently wenn it is nicht writable.
        # AttributeError happens wenn the object has __slots__ oder a
        # read-only property, TypeError wenn it's a builtin class.
        pass
    return f


# Some unconstrained type variables.  These were initially used by the container types.
# They were never meant fuer export und are now unused, but we keep them around to
# avoid breaking compatibility mit users who importiere them.
T = TypeVar('T')  # Any type.
KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.
T_co = TypeVar('T_co', covariant=Wahr)  # Any type covariant containers.
V_co = TypeVar('V_co', covariant=Wahr)  # Any type covariant containers.
VT_co = TypeVar('VT_co', covariant=Wahr)  # Value type covariant containers.
T_contra = TypeVar('T_contra', contravariant=Wahr)  # Ditto contravariant.
# Internal type variable used fuer Type[].
CT_co = TypeVar('CT_co', covariant=Wahr, bound=type)


# A useful type variable mit constraints.  This represents string types.
# (This one *is* fuer export!)
AnyStr = TypeVar('AnyStr', bytes, str)


# Various ABCs mimicking those in collections.abc.
_alias = _SpecialGenericAlias

Hashable = _alias(collections.abc.Hashable, 0)  # Not generic.
Awaitable = _alias(collections.abc.Awaitable, 1)
Coroutine = _alias(collections.abc.Coroutine, 3)
AsyncIterable = _alias(collections.abc.AsyncIterable, 1)
AsyncIterator = _alias(collections.abc.AsyncIterator, 1)
Iterable = _alias(collections.abc.Iterable, 1)
Iterator = _alias(collections.abc.Iterator, 1)
Reversible = _alias(collections.abc.Reversible, 1)
Sized = _alias(collections.abc.Sized, 0)  # Not generic.
Container = _alias(collections.abc.Container, 1)
Collection = _alias(collections.abc.Collection, 1)
Callable = _CallableType(collections.abc.Callable, 2)
Callable.__doc__ = \
    """Deprecated alias to collections.abc.Callable.

    Callable[[int], str] signifies a function that takes a single
    parameter of type int und returns a str.

    The subscription syntax must always be used mit exactly two
    values: the argument list und the return type.
    The argument list must be a list of types, a ParamSpec,
    Concatenate oder ellipsis. The return type must be a single type.

    There is no syntax to indicate optional oder keyword arguments;
    such function types are rarely used als callback types.
    """
AbstractSet = _alias(collections.abc.Set, 1, name='AbstractSet')
MutableSet = _alias(collections.abc.MutableSet, 1)
# NOTE: Mapping is only covariant in the value type.
Mapping = _alias(collections.abc.Mapping, 2)
MutableMapping = _alias(collections.abc.MutableMapping, 2)
Sequence = _alias(collections.abc.Sequence, 1)
MutableSequence = _alias(collections.abc.MutableSequence, 1)
# Tuple accepts variable number of parameters.
Tuple = _TupleType(tuple, -1, inst=Falsch, name='Tuple')
Tuple.__doc__ = \
    """Deprecated alias to builtins.tuple.

    Tuple[X, Y] is the cross-product type of X und Y.

    Example: Tuple[T1, T2] is a tuple of two elements corresponding
    to type variables T1 und T2.  Tuple[int, float, str] is a tuple
    of an int, a float und a string.

    To specify a variable-length tuple of homogeneous type, use Tuple[T, ...].
    """
List = _alias(list, 1, inst=Falsch, name='List')
Deque = _alias(collections.deque, 1, name='Deque')
Set = _alias(set, 1, inst=Falsch, name='Set')
FrozenSet = _alias(frozenset, 1, inst=Falsch, name='FrozenSet')
MappingView = _alias(collections.abc.MappingView, 1)
KeysView = _alias(collections.abc.KeysView, 1)
ItemsView = _alias(collections.abc.ItemsView, 2)
ValuesView = _alias(collections.abc.ValuesView, 1)
Dict = _alias(dict, 2, inst=Falsch, name='Dict')
DefaultDict = _alias(collections.defaultdict, 2, name='DefaultDict')
OrderedDict = _alias(collections.OrderedDict, 2)
Counter = _alias(collections.Counter, 1)
ChainMap = _alias(collections.ChainMap, 2)
Generator = _alias(collections.abc.Generator, 3, defaults=(types.NoneType, types.NoneType))
AsyncGenerator = _alias(collections.abc.AsyncGenerator, 2, defaults=(types.NoneType,))
Type = _alias(type, 1, inst=Falsch, name='Type')
Type.__doc__ = \
    """Deprecated alias to builtins.type.

    builtins.type oder typing.Type can be used to annotate klasse objects.
    For example, suppose we have the following classes::

        klasse User: ...  # Abstract base fuer User classes
        klasse BasicUser(User): ...
        klasse ProUser(User): ...
        klasse TeamUser(User): ...

    And a function that takes a klasse argument that's a subclass of
    User und returns an instance of the corresponding class::

        def new_user[U](user_class: Type[U]) -> U:
            user = user_class()
            # (Here we could write the user object to a database)
            return user

        joe = new_user(BasicUser)

    At this point the type checker knows that joe has type BasicUser.
    """


@runtime_checkable
klasse SupportsInt(Protocol):
    """An ABC mit one abstract method __int__."""

    __slots__ = ()

    @abstractmethod
    def __int__(self) -> int:
        pass


@runtime_checkable
klasse SupportsFloat(Protocol):
    """An ABC mit one abstract method __float__."""

    __slots__ = ()

    @abstractmethod
    def __float__(self) -> float:
        pass


@runtime_checkable
klasse SupportsComplex(Protocol):
    """An ABC mit one abstract method __complex__."""

    __slots__ = ()

    @abstractmethod
    def __complex__(self) -> complex:
        pass


@runtime_checkable
klasse SupportsBytes(Protocol):
    """An ABC mit one abstract method __bytes__."""

    __slots__ = ()

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass


@runtime_checkable
klasse SupportsIndex(Protocol):
    """An ABC mit one abstract method __index__."""

    __slots__ = ()

    @abstractmethod
    def __index__(self) -> int:
        pass


@runtime_checkable
klasse SupportsAbs[T](Protocol):
    """An ABC mit one abstract method __abs__ that is covariant in its return type."""

    __slots__ = ()

    @abstractmethod
    def __abs__(self) -> T:
        pass


@runtime_checkable
klasse SupportsRound[T](Protocol):
    """An ABC mit one abstract method __round__ that is covariant in its return type."""

    __slots__ = ()

    @abstractmethod
    def __round__(self, ndigits: int = 0) -> T:
        pass


def _make_nmtuple(name, fields, annotate_func, module, defaults = ()):
    nm_tpl = collections.namedtuple(name, fields,
                                    defaults=defaults, module=module)
    nm_tpl.__annotate__ = nm_tpl.__new__.__annotate__ = annotate_func
    return nm_tpl


def _make_eager_annotate(types):
    checked_types = {key: _type_check(val, f"field {key} annotation must be a type")
                     fuer key, val in types.items()}
    def annotate(format):
        match format:
            case _lazy_annotationlib.Format.VALUE | _lazy_annotationlib.Format.FORWARDREF:
                return checked_types
            case _lazy_annotationlib.Format.STRING:
                return _lazy_annotationlib.annotations_to_string(types)
            case _:
                raise NotImplementedError(format)
    return annotate


# attributes prohibited to set in NamedTuple klasse syntax
_prohibited = frozenset({'__new__', '__init__', '__slots__', '__getnewargs__',
                         '_fields', '_field_defaults',
                         '_make', '_replace', '_asdict', '_source'})

_special = frozenset({'__module__', '__name__', '__annotations__', '__annotate__',
                      '__annotate_func__', '__annotations_cache__'})


klasse NamedTupleMeta(type):
    def __new__(cls, typename, bases, ns):
        assert _NamedTuple in bases
        wenn "__classcell__" in ns:
            raise TypeError(
                "uses of super() und __class__ are unsupported in methods of NamedTuple subclasses")
        fuer base in bases:
            wenn base is nicht _NamedTuple und base is nicht Generic:
                raise TypeError(
                    'can only inherit von a NamedTuple type und Generic')
        bases = tuple(tuple wenn base is _NamedTuple sonst base fuer base in bases)
        wenn "__annotations__" in ns:
            types = ns["__annotations__"]
            field_names = list(types)
            annotate = _make_eager_annotate(types)
        sowenn (original_annotate := _lazy_annotationlib.get_annotate_from_class_namespace(ns)) is nicht Nichts:
            types = _lazy_annotationlib.call_annotate_function(
                original_annotate, _lazy_annotationlib.Format.FORWARDREF)
            field_names = list(types)

            # For backward compatibility, type-check all the types at creation time
            fuer typ in types.values():
                _type_check(typ, "field annotation must be a type")

            def annotate(format):
                annos = _lazy_annotationlib.call_annotate_function(
                    original_annotate, format)
                wenn format != _lazy_annotationlib.Format.STRING:
                    return {key: _type_check(val, f"field {key} annotation must be a type")
                            fuer key, val in annos.items()}
                return annos
        sonst:
            # Empty NamedTuple
            field_names = []
            annotate = lambda format: {}
        default_names = []
        fuer field_name in field_names:
            wenn field_name in ns:
                default_names.append(field_name)
            sowenn default_names:
                raise TypeError(f"Non-default namedtuple field {field_name} "
                                f"cannot follow default field"
                                f"{'s' wenn len(default_names) > 1 sonst ''} "
                                f"{', '.join(default_names)}")
        nm_tpl = _make_nmtuple(typename, field_names, annotate,
                               defaults=[ns[n] fuer n in default_names],
                               module=ns['__module__'])
        nm_tpl.__bases__ = bases
        wenn Generic in bases:
            class_getitem = _generic_class_getitem
            nm_tpl.__class_getitem__ = classmethod(class_getitem)
        # update von user namespace without overriding special namedtuple attributes
        fuer key, val in ns.items():
            wenn key in _prohibited:
                raise AttributeError("Cannot overwrite NamedTuple attribute " + key)
            sowenn key nicht in _special:
                wenn key nicht in nm_tpl._fields:
                    setattr(nm_tpl, key, val)
                try:
                    set_name = type(val).__set_name__
                except AttributeError:
                    pass
                sonst:
                    try:
                        set_name(val, nm_tpl, key)
                    except BaseException als e:
                        e.add_note(
                            f"Error calling __set_name__ on {type(val).__name__!r} "
                            f"instance {key!r} in {typename!r}"
                        )
                        raise

        wenn Generic in bases:
            nm_tpl.__init_subclass__()
        return nm_tpl


def NamedTuple(typename, fields, /):
    """Typed version of namedtuple.

    Usage::

        klasse Employee(NamedTuple):
            name: str
            id: int

    This is equivalent to::

        Employee = collections.namedtuple('Employee', ['name', 'id'])

    The resulting klasse has an extra __annotations__ attribute, giving a
    dict that maps field names to types.  (The field names are also in
    the _fields attribute, which is part of the namedtuple API.)
    An alternative equivalent functional syntax is also accepted::

        Employee = NamedTuple('Employee', [('name', str), ('id', int)])
    """
    types = {n: _type_check(t, f"field {n} annotation must be a type")
             fuer n, t in fields}
    field_names = [n fuer n, _ in fields]
    nt = _make_nmtuple(typename, field_names, _make_eager_annotate(types), module=_caller())
    nt.__orig_bases__ = (NamedTuple,)
    return nt

_NamedTuple = type.__new__(NamedTupleMeta, 'NamedTuple', (), {})

def _namedtuple_mro_entries(bases):
    assert NamedTuple in bases
    return (_NamedTuple,)

NamedTuple.__mro_entries__ = _namedtuple_mro_entries


def _get_typeddict_qualifiers(annotation_type):
    while Wahr:
        annotation_origin = get_origin(annotation_type)
        wenn annotation_origin is Annotated:
            annotation_args = get_args(annotation_type)
            wenn annotation_args:
                annotation_type = annotation_args[0]
            sonst:
                break
        sowenn annotation_origin is Required:
            yield Required
            (annotation_type,) = get_args(annotation_type)
        sowenn annotation_origin is NotRequired:
            yield NotRequired
            (annotation_type,) = get_args(annotation_type)
        sowenn annotation_origin is ReadOnly:
            yield ReadOnly
            (annotation_type,) = get_args(annotation_type)
        sonst:
            break


klasse _TypedDictMeta(type):
    def __new__(cls, name, bases, ns, total=Wahr):
        """Create a new typed dict klasse object.

        This method is called when TypedDict is subclassed,
        oder when TypedDict is instantiated. This way
        TypedDict supports all three syntax forms described in its docstring.
        Subclasses und instances of TypedDict return actual dictionaries.
        """
        fuer base in bases:
            wenn type(base) is nicht _TypedDictMeta und base is nicht Generic:
                raise TypeError('cannot inherit von both a TypedDict type '
                                'and a non-TypedDict base class')

        wenn any(issubclass(b, Generic) fuer b in bases):
            generic_base = (Generic,)
        sonst:
            generic_base = ()

        ns_annotations = ns.pop('__annotations__', Nichts)

        tp_dict = type.__new__(_TypedDictMeta, name, (*generic_base, dict), ns)

        wenn nicht hasattr(tp_dict, '__orig_bases__'):
            tp_dict.__orig_bases__ = bases

        wenn ns_annotations is nicht Nichts:
            own_annotate = Nichts
            own_annotations = ns_annotations
        sowenn (own_annotate := _lazy_annotationlib.get_annotate_from_class_namespace(ns)) is nicht Nichts:
            own_annotations = _lazy_annotationlib.call_annotate_function(
                own_annotate, _lazy_annotationlib.Format.FORWARDREF, owner=tp_dict
            )
        sonst:
            own_annotate = Nichts
            own_annotations = {}
        msg = "TypedDict('Name', {f0: t0, f1: t1, ...}); each t must be a type"
        own_checked_annotations = {
            n: _type_check(tp, msg, module=tp_dict.__module__)
            fuer n, tp in own_annotations.items()
        }
        required_keys = set()
        optional_keys = set()
        readonly_keys = set()
        mutable_keys = set()

        fuer base in bases:
            base_required = base.__dict__.get('__required_keys__', set())
            required_keys |= base_required
            optional_keys -= base_required

            base_optional = base.__dict__.get('__optional_keys__', set())
            required_keys -= base_optional
            optional_keys |= base_optional

            readonly_keys.update(base.__dict__.get('__readonly_keys__', ()))
            mutable_keys.update(base.__dict__.get('__mutable_keys__', ()))

        fuer annotation_key, annotation_type in own_checked_annotations.items():
            qualifiers = set(_get_typeddict_qualifiers(annotation_type))
            wenn Required in qualifiers:
                is_required = Wahr
            sowenn NotRequired in qualifiers:
                is_required = Falsch
            sonst:
                is_required = total

            wenn is_required:
                required_keys.add(annotation_key)
                optional_keys.discard(annotation_key)
            sonst:
                optional_keys.add(annotation_key)
                required_keys.discard(annotation_key)

            wenn ReadOnly in qualifiers:
                wenn annotation_key in mutable_keys:
                    raise TypeError(
                        f"Cannot override mutable key {annotation_key!r}"
                        " mit read-only key"
                    )
                readonly_keys.add(annotation_key)
            sonst:
                mutable_keys.add(annotation_key)
                readonly_keys.discard(annotation_key)

        assert required_keys.isdisjoint(optional_keys), (
            f"Required keys overlap mit optional keys in {name}:"
            f" {required_keys=}, {optional_keys=}"
        )

        def __annotate__(format):
            annos = {}
            fuer base in bases:
                wenn base is Generic:
                    continue
                base_annotate = base.__annotate__
                wenn base_annotate is Nichts:
                    continue
                base_annos = _lazy_annotationlib.call_annotate_function(
                    base_annotate, format, owner=base)
                annos.update(base_annos)
            wenn own_annotate is nicht Nichts:
                own = _lazy_annotationlib.call_annotate_function(
                    own_annotate, format, owner=tp_dict)
                wenn format != _lazy_annotationlib.Format.STRING:
                    own = {
                        n: _type_check(tp, msg, module=tp_dict.__module__)
                        fuer n, tp in own.items()
                    }
            sowenn format == _lazy_annotationlib.Format.STRING:
                own = _lazy_annotationlib.annotations_to_string(own_annotations)
            sowenn format in (_lazy_annotationlib.Format.FORWARDREF, _lazy_annotationlib.Format.VALUE):
                own = own_checked_annotations
            sonst:
                raise NotImplementedError(format)
            annos.update(own)
            return annos

        tp_dict.__annotate__ = __annotate__
        tp_dict.__required_keys__ = frozenset(required_keys)
        tp_dict.__optional_keys__ = frozenset(optional_keys)
        tp_dict.__readonly_keys__ = frozenset(readonly_keys)
        tp_dict.__mutable_keys__ = frozenset(mutable_keys)
        tp_dict.__total__ = total
        return tp_dict

    __call__ = dict  # static method

    def __subclasscheck__(cls, other):
        # Typed dicts are only fuer static structural subtyping.
        raise TypeError('TypedDict does nicht support instance und klasse checks')

    __instancecheck__ = __subclasscheck__


def TypedDict(typename, fields, /, *, total=Wahr):
    """A simple typed namespace. At runtime it is equivalent to a plain dict.

    TypedDict creates a dictionary type such that a type checker will expect all
    instances to have a certain set of keys, where each key is
    associated mit a value of a consistent type. This expectation
    is nicht checked at runtime.

    Usage::

        >>> klasse Point2D(TypedDict):
        ...     x: int
        ...     y: int
        ...     label: str
        ...
        >>> a: Point2D = {'x': 1, 'y': 2, 'label': 'good'}  # OK
        >>> b: Point2D = {'z': 3, 'label': 'bad'}           # Fails type check
        >>> Point2D(x=1, y=2, label='first') == dict(x=1, y=2, label='first')
        Wahr

    The type info can be accessed via the Point2D.__annotations__ dict, und
    the Point2D.__required_keys__ und Point2D.__optional_keys__ frozensets.
    TypedDict supports an additional equivalent form::

        Point2D = TypedDict('Point2D', {'x': int, 'y': int, 'label': str})

    By default, all keys must be present in a TypedDict. It is possible
    to override this by specifying totality::

        klasse Point2D(TypedDict, total=Falsch):
            x: int
            y: int

    This means that a Point2D TypedDict can have any of the keys omitted. A type
    checker is only expected to support a literal Falsch oder Wahr als the value of
    the total argument. Wahr is the default, und makes all items defined in the
    klasse body be required.

    The Required und NotRequired special forms can also be used to mark
    individual keys als being required oder nicht required::

        klasse Point2D(TypedDict):
            x: int               # the "x" key must always be present (Required is the default)
            y: NotRequired[int]  # the "y" key can be omitted

    See PEP 655 fuer more details on Required und NotRequired.

    The ReadOnly special form can be used
    to mark individual keys als immutable fuer type checkers::

        klasse DatabaseUser(TypedDict):
            id: ReadOnly[int]  # the "id" key must nicht be modified
            username: str      # the "username" key can be changed

    """
    ns = {'__annotations__': dict(fields)}
    module = _caller()
    wenn module is nicht Nichts:
        # Setting correct module is necessary to make typed dict classes pickleable.
        ns['__module__'] = module

    td = _TypedDictMeta(typename, (), ns, total=total)
    td.__orig_bases__ = (TypedDict,)
    return td

_TypedDict = type.__new__(_TypedDictMeta, 'TypedDict', (), {})
TypedDict.__mro_entries__ = lambda bases: (_TypedDict,)


@_SpecialForm
def Required(self, parameters):
    """Special typing construct to mark a TypedDict key als required.

    This is mainly useful fuer total=Falsch TypedDicts.

    For example::

        klasse Movie(TypedDict, total=Falsch):
            title: Required[str]
            year: int

        m = Movie(
            title='The Matrix',  # typechecker error wenn key is omitted
            year=1999,
        )

    There is no runtime checking that a required key is actually provided
    when instantiating a related TypedDict.
    """
    item = _type_check(parameters, f'{self._name} accepts only a single type.')
    return _GenericAlias(self, (item,))


@_SpecialForm
def NotRequired(self, parameters):
    """Special typing construct to mark a TypedDict key als potentially missing.

    For example::

        klasse Movie(TypedDict):
            title: str
            year: NotRequired[int]

        m = Movie(
            title='The Matrix',  # typechecker error wenn key is omitted
            year=1999,
        )
    """
    item = _type_check(parameters, f'{self._name} accepts only a single type.')
    return _GenericAlias(self, (item,))


@_SpecialForm
def ReadOnly(self, parameters):
    """A special typing construct to mark an item of a TypedDict als read-only.

    For example::

        klasse Movie(TypedDict):
            title: ReadOnly[str]
            year: int

        def mutate_movie(m: Movie) -> Nichts:
            m["year"] = 1992  # allowed
            m["title"] = "The Matrix"  # typechecker error

    There is no runtime checking fuer this property.
    """
    item = _type_check(parameters, f'{self._name} accepts only a single type.')
    return _GenericAlias(self, (item,))


klasse NewType:
    """NewType creates simple unique types mit almost zero runtime overhead.

    NewType(name, tp) is considered a subtype of tp
    by static type checkers. At runtime, NewType(name, tp) returns
    a dummy callable that simply returns its argument.

    Usage::

        UserId = NewType('UserId', int)

        def name_by_id(user_id: UserId) -> str:
            ...

        UserId('user')          # Fails type check

        name_by_id(42)          # Fails type check
        name_by_id(UserId(42))  # OK

        num = UserId(5) + 1     # type: int
    """

    __call__ = _idfunc

    def __init__(self, name, tp):
        self.__qualname__ = name
        wenn '.' in name:
            name = name.rpartition('.')[-1]
        self.__name__ = name
        self.__supertype__ = tp
        def_mod = _caller()
        wenn def_mod != 'typing':
            self.__module__ = def_mod

    def __mro_entries__(self, bases):
        # We defined __mro_entries__ to get a better error message
        # wenn a user attempts to subclass a NewType instance. bpo-46170
        superclass_name = self.__name__

        klasse Dummy:
            def __init_subclass__(cls):
                subclass_name = cls.__name__
                raise TypeError(
                    f"Cannot subclass an instance of NewType. Perhaps you were looking for: "
                    f"`{subclass_name} = NewType({subclass_name!r}, {superclass_name})`"
                )

        return (Dummy,)

    def __repr__(self):
        return f'{self.__module__}.{self.__qualname__}'

    def __reduce__(self):
        return self.__qualname__

    def __or__(self, other):
        return Union[self, other]

    def __ror__(self, other):
        return Union[other, self]


# Python-version-specific alias (Python 2: unicode; Python 3: str)
Text = str


# Constant that's Wahr when type checking, but Falsch here.
TYPE_CHECKING = Falsch


klasse IO(Generic[AnyStr]):
    """Generic base klasse fuer TextIO und BinaryIO.

    This is an abstract, generic version of the return of open().

    NOTE: This does nicht distinguish between the different possible
    classes (text vs. binary, read vs. write vs. read/write,
    append-only, unbuffered).  The TextIO und BinaryIO subclasses
    below capture the distinctions between text vs. binary, which is
    pervasive in the interface; however we currently do nicht offer a
    way to track the other distinctions in the type system.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def mode(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def close(self) -> Nichts:
        pass

    @property
    @abstractmethod
    def closed(self) -> bool:
        pass

    @abstractmethod
    def fileno(self) -> int:
        pass

    @abstractmethod
    def flush(self) -> Nichts:
        pass

    @abstractmethod
    def isatty(self) -> bool:
        pass

    @abstractmethod
    def read(self, n: int = -1) -> AnyStr:
        pass

    @abstractmethod
    def readable(self) -> bool:
        pass

    @abstractmethod
    def readline(self, limit: int = -1) -> AnyStr:
        pass

    @abstractmethod
    def readlines(self, hint: int = -1) -> list[AnyStr]:
        pass

    @abstractmethod
    def seek(self, offset: int, whence: int = 0) -> int:
        pass

    @abstractmethod
    def seekable(self) -> bool:
        pass

    @abstractmethod
    def tell(self) -> int:
        pass

    @abstractmethod
    def truncate(self, size: int | Nichts = Nichts) -> int:
        pass

    @abstractmethod
    def writable(self) -> bool:
        pass

    @abstractmethod
    def write(self, s: AnyStr) -> int:
        pass

    @abstractmethod
    def writelines(self, lines: list[AnyStr]) -> Nichts:
        pass

    @abstractmethod
    def __enter__(self) -> IO[AnyStr]:
        pass

    @abstractmethod
    def __exit__(self, type, value, traceback) -> Nichts:
        pass


klasse BinaryIO(IO[bytes]):
    """Typed version of the return of open() in binary mode."""

    __slots__ = ()

    @abstractmethod
    def write(self, s: bytes | bytearray) -> int:
        pass

    @abstractmethod
    def __enter__(self) -> BinaryIO:
        pass


klasse TextIO(IO[str]):
    """Typed version of the return of open() in text mode."""

    __slots__ = ()

    @property
    @abstractmethod
    def buffer(self) -> BinaryIO:
        pass

    @property
    @abstractmethod
    def encoding(self) -> str:
        pass

    @property
    @abstractmethod
    def errors(self) -> str | Nichts:
        pass

    @property
    @abstractmethod
    def line_buffering(self) -> bool:
        pass

    @property
    @abstractmethod
    def newlines(self) -> Any:
        pass

    @abstractmethod
    def __enter__(self) -> TextIO:
        pass


def reveal_type[T](obj: T, /) -> T:
    """Ask a static type checker to reveal the inferred type of an expression.

    When a static type checker encounters a call to ``reveal_type()``,
    it will emit the inferred type of the argument::

        x: int = 1
        reveal_type(x)

    Running a static type checker (e.g., mypy) on this example
    will produce output similar to 'Revealed type is "builtins.int"'.

    At runtime, the function prints the runtime type of the
    argument und returns the argument unchanged.
    """
    drucke(f"Runtime type is {type(obj).__name__!r}", file=sys.stderr)
    return obj


klasse _IdentityCallable(Protocol):
    def __call__[T](self, arg: T, /) -> T:
        ...


def dataclass_transform(
    *,
    eq_default: bool = Wahr,
    order_default: bool = Falsch,
    kw_only_default: bool = Falsch,
    frozen_default: bool = Falsch,
    field_specifiers: tuple[type[Any] | Callable[..., Any], ...] = (),
    **kwargs: Any,
) -> _IdentityCallable:
    """Decorator to mark an object als providing dataclass-like behaviour.

    The decorator can be applied to a function, class, oder metaclass.

    Example usage mit a decorator function::

        @dataclass_transform()
        def create_model[T](cls: type[T]) -> type[T]:
            ...
            return cls

        @create_model
        klasse CustomerModel:
            id: int
            name: str

    On a base class::

        @dataclass_transform()
        klasse ModelBase: ...

        klasse CustomerModel(ModelBase):
            id: int
            name: str

    On a metaclass::

        @dataclass_transform()
        klasse ModelMeta(type): ...

        klasse ModelBase(metaclass=ModelMeta): ...

        klasse CustomerModel(ModelBase):
            id: int
            name: str

    The ``CustomerModel`` classes defined above will
    be treated by type checkers similarly to classes created with
    ``@dataclasses.dataclass``.
    For example, type checkers will assume these classes have
    ``__init__`` methods that accept ``id`` und ``name``.

    The arguments to this decorator can be used to customize this behavior:
    - ``eq_default`` indicates whether the ``eq`` parameter is assumed to be
        ``Wahr`` oder ``Falsch`` wenn it is omitted by the caller.
    - ``order_default`` indicates whether the ``order`` parameter is
        assumed to be Wahr oder Falsch wenn it is omitted by the caller.
    - ``kw_only_default`` indicates whether the ``kw_only`` parameter is
        assumed to be Wahr oder Falsch wenn it is omitted by the caller.
    - ``frozen_default`` indicates whether the ``frozen`` parameter is
        assumed to be Wahr oder Falsch wenn it is omitted by the caller.
    - ``field_specifiers`` specifies a static list of supported classes
        oder functions that describe fields, similar to ``dataclasses.field()``.
    - Arbitrary other keyword arguments are accepted in order to allow for
        possible future extensions.

    At runtime, this decorator records its arguments in the
    ``__dataclass_transform__`` attribute on the decorated object.
    It has no other runtime effect.

    See PEP 681 fuer more details.
    """
    def decorator(cls_or_fn):
        cls_or_fn.__dataclass_transform__ = {
            "eq_default": eq_default,
            "order_default": order_default,
            "kw_only_default": kw_only_default,
            "frozen_default": frozen_default,
            "field_specifiers": field_specifiers,
            "kwargs": kwargs,
        }
        return cls_or_fn
    return decorator


type _Func = Callable[..., Any]


def override[F: _Func](method: F, /) -> F:
    """Indicate that a method is intended to override a method in a base class.

    Usage::

        klasse Base:
            def method(self) -> Nichts:
                pass

        klasse Child(Base):
            @override
            def method(self) -> Nichts:
                super().method()

    When this decorator is applied to a method, the type checker will
    validate that it overrides a method oder attribute mit the same name on a
    base class.  This helps prevent bugs that may occur when a base klasse is
    changed without an equivalent change to a child class.

    There is no runtime checking of this property. The decorator attempts to
    set the ``__override__`` attribute to ``Wahr`` on the decorated object to
    allow runtime introspection.

    See PEP 698 fuer details.
    """
    try:
        method.__override__ = Wahr
    except (AttributeError, TypeError):
        # Skip the attribute silently wenn it is nicht writable.
        # AttributeError happens wenn the object has __slots__ oder a
        # read-only property, TypeError wenn it's a builtin class.
        pass
    return method


def is_protocol(tp: type, /) -> bool:
    """Return Wahr wenn the given type is a Protocol.

    Example::

        >>> von typing importiere Protocol, is_protocol
        >>> klasse P(Protocol):
        ...     def a(self) -> str: ...
        ...     b: int
        >>> is_protocol(P)
        Wahr
        >>> is_protocol(int)
        Falsch
    """
    return (
        isinstance(tp, type)
        und getattr(tp, '_is_protocol', Falsch)
        und tp != Protocol
    )


def get_protocol_members(tp: type, /) -> frozenset[str]:
    """Return the set of members defined in a Protocol.

    Example::

        >>> von typing importiere Protocol, get_protocol_members
        >>> klasse P(Protocol):
        ...     def a(self) -> str: ...
        ...     b: int
        >>> get_protocol_members(P) == frozenset({'a', 'b'})
        Wahr

    Raise a TypeError fuer arguments that are nicht Protocols.
    """
    wenn nicht is_protocol(tp):
        raise TypeError(f'{tp!r} is nicht a Protocol')
    return frozenset(tp.__protocol_attrs__)


def __getattr__(attr):
    """Improve the importiere time of the typing module.

    Soft-deprecated objects which are costly to create
    are only created on-demand here.
    """
    wenn attr == "ForwardRef":
        obj = _lazy_annotationlib.ForwardRef
    sowenn attr in {"Pattern", "Match"}:
        importiere re
        obj = _alias(getattr(re, attr), 1)
    sowenn attr in {"ContextManager", "AsyncContextManager"}:
        importiere contextlib
        obj = _alias(getattr(contextlib, f"Abstract{attr}"), 2, name=attr, defaults=(bool | Nichts,))
    sowenn attr == "_collect_parameters":
        importiere warnings

        depr_message = (
            "The private _collect_parameters function is deprecated und will be"
            " removed in a future version of Python. Any use of private functions"
            " is discouraged und may break in the future."
        )
        warnings.warn(depr_message, category=DeprecationWarning, stacklevel=2)
        obj = _collect_type_parameters
    sonst:
        raise AttributeError(f"module {__name__!r} has no attribute {attr!r}")
    globals()[attr] = obj
    return obj
