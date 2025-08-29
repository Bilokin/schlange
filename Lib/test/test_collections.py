"""Unit tests fuer collections.py."""

importiere array
importiere collections
importiere copy
importiere doctest
importiere inspect
importiere operator
importiere pickle
von random importiere choice, randrange
von itertools importiere product, chain, combinations
importiere string
importiere sys
von test importiere support
importiere types
importiere unittest

von collections importiere namedtuple, Counter, OrderedDict, _count_elements
von collections importiere UserDict, UserString, UserList
von collections importiere ChainMap
von collections importiere deque
von collections.abc importiere Awaitable, Coroutine
von collections.abc importiere AsyncIterator, AsyncIterable, AsyncGenerator
von collections.abc importiere Hashable, Iterable, Iterator, Generator, Reversible
von collections.abc importiere Sized, Container, Callable, Collection
von collections.abc importiere Set, MutableSet
von collections.abc importiere Mapping, MutableMapping, KeysView, ItemsView, ValuesView
von collections.abc importiere Sequence, MutableSequence
von collections.abc importiere Buffer


klasse TestUserObjects(unittest.TestCase):
    def _superset_test(self, a, b):
        self.assertGreaterEqual(
            set(dir(a)),
            set(dir(b)),
            '{a} should have all the methods of {b}'.format(
                a=a.__name__,
                b=b.__name__,
            ),
        )

    def _copy_test(self, obj):
        # Test internal copy
        obj_copy = obj.copy()
        self.assertIsNot(obj.data, obj_copy.data)
        self.assertEqual(obj.data, obj_copy.data)

        # Test copy.copy
        obj.test = [1234]  # Make sure instance vars are also copied.
        obj_copy = copy.copy(obj)
        self.assertIsNot(obj.data, obj_copy.data)
        self.assertEqual(obj.data, obj_copy.data)
        self.assertIs(obj.test, obj_copy.test)

    def test_str_protocol(self):
        self._superset_test(UserString, str)

    def test_list_protocol(self):
        self._superset_test(UserList, list)

    def test_dict_protocol(self):
        self._superset_test(UserDict, dict)

    def test_list_copy(self):
        obj = UserList()
        obj.append(123)
        self._copy_test(obj)

    def test_dict_copy(self):
        obj = UserDict()
        obj[123] = "abc"
        self._copy_test(obj)

    def test_dict_missing(self):
        klasse A(UserDict):
            def __missing__(self, key):
                gib 456
        self.assertEqual(A()[123], 456)
        # get() ignores __missing__ on dict
        self.assertIs(A().get(123), Nichts)


################################################################################
### ChainMap (helper klasse fuer configparser und the string module)
################################################################################

klasse TestChainMap(unittest.TestCase):

    def test_basics(self):
        c = ChainMap()
        c['a'] = 1
        c['b'] = 2
        d = c.new_child()
        d['b'] = 20
        d['c'] = 30
        self.assertEqual(d.maps, [{'b':20, 'c':30}, {'a':1, 'b':2}])  # check internal state
        self.assertEqual(d.items(), dict(a=1, b=20, c=30).items())    # check items/iter/getitem
        self.assertEqual(len(d), 3)                                   # check len
        fuer key in 'abc':                                             # check contains
            self.assertIn(key, d)
        fuer k, v in dict(a=1, b=20, c=30, z=100).items():             # check get
            self.assertEqual(d.get(k, 100), v)

        del d['b']                                                    # unmask a value
        self.assertEqual(d.maps, [{'c':30}, {'a':1, 'b':2}])          # check internal state
        self.assertEqual(d.items(), dict(a=1, b=2, c=30).items())     # check items/iter/getitem
        self.assertEqual(len(d), 3)                                   # check len
        fuer key in 'abc':                                             # check contains
            self.assertIn(key, d)
        fuer k, v in dict(a=1, b=2, c=30, z=100).items():              # check get
            self.assertEqual(d.get(k, 100), v)
        self.assertIn(repr(d), [                                      # check repr
            type(d).__name__ + "({'c': 30}, {'a': 1, 'b': 2})",
            type(d).__name__ + "({'c': 30}, {'b': 2, 'a': 1})"
        ])

        fuer e in d.copy(), copy.copy(d):                               # check shallow copies
            self.assertEqual(d, e)
            self.assertEqual(d.maps, e.maps)
            self.assertIsNot(d, e)
            self.assertIsNot(d.maps[0], e.maps[0])
            fuer m1, m2 in zip(d.maps[1:], e.maps[1:]):
                self.assertIs(m1, m2)

        # check deep copies
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            e = pickle.loads(pickle.dumps(d, proto))
            self.assertEqual(d, e)
            self.assertEqual(d.maps, e.maps)
            self.assertIsNot(d, e)
            fuer m1, m2 in zip(d.maps, e.maps):
                self.assertIsNot(m1, m2, e)
        fuer e in [copy.deepcopy(d),
                  eval(repr(d))
                ]:
            self.assertEqual(d, e)
            self.assertEqual(d.maps, e.maps)
            self.assertIsNot(d, e)
            fuer m1, m2 in zip(d.maps, e.maps):
                self.assertIsNot(m1, m2, e)

        f = d.new_child()
        f['b'] = 5
        self.assertEqual(f.maps, [{'b': 5}, {'c':30}, {'a':1, 'b':2}])
        self.assertEqual(f.parents.maps, [{'c':30}, {'a':1, 'b':2}])   # check parents
        self.assertEqual(f['b'], 5)                                    # find first in chain
        self.assertEqual(f.parents['b'], 2)                            # look beyond maps[0]

    def test_ordering(self):
        # Combined order matches a series of dict updates von last to first.
        # This test relies on the ordering of the underlying dicts.

        baseline = {'music': 'bach', 'art': 'rembrandt'}
        adjustments = {'art': 'van gogh', 'opera': 'carmen'}

        cm = ChainMap(adjustments, baseline)

        combined = baseline.copy()
        combined.update(adjustments)

        self.assertEqual(list(combined.items()), list(cm.items()))

    def test_constructor(self):
        self.assertEqual(ChainMap().maps, [{}])                        # no-args --> one new dict
        self.assertEqual(ChainMap({1:2}).maps, [{1:2}])                # 1 arg --> list

    def test_bool(self):
        self.assertFalsch(ChainMap())
        self.assertFalsch(ChainMap({}, {}))
        self.assertWahr(ChainMap({1:2}, {}))
        self.assertWahr(ChainMap({}, {1:2}))

    def test_missing(self):
        klasse DefaultChainMap(ChainMap):
            def __missing__(self, key):
                gib 999
        d = DefaultChainMap(dict(a=1, b=2), dict(b=20, c=30))
        fuer k, v in dict(a=1, b=2, c=30, d=999).items():
            self.assertEqual(d[k], v)                                  # check __getitem__ w/missing
        fuer k, v in dict(a=1, b=2, c=30, d=77).items():
            self.assertEqual(d.get(k, 77), v)                          # check get() w/ missing
        fuer k, v in dict(a=Wahr, b=Wahr, c=Wahr, d=Falsch).items():
            self.assertEqual(k in d, v)                                # check __contains__ w/missing
        self.assertEqual(d.pop('a', 1001), 1, d)
        self.assertEqual(d.pop('a', 1002), 1002)                       # check pop() w/missing
        self.assertEqual(d.popitem(), ('b', 2))                        # check popitem() w/missing
        mit self.assertRaises(KeyError):
            d.popitem()

    def test_order_preservation(self):
        d = ChainMap(
                OrderedDict(j=0, h=88888),
                OrderedDict(),
                OrderedDict(i=9999, d=4444, c=3333),
                OrderedDict(f=666, b=222, g=777, c=333, h=888),
                OrderedDict(),
                OrderedDict(e=55, b=22),
                OrderedDict(a=1, b=2, c=3, d=4, e=5),
                OrderedDict(),
            )
        self.assertEqual(''.join(d), 'abcdefghij')
        self.assertEqual(list(d.items()),
            [('a', 1), ('b', 222), ('c', 3333), ('d', 4444),
             ('e', 55), ('f', 666), ('g', 777), ('h', 88888),
             ('i', 9999), ('j', 0)])

    def test_iter_not_calling_getitem_on_maps(self):
        klasse DictWithGetItem(UserDict):
            def __init__(self, *args, **kwds):
                self.called = Falsch
                UserDict.__init__(self, *args, **kwds)
            def __getitem__(self, item):
                self.called = Wahr
                UserDict.__getitem__(self, item)

        d = DictWithGetItem(a=1)
        c = ChainMap(d)
        d.called = Falsch

        set(c)  # iterate over chain map
        self.assertFalsch(d.called, '__getitem__ was called')

    def test_dict_coercion(self):
        d = ChainMap(dict(a=1, b=2), dict(b=20, c=30))
        self.assertEqual(dict(d), dict(a=1, b=2, c=30))
        self.assertEqual(dict(d.items()), dict(a=1, b=2, c=30))

    def test_new_child(self):
        'Tests fuer changes fuer issue #16613.'
        c = ChainMap()
        c['a'] = 1
        c['b'] = 2
        m = {'b':20, 'c': 30}
        d = c.new_child(m)
        self.assertEqual(d.maps, [{'b':20, 'c':30}, {'a':1, 'b':2}])  # check internal state
        self.assertIs(m, d.maps[0])

        # Use a different map than a dict
        klasse lowerdict(dict):
            def __getitem__(self, key):
                wenn isinstance(key, str):
                    key = key.lower()
                gib dict.__getitem__(self, key)
            def __contains__(self, key):
                wenn isinstance(key, str):
                    key = key.lower()
                gib dict.__contains__(self, key)

        c = ChainMap()
        c['a'] = 1
        c['b'] = 2
        m = lowerdict(b=20, c=30)
        d = c.new_child(m)
        self.assertIs(m, d.maps[0])
        fuer key in 'abc':                                             # check contains
            self.assertIn(key, d)
        fuer k, v in dict(a=1, B=20, C=30, z=100).items():             # check get
            self.assertEqual(d.get(k, 100), v)

        c = ChainMap({'a': 1, 'b': 2})
        d = c.new_child(b=20, c=30)
        self.assertEqual(d.maps, [{'b': 20, 'c': 30}, {'a': 1, 'b': 2}])

    def test_union_operators(self):
        cm1 = ChainMap(dict(a=1, b=2), dict(c=3, d=4))
        cm2 = ChainMap(dict(a=10, e=5), dict(b=20, d=4))
        cm3 = cm1.copy()
        d = dict(a=10, c=30)
        pairs = [('c', 3), ('p',0)]

        tmp = cm1 | cm2 # testing between chainmaps
        self.assertEqual(tmp.maps, [cm1.maps[0] | dict(cm2), *cm1.maps[1:]])
        cm1 |= cm2
        self.assertEqual(tmp, cm1)

        tmp = cm2 | d # testing between chainmap und mapping
        self.assertEqual(tmp.maps, [cm2.maps[0] | d, *cm2.maps[1:]])
        self.assertEqual((d | cm2).maps, [d | dict(cm2)])
        cm2 |= d
        self.assertEqual(tmp, cm2)

        # testing behavior between chainmap und iterable key-value pairs
        mit self.assertRaises(TypeError):
            cm3 | pairs
        tmp = cm3.copy()
        cm3 |= pairs
        self.assertEqual(cm3.maps, [tmp.maps[0] | dict(pairs), *tmp.maps[1:]])

        # testing proper gib types fuer ChainMap und it's subclasses
        klasse Subclass(ChainMap):
            pass

        klasse SubclassRor(ChainMap):
            def __ror__(self, other):
                gib super().__ror__(other)

        tmp = ChainMap() | ChainMap()
        self.assertIs(type(tmp), ChainMap)
        self.assertIs(type(tmp.maps[0]), dict)
        tmp = ChainMap() | Subclass()
        self.assertIs(type(tmp), ChainMap)
        self.assertIs(type(tmp.maps[0]), dict)
        tmp = Subclass() | ChainMap()
        self.assertIs(type(tmp), Subclass)
        self.assertIs(type(tmp.maps[0]), dict)
        tmp = ChainMap() | SubclassRor()
        self.assertIs(type(tmp), SubclassRor)
        self.assertIs(type(tmp.maps[0]), dict)


