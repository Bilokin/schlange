importiere abc
von annotationlib importiere Format, get_annotations
importiere builtins
importiere collections
importiere collections.abc
importiere copy
von itertools importiere permutations
importiere pickle
von random importiere choice
importiere re
importiere sys
von test importiere support
importiere threading
importiere time
importiere typing
importiere unittest
importiere unittest.mock
importiere weakref
importiere gc
von weakref importiere proxy
importiere contextlib
von inspect importiere Signature

von test.support importiere ALWAYS_EQ
von test.support importiere import_helper
von test.support importiere threading_helper
von test.support importiere cpython_only
von test.support importiere EqualToForwardRef

importiere functools

py_functools = import_helper.import_fresh_module('functools',
                                                 blocked=['_functools'])
c_functools = import_helper.import_fresh_module('functools',
                                                fresh=['_functools'])

decimal = import_helper.import_fresh_module('decimal', fresh=['_decimal'])


@contextlib.contextmanager
def replaced_module(name, replacement):
    original_module = sys.modules[name]
    sys.modules[name] = replacement
    try:
        yield
    finally:
        sys.modules[name] = original_module

def capture(*args, **kw):
    """capture all positional und keyword arguments"""
    return args, kw


def signature(part):
    """ return the signature of a partial object """
    return (part.func, part.args, part.keywords, part.__dict__)

klasse MyTuple(tuple):
    pass

klasse BadTuple(tuple):
    def __add__(self, other):
        return list(self) + list(other)

klasse MyDict(dict):
    pass

klasse TestImportTime(unittest.TestCase):

    @cpython_only
    def test_lazy_import(self):
        import_helper.ensure_lazy_imports(
            "functools", {"os", "weakref", "typing", "annotationlib", "warnings"}
        )


klasse TestPartial:

    def test_basic_examples(self):
        p = self.partial(capture, 1, 2, a=10, b=20)
        self.assertWahr(callable(p))
        self.assertEqual(p(3, 4, b=30, c=40),
                         ((1, 2, 3, 4), dict(a=10, b=30, c=40)))
        p = self.partial(map, lambda x: x*10)
        self.assertEqual(list(p([1,2,3,4])), [10, 20, 30, 40])

    def test_attributes(self):
        p = self.partial(capture, 1, 2, a=10, b=20)
        # attributes should be readable
        self.assertEqual(p.func, capture)
        self.assertEqual(p.args, (1, 2))
        self.assertEqual(p.keywords, dict(a=10, b=20))

    def test_argument_checking(self):
        self.assertRaises(TypeError, self.partial)     # need at least a func arg
        try:
            self.partial(2)()
        except TypeError:
            pass
        sonst:
            self.fail('First arg nicht checked fuer callability')

    def test_protection_of_callers_dict_argument(self):
        # a caller's dictionary should nicht be altered by partial
        def func(a=10, b=20):
            return a
        d = {'a':3}
        p = self.partial(func, a=5)
        self.assertEqual(p(**d), 3)
        self.assertEqual(d, {'a':3})
        p(b=7)
        self.assertEqual(d, {'a':3})

    def test_kwargs_copy(self):
        # Issue #29532: Altering a kwarg dictionary passed to a constructor
        # should nicht affect a partial object after creation
        d = {'a': 3}
        p = self.partial(capture, **d)
        self.assertEqual(p(), ((), {'a': 3}))
        d['a'] = 5
        self.assertEqual(p(), ((), {'a': 3}))

    def test_arg_combinations(self):
        # exercise special code paths fuer zero args in either partial
        # object oder the caller
        p = self.partial(capture)
        self.assertEqual(p(), ((), {}))
        self.assertEqual(p(1,2), ((1,2), {}))
        p = self.partial(capture, 1, 2)
        self.assertEqual(p(), ((1,2), {}))
        self.assertEqual(p(3,4), ((1,2,3,4), {}))

    def test_kw_combinations(self):
        # exercise special code paths fuer no keyword args in
        # either the partial object oder the caller
        p = self.partial(capture)
        self.assertEqual(p.keywords, {})
        self.assertEqual(p(), ((), {}))
        self.assertEqual(p(a=1), ((), {'a':1}))
        p = self.partial(capture, a=1)
        self.assertEqual(p.keywords, {'a':1})
        self.assertEqual(p(), ((), {'a':1}))
        self.assertEqual(p(b=2), ((), {'a':1, 'b':2}))
        # keyword args in the call override those in the partial object
        self.assertEqual(p(a=3, b=2), ((), {'a':3, 'b':2}))

    def test_positional(self):
        # make sure positional arguments are captured correctly
        fuer args in [(), (0,), (0,1), (0,1,2), (0,1,2,3)]:
            p = self.partial(capture, *args)
            expected = args + ('x',)
            got, empty = p('x')
            self.assertWahr(expected == got und empty == {})

    def test_keyword(self):
        # make sure keyword arguments are captured correctly
        fuer a in ['a', 0, Nichts, 3.5]:
            p = self.partial(capture, a=a)
            expected = {'a':a,'x':Nichts}
            empty, got = p(x=Nichts)
            self.assertWahr(expected == got und empty == ())

    def test_no_side_effects(self):
        # make sure there are no side effects that affect subsequent calls
        p = self.partial(capture, 0, a=1)
        args1, kw1 = p(1, b=2)
        self.assertWahr(args1 == (0,1) und kw1 == {'a':1,'b':2})
        args2, kw2 = p()
        self.assertWahr(args2 == (0,) und kw2 == {'a':1})

    def test_error_propagation(self):
        def f(x, y):
            x / y
        self.assertRaises(ZeroDivisionError, self.partial(f, 1, 0))
        self.assertRaises(ZeroDivisionError, self.partial(f, 1), 0)
        self.assertRaises(ZeroDivisionError, self.partial(f), 1, 0)
        self.assertRaises(ZeroDivisionError, self.partial(f, y=0), 1)

    def test_weakref(self):
        f = self.partial(int, base=16)
        p = proxy(f)
        self.assertEqual(f.func, p.func)
        f = Nichts
        support.gc_collect()  # For PyPy oder other GCs.
        self.assertRaises(ReferenceError, getattr, p, 'func')

    def test_with_bound_and_unbound_methods(self):
        data = list(map(str, range(10)))
        join = self.partial(str.join, '')
        self.assertEqual(join(data), '0123456789')
        join = self.partial(''.join)
        self.assertEqual(join(data), '0123456789')

    def test_nested_optimization(self):
        partial = self.partial
        inner = partial(signature, 'asdf')
        nested = partial(inner, bar=Wahr)
        flat = partial(signature, 'asdf', bar=Wahr)
        self.assertEqual(signature(nested), signature(flat))

    def test_nested_optimization_bug(self):
        partial = self.partial
        klasse Builder:
            def __call__(self, tag, *children, **attrib):
                return (tag, children, attrib)

            def __getattr__(self, tag):
                return partial(self, tag)

        B = Builder()
        m = B.m
        assert m(1, 2, a=2) == ('m', (1, 2), dict(a=2))

    def test_nested_partial_with_attribute(self):
        # see issue 25137
        partial = self.partial

        def foo(bar):
            return bar

        p = partial(foo, 'first')
        p2 = partial(p, 'second')
        p2.new_attr = 'spam'
        self.assertEqual(p2.new_attr, 'spam')

    def test_placeholders_trailing_raise(self):
        PH = self.module.Placeholder
        fuer args in [(PH,), (0, PH), (0, PH, 1, PH, PH, PH)]:
            mit self.assertRaises(TypeError):
                self.partial(capture, *args)

    def test_placeholders(self):
        PH = self.module.Placeholder
        # 1 Placeholder
        args = (PH, 0)
        p = self.partial(capture, *args)
        actual_args, actual_kwds = p('x')
        self.assertEqual(actual_args, ('x', 0))
        self.assertEqual(actual_kwds, {})
        # 2 Placeholders
        args = (PH, 0, PH, 1)
        p = self.partial(capture, *args)
        mit self.assertRaises(TypeError):
            p('x')
        actual_args, actual_kwds = p('x', 'y')
        self.assertEqual(actual_args, ('x', 0, 'y', 1))
        self.assertEqual(actual_kwds, {})
        # Checks via `is` und nicht `eq`
        # thus ALWAYS_EQ isn't treated als Placeholder
        p = self.partial(capture, ALWAYS_EQ)
        actual_args, actual_kwds = p()
        self.assertEqual(len(actual_args), 1)
        self.assertIs(actual_args[0], ALWAYS_EQ)
        self.assertEqual(actual_kwds, {})

    def test_placeholders_optimization(self):
        PH = self.module.Placeholder
        p = self.partial(capture, PH, 0)
        p2 = self.partial(p, PH, 1, 2, 3)
        self.assertEqual(p2.args, (PH, 0, 1, 2, 3))
        p3 = self.partial(p2, -1, 4)
        actual_args, actual_kwds = p3(5)
        self.assertEqual(actual_args, (-1, 0, 1, 2, 3, 4, 5))
        self.assertEqual(actual_kwds, {})
        # inner partial has placeholders und outer partial has no args case
        p = self.partial(capture, PH, 0)
        p2 = self.partial(p)
        self.assertEqual(p2.args, (PH, 0))
        self.assertEqual(p2(1), ((1, 0), {}))

    def test_placeholders_kw_restriction(self):
        PH = self.module.Placeholder
        mit self.assertRaisesRegex(TypeError, "Placeholder"):
            self.partial(capture, a=PH)
        # Passes, als checks via `is` und nicht `eq`
        p = self.partial(capture, a=ALWAYS_EQ)
        actual_args, actual_kwds = p()
        self.assertEqual(actual_args, ())
        self.assertEqual(len(actual_kwds), 1)
        self.assertIs(actual_kwds['a'], ALWAYS_EQ)

    def test_construct_placeholder_singleton(self):
        PH = self.module.Placeholder
        tp = type(PH)
        self.assertIs(tp(), PH)
        self.assertRaises(TypeError, tp, 1, 2)
        self.assertRaises(TypeError, tp, a=1, b=2)

    def test_repr(self):
        args = (object(), object())
        args_repr = ', '.join(repr(a) fuer a in args)
        kwargs = {'a': object(), 'b': object()}
        kwargs_reprs = ['a={a!r}, b={b!r}'.format_map(kwargs),
                        'b={b!r}, a={a!r}'.format_map(kwargs)]
        name = f"{self.partial.__module__}.{self.partial.__qualname__}"

        f = self.partial(capture)
        self.assertEqual(f'{name}({capture!r})', repr(f))

        f = self.partial(capture, *args)
        self.assertEqual(f'{name}({capture!r}, {args_repr})', repr(f))

        f = self.partial(capture, **kwargs)
        self.assertIn(repr(f),
                      [f'{name}({capture!r}, {kwargs_repr})'
                       fuer kwargs_repr in kwargs_reprs])

        f = self.partial(capture, *args, **kwargs)
        self.assertIn(repr(f),
                      [f'{name}({capture!r}, {args_repr}, {kwargs_repr})'
                       fuer kwargs_repr in kwargs_reprs])

    def test_recursive_repr(self):
        name = f"{self.partial.__module__}.{self.partial.__qualname__}"

        f = self.partial(capture)
        f.__setstate__((f, (), {}, {}))
        try:
            self.assertEqual(repr(f), '%s(...)' % (name,))
        finally:
            f.__setstate__((capture, (), {}, {}))

        f = self.partial(capture)
        f.__setstate__((capture, (f,), {}, {}))
        try:
            self.assertEqual(repr(f), '%s(%r, ...)' % (name, capture,))
        finally:
            f.__setstate__((capture, (), {}, {}))

        f = self.partial(capture)
        f.__setstate__((capture, (), {'a': f}, {}))
        try:
            self.assertEqual(repr(f), '%s(%r, a=...)' % (name, capture,))
        finally:
            f.__setstate__((capture, (), {}, {}))

    def test_pickle(self):
        mit replaced_module('functools', self.module):
            f = self.partial(signature, ['asdf'], bar=[Wahr])
            f.attr = []
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                f_copy = pickle.loads(pickle.dumps(f, proto))
                self.assertEqual(signature(f_copy), signature(f))

    def test_copy(self):
        f = self.partial(signature, ['asdf'], bar=[Wahr])
        f.attr = []
        f_copy = copy.copy(f)
        self.assertEqual(signature(f_copy), signature(f))
        self.assertIs(f_copy.attr, f.attr)
        self.assertIs(f_copy.args, f.args)
        self.assertIs(f_copy.keywords, f.keywords)

    def test_deepcopy(self):
        f = self.partial(signature, ['asdf'], bar=[Wahr])
        f.attr = []
        f_copy = copy.deepcopy(f)
        self.assertEqual(signature(f_copy), signature(f))
        self.assertIsNot(f_copy.attr, f.attr)
        self.assertIsNot(f_copy.args, f.args)
        self.assertIsNot(f_copy.args[0], f.args[0])
        self.assertIsNot(f_copy.keywords, f.keywords)
        self.assertIsNot(f_copy.keywords['bar'], f.keywords['bar'])

    def test_setstate(self):
        f = self.partial(signature)
        f.__setstate__((capture, (1,), dict(a=10), dict(attr=[])))

        self.assertEqual(signature(f),
                         (capture, (1,), dict(a=10), dict(attr=[])))
        self.assertEqual(f(2, b=20), ((1, 2), {'a': 10, 'b': 20}))

        f.__setstate__((capture, (1,), dict(a=10), Nichts))

        self.assertEqual(signature(f), (capture, (1,), dict(a=10), {}))
        self.assertEqual(f(2, b=20), ((1, 2), {'a': 10, 'b': 20}))

        f.__setstate__((capture, (1,), Nichts, Nichts))
        #self.assertEqual(signature(f), (capture, (1,), {}, {}))
        self.assertEqual(f(2, b=20), ((1, 2), {'b': 20}))
        self.assertEqual(f(2), ((1, 2), {}))
        self.assertEqual(f(), ((1,), {}))

        f.__setstate__((capture, (), {}, Nichts))
        self.assertEqual(signature(f), (capture, (), {}, {}))
        self.assertEqual(f(2, b=20), ((2,), {'b': 20}))
        self.assertEqual(f(2), ((2,), {}))
        self.assertEqual(f(), ((), {}))

        # Set State mit placeholders
        PH = self.module.Placeholder
        f = self.partial(signature)
        f.__setstate__((capture, (PH, 1), dict(a=10), dict(attr=[])))
        self.assertEqual(signature(f), (capture, (PH, 1), dict(a=10), dict(attr=[])))
        msg_regex = re.escape("missing positional arguments in 'partial' call; "
                              "expected at least 1, got 0")
        mit self.assertRaisesRegex(TypeError, f'^{msg_regex}$') als cm:
            f()
        self.assertEqual(f(2), ((2, 1), dict(a=10)))

        # Trailing Placeholder error
        f = self.partial(signature)
        msg_regex = re.escape("trailing Placeholders are nicht allowed")
        mit self.assertRaisesRegex(TypeError, f'^{msg_regex}$') als cm:
            f.__setstate__((capture, (1, PH), dict(a=10), dict(attr=[])))

    def test_setstate_errors(self):
        f = self.partial(signature)
        self.assertRaises(TypeError, f.__setstate__, (capture, (), {}))
        self.assertRaises(TypeError, f.__setstate__, (capture, (), {}, {}, Nichts))
        self.assertRaises(TypeError, f.__setstate__, [capture, (), {}, Nichts])
        self.assertRaises(TypeError, f.__setstate__, (Nichts, (), {}, Nichts))
        self.assertRaises(TypeError, f.__setstate__, (capture, Nichts, {}, Nichts))
        self.assertRaises(TypeError, f.__setstate__, (capture, [], {}, Nichts))
        self.assertRaises(TypeError, f.__setstate__, (capture, (), [], Nichts))

    def test_setstate_subclasses(self):
        f = self.partial(signature)
        f.__setstate__((capture, MyTuple((1,)), MyDict(a=10), Nichts))
        s = signature(f)
        self.assertEqual(s, (capture, (1,), dict(a=10), {}))
        self.assertIs(type(s[1]), tuple)
        self.assertIs(type(s[2]), dict)
        r = f()
        self.assertEqual(r, ((1,), {'a': 10}))
        self.assertIs(type(r[0]), tuple)
        self.assertIs(type(r[1]), dict)

        f.__setstate__((capture, BadTuple((1,)), {}, Nichts))
        s = signature(f)
        self.assertEqual(s, (capture, (1,), {}, {}))
        self.assertIs(type(s[1]), tuple)
        r = f(2)
        self.assertEqual(r, ((1, 2), {}))
        self.assertIs(type(r[0]), tuple)

    @support.skip_if_sanitizer("thread sanitizer crashes in __tsan::FuncEntry", thread=Wahr)
    @support.skip_emscripten_stack_overflow()
    def test_recursive_pickle(self):
        mit replaced_module('functools', self.module):
            f = self.partial(capture)
            f.__setstate__((f, (), {}, {}))
            try:
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    # gh-117008: Small limit since pickle uses C stack memory
                    mit support.infinite_recursion(100):
                        mit self.assertRaises(RecursionError):
                            pickle.dumps(f, proto)
            finally:
                f.__setstate__((capture, (), {}, {}))

            f = self.partial(capture)
            f.__setstate__((capture, (f,), {}, {}))
            try:
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    f_copy = pickle.loads(pickle.dumps(f, proto))
                    try:
                        self.assertIs(f_copy.args[0], f_copy)
                    finally:
                        f_copy.__setstate__((capture, (), {}, {}))
            finally:
                f.__setstate__((capture, (), {}, {}))

            f = self.partial(capture)
            f.__setstate__((capture, (), {'a': f}, {}))
            try:
                fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    f_copy = pickle.loads(pickle.dumps(f, proto))
                    try:
                        self.assertIs(f_copy.keywords['a'], f_copy)
                    finally:
                        f_copy.__setstate__((capture, (), {}, {}))
            finally:
                f.__setstate__((capture, (), {}, {}))

    # Issue 6083: Reference counting bug
    def test_setstate_refcount(self):
        klasse BadSequence:
            def __len__(self):
                return 4
            def __getitem__(self, key):
                wenn key == 0:
                    return max
                sowenn key == 1:
                    return tuple(range(1000000))
                sowenn key in (2, 3):
                    return {}
                raise IndexError

        f = self.partial(object)
        self.assertRaises(TypeError, f.__setstate__, BadSequence())

    def test_partial_as_method(self):
        klasse A:
            meth = self.partial(capture, 1, a=2)
            cmeth = classmethod(self.partial(capture, 1, a=2))
            smeth = staticmethod(self.partial(capture, 1, a=2))

        a = A()
        self.assertEqual(A.meth(3, b=4), ((1, 3), {'a': 2, 'b': 4}))
        self.assertEqual(A.cmeth(3, b=4), ((1, A, 3), {'a': 2, 'b': 4}))
        self.assertEqual(A.smeth(3, b=4), ((1, 3), {'a': 2, 'b': 4}))
        self.assertEqual(a.meth(3, b=4), ((1, a, 3), {'a': 2, 'b': 4}))
        self.assertEqual(a.cmeth(3, b=4), ((1, A, 3), {'a': 2, 'b': 4}))
        self.assertEqual(a.smeth(3, b=4), ((1, 3), {'a': 2, 'b': 4}))

    def test_partial_genericalias(self):
        alias = self.partial[int]
        self.assertIs(alias.__origin__, self.partial)
        self.assertEqual(alias.__args__, (int,))
        self.assertEqual(alias.__parameters__, ())


