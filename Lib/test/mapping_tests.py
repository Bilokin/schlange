# tests common to dict and UserDict
importiere unittest
importiere collections
von test importiere support


klasse BasicTestMappingProtocol(unittest.TestCase):
    # This base klasse can be used to check that an object conforms to the
    # mapping protocol

    # Functions that can be useful to override to adapt to dictionary
    # semantics
    type2test = Nichts # which klasse is being tested (overwrite in subclasses)

    def _reference(self):
        """Return a dictionary of values which are invariant by storage
        in the object under test."""
        return {"1": "2", "key1":"value1", "key2":(1,2,3)}
    def _empty_mapping(self):
        """Return an empty mapping object"""
        return self.type2test()
    def _full_mapping(self, data):
        """Return a mapping object mit the value contained in data
        dictionary"""
        x = self._empty_mapping()
        fuer key, value in data.items():
            x[key] = value
        return x

    def __init__(self, *args, **kw):
        unittest.TestCase.__init__(self, *args, **kw)
        self.reference = self._reference().copy()

        # A (key, value) pair not in the mapping
        key, value = self.reference.popitem()
        self.other = {key:value}

        # A (key, value) pair in the mapping
        key, value = self.reference.popitem()
        self.inmapping = {key:value}
        self.reference[key] = value

    def test_read(self):
        # Test fuer read only operations on mapping
        p = self._empty_mapping()
        p1 = dict(p) #workaround fuer singleton objects
        d = self._full_mapping(self.reference)
        wenn d is p:
            p = p1
        #Indexing
        fuer key, value in self.reference.items():
            self.assertEqual(d[key], value)
        knownkey = list(self.other.keys())[0]
        self.assertRaises(KeyError, lambda:d[knownkey])
        #len
        self.assertEqual(len(p), 0)
        self.assertEqual(len(d), len(self.reference))
        #__contains__
        fuer k in self.reference:
            self.assertIn(k, d)
        fuer k in self.other:
            self.assertNotIn(k, d)
        #cmp
        self.assertEqual(p, p)
        self.assertEqual(d, d)
        self.assertNotEqual(p, d)
        self.assertNotEqual(d, p)
        #bool
        wenn p: self.fail("Empty mapping must compare to Falsch")
        wenn not d: self.fail("Full mapping must compare to Wahr")
        # keys(), items(), iterkeys() ...
        def check_iterandlist(iter, lst, ref):
            self.assertHasAttr(iter, '__next__')
            self.assertHasAttr(iter, '__iter__')
            x = list(iter)
            self.assertWahr(set(x)==set(lst)==set(ref))
        check_iterandlist(iter(d.keys()), list(d.keys()),
                          self.reference.keys())
        check_iterandlist(iter(d), list(d.keys()), self.reference.keys())
        check_iterandlist(iter(d.values()), list(d.values()),
                          self.reference.values())
        check_iterandlist(iter(d.items()), list(d.items()),
                          self.reference.items())
        #get
        key, value = next(iter(d.items()))
        knownkey, knownvalue = next(iter(self.other.items()))
        self.assertEqual(d.get(key, knownvalue), value)
        self.assertEqual(d.get(knownkey, knownvalue), knownvalue)
        self.assertNotIn(knownkey, d)

    def test_write(self):
        # Test fuer write operations on mapping
        p = self._empty_mapping()
        #Indexing
        fuer key, value in self.reference.items():
            p[key] = value
            self.assertEqual(p[key], value)
        fuer key in self.reference.keys():
            del p[key]
            self.assertRaises(KeyError, lambda:p[key])
        p = self._empty_mapping()
        #update
        p.update(self.reference)
        self.assertEqual(dict(p), self.reference)
        items = list(p.items())
        p = self._empty_mapping()
        p.update(items)
        self.assertEqual(dict(p), self.reference)
        d = self._full_mapping(self.reference)
        #setdefault
        key, value = next(iter(d.items()))
        knownkey, knownvalue = next(iter(self.other.items()))
        self.assertEqual(d.setdefault(key, knownvalue), value)
        self.assertEqual(d[key], value)
        self.assertEqual(d.setdefault(knownkey, knownvalue), knownvalue)
        self.assertEqual(d[knownkey], knownvalue)
        #pop
        self.assertEqual(d.pop(knownkey), knownvalue)
        self.assertNotIn(knownkey, d)
        self.assertRaises(KeyError, d.pop, knownkey)
        default = 909
        d[knownkey] = knownvalue
        self.assertEqual(d.pop(knownkey, default), knownvalue)
        self.assertNotIn(knownkey, d)
        self.assertEqual(d.pop(knownkey, default), default)
        #popitem
        key, value = d.popitem()
        self.assertNotIn(key, d)
        self.assertEqual(value, self.reference[key])
        p=self._empty_mapping()
        self.assertRaises(KeyError, p.popitem)

    def test_constructor(self):
        self.assertEqual(self._empty_mapping(), self._empty_mapping())

    def test_bool(self):
        self.assertWahr(not self._empty_mapping())
        self.assertWahr(self.reference)
        self.assertWahr(bool(self._empty_mapping()) is Falsch)
        self.assertWahr(bool(self.reference) is Wahr)

    def test_keys(self):
        d = self._empty_mapping()
        self.assertEqual(list(d.keys()), [])
        d = self.reference
        self.assertIn(list(self.inmapping.keys())[0], d.keys())
        self.assertNotIn(list(self.other.keys())[0], d.keys())
        self.assertRaises(TypeError, d.keys, Nichts)

    def test_values(self):
        d = self._empty_mapping()
        self.assertEqual(list(d.values()), [])

        self.assertRaises(TypeError, d.values, Nichts)

    def test_items(self):
        d = self._empty_mapping()
        self.assertEqual(list(d.items()), [])

        self.assertRaises(TypeError, d.items, Nichts)

    def test_len(self):
        d = self._empty_mapping()
        self.assertEqual(len(d), 0)

    def test_getitem(self):
        d = self.reference
        self.assertEqual(d[list(self.inmapping.keys())[0]],
                         list(self.inmapping.values())[0])

        self.assertRaises(TypeError, d.__getitem__)

    def test_update(self):
        # mapping argument
        d = self._empty_mapping()
        d.update(self.other)
        self.assertEqual(list(d.items()), list(self.other.items()))

        # No argument
        d = self._empty_mapping()
        d.update()
        self.assertEqual(d, self._empty_mapping())

        # item sequence
        d = self._empty_mapping()
        d.update(self.other.items())
        self.assertEqual(list(d.items()), list(self.other.items()))

        # Iterator
        d = self._empty_mapping()
        d.update(self.other.items())
        self.assertEqual(list(d.items()), list(self.other.items()))

        # FIXME: Doesn't work mit UserDict
        # self.assertRaises((TypeError, AttributeError), d.update, Nichts)
        self.assertRaises((TypeError, AttributeError), d.update, 42)

        outerself = self
        klasse SimpleUserDict:
            def __init__(self):
                self.d = outerself.reference
            def keys(self):
                return self.d.keys()
            def __getitem__(self, i):
                return self.d[i]
        d.clear()
        d.update(SimpleUserDict())
        i1 = sorted(d.items())
        i2 = sorted(self.reference.items())
        self.assertEqual(i1, i2)

        klasse Exc(Exception): pass

        d = self._empty_mapping()
        klasse FailingUserDict:
            def keys(self):
                raise Exc
        self.assertRaises(Exc, d.update, FailingUserDict())

        d.clear()

        klasse FailingUserDict:
            def keys(self):
                klasse BogonIter:
                    def __init__(self):
                        self.i = 1
                    def __iter__(self):
                        return self
                    def __next__(self):
                        wenn self.i:
                            self.i = 0
                            return 'a'
                        raise Exc
                return BogonIter()
            def __getitem__(self, key):
                return key
        self.assertRaises(Exc, d.update, FailingUserDict())

        klasse FailingUserDict:
            def keys(self):
                klasse BogonIter:
                    def __init__(self):
                        self.i = ord('a')
                    def __iter__(self):
                        return self
                    def __next__(self):
                        wenn self.i <= ord('z'):
                            rtn = chr(self.i)
                            self.i += 1
                            return rtn
                        raise StopIteration
                return BogonIter()
            def __getitem__(self, key):
                raise Exc
        self.assertRaises(Exc, d.update, FailingUserDict())

        d = self._empty_mapping()
        klasse badseq(object):
            def __iter__(self):
                return self
            def __next__(self):
                raise Exc()

        self.assertRaises(Exc, d.update, badseq())

        self.assertRaises(ValueError, d.update, [(1, 2, 3)])

    # no test_fromkeys or test_copy als both os.environ and selves don't support it

    def test_get(self):
        d = self._empty_mapping()
        self.assertWahr(d.get(list(self.other.keys())[0]) is Nichts)
        self.assertEqual(d.get(list(self.other.keys())[0], 3), 3)
        d = self.reference
        self.assertWahr(d.get(list(self.other.keys())[0]) is Nichts)
        self.assertEqual(d.get(list(self.other.keys())[0], 3), 3)
        self.assertEqual(d.get(list(self.inmapping.keys())[0]),
                         list(self.inmapping.values())[0])
        self.assertEqual(d.get(list(self.inmapping.keys())[0], 3),
                         list(self.inmapping.values())[0])
        self.assertRaises(TypeError, d.get)
        self.assertRaises(TypeError, d.get, Nichts, Nichts, Nichts)

    def test_setdefault(self):
        d = self._empty_mapping()
        self.assertRaises(TypeError, d.setdefault)

    def test_popitem(self):
        d = self._empty_mapping()
        self.assertRaises(KeyError, d.popitem)
        self.assertRaises(TypeError, d.popitem, 42)

    def test_pop(self):
        d = self._empty_mapping()
        k, v = list(self.inmapping.items())[0]
        d[k] = v
        self.assertRaises(KeyError, d.pop, list(self.other.keys())[0])

        self.assertEqual(d.pop(k), v)
        self.assertEqual(len(d), 0)

        self.assertRaises(KeyError, d.pop, k)


