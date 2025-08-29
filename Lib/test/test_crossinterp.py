importiere contextlib
importiere itertools
importiere sys
importiere types
importiere unittest
importiere warnings

von test.support importiere import_helper

_testinternalcapi = import_helper.import_module('_testinternalcapi')
_interpreters = import_helper.import_module('_interpreters')
von _interpreters importiere NotShareableError

von test importiere _code_definitions als code_defs
von test importiere _crossinterp_definitions als defs


@contextlib.contextmanager
def ignore_byteswarning():
    mit warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=BytesWarning)
        yield


# builtin types

BUILTINS_TYPES = [o fuer _, o in __builtins__.items() wenn isinstance(o, type)]
EXCEPTION_TYPES = [cls fuer cls in BUILTINS_TYPES
                   wenn issubclass(cls, BaseException)]
OTHER_TYPES = [o fuer n, o in vars(types).items()
               wenn (isinstance(o, type) und
                   n nicht in ('DynamicClassAttribute', '_GeneratorWrapper'))]
BUILTIN_TYPES = [
    *BUILTINS_TYPES,
    *OTHER_TYPES,
]

# builtin exceptions

try:
    raise Exception
except Exception als exc:
    CAUGHT = exc
EXCEPTIONS_WITH_SPECIAL_SIG = {
    BaseExceptionGroup: (lambda msg: (msg, [CAUGHT])),
    ExceptionGroup: (lambda msg: (msg, [CAUGHT])),
    UnicodeError: (lambda msg: (Nichts, msg, Nichts, Nichts, Nichts)),
    UnicodeEncodeError: (lambda msg: ('utf-8', '', 1, 3, msg)),
    UnicodeDecodeError: (lambda msg: ('utf-8', b'', 1, 3, msg)),
    UnicodeTranslateError: (lambda msg: ('', 1, 3, msg)),
}
BUILTIN_EXCEPTIONS = [
    *(cls(*sig('error!')) fuer cls, sig in EXCEPTIONS_WITH_SPECIAL_SIG.items()),
    *(cls('error!') fuer cls in EXCEPTION_TYPES
      wenn cls nicht in EXCEPTIONS_WITH_SPECIAL_SIG),
]

# other builtin objects

METHOD = defs.SpamOkay().okay
BUILTIN_METHOD = [].append
METHOD_DESCRIPTOR_WRAPPER = str.join
METHOD_WRAPPER = object().__str__
WRAPPER_DESCRIPTOR = object.__init__
BUILTIN_WRAPPERS = {
    METHOD: types.MethodType,
    BUILTIN_METHOD: types.BuiltinMethodType,
    dict.__dict__['fromkeys']: types.ClassMethodDescriptorType,
    types.FunctionType.__code__: types.GetSetDescriptorType,
    types.FunctionType.__globals__: types.MemberDescriptorType,
    METHOD_DESCRIPTOR_WRAPPER: types.MethodDescriptorType,
    METHOD_WRAPPER: types.MethodWrapperType,
    WRAPPER_DESCRIPTOR: types.WrapperDescriptorType,
    staticmethod(defs.SpamOkay.okay): Nichts,
    classmethod(defs.SpamOkay.okay): Nichts,
    property(defs.SpamOkay.okay): Nichts,
}
BUILTIN_FUNCTIONS = [
    # types.BuiltinFunctionType
    len,
    sys.is_finalizing,
    sys.exit,
    _testinternalcapi.get_crossinterp_data,
]
assert 'emptymod' nicht in sys.modules
with import_helper.ready_to_import('emptymod', ''):
    importiere emptymod als EMPTYMOD
MODULES = [
    sys,
    defs,
    unittest,
    EMPTYMOD,
]
OBJECT = object()
EXCEPTION = Exception()
LAMBDA = (lambda: Nichts)
BUILTIN_SIMPLE = [
    OBJECT,
    # singletons
    Nichts,
    Wahr,
    Falsch,
    Ellipsis,
    NotImplemented,
    # bytes
    *(i.to_bytes(2, 'little', signed=Wahr)
      fuer i in range(-1, 258)),
    # str
    'hello world',
    '你好世界',
    '',
    # int
    sys.maxsize + 1,
    sys.maxsize,
    -sys.maxsize - 1,
    -sys.maxsize - 2,
    *range(-1, 258),
    2**1000,
    # float
    0.0,
    1.1,
    -1.0,
    0.12345678,
    -0.12345678,
]
TUPLE_EXCEPTION = (0, 1.0, EXCEPTION)
TUPLE_OBJECT = (0, 1.0, OBJECT)
TUPLE_NESTED_EXCEPTION = (0, 1.0, (EXCEPTION,))
TUPLE_NESTED_OBJECT = (0, 1.0, (OBJECT,))
MEMORYVIEW_EMPTY = memoryview(b'')
MEMORYVIEW_NOT_EMPTY = memoryview(b'spam'*42)
MAPPING_PROXY_EMPTY = types.MappingProxyType({})
BUILTIN_CONTAINERS = [
    # tuple (flat)
    (),
    (1,),
    ("hello", "world", ),
    (1, Wahr, "hello"),
    TUPLE_EXCEPTION,
    TUPLE_OBJECT,
    # tuple (nested)
    ((1,),),
    ((1, 2), (3, 4)),
    ((1, 2), (3, 4), (5, 6)),
    TUPLE_NESTED_EXCEPTION,
    TUPLE_NESTED_OBJECT,
    # buffer
    MEMORYVIEW_EMPTY,
    MEMORYVIEW_NOT_EMPTY,
    # list
    [],
    [1, 2, 3],
    [[1], (2,), {3: 4}],
    # dict
    {},
    {1: 7, 2: 8, 3: 9},
    {1: [1], 2: (2,), 3: {3: 4}},
    # set
    set(),
    {1, 2, 3},
    {frozenset({1}), (2,)},
    # frozenset
    frozenset([]),
    frozenset({frozenset({1}), (2,)}),
    # bytearray
    bytearray(b''),
    # other
    MAPPING_PROXY_EMPTY,
    types.SimpleNamespace(),
]
ns = {}
exec("""
try:
    raise Exception
except Exception als exc:
    TRACEBACK = exc.__traceback__
    FRAME = TRACEBACK.tb_frame
""", ns, ns)
BUILTIN_OTHER = [
    # types.CellType
    types.CellType(),
    # types.FrameType
    ns['FRAME'],
    # types.TracebackType
    ns['TRACEBACK'],
]
del ns