@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestPartialC(TestPartial, unittest.TestCase):
    wenn c_functools:
        module = c_functools
        partial = c_functools.partial

    def test_attributes_unwritable(self):
        # attributes should nicht be writable
        p = self.partial(capture, 1, 2, a=10, b=20)
        self.assertRaises(AttributeError, setattr, p, 'func', map)
        self.assertRaises(AttributeError, setattr, p, 'args', (1, 2))
        self.assertRaises(AttributeError, setattr, p, 'keywords', dict(a=1, b=2))

        p = self.partial(hex)
        try:
            del p.__dict__
        except TypeError:
            pass
        sonst:
            self.fail('partial object allowed __dict__ to be deleted')

    def test_manually_adding_non_string_keyword(self):
        p = self.partial(capture)
        # Adding a non-string/unicode keyword to partial kwargs
        p.keywords[1234] = 'value'
        r = repr(p)
        self.assertIn('1234', r)
        self.assertIn("'value'", r)
        mit self.assertRaises(TypeError):
            p()

    def test_keystr_replaces_value(self):
        p = self.partial(capture)

        klasse MutatesYourDict(object):
            def __str__(self):
                p.keywords[self] = ['sth2']
                return 'astr'

        # Replacing the value during key formatting should keep the original
        # value alive (at least long enough).
        p.keywords[MutatesYourDict()] = ['sth']
        r = repr(p)
        self.assertIn('astr', r)
        self.assertIn("['sth']", r)

    def test_placeholders_refcount_smoke(self):
        PH = self.module.Placeholder
        # sum supports vector call
        lst1, start = [], []
        sum_lists = self.partial(sum, PH, start)
        fuer i in range(10):
            sum_lists([lst1, lst1])
        # collections.ChainMap initializer does nicht support vectorcall
        map1, map2 = {}, {}
        partial_cm = self.partial(collections.ChainMap, PH, map1)
        fuer i in range(10):
            partial_cm(map2, map2)


klasse TestPartialPy(TestPartial, unittest.TestCase):
    module = py_functools
    partial = py_functools.partial


wenn c_functools:
    klasse CPartialSubclass(c_functools.partial):
        pass

klasse PyPartialSubclass(py_functools.partial):
    pass

@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestPartialCSubclass(TestPartialC):
    wenn c_functools:
        partial = CPartialSubclass

    # partial subclasses are nicht optimized fuer nested calls
    test_nested_optimization = Nichts

klasse TestPartialPySubclass(TestPartialPy):
    partial = PyPartialSubclass

    def test_subclass_optimization(self):
        # `partial` input to `partial` subclass
        p = py_functools.partial(min, 2)
        p2 = self.partial(p, 1)
        self.assertIs(p2.func, min)
        self.assertEqual(p2(0), 0)
        # `partial` subclass input to `partial` subclass
        p = self.partial(min, 2)
        p2 = self.partial(p, 1)
        self.assertIs(p2.func, min)
        self.assertEqual(p2(0), 0)


klasse TestPartialMethod(unittest.TestCase):

    klasse A(object):
        nothing = functools.partialmethod(capture)
        positional = functools.partialmethod(capture, 1)
        keywords = functools.partialmethod(capture, a=2)
        both = functools.partialmethod(capture, 3, b=4)
        spec_keywords = functools.partialmethod(capture, self=1, func=2)

        nested = functools.partialmethod(positional, 5)

        over_partial = functools.partialmethod(functools.partial(capture, c=6), 7)

        static = functools.partialmethod(staticmethod(capture), 8)
        cls = functools.partialmethod(classmethod(capture), d=9)

    a = A()

    def test_arg_combinations(self):
        self.assertEqual(self.a.nothing(), ((self.a,), {}))
        self.assertEqual(self.a.nothing(5), ((self.a, 5), {}))
        self.assertEqual(self.a.nothing(c=6), ((self.a,), {'c': 6}))
        self.assertEqual(self.a.nothing(5, c=6), ((self.a, 5), {'c': 6}))

        self.assertEqual(self.a.positional(), ((self.a, 1), {}))
        self.assertEqual(self.a.positional(5), ((self.a, 1, 5), {}))
        self.assertEqual(self.a.positional(c=6), ((self.a, 1), {'c': 6}))
        self.assertEqual(self.a.positional(5, c=6), ((self.a, 1, 5), {'c': 6}))

        self.assertEqual(self.a.keywords(), ((self.a,), {'a': 2}))
        self.assertEqual(self.a.keywords(5), ((self.a, 5), {'a': 2}))
        self.assertEqual(self.a.keywords(c=6), ((self.a,), {'a': 2, 'c': 6}))
        self.assertEqual(self.a.keywords(5, c=6), ((self.a, 5), {'a': 2, 'c': 6}))

        self.assertEqual(self.a.both(), ((self.a, 3), {'b': 4}))
        self.assertEqual(self.a.both(5), ((self.a, 3, 5), {'b': 4}))
        self.assertEqual(self.a.both(c=6), ((self.a, 3), {'b': 4, 'c': 6}))
        self.assertEqual(self.a.both(5, c=6), ((self.a, 3, 5), {'b': 4, 'c': 6}))

        self.assertEqual(self.A.both(self.a, 5, c=6), ((self.a, 3, 5), {'b': 4, 'c': 6}))

        self.assertEqual(self.a.spec_keywords(), ((self.a,), {'self': 1, 'func': 2}))

    def test_nested(self):
        self.assertEqual(self.a.nested(), ((self.a, 1, 5), {}))
        self.assertEqual(self.a.nested(6), ((self.a, 1, 5, 6), {}))
        self.assertEqual(self.a.nested(d=7), ((self.a, 1, 5), {'d': 7}))
        self.assertEqual(self.a.nested(6, d=7), ((self.a, 1, 5, 6), {'d': 7}))

        self.assertEqual(self.A.nested(self.a, 6, d=7), ((self.a, 1, 5, 6), {'d': 7}))

    def test_over_partial(self):
        self.assertEqual(self.a.over_partial(), ((self.a, 7), {'c': 6}))
        self.assertEqual(self.a.over_partial(5), ((self.a, 7, 5), {'c': 6}))
        self.assertEqual(self.a.over_partial(d=8), ((self.a, 7), {'c': 6, 'd': 8}))
        self.assertEqual(self.a.over_partial(5, d=8), ((self.a, 7, 5), {'c': 6, 'd': 8}))

        self.assertEqual(self.A.over_partial(self.a, 5, d=8), ((self.a, 7, 5), {'c': 6, 'd': 8}))

    def test_bound_method_introspection(self):
        obj = self.a
        self.assertIs(obj.both.__self__, obj)
        self.assertIs(obj.nested.__self__, obj)
        self.assertIs(obj.over_partial.__self__, obj)
        self.assertIs(obj.cls.__self__, self.A)
        self.assertIs(self.A.cls.__self__, self.A)

    def test_unbound_method_retrieval(self):
        obj = self.A
        self.assertNotHasAttr(obj.both, "__self__")
        self.assertNotHasAttr(obj.nested, "__self__")
        self.assertNotHasAttr(obj.over_partial, "__self__")
        self.assertNotHasAttr(obj.static, "__self__")
        self.assertNotHasAttr(self.a.static, "__self__")

    def test_descriptors(self):
        fuer obj in [self.A, self.a]:
            mit self.subTest(obj=obj):
                self.assertEqual(obj.static(), ((8,), {}))
                self.assertEqual(obj.static(5), ((8, 5), {}))
                self.assertEqual(obj.static(d=8), ((8,), {'d': 8}))
                self.assertEqual(obj.static(5, d=8), ((8, 5), {'d': 8}))

                self.assertEqual(obj.cls(), ((self.A,), {'d': 9}))
                self.assertEqual(obj.cls(5), ((self.A, 5), {'d': 9}))
                self.assertEqual(obj.cls(c=8), ((self.A,), {'c': 8, 'd': 9}))
                self.assertEqual(obj.cls(5, c=8), ((self.A, 5), {'c': 8, 'd': 9}))

    def test_overriding_keywords(self):
        self.assertEqual(self.a.keywords(a=3), ((self.a,), {'a': 3}))
        self.assertEqual(self.A.keywords(self.a, a=3), ((self.a,), {'a': 3}))

    def test_invalid_args(self):
        mit self.assertRaises(TypeError):
            klasse B(object):
                method = functools.partialmethod(Nichts, 1)
        mit self.assertRaises(TypeError):
            klasse B:
                method = functools.partialmethod()
        mit self.assertRaises(TypeError):
            klasse B:
                method = functools.partialmethod(func=capture, a=1)

    def test_repr(self):
        self.assertEqual(repr(vars(self.A)['nothing']),
                         'functools.partialmethod({})'.format(capture))
        self.assertEqual(repr(vars(self.A)['positional']),
                         'functools.partialmethod({}, 1)'.format(capture))
        self.assertEqual(repr(vars(self.A)['keywords']),
                         'functools.partialmethod({}, a=2)'.format(capture))
        self.assertEqual(repr(vars(self.A)['spec_keywords']),
                         'functools.partialmethod({}, self=1, func=2)'.format(capture))
        self.assertEqual(repr(vars(self.A)['both']),
                         'functools.partialmethod({}, 3, b=4)'.format(capture))

    def test_abstract(self):
        klasse Abstract(abc.ABCMeta):

            @abc.abstractmethod
            def add(self, x, y):
                pass

            add5 = functools.partialmethod(add, 5)

        self.assertWahr(Abstract.add.__isabstractmethod__)
        self.assertWahr(Abstract.add5.__isabstractmethod__)

        fuer func in [self.A.static, self.A.cls, self.A.over_partial, self.A.nested, self.A.both]:
            self.assertFalsch(getattr(func, '__isabstractmethod__', Falsch))

    def test_positional_only(self):
        def f(a, b, /):
            return a + b

        p = functools.partial(f, 1)
        self.assertEqual(p(2), f(1, 2))

    def test_subclass_optimization(self):
        klasse PartialMethodSubclass(functools.partialmethod):
            pass
        # `partialmethod` input to `partialmethod` subclass
        p = functools.partialmethod(min, 2)
        p2 = PartialMethodSubclass(p, 1)
        self.assertIs(p2.func, min)
        self.assertEqual(p2.__get__(0)(), 0)
        # `partialmethod` subclass input to `partialmethod` subclass
        p = PartialMethodSubclass(min, 2)
        p2 = PartialMethodSubclass(p, 1)
        self.assertIs(p2.func, min)
        self.assertEqual(p2.__get__(0)(), 0)


