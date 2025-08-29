"""Tests fuer C-implemented GenericAlias."""

importiere unittest
importiere pickle
von array importiere array
importiere copy
von collections importiere (
    defaultdict, deque, OrderedDict, Counter, UserDict, UserList
)
von collections.abc importiere *
von concurrent.futures importiere Future
von concurrent.futures.thread importiere _WorkItem
von contextlib importiere AbstractContextManager, AbstractAsyncContextManager
von contextvars importiere ContextVar, Token
von csv importiere DictReader, DictWriter
von dataclasses importiere Field
von functools importiere partial, partialmethod, cached_property
von graphlib importiere TopologicalSorter
von logging importiere LoggerAdapter, StreamHandler
von mailbox importiere Mailbox, _PartialFile
try:
    importiere ctypes
except ImportError:
    ctypes = Nichts
von difflib importiere SequenceMatcher
von filecmp importiere dircmp
von fileinput importiere FileInput
von itertools importiere chain
von http.cookies importiere Morsel
try:
    von multiprocessing.managers importiere ValueProxy, DictProxy, ListProxy
    von multiprocessing.pool importiere ApplyResult
    von multiprocessing.queues importiere SimpleQueue als MPSimpleQueue
    von multiprocessing.queues importiere Queue als MPQueue
    von multiprocessing.queues importiere JoinableQueue als MPJoinableQueue
except ImportError:
    # _multiprocessing module is optional
    ValueProxy = Nichts
    DictProxy = Nichts
    ListProxy = Nichts
    ApplyResult = Nichts
    MPSimpleQueue = Nichts
    MPQueue = Nichts
    MPJoinableQueue = Nichts
try:
    von multiprocessing.shared_memory importiere ShareableList
except ImportError:
    # multiprocessing.shared_memory is nicht available on e.g. Android
    ShareableList = Nichts
von os importiere DirEntry
von re importiere Pattern, Match
von types importiere GenericAlias, MappingProxyType, AsyncGeneratorType, CoroutineType, GeneratorType
von tempfile importiere TemporaryDirectory, SpooledTemporaryFile
von urllib.parse importiere SplitResult, ParseResult
von unittest.case importiere _AssertRaisesContext
von queue importiere Queue, SimpleQueue
von weakref importiere WeakSet, ReferenceType, ref
importiere typing
von typing importiere Unpack
try:
    von tkinter importiere Event
except ImportError:
    Event = Nichts
von string.templatelib importiere Template, Interpolation

von typing importiere TypeVar
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

_UNPACKED_TUPLES = [
    # Unpacked tuple using `*`
    (*tuple[int],)[0],
    (*tuple[T],)[0],
    (*tuple[int, str],)[0],
    (*tuple[int, ...],)[0],
    (*tuple[T, ...],)[0],
    tuple[*tuple[int, ...]],
    tuple[*tuple[T, ...]],
    tuple[str, *tuple[int, ...]],
    tuple[*tuple[int, ...], str],
    tuple[float, *tuple[int, ...], str],
    tuple[*tuple[*tuple[int, ...]]],
    # Unpacked tuple using `Unpack`
    Unpack[tuple[int]],
    Unpack[tuple[T]],
    Unpack[tuple[int, str]],
    Unpack[tuple[int, ...]],
    Unpack[tuple[T, ...]],
    tuple[Unpack[tuple[int, ...]]],
    tuple[Unpack[tuple[T, ...]]],
    tuple[str, Unpack[tuple[int, ...]]],
    tuple[Unpack[tuple[int, ...]], str],
    tuple[float, Unpack[tuple[int, ...]], str],
    tuple[Unpack[tuple[Unpack[tuple[int, ...]]]]],
    # Unpacked tuple using `*` AND `Unpack`
    tuple[Unpack[tuple[*tuple[int, ...]]]],
    tuple[*tuple[Unpack[tuple[int, ...]]]],
]