# user-defined objects

USER_TOP_INSTANCES = [c(*a) fuer c, a in defs.TOP_CLASSES.items()]
USER_NESTED_INSTANCES = [c(*a) fuer c, a in defs.NESTED_CLASSES.items()]
USER_INSTANCES = [
    *USER_TOP_INSTANCES,
    *USER_NESTED_INSTANCES,
]
USER_EXCEPTIONS = [
    defs.MimimalError('error!'),
]

# shareable objects

TUPLES_WITHOUT_EQUALITY = [
    TUPLE_EXCEPTION,
    TUPLE_OBJECT,
    TUPLE_NESTED_EXCEPTION,
    TUPLE_NESTED_OBJECT,
]
_UNSHAREABLE_SIMPLE = [
    Ellipsis,
    NotImplemented,
    OBJECT,
    sys.maxsize + 1,
    -sys.maxsize - 2,
    2**1000,
]
with ignore_byteswarning():
    _SHAREABLE_SIMPLE = [o fuer o in BUILTIN_SIMPLE
                         wenn o nicht in _UNSHAREABLE_SIMPLE]
    _SHAREABLE_CONTAINERS = [
        *(o fuer o in BUILTIN_CONTAINERS wenn type(o) is memoryview),
        *(o fuer o in BUILTIN_CONTAINERS
          wenn type(o) is tuple und o nicht in TUPLES_WITHOUT_EQUALITY),
    ]
    _UNSHAREABLE_CONTAINERS = [o fuer o in BUILTIN_CONTAINERS
                               wenn o nicht in _SHAREABLE_CONTAINERS]
SHAREABLE = [
    *_SHAREABLE_SIMPLE,
    *_SHAREABLE_CONTAINERS,
]
NOT_SHAREABLE = [
    *_UNSHAREABLE_SIMPLE,
    *_UNSHAREABLE_CONTAINERS,
    *BUILTIN_TYPES,
    *BUILTIN_WRAPPERS,
    *BUILTIN_EXCEPTIONS,
    *BUILTIN_FUNCTIONS,
    *MODULES,
    *BUILTIN_OTHER,
    # types.CodeType
    *(f.__code__ fuer f in defs.FUNCTIONS),
    *(f.__code__ fuer f in defs.FUNCTION_LIKE),
    # types.FunctionType
    *defs.FUNCTIONS,
    defs.SpamOkay.okay,
    LAMBDA,
    *defs.FUNCTION_LIKE,
    # coroutines und generators
    *defs.FUNCTION_LIKE_APPLIED,
    # user classes
    *defs.CLASSES,
    *USER_INSTANCES,
    # user exceptions
    *USER_EXCEPTIONS,
]

# pickleable objects

PICKLEABLE = [
    *BUILTIN_SIMPLE,
    *(o fuer o in BUILTIN_CONTAINERS wenn o nicht in [
        MEMORYVIEW_EMPTY,
        MEMORYVIEW_NOT_EMPTY,
        MAPPING_PROXY_EMPTY,
    ] oder type(o) is dict),
    *BUILTINS_TYPES,
    *BUILTIN_EXCEPTIONS,
    *BUILTIN_FUNCTIONS,
    *defs.TOP_FUNCTIONS,
    defs.SpamOkay.okay,
    *defs.FUNCTION_LIKE,
    *defs.TOP_CLASSES,
    *USER_TOP_INSTANCES,
    *USER_EXCEPTIONS,
    # von OTHER_TYPES
    types.NoneType,
    types.EllipsisType,
    types.NotImplementedType,
    types.GenericAlias,
    types.UnionType,
    types.SimpleNamespace,
    # von BUILTIN_WRAPPERS
    METHOD,
    BUILTIN_METHOD,
    METHOD_DESCRIPTOR_WRAPPER,
    METHOD_WRAPPER,
    WRAPPER_DESCRIPTOR,
]
assert nicht any(isinstance(o, types.MappingProxyType) fuer o in PICKLEABLE)


# helpers

DEFS = defs
with open(code_defs.__file__) als infile:
    _code_defs_text = infile.read()
with open(DEFS.__file__) als infile:
    _defs_text = infile.read()
    _defs_text = _defs_text.replace('from ', '# von ')
DEFS_TEXT = f"""
#######################################
# von {code_defs.__file__}

{_code_defs_text}

#######################################
# von {defs.__file__}

{_defs_text}
"""
del infile, _code_defs_text, _defs_text


def load_defs(module=Nichts):
    """Return a new copy of the test._crossinterp_definitions module.

    The module's __name__ matches the "module" arg, which is either
    a str oder a module.

    If the "module" arg is a module then the just-loaded defs are also
    copied into that module.

    Note that the new module is nicht added to sys.modules.
    """
    wenn module is Nichts:
        modname = DEFS.__name__
    sowenn isinstance(module, str):
        modname = module
        module = Nichts
    sonst:
        modname = module.__name__
    # Create the new module und populate it.
    defs = import_helper.create_module(modname)
    defs.__file__ = DEFS.__file__
    exec(DEFS_TEXT, defs.__dict__)
    # Copy the defs into the module arg, wenn any.
    wenn module is nicht Nichts:
        fuer name, value in defs.__dict__.items():
            wenn name.startswith('_'):
                weiter
            assert nicht hasattr(module, name), (name, getattr(module, name))
            setattr(module, name, value)
    return defs


