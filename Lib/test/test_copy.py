"""Unit tests fuer the copy module."""

importiere copy
importiere copyreg
importiere weakref
importiere abc
von operator importiere le, lt, ge, gt, eq, ne, attrgetter

importiere unittest
von test importiere support

order_comparisons = le, lt, ge, gt
equality_comparisons = eq, ne
comparisons = order_comparisons + equality_comparisons

klasse TestCopy(unittest.TestCase):

    # Attempt full line coverage of copy.py von top to bottom

    def test_exceptions(self):
        self.assertIs(copy.Error, copy.error)
        self.assertIsSubclass(copy.Error, Exception)

    # The copy() method

    def test_copy_basic(self):
        x = 42
        y = copy.copy(x)
        self.assertEqual(x, y)

    def test_copy_copy(self):
        klasse C(object):
            def __init__(self, foo):
                self.foo = foo
            def __copy__(self):
                gib C(self.foo)
        x = C(42)
        y = copy.copy(x)
        self.assertEqual(y.__class__, x.__class__)
        self.assertEqual(y.foo, x.foo)

    def test_copy_registry(self):
        klasse C(object):
            def __new__(cls, foo):
                obj = object.__new__(cls)
                obj.foo = foo
                gib obj
        def pickle_C(obj):
            gib (C, (obj.foo,))
        x = C(42)
        self.assertRaises(TypeError, copy.copy, x)
        copyreg.pickle(C, pickle_C, C)
        y = copy.copy(x)
        self.assertIsNot(x, y)
        self.assertEqual(type(y), C)
        self.assertEqual(y.foo, x.foo)

    def test_copy_reduce_ex(self):
        klasse C(object):
            def __reduce_ex__(self, proto):
                c.append(1)
                gib ""
            def __reduce__(self):
                self.fail("shouldn't call this")
        c = []
        x = C()
        y = copy.copy(x)
        self.assertIs(y, x)
        self.assertEqual(c, [1])

    def test_copy_reduce(self):
        klasse C(object):
            def __reduce__(self):
                c.append(1)
                gib ""
        c = []
        x = C()
        y = copy.copy(x)
        self.assertIs(y, x)
        self.assertEqual(c, [1])

    def test_copy_cant(self):
        klasse C(object):
            def __getattribute__(self, name):
                wenn name.startswith("__reduce"):
                    raise AttributeError(name)
                gib object.__getattribute__(self, name)
        x = C()
        self.assertRaises(copy.Error, copy.copy, x)

    # Type-specific _copy_xxx() methods

    def test_copy_atomic(self):
        klasse NewStyle:
            pass
        def f():
            pass
        klasse WithMetaclass(metaclass=abc.ABCMeta):
            pass
        tests = [Nichts, ..., NotImplemented,
                 42, 2**100, 3.14, Wahr, Falsch, 1j,
                 "hello", "hello\u1234", f.__code__,
                 b"world", bytes(range(256)), range(10), slice(1, 10, 2),
                 NewStyle, max, WithMetaclass, property()]
        fuer x in tests:
            self.assertIs(copy.copy(x), x)

    def test_copy_list(self):
        x = [1, 2, 3]
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        x = []
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)

    def test_copy_tuple(self):
        x = (1, 2, 3)
        self.assertIs(copy.copy(x), x)
        x = ()
        self.assertIs(copy.copy(x), x)
        x = (1, 2, 3, [])
        self.assertIs(copy.copy(x), x)

    def test_copy_dict(self):
        x = {"foo": 1, "bar": 2}
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        x = {}
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)

    def test_copy_set(self):
        x = {1, 2, 3}
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        x = set()
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)

    def test_copy_frozenset(self):
        x = frozenset({1, 2, 3})
        self.assertIs(copy.copy(x), x)
        x = frozenset()
        self.assertIs(copy.copy(x), x)

    def test_copy_bytearray(self):
        x = bytearray(b'abc')
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        x = bytearray()
        y = copy.copy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)

    def test_copy_inst_vanilla(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)

    def test_copy_inst_copy(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __copy__(self):
                gib C(self.foo)
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)

    def test_copy_inst_getinitargs(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getinitargs__(self):
                gib (self.foo,)
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)

    def test_copy_inst_getnewargs(self):
        klasse C(int):
            def __new__(cls, foo):
                self = int.__new__(cls)
                self.foo = foo
                gib self
            def __getnewargs__(self):
                gib self.foo,
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        y = copy.copy(x)
        self.assertIsInstance(y, C)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertEqual(y.foo, x.foo)

    def test_copy_inst_getnewargs_ex(self):
        klasse C(int):
            def __new__(cls, *, foo):
                self = int.__new__(cls)
                self.foo = foo
                gib self
            def __getnewargs_ex__(self):
                gib (), {'foo': self.foo}
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(foo=42)
        y = copy.copy(x)
        self.assertIsInstance(y, C)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertEqual(y.foo, x.foo)

    def test_copy_inst_getstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getstate__(self):
                gib {"foo": self.foo}
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)

    def test_copy_inst_setstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __setstate__(self, state):
                self.foo = state["foo"]
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)

    def test_copy_inst_getstate_setstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getstate__(self):
                gib self.foo
            def __setstate__(self, state):
                self.foo = state
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(42)
        self.assertEqual(copy.copy(x), x)
        # State mit boolean value is false (issue #25718)
        x = C(0.0)
        self.assertEqual(copy.copy(x), x)

    # The deepcopy() method

    def test_deepcopy_basic(self):
        x = 42
        y = copy.deepcopy(x)
        self.assertEqual(y, x)

    def test_deepcopy_memo(self):
        # Tests of reflexive objects are under type-specific sections below.
        # This tests only repetitions of objects.
        x = []
        x = [x, x]
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y[0], x[0])
        self.assertIs(y[0], y[1])

    def test_deepcopy_issubclass(self):
        # XXX Note: there's no way to test the TypeError coming out of
        # issubclass() -- this can only happen when an extension
        # module defines a "type" that doesn't formally inherit from
        # type.
        klasse Meta(type):
            pass
        klasse C(metaclass=Meta):
            pass
        self.assertEqual(copy.deepcopy(C), C)

    def test_deepcopy_deepcopy(self):
        klasse C(object):
            def __init__(self, foo):
                self.foo = foo
            def __deepcopy__(self, memo=Nichts):
                gib C(self.foo)
        x = C(42)
        y = copy.deepcopy(x)
        self.assertEqual(y.__class__, x.__class__)
        self.assertEqual(y.foo, x.foo)

    def test_deepcopy_registry(self):
        klasse C(object):
            def __new__(cls, foo):
                obj = object.__new__(cls)
                obj.foo = foo
                gib obj
        def pickle_C(obj):
            gib (C, (obj.foo,))
        x = C(42)
        self.assertRaises(TypeError, copy.deepcopy, x)
        copyreg.pickle(C, pickle_C, C)
        y = copy.deepcopy(x)
        self.assertIsNot(x, y)
        self.assertEqual(type(y), C)
        self.assertEqual(y.foo, x.foo)

    def test_deepcopy_reduce_ex(self):
        klasse C(object):
            def __reduce_ex__(self, proto):
                c.append(1)
                gib ""
            def __reduce__(self):
                self.fail("shouldn't call this")
        c = []
        x = C()
        y = copy.deepcopy(x)
        self.assertIs(y, x)
        self.assertEqual(c, [1])

    def test_deepcopy_reduce(self):
        klasse C(object):
            def __reduce__(self):
                c.append(1)
                gib ""
        c = []
        x = C()
        y = copy.deepcopy(x)
        self.assertIs(y, x)
        self.assertEqual(c, [1])

    def test_deepcopy_cant(self):
        klasse C(object):
            def __getattribute__(self, name):
                wenn name.startswith("__reduce"):
                    raise AttributeError(name)
                gib object.__getattribute__(self, name)
        x = C()
        self.assertRaises(copy.Error, copy.deepcopy, x)

    # Type-specific _deepcopy_xxx() methods

    def test_deepcopy_atomic(self):
        klasse NewStyle:
            pass
        def f():
            pass
        tests = [Nichts, ..., NotImplemented, 42, 2**100, 3.14, Wahr, Falsch, 1j,
                 b"bytes", "hello", "hello\u1234", f.__code__,
                 NewStyle, range(10), max, property()]
        fuer x in tests:
            self.assertIs(copy.deepcopy(x), x)

    def test_deepcopy_list(self):
        x = [[1, 2], 3]
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(x, y)
        self.assertIsNot(x[0], y[0])

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_deepcopy_reflexive_list(self):
        x = []
        x.append(x)
        y = copy.deepcopy(x)
        fuer op in comparisons:
            self.assertRaises(RecursionError, op, y, x)
        self.assertIsNot(y, x)
        self.assertIs(y[0], y)
        self.assertEqual(len(y), 1)

    def test_deepcopy_empty_tuple(self):
        x = ()
        y = copy.deepcopy(x)
        self.assertIs(x, y)

    def test_deepcopy_tuple(self):
        x = ([1, 2], 3)
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(x, y)
        self.assertIsNot(x[0], y[0])

    def test_deepcopy_tuple_of_immutables(self):
        x = ((1, 2), 3)
        y = copy.deepcopy(x)
        self.assertIs(x, y)

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_deepcopy_reflexive_tuple(self):
        x = ([],)
        x[0].append(x)
        y = copy.deepcopy(x)
        fuer op in comparisons:
            self.assertRaises(RecursionError, op, y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y[0], x[0])
        self.assertIs(y[0][0], y)

    def test_deepcopy_dict(self):
        x = {"foo": [1, 2], "bar": 3}
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(x, y)
        self.assertIsNot(x["foo"], y["foo"])

    @support.skip_emscripten_stack_overflow()
    @support.skip_wasi_stack_overflow()
    def test_deepcopy_reflexive_dict(self):
        x = {}
        x['foo'] = x
        y = copy.deepcopy(x)
        fuer op in order_comparisons:
            self.assertRaises(TypeError, op, y, x)
        fuer op in equality_comparisons:
            self.assertRaises(RecursionError, op, y, x)
        self.assertIsNot(y, x)
        self.assertIs(y['foo'], y)
        self.assertEqual(len(y), 1)

    def test_deepcopy_keepalive(self):
        memo = {}
        x = []
        y = copy.deepcopy(x, memo)
        self.assertIs(memo[id(memo)][0], x)

    def test_deepcopy_dont_memo_immutable(self):
        memo = {}
        x = [1, 2, 3, 4]
        y = copy.deepcopy(x, memo)
        self.assertEqual(y, x)
        # There's the entry fuer the new list, und the keep alive.
        self.assertEqual(len(memo), 2)

        memo = {}
        x = [(1, 2)]
        y = copy.deepcopy(x, memo)
        self.assertEqual(y, x)
        # Tuples mit immutable contents are immutable fuer deepcopy.
        self.assertEqual(len(memo), 2)

    def test_deepcopy_inst_vanilla(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_deepcopy(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __deepcopy__(self, memo):
                gib C(copy.deepcopy(self.foo, memo))
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_getinitargs(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getinitargs__(self):
                gib (self.foo,)
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_getnewargs(self):
        klasse C(int):
            def __new__(cls, foo):
                self = int.__new__(cls)
                self.foo = foo
                gib self
            def __getnewargs__(self):
                gib self.foo,
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertIsInstance(y, C)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertEqual(y.foo, x.foo)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_getnewargs_ex(self):
        klasse C(int):
            def __new__(cls, *, foo):
                self = int.__new__(cls)
                self.foo = foo
                gib self
            def __getnewargs_ex__(self):
                gib (), {'foo': self.foo}
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C(foo=[42])
        y = copy.deepcopy(x)
        self.assertIsInstance(y, C)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertEqual(y.foo, x.foo)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_getstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getstate__(self):
                gib {"foo": self.foo}
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_setstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __setstate__(self, state):
                self.foo = state["foo"]
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_inst_getstate_setstate(self):
        klasse C:
            def __init__(self, foo):
                self.foo = foo
            def __getstate__(self):
                gib self.foo
            def __setstate__(self, state):
                self.foo = state
            def __eq__(self, other):
                gib self.foo == other.foo
        x = C([42])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)
        # State mit boolean value is false (issue #25718)
        x = C([])
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_deepcopy_reflexive_inst(self):
        klasse C:
            pass
        x = C()
        x.foo = x
        y = copy.deepcopy(x)
        self.assertIsNot(y, x)
        self.assertIs(y.foo, y)

    # _reconstruct()

    def test_reconstruct_string(self):
        klasse C(object):
            def __reduce__(self):
                gib ""
        x = C()
        y = copy.copy(x)
        self.assertIs(y, x)
        y = copy.deepcopy(x)
        self.assertIs(y, x)

    def test_reconstruct_nostate(self):
        klasse C(object):
            def __reduce__(self):
                gib (C, ())
        x = C()
        x.foo = 42
        y = copy.copy(x)
        self.assertIs(y.__class__, x.__class__)
        y = copy.deepcopy(x)
        self.assertIs(y.__class__, x.__class__)

    def test_reconstruct_state(self):
        klasse C(object):
            def __reduce__(self):
                gib (C, (), self.__dict__)
            def __eq__(self, other):
                gib self.__dict__ == other.__dict__
        x = C()
        x.foo = [42]
        y = copy.copy(x)
        self.assertEqual(y, x)
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_reconstruct_state_setstate(self):
        klasse C(object):
            def __reduce__(self):
                gib (C, (), self.__dict__)
            def __setstate__(self, state):
                self.__dict__.update(state)
            def __eq__(self, other):
                gib self.__dict__ == other.__dict__
        x = C()
        x.foo = [42]
        y = copy.copy(x)
        self.assertEqual(y, x)
        y = copy.deepcopy(x)
        self.assertEqual(y, x)
        self.assertIsNot(y.foo, x.foo)

    def test_reconstruct_reflexive(self):
        klasse C(object):
            pass
        x = C()
        x.foo = x
        y = copy.deepcopy(x)
        self.assertIsNot(y, x)
        self.assertIs(y.foo, y)

    # Additions fuer Python 2.3 und pickle protocol 2

    def test_reduce_4tuple(self):
        klasse C(list):
            def __reduce__(self):
                gib (C, (), self.__dict__, iter(self))
            def __eq__(self, other):
                gib (list(self) == list(other) und
                        self.__dict__ == other.__dict__)
        x = C([[1, 2], 3])
        y = copy.copy(x)
        self.assertEqual(x, y)
        self.assertIsNot(x, y)
        self.assertIs(x[0], y[0])
        y = copy.deepcopy(x)
        self.assertEqual(x, y)
        self.assertIsNot(x, y)
        self.assertIsNot(x[0], y[0])

    def test_reduce_5tuple(self):
        klasse C(dict):
            def __reduce__(self):
                gib (C, (), self.__dict__, Nichts, self.items())
            def __eq__(self, other):
                gib (dict(self) == dict(other) und
                        self.__dict__ == other.__dict__)
        x = C([("foo", [1, 2]), ("bar", 3)])
        y = copy.copy(x)
        self.assertEqual(x, y)
        self.assertIsNot(x, y)
        self.assertIs(x["foo"], y["foo"])
        y = copy.deepcopy(x)
        self.assertEqual(x, y)
        self.assertIsNot(x, y)
        self.assertIsNot(x["foo"], y["foo"])

    def test_reduce_6tuple(self):
        def state_setter(*args, **kwargs):
            self.fail("shouldn't call this")
        klasse C:
            def __reduce__(self):
                gib C, (), self.__dict__, Nichts, Nichts, state_setter
        x = C()
        mit self.assertRaises(TypeError):
            copy.copy(x)
        mit self.assertRaises(TypeError):
            copy.deepcopy(x)

    def test_reduce_6tuple_none(self):
        klasse C:
            def __reduce__(self):
                gib C, (), self.__dict__, Nichts, Nichts, Nichts
        x = C()
        mit self.assertRaises(TypeError):
            copy.copy(x)
        mit self.assertRaises(TypeError):
            copy.deepcopy(x)

    def test_copy_slots(self):
        klasse C(object):
            __slots__ = ["foo"]
        x = C()
        x.foo = [42]
        y = copy.copy(x)
        self.assertIs(x.foo, y.foo)

    def test_deepcopy_slots(self):
        klasse C(object):
            __slots__ = ["foo"]
        x = C()
        x.foo = [42]
        y = copy.deepcopy(x)
        self.assertEqual(x.foo, y.foo)
        self.assertIsNot(x.foo, y.foo)

    def test_deepcopy_dict_subclass(self):
        klasse C(dict):
            def __init__(self, d=Nichts):
                wenn nicht d:
                    d = {}
                self._keys = list(d.keys())
                super().__init__(d)
            def __setitem__(self, key, item):
                super().__setitem__(key, item)
                wenn key nicht in self._keys:
                    self._keys.append(key)
        x = C(d={'foo':0})
        y = copy.deepcopy(x)
        self.assertEqual(x, y)
        self.assertEqual(x._keys, y._keys)
        self.assertIsNot(x, y)
        x['bar'] = 1
        self.assertNotEqual(x, y)
        self.assertNotEqual(x._keys, y._keys)

    def test_copy_list_subclass(self):
        klasse C(list):
            pass
        x = C([[1, 2], 3])
        x.foo = [4, 5]
        y = copy.copy(x)
        self.assertEqual(list(x), list(y))
        self.assertEqual(x.foo, y.foo)
        self.assertIs(x[0], y[0])
        self.assertIs(x.foo, y.foo)

    def test_deepcopy_list_subclass(self):
        klasse C(list):
            pass
        x = C([[1, 2], 3])
        x.foo = [4, 5]
        y = copy.deepcopy(x)
        self.assertEqual(list(x), list(y))
        self.assertEqual(x.foo, y.foo)
        self.assertIsNot(x[0], y[0])
        self.assertIsNot(x.foo, y.foo)

    def test_copy_tuple_subclass(self):
        klasse C(tuple):
            pass
        x = C([1, 2, 3])
        self.assertEqual(tuple(x), (1, 2, 3))
        y = copy.copy(x)
        self.assertEqual(tuple(y), (1, 2, 3))

    def test_deepcopy_tuple_subclass(self):
        klasse C(tuple):
            pass
        x = C([[1, 2], 3])
        self.assertEqual(tuple(x), ([1, 2], 3))
        y = copy.deepcopy(x)
        self.assertEqual(tuple(y), ([1, 2], 3))
        self.assertIsNot(x, y)
        self.assertIsNot(x[0], y[0])

    def test_getstate_exc(self):
        klasse EvilState(object):
            def __getstate__(self):
                raise ValueError("ain't got no stickin' state")
        self.assertRaises(ValueError, copy.copy, EvilState())

    def test_copy_function(self):
        self.assertEqual(copy.copy(global_foo), global_foo)
        def foo(x, y): gib x+y
        self.assertEqual(copy.copy(foo), foo)
        bar = lambda: Nichts
        self.assertEqual(copy.copy(bar), bar)

    def test_deepcopy_function(self):
        self.assertEqual(copy.deepcopy(global_foo), global_foo)
        def foo(x, y): gib x+y
        self.assertEqual(copy.deepcopy(foo), foo)
        bar = lambda: Nichts
        self.assertEqual(copy.deepcopy(bar), bar)

    def _check_weakref(self, _copy):
        klasse C(object):
            pass
        obj = C()
        x = weakref.ref(obj)
        y = _copy(x)
        self.assertIs(y, x)
        del obj
        y = _copy(x)
        self.assertIs(y, x)

    def test_copy_weakref(self):
        self._check_weakref(copy.copy)

    def test_deepcopy_weakref(self):
        self._check_weakref(copy.deepcopy)

    def _check_copy_weakdict(self, _dicttype):
        klasse C(object):
            pass
        a, b, c, d = [C() fuer i in range(4)]
        u = _dicttype()
        u[a] = b
        u[c] = d
        v = copy.copy(u)
        self.assertIsNot(v, u)
        self.assertEqual(v, u)
        self.assertEqual(v[a], b)
        self.assertEqual(v[c], d)
        self.assertEqual(len(v), 2)
        del c, d
        support.gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(v), 1)
        x, y = C(), C()
        # The underlying containers are decoupled
        v[x] = y
        self.assertNotIn(x, u)

    def test_copy_weakkeydict(self):
        self._check_copy_weakdict(weakref.WeakKeyDictionary)

    def test_copy_weakvaluedict(self):
        self._check_copy_weakdict(weakref.WeakValueDictionary)

    def test_deepcopy_weakkeydict(self):
        klasse C(object):
            def __init__(self, i):
                self.i = i
        a, b, c, d = [C(i) fuer i in range(4)]
        u = weakref.WeakKeyDictionary()
        u[a] = b
        u[c] = d
        # Keys aren't copied, values are
        v = copy.deepcopy(u)
        self.assertNotEqual(v, u)
        self.assertEqual(len(v), 2)
        self.assertIsNot(v[a], b)
        self.assertIsNot(v[c], d)
        self.assertEqual(v[a].i, b.i)
        self.assertEqual(v[c].i, d.i)
        del c
        support.gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(v), 1)

    def test_deepcopy_weakvaluedict(self):
        klasse C(object):
            def __init__(self, i):
                self.i = i
        a, b, c, d = [C(i) fuer i in range(4)]
        u = weakref.WeakValueDictionary()
        u[a] = b
        u[c] = d
        # Keys are copied, values aren't
        v = copy.deepcopy(u)
        self.assertNotEqual(v, u)
        self.assertEqual(len(v), 2)
        (x, y), (z, t) = sorted(v.items(), key=lambda pair: pair[0].i)
        self.assertIsNot(x, a)
        self.assertEqual(x.i, a.i)
        self.assertIs(y, b)
        self.assertIsNot(z, c)
        self.assertEqual(z.i, c.i)
        self.assertIs(t, d)
        del x, y, z, t
        del d
        support.gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(v), 1)

    def test_deepcopy_bound_method(self):
        klasse Foo(object):
            def m(self):
                pass
        f = Foo()
        f.b = f.m
        g = copy.deepcopy(f)
        self.assertEqual(g.m, g.b)
        self.assertIs(g.b.__self__, g)
        g.b()