################################################################################
### Named Tuples
################################################################################

TestNT = namedtuple('TestNT', 'x y z')    # type used fuer pickle tests

klasse TestNamedTuple(unittest.TestCase):

    def test_factory(self):
        Point = namedtuple('Point', 'x y')
        self.assertEqual(Point.__name__, 'Point')
        self.assertEqual(Point.__slots__, ())
        self.assertEqual(Point.__module__, __name__)
        self.assertEqual(Point.__getitem__, tuple.__getitem__)
        self.assertEqual(Point._fields, ('x', 'y'))

        self.assertRaises(ValueError, namedtuple, 'abc%', 'efg ghi')       # type has non-alpha char
        self.assertRaises(ValueError, namedtuple, 'class', 'efg ghi')      # type has keyword
        self.assertRaises(ValueError, namedtuple, '9abc', 'efg ghi')       # type starts mit digit

        self.assertRaises(ValueError, namedtuple, 'abc', 'efg g%hi')       # field mit non-alpha char
        self.assertRaises(ValueError, namedtuple, 'abc', 'abc class')      # field has keyword
        self.assertRaises(ValueError, namedtuple, 'abc', '8efg 9ghi')      # field starts mit digit
        self.assertRaises(ValueError, namedtuple, 'abc', '_efg ghi')       # field mit leading underscore
        self.assertRaises(ValueError, namedtuple, 'abc', 'efg efg ghi')    # duplicate field

        namedtuple('Point0', 'x1 y2')   # Verify that numbers are allowed in names
        namedtuple('_', 'a b c')        # Test leading underscores in a typename

        nt = namedtuple('nt', 'the quick brown fox')                       # check unicode input
        self.assertNotIn("u'", repr(nt._fields))
        nt = namedtuple('nt', ('the', 'quick'))                           # check unicode input
        self.assertNotIn("u'", repr(nt._fields))

        self.assertRaises(TypeError, Point._make, [11])                     # catch too few args
        self.assertRaises(TypeError, Point._make, [11, 22, 33])             # catch too many args

    def test_defaults(self):
        Point = namedtuple('Point', 'x y', defaults=(10, 20))              # 2 defaults
        self.assertEqual(Point._field_defaults, {'x': 10, 'y': 20})
        self.assertEqual(Point(1, 2), (1, 2))
        self.assertEqual(Point(1), (1, 20))
        self.assertEqual(Point(), (10, 20))

        Point = namedtuple('Point', 'x y', defaults=(20,))                 # 1 default
        self.assertEqual(Point._field_defaults, {'y': 20})
        self.assertEqual(Point(1, 2), (1, 2))
        self.assertEqual(Point(1), (1, 20))

        Point = namedtuple('Point', 'x y', defaults=())                     # 0 defaults
        self.assertEqual(Point._field_defaults, {})
        self.assertEqual(Point(1, 2), (1, 2))
        mit self.assertRaises(TypeError):
            Point(1)

        mit self.assertRaises(TypeError):                                  # catch too few args
            Point()
        mit self.assertRaises(TypeError):                                  # catch too many args
            Point(1, 2, 3)
        mit self.assertRaises(TypeError):                                  # too many defaults
            Point = namedtuple('Point', 'x y', defaults=(10, 20, 30))
        mit self.assertRaises(TypeError):                                  # non-iterable defaults
            Point = namedtuple('Point', 'x y', defaults=10)
        mit self.assertRaises(TypeError):                                  # another non-iterable default
            Point = namedtuple('Point', 'x y', defaults=Falsch)

        Point = namedtuple('Point', 'x y', defaults=Nichts)                   # default is Nichts
        self.assertEqual(Point._field_defaults, {})
        self.assertIsNichts(Point.__new__.__defaults__, Nichts)
        self.assertEqual(Point(10, 20), (10, 20))
        mit self.assertRaises(TypeError):                                  # catch too few args
            Point(10)

        Point = namedtuple('Point', 'x y', defaults=[10, 20])               # allow non-tuple iterable
        self.assertEqual(Point._field_defaults, {'x': 10, 'y': 20})
        self.assertEqual(Point.__new__.__defaults__, (10, 20))
        self.assertEqual(Point(1, 2), (1, 2))
        self.assertEqual(Point(1), (1, 20))
        self.assertEqual(Point(), (10, 20))

        Point = namedtuple('Point', 'x y', defaults=iter([10, 20]))         # allow plain iterator
        self.assertEqual(Point._field_defaults, {'x': 10, 'y': 20})
        self.assertEqual(Point.__new__.__defaults__, (10, 20))
        self.assertEqual(Point(1, 2), (1, 2))
        self.assertEqual(Point(1), (1, 20))
        self.assertEqual(Point(), (10, 20))

    def test_readonly(self):
        Point = namedtuple('Point', 'x y')
        p = Point(11, 22)
        mit self.assertRaises(AttributeError):
            p.x = 33
        mit self.assertRaises(AttributeError):
            del p.x
        mit self.assertRaises(TypeError):
            p[0] = 33
        mit self.assertRaises(TypeError):
            del p[0]
        self.assertEqual(p.x, 11)
        self.assertEqual(p[0], 11)

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_factory_doc_attr(self):
        Point = namedtuple('Point', 'x y')
        self.assertEqual(Point.__doc__, 'Point(x, y)')
        Point.__doc__ = '2D point'
        self.assertEqual(Point.__doc__, '2D point')

    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_field_doc(self):
        Point = namedtuple('Point', 'x y')
        self.assertEqual(Point.x.__doc__, 'Alias fuer field number 0')
        self.assertEqual(Point.y.__doc__, 'Alias fuer field number 1')
        Point.x.__doc__ = 'docstring fuer Point.x'
        self.assertEqual(Point.x.__doc__, 'docstring fuer Point.x')
        # namedtuple can mutate doc of descriptors independently
        Vector = namedtuple('Vector', 'x y')
        self.assertEqual(Vector.x.__doc__, 'Alias fuer field number 0')
        Vector.x.__doc__ = 'docstring fuer Vector.x'
        self.assertEqual(Vector.x.__doc__, 'docstring fuer Vector.x')

    @support.cpython_only
    @unittest.skipIf(sys.flags.optimize >= 2,
                     "Docstrings are omitted mit -O2 und above")
    def test_field_doc_reuse(self):
        P = namedtuple('P', ['m', 'n'])
        Q = namedtuple('Q', ['o', 'p'])
        self.assertIs(P.m.__doc__, Q.o.__doc__)
        self.assertIs(P.n.__doc__, Q.p.__doc__)

    @support.cpython_only
    def test_field_repr(self):
        Point = namedtuple('Point', 'x y')
        self.assertEqual(repr(Point.x), "_tuplegetter(0, 'Alias fuer field number 0')")
        self.assertEqual(repr(Point.y), "_tuplegetter(1, 'Alias fuer field number 1')")

        Point.x.__doc__ = 'The x-coordinate'
        Point.y.__doc__ = 'The y-coordinate'

        self.assertEqual(repr(Point.x), "_tuplegetter(0, 'The x-coordinate')")
        self.assertEqual(repr(Point.y), "_tuplegetter(1, 'The y-coordinate')")

    def test_name_fixer(self):
        fuer spec, renamed in [
            [('efg', 'g%hi'),  ('efg', '_1')],                              # field mit non-alpha char
            [('abc', 'class'), ('abc', '_1')],                              # field has keyword
            [('8efg', '9ghi'), ('_0', '_1')],                               # field starts mit digit
            [('abc', '_efg'), ('abc', '_1')],                               # field mit leading underscore
            [('abc', 'efg', 'efg', 'ghi'), ('abc', 'efg', '_2', 'ghi')],    # duplicate field
            [('abc', '', 'x'), ('abc', '_1', 'x')],                         # fieldname is a space
        ]:
            self.assertEqual(namedtuple('NT', spec, rename=Wahr)._fields, renamed)

    def test_module_parameter(self):
        NT = namedtuple('NT', ['x', 'y'], module=collections)
        self.assertEqual(NT.__module__, collections)

    def test_instance(self):
        Point = namedtuple('Point', 'x y')
        p = Point(11, 22)
        self.assertEqual(p, Point(x=11, y=22))
        self.assertEqual(p, Point(11, y=22))
        self.assertEqual(p, Point(y=22, x=11))
        self.assertEqual(p, Point(*(11, 22)))
        self.assertEqual(p, Point(**dict(x=11, y=22)))
        self.assertRaises(TypeError, Point, 1)          # too few args
        self.assertRaises(TypeError, Point, 1, 2, 3)    # too many args
        mit self.assertRaises(TypeError):              # wrong keyword argument
            Point(XXX=1, y=2)
        mit self.assertRaises(TypeError):              # missing keyword argument
            Point(x=1)
        self.assertEqual(repr(p), 'Point(x=11, y=22)')
        self.assertNotIn('__weakref__', dir(p))
        self.assertEqual(p, Point._make([11, 22]))      # test _make classmethod
        self.assertEqual(p._fields, ('x', 'y'))         # test _fields attribute
        self.assertEqual(p._replace(x=1), (1, 22))      # test _replace method
        self.assertEqual(p._asdict(), dict(x=11, y=22)) # test _asdict method

        mit self.assertRaises(TypeError):
            p._replace(x=1, error=2)

        # verify that field string can have commas
        Point = namedtuple('Point', 'x, y')
        p = Point(x=11, y=22)
        self.assertEqual(repr(p), 'Point(x=11, y=22)')

        # verify that fieldspec can be a non-string sequence
        Point = namedtuple('Point', ('x', 'y'))
        p = Point(x=11, y=22)
        self.assertEqual(repr(p), 'Point(x=11, y=22)')

    def test_tupleness(self):
        Point = namedtuple('Point', 'x y')
        p = Point(11, 22)

        self.assertIsInstance(p, tuple)
        self.assertEqual(p, (11, 22))                                       # matches a real tuple
        self.assertEqual(tuple(p), (11, 22))                                # coercible to a real tuple
        self.assertEqual(list(p), [11, 22])                                 # coercible to a list
        self.assertEqual(max(p), 22)                                        # iterable
        self.assertEqual(max(*p), 22)                                       # star-able
        x, y = p
        self.assertEqual(p, (x, y))                                         # unpacks like a tuple
        self.assertEqual((p[0], p[1]), (11, 22))                            # indexable like a tuple
        mit self.assertRaises(IndexError):
            p[3]
        self.assertEqual(p[-1], 22)
        self.assertEqual(hash(p), hash((11, 22)))

        self.assertEqual(p.x, x)
        self.assertEqual(p.y, y)
        mit self.assertRaises(AttributeError):
            p.z

    def test_odd_sizes(self):
        Zero = namedtuple('Zero', '')
        self.assertEqual(Zero(), ())
        self.assertEqual(Zero._make([]), ())
        self.assertEqual(repr(Zero()), 'Zero()')
        self.assertEqual(Zero()._asdict(), {})
        self.assertEqual(Zero()._fields, ())

        Dot = namedtuple('Dot', 'd')
        self.assertEqual(Dot(1), (1,))
        self.assertEqual(Dot._make([1]), (1,))
        self.assertEqual(Dot(1).d, 1)
        self.assertEqual(repr(Dot(1)), 'Dot(d=1)')
        self.assertEqual(Dot(1)._asdict(), {'d':1})
        self.assertEqual(Dot(1)._replace(d=999), (999,))
        self.assertEqual(Dot(1)._fields, ('d',))

    @support.requires_resource('cpu')
    def test_large_size(self):
        n = support.exceeds_recursion_limit()
        names = list(set(''.join([choice(string.ascii_letters)
                                  fuer j in range(10)]) fuer i in range(n)))
        n = len(names)
        Big = namedtuple('Big', names)
        b = Big(*range(n))
        self.assertEqual(b, tuple(range(n)))
        self.assertEqual(Big._make(range(n)), tuple(range(n)))
        fuer pos, name in enumerate(names):
            self.assertEqual(getattr(b, name), pos)
        repr(b)                                 # make sure repr() doesn't blow-up
        d = b._asdict()
        d_expected = dict(zip(names, range(n)))
        self.assertEqual(d, d_expected)
        b2 = b._replace(**dict([(names[1], 999),(names[-5], 42)]))
        b2_expected = list(range(n))
        b2_expected[1] = 999
        b2_expected[-5] = 42
        self.assertEqual(b2, tuple(b2_expected))
        self.assertEqual(b._fields, tuple(names))

    def test_pickle(self):
        p = TestNT(x=10, y=20, z=30)
        fuer module in (pickle,):
            loads = getattr(module, 'loads')
            dumps = getattr(module, 'dumps')
            fuer protocol in range(-1, module.HIGHEST_PROTOCOL + 1):
                q = loads(dumps(p, protocol))
                self.assertEqual(p, q)
                self.assertEqual(p._fields, q._fields)
                self.assertNotIn(b'OrderedDict', dumps(p, protocol))

    def test_copy(self):
        p = TestNT(x=10, y=20, z=30)
        fuer copier in copy.copy, copy.deepcopy:
            q = copier(p)
            self.assertEqual(p, q)
            self.assertEqual(p._fields, q._fields)

    def test_name_conflicts(self):
        # Some names like "self", "cls", "tuple", "itemgetter", und "property"
        # failed when used als field names.  Test to make sure these now work.
        T = namedtuple('T', 'itemgetter property self cls tuple')
        t = T(1, 2, 3, 4, 5)
        self.assertEqual(t, (1,2,3,4,5))
        newt = t._replace(itemgetter=10, property=20, self=30, cls=40, tuple=50)
        self.assertEqual(newt, (10,20,30,40,50))

       # Broader test of all interesting names taken von the code, old
       # template, und an example
        words = {'Alias', 'At', 'AttributeError', 'Build', 'Bypass', 'Create',
        'Encountered', 'Expected', 'Field', 'For', 'Got', 'Helper',
        'IronPython', 'Jython', 'KeyError', 'Make', 'Modify', 'Note',
        'OrderedDict', 'Point', 'Return', 'Returns', 'Type', 'TypeError',
        'Used', 'Validate', 'ValueError', 'Variables', 'a', 'accessible', 'add',
        'added', 'all', 'also', 'an', 'arg_list', 'args', 'arguments',
        'automatically', 'be', 'build', 'builtins', 'but', 'by', 'cannot',
        'class_namespace', 'classmethod', 'cls', 'collections', 'convert',
        'copy', 'created', 'creation', 'd', 'debugging', 'defined', 'dict',
        'dictionary', 'doc', 'docstring', 'docstrings', 'duplicate', 'effect',
        'either', 'enumerate', 'environments', 'error', 'example', 'exec', 'f',
        'f_globals', 'field', 'field_names', 'fields', 'formatted', 'frame',
        'function', 'functions', 'generate', 'get', 'getter', 'got', 'greater',
        'has', 'help', 'identifiers', 'index', 'indexable', 'instance',
        'instantiate', 'interning', 'introspection', 'isidentifier',
        'isinstance', 'itemgetter', 'iterable', 'join', 'keyword', 'keywords',
        'kwds', 'len', 'like', 'list', 'map', 'maps', 'message', 'metadata',
        'method', 'methods', 'module', 'module_name', 'must', 'name', 'named',
        'namedtuple', 'namedtuple_', 'names', 'namespace', 'needs', 'new',
        'nicely', 'num_fields', 'number', 'object', 'of', 'operator', 'option',
        'p', 'particular', 'pickle', 'pickling', 'plain', 'pop', 'positional',
        'property', 'r', 'regular', 'rename', 'replace', 'replacing', 'repr',
        'repr_fmt', 'representation', 'result', 'reuse_itemgetter', 's', 'seen',
        'self', 'sequence', 'set', 'side', 'specified', 'split', 'start',
        'startswith', 'step', 'str', 'string', 'strings', 'subclass', 'sys',
        'targets', 'than', 'the', 'their', 'this', 'to', 'tuple', 'tuple_new',
        'type', 'typename', 'underscore', 'unexpected', 'unpack', 'up', 'use',
        'used', 'user', 'valid', 'values', 'variable', 'verbose', 'where',
        'which', 'work', 'x', 'y', 'z', 'zip'}
        T = namedtuple('T', words)
        # test __new__
        values = tuple(range(len(words)))
        t = T(*values)
        self.assertEqual(t, values)
        t = T(**dict(zip(T._fields, values)))
        self.assertEqual(t, values)
        # test _make
        t = T._make(values)
        self.assertEqual(t, values)
        # exercise __repr__
        repr(t)
        # test _asdict
        self.assertEqual(t._asdict(), dict(zip(T._fields, values)))
        # test _replace
        t = T._make(values)
        newvalues = tuple(v*10 fuer v in values)
        newt = t._replace(**dict(zip(T._fields, newvalues)))
        self.assertEqual(newt, newvalues)
        # test _fields
        self.assertEqual(T._fields, tuple(words))
        # test __getnewargs__
        self.assertEqual(t.__getnewargs__(), values)

    def test_repr(self):
        A = namedtuple('A', 'x')
        self.assertEqual(repr(A(1)), 'A(x=1)')
        # repr should show the name of the subclass
        klasse B(A):
            pass
        self.assertEqual(repr(B(1)), 'B(x=1)')

    def test_keyword_only_arguments(self):
        # See issue 25628
        mit self.assertRaises(TypeError):
            NT = namedtuple('NT', ['x', 'y'], Wahr)

        NT = namedtuple('NT', ['abc', 'def'], rename=Wahr)
        self.assertEqual(NT._fields, ('abc', '_1'))
        mit self.assertRaises(TypeError):
            NT = namedtuple('NT', ['abc', 'def'], Falsch, Wahr)

    def test_namedtuple_subclass_issue_24931(self):
        klasse Point(namedtuple('_Point', ['x', 'y'])):
            pass

        a = Point(3, 4)
        self.assertEqual(a._asdict(), OrderedDict([('x', 3), ('y', 4)]))

        a.w = 5
        self.assertEqual(a.__dict__, {'w': 5})

    @support.cpython_only
    def test_field_descriptor(self):
        Point = namedtuple('Point', 'x y')
        p = Point(11, 22)
        self.assertWahr(inspect.isdatadescriptor(Point.x))
        self.assertEqual(Point.x.__get__(p), 11)
        self.assertRaises(AttributeError, Point.x.__set__, p, 33)
        self.assertRaises(AttributeError, Point.x.__delete__, p)

        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                klasse NewPoint(tuple):
                    x = pickle.loads(pickle.dumps(Point.x, proto))
                    y = pickle.loads(pickle.dumps(Point.y, proto))

                np = NewPoint([1, 2])

                self.assertEqual(np.x, 1)
                self.assertEqual(np.y, 2)

    def test_new_builtins_issue_43102(self):
        obj = namedtuple('C', ())
        new_func = obj.__new__
        self.assertEqual(new_func.__globals__['__builtins__'], {})
        self.assertEqual(new_func.__builtins__, {})

    def test_match_args(self):
        Point = namedtuple('Point', 'x y')
        self.assertEqual(Point.__match_args__, ('x', 'y'))

    def test_non_generic_subscript(self):
        # For backward compatibility, subscription works
        # on arbitrary named tuple types.
        Group = collections.namedtuple('Group', 'key group')
        A = Group[int, list[int]]
        self.assertEqual(A.__origin__, Group)
        self.assertEqual(A.__parameters__, ())
        self.assertEqual(A.__args__, (int, list[int]))
        a = A(1, [2])
        self.assertIs(type(a), Group)
        self.assertEqual(a, (1, [2]))