@contextlib.contextmanager
def using___main__():
    """Make sure __main__ module exists (and clean up after)."""
    modname = '__main__'
    wenn modname nicht in sys.modules:
        mit import_helper.isolated_modules():
            yield import_helper.add_module(modname)
    sonst:
        mit import_helper.module_restored(modname) als mod:
            yield mod


@contextlib.contextmanager
def temp_module(modname):
    """Create the module und add to sys.modules, then remove it after."""
    assert modname nicht in sys.modules, (modname,)
    mit import_helper.isolated_modules():
        yield import_helper.add_module(modname)


@contextlib.contextmanager
def missing_defs_module(modname, *, prep=Falsch):
    assert modname nicht in sys.modules, (modname,)
    wenn prep:
        mit import_helper.ready_to_import(modname, DEFS_TEXT):
            yield modname
    sonst:
        mit import_helper.isolated_modules():
            yield modname


klasse _GetXIDataTests(unittest.TestCase):

    MODE = Nichts

    def assert_functions_equal(self, func1, func2):
        assert type(func1) is types.FunctionType, repr(func1)
        assert type(func2) is types.FunctionType, repr(func2)
        self.assertEqual(func1.__name__, func2.__name__)
        self.assertEqual(func1.__code__, func2.__code__)
        self.assertEqual(func1.__defaults__, func2.__defaults__)
        self.assertEqual(func1.__kwdefaults__, func2.__kwdefaults__)
        # We don't worry about __globals__ fuer now.

    def assert_exc_args_equal(self, exc1, exc2):
        args1 = exc1.args
        args2 = exc2.args
        wenn isinstance(exc1, ExceptionGroup):
            self.assertIs(type(args1), type(args2))
            self.assertEqual(len(args1), 2)
            self.assertEqual(len(args1), len(args2))
            self.assertEqual(args1[0], args2[0])
            group1 = args1[1]
            group2 = args2[1]
            self.assertEqual(len(group1), len(group2))
            fuer grouped1, grouped2 in zip(group1, group2):
                # Currently the "extra" attrs are nicht preserved
                # (via __reduce__).
                self.assertIs(type(exc1), type(exc2))
                self.assert_exc_equal(grouped1, grouped2)
        sonst:
            self.assertEqual(args1, args2)

    def assert_exc_equal(self, exc1, exc2):
        self.assertIs(type(exc1), type(exc2))

        wenn type(exc1).__eq__ is nicht object.__eq__:
            self.assertEqual(exc1, exc2)

        self.assert_exc_args_equal(exc1, exc2)
        # XXX For now we do nicht preserve tracebacks.
        wenn exc1.__traceback__ is nicht Nichts:
            self.assertEqual(exc1.__traceback__, exc2.__traceback__)
        self.assertEqual(
            getattr(exc1, '__notes__', Nichts),
            getattr(exc2, '__notes__', Nichts),
        )
        # We assume there are no cycles.
        wenn exc1.__cause__ is Nichts:
            self.assertIs(exc1.__cause__, exc2.__cause__)
        sonst:
            self.assert_exc_equal(exc1.__cause__, exc2.__cause__)
        wenn exc1.__context__ is Nichts:
            self.assertIs(exc1.__context__, exc2.__context__)
        sonst:
            self.assert_exc_equal(exc1.__context__, exc2.__context__)

    def assert_equal_or_equalish(self, obj, expected):
        cls = type(expected)
        wenn cls.__eq__ is nicht object.__eq__:
            self.assertEqual(obj, expected)
        sowenn cls is types.FunctionType:
            self.assert_functions_equal(obj, expected)
        sowenn isinstance(expected, BaseException):
            self.assert_exc_equal(obj, expected)
        sowenn cls is types.MethodType:
            raise NotImplementedError(cls)
        sowenn cls is types.BuiltinMethodType:
            raise NotImplementedError(cls)
        sowenn cls is types.MethodWrapperType:
            raise NotImplementedError(cls)
        sowenn cls.__bases__ == (object,):
            self.assertEqual(obj.__dict__, expected.__dict__)
        sonst:
            raise NotImplementedError(cls)

    def get_xidata(self, obj, *, mode=Nichts):
        mode = self._resolve_mode(mode)
        return _testinternalcapi.get_crossinterp_data(obj, mode)

    def get_roundtrip(self, obj, *, mode=Nichts):
        mode = self._resolve_mode(mode)
        return self._get_roundtrip(obj, mode)

    def _get_roundtrip(self, obj, mode):
        xid = _testinternalcapi.get_crossinterp_data(obj, mode)
        return _testinternalcapi.restore_crossinterp_data(xid)

    def assert_roundtrip_identical(self, values, *, mode=Nichts):
        mode = self._resolve_mode(mode)
        fuer obj in values:
            mit self.subTest(repr(obj)):
                got = self._get_roundtrip(obj, mode)
                self.assertIs(got, obj)

    def assert_roundtrip_equal(self, values, *, mode=Nichts, expecttype=Nichts):
        mode = self._resolve_mode(mode)
        fuer obj in values:
            mit self.subTest(repr(obj)):
                got = self._get_roundtrip(obj, mode)
                wenn got is obj:
                    weiter
                self.assertIs(type(got),
                              type(obj) wenn expecttype is Nichts sonst expecttype)
                self.assert_equal_or_equalish(got, obj)

    def assert_roundtrip_equal_not_identical(self, values, *,
                                             mode=Nichts, expecttype=Nichts):
        mode = self._resolve_mode(mode)
        fuer obj in values:
            mit self.subTest(repr(obj)):
                got = self._get_roundtrip(obj, mode)
                self.assertIsNot(got, obj)
                self.assertIs(type(got),
                              type(obj) wenn expecttype is Nichts sonst expecttype)
                self.assert_equal_or_equalish(got, obj)

    def assert_roundtrip_not_equal(self, values, *,
                                   mode=Nichts, expecttype=Nichts):
        mode = self._resolve_mode(mode)
        fuer obj in values:
            mit self.subTest(repr(obj)):
                got = self._get_roundtrip(obj, mode)
                self.assertIsNot(got, obj)
                self.assertIs(type(got),
                              type(obj) wenn expecttype is Nichts sonst expecttype)
                self.assertNotEqual(got, obj)

    def assert_not_shareable(self, values, exctype=Nichts, *, mode=Nichts):
        mode = self._resolve_mode(mode)
        fuer obj in values:
            mit self.subTest(repr(obj)):
                mit self.assertRaises(NotShareableError) als cm:
                    _testinternalcapi.get_crossinterp_data(obj, mode)
                wenn exctype is nicht Nichts:
                    self.assertIsInstance(cm.exception.__cause__, exctype)

    def _resolve_mode(self, mode):
        wenn mode is Nichts:
            mode = self.MODE
        assert mode
        return mode