klasse TestUpdateWrapper(unittest.TestCase):

    def check_wrapper(self, wrapper, wrapped,
                      assigned=functools.WRAPPER_ASSIGNMENTS,
                      updated=functools.WRAPPER_UPDATES):
        # Check attributes were assigned
        fuer name in assigned:
            self.assertIs(getattr(wrapper, name), getattr(wrapped, name))
        # Check attributes were updated
        fuer name in updated:
            wrapper_attr = getattr(wrapper, name)
            wrapped_attr = getattr(wrapped, name)
            fuer key in wrapped_attr:
                wenn name == "__dict__" und key == "__wrapped__":
                    # __wrapped__ is overwritten by the update code
                    weiter
                self.assertIs(wrapped_attr[key], wrapper_attr[key])
        # Check __wrapped__
        self.assertIs(wrapper.__wrapped__, wrapped)


    def _default_update(self):
        def f[T](a:'This is a new annotation'):
            """This is a test"""
            pass
        f.attr = 'This is also a test'
        f.__wrapped__ = "This is a bald faced lie"
        def wrapper(b:'This is the prior annotation'):
            pass
        functools.update_wrapper(wrapper, f)
        return wrapper, f

    def test_default_update(self):
        wrapper, f = self._default_update()
        self.check_wrapper(wrapper, f)
        T, = f.__type_params__
        self.assertIs(wrapper.__wrapped__, f)
        self.assertEqual(wrapper.__name__, 'f')
        self.assertEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.attr, 'This is also a test')
        self.assertEqual(wrapper.__annotations__['a'], 'This is a new annotation')
        self.assertNotIn('b', wrapper.__annotations__)
        self.assertEqual(wrapper.__type_params__, (T,))

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_default_update_doc(self):
        wrapper, f = self._default_update()
        self.assertEqual(wrapper.__doc__, 'This is a test')

    def test_no_update(self):
        def f():
            """This is a test"""
            pass
        f.attr = 'This is also a test'
        def wrapper():
            pass
        functools.update_wrapper(wrapper, f, (), ())
        self.check_wrapper(wrapper, f, (), ())
        self.assertEqual(wrapper.__name__, 'wrapper')
        self.assertNotEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.__doc__, Nichts)
        self.assertEqual(wrapper.__annotations__, {})
        self.assertNotHasAttr(wrapper, 'attr')

    def test_selective_update(self):
        def f():
            pass
        f.attr = 'This is a different test'
        f.dict_attr = dict(a=1, b=2, c=3)
        def wrapper():
            pass
        wrapper.dict_attr = {}
        assign = ('attr',)
        update = ('dict_attr',)
        functools.update_wrapper(wrapper, f, assign, update)
        self.check_wrapper(wrapper, f, assign, update)
        self.assertEqual(wrapper.__name__, 'wrapper')
        self.assertNotEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.__doc__, Nichts)
        self.assertEqual(wrapper.attr, 'This is a different test')
        self.assertEqual(wrapper.dict_attr, f.dict_attr)

    def test_missing_attributes(self):
        def f():
            pass
        def wrapper():
            pass
        wrapper.dict_attr = {}
        assign = ('attr',)
        update = ('dict_attr',)
        # Missing attributes on wrapped object are ignored
        functools.update_wrapper(wrapper, f, assign, update)
        self.assertNotIn('attr', wrapper.__dict__)
        self.assertEqual(wrapper.dict_attr, {})
        # Wrapper must have expected attributes fuer updating
        del wrapper.dict_attr
        mit self.assertRaises(AttributeError):
            functools.update_wrapper(wrapper, f, assign, update)
        wrapper.dict_attr = 1
        mit self.assertRaises(AttributeError):
            functools.update_wrapper(wrapper, f, assign, update)

    @support.requires_docstrings
    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_builtin_update(self):
        # Test fuer bug #1576241
        def wrapper():
            pass
        functools.update_wrapper(wrapper, max)
        self.assertEqual(wrapper.__name__, 'max')
        self.assertStartsWith(wrapper.__doc__, 'max(')
        self.assertEqual(wrapper.__annotations__, {})

    def test_update_type_wrapper(self):
        def wrapper(*args): pass

        functools.update_wrapper(wrapper, type)
        self.assertEqual(wrapper.__name__, 'type')
        self.assertEqual(wrapper.__annotations__, {})
        self.assertEqual(wrapper.__type_params__, ())

    def test_update_wrapper_annotations(self):
        def inner(x: int): pass
        def wrapper(*args): pass

        functools.update_wrapper(wrapper, inner)
        self.assertEqual(wrapper.__annotations__, {'x': int})
        self.assertIs(wrapper.__annotate__, inner.__annotate__)

        def with_forward_ref(x: undefined): pass
        def wrapper(*args): pass

        functools.update_wrapper(wrapper, with_forward_ref)

        self.assertIs(wrapper.__annotate__, with_forward_ref.__annotate__)
        mit self.assertRaises(NameError):
            wrapper.__annotations__

        undefined = str
        self.assertEqual(wrapper.__annotations__, {'x': undefined})


klasse TestWraps(TestUpdateWrapper):

    def _default_update(self):
        def f():
            """This is a test"""
            pass
        f.attr = 'This is also a test'
        f.__wrapped__ = "This is still a bald faced lie"
        @functools.wraps(f)
        def wrapper():
            pass
        return wrapper, f

    def test_default_update(self):
        wrapper, f = self._default_update()
        self.check_wrapper(wrapper, f)
        self.assertEqual(wrapper.__name__, 'f')
        self.assertEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.attr, 'This is also a test')

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_default_update_doc(self):
        wrapper, _ = self._default_update()
        self.assertEqual(wrapper.__doc__, 'This is a test')

    def test_no_update(self):
        def f():
            """This is a test"""
            pass
        f.attr = 'This is also a test'
        @functools.wraps(f, (), ())
        def wrapper():
            pass
        self.check_wrapper(wrapper, f, (), ())
        self.assertEqual(wrapper.__name__, 'wrapper')
        self.assertNotEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.__doc__, Nichts)
        self.assertNotHasAttr(wrapper, 'attr')

    def test_selective_update(self):
        def f():
            pass
        f.attr = 'This is a different test'
        f.dict_attr = dict(a=1, b=2, c=3)
        def add_dict_attr(f):
            f.dict_attr = {}
            return f
        assign = ('attr',)
        update = ('dict_attr',)
        @functools.wraps(f, assign, update)
        @add_dict_attr
        def wrapper():
            pass
        self.check_wrapper(wrapper, f, assign, update)
        self.assertEqual(wrapper.__name__, 'wrapper')
        self.assertNotEqual(wrapper.__qualname__, f.__qualname__)
        self.assertEqual(wrapper.__doc__, Nichts)
        self.assertEqual(wrapper.attr, 'This is a different test')
        self.assertEqual(wrapper.dict_attr, f.dict_attr)


klasse TestReduce:
    def test_reduce(self):
        klasse Squares:
            def __init__(self, max):
                self.max = max
                self.sofar = []

            def __len__(self):
                return len(self.sofar)

            def __getitem__(self, i):
                wenn nicht 0 <= i < self.max: raise IndexError
                n = len(self.sofar)
                waehrend n <= i:
                    self.sofar.append(n*n)
                    n += 1
                return self.sofar[i]
        def add(x, y):
            return x + y
        self.assertEqual(self.reduce(add, ['a', 'b', 'c'], ''), 'abc')
        self.assertEqual(
            self.reduce(add, [['a', 'c'], [], ['d', 'w']], []),
            ['a','c','d','w']
        )
        self.assertEqual(self.reduce(lambda x, y: x*y, range(2,8), 1), 5040)
        self.assertEqual(
            self.reduce(lambda x, y: x*y, range(2,21), 1),
            2432902008176640000
        )
        self.assertEqual(self.reduce(add, Squares(10)), 285)
        self.assertEqual(self.reduce(add, Squares(10), 0), 285)
        self.assertEqual(self.reduce(add, Squares(0), 0), 0)
        self.assertRaises(TypeError, self.reduce)
        self.assertRaises(TypeError, self.reduce, 42, 42)
        self.assertRaises(TypeError, self.reduce, 42, 42, 42)
        self.assertEqual(self.reduce(42, "1"), "1") # func is never called mit one item
        self.assertEqual(self.reduce(42, "", "1"), "1") # func is never called mit one item
        self.assertRaises(TypeError, self.reduce, 42, (42, 42))
        self.assertRaises(TypeError, self.reduce, add, []) # arg 2 must nicht be empty sequence mit no initial value
        self.assertRaises(TypeError, self.reduce, add, "")
        self.assertRaises(TypeError, self.reduce, add, ())
        self.assertRaises(TypeError, self.reduce, add, object())

        klasse TestFailingIter:
            def __iter__(self):
                raise RuntimeError
        self.assertRaises(RuntimeError, self.reduce, add, TestFailingIter())

        self.assertEqual(self.reduce(add, [], Nichts), Nichts)
        self.assertEqual(self.reduce(add, [], 42), 42)

        klasse BadSeq:
            def __getitem__(self, index):
                raise ValueError
        self.assertRaises(ValueError, self.reduce, 42, BadSeq())

    # Test reduce()'s use of iterators.
    def test_iterator_usage(self):
        klasse SequenceClass:
            def __init__(self, n):
                self.n = n
            def __getitem__(self, i):
                wenn 0 <= i < self.n:
                    return i
                sonst:
                    raise IndexError

        von operator importiere add
        self.assertEqual(self.reduce(add, SequenceClass(5)), 10)
        self.assertEqual(self.reduce(add, SequenceClass(5), 42), 52)
        self.assertRaises(TypeError, self.reduce, add, SequenceClass(0))
        self.assertEqual(self.reduce(add, SequenceClass(0), 42), 42)
        self.assertEqual(self.reduce(add, SequenceClass(1)), 0)
        self.assertEqual(self.reduce(add, SequenceClass(1), 42), 42)

        d = {"one": 1, "two": 2, "three": 3}
        self.assertEqual(self.reduce(add, d), "".join(d.keys()))

    # test correctness of keyword usage of `initial` in `reduce`
    def test_initial_keyword(self):
        def add(x, y):
            return x + y
        self.assertEqual(
            self.reduce(add, ['a', 'b', 'c'], ''),
            self.reduce(add, ['a', 'b', 'c'], initial=''),
        )
        self.assertEqual(
            self.reduce(add, [['a', 'c'], [], ['d', 'w']], []),
            self.reduce(add, [['a', 'c'], [], ['d', 'w']], initial=[]),
        )
        self.assertEqual(
            self.reduce(lambda x, y: x*y, range(2,8), 1),
            self.reduce(lambda x, y: x*y, range(2,8), initial=1),
        )
        self.assertEqual(
            self.reduce(lambda x, y: x*y, range(2,21), 1),
            self.reduce(lambda x, y: x*y, range(2,21), initial=1),
        )
        self.assertRaises(TypeError, self.reduce, add, [0, 1], initial="")
        self.assertEqual(self.reduce(42, "", initial="1"), "1") # func is never called mit one item


@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestReduceC(TestReduce, unittest.TestCase):
    wenn c_functools:
        reduce = c_functools.reduce


klasse TestReducePy(TestReduce, unittest.TestCase):
    reduce = staticmethod(py_functools.reduce)

    def test_reduce_with_kwargs(self):
        mit self.assertWarns(DeprecationWarning):
            self.reduce(function=lambda x, y: x + y, sequence=[1, 2, 3, 4, 5], initial=1)
        mit self.assertWarns(DeprecationWarning):
            self.reduce(lambda x, y: x + y, sequence=[1, 2, 3, 4, 5], initial=1)


klasse TestCmpToKey:

    def test_cmp_to_key(self):
        def cmp1(x, y):
            return (x > y) - (x < y)
        key = self.cmp_to_key(cmp1)
        self.assertEqual(key(3), key(3))
        self.assertGreater(key(3), key(1))
        self.assertGreaterEqual(key(3), key(3))

        def cmp2(x, y):
            return int(x) - int(y)
        key = self.cmp_to_key(cmp2)
        self.assertEqual(key(4.0), key('4'))
        self.assertLess(key(2), key('35'))
        self.assertLessEqual(key(2), key('35'))
        self.assertNotEqual(key(2), key('35'))

    def test_cmp_to_key_arguments(self):
        def cmp1(x, y):
            return (x > y) - (x < y)
        key = self.cmp_to_key(mycmp=cmp1)
        self.assertEqual(key(obj=3), key(obj=3))
        self.assertGreater(key(obj=3), key(obj=1))
        mit self.assertRaises((TypeError, AttributeError)):
            key(3) > 1    # rhs is nicht a K object
        mit self.assertRaises((TypeError, AttributeError)):
            1 < key(3)    # lhs is nicht a K object
        mit self.assertRaises(TypeError):
            key = self.cmp_to_key()             # too few args
        mit self.assertRaises(TypeError):
            key = self.cmp_to_key(cmp1, Nichts)   # too many args
        key = self.cmp_to_key(cmp1)
        mit self.assertRaises(TypeError):
            key()                                    # too few args
        mit self.assertRaises(TypeError):
            key(Nichts, Nichts)                          # too many args

    def test_bad_cmp(self):
        def cmp1(x, y):
            raise ZeroDivisionError
        key = self.cmp_to_key(cmp1)
        mit self.assertRaises(ZeroDivisionError):
            key(3) > key(1)

        klasse BadCmp:
            def __lt__(self, other):
                raise ZeroDivisionError
        def cmp1(x, y):
            return BadCmp()
        mit self.assertRaises(ZeroDivisionError):
            key(3) > key(1)

    def test_obj_field(self):
        def cmp1(x, y):
            return (x > y) - (x < y)
        key = self.cmp_to_key(mycmp=cmp1)
        self.assertEqual(key(50).obj, 50)

    def test_sort_int(self):
        def mycmp(x, y):
            return y - x
        self.assertEqual(sorted(range(5), key=self.cmp_to_key(mycmp)),
                         [4, 3, 2, 1, 0])

    def test_sort_int_str(self):
        def mycmp(x, y):
            x, y = int(x), int(y)
            return (x > y) - (x < y)
        values = [5, '3', 7, 2, '0', '1', 4, '10', 1]
        values = sorted(values, key=self.cmp_to_key(mycmp))
        self.assertEqual([int(value) fuer value in values],
                         [0, 1, 1, 2, 3, 4, 5, 7, 10])

    def test_hash(self):
        def mycmp(x, y):
            return y - x
        key = self.cmp_to_key(mycmp)
        k = key(10)
        self.assertRaises(TypeError, hash, k)
        self.assertNotIsInstance(k, collections.abc.Hashable)

    @unittest.skipIf(support.MISSING_C_DOCSTRINGS,
                     "Signature information fuer builtins requires docstrings")
    def test_cmp_to_signature(self):
        sig = Signature.from_callable(self.cmp_to_key)
        self.assertEqual(str(sig), '(mycmp)')
        def mycmp(x, y):
            return y - x
        sig = Signature.from_callable(self.cmp_to_key(mycmp))
        self.assertEqual(str(sig), '(obj)')



@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestCmpToKeyC(TestCmpToKey, unittest.TestCase):
    wenn c_functools:
        cmp_to_key = c_functools.cmp_to_key

    @support.cpython_only
    def test_disallow_instantiation(self):
        # Ensure that the type disallows instantiation (bpo-43916)
        support.check_disallow_instantiation(
            self, type(c_functools.cmp_to_key(Nichts))
        )


