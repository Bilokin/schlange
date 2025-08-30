importiere annotationlib
importiere contextlib
importiere collections
importiere collections.abc
von collections importiere defaultdict
von functools importiere lru_cache, wraps, reduce
importiere gc
importiere inspect
importiere io
importiere itertools
importiere operator
importiere os
importiere pickle
importiere re
importiere sys
von unittest importiere TestCase, main, skip
von unittest.mock importiere patch
von copy importiere copy, deepcopy

von typing importiere Any, NoReturn, Never, assert_never
von typing importiere overload, get_overloads, clear_overloads
von typing importiere TypeVar, TypeVarTuple, Unpack, AnyStr
von typing importiere T, KT, VT  # Not in __all__.
von typing importiere Union, Optional, Literal
von typing importiere Tuple, List, Dict, MutableMapping
von typing importiere Callable
von typing importiere Generic, ClassVar, Final, final, Protocol
von typing importiere assert_type, cast, runtime_checkable
von typing importiere get_type_hints
von typing importiere get_origin, get_args, get_protocol_members
von typing importiere override
von typing importiere is_typeddict, is_protocol
von typing importiere reveal_type
von typing importiere dataclass_transform
von typing importiere no_type_check, no_type_check_decorator
von typing importiere Type
von typing importiere NamedTuple, NotRequired, Required, ReadOnly, TypedDict
von typing importiere IO, TextIO, BinaryIO
von typing importiere Pattern, Match
von typing importiere Annotated, ForwardRef
von typing importiere Self, LiteralString
von typing importiere TypeAlias
von typing importiere ParamSpec, Concatenate, ParamSpecArgs, ParamSpecKwargs
von typing importiere TypeGuard, TypeIs, NoDefault
importiere abc
importiere textwrap
importiere typing
importiere weakref
importiere types

von test.support importiere (
    captured_stderr, cpython_only, requires_docstrings, import_helper, run_code,
    EqualToForwardRef,
)
von test.typinganndata importiere (
    ann_module695, mod_generics_cache, _typed_dict_helper,
    ann_module, ann_module2, ann_module3, ann_module5, ann_module6, ann_module8
)


CANNOT_SUBCLASS_TYPE = 'Cannot subclass special typing classes'
NOT_A_BASE_TYPE = "type 'typing.%s' ist nicht an acceptable base type"
CANNOT_SUBCLASS_INSTANCE = 'Cannot subclass an instance of %s'


klasse BaseTestCase(TestCase):

    def clear_caches(self):
        fuer f in typing._cleanups:
            f()


def all_pickle_protocols(test_func):
    """Runs `test_func` mit various values fuer `proto` argument."""

    @wraps(test_func)
    def wrapper(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(pickle_proto=proto):
                test_func(self, proto=proto)

    gib wrapper


klasse Employee:
    pass


klasse Manager(Employee):
    pass


klasse Founder(Employee):
    pass


klasse ManagingFounder(Manager, Founder):
    pass


klasse AnyTests(BaseTestCase):

    def test_any_instance_type_error(self):
        mit self.assertRaises(TypeError):
            isinstance(42, Any)

    def test_repr(self):
        self.assertEqual(repr(Any), 'typing.Any')

        klasse Sub(Any): pass
        self.assertEqual(
            repr(Sub),
            f"<class '{__name__}.AnyTests.test_repr.<locals>.Sub'>",
        )

    def test_errors(self):
        mit self.assertRaises(TypeError):
            isinstance(42, Any)
        mit self.assertRaises(TypeError):
            Any[int]  # Any ist nicht a generic type.

    def test_can_subclass(self):
        klasse Mock(Any): pass
        self.assertIsSubclass(Mock, Any)
        self.assertIsInstance(Mock(), Mock)

        klasse Something: pass
        self.assertNotIsSubclass(Something, Any)
        self.assertNotIsInstance(Something(), Mock)

        klasse MockSomething(Something, Mock): pass
        self.assertIsSubclass(MockSomething, Any)
        self.assertIsSubclass(MockSomething, MockSomething)
        self.assertIsSubclass(MockSomething, Something)
        self.assertIsSubclass(MockSomething, Mock)
        ms = MockSomething()
        self.assertIsInstance(ms, MockSomething)
        self.assertIsInstance(ms, Something)
        self.assertIsInstance(ms, Mock)

    def test_subclassing_with_custom_constructor(self):
        klasse Sub(Any):
            def __init__(self, *args, **kwargs): pass
        # The instantiation must nicht fail.
        Sub(0, s="")

    def test_multiple_inheritance_with_custom_constructors(self):
        klasse Foo:
            def __init__(self, x):
                self.x = x

        klasse Bar(Any, Foo):
            def __init__(self, x, y):
                self.y = y
                super().__init__(x)

        b = Bar(1, 2)
        self.assertEqual(b.x, 1)
        self.assertEqual(b.y, 2)

    def test_cannot_instantiate(self):
        mit self.assertRaises(TypeError):
            Any()
        mit self.assertRaises(TypeError):
            type(Any)()

    def test_any_works_with_alias(self):
        # These expressions must simply nicht fail.
        typing.Match[Any]
        typing.Pattern[Any]
        typing.IO[Any]


klasse BottomTypeTestsMixin:
    bottom_type: ClassVar[Any]

    def test_equality(self):
        self.assertEqual(self.bottom_type, self.bottom_type)
        self.assertIs(self.bottom_type, self.bottom_type)
        self.assertNotEqual(self.bottom_type, Nichts)

    def test_get_origin(self):
        self.assertIs(get_origin(self.bottom_type), Nichts)

    def test_instance_type_error(self):
        mit self.assertRaises(TypeError):
            isinstance(42, self.bottom_type)

    def test_subclass_type_error(self):
        mit self.assertRaises(TypeError):
            issubclass(Employee, self.bottom_type)
        mit self.assertRaises(TypeError):
            issubclass(NoReturn, self.bottom_type)

    def test_not_generic(self):
        mit self.assertRaises(TypeError):
            self.bottom_type[int]

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError,
                'Cannot subclass ' + re.escape(str(self.bottom_type))):
            klasse A(self.bottom_type):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse B(type(self.bottom_type)):
                pass

    def test_cannot_instantiate(self):
        mit self.assertRaises(TypeError):
            self.bottom_type()
        mit self.assertRaises(TypeError):
            type(self.bottom_type)()


klasse NoReturnTests(BottomTypeTestsMixin, BaseTestCase):
    bottom_type = NoReturn

    def test_repr(self):
        self.assertEqual(repr(NoReturn), 'typing.NoReturn')

    def test_get_type_hints(self):
        def some(arg: NoReturn) -> NoReturn: ...
        def some_str(arg: 'NoReturn') -> 'typing.NoReturn': ...

        expected = {'arg': NoReturn, 'return': NoReturn}
        fuer target in [some, some_str]:
            mit self.subTest(target=target):
                self.assertEqual(gth(target), expected)

    def test_not_equality(self):
        self.assertNotEqual(NoReturn, Never)
        self.assertNotEqual(Never, NoReturn)


klasse NeverTests(BottomTypeTestsMixin, BaseTestCase):
    bottom_type = Never

    def test_repr(self):
        self.assertEqual(repr(Never), 'typing.Never')

    def test_get_type_hints(self):
        def some(arg: Never) -> Never: ...
        def some_str(arg: 'Never') -> 'typing.Never': ...

        expected = {'arg': Never, 'return': Never}
        fuer target in [some, some_str]:
            mit self.subTest(target=target):
                self.assertEqual(gth(target), expected)


klasse AssertNeverTests(BaseTestCase):
    def test_exception(self):
        mit self.assertRaises(AssertionError):
            assert_never(Nichts)

        value = "some value"
        mit self.assertRaisesRegex(AssertionError, value):
            assert_never(value)

        # Make sure a huge value doesn't get printed in its entirety
        huge_value = "a" * 10000
        mit self.assertRaises(AssertionError) als cm:
            assert_never(huge_value)
        self.assertLess(
            len(cm.exception.args[0]),
            typing._ASSERT_NEVER_REPR_MAX_LENGTH * 2,
        )


klasse SelfTests(BaseTestCase):
    def test_equality(self):
        self.assertEqual(Self, Self)
        self.assertIs(Self, Self)
        self.assertNotEqual(Self, Nichts)

    def test_basics(self):
        klasse Foo:
            def bar(self) -> Self: ...
        klasse FooStr:
            def bar(self) -> 'Self': ...
        klasse FooStrTyping:
            def bar(self) -> 'typing.Self': ...

        fuer target in [Foo, FooStr, FooStrTyping]:
            mit self.subTest(target=target):
                self.assertEqual(gth(target.bar), {'return': Self})
        self.assertIs(get_origin(Self), Nichts)

    def test_repr(self):
        self.assertEqual(repr(Self), 'typing.Self')

    def test_cannot_subscript(self):
        mit self.assertRaises(TypeError):
            Self[int]

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(Self)):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.Self'):
            klasse D(Self):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            Self()
        mit self.assertRaises(TypeError):
            type(Self)()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, Self)
        mit self.assertRaises(TypeError):
            issubclass(int, Self)

    def test_alias(self):
        # TypeAliases are nicht actually part of the spec
        alias_1 = Tuple[Self, Self]
        alias_2 = List[Self]
        alias_3 = ClassVar[Self]
        self.assertEqual(get_args(alias_1), (Self, Self))
        self.assertEqual(get_args(alias_2), (Self,))
        self.assertEqual(get_args(alias_3), (Self,))


klasse LiteralStringTests(BaseTestCase):
    def test_equality(self):
        self.assertEqual(LiteralString, LiteralString)
        self.assertIs(LiteralString, LiteralString)
        self.assertNotEqual(LiteralString, Nichts)

    def test_basics(self):
        klasse Foo:
            def bar(self) -> LiteralString: ...
        klasse FooStr:
            def bar(self) -> 'LiteralString': ...
        klasse FooStrTyping:
            def bar(self) -> 'typing.LiteralString': ...

        fuer target in [Foo, FooStr, FooStrTyping]:
            mit self.subTest(target=target):
                self.assertEqual(gth(target.bar), {'return': LiteralString})
        self.assertIs(get_origin(LiteralString), Nichts)

    def test_repr(self):
        self.assertEqual(repr(LiteralString), 'typing.LiteralString')

    def test_cannot_subscript(self):
        mit self.assertRaises(TypeError):
            LiteralString[int]

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(LiteralString)):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.LiteralString'):
            klasse D(LiteralString):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            LiteralString()
        mit self.assertRaises(TypeError):
            type(LiteralString)()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, LiteralString)
        mit self.assertRaises(TypeError):
            issubclass(int, LiteralString)

    def test_alias(self):
        alias_1 = Tuple[LiteralString, LiteralString]
        alias_2 = List[LiteralString]
        alias_3 = ClassVar[LiteralString]
        self.assertEqual(get_args(alias_1), (LiteralString, LiteralString))
        self.assertEqual(get_args(alias_2), (LiteralString,))
        self.assertEqual(get_args(alias_3), (LiteralString,))


klasse TypeVarTests(BaseTestCase):
    def test_basic_plain(self):
        T = TypeVar('T')
        # T equals itself.
        self.assertEqual(T, T)
        # T ist an instance of TypeVar
        self.assertIsInstance(T, TypeVar)
        self.assertEqual(T.__name__, 'T')
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)
        self.assertEqual(T.__module__, __name__)

    def test_basic_with_exec(self):
        ns = {}
        exec('from typing importiere TypeVar; T = TypeVar("T", bound=float)', ns, ns)
        T = ns['T']
        self.assertIsInstance(T, TypeVar)
        self.assertEqual(T.__name__, 'T')
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, float)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)
        self.assertIs(T.__module__, Nichts)

    def test_attributes(self):
        T_bound = TypeVar('T_bound', bound=int)
        self.assertEqual(T_bound.__name__, 'T_bound')
        self.assertEqual(T_bound.__constraints__, ())
        self.assertIs(T_bound.__bound__, int)

        T_constraints = TypeVar('T_constraints', int, str)
        self.assertEqual(T_constraints.__name__, 'T_constraints')
        self.assertEqual(T_constraints.__constraints__, (int, str))
        self.assertIs(T_constraints.__bound__, Nichts)

        T_co = TypeVar('T_co', covariant=Wahr)
        self.assertEqual(T_co.__name__, 'T_co')
        self.assertIs(T_co.__covariant__, Wahr)
        self.assertIs(T_co.__contravariant__, Falsch)
        self.assertIs(T_co.__infer_variance__, Falsch)

        T_contra = TypeVar('T_contra', contravariant=Wahr)
        self.assertEqual(T_contra.__name__, 'T_contra')
        self.assertIs(T_contra.__covariant__, Falsch)
        self.assertIs(T_contra.__contravariant__, Wahr)
        self.assertIs(T_contra.__infer_variance__, Falsch)

        T_infer = TypeVar('T_infer', infer_variance=Wahr)
        self.assertEqual(T_infer.__name__, 'T_infer')
        self.assertIs(T_infer.__covariant__, Falsch)
        self.assertIs(T_infer.__contravariant__, Falsch)
        self.assertIs(T_infer.__infer_variance__, Wahr)

    def test_typevar_instance_type_error(self):
        T = TypeVar('T')
        mit self.assertRaises(TypeError):
            isinstance(42, T)

    def test_typevar_subclass_type_error(self):
        T = TypeVar('T')
        mit self.assertRaises(TypeError):
            issubclass(int, T)
        mit self.assertRaises(TypeError):
            issubclass(T, int)

    def test_constrained_error(self):
        mit self.assertRaises(TypeError):
            X = TypeVar('X', int)
            X

    def test_union_unique(self):
        X = TypeVar('X')
        Y = TypeVar('Y')
        self.assertNotEqual(X, Y)
        self.assertEqual(Union[X], X)
        self.assertNotEqual(Union[X], Union[X, Y])
        self.assertEqual(Union[X, X], X)
        self.assertNotEqual(Union[X, int], Union[X])
        self.assertNotEqual(Union[X, int], Union[int])
        self.assertEqual(Union[X, int].__args__, (X, int))
        self.assertEqual(Union[X, int].__parameters__, (X,))
        self.assertIs(Union[X, int].__origin__, Union)

    def test_or(self):
        X = TypeVar('X')
        # use a string because str doesn't implement
        # __or__/__ror__ itself
        self.assertEqual(X | "x", Union[X, "x"])
        self.assertEqual("x" | X, Union["x", X])
        # make sure the order ist correct
        self.assertEqual(get_args(X | "x"), (X, EqualToForwardRef("x")))
        self.assertEqual(get_args("x" | X), (EqualToForwardRef("x"), X))

    def test_union_constrained(self):
        A = TypeVar('A', str, bytes)
        self.assertNotEqual(Union[A, str], Union[A])

    def test_repr(self):
        self.assertEqual(repr(T), '~T')
        self.assertEqual(repr(KT), '~KT')
        self.assertEqual(repr(VT), '~VT')
        self.assertEqual(repr(AnyStr), '~AnyStr')
        T_co = TypeVar('T_co', covariant=Wahr)
        self.assertEqual(repr(T_co), '+T_co')
        T_contra = TypeVar('T_contra', contravariant=Wahr)
        self.assertEqual(repr(T_contra), '-T_contra')

    def test_no_redefinition(self):
        self.assertNotEqual(TypeVar('T'), TypeVar('T'))
        self.assertNotEqual(TypeVar('T', int, str), TypeVar('T', int, str))

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, NOT_A_BASE_TYPE % 'TypeVar'):
            klasse V(TypeVar): pass
        T = TypeVar("T")
        mit self.assertRaisesRegex(TypeError,
                CANNOT_SUBCLASS_INSTANCE % 'TypeVar'):
            klasse W(T): pass

    def test_cannot_instantiate_vars(self):
        mit self.assertRaises(TypeError):
            TypeVar('A')()

    def test_bound_errors(self):
        mit self.assertRaises(TypeError):
            TypeVar('X', bound=Optional)
        mit self.assertRaises(TypeError):
            TypeVar('X', str, float, bound=Employee)
        mit self.assertRaisesRegex(TypeError,
                                    r"Bound must be a type\. Got \(1, 2\)\."):
            TypeVar('X', bound=(1, 2))

    def test_missing__name__(self):
        # See bpo-39942
        code = ("import typing\n"
                "T = typing.TypeVar('T')\n"
                )
        exec(code, {})

    def test_no_bivariant(self):
        mit self.assertRaises(ValueError):
            TypeVar('T', covariant=Wahr, contravariant=Wahr)

    def test_cannot_combine_explicit_and_infer(self):
        mit self.assertRaises(ValueError):
            TypeVar('T', covariant=Wahr, infer_variance=Wahr)
        mit self.assertRaises(ValueError):
            TypeVar('T', contravariant=Wahr, infer_variance=Wahr)

    def test_var_substitution(self):
        T = TypeVar('T')
        subst = T.__typing_subst__
        self.assertIs(subst(int), int)
        self.assertEqual(subst(list[int]), list[int])
        self.assertEqual(subst(List[int]), List[int])
        self.assertEqual(subst(List), List)
        self.assertIs(subst(Any), Any)
        self.assertIs(subst(Nichts), type(Nichts))
        self.assertIs(subst(T), T)
        self.assertEqual(subst(int|str), int|str)
        self.assertEqual(subst(Union[int, str]), Union[int, str])

    def test_bad_var_substitution(self):
        T = TypeVar('T')
        bad_args = (
            (), (int, str), Optional,
            Generic, Generic[T], Protocol, Protocol[T],
            Final, Final[int], ClassVar, ClassVar[int],
        )
        fuer arg in bad_args:
            mit self.subTest(arg=arg):
                mit self.assertRaises(TypeError):
                    T.__typing_subst__(arg)
                mit self.assertRaises(TypeError):
                    List[T][arg]
                mit self.assertRaises(TypeError):
                    list[T][arg]

    def test_many_weakrefs(self):
        # gh-108295: this used to segfault
        fuer cls in (ParamSpec, TypeVarTuple, TypeVar):
            mit self.subTest(cls=cls):
                vals = weakref.WeakValueDictionary()

                fuer x in range(10):
                    vals[x] = cls(str(x))
                loesche vals

    def test_constructor(self):
        T = TypeVar(name="T")
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__default__, typing.NoDefault)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)

        T = TypeVar(name="T", bound=type)
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, type)
        self.assertIs(T.__default__, typing.NoDefault)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)

        T = TypeVar(name="T", default=())
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__default__, ())
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)

        T = TypeVar(name="T", covariant=Wahr)
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__default__, typing.NoDefault)
        self.assertIs(T.__covariant__, Wahr)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Falsch)

        T = TypeVar(name="T", contravariant=Wahr)
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__default__, typing.NoDefault)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Wahr)
        self.assertIs(T.__infer_variance__, Falsch)

        T = TypeVar(name="T", infer_variance=Wahr)
        self.assertEqual(T.__name__, "T")
        self.assertEqual(T.__constraints__, ())
        self.assertIs(T.__bound__, Nichts)
        self.assertIs(T.__default__, typing.NoDefault)
        self.assertIs(T.__covariant__, Falsch)
        self.assertIs(T.__contravariant__, Falsch)
        self.assertIs(T.__infer_variance__, Wahr)


klasse TypeParameterDefaultsTests(BaseTestCase):
    def test_typevar(self):
        T = TypeVar('T', default=int)
        self.assertEqual(T.__default__, int)
        self.assertIs(T.has_default(), Wahr)
        self.assertIsInstance(T, TypeVar)

        klasse A(Generic[T]): ...
        Alias = Optional[T]

    def test_typevar_none(self):
        U = TypeVar('U')
        U_Nichts = TypeVar('U_Nichts', default=Nichts)
        self.assertIs(U.__default__, NoDefault)
        self.assertIs(U.has_default(), Falsch)
        self.assertIs(U_Nichts.__default__, Nichts)
        self.assertIs(U_Nichts.has_default(), Wahr)

        klasse X[T]: ...
        T, = X.__type_params__
        self.assertIs(T.__default__, NoDefault)
        self.assertIs(T.has_default(), Falsch)

    def test_paramspec(self):
        P = ParamSpec('P', default=(str, int))
        self.assertEqual(P.__default__, (str, int))
        self.assertIs(P.has_default(), Wahr)
        self.assertIsInstance(P, ParamSpec)

        klasse A(Generic[P]): ...
        Alias = typing.Callable[P, Nichts]

        P_default = ParamSpec('P_default', default=...)
        self.assertIs(P_default.__default__, ...)

    def test_paramspec_none(self):
        U = ParamSpec('U')
        U_Nichts = ParamSpec('U_Nichts', default=Nichts)
        self.assertIs(U.__default__, NoDefault)
        self.assertIs(U.has_default(), Falsch)
        self.assertIs(U_Nichts.__default__, Nichts)
        self.assertIs(U_Nichts.has_default(), Wahr)

        klasse X[**P]: ...
        P, = X.__type_params__
        self.assertIs(P.__default__, NoDefault)
        self.assertIs(P.has_default(), Falsch)

    def test_typevartuple(self):
        Ts = TypeVarTuple('Ts', default=Unpack[Tuple[str, int]])
        self.assertEqual(Ts.__default__, Unpack[Tuple[str, int]])
        self.assertIs(Ts.has_default(), Wahr)
        self.assertIsInstance(Ts, TypeVarTuple)

        klasse A(Generic[Unpack[Ts]]): ...
        Alias = Optional[Unpack[Ts]]

    def test_typevartuple_specialization(self):
        T = TypeVar("T")
        Ts = TypeVarTuple('Ts', default=Unpack[Tuple[str, int]])
        self.assertEqual(Ts.__default__, Unpack[Tuple[str, int]])
        klasse A(Generic[T, Unpack[Ts]]): ...
        self.assertEqual(A[float].__args__, (float, str, int))
        self.assertEqual(A[float, range].__args__, (float, range))
        self.assertEqual(A[float, *tuple[int, ...]].__args__, (float, *tuple[int, ...]))

    def test_typevar_and_typevartuple_specialization(self):
        T = TypeVar("T")
        U = TypeVar("U", default=float)
        Ts = TypeVarTuple('Ts', default=Unpack[Tuple[str, int]])
        self.assertEqual(Ts.__default__, Unpack[Tuple[str, int]])
        klasse A(Generic[T, U, Unpack[Ts]]): ...
        self.assertEqual(A[int].__args__, (int, float, str, int))
        self.assertEqual(A[int, str].__args__, (int, str, str, int))
        self.assertEqual(A[int, str, range].__args__, (int, str, range))
        self.assertEqual(A[int, str, *tuple[int, ...]].__args__, (int, str, *tuple[int, ...]))

    def test_no_default_after_typevar_tuple(self):
        T = TypeVar("T", default=int)
        Ts = TypeVarTuple("Ts")
        Ts_default = TypeVarTuple("Ts_default", default=Unpack[Tuple[str, int]])

        mit self.assertRaises(TypeError):
            klasse X(Generic[*Ts, T]): ...

        mit self.assertRaises(TypeError):
            klasse Y(Generic[*Ts_default, T]): ...

    def test_allow_default_after_non_default_in_alias(self):
        T_default = TypeVar('T_default', default=int)
        T = TypeVar('T')
        Ts = TypeVarTuple('Ts')

        a1 = Callable[[T_default], T]
        self.assertEqual(a1.__args__, (T_default, T))

        a2 = dict[T_default, T]
        self.assertEqual(a2.__args__, (T_default, T))

        a3 = typing.Dict[T_default, T]
        self.assertEqual(a3.__args__, (T_default, T))

        a4 = Callable[*Ts, T]
        self.assertEqual(a4.__args__, (*Ts, T))

    def test_paramspec_specialization(self):
        T = TypeVar("T")
        P = ParamSpec('P', default=[str, int])
        self.assertEqual(P.__default__, [str, int])
        klasse A(Generic[T, P]): ...
        self.assertEqual(A[float].__args__, (float, (str, int)))
        self.assertEqual(A[float, [range]].__args__, (float, (range,)))

    def test_typevar_and_paramspec_specialization(self):
        T = TypeVar("T")
        U = TypeVar("U", default=float)
        P = ParamSpec('P', default=[str, int])
        self.assertEqual(P.__default__, [str, int])
        klasse A(Generic[T, U, P]): ...
        self.assertEqual(A[float].__args__, (float, float, (str, int)))
        self.assertEqual(A[float, int].__args__, (float, int, (str, int)))
        self.assertEqual(A[float, int, [range]].__args__, (float, int, (range,)))

    def test_paramspec_and_typevar_specialization(self):
        T = TypeVar("T")
        P = ParamSpec('P', default=[str, int])
        U = TypeVar("U", default=float)
        self.assertEqual(P.__default__, [str, int])
        klasse A(Generic[T, P, U]): ...
        self.assertEqual(A[float].__args__, (float, (str, int), float))
        self.assertEqual(A[float, [range]].__args__, (float, (range,), float))
        self.assertEqual(A[float, [range], int].__args__, (float, (range,), int))

    def test_typevartuple_none(self):
        U = TypeVarTuple('U')
        U_Nichts = TypeVarTuple('U_Nichts', default=Nichts)
        self.assertIs(U.__default__, NoDefault)
        self.assertIs(U.has_default(), Falsch)
        self.assertIs(U_Nichts.__default__, Nichts)
        self.assertIs(U_Nichts.has_default(), Wahr)

        klasse X[**Ts]: ...
        Ts, = X.__type_params__
        self.assertIs(Ts.__default__, NoDefault)
        self.assertIs(Ts.has_default(), Falsch)

    def test_no_default_after_non_default(self):
        DefaultStrT = TypeVar('DefaultStrT', default=str)
        T = TypeVar('T')

        mit self.assertRaisesRegex(
            TypeError, r"Type parameter ~T without a default follows type parameter mit a default"
        ):
            Test = Generic[DefaultStrT, T]

    def test_need_more_params(self):
        DefaultStrT = TypeVar('DefaultStrT', default=str)
        T = TypeVar('T')
        U = TypeVar('U')

        klasse A(Generic[T, U, DefaultStrT]): ...
        A[int, bool]
        A[int, bool, str]

        mit self.assertRaisesRegex(
            TypeError, r"Too few arguments fuer .+; actual 1, expected at least 2"
        ):
            Test = A[int]

    def test_pickle(self):
        global U, U_co, U_contra, U_default  # pickle wants to reference the klasse by name
        U = TypeVar('U')
        U_co = TypeVar('U_co', covariant=Wahr)
        U_contra = TypeVar('U_contra', contravariant=Wahr)
        U_default = TypeVar('U_default', default=int)
        fuer proto in range(pickle.HIGHEST_PROTOCOL):
            fuer typevar in (U, U_co, U_contra, U_default):
                z = pickle.loads(pickle.dumps(typevar, proto))
                self.assertEqual(z.__name__, typevar.__name__)
                self.assertEqual(z.__covariant__, typevar.__covariant__)
                self.assertEqual(z.__contravariant__, typevar.__contravariant__)
                self.assertEqual(z.__bound__, typevar.__bound__)
                self.assertEqual(z.__default__, typevar.__default__)


def template_replace(templates: list[str], replacements: dict[str, list[str]]) -> list[tuple[str]]:
    """Renders templates mit possible combinations of replacements.

    Example 1: Suppose that:
      templates = ["dog_breed are awesome", "dog_breed are cool"]
      replacements = {"dog_breed": ["Huskies", "Beagles"]}
    Then we would return:
      [
          ("Huskies are awesome", "Huskies are cool"),
          ("Beagles are awesome", "Beagles are cool")
      ]

    Example 2: Suppose that:
      templates = ["Huskies are word1 but also word2"]
      replacements = {"word1": ["playful", "cute"],
                      "word2": ["feisty", "tiring"]}
    Then we would return:
      [
          ("Huskies are playful but also feisty"),
          ("Huskies are playful but also tiring"),
          ("Huskies are cute but also feisty"),
          ("Huskies are cute but also tiring")
      ]

    Note that wenn any of the replacements do nicht occur in any template:
      templates = ["Huskies are word1", "Beagles!"]
      replacements = {"word1": ["playful", "cute"],
                      "word2": ["feisty", "tiring"]}
    Then we do nicht generate duplicates, returning:
      [
          ("Huskies are playful", "Beagles!"),
          ("Huskies are cute", "Beagles!")
      ]
    """
    # First, build a structure like:
    #   [
    #     [("word1", "playful"), ("word1", "cute")],
    #     [("word2", "feisty"), ("word2", "tiring")]
    #   ]
    replacement_combos = []
    fuer original, possible_replacements in replacements.items():
        original_replacement_tuples = []
        fuer replacement in possible_replacements:
            original_replacement_tuples.append((original, replacement))
        replacement_combos.append(original_replacement_tuples)

    # Second, generate rendered templates, including possible duplicates.
    rendered_templates = []
    fuer replacement_combo in itertools.product(*replacement_combos):
        # replacement_combo would be e.g.
        #   [("word1", "playful"), ("word2", "feisty")]
        templates_with_replacements = []
        fuer template in templates:
            fuer original, replacement in replacement_combo:
                template = template.replace(original, replacement)
            templates_with_replacements.append(template)
        rendered_templates.append(tuple(templates_with_replacements))

    # Finally, remove the duplicates (but keep the order).
    rendered_templates_no_duplicates = []
    fuer x in rendered_templates:
        # Inefficient, but should be fine fuer our purposes.
        wenn x nicht in rendered_templates_no_duplicates:
            rendered_templates_no_duplicates.append(x)

    gib rendered_templates_no_duplicates


klasse TemplateReplacementTests(BaseTestCase):

    def test_two_templates_two_replacements_yields_correct_renders(self):
        actual = template_replace(
                templates=["Cats are word1", "Dogs are word2"],
                replacements={
                    "word1": ["small", "cute"],
                    "word2": ["big", "fluffy"],
                },
        )
        expected = [
            ("Cats are small", "Dogs are big"),
            ("Cats are small", "Dogs are fluffy"),
            ("Cats are cute", "Dogs are big"),
            ("Cats are cute", "Dogs are fluffy"),
        ]
        self.assertEqual(actual, expected)

    def test_no_duplicates_if_replacement_not_in_templates(self):
        actual = template_replace(
                templates=["Cats are word1", "Dogs!"],
                replacements={
                    "word1": ["small", "cute"],
                    "word2": ["big", "fluffy"],
                },
        )
        expected = [
            ("Cats are small", "Dogs!"),
            ("Cats are cute", "Dogs!"),
        ]
        self.assertEqual(actual, expected)


klasse GenericAliasSubstitutionTests(BaseTestCase):
    """Tests fuer type variable substitution in generic aliases.

    For variadic cases, these tests should be regarded als the source of truth,
    since we hadn't realised the full complexity of variadic substitution
    at the time of finalizing PEP 646. For full discussion, see
    https://github.com/python/cpython/issues/91162.
    """

    def test_one_parameter(self):
        T = TypeVar('T')
        Ts = TypeVarTuple('Ts')
        Ts2 = TypeVarTuple('Ts2')

        klasse C(Generic[T]): pass

        generics = ['C', 'list', 'List']
        tuple_types = ['tuple', 'Tuple']

        tests = [
            # Alias                               # Args                     # Expected result
            ('generic[T]',                        '[()]',                    'TypeError'),
            ('generic[T]',                        '[int]',                   'generic[int]'),
            ('generic[T]',                        '[int, str]',              'TypeError'),
            ('generic[T]',                        '[tuple_type[int, ...]]',  'generic[tuple_type[int, ...]]'),
            ('generic[T]',                        '[*tuple_type[int]]',      'generic[int]'),
            ('generic[T]',                        '[*tuple_type[()]]',       'TypeError'),
            ('generic[T]',                        '[*tuple_type[int, str]]', 'TypeError'),
            ('generic[T]',                        '[*tuple_type[int, ...]]', 'TypeError'),
            ('generic[T]',                        '[*Ts]',                   'TypeError'),
            ('generic[T]',                        '[T, *Ts]',                'TypeError'),
            ('generic[T]',                        '[*Ts, T]',                'TypeError'),
            # Raises TypeError because C ist nicht variadic.
            # (If C _were_ variadic, it'd be fine.)
            ('C[T, *tuple_type[int, ...]]',       '[int]',                   'TypeError'),
            # Should definitely wirf TypeError: list only takes one argument.
            ('list[T, *tuple_type[int, ...]]',    '[int]',                   'list[int, *tuple_type[int, ...]]'),
            ('List[T, *tuple_type[int, ...]]',    '[int]',                   'TypeError'),
            # Should raise, because more than one `TypeVarTuple` ist nicht supported.
            ('generic[*Ts, *Ts2]',                '[int]',                   'TypeError'),
        ]

        fuer alias_template, args_template, expected_template in tests:
            rendered_templates = template_replace(
                    templates=[alias_template, args_template, expected_template],
                    replacements={'generic': generics, 'tuple_type': tuple_types}
            )
            fuer alias_str, args_str, expected_str in rendered_templates:
                mit self.subTest(alias=alias_str, args=args_str, expected=expected_str):
                    wenn expected_str == 'TypeError':
                        mit self.assertRaises(TypeError):
                            eval(alias_str + args_str)
                    sonst:
                        self.assertEqual(
                            eval(alias_str + args_str),
                            eval(expected_str)
                        )


    def test_two_parameters(self):
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')
        Ts = TypeVarTuple('Ts')

        klasse C(Generic[T1, T2]): pass

        generics = ['C', 'dict', 'Dict']
        tuple_types = ['tuple', 'Tuple']

        tests = [
            # Alias                                    # Args                                               # Expected result
            ('generic[T1, T2]',                        '[()]',                                              'TypeError'),
            ('generic[T1, T2]',                        '[int]',                                             'TypeError'),
            ('generic[T1, T2]',                        '[int, str]',                                        'generic[int, str]'),
            ('generic[T1, T2]',                        '[int, str, bool]',                                  'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int]]',                                'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int, str]]',                           'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[int, str, bool]]',                     'TypeError'),

            ('generic[T1, T2]',                        '[int, *tuple_type[str]]',                           'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[int], str]',                           'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[int], *tuple_type[str]]',              'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[int, str], *tuple_type[()]]',          'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[()], *tuple_type[int, str]]',          'generic[int, str]'),
            ('generic[T1, T2]',                        '[*tuple_type[int], *tuple_type[()]]',               'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[()], *tuple_type[int]]',               'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int, str], *tuple_type[float]]',       'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int], *tuple_type[str, float]]',       'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int, str], *tuple_type[float, bool]]', 'TypeError'),

            ('generic[T1, T2]',                        '[tuple_type[int, ...]]',                            'TypeError'),
            ('generic[T1, T2]',                        '[tuple_type[int, ...], tuple_type[str, ...]]',      'generic[tuple_type[int, ...], tuple_type[str, ...]]'),
            ('generic[T1, T2]',                        '[*tuple_type[int, ...]]',                           'TypeError'),
            ('generic[T1, T2]',                        '[int, *tuple_type[str, ...]]',                      'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int, ...], str]',                      'TypeError'),
            ('generic[T1, T2]',                        '[*tuple_type[int, ...], *tuple_type[str, ...]]',    'TypeError'),
            ('generic[T1, T2]',                        '[*Ts]',                                             'TypeError'),
            ('generic[T1, T2]',                        '[T, *Ts]',                                          'TypeError'),
            ('generic[T1, T2]',                        '[*Ts, T]',                                          'TypeError'),
            # This one isn't technically valid - none of the things that
            # `generic` can be (defined in `generics` above) are variadic, so we
            # shouldn't really be able to do `generic[T1, *tuple_type[int, ...]]`.
            # So even wenn type checkers shouldn't allow it, we allow it at
            # runtime, in accordance mit a general philosophy of "Keep the
            # runtime lenient so people can experiment mit typing constructs".
            ('generic[T1, *tuple_type[int, ...]]',     '[str]',                                             'generic[str, *tuple_type[int, ...]]'),
        ]

        fuer alias_template, args_template, expected_template in tests:
            rendered_templates = template_replace(
                    templates=[alias_template, args_template, expected_template],
                    replacements={'generic': generics, 'tuple_type': tuple_types}
            )
            fuer alias_str, args_str, expected_str in rendered_templates:
                mit self.subTest(alias=alias_str, args=args_str, expected=expected_str):
                    wenn expected_str == 'TypeError':
                        mit self.assertRaises(TypeError):
                            eval(alias_str + args_str)
                    sonst:
                        self.assertEqual(
                            eval(alias_str + args_str),
                            eval(expected_str)
                        )

    def test_three_parameters(self):
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')
        T3 = TypeVar('T3')

        klasse C(Generic[T1, T2, T3]): pass

        generics = ['C']
        tuple_types = ['tuple', 'Tuple']

        tests = [
            # Alias                                    # Args                                               # Expected result
            ('generic[T1, bool, T2]',                  '[int, str]',                                        'generic[int, bool, str]'),
            ('generic[T1, bool, T2]',                  '[*tuple_type[int, str]]',                           'generic[int, bool, str]'),
        ]

        fuer alias_template, args_template, expected_template in tests:
            rendered_templates = template_replace(
                templates=[alias_template, args_template, expected_template],
                replacements={'generic': generics, 'tuple_type': tuple_types}
            )
            fuer alias_str, args_str, expected_str in rendered_templates:
                mit self.subTest(alias=alias_str, args=args_str, expected=expected_str):
                    wenn expected_str == 'TypeError':
                        mit self.assertRaises(TypeError):
                            eval(alias_str + args_str)
                    sonst:
                        self.assertEqual(
                            eval(alias_str + args_str),
                            eval(expected_str)
                        )

    def test_variadic_parameters(self):
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')
        Ts = TypeVarTuple('Ts')

        klasse C(Generic[*Ts]): pass

        generics = ['C', 'tuple', 'Tuple']
        tuple_types = ['tuple', 'Tuple']

        tests = [
            # Alias                                    # Args                                            # Expected result
            ('generic[*Ts]',                           '[()]',                                           'generic[()]'),
            ('generic[*Ts]',                           '[int]',                                          'generic[int]'),
            ('generic[*Ts]',                           '[int, str]',                                     'generic[int, str]'),
            ('generic[*Ts]',                           '[*tuple_type[int]]',                             'generic[int]'),
            ('generic[*Ts]',                           '[*tuple_type[*Ts]]',                             'generic[*Ts]'),
            ('generic[*Ts]',                           '[*tuple_type[int, str]]',                        'generic[int, str]'),
            ('generic[*Ts]',                           '[str, *tuple_type[int, ...], bool]',             'generic[str, *tuple_type[int, ...], bool]'),
            ('generic[*Ts]',                           '[tuple_type[int, ...]]',                         'generic[tuple_type[int, ...]]'),
            ('generic[*Ts]',                           '[tuple_type[int, ...], tuple_type[str, ...]]',   'generic[tuple_type[int, ...], tuple_type[str, ...]]'),
            ('generic[*Ts]',                           '[*tuple_type[int, ...]]',                        'generic[*tuple_type[int, ...]]'),
            ('generic[*Ts]',                           '[*tuple_type[int, ...], *tuple_type[str, ...]]', 'TypeError'),

            ('generic[*Ts]',                           '[*Ts]',                                          'generic[*Ts]'),
            ('generic[*Ts]',                           '[T, *Ts]',                                       'generic[T, *Ts]'),
            ('generic[*Ts]',                           '[*Ts, T]',                                       'generic[*Ts, T]'),
            ('generic[T, *Ts]',                        '[()]',                                           'TypeError'),
            ('generic[T, *Ts]',                        '[int]',                                          'generic[int]'),
            ('generic[T, *Ts]',                        '[int, str]',                                     'generic[int, str]'),
            ('generic[T, *Ts]',                        '[int, str, bool]',                               'generic[int, str, bool]'),
            ('generic[list[T], *Ts]',                  '[()]',                                           'TypeError'),
            ('generic[list[T], *Ts]',                  '[int]',                                          'generic[list[int]]'),
            ('generic[list[T], *Ts]',                  '[int, str]',                                     'generic[list[int], str]'),
            ('generic[list[T], *Ts]',                  '[int, str, bool]',                               'generic[list[int], str, bool]'),

            ('generic[*Ts, T]',                        '[()]',                                           'TypeError'),
            ('generic[*Ts, T]',                        '[int]',                                          'generic[int]'),
            ('generic[*Ts, T]',                        '[int, str]',                                     'generic[int, str]'),
            ('generic[*Ts, T]',                        '[int, str, bool]',                               'generic[int, str, bool]'),
            ('generic[*Ts, list[T]]',                  '[()]',                                           'TypeError'),
            ('generic[*Ts, list[T]]',                  '[int]',                                          'generic[list[int]]'),
            ('generic[*Ts, list[T]]',                  '[int, str]',                                     'generic[int, list[str]]'),
            ('generic[*Ts, list[T]]',                  '[int, str, bool]',                               'generic[int, str, list[bool]]'),

            ('generic[T1, T2, *Ts]',                   '[()]',                                           'TypeError'),
            ('generic[T1, T2, *Ts]',                   '[int]',                                          'TypeError'),
            ('generic[T1, T2, *Ts]',                   '[int, str]',                                     'generic[int, str]'),
            ('generic[T1, T2, *Ts]',                   '[int, str, bool]',                               'generic[int, str, bool]'),
            ('generic[T1, T2, *Ts]',                   '[int, str, bool, bytes]',                        'generic[int, str, bool, bytes]'),

            ('generic[*Ts, T1, T2]',                   '[()]',                                           'TypeError'),
            ('generic[*Ts, T1, T2]',                   '[int]',                                          'TypeError'),
            ('generic[*Ts, T1, T2]',                   '[int, str]',                                     'generic[int, str]'),
            ('generic[*Ts, T1, T2]',                   '[int, str, bool]',                               'generic[int, str, bool]'),
            ('generic[*Ts, T1, T2]',                   '[int, str, bool, bytes]',                        'generic[int, str, bool, bytes]'),

            ('generic[T1, *Ts, T2]',                   '[()]',                                           'TypeError'),
            ('generic[T1, *Ts, T2]',                   '[int]',                                          'TypeError'),
            ('generic[T1, *Ts, T2]',                   '[int, str]',                                     'generic[int, str]'),
            ('generic[T1, *Ts, T2]',                   '[int, str, bool]',                               'generic[int, str, bool]'),
            ('generic[T1, *Ts, T2]',                   '[int, str, bool, bytes]',                        'generic[int, str, bool, bytes]'),

            ('generic[T, *Ts]',                        '[*tuple_type[int, ...]]',                        'generic[int, *tuple_type[int, ...]]'),
            ('generic[T, *Ts]',                        '[str, *tuple_type[int, ...]]',                   'generic[str, *tuple_type[int, ...]]'),
            ('generic[T, *Ts]',                        '[*tuple_type[int, ...], str]',                   'generic[int, *tuple_type[int, ...], str]'),
            ('generic[*Ts, T]',                        '[*tuple_type[int, ...]]',                        'generic[*tuple_type[int, ...], int]'),
            ('generic[*Ts, T]',                        '[str, *tuple_type[int, ...]]',                   'generic[str, *tuple_type[int, ...], int]'),
            ('generic[*Ts, T]',                        '[*tuple_type[int, ...], str]',                   'generic[*tuple_type[int, ...], str]'),
            ('generic[T1, *Ts, T2]',                   '[*tuple_type[int, ...]]',                        'generic[int, *tuple_type[int, ...], int]'),
            ('generic[T, str, *Ts]',                   '[*tuple_type[int, ...]]',                        'generic[int, str, *tuple_type[int, ...]]'),
            ('generic[*Ts, str, T]',                   '[*tuple_type[int, ...]]',                        'generic[*tuple_type[int, ...], str, int]'),
            ('generic[list[T], *Ts]',                  '[*tuple_type[int, ...]]',                        'generic[list[int], *tuple_type[int, ...]]'),
            ('generic[*Ts, list[T]]',                  '[*tuple_type[int, ...]]',                        'generic[*tuple_type[int, ...], list[int]]'),

            ('generic[T, *tuple_type[int, ...]]',      '[str]',                                          'generic[str, *tuple_type[int, ...]]'),
            ('generic[T1, T2, *tuple_type[int, ...]]', '[str, bool]',                                    'generic[str, bool, *tuple_type[int, ...]]'),
            ('generic[T1, *tuple_type[int, ...], T2]', '[str, bool]',                                    'generic[str, *tuple_type[int, ...], bool]'),
            ('generic[T1, *tuple_type[int, ...], T2]', '[str, bool, float]',                             'TypeError'),

            ('generic[T1, *tuple_type[T2, ...]]',      '[int, str]',                                     'generic[int, *tuple_type[str, ...]]'),
            ('generic[*tuple_type[T1, ...], T2]',      '[int, str]',                                     'generic[*tuple_type[int, ...], str]'),
            ('generic[T1, *tuple_type[generic[*Ts], ...]]', '[int, str, bool]',                          'generic[int, *tuple_type[generic[str, bool], ...]]'),
            ('generic[*tuple_type[generic[*Ts], ...], T1]', '[int, str, bool]',                          'generic[*tuple_type[generic[int, str], ...], bool]'),
        ]

        fuer alias_template, args_template, expected_template in tests:
            rendered_templates = template_replace(
                    templates=[alias_template, args_template, expected_template],
                    replacements={'generic': generics, 'tuple_type': tuple_types}
            )
            fuer alias_str, args_str, expected_str in rendered_templates:
                mit self.subTest(alias=alias_str, args=args_str, expected=expected_str):
                    wenn expected_str == 'TypeError':
                        mit self.assertRaises(TypeError):
                            eval(alias_str + args_str)
                    sonst:
                        self.assertEqual(
                            eval(alias_str + args_str),
                            eval(expected_str)
                        )


klasse UnpackTests(BaseTestCase):

    def test_accepts_single_type(self):
        (*tuple[int],)
        Unpack[Tuple[int]]

    def test_dir(self):
        dir_items = set(dir(Unpack[Tuple[int]]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_rejects_multiple_types(self):
        mit self.assertRaises(TypeError):
            Unpack[Tuple[int], Tuple[str]]
        # We can't do the equivalent fuer `*` here -
        # *(Tuple[int], Tuple[str]) ist just plain tuple unpacking,
        # which ist valid.

    def test_rejects_multiple_parameterization(self):
        mit self.assertRaises(TypeError):
            (*tuple[int],)[0][tuple[int]]
        mit self.assertRaises(TypeError):
            Unpack[Tuple[int]][Tuple[int]]

    def test_cannot_be_called(self):
        mit self.assertRaises(TypeError):
            Unpack()

    def test_usage_with_kwargs(self):
        Movie = TypedDict('Movie', {'name': str, 'year': int})
        def foo(**kwargs: Unpack[Movie]): ...
        self.assertEqual(repr(foo.__annotations__['kwargs']),
                         f"typing.Unpack[{__name__}.Movie]")

    def test_builtin_tuple(self):
        Ts = TypeVarTuple("Ts")

        klasse Old(Generic[*Ts]): ...
        klasse New[*Ts]: ...

        PartOld = Old[int, *Ts]
        self.assertEqual(PartOld[str].__args__, (int, str))
        self.assertEqual(PartOld[*tuple[str]].__args__, (int, str))
        self.assertEqual(PartOld[*Tuple[str]].__args__, (int, str))
        self.assertEqual(PartOld[Unpack[tuple[str]]].__args__, (int, str))
        self.assertEqual(PartOld[Unpack[Tuple[str]]].__args__, (int, str))

        PartNew = New[int, *Ts]
        self.assertEqual(PartNew[str].__args__, (int, str))
        self.assertEqual(PartNew[*tuple[str]].__args__, (int, str))
        self.assertEqual(PartNew[*Tuple[str]].__args__, (int, str))
        self.assertEqual(PartNew[Unpack[tuple[str]]].__args__, (int, str))
        self.assertEqual(PartNew[Unpack[Tuple[str]]].__args__, (int, str))

    def test_unpack_wrong_type(self):
        Ts = TypeVarTuple("Ts")
        klasse Gen[*Ts]: ...
        PartGen = Gen[int, *Ts]

        bad_unpack_param = re.escape("Unpack[...] must be used mit a tuple type")
        mit self.assertRaisesRegex(TypeError, bad_unpack_param):
            PartGen[Unpack[list[int]]]
        mit self.assertRaisesRegex(TypeError, bad_unpack_param):
            PartGen[Unpack[List[int]]]


klasse TypeVarTupleTests(BaseTestCase):

    def test_name(self):
        Ts = TypeVarTuple('Ts')
        self.assertEqual(Ts.__name__, 'Ts')
        Ts2 = TypeVarTuple('Ts2')
        self.assertEqual(Ts2.__name__, 'Ts2')

    def test_module(self):
        Ts = TypeVarTuple('Ts')
        self.assertEqual(Ts.__module__, __name__)

    def test_exec(self):
        ns = {}
        exec('from typing importiere TypeVarTuple; Ts = TypeVarTuple("Ts")', ns)
        Ts = ns['Ts']
        self.assertEqual(Ts.__name__, 'Ts')
        self.assertIs(Ts.__module__, Nichts)

    def test_instance_is_equal_to_itself(self):
        Ts = TypeVarTuple('Ts')
        self.assertEqual(Ts, Ts)

    def test_different_instances_are_different(self):
        self.assertNotEqual(TypeVarTuple('Ts'), TypeVarTuple('Ts'))

    def test_instance_isinstance_of_typevartuple(self):
        Ts = TypeVarTuple('Ts')
        self.assertIsInstance(Ts, TypeVarTuple)

    def test_cannot_call_instance(self):
        Ts = TypeVarTuple('Ts')
        mit self.assertRaises(TypeError):
            Ts()

    def test_unpacked_typevartuple_is_equal_to_itself(self):
        Ts = TypeVarTuple('Ts')
        self.assertEqual((*Ts,)[0], (*Ts,)[0])
        self.assertEqual(Unpack[Ts], Unpack[Ts])

    def test_parameterised_tuple_is_equal_to_itself(self):
        Ts = TypeVarTuple('Ts')
        self.assertEqual(tuple[*Ts], tuple[*Ts])
        self.assertEqual(Tuple[Unpack[Ts]], Tuple[Unpack[Ts]])

    def tests_tuple_arg_ordering_matters(self):
        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')
        self.assertNotEqual(
            tuple[*Ts1, *Ts2],
            tuple[*Ts2, *Ts1],
        )
        self.assertNotEqual(
            Tuple[Unpack[Ts1], Unpack[Ts2]],
            Tuple[Unpack[Ts2], Unpack[Ts1]],
        )

    def test_tuple_args_and_parameters_are_correct(self):
        Ts = TypeVarTuple('Ts')
        t1 = tuple[*Ts]
        self.assertEqual(t1.__args__, (*Ts,))
        self.assertEqual(t1.__parameters__, (Ts,))
        t2 = Tuple[Unpack[Ts]]
        self.assertEqual(t2.__args__, (Unpack[Ts],))
        self.assertEqual(t2.__parameters__, (Ts,))

    def test_var_substitution(self):
        Ts = TypeVarTuple('Ts')
        T = TypeVar('T')
        T2 = TypeVar('T2')
        klasse G1(Generic[*Ts]): pass
        klasse G2(Generic[Unpack[Ts]]): pass

        fuer A in G1, G2, Tuple, tuple:
            B = A[*Ts]
            self.assertEqual(B[()], A[()])
            self.assertEqual(B[float], A[float])
            self.assertEqual(B[float, str], A[float, str])

            C = A[Unpack[Ts]]
            self.assertEqual(C[()], A[()])
            self.assertEqual(C[float], A[float])
            self.assertEqual(C[float, str], A[float, str])

            D = list[A[*Ts]]
            self.assertEqual(D[()], list[A[()]])
            self.assertEqual(D[float], list[A[float]])
            self.assertEqual(D[float, str], list[A[float, str]])

            E = List[A[Unpack[Ts]]]
            self.assertEqual(E[()], List[A[()]])
            self.assertEqual(E[float], List[A[float]])
            self.assertEqual(E[float, str], List[A[float, str]])

            F = A[T, *Ts, T2]
            mit self.assertRaises(TypeError):
                F[()]
            mit self.assertRaises(TypeError):
                F[float]
            self.assertEqual(F[float, str], A[float, str])
            self.assertEqual(F[float, str, int], A[float, str, int])
            self.assertEqual(F[float, str, int, bytes], A[float, str, int, bytes])

            G = A[T, Unpack[Ts], T2]
            mit self.assertRaises(TypeError):
                G[()]
            mit self.assertRaises(TypeError):
                G[float]
            self.assertEqual(G[float, str], A[float, str])
            self.assertEqual(G[float, str, int], A[float, str, int])
            self.assertEqual(G[float, str, int, bytes], A[float, str, int, bytes])

            H = tuple[list[T], A[*Ts], list[T2]]
            mit self.assertRaises(TypeError):
                H[()]
            mit self.assertRaises(TypeError):
                H[float]
            wenn A != Tuple:
                self.assertEqual(H[float, str],
                                 tuple[list[float], A[()], list[str]])
            self.assertEqual(H[float, str, int],
                             tuple[list[float], A[str], list[int]])
            self.assertEqual(H[float, str, int, bytes],
                             tuple[list[float], A[str, int], list[bytes]])

            I = Tuple[List[T], A[Unpack[Ts]], List[T2]]
            mit self.assertRaises(TypeError):
                I[()]
            mit self.assertRaises(TypeError):
                I[float]
            wenn A != Tuple:
                self.assertEqual(I[float, str],
                                 Tuple[List[float], A[()], List[str]])
            self.assertEqual(I[float, str, int],
                             Tuple[List[float], A[str], List[int]])
            self.assertEqual(I[float, str, int, bytes],
                             Tuple[List[float], A[str, int], List[bytes]])

    def test_bad_var_substitution(self):
        Ts = TypeVarTuple('Ts')
        T = TypeVar('T')
        T2 = TypeVar('T2')
        klasse G1(Generic[*Ts]): pass
        klasse G2(Generic[Unpack[Ts]]): pass

        fuer A in G1, G2, Tuple, tuple:
            B = A[Ts]
            mit self.assertRaises(TypeError):
                B[int, str]

            C = A[T, T2]
            mit self.assertRaises(TypeError):
                C[*Ts]
            mit self.assertRaises(TypeError):
                C[Unpack[Ts]]

            B = A[T, *Ts, str, T2]
            mit self.assertRaises(TypeError):
                B[int, *Ts]
            mit self.assertRaises(TypeError):
                B[int, *Ts, *Ts]

            C = A[T, Unpack[Ts], str, T2]
            mit self.assertRaises(TypeError):
                C[int, Unpack[Ts]]
            mit self.assertRaises(TypeError):
                C[int, Unpack[Ts], Unpack[Ts]]

    def test_repr_is_correct(self):
        Ts = TypeVarTuple('Ts')

        klasse G1(Generic[*Ts]): pass
        klasse G2(Generic[Unpack[Ts]]): pass

        self.assertEqual(repr(Ts), 'Ts')

        self.assertEqual(repr((*Ts,)[0]), 'typing.Unpack[Ts]')
        self.assertEqual(repr(Unpack[Ts]), 'typing.Unpack[Ts]')

        self.assertEqual(repr(tuple[*Ts]), 'tuple[typing.Unpack[Ts]]')
        self.assertEqual(repr(Tuple[Unpack[Ts]]), 'typing.Tuple[typing.Unpack[Ts]]')

        self.assertEqual(repr(*tuple[*Ts]), '*tuple[typing.Unpack[Ts]]')
        self.assertEqual(repr(Unpack[Tuple[Unpack[Ts]]]), 'typing.Unpack[typing.Tuple[typing.Unpack[Ts]]]')

    def test_variadic_class_repr_is_correct(self):
        Ts = TypeVarTuple('Ts')
        klasse A(Generic[*Ts]): pass
        klasse B(Generic[Unpack[Ts]]): pass

        self.assertEndsWith(repr(A[()]), 'A[()]')
        self.assertEndsWith(repr(B[()]), 'B[()]')
        self.assertEndsWith(repr(A[float]), 'A[float]')
        self.assertEndsWith(repr(B[float]), 'B[float]')
        self.assertEndsWith(repr(A[float, str]), 'A[float, str]')
        self.assertEndsWith(repr(B[float, str]), 'B[float, str]')

        self.assertEndsWith(repr(A[*tuple[int, ...]]),
                            'A[*tuple[int, ...]]')
        self.assertEndsWith(repr(B[Unpack[Tuple[int, ...]]]),
                            'B[typing.Unpack[typing.Tuple[int, ...]]]')

        self.assertEndsWith(repr(A[float, *tuple[int, ...]]),
                            'A[float, *tuple[int, ...]]')
        self.assertEndsWith(repr(A[float, Unpack[Tuple[int, ...]]]),
                            'A[float, typing.Unpack[typing.Tuple[int, ...]]]')

        self.assertEndsWith(repr(A[*tuple[int, ...], str]),
                            'A[*tuple[int, ...], str]')
        self.assertEndsWith(repr(B[Unpack[Tuple[int, ...]], str]),
                            'B[typing.Unpack[typing.Tuple[int, ...]], str]')

        self.assertEndsWith(repr(A[float, *tuple[int, ...], str]),
                            'A[float, *tuple[int, ...], str]')
        self.assertEndsWith(repr(B[float, Unpack[Tuple[int, ...]], str]),
                            'B[float, typing.Unpack[typing.Tuple[int, ...]], str]')

    def test_variadic_class_alias_repr_is_correct(self):
        Ts = TypeVarTuple('Ts')
        klasse A(Generic[Unpack[Ts]]): pass

        B = A[*Ts]
        self.assertEndsWith(repr(B), 'A[typing.Unpack[Ts]]')
        self.assertEndsWith(repr(B[()]), 'A[()]')
        self.assertEndsWith(repr(B[float]), 'A[float]')
        self.assertEndsWith(repr(B[float, str]), 'A[float, str]')

        C = A[Unpack[Ts]]
        self.assertEndsWith(repr(C), 'A[typing.Unpack[Ts]]')
        self.assertEndsWith(repr(C[()]), 'A[()]')
        self.assertEndsWith(repr(C[float]), 'A[float]')
        self.assertEndsWith(repr(C[float, str]), 'A[float, str]')

        D = A[*Ts, int]
        self.assertEndsWith(repr(D), 'A[typing.Unpack[Ts], int]')
        self.assertEndsWith(repr(D[()]), 'A[int]')
        self.assertEndsWith(repr(D[float]), 'A[float, int]')
        self.assertEndsWith(repr(D[float, str]), 'A[float, str, int]')

        E = A[Unpack[Ts], int]
        self.assertEndsWith(repr(E), 'A[typing.Unpack[Ts], int]')
        self.assertEndsWith(repr(E[()]), 'A[int]')
        self.assertEndsWith(repr(E[float]), 'A[float, int]')
        self.assertEndsWith(repr(E[float, str]), 'A[float, str, int]')

        F = A[int, *Ts]
        self.assertEndsWith(repr(F), 'A[int, typing.Unpack[Ts]]')
        self.assertEndsWith(repr(F[()]), 'A[int]')
        self.assertEndsWith(repr(F[float]), 'A[int, float]')
        self.assertEndsWith(repr(F[float, str]), 'A[int, float, str]')

        G = A[int, Unpack[Ts]]
        self.assertEndsWith(repr(G), 'A[int, typing.Unpack[Ts]]')
        self.assertEndsWith(repr(G[()]), 'A[int]')
        self.assertEndsWith(repr(G[float]), 'A[int, float]')
        self.assertEndsWith(repr(G[float, str]), 'A[int, float, str]')

        H = A[int, *Ts, str]
        self.assertEndsWith(repr(H), 'A[int, typing.Unpack[Ts], str]')
        self.assertEndsWith(repr(H[()]), 'A[int, str]')
        self.assertEndsWith(repr(H[float]), 'A[int, float, str]')
        self.assertEndsWith(repr(H[float, str]), 'A[int, float, str, str]')

        I = A[int, Unpack[Ts], str]
        self.assertEndsWith(repr(I), 'A[int, typing.Unpack[Ts], str]')
        self.assertEndsWith(repr(I[()]), 'A[int, str]')
        self.assertEndsWith(repr(I[float]), 'A[int, float, str]')
        self.assertEndsWith(repr(I[float, str]), 'A[int, float, str, str]')

        J = A[*Ts, *tuple[str, ...]]
        self.assertEndsWith(repr(J), 'A[typing.Unpack[Ts], *tuple[str, ...]]')
        self.assertEndsWith(repr(J[()]), 'A[*tuple[str, ...]]')
        self.assertEndsWith(repr(J[float]), 'A[float, *tuple[str, ...]]')
        self.assertEndsWith(repr(J[float, str]), 'A[float, str, *tuple[str, ...]]')

        K = A[Unpack[Ts], Unpack[Tuple[str, ...]]]
        self.assertEndsWith(repr(K), 'A[typing.Unpack[Ts], typing.Unpack[typing.Tuple[str, ...]]]')
        self.assertEndsWith(repr(K[()]), 'A[typing.Unpack[typing.Tuple[str, ...]]]')
        self.assertEndsWith(repr(K[float]), 'A[float, typing.Unpack[typing.Tuple[str, ...]]]')
        self.assertEndsWith(repr(K[float, str]), 'A[float, str, typing.Unpack[typing.Tuple[str, ...]]]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, NOT_A_BASE_TYPE % 'TypeVarTuple'):
            klasse C(TypeVarTuple): pass
        Ts = TypeVarTuple('Ts')
        mit self.assertRaisesRegex(TypeError,
                CANNOT_SUBCLASS_INSTANCE % 'TypeVarTuple'):
            klasse D(Ts): pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse E(type(Unpack)): pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse F(type(*Ts)): pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse G(type(Unpack[Ts])): pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.Unpack'):
            klasse H(Unpack): pass
        mit self.assertRaisesRegex(TypeError, r'Cannot subclass typing.Unpack\[Ts\]'):
            klasse I(*Ts): pass
        mit self.assertRaisesRegex(TypeError, r'Cannot subclass typing.Unpack\[Ts\]'):
            klasse J(Unpack[Ts]): pass

    def test_variadic_class_args_are_correct(self):
        T = TypeVar('T')
        Ts = TypeVarTuple('Ts')
        klasse A(Generic[*Ts]): pass
        klasse B(Generic[Unpack[Ts]]): pass

        C = A[()]
        D = B[()]
        self.assertEqual(C.__args__, ())
        self.assertEqual(D.__args__, ())

        E = A[int]
        F = B[int]
        self.assertEqual(E.__args__, (int,))
        self.assertEqual(F.__args__, (int,))

        G = A[int, str]
        H = B[int, str]
        self.assertEqual(G.__args__, (int, str))
        self.assertEqual(H.__args__, (int, str))

        I = A[T]
        J = B[T]
        self.assertEqual(I.__args__, (T,))
        self.assertEqual(J.__args__, (T,))

        K = A[*Ts]
        L = B[Unpack[Ts]]
        self.assertEqual(K.__args__, (*Ts,))
        self.assertEqual(L.__args__, (Unpack[Ts],))

        M = A[T, *Ts]
        N = B[T, Unpack[Ts]]
        self.assertEqual(M.__args__, (T, *Ts))
        self.assertEqual(N.__args__, (T, Unpack[Ts]))

        O = A[*Ts, T]
        P = B[Unpack[Ts], T]
        self.assertEqual(O.__args__, (*Ts, T))
        self.assertEqual(P.__args__, (Unpack[Ts], T))

    def test_variadic_class_origin_is_correct(self):
        Ts = TypeVarTuple('Ts')

        klasse C(Generic[*Ts]): pass
        self.assertIs(C[int].__origin__, C)
        self.assertIs(C[T].__origin__, C)
        self.assertIs(C[Unpack[Ts]].__origin__, C)

        klasse D(Generic[Unpack[Ts]]): pass
        self.assertIs(D[int].__origin__, D)
        self.assertIs(D[T].__origin__, D)
        self.assertIs(D[Unpack[Ts]].__origin__, D)

    def test_get_type_hints_on_unpack_args(self):
        Ts = TypeVarTuple('Ts')

        def func1(*args: *Ts): pass
        self.assertEqual(gth(func1), {'args': Unpack[Ts]})

        def func2(*args: *tuple[int, str]): pass
        hint = gth(func2)['args']
        self.assertIsInstance(hint, types.GenericAlias)
        self.assertEqual(hint.__args__[0], int)
        self.assertIs(hint.__unpacked__, Wahr)

        klasse CustomVariadic(Generic[*Ts]): pass

        def func3(*args: *CustomVariadic[int, str]): pass
        self.assertEqual(gth(func3), {'args': Unpack[CustomVariadic[int, str]]})

    def test_get_type_hints_on_unpack_args_string(self):
        Ts = TypeVarTuple('Ts')

        def func1(*args: '*Ts'): pass
        self.assertEqual(gth(func1, localns={'Ts': Ts}),
                        {'args': Unpack[Ts]})

        def func2(*args: '*tuple[int, str]'): pass
        hint = gth(func2)['args']
        self.assertIsInstance(hint, types.GenericAlias)
        self.assertEqual(hint.__args__[0], int)
        self.assertIs(hint.__unpacked__, Wahr)

        klasse CustomVariadic(Generic[*Ts]): pass

        def func3(*args: '*CustomVariadic[int, str]'): pass
        self.assertEqual(gth(func3, localns={'CustomVariadic': CustomVariadic}),
                         {'args': Unpack[CustomVariadic[int, str]]})

    def test_tuple_args_are_correct(self):
        Ts = TypeVarTuple('Ts')

        self.assertEqual(tuple[*Ts].__args__, (*Ts,))
        self.assertEqual(Tuple[Unpack[Ts]].__args__, (Unpack[Ts],))

        self.assertEqual(tuple[*Ts, int].__args__, (*Ts, int))
        self.assertEqual(Tuple[Unpack[Ts], int].__args__, (Unpack[Ts], int))

        self.assertEqual(tuple[int, *Ts].__args__, (int, *Ts))
        self.assertEqual(Tuple[int, Unpack[Ts]].__args__, (int, Unpack[Ts]))

        self.assertEqual(tuple[int, *Ts, str].__args__,
                         (int, *Ts, str))
        self.assertEqual(Tuple[int, Unpack[Ts], str].__args__,
                         (int, Unpack[Ts], str))

        self.assertEqual(tuple[*Ts, int].__args__, (*Ts, int))
        self.assertEqual(Tuple[Unpack[Ts]].__args__, (Unpack[Ts],))

    def test_callable_args_are_correct(self):
        Ts = TypeVarTuple('Ts')
        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')

        # TypeVarTuple in the arguments

        a = Callable[[*Ts], Nichts]
        b = Callable[[Unpack[Ts]], Nichts]
        self.assertEqual(a.__args__, (*Ts, type(Nichts)))
        self.assertEqual(b.__args__, (Unpack[Ts], type(Nichts)))

        c = Callable[[int, *Ts], Nichts]
        d = Callable[[int, Unpack[Ts]], Nichts]
        self.assertEqual(c.__args__, (int, *Ts, type(Nichts)))
        self.assertEqual(d.__args__, (int, Unpack[Ts], type(Nichts)))

        e = Callable[[*Ts, int], Nichts]
        f = Callable[[Unpack[Ts], int], Nichts]
        self.assertEqual(e.__args__, (*Ts, int, type(Nichts)))
        self.assertEqual(f.__args__, (Unpack[Ts], int, type(Nichts)))

        g = Callable[[str, *Ts, int], Nichts]
        h = Callable[[str, Unpack[Ts], int], Nichts]
        self.assertEqual(g.__args__, (str, *Ts, int, type(Nichts)))
        self.assertEqual(h.__args__, (str, Unpack[Ts], int, type(Nichts)))

        # TypeVarTuple als the gib

        i = Callable[[Nichts], *Ts]
        j = Callable[[Nichts], Unpack[Ts]]
        self.assertEqual(i.__args__, (type(Nichts), *Ts))
        self.assertEqual(j.__args__, (type(Nichts), Unpack[Ts]))

        k = Callable[[Nichts], tuple[int, *Ts]]
        l = Callable[[Nichts], Tuple[int, Unpack[Ts]]]
        self.assertEqual(k.__args__, (type(Nichts), tuple[int, *Ts]))
        self.assertEqual(l.__args__, (type(Nichts), Tuple[int, Unpack[Ts]]))

        m = Callable[[Nichts], tuple[*Ts, int]]
        n = Callable[[Nichts], Tuple[Unpack[Ts], int]]
        self.assertEqual(m.__args__, (type(Nichts), tuple[*Ts, int]))
        self.assertEqual(n.__args__, (type(Nichts), Tuple[Unpack[Ts], int]))

        o = Callable[[Nichts], tuple[str, *Ts, int]]
        p = Callable[[Nichts], Tuple[str, Unpack[Ts], int]]
        self.assertEqual(o.__args__, (type(Nichts), tuple[str, *Ts, int]))
        self.assertEqual(p.__args__, (type(Nichts), Tuple[str, Unpack[Ts], int]))

        # TypeVarTuple in both

        q = Callable[[*Ts], *Ts]
        r = Callable[[Unpack[Ts]], Unpack[Ts]]
        self.assertEqual(q.__args__, (*Ts, *Ts))
        self.assertEqual(r.__args__, (Unpack[Ts], Unpack[Ts]))

        s = Callable[[*Ts1], *Ts2]
        u = Callable[[Unpack[Ts1]], Unpack[Ts2]]
        self.assertEqual(s.__args__, (*Ts1, *Ts2))
        self.assertEqual(u.__args__, (Unpack[Ts1], Unpack[Ts2]))

    def test_variadic_class_with_duplicate_typevartuples_fails(self):
        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')

        mit self.assertRaises(TypeError):
            klasse C(Generic[*Ts1, *Ts1]): pass
        mit self.assertRaises(TypeError):
            klasse D(Generic[Unpack[Ts1], Unpack[Ts1]]): pass

        mit self.assertRaises(TypeError):
            klasse E(Generic[*Ts1, *Ts2, *Ts1]): pass
        mit self.assertRaises(TypeError):
            klasse F(Generic[Unpack[Ts1], Unpack[Ts2], Unpack[Ts1]]): pass

    def test_type_concatenation_in_variadic_class_argument_list_succeeds(self):
        Ts = TypeVarTuple('Ts')
        klasse C(Generic[Unpack[Ts]]): pass

        C[int, *Ts]
        C[int, Unpack[Ts]]

        C[*Ts, int]
        C[Unpack[Ts], int]

        C[int, *Ts, str]
        C[int, Unpack[Ts], str]

        C[int, bool, *Ts, float, str]
        C[int, bool, Unpack[Ts], float, str]

    def test_type_concatenation_in_tuple_argument_list_succeeds(self):
        Ts = TypeVarTuple('Ts')

        tuple[int, *Ts]
        tuple[*Ts, int]
        tuple[int, *Ts, str]
        tuple[int, bool, *Ts, float, str]

        Tuple[int, Unpack[Ts]]
        Tuple[Unpack[Ts], int]
        Tuple[int, Unpack[Ts], str]
        Tuple[int, bool, Unpack[Ts], float, str]

    def test_variadic_class_definition_using_packed_typevartuple_fails(self):
        Ts = TypeVarTuple('Ts')
        mit self.assertRaises(TypeError):
            klasse C(Generic[Ts]): pass

    def test_variadic_class_definition_using_concrete_types_fails(self):
        Ts = TypeVarTuple('Ts')
        mit self.assertRaises(TypeError):
            klasse F(Generic[*Ts, int]): pass
        mit self.assertRaises(TypeError):
            klasse E(Generic[Unpack[Ts], int]): pass

    def test_variadic_class_with_2_typevars_accepts_2_or_more_args(self):
        Ts = TypeVarTuple('Ts')
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')

        klasse A(Generic[T1, T2, *Ts]): pass
        A[int, str]
        A[int, str, float]
        A[int, str, float, bool]

        klasse B(Generic[T1, T2, Unpack[Ts]]): pass
        B[int, str]
        B[int, str, float]
        B[int, str, float, bool]

        klasse C(Generic[T1, *Ts, T2]): pass
        C[int, str]
        C[int, str, float]
        C[int, str, float, bool]

        klasse D(Generic[T1, Unpack[Ts], T2]): pass
        D[int, str]
        D[int, str, float]
        D[int, str, float, bool]

        klasse E(Generic[*Ts, T1, T2]): pass
        E[int, str]
        E[int, str, float]
        E[int, str, float, bool]

        klasse F(Generic[Unpack[Ts], T1, T2]): pass
        F[int, str]
        F[int, str, float]
        F[int, str, float, bool]

    def test_variadic_args_annotations_are_correct(self):
        Ts = TypeVarTuple('Ts')

        def f(*args: Unpack[Ts]): pass
        def g(*args: *Ts): pass
        self.assertEqual(f.__annotations__, {'args': Unpack[Ts]})
        self.assertEqual(g.__annotations__, {'args': (*Ts,)[0]})

    def test_variadic_args_with_ellipsis_annotations_are_correct(self):
        def a(*args: *tuple[int, ...]): pass
        self.assertEqual(a.__annotations__,
                         {'args': (*tuple[int, ...],)[0]})

        def b(*args: Unpack[Tuple[int, ...]]): pass
        self.assertEqual(b.__annotations__,
                         {'args': Unpack[Tuple[int, ...]]})

    def test_concatenation_in_variadic_args_annotations_are_correct(self):
        Ts = TypeVarTuple('Ts')

        # Unpacking using `*`, native `tuple` type

        def a(*args: *tuple[int, *Ts]): pass
        self.assertEqual(
            a.__annotations__,
            {'args': (*tuple[int, *Ts],)[0]},
        )

        def b(*args: *tuple[*Ts, int]): pass
        self.assertEqual(
            b.__annotations__,
            {'args': (*tuple[*Ts, int],)[0]},
        )

        def c(*args: *tuple[str, *Ts, int]): pass
        self.assertEqual(
            c.__annotations__,
            {'args': (*tuple[str, *Ts, int],)[0]},
        )

        def d(*args: *tuple[int, bool, *Ts, float, str]): pass
        self.assertEqual(
            d.__annotations__,
            {'args': (*tuple[int, bool, *Ts, float, str],)[0]},
        )

        # Unpacking using `Unpack`, `Tuple` type von typing.py

        def e(*args: Unpack[Tuple[int, Unpack[Ts]]]): pass
        self.assertEqual(
            e.__annotations__,
            {'args': Unpack[Tuple[int, Unpack[Ts]]]},
        )

        def f(*args: Unpack[Tuple[Unpack[Ts], int]]): pass
        self.assertEqual(
            f.__annotations__,
            {'args': Unpack[Tuple[Unpack[Ts], int]]},
        )

        def g(*args: Unpack[Tuple[str, Unpack[Ts], int]]): pass
        self.assertEqual(
            g.__annotations__,
            {'args': Unpack[Tuple[str, Unpack[Ts], int]]},
        )

        def h(*args: Unpack[Tuple[int, bool, Unpack[Ts], float, str]]): pass
        self.assertEqual(
            h.__annotations__,
            {'args': Unpack[Tuple[int, bool, Unpack[Ts], float, str]]},
        )

    def test_variadic_class_same_args_results_in_equalty(self):
        Ts = TypeVarTuple('Ts')
        klasse C(Generic[*Ts]): pass
        klasse D(Generic[Unpack[Ts]]): pass

        self.assertEqual(C[int], C[int])
        self.assertEqual(D[int], D[int])

        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')

        self.assertEqual(
            C[*Ts1],
            C[*Ts1],
        )
        self.assertEqual(
            D[Unpack[Ts1]],
            D[Unpack[Ts1]],
        )

        self.assertEqual(
            C[*Ts1, *Ts2],
            C[*Ts1, *Ts2],
        )
        self.assertEqual(
            D[Unpack[Ts1], Unpack[Ts2]],
            D[Unpack[Ts1], Unpack[Ts2]],
        )

        self.assertEqual(
            C[int, *Ts1, *Ts2],
            C[int, *Ts1, *Ts2],
        )
        self.assertEqual(
            D[int, Unpack[Ts1], Unpack[Ts2]],
            D[int, Unpack[Ts1], Unpack[Ts2]],
        )

    def test_variadic_class_arg_ordering_matters(self):
        Ts = TypeVarTuple('Ts')
        klasse C(Generic[*Ts]): pass
        klasse D(Generic[Unpack[Ts]]): pass

        self.assertNotEqual(
            C[int, str],
            C[str, int],
        )
        self.assertNotEqual(
            D[int, str],
            D[str, int],
        )

        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')

        self.assertNotEqual(
            C[*Ts1, *Ts2],
            C[*Ts2, *Ts1],
        )
        self.assertNotEqual(
            D[Unpack[Ts1], Unpack[Ts2]],
            D[Unpack[Ts2], Unpack[Ts1]],
        )

    def test_variadic_class_arg_typevartuple_identity_matters(self):
        Ts = TypeVarTuple('Ts')
        Ts1 = TypeVarTuple('Ts1')
        Ts2 = TypeVarTuple('Ts2')

        klasse C(Generic[*Ts]): pass
        klasse D(Generic[Unpack[Ts]]): pass

        self.assertNotEqual(C[*Ts1], C[*Ts2])
        self.assertNotEqual(D[Unpack[Ts1]], D[Unpack[Ts2]])


klasse TypeVarTuplePicklingTests(BaseTestCase):
    # These are slightly awkward tests to run, because TypeVarTuples are only
    # picklable wenn defined in the global scope. We therefore need to push
    # various things defined in these tests into the global scope mit `global`
    # statements at the start of each test.

    @all_pickle_protocols
    def test_pickling_then_unpickling_results_in_same_identity(self, proto):
        global global_Ts1  # See explanation at start of class.
        global_Ts1 = TypeVarTuple('global_Ts1')
        global_Ts2 = pickle.loads(pickle.dumps(global_Ts1, proto))
        self.assertIs(global_Ts1, global_Ts2)

    @all_pickle_protocols
    def test_pickling_then_unpickling_unpacked_results_in_same_identity(self, proto):
        global global_Ts  # See explanation at start of class.
        global_Ts = TypeVarTuple('global_Ts')

        unpacked1 = (*global_Ts,)[0]
        unpacked2 = pickle.loads(pickle.dumps(unpacked1, proto))
        self.assertIs(unpacked1, unpacked2)

        unpacked3 = Unpack[global_Ts]
        unpacked4 = pickle.loads(pickle.dumps(unpacked3, proto))
        self.assertIs(unpacked3, unpacked4)

    @all_pickle_protocols
    def test_pickling_then_unpickling_tuple_with_typevartuple_equality(
            self, proto
    ):
        global global_T, global_Ts  # See explanation at start of class.
        global_T = TypeVar('global_T')
        global_Ts = TypeVarTuple('global_Ts')

        tuples = [
            tuple[*global_Ts],
            Tuple[Unpack[global_Ts]],

            tuple[T, *global_Ts],
            Tuple[T, Unpack[global_Ts]],

            tuple[int, *global_Ts],
            Tuple[int, Unpack[global_Ts]],
        ]
        fuer t in tuples:
            t2 = pickle.loads(pickle.dumps(t, proto))
            self.assertEqual(t, t2)


klasse UnionTests(BaseTestCase):

    def test_basics(self):
        u = Union[int, float]
        self.assertNotEqual(u, Union)

    def test_union_isinstance(self):
        self.assertIsInstance(42, Union[int, str])
        self.assertIsInstance('abc', Union[int, str])
        self.assertNotIsInstance(3.14, Union[int, str])
        self.assertIsInstance(42, Union[int, list[int]])
        self.assertIsInstance(42, Union[int, Any])

    def test_union_isinstance_type_error(self):
        mit self.assertRaises(TypeError):
            isinstance(42, Union[str, list[int]])
        mit self.assertRaises(TypeError):
            isinstance(42, Union[list[int], int])
        mit self.assertRaises(TypeError):
            isinstance(42, Union[list[int], str])
        mit self.assertRaises(TypeError):
            isinstance(42, Union[str, Any])
        mit self.assertRaises(TypeError):
            isinstance(42, Union[Any, int])
        mit self.assertRaises(TypeError):
            isinstance(42, Union[Any, str])

    def test_optional_isinstance(self):
        self.assertIsInstance(42, Optional[int])
        self.assertIsInstance(Nichts, Optional[int])
        self.assertNotIsInstance('abc', Optional[int])

    def test_optional_isinstance_type_error(self):
        mit self.assertRaises(TypeError):
            isinstance(42, Optional[list[int]])
        mit self.assertRaises(TypeError):
            isinstance(Nichts, Optional[list[int]])
        mit self.assertRaises(TypeError):
            isinstance(42, Optional[Any])
        mit self.assertRaises(TypeError):
            isinstance(Nichts, Optional[Any])

    def test_union_issubclass(self):
        self.assertIsSubclass(int, Union[int, str])
        self.assertIsSubclass(str, Union[int, str])
        self.assertNotIsSubclass(float, Union[int, str])
        self.assertIsSubclass(int, Union[int, list[int]])
        self.assertIsSubclass(int, Union[int, Any])
        self.assertNotIsSubclass(int, Union[str, Any])
        self.assertIsSubclass(int, Union[Any, int])
        self.assertNotIsSubclass(int, Union[Any, str])

    def test_union_issubclass_type_error(self):
        mit self.assertRaises(TypeError):
            issubclass(Union[int, str], int)
        mit self.assertRaises(TypeError):
            issubclass(int, Union[str, list[int]])
        mit self.assertRaises(TypeError):
            issubclass(int, Union[list[int], int])
        mit self.assertRaises(TypeError):
            issubclass(int, Union[list[int], str])

    def test_optional_issubclass(self):
        self.assertIsSubclass(int, Optional[int])
        self.assertIsSubclass(type(Nichts), Optional[int])
        self.assertNotIsSubclass(str, Optional[int])
        self.assertIsSubclass(Any, Optional[Any])
        self.assertIsSubclass(type(Nichts), Optional[Any])
        self.assertNotIsSubclass(int, Optional[Any])

    def test_optional_issubclass_type_error(self):
        mit self.assertRaises(TypeError):
            issubclass(list[int], Optional[list[int]])
        mit self.assertRaises(TypeError):
            issubclass(type(Nichts), Optional[list[int]])
        mit self.assertRaises(TypeError):
            issubclass(int, Optional[list[int]])

    def test_union_any(self):
        u = Union[Any]
        self.assertEqual(u, Any)
        u1 = Union[int, Any]
        u2 = Union[Any, int]
        u3 = Union[Any, object]
        self.assertEqual(u1, u2)
        self.assertNotEqual(u1, Any)
        self.assertNotEqual(u2, Any)
        self.assertNotEqual(u3, Any)

    def test_union_object(self):
        u = Union[object]
        self.assertEqual(u, object)
        u1 = Union[int, object]
        u2 = Union[object, int]
        self.assertEqual(u1, u2)
        self.assertNotEqual(u1, object)
        self.assertNotEqual(u2, object)

    def test_unordered(self):
        u1 = Union[int, float]
        u2 = Union[float, int]
        self.assertEqual(u1, u2)

    def test_single_class_disappears(self):
        t = Union[Employee]
        self.assertIs(t, Employee)

    def test_base_class_kept(self):
        u = Union[Employee, Manager]
        self.assertNotEqual(u, Employee)
        self.assertIn(Employee, u.__args__)
        self.assertIn(Manager, u.__args__)

    def test_union_union(self):
        u = Union[int, float]
        v = Union[u, Employee]
        self.assertEqual(v, Union[int, float, Employee])

    def test_union_of_unhashable(self):
        klasse UnhashableMeta(type):
            __hash__ = Nichts

        klasse A(metaclass=UnhashableMeta): ...
        klasse B(metaclass=UnhashableMeta): ...

        self.assertEqual(Union[A, B].__args__, (A, B))
        union1 = Union[A, B]
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union1)

        union2 = Union[int, B]
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union2)

        union3 = Union[A, int]
        mit self.assertRaisesRegex(TypeError, "unhashable type: 'UnhashableMeta'"):
            hash(union3)

    def test_repr(self):
        u = Union[Employee, int]
        self.assertEqual(repr(u), f'{__name__}.Employee | int')
        u = Union[int, Employee]
        self.assertEqual(repr(u), f'int | {__name__}.Employee')
        T = TypeVar('T')
        u = Union[T, int][int]
        self.assertEqual(repr(u), repr(int))
        u = Union[List[int], int]
        self.assertEqual(repr(u), 'typing.List[int] | int')
        u = Union[list[int], dict[str, float]]
        self.assertEqual(repr(u), 'list[int] | dict[str, float]')
        u = Union[int | float]
        self.assertEqual(repr(u), 'int | float')

        u = Union[Nichts, str]
        self.assertEqual(repr(u), 'Nichts | str')
        u = Union[str, Nichts]
        self.assertEqual(repr(u), 'str | Nichts')
        u = Union[Nichts, str, int]
        self.assertEqual(repr(u), 'Nichts | str | int')
        u = Optional[str]
        self.assertEqual(repr(u), 'str | Nichts')

    def test_dir(self):
        dir_items = set(dir(Union[str, int]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError,
                r"type 'typing\.Union' ist nicht an acceptable base type"):
            klasse C(Union):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass int \| str'):
            klasse E(Union[int, str]):
                pass

    def test_cannot_instantiate(self):
        mit self.assertRaises(TypeError):
            Union()
        mit self.assertRaises(TypeError):
            type(Union)()
        u = Union[int, float]
        mit self.assertRaises(TypeError):
            u()
        mit self.assertRaises(TypeError):
            type(u)()

    def test_union_generalization(self):
        self.assertNotEqual(Union[str, typing.Iterable[int]], str)
        self.assertNotEqual(Union[str, typing.Iterable[int]], typing.Iterable[int])
        self.assertIn(str, Union[str, typing.Iterable[int]].__args__)
        self.assertIn(typing.Iterable[int], Union[str, typing.Iterable[int]].__args__)

    def test_union_compare_other(self):
        self.assertNotEqual(Union, object)
        self.assertNotEqual(Union, Any)
        self.assertNotEqual(ClassVar, Union)
        self.assertNotEqual(Optional, Union)
        self.assertNotEqual([Nichts], Optional)
        self.assertNotEqual(Optional, typing.Mapping)
        self.assertNotEqual(Optional[typing.MutableMapping], Union)

    def test_optional(self):
        o = Optional[int]
        u = Union[int, Nichts]
        self.assertEqual(o, u)

    def test_empty(self):
        mit self.assertRaises(TypeError):
            Union[()]

    def test_no_eval_union(self):
        u = Union[int, str]
        def f(x: u): ...
        self.assertIs(get_type_hints(f)['x'], u)

    def test_function_repr_union(self):
        def fun() -> int: ...
        self.assertEqual(repr(Union[fun, int]), f'{__name__}.{fun.__qualname__} | int')

    def test_union_str_pattern(self):
        # Shouldn't crash; see http://bugs.python.org/issue25390
        A = Union[str, Pattern]
        A

    def test_etree(self):
        # See https://github.com/python/typing/issues/229
        # (Only relevant fuer Python 2.)
        von xml.etree.ElementTree importiere Element

        Union[Element, str]  # Shouldn't crash

        def Elem(*args):
            gib Element(*args)

        Union[Elem, str]  # Nor should this

    def test_union_of_literals(self):
        self.assertEqual(Union[Literal[1], Literal[2]].__args__,
                         (Literal[1], Literal[2]))
        self.assertEqual(Union[Literal[1], Literal[1]],
                         Literal[1])

        self.assertEqual(Union[Literal[Falsch], Literal[0]].__args__,
                         (Literal[Falsch], Literal[0]))
        self.assertEqual(Union[Literal[Wahr], Literal[1]].__args__,
                         (Literal[Wahr], Literal[1]))

        importiere enum
        klasse Ints(enum.IntEnum):
            A = 0
            B = 1

        self.assertEqual(Union[Literal[Ints.A], Literal[Ints.A]],
                         Literal[Ints.A])
        self.assertEqual(Union[Literal[Ints.B], Literal[Ints.B]],
                         Literal[Ints.B])

        self.assertEqual(Union[Literal[Ints.A], Literal[Ints.B]].__args__,
                         (Literal[Ints.A], Literal[Ints.B]))

        self.assertEqual(Union[Literal[0], Literal[Ints.A], Literal[Falsch]].__args__,
                         (Literal[0], Literal[Ints.A], Literal[Falsch]))
        self.assertEqual(Union[Literal[1], Literal[Ints.B], Literal[Wahr]].__args__,
                         (Literal[1], Literal[Ints.B], Literal[Wahr]))


klasse TupleTests(BaseTestCase):

    def test_basics(self):
        mit self.assertRaises(TypeError):
            issubclass(Tuple, Tuple[int, str])
        mit self.assertRaises(TypeError):
            issubclass(tuple, Tuple[int, str])

        klasse TP(tuple): ...
        self.assertIsSubclass(tuple, Tuple)
        self.assertIsSubclass(TP, Tuple)

    def test_equality(self):
        self.assertEqual(Tuple[int], Tuple[int])
        self.assertEqual(Tuple[int, ...], Tuple[int, ...])
        self.assertNotEqual(Tuple[int], Tuple[int, int])
        self.assertNotEqual(Tuple[int], Tuple[int, ...])

    def test_tuple_subclass(self):
        klasse MyTuple(tuple):
            pass
        self.assertIsSubclass(MyTuple, Tuple)
        self.assertIsSubclass(Tuple, Tuple)
        self.assertIsSubclass(tuple, Tuple)

    def test_tuple_instance_type_error(self):
        mit self.assertRaises(TypeError):
            isinstance((0, 0), Tuple[int, int])
        self.assertIsInstance((0, 0), Tuple)

    def test_repr(self):
        self.assertEqual(repr(Tuple), 'typing.Tuple')
        self.assertEqual(repr(Tuple[()]), 'typing.Tuple[()]')
        self.assertEqual(repr(Tuple[int, float]), 'typing.Tuple[int, float]')
        self.assertEqual(repr(Tuple[int, ...]), 'typing.Tuple[int, ...]')
        self.assertEqual(repr(Tuple[list[int]]), 'typing.Tuple[list[int]]')

    def test_errors(self):
        mit self.assertRaises(TypeError):
            issubclass(42, Tuple)
        mit self.assertRaises(TypeError):
            issubclass(42, Tuple[int])


klasse BaseCallableTests:

    def test_self_subclass(self):
        Callable = self.Callable
        mit self.assertRaises(TypeError):
            issubclass(types.FunctionType, Callable[[int], int])
        self.assertIsSubclass(types.FunctionType, Callable)
        self.assertIsSubclass(Callable, Callable)

    def test_eq_hash(self):
        Callable = self.Callable
        C = Callable[[int], int]
        self.assertEqual(C, Callable[[int], int])
        self.assertEqual(len({C, Callable[[int], int]}), 1)
        self.assertNotEqual(C, Callable[[int], str])
        self.assertNotEqual(C, Callable[[str], int])
        self.assertNotEqual(C, Callable[[int, int], int])
        self.assertNotEqual(C, Callable[[], int])
        self.assertNotEqual(C, Callable[..., int])
        self.assertNotEqual(C, Callable)

    def test_dir(self):
        Callable = self.Callable
        dir_items = set(dir(Callable[..., int]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_cannot_instantiate(self):
        Callable = self.Callable
        mit self.assertRaises(TypeError):
            Callable()
        mit self.assertRaises(TypeError):
            type(Callable)()
        c = Callable[[int], str]
        mit self.assertRaises(TypeError):
            c()
        mit self.assertRaises(TypeError):
            type(c)()

    def test_callable_wrong_forms(self):
        Callable = self.Callable
        mit self.assertRaises(TypeError):
            Callable[int]

    def test_callable_instance_works(self):
        Callable = self.Callable
        def f():
            pass
        self.assertIsInstance(f, Callable)
        self.assertNotIsInstance(Nichts, Callable)

    def test_callable_instance_type_error(self):
        Callable = self.Callable
        def f():
            pass
        mit self.assertRaises(TypeError):
            isinstance(f, Callable[[], Nichts])
        mit self.assertRaises(TypeError):
            isinstance(f, Callable[[], Any])
        mit self.assertRaises(TypeError):
            isinstance(Nichts, Callable[[], Nichts])
        mit self.assertRaises(TypeError):
            isinstance(Nichts, Callable[[], Any])

    def test_repr(self):
        Callable = self.Callable
        fullname = f'{Callable.__module__}.Callable'
        ct0 = Callable[[], bool]
        self.assertEqual(repr(ct0), f'{fullname}[[], bool]')
        ct2 = Callable[[str, float], int]
        self.assertEqual(repr(ct2), f'{fullname}[[str, float], int]')
        ctv = Callable[..., str]
        self.assertEqual(repr(ctv), f'{fullname}[..., str]')
        ct3 = Callable[[str, float], list[int]]
        self.assertEqual(repr(ct3), f'{fullname}[[str, float], list[int]]')

    def test_callable_with_ellipsis(self):
        Callable = self.Callable
        def foo(a: Callable[..., T]):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': Callable[..., T]})

    def test_ellipsis_in_generic(self):
        Callable = self.Callable
        # Shouldn't crash; see https://github.com/python/typing/issues/259
        typing.List[Callable[..., str]]

    def test_or_and_ror(self):
        Callable = self.Callable
        self.assertEqual(Callable | Tuple, Union[Callable, Tuple])
        self.assertEqual(Tuple | Callable, Union[Tuple, Callable])

    def test_basic(self):
        Callable = self.Callable
        alias = Callable[[int, str], float]
        wenn Callable ist collections.abc.Callable:
            self.assertIsInstance(alias, types.GenericAlias)
        self.assertIs(alias.__origin__, collections.abc.Callable)
        self.assertEqual(alias.__args__, (int, str, float))
        self.assertEqual(alias.__parameters__, ())

    def test_weakref(self):
        Callable = self.Callable
        alias = Callable[[int, str], float]
        self.assertEqual(weakref.ref(alias)(), alias)

    def test_pickle(self):
        global T_pickle, P_pickle, TS_pickle  # needed fuer pickling
        Callable = self.Callable
        T_pickle = TypeVar('T_pickle')
        P_pickle = ParamSpec('P_pickle')
        TS_pickle = TypeVarTuple('TS_pickle')

        samples = [
            Callable[[int, str], float],
            Callable[P_pickle, int],
            Callable[P_pickle, T_pickle],
            Callable[Concatenate[int, P_pickle], int],
            Callable[Concatenate[*TS_pickle, P_pickle], int],
        ]
        fuer alias in samples:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(alias=alias, proto=proto):
                    s = pickle.dumps(alias, proto)
                    loaded = pickle.loads(s)
                    self.assertEqual(alias.__origin__, loaded.__origin__)
                    self.assertEqual(alias.__args__, loaded.__args__)
                    self.assertEqual(alias.__parameters__, loaded.__parameters__)

        loesche T_pickle, P_pickle, TS_pickle  # cleaning up global state

    def test_var_substitution(self):
        Callable = self.Callable
        fullname = f"{Callable.__module__}.Callable"
        C1 = Callable[[int, T], T]
        C2 = Callable[[KT, T], VT]
        C3 = Callable[..., T]
        self.assertEqual(C1[str], Callable[[int, str], str])
        self.assertEqual(C1[Nichts], Callable[[int, type(Nichts)], type(Nichts)])
        self.assertEqual(C2[int, float, str], Callable[[int, float], str])
        self.assertEqual(C3[int], Callable[..., int])
        self.assertEqual(C3[NoReturn], Callable[..., NoReturn])

        # multi chaining
        C4 = C2[int, VT, str]
        self.assertEqual(repr(C4), f"{fullname}[[int, ~VT], str]")
        self.assertEqual(repr(C4[dict]), f"{fullname}[[int, dict], str]")
        self.assertEqual(C4[dict], Callable[[int, dict], str])

        # substitute a nested GenericAlias (both typing und the builtin
        # version)
        C5 = Callable[[typing.List[T], tuple[KT, T], VT], int]
        self.assertEqual(C5[int, str, float],
                         Callable[[typing.List[int], tuple[str, int], float], int])

    def test_type_subst_error(self):
        Callable = self.Callable
        P = ParamSpec('P')
        T = TypeVar('T')

        pat = "Expected a list of types, an ellipsis, ParamSpec, oder Concatenate."

        mit self.assertRaisesRegex(TypeError, pat):
            Callable[P, T][0, int]

    def test_type_erasure(self):
        Callable = self.Callable
        klasse C1(Callable):
            def __call__(self):
                gib Nichts
        a = C1[[int], T]
        self.assertIs(a().__class__, C1)
        self.assertEqual(a().__orig_class__, C1[[int], T])

    def test_paramspec(self):
        Callable = self.Callable
        fullname = f"{Callable.__module__}.Callable"
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        C1 = Callable[P, T]
        # substitution
        self.assertEqual(C1[[int], str], Callable[[int], str])
        self.assertEqual(C1[[int, str], str], Callable[[int, str], str])
        self.assertEqual(C1[[], str], Callable[[], str])
        self.assertEqual(C1[..., str], Callable[..., str])
        self.assertEqual(C1[P2, str], Callable[P2, str])
        self.assertEqual(C1[Concatenate[int, P2], str],
                         Callable[Concatenate[int, P2], str])
        self.assertEqual(repr(C1), f"{fullname}[~P, ~T]")
        self.assertEqual(repr(C1[[int, str], str]), f"{fullname}[[int, str], str]")
        mit self.assertRaises(TypeError):
            C1[int, str]

        C2 = Callable[P, int]
        self.assertEqual(C2[[int]], Callable[[int], int])
        self.assertEqual(C2[[int, str]], Callable[[int, str], int])
        self.assertEqual(C2[[]], Callable[[], int])
        self.assertEqual(C2[...], Callable[..., int])
        self.assertEqual(C2[P2], Callable[P2, int])
        self.assertEqual(C2[Concatenate[int, P2]],
                         Callable[Concatenate[int, P2], int])
        # special case in PEP 612 where
        # X[int, str, float] == X[[int, str, float]]
        self.assertEqual(C2[int], Callable[[int], int])
        self.assertEqual(C2[int, str], Callable[[int, str], int])
        self.assertEqual(repr(C2), f"{fullname}[~P, int]")
        self.assertEqual(repr(C2[int, str]), f"{fullname}[[int, str], int]")

    def test_concatenate(self):
        Callable = self.Callable
        fullname = f"{Callable.__module__}.Callable"
        T = TypeVar('T')
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        C = Callable[Concatenate[int, P], T]
        self.assertEqual(repr(C),
                         f"{fullname}[typing.Concatenate[int, ~P], ~T]")
        self.assertEqual(C[P2, int], Callable[Concatenate[int, P2], int])
        self.assertEqual(C[[str, float], int], Callable[[int, str, float], int])
        self.assertEqual(C[[], int], Callable[[int], int])
        self.assertEqual(C[Concatenate[str, P2], int],
                         Callable[Concatenate[int, str, P2], int])
        self.assertEqual(C[..., int], Callable[Concatenate[int, ...], int])

        C = Callable[Concatenate[int, P], int]
        self.assertEqual(repr(C),
                         f"{fullname}[typing.Concatenate[int, ~P], int]")
        self.assertEqual(C[P2], Callable[Concatenate[int, P2], int])
        self.assertEqual(C[[str, float]], Callable[[int, str, float], int])
        self.assertEqual(C[str, float], Callable[[int, str, float], int])
        self.assertEqual(C[[]], Callable[[int], int])
        self.assertEqual(C[Concatenate[str, P2]],
                         Callable[Concatenate[int, str, P2], int])
        self.assertEqual(C[...], Callable[Concatenate[int, ...], int])

    def test_nested_paramspec(self):
        # Since Callable has some special treatment, we want to be sure
        # that substitution works correctly, see gh-103054
        Callable = self.Callable
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        T = TypeVar('T')
        T2 = TypeVar('T2')
        Ts = TypeVarTuple('Ts')
        klasse My(Generic[P, T]):
            pass

        self.assertEqual(My.__parameters__, (P, T))

        C1 = My[[int, T2], Callable[P2, T2]]
        self.assertEqual(C1.__args__, ((int, T2), Callable[P2, T2]))
        self.assertEqual(C1.__parameters__, (T2, P2))
        self.assertEqual(C1[str, [list[int], bytes]],
                         My[[int, str], Callable[[list[int], bytes], str]])

        C2 = My[[Callable[[T2], int], list[T2]], str]
        self.assertEqual(C2.__args__, ((Callable[[T2], int], list[T2]), str))
        self.assertEqual(C2.__parameters__, (T2,))
        self.assertEqual(C2[list[str]],
                         My[[Callable[[list[str]], int], list[list[str]]], str])

        C3 = My[[Callable[P2, T2], T2], T2]
        self.assertEqual(C3.__args__, ((Callable[P2, T2], T2), T2))
        self.assertEqual(C3.__parameters__, (P2, T2))
        self.assertEqual(C3[[], int],
                         My[[Callable[[], int], int], int])
        self.assertEqual(C3[[str, bool], int],
                         My[[Callable[[str, bool], int], int], int])
        self.assertEqual(C3[[str, bool], T][int],
                         My[[Callable[[str, bool], int], int], int])

        C4 = My[[Callable[[int, *Ts, str], T2], T2], T2]
        self.assertEqual(C4.__args__, ((Callable[[int, *Ts, str], T2], T2), T2))
        self.assertEqual(C4.__parameters__, (Ts, T2))
        self.assertEqual(C4[bool, bytes, float],
                         My[[Callable[[int, bool, bytes, str], float], float], float])

    def test_errors(self):
        Callable = self.Callable
        alias = Callable[[int, str], float]
        mit self.assertRaisesRegex(TypeError, "is nicht a generic class"):
            alias[int]
        P = ParamSpec('P')
        C1 = Callable[P, T]
        mit self.assertRaisesRegex(TypeError, "many arguments for"):
            C1[int, str, str]
        mit self.assertRaisesRegex(TypeError, "few arguments for"):
            C1[int]


klasse TypingCallableTests(BaseCallableTests, BaseTestCase):
    Callable = typing.Callable

    def test_consistency(self):
        # bpo-42195
        # Testing collections.abc.Callable's consistency mit typing.Callable
        c1 = typing.Callable[[int, str], dict]
        c2 = collections.abc.Callable[[int, str], dict]
        self.assertEqual(c1.__args__, c2.__args__)
        self.assertEqual(hash(c1.__args__), hash(c2.__args__))


klasse CollectionsCallableTests(BaseCallableTests, BaseTestCase):
    Callable = collections.abc.Callable


klasse LiteralTests(BaseTestCase):
    def test_basics(self):
        # All of these are allowed.
        Literal[1]
        Literal[1, 2, 3]
        Literal["x", "y", "z"]
        Literal[Nichts]
        Literal[Wahr]
        Literal[1, "2", Falsch]
        Literal[Literal[1, 2], Literal[4, 5]]
        Literal[b"foo", u"bar"]

    def test_enum(self):
        importiere enum
        klasse My(enum.Enum):
            A = 'A'

        self.assertEqual(Literal[My.A].__args__, (My.A,))

    def test_illegal_parameters_do_not_raise_runtime_errors(self):
        # Type checkers should reject these types, but we do not
        # wirf errors at runtime to maintain maximum flexibility.
        Literal[int]
        Literal[3j + 2, ..., ()]
        Literal[{"foo": 3, "bar": 4}]
        Literal[T]

    def test_literals_inside_other_types(self):
        List[Literal[1, 2, 3]]
        List[Literal[("foo", "bar", "baz")]]

    def test_repr(self):
        self.assertEqual(repr(Literal[1]), "typing.Literal[1]")
        self.assertEqual(repr(Literal[1, Wahr, "foo"]), "typing.Literal[1, Wahr, 'foo']")
        self.assertEqual(repr(Literal[int]), "typing.Literal[int]")
        self.assertEqual(repr(Literal), "typing.Literal")
        self.assertEqual(repr(Literal[Nichts]), "typing.Literal[Nichts]")
        self.assertEqual(repr(Literal[1, 2, 3, 3]), "typing.Literal[1, 2, 3]")

    def test_dir(self):
        dir_items = set(dir(Literal[1, 2, 3]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            Literal()
        mit self.assertRaises(TypeError):
            Literal[1]()
        mit self.assertRaises(TypeError):
            type(Literal)()
        mit self.assertRaises(TypeError):
            type(Literal[1])()

    def test_no_isinstance_or_issubclass(self):
        mit self.assertRaises(TypeError):
            isinstance(1, Literal[1])
        mit self.assertRaises(TypeError):
            isinstance(int, Literal[1])
        mit self.assertRaises(TypeError):
            issubclass(1, Literal[1])
        mit self.assertRaises(TypeError):
            issubclass(int, Literal[1])

    def test_no_subclassing(self):
        mit self.assertRaises(TypeError):
            klasse Foo(Literal[1]): pass
        mit self.assertRaises(TypeError):
            klasse Bar(Literal): pass

    def test_no_multiple_subscripts(self):
        mit self.assertRaises(TypeError):
            Literal[1][1]

    def test_equal(self):
        self.assertNotEqual(Literal[0], Literal[Falsch])
        self.assertNotEqual(Literal[Wahr], Literal[1])
        self.assertNotEqual(Literal[1], Literal[2])
        self.assertNotEqual(Literal[1, Wahr], Literal[1])
        self.assertNotEqual(Literal[1, Wahr], Literal[1, 1])
        self.assertNotEqual(Literal[1, 2], Literal[Wahr, 2])
        self.assertEqual(Literal[1], Literal[1])
        self.assertEqual(Literal[1, 2], Literal[2, 1])
        self.assertEqual(Literal[1, 2, 3], Literal[1, 2, 3, 3])

    def test_hash(self):
        self.assertEqual(hash(Literal[1]), hash(Literal[1]))
        self.assertEqual(hash(Literal[1, 2]), hash(Literal[2, 1]))
        self.assertEqual(hash(Literal[1, 2, 3]), hash(Literal[1, 2, 3, 3]))

    def test_args(self):
        self.assertEqual(Literal[1, 2, 3].__args__, (1, 2, 3))
        self.assertEqual(Literal[1, 2, 3, 3].__args__, (1, 2, 3))
        self.assertEqual(Literal[1, Literal[2], Literal[3, 4]].__args__, (1, 2, 3, 4))
        # Mutable arguments will nicht be deduplicated
        self.assertEqual(Literal[[], []].__args__, ([], []))

    def test_flatten(self):
        l1 = Literal[Literal[1], Literal[2], Literal[3]]
        l2 = Literal[Literal[1, 2], 3]
        l3 = Literal[Literal[1, 2, 3]]
        fuer l in l1, l2, l3:
            self.assertEqual(l, Literal[1, 2, 3])
            self.assertEqual(l.__args__, (1, 2, 3))

    def test_does_not_flatten_enum(self):
        importiere enum
        klasse Ints(enum.IntEnum):
            A = 1
            B = 2

        l = Literal[
            Literal[Ints.A],
            Literal[Ints.B],
            Literal[1],
            Literal[2],
        ]
        self.assertEqual(l.__args__, (Ints.A, Ints.B, 1, 2))


XK = TypeVar('XK', str, bytes)
XV = TypeVar('XV')


klasse SimpleMapping(Generic[XK, XV]):

    def __getitem__(self, key: XK) -> XV:
        ...

    def __setitem__(self, key: XK, value: XV):
        ...

    def get(self, key: XK, default: XV = Nichts) -> XV:
        ...


klasse MySimpleMapping(SimpleMapping[XK, XV]):

    def __init__(self):
        self.store = {}

    def __getitem__(self, key: str):
        gib self.store[key]

    def __setitem__(self, key: str, value):
        self.store[key] = value

    def get(self, key: str, default=Nichts):
        versuch:
            gib self.store[key]
        ausser KeyError:
            gib default


klasse Coordinate(Protocol):
    x: int
    y: int


@runtime_checkable
klasse Point(Coordinate, Protocol):
    label: str

klasse MyPoint:
    x: int
    y: int
    label: str

klasse XAxis(Protocol):
    x: int

klasse YAxis(Protocol):
    y: int

@runtime_checkable
klasse Position(XAxis, YAxis, Protocol):
    pass

@runtime_checkable
klasse Proto(Protocol):
    attr: int
    def meth(self, arg: str) -> int:
        ...

klasse Concrete(Proto):
    pass

klasse Other:
    attr: int = 1
    def meth(self, arg: str) -> int:
        wenn arg == 'this':
            gib 1
        gib 0

klasse NT(NamedTuple):
    x: int
    y: int

@runtime_checkable
klasse HasCallProtocol(Protocol):
    __call__: typing.Callable


klasse ProtocolTests(BaseTestCase):
    def test_basic_protocol(self):
        @runtime_checkable
        klasse P(Protocol):
            def meth(self):
                pass

        klasse C: pass

        klasse D:
            def meth(self):
                pass

        def f():
            pass

        self.assertIsSubclass(D, P)
        self.assertIsInstance(D(), P)
        self.assertNotIsSubclass(C, P)
        self.assertNotIsInstance(C(), P)
        self.assertNotIsSubclass(types.FunctionType, P)
        self.assertNotIsInstance(f, P)

    def test_runtime_checkable_generic_non_protocol(self):
        # Make sure this doesn't wirf AttributeError
        mit self.assertRaisesRegex(
            TypeError,
            "@runtime_checkable can be only applied to protocol classes",
        ):
            @runtime_checkable
            klasse Foo[T]: ...

    def test_runtime_checkable_generic(self):
        @runtime_checkable
        klasse Foo[T](Protocol):
            def meth(self) -> T: ...

        klasse Impl:
            def meth(self) -> int: ...

        self.assertIsSubclass(Impl, Foo)

        klasse NotImpl:
            def method(self) -> int: ...

        self.assertNotIsSubclass(NotImpl, Foo)

    def test_pep695_generics_can_be_runtime_checkable(self):
        @runtime_checkable
        klasse HasX(Protocol):
            x: int

        klasse Bar[T]:
            x: T
            def __init__(self, x):
                self.x = x

        klasse Capybara[T]:
            y: str
            def __init__(self, y):
                self.y = y

        self.assertIsInstance(Bar(1), HasX)
        self.assertNotIsInstance(Capybara('a'), HasX)

    def test_everything_implements_empty_protocol(self):
        @runtime_checkable
        klasse Empty(Protocol):
            pass

        klasse C:
            pass

        def f():
            pass

        fuer thing in (object, type, tuple, C, types.FunctionType):
            self.assertIsSubclass(thing, Empty)
        fuer thing in (object(), 1, (), typing, f):
            self.assertIsInstance(thing, Empty)

    def test_function_implements_protocol(self):
        def f():
            pass

        self.assertIsInstance(f, HasCallProtocol)

    def test_no_inheritance_from_nominal(self):
        klasse C: pass

        klasse BP(Protocol): pass

        mit self.assertRaises(TypeError):
            klasse P(C, Protocol):
                pass
        mit self.assertRaises(TypeError):
            klasse Q(Protocol, C):
                pass
        mit self.assertRaises(TypeError):
            klasse R(BP, C, Protocol):
                pass

        klasse D(BP, C): pass

        klasse E(C, BP): pass

        self.assertNotIsInstance(D(), E)
        self.assertNotIsInstance(E(), D)

    def test_inheritance_from_object(self):
        # Inheritance von object ist specifically allowed, unlike other nominal classes
        klasse P(Protocol, object):
            x: int

        self.assertEqual(typing.get_protocol_members(P), {'x'})

        klasse OldGeneric(Protocol, Generic[T], object):
            y: T

        self.assertEqual(typing.get_protocol_members(OldGeneric), {'y'})

        klasse NewGeneric[T](Protocol, object):
            z: T

        self.assertEqual(typing.get_protocol_members(NewGeneric), {'z'})

    def test_no_instantiation(self):
        klasse P(Protocol): pass

        mit self.assertRaises(TypeError):
            P()

        klasse C(P): pass

        self.assertIsInstance(C(), C)
        mit self.assertRaises(TypeError):
            C(42)

        T = TypeVar('T')

        klasse PG(Protocol[T]): pass

        mit self.assertRaises(TypeError):
            PG()
        mit self.assertRaises(TypeError):
            PG[int]()
        mit self.assertRaises(TypeError):
            PG[T]()

        klasse CG(PG[T]): pass

        self.assertIsInstance(CG[int](), CG)
        mit self.assertRaises(TypeError):
            CG[int](42)

    def test_protocol_defining_init_does_not_get_overridden(self):
        # check that P.__init__ doesn't get clobbered
        # see https://bugs.python.org/issue44807

        klasse P(Protocol):
            x: int
            def __init__(self, x: int) -> Nichts:
                self.x = x
        klasse C: pass

        c = C()
        P.__init__(c, 1)
        self.assertEqual(c.x, 1)

    def test_concrete_class_inheriting_init_from_protocol(self):
        klasse P(Protocol):
            x: int
            def __init__(self, x: int) -> Nichts:
                self.x = x

        klasse C(P): pass

        c = C(1)
        self.assertIsInstance(c, C)
        self.assertEqual(c.x, 1)

    def test_cannot_instantiate_abstract(self):
        @runtime_checkable
        klasse P(Protocol):
            @abc.abstractmethod
            def ameth(self) -> int:
                wirf NotImplementedError

        klasse B(P):
            pass

        klasse C(B):
            def ameth(self) -> int:
                gib 26

        mit self.assertRaises(TypeError):
            B()
        self.assertIsInstance(C(), P)

    def test_subprotocols_extending(self):
        klasse P1(Protocol):
            def meth1(self):
                pass

        @runtime_checkable
        klasse P2(P1, Protocol):
            def meth2(self):
                pass

        klasse C:
            def meth1(self):
                pass

            def meth2(self):
                pass

        klasse C1:
            def meth1(self):
                pass

        klasse C2:
            def meth2(self):
                pass

        self.assertNotIsInstance(C1(), P2)
        self.assertNotIsInstance(C2(), P2)
        self.assertNotIsSubclass(C1, P2)
        self.assertNotIsSubclass(C2, P2)
        self.assertIsInstance(C(), P2)
        self.assertIsSubclass(C, P2)

    def test_subprotocols_merging(self):
        klasse P1(Protocol):
            def meth1(self):
                pass

        klasse P2(Protocol):
            def meth2(self):
                pass

        @runtime_checkable
        klasse P(P1, P2, Protocol):
            pass

        klasse C:
            def meth1(self):
                pass

            def meth2(self):
                pass

        klasse C1:
            def meth1(self):
                pass

        klasse C2:
            def meth2(self):
                pass

        self.assertNotIsInstance(C1(), P)
        self.assertNotIsInstance(C2(), P)
        self.assertNotIsSubclass(C1, P)
        self.assertNotIsSubclass(C2, P)
        self.assertIsInstance(C(), P)
        self.assertIsSubclass(C, P)

    def test_protocols_issubclass(self):
        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol):
            def x(self): ...

        @runtime_checkable
        klasse PG(Protocol[T]):
            def x(self): ...

        klasse BadP(Protocol):
            def x(self): ...

        klasse BadPG(Protocol[T]):
            def x(self): ...

        klasse C:
            def x(self): ...

        self.assertIsSubclass(C, P)
        self.assertIsSubclass(C, PG)
        self.assertIsSubclass(BadP, PG)

        no_subscripted_generics = (
            "Subscripted generics cannot be used mit klasse und instance checks"
        )

        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            issubclass(C, PG[T])
        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            issubclass(C, PG[C])

        only_runtime_checkable_protocols = (
            "Instance und klasse checks can only be used mit "
            "@runtime_checkable protocols"
        )

        mit self.assertRaisesRegex(TypeError, only_runtime_checkable_protocols):
            issubclass(C, BadP)
        mit self.assertRaisesRegex(TypeError, only_runtime_checkable_protocols):
            issubclass(C, BadPG)

        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            issubclass(P, PG[T])
        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            issubclass(PG, PG[int])

        only_classes_allowed = r"issubclass\(\) arg 1 must be a class"

        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(1, P)
        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(1, PG)
        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(1, BadP)
        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(1, BadPG)

    def test_isinstance_against_superproto_doesnt_affect_subproto_instance(self):
        @runtime_checkable
        klasse Base(Protocol):
            x: int

        @runtime_checkable
        klasse Child(Base, Protocol):
            y: str

        klasse Capybara:
            x = 43

        self.assertIsInstance(Capybara(), Base)
        self.assertNotIsInstance(Capybara(), Child)

    def test_implicit_issubclass_between_two_protocols(self):
        @runtime_checkable
        klasse CallableMembersProto(Protocol):
            def meth(self): ...

        # All the below protocols should be considered "subclasses"
        # of CallableMembersProto at runtime,
        # even though none of them explicitly subclass CallableMembersProto

        klasse IdenticalProto(Protocol):
            def meth(self): ...

        klasse SupersetProto(Protocol):
            def meth(self): ...
            def meth2(self): ...

        klasse NonCallableMembersProto(Protocol):
            meth: Callable[[], Nichts]

        klasse NonCallableMembersSupersetProto(Protocol):
            meth: Callable[[], Nichts]
            meth2: Callable[[str, int], bool]

        klasse MixedMembersProto1(Protocol):
            meth: Callable[[], Nichts]
            def meth2(self): ...

        klasse MixedMembersProto2(Protocol):
            def meth(self): ...
            meth2: Callable[[str, int], bool]

        fuer proto in (
            IdenticalProto, SupersetProto, NonCallableMembersProto,
            NonCallableMembersSupersetProto, MixedMembersProto1, MixedMembersProto2
        ):
            mit self.subTest(proto=proto.__name__):
                self.assertIsSubclass(proto, CallableMembersProto)

        # These two shouldn't be considered subclasses of CallableMembersProto, however,
        # since they don't have the `meth` protocol member

        klasse EmptyProtocol(Protocol): ...
        klasse UnrelatedProtocol(Protocol):
            def wut(self): ...

        self.assertNotIsSubclass(EmptyProtocol, CallableMembersProto)
        self.assertNotIsSubclass(UnrelatedProtocol, CallableMembersProto)

        # These aren't protocols at all (despite having annotations),
        # so they should only be considered subclasses of CallableMembersProto
        # wenn they *actually have an attribute* matching the `meth` member
        # (just having an annotation ist insufficient)

        klasse AnnotatedButNotAProtocol:
            meth: Callable[[], Nichts]

        klasse NotAProtocolButAnImplicitSubclass:
            def meth(self): pass

        klasse NotAProtocolButAnImplicitSubclass2:
            meth: Callable[[], Nichts]
            def meth(self): pass

        klasse NotAProtocolButAnImplicitSubclass3:
            meth: Callable[[], Nichts]
            meth2: Callable[[int, str], bool]
            def meth(self): pass
            def meth2(self, x, y): gib Wahr

        self.assertNotIsSubclass(AnnotatedButNotAProtocol, CallableMembersProto)
        self.assertIsSubclass(NotAProtocolButAnImplicitSubclass, CallableMembersProto)
        self.assertIsSubclass(NotAProtocolButAnImplicitSubclass2, CallableMembersProto)
        self.assertIsSubclass(NotAProtocolButAnImplicitSubclass3, CallableMembersProto)

    def test_isinstance_checks_not_at_whim_of_gc(self):
        self.addCleanup(gc.enable)
        gc.disable()

        mit self.assertRaisesRegex(
            TypeError,
            "Protocols can only inherit von other protocols"
        ):
            klasse Foo(collections.abc.Mapping, Protocol):
                pass

        self.assertNotIsInstance([], collections.abc.Mapping)

    def test_issubclass_and_isinstance_on_Protocol_itself(self):
        klasse C:
            def x(self): pass

        self.assertNotIsSubclass(object, Protocol)
        self.assertNotIsInstance(object(), Protocol)

        self.assertNotIsSubclass(str, Protocol)
        self.assertNotIsInstance('foo', Protocol)

        self.assertNotIsSubclass(C, Protocol)
        self.assertNotIsInstance(C(), Protocol)

        only_classes_allowed = r"issubclass\(\) arg 1 must be a class"

        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(1, Protocol)
        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass('foo', Protocol)
        mit self.assertRaisesRegex(TypeError, only_classes_allowed):
            issubclass(C(), Protocol)

        T = TypeVar('T')

        @runtime_checkable
        klasse EmptyProtocol(Protocol): pass

        @runtime_checkable
        klasse SupportsStartsWith(Protocol):
            def startswith(self, x: str) -> bool: ...

        @runtime_checkable
        klasse SupportsX(Protocol[T]):
            def x(self): ...

        fuer proto in EmptyProtocol, SupportsStartsWith, SupportsX:
            mit self.subTest(proto=proto.__name__):
                self.assertIsSubclass(proto, Protocol)

        # gh-105237 / PR #105239:
        # check that the presence of Protocol subclasses
        # where `issubclass(X, <subclass>)` evaluates to Wahr
        # doesn't influence the result of `issubclass(X, Protocol)`

        self.assertIsSubclass(object, EmptyProtocol)
        self.assertIsInstance(object(), EmptyProtocol)
        self.assertNotIsSubclass(object, Protocol)
        self.assertNotIsInstance(object(), Protocol)

        self.assertIsSubclass(str, SupportsStartsWith)
        self.assertIsInstance('foo', SupportsStartsWith)
        self.assertNotIsSubclass(str, Protocol)
        self.assertNotIsInstance('foo', Protocol)

        self.assertIsSubclass(C, SupportsX)
        self.assertIsInstance(C(), SupportsX)
        self.assertNotIsSubclass(C, Protocol)
        self.assertNotIsInstance(C(), Protocol)

    def test_protocols_issubclass_non_callable(self):
        klasse C:
            x = 1

        @runtime_checkable
        klasse PNonCall(Protocol):
            x = 1

        non_callable_members_illegal = (
            "Protocols mit non-method members don't support issubclass()"
        )

        mit self.assertRaisesRegex(TypeError, non_callable_members_illegal):
            issubclass(C, PNonCall)

        self.assertIsInstance(C(), PNonCall)
        PNonCall.register(C)

        mit self.assertRaisesRegex(TypeError, non_callable_members_illegal):
            issubclass(C, PNonCall)

        self.assertIsInstance(C(), PNonCall)

        # check that non-protocol subclasses are nicht affected
        klasse D(PNonCall): ...

        self.assertNotIsSubclass(C, D)
        self.assertNotIsInstance(C(), D)
        D.register(C)
        self.assertIsSubclass(C, D)
        self.assertIsInstance(C(), D)

        mit self.assertRaisesRegex(TypeError, non_callable_members_illegal):
            issubclass(D, PNonCall)

    def test_no_weird_caching_with_issubclass_after_isinstance(self):
        @runtime_checkable
        klasse Spam(Protocol):
            x: int

        klasse Eggs:
            def __init__(self) -> Nichts:
                self.x = 42

        self.assertIsInstance(Eggs(), Spam)

        # gh-104555: If we didn't override ABCMeta.__subclasscheck__ in _ProtocolMeta,
        # TypeError wouldn't be raised here,
        # als the cached result of the isinstance() check immediately above
        # would mean the issubclass() call would short-circuit
        # before we got to the "raise TypeError" line
        mit self.assertRaisesRegex(
            TypeError,
            "Protocols mit non-method members don't support issubclass()"
        ):
            issubclass(Eggs, Spam)

    def test_no_weird_caching_with_issubclass_after_isinstance_2(self):
        @runtime_checkable
        klasse Spam(Protocol):
            x: int

        klasse Eggs: ...

        self.assertNotIsInstance(Eggs(), Spam)

        # gh-104555: If we didn't override ABCMeta.__subclasscheck__ in _ProtocolMeta,
        # TypeError wouldn't be raised here,
        # als the cached result of the isinstance() check immediately above
        # would mean the issubclass() call would short-circuit
        # before we got to the "raise TypeError" line
        mit self.assertRaisesRegex(
            TypeError,
            "Protocols mit non-method members don't support issubclass()"
        ):
            issubclass(Eggs, Spam)

    def test_no_weird_caching_with_issubclass_after_isinstance_3(self):
        @runtime_checkable
        klasse Spam(Protocol):
            x: int

        klasse Eggs:
            def __getattr__(self, attr):
                wenn attr == "x":
                    gib 42
                wirf AttributeError(attr)

        self.assertNotIsInstance(Eggs(), Spam)

        # gh-104555: If we didn't override ABCMeta.__subclasscheck__ in _ProtocolMeta,
        # TypeError wouldn't be raised here,
        # als the cached result of the isinstance() check immediately above
        # would mean the issubclass() call would short-circuit
        # before we got to the "raise TypeError" line
        mit self.assertRaisesRegex(
            TypeError,
            "Protocols mit non-method members don't support issubclass()"
        ):
            issubclass(Eggs, Spam)

    def test_no_weird_caching_with_issubclass_after_isinstance_pep695(self):
        @runtime_checkable
        klasse Spam[T](Protocol):
            x: T

        klasse Eggs[T]:
            def __init__(self, x: T) -> Nichts:
                self.x = x

        self.assertIsInstance(Eggs(42), Spam)

        # gh-104555: If we didn't override ABCMeta.__subclasscheck__ in _ProtocolMeta,
        # TypeError wouldn't be raised here,
        # als the cached result of the isinstance() check immediately above
        # would mean the issubclass() call would short-circuit
        # before we got to the "raise TypeError" line
        mit self.assertRaisesRegex(
            TypeError,
            "Protocols mit non-method members don't support issubclass()"
        ):
            issubclass(Eggs, Spam)

    def test_protocols_isinstance(self):
        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol):
            def meth(x): ...

        @runtime_checkable
        klasse PG(Protocol[T]):
            def meth(x): ...

        @runtime_checkable
        klasse WeirdProto(Protocol):
            meth = str.maketrans

        @runtime_checkable
        klasse WeirdProto2(Protocol):
            meth = lambda *args, **kwargs: Nichts

        klasse CustomCallable:
            def __call__(self, *args, **kwargs):
                pass

        @runtime_checkable
        klasse WeirderProto(Protocol):
            meth = CustomCallable()

        klasse BadP(Protocol):
            def meth(x): ...

        klasse BadPG(Protocol[T]):
            def meth(x): ...

        klasse C:
            def meth(x): ...

        klasse C2:
            def __init__(self):
                self.meth = lambda: Nichts

        fuer klass in C, C2:
            fuer proto in P, PG, WeirdProto, WeirdProto2, WeirderProto:
                mit self.subTest(klass=klass.__name__, proto=proto.__name__):
                    self.assertIsInstance(klass(), proto)

        no_subscripted_generics = "Subscripted generics cannot be used mit klasse und instance checks"

        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            isinstance(C(), PG[T])
        mit self.assertRaisesRegex(TypeError, no_subscripted_generics):
            isinstance(C(), PG[C])

        only_runtime_checkable_msg = (
            "Instance und klasse checks can only be used "
            "with @runtime_checkable protocols"
        )

        mit self.assertRaisesRegex(TypeError, only_runtime_checkable_msg):
            isinstance(C(), BadP)
        mit self.assertRaisesRegex(TypeError, only_runtime_checkable_msg):
            isinstance(C(), BadPG)

    def test_protocols_isinstance_properties_and_descriptors(self):
        klasse C:
            @property
            def attr(self):
                gib 42

        klasse CustomDescriptor:
            def __get__(self, obj, objtype=Nichts):
                gib 42

        klasse D:
            attr = CustomDescriptor()

        # Check that properties set on superclasses
        # are still found by the isinstance() logic
        klasse E(C): ...
        klasse F(D): ...

        klasse Empty: ...

        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol):
            @property
            def attr(self): ...

        @runtime_checkable
        klasse P1(Protocol):
            attr: int

        @runtime_checkable
        klasse PG(Protocol[T]):
            @property
            def attr(self): ...

        @runtime_checkable
        klasse PG1(Protocol[T]):
            attr: T

        @runtime_checkable
        klasse MethodP(Protocol):
            def attr(self): ...

        @runtime_checkable
        klasse MethodPG(Protocol[T]):
            def attr(self) -> T: ...

        fuer protocol_class in P, P1, PG, PG1, MethodP, MethodPG:
            fuer klass in C, D, E, F:
                mit self.subTest(
                    klass=klass.__name__,
                    protocol_class=protocol_class.__name__
                ):
                    self.assertIsInstance(klass(), protocol_class)

            mit self.subTest(klass="Empty", protocol_class=protocol_class.__name__):
                self.assertNotIsInstance(Empty(), protocol_class)

        klasse BadP(Protocol):
            @property
            def attr(self): ...

        klasse BadP1(Protocol):
            attr: int

        klasse BadPG(Protocol[T]):
            @property
            def attr(self): ...

        klasse BadPG1(Protocol[T]):
            attr: T

        cases = (
            PG[T], PG[C], PG1[T], PG1[C], MethodPG[T],
            MethodPG[C], BadP, BadP1, BadPG, BadPG1
        )

        fuer obj in cases:
            fuer klass in C, D, E, F, Empty:
                mit self.subTest(klass=klass.__name__, obj=obj):
                    mit self.assertRaises(TypeError):
                        isinstance(klass(), obj)

    def test_protocols_isinstance_not_fooled_by_custom_dir(self):
        @runtime_checkable
        klasse HasX(Protocol):
            x: int

        klasse CustomDirWithX:
            x = 10
            def __dir__(self):
                gib []

        klasse CustomDirWithoutX:
            def __dir__(self):
                gib ["x"]

        self.assertIsInstance(CustomDirWithX(), HasX)
        self.assertNotIsInstance(CustomDirWithoutX(), HasX)

    def test_protocols_isinstance_attribute_access_with_side_effects(self):
        klasse C:
            @property
            def attr(self):
                wirf AttributeError('no')

        klasse CustomDescriptor:
            def __get__(self, obj, objtype=Nichts):
                wirf RuntimeError("NO")

        klasse D:
            attr = CustomDescriptor()

        # Check that properties set on superclasses
        # are still found by the isinstance() logic
        klasse E(C): ...
        klasse F(D): ...

        klasse WhyWouldYouDoThis:
            def __getattr__(self, name):
                wirf RuntimeError("wut")

        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol):
            @property
            def attr(self): ...

        @runtime_checkable
        klasse P1(Protocol):
            attr: int

        @runtime_checkable
        klasse PG(Protocol[T]):
            @property
            def attr(self): ...

        @runtime_checkable
        klasse PG1(Protocol[T]):
            attr: T

        @runtime_checkable
        klasse MethodP(Protocol):
            def attr(self): ...

        @runtime_checkable
        klasse MethodPG(Protocol[T]):
            def attr(self) -> T: ...

        fuer protocol_class in P, P1, PG, PG1, MethodP, MethodPG:
            fuer klass in C, D, E, F:
                mit self.subTest(
                    klass=klass.__name__,
                    protocol_class=protocol_class.__name__
                ):
                    self.assertIsInstance(klass(), protocol_class)

            mit self.subTest(
                klass="WhyWouldYouDoThis",
                protocol_class=protocol_class.__name__
            ):
                self.assertNotIsInstance(WhyWouldYouDoThis(), protocol_class)

    def test_protocols_isinstance___slots__(self):
        # As per the consensus in https://github.com/python/typing/issues/1367,
        # this ist desirable behaviour
        @runtime_checkable
        klasse HasX(Protocol):
            x: int

        klasse HasNothingButSlots:
            __slots__ = ("x",)

        self.assertIsInstance(HasNothingButSlots(), HasX)

    def test_protocols_isinstance_py36(self):
        klasse APoint:
            def __init__(self, x, y, label):
                self.x = x
                self.y = y
                self.label = label

        klasse BPoint:
            label = 'B'

            def __init__(self, x, y):
                self.x = x
                self.y = y

        klasse C:
            def __init__(self, attr):
                self.attr = attr

            def meth(self, arg):
                gib 0

        klasse Bad: pass

        self.assertIsInstance(APoint(1, 2, 'A'), Point)
        self.assertIsInstance(BPoint(1, 2), Point)
        self.assertNotIsInstance(MyPoint(), Point)
        self.assertIsInstance(BPoint(1, 2), Position)
        self.assertIsInstance(Other(), Proto)
        self.assertIsInstance(Concrete(), Proto)
        self.assertIsInstance(C(42), Proto)
        self.assertNotIsInstance(Bad(), Proto)
        self.assertNotIsInstance(Bad(), Point)
        self.assertNotIsInstance(Bad(), Position)
        self.assertNotIsInstance(Bad(), Concrete)
        self.assertNotIsInstance(Other(), Concrete)
        self.assertIsInstance(NT(1, 2), Position)

    def test_protocols_isinstance_init(self):
        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol):
            x = 1

        @runtime_checkable
        klasse PG(Protocol[T]):
            x = 1

        klasse C:
            def __init__(self, x):
                self.x = x

        self.assertIsInstance(C(1), P)
        self.assertIsInstance(C(1), PG)

    def test_protocols_isinstance_monkeypatching(self):
        @runtime_checkable
        klasse HasX(Protocol):
            x: int

        klasse Foo: ...

        f = Foo()
        self.assertNotIsInstance(f, HasX)
        f.x = 42
        self.assertIsInstance(f, HasX)
        loesche f.x
        self.assertNotIsInstance(f, HasX)

    def test_protocol_checks_after_subscript(self):
        klasse P(Protocol[T]): pass
        klasse C(P[T]): pass
        klasse Other1: pass
        klasse Other2: pass
        CA = C[Any]

        self.assertNotIsInstance(Other1(), C)
        self.assertNotIsSubclass(Other2, C)

        klasse D1(C[Any]): pass
        klasse D2(C[Any]): pass
        CI = C[int]

        self.assertIsInstance(D1(), C)
        self.assertIsSubclass(D2, C)

    def test_protocols_support_register(self):
        @runtime_checkable
        klasse P(Protocol):
            x = 1

        klasse PM(Protocol):
            def meth(self): pass

        klasse D(PM): pass

        klasse C: pass

        D.register(C)
        P.register(C)
        self.assertIsInstance(C(), P)
        self.assertIsInstance(C(), D)

    def test_none_on_non_callable_doesnt_block_implementation(self):
        @runtime_checkable
        klasse P(Protocol):
            x = 1

        klasse A:
            x = 1

        klasse B(A):
            x = Nichts

        klasse C:
            def __init__(self):
                self.x = Nichts

        self.assertIsInstance(B(), P)
        self.assertIsInstance(C(), P)

    def test_none_on_callable_blocks_implementation(self):
        @runtime_checkable
        klasse P(Protocol):
            def x(self): ...

        klasse A:
            def x(self): ...

        klasse B(A):
            x = Nichts

        klasse C:
            def __init__(self):
                self.x = Nichts

        self.assertNotIsInstance(B(), P)
        self.assertNotIsInstance(C(), P)

    def test_non_protocol_subclasses(self):
        klasse P(Protocol):
            x = 1

        @runtime_checkable
        klasse PR(Protocol):
            def meth(self): pass

        klasse NonP(P):
            x = 1

        klasse NonPR(PR): pass

        klasse C(metaclass=abc.ABCMeta):
            x = 1

        klasse D(metaclass=abc.ABCMeta):
            def meth(self): pass

        self.assertNotIsInstance(C(), NonP)
        self.assertNotIsInstance(D(), NonPR)
        self.assertNotIsSubclass(C, NonP)
        self.assertNotIsSubclass(D, NonPR)
        self.assertIsInstance(NonPR(), PR)
        self.assertIsSubclass(NonPR, PR)

        self.assertNotIn("__protocol_attrs__", vars(NonP))
        self.assertNotIn("__protocol_attrs__", vars(NonPR))
        self.assertNotIn("__non_callable_proto_members__", vars(NonP))
        self.assertNotIn("__non_callable_proto_members__", vars(NonPR))

        self.assertEqual(get_protocol_members(P), {"x"})
        self.assertEqual(get_protocol_members(PR), {"meth"})

        # the returned object should be immutable,
        # und should be a different object to the original attribute
        # to prevent users von (accidentally oder deliberately)
        # mutating the attribute on the original class
        self.assertIsInstance(get_protocol_members(P), frozenset)
        self.assertIsNot(get_protocol_members(P), P.__protocol_attrs__)
        self.assertIsInstance(get_protocol_members(PR), frozenset)
        self.assertIsNot(get_protocol_members(PR), P.__protocol_attrs__)

        acceptable_extra_attrs = {
            '_is_protocol', '_is_runtime_protocol', '__parameters__',
            '__init__', '__annotations__', '__subclasshook__', '__annotate__',
            '__annotations_cache__', '__annotate_func__',
        }
        self.assertLessEqual(vars(NonP).keys(), vars(C).keys() | acceptable_extra_attrs)
        self.assertLessEqual(
            vars(NonPR).keys(), vars(D).keys() | acceptable_extra_attrs
        )

    def test_custom_subclasshook(self):
        klasse P(Protocol):
            x = 1

        klasse OKClass: pass

        klasse BadClass:
            x = 1

        klasse C(P):
            @classmethod
            def __subclasshook__(cls, other):
                gib other.__name__.startswith("OK")

        self.assertIsInstance(OKClass(), C)
        self.assertNotIsInstance(BadClass(), C)
        self.assertIsSubclass(OKClass, C)
        self.assertNotIsSubclass(BadClass, C)

    def test_custom_subclasshook_2(self):
        @runtime_checkable
        klasse HasX(Protocol):
            # The presence of a non-callable member
            # would mean issubclass() checks would fail mit TypeError
            # wenn it weren't fuer the custom `__subclasshook__` method
            x = 1

            @classmethod
            def __subclasshook__(cls, other):
                gib hasattr(other, 'x')

        klasse Empty: pass

        klasse ImplementsHasX:
            x = 1

        self.assertIsInstance(ImplementsHasX(), HasX)
        self.assertNotIsInstance(Empty(), HasX)
        self.assertIsSubclass(ImplementsHasX, HasX)
        self.assertNotIsSubclass(Empty, HasX)

        # isinstance() und issubclass() checks against this still wirf TypeError,
        # despite the presence of the custom __subclasshook__ method,
        # als it's nicht decorated mit @runtime_checkable
        klasse NotRuntimeCheckable(Protocol):
            @classmethod
            def __subclasshook__(cls, other):
                gib hasattr(other, 'x')

        must_be_runtime_checkable = (
            "Instance und klasse checks can only be used "
            "with @runtime_checkable protocols"
        )

        mit self.assertRaisesRegex(TypeError, must_be_runtime_checkable):
            issubclass(object, NotRuntimeCheckable)
        mit self.assertRaisesRegex(TypeError, must_be_runtime_checkable):
            isinstance(object(), NotRuntimeCheckable)

    def test_issubclass_fails_correctly(self):
        @runtime_checkable
        klasse NonCallableMembers(Protocol):
            x = 1

        klasse NotRuntimeCheckable(Protocol):
            def callable_member(self) -> int: ...

        @runtime_checkable
        klasse RuntimeCheckable(Protocol):
            def callable_member(self) -> int: ...

        klasse C: pass

        # These three all exercise different code paths,
        # but should result in the same error message:
        fuer protocol in NonCallableMembers, NotRuntimeCheckable, RuntimeCheckable:
            mit self.subTest(proto_name=protocol.__name__):
                mit self.assertRaisesRegex(
                    TypeError, r"issubclass\(\) arg 1 must be a class"
                ):
                    issubclass(C(), protocol)

    def test_defining_generic_protocols(self):
        T = TypeVar('T')
        T2 = TypeVar('T2')
        S = TypeVar('S')

        @runtime_checkable
        klasse PR(Protocol[T, S]):
            def meth(self): pass

        klasse P(PR[int, T], Protocol[T]):
            y = 1

        self.assertEqual(P.__parameters__, (T,))

        mit self.assertRaises(TypeError):
            PR[int]
        mit self.assertRaises(TypeError):
            P[int, str]
        mit self.assertRaisesRegex(
            TypeError,
            re.escape('Some type variables (~S) are nicht listed in Protocol[~T, ~T2]'),
        ):
            klasse ExtraTypeVars(P[S], Protocol[T, T2]): ...

        klasse C(PR[int, T]): pass

        self.assertEqual(C.__parameters__, (T,))
        self.assertIsInstance(C[str](), C)

    def test_defining_generic_protocols_old_style(self):
        T = TypeVar('T')
        T2 = TypeVar('T2')
        S = TypeVar('S')

        @runtime_checkable
        klasse PR(Protocol, Generic[T, S]):
            def meth(self): pass

        klasse P(PR[int, str], Protocol):
            y = 1

        mit self.assertRaises(TypeError):
            issubclass(PR[int, str], PR)
        self.assertIsSubclass(P, PR)
        mit self.assertRaises(TypeError):
            PR[int]

        klasse P1(Protocol, Generic[T]):
            def bar(self, x: T) -> str: ...

        self.assertEqual(P1.__parameters__, (T,))

        klasse P2(Generic[T], Protocol):
            def bar(self, x: T) -> str: ...

        self.assertEqual(P2.__parameters__, (T,))

        msg = re.escape('Some type variables (~S) are nicht listed in Protocol[~T, ~T2]')
        mit self.assertRaisesRegex(TypeError, msg):
            klasse ExtraTypeVars(P1[S], Protocol[T, T2]): ...
        mit self.assertRaisesRegex(TypeError, msg):
            klasse ExtraTypeVars(P2[S], Protocol[T, T2]): ...

        @runtime_checkable
        klasse PSub(P1[str], Protocol):
            x = 1

        klasse Test:
            x = 1

            def bar(self, x: str) -> str:
                gib x

        self.assertIsInstance(Test(), PSub)

    def test_protocol_parameter_order(self):
        # https://github.com/python/cpython/issues/137191
        T1 = TypeVar("T1")
        T2 = TypeVar("T2", default=object)

        klasse A(Protocol[T1]): ...

        klasse B0(A[T2], Generic[T1, T2]): ...
        self.assertEqual(B0.__parameters__, (T1, T2))

        klasse B1(A[T2], Protocol, Generic[T1, T2]): ...
        self.assertEqual(B1.__parameters__, (T1, T2))

        klasse B2(A[T2], Protocol[T1, T2]): ...
        self.assertEqual(B2.__parameters__, (T1, T2))

        klasse B3[T1, T2](A[T2], Protocol):
            @staticmethod
            def get_typeparams():
                gib (T1, T2)
        self.assertEqual(B3.__parameters__, B3.get_typeparams())

    def test_pep695_generic_protocol_callable_members(self):
        @runtime_checkable
        klasse Foo[T](Protocol):
            def meth(self, x: T) -> Nichts: ...

        klasse Bar[T]:
            def meth(self, x: T) -> Nichts: ...

        self.assertIsInstance(Bar(), Foo)
        self.assertIsSubclass(Bar, Foo)

        @runtime_checkable
        klasse SupportsTrunc[T](Protocol):
            def __trunc__(self) -> T: ...

        self.assertIsInstance(0.0, SupportsTrunc)
        self.assertIsSubclass(float, SupportsTrunc)

    def test_init_called(self):
        T = TypeVar('T')

        klasse P(Protocol[T]): pass

        klasse C(P[T]):
            def __init__(self):
                self.test = 'OK'

        self.assertEqual(C[int]().test, 'OK')

        klasse B:
            def __init__(self):
                self.test = 'OK'

        klasse D1(B, P[T]):
            pass

        self.assertEqual(D1[int]().test, 'OK')

        klasse D2(P[T], B):
            pass

        self.assertEqual(D2[int]().test, 'OK')

    def test_new_called(self):
        T = TypeVar('T')

        klasse P(Protocol[T]): pass

        klasse C(P[T]):
            def __new__(cls, *args):
                self = super().__new__(cls, *args)
                self.test = 'OK'
                gib self

        self.assertEqual(C[int]().test, 'OK')
        mit self.assertRaises(TypeError):
            C[int](42)
        mit self.assertRaises(TypeError):
            C[int](a=42)

    def test_protocols_bad_subscripts(self):
        T = TypeVar('T')
        S = TypeVar('S')
        mit self.assertRaises(TypeError):
            klasse P(Protocol[T, T]): pass
        mit self.assertRaises(TypeError):
            klasse Q(Protocol[int]): pass
        mit self.assertRaises(TypeError):
            klasse R(Protocol[T], Protocol[S]): pass
        mit self.assertRaises(TypeError):
            klasse S(typing.Mapping[T, S], Protocol[T]): pass

    def test_generic_protocols_repr(self):
        T = TypeVar('T')
        S = TypeVar('S')

        klasse P(Protocol[T, S]): pass

        self.assertEndsWith(repr(P[T, S]), 'P[~T, ~S]')
        self.assertEndsWith(repr(P[int, str]), 'P[int, str]')

    def test_generic_protocols_eq(self):
        T = TypeVar('T')
        S = TypeVar('S')

        klasse P(Protocol[T, S]): pass

        self.assertEqual(P, P)
        self.assertEqual(P[int, T], P[int, T])
        self.assertEqual(P[T, T][Tuple[T, S]][int, str],
                         P[Tuple[int, str], Tuple[int, str]])

    def test_generic_protocols_special_from_generic(self):
        T = TypeVar('T')

        klasse P(Protocol[T]): pass

        self.assertEqual(P.__parameters__, (T,))
        self.assertEqual(P[int].__parameters__, ())
        self.assertEqual(P[int].__args__, (int,))
        self.assertIs(P[int].__origin__, P)

    def test_generic_protocols_special_from_protocol(self):
        @runtime_checkable
        klasse PR(Protocol):
            x = 1

        klasse P(Protocol):
            def meth(self):
                pass

        T = TypeVar('T')

        klasse PG(Protocol[T]):
            x = 1

            def meth(self):
                pass

        self.assertIs(P._is_protocol, Wahr)
        self.assertIs(PR._is_protocol, Wahr)
        self.assertIs(PG._is_protocol, Wahr)
        self.assertIs(P._is_runtime_protocol, Falsch)
        self.assertIs(PR._is_runtime_protocol, Wahr)
        self.assertIs(PG[int]._is_protocol, Wahr)
        self.assertEqual(typing._get_protocol_attrs(P), {'meth'})
        self.assertEqual(typing._get_protocol_attrs(PR), {'x'})
        self.assertEqual(frozenset(typing._get_protocol_attrs(PG)),
                         frozenset({'x', 'meth'}))

    def test_no_runtime_deco_on_nominal(self):
        mit self.assertRaises(TypeError):
            @runtime_checkable
            klasse C: pass

        klasse Proto(Protocol):
            x = 1

        mit self.assertRaises(TypeError):
            @runtime_checkable
            klasse Concrete(Proto):
                pass

    def test_none_treated_correctly(self):
        @runtime_checkable
        klasse P(Protocol):
            x = Nichts  # type: int

        klasse B(object): pass

        self.assertNotIsInstance(B(), P)

        klasse C:
            x = 1

        klasse D:
            x = Nichts

        self.assertIsInstance(C(), P)
        self.assertIsInstance(D(), P)

        klasse CI:
            def __init__(self):
                self.x = 1

        klasse DI:
            def __init__(self):
                self.x = Nichts

        self.assertIsInstance(CI(), P)
        self.assertIsInstance(DI(), P)

    def test_protocols_in_unions(self):
        klasse P(Protocol):
            x = Nichts  # type: int

        Alias = typing.Union[typing.Iterable, P]
        Alias2 = typing.Union[P, typing.Iterable]
        self.assertEqual(Alias, Alias2)

    def test_protocols_pickleable(self):
        global P, CP  # pickle wants to reference the klasse by name
        T = TypeVar('T')

        @runtime_checkable
        klasse P(Protocol[T]):
            x = 1

        klasse CP(P[int]):
            pass

        c = CP()
        c.foo = 42
        c.bar = 'abc'
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(c, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.x, 1)
            self.assertEqual(x.__dict__, {'foo': 42, 'bar': 'abc'})
            s = pickle.dumps(P, proto)
            D = pickle.loads(s)

            klasse E:
                x = 1

            self.assertIsInstance(E(), D)

    def test_runtime_checkable_with_match_args(self):
        @runtime_checkable
        klasse P_regular(Protocol):
            x: int
            y: int

        @runtime_checkable
        klasse P_match(Protocol):
            __match_args__ = ('x', 'y')
            x: int
            y: int

        klasse Regular:
            def __init__(self, x: int, y: int):
                self.x = x
                self.y = y

        klasse WithMatch:
            __match_args__ = ('x', 'y', 'z')
            def __init__(self, x: int, y: int, z: int):
                self.x = x
                self.y = y
                self.z = z

        klasse Nope: ...

        self.assertIsInstance(Regular(1, 2), P_regular)
        self.assertIsInstance(Regular(1, 2), P_match)
        self.assertIsInstance(WithMatch(1, 2, 3), P_regular)
        self.assertIsInstance(WithMatch(1, 2, 3), P_match)
        self.assertNotIsInstance(Nope(), P_regular)
        self.assertNotIsInstance(Nope(), P_match)

    def test_supports_int(self):
        self.assertIsSubclass(int, typing.SupportsInt)
        self.assertNotIsSubclass(str, typing.SupportsInt)

    def test_supports_float(self):
        self.assertIsSubclass(float, typing.SupportsFloat)
        self.assertNotIsSubclass(str, typing.SupportsFloat)

    def test_supports_complex(self):

        klasse C:
            def __complex__(self):
                gib 0j

        self.assertIsSubclass(complex, typing.SupportsComplex)
        self.assertIsSubclass(C, typing.SupportsComplex)
        self.assertNotIsSubclass(str, typing.SupportsComplex)

    def test_supports_bytes(self):

        klasse B:
            def __bytes__(self):
                gib b''

        self.assertIsSubclass(bytes, typing.SupportsBytes)
        self.assertIsSubclass(B, typing.SupportsBytes)
        self.assertNotIsSubclass(str, typing.SupportsBytes)

    def test_supports_abs(self):
        self.assertIsSubclass(float, typing.SupportsAbs)
        self.assertIsSubclass(int, typing.SupportsAbs)
        self.assertNotIsSubclass(str, typing.SupportsAbs)

    def test_supports_round(self):
        issubclass(float, typing.SupportsRound)
        self.assertIsSubclass(float, typing.SupportsRound)
        self.assertIsSubclass(int, typing.SupportsRound)
        self.assertNotIsSubclass(str, typing.SupportsRound)

    def test_reversible(self):
        self.assertIsSubclass(list, typing.Reversible)
        self.assertNotIsSubclass(int, typing.Reversible)

    def test_supports_index(self):
        self.assertIsSubclass(int, typing.SupportsIndex)
        self.assertNotIsSubclass(str, typing.SupportsIndex)

    def test_bundled_protocol_instance_works(self):
        self.assertIsInstance(0, typing.SupportsAbs)
        klasse C1(typing.SupportsInt):
            def __int__(self) -> int:
                gib 42
        klasse C2(C1):
            pass
        c = C2()
        self.assertIsInstance(c, C1)

    def test_collections_protocols_allowed(self):
        @runtime_checkable
        klasse Custom(collections.abc.Iterable, Protocol):
            def close(self): ...

        klasse A: pass
        klasse B:
            def __iter__(self):
                gib []
            def close(self):
                gib 0

        self.assertIsSubclass(B, Custom)
        self.assertNotIsSubclass(A, Custom)

        @runtime_checkable
        klasse ReleasableBuffer(collections.abc.Buffer, Protocol):
            def __release_buffer__(self, mv: memoryview) -> Nichts: ...

        klasse C: pass
        klasse D:
            def __buffer__(self, flags: int) -> memoryview:
                gib memoryview(b'')
            def __release_buffer__(self, mv: memoryview) -> Nichts:
                pass

        self.assertIsSubclass(D, ReleasableBuffer)
        self.assertIsInstance(D(), ReleasableBuffer)
        self.assertNotIsSubclass(C, ReleasableBuffer)
        self.assertNotIsInstance(C(), ReleasableBuffer)

    def test_io_reader_protocol_allowed(self):
        @runtime_checkable
        klasse CustomReader(io.Reader[bytes], Protocol):
            def close(self): ...

        klasse A: pass
        klasse B:
            def read(self, sz=-1):
                gib b""
            def close(self):
                pass

        self.assertIsSubclass(B, CustomReader)
        self.assertIsInstance(B(), CustomReader)
        self.assertNotIsSubclass(A, CustomReader)
        self.assertNotIsInstance(A(), CustomReader)

    def test_io_writer_protocol_allowed(self):
        @runtime_checkable
        klasse CustomWriter(io.Writer[bytes], Protocol):
            def close(self): ...

        klasse A: pass
        klasse B:
            def write(self, b):
                pass
            def close(self):
                pass

        self.assertIsSubclass(B, CustomWriter)
        self.assertIsInstance(B(), CustomWriter)
        self.assertNotIsSubclass(A, CustomWriter)
        self.assertNotIsInstance(A(), CustomWriter)

    def test_builtin_protocol_allowlist(self):
        mit self.assertRaises(TypeError):
            klasse CustomProtocol(TestCase, Protocol):
                pass

        klasse CustomPathLikeProtocol(os.PathLike, Protocol):
            pass

        klasse CustomContextManager(typing.ContextManager, Protocol):
            pass

        klasse CustomAsyncIterator(typing.AsyncIterator, Protocol):
            pass

    def test_non_runtime_protocol_isinstance_check(self):
        klasse P(Protocol):
            x: int

        mit self.assertRaisesRegex(TypeError, "@runtime_checkable"):
            isinstance(1, P)

    def test_super_call_init(self):
        klasse P(Protocol):
            x: int

        klasse Foo(P):
            def __init__(self):
                super().__init__()

        Foo()  # Previously triggered RecursionError

    def test_get_protocol_members(self):
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(object)
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(object())
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(Protocol)
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(Generic)

        klasse P(Protocol):
            a: int
            def b(self) -> str: ...
            @property
            def c(self) -> int: ...

        self.assertEqual(get_protocol_members(P), {'a', 'b', 'c'})
        self.assertIsInstance(get_protocol_members(P), frozenset)
        self.assertIsNot(get_protocol_members(P), P.__protocol_attrs__)

        klasse Concrete:
            a: int
            def b(self) -> str: gib "capybara"
            @property
            def c(self) -> int: gib 5

        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(Concrete)
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(Concrete())

        klasse ConcreteInherit(P):
            a: int = 42
            def b(self) -> str: gib "capybara"
            @property
            def c(self) -> int: gib 5

        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(ConcreteInherit)
        mit self.assertRaisesRegex(TypeError, "not a Protocol"):
            get_protocol_members(ConcreteInherit())

    def test_is_protocol(self):
        self.assertWahr(is_protocol(Proto))
        self.assertWahr(is_protocol(Point))
        self.assertFalsch(is_protocol(Concrete))
        self.assertFalsch(is_protocol(Concrete()))
        self.assertFalsch(is_protocol(Generic))
        self.assertFalsch(is_protocol(object))

        # Protocol ist nicht itself a protocol
        self.assertFalsch(is_protocol(Protocol))

    def test_interaction_with_isinstance_checks_on_superclasses_with_ABCMeta(self):
        # Ensure the cache ist empty, oder this test won't work correctly
        collections.abc.Sized._abc_registry_clear()

        klasse Foo(collections.abc.Sized, Protocol): pass

        # gh-105144: this previously raised TypeError
        # wenn a Protocol subclass of Sized had been created
        # before any isinstance() checks against Sized
        self.assertNotIsInstance(1, collections.abc.Sized)

    def test_interaction_with_isinstance_checks_on_superclasses_with_ABCMeta_2(self):
        # Ensure the cache ist empty, oder this test won't work correctly
        collections.abc.Sized._abc_registry_clear()

        klasse Foo(typing.Sized, Protocol): pass

        # gh-105144: this previously raised TypeError
        # wenn a Protocol subclass of Sized had been created
        # before any isinstance() checks against Sized
        self.assertNotIsInstance(1, typing.Sized)

    def test_empty_protocol_decorated_with_final(self):
        @final
        @runtime_checkable
        klasse EmptyProtocol(Protocol): ...

        self.assertIsSubclass(object, EmptyProtocol)
        self.assertIsInstance(object(), EmptyProtocol)

    def test_protocol_decorated_with_final_callable_members(self):
        @final
        @runtime_checkable
        klasse ProtocolWithMethod(Protocol):
            def startswith(self, string: str) -> bool: ...

        self.assertIsSubclass(str, ProtocolWithMethod)
        self.assertNotIsSubclass(int, ProtocolWithMethod)
        self.assertIsInstance('foo', ProtocolWithMethod)
        self.assertNotIsInstance(42, ProtocolWithMethod)

    def test_protocol_decorated_with_final_noncallable_members(self):
        @final
        @runtime_checkable
        klasse ProtocolWithNonCallableMember(Protocol):
            x: int

        klasse Foo:
            x = 42

        only_callable_members_please = (
            r"Protocols mit non-method members don't support issubclass()"
        )

        mit self.assertRaisesRegex(TypeError, only_callable_members_please):
            issubclass(Foo, ProtocolWithNonCallableMember)

        mit self.assertRaisesRegex(TypeError, only_callable_members_please):
            issubclass(int, ProtocolWithNonCallableMember)

        self.assertIsInstance(Foo(), ProtocolWithNonCallableMember)
        self.assertNotIsInstance(42, ProtocolWithNonCallableMember)

    def test_protocol_decorated_with_final_mixed_members(self):
        @final
        @runtime_checkable
        klasse ProtocolWithMixedMembers(Protocol):
            x: int
            def method(self) -> Nichts: ...

        klasse Foo:
            x = 42
            def method(self) -> Nichts: ...

        only_callable_members_please = (
            r"Protocols mit non-method members don't support issubclass()"
        )

        mit self.assertRaisesRegex(TypeError, only_callable_members_please):
            issubclass(Foo, ProtocolWithMixedMembers)

        mit self.assertRaisesRegex(TypeError, only_callable_members_please):
            issubclass(int, ProtocolWithMixedMembers)

        self.assertIsInstance(Foo(), ProtocolWithMixedMembers)
        self.assertNotIsInstance(42, ProtocolWithMixedMembers)

    def test_protocol_issubclass_error_message(self):
        @runtime_checkable
        klasse Vec2D(Protocol):
            x: float
            y: float

            def square_norm(self) -> float:
                gib self.x ** 2 + self.y ** 2

        self.assertEqual(Vec2D.__protocol_attrs__, {'x', 'y', 'square_norm'})
        expected_error_message = (
            "Protocols mit non-method members don't support issubclass()."
            " Non-method members: 'x', 'y'."
        )
        mit self.assertRaisesRegex(TypeError, re.escape(expected_error_message)):
            issubclass(int, Vec2D)

    def test_nonruntime_protocol_interaction_with_evil_classproperty(self):
        klasse classproperty:
            def __get__(self, instance, type):
                wirf RuntimeError("NO")

        klasse Commentable(Protocol):
            evil = classproperty()

        # recognised als a protocol attr,
        # but nicht actually accessed by the protocol metaclass
        # (which would wirf RuntimeError) fuer non-runtime protocols.
        # See gh-113320
        self.assertEqual(get_protocol_members(Commentable), {"evil"})

    def test_runtime_protocol_interaction_with_evil_classproperty(self):
        klasse CustomError(Exception): pass

        klasse classproperty:
            def __get__(self, instance, type):
                wirf CustomError

        mit self.assertRaises(TypeError) als cm:
            @runtime_checkable
            klasse Commentable(Protocol):
                evil = classproperty()

        exc = cm.exception
        self.assertEqual(
            exc.args[0],
            "Failed to determine whether protocol member 'evil' ist a method member"
        )
        self.assertIs(type(exc.__cause__), CustomError)

    def test_isinstance_with_deferred_evaluation_of_annotations(self):
        @runtime_checkable
        klasse P(Protocol):
            def meth(self):
                ...

        klasse DeferredClass:
            x: undefined

        klasse DeferredClassImplementingP:
            x: undefined | int

            def __init__(self):
                self.x = 0

            def meth(self):
                ...

        # override meth mit a non-method attribute to make it part of __annotations__ instead of __dict__
        klasse SubProtocol(P, Protocol):
            meth: undefined


        self.assertIsSubclass(SubProtocol, P)
        self.assertNotIsInstance(DeferredClass(), P)
        self.assertIsInstance(DeferredClassImplementingP(), P)

    def test_deferred_evaluation_of_annotations(self):
        klasse DeferredProto(Protocol):
            x: DoesNotExist
        self.assertEqual(get_protocol_members(DeferredProto), {"x"})
        self.assertEqual(
            annotationlib.get_annotations(DeferredProto, format=annotationlib.Format.STRING),
            {'x': 'DoesNotExist'}
        )


klasse GenericTests(BaseTestCase):

    def test_basics(self):
        X = SimpleMapping[str, Any]
        self.assertEqual(X.__parameters__, ())
        mit self.assertRaises(TypeError):
            X[str]
        mit self.assertRaises(TypeError):
            X[str, str]
        Y = SimpleMapping[XK, str]
        self.assertEqual(Y.__parameters__, (XK,))
        Y[str]
        mit self.assertRaises(TypeError):
            Y[str, str]
        SM1 = SimpleMapping[str, int]
        mit self.assertRaises(TypeError):
            issubclass(SM1, SimpleMapping)
        self.assertIsInstance(SM1(), SimpleMapping)
        T = TypeVar("T")
        self.assertEqual(List[list[T] | float].__parameters__, (T,))

    def test_generic_errors(self):
        T = TypeVar('T')
        S = TypeVar('S')
        mit self.assertRaises(TypeError):
            Generic[T][T]
        mit self.assertRaises(TypeError):
            Generic[T][S]
        mit self.assertRaises(TypeError):
            klasse C(Generic[T], Generic[T]): ...
        mit self.assertRaises(TypeError):
            isinstance([], List[int])
        mit self.assertRaises(TypeError):
            issubclass(list, List[int])
        mit self.assertRaises(TypeError):
            klasse NewGeneric(Generic): ...
        mit self.assertRaises(TypeError):
            klasse MyGeneric(Generic[T], Generic[S]): ...
        mit self.assertRaises(TypeError):
            klasse MyGeneric2(List[T], Generic[S]): ...
        mit self.assertRaises(TypeError):
            Generic[()]
        klasse D(Generic[T]): pass
        mit self.assertRaises(TypeError):
            D[()]

    def test_generic_subclass_checks(self):
        fuer typ in [list[int], List[int],
                    tuple[int, str], Tuple[int, str],
                    typing.Callable[..., Nichts],
                    collections.abc.Callable[..., Nichts]]:
            mit self.subTest(typ=typ):
                self.assertRaises(TypeError, issubclass, typ, object)
                self.assertRaises(TypeError, issubclass, typ, type)
                self.assertRaises(TypeError, issubclass, typ, typ)
                self.assertRaises(TypeError, issubclass, object, typ)

                # isinstance ist fine:
                self.assertWahr(isinstance(typ, object))
                # but, nicht when the right arg ist also a generic:
                self.assertRaises(TypeError, isinstance, typ, typ)

    def test_init(self):
        T = TypeVar('T')
        S = TypeVar('S')
        mit self.assertRaises(TypeError):
            Generic[T, T]
        mit self.assertRaises(TypeError):
            Generic[T, S, T]

    def test_init_subclass(self):
        klasse X(typing.Generic[T]):
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.attr = 42
        klasse Y(X):
            pass
        self.assertEqual(Y.attr, 42)
        mit self.assertRaises(AttributeError):
            X.attr
        X.attr = 1
        Y.attr = 2
        klasse Z(Y):
            pass
        klasse W(X[int]):
            pass
        self.assertEqual(Y.attr, 2)
        self.assertEqual(Z.attr, 42)
        self.assertEqual(W.attr, 42)

    def test_repr(self):
        self.assertEqual(repr(SimpleMapping),
                         f"<class '{__name__}.SimpleMapping'>")
        self.assertEqual(repr(MySimpleMapping),
                         f"<class '{__name__}.MySimpleMapping'>")

    def test_chain_repr(self):
        T = TypeVar('T')
        S = TypeVar('S')

        klasse C(Generic[T]):
            pass

        X = C[Tuple[S, T]]
        self.assertEqual(X, C[Tuple[S, T]])
        self.assertNotEqual(X, C[Tuple[T, S]])

        Y = X[T, int]
        self.assertEqual(Y, X[T, int])
        self.assertNotEqual(Y, X[S, int])
        self.assertNotEqual(Y, X[T, str])

        Z = Y[str]
        self.assertEqual(Z, Y[str])
        self.assertNotEqual(Z, Y[int])
        self.assertNotEqual(Z, Y[T])

        self.assertEndsWith(str(Z), '.C[typing.Tuple[str, int]]')

    def test_new_repr(self):
        T = TypeVar('T')
        U = TypeVar('U', covariant=Wahr)
        S = TypeVar('S')

        self.assertEqual(repr(List), 'typing.List')
        self.assertEqual(repr(List[T]), 'typing.List[~T]')
        self.assertEqual(repr(List[U]), 'typing.List[+U]')
        self.assertEqual(repr(List[S][T][int]), 'typing.List[int]')
        self.assertEqual(repr(List[int]), 'typing.List[int]')

    def test_new_repr_complex(self):
        T = TypeVar('T')
        TS = TypeVar('TS')

        self.assertEqual(repr(typing.Mapping[T, TS][TS, T]), 'typing.Mapping[~TS, ~T]')
        self.assertEqual(repr(List[Tuple[T, TS]][int, T]),
                         'typing.List[typing.Tuple[int, ~T]]')
        self.assertEqual(
            repr(List[Tuple[T, T]][List[int]]),
            'typing.List[typing.Tuple[typing.List[int], typing.List[int]]]'
        )

    def test_new_repr_bare(self):
        T = TypeVar('T')
        self.assertEqual(repr(Generic[T]), 'typing.Generic[~T]')
        self.assertEqual(repr(typing.Protocol[T]), 'typing.Protocol[~T]')
        klasse C(typing.Dict[Any, Any]): ...
        # this line should just work
        repr(C.__mro__)

    def test_dict(self):
        T = TypeVar('T')

        klasse B(Generic[T]):
            pass

        b = B()
        b.foo = 42
        self.assertEqual(b.__dict__, {'foo': 42})

        klasse C(B[int]):
            pass

        c = C()
        c.bar = 'abc'
        self.assertEqual(c.__dict__, {'bar': 'abc'})

    def test_setattr_exceptions(self):
        klasse Immutable[T]:
            def __setattr__(self, key, value):
                wirf RuntimeError("immutable")

        # gh-115165: This used to cause RuntimeError to be raised
        # when we tried to set `__orig_class__` on the `Immutable` instance
        # returned by the `Immutable[int]()` call
        self.assertIsInstance(Immutable[int](), Immutable)

    def test_subscripted_generics_as_proxies(self):
        T = TypeVar('T')
        klasse C(Generic[T]):
            x = 'def'
        self.assertEqual(C[int].x, 'def')
        self.assertEqual(C[C[int]].x, 'def')
        C[C[int]].x = 'changed'
        self.assertEqual(C.x, 'changed')
        self.assertEqual(C[str].x, 'changed')
        C[List[str]].z = 'new'
        self.assertEqual(C.z, 'new')
        self.assertEqual(C[Tuple[int]].z, 'new')

        self.assertEqual(C().x, 'changed')
        self.assertEqual(C[Tuple[str]]().z, 'new')

        klasse D(C[T]):
            pass
        self.assertEqual(D[int].x, 'changed')
        self.assertEqual(D.z, 'new')
        D.z = 'from derived z'
        D[int].x = 'from derived x'
        self.assertEqual(C.x, 'changed')
        self.assertEqual(C[int].z, 'new')
        self.assertEqual(D.x, 'from derived x')
        self.assertEqual(D[str].z, 'from derived z')

    def test_abc_registry_kept(self):
        T = TypeVar('T')
        klasse C(collections.abc.Mapping, Generic[T]): ...
        C.register(int)
        self.assertIsInstance(1, C)
        C[int]
        self.assertIsInstance(1, C)
        C._abc_registry_clear()
        C._abc_caches_clear()  # To keep refleak hunting mode clean

    def test_false_subclasses(self):
        klasse MyMapping(MutableMapping[str, str]): pass
        self.assertNotIsInstance({}, MyMapping)
        self.assertNotIsSubclass(dict, MyMapping)

    def test_abc_bases(self):
        klasse MM(MutableMapping[str, str]):
            def __getitem__(self, k):
                gib Nichts
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                gib iter(())
            def __len__(self):
                gib 0
        # this should just work
        MM().update()
        self.assertIsInstance(MM(), collections.abc.MutableMapping)
        self.assertIsInstance(MM(), MutableMapping)
        self.assertNotIsInstance(MM(), List)
        self.assertNotIsInstance({}, MM)

    def test_multiple_bases(self):
        klasse MM1(MutableMapping[str, str], collections.abc.MutableMapping):
            pass
        klasse MM2(collections.abc.MutableMapping, MutableMapping[str, str]):
            pass
        self.assertEqual(MM2.__bases__, (collections.abc.MutableMapping, Generic))

    def test_orig_bases(self):
        T = TypeVar('T')
        klasse C(typing.Dict[str, T]): ...
        self.assertEqual(C.__orig_bases__, (typing.Dict[str, T],))

    def test_naive_runtime_checks(self):
        def naive_dict_check(obj, tp):
            # Check wenn a dictionary conforms to Dict type
            wenn len(tp.__parameters__) > 0:
                wirf NotImplementedError
            wenn tp.__args__:
                KT, VT = tp.__args__
                gib all(
                    isinstance(k, KT) und isinstance(v, VT)
                    fuer k, v in obj.items()
                )
        self.assertWahr(naive_dict_check({'x': 1}, typing.Dict[str, int]))
        self.assertFalsch(naive_dict_check({1: 'x'}, typing.Dict[str, int]))
        mit self.assertRaises(NotImplementedError):
            naive_dict_check({1: 'x'}, typing.Dict[str, T])

        def naive_generic_check(obj, tp):
            # Check wenn an instance conforms to the generic class
            wenn nicht hasattr(obj, '__orig_class__'):
                wirf NotImplementedError
            gib obj.__orig_class__ == tp
        klasse Node(Generic[T]): ...
        self.assertWahr(naive_generic_check(Node[int](), Node[int]))
        self.assertFalsch(naive_generic_check(Node[str](), Node[int]))
        self.assertFalsch(naive_generic_check(Node[str](), List))
        mit self.assertRaises(NotImplementedError):
            naive_generic_check([1, 2, 3], Node[int])

        def naive_list_base_check(obj, tp):
            # Check wenn list conforms to a List subclass
            gib all(isinstance(x, tp.__orig_bases__[0].__args__[0])
                       fuer x in obj)
        klasse C(List[int]): ...
        self.assertWahr(naive_list_base_check([1, 2, 3], C))
        self.assertFalsch(naive_list_base_check(['a', 'b'], C))

    def test_multi_subscr_base(self):
        T = TypeVar('T')
        U = TypeVar('U')
        V = TypeVar('V')
        klasse C(List[T][U][V]): ...
        klasse D(C, List[T][U][V]): ...
        self.assertEqual(C.__parameters__, (V,))
        self.assertEqual(D.__parameters__, (V,))
        self.assertEqual(C[int].__parameters__, ())
        self.assertEqual(D[int].__parameters__, ())
        self.assertEqual(C[int].__args__, (int,))
        self.assertEqual(D[int].__args__, (int,))
        self.assertEqual(C.__bases__, (list, Generic))
        self.assertEqual(D.__bases__, (C, list, Generic))
        self.assertEqual(C.__orig_bases__, (List[T][U][V],))
        self.assertEqual(D.__orig_bases__, (C, List[T][U][V]))

    def test_subscript_meta(self):
        T = TypeVar('T')
        klasse Meta(type): ...
        self.assertEqual(Type[Meta], Type[Meta])
        self.assertEqual(Union[T, int][Meta], Union[Meta, int])
        self.assertEqual(Callable[..., Meta].__args__, (Ellipsis, Meta))

    def test_generic_hashes(self):
        klasse A(Generic[T]):
            ...

        klasse B(Generic[T]):
            klasse A(Generic[T]):
                ...

        self.assertEqual(A, A)
        self.assertEqual(mod_generics_cache.A[str], mod_generics_cache.A[str])
        self.assertEqual(B.A, B.A)
        self.assertEqual(mod_generics_cache.B.A[B.A[str]],
                         mod_generics_cache.B.A[B.A[str]])

        self.assertNotEqual(A, B.A)
        self.assertNotEqual(A, mod_generics_cache.A)
        self.assertNotEqual(A, mod_generics_cache.B.A)
        self.assertNotEqual(B.A, mod_generics_cache.A)
        self.assertNotEqual(B.A, mod_generics_cache.B.A)

        self.assertNotEqual(A[str], B.A[str])
        self.assertNotEqual(A[List[Any]], B.A[List[Any]])
        self.assertNotEqual(A[str], mod_generics_cache.A[str])
        self.assertNotEqual(A[str], mod_generics_cache.B.A[str])
        self.assertNotEqual(B.A[int], mod_generics_cache.A[int])
        self.assertNotEqual(B.A[List[Any]], mod_generics_cache.B.A[List[Any]])

        self.assertNotEqual(Tuple[A[str]], Tuple[B.A[str]])
        self.assertNotEqual(Tuple[A[List[Any]]], Tuple[B.A[List[Any]]])
        self.assertNotEqual(Union[str, A[str]], Union[str, mod_generics_cache.A[str]])
        self.assertNotEqual(Union[A[str], A[str]],
                            Union[A[str], mod_generics_cache.A[str]])
        self.assertNotEqual(typing.FrozenSet[A[str]],
                            typing.FrozenSet[mod_generics_cache.B.A[str]])

        self.assertEndsWith(repr(Tuple[A[str]]), '<locals>.A[str]]')
        self.assertEndsWith(repr(Tuple[B.A[str]]), '<locals>.B.A[str]]')
        self.assertEndsWith(repr(Tuple[mod_generics_cache.A[str]]),
                            'mod_generics_cache.A[str]]')
        self.assertEndsWith(repr(Tuple[mod_generics_cache.B.A[str]]),
                            'mod_generics_cache.B.A[str]]')

    def test_extended_generic_rules_eq(self):
        T = TypeVar('T')
        U = TypeVar('U')
        self.assertEqual(Tuple[T, T][int], Tuple[int, int])
        self.assertEqual(typing.Iterable[Tuple[T, T]][T], typing.Iterable[Tuple[T, T]])
        mit self.assertRaises(TypeError):
            Tuple[T, int][()]

        self.assertEqual(Union[T, int][int], int)
        self.assertEqual(Union[T, U][int, Union[int, str]], Union[int, str])
        klasse Base: ...
        klasse Derived(Base): ...
        self.assertEqual(Union[T, Base][Union[Base, Derived]], Union[Base, Derived])
        self.assertEqual(Callable[[T], T][KT], Callable[[KT], KT])
        self.assertEqual(Callable[..., List[T]][int], Callable[..., List[int]])

    def test_extended_generic_rules_repr(self):
        T = TypeVar('T')
        self.assertEqual(repr(Union[Tuple, Callable]).replace('typing.', ''),
                         'Tuple | Callable')
        self.assertEqual(repr(Union[Tuple, Tuple[int]]).replace('typing.', ''),
                         'Tuple | Tuple[int]')
        self.assertEqual(repr(Callable[..., Optional[T]][int]).replace('typing.', ''),
                         'Callable[..., int | Nichts]')
        self.assertEqual(repr(Callable[[], List[T]][int]).replace('typing.', ''),
                         'Callable[[], List[int]]')

    def test_generic_forward_ref(self):
        def foobar(x: List[List['CC']]): ...
        def foobar2(x: list[list[ForwardRef('CC')]]): ...
        def foobar3(x: list[ForwardRef('CC | int')] | int): ...
        klasse CC: ...
        self.assertEqual(
            get_type_hints(foobar, globals(), locals()),
            {'x': List[List[CC]]}
        )
        self.assertEqual(
            get_type_hints(foobar2, globals(), locals()),
            {'x': list[list[CC]]}
        )
        self.assertEqual(
            get_type_hints(foobar3, globals(), locals()),
            {'x': list[CC | int] | int}
        )

        T = TypeVar('T')
        AT = Tuple[T, ...]
        def barfoo(x: AT): ...
        self.assertIs(get_type_hints(barfoo, globals(), locals())['x'], AT)
        CT = Callable[..., List[T]]
        def barfoo2(x: CT): ...
        self.assertIs(get_type_hints(barfoo2, globals(), locals())['x'], CT)

    def test_generic_pep585_forward_ref(self):
        # See https://bugs.python.org/issue41370

        klasse C1:
            a: list['C1']
        self.assertEqual(
            get_type_hints(C1, globals(), locals()),
            {'a': list[C1]}
        )

        klasse C2:
            a: dict['C1', list[List[list['C2']]]]
        self.assertEqual(
            get_type_hints(C2, globals(), locals()),
            {'a': dict[C1, list[List[list[C2]]]]}
        )

        # Test stringified annotations
        scope = {}
        exec(textwrap.dedent('''
        von __future__ importiere annotations
        klasse C3:
            a: List[list["C2"]]
        '''), scope)
        C3 = scope['C3']
        self.assertEqual(C3.__annotations__['a'], "List[list['C2']]")
        self.assertEqual(
            get_type_hints(C3, globals(), locals()),
            {'a': List[list[C2]]}
        )

        # Test recursive types
        X = list["X"]
        def f(x: X): ...
        self.assertEqual(
            get_type_hints(f, globals(), locals()),
            {'x': list[list[EqualToForwardRef('X')]]}
        )

    def test_pep695_generic_class_with_future_annotations(self):
        original_globals = dict(ann_module695.__dict__)

        hints_for_A = get_type_hints(ann_module695.A)
        A_type_params = ann_module695.A.__type_params__
        self.assertIs(hints_for_A["x"], A_type_params[0])
        self.assertEqual(hints_for_A["y"].__args__[0], Unpack[A_type_params[1]])
        self.assertIs(hints_for_A["z"].__args__[0], A_type_params[2])

        # should nicht have changed als a result of the get_type_hints() calls!
        self.assertEqual(ann_module695.__dict__, original_globals)

    def test_pep695_generic_class_with_future_annotations_and_local_shadowing(self):
        hints_for_B = get_type_hints(ann_module695.B)
        self.assertEqual(hints_for_B, {"x": int, "y": str, "z": bytes})

    def test_pep695_generic_class_with_future_annotations_name_clash_with_global_vars(self):
        hints_for_C = get_type_hints(ann_module695.C)
        self.assertEqual(
            set(hints_for_C.values()),
            set(ann_module695.C.__type_params__)
        )

    def test_pep_695_generic_function_with_future_annotations(self):
        hints_for_generic_function = get_type_hints(ann_module695.generic_function)
        func_t_params = ann_module695.generic_function.__type_params__
        self.assertEqual(
            hints_for_generic_function.keys(), {"x", "y", "z", "zz", "return"}
        )
        self.assertIs(hints_for_generic_function["x"], func_t_params[0])
        self.assertEqual(hints_for_generic_function["y"], Unpack[func_t_params[1]])
        self.assertIs(hints_for_generic_function["z"].__origin__, func_t_params[2])
        self.assertIs(hints_for_generic_function["zz"].__origin__, func_t_params[2])

    def test_pep_695_generic_function_with_future_annotations_name_clash_with_global_vars(self):
        self.assertEqual(
            set(get_type_hints(ann_module695.generic_function_2).values()),
            set(ann_module695.generic_function_2.__type_params__)
        )

    def test_pep_695_generic_method_with_future_annotations(self):
        hints_for_generic_method = get_type_hints(ann_module695.D.generic_method)
        params = {
            param.__name__: param
            fuer param in ann_module695.D.generic_method.__type_params__
        }
        self.assertEqual(
            hints_for_generic_method,
            {"x": params["Foo"], "y": params["Bar"], "return": types.NoneType}
        )

    def test_pep_695_generic_method_with_future_annotations_name_clash_with_global_vars(self):
        self.assertEqual(
            set(get_type_hints(ann_module695.D.generic_method_2).values()),
            set(ann_module695.D.generic_method_2.__type_params__)
        )

    def test_pep_695_generics_with_future_annotations_nested_in_function(self):
        results = ann_module695.nested()

        self.assertEqual(
            set(results.hints_for_E.values()),
            set(results.E.__type_params__)
        )
        self.assertEqual(
            set(results.hints_for_E_meth.values()),
            set(results.E.generic_method.__type_params__)
        )
        self.assertNotEqual(
            set(results.hints_for_E_meth.values()),
            set(results.E.__type_params__)
        )
        self.assertEqual(
            set(results.hints_for_E_meth.values()).intersection(results.E.__type_params__),
            set()
        )

        self.assertEqual(
            set(results.hints_for_generic_func.values()),
            set(results.generic_func.__type_params__)
        )

    def test_extended_generic_rules_subclassing(self):
        klasse T1(Tuple[T, KT]): ...
        klasse T2(Tuple[T, ...]): ...
        klasse C1(typing.Container[T]):
            def __contains__(self, item):
                gib Falsch

        self.assertEqual(T1.__parameters__, (T, KT))
        self.assertEqual(T1[int, str].__args__, (int, str))
        self.assertEqual(T1[int, T].__origin__, T1)

        self.assertEqual(T2.__parameters__, (T,))
        # These don't work because of tuple.__class_item__
        ## mit self.assertRaises(TypeError):
        ##     T1[int]
        ## mit self.assertRaises(TypeError):
        ##     T2[int, str]

        self.assertEqual(repr(C1[int]).split('.')[-1], 'C1[int]')
        self.assertEqual(C1.__parameters__, (T,))
        self.assertIsInstance(C1(), collections.abc.Container)
        self.assertIsSubclass(C1, collections.abc.Container)
        self.assertIsInstance(T1(), tuple)
        self.assertIsSubclass(T2, tuple)
        mit self.assertRaises(TypeError):
            issubclass(Tuple[int, ...], typing.Sequence)
        mit self.assertRaises(TypeError):
            issubclass(Tuple[int, ...], typing.Iterable)

    def test_fail_with_special_forms(self):
        mit self.assertRaises(TypeError):
            List[Final]
        mit self.assertRaises(TypeError):
            Tuple[Optional]
        mit self.assertRaises(TypeError):
            List[ClassVar[int]]

    def test_fail_with_bare_generic(self):
        T = TypeVar('T')
        mit self.assertRaises(TypeError):
            List[Generic]
        mit self.assertRaises(TypeError):
            Tuple[Generic[T]]
        mit self.assertRaises(TypeError):
            List[typing.Protocol]

    def test_type_erasure_special(self):
        T = TypeVar('T')
        # this ist the only test that checks type caching
        self.clear_caches()
        klasse MyTup(Tuple[T, T]): ...
        self.assertIs(MyTup[int]().__class__, MyTup)
        self.assertEqual(MyTup[int]().__orig_class__, MyTup[int])
        klasse MyDict(typing.Dict[T, T]): ...
        self.assertIs(MyDict[int]().__class__, MyDict)
        self.assertEqual(MyDict[int]().__orig_class__, MyDict[int])
        klasse MyDef(typing.DefaultDict[str, T]): ...
        self.assertIs(MyDef[int]().__class__, MyDef)
        self.assertEqual(MyDef[int]().__orig_class__, MyDef[int])
        klasse MyChain(typing.ChainMap[str, T]): ...
        self.assertIs(MyChain[int]().__class__, MyChain)
        self.assertEqual(MyChain[int]().__orig_class__, MyChain[int])

    def test_all_repr_eq_any(self):
        objs = (getattr(typing, el) fuer el in typing.__all__)
        fuer obj in objs:
            self.assertNotEqual(repr(obj), '')
            self.assertEqual(obj, obj)
            wenn (getattr(obj, '__parameters__', Nichts)
                    und nicht isinstance(obj, typing.TypeVar)
                    und isinstance(obj.__parameters__, tuple)
                    und len(obj.__parameters__) == 1):
                self.assertEqual(obj[Any].__args__, (Any,))
            wenn isinstance(obj, type):
                fuer base in obj.__mro__:
                    self.assertNotEqual(repr(base), '')
                    self.assertEqual(base, base)

    def test_pickle(self):
        global C  # pickle wants to reference the klasse by name
        T = TypeVar('T')

        klasse B(Generic[T]):
            pass

        klasse C(B[int]):
            pass

        c = C()
        c.foo = 42
        c.bar = 'abc'
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(c, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.__dict__, {'foo': 42, 'bar': 'abc'})
        samples = [Any, Union, Tuple, Callable, ClassVar,
                   Union[int, str], ClassVar[List], Tuple[int, ...], Tuple[()],
                   Callable[[str], bytes],
                   typing.DefaultDict, typing.FrozenSet[int]]
        fuer s in samples:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                z = pickle.dumps(s, proto)
                x = pickle.loads(z)
                self.assertEqual(s, x)
        more_samples = [List, typing.Iterable, typing.Type, List[int],
                        typing.Type[typing.Mapping], typing.AbstractSet[Tuple[int, str]]]
        fuer s in more_samples:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                z = pickle.dumps(s, proto)
                x = pickle.loads(z)
                self.assertEqual(s, x)

        # Test ParamSpec args und kwargs
        global PP
        PP = ParamSpec('PP')
        fuer thing in [PP.args, PP.kwargs]:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(thing=thing, proto=proto):
                    self.assertEqual(
                        pickle.loads(pickle.dumps(thing, proto)),
                        thing,
                    )
        loesche PP

    def test_copy_and_deepcopy(self):
        T = TypeVar('T')
        klasse Node(Generic[T]): ...
        things = [Union[T, int], Tuple[T, int], Tuple[()],
                  Callable[..., T], Callable[[int], int],
                  Tuple[Any, Any], Node[T], Node[int], Node[Any], typing.Iterable[T],
                  typing.Iterable[Any], typing.Iterable[int], typing.Dict[int, str],
                  typing.Dict[T, Any], ClassVar[int], ClassVar[List[T]], Tuple['T', 'T'],
                  Union['T', int], List['T'], typing.Mapping['T', int],
                  Union[b"x", b"y"], Any]
        fuer t in things:
            mit self.subTest(thing=t):
                self.assertEqual(t, copy(t))
                self.assertEqual(t, deepcopy(t))

    def test_immutability_by_copy_and_pickle(self):
        # Special forms like Union, Any, etc., generic aliases to containers like List,
        # Mapping, etc., und type variabcles are considered immutable by copy und pickle.
        global TP, TPB, TPV, PP  # fuer pickle
        TP = TypeVar('TP')
        TPB = TypeVar('TPB', bound=int)
        TPV = TypeVar('TPV', bytes, str)
        PP = ParamSpec('PP')
        fuer X in [TP, TPB, TPV, PP,
                  List, typing.Mapping, ClassVar, typing.Iterable,
                  Union, Any, Tuple, Callable]:
            mit self.subTest(thing=X):
                self.assertIs(copy(X), X)
                self.assertIs(deepcopy(X), X)
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    self.assertIs(pickle.loads(pickle.dumps(X, proto)), X)
        loesche TP, TPB, TPV, PP

        # Check that local type variables are copyable.
        TL = TypeVar('TL')
        TLB = TypeVar('TLB', bound=int)
        TLV = TypeVar('TLV', bytes, str)
        PL = ParamSpec('PL')
        fuer X in [TL, TLB, TLV, PL]:
            mit self.subTest(thing=X):
                self.assertIs(copy(X), X)
                self.assertIs(deepcopy(X), X)

    def test_copy_generic_instances(self):
        T = TypeVar('T')
        klasse C(Generic[T]):
            def __init__(self, attr: T) -> Nichts:
                self.attr = attr

        c = C(42)
        self.assertEqual(copy(c).attr, 42)
        self.assertEqual(deepcopy(c).attr, 42)
        self.assertIsNot(copy(c), c)
        self.assertIsNot(deepcopy(c), c)
        c.attr = 1
        self.assertEqual(copy(c).attr, 1)
        self.assertEqual(deepcopy(c).attr, 1)
        ci = C[int](42)
        self.assertEqual(copy(ci).attr, 42)
        self.assertEqual(deepcopy(ci).attr, 42)
        self.assertIsNot(copy(ci), ci)
        self.assertIsNot(deepcopy(ci), ci)
        ci.attr = 1
        self.assertEqual(copy(ci).attr, 1)
        self.assertEqual(deepcopy(ci).attr, 1)
        self.assertEqual(ci.__orig_class__, C[int])

    def test_weakref_all(self):
        T = TypeVar('T')
        things = [Any, Union[T, int], Callable[..., T], Tuple[Any, Any],
                  Optional[List[int]], typing.Mapping[int, str],
                  typing.Match[bytes], typing.Iterable['whatever']]
        fuer t in things:
            self.assertEqual(weakref.ref(t)(), t)

    def test_parameterized_slots(self):
        T = TypeVar('T')
        klasse C(Generic[T]):
            __slots__ = ('potato',)

        c = C()
        c_int = C[int]()

        c.potato = 0
        c_int.potato = 0
        mit self.assertRaises(AttributeError):
            c.tomato = 0
        mit self.assertRaises(AttributeError):
            c_int.tomato = 0

        def foo(x: C['C']): ...
        self.assertEqual(get_type_hints(foo, globals(), locals())['x'], C[C])
        self.assertEqual(copy(C[int]), deepcopy(C[int]))

    def test_parameterized_slots_dict(self):
        T = TypeVar('T')
        klasse D(Generic[T]):
            __slots__ = {'banana': 42}

        d = D()
        d_int = D[int]()

        d.banana = 'yes'
        d_int.banana = 'yes'
        mit self.assertRaises(AttributeError):
            d.foobar = 'no'
        mit self.assertRaises(AttributeError):
            d_int.foobar = 'no'

    def test_errors(self):
        mit self.assertRaises(TypeError):
            B = SimpleMapping[XK, Any]

            klasse C(Generic[B]):
                pass

    def test_repr_2(self):
        klasse C(Generic[T]):
            pass

        self.assertEqual(C.__module__, __name__)
        self.assertEqual(C.__qualname__,
                         'GenericTests.test_repr_2.<locals>.C')
        X = C[int]
        self.assertEqual(X.__module__, __name__)
        self.assertEqual(repr(X).split('.')[-1], 'C[int]')

        klasse Y(C[int]):
            pass

        self.assertEqual(Y.__module__, __name__)
        self.assertEqual(Y.__qualname__,
                         'GenericTests.test_repr_2.<locals>.Y')

    def test_repr_3(self):
        T = TypeVar('T')
        T1 = TypeVar('T1')
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        Ts = TypeVarTuple('Ts')

        klasse MyCallable(Generic[P, T]):
            pass

        klasse DoubleSpec(Generic[P, P2, T]):
            pass

        klasse TsP(Generic[*Ts, P]):
            pass

        object_to_expected_repr = {
            MyCallable[P, T]:                         "MyCallable[~P, ~T]",
            MyCallable[Concatenate[T1, P], T]:        "MyCallable[typing.Concatenate[~T1, ~P], ~T]",
            MyCallable[[], bool]:                     "MyCallable[[], bool]",
            MyCallable[[int], bool]:                  "MyCallable[[int], bool]",
            MyCallable[[int, str], bool]:             "MyCallable[[int, str], bool]",
            MyCallable[[int, list[int]], bool]:       "MyCallable[[int, list[int]], bool]",
            MyCallable[Concatenate[*Ts, P], T]:       "MyCallable[typing.Concatenate[typing.Unpack[Ts], ~P], ~T]",

            DoubleSpec[P2, P, T]:                     "DoubleSpec[~P2, ~P, ~T]",
            DoubleSpec[[int], [str], bool]:           "DoubleSpec[[int], [str], bool]",
            DoubleSpec[[int, int], [str, str], bool]: "DoubleSpec[[int, int], [str, str], bool]",

            TsP[*Ts, P]:                              "TsP[typing.Unpack[Ts], ~P]",
            TsP[int, str, list[int], []]:             "TsP[int, str, list[int], []]",
            TsP[int, [str, list[int]]]:               "TsP[int, [str, list[int]]]",

            # These lines are just too long to fit:
            MyCallable[Concatenate[*Ts, P], int][int, str, [bool, float]]:
                                                      "MyCallable[[int, str, bool, float], int]",
        }

        fuer obj, expected_repr in object_to_expected_repr.items():
            mit self.subTest(obj=obj, expected_repr=expected_repr):
                self.assertRegex(
                    repr(obj),
                    fr"^{re.escape(MyCallable.__module__)}.*\.{re.escape(expected_repr)}$",
                )

    def test_eq_1(self):
        self.assertEqual(Generic, Generic)
        self.assertEqual(Generic[T], Generic[T])
        self.assertNotEqual(Generic[KT], Generic[VT])

    def test_eq_2(self):

        klasse A(Generic[T]):
            pass

        klasse B(Generic[T]):
            pass

        self.assertEqual(A, A)
        self.assertNotEqual(A, B)
        self.assertEqual(A[T], A[T])
        self.assertNotEqual(A[T], B[T])

    def test_multiple_inheritance(self):

        klasse A(Generic[T, VT]):
            pass

        klasse B(Generic[KT, T]):
            pass

        klasse C(A[T, VT], Generic[VT, T, KT], B[KT, T]):
            pass

        self.assertEqual(C.__parameters__, (VT, T, KT))

    def test_multiple_inheritance_special(self):
        S = TypeVar('S')
        klasse B(Generic[S]): ...
        klasse C(List[int], B): ...
        self.assertEqual(C.__mro__, (C, list, B, Generic, object))

    def test_multiple_inheritance_non_type_with___mro_entries__(self):
        klasse GoodEntries:
            def __mro_entries__(self, bases):
                gib (object,)

        klasse A(List[int], GoodEntries()): ...

        self.assertEqual(A.__mro__, (A, list, Generic, object))

    def test_multiple_inheritance_non_type_without___mro_entries__(self):
        # Error should be von the type machinery, nicht von typing.py
        mit self.assertRaisesRegex(TypeError, r"^bases must be types"):
            klasse A(List[int], object()): ...

    def test_multiple_inheritance_non_type_bad___mro_entries__(self):
        klasse BadEntries:
            def __mro_entries__(self, bases):
                gib Nichts

        # Error should be von the type machinery, nicht von typing.py
        mit self.assertRaisesRegex(
            TypeError,
            r"^__mro_entries__ must gib a tuple",
        ):
            klasse A(List[int], BadEntries()): ...

    def test_multiple_inheritance___mro_entries___returns_non_type(self):
        klasse BadEntries:
            def __mro_entries__(self, bases):
                gib (object(),)

        # Error should be von the type machinery, nicht von typing.py
        mit self.assertRaisesRegex(
            TypeError,
            r"^bases must be types",
        ):
            klasse A(List[int], BadEntries()): ...

    def test_multiple_inheritance_with_genericalias(self):
        klasse A(typing.Sized, list[int]): ...

        self.assertEqual(
            A.__mro__,
            (A, collections.abc.Sized, Generic, list, object),
        )

    def test_multiple_inheritance_with_genericalias_2(self):
        T = TypeVar("T")

        klasse BaseSeq(typing.Sequence[T]): ...
        klasse MySeq(List[T], BaseSeq[T]): ...

        self.assertEqual(
            MySeq.__mro__,
            (
                MySeq,
                list,
                BaseSeq,
                collections.abc.Sequence,
                collections.abc.Reversible,
                collections.abc.Collection,
                collections.abc.Sized,
                collections.abc.Iterable,
                collections.abc.Container,
                Generic,
                object,
            ),
        )

    def test_init_subclass_super_called(self):
        klasse FinalException(Exception):
            pass

        klasse Final:
            def __init_subclass__(cls, **kwargs) -> Nichts:
                fuer base in cls.__bases__:
                    wenn base ist nicht Final und issubclass(base, Final):
                        wirf FinalException(base)
                super().__init_subclass__(**kwargs)
        klasse Test(Generic[T], Final):
            pass
        mit self.assertRaises(FinalException):
            klasse Subclass(Test):
                pass
        mit self.assertRaises(FinalException):
            klasse Subclass2(Test[int]):
                pass

    def test_nested(self):

        G = Generic

        klasse Visitor(G[T]):

            a = Nichts

            def set(self, a: T):
                self.a = a

            def get(self):
                gib self.a

            def visit(self) -> T:
                gib self.a

        V = Visitor[typing.List[int]]

        klasse IntListVisitor(V):

            def append(self, x: int):
                self.a.append(x)

        a = IntListVisitor()
        a.set([])
        a.append(1)
        a.append(42)
        self.assertEqual(a.get(), [1, 42])

    def test_type_erasure(self):
        T = TypeVar('T')

        klasse Node(Generic[T]):
            def __init__(self, label: T,
                         left: 'Node[T]' = Nichts,
                         right: 'Node[T]' = Nichts):
                self.label = label  # type: T
                self.left = left  # type: Optional[Node[T]]
                self.right = right  # type: Optional[Node[T]]

        def foo(x: T):
            a = Node(x)
            b = Node[T](x)
            c = Node[Any](x)
            self.assertIs(type(a), Node)
            self.assertIs(type(b), Node)
            self.assertIs(type(c), Node)
            self.assertEqual(a.label, x)
            self.assertEqual(b.label, x)
            self.assertEqual(c.label, x)

        foo(42)

    def test_implicit_any(self):
        T = TypeVar('T')

        klasse C(Generic[T]):
            pass

        klasse D(C):
            pass

        self.assertEqual(D.__parameters__, ())

        mit self.assertRaises(TypeError):
            D[int]
        mit self.assertRaises(TypeError):
            D[Any]
        mit self.assertRaises(TypeError):
            D[T]

    def test_new_with_args(self):

        klasse A(Generic[T]):
            pass

        klasse B:
            def __new__(cls, arg):
                # call object
                obj = super().__new__(cls)
                obj.arg = arg
                gib obj

        # mro: C, A, Generic, B, object
        klasse C(A, B):
            pass

        c = C('foo')
        self.assertEqual(c.arg, 'foo')

    def test_new_with_args2(self):

        klasse A:
            def __init__(self, arg):
                self.from_a = arg
                # call object
                super().__init__()

        # mro: C, Generic, A, object
        klasse C(Generic[T], A):
            def __init__(self, arg):
                self.from_c = arg
                # call Generic
                super().__init__(arg)

        c = C('foo')
        self.assertEqual(c.from_a, 'foo')
        self.assertEqual(c.from_c, 'foo')

    def test_new_no_args(self):

        klasse A(Generic[T]):
            pass

        mit self.assertRaises(TypeError):
            A('foo')

        klasse B:
            def __new__(cls):
                # call object
                obj = super().__new__(cls)
                obj.from_b = 'b'
                gib obj

        # mro: C, A, Generic, B, object
        klasse C(A, B):
            def __init__(self, arg):
                self.arg = arg

            def __new__(cls, arg):
                # call A
                obj = super().__new__(cls)
                obj.from_c = 'c'
                gib obj

        c = C('foo')
        self.assertEqual(c.arg, 'foo')
        self.assertEqual(c.from_b, 'b')
        self.assertEqual(c.from_c, 'c')

    def test_subclass_special_form(self):
        fuer obj in (
            ClassVar[int],
            Final[int],
            Literal[1, 2],
            Concatenate[int, ParamSpec("P")],
            TypeGuard[int],
            TypeIs[range],
        ):
            mit self.subTest(msg=obj):
                mit self.assertRaisesRegex(
                        TypeError, f'^{re.escape(f"Cannot subclass {obj!r}")}$'
                ):
                    klasse Foo(obj):
                        pass

    def test_complex_subclasses(self):
        T_co = TypeVar("T_co", covariant=Wahr)

        klasse Base(Generic[T_co]):
            ...

        T = TypeVar("T")

        # see gh-94607: this fails in that bug
        klasse Sub(Base, Generic[T]):
            ...

    def test_parameter_detection(self):
        self.assertEqual(List[T].__parameters__, (T,))
        self.assertEqual(List[List[T]].__parameters__, (T,))
        klasse A:
            __parameters__ = (T,)
        # Bare classes should be skipped
        fuer a in (List, list):
            fuer b in (A, int, TypeVar, TypeVarTuple, ParamSpec, types.GenericAlias, Union):
                mit self.subTest(generic=a, sub=b):
                    mit self.assertRaisesRegex(TypeError, '.* ist nicht a generic class'):
                        a[b][str]
        # Duck-typing anything that looks like it has __parameters__.
        # These tests are optional und failure ist okay.
        self.assertEqual(List[A()].__parameters__, (T,))
        # C version of GenericAlias
        self.assertEqual(list[A()].__parameters__, (T,))

    def test_non_generic_subscript(self):
        T = TypeVar('T')
        klasse G(Generic[T]):
            pass
        klasse A:
            __parameters__ = (T,)

        fuer s in (int, G, A, List, list,
                  TypeVar, TypeVarTuple, ParamSpec,
                  types.GenericAlias, Union):

            fuer t in Tuple, tuple:
                mit self.subTest(tuple=t, sub=s):
                    self.assertEqual(t[s, T][int], t[s, int])
                    self.assertEqual(t[T, s][int], t[int, s])
                    a = t[s]
                    mit self.assertRaises(TypeError):
                        a[int]

            fuer c in Callable, collections.abc.Callable:
                mit self.subTest(callable=c, sub=s):
                    self.assertEqual(c[[s], T][int], c[[s], int])
                    self.assertEqual(c[[T], s][int], c[[int], s])
                    a = c[[s], s]
                    mit self.assertRaises(TypeError):
                        a[int]


klasse ClassVarTests(BaseTestCase):

    def test_basics(self):
        mit self.assertRaises(TypeError):
            ClassVar[int, str]
        mit self.assertRaises(TypeError):
            ClassVar[int][str]

    def test_repr(self):
        self.assertEqual(repr(ClassVar), 'typing.ClassVar')
        cv = ClassVar[int]
        self.assertEqual(repr(cv), 'typing.ClassVar[int]')
        cv = ClassVar[Employee]
        self.assertEqual(repr(cv), 'typing.ClassVar[%s.Employee]' % __name__)

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(ClassVar)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(ClassVar[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.ClassVar'):
            klasse E(ClassVar):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.ClassVar\[int\]'):
            klasse F(ClassVar[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            ClassVar()
        mit self.assertRaises(TypeError):
            type(ClassVar)()
        mit self.assertRaises(TypeError):
            type(ClassVar[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, ClassVar[int])
        mit self.assertRaises(TypeError):
            issubclass(int, ClassVar)


klasse FinalTests(BaseTestCase):

    def test_basics(self):
        Final[int]  # OK
        mit self.assertRaises(TypeError):
            Final[int, str]
        mit self.assertRaises(TypeError):
            Final[int][str]
        mit self.assertRaises(TypeError):
            Optional[Final[int]]

    def test_repr(self):
        self.assertEqual(repr(Final), 'typing.Final')
        cv = Final[int]
        self.assertEqual(repr(cv), 'typing.Final[int]')
        cv = Final[Employee]
        self.assertEqual(repr(cv), 'typing.Final[%s.Employee]' % __name__)
        cv = Final[tuple[int]]
        self.assertEqual(repr(cv), 'typing.Final[tuple[int]]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(Final)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(Final[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.Final'):
            klasse E(Final):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.Final\[int\]'):
            klasse F(Final[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            Final()
        mit self.assertRaises(TypeError):
            type(Final)()
        mit self.assertRaises(TypeError):
            type(Final[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, Final[int])
        mit self.assertRaises(TypeError):
            issubclass(int, Final)


klasse FinalDecoratorTests(BaseTestCase):
    def test_final_unmodified(self):
        def func(x): ...
        self.assertIs(func, final(func))

    def test_dunder_final(self):
        @final
        def func(): ...
        @final
        klasse Cls: ...
        self.assertIs(Wahr, func.__final__)
        self.assertIs(Wahr, Cls.__final__)

        klasse Wrapper:
            __slots__ = ("func",)
            def __init__(self, func):
                self.func = func
            def __call__(self, *args, **kwargs):
                gib self.func(*args, **kwargs)

        # Check that no error ist thrown wenn the attribute
        # ist nicht writable.
        @final
        @Wrapper
        def wrapped(): ...
        self.assertIsInstance(wrapped, Wrapper)
        self.assertNotHasAttr(wrapped, "__final__")

        klasse Meta(type):
            @property
            def __final__(self): gib "can't set me"
        @final
        klasse WithMeta(metaclass=Meta): ...
        self.assertEqual(WithMeta.__final__, "can't set me")

        # Builtin classes throw TypeError wenn you try to set an
        # attribute.
        final(int)
        self.assertNotHasAttr(int, "__final__")

        # Make sure it works mit common builtin decorators
        klasse Methods:
            @final
            @classmethod
            def clsmethod(cls): ...

            @final
            @staticmethod
            def stmethod(): ...

            # The other order doesn't work because property objects
            # don't allow attribute assignment.
            @property
            @final
            def prop(self): ...

            @final
            @lru_cache()
            def cached(self): ...

        # Use getattr_static because the descriptor returns the
        # underlying function, which doesn't have __final__.
        self.assertIs(
            Wahr,
            inspect.getattr_static(Methods, "clsmethod").__final__
        )
        self.assertIs(
            Wahr,
            inspect.getattr_static(Methods, "stmethod").__final__
        )
        self.assertIs(Wahr, Methods.prop.fget.__final__)
        self.assertIs(Wahr, Methods.cached.__final__)


klasse OverrideDecoratorTests(BaseTestCase):
    def test_override(self):
        klasse Base:
            def normal_method(self): ...
            @classmethod
            def class_method_good_order(cls): ...
            @classmethod
            def class_method_bad_order(cls): ...
            @staticmethod
            def static_method_good_order(): ...
            @staticmethod
            def static_method_bad_order(): ...

        klasse Derived(Base):
            @override
            def normal_method(self):
                gib 42

            @classmethod
            @override
            def class_method_good_order(cls):
                gib 42
            @override
            @classmethod
            def class_method_bad_order(cls):
                gib 42

            @staticmethod
            @override
            def static_method_good_order():
                gib 42
            @override
            @staticmethod
            def static_method_bad_order():
                gib 42

        self.assertIsSubclass(Derived, Base)
        instance = Derived()
        self.assertEqual(instance.normal_method(), 42)
        self.assertIs(Wahr, Derived.normal_method.__override__)
        self.assertIs(Wahr, instance.normal_method.__override__)

        self.assertEqual(Derived.class_method_good_order(), 42)
        self.assertIs(Wahr, Derived.class_method_good_order.__override__)
        self.assertEqual(Derived.class_method_bad_order(), 42)
        self.assertNotHasAttr(Derived.class_method_bad_order, "__override__")

        self.assertEqual(Derived.static_method_good_order(), 42)
        self.assertIs(Wahr, Derived.static_method_good_order.__override__)
        self.assertEqual(Derived.static_method_bad_order(), 42)
        self.assertNotHasAttr(Derived.static_method_bad_order, "__override__")

        # Base object ist nicht changed:
        self.assertNotHasAttr(Base.normal_method, "__override__")
        self.assertNotHasAttr(Base.class_method_good_order, "__override__")
        self.assertNotHasAttr(Base.class_method_bad_order, "__override__")
        self.assertNotHasAttr(Base.static_method_good_order, "__override__")
        self.assertNotHasAttr(Base.static_method_bad_order, "__override__")

    def test_property(self):
        klasse Base:
            @property
            def correct(self) -> int:
                gib 1
            @property
            def wrong(self) -> int:
                gib 1

        klasse Child(Base):
            @property
            @override
            def correct(self) -> int:
                gib 2
            @override
            @property
            def wrong(self) -> int:
                gib 2

        instance = Child()
        self.assertEqual(instance.correct, 2)
        self.assertIs(Child.correct.fget.__override__, Wahr)
        self.assertEqual(instance.wrong, 2)
        self.assertNotHasAttr(Child.wrong, "__override__")
        self.assertNotHasAttr(Child.wrong.fset, "__override__")

    def test_silent_failure(self):
        klasse CustomProp:
            __slots__ = ('fget',)
            def __init__(self, fget):
                self.fget = fget
            def __get__(self, obj, objtype=Nichts):
                gib self.fget(obj)

        klasse WithOverride:
            @override  # must nicht fail on object mit `__slots__`
            @CustomProp
            def some(self):
                gib 1

        self.assertEqual(WithOverride.some, 1)
        self.assertNotHasAttr(WithOverride.some, "__override__")

    def test_multiple_decorators(self):
        def with_wraps(f):  # similar to `lru_cache` definition
            @wraps(f)
            def wrapper(*args, **kwargs):
                gib f(*args, **kwargs)
            gib wrapper

        klasse WithOverride:
            @override
            @with_wraps
            def on_top(self, a: int) -> int:
                gib a + 1
            @with_wraps
            @override
            def on_bottom(self, a: int) -> int:
                gib a + 2

        instance = WithOverride()
        self.assertEqual(instance.on_top(1), 2)
        self.assertIs(instance.on_top.__override__, Wahr)
        self.assertEqual(instance.on_bottom(1), 3)
        self.assertIs(instance.on_bottom.__override__, Wahr)


klasse CastTests(BaseTestCase):

    def test_basics(self):
        self.assertEqual(cast(int, 42), 42)
        self.assertEqual(cast(float, 42), 42)
        self.assertIs(type(cast(float, 42)), int)
        self.assertEqual(cast(Any, 42), 42)
        self.assertEqual(cast(list, 42), 42)
        self.assertEqual(cast(Union[str, float], 42), 42)
        self.assertEqual(cast(AnyStr, 42), 42)
        self.assertEqual(cast(Nichts, 42), 42)

    def test_errors(self):
        # Bogus calls are nicht expected to fail.
        cast(42, 42)
        cast('hello', 42)


klasse AssertTypeTests(BaseTestCase):

    def test_basics(self):
        arg = 42
        self.assertIs(assert_type(arg, int), arg)
        self.assertIs(assert_type(arg, str | float), arg)
        self.assertIs(assert_type(arg, AnyStr), arg)
        self.assertIs(assert_type(arg, Nichts), arg)

    def test_errors(self):
        # Bogus calls are nicht expected to fail.
        arg = 42
        self.assertIs(assert_type(arg, 42), arg)
        self.assertIs(assert_type(arg, 'hello'), arg)


# We need this to make sure that `@no_type_check` respects `__module__` attr:
@no_type_check
klasse NoTypeCheck_Outer:
    Inner = ann_module8.NoTypeCheck_Outer.Inner

@no_type_check
klasse NoTypeCheck_WithFunction:
    NoTypeCheck_function = ann_module8.NoTypeCheck_function


klasse NoTypeCheckTests(BaseTestCase):
    def test_no_type_check(self):

        @no_type_check
        def foo(a: 'whatevers') -> {}:
            pass

        th = get_type_hints(foo)
        self.assertEqual(th, {})

    def test_no_type_check_class(self):

        @no_type_check
        klasse C:
            def foo(a: 'whatevers') -> {}:
                pass

        cth = get_type_hints(C.foo)
        self.assertEqual(cth, {})
        ith = get_type_hints(C().foo)
        self.assertEqual(ith, {})

    def test_no_type_check_no_bases(self):
        klasse C:
            def meth(self, x: int): ...
        @no_type_check
        klasse D(C):
            c = C

        # verify that @no_type_check never affects bases
        self.assertEqual(get_type_hints(C.meth), {'x': int})

        # und never child classes:
        klasse Child(D):
            def foo(self, x: int): ...

        self.assertEqual(get_type_hints(Child.foo), {'x': int})

    def test_no_type_check_nested_types(self):
        # See https://bugs.python.org/issue46571
        klasse Other:
            o: int
        klasse B:  # Has the same `__name__`` als `A.B` und different `__qualname__`
            o: int
        @no_type_check
        klasse A:
            a: int
            klasse B:
                b: int
                klasse C:
                    c: int
            klasse D:
                d: int

            Other = Other

        fuer klass in [A, A.B, A.B.C, A.D]:
            mit self.subTest(klass=klass):
                self.assertIs(klass.__no_type_check__, Wahr)
                self.assertEqual(get_type_hints(klass), {})

        fuer not_modified in [Other, B]:
            mit self.subTest(not_modified=not_modified):
                mit self.assertRaises(AttributeError):
                    not_modified.__no_type_check__
                self.assertNotEqual(get_type_hints(not_modified), {})

    def test_no_type_check_class_and_static_methods(self):
        @no_type_check
        klasse Some:
            @staticmethod
            def st(x: int) -> int: ...
            @classmethod
            def cl(cls, y: int) -> int: ...

        self.assertIs(Some.st.__no_type_check__, Wahr)
        self.assertEqual(get_type_hints(Some.st), {})
        self.assertIs(Some.cl.__no_type_check__, Wahr)
        self.assertEqual(get_type_hints(Some.cl), {})

    def test_no_type_check_other_module(self):
        self.assertIs(NoTypeCheck_Outer.__no_type_check__, Wahr)
        mit self.assertRaises(AttributeError):
            ann_module8.NoTypeCheck_Outer.__no_type_check__
        mit self.assertRaises(AttributeError):
            ann_module8.NoTypeCheck_Outer.Inner.__no_type_check__

        self.assertIs(NoTypeCheck_WithFunction.__no_type_check__, Wahr)
        mit self.assertRaises(AttributeError):
            ann_module8.NoTypeCheck_function.__no_type_check__

    def test_no_type_check_foreign_functions(self):
        # We should nicht modify this function:
        def some(*args: int) -> int:
            ...

        @no_type_check
        klasse A:
            some_alias = some
            some_class = classmethod(some)
            some_static = staticmethod(some)

        mit self.assertRaises(AttributeError):
            some.__no_type_check__
        self.assertEqual(get_type_hints(some), {'args': int, 'return': int})

    def test_no_type_check_lambda(self):
        @no_type_check
        klasse A:
            # Corner case: `lambda` ist both an assignment und a function:
            bar: Callable[[int], int] = lambda arg: arg

        self.assertIs(A.bar.__no_type_check__, Wahr)
        self.assertEqual(get_type_hints(A.bar), {})

    def test_no_type_check_TypeError(self):
        # This simply should nicht fail with
        # `TypeError: can't set attributes of built-in/extension type 'dict'`
        no_type_check(dict)

    def test_no_type_check_forward_ref_as_string(self):
        klasse C:
            foo: typing.ClassVar[int] = 7
        klasse D:
            foo: ClassVar[int] = 7
        klasse E:
            foo: 'typing.ClassVar[int]' = 7
        klasse F:
            foo: 'ClassVar[int]' = 7

        expected_result = {'foo': typing.ClassVar[int]}
        fuer clazz in [C, D, E, F]:
            self.assertEqual(get_type_hints(clazz), expected_result)

    def test_meta_no_type_check(self):
        depr_msg = (
            "'typing.no_type_check_decorator' ist deprecated "
            "and slated fuer removal in Python 3.15"
        )
        mit self.assertWarnsRegex(DeprecationWarning, depr_msg):
            @no_type_check_decorator
            def magic_decorator(func):
                gib func

        self.assertEqual(magic_decorator.__name__, 'magic_decorator')

        @magic_decorator
        def foo(a: 'whatevers') -> {}:
            pass

        @magic_decorator
        klasse C:
            def foo(a: 'whatevers') -> {}:
                pass

        self.assertEqual(foo.__name__, 'foo')
        th = get_type_hints(foo)
        self.assertEqual(th, {})
        cth = get_type_hints(C.foo)
        self.assertEqual(cth, {})
        ith = get_type_hints(C().foo)
        self.assertEqual(ith, {})


klasse InternalsTests(BaseTestCase):
    def test_collect_parameters(self):
        typing = import_helper.import_fresh_module("typing")
        mit self.assertWarnsRegex(
            DeprecationWarning,
            "The private _collect_parameters function ist deprecated"
        ) als cm:
            typing._collect_parameters
        self.assertEqual(cm.filename, __file__)

    @cpython_only
    def test_lazy_import(self):
        import_helper.ensure_lazy_imports("typing", {
            "warnings",
            "inspect",
            "re",
            "contextlib",
            "annotationlib",
        })


@lru_cache()
def cached_func(x, y):
    gib 3 * x + y


klasse MethodHolder:
    @classmethod
    def clsmethod(cls): ...
    @staticmethod
    def stmethod(): ...
    def method(self): ...


klasse OverloadTests(BaseTestCase):

    def test_overload_fails(self):
        mit self.assertRaises(NotImplementedError):

            @overload
            def blah():
                pass

            blah()

    def test_overload_succeeds(self):
        @overload
        def blah():
            pass

        def blah():
            pass

        blah()

    @cpython_only  # gh-98713
    def test_overload_on_compiled_functions(self):
        mit patch("typing._overload_registry",
                   defaultdict(lambda: defaultdict(dict))):
            # The registry starts out empty:
            self.assertEqual(typing._overload_registry, {})

            # This should just nicht fail:
            overload(sum)
            overload(print)

            # No overloads are recorded (but, it still has a side-effect):
            self.assertEqual(typing.get_overloads(sum), [])
            self.assertEqual(typing.get_overloads(print), [])

    def set_up_overloads(self):
        def blah():
            pass

        overload1 = blah
        overload(blah)

        def blah():
            pass

        overload2 = blah
        overload(blah)

        def blah():
            pass

        gib blah, [overload1, overload2]

    # Make sure we don't clear the global overload registry
    @patch("typing._overload_registry",
        defaultdict(lambda: defaultdict(dict)))
    def test_overload_registry(self):
        # The registry starts out empty
        self.assertEqual(typing._overload_registry, {})

        impl, overloads = self.set_up_overloads()
        self.assertNotEqual(typing._overload_registry, {})
        self.assertEqual(list(get_overloads(impl)), overloads)

        def some_other_func(): pass
        overload(some_other_func)
        other_overload = some_other_func
        def some_other_func(): pass
        self.assertEqual(list(get_overloads(some_other_func)), [other_overload])
        # Unrelated function still has no overloads:
        def not_overloaded(): pass
        self.assertEqual(list(get_overloads(not_overloaded)), [])

        # Make sure that after we clear all overloads, the registry is
        # completely empty.
        clear_overloads()
        self.assertEqual(typing._overload_registry, {})
        self.assertEqual(get_overloads(impl), [])

        # Querying a function mit no overloads shouldn't change the registry.
        def the_only_one(): pass
        self.assertEqual(get_overloads(the_only_one), [])
        self.assertEqual(typing._overload_registry, {})

    def test_overload_registry_repeated(self):
        fuer _ in range(2):
            impl, overloads = self.set_up_overloads()

            self.assertEqual(list(get_overloads(impl)), overloads)


T_a = TypeVar('T_a')

klasse AwaitableWrapper(typing.Awaitable[T_a]):

    def __init__(self, value):
        self.value = value

    def __await__(self) -> typing.Iterator[T_a]:
        liefere
        gib self.value

klasse AsyncIteratorWrapper(typing.AsyncIterator[T_a]):

    def __init__(self, value: typing.Iterable[T_a]):
        self.value = value

    def __aiter__(self) -> typing.AsyncIterator[T_a]:
        gib self

    async def __anext__(self) -> T_a:
        data = warte self.value
        wenn data:
            gib data
        sonst:
            wirf StopAsyncIteration

klasse ACM:
    async def __aenter__(self) -> int:
        gib 42
    async def __aexit__(self, etype, eval, tb):
        gib Nichts

klasse A:
    y: float
klasse B(A):
    x: ClassVar[Optional['B']] = Nichts
    y: int
    b: int
klasse CSub(B):
    z: ClassVar['CSub'] = B()
klasse G(Generic[T]):
    lst: ClassVar[List[T]] = []

klasse Loop:
    attr: Final['Loop']

klasse NichtsAndForward:
    parent: 'NichtsAndForward'
    meaning: Nichts

klasse CoolEmployee(NamedTuple):
    name: str
    cool: int

klasse CoolEmployeeWithDefault(NamedTuple):
    name: str
    cool: int = 0

klasse XMeth(NamedTuple):
    x: int
    def double(self):
        gib 2 * self.x

klasse XRepr(NamedTuple):
    x: int
    y: int = 1
    def __str__(self):
        gib f'{self.x} -> {self.y}'
    def __add__(self, other):
        gib 0

Label = TypedDict('Label', [('label', str)])

klasse Point2D(TypedDict):
    x: int
    y: int

klasse Point2DGeneric(Generic[T], TypedDict):
    a: T
    b: T

klasse Bar(_typed_dict_helper.Foo, total=Falsch):
    b: int

klasse BarGeneric(_typed_dict_helper.FooGeneric[T], total=Falsch):
    b: int

klasse LabelPoint2D(Point2D, Label): ...

klasse Options(TypedDict, total=Falsch):
    log_level: int
    log_path: str

klasse TotalMovie(TypedDict):
    title: str
    year: NotRequired[int]

klasse NontotalMovie(TypedDict, total=Falsch):
    title: Required[str]
    year: int

klasse ParentNontotalMovie(TypedDict, total=Falsch):
    title: Required[str]

klasse ChildTotalMovie(ParentNontotalMovie):
    year: NotRequired[int]

klasse ParentDeeplyAnnotatedMovie(TypedDict):
    title: Annotated[Annotated[Required[str], "foobar"], "another level"]

klasse ChildDeeplyAnnotatedMovie(ParentDeeplyAnnotatedMovie):
    year: NotRequired[Annotated[int, 2000]]

klasse AnnotatedMovie(TypedDict):
    title: Annotated[Required[str], "foobar"]
    year: NotRequired[Annotated[int, 2000]]

klasse DeeplyAnnotatedMovie(TypedDict):
    title: Annotated[Annotated[Required[str], "foobar"], "another level"]
    year: NotRequired[Annotated[int, 2000]]

klasse WeirdlyQuotedMovie(TypedDict):
    title: Annotated['Annotated[Required[str], "foobar"]', "another level"]
    year: NotRequired['Annotated[int, 2000]']

klasse HasForeignBaseClass(mod_generics_cache.A):
    some_xrepr: 'XRepr'
    other_a: 'mod_generics_cache.A'

async def g_with(am: typing.AsyncContextManager[int]):
    x: int
    async mit am als x:
        gib x

versuch:
    g_with(ACM()).send(Nichts)
ausser StopIteration als e:
    assert e.args[0] == 42

gth = get_type_hints

klasse ForRefExample:
    @ann_module.dec
    def func(self: 'ForRefExample'):
        pass

    @ann_module.dec
    @ann_module.dec
    def nested(self: 'ForRefExample'):
        pass


klasse GetTypeHintsTests(BaseTestCase):
    def test_get_type_hints_from_various_objects(self):
        # For invalid objects should fail mit TypeError (nicht AttributeError etc).
        mit self.assertRaises(TypeError):
            gth(123)
        mit self.assertRaises(TypeError):
            gth('abc')
        mit self.assertRaises(TypeError):
            gth(Nichts)

    def test_get_type_hints_modules(self):
        ann_module_type_hints = {'f': Tuple[int, int], 'x': int, 'y': str, 'u': int | float}
        self.assertEqual(gth(ann_module), ann_module_type_hints)
        self.assertEqual(gth(ann_module2), {})
        self.assertEqual(gth(ann_module3), {})

    @skip("known bug")
    def test_get_type_hints_modules_forwardref(self):
        # FIXME: This currently exposes a bug in typing. Cached forward references
        # don't account fuer the case where there are multiple types of the same
        # name coming von different modules in the same program.
        mgc_hints = {'default_a': Optional[mod_generics_cache.A],
                     'default_b': Optional[mod_generics_cache.B]}
        self.assertEqual(gth(mod_generics_cache), mgc_hints)

    def test_get_type_hints_classes(self):
        self.assertEqual(gth(ann_module.C),  # gth will find the right globalns
                         {'y': Optional[ann_module.C]})
        self.assertIsInstance(gth(ann_module.j_class), dict)
        self.assertEqual(gth(ann_module.M), {'o': type})
        self.assertEqual(gth(ann_module.D),
                         {'j': str, 'k': str, 'y': Optional[ann_module.C]})
        self.assertEqual(gth(ann_module.Y), {'z': int})
        self.assertEqual(gth(ann_module.h_class),
                         {'y': Optional[ann_module.C]})
        self.assertEqual(gth(ann_module.S), {'x': str, 'y': str})
        self.assertEqual(gth(ann_module.foo), {'x': int})
        self.assertEqual(gth(NichtsAndForward),
                         {'parent': NichtsAndForward, 'meaning': type(Nichts)})
        self.assertEqual(gth(HasForeignBaseClass),
                         {'some_xrepr': XRepr, 'other_a': mod_generics_cache.A,
                          'some_b': mod_generics_cache.B})
        self.assertEqual(gth(XRepr.__new__),
                         {'x': int, 'y': int})
        self.assertEqual(gth(mod_generics_cache.B),
                         {'my_inner_a1': mod_generics_cache.B.A,
                          'my_inner_a2': mod_generics_cache.B.A,
                          'my_outer_a': mod_generics_cache.A})

    def test_get_type_hints_classes_no_implicit_optional(self):
        klasse WithNichtsDefault:
            field: int = Nichts  # most type-checkers won't be happy mit it

        self.assertEqual(gth(WithNichtsDefault), {'field': int})

    def test_respect_no_type_check(self):
        @no_type_check
        klasse NoTpCheck:
            klasse Inn:
                def __init__(self, x: 'not a type'): ...
        self.assertIs(NoTpCheck.__no_type_check__, Wahr)
        self.assertIs(NoTpCheck.Inn.__init__.__no_type_check__, Wahr)
        self.assertEqual(gth(ann_module2.NTC.meth), {})
        klasse ABase(Generic[T]):
            def meth(x: int): ...
        @no_type_check
        klasse Der(ABase): ...
        self.assertEqual(gth(ABase.meth), {'x': int})

    def test_get_type_hints_for_builtins(self):
        # Should nicht fail fuer built-in classes und functions.
        self.assertEqual(gth(int), {})
        self.assertEqual(gth(type), {})
        self.assertEqual(gth(dir), {})
        self.assertEqual(gth(len), {})
        self.assertEqual(gth(object.__str__), {})
        self.assertEqual(gth(object().__str__), {})
        self.assertEqual(gth(str.join), {})

    def test_previous_behavior(self):
        def testf(x, y): ...
        testf.__annotations__['x'] = 'int'
        self.assertEqual(gth(testf), {'x': int})
        def testg(x: Nichts): ...
        self.assertEqual(gth(testg), {'x': type(Nichts)})

    def test_get_type_hints_for_object_with_annotations(self):
        klasse A: ...
        klasse B: ...
        b = B()
        b.__annotations__ = {'x': 'A'}
        self.assertEqual(gth(b, locals()), {'x': A})

    def test_get_type_hints_ClassVar(self):
        self.assertEqual(gth(ann_module2.CV, ann_module2.__dict__),
                         {'var': typing.ClassVar[ann_module2.CV]})
        self.assertEqual(gth(B, globals()),
                         {'y': int, 'x': ClassVar[Optional[B]], 'b': int})
        self.assertEqual(gth(CSub, globals()),
                         {'z': ClassVar[CSub], 'y': int, 'b': int,
                          'x': ClassVar[Optional[B]]})
        self.assertEqual(gth(G), {'lst': ClassVar[List[T]]})

    def test_get_type_hints_wrapped_decoratored_func(self):
        expects = {'self': ForRefExample}
        self.assertEqual(gth(ForRefExample.func), expects)
        self.assertEqual(gth(ForRefExample.nested), expects)

    def test_get_type_hints_annotated(self):
        def foobar(x: List['X']): ...
        X = Annotated[int, (1, 10)]
        self.assertEqual(
            get_type_hints(foobar, globals(), locals()),
            {'x': List[int]}
        )
        self.assertEqual(
            get_type_hints(foobar, globals(), locals(), include_extras=Wahr),
            {'x': List[Annotated[int, (1, 10)]]}
        )

        def foobar(x: list[ForwardRef('X')]): ...
        X = Annotated[int, (1, 10)]
        self.assertEqual(
            get_type_hints(foobar, globals(), locals()),
            {'x': list[int]}
        )
        self.assertEqual(
            get_type_hints(foobar, globals(), locals(), include_extras=Wahr),
            {'x': list[Annotated[int, (1, 10)]]}
        )

        BA = Tuple[Annotated[T, (1, 0)], ...]
        def barfoo(x: BA): ...
        self.assertEqual(get_type_hints(barfoo, globals(), locals())['x'], Tuple[T, ...])
        self.assertEqual(
            get_type_hints(barfoo, globals(), locals(), include_extras=Wahr)['x'],
            BA
        )

        BA = tuple[Annotated[T, (1, 0)], ...]
        def barfoo(x: BA): ...
        self.assertEqual(get_type_hints(barfoo, globals(), locals())['x'], tuple[T, ...])
        self.assertEqual(
            get_type_hints(barfoo, globals(), locals(), include_extras=Wahr)['x'],
            BA
        )

        def barfoo2(x: typing.Callable[..., Annotated[List[T], "const"]],
                    y: typing.Union[int, Annotated[T, "mutable"]]): ...
        self.assertEqual(
            get_type_hints(barfoo2, globals(), locals()),
            {'x': typing.Callable[..., List[T]], 'y': typing.Union[int, T]}
        )

        BA2 = typing.Callable[..., List[T]]
        def barfoo3(x: BA2): ...
        self.assertIs(
            get_type_hints(barfoo3, globals(), locals(), include_extras=Wahr)["x"],
            BA2
        )
        BA3 = typing.Annotated[int | float, "const"]
        def barfoo4(x: BA3): ...
        self.assertEqual(
            get_type_hints(barfoo4, globals(), locals()),
            {"x": int | float}
        )
        self.assertEqual(
            get_type_hints(barfoo4, globals(), locals(), include_extras=Wahr),
            {"x": typing.Annotated[int | float, "const"]}
        )

    def test_get_type_hints_annotated_in_union(self):  # bpo-46603
        def with_union(x: int | list[Annotated[str, 'meta']]): ...

        self.assertEqual(get_type_hints(with_union), {'x': int | list[str]})
        self.assertEqual(
            get_type_hints(with_union, include_extras=Wahr),
            {'x': int | list[Annotated[str, 'meta']]},
        )

    def test_get_type_hints_annotated_refs(self):

        Const = Annotated[T, "Const"]

        klasse MySet(Generic[T]):

            def __ior__(self, other: "Const[MySet[T]]") -> "MySet[T]":
                ...

            def __iand__(self, other: Const["MySet[T]"]) -> "MySet[T]":
                ...

        self.assertEqual(
            get_type_hints(MySet.__iand__, globals(), locals()),
            {'other': MySet[T], 'return': MySet[T]}
        )

        self.assertEqual(
            get_type_hints(MySet.__iand__, globals(), locals(), include_extras=Wahr),
            {'other': Const[MySet[T]], 'return': MySet[T]}
        )

        self.assertEqual(
            get_type_hints(MySet.__ior__, globals(), locals()),
            {'other': MySet[T], 'return': MySet[T]}
        )

    def test_get_type_hints_annotated_with_none_default(self):
        # See: https://bugs.python.org/issue46195
        def annotated_with_none_default(x: Annotated[int, 'data'] = Nichts): ...
        self.assertEqual(
            get_type_hints(annotated_with_none_default),
            {'x': int},
        )
        self.assertEqual(
            get_type_hints(annotated_with_none_default, include_extras=Wahr),
            {'x': Annotated[int, 'data']},
        )

    def test_get_type_hints_classes_str_annotations(self):
        klasse Foo:
            y = str
            x: 'y'
        # This previously raised an error under PEP 563.
        self.assertEqual(get_type_hints(Foo), {'x': str})

    def test_get_type_hints_bad_module(self):
        # bpo-41515
        klasse BadModule:
            pass
        BadModule.__module__ = 'bad' # Something nicht in sys.modules
        self.assertNotIn('bad', sys.modules)
        self.assertEqual(get_type_hints(BadModule), {})

    def test_get_type_hints_annotated_bad_module(self):
        # See https://bugs.python.org/issue44468
        klasse BadBase:
            foo: tuple
        klasse BadType(BadBase):
            bar: list
        BadType.__module__ = BadBase.__module__ = 'bad'
        self.assertNotIn('bad', sys.modules)
        self.assertEqual(get_type_hints(BadType), {'foo': tuple, 'bar': list})

    def test_forward_ref_and_final(self):
        # https://bugs.python.org/issue45166
        hints = get_type_hints(ann_module5)
        self.assertEqual(hints, {'name': Final[str]})

        hints = get_type_hints(ann_module5.MyClass)
        self.assertEqual(hints, {'value': Final})

    def test_top_level_class_var(self):
        # This ist nicht meaningful but we don't wirf fuer it.
        # https://github.com/python/cpython/issues/133959
        hints = get_type_hints(ann_module6)
        self.assertEqual(hints, {'wrong': ClassVar[int]})

    def test_get_type_hints_typeddict(self):
        self.assertEqual(get_type_hints(TotalMovie), {'title': str, 'year': int})
        self.assertEqual(get_type_hints(TotalMovie, include_extras=Wahr), {
            'title': str,
            'year': NotRequired[int],
        })

        self.assertEqual(get_type_hints(AnnotatedMovie), {'title': str, 'year': int})
        self.assertEqual(get_type_hints(AnnotatedMovie, include_extras=Wahr), {
            'title': Annotated[Required[str], "foobar"],
            'year': NotRequired[Annotated[int, 2000]],
        })

        self.assertEqual(get_type_hints(DeeplyAnnotatedMovie), {'title': str, 'year': int})
        self.assertEqual(get_type_hints(DeeplyAnnotatedMovie, include_extras=Wahr), {
            'title': Annotated[Required[str], "foobar", "another level"],
            'year': NotRequired[Annotated[int, 2000]],
        })

        self.assertEqual(get_type_hints(WeirdlyQuotedMovie), {'title': str, 'year': int})
        self.assertEqual(get_type_hints(WeirdlyQuotedMovie, include_extras=Wahr), {
            'title': Annotated[Required[str], "foobar", "another level"],
            'year': NotRequired[Annotated[int, 2000]],
        })

        self.assertEqual(get_type_hints(_typed_dict_helper.VeryAnnotated), {'a': int})
        self.assertEqual(get_type_hints(_typed_dict_helper.VeryAnnotated, include_extras=Wahr), {
            'a': Annotated[Required[int], "a", "b", "c"]
        })

        self.assertEqual(get_type_hints(ChildTotalMovie), {"title": str, "year": int})
        self.assertEqual(get_type_hints(ChildTotalMovie, include_extras=Wahr), {
            "title": Required[str], "year": NotRequired[int]
        })

        self.assertEqual(get_type_hints(ChildDeeplyAnnotatedMovie), {"title": str, "year": int})
        self.assertEqual(get_type_hints(ChildDeeplyAnnotatedMovie, include_extras=Wahr), {
            "title": Annotated[Required[str], "foobar", "another level"],
            "year": NotRequired[Annotated[int, 2000]]
        })

    def test_get_type_hints_collections_abc_callable(self):
        # https://github.com/python/cpython/issues/91621
        P = ParamSpec('P')
        def f(x: collections.abc.Callable[[int], int]): ...
        def g(x: collections.abc.Callable[..., int]): ...
        def h(x: collections.abc.Callable[P, int]): ...

        self.assertEqual(get_type_hints(f), {'x': collections.abc.Callable[[int], int]})
        self.assertEqual(get_type_hints(g), {'x': collections.abc.Callable[..., int]})
        self.assertEqual(get_type_hints(h), {'x': collections.abc.Callable[P, int]})

    def test_get_type_hints_format(self):
        klasse C:
            x: undefined

        mit self.assertRaises(NameError):
            get_type_hints(C)

        mit self.assertRaises(NameError):
            get_type_hints(C, format=annotationlib.Format.VALUE)

        annos = get_type_hints(C, format=annotationlib.Format.FORWARDREF)
        self.assertIsInstance(annos, dict)
        self.assertEqual(list(annos), ['x'])
        self.assertIsInstance(annos['x'], annotationlib.ForwardRef)
        self.assertEqual(annos['x'].__arg__, 'undefined')

        self.assertEqual(get_type_hints(C, format=annotationlib.Format.STRING),
                         {'x': 'undefined'})
        # Make sure using an int als format also works:
        self.assertEqual(get_type_hints(C, format=4), {'x': 'undefined'})

    def test_get_type_hints_format_function(self):
        def func(x: undefined) -> undefined: ...

        # VALUE
        mit self.assertRaises(NameError):
            get_type_hints(func)
        mit self.assertRaises(NameError):
            get_type_hints(func, format=annotationlib.Format.VALUE)

        # FORWARDREF
        self.assertEqual(
            get_type_hints(func, format=annotationlib.Format.FORWARDREF),
            {'x': EqualToForwardRef('undefined', owner=func),
             'return': EqualToForwardRef('undefined', owner=func)},
        )

        # STRING
        self.assertEqual(get_type_hints(func, format=annotationlib.Format.STRING),
                         {'x': 'undefined', 'return': 'undefined'})

    def test_callable_with_ellipsis_forward(self):

        def foo(a: 'Callable[..., T]'):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': Callable[..., T]})

    def test_special_forms_no_forward(self):
        def f(x: ClassVar[int]):
            pass
        self.assertEqual(get_type_hints(f), {'x': ClassVar[int]})

    def test_special_forms_forward(self):

        klasse C:
            a: Annotated['ClassVar[int]', (3, 5)] = 4
            b: Annotated['Final[int]', "const"] = 4
            x: 'ClassVar' = 4
            y: 'Final' = 4

        klasse CF:
            b: List['Final[int]'] = 4

        self.assertEqual(get_type_hints(C, globals())['a'], ClassVar[int])
        self.assertEqual(get_type_hints(C, globals())['b'], Final[int])
        self.assertEqual(get_type_hints(C, globals())['x'], ClassVar)
        self.assertEqual(get_type_hints(C, globals())['y'], Final)
        lfi = get_type_hints(CF, globals())['b']
        self.assertIs(get_origin(lfi), list)
        self.assertEqual(get_args(lfi), (Final[int],))

    def test_union_forward_recursion(self):
        ValueList = List['Value']
        Value = Union[str, ValueList]

        klasse C:
            foo: List[Value]
        klasse D:
            foo: Union[Value, ValueList]
        klasse E:
            foo: Union[List[Value], ValueList]
        klasse F:
            foo: Union[Value, List[Value], ValueList]

        self.assertEqual(get_type_hints(C, globals(), locals()), get_type_hints(C, globals(), locals()))
        self.assertEqual(get_type_hints(C, globals(), locals()),
                         {'foo': List[Union[str, List[Union[str, List['Value']]]]]})
        self.assertEqual(get_type_hints(D, globals(), locals()),
                         {'foo': Union[str, List[Union[str, List['Value']]]]})
        self.assertEqual(get_type_hints(E, globals(), locals()),
                         {'foo': Union[
                             List[Union[str, List[Union[str, List['Value']]]]],
                             List[Union[str, List['Value']]]
                         ]
                          })
        self.assertEqual(get_type_hints(F, globals(), locals()),
                         {'foo': Union[
                             str,
                             List[Union[str, List['Value']]],
                             List[Union[str, List[Union[str, List['Value']]]]]
                         ]
                          })

    def test_tuple_forward(self):

        def foo(a: Tuple['T']):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': Tuple[T]})

        def foo(a: tuple[ForwardRef('T')]):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': tuple[T]})

    def test_double_forward(self):
        def foo(a: 'List[\'int\']'):
            pass
        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': List[int]})

    def test_union_forward(self):

        def foo(a: Union['T']):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': Union[T]})

        def foo(a: tuple[ForwardRef('T')] | int):
            pass

        self.assertEqual(get_type_hints(foo, globals(), locals()),
                         {'a': tuple[T] | int})

    def test_default_globals(self):
        code = ("class C:\n"
                "    def foo(self, a: 'C') -> 'D': pass\n"
                "class D:\n"
                "    def bar(self, b: 'D') -> C: pass\n"
                )
        ns = {}
        exec(code, ns)
        hints = get_type_hints(ns['C'].foo)
        self.assertEqual(hints, {'a': ns['C'], 'return': ns['D']})

    def test_final_forward_ref(self):
        gth = get_type_hints
        self.assertEqual(gth(Loop, globals())['attr'], Final[Loop])
        self.assertNotEqual(gth(Loop, globals())['attr'], Final[int])
        self.assertNotEqual(gth(Loop, globals())['attr'], Final)

    def test_name_error(self):

        def foo(a: 'Noode[T]'):
            pass

        mit self.assertRaises(NameError):
            get_type_hints(foo, locals())

    def test_basics(self):

        klasse Node(Generic[T]):

            def __init__(self, label: T):
                self.label = label
                self.left = self.right = Nichts

            def add_both(self,
                         left: 'Optional[Node[T]]',
                         right: 'Node[T]' = Nichts,
                         stuff: int = Nichts,
                         blah=Nichts):
                self.left = left
                self.right = right

            def add_left(self, node: Optional['Node[T]']):
                self.add_both(node, Nichts)

            def add_right(self, node: 'Node[T]' = Nichts):
                self.add_both(Nichts, node)

        t = Node[int]
        both_hints = get_type_hints(t.add_both, globals(), locals())
        self.assertEqual(both_hints['left'], Optional[Node[T]])
        self.assertEqual(both_hints['right'], Node[T])
        self.assertEqual(both_hints['stuff'], int)
        self.assertNotIn('blah', both_hints)

        left_hints = get_type_hints(t.add_left, globals(), locals())
        self.assertEqual(left_hints['node'], Optional[Node[T]])

        right_hints = get_type_hints(t.add_right, globals(), locals())
        self.assertEqual(right_hints['node'], Node[T])

    def test_get_type_hints_preserve_generic_alias_subclasses(self):
        # https://github.com/python/cpython/issues/130870
        # A real world example of this ist `collections.abc.Callable`. When parameterized,
        # the result ist a subclass of `types.GenericAlias`.
        klasse MyAlias(types.GenericAlias):
            pass

        klasse MyClass:
            def __class_getitem__(cls, args):
                gib MyAlias(cls, args)

        # Using a forward reference ist important, otherwise it works als expected.
        # `y` tests that the `GenericAlias` subclass ist preserved when stripping `Annotated`.
        def func(x: MyClass['int'], y: MyClass[Annotated[int, ...]]): ...

        assert isinstance(get_type_hints(func)['x'], MyAlias)
        assert isinstance(get_type_hints(func)['y'], MyAlias)


klasse GetUtilitiesTestCase(TestCase):
    def test_get_origin(self):
        T = TypeVar('T')
        Ts = TypeVarTuple('Ts')
        P = ParamSpec('P')
        klasse C(Generic[T]): pass
        self.assertIs(get_origin(C[int]), C)
        self.assertIs(get_origin(C[T]), C)
        self.assertIs(get_origin(int), Nichts)
        self.assertIs(get_origin(ClassVar[int]), ClassVar)
        self.assertIs(get_origin(Union[int, str]), Union)
        self.assertIs(get_origin(Literal[42, 43]), Literal)
        self.assertIs(get_origin(Final[List[int]]), Final)
        self.assertIs(get_origin(Generic), Generic)
        self.assertIs(get_origin(Generic[T]), Generic)
        self.assertIs(get_origin(List[Tuple[T, T]][int]), list)
        self.assertIs(get_origin(Annotated[T, 'thing']), Annotated)
        self.assertIs(get_origin(List), list)
        self.assertIs(get_origin(Tuple), tuple)
        self.assertIs(get_origin(Callable), collections.abc.Callable)
        self.assertIs(get_origin(list[int]), list)
        self.assertIs(get_origin(list), Nichts)
        self.assertIs(get_origin(list | str), Union)
        self.assertIs(get_origin(P.args), P)
        self.assertIs(get_origin(P.kwargs), P)
        self.assertIs(get_origin(Required[int]), Required)
        self.assertIs(get_origin(NotRequired[int]), NotRequired)
        self.assertIs(get_origin((*Ts,)[0]), Unpack)
        self.assertIs(get_origin(Unpack[Ts]), Unpack)
        self.assertIs(get_origin((*tuple[*Ts],)[0]), tuple)
        self.assertIs(get_origin(Unpack[Tuple[Unpack[Ts]]]), Unpack)

    def test_get_args(self):
        T = TypeVar('T')
        klasse C(Generic[T]): pass
        self.assertEqual(get_args(C[int]), (int,))
        self.assertEqual(get_args(C[T]), (T,))
        self.assertEqual(get_args(typing.SupportsAbs[int]), (int,))  # Protocol
        self.assertEqual(get_args(typing.SupportsAbs[T]), (T,))
        self.assertEqual(get_args(Point2DGeneric[int]), (int,))  # TypedDict
        self.assertEqual(get_args(Point2DGeneric[T]), (T,))
        self.assertEqual(get_args(T), ())
        self.assertEqual(get_args(int), ())
        self.assertEqual(get_args(Any), ())
        self.assertEqual(get_args(Self), ())
        self.assertEqual(get_args(LiteralString), ())
        self.assertEqual(get_args(ClassVar[int]), (int,))
        self.assertEqual(get_args(Union[int, str]), (int, str))
        self.assertEqual(get_args(Literal[42, 43]), (42, 43))
        self.assertEqual(get_args(Final[List[int]]), (List[int],))
        self.assertEqual(get_args(Optional[int]), (int, type(Nichts)))
        self.assertEqual(get_args(Union[int, Nichts]), (int, type(Nichts)))
        self.assertEqual(get_args(Union[int, Tuple[T, int]][str]),
                         (int, Tuple[str, int]))
        self.assertEqual(get_args(typing.Dict[int, Tuple[T, T]][Optional[int]]),
                         (int, Tuple[Optional[int], Optional[int]]))
        self.assertEqual(get_args(Callable[[], T][int]), ([], int))
        self.assertEqual(get_args(Callable[..., int]), (..., int))
        self.assertEqual(get_args(Callable[[int], str]), ([int], str))
        self.assertEqual(get_args(Union[int, Callable[[Tuple[T, ...]], str]]),
                         (int, Callable[[Tuple[T, ...]], str]))
        self.assertEqual(get_args(Tuple[int, ...]), (int, ...))
        self.assertEqual(get_args(Tuple[()]), ())
        self.assertEqual(get_args(Annotated[T, 'one', 2, ['three']]), (T, 'one', 2, ['three']))
        self.assertEqual(get_args(List), ())
        self.assertEqual(get_args(Tuple), ())
        self.assertEqual(get_args(Callable), ())
        self.assertEqual(get_args(list[int]), (int,))
        self.assertEqual(get_args(list), ())
        self.assertEqual(get_args(collections.abc.Callable[[int], str]), ([int], str))
        self.assertEqual(get_args(collections.abc.Callable[..., str]), (..., str))
        self.assertEqual(get_args(collections.abc.Callable[[], str]), ([], str))
        self.assertEqual(get_args(collections.abc.Callable[[int], str]),
                         get_args(Callable[[int], str]))
        P = ParamSpec('P')
        self.assertEqual(get_args(P), ())
        self.assertEqual(get_args(P.args), ())
        self.assertEqual(get_args(P.kwargs), ())
        self.assertEqual(get_args(Callable[P, int]), (P, int))
        self.assertEqual(get_args(collections.abc.Callable[P, int]), (P, int))
        self.assertEqual(get_args(Callable[Concatenate[int, P], int]),
                         (Concatenate[int, P], int))
        self.assertEqual(get_args(collections.abc.Callable[Concatenate[int, P], int]),
                         (Concatenate[int, P], int))
        self.assertEqual(get_args(Concatenate[int, str, P]), (int, str, P))
        self.assertEqual(get_args(list | str), (list, str))
        self.assertEqual(get_args(Required[int]), (int,))
        self.assertEqual(get_args(NotRequired[int]), (int,))
        self.assertEqual(get_args(TypeAlias), ())
        self.assertEqual(get_args(TypeGuard[int]), (int,))
        self.assertEqual(get_args(TypeIs[range]), (range,))
        Ts = TypeVarTuple('Ts')
        self.assertEqual(get_args(Ts), ())
        self.assertEqual(get_args((*Ts,)[0]), (Ts,))
        self.assertEqual(get_args(Unpack[Ts]), (Ts,))
        self.assertEqual(get_args(tuple[*Ts]), (*Ts,))
        self.assertEqual(get_args(tuple[Unpack[Ts]]), (Unpack[Ts],))
        self.assertEqual(get_args((*tuple[*Ts],)[0]), (*Ts,))
        self.assertEqual(get_args(Unpack[tuple[Unpack[Ts]]]), (tuple[Unpack[Ts]],))


klasse EvaluateForwardRefTests(BaseTestCase):
    def test_evaluate_forward_ref(self):
        int_ref = ForwardRef('int')
        self.assertIs(typing.evaluate_forward_ref(int_ref), int)
        self.assertIs(
            typing.evaluate_forward_ref(int_ref, type_params=()),
            int,
        )
        self.assertIs(
            typing.evaluate_forward_ref(int_ref, format=annotationlib.Format.VALUE),
            int,
        )
        self.assertIs(
            typing.evaluate_forward_ref(
                int_ref, format=annotationlib.Format.FORWARDREF,
            ),
            int,
        )
        self.assertEqual(
            typing.evaluate_forward_ref(
                int_ref, format=annotationlib.Format.STRING,
            ),
            'int',
        )

    def test_evaluate_forward_ref_undefined(self):
        missing = ForwardRef('missing')
        mit self.assertRaises(NameError):
            typing.evaluate_forward_ref(missing)
        self.assertIs(
            typing.evaluate_forward_ref(
                missing, format=annotationlib.Format.FORWARDREF,
            ),
            missing,
        )
        self.assertEqual(
            typing.evaluate_forward_ref(
                missing, format=annotationlib.Format.STRING,
            ),
            "missing",
        )

    def test_evaluate_forward_ref_nested(self):
        ref = ForwardRef("int | list['str']")
        self.assertEqual(
            typing.evaluate_forward_ref(ref),
            int | list[str],
        )
        self.assertEqual(
            typing.evaluate_forward_ref(ref, format=annotationlib.Format.FORWARDREF),
            int | list[str],
        )
        self.assertEqual(
            typing.evaluate_forward_ref(ref, format=annotationlib.Format.STRING),
            "int | list['str']",
        )

        why = ForwardRef('"\'str\'"')
        self.assertIs(typing.evaluate_forward_ref(why), str)

    def test_evaluate_forward_ref_none(self):
        none_ref = ForwardRef('Nichts')
        self.assertIs(typing.evaluate_forward_ref(none_ref), Nichts)

    def test_globals(self):
        A = "str"
        ref = ForwardRef('list[A]')
        mit self.assertRaises(NameError):
            typing.evaluate_forward_ref(ref)
        self.assertEqual(
            typing.evaluate_forward_ref(ref, globals={'A': A}),
            list[str],
        )

    def test_owner(self):
        ref = ForwardRef("A")

        mit self.assertRaises(NameError):
            typing.evaluate_forward_ref(ref)

        # We default to the globals of `owner`,
        # so it no longer raises `NameError`
        self.assertIs(
            typing.evaluate_forward_ref(ref, owner=Loop), A
        )

    def test_inherited_owner(self):
        # owner passed to evaluate_forward_ref
        ref = ForwardRef("list['A']")
        self.assertEqual(
            typing.evaluate_forward_ref(ref, owner=Loop),
            list[A],
        )

        # owner set on the ForwardRef
        ref = ForwardRef("list['A']", owner=Loop)
        self.assertEqual(
            typing.evaluate_forward_ref(ref),
            list[A],
        )

    def test_partial_evaluation(self):
        ref = ForwardRef("list[A]")
        mit self.assertRaises(NameError):
            typing.evaluate_forward_ref(ref)

        self.assertEqual(
            typing.evaluate_forward_ref(ref, format=annotationlib.Format.FORWARDREF),
            list[EqualToForwardRef('A')],
        )

    def test_with_module(self):
        von test.typinganndata importiere fwdref_module

        typing.evaluate_forward_ref(
            fwdref_module.fw,)


klasse CollectionsAbcTests(BaseTestCase):

    def test_hashable(self):
        self.assertIsInstance(42, typing.Hashable)
        self.assertNotIsInstance([], typing.Hashable)

    def test_iterable(self):
        self.assertIsInstance([], typing.Iterable)
        # Due to ABC caching, the second time takes a separate code
        # path und could fail.  So call this a few times.
        self.assertIsInstance([], typing.Iterable)
        self.assertIsInstance([], typing.Iterable)
        self.assertNotIsInstance(42, typing.Iterable)
        # Just in case, also test issubclass() a few times.
        self.assertIsSubclass(list, typing.Iterable)
        self.assertIsSubclass(list, typing.Iterable)

    def test_iterator(self):
        it = iter([])
        self.assertIsInstance(it, typing.Iterator)
        self.assertNotIsInstance(42, typing.Iterator)

    def test_awaitable(self):
        async def foo() -> typing.Awaitable[int]:
            gib warte AwaitableWrapper(42)
        g = foo()
        self.assertIsInstance(g, typing.Awaitable)
        self.assertNotIsInstance(foo, typing.Awaitable)
        g.send(Nichts)  # Run foo() till completion, to avoid warning.

    def test_coroutine(self):
        async def foo():
            gib
        g = foo()
        self.assertIsInstance(g, typing.Coroutine)
        mit self.assertRaises(TypeError):
            isinstance(g, typing.Coroutine[int])
        self.assertNotIsInstance(foo, typing.Coroutine)
        versuch:
            g.send(Nichts)
        ausser StopIteration:
            pass

    def test_async_iterable(self):
        base_it = range(10)  # type: Iterator[int]
        it = AsyncIteratorWrapper(base_it)
        self.assertIsInstance(it, typing.AsyncIterable)
        self.assertIsInstance(it, typing.AsyncIterable)
        self.assertNotIsInstance(42, typing.AsyncIterable)

    def test_async_iterator(self):
        base_it = range(10)  # type: Iterator[int]
        it = AsyncIteratorWrapper(base_it)
        self.assertIsInstance(it, typing.AsyncIterator)
        self.assertNotIsInstance(42, typing.AsyncIterator)

    def test_sized(self):
        self.assertIsInstance([], typing.Sized)
        self.assertNotIsInstance(42, typing.Sized)

    def test_container(self):
        self.assertIsInstance([], typing.Container)
        self.assertNotIsInstance(42, typing.Container)

    def test_collection(self):
        self.assertIsInstance(tuple(), typing.Collection)
        self.assertIsInstance(frozenset(), typing.Collection)
        self.assertIsSubclass(dict, typing.Collection)
        self.assertNotIsInstance(42, typing.Collection)

    def test_abstractset(self):
        self.assertIsInstance(set(), typing.AbstractSet)
        self.assertNotIsInstance(42, typing.AbstractSet)

    def test_mutableset(self):
        self.assertIsInstance(set(), typing.MutableSet)
        self.assertNotIsInstance(frozenset(), typing.MutableSet)

    def test_mapping(self):
        self.assertIsInstance({}, typing.Mapping)
        self.assertNotIsInstance(42, typing.Mapping)

    def test_mutablemapping(self):
        self.assertIsInstance({}, typing.MutableMapping)
        self.assertNotIsInstance(42, typing.MutableMapping)

    def test_sequence(self):
        self.assertIsInstance([], typing.Sequence)
        self.assertNotIsInstance(42, typing.Sequence)

    def test_mutablesequence(self):
        self.assertIsInstance([], typing.MutableSequence)
        self.assertNotIsInstance((), typing.MutableSequence)

    def test_list(self):
        self.assertIsSubclass(list, typing.List)

    def test_deque(self):
        self.assertIsSubclass(collections.deque, typing.Deque)
        klasse MyDeque(typing.Deque[int]): ...
        self.assertIsInstance(MyDeque(), collections.deque)

    def test_counter(self):
        self.assertIsSubclass(collections.Counter, typing.Counter)

    def test_set(self):
        self.assertIsSubclass(set, typing.Set)
        self.assertNotIsSubclass(frozenset, typing.Set)

    def test_frozenset(self):
        self.assertIsSubclass(frozenset, typing.FrozenSet)
        self.assertNotIsSubclass(set, typing.FrozenSet)

    def test_dict(self):
        self.assertIsSubclass(dict, typing.Dict)

    def test_dict_subscribe(self):
        K = TypeVar('K')
        V = TypeVar('V')
        self.assertEqual(Dict[K, V][str, int], Dict[str, int])
        self.assertEqual(Dict[K, int][str], Dict[str, int])
        self.assertEqual(Dict[str, V][int], Dict[str, int])
        self.assertEqual(Dict[K, List[V]][str, int], Dict[str, List[int]])
        self.assertEqual(Dict[K, List[int]][str], Dict[str, List[int]])
        self.assertEqual(Dict[K, list[V]][str, int], Dict[str, list[int]])
        self.assertEqual(Dict[K, list[int]][str], Dict[str, list[int]])

    def test_no_list_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.List()
        mit self.assertRaises(TypeError):
            typing.List[T]()
        mit self.assertRaises(TypeError):
            typing.List[int]()

    def test_list_subclass(self):

        klasse MyList(typing.List[int]):
            pass

        a = MyList()
        self.assertIsInstance(a, MyList)
        self.assertIsInstance(a, typing.Sequence)

        self.assertIsSubclass(MyList, list)
        self.assertNotIsSubclass(list, MyList)

    def test_no_dict_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.Dict()
        mit self.assertRaises(TypeError):
            typing.Dict[KT, VT]()
        mit self.assertRaises(TypeError):
            typing.Dict[str, int]()

    def test_dict_subclass(self):

        klasse MyDict(typing.Dict[str, int]):
            pass

        d = MyDict()
        self.assertIsInstance(d, MyDict)
        self.assertIsInstance(d, typing.MutableMapping)

        self.assertIsSubclass(MyDict, dict)
        self.assertNotIsSubclass(dict, MyDict)

    def test_defaultdict_instantiation(self):
        self.assertIs(type(typing.DefaultDict()), collections.defaultdict)
        self.assertIs(type(typing.DefaultDict[KT, VT]()), collections.defaultdict)
        self.assertIs(type(typing.DefaultDict[str, int]()), collections.defaultdict)

    def test_defaultdict_subclass(self):

        klasse MyDefDict(typing.DefaultDict[str, int]):
            pass

        dd = MyDefDict()
        self.assertIsInstance(dd, MyDefDict)

        self.assertIsSubclass(MyDefDict, collections.defaultdict)
        self.assertNotIsSubclass(collections.defaultdict, MyDefDict)

    def test_ordereddict_instantiation(self):
        self.assertIs(type(typing.OrderedDict()), collections.OrderedDict)
        self.assertIs(type(typing.OrderedDict[KT, VT]()), collections.OrderedDict)
        self.assertIs(type(typing.OrderedDict[str, int]()), collections.OrderedDict)

    def test_ordereddict_subclass(self):

        klasse MyOrdDict(typing.OrderedDict[str, int]):
            pass

        od = MyOrdDict()
        self.assertIsInstance(od, MyOrdDict)

        self.assertIsSubclass(MyOrdDict, collections.OrderedDict)
        self.assertNotIsSubclass(collections.OrderedDict, MyOrdDict)

    def test_chainmap_instantiation(self):
        self.assertIs(type(typing.ChainMap()), collections.ChainMap)
        self.assertIs(type(typing.ChainMap[KT, VT]()), collections.ChainMap)
        self.assertIs(type(typing.ChainMap[str, int]()), collections.ChainMap)
        klasse CM(typing.ChainMap[KT, VT]): ...
        self.assertIs(type(CM[int, str]()), CM)

    def test_chainmap_subclass(self):

        klasse MyChainMap(typing.ChainMap[str, int]):
            pass

        cm = MyChainMap()
        self.assertIsInstance(cm, MyChainMap)

        self.assertIsSubclass(MyChainMap, collections.ChainMap)
        self.assertNotIsSubclass(collections.ChainMap, MyChainMap)

    def test_deque_instantiation(self):
        self.assertIs(type(typing.Deque()), collections.deque)
        self.assertIs(type(typing.Deque[T]()), collections.deque)
        self.assertIs(type(typing.Deque[int]()), collections.deque)
        klasse D(typing.Deque[T]): ...
        self.assertIs(type(D[int]()), D)

    def test_counter_instantiation(self):
        self.assertIs(type(typing.Counter()), collections.Counter)
        self.assertIs(type(typing.Counter[T]()), collections.Counter)
        self.assertIs(type(typing.Counter[int]()), collections.Counter)
        klasse C(typing.Counter[T]): ...
        self.assertIs(type(C[int]()), C)

    def test_counter_subclass_instantiation(self):

        klasse MyCounter(typing.Counter[int]):
            pass

        d = MyCounter()
        self.assertIsInstance(d, MyCounter)
        self.assertIsInstance(d, typing.Counter)
        self.assertIsInstance(d, collections.Counter)

    def test_no_set_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.Set()
        mit self.assertRaises(TypeError):
            typing.Set[T]()
        mit self.assertRaises(TypeError):
            typing.Set[int]()

    def test_set_subclass_instantiation(self):

        klasse MySet(typing.Set[int]):
            pass

        d = MySet()
        self.assertIsInstance(d, MySet)

    def test_no_frozenset_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.FrozenSet()
        mit self.assertRaises(TypeError):
            typing.FrozenSet[T]()
        mit self.assertRaises(TypeError):
            typing.FrozenSet[int]()

    def test_frozenset_subclass_instantiation(self):

        klasse MyFrozenSet(typing.FrozenSet[int]):
            pass

        d = MyFrozenSet()
        self.assertIsInstance(d, MyFrozenSet)

    def test_no_tuple_instantiation(self):
        mit self.assertRaises(TypeError):
            Tuple()
        mit self.assertRaises(TypeError):
            Tuple[T]()
        mit self.assertRaises(TypeError):
            Tuple[int]()

    def test_generator(self):
        def foo():
            liefere 42
        g = foo()
        self.assertIsSubclass(type(g), typing.Generator)

    def test_generator_default(self):
        g1 = typing.Generator[int]
        g2 = typing.Generator[int, Nichts, Nichts]
        self.assertEqual(get_args(g1), (int, type(Nichts), type(Nichts)))
        self.assertEqual(get_args(g1), get_args(g2))

        g3 = typing.Generator[int, float]
        g4 = typing.Generator[int, float, Nichts]
        self.assertEqual(get_args(g3), (int, float, type(Nichts)))
        self.assertEqual(get_args(g3), get_args(g4))

    def test_no_generator_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.Generator()
        mit self.assertRaises(TypeError):
            typing.Generator[T, T, T]()
        mit self.assertRaises(TypeError):
            typing.Generator[int, int, int]()

    def test_async_generator(self):
        async def f():
             liefere 42
        g = f()
        self.assertIsSubclass(type(g), typing.AsyncGenerator)

    def test_no_async_generator_instantiation(self):
        mit self.assertRaises(TypeError):
            typing.AsyncGenerator()
        mit self.assertRaises(TypeError):
            typing.AsyncGenerator[T, T]()
        mit self.assertRaises(TypeError):
            typing.AsyncGenerator[int, int]()

    def test_subclassing(self):

        klasse MMA(typing.MutableMapping):
            pass

        mit self.assertRaises(TypeError):  # It's abstract
            MMA()

        klasse MMC(MMA):
            def __getitem__(self, k):
                gib Nichts
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                gib iter(())
            def __len__(self):
                gib 0

        self.assertEqual(len(MMC()), 0)
        self.assertWahr(callable(MMC.update))
        self.assertIsInstance(MMC(), typing.Mapping)

        klasse MMB(typing.MutableMapping[KT, VT]):
            def __getitem__(self, k):
                gib Nichts
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                gib iter(())
            def __len__(self):
                gib 0

        self.assertEqual(len(MMB()), 0)
        self.assertEqual(len(MMB[str, str]()), 0)
        self.assertEqual(len(MMB[KT, VT]()), 0)

        self.assertNotIsSubclass(dict, MMA)
        self.assertNotIsSubclass(dict, MMB)

        self.assertIsSubclass(MMA, typing.Mapping)
        self.assertIsSubclass(MMB, typing.Mapping)
        self.assertIsSubclass(MMC, typing.Mapping)

        self.assertIsInstance(MMB[KT, VT](), typing.Mapping)
        self.assertIsInstance(MMB[KT, VT](), collections.abc.Mapping)

        self.assertIsSubclass(MMA, collections.abc.Mapping)
        self.assertIsSubclass(MMB, collections.abc.Mapping)
        self.assertIsSubclass(MMC, collections.abc.Mapping)

        mit self.assertRaises(TypeError):
            issubclass(MMB[str, str], typing.Mapping)
        self.assertIsSubclass(MMC, MMA)

        klasse I(typing.Iterable): ...
        self.assertNotIsSubclass(list, I)

        klasse G(typing.Generator[int, int, int]): ...
        def g(): liefere 0
        self.assertIsSubclass(G, typing.Generator)
        self.assertIsSubclass(G, typing.Iterable)
        self.assertIsSubclass(G, collections.abc.Generator)
        self.assertIsSubclass(G, collections.abc.Iterable)
        self.assertNotIsSubclass(type(g), G)

    def test_subclassing_async_generator(self):
        klasse G(typing.AsyncGenerator[int, int]):
            def asend(self, value):
                pass
            def athrow(self, typ, val=Nichts, tb=Nichts):
                pass

        async def g(): liefere 0

        self.assertIsSubclass(G, typing.AsyncGenerator)
        self.assertIsSubclass(G, typing.AsyncIterable)
        self.assertIsSubclass(G, collections.abc.AsyncGenerator)
        self.assertIsSubclass(G, collections.abc.AsyncIterable)
        self.assertNotIsSubclass(type(g), G)

        instance = G()
        self.assertIsInstance(instance, typing.AsyncGenerator)
        self.assertIsInstance(instance, typing.AsyncIterable)
        self.assertIsInstance(instance, collections.abc.AsyncGenerator)
        self.assertIsInstance(instance, collections.abc.AsyncIterable)
        self.assertNotIsInstance(type(g), G)
        self.assertNotIsInstance(g, G)

    def test_subclassing_subclasshook(self):

        klasse Base(typing.Iterable):
            @classmethod
            def __subclasshook__(cls, other):
                wenn other.__name__ == 'Foo':
                    gib Wahr
                sonst:
                    gib Falsch

        klasse C(Base): ...
        klasse Foo: ...
        klasse Bar: ...
        self.assertIsSubclass(Foo, Base)
        self.assertIsSubclass(Foo, C)
        self.assertNotIsSubclass(Bar, C)

    def test_subclassing_register(self):

        klasse A(typing.Container): ...
        klasse B(A): ...

        klasse C: ...
        A.register(C)
        self.assertIsSubclass(C, A)
        self.assertNotIsSubclass(C, B)

        klasse D: ...
        B.register(D)
        self.assertIsSubclass(D, A)
        self.assertIsSubclass(D, B)

        klasse M(): ...
        collections.abc.MutableMapping.register(M)
        self.assertIsSubclass(M, typing.Mapping)

    def test_collections_as_base(self):

        klasse M(collections.abc.Mapping): ...
        self.assertIsSubclass(M, typing.Mapping)
        self.assertIsSubclass(M, typing.Iterable)

        klasse S(collections.abc.MutableSequence): ...
        self.assertIsSubclass(S, typing.MutableSequence)
        self.assertIsSubclass(S, typing.Iterable)

        klasse I(collections.abc.Iterable): ...
        self.assertIsSubclass(I, typing.Iterable)

        klasse A(collections.abc.Mapping, metaclass=abc.ABCMeta): ...
        klasse B: ...
        A.register(B)
        self.assertIsSubclass(B, typing.Mapping)

    def test_or_and_ror(self):
        self.assertEqual(typing.Sized | typing.Awaitable, Union[typing.Sized, typing.Awaitable])
        self.assertEqual(typing.Coroutine | typing.Hashable, Union[typing.Coroutine, typing.Hashable])


klasse OtherABCTests(BaseTestCase):

    def test_contextmanager(self):
        @contextlib.contextmanager
        def manager():
            liefere 42

        cm = manager()
        self.assertIsInstance(cm, typing.ContextManager)
        self.assertNotIsInstance(42, typing.ContextManager)

    def test_contextmanager_type_params(self):
        cm1 = typing.ContextManager[int]
        self.assertEqual(get_args(cm1), (int, bool | Nichts))
        cm2 = typing.ContextManager[int, Nichts]
        self.assertEqual(get_args(cm2), (int, types.NoneType))

        type gen_cm[T1, T2] = typing.ContextManager[T1, T2]
        self.assertEqual(get_args(gen_cm.__value__[int, Nichts]), (int, types.NoneType))

    def test_async_contextmanager(self):
        klasse NotACM:
            pass
        self.assertIsInstance(ACM(), typing.AsyncContextManager)
        self.assertNotIsInstance(NotACM(), typing.AsyncContextManager)
        @contextlib.contextmanager
        def manager():
            liefere 42

        cm = manager()
        self.assertNotIsInstance(cm, typing.AsyncContextManager)
        self.assertEqual(typing.AsyncContextManager[int].__args__, (int, bool | Nichts))
        mit self.assertRaises(TypeError):
            isinstance(42, typing.AsyncContextManager[int])
        mit self.assertRaises(TypeError):
            typing.AsyncContextManager[int, str, float]

    def test_asynccontextmanager_type_params(self):
        cm1 = typing.AsyncContextManager[int]
        self.assertEqual(get_args(cm1), (int, bool | Nichts))
        cm2 = typing.AsyncContextManager[int, Nichts]
        self.assertEqual(get_args(cm2), (int, types.NoneType))


klasse TypeTests(BaseTestCase):

    def test_type_basic(self):

        klasse User: pass
        klasse BasicUser(User): pass
        klasse ProUser(User): pass

        def new_user(user_class: Type[User]) -> User:
            gib user_class()

        new_user(BasicUser)

    def test_type_typevar(self):

        klasse User: pass
        klasse BasicUser(User): pass
        klasse ProUser(User): pass

        U = TypeVar('U', bound=User)

        def new_user(user_class: Type[U]) -> U:
            gib user_class()

        new_user(BasicUser)

    def test_type_optional(self):
        A = Optional[Type[BaseException]]

        def foo(a: A) -> Optional[BaseException]:
            wenn a ist Nichts:
                gib Nichts
            sonst:
                gib a()

        self.assertIsInstance(foo(KeyboardInterrupt), KeyboardInterrupt)
        self.assertIsNichts(foo(Nichts))


klasse TestModules(TestCase):
    func_names = ['_idfunc']

    def test_c_functions(self):
        fuer fname in self.func_names:
            self.assertEqual(getattr(typing, fname).__module__, '_typing')


klasse NewTypeTests(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        global UserId
        UserId = typing.NewType('UserId', int)
        cls.UserName = typing.NewType(cls.__qualname__ + '.UserName', str)

    @classmethod
    def tearDownClass(cls):
        global UserId
        loesche UserId
        loesche cls.UserName

    def test_basic(self):
        self.assertIsInstance(UserId(5), int)
        self.assertIsInstance(self.UserName('Joe'), str)
        self.assertEqual(UserId(5) + 1, 6)

    def test_errors(self):
        mit self.assertRaises(TypeError):
            issubclass(UserId, int)
        mit self.assertRaises(TypeError):
            klasse D(UserId):
                pass

    def test_or(self):
        fuer cls in (int, self.UserName):
            mit self.subTest(cls=cls):
                self.assertEqual(UserId | cls, typing.Union[UserId, cls])
                self.assertEqual(cls | UserId, typing.Union[cls, UserId])

                self.assertEqual(typing.get_args(UserId | cls), (UserId, cls))
                self.assertEqual(typing.get_args(cls | UserId), (cls, UserId))

    def test_special_attrs(self):
        self.assertEqual(UserId.__name__, 'UserId')
        self.assertEqual(UserId.__qualname__, 'UserId')
        self.assertEqual(UserId.__module__, __name__)
        self.assertEqual(UserId.__supertype__, int)

        UserName = self.UserName
        self.assertEqual(UserName.__name__, 'UserName')
        self.assertEqual(UserName.__qualname__,
                         self.__class__.__qualname__ + '.UserName')
        self.assertEqual(UserName.__module__, __name__)
        self.assertEqual(UserName.__supertype__, str)

    def test_repr(self):
        self.assertEqual(repr(UserId), f'{__name__}.UserId')
        self.assertEqual(repr(self.UserName),
                         f'{__name__}.{self.__class__.__qualname__}.UserName')

    def test_pickle(self):
        UserAge = typing.NewType('UserAge', float)
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                pickled = pickle.dumps(UserId, proto)
                loaded = pickle.loads(pickled)
                self.assertIs(loaded, UserId)

                pickled = pickle.dumps(self.UserName, proto)
                loaded = pickle.loads(pickled)
                self.assertIs(loaded, self.UserName)

                mit self.assertRaises(pickle.PicklingError):
                    pickle.dumps(UserAge, proto)

    def test_missing__name__(self):
        code = ("import typing\n"
                "NT = typing.NewType('NT', int)\n"
                )
        exec(code, {})

    def test_error_message_when_subclassing(self):
        mit self.assertRaisesRegex(
            TypeError,
            re.escape(
                "Cannot subclass an instance of NewType. Perhaps you were looking for: "
                "`ProUserId = NewType('ProUserId', UserId)`"
            )
        ):
            klasse ProUserId(UserId):
                ...


klasse NamedTupleTests(BaseTestCase):
    klasse NestedEmployee(NamedTuple):
        name: str
        cool: int

    def test_basics(self):
        Emp = NamedTuple('Emp', [('name', str), ('id', int)])
        self.assertIsSubclass(Emp, tuple)
        joe = Emp('Joe', 42)
        jim = Emp(name='Jim', id=1)
        self.assertIsInstance(joe, Emp)
        self.assertIsInstance(joe, tuple)
        self.assertEqual(joe.name, 'Joe')
        self.assertEqual(joe.id, 42)
        self.assertEqual(jim.name, 'Jim')
        self.assertEqual(jim.id, 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp._fields, ('name', 'id'))
        self.assertEqual(Emp.__annotations__,
                         collections.OrderedDict([('name', str), ('id', int)]))

    def test_annotation_usage(self):
        tim = CoolEmployee('Tim', 9000)
        self.assertIsInstance(tim, CoolEmployee)
        self.assertIsInstance(tim, tuple)
        self.assertEqual(tim.name, 'Tim')
        self.assertEqual(tim.cool, 9000)
        self.assertEqual(CoolEmployee.__name__, 'CoolEmployee')
        self.assertEqual(CoolEmployee._fields, ('name', 'cool'))
        self.assertEqual(CoolEmployee.__annotations__,
                         collections.OrderedDict(name=str, cool=int))

    def test_annotation_usage_with_default(self):
        jelle = CoolEmployeeWithDefault('Jelle')
        self.assertIsInstance(jelle, CoolEmployeeWithDefault)
        self.assertIsInstance(jelle, tuple)
        self.assertEqual(jelle.name, 'Jelle')
        self.assertEqual(jelle.cool, 0)
        cooler_employee = CoolEmployeeWithDefault('Sjoerd', 1)
        self.assertEqual(cooler_employee.cool, 1)

        self.assertEqual(CoolEmployeeWithDefault.__name__, 'CoolEmployeeWithDefault')
        self.assertEqual(CoolEmployeeWithDefault._fields, ('name', 'cool'))
        self.assertEqual(CoolEmployeeWithDefault.__annotations__,
                         dict(name=str, cool=int))
        self.assertEqual(CoolEmployeeWithDefault._field_defaults, dict(cool=0))

        mit self.assertRaises(TypeError):
            klasse NonDefaultAfterDefault(NamedTuple):
                x: int = 3
                y: int

    def test_annotation_usage_with_methods(self):
        self.assertEqual(XMeth(1).double(), 2)
        self.assertEqual(XMeth(42).x, XMeth(42)[0])
        self.assertEqual(str(XRepr(42)), '42 -> 1')
        self.assertEqual(XRepr(1, 2) + XRepr(3), 0)

        mit self.assertRaises(AttributeError):
            klasse XMethBad(NamedTuple):
                x: int
                def _fields(self):
                    gib 'no chance fuer this'

        mit self.assertRaises(AttributeError):
            klasse XMethBad2(NamedTuple):
                x: int
                def _source(self):
                    gib 'no chance fuer this als well'

    def test_annotation_type_check(self):
        # These are rejected by _type_check
        mit self.assertRaises(TypeError):
            klasse X(NamedTuple):
                a: Final
        mit self.assertRaises(TypeError):
            klasse Y(NamedTuple):
                a: (1, 2)

        # Conversion by _type_convert
        klasse Z(NamedTuple):
            a: Nichts
            b: "str"
        annos = {'a': type(Nichts), 'b': EqualToForwardRef("str")}
        self.assertEqual(Z.__annotations__, annos)
        self.assertEqual(Z.__annotate__(annotationlib.Format.VALUE), annos)
        self.assertEqual(Z.__annotate__(annotationlib.Format.FORWARDREF), annos)
        self.assertEqual(Z.__annotate__(annotationlib.Format.STRING), {"a": "Nichts", "b": "str"})

    def test_future_annotations(self):
        code = """
        von __future__ importiere annotations
        von typing importiere NamedTuple
        klasse X(NamedTuple):
            a: int
            b: Nichts
        """
        ns = run_code(textwrap.dedent(code))
        X = ns['X']
        self.assertEqual(X.__annotations__, {'a': EqualToForwardRef("int"), 'b': EqualToForwardRef("Nichts")})

    def test_deferred_annotations(self):
        klasse X(NamedTuple):
            y: undefined

        self.assertEqual(X._fields, ('y',))
        mit self.assertRaises(NameError):
            X.__annotations__

        undefined = int
        self.assertEqual(X.__annotations__, {'y': int})

    def test_multiple_inheritance(self):
        klasse A:
            pass
        mit self.assertRaises(TypeError):
            klasse X(NamedTuple, A):
                x: int
        mit self.assertRaises(TypeError):
            klasse Y(NamedTuple, tuple):
                x: int
        mit self.assertRaises(TypeError):
            klasse Z(NamedTuple, NamedTuple):
                x: int
        klasse B(NamedTuple):
            x: int
        mit self.assertRaises(TypeError):
            klasse C(NamedTuple, B):
                y: str

    def test_generic(self):
        klasse X(NamedTuple, Generic[T]):
            x: T
        self.assertEqual(X.__bases__, (tuple, Generic))
        self.assertEqual(X.__orig_bases__, (NamedTuple, Generic[T]))
        self.assertEqual(X.__mro__, (X, tuple, Generic, object))

        klasse Y(Generic[T], NamedTuple):
            x: T
        self.assertEqual(Y.__bases__, (Generic, tuple))
        self.assertEqual(Y.__orig_bases__, (Generic[T], NamedTuple))
        self.assertEqual(Y.__mro__, (Y, Generic, tuple, object))

        fuer G in X, Y:
            mit self.subTest(type=G):
                self.assertEqual(G.__parameters__, (T,))
                self.assertEqual(G[T].__args__, (T,))
                self.assertEqual(get_args(G[T]), (T,))
                A = G[int]
                self.assertIs(A.__origin__, G)
                self.assertEqual(A.__args__, (int,))
                self.assertEqual(get_args(A), (int,))
                self.assertEqual(A.__parameters__, ())

                a = A(3)
                self.assertIs(type(a), G)
                self.assertEqual(a.x, 3)

                mit self.assertRaises(TypeError):
                    G[int, str]

    def test_generic_pep695(self):
        klasse X[T](NamedTuple):
            x: T
        T, = X.__type_params__
        self.assertIsInstance(T, TypeVar)
        self.assertEqual(T.__name__, 'T')
        self.assertEqual(X.__bases__, (tuple, Generic))
        self.assertEqual(X.__orig_bases__, (NamedTuple, Generic[T]))
        self.assertEqual(X.__mro__, (X, tuple, Generic, object))
        self.assertEqual(X.__parameters__, (T,))
        self.assertEqual(X[str].__args__, (str,))
        self.assertEqual(X[str].__parameters__, ())

    def test_non_generic_subscript(self):
        # For backward compatibility, subscription works
        # on arbitrary NamedTuple types.
        klasse Group(NamedTuple):
            key: T
            group: list[T]
        A = Group[int]
        self.assertEqual(A.__origin__, Group)
        self.assertEqual(A.__parameters__, ())
        self.assertEqual(A.__args__, (int,))
        a = A(1, [2])
        self.assertIs(type(a), Group)
        self.assertEqual(a, (1, [2]))

    def test_empty_namedtuple(self):
        mit self.assertRaisesRegex(TypeError, "missing.*required.*argument"):
            BAD = NamedTuple('BAD')

        NT1 = NamedTuple('NT1', {})
        NT2 = NamedTuple('NT2', ())
        NT3 = NamedTuple('NT3', [])

        klasse CNT(NamedTuple):
            pass  # empty body

        fuer struct in NT1, NT2, NT3, CNT:
            mit self.subTest(struct=struct):
                self.assertEqual(struct._fields, ())
                self.assertEqual(struct._field_defaults, {})
                self.assertEqual(struct.__annotations__, {})
                self.assertIsInstance(struct(), struct)

    def test_namedtuple_errors(self):
        mit self.assertRaises(TypeError):
            NamedTuple.__new__()
        mit self.assertRaisesRegex(TypeError, "object ist nicht iterable"):
            NamedTuple('Name', Nichts)

        mit self.assertRaisesRegex(
            TypeError,
            "missing 2 required positional arguments"
        ):
            NamedTuple()

        mit self.assertRaisesRegex(
            TypeError,
            "takes 2 positional arguments but 3 were given"
        ):
            NamedTuple('Emp', [('name', str)], Nichts)

        mit self.assertRaisesRegex(
            ValueError,
            "Field names cannot start mit an underscore"
        ):
            NamedTuple('Emp', [('_name', str)])

        mit self.assertRaisesRegex(
            TypeError,
            "got some positional-only arguments passed als keyword arguments"
        ):
            NamedTuple(typename='Emp', name=str, id=int)

        mit self.assertRaisesRegex(
            TypeError,
            "got an unexpected keyword argument"
        ):
            NamedTuple('Name', [('x', int)], y=str)

        mit self.assertRaisesRegex(
            TypeError,
            "got an unexpected keyword argument"
        ):
            NamedTuple('Name', [], y=str)

    def test_copy_and_pickle(self):
        global Emp  # pickle wants to reference the klasse by name
        Emp = NamedTuple('Emp', [('name', str), ('cool', int)])
        fuer cls in Emp, CoolEmployee, self.NestedEmployee:
            mit self.subTest(cls=cls):
                jane = cls('jane', 37)
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    z = pickle.dumps(jane, proto)
                    jane2 = pickle.loads(z)
                    self.assertEqual(jane2, jane)
                    self.assertIsInstance(jane2, cls)

                jane2 = copy(jane)
                self.assertEqual(jane2, jane)
                self.assertIsInstance(jane2, cls)

                jane2 = deepcopy(jane)
                self.assertEqual(jane2, jane)
                self.assertIsInstance(jane2, cls)

    def test_orig_bases(self):
        T = TypeVar('T')

        klasse SimpleNamedTuple(NamedTuple):
            pass

        klasse GenericNamedTuple(NamedTuple, Generic[T]):
            pass

        self.assertEqual(SimpleNamedTuple.__orig_bases__, (NamedTuple,))
        self.assertEqual(GenericNamedTuple.__orig_bases__, (NamedTuple, Generic[T]))

        CallNamedTuple = NamedTuple('CallNamedTuple', [])

        self.assertEqual(CallNamedTuple.__orig_bases__, (NamedTuple,))

    def test_setname_called_on_values_in_class_dictionary(self):
        klasse Vanilla:
            def __set_name__(self, owner, name):
                self.name = name

        klasse Foo(NamedTuple):
            attr = Vanilla()

        foo = Foo()
        self.assertEqual(len(foo), 0)
        self.assertNotIn('attr', Foo._fields)
        self.assertIsInstance(foo.attr, Vanilla)
        self.assertEqual(foo.attr.name, "attr")

        klasse Bar(NamedTuple):
            attr: Vanilla = Vanilla()

        bar = Bar()
        self.assertEqual(len(bar), 1)
        self.assertIn('attr', Bar._fields)
        self.assertIsInstance(bar.attr, Vanilla)
        self.assertEqual(bar.attr.name, "attr")

    def test_setname_raises_the_same_as_on_other_classes(self):
        klasse CustomException(BaseException): pass

        klasse Annoying:
            def __set_name__(self, owner, name):
                wirf CustomException

        annoying = Annoying()

        mit self.assertRaises(CustomException) als cm:
            klasse NormalClass:
                attr = annoying
        normal_exception = cm.exception

        mit self.assertRaises(CustomException) als cm:
            klasse NamedTupleClass(NamedTuple):
                attr = annoying
        namedtuple_exception = cm.exception

        self.assertIs(type(namedtuple_exception), CustomException)
        self.assertIs(type(namedtuple_exception), type(normal_exception))

        self.assertEqual(len(namedtuple_exception.__notes__), 1)
        self.assertEqual(
            len(namedtuple_exception.__notes__), len(normal_exception.__notes__)
        )

        expected_note = (
            "Error calling __set_name__ on 'Annoying' instance "
            "'attr' in 'NamedTupleClass'"
        )
        self.assertEqual(namedtuple_exception.__notes__[0], expected_note)
        self.assertEqual(
            namedtuple_exception.__notes__[0],
            normal_exception.__notes__[0].replace("NormalClass", "NamedTupleClass")
        )

    def test_strange_errors_when_accessing_set_name_itself(self):
        klasse CustomException(Exception): pass

        klasse Meta(type):
            def __getattribute__(self, attr):
                wenn attr == "__set_name__":
                    wirf CustomException
                gib object.__getattribute__(self, attr)

        klasse VeryAnnoying(metaclass=Meta): pass

        very_annoying = VeryAnnoying()

        mit self.assertRaises(CustomException):
            klasse Foo(NamedTuple):
                attr = very_annoying

    def test_super_explicitly_disallowed(self):
        expected_message = (
            "uses of super() und __class__ are unsupported "
            "in methods of NamedTuple subclasses"
        )

        mit self.assertRaises(TypeError, msg=expected_message):
            klasse ThisWontWork(NamedTuple):
                def __repr__(self):
                    gib super().__repr__()

        mit self.assertRaises(TypeError, msg=expected_message):
            klasse ThisWontWorkEither(NamedTuple):
                @property
                def name(self):
                    gib __class__.__name__


klasse TypedDictTests(BaseTestCase):
    def test_basics_functional_syntax(self):
        Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertIsSubclass(Emp, dict)
        self.assertIsSubclass(Emp, typing.MutableMapping)
        self.assertNotIsSubclass(Emp, collections.abc.Sequence)
        jim = Emp(name='Jim', id=1)
        self.assertIs(type(jim), dict)
        self.assertEqual(jim['name'], 'Jim')
        self.assertEqual(jim['id'], 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp.__module__, __name__)
        self.assertEqual(Emp.__bases__, (dict,))
        annos = {'name': str, 'id': int}
        self.assertEqual(Emp.__annotations__, annos)
        self.assertEqual(Emp.__annotate__(annotationlib.Format.VALUE), annos)
        self.assertEqual(Emp.__annotate__(annotationlib.Format.FORWARDREF), annos)
        self.assertEqual(Emp.__annotate__(annotationlib.Format.STRING), {'name': 'str', 'id': 'int'})
        self.assertEqual(Emp.__total__, Wahr)
        self.assertEqual(Emp.__required_keys__, {'name', 'id'})
        self.assertIsInstance(Emp.__required_keys__, frozenset)
        self.assertEqual(Emp.__optional_keys__, set())
        self.assertIsInstance(Emp.__optional_keys__, frozenset)

    def test_typeddict_create_errors(self):
        mit self.assertRaises(TypeError):
            TypedDict.__new__()
        mit self.assertRaises(TypeError):
            TypedDict()
        mit self.assertRaises(TypeError):
            TypedDict('Emp', [('name', str)], Nichts)
        mit self.assertRaises(TypeError):
            TypedDict(_typename='Emp')
        mit self.assertRaises(TypeError):
            TypedDict('Emp', name=str, id=int)

    def test_typeddict_errors(self):
        Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertEqual(TypedDict.__module__, 'typing')
        jim = Emp(name='Jim', id=1)
        mit self.assertRaises(TypeError):
            isinstance({}, Emp)
        mit self.assertRaises(TypeError):
            isinstance(jim, Emp)
        mit self.assertRaises(TypeError):
            issubclass(dict, Emp)
        mit self.assertRaises(TypeError):
            TypedDict('Hi', [('x', int)], y=int)

    def test_py36_class_syntax_usage(self):
        self.assertEqual(LabelPoint2D.__name__, 'LabelPoint2D')
        self.assertEqual(LabelPoint2D.__module__, __name__)
        self.assertEqual(LabelPoint2D.__annotations__, {'x': int, 'y': int, 'label': str})
        self.assertEqual(LabelPoint2D.__bases__, (dict,))
        self.assertEqual(LabelPoint2D.__total__, Wahr)
        self.assertNotIsSubclass(LabelPoint2D, typing.Sequence)
        not_origin = Point2D(x=0, y=1)
        self.assertEqual(not_origin['x'], 0)
        self.assertEqual(not_origin['y'], 1)
        other = LabelPoint2D(x=0, y=1, label='hi')
        self.assertEqual(other['label'], 'hi')

    def test_pickle(self):
        global EmpD  # pickle wants to reference the klasse by name
        EmpD = TypedDict('EmpD', {'name': str, 'id': int})
        jane = EmpD({'name': 'jane', 'id': 37})
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(jane, proto)
            jane2 = pickle.loads(z)
            self.assertEqual(jane2, jane)
            self.assertEqual(jane2, {'name': 'jane', 'id': 37})
            ZZ = pickle.dumps(EmpD, proto)
            EmpDnew = pickle.loads(ZZ)
            self.assertEqual(EmpDnew({'name': 'jane', 'id': 37}), jane)

    def test_pickle_generic(self):
        point = Point2DGeneric(a=5.0, b=3.0)
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(point, proto)
            point2 = pickle.loads(z)
            self.assertEqual(point2, point)
            self.assertEqual(point2, {'a': 5.0, 'b': 3.0})
            ZZ = pickle.dumps(Point2DGeneric, proto)
            Point2DGenericNew = pickle.loads(ZZ)
            self.assertEqual(Point2DGenericNew({'a': 5.0, 'b': 3.0}), point)

    def test_optional(self):
        EmpD = TypedDict('EmpD', {'name': str, 'id': int})

        self.assertEqual(typing.Optional[EmpD], typing.Union[Nichts, EmpD])
        self.assertNotEqual(typing.List[EmpD], typing.Tuple[EmpD])

    def test_total(self):
        D = TypedDict('D', {'x': int}, total=Falsch)
        self.assertEqual(D(), {})
        self.assertEqual(D(x=1), {'x': 1})
        self.assertEqual(D.__total__, Falsch)
        self.assertEqual(D.__required_keys__, frozenset())
        self.assertIsInstance(D.__required_keys__, frozenset)
        self.assertEqual(D.__optional_keys__, {'x'})
        self.assertIsInstance(D.__optional_keys__, frozenset)

        self.assertEqual(Options(), {})
        self.assertEqual(Options(log_level=2), {'log_level': 2})
        self.assertEqual(Options.__total__, Falsch)
        self.assertEqual(Options.__required_keys__, frozenset())
        self.assertEqual(Options.__optional_keys__, {'log_level', 'log_path'})

    def test_total_inherits_non_total(self):
        klasse TD1(TypedDict, total=Falsch):
            a: int

        self.assertIs(TD1.__total__, Falsch)

        klasse TD2(TD1):
            b: str

        self.assertIs(TD2.__total__, Wahr)

    def test_total_with_assigned_value(self):
        klasse TD(TypedDict):
            __total__ = "some_value"

        self.assertIs(TD.__total__, Wahr)

        klasse TD2(TypedDict, total=Wahr):
            __total__ = "some_value"

        self.assertIs(TD2.__total__, Wahr)

        klasse TD3(TypedDict, total=Falsch):
            __total__ = "some value"

        self.assertIs(TD3.__total__, Falsch)

    def test_optional_keys(self):
        klasse Point2Dor3D(Point2D, total=Falsch):
            z: int

        self.assertEqual(Point2Dor3D.__required_keys__, frozenset(['x', 'y']))
        self.assertIsInstance(Point2Dor3D.__required_keys__, frozenset)
        self.assertEqual(Point2Dor3D.__optional_keys__, frozenset(['z']))
        self.assertIsInstance(Point2Dor3D.__optional_keys__, frozenset)

    def test_keys_inheritance(self):
        klasse BaseAnimal(TypedDict):
            name: str

        klasse Animal(BaseAnimal, total=Falsch):
            voice: str
            tail: bool

        klasse Cat(Animal):
            fur_color: str

        self.assertEqual(BaseAnimal.__required_keys__, frozenset(['name']))
        self.assertEqual(BaseAnimal.__optional_keys__, frozenset([]))
        self.assertEqual(BaseAnimal.__annotations__, {'name': str})

        self.assertEqual(Animal.__required_keys__, frozenset(['name']))
        self.assertEqual(Animal.__optional_keys__, frozenset(['tail', 'voice']))
        self.assertEqual(Animal.__annotations__, {
            'name': str,
            'tail': bool,
            'voice': str,
        })

        self.assertEqual(Cat.__required_keys__, frozenset(['name', 'fur_color']))
        self.assertEqual(Cat.__optional_keys__, frozenset(['tail', 'voice']))
        self.assertEqual(Cat.__annotations__, {
            'fur_color': str,
            'name': str,
            'tail': bool,
            'voice': str,
        })

    def test_keys_inheritance_with_same_name(self):
        klasse NotTotal(TypedDict, total=Falsch):
            a: int

        klasse Total(NotTotal):
            a: int

        self.assertEqual(NotTotal.__required_keys__, frozenset())
        self.assertEqual(NotTotal.__optional_keys__, frozenset(['a']))
        self.assertEqual(Total.__required_keys__, frozenset(['a']))
        self.assertEqual(Total.__optional_keys__, frozenset())

        klasse Base(TypedDict):
            a: NotRequired[int]
            b: Required[int]

        klasse Child(Base):
            a: Required[int]
            b: NotRequired[int]

        self.assertEqual(Base.__required_keys__, frozenset(['b']))
        self.assertEqual(Base.__optional_keys__, frozenset(['a']))
        self.assertEqual(Child.__required_keys__, frozenset(['a']))
        self.assertEqual(Child.__optional_keys__, frozenset(['b']))

    def test_multiple_inheritance_with_same_key(self):
        klasse Base1(TypedDict):
            a: NotRequired[int]

        klasse Base2(TypedDict):
            a: Required[str]

        klasse Child(Base1, Base2):
            pass

        # Last base wins
        self.assertEqual(Child.__annotations__, {'a': Required[str]})
        self.assertEqual(Child.__required_keys__, frozenset(['a']))
        self.assertEqual(Child.__optional_keys__, frozenset())

    def test_inheritance_pep563(self):
        def _make_td(future, class_name, annos, base, extra_names=Nichts):
            lines = []
            wenn future:
                lines.append('from __future__ importiere annotations')
            lines.append('from typing importiere TypedDict')
            lines.append(f'class {class_name}({base}):')
            fuer name, anno in annos.items():
                lines.append(f'    {name}: {anno}')
            code = '\n'.join(lines)
            ns = run_code(code, extra_names)
            gib ns[class_name]

        fuer base_future in (Wahr, Falsch):
            fuer child_future in (Wahr, Falsch):
                mit self.subTest(base_future=base_future, child_future=child_future):
                    base = _make_td(
                        base_future, "Base", {"base": "int"}, "TypedDict"
                    )
                    self.assertIsNotNichts(base.__annotate__)
                    child = _make_td(
                        child_future, "Child", {"child": "int"}, "Base", {"Base": base}
                    )
                    base_anno = ForwardRef("int", module="builtins") wenn base_future sonst int
                    child_anno = ForwardRef("int", module="builtins") wenn child_future sonst int
                    self.assertEqual(base.__annotations__, {'base': base_anno})
                    self.assertEqual(
                        child.__annotations__, {'child': child_anno, 'base': base_anno}
                    )

    def test_required_notrequired_keys(self):
        self.assertEqual(NontotalMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(NontotalMovie.__optional_keys__,
                         frozenset({"year"}))

        self.assertEqual(TotalMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(TotalMovie.__optional_keys__,
                         frozenset({"year"}))

        self.assertEqual(_typed_dict_helper.VeryAnnotated.__required_keys__,
                         frozenset())
        self.assertEqual(_typed_dict_helper.VeryAnnotated.__optional_keys__,
                         frozenset({"a"}))

        self.assertEqual(AnnotatedMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(AnnotatedMovie.__optional_keys__,
                         frozenset({"year"}))

        self.assertEqual(WeirdlyQuotedMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(WeirdlyQuotedMovie.__optional_keys__,
                         frozenset({"year"}))

        self.assertEqual(ChildTotalMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(ChildTotalMovie.__optional_keys__,
                         frozenset({"year"}))

        self.assertEqual(ChildDeeplyAnnotatedMovie.__required_keys__,
                         frozenset({"title"}))
        self.assertEqual(ChildDeeplyAnnotatedMovie.__optional_keys__,
                         frozenset({"year"}))

    def test_multiple_inheritance(self):
        klasse One(TypedDict):
            one: int
        klasse Two(TypedDict):
            two: str
        klasse Untotal(TypedDict, total=Falsch):
            untotal: str
        Inline = TypedDict('Inline', {'inline': bool})
        klasse Regular:
            pass

        klasse Child(One, Two):
            child: bool
        self.assertEqual(
            Child.__required_keys__,
            frozenset(['one', 'two', 'child']),
        )
        self.assertEqual(
            Child.__optional_keys__,
            frozenset([]),
        )
        self.assertEqual(
            Child.__annotations__,
            {'one': int, 'two': str, 'child': bool},
        )

        klasse ChildWithOptional(One, Untotal):
            child: bool
        self.assertEqual(
            ChildWithOptional.__required_keys__,
            frozenset(['one', 'child']),
        )
        self.assertEqual(
            ChildWithOptional.__optional_keys__,
            frozenset(['untotal']),
        )
        self.assertEqual(
            ChildWithOptional.__annotations__,
            {'one': int, 'untotal': str, 'child': bool},
        )

        klasse ChildWithTotalFalsch(One, Untotal, total=Falsch):
            child: bool
        self.assertEqual(
            ChildWithTotalFalsch.__required_keys__,
            frozenset(['one']),
        )
        self.assertEqual(
            ChildWithTotalFalsch.__optional_keys__,
            frozenset(['untotal', 'child']),
        )
        self.assertEqual(
            ChildWithTotalFalsch.__annotations__,
            {'one': int, 'untotal': str, 'child': bool},
        )

        klasse ChildWithInlineAndOptional(Untotal, Inline):
            child: bool
        self.assertEqual(
            ChildWithInlineAndOptional.__required_keys__,
            frozenset(['inline', 'child']),
        )
        self.assertEqual(
            ChildWithInlineAndOptional.__optional_keys__,
            frozenset(['untotal']),
        )
        self.assertEqual(
            ChildWithInlineAndOptional.__annotations__,
            {'inline': bool, 'untotal': str, 'child': bool},
        )

        wrong_bases = [
            (One, Regular),
            (Regular, One),
            (One, Two, Regular),
            (Inline, Regular),
            (Untotal, Regular),
        ]
        fuer bases in wrong_bases:
            mit self.subTest(bases=bases):
                mit self.assertRaisesRegex(
                    TypeError,
                    'cannot inherit von both a TypedDict type und a non-TypedDict',
                ):
                    klasse Wrong(*bases):
                        pass

    def test_is_typeddict(self):
        self.assertIs(is_typeddict(Point2D), Wahr)
        self.assertIs(is_typeddict(Union[str, int]), Falsch)
        # classes, nicht instances
        self.assertIs(is_typeddict(Point2D()), Falsch)
        call_based = TypedDict('call_based', {'a': int})
        self.assertIs(is_typeddict(call_based), Wahr)
        self.assertIs(is_typeddict(call_based()), Falsch)

        T = TypeVar("T")
        klasse BarGeneric(TypedDict, Generic[T]):
            a: T
        self.assertIs(is_typeddict(BarGeneric), Wahr)
        self.assertIs(is_typeddict(BarGeneric[int]), Falsch)
        self.assertIs(is_typeddict(BarGeneric()), Falsch)

        klasse NewGeneric[T](TypedDict):
            a: T
        self.assertIs(is_typeddict(NewGeneric), Wahr)
        self.assertIs(is_typeddict(NewGeneric[int]), Falsch)
        self.assertIs(is_typeddict(NewGeneric()), Falsch)

        # The TypedDict constructor ist nicht itself a TypedDict
        self.assertIs(is_typeddict(TypedDict), Falsch)

    def test_get_type_hints(self):
        self.assertEqual(
            get_type_hints(Bar),
            {'a': typing.Optional[int], 'b': int}
        )

    def test_get_type_hints_generic(self):
        self.assertEqual(
            get_type_hints(BarGeneric),
            {'a': typing.Optional[T], 'b': int}
        )

        klasse FooBarGeneric(BarGeneric[int]):
            c: str

        self.assertEqual(
            get_type_hints(FooBarGeneric),
            {'a': typing.Optional[T], 'b': int, 'c': str}
        )

    def test_pep695_generic_typeddict(self):
        klasse A[T](TypedDict):
            a: T

        T, = A.__type_params__
        self.assertIsInstance(T, TypeVar)
        self.assertEqual(T.__name__, 'T')
        self.assertEqual(A.__bases__, (Generic, dict))
        self.assertEqual(A.__orig_bases__, (TypedDict, Generic[T]))
        self.assertEqual(A.__mro__, (A, Generic, dict, object))
        self.assertEqual(A.__annotations__, {'a': T})
        self.assertEqual(A.__annotate__(annotationlib.Format.STRING), {'a': 'T'})
        self.assertEqual(A.__parameters__, (T,))
        self.assertEqual(A[str].__parameters__, ())
        self.assertEqual(A[str].__args__, (str,))

    def test_generic_inheritance(self):
        klasse A(TypedDict, Generic[T]):
            a: T

        self.assertEqual(A.__bases__, (Generic, dict))
        self.assertEqual(A.__orig_bases__, (TypedDict, Generic[T]))
        self.assertEqual(A.__mro__, (A, Generic, dict, object))
        self.assertEqual(A.__annotations__, {'a': T})
        self.assertEqual(A.__annotate__(annotationlib.Format.STRING), {'a': 'T'})
        self.assertEqual(A.__parameters__, (T,))
        self.assertEqual(A[str].__parameters__, ())
        self.assertEqual(A[str].__args__, (str,))

        klasse A2(Generic[T], TypedDict):
            a: T

        self.assertEqual(A2.__bases__, (Generic, dict))
        self.assertEqual(A2.__orig_bases__, (Generic[T], TypedDict))
        self.assertEqual(A2.__mro__, (A2, Generic, dict, object))
        self.assertEqual(A2.__annotations__, {'a': T})
        self.assertEqual(A2.__annotate__(annotationlib.Format.STRING), {'a': 'T'})
        self.assertEqual(A2.__parameters__, (T,))
        self.assertEqual(A2[str].__parameters__, ())
        self.assertEqual(A2[str].__args__, (str,))

        klasse B(A[KT], total=Falsch):
            b: KT

        self.assertEqual(B.__bases__, (Generic, dict))
        self.assertEqual(B.__orig_bases__, (A[KT],))
        self.assertEqual(B.__mro__, (B, Generic, dict, object))
        self.assertEqual(B.__annotations__, {'a': T, 'b': KT})
        self.assertEqual(B.__annotate__(annotationlib.Format.STRING), {'a': 'T', 'b': 'KT'})
        self.assertEqual(B.__parameters__, (KT,))
        self.assertEqual(B.__total__, Falsch)
        self.assertEqual(B.__optional_keys__, frozenset(['b']))
        self.assertEqual(B.__required_keys__, frozenset(['a']))

        self.assertEqual(B[str].__parameters__, ())
        self.assertEqual(B[str].__args__, (str,))
        self.assertEqual(B[str].__origin__, B)

        klasse C(B[int]):
            c: int

        self.assertEqual(C.__bases__, (Generic, dict))
        self.assertEqual(C.__orig_bases__, (B[int],))
        self.assertEqual(C.__mro__, (C, Generic, dict, object))
        self.assertEqual(C.__parameters__, ())
        self.assertEqual(C.__total__, Wahr)
        self.assertEqual(C.__optional_keys__, frozenset(['b']))
        self.assertEqual(C.__required_keys__, frozenset(['a', 'c']))
        self.assertEqual(C.__annotations__, {
            'a': T,
            'b': KT,
            'c': int,
        })
        self.assertEqual(C.__annotate__(annotationlib.Format.STRING), {
            'a': 'T',
            'b': 'KT',
            'c': 'int',
        })
        mit self.assertRaises(TypeError):
            C[str]


        klasse Point3D(Point2DGeneric[T], Generic[T, KT]):
            c: KT

        self.assertEqual(Point3D.__bases__, (Generic, dict))
        self.assertEqual(Point3D.__orig_bases__, (Point2DGeneric[T], Generic[T, KT]))
        self.assertEqual(Point3D.__mro__, (Point3D, Generic, dict, object))
        self.assertEqual(Point3D.__parameters__, (T, KT))
        self.assertEqual(Point3D.__total__, Wahr)
        self.assertEqual(Point3D.__optional_keys__, frozenset())
        self.assertEqual(Point3D.__required_keys__, frozenset(['a', 'b', 'c']))
        self.assertEqual(Point3D.__annotations__, {
            'a': T,
            'b': T,
            'c': KT,
        })
        self.assertEqual(Point3D.__annotate__(annotationlib.Format.STRING), {
            'a': 'T',
            'b': 'T',
            'c': 'KT',
        })
        self.assertEqual(Point3D[int, str].__origin__, Point3D)

        mit self.assertRaises(TypeError):
            Point3D[int]

        mit self.assertRaises(TypeError):
            klasse Point3D(Point2DGeneric[T], Generic[KT]):
                c: KT

    def test_implicit_any_inheritance(self):
        klasse A(TypedDict, Generic[T]):
            a: T

        klasse B(A[KT], total=Falsch):
            b: KT

        klasse WithImplicitAny(B):
            c: int

        self.assertEqual(WithImplicitAny.__bases__, (Generic, dict,))
        self.assertEqual(WithImplicitAny.__mro__, (WithImplicitAny, Generic, dict, object))
        # Consistent mit GenericTests.test_implicit_any
        self.assertEqual(WithImplicitAny.__parameters__, ())
        self.assertEqual(WithImplicitAny.__total__, Wahr)
        self.assertEqual(WithImplicitAny.__optional_keys__, frozenset(['b']))
        self.assertEqual(WithImplicitAny.__required_keys__, frozenset(['a', 'c']))
        self.assertEqual(WithImplicitAny.__annotations__, {
            'a': T,
            'b': KT,
            'c': int,
        })
        self.assertEqual(WithImplicitAny.__annotate__(annotationlib.Format.STRING), {
            'a': 'T',
            'b': 'KT',
            'c': 'int',
        })
        mit self.assertRaises(TypeError):
            WithImplicitAny[str]

    def test_non_generic_subscript(self):
        # For backward compatibility, subscription works
        # on arbitrary TypedDict types.
        klasse TD(TypedDict):
            a: T
        A = TD[int]
        self.assertEqual(A.__origin__, TD)
        self.assertEqual(A.__parameters__, ())
        self.assertEqual(A.__args__, (int,))
        a = A(a = 1)
        self.assertIs(type(a), dict)
        self.assertEqual(a, {'a': 1})

    def test_orig_bases(self):
        T = TypeVar('T')

        klasse Parent(TypedDict):
            pass

        klasse Child(Parent):
            pass

        klasse OtherChild(Parent):
            pass

        klasse MixedChild(Child, OtherChild, Parent):
            pass

        klasse GenericParent(TypedDict, Generic[T]):
            pass

        klasse GenericChild(GenericParent[int]):
            pass

        klasse OtherGenericChild(GenericParent[str]):
            pass

        klasse MixedGenericChild(GenericChild, OtherGenericChild, GenericParent[float]):
            pass

        klasse MultipleGenericBases(GenericParent[int], GenericParent[float]):
            pass

        CallTypedDict = TypedDict('CallTypedDict', {})

        self.assertEqual(Parent.__orig_bases__, (TypedDict,))
        self.assertEqual(Child.__orig_bases__, (Parent,))
        self.assertEqual(OtherChild.__orig_bases__, (Parent,))
        self.assertEqual(MixedChild.__orig_bases__, (Child, OtherChild, Parent,))
        self.assertEqual(GenericParent.__orig_bases__, (TypedDict, Generic[T]))
        self.assertEqual(GenericChild.__orig_bases__, (GenericParent[int],))
        self.assertEqual(OtherGenericChild.__orig_bases__, (GenericParent[str],))
        self.assertEqual(MixedGenericChild.__orig_bases__, (GenericChild, OtherGenericChild, GenericParent[float]))
        self.assertEqual(MultipleGenericBases.__orig_bases__, (GenericParent[int], GenericParent[float]))
        self.assertEqual(CallTypedDict.__orig_bases__, (TypedDict,))

    def test_zero_fields_typeddicts(self):
        T1a = TypedDict("T1a", {})
        T1b = TypedDict("T1b", [])
        T1c = TypedDict("T1c", ())
        klasse T2(TypedDict): pass
        klasse T3[tvar](TypedDict): pass
        S = TypeVar("S")
        klasse T4(TypedDict, Generic[S]): pass

        fuer klass in T1a, T1b, T1c, T2, T3, T4:
            mit self.subTest(klass=klass.__name__):
                self.assertEqual(klass.__annotations__, {})
                self.assertEqual(klass.__required_keys__, set())
                self.assertEqual(klass.__optional_keys__, set())
                self.assertIsInstance(klass(), dict)

    def test_errors(self):
        mit self.assertRaisesRegex(TypeError, "missing 1 required.*argument"):
            TypedDict('TD')
        mit self.assertRaisesRegex(TypeError, "object ist nicht iterable"):
            TypedDict('TD', Nichts)

    def test_readonly_inheritance(self):
        klasse Base1(TypedDict):
            a: ReadOnly[int]

        klasse Child1(Base1):
            b: str

        self.assertEqual(Child1.__readonly_keys__, frozenset({'a'}))
        self.assertEqual(Child1.__mutable_keys__, frozenset({'b'}))

        klasse Base2(TypedDict):
            a: int

        klasse Child2(Base2):
            b: ReadOnly[str]

        self.assertEqual(Child2.__readonly_keys__, frozenset({'b'}))
        self.assertEqual(Child2.__mutable_keys__, frozenset({'a'}))

    def test_cannot_make_mutable_key_readonly(self):
        klasse Base(TypedDict):
            a: int

        mit self.assertRaises(TypeError):
            klasse Child(Base):
                a: ReadOnly[int]

    def test_can_make_readonly_key_mutable(self):
        klasse Base(TypedDict):
            a: ReadOnly[int]

        klasse Child(Base):
            a: int

        self.assertEqual(Child.__readonly_keys__, frozenset())
        self.assertEqual(Child.__mutable_keys__, frozenset({'a'}))

    def test_combine_qualifiers(self):
        klasse AllTheThings(TypedDict):
            a: Annotated[Required[ReadOnly[int]], "why not"]
            b: Required[Annotated[ReadOnly[int], "why not"]]
            c: ReadOnly[NotRequired[Annotated[int, "why not"]]]
            d: NotRequired[Annotated[int, "why not"]]

        self.assertEqual(AllTheThings.__required_keys__, frozenset({'a', 'b'}))
        self.assertEqual(AllTheThings.__optional_keys__, frozenset({'c', 'd'}))
        self.assertEqual(AllTheThings.__readonly_keys__, frozenset({'a', 'b', 'c'}))
        self.assertEqual(AllTheThings.__mutable_keys__, frozenset({'d'}))

        self.assertEqual(
            get_type_hints(AllTheThings, include_extras=Falsch),
            {'a': int, 'b': int, 'c': int, 'd': int},
        )
        self.assertEqual(
            get_type_hints(AllTheThings, include_extras=Wahr),
            {
                'a': Annotated[Required[ReadOnly[int]], 'why not'],
                'b': Required[Annotated[ReadOnly[int], 'why not']],
                'c': ReadOnly[NotRequired[Annotated[int, 'why not']]],
                'd': NotRequired[Annotated[int, 'why not']],
            },
        )

    def test_annotations(self):
        # _type_check ist applied
        mit self.assertRaisesRegex(TypeError, "Plain typing.Final ist nicht valid als type argument"):
            klasse X(TypedDict):
                a: Final

        # _type_convert ist applied
        klasse Y(TypedDict):
            a: Nichts
            b: "int"
        fwdref = EqualToForwardRef('int', module=__name__)
        self.assertEqual(Y.__annotations__, {'a': type(Nichts), 'b': fwdref})
        self.assertEqual(Y.__annotate__(annotationlib.Format.FORWARDREF), {'a': type(Nichts), 'b': fwdref})

        # _type_check ist also applied later
        klasse Z(TypedDict):
            a: undefined

        mit self.assertRaises(NameError):
            Z.__annotations__

        undefined = Final
        mit self.assertRaisesRegex(TypeError, "Plain typing.Final ist nicht valid als type argument"):
            Z.__annotations__

        undefined = Nichts
        self.assertEqual(Z.__annotations__, {'a': type(Nichts)})

    def test_deferred_evaluation(self):
        klasse A(TypedDict):
            x: NotRequired[undefined]
            y: ReadOnly[undefined]
            z: Required[undefined]

        self.assertEqual(A.__required_keys__, frozenset({'y', 'z'}))
        self.assertEqual(A.__optional_keys__, frozenset({'x'}))
        self.assertEqual(A.__readonly_keys__, frozenset({'y'}))
        self.assertEqual(A.__mutable_keys__, frozenset({'x', 'z'}))

        mit self.assertRaises(NameError):
            A.__annotations__

        self.assertEqual(
            A.__annotate__(annotationlib.Format.STRING),
            {'x': 'NotRequired[undefined]', 'y': 'ReadOnly[undefined]',
             'z': 'Required[undefined]'},
        )


klasse RequiredTests(BaseTestCase):

    def test_basics(self):
        mit self.assertRaises(TypeError):
            Required[NotRequired]
        mit self.assertRaises(TypeError):
            Required[int, str]
        mit self.assertRaises(TypeError):
            Required[int][str]

    def test_repr(self):
        self.assertEqual(repr(Required), 'typing.Required')
        cv = Required[int]
        self.assertEqual(repr(cv), 'typing.Required[int]')
        cv = Required[Employee]
        self.assertEqual(repr(cv), f'typing.Required[{__name__}.Employee]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(Required)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(Required[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.Required'):
            klasse E(Required):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.Required\[int\]'):
            klasse F(Required[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            Required()
        mit self.assertRaises(TypeError):
            type(Required)()
        mit self.assertRaises(TypeError):
            type(Required[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, Required[int])
        mit self.assertRaises(TypeError):
            issubclass(int, Required)


klasse NotRequiredTests(BaseTestCase):

    def test_basics(self):
        mit self.assertRaises(TypeError):
            NotRequired[Required]
        mit self.assertRaises(TypeError):
            NotRequired[int, str]
        mit self.assertRaises(TypeError):
            NotRequired[int][str]

    def test_repr(self):
        self.assertEqual(repr(NotRequired), 'typing.NotRequired')
        cv = NotRequired[int]
        self.assertEqual(repr(cv), 'typing.NotRequired[int]')
        cv = NotRequired[Employee]
        self.assertEqual(repr(cv), f'typing.NotRequired[{__name__}.Employee]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(NotRequired)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(NotRequired[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.NotRequired'):
            klasse E(NotRequired):
                pass
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.NotRequired\[int\]'):
            klasse F(NotRequired[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            NotRequired()
        mit self.assertRaises(TypeError):
            type(NotRequired)()
        mit self.assertRaises(TypeError):
            type(NotRequired[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, NotRequired[int])
        mit self.assertRaises(TypeError):
            issubclass(int, NotRequired)


klasse IOTests(BaseTestCase):

    def test_io(self):

        def stuff(a: IO) -> AnyStr:
            gib a.readline()

        a = stuff.__annotations__['a']
        self.assertEqual(a.__parameters__, (AnyStr,))

    def test_textio(self):

        def stuff(a: TextIO) -> str:
            gib a.readline()

        a = stuff.__annotations__['a']
        self.assertEqual(a.__parameters__, ())

    def test_binaryio(self):

        def stuff(a: BinaryIO) -> bytes:
            gib a.readline()

        a = stuff.__annotations__['a']
        self.assertEqual(a.__parameters__, ())


klasse RETests(BaseTestCase):
    # Much of this ist really testing _TypeAlias.

    def test_basics(self):
        pat = re.compile('[a-z]+', re.I)
        self.assertIsSubclass(pat.__class__, Pattern)
        self.assertIsSubclass(type(pat), Pattern)
        self.assertIsInstance(pat, Pattern)

        mat = pat.search('12345abcde.....')
        self.assertIsSubclass(mat.__class__, Match)
        self.assertIsSubclass(type(mat), Match)
        self.assertIsInstance(mat, Match)

        # these should just work
        Pattern[Union[str, bytes]]
        Match[Union[bytes, str]]

    def test_alias_equality(self):
        self.assertEqual(Pattern[str], Pattern[str])
        self.assertNotEqual(Pattern[str], Pattern[bytes])
        self.assertNotEqual(Pattern[str], Match[str])
        self.assertNotEqual(Pattern[str], str)

    def test_errors(self):
        m = Match[Union[str, bytes]]
        mit self.assertRaises(TypeError):
            m[str]
        mit self.assertRaises(TypeError):
            # We don't support isinstance().
            isinstance(42, Pattern[str])
        mit self.assertRaises(TypeError):
            # We don't support issubclass().
            issubclass(Pattern[bytes], Pattern[str])

    def test_repr(self):
        self.assertEqual(repr(Pattern), 'typing.Pattern')
        self.assertEqual(repr(Pattern[str]), 'typing.Pattern[str]')
        self.assertEqual(repr(Pattern[bytes]), 'typing.Pattern[bytes]')
        self.assertEqual(repr(Match), 'typing.Match')
        self.assertEqual(repr(Match[str]), 'typing.Match[str]')
        self.assertEqual(repr(Match[bytes]), 'typing.Match[bytes]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(
            TypeError,
            r"type 're\.Match' ist nicht an acceptable base type",
        ):
            klasse A(typing.Match):
                pass
        mit self.assertRaisesRegex(
            TypeError,
            r"type 're\.Pattern' ist nicht an acceptable base type",
        ):
            klasse B(typing.Pattern):
                pass


klasse AnnotatedTests(BaseTestCase):

    def test_new(self):
        mit self.assertRaisesRegex(
            TypeError, 'Cannot instantiate typing.Annotated',
        ):
            Annotated()

    def test_repr(self):
        self.assertEqual(
            repr(Annotated[int, 4, 5]),
            "typing.Annotated[int, 4, 5]"
        )
        self.assertEqual(
            repr(Annotated[List[int], 4, 5]),
            "typing.Annotated[typing.List[int], 4, 5]"
        )

    def test_dir(self):
        dir_items = set(dir(Annotated[int, 4]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
            '__metadata__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_flatten(self):
        A = Annotated[Annotated[int, 4], 5]
        self.assertEqual(A, Annotated[int, 4, 5])
        self.assertEqual(A.__metadata__, (4, 5))
        self.assertEqual(A.__origin__, int)

    def test_deduplicate_from_union(self):
        # Regular:
        self.assertEqual(get_args(Annotated[int, 1] | int),
                         (Annotated[int, 1], int))
        self.assertEqual(get_args(Union[Annotated[int, 1], int]),
                         (Annotated[int, 1], int))
        self.assertEqual(get_args(Annotated[int, 1] | Annotated[int, 2] | int),
                         (Annotated[int, 1], Annotated[int, 2], int))
        self.assertEqual(get_args(Union[Annotated[int, 1], Annotated[int, 2], int]),
                         (Annotated[int, 1], Annotated[int, 2], int))
        self.assertEqual(get_args(Annotated[int, 1] | Annotated[str, 1] | int),
                         (Annotated[int, 1], Annotated[str, 1], int))
        self.assertEqual(get_args(Union[Annotated[int, 1], Annotated[str, 1], int]),
                         (Annotated[int, 1], Annotated[str, 1], int))

        # Duplicates:
        self.assertEqual(Annotated[int, 1] | Annotated[int, 1] | int,
                         Annotated[int, 1] | int)
        self.assertEqual(Union[Annotated[int, 1], Annotated[int, 1], int],
                         Union[Annotated[int, 1], int])

        # Unhashable metadata:
        self.assertEqual(get_args(str | Annotated[int, {}] | Annotated[int, set()] | int),
                         (str, Annotated[int, {}], Annotated[int, set()], int))
        self.assertEqual(get_args(Union[str, Annotated[int, {}], Annotated[int, set()], int]),
                         (str, Annotated[int, {}], Annotated[int, set()], int))
        self.assertEqual(get_args(str | Annotated[int, {}] | Annotated[str, {}] | int),
                         (str, Annotated[int, {}], Annotated[str, {}], int))
        self.assertEqual(get_args(Union[str, Annotated[int, {}], Annotated[str, {}], int]),
                         (str, Annotated[int, {}], Annotated[str, {}], int))

        self.assertEqual(get_args(Annotated[int, 1] | str | Annotated[str, {}] | int),
                         (Annotated[int, 1], str, Annotated[str, {}], int))
        self.assertEqual(get_args(Union[Annotated[int, 1], str, Annotated[str, {}], int]),
                         (Annotated[int, 1], str, Annotated[str, {}], int))

        importiere dataclasses
        @dataclasses.dataclass
        klasse ValueRange:
            lo: int
            hi: int
        v = ValueRange(1, 2)
        self.assertEqual(get_args(Annotated[int, v] | Nichts),
                         (Annotated[int, v], types.NoneType))
        self.assertEqual(get_args(Union[Annotated[int, v], Nichts]),
                         (Annotated[int, v], types.NoneType))
        self.assertEqual(get_args(Optional[Annotated[int, v]]),
                         (Annotated[int, v], types.NoneType))

        # Unhashable metadata duplicated:
        self.assertEqual(Annotated[int, {}] | Annotated[int, {}] | int,
                         Annotated[int, {}] | int)
        self.assertEqual(Annotated[int, {}] | Annotated[int, {}] | int,
                         int | Annotated[int, {}])
        self.assertEqual(Union[Annotated[int, {}], Annotated[int, {}], int],
                         Union[Annotated[int, {}], int])
        self.assertEqual(Union[Annotated[int, {}], Annotated[int, {}], int],
                         Union[int, Annotated[int, {}]])

    def test_order_in_union(self):
        expr1 = Annotated[int, 1] | str | Annotated[str, {}] | int
        fuer args in itertools.permutations(get_args(expr1)):
            mit self.subTest(args=args):
                self.assertEqual(expr1, reduce(operator.or_, args))

        expr2 = Union[Annotated[int, 1], str, Annotated[str, {}], int]
        fuer args in itertools.permutations(get_args(expr2)):
            mit self.subTest(args=args):
                self.assertEqual(expr2, Union[args])

    def test_specialize(self):
        L = Annotated[List[T], "my decoration"]
        LI = Annotated[List[int], "my decoration"]
        self.assertEqual(L[int], Annotated[List[int], "my decoration"])
        self.assertEqual(L[int].__metadata__, ("my decoration",))
        self.assertEqual(L[int].__origin__, List[int])
        mit self.assertRaises(TypeError):
            LI[int]
        mit self.assertRaises(TypeError):
            L[int, float]

    def test_hash_eq(self):
        self.assertEqual(len({Annotated[int, 4, 5], Annotated[int, 4, 5]}), 1)
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[int, 5, 4])
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[str, 4, 5])
        self.assertNotEqual(Annotated[int, 4], Annotated[int, 4, 4])
        self.assertEqual(
            {Annotated[int, 4, 5], Annotated[int, 4, 5], Annotated[T, 4, 5]},
            {Annotated[int, 4, 5], Annotated[T, 4, 5]}
        )
        # Unhashable `metadata` raises `TypeError`:
        a1 = Annotated[int, []]
        mit self.assertRaises(TypeError):
            hash(a1)

        klasse A:
            __hash__ = Nichts
        a2 = Annotated[int, A()]
        mit self.assertRaises(TypeError):
            hash(a2)

    def test_instantiate(self):
        klasse C:
            classvar = 4

            def __init__(self, x):
                self.x = x

            def __eq__(self, other):
                wenn nicht isinstance(other, C):
                    gib NotImplemented
                gib other.x == self.x

        A = Annotated[C, "a decoration"]
        a = A(5)
        c = C(5)
        self.assertEqual(a, c)
        self.assertEqual(a.x, c.x)
        self.assertEqual(a.classvar, c.classvar)

    def test_instantiate_generic(self):
        MyCount = Annotated[typing.Counter[T], "my decoration"]
        self.assertEqual(MyCount([4, 4, 5]), {4: 2, 5: 1})
        self.assertEqual(MyCount[int]([4, 4, 5]), {4: 2, 5: 1})

    def test_instantiate_immutable(self):
        klasse C:
            def __setattr__(self, key, value):
                wirf Exception("should be ignored")

        A = Annotated[C, "a decoration"]
        # gh-115165: This used to cause RuntimeError to be raised
        # when we tried to set `__orig_class__` on the `C` instance
        # returned by the `A()` call
        self.assertIsInstance(A(), C)

    def test_cannot_instantiate_forward(self):
        A = Annotated["int", (5, 6)]
        mit self.assertRaises(TypeError):
            A(5)

    def test_cannot_instantiate_type_var(self):
        A = Annotated[T, (5, 6)]
        mit self.assertRaises(TypeError):
            A(5)

    def test_cannot_getattr_typevar(self):
        mit self.assertRaises(AttributeError):
            Annotated[T, (5, 7)].x

    def test_attr_passthrough(self):
        klasse C:
            classvar = 4

        A = Annotated[C, "a decoration"]
        self.assertEqual(A.classvar, 4)
        A.x = 5
        self.assertEqual(C.x, 5)

    def test_special_form_containment(self):
        klasse C:
            classvar: Annotated[ClassVar[int], "a decoration"] = 4
            const: Annotated[Final[int], "Const"] = 4

        self.assertEqual(get_type_hints(C, globals())['classvar'], ClassVar[int])
        self.assertEqual(get_type_hints(C, globals())['const'], Final[int])

    def test_special_forms_nesting(self):
        # These are uncommon types und are to ensure runtime
        # ist lax on validation. See gh-89547 fuer more context.
        klasse CF:
            x: ClassVar[Final[int]]

        klasse FC:
            x: Final[ClassVar[int]]

        klasse ACF:
            x: Annotated[ClassVar[Final[int]], "a decoration"]

        klasse CAF:
            x: ClassVar[Annotated[Final[int], "a decoration"]]

        klasse AFC:
            x: Annotated[Final[ClassVar[int]], "a decoration"]

        klasse FAC:
            x: Final[Annotated[ClassVar[int], "a decoration"]]

        self.assertEqual(get_type_hints(CF, globals())['x'], ClassVar[Final[int]])
        self.assertEqual(get_type_hints(FC, globals())['x'], Final[ClassVar[int]])
        self.assertEqual(get_type_hints(ACF, globals())['x'], ClassVar[Final[int]])
        self.assertEqual(get_type_hints(CAF, globals())['x'], ClassVar[Final[int]])
        self.assertEqual(get_type_hints(AFC, globals())['x'], Final[ClassVar[int]])
        self.assertEqual(get_type_hints(FAC, globals())['x'], Final[ClassVar[int]])

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, "Cannot subclass .*Annotated"):
            klasse C(Annotated):
                pass

    def test_cannot_check_instance(self):
        mit self.assertRaises(TypeError):
            isinstance(5, Annotated[int, "positive"])

    def test_cannot_check_subclass(self):
        mit self.assertRaises(TypeError):
            issubclass(int, Annotated[int, "positive"])

    def test_too_few_type_args(self):
        mit self.assertRaisesRegex(TypeError, 'at least two arguments'):
            Annotated[int]

    def test_pickle(self):
        samples = [typing.Any, typing.Union[int, str],
                   typing.Optional[str], Tuple[int, ...],
                   typing.Callable[[str], bytes]]

        fuer t in samples:
            x = Annotated[t, "a"]

            fuer prot in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(protocol=prot, type=t):
                    pickled = pickle.dumps(x, prot)
                    restored = pickle.loads(pickled)
                    self.assertEqual(x, restored)

        global _Annotated_test_G

        klasse _Annotated_test_G(Generic[T]):
            x = 1

        G = Annotated[_Annotated_test_G[int], "A decoration"]
        G.foo = 42
        G.bar = 'abc'

        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(G, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.x, 1)

    def test_subst(self):
        dec = "a decoration"
        dec2 = "another decoration"

        S = Annotated[T, dec2]
        self.assertEqual(S[int], Annotated[int, dec2])

        self.assertEqual(S[Annotated[int, dec]], Annotated[int, dec, dec2])
        L = Annotated[List[T], dec]

        self.assertEqual(L[int], Annotated[List[int], dec])
        mit self.assertRaises(TypeError):
            L[int, int]

        self.assertEqual(S[L[int]], Annotated[List[int], dec, dec2])

        D = Annotated[typing.Dict[KT, VT], dec]
        self.assertEqual(D[str, int], Annotated[typing.Dict[str, int], dec])
        mit self.assertRaises(TypeError):
            D[int]

        It = Annotated[int, dec]
        mit self.assertRaises(TypeError):
            It[Nichts]

        LI = L[int]
        mit self.assertRaises(TypeError):
            LI[Nichts]

    def test_typevar_subst(self):
        dec = "a decoration"
        Ts = TypeVarTuple('Ts')
        T = TypeVar('T')
        T1 = TypeVar('T1')
        T2 = TypeVar('T2')

        A = Annotated[tuple[*Ts], dec]
        self.assertEqual(A[int], Annotated[tuple[int], dec])
        self.assertEqual(A[str, int], Annotated[tuple[str, int], dec])
        mit self.assertRaises(TypeError):
            Annotated[*Ts, dec]

        B = Annotated[Tuple[Unpack[Ts]], dec]
        self.assertEqual(B[int], Annotated[Tuple[int], dec])
        self.assertEqual(B[str, int], Annotated[Tuple[str, int], dec])
        mit self.assertRaises(TypeError):
            Annotated[Unpack[Ts], dec]

        C = Annotated[tuple[T, *Ts], dec]
        self.assertEqual(C[int], Annotated[tuple[int], dec])
        self.assertEqual(C[int, str], Annotated[tuple[int, str], dec])
        self.assertEqual(
            C[int, str, float],
            Annotated[tuple[int, str, float], dec]
        )
        mit self.assertRaises(TypeError):
            C[()]

        D = Annotated[Tuple[T, Unpack[Ts]], dec]
        self.assertEqual(D[int], Annotated[Tuple[int], dec])
        self.assertEqual(D[int, str], Annotated[Tuple[int, str], dec])
        self.assertEqual(
            D[int, str, float],
            Annotated[Tuple[int, str, float], dec]
        )
        mit self.assertRaises(TypeError):
            D[()]

        E = Annotated[tuple[*Ts, T], dec]
        self.assertEqual(E[int], Annotated[tuple[int], dec])
        self.assertEqual(E[int, str], Annotated[tuple[int, str], dec])
        self.assertEqual(
            E[int, str, float],
            Annotated[tuple[int, str, float], dec]
        )
        mit self.assertRaises(TypeError):
            E[()]

        F = Annotated[Tuple[Unpack[Ts], T], dec]
        self.assertEqual(F[int], Annotated[Tuple[int], dec])
        self.assertEqual(F[int, str], Annotated[Tuple[int, str], dec])
        self.assertEqual(
            F[int, str, float],
            Annotated[Tuple[int, str, float], dec]
        )
        mit self.assertRaises(TypeError):
            F[()]

        G = Annotated[tuple[T1, *Ts, T2], dec]
        self.assertEqual(G[int, str], Annotated[tuple[int, str], dec])
        self.assertEqual(
            G[int, str, float],
            Annotated[tuple[int, str, float], dec]
        )
        self.assertEqual(
            G[int, str, bool, float],
            Annotated[tuple[int, str, bool, float], dec]
        )
        mit self.assertRaises(TypeError):
            G[int]

        H = Annotated[Tuple[T1, Unpack[Ts], T2], dec]
        self.assertEqual(H[int, str], Annotated[Tuple[int, str], dec])
        self.assertEqual(
            H[int, str, float],
            Annotated[Tuple[int, str, float], dec]
        )
        self.assertEqual(
            H[int, str, bool, float],
            Annotated[Tuple[int, str, bool, float], dec]
        )
        mit self.assertRaises(TypeError):
            H[int]

        # Now let's try creating an alias von an alias.

        Ts2 = TypeVarTuple('Ts2')
        T3 = TypeVar('T3')
        T4 = TypeVar('T4')

        # G ist Annotated[tuple[T1, *Ts, T2], dec].
        I = G[T3, *Ts2, T4]
        J = G[T3, Unpack[Ts2], T4]

        fuer x, y in [
            (I,                  Annotated[tuple[T3, *Ts2, T4], dec]),
            (J,                  Annotated[tuple[T3, Unpack[Ts2], T4], dec]),
            (I[int, str],        Annotated[tuple[int, str], dec]),
            (J[int, str],        Annotated[tuple[int, str], dec]),
            (I[int, str, float], Annotated[tuple[int, str, float], dec]),
            (J[int, str, float], Annotated[tuple[int, str, float], dec]),
            (I[int, str, bool, float],
                                 Annotated[tuple[int, str, bool, float], dec]),
            (J[int, str, bool, float],
                                 Annotated[tuple[int, str, bool, float], dec]),
        ]:
            self.assertEqual(x, y)

        mit self.assertRaises(TypeError):
            I[int]
        mit self.assertRaises(TypeError):
            J[int]

    def test_annotated_in_other_types(self):
        X = List[Annotated[T, 5]]
        self.assertEqual(X[int], List[Annotated[int, 5]])

    def test_annotated_mro(self):
        klasse X(Annotated[int, (1, 10)]): ...
        self.assertEqual(X.__mro__, (X, int, object),
                         "Annotated should be transparent.")

    def test_annotated_cached_with_types(self):
        klasse A(str): ...
        klasse B(str): ...

        field_a1 = Annotated[str, A("X")]
        field_a2 = Annotated[str, B("X")]
        a1_metadata = field_a1.__metadata__[0]
        a2_metadata = field_a2.__metadata__[0]

        self.assertIs(type(a1_metadata), A)
        self.assertEqual(a1_metadata, A("X"))
        self.assertIs(type(a2_metadata), B)
        self.assertEqual(a2_metadata, B("X"))
        self.assertIsNot(type(a1_metadata), type(a2_metadata))

        field_b1 = Annotated[str, A("Y")]
        field_b2 = Annotated[str, B("Y")]
        b1_metadata = field_b1.__metadata__[0]
        b2_metadata = field_b2.__metadata__[0]

        self.assertIs(type(b1_metadata), A)
        self.assertEqual(b1_metadata, A("Y"))
        self.assertIs(type(b2_metadata), B)
        self.assertEqual(b2_metadata, B("Y"))
        self.assertIsNot(type(b1_metadata), type(b2_metadata))

        field_c1 = Annotated[int, 1]
        field_c2 = Annotated[int, 1.0]
        field_c3 = Annotated[int, Wahr]

        self.assertIs(type(field_c1.__metadata__[0]), int)
        self.assertIs(type(field_c2.__metadata__[0]), float)
        self.assertIs(type(field_c3.__metadata__[0]), bool)


klasse TypeAliasTests(BaseTestCase):
    def test_canonical_usage_with_variable_annotation(self):
        Alias: TypeAlias = Employee

    def test_canonical_usage_with_type_comment(self):
        Alias = Employee  # type: TypeAlias

    def test_cannot_instantiate(self):
        mit self.assertRaises(TypeError):
            TypeAlias()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(42, TypeAlias)

    def test_stringized_usage(self):
        klasse A:
            a: "TypeAlias"
        self.assertEqual(get_type_hints(A), {'a': TypeAlias})

    def test_no_issubclass(self):
        mit self.assertRaises(TypeError):
            issubclass(Employee, TypeAlias)

        mit self.assertRaises(TypeError):
            issubclass(TypeAlias, Employee)

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError,
                r'Cannot subclass typing\.TypeAlias'):
            klasse C(TypeAlias):
                pass

        mit self.assertRaises(TypeError):
            klasse D(type(TypeAlias)):
                pass

    def test_repr(self):
        self.assertEqual(repr(TypeAlias), 'typing.TypeAlias')

    def test_cannot_subscript(self):
        mit self.assertRaises(TypeError):
            TypeAlias[int]


klasse ParamSpecTests(BaseTestCase):

    def test_basic_plain(self):
        P = ParamSpec('P')
        self.assertEqual(P, P)
        self.assertIsInstance(P, ParamSpec)
        self.assertEqual(P.__name__, 'P')
        self.assertEqual(P.__module__, __name__)

    def test_basic_with_exec(self):
        ns = {}
        exec('from typing importiere ParamSpec; P = ParamSpec("P")', ns, ns)
        P = ns['P']
        self.assertIsInstance(P, ParamSpec)
        self.assertEqual(P.__name__, 'P')
        self.assertIs(P.__module__, Nichts)

    def test_valid_uses(self):
        P = ParamSpec('P')
        T = TypeVar('T')
        C1 = Callable[P, int]
        self.assertEqual(C1.__args__, (P, int))
        self.assertEqual(C1.__parameters__, (P,))
        C2 = Callable[P, T]
        self.assertEqual(C2.__args__, (P, T))
        self.assertEqual(C2.__parameters__, (P, T))
        # Test collections.abc.Callable too.
        C3 = collections.abc.Callable[P, int]
        self.assertEqual(C3.__args__, (P, int))
        self.assertEqual(C3.__parameters__, (P,))
        C4 = collections.abc.Callable[P, T]
        self.assertEqual(C4.__args__, (P, T))
        self.assertEqual(C4.__parameters__, (P, T))

    def test_args_kwargs(self):
        P = ParamSpec('P')
        P_2 = ParamSpec('P_2')
        self.assertIn('args', dir(P))
        self.assertIn('kwargs', dir(P))
        self.assertIsInstance(P.args, ParamSpecArgs)
        self.assertIsInstance(P.kwargs, ParamSpecKwargs)
        self.assertIs(P.args.__origin__, P)
        self.assertIs(P.kwargs.__origin__, P)
        self.assertEqual(P.args, P.args)
        self.assertEqual(P.kwargs, P.kwargs)
        self.assertNotEqual(P.args, P_2.args)
        self.assertNotEqual(P.kwargs, P_2.kwargs)
        self.assertNotEqual(P.args, P.kwargs)
        self.assertNotEqual(P.kwargs, P.args)
        self.assertNotEqual(P.args, P_2.kwargs)
        self.assertEqual(repr(P.args), "P.args")
        self.assertEqual(repr(P.kwargs), "P.kwargs")

    def test_stringized(self):
        P = ParamSpec('P')
        klasse C(Generic[P]):
            func: Callable["P", int]
            def foo(self, *args: "P.args", **kwargs: "P.kwargs"):
                pass

        self.assertEqual(gth(C, globals(), locals()), {"func": Callable[P, int]})
        self.assertEqual(
            gth(C.foo, globals(), locals()), {"args": P.args, "kwargs": P.kwargs}
        )

    def test_user_generics(self):
        T = TypeVar("T")
        P = ParamSpec("P")
        P_2 = ParamSpec("P_2")

        klasse X(Generic[T, P]):
            f: Callable[P, int]
            x: T
        G1 = X[int, P_2]
        self.assertEqual(G1.__args__, (int, P_2))
        self.assertEqual(G1.__parameters__, (P_2,))
        mit self.assertRaisesRegex(TypeError, "few arguments for"):
            X[int]
        mit self.assertRaisesRegex(TypeError, "many arguments for"):
            X[int, P_2, str]

        G2 = X[int, Concatenate[int, P_2]]
        self.assertEqual(G2.__args__, (int, Concatenate[int, P_2]))
        self.assertEqual(G2.__parameters__, (P_2,))

        G3 = X[int, [int, bool]]
        self.assertEqual(G3.__args__, (int, (int, bool)))
        self.assertEqual(G3.__parameters__, ())

        G4 = X[int, ...]
        self.assertEqual(G4.__args__, (int, Ellipsis))
        self.assertEqual(G4.__parameters__, ())

        klasse Z(Generic[P]):
            f: Callable[P, int]

        G5 = Z[[int, str, bool]]
        self.assertEqual(G5.__args__, ((int, str, bool),))
        self.assertEqual(G5.__parameters__, ())

        G6 = Z[int, str, bool]
        self.assertEqual(G6.__args__, ((int, str, bool),))
        self.assertEqual(G6.__parameters__, ())

        # G5 und G6 should be equivalent according to the PEP
        self.assertEqual(G5.__args__, G6.__args__)
        self.assertEqual(G5.__origin__, G6.__origin__)
        self.assertEqual(G5.__parameters__, G6.__parameters__)
        self.assertEqual(G5, G6)

        G7 = Z[int]
        self.assertEqual(G7.__args__, ((int,),))
        self.assertEqual(G7.__parameters__, ())

        mit self.assertRaisesRegex(TypeError, "many arguments for"):
            Z[[int, str], bool]
        mit self.assertRaisesRegex(TypeError, "many arguments for"):
            Z[P_2, bool]

    def test_multiple_paramspecs_in_user_generics(self):
        P = ParamSpec("P")
        P2 = ParamSpec("P2")

        klasse X(Generic[P, P2]):
            f: Callable[P, int]
            g: Callable[P2, str]

        G1 = X[[int, str], [bytes]]
        G2 = X[[int], [str, bytes]]
        self.assertNotEqual(G1, G2)
        self.assertEqual(G1.__args__, ((int, str), (bytes,)))
        self.assertEqual(G2.__args__, ((int,), (str, bytes)))

    def test_typevartuple_and_paramspecs_in_user_generics(self):
        Ts = TypeVarTuple("Ts")
        P = ParamSpec("P")

        klasse X(Generic[*Ts, P]):
            f: Callable[P, int]
            g: Tuple[*Ts]

        G1 = X[int, [bytes]]
        self.assertEqual(G1.__args__, (int, (bytes,)))
        G2 = X[int, str, [bytes]]
        self.assertEqual(G2.__args__, (int, str, (bytes,)))
        G3 = X[[bytes]]
        self.assertEqual(G3.__args__, ((bytes,),))
        G4 = X[[]]
        self.assertEqual(G4.__args__, ((),))
        mit self.assertRaises(TypeError):
            X[()]

        klasse Y(Generic[P, *Ts]):
            f: Callable[P, int]
            g: Tuple[*Ts]

        G1 = Y[[bytes], int]
        self.assertEqual(G1.__args__, ((bytes,), int))
        G2 = Y[[bytes], int, str]
        self.assertEqual(G2.__args__, ((bytes,), int, str))
        G3 = Y[[bytes]]
        self.assertEqual(G3.__args__, ((bytes,),))
        G4 = Y[[]]
        self.assertEqual(G4.__args__, ((),))
        mit self.assertRaises(TypeError):
            Y[()]

    def test_typevartuple_and_paramspecs_in_generic_aliases(self):
        P = ParamSpec('P')
        T = TypeVar('T')
        Ts = TypeVarTuple('Ts')

        fuer C in Callable, collections.abc.Callable:
            mit self.subTest(generic=C):
                A = C[P, Tuple[*Ts]]
                B = A[[int, str], bytes, float]
                self.assertEqual(B.__args__, (int, str, Tuple[bytes, float]))

        klasse X(Generic[T, P]):
            pass

        A = X[Tuple[*Ts], P]
        B = A[bytes, float, [int, str]]
        self.assertEqual(B.__args__, (Tuple[bytes, float], (int, str,)))

        klasse Y(Generic[P, T]):
            pass

        A = Y[P, Tuple[*Ts]]
        B = A[[int, str], bytes, float]
        self.assertEqual(B.__args__, ((int, str,), Tuple[bytes, float]))

    def test_var_substitution(self):
        P = ParamSpec("P")
        subst = P.__typing_subst__
        self.assertEqual(subst((int, str)), (int, str))
        self.assertEqual(subst([int, str]), (int, str))
        self.assertEqual(subst([Nichts]), (type(Nichts),))
        self.assertIs(subst(...), ...)
        self.assertIs(subst(P), P)
        self.assertEqual(subst(Concatenate[int, P]), Concatenate[int, P])

    def test_bad_var_substitution(self):
        T = TypeVar('T')
        P = ParamSpec('P')
        bad_args = (42, int, Nichts, T, int|str, Union[int, str])
        fuer arg in bad_args:
            mit self.subTest(arg=arg):
                mit self.assertRaises(TypeError):
                    P.__typing_subst__(arg)
                mit self.assertRaises(TypeError):
                    typing.Callable[P, T][arg, str]
                mit self.assertRaises(TypeError):
                    collections.abc.Callable[P, T][arg, str]

    def test_type_var_subst_for_other_type_vars(self):
        T = TypeVar('T')
        T2 = TypeVar('T2')
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        Ts = TypeVarTuple('Ts')

        klasse Base(Generic[P]):
            pass

        A1 = Base[T]
        self.assertEqual(A1.__parameters__, (T,))
        self.assertEqual(A1.__args__, ((T,),))
        self.assertEqual(A1[int], Base[int])

        A2 = Base[[T]]
        self.assertEqual(A2.__parameters__, (T,))
        self.assertEqual(A2.__args__, ((T,),))
        self.assertEqual(A2[int], Base[int])

        A3 = Base[[int, T]]
        self.assertEqual(A3.__parameters__, (T,))
        self.assertEqual(A3.__args__, ((int, T),))
        self.assertEqual(A3[str], Base[[int, str]])

        A4 = Base[[T, int, T2]]
        self.assertEqual(A4.__parameters__, (T, T2))
        self.assertEqual(A4.__args__, ((T, int, T2),))
        self.assertEqual(A4[str, bool], Base[[str, int, bool]])

        A5 = Base[[*Ts, int]]
        self.assertEqual(A5.__parameters__, (Ts,))
        self.assertEqual(A5.__args__, ((*Ts, int),))
        self.assertEqual(A5[str, bool], Base[[str, bool, int]])

        A5_2 = Base[[int, *Ts]]
        self.assertEqual(A5_2.__parameters__, (Ts,))
        self.assertEqual(A5_2.__args__, ((int, *Ts),))
        self.assertEqual(A5_2[str, bool], Base[[int, str, bool]])

        A6 = Base[[T, *Ts]]
        self.assertEqual(A6.__parameters__, (T, Ts))
        self.assertEqual(A6.__args__, ((T, *Ts),))
        self.assertEqual(A6[int, str, bool], Base[[int, str, bool]])

        A7 = Base[[T, T]]
        self.assertEqual(A7.__parameters__, (T,))
        self.assertEqual(A7.__args__, ((T, T),))
        self.assertEqual(A7[int], Base[[int, int]])

        A8 = Base[[T, list[T]]]
        self.assertEqual(A8.__parameters__, (T,))
        self.assertEqual(A8.__args__, ((T, list[T]),))
        self.assertEqual(A8[int], Base[[int, list[int]]])

        A9 = Base[[Tuple[*Ts], *Ts]]
        self.assertEqual(A9.__parameters__, (Ts,))
        self.assertEqual(A9.__args__, ((Tuple[*Ts], *Ts),))
        self.assertEqual(A9[int, str], Base[Tuple[int, str], int, str])

        A10 = Base[P2]
        self.assertEqual(A10.__parameters__, (P2,))
        self.assertEqual(A10.__args__, (P2,))
        self.assertEqual(A10[[int, str]], Base[[int, str]])

        klasse DoubleP(Generic[P, P2]):
            pass

        B1 = DoubleP[P, P2]
        self.assertEqual(B1.__parameters__, (P, P2))
        self.assertEqual(B1.__args__, (P, P2))
        self.assertEqual(B1[[int, str], [bool]], DoubleP[[int,  str], [bool]])
        self.assertEqual(B1[[], []], DoubleP[[], []])

        B2 = DoubleP[[int, str], P2]
        self.assertEqual(B2.__parameters__, (P2,))
        self.assertEqual(B2.__args__, ((int, str), P2))
        self.assertEqual(B2[[bool, bool]], DoubleP[[int,  str], [bool, bool]])
        self.assertEqual(B2[[]], DoubleP[[int,  str], []])

        B3 = DoubleP[P, [bool, bool]]
        self.assertEqual(B3.__parameters__, (P,))
        self.assertEqual(B3.__args__, (P, (bool, bool)))
        self.assertEqual(B3[[int, str]], DoubleP[[int,  str], [bool, bool]])
        self.assertEqual(B3[[]], DoubleP[[], [bool, bool]])

        B4 = DoubleP[[T, int], [bool, T2]]
        self.assertEqual(B4.__parameters__, (T, T2))
        self.assertEqual(B4.__args__, ((T, int), (bool, T2)))
        self.assertEqual(B4[str, float], DoubleP[[str, int], [bool, float]])

        B5 = DoubleP[[*Ts, int], [bool, T2]]
        self.assertEqual(B5.__parameters__, (Ts, T2))
        self.assertEqual(B5.__args__, ((*Ts, int), (bool, T2)))
        self.assertEqual(B5[str, bytes, float],
                         DoubleP[[str, bytes, int], [bool, float]])

        B6 = DoubleP[[T, int], [bool, *Ts]]
        self.assertEqual(B6.__parameters__, (T, Ts))
        self.assertEqual(B6.__args__, ((T, int), (bool, *Ts)))
        self.assertEqual(B6[str, bytes, float],
                         DoubleP[[str, int], [bool, bytes, float]])

        klasse PandT(Generic[P, T]):
            pass

        C1 = PandT[P, T]
        self.assertEqual(C1.__parameters__, (P, T))
        self.assertEqual(C1.__args__, (P, T))
        self.assertEqual(C1[[int, str], bool], PandT[[int, str], bool])

        C2 = PandT[[int, T], T]
        self.assertEqual(C2.__parameters__, (T,))
        self.assertEqual(C2.__args__, ((int, T), T))
        self.assertEqual(C2[str], PandT[[int, str], str])

        C3 = PandT[[int, *Ts], T]
        self.assertEqual(C3.__parameters__, (Ts, T))
        self.assertEqual(C3.__args__, ((int, *Ts), T))
        self.assertEqual(C3[str, bool, bytes], PandT[[int, str, bool], bytes])

    def test_paramspec_in_nested_generics(self):
        # Although ParamSpec should nicht be found in __parameters__ of most
        # generics, they probably should be found when nested in
        # a valid location.
        T = TypeVar("T")
        P = ParamSpec("P")
        C1 = Callable[P, T]
        G1 = List[C1]
        G2 = list[C1]
        G3 = list[C1] | int
        self.assertEqual(G1.__parameters__, (P, T))
        self.assertEqual(G2.__parameters__, (P, T))
        self.assertEqual(G3.__parameters__, (P, T))
        C = Callable[[int, str], float]
        self.assertEqual(G1[[int, str], float], List[C])
        self.assertEqual(G2[[int, str], float], list[C])
        self.assertEqual(G3[[int, str], float], list[C] | int)

    def test_paramspec_gets_copied(self):
        # bpo-46581
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        C1 = Callable[P, int]
        self.assertEqual(C1.__parameters__, (P,))
        self.assertEqual(C1[P2].__parameters__, (P2,))
        self.assertEqual(C1[str].__parameters__, ())
        self.assertEqual(C1[str, T].__parameters__, (T,))
        self.assertEqual(C1[Concatenate[str, P2]].__parameters__, (P2,))
        self.assertEqual(C1[Concatenate[T, P2]].__parameters__, (T, P2))
        self.assertEqual(C1[...].__parameters__, ())

        C2 = Callable[Concatenate[str, P], int]
        self.assertEqual(C2.__parameters__, (P,))
        self.assertEqual(C2[P2].__parameters__, (P2,))
        self.assertEqual(C2[str].__parameters__, ())
        self.assertEqual(C2[str, T].__parameters__, (T,))
        self.assertEqual(C2[Concatenate[str, P2]].__parameters__, (P2,))
        self.assertEqual(C2[Concatenate[T, P2]].__parameters__, (T, P2))

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, NOT_A_BASE_TYPE % 'ParamSpec'):
            klasse C(ParamSpec): pass
        mit self.assertRaisesRegex(TypeError, NOT_A_BASE_TYPE % 'ParamSpecArgs'):
            klasse D(ParamSpecArgs): pass
        mit self.assertRaisesRegex(TypeError, NOT_A_BASE_TYPE % 'ParamSpecKwargs'):
            klasse E(ParamSpecKwargs): pass
        P = ParamSpec('P')
        mit self.assertRaisesRegex(TypeError,
                CANNOT_SUBCLASS_INSTANCE % 'ParamSpec'):
            klasse F(P): pass
        mit self.assertRaisesRegex(TypeError,
                CANNOT_SUBCLASS_INSTANCE % 'ParamSpecArgs'):
            klasse G(P.args): pass
        mit self.assertRaisesRegex(TypeError,
                CANNOT_SUBCLASS_INSTANCE % 'ParamSpecKwargs'):
            klasse H(P.kwargs): pass


klasse ConcatenateTests(BaseTestCase):
    def test_basics(self):
        P = ParamSpec('P')
        klasse MyClass: ...
        c = Concatenate[MyClass, P]
        self.assertNotEqual(c, Concatenate)

    def test_dir(self):
        P = ParamSpec('P')
        dir_items = set(dir(Concatenate[int, P]))
        fuer required_item in [
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)

    def test_valid_uses(self):
        P = ParamSpec('P')
        T = TypeVar('T')
        C1 = Callable[Concatenate[int, P], int]
        self.assertEqual(C1.__args__, (Concatenate[int, P], int))
        self.assertEqual(C1.__parameters__, (P,))
        C2 = Callable[Concatenate[int, T, P], T]
        self.assertEqual(C2.__args__, (Concatenate[int, T, P], T))
        self.assertEqual(C2.__parameters__, (T, P))

        # Test collections.abc.Callable too.
        C3 = collections.abc.Callable[Concatenate[int, P], int]
        self.assertEqual(C3.__args__, (Concatenate[int, P], int))
        self.assertEqual(C3.__parameters__, (P,))
        C4 = collections.abc.Callable[Concatenate[int, T, P], T]
        self.assertEqual(C4.__args__, (Concatenate[int, T, P], T))
        self.assertEqual(C4.__parameters__, (T, P))

    def test_invalid_uses(self):
        mit self.assertRaisesRegex(TypeError, 'Concatenate of no types'):
            Concatenate[()]
        mit self.assertRaisesRegex(
            TypeError,
            (
                'The last parameter to Concatenate should be a '
                'ParamSpec variable oder ellipsis'
            ),
        ):
            Concatenate[int]

    def test_var_substitution(self):
        T = TypeVar('T')
        P = ParamSpec('P')
        P2 = ParamSpec('P2')
        C = Concatenate[T, P]
        self.assertEqual(C[int, P2], Concatenate[int, P2])
        self.assertEqual(C[int, [str, float]], (int, str, float))
        self.assertEqual(C[int, []], (int,))
        self.assertEqual(C[int, Concatenate[str, P2]],
                         Concatenate[int, str, P2])
        self.assertEqual(C[int, ...], Concatenate[int, ...])

        C = Concatenate[int, P]
        self.assertEqual(C[P2], Concatenate[int, P2])
        self.assertEqual(C[[str, float]], (int, str, float))
        self.assertEqual(C[str, float], (int, str, float))
        self.assertEqual(C[[]], (int,))
        self.assertEqual(C[Concatenate[str, P2]], Concatenate[int, str, P2])
        self.assertEqual(C[...], Concatenate[int, ...])


klasse TypeGuardTests(BaseTestCase):
    def test_basics(self):
        TypeGuard[int]  # OK

        def foo(arg) -> TypeGuard[int]: ...
        self.assertEqual(gth(foo), {'return': TypeGuard[int]})

        mit self.assertRaises(TypeError):
            TypeGuard[int, str]

    def test_repr(self):
        self.assertEqual(repr(TypeGuard), 'typing.TypeGuard')
        cv = TypeGuard[int]
        self.assertEqual(repr(cv), 'typing.TypeGuard[int]')
        cv = TypeGuard[Employee]
        self.assertEqual(repr(cv), 'typing.TypeGuard[%s.Employee]' % __name__)
        cv = TypeGuard[tuple[int]]
        self.assertEqual(repr(cv), 'typing.TypeGuard[tuple[int]]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(TypeGuard)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(TypeGuard[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.TypeGuard'):
            klasse E(TypeGuard):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.TypeGuard\[int\]'):
            klasse F(TypeGuard[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            TypeGuard()
        mit self.assertRaises(TypeError):
            type(TypeGuard)()
        mit self.assertRaises(TypeError):
            type(TypeGuard[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, TypeGuard[int])
        mit self.assertRaises(TypeError):
            issubclass(int, TypeGuard)


klasse TypeIsTests(BaseTestCase):
    def test_basics(self):
        TypeIs[int]  # OK

        def foo(arg) -> TypeIs[int]: ...
        self.assertEqual(gth(foo), {'return': TypeIs[int]})

        mit self.assertRaises(TypeError):
            TypeIs[int, str]

    def test_repr(self):
        self.assertEqual(repr(TypeIs), 'typing.TypeIs')
        cv = TypeIs[int]
        self.assertEqual(repr(cv), 'typing.TypeIs[int]')
        cv = TypeIs[Employee]
        self.assertEqual(repr(cv), 'typing.TypeIs[%s.Employee]' % __name__)
        cv = TypeIs[tuple[int]]
        self.assertEqual(repr(cv), 'typing.TypeIs[tuple[int]]')

    def test_cannot_subclass(self):
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse C(type(TypeIs)):
                pass
        mit self.assertRaisesRegex(TypeError, CANNOT_SUBCLASS_TYPE):
            klasse D(type(TypeIs[int])):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.TypeIs'):
            klasse E(TypeIs):
                pass
        mit self.assertRaisesRegex(TypeError,
                                    r'Cannot subclass typing\.TypeIs\[int\]'):
            klasse F(TypeIs[int]):
                pass

    def test_cannot_init(self):
        mit self.assertRaises(TypeError):
            TypeIs()
        mit self.assertRaises(TypeError):
            type(TypeIs)()
        mit self.assertRaises(TypeError):
            type(TypeIs[Optional[int]])()

    def test_no_isinstance(self):
        mit self.assertRaises(TypeError):
            isinstance(1, TypeIs[int])
        mit self.assertRaises(TypeError):
            issubclass(int, TypeIs)


SpecialAttrsP = typing.ParamSpec('SpecialAttrsP')
SpecialAttrsT = typing.TypeVar('SpecialAttrsT', int, float, complex)


klasse SpecialAttrsTests(BaseTestCase):

    def test_special_attrs(self):
        cls_to_check = {
            # ABC classes
            typing.AbstractSet: 'AbstractSet',
            typing.AsyncContextManager: 'AsyncContextManager',
            typing.AsyncGenerator: 'AsyncGenerator',
            typing.AsyncIterable: 'AsyncIterable',
            typing.AsyncIterator: 'AsyncIterator',
            typing.Awaitable: 'Awaitable',
            typing.Callable: 'Callable',
            typing.ChainMap: 'ChainMap',
            typing.Collection: 'Collection',
            typing.Container: 'Container',
            typing.ContextManager: 'ContextManager',
            typing.Coroutine: 'Coroutine',
            typing.Counter: 'Counter',
            typing.DefaultDict: 'DefaultDict',
            typing.Deque: 'Deque',
            typing.Dict: 'Dict',
            typing.FrozenSet: 'FrozenSet',
            typing.Generator: 'Generator',
            typing.Hashable: 'Hashable',
            typing.ItemsView: 'ItemsView',
            typing.Iterable: 'Iterable',
            typing.Iterator: 'Iterator',
            typing.KeysView: 'KeysView',
            typing.List: 'List',
            typing.Mapping: 'Mapping',
            typing.MappingView: 'MappingView',
            typing.MutableMapping: 'MutableMapping',
            typing.MutableSequence: 'MutableSequence',
            typing.MutableSet: 'MutableSet',
            typing.OrderedDict: 'OrderedDict',
            typing.Reversible: 'Reversible',
            typing.Sequence: 'Sequence',
            typing.Set: 'Set',
            typing.Sized: 'Sized',
            typing.Tuple: 'Tuple',
            typing.Type: 'Type',
            typing.ValuesView: 'ValuesView',
            # Subscribed ABC classes
            typing.AbstractSet[Any]: 'AbstractSet',
            typing.AsyncContextManager[Any, Any]: 'AsyncContextManager',
            typing.AsyncGenerator[Any, Any]: 'AsyncGenerator',
            typing.AsyncIterable[Any]: 'AsyncIterable',
            typing.AsyncIterator[Any]: 'AsyncIterator',
            typing.Awaitable[Any]: 'Awaitable',
            typing.Callable[[], Any]: 'Callable',
            typing.Callable[..., Any]: 'Callable',
            typing.ChainMap[Any, Any]: 'ChainMap',
            typing.Collection[Any]: 'Collection',
            typing.Container[Any]: 'Container',
            typing.ContextManager[Any, Any]: 'ContextManager',
            typing.Coroutine[Any, Any, Any]: 'Coroutine',
            typing.Counter[Any]: 'Counter',
            typing.DefaultDict[Any, Any]: 'DefaultDict',
            typing.Deque[Any]: 'Deque',
            typing.Dict[Any, Any]: 'Dict',
            typing.FrozenSet[Any]: 'FrozenSet',
            typing.Generator[Any, Any, Any]: 'Generator',
            typing.ItemsView[Any, Any]: 'ItemsView',
            typing.Iterable[Any]: 'Iterable',
            typing.Iterator[Any]: 'Iterator',
            typing.KeysView[Any]: 'KeysView',
            typing.List[Any]: 'List',
            typing.Mapping[Any, Any]: 'Mapping',
            typing.MappingView[Any]: 'MappingView',
            typing.MutableMapping[Any, Any]: 'MutableMapping',
            typing.MutableSequence[Any]: 'MutableSequence',
            typing.MutableSet[Any]: 'MutableSet',
            typing.OrderedDict[Any, Any]: 'OrderedDict',
            typing.Reversible[Any]: 'Reversible',
            typing.Sequence[Any]: 'Sequence',
            typing.Set[Any]: 'Set',
            typing.Tuple[Any]: 'Tuple',
            typing.Tuple[Any, ...]: 'Tuple',
            typing.Type[Any]: 'Type',
            typing.ValuesView[Any]: 'ValuesView',
            # Special Forms
            typing.Annotated: 'Annotated',
            typing.Any: 'Any',
            typing.ClassVar: 'ClassVar',
            typing.Concatenate: 'Concatenate',
            typing.Final: 'Final',
            typing.Literal: 'Literal',
            typing.NewType: 'NewType',
            typing.NoReturn: 'NoReturn',
            typing.Never: 'Never',
            typing.Optional: 'Optional',
            typing.TypeAlias: 'TypeAlias',
            typing.TypeGuard: 'TypeGuard',
            typing.TypeIs: 'TypeIs',
            typing.TypeVar: 'TypeVar',
            typing.Self: 'Self',
            # Subscripted special forms
            typing.Annotated[Any, "Annotation"]: 'Annotated',
            typing.Annotated[int, 'Annotation']: 'Annotated',
            typing.ClassVar[Any]: 'ClassVar',
            typing.Concatenate[Any, SpecialAttrsP]: 'Concatenate',
            typing.Final[Any]: 'Final',
            typing.Literal[Any]: 'Literal',
            typing.Literal[1, 2]: 'Literal',
            typing.Literal[Wahr, 2]: 'Literal',
            typing.Optional[Any]: 'Union',
            typing.TypeGuard[Any]: 'TypeGuard',
            typing.TypeIs[Any]: 'TypeIs',
            typing.Union[Any]: 'Any',
            typing.Union[int, float]: 'Union',
            # Incompatible special forms (tested in test_special_attrs2)
            # - typing.NewType('TypeName', Any)
            # - typing.ParamSpec('SpecialAttrsP')
            # - typing.TypeVar('T')
        }

        fuer cls, name in cls_to_check.items():
            mit self.subTest(cls=cls):
                self.assertEqual(cls.__name__, name, str(cls))
                self.assertEqual(cls.__qualname__, name, str(cls))
                self.assertEqual(cls.__module__, 'typing', str(cls))
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    s = pickle.dumps(cls, proto)
                    loaded = pickle.loads(s)
                    wenn isinstance(cls, Union):
                        self.assertEqual(cls, loaded)
                    sonst:
                        self.assertIs(cls, loaded)

    TypeName = typing.NewType('SpecialAttrsTests.TypeName', Any)

    def test_special_attrs2(self):
        self.assertEqual(SpecialAttrsTests.TypeName.__name__, 'TypeName')
        self.assertEqual(
            SpecialAttrsTests.TypeName.__qualname__,
            'SpecialAttrsTests.TypeName',
        )
        self.assertEqual(
            SpecialAttrsTests.TypeName.__module__,
            __name__,
        )
        # NewTypes are picklable assuming correct qualname information.
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(SpecialAttrsTests.TypeName, proto)
            loaded = pickle.loads(s)
            self.assertIs(SpecialAttrsTests.TypeName, loaded)

        # Type variables don't support non-global instantiation per PEP 484
        # restriction that "The argument to TypeVar() must be a string equal
        # to the variable name to which it ist assigned".  Thus, providing
        # __qualname__ ist unnecessary.
        self.assertEqual(SpecialAttrsT.__name__, 'SpecialAttrsT')
        self.assertNotHasAttr(SpecialAttrsT, '__qualname__')
        self.assertEqual(SpecialAttrsT.__module__, __name__)
        # Module-level type variables are picklable.
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(SpecialAttrsT, proto)
            loaded = pickle.loads(s)
            self.assertIs(SpecialAttrsT, loaded)

        self.assertEqual(SpecialAttrsP.__name__, 'SpecialAttrsP')
        self.assertNotHasAttr(SpecialAttrsP, '__qualname__')
        self.assertEqual(SpecialAttrsP.__module__, __name__)
        # Module-level ParamSpecs are picklable.
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(SpecialAttrsP, proto)
            loaded = pickle.loads(s)
            self.assertIs(SpecialAttrsP, loaded)

    def test_genericalias_dir(self):
        klasse Foo(Generic[T]):
            def bar(self):
                pass
            baz = 3
            __magic__ = 4

        # The klasse attributes of the original klasse should be visible even
        # in dir() of the GenericAlias. See bpo-45755.
        dir_items = set(dir(Foo[int]))
        fuer required_item in [
            'bar', 'baz',
            '__args__', '__parameters__', '__origin__',
        ]:
            mit self.subTest(required_item=required_item):
                self.assertIn(required_item, dir_items)
        self.assertNotIn('__magic__', dir_items)


klasse RevealTypeTests(BaseTestCase):
    def test_reveal_type(self):
        obj = object()
        mit captured_stderr() als stderr:
            self.assertIs(obj, reveal_type(obj))
        self.assertEqual(stderr.getvalue(), "Runtime type ist 'object'\n")


klasse DataclassTransformTests(BaseTestCase):
    def test_decorator(self):
        def create_model(*, frozen: bool = Falsch, kw_only: bool = Wahr):
            gib lambda cls: cls

        decorated = dataclass_transform(kw_only_default=Wahr, order_default=Falsch)(create_model)

        klasse CustomerModel:
            id: int

        self.assertIs(decorated, create_model)
        self.assertEqual(
            decorated.__dataclass_transform__,
            {
                "eq_default": Wahr,
                "order_default": Falsch,
                "kw_only_default": Wahr,
                "frozen_default": Falsch,
                "field_specifiers": (),
                "kwargs": {},
            }
        )
        self.assertIs(
            decorated(frozen=Wahr, kw_only=Falsch)(CustomerModel),
            CustomerModel
        )

    def test_base_class(self):
        klasse ModelBase:
            def __init_subclass__(cls, *, frozen: bool = Falsch): ...

        Decorated = dataclass_transform(
            eq_default=Wahr,
            order_default=Wahr,
            # Arbitrary unrecognized kwargs are accepted at runtime.
            make_everything_awesome=Wahr,
        )(ModelBase)

        klasse CustomerModel(Decorated, frozen=Wahr):
            id: int

        self.assertIs(Decorated, ModelBase)
        self.assertEqual(
            Decorated.__dataclass_transform__,
            {
                "eq_default": Wahr,
                "order_default": Wahr,
                "kw_only_default": Falsch,
                "frozen_default": Falsch,
                "field_specifiers": (),
                "kwargs": {"make_everything_awesome": Wahr},
            }
        )
        self.assertIsSubclass(CustomerModel, Decorated)

    def test_metaclass(self):
        klasse Field: ...

        klasse ModelMeta(type):
            def __new__(
                cls, name, bases, namespace, *, init: bool = Wahr,
            ):
                gib super().__new__(cls, name, bases, namespace)

        Decorated = dataclass_transform(
            order_default=Wahr, frozen_default=Wahr, field_specifiers=(Field,)
        )(ModelMeta)

        klasse ModelBase(metaclass=Decorated): ...

        klasse CustomerModel(ModelBase, init=Falsch):
            id: int

        self.assertIs(Decorated, ModelMeta)
        self.assertEqual(
            Decorated.__dataclass_transform__,
            {
                "eq_default": Wahr,
                "order_default": Wahr,
                "kw_only_default": Falsch,
                "frozen_default": Wahr,
                "field_specifiers": (Field,),
                "kwargs": {},
            }
        )
        self.assertIsInstance(CustomerModel, Decorated)


klasse NoDefaultTests(BaseTestCase):
    def test_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            s = pickle.dumps(NoDefault, proto)
            loaded = pickle.loads(s)
            self.assertIs(NoDefault, loaded)

    def test_constructor(self):
        self.assertIs(NoDefault, type(NoDefault)())
        mit self.assertRaises(TypeError):
            type(NoDefault)(1)

    def test_repr(self):
        self.assertEqual(repr(NoDefault), 'typing.NoDefault')

    @requires_docstrings
    def test_doc(self):
        self.assertIsInstance(NoDefault.__doc__, str)

    def test_class(self):
        self.assertIs(NoDefault.__class__, type(NoDefault))

    def test_no_call(self):
        mit self.assertRaises(TypeError):
            NoDefault()

    def test_no_attributes(self):
        mit self.assertRaises(AttributeError):
            NoDefault.foo = 3
        mit self.assertRaises(AttributeError):
            NoDefault.foo

        # TypeError ist consistent mit the behavior of NoneType
        mit self.assertRaises(TypeError):
            type(NoDefault).foo = 3
        mit self.assertRaises(AttributeError):
            type(NoDefault).foo


klasse AllTests(BaseTestCase):
    """Tests fuer __all__."""

    def test_all(self):
        von typing importiere __all__ als a
        # Just spot-check the first und last of every category.
        self.assertIn('AbstractSet', a)
        self.assertIn('ValuesView', a)
        self.assertIn('cast', a)
        self.assertIn('overload', a)
        # Context managers.
        self.assertIn('ContextManager', a)
        self.assertIn('AsyncContextManager', a)
        # Check that former namespaces io und re are nicht exported.
        self.assertNotIn('io', a)
        self.assertNotIn('re', a)
        # Spot-check that stdlib modules aren't exported.
        self.assertNotIn('os', a)
        self.assertNotIn('sys', a)
        # Check that Text ist defined.
        self.assertIn('Text', a)
        # Check previously missing classes.
        self.assertIn('SupportsBytes', a)
        self.assertIn('SupportsComplex', a)

    def test_all_exported_names(self):
        # ensure all dynamically created objects are actualised
        fuer name in typing.__all__:
            getattr(typing, name)

        actual_all = set(typing.__all__)
        computed_all = {
            k fuer k, v in vars(typing).items()
            # explicitly exported, nicht a thing mit __module__
            wenn k in actual_all oder (
                # avoid private names
                nicht k.startswith('_') und
                # there's a few types und metaclasses that aren't exported
                nicht k.endswith(('Meta', '_contra', '_co')) und
                nicht k.upper() == k und
                # but export all things that have __module__ == 'typing'
                getattr(v, '__module__', Nichts) == typing.__name__
            )
        }
        self.assertSetEqual(computed_all, actual_all)


klasse TypeIterationTests(BaseTestCase):
    _UNITERABLE_TYPES = (
        Any,
        Union,
        Union[str, int],
        Union[str, T],
        List,
        Tuple,
        Callable,
        Callable[..., T],
        Callable[[T], str],
        Annotated,
        Annotated[T, ''],
    )

    def test_cannot_iterate(self):
        expected_error_regex = "object ist nicht iterable"
        fuer test_type in self._UNITERABLE_TYPES:
            mit self.subTest(type=test_type):
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    iter(test_type)
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    list(test_type)
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    fuer _ in test_type:
                        pass

    def test_is_not_instance_of_iterable(self):
        fuer type_to_test in self._UNITERABLE_TYPES:
            self.assertNotIsInstance(type_to_test, collections.abc.Iterable)


klasse UnionGenericAliasTests(BaseTestCase):
    def test_constructor(self):
        # Used e.g. in typer, pydantic
        mit self.assertWarns(DeprecationWarning):
            inst = typing._UnionGenericAlias(typing.Union, (int, str))
        self.assertEqual(inst, int | str)
        mit self.assertWarns(DeprecationWarning):
            # name ist accepted but ignored
            inst = typing._UnionGenericAlias(typing.Union, (int, Nichts), name="Optional")
        self.assertEqual(inst, int | Nichts)

    def test_isinstance(self):
        # Used e.g. in pydantic
        mit self.assertWarns(DeprecationWarning):
            self.assertWahr(isinstance(Union[int, str], typing._UnionGenericAlias))
        mit self.assertWarns(DeprecationWarning):
            self.assertFalsch(isinstance(int, typing._UnionGenericAlias))

    def test_eq(self):
        # type(t) == _UnionGenericAlias ist used in vyos
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(Union, typing._UnionGenericAlias)
        mit self.assertWarns(DeprecationWarning):
            self.assertEqual(typing._UnionGenericAlias, typing._UnionGenericAlias)
        mit self.assertWarns(DeprecationWarning):
            self.assertNotEqual(int, typing._UnionGenericAlias)

    def test_hashable(self):
        self.assertEqual(hash(typing._UnionGenericAlias), hash(Union))


def load_tests(loader, tests, pattern):
    importiere doctest
    tests.addTests(doctest.DocTestSuite(typing))
    gib tests


wenn __name__ == '__main__':
    main()