################################################################################
### Abstract Base Classes
################################################################################

klasse ABCTestCase(unittest.TestCase):

    def validate_abstract_methods(self, abc, *names):
        methodstubs = dict.fromkeys(names, lambda s, *args: 0)

        # everything should work will all required methods are present
        C = type('C', (abc,), methodstubs)
        C()

        # instantiation should fail wenn a required method is missing
        fuer name in names:
            stubs = methodstubs.copy()
            del stubs[name]
            C = type('C', (abc,), stubs)
            self.assertRaises(TypeError, C)

    def validate_isinstance(self, abc, name):
        stub = lambda s, *args: 0

        C = type('C', (object,), {'__hash__': Nichts})
        setattr(C, name, stub)
        self.assertIsInstance(C(), abc)
        self.assertIsSubclass(C, abc)

        C = type('C', (object,), {'__hash__': Nichts})
        self.assertNotIsInstance(C(), abc)
        self.assertNotIsSubclass(C, abc)

    def validate_comparison(self, instance):
        ops = ['lt', 'gt', 'le', 'ge', 'ne', 'or', 'and', 'xor', 'sub']
        operators = {}
        fuer op in ops:
            name = '__' + op + '__'
            operators[name] = getattr(operator, name)

        klasse Other:
            def __init__(self):
                self.right_side = Falsch
            def __eq__(self, other):
                self.right_side = Wahr
                gib Wahr
            __lt__ = __eq__
            __gt__ = __eq__
            __le__ = __eq__
            __ge__ = __eq__
            __ne__ = __eq__
            __ror__ = __eq__
            __rand__ = __eq__
            __rxor__ = __eq__
            __rsub__ = __eq__

        fuer name, op in operators.items():
            wenn nicht hasattr(instance, name):
                weiter
            other = Other()
            op(instance, other)
            self.assertWahr(other.right_side,'Right side nicht called fuer %s.%s'
                            % (type(instance), name))

def _test_gen():
    liefere