klasse TestCmpToKeyPy(TestCmpToKey, unittest.TestCase):
    cmp_to_key = staticmethod(py_functools.cmp_to_key)


klasse TestTotalOrdering(unittest.TestCase):

    def test_total_ordering_lt(self):
        @functools.total_ordering
        klasse A:
            def __init__(self, value):
                self.value = value
            def __lt__(self, other):
                return self.value < other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertWahr(A(1) < A(2))
        self.assertWahr(A(2) > A(1))
        self.assertWahr(A(1) <= A(2))
        self.assertWahr(A(2) >= A(1))
        self.assertWahr(A(2) <= A(2))
        self.assertWahr(A(2) >= A(2))
        self.assertFalsch(A(1) > A(2))

    def test_total_ordering_le(self):
        @functools.total_ordering
        klasse A:
            def __init__(self, value):
                self.value = value
            def __le__(self, other):
                return self.value <= other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertWahr(A(1) < A(2))
        self.assertWahr(A(2) > A(1))
        self.assertWahr(A(1) <= A(2))
        self.assertWahr(A(2) >= A(1))
        self.assertWahr(A(2) <= A(2))
        self.assertWahr(A(2) >= A(2))
        self.assertFalsch(A(1) >= A(2))

    def test_total_ordering_gt(self):
        @functools.total_ordering
        klasse A:
            def __init__(self, value):
                self.value = value
            def __gt__(self, other):
                return self.value > other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertWahr(A(1) < A(2))
        self.assertWahr(A(2) > A(1))
        self.assertWahr(A(1) <= A(2))
        self.assertWahr(A(2) >= A(1))
        self.assertWahr(A(2) <= A(2))
        self.assertWahr(A(2) >= A(2))
        self.assertFalsch(A(2) < A(1))

    def test_total_ordering_ge(self):
        @functools.total_ordering
        klasse A:
            def __init__(self, value):
                self.value = value
            def __ge__(self, other):
                return self.value >= other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertWahr(A(1) < A(2))
        self.assertWahr(A(2) > A(1))
        self.assertWahr(A(1) <= A(2))
        self.assertWahr(A(2) >= A(1))
        self.assertWahr(A(2) <= A(2))
        self.assertWahr(A(2) >= A(2))
        self.assertFalsch(A(2) <= A(1))

    def test_total_ordering_no_overwrite(self):
        # new methods should nicht overwrite existing
        @functools.total_ordering
        klasse A(int):
            pass
        self.assertWahr(A(1) < A(2))
        self.assertWahr(A(2) > A(1))
        self.assertWahr(A(1) <= A(2))
        self.assertWahr(A(2) >= A(1))
        self.assertWahr(A(2) <= A(2))
        self.assertWahr(A(2) >= A(2))

    def test_no_operations_defined(self):
        mit self.assertRaises(ValueError):
            @functools.total_ordering
            klasse A:
                pass

    def test_notimplemented(self):
        # Verify NotImplemented results are correctly handled
        @functools.total_ordering
        klasse ImplementsLessThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsLessThan):
                    return self.value == other.value
                return Falsch
            def __lt__(self, other):
                wenn isinstance(other, ImplementsLessThan):
                    return self.value < other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsLessThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsLessThanEqualTo):
                    return self.value == other.value
                return Falsch
            def __le__(self, other):
                wenn isinstance(other, ImplementsLessThanEqualTo):
                    return self.value <= other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsGreaterThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsGreaterThan):
                    return self.value == other.value
                return Falsch
            def __gt__(self, other):
                wenn isinstance(other, ImplementsGreaterThan):
                    return self.value > other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsGreaterThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value == other.value
                return Falsch
            def __ge__(self, other):
                wenn isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value >= other.value
                return NotImplemented

        self.assertIs(ImplementsLessThan(1).__le__(1), NotImplemented)
        self.assertIs(ImplementsLessThan(1).__gt__(1), NotImplemented)
        self.assertIs(ImplementsLessThan(1).__ge__(1), NotImplemented)
        self.assertIs(ImplementsLessThanEqualTo(1).__lt__(1), NotImplemented)
        self.assertIs(ImplementsLessThanEqualTo(1).__gt__(1), NotImplemented)
        self.assertIs(ImplementsLessThanEqualTo(1).__ge__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThan(1).__lt__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThan(1).__gt__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThan(1).__ge__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThanEqualTo(1).__lt__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThanEqualTo(1).__le__(1), NotImplemented)
        self.assertIs(ImplementsGreaterThanEqualTo(1).__gt__(1), NotImplemented)

    def test_type_error_when_not_implemented(self):
        # bug 10042; ensure stack overflow does nicht occur
        # when decorated types return NotImplemented
        @functools.total_ordering
        klasse ImplementsLessThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsLessThan):
                    return self.value == other.value
                return Falsch
            def __lt__(self, other):
                wenn isinstance(other, ImplementsLessThan):
                    return self.value < other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsGreaterThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsGreaterThan):
                    return self.value == other.value
                return Falsch
            def __gt__(self, other):
                wenn isinstance(other, ImplementsGreaterThan):
                    return self.value > other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsLessThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsLessThanEqualTo):
                    return self.value == other.value
                return Falsch
            def __le__(self, other):
                wenn isinstance(other, ImplementsLessThanEqualTo):
                    return self.value <= other.value
                return NotImplemented

        @functools.total_ordering
        klasse ImplementsGreaterThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value == other.value
                return Falsch
            def __ge__(self, other):
                wenn isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value >= other.value
                return NotImplemented

        @functools.total_ordering
        klasse ComparatorNotImplemented:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                wenn isinstance(other, ComparatorNotImplemented):
                    return self.value == other.value
                return Falsch
            def __lt__(self, other):
                return NotImplemented

        mit self.subTest("LT < 1"), self.assertRaises(TypeError):
            ImplementsLessThan(-1) < 1

        mit self.subTest("LT < LE"), self.assertRaises(TypeError):
            ImplementsLessThan(0) < ImplementsLessThanEqualTo(0)

        mit self.subTest("LT < GT"), self.assertRaises(TypeError):
            ImplementsLessThan(1) < ImplementsGreaterThan(1)

        mit self.subTest("LE <= LT"), self.assertRaises(TypeError):
            ImplementsLessThanEqualTo(2) <= ImplementsLessThan(2)

        mit self.subTest("LE <= GE"), self.assertRaises(TypeError):
            ImplementsLessThanEqualTo(3) <= ImplementsGreaterThanEqualTo(3)

        mit self.subTest("GT > GE"), self.assertRaises(TypeError):
            ImplementsGreaterThan(4) > ImplementsGreaterThanEqualTo(4)

        mit self.subTest("GT > LT"), self.assertRaises(TypeError):
            ImplementsGreaterThan(5) > ImplementsLessThan(5)

        mit self.subTest("GE >= GT"), self.assertRaises(TypeError):
            ImplementsGreaterThanEqualTo(6) >= ImplementsGreaterThan(6)

        mit self.subTest("GE >= LE"), self.assertRaises(TypeError):
            ImplementsGreaterThanEqualTo(7) >= ImplementsLessThanEqualTo(7)

        mit self.subTest("GE when equal"):
            a = ComparatorNotImplemented(8)
            b = ComparatorNotImplemented(8)
            self.assertEqual(a, b)
            mit self.assertRaises(TypeError):
                a >= b

        mit self.subTest("LE when equal"):
            a = ComparatorNotImplemented(9)
            b = ComparatorNotImplemented(9)
            self.assertEqual(a, b)
            mit self.assertRaises(TypeError):
                a <= b

    def test_pickle(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            fuer name in '__lt__', '__gt__', '__le__', '__ge__':
                mit self.subTest(method=name, proto=proto):
                    method = getattr(Orderable_LT, name)
                    method_copy = pickle.loads(pickle.dumps(method, proto))
                    self.assertIs(method_copy, method)


    def test_total_ordering_for_metaclasses_issue_44605(self):

        @functools.total_ordering
        klasse SortableMeta(type):
            def __new__(cls, name, bases, ns):
                return super().__new__(cls, name, bases, ns)

            def __lt__(self, other):
                wenn nicht isinstance(other, SortableMeta):
                    pass
                return self.__name__ < other.__name__

            def __eq__(self, other):
                wenn nicht isinstance(other, SortableMeta):
                    pass
                return self.__name__ == other.__name__

        klasse B(metaclass=SortableMeta):
            pass

        klasse A(metaclass=SortableMeta):
            pass

        self.assertWahr(A < B)
        self.assertFalsch(A > B)


@functools.total_ordering
klasse Orderable_LT:
    def __init__(self, value):
        self.value = value
    def __lt__(self, other):
        return self.value < other.value
    def __eq__(self, other):
        return self.value == other.value


klasse TestCache:
    # This tests that the pass-through is working als designed.
    # The underlying functionality is tested in TestLRU.

    def test_cache(self):
        @self.module.cache
        def fib(n):
            wenn n < 2:
                return n
            return fib(n-1) + fib(n-2)
        self.assertEqual([fib(n) fuer n in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610])
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=28, misses=16, maxsize=Nichts, currsize=16))
        fib.cache_clear()
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=0, misses=0, maxsize=Nichts, currsize=0))


klasse TestCachePy(TestCache, unittest.TestCase):
    module = py_functools


@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestCacheC(TestCache, unittest.TestCase):
    wenn c_functools:
        module = c_functools