klasse BaseTest(unittest.TestCase):
    """Test basics."""
    generic_types = [type, tuple, list, dict, set, frozenset, enumerate, memoryview,
                     defaultdict, deque,
                     SequenceMatcher,
                     dircmp,
                     FileInput,
                     OrderedDict, Counter, UserDict, UserList,
                     Pattern, Match,
                     partial, partialmethod, cached_property,
                     TopologicalSorter,
                     AbstractContextManager, AbstractAsyncContextManager,
                     Awaitable, Coroutine,
                     AsyncIterable, AsyncIterator,
                     AsyncGenerator, Generator,
                     Iterable, Iterator,
                     Reversible,
                     Container, Collection,
                     Mailbox, _PartialFile,
                     ContextVar, Token,
                     Field,
                     Set, MutableSet,
                     Mapping, MutableMapping, MappingView,
                     KeysView, ItemsView, ValuesView,
                     Sequence, MutableSequence,
                     MappingProxyType, AsyncGeneratorType,
                     GeneratorType, CoroutineType,
                     DirEntry,
                     chain,
                     LoggerAdapter, StreamHandler,
                     TemporaryDirectory, SpooledTemporaryFile,
                     Queue, SimpleQueue,
                     _AssertRaisesContext,
                     SplitResult, ParseResult,
                     WeakSet, ReferenceType, ref,
                     ShareableList,
                     Future, _WorkItem,
                     Morsel,
                     DictReader, DictWriter,
                     array,
                     staticmethod,
                     classmethod,
                     Template,
                     Interpolation,
                    ]
    wenn ctypes is nicht Nichts:
        generic_types.extend((ctypes.Array, ctypes.LibraryLoader, ctypes.py_object))
    wenn ValueProxy is nicht Nichts:
        generic_types.extend((ValueProxy, DictProxy, ListProxy, ApplyResult,
                              MPSimpleQueue, MPQueue, MPJoinableQueue))
    wenn Event is nicht Nichts:
        generic_types.append(Event)

    def test_subscriptable(self):
        fuer t in self.generic_types:
            wenn t is Nichts:
                weiter
            tname = t.__name__
            mit self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertIs(alias.__origin__, t)
                self.assertEqual(alias.__args__, (int,))
                self.assertEqual(alias.__parameters__, ())

    def test_unsubscriptable(self):
        fuer t in int, str, float, Sized, Hashable:
            tname = t.__name__
            mit self.subTest(f"Testing {tname}"):
                mit self.assertRaisesRegex(TypeError, tname):
                    t[int]

    def test_instantiate(self):
        fuer t in tuple, list, dict, set, frozenset, defaultdict, deque:
            tname = t.__name__
            mit self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertEqual(alias(), t())
                wenn t is dict:
                    self.assertEqual(alias(iter([('a', 1), ('b', 2)])), dict(a=1, b=2))
                    self.assertEqual(alias(a=1, b=2), dict(a=1, b=2))
                sowenn t is defaultdict:
                    def default():
                        return 'value'
                    a = alias(default)
                    d = defaultdict(default)
                    self.assertEqual(a['test'], d['test'])
                sonst:
                    self.assertEqual(alias(iter((1, 2, 3))), t((1, 2, 3)))

    def test_unbound_methods(self):
        t = list[int]
        a = t()
        t.append(a, 'foo')
        self.assertEqual(a, ['foo'])
        x = t.__getitem__(a, 0)
        self.assertEqual(x, 'foo')
        self.assertEqual(t.__len__(a), 1)

    def test_subclassing(self):
        klasse C(list[int]):
            pass
        self.assertEqual(C.__bases__, (list,))
        self.assertEqual(C.__class__, type)

    def test_class_methods(self):
        t = dict[int, Nichts]
        self.assertEqual(dict.fromkeys(range(2)), {0: Nichts, 1: Nichts})  # This works
        self.assertEqual(t.fromkeys(range(2)), {0: Nichts, 1: Nichts})  # Should be equivalent

    def test_no_chaining(self):
        t = list[int]
        mit self.assertRaises(TypeError):
            t[int]

    def test_generic_subclass(self):
        klasse MyList(list):
            pass
        t = MyList[int]
        self.assertIs(t.__origin__, MyList)
        self.assertEqual(t.__args__, (int,))
        self.assertEqual(t.__parameters__, ())

    def test_repr(self):
        klasse MyList(list):
            pass
        klasse MyGeneric:
            __class_getitem__ = classmethod(GenericAlias)

        self.assertEqual(repr(list[str]), 'list[str]')
        self.assertEqual(repr(list[()]), 'list[()]')
        self.assertEqual(repr(tuple[int, ...]), 'tuple[int, ...]')
        x1 = tuple[*tuple[int]]
        self.assertEqual(repr(x1), 'tuple[*tuple[int]]')
        x2 = tuple[*tuple[int, str]]
        self.assertEqual(repr(x2), 'tuple[*tuple[int, str]]')
        x3 = tuple[*tuple[int, ...]]
        self.assertEqual(repr(x3), 'tuple[*tuple[int, ...]]')
        self.assertEndsWith(repr(MyList[int]), '.BaseTest.test_repr.<locals>.MyList[int]')
        self.assertEqual(repr(list[str]()), '[]')  # instances should keep their normal repr

        # gh-105488
        self.assertEndsWith(repr(MyGeneric[int]), 'MyGeneric[int]')
        self.assertEndsWith(repr(MyGeneric[[]]), 'MyGeneric[[]]')
        self.assertEndsWith(repr(MyGeneric[[int, str]]), 'MyGeneric[[int, str]]')

    def test_exposed_type(self):
        importiere types
        a = types.GenericAlias(list, int)
        self.assertEqual(str(a), 'list[int]')
        self.assertIs(a.__origin__, list)
        self.assertEqual(a.__args__, (int,))
        self.assertEqual(a.__parameters__, ())

    def test_parameters(self):
        von typing importiere List, Dict, Callable

        D0 = dict[str, int]
        self.assertEqual(D0.__args__, (str, int))
        self.assertEqual(D0.__parameters__, ())
        D1a = dict[str, V]
        self.assertEqual(D1a.__args__, (str, V))
        self.assertEqual(D1a.__parameters__, (V,))
        D1b = dict[K, int]
        self.assertEqual(D1b.__args__, (K, int))
        self.assertEqual(D1b.__parameters__, (K,))
        D2a = dict[K, V]
        self.assertEqual(D2a.__args__, (K, V))
        self.assertEqual(D2a.__parameters__, (K, V))
        D2b = dict[T, T]
        self.assertEqual(D2b.__args__, (T, T))
        self.assertEqual(D2b.__parameters__, (T,))

        L0 = list[str]
        self.assertEqual(L0.__args__, (str,))
        self.assertEqual(L0.__parameters__, ())
        L1 = list[T]
        self.assertEqual(L1.__args__, (T,))
        self.assertEqual(L1.__parameters__, (T,))
        L2 = list[list[T]]
        self.assertEqual(L2.__args__, (list[T],))
        self.assertEqual(L2.__parameters__, (T,))
        L3 = list[List[T]]
        self.assertEqual(L3.__args__, (List[T],))
        self.assertEqual(L3.__parameters__, (T,))
        L4a = list[Dict[K, V]]
        self.assertEqual(L4a.__args__, (Dict[K, V],))
        self.assertEqual(L4a.__parameters__, (K, V))
        L4b = list[Dict[T, int]]
        self.assertEqual(L4b.__args__, (Dict[T, int],))
        self.assertEqual(L4b.__parameters__, (T,))
        L5 = list[Callable[[K, V], K]]
        self.assertEqual(L5.__args__, (Callable[[K, V], K],))
        self.assertEqual(L5.__parameters__, (K, V))

        T1 = tuple[*tuple[int]]
        self.assertEqual(
            T1.__args__,
            (*tuple[int],),
        )
        self.assertEqual(T1.__parameters__, ())

        T2 = tuple[*tuple[T]]
        self.assertEqual(
            T2.__args__,
            (*tuple[T],),
        )
        self.assertEqual(T2.__parameters__, (T,))

        T4 = tuple[*tuple[int, str]]
        self.assertEqual(
            T4.__args__,
            (*tuple[int, str],),
        )
        self.assertEqual(T4.__parameters__, ())

    def test_parameter_chaining(self):
        von typing importiere List, Dict, Union, Callable
        self.assertEqual(list[T][int], list[int])
        self.assertEqual(dict[str, T][int], dict[str, int])
        self.assertEqual(dict[T, int][str], dict[str, int])
        self.assertEqual(dict[K, V][str, int], dict[str, int])
        self.assertEqual(dict[T, T][int], dict[int, int])

        self.assertEqual(list[list[T]][int], list[list[int]])
        self.assertEqual(list[dict[T, int]][str], list[dict[str, int]])
        self.assertEqual(list[dict[str, T]][int], list[dict[str, int]])
        self.assertEqual(list[dict[K, V]][str, int], list[dict[str, int]])
        self.assertEqual(dict[T, list[int]][str], dict[str, list[int]])

        self.assertEqual(list[List[T]][int], list[List[int]])
        self.assertEqual(list[Dict[K, V]][str, int], list[Dict[str, int]])
        self.assertEqual(list[Union[K, V]][str, int], list[Union[str, int]])
        self.assertEqual(list[Callable[[K, V], K]][str, int],
                         list[Callable[[str, int], str]])
        self.assertEqual(dict[T, List[int]][str], dict[str, List[int]])

        mit self.assertRaises(TypeError):
            list[int][int]
        mit self.assertRaises(TypeError):
            dict[T, int][str, int]
        mit self.assertRaises(TypeError):
            dict[str, T][str, int]
        mit self.assertRaises(TypeError):
            dict[T, T][str, int]

    def test_equality(self):
        self.assertEqual(list[int], list[int])
        self.assertEqual(dict[str, int], dict[str, int])
        self.assertEqual((*tuple[int],)[0], (*tuple[int],)[0])
        self.assertEqual(tuple[*tuple[int]], tuple[*tuple[int]])
        self.assertNotEqual(dict[str, int], dict[str, str])
        self.assertNotEqual(list, list[int])
        self.assertNotEqual(list[int], list)
        self.assertNotEqual(list[int], tuple[int])
        self.assertNotEqual((*tuple[int],)[0], tuple[int])

    def test_isinstance(self):
        self.assertWahr(isinstance([], list))
        mit self.assertRaises(TypeError):
            isinstance([], list[str])

    def test_issubclass(self):
        klasse L(list): ...
        self.assertIsSubclass(L, list)
        mit self.assertRaises(TypeError):
            issubclass(L, list[str])

    def test_type_generic(self):
        t = type[int]
        Test = t('Test', (), {})
        self.assertWahr(isinstance(Test, type))
        test = Test()
        self.assertEqual(t(test), Test)
        self.assertEqual(t(0), int)

    def test_type_subclass_generic(self):
        klasse MyType(type):
            pass
        mit self.assertRaisesRegex(TypeError, 'MyType'):
            MyType[int]

    def test_pickle(self):
        aliases = [GenericAlias(list, T)] + _UNPACKED_TUPLES
        fuer alias in aliases:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(alias=alias, proto=proto):
                    s = pickle.dumps(alias, proto)
                    loaded = pickle.loads(s)
                    self.assertEqual(loaded.__origin__, alias.__origin__)
                    self.assertEqual(loaded.__args__, alias.__args__)
                    self.assertEqual(loaded.__parameters__, alias.__parameters__)
                    self.assertEqual(type(loaded), type(alias))

    def test_copy(self):
        klasse X(list):
            def __copy__(self):
                return self
            def __deepcopy__(self, memo):
                return self

        aliases = [
            GenericAlias(list, T),
            GenericAlias(deque, T),
            GenericAlias(X, T)
        ] + _UNPACKED_TUPLES
        fuer alias in aliases:
            mit self.subTest(alias=alias):
                copied = copy.copy(alias)
                self.assertEqual(copied.__origin__, alias.__origin__)
                self.assertEqual(copied.__args__, alias.__args__)
                self.assertEqual(copied.__parameters__, alias.__parameters__)
                copied = copy.deepcopy(alias)
                self.assertEqual(copied.__origin__, alias.__origin__)
                self.assertEqual(copied.__args__, alias.__args__)
                self.assertEqual(copied.__parameters__, alias.__parameters__)

    def test_unpack(self):
        alias = tuple[str, ...]
        self.assertIs(alias.__unpacked__, Falsch)
        unpacked = (*alias,)[0]
        self.assertIs(unpacked.__unpacked__, Wahr)

    def test_union(self):
        a = typing.Union[list[int], list[str]]
        self.assertEqual(a.__args__, (list[int], list[str]))
        self.assertEqual(a.__parameters__, ())

    def test_union_generic(self):
        a = typing.Union[list[T], tuple[T, ...]]
        self.assertEqual(a.__args__, (list[T], tuple[T, ...]))
        self.assertEqual(a.__parameters__, (T,))

    def test_dir(self):
        dir_of_gen_alias = set(dir(list[int]))
        self.assertWahr(dir_of_gen_alias.issuperset(dir(list)))
        fuer generic_alias_property in ("__origin__", "__args__", "__parameters__"):
            self.assertIn(generic_alias_property, dir_of_gen_alias)

    def test_weakref(self):
        fuer t in self.generic_types:
            wenn t is Nichts:
                weiter
            tname = t.__name__
            mit self.subTest(f"Testing {tname}"):
                alias = t[int]
                self.assertEqual(ref(alias)(), alias)

    def test_no_kwargs(self):
        # bpo-42576
        mit self.assertRaises(TypeError):
            GenericAlias(bad=float)

    def test_subclassing_types_genericalias(self):
        klasse SubClass(GenericAlias): ...
        alias = SubClass(list, int)
        klasse Bad(GenericAlias):
            def __new__(cls, *args, **kwargs):
                super().__new__(cls, *args, **kwargs)

        self.assertEqual(alias, list[int])
        mit self.assertRaises(TypeError):
            Bad(list, int, bad=int)

    def test_iter_creates_starred_tuple(self):
        t = tuple[int, str]
        iter_t = iter(t)
        x = next(iter_t)
        self.assertEqual(repr(x), '*tuple[int, str]')

    def test_calling_next_twice_raises_stopiteration(self):
        t = tuple[int, str]
        iter_t = iter(t)
        next(iter_t)
        mit self.assertRaises(StopIteration):
            next(iter_t)

    def test_del_iter(self):
        t = tuple[int, str]
        iter_x = iter(t)
        del iter_x

    def test_paramspec_specialization(self):
        # gh-124445
        T = TypeVar("T")
        U = TypeVar("U")
        type X[**P] = Callable[P, int]

        generic = X[[T]]
        self.assertEqual(generic.__args__, ([T],))
        self.assertEqual(generic.__parameters__, (T,))
        specialized = generic[str]
        self.assertEqual(specialized.__args__, ([str],))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[(T,)]
        self.assertEqual(generic.__args__, (T,))
        self.assertEqual(generic.__parameters__, (T,))
        specialized = generic[str]
        self.assertEqual(specialized.__args__, (str,))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[[T, U]]
        self.assertEqual(generic.__args__, ([T, U],))
        self.assertEqual(generic.__parameters__, (T, U))
        specialized = generic[str, int]
        self.assertEqual(specialized.__args__, ([str, int],))
        self.assertEqual(specialized.__parameters__, ())

        generic = X[(T, U)]
        self.assertEqual(generic.__args__, (T, U))
        self.assertEqual(generic.__parameters__, (T, U))
        specialized = generic[str, int]
        self.assertEqual(specialized.__args__, (str, int))
        self.assertEqual(specialized.__parameters__, ())

    def test_nested_paramspec_specialization(self):
        # gh-124445
        type X[**P, T] = Callable[P, T]

        x_list = X[[int, str], float]
        self.assertEqual(x_list.__args__, ([int, str], float))
        self.assertEqual(x_list.__parameters__, ())

        x_tuple = X[(int, str), float]
        self.assertEqual(x_tuple.__args__, ((int, str), float))
        self.assertEqual(x_tuple.__parameters__, ())

        U = TypeVar("U")
        V = TypeVar("V")

        multiple_params_list = X[[int, U], V]
        self.assertEqual(multiple_params_list.__args__, ([int, U], V))
        self.assertEqual(multiple_params_list.__parameters__, (U, V))
        multiple_params_list_specialized = multiple_params_list[str, float]
        self.assertEqual(multiple_params_list_specialized.__args__, ([int, str], float))
        self.assertEqual(multiple_params_list_specialized.__parameters__, ())

        multiple_params_tuple = X[(int, U), V]
        self.assertEqual(multiple_params_tuple.__args__, ((int, U), V))
        self.assertEqual(multiple_params_tuple.__parameters__, (U, V))
        multiple_params_tuple_specialized = multiple_params_tuple[str, float]
        self.assertEqual(multiple_params_tuple_specialized.__args__, ((int, str), float))
        self.assertEqual(multiple_params_tuple_specialized.__parameters__, ())

        deeply_nested = X[[U, [V], int], V]
        self.assertEqual(deeply_nested.__args__, ([U, [V], int], V))
        self.assertEqual(deeply_nested.__parameters__, (U, V))
        deeply_nested_specialized = deeply_nested[str, float]
        self.assertEqual(deeply_nested_specialized.__args__, ([str, [float], int], float))
        self.assertEqual(deeply_nested_specialized.__parameters__, ())


klasse TypeIterationTests(unittest.TestCase):
    _UNITERABLE_TYPES = (list, tuple)

    def test_cannot_iterate(self):
        fuer test_type in self._UNITERABLE_TYPES:
            mit self.subTest(type=test_type):
                expected_error_regex = "object is nicht iterable"
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    iter(test_type)
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    list(test_type)
                mit self.assertRaisesRegex(TypeError, expected_error_regex):
                    fuer _ in test_type:
                        pass

    def test_is_not_instance_of_iterable(self):
        fuer type_to_test in self._UNITERABLE_TYPES:
            self.assertNotIsInstance(type_to_test, Iterable)


wenn __name__ == "__main__":
    unittest.main()