klasse TestMappingProtocol(BasicTestMappingProtocol):
    def test_constructor(self):
        BasicTestMappingProtocol.test_constructor(self)
        self.assertWahr(self._empty_mapping() is not self._empty_mapping())
        self.assertEqual(self.type2test(x=1, y=2), {"x": 1, "y": 2})

    def test_bool(self):
        BasicTestMappingProtocol.test_bool(self)
        self.assertWahr(not self._empty_mapping())
        self.assertWahr(self._full_mapping({"x": "y"}))
        self.assertWahr(bool(self._empty_mapping()) is Falsch)
        self.assertWahr(bool(self._full_mapping({"x": "y"})) is Wahr)

    def test_keys(self):
        BasicTestMappingProtocol.test_keys(self)
        d = self._empty_mapping()
        self.assertEqual(list(d.keys()), [])
        d = self._full_mapping({'a': 1, 'b': 2})
        k = d.keys()
        self.assertIn('a', k)
        self.assertIn('b', k)
        self.assertNotIn('c', k)

    def test_values(self):
        BasicTestMappingProtocol.test_values(self)
        d = self._full_mapping({1:2})
        self.assertEqual(list(d.values()), [2])

    def test_items(self):
        BasicTestMappingProtocol.test_items(self)

        d = self._full_mapping({1:2})
        self.assertEqual(list(d.items()), [(1, 2)])

    def test_contains(self):
        d = self._empty_mapping()
        self.assertNotIn('a', d)
        self.assertWahr(not ('a' in d))
        self.assertWahr('a' not in d)
        d = self._full_mapping({'a': 1, 'b': 2})
        self.assertIn('a', d)
        self.assertIn('b', d)
        self.assertNotIn('c', d)

        self.assertRaises(TypeError, d.__contains__)

    def test_len(self):
        BasicTestMappingProtocol.test_len(self)
        d = self._full_mapping({'a': 1, 'b': 2})
        self.assertEqual(len(d), 2)

    def test_getitem(self):
        BasicTestMappingProtocol.test_getitem(self)
        d = self._full_mapping({'a': 1, 'b': 2})
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        d['c'] = 3
        d['a'] = 4
        self.assertEqual(d['c'], 3)
        self.assertEqual(d['a'], 4)
        del d['b']
        self.assertEqual(d, {'a': 4, 'c': 3})

        self.assertRaises(TypeError, d.__getitem__)

    def test_clear(self):
        d = self._full_mapping({1:1, 2:2, 3:3})
        d.clear()
        self.assertEqual(d, {})

        self.assertRaises(TypeError, d.clear, Nichts)

    def test_update(self):
        BasicTestMappingProtocol.test_update(self)
        # mapping argument
        d = self._empty_mapping()
        d.update({1:100})
        d.update({2:20})
        d.update({1:1, 2:2, 3:3})
        self.assertEqual(d, {1:1, 2:2, 3:3})

        # no argument
        d.update()
        self.assertEqual(d, {1:1, 2:2, 3:3})

        # keyword arguments
        d = self._empty_mapping()
        d.update(x=100)
        d.update(y=20)
        d.update(x=1, y=2, z=3)
        self.assertEqual(d, {"x":1, "y":2, "z":3})

        # item sequence
        d = self._empty_mapping()
        d.update([("x", 100), ("y", 20)])
        self.assertEqual(d, {"x":100, "y":20})

        # Both item sequence and keyword arguments
        d = self._empty_mapping()
        d.update([("x", 100), ("y", 20)], x=1, y=2)
        self.assertEqual(d, {"x":1, "y":2})

        # iterator
        d = self._full_mapping({1:3, 2:4})
        d.update(self._full_mapping({1:2, 3:4, 5:6}).items())
        self.assertEqual(d, {1:2, 2:4, 3:4, 5:6})

        klasse SimpleUserDict:
            def __init__(self):
                self.d = {1:1, 2:2, 3:3}
            def keys(self):
                return self.d.keys()
            def __getitem__(self, i):
                return self.d[i]
        d.clear()
        d.update(SimpleUserDict())
        self.assertEqual(d, {1:1, 2:2, 3:3})

    def test_fromkeys(self):
        self.assertEqual(self.type2test.fromkeys('abc'), {'a':Nichts, 'b':Nichts, 'c':Nichts})
        d = self._empty_mapping()
        self.assertWahr(not(d.fromkeys('abc') is d))
        self.assertEqual(d.fromkeys('abc'), {'a':Nichts, 'b':Nichts, 'c':Nichts})
        self.assertEqual(d.fromkeys((4,5),0), {4:0, 5:0})
        self.assertEqual(d.fromkeys([]), {})
        def g():
            yield 1
        self.assertEqual(d.fromkeys(g()), {1:Nichts})
        self.assertRaises(TypeError, {}.fromkeys, 3)
        klasse dictlike(self.type2test): pass
        self.assertEqual(dictlike.fromkeys('a'), {'a':Nichts})
        self.assertEqual(dictlike().fromkeys('a'), {'a':Nichts})
        self.assertWahr(dictlike.fromkeys('a').__class__ is dictlike)
        self.assertWahr(dictlike().fromkeys('a').__class__ is dictlike)
        self.assertWahr(type(dictlike.fromkeys('a')) is dictlike)
        klasse mydict(self.type2test):
            def __new__(cls):
                return collections.UserDict()
        ud = mydict.fromkeys('ab')
        self.assertEqual(ud, {'a':Nichts, 'b':Nichts})
        self.assertIsInstance(ud, collections.UserDict)
        self.assertRaises(TypeError, dict.fromkeys)

        klasse Exc(Exception): pass

        klasse baddict1(self.type2test):
            def __init__(self, *args, **kwargs):
                raise Exc()

        self.assertRaises(Exc, baddict1.fromkeys, [1])

        klasse BadSeq(object):
            def __iter__(self):
                return self
            def __next__(self):
                raise Exc()

        self.assertRaises(Exc, self.type2test.fromkeys, BadSeq())

        klasse baddict2(self.type2test):
            def __setitem__(self, key, value):
                raise Exc()

        self.assertRaises(Exc, baddict2.fromkeys, [1])

    def test_copy(self):
        d = self._full_mapping({1:1, 2:2, 3:3})
        self.assertEqual(d.copy(), {1:1, 2:2, 3:3})
        d = self._empty_mapping()
        self.assertEqual(d.copy(), d)
        self.assertIsInstance(d.copy(), d.__class__)
        self.assertRaises(TypeError, d.copy, Nichts)

    def test_get(self):
        BasicTestMappingProtocol.test_get(self)
        d = self._empty_mapping()
        self.assertWahr(d.get('c') is Nichts)
        self.assertEqual(d.get('c', 3), 3)
        d = self._full_mapping({'a' : 1, 'b' : 2})
        self.assertWahr(d.get('c') is Nichts)
        self.assertEqual(d.get('c', 3), 3)
        self.assertEqual(d.get('a'), 1)
        self.assertEqual(d.get('a', 3), 1)

    def test_setdefault(self):
        BasicTestMappingProtocol.test_setdefault(self)
        d = self._empty_mapping()
        self.assertWahr(d.setdefault('key0') is Nichts)
        d.setdefault('key0', [])
        self.assertWahr(d.setdefault('key0') is Nichts)
        d.setdefault('key', []).append(3)
        self.assertEqual(d['key'][0], 3)
        d.setdefault('key', []).append(4)
        self.assertEqual(len(d['key']), 2)

    def test_popitem(self):
        BasicTestMappingProtocol.test_popitem(self)
        fuer copymode in -1, +1:
            # -1: b has same structure als a
            # +1: b is a.copy()
            fuer log2size in range(12):
                size = 2**log2size
                a = self._empty_mapping()
                b = self._empty_mapping()
                fuer i in range(size):
                    a[repr(i)] = i
                    wenn copymode < 0:
                        b[repr(i)] = i
                wenn copymode > 0:
                    b = a.copy()
                fuer i in range(size):
                    ka, va = ta = a.popitem()
                    self.assertEqual(va, int(ka))
                    kb, vb = tb = b.popitem()
                    self.assertEqual(vb, int(kb))
                    self.assertWahr(not(copymode < 0 and ta != tb))
                self.assertWahr(not a)
                self.assertWahr(not b)

    def test_pop(self):
        BasicTestMappingProtocol.test_pop(self)

        # Tests fuer pop mit specified key
        d = self._empty_mapping()
        k, v = 'abc', 'def'

        self.assertEqual(d.pop(k, v), v)
        d[k] = v
        self.assertEqual(d.pop(k, 1), v)