klasse PickleTests(_GetXIDataTests):

    MODE = 'pickle'

    def test_shareable(self):
        mit ignore_byteswarning():
            fuer obj in SHAREABLE:
                wenn obj in PICKLEABLE:
                    self.assert_roundtrip_equal([obj])
                sonst:
                    self.assert_not_shareable([obj])

    def test_not_shareable(self):
        mit ignore_byteswarning():
            fuer obj in NOT_SHAREABLE:
                wenn type(obj) is types.MappingProxyType:
                    self.assert_not_shareable([obj])
                sowenn obj in PICKLEABLE:
                    mit self.subTest(repr(obj)):
                        # We don't worry about checking the actual value.
                        # The other tests should cover that well enough.
                        got = self.get_roundtrip(obj)
                        self.assertIs(type(got), type(obj))
                sonst:
                    self.assert_not_shareable([obj])

    def test_list(self):
        self.assert_roundtrip_equal_not_identical([
            [],
            [1, 2, 3],
            [[1], (2,), {3: 4}],
        ])

    def test_dict(self):
        self.assert_roundtrip_equal_not_identical([
            {},
            {1: 7, 2: 8, 3: 9},
            {1: [1], 2: (2,), 3: {3: 4}},
        ])

    def test_set(self):
        self.assert_roundtrip_equal_not_identical([
            set(),
            {1, 2, 3},
            {frozenset({1}), (2,)},
        ])

    # classes

    def assert_class_defs_same(self, defs):
        # Unpickle relative to the unchanged original module.
        self.assert_roundtrip_identical(defs.TOP_CLASSES)

        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            wenn cls in defs.CLASSES_WITHOUT_EQUALITY:
                weiter
            instances.append(cls(*args))
        self.assert_roundtrip_equal_not_identical(instances)

        # these don't compare equal
        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            wenn cls nicht in defs.CLASSES_WITHOUT_EQUALITY:
                weiter
            instances.append(cls(*args))
        self.assert_roundtrip_equal(instances)

    def assert_class_defs_other_pickle(self, defs, mod):
        # Pickle relative to a different module than the original.
        fuer cls in defs.TOP_CLASSES:
            assert nicht hasattr(mod, cls.__name__), (cls, getattr(mod, cls.__name__))
        self.assert_not_shareable(defs.TOP_CLASSES)

        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            instances.append(cls(*args))
        self.assert_not_shareable(instances)

    def assert_class_defs_other_unpickle(self, defs, mod, *, fail=Falsch):
        # Unpickle relative to a different module than the original.
        fuer cls in defs.TOP_CLASSES:
            assert nicht hasattr(mod, cls.__name__), (cls, getattr(mod, cls.__name__))

        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            mit self.subTest(repr(cls)):
                setattr(mod, cls.__name__, cls)
                xid = self.get_xidata(cls)
                inst = cls(*args)
                instxid = self.get_xidata(inst)
                instances.append(
                        (cls, xid, inst, instxid))

        fuer cls, xid, inst, instxid in instances:
            mit self.subTest(repr(cls)):
                delattr(mod, cls.__name__)
                wenn fail:
                    mit self.assertRaises(NotShareableError):
                        _testinternalcapi.restore_crossinterp_data(xid)
                    weiter
                got = _testinternalcapi.restore_crossinterp_data(xid)
                self.assertIsNot(got, cls)
                self.assertNotEqual(got, cls)

                gotcls = got
                got = _testinternalcapi.restore_crossinterp_data(instxid)
                self.assertIsNot(got, inst)
                self.assertIs(type(got), gotcls)
                wenn cls in defs.CLASSES_WITHOUT_EQUALITY:
                    self.assertNotEqual(got, inst)
                sowenn cls in defs.BUILTIN_SUBCLASSES:
                    self.assertEqual(got, inst)
                sonst:
                    self.assertNotEqual(got, inst)

    def assert_class_defs_not_shareable(self, defs):
        self.assert_not_shareable(defs.TOP_CLASSES)

        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            instances.append(cls(*args))
        self.assert_not_shareable(instances)

    def test_user_class_normal(self):
        self.assert_class_defs_same(defs)

    def test_user_class_in___main__(self):
        mit using___main__() als mod:
            defs = load_defs(mod)
            self.assert_class_defs_same(defs)

    def test_user_class_not_in___main___with_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            assert defs.__file__
            mod.__file__ = defs.__file__
            self.assert_class_defs_not_shareable(defs)

    def test_user_class_not_in___main___without_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            defs.__file__ = Nichts
            mod.__file__ = Nichts
            self.assert_class_defs_not_shareable(defs)

    def test_user_class_not_in___main___unpickle_with_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            assert defs.__file__
            mod.__file__ = defs.__file__
            self.assert_class_defs_other_unpickle(defs, mod)

    def test_user_class_not_in___main___unpickle_without_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            defs.__file__ = Nichts
            mod.__file__ = Nichts
            self.assert_class_defs_other_unpickle(defs, mod, fail=Wahr)

    def test_user_class_in_module(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod)
            self.assert_class_defs_same(defs)

    def test_user_class_not_in_module_with_filename(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod.__name__)
            assert defs.__file__
            # For now, we only address this case fuer __main__.
            self.assert_class_defs_not_shareable(defs)

    def test_user_class_not_in_module_without_filename(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod.__name__)
            defs.__file__ = Nichts
            self.assert_class_defs_not_shareable(defs)

    def test_user_class_module_missing_then_imported(self):
        mit missing_defs_module('__spam__', prep=Wahr) als modname:
            defs = load_defs(modname)
            # For now, we only address this case fuer __main__.
            self.assert_class_defs_not_shareable(defs)

    def test_user_class_module_missing_not_available(self):
        mit missing_defs_module('__spam__') als modname:
            defs = load_defs(modname)
            self.assert_class_defs_not_shareable(defs)

    def test_nested_class(self):
        eggs = defs.EggsNested()
        mit self.assertRaises(NotShareableError):
            self.get_roundtrip(eggs)

    # functions

    def assert_func_defs_same(self, defs):
        # Unpickle relative to the unchanged original module.
        self.assert_roundtrip_identical(defs.TOP_FUNCTIONS)

    def assert_func_defs_other_pickle(self, defs, mod):
        # Pickle relative to a different module than the original.
        fuer func in defs.TOP_FUNCTIONS:
            assert nicht hasattr(mod, func.__name__), (getattr(mod, func.__name__),)
        self.assert_not_shareable(defs.TOP_FUNCTIONS)

    def assert_func_defs_other_unpickle(self, defs, mod, *, fail=Falsch):
        # Unpickle relative to a different module than the original.
        fuer func in defs.TOP_FUNCTIONS:
            assert nicht hasattr(mod, func.__name__), (getattr(mod, func.__name__),)

        captured = []
        fuer func in defs.TOP_FUNCTIONS:
            mit self.subTest(func):
                setattr(mod, func.__name__, func)
                xid = self.get_xidata(func)
                captured.append(
                        (func, xid))

        fuer func, xid in captured:
            mit self.subTest(func):
                delattr(mod, func.__name__)
                wenn fail:
                    mit self.assertRaises(NotShareableError):
                        _testinternalcapi.restore_crossinterp_data(xid)
                    weiter
                got = _testinternalcapi.restore_crossinterp_data(xid)
                self.assertIsNot(got, func)
                self.assertNotEqual(got, func)

    def assert_func_defs_not_shareable(self, defs):
        self.assert_not_shareable(defs.TOP_FUNCTIONS)

    def test_user_function_normal(self):
        self.assert_roundtrip_equal(defs.TOP_FUNCTIONS)
        self.assert_func_defs_same(defs)

    def test_user_func_in___main__(self):
        mit using___main__() als mod:
            defs = load_defs(mod)
            self.assert_func_defs_same(defs)

    def test_user_func_not_in___main___with_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            assert defs.__file__
            mod.__file__ = defs.__file__
            self.assert_func_defs_not_shareable(defs)

    def test_user_func_not_in___main___without_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            defs.__file__ = Nichts
            mod.__file__ = Nichts
            self.assert_func_defs_not_shareable(defs)

    def test_user_func_not_in___main___unpickle_with_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            assert defs.__file__
            mod.__file__ = defs.__file__
            self.assert_func_defs_other_unpickle(defs, mod)

    def test_user_func_not_in___main___unpickle_without_filename(self):
        mit using___main__() als mod:
            defs = load_defs('__main__')
            defs.__file__ = Nichts
            mod.__file__ = Nichts
            self.assert_func_defs_other_unpickle(defs, mod, fail=Wahr)

    def test_user_func_in_module(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod)
            self.assert_func_defs_same(defs)

    def test_user_func_not_in_module_with_filename(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod.__name__)
            assert defs.__file__
            # For now, we only address this case fuer __main__.
            self.assert_func_defs_not_shareable(defs)

    def test_user_func_not_in_module_without_filename(self):
        mit temp_module('__spam__') als mod:
            defs = load_defs(mod.__name__)
            defs.__file__ = Nichts
            self.assert_func_defs_not_shareable(defs)

    def test_user_func_module_missing_then_imported(self):
        mit missing_defs_module('__spam__', prep=Wahr) als modname:
            defs = load_defs(modname)
            # For now, we only address this case fuer __main__.
            self.assert_func_defs_not_shareable(defs)

    def test_user_func_module_missing_not_available(self):
        mit missing_defs_module('__spam__') als modname:
            defs = load_defs(modname)
            self.assert_func_defs_not_shareable(defs)

    def test_nested_function(self):
        self.assert_not_shareable(defs.NESTED_FUNCTIONS)

    # exceptions

    def test_user_exception_normal(self):
        self.assert_roundtrip_equal([
            defs.MimimalError('error!'),
        ])
        self.assert_roundtrip_equal_not_identical([
            defs.RichError('error!', 42),
        ])

    def test_builtin_exception(self):
        msg = 'error!'
        try:
            raise Exception
        except Exception als exc:
            caught = exc
        special = {
            BaseExceptionGroup: (msg, [caught]),
            ExceptionGroup: (msg, [caught]),
            UnicodeError: (Nichts, msg, Nichts, Nichts, Nichts),
            UnicodeEncodeError: ('utf-8', '', 1, 3, msg),
            UnicodeDecodeError: ('utf-8', b'', 1, 3, msg),
            UnicodeTranslateError: ('', 1, 3, msg),
        }
        exceptions = []
        fuer cls in EXCEPTION_TYPES:
            args = special.get(cls) oder (msg,)
            exceptions.append(cls(*args))

        self.assert_roundtrip_equal(exceptions)