klasse TestReplace(unittest.TestCase):

    def test_unsupported(self):
        self.assertRaises(TypeError, copy.replace, 1)
        self.assertRaises(TypeError, copy.replace, [])
        self.assertRaises(TypeError, copy.replace, {})
        def f(): pass
        self.assertRaises(TypeError, copy.replace, f)
        klasse A: pass
        self.assertRaises(TypeError, copy.replace, A)
        self.assertRaises(TypeError, copy.replace, A())

    def test_replace_method(self):
        klasse A:
            def __new__(cls, x, y=0):
                self = object.__new__(cls)
                self.x = x
                self.y = y
                gib self

            def __init__(self, *args, **kwargs):
                self.z = self.x + self.y

            def __replace__(self, **changes):
                x = changes.get('x', self.x)
                y = changes.get('y', self.y)
                gib type(self)(x, y)

        attrs = attrgetter('x', 'y', 'z')
        a = A(11, 22)
        self.assertEqual(attrs(copy.replace(a)), (11, 22, 33))
        self.assertEqual(attrs(copy.replace(a, x=1)), (1, 22, 23))
        self.assertEqual(attrs(copy.replace(a, y=2)), (11, 2, 13))
        self.assertEqual(attrs(copy.replace(a, x=1, y=2)), (1, 2, 3))

    def test_namedtuple(self):
        von collections importiere namedtuple
        von typing importiere NamedTuple
        PointFromCall = namedtuple('Point', 'x y', defaults=(0,))
        klasse PointFromInheritance(PointFromCall):
            pass
        klasse PointFromClass(NamedTuple):
            x: int
            y: int = 0
        fuer Point in (PointFromCall, PointFromInheritance, PointFromClass):
            mit self.subTest(Point=Point):
                p = Point(11, 22)
                self.assertIsInstance(p, Point)
                self.assertEqual(copy.replace(p), (11, 22))
                self.assertIsInstance(copy.replace(p), Point)
                self.assertEqual(copy.replace(p, x=1), (1, 22))
                self.assertEqual(copy.replace(p, y=2), (11, 2))
                self.assertEqual(copy.replace(p, x=1, y=2), (1, 2))
                mit self.assertRaisesRegex(TypeError, 'unexpected field name'):
                    copy.replace(p, x=1, error=2)

    def test_dataclass(self):
        von dataclasses importiere dataclass
        @dataclass
        klasse C:
            x: int
            y: int = 0

        attrs = attrgetter('x', 'y')
        c = C(11, 22)
        self.assertEqual(attrs(copy.replace(c)), (11, 22))
        self.assertEqual(attrs(copy.replace(c, x=1)), (1, 22))
        self.assertEqual(attrs(copy.replace(c, y=2)), (11, 2))
        self.assertEqual(attrs(copy.replace(c, x=1, y=2)), (1, 2))
        mit self.assertRaisesRegex(TypeError, 'unexpected keyword argument'):
            copy.replace(c, x=1, error=2)


klasse MiscTestCase(unittest.TestCase):
    def test__all__(self):
        support.check__all__(self, copy, not_exported={"dispatch_table", "error"})

def global_foo(x, y): gib x+y


wenn __name__ == "__main__":
    unittest.main()