klasse TestOneTrickPonyABCs(ABCTestCase):

    def test_Awaitable(self):
        def gen():
            liefere

        @types.coroutine
        def coro():
            liefere

        async def new_coro():
            pass

        klasse Bar:
            def __await__(self):
                liefere

        klasse MinimalCoro(Coroutine):
            def send(self, value):
                gib value
            def throw(self, typ, val=Nichts, tb=Nichts):
                super().throw(typ, val, tb)
            def __await__(self):
                liefere

        self.validate_abstract_methods(Awaitable, '__await__')

        non_samples = [Nichts, int(), gen(), object()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Awaitable)
            self.assertNotIsSubclass(type(x), Awaitable)

        samples = [Bar(), MinimalCoro()]
        fuer x in samples:
            self.assertIsInstance(x, Awaitable)
            self.assertIsSubclass(type(x), Awaitable)

        c = coro()
        # Iterable coroutines (generators mit CO_ITERABLE_COROUTINE
        # flag don't have '__await__' method, hence can't be instances
        # of Awaitable. Use inspect.isawaitable to detect them.
        self.assertNotIsInstance(c, Awaitable)

        c = new_coro()
        self.assertIsInstance(c, Awaitable)
        c.close() # avoid RuntimeWarning that coro() was nicht awaited

        klasse CoroLike: pass
        Coroutine.register(CoroLike)
        self.assertIsInstance(CoroLike(), Awaitable)
        self.assertIsSubclass(CoroLike, Awaitable)
        CoroLike = Nichts
        support.gc_collect() # Kill CoroLike to clean-up ABCMeta cache

    def test_Coroutine(self):
        def gen():
            liefere

        @types.coroutine
        def coro():
            liefere

        async def new_coro():
            pass

        klasse Bar:
            def __await__(self):
                liefere

        klasse MinimalCoro(Coroutine):
            def send(self, value):
                gib value
            def throw(self, typ, val=Nichts, tb=Nichts):
                super().throw(typ, val, tb)
            def __await__(self):
                liefere

        self.validate_abstract_methods(Coroutine, '__await__', 'send', 'throw')

        non_samples = [Nichts, int(), gen(), object(), Bar()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Coroutine)
            self.assertNotIsSubclass(type(x), Coroutine)

        samples = [MinimalCoro()]
        fuer x in samples:
            self.assertIsInstance(x, Awaitable)
            self.assertIsSubclass(type(x), Awaitable)

        c = coro()
        # Iterable coroutines (generators mit CO_ITERABLE_COROUTINE
        # flag don't have '__await__' method, hence can't be instances
        # of Coroutine. Use inspect.isawaitable to detect them.
        self.assertNotIsInstance(c, Coroutine)

        c = new_coro()
        self.assertIsInstance(c, Coroutine)
        c.close() # avoid RuntimeWarning that coro() was nicht awaited

        klasse CoroLike:
            def send(self, value):
                pass
            def throw(self, typ, val=Nichts, tb=Nichts):
                pass
            def close(self):
                pass
            def __await__(self):
                pass
        self.assertIsInstance(CoroLike(), Coroutine)
        self.assertIsSubclass(CoroLike, Coroutine)

        klasse CoroLike:
            def send(self, value):
                pass
            def close(self):
                pass
            def __await__(self):
                pass
        self.assertNotIsInstance(CoroLike(), Coroutine)
        self.assertNotIsSubclass(CoroLike, Coroutine)

    def test_Hashable(self):
        # Check some non-hashables
        non_samples = [bytearray(), list(), set(), dict()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Hashable)
            self.assertNotIsSubclass(type(x), Hashable)
        # Check some hashables
        samples = [Nichts,
                   int(), float(), complex(),
                   str(),
                   tuple(), frozenset(),
                   int, list, object, type, bytes()
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Hashable)
            self.assertIsSubclass(type(x), Hashable)
        self.assertRaises(TypeError, Hashable)
        # Check direct subclassing
        klasse H(Hashable):
            def __hash__(self):
                gib super().__hash__()
        self.assertEqual(hash(H()), 0)
        self.assertNotIsSubclass(int, H)
        self.validate_abstract_methods(Hashable, '__hash__')
        self.validate_isinstance(Hashable, '__hash__')

    def test_AsyncIterable(self):
        klasse AI:
            def __aiter__(self):
                gib self
        self.assertIsInstance(AI(), AsyncIterable)
        self.assertIsSubclass(AI, AsyncIterable)
        # Check some non-iterables
        non_samples = [Nichts, object, []]
        fuer x in non_samples:
            self.assertNotIsInstance(x, AsyncIterable)
            self.assertNotIsSubclass(type(x), AsyncIterable)
        self.validate_abstract_methods(AsyncIterable, '__aiter__')
        self.validate_isinstance(AsyncIterable, '__aiter__')

    def test_AsyncIterator(self):
        klasse AI:
            def __aiter__(self):
                gib self
            async def __anext__(self):
                raise StopAsyncIteration
        self.assertIsInstance(AI(), AsyncIterator)
        self.assertIsSubclass(AI, AsyncIterator)
        non_samples = [Nichts, object, []]
        # Check some non-iterables
        fuer x in non_samples:
            self.assertNotIsInstance(x, AsyncIterator)
            self.assertNotIsSubclass(type(x), AsyncIterator)
        # Similarly to regular iterators (see issue 10565)
        klasse AnextOnly:
            async def __anext__(self):
                raise StopAsyncIteration
        self.assertNotIsInstance(AnextOnly(), AsyncIterator)
        self.validate_abstract_methods(AsyncIterator, '__anext__')

    def test_Iterable(self):
        # Check some non-iterables
        non_samples = [Nichts, 42, 3.14, 1j]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Iterable)
            self.assertNotIsSubclass(type(x), Iterable)
        # Check some iterables
        samples = [bytes(), str(),
                   tuple(), list(), set(), frozenset(), dict(),
                   dict().keys(), dict().items(), dict().values(),
                   _test_gen(),
                   (x fuer x in []),
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Iterable)
            self.assertIsSubclass(type(x), Iterable)
        # Check direct subclassing
        klasse I(Iterable):
            def __iter__(self):
                gib super().__iter__()
        self.assertEqual(list(I()), [])
        self.assertNotIsSubclass(str, I)
        self.validate_abstract_methods(Iterable, '__iter__')
        self.validate_isinstance(Iterable, '__iter__')
        # Check Nichts blocking
        klasse It:
            def __iter__(self): gib iter([])
        klasse ItBlocked(It):
            __iter__ = Nichts
        self.assertIsSubclass(It, Iterable)
        self.assertIsInstance(It(), Iterable)
        self.assertNotIsSubclass(ItBlocked, Iterable)
        self.assertNotIsInstance(ItBlocked(), Iterable)

    def test_Reversible(self):
        # Check some non-reversibles
        non_samples = [Nichts, 42, 3.14, 1j, set(), frozenset()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Reversible)
            self.assertNotIsSubclass(type(x), Reversible)
        # Check some non-reversible iterables
        non_reversibles = [_test_gen(), (x fuer x in []), iter([]), reversed([])]
        fuer x in non_reversibles:
            self.assertNotIsInstance(x, Reversible)
            self.assertNotIsSubclass(type(x), Reversible)
        # Check some reversible iterables
        samples = [bytes(), str(), tuple(), list(), OrderedDict(),
                   OrderedDict().keys(), OrderedDict().items(),
                   OrderedDict().values(), Counter(), Counter().keys(),
                   Counter().items(), Counter().values(), dict(),
                   dict().keys(), dict().items(), dict().values()]
        fuer x in samples:
            self.assertIsInstance(x, Reversible)
            self.assertIsSubclass(type(x), Reversible)
        # Check also Mapping, MutableMapping, und Sequence
        self.assertIsSubclass(Sequence, Reversible)
        self.assertNotIsSubclass(Mapping, Reversible)
        self.assertNotIsSubclass(MutableMapping, Reversible)
        # Check direct subclassing
        klasse R(Reversible):
            def __iter__(self):
                gib iter(list())
            def __reversed__(self):
                gib iter(list())
        self.assertEqual(list(reversed(R())), [])
        self.assertNotIsSubclass(float, R)
        self.validate_abstract_methods(Reversible, '__reversed__', '__iter__')
        # Check reversible non-iterable (which is nicht Reversible)
        klasse RevNoIter:
            def __reversed__(self): gib reversed([])
        klasse RevPlusIter(RevNoIter):
            def __iter__(self): gib iter([])
        self.assertNotIsSubclass(RevNoIter, Reversible)
        self.assertNotIsInstance(RevNoIter(), Reversible)
        self.assertIsSubclass(RevPlusIter, Reversible)
        self.assertIsInstance(RevPlusIter(), Reversible)
        # Check Nichts blocking
        klasse Rev:
            def __iter__(self): gib iter([])
            def __reversed__(self): gib reversed([])
        klasse RevItBlocked(Rev):
            __iter__ = Nichts
        klasse RevRevBlocked(Rev):
            __reversed__ = Nichts
        self.assertIsSubclass(Rev, Reversible)
        self.assertIsInstance(Rev(), Reversible)
        self.assertNotIsSubclass(RevItBlocked, Reversible)
        self.assertNotIsInstance(RevItBlocked(), Reversible)
        self.assertNotIsSubclass(RevRevBlocked, Reversible)
        self.assertNotIsInstance(RevRevBlocked(), Reversible)

    def test_Collection(self):
        # Check some non-collections
        non_collections = [Nichts, 42, 3.14, 1j, lambda x: 2*x]
        fuer x in non_collections:
            self.assertNotIsInstance(x, Collection)
            self.assertNotIsSubclass(type(x), Collection)
        # Check some non-collection iterables
        non_col_iterables = [_test_gen(), iter(b''), iter(bytearray()),
                             (x fuer x in [])]
        fuer x in non_col_iterables:
            self.assertNotIsInstance(x, Collection)
            self.assertNotIsSubclass(type(x), Collection)
        # Check some collections
        samples = [set(), frozenset(), dict(), bytes(), str(), tuple(),
                   list(), dict().keys(), dict().items(), dict().values()]
        fuer x in samples:
            self.assertIsInstance(x, Collection)
            self.assertIsSubclass(type(x), Collection)
        # Check also Mapping, MutableMapping, etc.
        self.assertIsSubclass(Sequence, Collection)
        self.assertIsSubclass(Mapping, Collection)
        self.assertIsSubclass(MutableMapping, Collection)
        self.assertIsSubclass(Set, Collection)
        self.assertIsSubclass(MutableSet, Collection)
        self.assertIsSubclass(Sequence, Collection)
        # Check direct subclassing
        klasse Col(Collection):
            def __iter__(self):
                gib iter(list())
            def __len__(self):
                gib 0
            def __contains__(self, item):
                gib Falsch
        klasse DerCol(Col): pass
        self.assertEqual(list(iter(Col())), [])
        self.assertNotIsSubclass(list, Col)
        self.assertNotIsSubclass(set, Col)
        self.assertNotIsSubclass(float, Col)
        self.assertEqual(list(iter(DerCol())), [])
        self.assertNotIsSubclass(list, DerCol)
        self.assertNotIsSubclass(set, DerCol)
        self.assertNotIsSubclass(float, DerCol)
        self.validate_abstract_methods(Collection, '__len__', '__iter__',
                                                   '__contains__')
        # Check sized container non-iterable (which is nicht Collection) etc.
        klasse ColNoIter:
            def __len__(self): gib 0
            def __contains__(self, item): gib Falsch
        klasse ColNoSize:
            def __iter__(self): gib iter([])
            def __contains__(self, item): gib Falsch
        klasse ColNoCont:
            def __iter__(self): gib iter([])
            def __len__(self): gib 0
        self.assertNotIsSubclass(ColNoIter, Collection)
        self.assertNotIsInstance(ColNoIter(), Collection)
        self.assertNotIsSubclass(ColNoSize, Collection)
        self.assertNotIsInstance(ColNoSize(), Collection)
        self.assertNotIsSubclass(ColNoCont, Collection)
        self.assertNotIsInstance(ColNoCont(), Collection)
        # Check Nichts blocking
        klasse SizeBlock:
            def __iter__(self): gib iter([])
            def __contains__(self): gib Falsch
            __len__ = Nichts
        klasse IterBlock:
            def __len__(self): gib 0
            def __contains__(self): gib Wahr
            __iter__ = Nichts
        self.assertNotIsSubclass(SizeBlock, Collection)
        self.assertNotIsInstance(SizeBlock(), Collection)
        self.assertNotIsSubclass(IterBlock, Collection)
        self.assertNotIsInstance(IterBlock(), Collection)
        # Check Nichts blocking in subclass
        klasse ColImpl:
            def __iter__(self):
                gib iter(list())
            def __len__(self):
                gib 0
            def __contains__(self, item):
                gib Falsch
        klasse NonCol(ColImpl):
            __contains__ = Nichts
        self.assertNotIsSubclass(NonCol, Collection)
        self.assertNotIsInstance(NonCol(), Collection)


    def test_Iterator(self):
        non_samples = [Nichts, 42, 3.14, 1j, b"", "", (), [], {}, set()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Iterator)
            self.assertNotIsSubclass(type(x), Iterator)
        samples = [iter(bytes()), iter(str()),
                   iter(tuple()), iter(list()), iter(dict()),
                   iter(set()), iter(frozenset()),
                   iter(dict().keys()), iter(dict().items()),
                   iter(dict().values()),
                   _test_gen(),
                   (x fuer x in []),
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Iterator)
            self.assertIsSubclass(type(x), Iterator)
        self.validate_abstract_methods(Iterator, '__next__')

        # Issue 10565
        klasse NextOnly:
            def __next__(self):
                liefere 1
                gib
        self.assertNotIsInstance(NextOnly(), Iterator)

    def test_Generator(self):
        klasse NonGen1:
            def __iter__(self): gib self
            def __next__(self): gib Nichts
            def close(self): pass
            def throw(self, typ, val=Nichts, tb=Nichts): pass

        klasse NonGen2:
            def __iter__(self): gib self
            def __next__(self): gib Nichts
            def close(self): pass
            def send(self, value): gib value

        klasse NonGen3:
            def close(self): pass
            def send(self, value): gib value
            def throw(self, typ, val=Nichts, tb=Nichts): pass

        non_samples = [
            Nichts, 42, 3.14, 1j, b"", "", (), [], {}, set(),
            iter(()), iter([]), NonGen1(), NonGen2(), NonGen3()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Generator)
            self.assertNotIsSubclass(type(x), Generator)

        klasse Gen:
            def __iter__(self): gib self
            def __next__(self): gib Nichts
            def close(self): pass
            def send(self, value): gib value
            def throw(self, typ, val=Nichts, tb=Nichts): pass

        klasse MinimalGen(Generator):
            def send(self, value):
                gib value
            def throw(self, typ, val=Nichts, tb=Nichts):
                super().throw(typ, val, tb)

        def gen():
            liefere 1

        samples = [gen(), (lambda: (yield))(), Gen(), MinimalGen()]
        fuer x in samples:
            self.assertIsInstance(x, Iterator)
            self.assertIsInstance(x, Generator)
            self.assertIsSubclass(type(x), Generator)
        self.validate_abstract_methods(Generator, 'send', 'throw')

        # mixin tests
        mgen = MinimalGen()
        self.assertIs(mgen, iter(mgen))
        self.assertIs(mgen.send(Nichts), next(mgen))
        self.assertEqual(2, mgen.send(2))
        self.assertIsNichts(mgen.close())
        self.assertRaises(ValueError, mgen.throw, ValueError)
        self.assertRaisesRegex(ValueError, "^huhu$",
                               mgen.throw, ValueError, ValueError("huhu"))
        self.assertRaises(StopIteration, mgen.throw, StopIteration())

        klasse FailOnClose(Generator):
            def send(self, value): gib value
            def throw(self, *args): raise ValueError

        self.assertRaises(ValueError, FailOnClose().close)

        klasse IgnoreGeneratorExit(Generator):
            def send(self, value): gib value
            def throw(self, *args): pass

        self.assertRaises(RuntimeError, IgnoreGeneratorExit().close)

    def test_AsyncGenerator(self):
        klasse NonAGen1:
            def __aiter__(self): gib self
            def __anext__(self): gib Nichts
            def aclose(self): pass
            def athrow(self, typ, val=Nichts, tb=Nichts): pass

        klasse NonAGen2:
            def __aiter__(self): gib self
            def __anext__(self): gib Nichts
            def aclose(self): pass
            def asend(self, value): gib value

        klasse NonAGen3:
            def aclose(self): pass
            def asend(self, value): gib value
            def athrow(self, typ, val=Nichts, tb=Nichts): pass

        non_samples = [
            Nichts, 42, 3.14, 1j, b"", "", (), [], {}, set(),
            iter(()), iter([]), NonAGen1(), NonAGen2(), NonAGen3()]
        fuer x in non_samples:
            self.assertNotIsInstance(x, AsyncGenerator)
            self.assertNotIsSubclass(type(x), AsyncGenerator)

        klasse Gen:
            def __aiter__(self): gib self
            async def __anext__(self): gib Nichts
            async def aclose(self): pass
            async def asend(self, value): gib value
            async def athrow(self, typ, val=Nichts, tb=Nichts): pass

        klasse MinimalAGen(AsyncGenerator):
            async def asend(self, value):
                gib value
            async def athrow(self, typ, val=Nichts, tb=Nichts):
                await super().athrow(typ, val, tb)

        async def gen():
            liefere 1

        samples = [gen(), Gen(), MinimalAGen()]
        fuer x in samples:
            self.assertIsInstance(x, AsyncIterator)
            self.assertIsInstance(x, AsyncGenerator)
            self.assertIsSubclass(type(x), AsyncGenerator)
        self.validate_abstract_methods(AsyncGenerator, 'asend', 'athrow')

        def run_async(coro):
            result = Nichts
            waehrend Wahr:
                try:
                    coro.send(Nichts)
                except StopIteration als ex:
                    result = ex.args[0] wenn ex.args sonst Nichts
                    breche
            gib result

        # mixin tests
        mgen = MinimalAGen()
        self.assertIs(mgen, mgen.__aiter__())
        self.assertIs(run_async(mgen.asend(Nichts)), run_async(mgen.__anext__()))
        self.assertEqual(2, run_async(mgen.asend(2)))
        self.assertIsNichts(run_async(mgen.aclose()))
        mit self.assertRaises(ValueError):
            run_async(mgen.athrow(ValueError))

        klasse FailOnClose(AsyncGenerator):
            async def asend(self, value): gib value
            async def athrow(self, *args): raise ValueError

        mit self.assertRaises(ValueError):
            run_async(FailOnClose().aclose())

        klasse IgnoreGeneratorExit(AsyncGenerator):
            async def asend(self, value): gib value
            async def athrow(self, *args): pass

        mit self.assertRaises(RuntimeError):
            run_async(IgnoreGeneratorExit().aclose())

    def test_Sized(self):
        non_samples = [Nichts, 42, 3.14, 1j,
                       _test_gen(),
                       (x fuer x in []),
                       ]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Sized)
            self.assertNotIsSubclass(type(x), Sized)
        samples = [bytes(), str(),
                   tuple(), list(), set(), frozenset(), dict(),
                   dict().keys(), dict().items(), dict().values(),
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Sized)
            self.assertIsSubclass(type(x), Sized)
        self.validate_abstract_methods(Sized, '__len__')
        self.validate_isinstance(Sized, '__len__')

    def test_Container(self):
        non_samples = [Nichts, 42, 3.14, 1j,
                       _test_gen(),
                       (x fuer x in []),
                       ]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Container)
            self.assertNotIsSubclass(type(x), Container)
        samples = [bytes(), str(),
                   tuple(), list(), set(), frozenset(), dict(),
                   dict().keys(), dict().items(),
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Container)
            self.assertIsSubclass(type(x), Container)
        self.validate_abstract_methods(Container, '__contains__')
        self.validate_isinstance(Container, '__contains__')

    def test_Callable(self):
        non_samples = [Nichts, 42, 3.14, 1j,
                       "", b"", (), [], {}, set(),
                       _test_gen(),
                       (x fuer x in []),
                       ]
        fuer x in non_samples:
            self.assertNotIsInstance(x, Callable)
            self.assertNotIsSubclass(type(x), Callable)
        samples = [lambda: Nichts,
                   type, int, object,
                   len,
                   list.append, [].append,
                   ]
        fuer x in samples:
            self.assertIsInstance(x, Callable)
            self.assertIsSubclass(type(x), Callable)
        self.validate_abstract_methods(Callable, '__call__')
        self.validate_isinstance(Callable, '__call__')

    def test_direct_subclassing(self):
        fuer B in Hashable, Iterable, Iterator, Reversible, Sized, Container, Callable:
            klasse C(B):
                pass
            self.assertIsSubclass(C, B)
            self.assertNotIsSubclass(int, C)

    def test_registration(self):
        fuer B in Hashable, Iterable, Iterator, Reversible, Sized, Container, Callable:
            klasse C:
                __hash__ = Nichts  # Make sure it isn't hashable by default
            self.assertNotIsSubclass(C, B)
            B.register(C)
            self.assertIsSubclass(C, B)