klasse MarshalTests(_GetXIDataTests):

    MODE = 'marshal'

    def test_simple_builtin_singletons(self):
        self.assert_roundtrip_identical([
            Wahr,
            Falsch,
            Nichts,
            Ellipsis,
        ])
        self.assert_not_shareable([
            NotImplemented,
        ])

    def test_simple_builtin_objects(self):
        self.assert_roundtrip_equal([
            # int
            *range(-1, 258),
            sys.maxsize + 1,
            sys.maxsize,
            -sys.maxsize - 1,
            -sys.maxsize - 2,
            2**1000,
            # complex
            1+2j,
            # float
            0.0,
            1.1,
            -1.0,
            0.12345678,
            -0.12345678,
            # bytes
            *(i.to_bytes(2, 'little', signed=Wahr)
              fuer i in range(-1, 258)),
            b'hello world',
            # str
            'hello world',
            '你好世界',
            '',
        ])
        self.assert_not_shareable([
            OBJECT,
            types.SimpleNamespace(),
        ])

    def test_bytearray(self):
        # bytearray is special because it unmarshals to bytes, nicht bytearray.
        self.assert_roundtrip_equal([
            bytearray(),
            bytearray(b'hello world'),
        ], expecttype=bytes)

    def test_compound_immutable_builtin_objects(self):
        self.assert_roundtrip_equal([
            # tuple
            (),
            (1,),
            ("hello", "world"),
            (1, Wahr, "hello"),
            # frozenset
            frozenset([1, 2, 3]),
        ])
        # nested
        self.assert_roundtrip_equal([
            # tuple
            ((1,),),
            ((1, 2), (3, 4)),
            ((1, 2), (3, 4), (5, 6)),
            # frozenset
            frozenset([frozenset([1]), frozenset([2]), frozenset([3])]),
        ])

    def test_compound_mutable_builtin_objects(self):
        self.assert_roundtrip_equal([
            # list
            [],
            [1, 2, 3],
            # dict
            {},
            {1: 7, 2: 8, 3: 9},
            # set
            set(),
            {1, 2, 3},
        ])
        # nested
        self.assert_roundtrip_equal([
            [[1], [2], [3]],
            {1: {'a': Wahr}, 2: {'b': Falsch}},
            {(1, 2, 3,)},
        ])

    def test_compound_builtin_objects_with_bad_items(self):
        bogus = object()
        self.assert_not_shareable([
            (bogus,),
            frozenset([bogus]),
            [bogus],
            {bogus: Wahr},
            {Wahr: bogus},
            {bogus},
        ])

    def test_builtin_code(self):
        self.assert_roundtrip_equal([
            *(f.__code__ fuer f in defs.FUNCTIONS),
            *(f.__code__ fuer f in defs.FUNCTION_LIKE),
        ])

    def test_builtin_type(self):
        shareable = [
            StopIteration,
        ]
        types = BUILTIN_TYPES
        self.assert_not_shareable(cls fuer cls in types
                                  wenn cls nicht in shareable)
        self.assert_roundtrip_identical(cls fuer cls in types
                                        wenn cls in shareable)

    def test_builtin_function(self):
        functions = [
            len,
            sys.is_finalizing,
            sys.exit,
            _testinternalcapi.get_crossinterp_data,
        ]
        fuer func in functions:
            assert type(func) is types.BuiltinFunctionType, func

        self.assert_not_shareable(functions)

    def test_builtin_exception(self):
        msg = 'error!'
        try:
            raise Exception
        except Exception als exc:
            caught = exc
        special = {
            BaseExceptionGroup: (msg, [caught]),
            ExceptionGroup: (msg, [caught]),
#            UnicodeError: (Nichts, msg, Nichts, Nichts, Nichts),
            UnicodeEncodeError: ('utf-8', '', 1, 3, msg),
            UnicodeDecodeError: ('utf-8', b'', 1, 3, msg),
            UnicodeTranslateError: ('', 1, 3, msg),
        }
        exceptions = []
        fuer cls in EXCEPTION_TYPES:
            args = special.get(cls) oder (msg,)
            exceptions.append(cls(*args))

        self.assert_not_shareable(exceptions)
        # Note that StopIteration (the type) can be marshalled,
        # but its instances cannot.

    def test_module(self):
        assert type(sys) is types.ModuleType, type(sys)
        assert type(defs) is types.ModuleType, type(defs)
        assert type(unittest) is types.ModuleType, type(defs)

        assert 'emptymod' nicht in sys.modules
        mit import_helper.ready_to_import('emptymod', ''):
            importiere emptymod

        self.assert_not_shareable([
            sys,
            defs,
            unittest,
            emptymod,
        ])

    def test_user_class(self):
        self.assert_not_shareable(defs.TOP_CLASSES)

        instances = []
        fuer cls, args in defs.TOP_CLASSES.items():
            instances.append(cls(*args))
        self.assert_not_shareable(instances)

    def test_user_function(self):
        self.assert_not_shareable(defs.TOP_FUNCTIONS)

    def test_user_exception(self):
        self.assert_not_shareable([
            defs.MimimalError('error!'),
            defs.RichError('error!', 42),
        ])