klasse TestLRU:

    def test_lru(self):
        def orig(x, y):
            return 3 * x + y
        f = self.module.lru_cache(maxsize=20)(orig)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(maxsize, 20)
        self.assertEqual(currsize, 0)
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 0)

        domain = range(5)
        fuer i in range(1000):
            x, y = choice(domain), choice(domain)
            actual = f(x, y)
            expected = orig(x, y)
            self.assertEqual(actual, expected)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertWahr(hits > misses)
        self.assertEqual(hits + misses, 1000)
        self.assertEqual(currsize, 20)

        f.cache_clear()   # test clearing
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 0)
        self.assertEqual(currsize, 0)
        f(x, y)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        # Test bypassing the cache
        self.assertIs(f.__wrapped__, orig)
        f.__wrapped__(x, y)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        # test size zero (which means "never-cache")
        @self.module.lru_cache(0)
        def f():
            nonlocal f_cnt
            f_cnt += 1
            return 20
        self.assertEqual(f.cache_info().maxsize, 0)
        f_cnt = 0
        fuer i in range(5):
            self.assertEqual(f(), 20)
        self.assertEqual(f_cnt, 5)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 5)
        self.assertEqual(currsize, 0)

        # test size one
        @self.module.lru_cache(1)
        def f():
            nonlocal f_cnt
            f_cnt += 1
            return 20
        self.assertEqual(f.cache_info().maxsize, 1)
        f_cnt = 0
        fuer i in range(5):
            self.assertEqual(f(), 20)
        self.assertEqual(f_cnt, 1)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 4)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        # test size two
        @self.module.lru_cache(2)
        def f(x):
            nonlocal f_cnt
            f_cnt += 1
            return x*10
        self.assertEqual(f.cache_info().maxsize, 2)
        f_cnt = 0
        fuer x in 7, 9, 7, 9, 7, 9, 8, 8, 8, 9, 9, 9, 8, 8, 8, 7:
            #    *  *              *                          *
            self.assertEqual(f(x), x*10)
        self.assertEqual(f_cnt, 4)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 12)
        self.assertEqual(misses, 4)
        self.assertEqual(currsize, 2)

    def test_lru_no_args(self):
        @self.module.lru_cache
        def square(x):
            return x ** 2

        self.assertEqual(list(map(square, [10, 20, 10])),
                         [100, 400, 100])
        self.assertEqual(square.cache_info().hits, 1)
        self.assertEqual(square.cache_info().misses, 2)
        self.assertEqual(square.cache_info().maxsize, 128)
        self.assertEqual(square.cache_info().currsize, 2)

    def test_lru_bug_35780(self):
        # C version of the lru_cache was nicht checking to see if
        # the user function call has already modified the cache
        # (this arises in recursive calls und in multi-threading).
        # This cause the cache to have orphan links nicht referenced
        # by the cache dictionary.

        once = Wahr                 # Modified by f(x) below

        @self.module.lru_cache(maxsize=10)
        def f(x):
            nonlocal once
            rv = f'.{x}.'
            wenn x == 20 und once:
                once = Falsch
                rv = f(x)
            return rv

        # Fill the cache
        fuer x in range(15):
            self.assertEqual(f(x), f'.{x}.')
        self.assertEqual(f.cache_info().currsize, 10)

        # Make a recursive call und make sure the cache remains full
        self.assertEqual(f(20), '.20.')
        self.assertEqual(f.cache_info().currsize, 10)

    def test_lru_bug_36650(self):
        # C version of lru_cache was treating a call mit an empty **kwargs
        # dictionary als being distinct von a call mit no keywords at all.
        # This did nicht result in an incorrect answer, but it did trigger
        # an unexpected cache miss.

        @self.module.lru_cache()
        def f(x):
            pass

        f(0)
        f(0, **{})
        self.assertEqual(f.cache_info().hits, 1)

    def test_lru_hash_only_once(self):
        # To protect against weird reentrancy bugs und to improve
        # efficiency when faced mit slow __hash__ methods, the
        # LRU cache guarantees that it will only call __hash__
        # only once per use als an argument to the cached function.

        @self.module.lru_cache(maxsize=1)
        def f(x, y):
            return x * 3 + y

        # Simulate the integer 5
        mock_int = unittest.mock.Mock()
        mock_int.__mul__ = unittest.mock.Mock(return_value=15)
        mock_int.__hash__ = unittest.mock.Mock(return_value=999)

        # Add to cache:  One use als an argument gives one call
        self.assertEqual(f(mock_int, 1), 16)
        self.assertEqual(mock_int.__hash__.call_count, 1)
        self.assertEqual(f.cache_info(), (0, 1, 1, 1))

        # Cache hit: One use als an argument gives one additional call
        self.assertEqual(f(mock_int, 1), 16)
        self.assertEqual(mock_int.__hash__.call_count, 2)
        self.assertEqual(f.cache_info(), (1, 1, 1, 1))

        # Cache eviction: No use als an argument gives no additional call
        self.assertEqual(f(6, 2), 20)
        self.assertEqual(mock_int.__hash__.call_count, 2)
        self.assertEqual(f.cache_info(), (1, 2, 1, 1))

        # Cache miss: One use als an argument gives one additional call
        self.assertEqual(f(mock_int, 1), 16)
        self.assertEqual(mock_int.__hash__.call_count, 3)
        self.assertEqual(f.cache_info(), (1, 3, 1, 1))

    def test_lru_reentrancy_with_len(self):
        # Test to make sure the LRU cache code isn't thrown-off by
        # caching the built-in len() function.  Since len() can be
        # cached, we shouldn't use it inside the lru code itself.
        old_len = builtins.len
        try:
            builtins.len = self.module.lru_cache(4)(len)
            fuer i in [0, 0, 1, 2, 3, 3, 4, 5, 6, 1, 7, 2, 1]:
                self.assertEqual(len('abcdefghijklmn'[:i]), i)
        finally:
            builtins.len = old_len

    def test_lru_star_arg_handling(self):
        # Test regression that arose in ea064ff3c10f
        @self.module.lru_cache()
        def f(*args):
            return args

        self.assertEqual(f(1, 2), (1, 2))
        self.assertEqual(f((1, 2)), ((1, 2),))

    def test_lru_type_error(self):
        # Regression test fuer issue #28653.
        # lru_cache was leaking when one of the arguments
        # wasn't cacheable.

        @self.module.lru_cache(maxsize=Nichts)
        def infinite_cache(o):
            pass

        @self.module.lru_cache(maxsize=10)
        def limited_cache(o):
            pass

        mit self.assertRaises(TypeError):
            infinite_cache([])

        mit self.assertRaises(TypeError):
            limited_cache([])

    def test_lru_with_maxsize_none(self):
        @self.module.lru_cache(maxsize=Nichts)
        def fib(n):
            wenn n < 2:
                return n
            return fib(n-1) + fib(n-2)
        self.assertEqual([fib(n) fuer n in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610])
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=28, misses=16, maxsize=Nichts, currsize=16))
        fib.cache_clear()
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=0, misses=0, maxsize=Nichts, currsize=0))

    def test_lru_with_maxsize_negative(self):
        @self.module.lru_cache(maxsize=-10)
        def eq(n):
            return n
        fuer i in (0, 1):
            self.assertEqual([eq(n) fuer n in range(150)], list(range(150)))
        self.assertEqual(eq.cache_info(),
            self.module._CacheInfo(hits=0, misses=300, maxsize=0, currsize=0))

    def test_lru_with_exceptions(self):
        # Verify that user_function exceptions get passed through without
        # creating a hard-to-read chained exception.
        # http://bugs.python.org/issue13177
        fuer maxsize in (Nichts, 128):
            @self.module.lru_cache(maxsize)
            def func(i):
                return 'abc'[i]
            self.assertEqual(func(0), 'a')
            mit self.assertRaises(IndexError) als cm:
                func(15)
            self.assertIsNichts(cm.exception.__context__)
            # Verify that the previous exception did nicht result in a cached entry
            mit self.assertRaises(IndexError):
                func(15)

    def test_lru_with_types(self):
        fuer maxsize in (Nichts, 128):
            @self.module.lru_cache(maxsize=maxsize, typed=Wahr)
            def square(x):
                return x * x
            self.assertEqual(square(3), 9)
            self.assertEqual(type(square(3)), type(9))
            self.assertEqual(square(3.0), 9.0)
            self.assertEqual(type(square(3.0)), type(9.0))
            self.assertEqual(square(x=3), 9)
            self.assertEqual(type(square(x=3)), type(9))
            self.assertEqual(square(x=3.0), 9.0)
            self.assertEqual(type(square(x=3.0)), type(9.0))
            self.assertEqual(square.cache_info().hits, 4)
            self.assertEqual(square.cache_info().misses, 4)

    def test_lru_cache_typed_is_not_recursive(self):
        cached = self.module.lru_cache(typed=Wahr)(repr)

        self.assertEqual(cached(1), '1')
        self.assertEqual(cached(Wahr), 'Wahr')
        self.assertEqual(cached(1.0), '1.0')
        self.assertEqual(cached(0), '0')
        self.assertEqual(cached(Falsch), 'Falsch')
        self.assertEqual(cached(0.0), '0.0')

        self.assertEqual(cached((1,)), '(1,)')
        self.assertEqual(cached((Wahr,)), '(1,)')
        self.assertEqual(cached((1.0,)), '(1,)')
        self.assertEqual(cached((0,)), '(0,)')
        self.assertEqual(cached((Falsch,)), '(0,)')
        self.assertEqual(cached((0.0,)), '(0,)')

        klasse T(tuple):
            pass

        self.assertEqual(cached(T((1,))), '(1,)')
        self.assertEqual(cached(T((Wahr,))), '(1,)')
        self.assertEqual(cached(T((1.0,))), '(1,)')
        self.assertEqual(cached(T((0,))), '(0,)')
        self.assertEqual(cached(T((Falsch,))), '(0,)')
        self.assertEqual(cached(T((0.0,))), '(0,)')

    def test_lru_with_keyword_args(self):
        @self.module.lru_cache()
        def fib(n):
            wenn n < 2:
                return n
            return fib(n=n-1) + fib(n=n-2)
        self.assertEqual(
            [fib(n=number) fuer number in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
        )
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=28, misses=16, maxsize=128, currsize=16))
        fib.cache_clear()
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=0, misses=0, maxsize=128, currsize=0))

    def test_lru_with_keyword_args_maxsize_none(self):
        @self.module.lru_cache(maxsize=Nichts)
        def fib(n):
            wenn n < 2:
                return n
            return fib(n=n-1) + fib(n=n-2)
        self.assertEqual([fib(n=number) fuer number in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610])
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=28, misses=16, maxsize=Nichts, currsize=16))
        fib.cache_clear()
        self.assertEqual(fib.cache_info(),
            self.module._CacheInfo(hits=0, misses=0, maxsize=Nichts, currsize=0))

    def test_kwargs_order(self):
        # PEP 468: Preserving Keyword Argument Order
        @self.module.lru_cache(maxsize=10)
        def f(**kwargs):
            return list(kwargs.items())
        self.assertEqual(f(a=1, b=2), [('a', 1), ('b', 2)])
        self.assertEqual(f(b=2, a=1), [('b', 2), ('a', 1)])
        self.assertEqual(f.cache_info(),
            self.module._CacheInfo(hits=0, misses=2, maxsize=10, currsize=2))

    def test_lru_cache_decoration(self):
        def f(zomg: 'zomg_annotation'):
            """f doc string"""
            return 42
        g = self.module.lru_cache()(f)
        fuer attr in self.module.WRAPPER_ASSIGNMENTS:
            self.assertEqual(getattr(g, attr), getattr(f, attr))

    @threading_helper.requires_working_threading()
    def test_lru_cache_threaded(self):
        n, m = 5, 11
        def orig(x, y):
            return 3 * x + y
        f = self.module.lru_cache(maxsize=n*m)(orig)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(currsize, 0)

        start = threading.Event()
        def full(k):
            start.wait(10)
            fuer _ in range(m):
                self.assertEqual(f(k, 0), orig(k, 0))

        def clear():
            start.wait(10)
            fuer _ in range(2*m):
                f.cache_clear()

        orig_si = sys.getswitchinterval()
        support.setswitchinterval(1e-6)
        try:
            # create n threads in order to fill cache
            threads = [threading.Thread(target=full, args=[k])
                       fuer k in range(n)]
            mit threading_helper.start_threads(threads):
                start.set()

            hits, misses, maxsize, currsize = f.cache_info()
            wenn self.module is py_functools:
                # XXX: Why can be nicht equal?
                self.assertLessEqual(misses, n)
                self.assertLessEqual(hits, m*n - misses)
            sonst:
                self.assertEqual(misses, n)
                self.assertEqual(hits, m*n - misses)
            self.assertEqual(currsize, n)

            # create n threads in order to fill cache und 1 to clear it
            threads = [threading.Thread(target=clear)]
            threads += [threading.Thread(target=full, args=[k])
                        fuer k in range(n)]
            start.clear()
            mit threading_helper.start_threads(threads):
                start.set()
        finally:
            sys.setswitchinterval(orig_si)

    @threading_helper.requires_working_threading()
    def test_lru_cache_threaded2(self):
        # Simultaneous call mit the same arguments
        n, m = 5, 7
        start = threading.Barrier(n+1)
        pause = threading.Barrier(n+1)
        stop = threading.Barrier(n+1)
        @self.module.lru_cache(maxsize=m*n)
        def f(x):
            pause.wait(10)
            return 3 * x
        self.assertEqual(f.cache_info(), (0, 0, m*n, 0))
        def test():
            fuer i in range(m):
                start.wait(10)
                self.assertEqual(f(i), 3 * i)
                stop.wait(10)
        threads = [threading.Thread(target=test) fuer k in range(n)]
        mit threading_helper.start_threads(threads):
            fuer i in range(m):
                start.wait(10)
                stop.reset()
                pause.wait(10)
                start.reset()
                stop.wait(10)
                pause.reset()
                self.assertEqual(f.cache_info(), (0, (i+1)*n, m*n, i+1))

    @threading_helper.requires_working_threading()
    def test_lru_cache_threaded3(self):
        @self.module.lru_cache(maxsize=2)
        def f(x):
            time.sleep(.01)
            return 3 * x
        def test(i, x):
            self.assertEqual(f(x), 3 * x, i)
        threads = [threading.Thread(target=test, args=(i, v))
                   fuer i, v in enumerate([1, 2, 2, 3, 2])]
        mit threading_helper.start_threads(threads):
            pass

    def test_need_for_rlock(self):
        # This will deadlock on an LRU cache that uses a regular lock

        @self.module.lru_cache(maxsize=10)
        def test_func(x):
            'Used to demonstrate a reentrant lru_cache call within a single thread'
            return x

        klasse DoubleEq:
            'Demonstrate a reentrant lru_cache call within a single thread'
            def __init__(self, x):
                self.x = x
            def __hash__(self):
                return self.x
            def __eq__(self, other):
                wenn self.x == 2:
                    test_func(DoubleEq(1))
                return self.x == other.x

        test_func(DoubleEq(1))                      # Load the cache
        test_func(DoubleEq(2))                      # Load the cache
        self.assertEqual(test_func(DoubleEq(2)),    # Trigger a re-entrant __eq__ call
                         DoubleEq(2))               # Verify the correct return value

    def test_lru_method(self):
        klasse X(int):
            f_cnt = 0
            @self.module.lru_cache(2)
            def f(self, x):
                self.f_cnt += 1
                return x*10+self
        a = X(5)
        b = X(5)
        c = X(7)
        self.assertEqual(X.f.cache_info(), (0, 0, 2, 0))

        fuer x in 1, 2, 2, 3, 1, 1, 1, 2, 3, 3:
            self.assertEqual(a.f(x), x*10 + 5)
        self.assertEqual((a.f_cnt, b.f_cnt, c.f_cnt), (6, 0, 0))
        self.assertEqual(X.f.cache_info(), (4, 6, 2, 2))

        fuer x in 1, 2, 1, 1, 1, 1, 3, 2, 2, 2:
            self.assertEqual(b.f(x), x*10 + 5)
        self.assertEqual((a.f_cnt, b.f_cnt, c.f_cnt), (6, 4, 0))
        self.assertEqual(X.f.cache_info(), (10, 10, 2, 2))

        fuer x in 2, 1, 1, 1, 1, 2, 1, 3, 2, 1:
            self.assertEqual(c.f(x), x*10 + 7)
        self.assertEqual((a.f_cnt, b.f_cnt, c.f_cnt), (6, 4, 5))
        self.assertEqual(X.f.cache_info(), (15, 15, 2, 2))

        self.assertEqual(a.f.cache_info(), X.f.cache_info())
        self.assertEqual(b.f.cache_info(), X.f.cache_info())
        self.assertEqual(c.f.cache_info(), X.f.cache_info())

    def test_pickle(self):
        cls = self.__class__
        fuer f in cls.cached_func[0], cls.cached_meth, cls.cached_staticmeth:
            fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
                mit self.subTest(proto=proto, func=f):
                    f_copy = pickle.loads(pickle.dumps(f, proto))
                    self.assertIs(f_copy, f)

    def test_copy(self):
        cls = self.__class__
        def orig(x, y):
            return 3 * x + y
        part = self.module.partial(orig, 2)
        funcs = (cls.cached_func[0], cls.cached_meth, cls.cached_staticmeth,
                 self.module.lru_cache(2)(part))
        fuer f in funcs:
            mit self.subTest(func=f):
                f_copy = copy.copy(f)
                self.assertIs(f_copy, f)

    def test_deepcopy(self):
        cls = self.__class__
        def orig(x, y):
            return 3 * x + y
        part = self.module.partial(orig, 2)
        funcs = (cls.cached_func[0], cls.cached_meth, cls.cached_staticmeth,
                 self.module.lru_cache(2)(part))
        fuer f in funcs:
            mit self.subTest(func=f):
                f_copy = copy.deepcopy(f)
                self.assertIs(f_copy, f)

    def test_lru_cache_parameters(self):
        @self.module.lru_cache(maxsize=2)
        def f():
            return 1
        self.assertEqual(f.cache_parameters(), {'maxsize': 2, "typed": Falsch})

        @self.module.lru_cache(maxsize=1000, typed=Wahr)
        def f():
            return 1
        self.assertEqual(f.cache_parameters(), {'maxsize': 1000, "typed": Wahr})

    def test_lru_cache_weakrefable(self):
        @self.module.lru_cache
        def test_function(x):
            return x

        klasse A:
            @self.module.lru_cache
            def test_method(self, x):
                return (self, x)

            @staticmethod
            @self.module.lru_cache
            def test_staticmethod(x):
                return (self, x)

        refs = [weakref.ref(test_function),
                weakref.ref(A.test_method),
                weakref.ref(A.test_staticmethod)]

        fuer ref in refs:
            self.assertIsNotNichts(ref())

        del A
        del test_function
        gc.collect()

        fuer ref in refs:
            self.assertIsNichts(ref())

    def test_common_signatures(self):
        def orig(a, /, b, c=Wahr): ...
        lru = self.module.lru_cache(1)(orig)

        self.assertEqual(str(Signature.from_callable(lru)), '(a, /, b, c=Wahr)')
        self.assertEqual(str(Signature.from_callable(lru.cache_info)), '()')
        self.assertEqual(str(Signature.from_callable(lru.cache_clear)), '()')

    def test_get_annotations(self):
        def orig(a: int) -> str: ...
        lru = self.module.lru_cache(1)(orig)

        self.assertEqual(
            get_annotations(orig), {"a": int, "return": str},
        )
        self.assertEqual(
            get_annotations(lru), {"a": int, "return": str},
        )

    def test_get_annotations_with_forwardref(self):
        def orig(a: int) -> nonexistent: ...
        lru = self.module.lru_cache(1)(orig)

        self.assertEqual(
            get_annotations(orig, format=Format.FORWARDREF),
            {"a": int, "return": EqualToForwardRef('nonexistent', owner=orig)},
        )
        self.assertEqual(
            get_annotations(lru, format=Format.FORWARDREF),
            {"a": int, "return": EqualToForwardRef('nonexistent', owner=lru)},
        )
        mit self.assertRaises(NameError):
            get_annotations(orig, format=Format.VALUE)
        mit self.assertRaises(NameError):
            get_annotations(lru, format=Format.VALUE)

    @support.skip_on_s390x
    @unittest.skipIf(support.is_wasi, "WASI has limited C stack")
    @support.skip_if_sanitizer("requires deep stack", ub=Wahr, thread=Wahr)
    @support.skip_emscripten_stack_overflow()
    def test_lru_recursion(self):

        @self.module.lru_cache
        def fib(n):
            wenn n <= 1:
                return n
            return fib(n-1) + fib(n-2)

        fib(100)
        wenn self.module == c_functools:
            fib.cache_clear()
            mit support.infinite_recursion():
                mit self.assertRaises(RecursionError):
                    fib(support.exceeds_recursion_limit())


@py_functools.lru_cache()
def py_cached_func(x, y):
    return 3 * x + y