klasse WithSet(MutableSet):

    def __init__(self, it=()):
        self.data = set(it)

    def __len__(self):
        gib len(self.data)

    def __iter__(self):
        gib iter(self.data)

    def __contains__(self, item):
        gib item in self.data

    def add(self, item):
        self.data.add(item)

    def discard(self, item):
        self.data.discard(item)

klasse TestCollectionABCs(ABCTestCase):

    # XXX For now, we only test some virtual inheritance properties.
    # We should also test the proper behavior of the collection ABCs
    # als real base classes oder mix-in classes.

    def test_Set(self):
        fuer sample in [set, frozenset]:
            self.assertIsInstance(sample(), Set)
            self.assertIsSubclass(sample, Set)
        self.validate_abstract_methods(Set, '__contains__', '__iter__', '__len__')
        klasse MySet(Set):
            def __contains__(self, x):
                gib Falsch
            def __len__(self):
                gib 0
            def __iter__(self):
                gib iter([])
        self.validate_comparison(MySet())

    def test_hash_Set(self):
        klasse OneTwoThreeSet(Set):
            def __init__(self):
                self.contents = [1, 2, 3]
            def __contains__(self, x):
                gib x in self.contents
            def __len__(self):
                gib len(self.contents)
            def __iter__(self):
                gib iter(self.contents)
            def __hash__(self):
                gib self._hash()
        a, b = OneTwoThreeSet(), OneTwoThreeSet()
        self.assertWahr(hash(a) == hash(b))

    def test_isdisjoint_Set(self):
        klasse MySet(Set):
            def __init__(self, itr):
                self.contents = itr
            def __contains__(self, x):
                gib x in self.contents
            def __iter__(self):
                gib iter(self.contents)
            def __len__(self):
                gib len([x fuer x in self.contents])
        s1 = MySet((1, 2, 3))
        s2 = MySet((4, 5, 6))
        s3 = MySet((1, 5, 6))
        self.assertWahr(s1.isdisjoint(s2))
        self.assertFalsch(s1.isdisjoint(s3))

    def test_equality_Set(self):
        klasse MySet(Set):
            def __init__(self, itr):
                self.contents = itr
            def __contains__(self, x):
                gib x in self.contents
            def __iter__(self):
                gib iter(self.contents)
            def __len__(self):
                gib len([x fuer x in self.contents])
        s1 = MySet((1,))
        s2 = MySet((1, 2))
        s3 = MySet((3, 4))
        s4 = MySet((3, 4))
        self.assertWahr(s2 > s1)
        self.assertWahr(s1 < s2)
        self.assertFalsch(s2 <= s1)
        self.assertFalsch(s2 <= s3)
        self.assertFalsch(s1 >= s2)
        self.assertEqual(s3, s4)
        self.assertNotEqual(s2, s3)

    def test_arithmetic_Set(self):
        klasse MySet(Set):
            def __init__(self, itr):
                self.contents = itr
            def __contains__(self, x):
                gib x in self.contents
            def __iter__(self):
                gib iter(self.contents)
            def __len__(self):
                gib len([x fuer x in self.contents])
        s1 = MySet((1, 2, 3))
        s2 = MySet((3, 4, 5))
        s3 = s1 & s2
        self.assertEqual(s3, MySet((3,)))

    def test_MutableSet(self):
        self.assertIsInstance(set(), MutableSet)
        self.assertIsSubclass(set, MutableSet)
        self.assertNotIsInstance(frozenset(), MutableSet)
        self.assertNotIsSubclass(frozenset, MutableSet)
        self.validate_abstract_methods(MutableSet, '__contains__', '__iter__', '__len__',
            'add', 'discard')

    def test_issue_5647(self):
        # MutableSet.__iand__ mutated the set during iteration
        s = WithSet('abcd')
        s &= WithSet('cdef')            # This used to fail
        self.assertEqual(set(s), set('cd'))

    def test_issue_4920(self):
        # MutableSet.pop() method did nicht work
        klasse MySet(MutableSet):
            __slots__=['__s']
            def __init__(self,items=Nichts):
                wenn items is Nichts:
                    items=[]
                self.__s=set(items)
            def __contains__(self,v):
                gib v in self.__s
            def __iter__(self):
                gib iter(self.__s)
            def __len__(self):
                gib len(self.__s)
            def add(self,v):
                result=v nicht in self.__s
                self.__s.add(v)
                gib result
            def discard(self,v):
                result=v in self.__s
                self.__s.discard(v)
                gib result
            def __repr__(self):
                gib "MySet(%s)" % repr(list(self))
        items = [5,43,2,1]
        s = MySet(items)
        r = s.pop()
        self.assertEqual(len(s), len(items) - 1)
        self.assertNotIn(r, s)
        self.assertIn(r, items)

    def test_issue8750(self):
        empty = WithSet()
        full = WithSet(range(10))
        s = WithSet(full)
        s -= s
        self.assertEqual(s, empty)
        s = WithSet(full)
        s ^= s
        self.assertEqual(s, empty)
        s = WithSet(full)
        s &= s
        self.assertEqual(s, full)
        s |= s
        self.assertEqual(s, full)

    def test_issue16373(self):
        # Recursion error comparing comparable und noncomparable
        # Set instances
        klasse MyComparableSet(Set):
            def __contains__(self, x):
                gib Falsch
            def __len__(self):
                gib 0
            def __iter__(self):
                gib iter([])
        klasse MyNonComparableSet(Set):
            def __contains__(self, x):
                gib Falsch
            def __len__(self):
                gib 0
            def __iter__(self):
                gib iter([])
            def __le__(self, x):
                gib NotImplemented
            def __lt__(self, x):
                gib NotImplemented

        cs = MyComparableSet()
        ncs = MyNonComparableSet()
        self.assertFalsch(ncs < cs)
        self.assertWahr(ncs <= cs)
        self.assertFalsch(ncs > cs)
        self.assertWahr(ncs >= cs)

    def test_issue26915(self):
        # Container membership test should check identity first
        klasse CustomSequence(Sequence):
            def __init__(self, seq):
                self._seq = seq
            def __getitem__(self, index):
                gib self._seq[index]
            def __len__(self):
                gib len(self._seq)

        nan = float('nan')
        obj = support.NEVER_EQ
        seq = CustomSequence([nan, obj, nan])
        containers = [
            seq,
            ItemsView({1: nan, 2: obj}),
            KeysView({1: nan, 2: obj}),
            ValuesView({1: nan, 2: obj})
        ]
        fuer container in containers:
            fuer elem in container:
                self.assertIn(elem, container)
        self.assertEqual(seq.index(nan), 0)
        self.assertEqual(seq.index(obj), 1)
        self.assertEqual(seq.count(nan), 2)
        self.assertEqual(seq.count(obj), 1)

    def assertSameSet(self, s1, s2):
        # coerce both to a real set then check equality
        self.assertSetEqual(set(s1), set(s2))

    def test_Set_from_iterable(self):
        """Verify _from_iterable overridden to an instance method works."""
        klasse SetUsingInstanceFromIterable(MutableSet):
            def __init__(self, values, created_by):
                wenn nicht created_by:
                    raise ValueError('created_by must be specified')
                self.created_by = created_by
                self._values = set(values)

            def _from_iterable(self, values):
                gib type(self)(values, 'from_iterable')

            def __contains__(self, value):
                gib value in self._values

            def __iter__(self):
                liefere von self._values

            def __len__(self):
                gib len(self._values)

            def add(self, value):
                self._values.add(value)

            def discard(self, value):
                self._values.discard(value)

        impl = SetUsingInstanceFromIterable([1, 2, 3], 'test')

        actual = impl - {1}
        self.assertIsInstance(actual, SetUsingInstanceFromIterable)
        self.assertEqual('from_iterable', actual.created_by)
        self.assertEqual({2, 3}, actual)

        actual = impl | {4}
        self.assertIsInstance(actual, SetUsingInstanceFromIterable)
        self.assertEqual('from_iterable', actual.created_by)
        self.assertEqual({1, 2, 3, 4}, actual)

        actual = impl & {2}
        self.assertIsInstance(actual, SetUsingInstanceFromIterable)
        self.assertEqual('from_iterable', actual.created_by)
        self.assertEqual({2}, actual)

        actual = impl ^ {3, 4}
        self.assertIsInstance(actual, SetUsingInstanceFromIterable)
        self.assertEqual('from_iterable', actual.created_by)
        self.assertEqual({1, 2, 4}, actual)

        # NOTE: ixor'ing mit a list is important here: internally, __ixor__
        # only calls _from_iterable wenn the other value isn't already a Set.
        impl ^= [3, 4]
        self.assertIsInstance(impl, SetUsingInstanceFromIterable)
        self.assertEqual('test', impl.created_by)
        self.assertEqual({1, 2, 4}, impl)

    def test_Set_interoperability_with_real_sets(self):
        # Issue: 8743
        klasse ListSet(Set):
            def __init__(self, elements=()):
                self.data = []
                fuer elem in elements:
                    wenn elem nicht in self.data:
                        self.data.append(elem)
            def __contains__(self, elem):
                gib elem in self.data
            def __iter__(self):
                gib iter(self.data)
            def __len__(self):
                gib len(self.data)
            def __repr__(self):
                gib 'Set({!r})'.format(self.data)

        r1 = set('abc')
        r2 = set('bcd')
        r3 = set('abcde')
        f1 = ListSet('abc')
        f2 = ListSet('bcd')
        f3 = ListSet('abcde')
        l1 = list('abccba')
        l2 = list('bcddcb')
        l3 = list('abcdeedcba')

        target = r1 & r2
        self.assertSameSet(f1 & f2, target)
        self.assertSameSet(f1 & r2, target)
        self.assertSameSet(r2 & f1, target)
        self.assertSameSet(f1 & l2, target)

        target = r1 | r2
        self.assertSameSet(f1 | f2, target)
        self.assertSameSet(f1 | r2, target)
        self.assertSameSet(r2 | f1, target)
        self.assertSameSet(f1 | l2, target)

        fwd_target = r1 - r2
        rev_target = r2 - r1
        self.assertSameSet(f1 - f2, fwd_target)
        self.assertSameSet(f2 - f1, rev_target)
        self.assertSameSet(f1 - r2, fwd_target)
        self.assertSameSet(f2 - r1, rev_target)
        self.assertSameSet(r1 - f2, fwd_target)
        self.assertSameSet(r2 - f1, rev_target)
        self.assertSameSet(f1 - l2, fwd_target)
        self.assertSameSet(f2 - l1, rev_target)

        target = r1 ^ r2
        self.assertSameSet(f1 ^ f2, target)
        self.assertSameSet(f1 ^ r2, target)
        self.assertSameSet(r2 ^ f1, target)
        self.assertSameSet(f1 ^ l2, target)

        # Don't change the following to use assertLess oder other
        # "more specific" unittest assertions.  The current
        # assertWahr/assertFalsch style makes the pattern of test
        # case combinations clear und allows us to know fuer sure
        # the exact operator being invoked.

        # proper subset
        self.assertWahr(f1 < f3)
        self.assertFalsch(f1 < f1)
        self.assertFalsch(f1 < f2)
        self.assertWahr(r1 < f3)
        self.assertFalsch(r1 < f1)
        self.assertFalsch(r1 < f2)
        self.assertWahr(r1 < r3)
        self.assertFalsch(r1 < r1)
        self.assertFalsch(r1 < r2)
        mit self.assertRaises(TypeError):
            f1 < l3
        mit self.assertRaises(TypeError):
            f1 < l1
        mit self.assertRaises(TypeError):
            f1 < l2

        # any subset
        self.assertWahr(f1 <= f3)
        self.assertWahr(f1 <= f1)
        self.assertFalsch(f1 <= f2)
        self.assertWahr(r1 <= f3)
        self.assertWahr(r1 <= f1)
        self.assertFalsch(r1 <= f2)
        self.assertWahr(r1 <= r3)
        self.assertWahr(r1 <= r1)
        self.assertFalsch(r1 <= r2)
        mit self.assertRaises(TypeError):
            f1 <= l3
        mit self.assertRaises(TypeError):
            f1 <= l1
        mit self.assertRaises(TypeError):
            f1 <= l2

        # proper superset
        self.assertWahr(f3 > f1)
        self.assertFalsch(f1 > f1)
        self.assertFalsch(f2 > f1)
        self.assertWahr(r3 > r1)
        self.assertFalsch(f1 > r1)
        self.assertFalsch(f2 > r1)
        self.assertWahr(r3 > r1)
        self.assertFalsch(r1 > r1)
        self.assertFalsch(r2 > r1)
        mit self.assertRaises(TypeError):
            f1 > l3
        mit self.assertRaises(TypeError):
            f1 > l1
        mit self.assertRaises(TypeError):
            f1 > l2

        # any superset
        self.assertWahr(f3 >= f1)
        self.assertWahr(f1 >= f1)
        self.assertFalsch(f2 >= f1)
        self.assertWahr(r3 >= r1)
        self.assertWahr(f1 >= r1)
        self.assertFalsch(f2 >= r1)
        self.assertWahr(r3 >= r1)
        self.assertWahr(r1 >= r1)
        self.assertFalsch(r2 >= r1)
        mit self.assertRaises(TypeError):
            f1 >= l3
        mit self.assertRaises(TypeError):
            f1 >=l1
        mit self.assertRaises(TypeError):
            f1 >= l2

        # equality
        self.assertWahr(f1 == f1)
        self.assertWahr(r1 == f1)
        self.assertWahr(f1 == r1)
        self.assertFalsch(f1 == f3)
        self.assertFalsch(r1 == f3)
        self.assertFalsch(f1 == r3)
        self.assertFalsch(f1 == l3)
        self.assertFalsch(f1 == l1)
        self.assertFalsch(f1 == l2)

        # inequality
        self.assertFalsch(f1 != f1)
        self.assertFalsch(r1 != f1)
        self.assertFalsch(f1 != r1)
        self.assertWahr(f1 != f3)
        self.assertWahr(r1 != f3)
        self.assertWahr(f1 != r3)
        self.assertWahr(f1 != l3)
        self.assertWahr(f1 != l1)
        self.assertWahr(f1 != l2)

    def test_Set_hash_matches_frozenset(self):
        sets = [
            {}, {1}, {Nichts}, {-1}, {0.0}, {"abc"}, {1, 2, 3},
            {10**100, 10**101}, {"a", "b", "ab", ""}, {Falsch, Wahr},
            {object(), object(), object()}, {float("nan")},  {frozenset()},
            {*range(1000)}, {*range(1000)} - {100, 200, 300},
            {*range(sys.maxsize - 10, sys.maxsize + 10)},
        ]
        fuer s in sets:
            fs = frozenset(s)
            self.assertEqual(hash(fs), Set._hash(fs), msg=s)

    def test_Mapping(self):
        fuer sample in [dict]:
            self.assertIsInstance(sample(), Mapping)
            self.assertIsSubclass(sample, Mapping)
        self.validate_abstract_methods(Mapping, '__iter__', '__len__', '__getitem__')
        klasse MyMapping(Mapping):
            def __len__(self):
                gib 0
            def __getitem__(self, i):
                raise IndexError
            def __iter__(self):
                gib iter(())
        self.validate_comparison(MyMapping())
        self.assertRaises(TypeError, reversed, MyMapping())

    def test_MutableMapping(self):
        fuer sample in [dict]:
            self.assertIsInstance(sample(), MutableMapping)
            self.assertIsSubclass(sample, MutableMapping)
        self.validate_abstract_methods(MutableMapping, '__iter__', '__len__',
            '__getitem__', '__setitem__', '__delitem__')

    def test_MutableMapping_subclass(self):
        # Test issue 9214
        mymap = UserDict()
        mymap['red'] = 5
        self.assertIsInstance(mymap.keys(), Set)
        self.assertIsInstance(mymap.keys(), KeysView)
        self.assertIsInstance(mymap.values(), Collection)
        self.assertIsInstance(mymap.values(), ValuesView)
        self.assertIsInstance(mymap.items(), Set)
        self.assertIsInstance(mymap.items(), ItemsView)

        mymap = UserDict()
        mymap['red'] = 5
        z = mymap.keys() | {'orange'}
        self.assertIsInstance(z, set)
        list(z)
        mymap['blue'] = 7               # Shouldn't affect 'z'
        self.assertEqual(sorted(z), ['orange', 'red'])

        mymap = UserDict()
        mymap['red'] = 5
        z = mymap.items() | {('orange', 3)}
        self.assertIsInstance(z, set)
        list(z)
        mymap['blue'] = 7               # Shouldn't affect 'z'
        self.assertEqual(z, {('orange', 3), ('red', 5)})

    def test_Sequence(self):
        fuer sample in [tuple, list, bytes, str]:
            self.assertIsInstance(sample(), Sequence)
            self.assertIsSubclass(sample, Sequence)
        self.assertIsInstance(range(10), Sequence)
        self.assertIsSubclass(range, Sequence)
        self.assertIsInstance(memoryview(b""), Sequence)
        self.assertIsSubclass(memoryview, Sequence)
        self.assertIsSubclass(str, Sequence)
        self.validate_abstract_methods(Sequence, '__len__', '__getitem__')

    def test_Sequence_mixins(self):
        klasse SequenceSubclass(Sequence):
            def __init__(self, seq=()):
                self.seq = seq

            def __getitem__(self, index):
                gib self.seq[index]

            def __len__(self):
                gib len(self.seq)

        # Compare Sequence.index() behavior to (list|str).index() behavior
        def assert_index_same(seq1, seq2, index_args):
            try:
                expected = seq1.index(*index_args)
            except ValueError:
                mit self.assertRaises(ValueError):
                    seq2.index(*index_args)
            sonst:
                actual = seq2.index(*index_args)
                self.assertEqual(
                    actual, expected, '%r.index%s' % (seq1, index_args))

        fuer ty in list, str:
            nativeseq = ty('abracadabra')
            indexes = [-10000, -9999] + list(range(-3, len(nativeseq) + 3))
            seqseq = SequenceSubclass(nativeseq)
            fuer letter in set(nativeseq) | {'z'}:
                assert_index_same(nativeseq, seqseq, (letter,))
                fuer start in range(-3, len(nativeseq) + 3):
                    assert_index_same(nativeseq, seqseq, (letter, start))
                    fuer stop in range(-3, len(nativeseq) + 3):
                        assert_index_same(
                            nativeseq, seqseq, (letter, start, stop))

    def test_Buffer(self):
        fuer sample in [bytes, bytearray, memoryview]:
            self.assertIsInstance(sample(b"x"), Buffer)
            self.assertIsSubclass(sample, Buffer)
        fuer sample in [str, list, tuple]:
            self.assertNotIsInstance(sample(), Buffer)
            self.assertNotIsSubclass(sample, Buffer)
        self.validate_abstract_methods(Buffer, '__buffer__')

    def test_MutableSequence(self):
        fuer sample in [tuple, str, bytes]:
            self.assertNotIsInstance(sample(), MutableSequence)
            self.assertNotIsSubclass(sample, MutableSequence)
        fuer sample in [list, bytearray, deque]:
            self.assertIsInstance(sample(), MutableSequence)
            self.assertIsSubclass(sample, MutableSequence)
        self.assertIsSubclass(array.array, MutableSequence)
        self.assertNotIsSubclass(str, MutableSequence)
        self.validate_abstract_methods(MutableSequence, '__len__', '__getitem__',
                                       '__setitem__', '__delitem__', 'insert')

    def test_MutableSequence_mixins(self):
        # Test the mixins of MutableSequence by creating a minimal concrete
        # klasse inherited von it.
        klasse MutableSequenceSubclass(MutableSequence):
            def __init__(self):
                self.lst = []

            def __setitem__(self, index, value):
                self.lst[index] = value

            def __getitem__(self, index):
                gib self.lst[index]

            def __len__(self):
                gib len(self.lst)

            def __delitem__(self, index):
                del self.lst[index]

            def insert(self, index, value):
                self.lst.insert(index, value)

        mss = MutableSequenceSubclass()
        mss.append(0)
        mss.extend((1, 2, 3, 4))
        self.assertEqual(len(mss), 5)
        self.assertEqual(mss[3], 3)
        mss.reverse()
        self.assertEqual(mss[3], 1)
        mss.pop()
        self.assertEqual(len(mss), 4)
        mss.remove(3)
        self.assertEqual(len(mss), 3)
        mss += (10, 20, 30)
        self.assertEqual(len(mss), 6)
        self.assertEqual(mss[-1], 30)
        mss.clear()
        self.assertEqual(len(mss), 0)

        # issue 34427
        # extending self should nicht cause infinite loop
        items = 'ABCD'
        mss2 = MutableSequenceSubclass()
        mss2.extend(items + items)
        mss.clear()
        mss.extend(items)
        mss.extend(mss)
        self.assertEqual(len(mss), len(mss2))
        self.assertEqual(list(mss), list(mss2))

    def test_illegal_patma_flags(self):
        mit self.assertRaises(TypeError):
            klasse Both(Collection):
                __abc_tpflags__ = (Sequence.__flags__ | Mapping.__flags__)