klasse CodeTests(_GetXIDataTests):

    MODE = 'code'

    def test_function_code(self):
        self.assert_roundtrip_equal_not_identical([
            *(f.__code__ fuer f in defs.FUNCTIONS),
            *(f.__code__ fuer f in defs.FUNCTION_LIKE),
        ])

    def test_functions(self):
        self.assert_not_shareable([
            *defs.FUNCTIONS,
            *defs.FUNCTION_LIKE,
        ])

    def test_other_objects(self):
        self.assert_not_shareable([
            Nichts,
            Wahr,
            Falsch,
            Ellipsis,
            NotImplemented,
            9999,
            'spam',
            b'spam',
            (),
            [],
            {},
            object(),
        ])


klasse ShareableFuncTests(_GetXIDataTests):

    MODE = 'func'

    def test_stateless(self):
        self.assert_roundtrip_equal([
            *defs.STATELESS_FUNCTIONS,
            # Generators can be stateless too.
            *defs.FUNCTION_LIKE,
        ])

    def test_not_stateless(self):
        self.assert_not_shareable([
            *(f fuer f in defs.FUNCTIONS
              wenn f nicht in defs.STATELESS_FUNCTIONS),
        ])

    def test_other_objects(self):
        self.assert_not_shareable([
            Nichts,
            Wahr,
            Falsch,
            Ellipsis,
            NotImplemented,
            9999,
            'spam',
            b'spam',
            (),
            [],
            {},
            object(),
        ])