wenn c_functools:
    @c_functools.lru_cache()
    def c_cached_func(x, y):
        return 3 * x + y


klasse TestLRUPy(TestLRU, unittest.TestCase):
    module = py_functools
    cached_func = py_cached_func,

    @module.lru_cache()
    def cached_meth(self, x, y):
        return 3 * x + y

    @staticmethod
    @module.lru_cache()
    def cached_staticmeth(x, y):
        return 3 * x + y


@unittest.skipUnless(c_functools, 'requires the C _functools module')
klasse TestLRUC(TestLRU, unittest.TestCase):
    wenn c_functools:
        module = c_functools
        cached_func = c_cached_func,

        @module.lru_cache()
        def cached_meth(self, x, y):
            return 3 * x + y

        @staticmethod
        @module.lru_cache()
        def cached_staticmeth(x, y):
            return 3 * x + y


klasse TestSingleDispatch(unittest.TestCase):
    def test_simple_overloads(self):
        @functools.singledispatch
        def g(obj):
            return "base"
        def g_int(i):
            return "integer"
        g.register(int, g_int)
        self.assertEqual(g("str"), "base")
        self.assertEqual(g(1), "integer")
        self.assertEqual(g([1,2,3]), "base")

    def test_mro(self):
        @functools.singledispatch
        def g(obj):
            return "base"
        klasse A:
            pass
        klasse C(A):
            pass
        klasse B(A):
            pass
        klasse D(C, B):
            pass
        def g_A(a):
            return "A"
        def g_B(b):
            return "B"
        g.register(A, g_A)
        g.register(B, g_B)
        self.assertEqual(g(A()), "A")
        self.assertEqual(g(B()), "B")
        self.assertEqual(g(C()), "A")
        self.assertEqual(g(D()), "B")

    def test_register_decorator(self):
        @functools.singledispatch
        def g(obj):
            return "base"
        @g.register(int)
        def g_int(i):
            return "int %s" % (i,)
        self.assertEqual(g(""), "base")
        self.assertEqual(g(12), "int 12")
        self.assertIs(g.dispatch(int), g_int)
        self.assertIs(g.dispatch(object), g.dispatch(str))
        # Note: in the assert above this is nicht g.
        # @singledispatch returns the wrapper.

    def test_wrapping_attributes(self):
        @functools.singledispatch
        def g(obj):
            "Simple test"
            return "Test"
        self.assertEqual(g.__name__, "g")
        wenn sys.flags.optimize < 2:
            self.assertEqual(g.__doc__, "Simple test")

    @unittest.skipUnless(decimal, 'requires _decimal')
    @support.cpython_only
    def test_c_classes(self):
        @functools.singledispatch
        def g(obj):
            return "base"
        @g.register(decimal.DecimalException)
        def _(obj):
            return obj.args
        subn = decimal.Subnormal("Exponent < Emin")
        rnd = decimal.Rounded("Number got rounded")
        self.assertEqual(g(subn), ("Exponent < Emin",))
        self.assertEqual(g(rnd), ("Number got rounded",))
        @g.register(decimal.Subnormal)
        def _(obj):
            return "Too small to care."
        self.assertEqual(g(subn), "Too small to care.")
        self.assertEqual(g(rnd), ("Number got rounded",))

    def test_compose_mro(self):
        # Nichts of the examples in this test depend on haystack ordering.
        c = collections.abc
        mro = functools._compose_mro
        bases = [c.Sequence, c.MutableMapping, c.Mapping, c.Set]
        fuer haystack in permutations(bases):
            m = mro(dict, haystack)
            self.assertEqual(m, [dict, c.MutableMapping, c.Mapping,
                                 c.Collection, c.Sized, c.Iterable,
                                 c.Container, object])
        bases = [c.Container, c.Mapping, c.MutableMapping, collections.OrderedDict]
        fuer haystack in permutations(bases):
            m = mro(collections.ChainMap, haystack)
            self.assertEqual(m, [collections.ChainMap, c.MutableMapping, c.Mapping,
                                 c.Collection, c.Sized, c.Iterable,
                                 c.Container, object])

        # If there's a generic function mit implementations registered for
        # both Sized und Container, passing a defaultdict to it results in an
        # ambiguous dispatch which will cause a RuntimeError (see
        # test_mro_conflicts).
        bases = [c.Container, c.Sized, str]
        fuer haystack in permutations(bases):
            m = mro(collections.defaultdict, [c.Sized, c.Container, str])
            self.assertEqual(m, [collections.defaultdict, dict, c.Sized,
                                 c.Container, object])

        # MutableSequence below is registered directly on D. In other words, it
        # precedes MutableMapping which means single dispatch will always
        # choose MutableSequence here.
        klasse D(collections.defaultdict):
            pass
        c.MutableSequence.register(D)
        bases = [c.MutableSequence, c.MutableMapping]
        fuer haystack in permutations(bases):
            m = mro(D, haystack)
            self.assertEqual(m, [D, c.MutableSequence, c.Sequence, c.Reversible,
                                 collections.defaultdict, dict, c.MutableMapping, c.Mapping,
                                 c.Collection, c.Sized, c.Iterable, c.Container,
                                 object])

        # Container und Callable are registered on different base classes und
        # a generic function supporting both should always pick the Callable
        # implementation wenn a C instance is passed.
        klasse C(collections.defaultdict):
            def __call__(self):
                pass
        bases = [c.Sized, c.Callable, c.Container, c.Mapping]
        fuer haystack in permutations(bases):
            m = mro(C, haystack)
            self.assertEqual(m, [C, c.Callable, collections.defaultdict, dict, c.Mapping,
                                 c.Collection, c.Sized, c.Iterable,
                                 c.Container, object])

    def test_register_abc(self):
        c = collections.abc
        d = {"a": "b"}
        l = [1, 2, 3]
        s = {object(), Nichts}
        f = frozenset(s)
        t = (1, 2, 3)
        @functools.singledispatch
        def g(obj):
            return "base"
        self.assertEqual(g(d), "base")
        self.assertEqual(g(l), "base")
        self.assertEqual(g(s), "base")
        self.assertEqual(g(f), "base")
        self.assertEqual(g(t), "base")
        g.register(c.Sized, lambda obj: "sized")
        self.assertEqual(g(d), "sized")
        self.assertEqual(g(l), "sized")
        self.assertEqual(g(s), "sized")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(c.MutableMapping, lambda obj: "mutablemapping")
        self.assertEqual(g(d), "mutablemapping")
        self.assertEqual(g(l), "sized")
        self.assertEqual(g(s), "sized")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(collections.ChainMap, lambda obj: "chainmap")
        self.assertEqual(g(d), "mutablemapping")  # irrelevant ABCs registered
        self.assertEqual(g(l), "sized")
        self.assertEqual(g(s), "sized")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(c.MutableSequence, lambda obj: "mutablesequence")
        self.assertEqual(g(d), "mutablemapping")
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "sized")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(c.MutableSet, lambda obj: "mutableset")
        self.assertEqual(g(d), "mutablemapping")
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(c.Mapping, lambda obj: "mapping")
        self.assertEqual(g(d), "mutablemapping")  # nicht specific enough
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sized")
        g.register(c.Sequence, lambda obj: "sequence")
        self.assertEqual(g(d), "mutablemapping")
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "sized")
        self.assertEqual(g(t), "sequence")
        g.register(c.Set, lambda obj: "set")
        self.assertEqual(g(d), "mutablemapping")
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "set")
        self.assertEqual(g(t), "sequence")
        g.register(dict, lambda obj: "dict")
        self.assertEqual(g(d), "dict")
        self.assertEqual(g(l), "mutablesequence")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "set")
        self.assertEqual(g(t), "sequence")
        g.register(list, lambda obj: "list")
        self.assertEqual(g(d), "dict")
        self.assertEqual(g(l), "list")
        self.assertEqual(g(s), "mutableset")
        self.assertEqual(g(f), "set")
        self.assertEqual(g(t), "sequence")
        g.register(set, lambda obj: "concrete-set")
        self.assertEqual(g(d), "dict")
        self.assertEqual(g(l), "list")
        self.assertEqual(g(s), "concrete-set")
        self.assertEqual(g(f), "set")
        self.assertEqual(g(t), "sequence")
        g.register(frozenset, lambda obj: "frozen-set")
        self.assertEqual(g(d), "dict")
        self.assertEqual(g(l), "list")
        self.assertEqual(g(s), "concrete-set")
        self.assertEqual(g(f), "frozen-set")
        self.assertEqual(g(t), "sequence")
        g.register(tuple, lambda obj: "tuple")
        self.assertEqual(g(d), "dict")
        self.assertEqual(g(l), "list")
        self.assertEqual(g(s), "concrete-set")
        self.assertEqual(g(f), "frozen-set")
        self.assertEqual(g(t), "tuple")

    def test_c3_abc(self):
        c = collections.abc
        mro = functools._c3_mro
        klasse A(object):
            pass
        klasse B(A):
            def __len__(self):
                return 0   # implies Sized
        @c.Container.register
        klasse C(object):
            pass
        klasse D(object):
            pass   # unrelated
        klasse X(D, C, B):
            def __call__(self):
                pass   # implies Callable
        expected = [X, c.Callable, D, C, c.Container, B, c.Sized, A, object]
        fuer abcs in permutations([c.Sized, c.Callable, c.Container]):
            self.assertEqual(mro(X, abcs=abcs), expected)
        # unrelated ABCs don't appear in the resulting MRO
        many_abcs = [c.Mapping, c.Sized, c.Callable, c.Container, c.Iterable]
        self.assertEqual(mro(X, abcs=many_abcs), expected)

    def test_false_meta(self):
        # see issue23572
        klasse MetaA(type):
            def __len__(self):
                return 0
        klasse A(metaclass=MetaA):
            pass
        klasse AA(A):
            pass
        @functools.singledispatch
        def fun(a):
            return 'base A'
        @fun.register(A)
        def _(a):
            return 'fun A'
        aa = AA()
        self.assertEqual(fun(aa), 'fun A')

    def test_mro_conflicts(self):
        c = collections.abc
        @functools.singledispatch
        def g(arg):
            return "base"
        klasse O(c.Sized):
            def __len__(self):
                return 0
        o = O()
        self.assertEqual(g(o), "base")
        g.register(c.Iterable, lambda arg: "iterable")
        g.register(c.Container, lambda arg: "container")
        g.register(c.Sized, lambda arg: "sized")
        g.register(c.Set, lambda arg: "set")
        self.assertEqual(g(o), "sized")
        c.Iterable.register(O)
        self.assertEqual(g(o), "sized")   # because it's explicitly in __mro__
        c.Container.register(O)
        self.assertEqual(g(o), "sized")   # see above: Sized is in __mro__
        c.Set.register(O)
        self.assertEqual(g(o), "set")     # because c.Set is a subclass of
                                          # c.Sized und c.Container
        klasse P:
            pass
        p = P()
        self.assertEqual(g(p), "base")
        c.Iterable.register(P)
        self.assertEqual(g(p), "iterable")
        c.Container.register(P)
        mit self.assertRaises(RuntimeError) als re_one:
            g(p)
        self.assertIn(
            str(re_one.exception),
            (("Ambiguous dispatch: <class 'collections.abc.Container'> "
              "or <class 'collections.abc.Iterable'>"),
             ("Ambiguous dispatch: <class 'collections.abc.Iterable'> "
              "or <class 'collections.abc.Container'>")),
        )
        klasse Q(c.Sized):
            def __len__(self):
                return 0
        q = Q()
        self.assertEqual(g(q), "sized")
        c.Iterable.register(Q)
        self.assertEqual(g(q), "sized")   # because it's explicitly in __mro__
        c.Set.register(Q)
        self.assertEqual(g(q), "set")     # because c.Set is a subclass of
                                          # c.Sized und c.Iterable
        @functools.singledispatch
        def h(arg):
            return "base"
        @h.register(c.Sized)
        def _(arg):
            return "sized"
        @h.register(c.Container)
        def _(arg):
            return "container"
        # Even though Sized und Container are explicit bases of MutableMapping,
        # this ABC is implicitly registered on defaultdict which makes all of
        # MutableMapping's bases implicit als well von defaultdict's
        # perspective.
        mit self.assertRaises(RuntimeError) als re_two:
            h(collections.defaultdict(lambda: 0))
        self.assertIn(
            str(re_two.exception),
            (("Ambiguous dispatch: <class 'collections.abc.Container'> "
              "or <class 'collections.abc.Sized'>"),
             ("Ambiguous dispatch: <class 'collections.abc.Sized'> "
              "or <class 'collections.abc.Container'>")),
        )
        klasse R(collections.defaultdict):
            pass
        c.MutableSequence.register(R)
        @functools.singledispatch
        def i(arg):
            return "base"
        @i.register(c.MutableMapping)
        def _(arg):
            return "mapping"
        @i.register(c.MutableSequence)
        def _(arg):
            return "sequence"
        r = R()
        self.assertEqual(i(r), "sequence")
        klasse S:
            pass
        klasse T(S, c.Sized):
            def __len__(self):
                return 0
        t = T()
        self.assertEqual(h(t), "sized")
        c.Container.register(T)
        self.assertEqual(h(t), "sized")   # because it's explicitly in the MRO
        klasse U:
            def __len__(self):
                return 0
        u = U()
        self.assertEqual(h(u), "sized")   # implicit Sized subclass inferred
                                          # von the existence of __len__()
        c.Container.register(U)
        # There is no preference fuer registered versus inferred ABCs.
        mit self.assertRaises(RuntimeError) als re_three:
            h(u)
        self.assertIn(
            str(re_three.exception),
            (("Ambiguous dispatch: <class 'collections.abc.Container'> "
              "or <class 'collections.abc.Sized'>"),
             ("Ambiguous dispatch: <class 'collections.abc.Sized'> "
              "or <class 'collections.abc.Container'>")),
        )
        klasse V(c.Sized, S):
            def __len__(self):
                return 0
        @functools.singledispatch
        def j(arg):
            return "base"
        @j.register(S)
        def _(arg):
            return "s"
        @j.register(c.Container)
        def _(arg):
            return "container"
        v = V()
        self.assertEqual(j(v), "s")
        c.Container.register(V)
        self.assertEqual(j(v), "container")   # because it ends up right after
                                              # Sized in the MRO

    def test_cache_invalidation(self):
        von collections importiere UserDict
        importiere weakref

        klasse TracingDict(UserDict):
            def __init__(self, *args, **kwargs):
                super(TracingDict, self).__init__(*args, **kwargs)
                self.set_ops = []
                self.get_ops = []
            def __getitem__(self, key):
                result = self.data[key]
                self.get_ops.append(key)
                return result
            def __setitem__(self, key, value):
                self.set_ops.append(key)
                self.data[key] = value
            def clear(self):
                self.data.clear()

        td = TracingDict()
        mit support.swap_attr(weakref, "WeakKeyDictionary", lambda: td):
            c = collections.abc
            @functools.singledispatch
            def g(arg):
                return "base"
            d = {}
            l = []
            self.assertEqual(len(td), 0)
            self.assertEqual(g(d), "base")
            self.assertEqual(len(td), 1)
            self.assertEqual(td.get_ops, [])
            self.assertEqual(td.set_ops, [dict])
            self.assertEqual(td.data[dict], g.registry[object])
            self.assertEqual(g(l), "base")
            self.assertEqual(len(td), 2)
            self.assertEqual(td.get_ops, [])
            self.assertEqual(td.set_ops, [dict, list])
            self.assertEqual(td.data[dict], g.registry[object])
            self.assertEqual(td.data[list], g.registry[object])
            self.assertEqual(td.data[dict], td.data[list])
            self.assertEqual(g(l), "base")
            self.assertEqual(g(d), "base")
            self.assertEqual(td.get_ops, [list, dict])
            self.assertEqual(td.set_ops, [dict, list])
            g.register(list, lambda arg: "list")
            self.assertEqual(td.get_ops, [list, dict])
            self.assertEqual(len(td), 0)
            self.assertEqual(g(d), "base")
            self.assertEqual(len(td), 1)
            self.assertEqual(td.get_ops, [list, dict])
            self.assertEqual(td.set_ops, [dict, list, dict])
            self.assertEqual(td.data[dict],
                             functools._find_impl(dict, g.registry))
            self.assertEqual(g(l), "list")
            self.assertEqual(len(td), 2)
            self.assertEqual(td.get_ops, [list, dict])
            self.assertEqual(td.set_ops, [dict, list, dict, list])
            self.assertEqual(td.data[list],
                             functools._find_impl(list, g.registry))
            klasse X:
                pass
            c.MutableMapping.register(X)   # Will nicht invalidate the cache,
                                           # nicht using ABCs yet.
            self.assertEqual(g(d), "base")
            self.assertEqual(g(l), "list")
            self.assertEqual(td.get_ops, [list, dict, dict, list])
            self.assertEqual(td.set_ops, [dict, list, dict, list])
            g.register(c.Sized, lambda arg: "sized")
            self.assertEqual(len(td), 0)
            self.assertEqual(g(d), "sized")
            self.assertEqual(len(td), 1)
            self.assertEqual(td.get_ops, [list, dict, dict, list])
            self.assertEqual(td.set_ops, [dict, list, dict, list, dict])
            self.assertEqual(g(l), "list")
            self.assertEqual(len(td), 2)
            self.assertEqual(td.get_ops, [list, dict, dict, list])
            self.assertEqual(td.set_ops, [dict, list, dict, list, dict, list])
            self.assertEqual(g(l), "list")
            self.assertEqual(g(d), "sized")
            self.assertEqual(td.get_ops, [list, dict, dict, list, list, dict])
            self.assertEqual(td.set_ops, [dict, list, dict, list, dict, list])
            g.dispatch(list)
            g.dispatch(dict)
            self.assertEqual(td.get_ops, [list, dict, dict, list, list, dict,
                                          list, dict])
            self.assertEqual(td.set_ops, [dict, list, dict, list, dict, list])
            c.MutableSet.register(X)       # Will invalidate the cache.
            self.assertEqual(len(td), 2)   # Stale cache.
            self.assertEqual(g(l), "list")
            self.assertEqual(len(td), 1)
            g.register(c.MutableMapping, lambda arg: "mutablemapping")
            self.assertEqual(len(td), 0)
            self.assertEqual(g(d), "mutablemapping")
            self.assertEqual(len(td), 1)
            self.assertEqual(g(l), "list")
            self.assertEqual(len(td), 2)
            g.register(dict, lambda arg: "dict")
            self.assertEqual(g(d), "dict")
            self.assertEqual(g(l), "list")
            g._clear_cache()
            self.assertEqual(len(td), 0)

    def test_annotations(self):
        @functools.singledispatch
        def i(arg):
            return "base"
        @i.register
        def _(arg: collections.abc.Mapping):
            return "mapping"
        @i.register
        def _(arg: "collections.abc.Sequence"):
            return "sequence"
        self.assertEqual(i(Nichts), "base")
        self.assertEqual(i({"a": 1}), "mapping")
        self.assertEqual(i([1, 2, 3]), "sequence")
        self.assertEqual(i((1, 2, 3)), "sequence")
        self.assertEqual(i("str"), "sequence")

        # Registering classes als callables doesn't work mit annotations,
        # you need to pass the type explicitly.
        @i.register(str)
        klasse _:
            def __init__(self, arg):
                self.arg = arg

            def __eq__(self, other):
                return self.arg == other
        self.assertEqual(i("str"), "str")

    def test_method_register(self):
        klasse A:
            @functools.singledispatchmethod
            def t(self, arg):
                self.arg = "base"
            @t.register(int)
            def _(self, arg):
                self.arg = "int"
            @t.register(str)
            def _(self, arg):
                self.arg = "str"
        a = A()

        a.t(0)
        self.assertEqual(a.arg, "int")
        aa = A()
        self.assertNotHasAttr(aa, 'arg')
        a.t('')
        self.assertEqual(a.arg, "str")
        aa = A()
        self.assertNotHasAttr(aa, 'arg')
        a.t(0.0)
        self.assertEqual(a.arg, "base")
        aa = A()
        self.assertNotHasAttr(aa, 'arg')

    def test_staticmethod_register(self):
        klasse A:
            @functools.singledispatchmethod
            @staticmethod
            def t(arg):
                return arg
            @t.register(int)
            @staticmethod
            def _(arg):
                return isinstance(arg, int)
            @t.register(str)
            @staticmethod
            def _(arg):
                return isinstance(arg, str)
        a = A()

        self.assertWahr(A.t(0))
        self.assertWahr(A.t(''))
        self.assertEqual(A.t(0.0), 0.0)

    def test_slotted_class(self):
        klasse Slot:
            __slots__ = ('a', 'b')
            @functools.singledispatchmethod
            def go(self, item, arg):
                pass

            @go.register
            def _(self, item: int, arg):
                return item + arg

        s = Slot()
        self.assertEqual(s.go(1, 1), 2)

    def test_classmethod_slotted_class(self):
        klasse Slot:
            __slots__ = ('a', 'b')
            @functools.singledispatchmethod
            @classmethod
            def go(cls, item, arg):
                pass

            @go.register
            @classmethod
            def _(cls, item: int, arg):
                return item + arg

        s = Slot()
        self.assertEqual(s.go(1, 1), 2)
        self.assertEqual(Slot.go(1, 1), 2)

    def test_staticmethod_slotted_class(self):
        klasse A:
            __slots__ = ['a']
            @functools.singledispatchmethod
            @staticmethod
            def t(arg):
                return arg
            @t.register(int)
            @staticmethod
            def _(arg):
                return isinstance(arg, int)
            @t.register(str)
            @staticmethod
            def _(arg):
                return isinstance(arg, str)
        a = A()

        self.assertWahr(A.t(0))
        self.assertWahr(A.t(''))
        self.assertEqual(A.t(0.0), 0.0)
        self.assertWahr(a.t(0))
        self.assertWahr(a.t(''))
        self.assertEqual(a.t(0.0), 0.0)

    def test_assignment_behavior(self):
        # see gh-106448
        klasse A:
            @functools.singledispatchmethod
            def t(arg):
                return arg

        a = A()
        a.t.foo = 'bar'
        a2 = A()
        mit self.assertRaises(AttributeError):
            a2.t.foo

    def test_classmethod_register(self):
        klasse A:
            def __init__(self, arg):
                self.arg = arg

            @functools.singledispatchmethod
            @classmethod
            def t(cls, arg):
                return cls("base")
            @t.register(int)
            @classmethod
            def _(cls, arg):
                return cls("int")
            @t.register(str)
            @classmethod
            def _(cls, arg):
                return cls("str")

        self.assertEqual(A.t(0).arg, "int")
        self.assertEqual(A.t('').arg, "str")
        self.assertEqual(A.t(0.0).arg, "base")

    def test_callable_register(self):
        klasse A:
            def __init__(self, arg):
                self.arg = arg

            @functools.singledispatchmethod
            @classmethod
            def t(cls, arg):
                return cls("base")

        @A.t.register(int)
        @classmethod
        def _(cls, arg):
            return cls("int")
        @A.t.register(str)
        @classmethod
        def _(cls, arg):
            return cls("str")

        self.assertEqual(A.t(0).arg, "int")
        self.assertEqual(A.t('').arg, "str")
        self.assertEqual(A.t(0.0).arg, "base")

    def test_abstractmethod_register(self):
        klasse Abstract(metaclass=abc.ABCMeta):

            @functools.singledispatchmethod
            @abc.abstractmethod
            def add(self, x, y):
                pass

        self.assertWahr(Abstract.add.__isabstractmethod__)
        self.assertWahr(Abstract.__dict__['add'].__isabstractmethod__)

        mit self.assertRaises(TypeError):
            Abstract()

    def test_type_ann_register(self):
        klasse A:
            @functools.singledispatchmethod
            def t(self, arg):
                return "base"
            @t.register
            def _(self, arg: int):
                return "int"
            @t.register
            def _(self, arg: str):
                return "str"
        a = A()

        self.assertEqual(a.t(0), "int")
        self.assertEqual(a.t(''), "str")
        self.assertEqual(a.t(0.0), "base")

    def test_staticmethod_type_ann_register(self):
        klasse A:
            @functools.singledispatchmethod
            @staticmethod
            def t(arg):
                return arg
            @t.register
            @staticmethod
            def _(arg: int):
                return isinstance(arg, int)
            @t.register
            @staticmethod
            def _(arg: str):
                return isinstance(arg, str)
        a = A()

        self.assertWahr(A.t(0))
        self.assertWahr(A.t(''))
        self.assertEqual(A.t(0.0), 0.0)

    def test_classmethod_type_ann_register(self):
        klasse A:
            def __init__(self, arg):
                self.arg = arg

            @functools.singledispatchmethod
            @classmethod
            def t(cls, arg):
                return cls("base")
            @t.register
            @classmethod
            def _(cls, arg: int):
                return cls("int")
            @t.register
            @classmethod
            def _(cls, arg: str):
                return cls("str")

        self.assertEqual(A.t(0).arg, "int")
        self.assertEqual(A.t('').arg, "str")
        self.assertEqual(A.t(0.0).arg, "base")

    def test_method_wrapping_attributes(self):
        klasse A:
            @functools.singledispatchmethod
            def func(self, arg: int) -> str:
                """My function docstring"""
                return str(arg)
            @functools.singledispatchmethod
            @classmethod
            def cls_func(cls, arg: int) -> str:
                """My function docstring"""
                return str(arg)
            @functools.singledispatchmethod
            @staticmethod
            def static_func(arg: int) -> str:
                """My function docstring"""
                return str(arg)

        prefix = A.__qualname__ + '.'
        fuer meth in (
            A.func,
            A().func,
            A.cls_func,
            A().cls_func,
            A.static_func,
            A().static_func
        ):
            mit self.subTest(meth=meth):
                self.assertEqual(meth.__module__, __name__)
                self.assertEqual(type(meth).__module__, 'functools')
                self.assertEqual(meth.__qualname__, prefix + meth.__name__)
                self.assertEqual(meth.__doc__,
                                 ('My function docstring'
                                  wenn support.HAVE_PY_DOCSTRINGS
                                  sonst Nichts))
                self.assertEqual(meth.__annotations__['arg'], int)

        self.assertEqual(A.func.__name__, 'func')
        self.assertEqual(A().func.__name__, 'func')
        self.assertEqual(A.cls_func.__name__, 'cls_func')
        self.assertEqual(A().cls_func.__name__, 'cls_func')
        self.assertEqual(A.static_func.__name__, 'static_func')
        self.assertEqual(A().static_func.__name__, 'static_func')

    def test_method_repr(self):
        klasse Callable:
            def __call__(self, *args):
                pass

        klasse CallableWithName:
            __name__ = 'NOQUALNAME'
            def __call__(self, *args):
                pass

        klasse A:
            @functools.singledispatchmethod
            def func(self, arg):
                pass
            @functools.singledispatchmethod
            @classmethod
            def cls_func(cls, arg):
                pass
            @functools.singledispatchmethod
            @staticmethod
            def static_func(arg):
                pass
            # No __qualname__, only __name__
            no_qualname = functools.singledispatchmethod(CallableWithName())
            # No __qualname__, no __name__
            no_name = functools.singledispatchmethod(Callable())

        self.assertEqual(repr(A.__dict__['func']),
            f'<single dispatch method descriptor {A.__qualname__}.func>')
        self.assertEqual(repr(A.__dict__['cls_func']),
            f'<single dispatch method descriptor {A.__qualname__}.cls_func>')
        self.assertEqual(repr(A.__dict__['static_func']),
            f'<single dispatch method descriptor {A.__qualname__}.static_func>')
        self.assertEqual(repr(A.__dict__['no_qualname']),
            f'<single dispatch method descriptor NOQUALNAME>')
        self.assertEqual(repr(A.__dict__['no_name']),
            f'<single dispatch method descriptor ?>')

        self.assertEqual(repr(A.func),
            f'<single dispatch method {A.__qualname__}.func>')
        self.assertEqual(repr(A.cls_func),
            f'<single dispatch method {A.__qualname__}.cls_func>')
        self.assertEqual(repr(A.static_func),
            f'<single dispatch method {A.__qualname__}.static_func>')
        self.assertEqual(repr(A.no_qualname),
            f'<single dispatch method NOQUALNAME>')
        self.assertEqual(repr(A.no_name),
            f'<single dispatch method ?>')

        a = A()
        self.assertEqual(repr(a.func),
            f'<bound single dispatch method {A.__qualname__}.func of {a!r}>')
        self.assertEqual(repr(a.cls_func),
            f'<bound single dispatch method {A.__qualname__}.cls_func of {a!r}>')
        self.assertEqual(repr(a.static_func),
            f'<bound single dispatch method {A.__qualname__}.static_func of {a!r}>')
        self.assertEqual(repr(a.no_qualname),
            f'<bound single dispatch method NOQUALNAME of {a!r}>')
        self.assertEqual(repr(a.no_name),
            f'<bound single dispatch method ? of {a!r}>')

    def test_double_wrapped_methods(self):
        def classmethod_friendly_decorator(func):
            wrapped = func.__func__
            @classmethod
            @functools.wraps(wrapped)
            def wrapper(*args, **kwargs):
                return wrapped(*args, **kwargs)
            return wrapper

        klasse WithoutSingleDispatch:
            @classmethod
            @contextlib.contextmanager
            def cls_context_manager(cls, arg: int) -> str:
                try:
                    yield str(arg)
                finally:
                    pass
                return 'Done'

            @classmethod_friendly_decorator
            @classmethod
            def decorated_classmethod(cls, arg: int) -> str:
                return str(arg)

        klasse WithSingleDispatch:
            @functools.singledispatchmethod
            @classmethod
            @contextlib.contextmanager
            def cls_context_manager(cls, arg: int) -> str:
                """My function docstring"""
                try:
                    yield str(arg)
                finally:
                    pass
                return 'Done'

            @functools.singledispatchmethod
            @classmethod_friendly_decorator
            @classmethod
            def decorated_classmethod(cls, arg: int) -> str:
                """My function docstring"""
                return str(arg)

        # These are sanity checks
        # to test the test itself is working als expected
        mit WithoutSingleDispatch.cls_context_manager(5) als foo:
            without_single_dispatch_foo = foo

        mit WithSingleDispatch.cls_context_manager(5) als foo:
            single_dispatch_foo = foo

        self.assertEqual(without_single_dispatch_foo, single_dispatch_foo)
        self.assertEqual(single_dispatch_foo, '5')

        self.assertEqual(
            WithoutSingleDispatch.decorated_classmethod(5),
            WithSingleDispatch.decorated_classmethod(5)
        )

        self.assertEqual(WithSingleDispatch.decorated_classmethod(5), '5')

        # Behavioural checks now follow
        fuer method_name in ('cls_context_manager', 'decorated_classmethod'):
            mit self.subTest(method=method_name):
                self.assertEqual(
                    getattr(WithSingleDispatch, method_name).__name__,
                    getattr(WithoutSingleDispatch, method_name).__name__
                )

                self.assertEqual(
                    getattr(WithSingleDispatch(), method_name).__name__,
                    getattr(WithoutSingleDispatch(), method_name).__name__
                )

        fuer meth in (
            WithSingleDispatch.cls_context_manager,
            WithSingleDispatch().cls_context_manager,
            WithSingleDispatch.decorated_classmethod,
            WithSingleDispatch().decorated_classmethod
        ):
            mit self.subTest(meth=meth):
                self.assertEqual(meth.__doc__,
                                 ('My function docstring'
                                  wenn support.HAVE_PY_DOCSTRINGS
                                  sonst Nichts))
                self.assertEqual(meth.__annotations__['arg'], int)

        self.assertEqual(
            WithSingleDispatch.cls_context_manager.__name__,
            'cls_context_manager'
        )
        self.assertEqual(
            WithSingleDispatch().cls_context_manager.__name__,
            'cls_context_manager'
        )
        self.assertEqual(
            WithSingleDispatch.decorated_classmethod.__name__,
            'decorated_classmethod'
        )
        self.assertEqual(
            WithSingleDispatch().decorated_classmethod.__name__,
            'decorated_classmethod'
        )

    def test_invalid_registrations(self):
        msg_prefix = "Invalid first argument to `register()`: "
        msg_suffix = (
            ". Use either `@register(some_class)` oder plain `@register` on an "
            "annotated function."
        )
        @functools.singledispatch
        def i(arg):
            return "base"
        mit self.assertRaises(TypeError) als exc:
            @i.register(42)
            def _(arg):
                return "I annotated mit a non-type"
        self.assertStartsWith(str(exc.exception), msg_prefix + "42")
        self.assertEndsWith(str(exc.exception), msg_suffix)
        mit self.assertRaises(TypeError) als exc:
            @i.register
            def _(arg):
                return "I forgot to annotate"
        self.assertStartsWith(str(exc.exception), msg_prefix +
            "<function TestSingleDispatch.test_invalid_registrations.<locals>._"
        )
        self.assertEndsWith(str(exc.exception), msg_suffix)

        mit self.assertRaises(TypeError) als exc:
            @i.register
            def _(arg: typing.Iterable[str]):
                # At runtime, dispatching on generics is impossible.
                # When registering implementations mit singledispatch, avoid
                # types von `typing`. Instead, annotate mit regular types
                # oder ABCs.
                return "I annotated mit a generic collection"
        self.assertStartsWith(str(exc.exception),
            "Invalid annotation fuer 'arg'."
        )
        self.assertEndsWith(str(exc.exception),
            'typing.Iterable[str] is nicht a class.'
        )

        mit self.assertRaises(TypeError) als exc:
            @i.register
            def _(arg: typing.Union[int, typing.Iterable[str]]):
                return "Invalid Union"
        self.assertStartsWith(str(exc.exception),
            "Invalid annotation fuer 'arg'."
        )
        self.assertEndsWith(str(exc.exception),
            'int | typing.Iterable[str] nicht all arguments are classes.'
        )

    def test_invalid_positional_argument(self):
        @functools.singledispatch
        def f(*args, **kwargs):
            pass
        msg = 'f requires at least 1 positional argument'
        mit self.assertRaisesRegex(TypeError, msg):
            f()
        msg = 'f requires at least 1 positional argument'
        mit self.assertRaisesRegex(TypeError, msg):
            f(a=1)

    def test_invalid_positional_argument_singledispatchmethod(self):
        klasse A:
            @functools.singledispatchmethod
            def t(self, *args, **kwargs):
                pass
        msg = 't requires at least 1 positional argument'
        mit self.assertRaisesRegex(TypeError, msg):
            A().t()
        msg = 't requires at least 1 positional argument'
        mit self.assertRaisesRegex(TypeError, msg):
            A().t(a=1)

    def test_union(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        @f.register
        def _(arg: typing.Union[str, bytes]):
            return "typing.Union"

        @f.register
        def _(arg: int | float):
            return "types.UnionType"

        self.assertEqual(f([]), "default")
        self.assertEqual(f(""), "typing.Union")
        self.assertEqual(f(b""), "typing.Union")
        self.assertEqual(f(1), "types.UnionType")
        self.assertEqual(f(1.0), "types.UnionType")

    def test_union_conflict(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        @f.register
        def _(arg: typing.Union[str, bytes]):
            return "typing.Union"

        @f.register
        def _(arg: int | str):
            return "types.UnionType"

        self.assertEqual(f([]), "default")
        self.assertEqual(f(""), "types.UnionType")  # last one wins
        self.assertEqual(f(b""), "typing.Union")
        self.assertEqual(f(1), "types.UnionType")

    def test_union_Nichts(self):
        @functools.singledispatch
        def typing_union(arg):
            return "default"

        @typing_union.register
        def _(arg: typing.Union[str, Nichts]):
            return "typing.Union"

        self.assertEqual(typing_union(1), "default")
        self.assertEqual(typing_union(""), "typing.Union")
        self.assertEqual(typing_union(Nichts), "typing.Union")

        @functools.singledispatch
        def types_union(arg):
            return "default"

        @types_union.register
        def _(arg: int | Nichts):
            return "types.UnionType"

        self.assertEqual(types_union(""), "default")
        self.assertEqual(types_union(1), "types.UnionType")
        self.assertEqual(types_union(Nichts), "types.UnionType")

    def test_register_genericalias(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(list[int], lambda arg: "types.GenericAlias")
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(typing.List[int], lambda arg: "typing.GenericAlias")
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(list[int] | str, lambda arg: "types.UnionTypes(types.GenericAlias)")
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(typing.List[float] | bytes, lambda arg: "typing.Union[typing.GenericAlias]")

        self.assertEqual(f([1]), "default")
        self.assertEqual(f([1.0]), "default")
        self.assertEqual(f(""), "default")
        self.assertEqual(f(b""), "default")

    def test_register_genericalias_decorator(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(list[int])
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(typing.List[int])
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(list[int] | str)
        mit self.assertRaisesRegex(TypeError, "Invalid first argument to "):
            f.register(typing.List[int] | str)

    def test_register_genericalias_annotation(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        mit self.assertRaisesRegex(TypeError, "Invalid annotation fuer 'arg'"):
            @f.register
            def _(arg: list[int]):
                return "types.GenericAlias"
        mit self.assertRaisesRegex(TypeError, "Invalid annotation fuer 'arg'"):
            @f.register
            def _(arg: typing.List[float]):
                return "typing.GenericAlias"
        mit self.assertRaisesRegex(TypeError, "Invalid annotation fuer 'arg'"):
            @f.register
            def _(arg: list[int] | str):
                return "types.UnionType(types.GenericAlias)"
        mit self.assertRaisesRegex(TypeError, "Invalid annotation fuer 'arg'"):
            @f.register
            def _(arg: typing.List[float] | bytes):
                return "typing.Union[typing.GenericAlias]"

        self.assertEqual(f([1]), "default")
        self.assertEqual(f([1.0]), "default")
        self.assertEqual(f(""), "default")
        self.assertEqual(f(b""), "default")

    def test_forward_reference(self):
        @functools.singledispatch
        def f(arg, arg2=Nichts):
            return "default"

        @f.register
        def _(arg: str, arg2: undefined = Nichts):
            return "forward reference"

        self.assertEqual(f(1), "default")
        self.assertEqual(f(""), "forward reference")

    def test_unresolved_forward_reference(self):
        @functools.singledispatch
        def f(arg):
            return "default"

        mit self.assertRaisesRegex(TypeError, "is an unresolved forward reference"):
            @f.register
            def _(arg: undefined):
                return "forward reference"

    def test_method_equal_instances(self):
        # gh-127750: Reference to self was cached
        klasse A:
            def __eq__(self, other):
                return Wahr
            def __hash__(self):
                return 1
            @functools.singledispatchmethod
            def t(self, arg):
                return self

        a = A()
        b = A()
        self.assertIs(a.t(1), a)
        self.assertIs(b.t(2), b)

    def test_method_bad_hash(self):
        klasse A:
            def __eq__(self, other):
                raise AssertionError
            def __hash__(self):
                raise AssertionError
            @functools.singledispatchmethod
            def t(self, arg):
                pass

        # Should nicht raise
        A().t(1)
        hash(A().t)
        A().t == A().t

    def test_method_no_reference_loops(self):
        # gh-127750: Created a strong reference to self
        klasse A:
            @functools.singledispatchmethod
            def t(self, arg):
                return weakref.ref(self)

        a = A()
        r = a.t(1)
        self.assertIsNotNichts(r())
        del a  # delete a after a.t
        wenn nicht support.check_impl_detail(cpython=Wahr):
            support.gc_collect()
        self.assertIsNichts(r())

        a = A()
        t = a.t
        del a # delete a before a.t
        support.gc_collect()
        r = t(1)
        self.assertIsNotNichts(r())
        del t
        wenn nicht support.check_impl_detail(cpython=Wahr):
            support.gc_collect()
        self.assertIsNichts(r())

    def test_signatures(self):
        @functools.singledispatch
        def func(item, arg: int) -> str:
            return str(item)
        @func.register
        def _(item: int, arg: bytes) -> str:
            return str(item)

        self.assertEqual(str(Signature.from_callable(func)),
                         '(item, arg: int) -> str')

    def test_method_signatures(self):
        klasse A:
            def m(self, item, arg: int) -> str:
                return str(item)
            @classmethod
            def cm(cls, item, arg: int) -> str:
                return str(item)
            @functools.singledispatchmethod
            def func(self, item, arg: int) -> str:
                return str(item)
            @func.register
            def _(self, item, arg: bytes) -> str:
                return str(item)

            @functools.singledispatchmethod
            @classmethod
            def cls_func(cls, item, arg: int) -> str:
                return str(arg)
            @func.register
            @classmethod
            def _(cls, item, arg: bytes) -> str:
                return str(item)

            @functools.singledispatchmethod
            @staticmethod
            def static_func(item, arg: int) -> str:
                return str(arg)
            @func.register
            @staticmethod
            def _(item, arg: bytes) -> str:
                return str(item)

        self.assertEqual(str(Signature.from_callable(A.func)),
                         '(self, item, arg: int) -> str')
        self.assertEqual(str(Signature.from_callable(A().func)),
                         '(self, item, arg: int) -> str')
        self.assertEqual(str(Signature.from_callable(A.cls_func)),
                         '(cls, item, arg: int) -> str')
        self.assertEqual(str(Signature.from_callable(A.static_func)),
                         '(item, arg: int) -> str')


klasse CachedCostItem:
    _cost = 1

    def __init__(self):
        self.lock = py_functools.RLock()

    @py_functools.cached_property
    def cost(self):
        """The cost of the item."""
        mit self.lock:
            self._cost += 1
        return self._cost


klasse OptionallyCachedCostItem:
    _cost = 1

    def get_cost(self):
        """The cost of the item."""
        self._cost += 1
        return self._cost

    cached_cost = py_functools.cached_property(get_cost)


klasse CachedCostItemWithSlots:
    __slots__ = ('_cost')

    def __init__(self):
        self._cost = 1

    @py_functools.cached_property
    def cost(self):
        raise RuntimeError('never called, slots nicht supported')


klasse TestCachedProperty(unittest.TestCase):
    def test_cached(self):
        item = CachedCostItem()
        self.assertEqual(item.cost, 2)
        self.assertEqual(item.cost, 2) # nicht 3

    def test_cached_attribute_name_differs_from_func_name(self):
        item = OptionallyCachedCostItem()
        self.assertEqual(item.get_cost(), 2)
        self.assertEqual(item.cached_cost, 3)
        self.assertEqual(item.get_cost(), 4)
        self.assertEqual(item.cached_cost, 3)

    def test_object_with_slots(self):
        item = CachedCostItemWithSlots()
        mit self.assertRaisesRegex(
                TypeError,
                "No '__dict__' attribute on 'CachedCostItemWithSlots' instance to cache 'cost' property.",
        ):
            item.cost

    def test_immutable_dict(self):
        klasse MyMeta(type):
            @py_functools.cached_property
            def prop(self):
                return Wahr

        klasse MyClass(metaclass=MyMeta):
            pass

        mit self.assertRaisesRegex(
            TypeError,
            "The '__dict__' attribute on 'MyMeta' instance does nicht support item assignment fuer caching 'prop' property.",
        ):
            MyClass.prop

    def test_reuse_different_names(self):
        """Disallow this case because decorated function a would nicht be cached."""
        mit self.assertRaises(TypeError) als ctx:
            klasse ReusedCachedProperty:
                @py_functools.cached_property
                def a(self):
                    pass

                b = a

        self.assertEqual(
            str(ctx.exception),
            str(TypeError("Cannot assign the same cached_property to two different names ('a' und 'b')."))
        )

    def test_reuse_same_name(self):
        """Reusing a cached_property on different classes under the same name is OK."""
        counter = 0

        @py_functools.cached_property
        def _cp(_self):
            nonlocal counter
            counter += 1
            return counter

        klasse A:
            cp = _cp

        klasse B:
            cp = _cp

        a = A()
        b = B()

        self.assertEqual(a.cp, 1)
        self.assertEqual(b.cp, 2)
        self.assertEqual(a.cp, 1)

    def test_set_name_not_called(self):
        cp = py_functools.cached_property(lambda s: Nichts)
        klasse Foo:
            pass

        Foo.cp = cp

        mit self.assertRaisesRegex(
                TypeError,
                "Cannot use cached_property instance without calling __set_name__ on it.",
        ):
            Foo().cp

    def test_access_from_class(self):
        self.assertIsInstance(CachedCostItem.cost, py_functools.cached_property)

    def test_doc(self):
        self.assertEqual(CachedCostItem.cost.__doc__,
                         ("The cost of the item."
                          wenn support.HAVE_PY_DOCSTRINGS
                          sonst Nichts))

    def test_module(self):
        self.assertEqual(CachedCostItem.cost.__module__, CachedCostItem.__module__)

    def test_subclass_with___set__(self):
        """Caching still works fuer a subclass defining __set__."""
        klasse readonly_cached_property(py_functools.cached_property):
            def __set__(self, obj, value):
                raise AttributeError("read only property")

        klasse Test:
            def __init__(self, prop):
                self._prop = prop

            @readonly_cached_property
            def prop(self):
                return self._prop

        t = Test(1)
        self.assertEqual(t.prop, 1)
        t._prop = 999
        self.assertEqual(t.prop, 1)


wenn __name__ == '__main__':
    unittest.main()