################################################################################
### Counter
################################################################################

klasse CounterSubclassWithSetItem(Counter):
    # Test a counter subclass that overrides __setitem__
    def __init__(self, *args, **kwds):
        self.called = Falsch
        Counter.__init__(self, *args, **kwds)
    def __setitem__(self, key, value):
        self.called = Wahr
        Counter.__setitem__(self, key, value)

klasse CounterSubclassWithGet(Counter):
    # Test a counter subclass that overrides get()
    def __init__(self, *args, **kwds):
        self.called = Falsch
        Counter.__init__(self, *args, **kwds)
    def get(self, key, default):
        self.called = Wahr
        gib Counter.get(self, key, default)

klasse TestCounter(unittest.TestCase):

    def test_basics(self):
        c = Counter('abcaba')
        self.assertEqual(c, Counter({'a':3 , 'b': 2, 'c': 1}))
        self.assertEqual(c, Counter(a=3, b=2, c=1))
        self.assertIsInstance(c, dict)
        self.assertIsInstance(c, Mapping)
        self.assertIsSubclass(Counter, dict)
        self.assertIsSubclass(Counter, Mapping)
        self.assertEqual(len(c), 3)
        self.assertEqual(sum(c.values()), 6)
        self.assertEqual(list(c.values()), [3, 2, 1])
        self.assertEqual(list(c.keys()), ['a', 'b', 'c'])
        self.assertEqual(list(c), ['a', 'b', 'c'])
        self.assertEqual(list(c.items()),
                         [('a', 3), ('b', 2), ('c', 1)])
        self.assertEqual(c['b'], 2)
        self.assertEqual(c['z'], 0)
        self.assertEqual(c.__contains__('c'), Wahr)
        self.assertEqual(c.__contains__('z'), Falsch)
        self.assertEqual(c.get('b', 10), 2)
        self.assertEqual(c.get('z', 10), 10)
        self.assertEqual(c, dict(a=3, b=2, c=1))
        self.assertEqual(repr(c), "Counter({'a': 3, 'b': 2, 'c': 1})")
        self.assertEqual(c.most_common(), [('a', 3), ('b', 2), ('c', 1)])
        fuer i in range(5):
            self.assertEqual(c.most_common(i),
                             [('a', 3), ('b', 2), ('c', 1)][:i])
        self.assertEqual(''.join(c.elements()), 'aaabbc')
        c['a'] += 1         # increment an existing value
        c['b'] -= 2         # sub existing value to zero
        del c['c']          # remove an entry
        del c['c']          # make sure that del doesn't raise KeyError
        c['d'] -= 2         # sub von a missing value
        c['e'] = -5         # directly assign a missing value
        c['f'] += 4         # add to a missing value
        self.assertEqual(c, dict(a=4, b=0, d=-2, e=-5, f=4))
        self.assertEqual(''.join(c.elements()), 'aaaaffff')
        self.assertEqual(c.pop('f'), 4)
        self.assertNotIn('f', c)
        fuer i in range(3):
            elem, cnt = c.popitem()
            self.assertNotIn(elem, c)
        c.clear()
        self.assertEqual(c, {})
        self.assertEqual(repr(c), 'Counter()')
        self.assertRaises(NotImplementedError, Counter.fromkeys, 'abc')
        self.assertRaises(TypeError, hash, c)
        c.update(dict(a=5, b=3))
        c.update(c=1)
        c.update(Counter('a' * 50 + 'b' * 30))
        c.update()          # test case mit no args
        c.__init__('a' * 500 + 'b' * 300)
        c.__init__('cdc')
        c.__init__()
        self.assertEqual(c, dict(a=555, b=333, c=3, d=1))
        self.assertEqual(c.setdefault('d', 5), 1)
        self.assertEqual(c['d'], 1)
        self.assertEqual(c.setdefault('e', 5), 5)
        self.assertEqual(c['e'], 5)

    def test_init(self):
        self.assertEqual(list(Counter(self=42).items()), [('self', 42)])
        self.assertEqual(list(Counter(iterable=42).items()), [('iterable', 42)])
        self.assertEqual(list(Counter(iterable=Nichts).items()), [('iterable', Nichts)])
        self.assertRaises(TypeError, Counter, 42)
        self.assertRaises(TypeError, Counter, (), ())
        self.assertRaises(TypeError, Counter.__init__)

    def test_total(self):
        c = Counter(a=10, b=5, c=0)
        self.assertEqual(c.total(), 15)

    def test_order_preservation(self):
        # Input order dictates items() order
        self.assertEqual(list(Counter('abracadabra').items()),
               [('a', 5), ('b', 2), ('r', 2), ('c', 1), ('d', 1)])
        # letters mit same count:   ^----------^         ^---------^

        # Verify retention of order even when all counts are equal
        self.assertEqual(list(Counter('xyzpdqqdpzyx').items()),
               [('x', 2), ('y', 2), ('z', 2), ('p', 2), ('d', 2), ('q', 2)])

        # Input order dictates elements() order
        self.assertEqual(list(Counter('abracadabra simsalabim').elements()),
                ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'b', 'b', 'b','r',
                 'r', 'c', 'd', ' ', 's', 's', 'i', 'i', 'm', 'm', 'l'])

        # Math operations order first by the order encountered in the left
        # operand und then by the order encountered in the right operand.
        ps = 'aaabbcdddeefggghhijjjkkl'
        qs = 'abbcccdeefffhkkllllmmnno'
        order = {letter: i fuer i, letter in enumerate(dict.fromkeys(ps + qs))}
        def correctly_ordered(seq):
            'Return true wenn the letters occur in the expected order'
            positions = [order[letter] fuer letter in seq]
            gib positions == sorted(positions)

        p, q = Counter(ps), Counter(qs)
        self.assertWahr(correctly_ordered(+p))
        self.assertWahr(correctly_ordered(-p))
        self.assertWahr(correctly_ordered(p + q))
        self.assertWahr(correctly_ordered(p - q))
        self.assertWahr(correctly_ordered(p | q))
        self.assertWahr(correctly_ordered(p & q))

        p, q = Counter(ps), Counter(qs)
        p += q
        self.assertWahr(correctly_ordered(p))

        p, q = Counter(ps), Counter(qs)
        p -= q
        self.assertWahr(correctly_ordered(p))

        p, q = Counter(ps), Counter(qs)
        p |= q
        self.assertWahr(correctly_ordered(p))

        p, q = Counter(ps), Counter(qs)
        p &= q
        self.assertWahr(correctly_ordered(p))

        p, q = Counter(ps), Counter(qs)
        p.update(q)
        self.assertWahr(correctly_ordered(p))

        p, q = Counter(ps), Counter(qs)
        p.subtract(q)
        self.assertWahr(correctly_ordered(p))

    def test_update(self):
        c = Counter()
        c.update(self=42)
        self.assertEqual(list(c.items()), [('self', 42)])
        c = Counter()
        c.update(iterable=42)
        self.assertEqual(list(c.items()), [('iterable', 42)])
        c = Counter()
        c.update(iterable=Nichts)
        self.assertEqual(list(c.items()), [('iterable', Nichts)])
        self.assertRaises(TypeError, Counter().update, 42)
        self.assertRaises(TypeError, Counter().update, {}, {})
        self.assertRaises(TypeError, Counter.update)

    def test_copying(self):
        # Check that counters are copyable, deepcopyable, picklable, und
        #have a repr/eval round-trip
        words = Counter('which witch had which witches wrist watch'.split())
        def check(dup):
            msg = "\ncopy: %s\nwords: %s" % (dup, words)
            self.assertIsNot(dup, words, msg)
            self.assertEqual(dup, words)
        check(words.copy())
        check(copy.copy(words))
        check(copy.deepcopy(words))
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.subTest(proto=proto):
                check(pickle.loads(pickle.dumps(words, proto)))
        check(eval(repr(words)))
        update_test = Counter()
        update_test.update(words)
        check(update_test)
        check(Counter(words))

    def test_copy_subclass(self):
        klasse MyCounter(Counter):
            pass
        c = MyCounter('slartibartfast')
        d = c.copy()
        self.assertEqual(d, c)
        self.assertEqual(len(d), len(c))
        self.assertEqual(type(d), type(c))

    def test_conversions(self):
        # Convert to: set, list, dict
        s = 'she sells sea shells by the sea shore'
        self.assertEqual(sorted(Counter(s).elements()), sorted(s))
        self.assertEqual(sorted(Counter(s)), sorted(set(s)))
        self.assertEqual(dict(Counter(s)), dict(Counter(s).items()))
        self.assertEqual(set(Counter(s)), set(s))

    def test_invariant_for_the_in_operator(self):
        c = Counter(a=10, b=-2, c=0)
        fuer elem in c:
            self.assertWahr(elem in c)
            self.assertIn(elem, c)

    def test_multiset_operations(self):
        # Verify that adding a zero counter will strip zeros und negatives
        c = Counter(a=10, b=-2, c=0) + Counter()
        self.assertEqual(dict(c), dict(a=10))

        elements = 'abcd'
        fuer i in range(1000):
            # test random pairs of multisets
            p = Counter(dict((elem, randrange(-2,4)) fuer elem in elements))
            p.update(e=1, f=-1, g=0)
            q = Counter(dict((elem, randrange(-2,4)) fuer elem in elements))
            q.update(h=1, i=-1, j=0)
            fuer counterop, numberop in [
                (Counter.__add__, lambda x, y: max(0, x+y)),
                (Counter.__sub__, lambda x, y: max(0, x-y)),
                (Counter.__or__, lambda x, y: max(0,x,y)),
                (Counter.__and__, lambda x, y: max(0, min(x,y))),
            ]:
                result = counterop(p, q)
                fuer x in elements:
                    self.assertEqual(numberop(p[x], q[x]), result[x],
                                     (counterop, x, p, q))
                # verify that results exclude non-positive counts
                self.assertWahr(x>0 fuer x in result.values())

        elements = 'abcdef'
        fuer i in range(100):
            # verify that random multisets mit no repeats are exactly like sets
            p = Counter(dict((elem, randrange(0, 2)) fuer elem in elements))
            q = Counter(dict((elem, randrange(0, 2)) fuer elem in elements))
            fuer counterop, setop in [
                (Counter.__sub__, set.__sub__),
                (Counter.__or__, set.__or__),
                (Counter.__and__, set.__and__),
            ]:
                counter_result = counterop(p, q)
                set_result = setop(set(p.elements()), set(q.elements()))
                self.assertEqual(counter_result, dict.fromkeys(set_result, 1))

    def test_inplace_operations(self):
        elements = 'abcd'
        fuer i in range(1000):
            # test random pairs of multisets
            p = Counter(dict((elem, randrange(-2,4)) fuer elem in elements))
            p.update(e=1, f=-1, g=0)
            q = Counter(dict((elem, randrange(-2,4)) fuer elem in elements))
            q.update(h=1, i=-1, j=0)
            fuer inplace_op, regular_op in [
                (Counter.__iadd__, Counter.__add__),
                (Counter.__isub__, Counter.__sub__),
                (Counter.__ior__, Counter.__or__),
                (Counter.__iand__, Counter.__and__),
            ]:
                c = p.copy()
                c_id = id(c)
                regular_result = regular_op(c, q)
                inplace_result = inplace_op(c, q)
                self.assertEqual(inplace_result, regular_result)
                self.assertEqual(id(inplace_result), c_id)

    def test_subtract(self):
        c = Counter(a=-5, b=0, c=5, d=10, e=15,g=40)
        c.subtract(a=1, b=2, c=-3, d=10, e=20, f=30, h=-50)
        self.assertEqual(c, Counter(a=-6, b=-2, c=8, d=0, e=-5, f=-30, g=40, h=50))
        c = Counter(a=-5, b=0, c=5, d=10, e=15,g=40)
        c.subtract(Counter(a=1, b=2, c=-3, d=10, e=20, f=30, h=-50))
        self.assertEqual(c, Counter(a=-6, b=-2, c=8, d=0, e=-5, f=-30, g=40, h=50))
        c = Counter('aaabbcd')
        c.subtract('aaaabbcce')
        self.assertEqual(c, Counter(a=-1, b=0, c=-1, d=1, e=-1))

        c = Counter()
        c.subtract(self=42)
        self.assertEqual(list(c.items()), [('self', -42)])
        c = Counter()
        c.subtract(iterable=42)
        self.assertEqual(list(c.items()), [('iterable', -42)])
        self.assertRaises(TypeError, Counter().subtract, 42)
        self.assertRaises(TypeError, Counter().subtract, {}, {})
        self.assertRaises(TypeError, Counter.subtract)

    def test_unary(self):
        c = Counter(a=-5, b=0, c=5, d=10, e=15,g=40)
        self.assertEqual(dict(+c), dict(c=5, d=10, e=15, g=40))
        self.assertEqual(dict(-c), dict(a=5))

    def test_repr_nonsortable(self):
        c = Counter(a=2, b=Nichts)
        r = repr(c)
        self.assertIn("'a': 2", r)
        self.assertIn("'b': Nichts", r)

    def test_helper_function(self):
        # two paths, one fuer real dicts und one fuer other mappings
        elems = list('abracadabra')

        d = dict()
        _count_elements(d, elems)
        self.assertEqual(d, {'a': 5, 'r': 2, 'b': 2, 'c': 1, 'd': 1})

        m = OrderedDict()
        _count_elements(m, elems)
        self.assertEqual(m,
             OrderedDict([('a', 5), ('b', 2), ('r', 2), ('c', 1), ('d', 1)]))

        # test fidelity to the pure python version
        c = CounterSubclassWithSetItem('abracadabra')
        self.assertWahr(c.called)
        self.assertEqual(dict(c), {'a': 5, 'b': 2, 'c': 1, 'd': 1, 'r':2 })
        c = CounterSubclassWithGet('abracadabra')
        self.assertWahr(c.called)
        self.assertEqual(dict(c), {'a': 5, 'b': 2, 'c': 1, 'd': 1, 'r':2 })

    def test_multiset_operations_equivalent_to_set_operations(self):
        # When the multiplicities are all zero oder one, multiset operations
        # are guaranteed to be equivalent to the corresponding operations
        # fuer regular sets.
        s = list(product(('a', 'b', 'c'), range(2)))
        powerset = chain.from_iterable(combinations(s, r) fuer r in range(len(s)+1))
        counters = [Counter(dict(groups)) fuer groups in powerset]
        fuer cp, cq in product(counters, repeat=2):
            sp = set(cp.elements())
            sq = set(cq.elements())
            self.assertEqual(set(cp + cq), sp | sq)
            self.assertEqual(set(cp - cq), sp - sq)
            self.assertEqual(set(cp | cq), sp | sq)
            self.assertEqual(set(cp & cq), sp & sq)
            self.assertEqual(cp == cq, sp == sq)
            self.assertEqual(cp != cq, sp != sq)
            self.assertEqual(cp <= cq, sp <= sq)
            self.assertEqual(cp >= cq, sp >= sq)
            self.assertEqual(cp < cq, sp < sq)
            self.assertEqual(cp > cq, sp > sq)

    def test_eq(self):
        self.assertEqual(Counter(a=3, b=2, c=0), Counter('ababa'))
        self.assertNotEqual(Counter(a=3, b=2), Counter('babab'))

    def test_le(self):
        self.assertWahr(Counter(a=3, b=2, c=0) <= Counter('ababa'))
        self.assertFalsch(Counter(a=3, b=2) <= Counter('babab'))

    def test_lt(self):
        self.assertWahr(Counter(a=3, b=1, c=0) < Counter('ababa'))
        self.assertFalsch(Counter(a=3, b=2, c=0) < Counter('ababa'))

    def test_ge(self):
        self.assertWahr(Counter(a=2, b=1, c=0) >= Counter('aab'))
        self.assertFalsch(Counter(a=3, b=2, c=0) >= Counter('aabd'))

    def test_gt(self):
        self.assertWahr(Counter(a=3, b=2, c=0) > Counter('aab'))
        self.assertFalsch(Counter(a=2, b=1, c=0) > Counter('aab'))


def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite(collections))
    gib tests


wenn __name__ == "__main__":
    unittest.main()