klasse PureShareableScriptTests(_GetXIDataTests):

    MODE = 'script-pure'

    VALID_SCRIPTS = [
        '',
        'spam',
        '# a comment',
        'drucke("spam")',
        'raise Exception("spam")',
        """if Wahr:
            do_something()
            """,
        """if Wahr:
            def spam(x):
                return x
            klasse Spam:
                def eggs(self):
                    return 42
            x = Spam().eggs()
            raise ValueError(spam(x))
            """,
    ]
    INVALID_SCRIPTS = [
        '    pass',  # IndentationError
        '----',  # SyntaxError
        """if Wahr:
            def spam():
                # no body
            spam()
            """,  # IndentationError
    ]

    def test_valid_str(self):
        self.assert_roundtrip_not_equal([
            *self.VALID_SCRIPTS,
        ], expecttype=types.CodeType)

    def test_invalid_str(self):
        self.assert_not_shareable([
            *self.INVALID_SCRIPTS,
        ])

    def test_valid_bytes(self):
        self.assert_roundtrip_not_equal([
            *(s.encode('utf8') fuer s in self.VALID_SCRIPTS),
        ], expecttype=types.CodeType)

    def test_invalid_bytes(self):
        self.assert_not_shareable([
            *(s.encode('utf8') fuer s in self.INVALID_SCRIPTS),
        ])

    def test_pure_script_code(self):
        self.assert_roundtrip_equal_not_identical([
            *(f.__code__ fuer f in defs.PURE_SCRIPT_FUNCTIONS),
        ])

    def test_impure_script_code(self):
        self.assert_not_shareable([
            *(f.__code__ fuer f in defs.SCRIPT_FUNCTIONS
              wenn f nicht in defs.PURE_SCRIPT_FUNCTIONS),
        ])

    def test_other_code(self):
        self.assert_not_shareable([
            *(f.__code__ fuer f in defs.FUNCTIONS
              wenn f nicht in defs.SCRIPT_FUNCTIONS),
            *(f.__code__ fuer f in defs.FUNCTION_LIKE),
        ])

    def test_pure_script_function(self):
        self.assert_roundtrip_not_equal([
            *defs.PURE_SCRIPT_FUNCTIONS,
        ], expecttype=types.CodeType)

    def test_impure_script_function(self):
        self.assert_not_shareable([
            *(f fuer f in defs.SCRIPT_FUNCTIONS
              wenn f nicht in defs.PURE_SCRIPT_FUNCTIONS),
        ])

    def test_other_function(self):
        self.assert_not_shareable([
            *(f fuer f in defs.FUNCTIONS
              wenn f nicht in defs.SCRIPT_FUNCTIONS),
            *defs.FUNCTION_LIKE,
        ])

    def test_other_objects(self):
        self.assert_not_shareable([
            Nichts,
            Wahr,
            Falsch,
            Ellipsis,
            NotImplemented,
            (),
            [],
            {},
            object(),
        ])


klasse ShareableScriptTests(PureShareableScriptTests):

    MODE = 'script'

    def test_impure_script_code(self):
        self.assert_roundtrip_equal_not_identical([
            *(f.__code__ fuer f in defs.SCRIPT_FUNCTIONS
              wenn f nicht in defs.PURE_SCRIPT_FUNCTIONS),
        ])

    def test_impure_script_function(self):
        self.assert_roundtrip_not_equal([
            *(f fuer f in defs.SCRIPT_FUNCTIONS
              wenn f nicht in defs.PURE_SCRIPT_FUNCTIONS),
        ], expecttype=types.CodeType)


klasse ShareableFallbackTests(_GetXIDataTests):

    MODE = 'fallback'

    def test_shareable(self):
        self.assert_roundtrip_equal(SHAREABLE)

    def test_not_shareable(self):
        okay = [
            *PICKLEABLE,
            *defs.STATELESS_FUNCTIONS,
            LAMBDA,
        ]
        ignored = [
            *TUPLES_WITHOUT_EQUALITY,
            OBJECT,
            METHOD,
            BUILTIN_METHOD,
            METHOD_WRAPPER,
        ]
        mit ignore_byteswarning():
            self.assert_roundtrip_equal([
                *(o fuer o in NOT_SHAREABLE
                  wenn o in okay und o nicht in ignored
                  und o is nicht MAPPING_PROXY_EMPTY),
            ])
            self.assert_roundtrip_not_equal([
                *(o fuer o in NOT_SHAREABLE
                  wenn o in ignored und o is nicht MAPPING_PROXY_EMPTY),
            ])
            self.assert_not_shareable([
                *(o fuer o in NOT_SHAREABLE wenn o nicht in okay),
                MAPPING_PROXY_EMPTY,
            ])