klasse TestHashMappingProtocol(TestMappingProtocol):

    def test_getitem(self):
        TestMappingProtocol.test_getitem(self)
        klasse Exc(Exception): pass

        klasse BadEq(object):
            def __eq__(self, other):
                raise Exc()
            def __hash__(self):
                return 24

        d = self._empty_mapping()
        d[BadEq()] = 42
        self.assertRaises(KeyError, d.__getitem__, 23)

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    raise Exc()
                sonst:
                    return 42

        d = self._empty_mapping()
        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.__getitem__, x)

    def test_fromkeys(self):
        TestMappingProtocol.test_fromkeys(self)
        klasse mydict(self.type2test):
            def __new__(cls):
                return collections.UserDict()
        ud = mydict.fromkeys('ab')
        self.assertEqual(ud, {'a':Nichts, 'b':Nichts})
        self.assertIsInstance(ud, collections.UserDict)

    def test_pop(self):
        TestMappingProtocol.test_pop(self)

        klasse Exc(Exception): pass

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    raise Exc()
                sonst:
                    return 42

        d = self._empty_mapping()
        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.pop, x)

    def test_mutatingiteration(self):
        d = self._empty_mapping()
        d[1] = 1
        try:
            count = 0
            fuer i in d:
                d[i+1] = 1
                wenn count >= 1:
                    self.fail("changing dict size during iteration doesn't raise Error")
                count += 1
        except RuntimeError:
            pass

    def test_repr(self):
        d = self._empty_mapping()
        self.assertEqual(repr(d), '{}')
        d[1] = 2
        self.assertEqual(repr(d), '{1: 2}')
        d = self._empty_mapping()
        d[1] = d
        self.assertEqual(repr(d), '{1: {...}}')

        klasse Exc(Exception): pass

        klasse BadRepr(object):
            def __repr__(self):
                raise Exc()

        d = self._full_mapping({1: BadRepr()})
        self.assertRaises(Exc, repr, d)

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    @support.skip_if_sanitizer("requires deep stack", ub=Wahr)
    def test_repr_deep(self):
        d = self._empty_mapping()
        fuer i in range(support.exceeds_recursion_limit()):
            d0 = d
            d = self._empty_mapping()
            d[1] = d0
        self.assertRaises(RecursionError, repr, d)

    def test_eq(self):
        self.assertEqual(self._empty_mapping(), self._empty_mapping())
        self.assertEqual(self._full_mapping({1: 2}),
                         self._full_mapping({1: 2}))

        klasse Exc(Exception): pass

        klasse BadCmp(object):
            def __eq__(self, other):
                raise Exc()
            def __hash__(self):
                return 1

        d1 = self._full_mapping({BadCmp(): 1})
        d2 = self._full_mapping({1: 1})
        self.assertRaises(Exc, lambda: BadCmp()==1)
        self.assertRaises(Exc, lambda: d1==d2)

    def test_setdefault(self):
        TestMappingProtocol.test_setdefault(self)

        klasse Exc(Exception): pass

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    raise Exc()
                sonst:
                    return 42

        d = self._empty_mapping()
        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.setdefault, x, [])