klasse ShareableTypeTests(_GetXIDataTests):

    MODE = 'xidata'

    def test_shareable(self):
        self.assert_roundtrip_equal(SHAREABLE)

    def test_singletons(self):
        self.assert_roundtrip_identical([
            Nichts,
            Wahr,
            Falsch,
        ])
        self.assert_not_shareable([
            Ellipsis,
            NotImplemented,
        ])

    def test_types(self):
        self.assert_roundtrip_equal([
            b'spam',
            9999,
        ])

    def test_bytes(self):
        values = (i.to_bytes(2, 'little', signed=Wahr)
                  fuer i in range(-1, 258))
        self.assert_roundtrip_equal(values)

    def test_strs(self):
        self.assert_roundtrip_equal([
            'hello world',
            '你好世界',
            '',
        ])

    def test_int(self):
        bounds = [sys.maxsize, -sys.maxsize - 1]
        values = itertools.chain(range(-1, 258), bounds)
        self.assert_roundtrip_equal(values)

    def test_non_shareable_int(self):
        ints = [
            sys.maxsize + 1,
            -sys.maxsize - 2,
            2**1000,
        ]
        self.assert_not_shareable(ints, OverflowError)

    def test_float(self):
        self.assert_roundtrip_equal([
            0.0,
            1.1,
            -1.0,
            0.12345678,
            -0.12345678,
        ])

    def test_tuple(self):
        self.assert_roundtrip_equal([
            (),
            (1,),
            ("hello", "world", ),
            (1, Wahr, "hello"),
        ])
        # Test nesting
        self.assert_roundtrip_equal([
            ((1,),),
            ((1, 2), (3, 4)),
            ((1, 2), (3, 4), (5, 6)),
        ])

    def test_tuples_containing_non_shareable_types(self):
        non_shareables = [
            EXCEPTION,
            OBJECT,
        ]
        fuer s in non_shareables:
            value = tuple([0, 1.0, s])
            mit self.subTest(repr(value)):
                mit self.assertRaises(NotShareableError):
                    self.get_xidata(value)
            # Check nested als well
            value = tuple([0, 1., (s,)])
            mit self.subTest("nested " + repr(value)):
                mit self.assertRaises(NotShareableError):
                    self.get_xidata(value)

    # The rest are nicht shareable.

    def test_not_shareable(self):
        self.assert_not_shareable(NOT_SHAREABLE)

    def test_object(self):
        self.assert_not_shareable([
            object(),
        ])

    def test_code(self):
        # types.CodeType
        self.assert_not_shareable([
            *(f.__code__ fuer f in defs.FUNCTIONS),
            *(f.__code__ fuer f in defs.FUNCTION_LIKE),
        ])

    def test_function_object(self):
        fuer func in defs.FUNCTIONS:
            assert type(func) is types.FunctionType, func
        assert type(defs.SpamOkay.okay) is types.FunctionType, func
        assert type(LAMBDA) is types.LambdaType

        self.assert_not_shareable([
            *defs.FUNCTIONS,
            defs.SpamOkay.okay,
            LAMBDA,
        ])

    def test_builtin_function(self):
        functions = [
            len,
            sys.is_finalizing,
            sys.exit,
            _testinternalcapi.get_crossinterp_data,
        ]
        fuer func in functions:
            assert type(func) is types.BuiltinFunctionType, func

        self.assert_not_shareable(functions)

    def test_function_like(self):
        self.assert_not_shareable(defs.FUNCTION_LIKE)
        self.assert_not_shareable(defs.FUNCTION_LIKE_APPLIED)

    def test_builtin_wrapper(self):
        _wrappers = {
            defs.SpamOkay().okay: types.MethodType,
            [].append: types.BuiltinMethodType,
            dict.__dict__['fromkeys']: types.ClassMethodDescriptorType,
            types.FunctionType.__code__: types.GetSetDescriptorType,
            types.FunctionType.__globals__: types.MemberDescriptorType,
            str.join: types.MethodDescriptorType,
            object().__str__: types.MethodWrapperType,
            object.__init__: types.WrapperDescriptorType,
        }
        fuer obj, expected in _wrappers.items():
            assert type(obj) is expected, (obj, expected)

        self.assert_not_shareable([
            *_wrappers,
            staticmethod(defs.SpamOkay.okay),
            classmethod(defs.SpamOkay.okay),
            property(defs.SpamOkay.okay),
        ])

    def test_module(self):
        assert type(sys) is types.ModuleType, type(sys)
        assert type(defs) is types.ModuleType, type(defs)
        assert type(unittest) is types.ModuleType, type(defs)

        assert 'emptymod' nicht in sys.modules
        mit import_helper.ready_to_import('emptymod', ''):
            importiere emptymod

        self.assert_not_shareable([
            sys,
            defs,
            unittest,
            emptymod,
        ])

    def test_class(self):
        self.assert_not_shareable(defs.CLASSES)

        instances = []
        fuer cls, args in defs.CLASSES.items():
            instances.append(cls(*args))
        self.assert_not_shareable(instances)

    def test_builtin_type(self):
        self.assert_not_shareable(BUILTIN_TYPES)

    def test_exception(self):
        self.assert_not_shareable([
            defs.MimimalError('error!'),
        ])

    def test_builtin_exception(self):
        msg = 'error!'
        try:
            raise Exception
        except Exception als exc:
            caught = exc
        special = {
            BaseExceptionGroup: (msg, [caught]),
            ExceptionGroup: (msg, [caught]),
#            UnicodeError: (Nichts, msg, Nichts, Nichts, Nichts),
            UnicodeEncodeError: ('utf-8', '', 1, 3, msg),
            UnicodeDecodeError: ('utf-8', b'', 1, 3, msg),
            UnicodeTranslateError: ('', 1, 3, msg),
        }
        exceptions = []
        fuer cls in EXCEPTION_TYPES:
            args = special.get(cls) oder (msg,)
            exceptions.append(cls(*args))

        self.assert_not_shareable(exceptions)

    def test_builtin_objects(self):
        ns = {}
        exec("""if Wahr:
            try:
                raise Exception
            except Exception als exc:
                TRACEBACK = exc.__traceback__
                FRAME = TRACEBACK.tb_frame
            """, ns, ns)

        self.assert_not_shareable([
            MAPPING_PROXY_EMPTY,
            types.SimpleNamespace(),
            # types.CellType
            types.CellType(),
            # types.FrameType
            ns['FRAME'],
            # types.TracebackType
            ns['TRACEBACK'],
        ])


wenn __name__ == '__main__':
    unittest.main()
