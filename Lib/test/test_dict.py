importiere collections
importiere collections.abc
importiere gc
importiere pickle
importiere random
importiere re
importiere string
importiere sys
importiere unittest
importiere weakref
von test importiere support
von test.support importiere import_helper


klasse DictTest(unittest.TestCase):

    def test_invalid_keyword_arguments(self):
        klasse Custom(dict):
            pass
        fuer invalid in {1 : 2}, Custom({1 : 2}):
            mit self.assertRaises(TypeError):
                dict(**invalid)
            mit self.assertRaises(TypeError):
                {}.update(**invalid)

    def test_constructor(self):
        # calling built-in types without argument must gib empty
        self.assertEqual(dict(), {})
        self.assertIsNot(dict(), {})

    def test_literal_constructor(self):
        # check literal constructor fuer different sized dicts
        # (to exercise the BUILD_MAP oparg).
        fuer n in (0, 1, 6, 256, 400):
            items = [(''.join(random.sample(string.ascii_letters, 8)), i)
                     fuer i in range(n)]
            random.shuffle(items)
            formatted_items = ('{!r}: {:d}'.format(k, v) fuer k, v in items)
            dictliteral = '{' + ', '.join(formatted_items) + '}'
            self.assertEqual(eval(dictliteral), dict(items))

    def test_merge_operator(self):

        a = {0: 0, 1: 1, 2: 1}
        b = {1: 1, 2: 2, 3: 3}

        c = a.copy()
        c |= b

        self.assertEqual(a | b, {0: 0, 1: 1, 2: 2, 3: 3})
        self.assertEqual(c, {0: 0, 1: 1, 2: 2, 3: 3})

        c = b.copy()
        c |= a

        self.assertEqual(b | a, {1: 1, 2: 1, 3: 3, 0: 0})
        self.assertEqual(c, {1: 1, 2: 1, 3: 3, 0: 0})

        c = a.copy()
        c |= [(1, 1), (2, 2), (3, 3)]

        self.assertEqual(c, {0: 0, 1: 1, 2: 2, 3: 3})

        self.assertIs(a.__or__(Nichts), NotImplemented)
        self.assertIs(a.__or__(()), NotImplemented)
        self.assertIs(a.__or__("BAD"), NotImplemented)
        self.assertIs(a.__or__(""), NotImplemented)

        self.assertRaises(TypeError, a.__ior__, Nichts)
        self.assertEqual(a.__ior__(()), {0: 0, 1: 1, 2: 1})
        self.assertRaises(ValueError, a.__ior__, "BAD")
        self.assertEqual(a.__ior__(""), {0: 0, 1: 1, 2: 1})

    def test_bool(self):
        self.assertIs(nicht {}, Wahr)
        self.assertWahr({1: 2})
        self.assertIs(bool({}), Falsch)
        self.assertIs(bool({1: 2}), Wahr)

    def test_keys(self):
        d = {}
        self.assertEqual(set(d.keys()), set())
        d = {'a': 1, 'b': 2}
        k = d.keys()
        self.assertEqual(set(k), {'a', 'b'})
        self.assertIn('a', k)
        self.assertIn('b', k)
        self.assertIn('a', d)
        self.assertIn('b', d)
        self.assertRaises(TypeError, d.keys, Nichts)
        self.assertEqual(repr(dict(a=1).keys()), "dict_keys(['a'])")

    def test_values(self):
        d = {}
        self.assertEqual(set(d.values()), set())
        d = {1:2}
        self.assertEqual(set(d.values()), {2})
        self.assertRaises(TypeError, d.values, Nichts)
        self.assertEqual(repr(dict(a=1).values()), "dict_values([1])")

    def test_items(self):
        d = {}
        self.assertEqual(set(d.items()), set())

        d = {1:2}
        self.assertEqual(set(d.items()), {(1, 2)})
        self.assertRaises(TypeError, d.items, Nichts)
        self.assertEqual(repr(dict(a=1).items()), "dict_items([('a', 1)])")

    def test_views_mapping(self):
        mappingproxy = type(type.__dict__)
        klasse Dict(dict):
            pass
        fuer cls in [dict, Dict]:
            d = cls()
            m1 = d.keys().mapping
            m2 = d.values().mapping
            m3 = d.items().mapping

            fuer m in [m1, m2, m3]:
                self.assertIsInstance(m, mappingproxy)
                self.assertEqual(m, d)

            d["foo"] = "bar"

            fuer m in [m1, m2, m3]:
                self.assertIsInstance(m, mappingproxy)
                self.assertEqual(m, d)

    def test_contains(self):
        d = {}
        self.assertNotIn('a', d)
        self.assertFalsch('a' in d)
        self.assertWahr('a' nicht in d)
        d = {'a': 1, 'b': 2}
        self.assertIn('a', d)
        self.assertIn('b', d)
        self.assertNotIn('c', d)

        self.assertRaises(TypeError, d.__contains__)

    def test_len(self):
        d = {}
        self.assertEqual(len(d), 0)
        d = {'a': 1, 'b': 2}
        self.assertEqual(len(d), 2)

    def test_getitem(self):
        d = {'a': 1, 'b': 2}
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        d['c'] = 3
        d['a'] = 4
        self.assertEqual(d['c'], 3)
        self.assertEqual(d['a'], 4)
        del d['b']
        self.assertEqual(d, {'a': 4, 'c': 3})

        self.assertRaises(TypeError, d.__getitem__)

        klasse BadEq(object):
            def __eq__(self, other):
                wirf Exc()
            def __hash__(self):
                gib 24

        d = {}
        d[BadEq()] = 42
        self.assertRaises(KeyError, d.__getitem__, 23)

        klasse Exc(Exception): pass

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    wirf Exc()
                sonst:
                    gib 42

        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.__getitem__, x)

    def test_clear(self):
        d = {1:1, 2:2, 3:3}
        d.clear()
        self.assertEqual(d, {})

        self.assertRaises(TypeError, d.clear, Nichts)

    def test_update(self):
        d = {}
        d.update({1:100})
        d.update({2:20})
        d.update({1:1, 2:2, 3:3})
        self.assertEqual(d, {1:1, 2:2, 3:3})

        d.update()
        self.assertEqual(d, {1:1, 2:2, 3:3})

        self.assertRaises((TypeError, AttributeError), d.update, Nichts)

        klasse SimpleUserDict:
            def __init__(self):
                self.d = {1:1, 2:2, 3:3}
            def keys(self):
                gib self.d.keys()
            def __getitem__(self, i):
                gib self.d[i]
        d.clear()
        d.update(SimpleUserDict())
        self.assertEqual(d, {1:1, 2:2, 3:3})

        klasse Exc(Exception): pass

        d.clear()
        klasse FailingUserDict:
            def keys(self):
                wirf Exc
        self.assertRaises(Exc, d.update, FailingUserDict())

        klasse FailingUserDict:
            def keys(self):
                klasse BogonIter:
                    def __init__(self):
                        self.i = 1
                    def __iter__(self):
                        gib self
                    def __next__(self):
                        wenn self.i:
                            self.i = 0
                            gib 'a'
                        wirf Exc
                gib BogonIter()
            def __getitem__(self, key):
                gib key
        self.assertRaises(Exc, d.update, FailingUserDict())

        klasse FailingUserDict:
            def keys(self):
                klasse BogonIter:
                    def __init__(self):
                        self.i = ord('a')
                    def __iter__(self):
                        gib self
                    def __next__(self):
                        wenn self.i <= ord('z'):
                            rtn = chr(self.i)
                            self.i += 1
                            gib rtn
                        wirf StopIteration
                gib BogonIter()
            def __getitem__(self, key):
                wirf Exc
        self.assertRaises(Exc, d.update, FailingUserDict())

        klasse badseq(object):
            def __iter__(self):
                gib self
            def __next__(self):
                wirf Exc()

        self.assertRaises(Exc, {}.update, badseq())

        self.assertRaises(ValueError, {}.update, [(1, 2, 3)])

    def test_update_type_error(self):
        mit self.assertRaises(TypeError) als cm:
            {}.update([object() fuer _ in range(3)])

        self.assertEqual(str(cm.exception), "object is nicht iterable")
        self.assertEqual(
            cm.exception.__notes__,
            ['Cannot convert dictionary update sequence element #0 to a sequence'],
        )

        def badgen():
            liefere "key"
            wirf TypeError("oops")
            liefere "value"

        mit self.assertRaises(TypeError) als cm:
            dict([badgen() fuer _ in range(3)])

        self.assertEqual(str(cm.exception), "oops")
        self.assertEqual(
            cm.exception.__notes__,
            ['Cannot convert dictionary update sequence element #0 to a sequence'],
        )

    def test_update_shared_keys(self):
        klasse MyClass: pass

        # Subclass str to enable us to create an object during the
        # dict.update() call.
        klasse MyStr(str):
            def __hash__(self):
                gib super().__hash__()

            def __eq__(self, other):
                # Create an object that shares the same PyDictKeysObject as
                # obj.__dict__.
                obj2 = MyClass()
                obj2.a = "a"
                obj2.b = "b"
                obj2.c = "c"
                gib super().__eq__(other)

        obj = MyClass()
        obj.a = "a"
        obj.b = "b"

        x = {}
        x[MyStr("a")] = MyStr("a")

        # gh-132617: this previously raised "dict mutated during update" error
        x.update(obj.__dict__)

        self.assertEqual(x, {
            MyStr("a"): "a",
            "b": "b",
        })

    def test_fromkeys(self):
        self.assertEqual(dict.fromkeys('abc'), {'a':Nichts, 'b':Nichts, 'c':Nichts})
        d = {}
        self.assertIsNot(d.fromkeys('abc'), d)
        self.assertEqual(d.fromkeys('abc'), {'a':Nichts, 'b':Nichts, 'c':Nichts})
        self.assertEqual(d.fromkeys((4,5),0), {4:0, 5:0})
        self.assertEqual(d.fromkeys([]), {})
        def g():
            liefere 1
        self.assertEqual(d.fromkeys(g()), {1:Nichts})
        self.assertRaises(TypeError, {}.fromkeys, 3)
        klasse dictlike(dict): pass
        self.assertEqual(dictlike.fromkeys('a'), {'a':Nichts})
        self.assertEqual(dictlike().fromkeys('a'), {'a':Nichts})
        self.assertIsInstance(dictlike.fromkeys('a'), dictlike)
        self.assertIsInstance(dictlike().fromkeys('a'), dictlike)
        klasse mydict(dict):
            def __new__(cls):
                gib collections.UserDict()
        ud = mydict.fromkeys('ab')
        self.assertEqual(ud, {'a':Nichts, 'b':Nichts})
        self.assertIsInstance(ud, collections.UserDict)
        self.assertRaises(TypeError, dict.fromkeys)

        klasse Exc(Exception): pass

        klasse baddict1(dict):
            def __init__(self):
                wirf Exc()

        self.assertRaises(Exc, baddict1.fromkeys, [1])

        klasse BadSeq(object):
            def __iter__(self):
                gib self
            def __next__(self):
                wirf Exc()

        self.assertRaises(Exc, dict.fromkeys, BadSeq())

        klasse baddict2(dict):
            def __setitem__(self, key, value):
                wirf Exc()

        self.assertRaises(Exc, baddict2.fromkeys, [1])

        # test fast path fuer dictionary inputs
        res = dict(zip(range(6), [0]*6))
        d = dict(zip(range(6), range(6)))
        self.assertEqual(dict.fromkeys(d, 0), res)
        # test fast path fuer set inputs
        d = set(range(6))
        self.assertEqual(dict.fromkeys(d, 0), res)
        # test slow path fuer other iterable inputs
        d = list(range(6))
        self.assertEqual(dict.fromkeys(d, 0), res)

        # test fast path when object's constructor returns large non-empty dict
        klasse baddict3(dict):
            def __new__(cls):
                gib d
        d = {i : i fuer i in range(1000)}
        res = d.copy()
        res.update(a=Nichts, b=Nichts, c=Nichts)
        self.assertEqual(baddict3.fromkeys({"a", "b", "c"}), res)

        # test slow path when object is a proper subclass of dict
        klasse baddict4(dict):
            def __init__(self):
                dict.__init__(self, d)
        d = {i : i fuer i in range(1000)}
        res = d.copy()
        res.update(a=Nichts, b=Nichts, c=Nichts)
        self.assertEqual(baddict4.fromkeys({"a", "b", "c"}), res)

    def test_copy(self):
        d = {1: 1, 2: 2, 3: 3}
        self.assertIsNot(d.copy(), d)
        self.assertEqual(d.copy(), d)
        self.assertEqual(d.copy(), {1: 1, 2: 2, 3: 3})

        copy = d.copy()
        d[4] = 4
        self.assertNotEqual(copy, d)

        self.assertEqual({}.copy(), {})
        self.assertRaises(TypeError, d.copy, Nichts)

    def test_copy_fuzz(self):
        fuer dict_size in [10, 100, 1000, 10000, 100000]:
            dict_size = random.randrange(
                dict_size // 2, dict_size + dict_size // 2)
            mit self.subTest(dict_size=dict_size):
                d = {}
                fuer i in range(dict_size):
                    d[i] = i

                d2 = d.copy()
                self.assertIsNot(d2, d)
                self.assertEqual(d, d2)
                d2['key'] = 'value'
                self.assertNotEqual(d, d2)
                self.assertEqual(len(d2), len(d) + 1)

    def test_copy_maintains_tracking(self):
        klasse A:
            pass

        key = A()

        fuer d in ({}, {'a': 1}, {key: 'val'}):
            d2 = d.copy()
            self.assertEqual(gc.is_tracked(d), gc.is_tracked(d2))

    def test_copy_noncompact(self):
        # Dicts don't compact themselves on del/pop operations.
        # Copy will use a slow merging strategy that produces
        # a compacted copy when roughly 33% of dict is a non-used
        # keys-space (to optimize memory footprint).
        # In this test we want to hit the slow/compacting
        # branch of dict.copy() und make sure it works OK.
        d = {k: k fuer k in range(1000)}
        fuer k in range(950):
            del d[k]
        d2 = d.copy()
        self.assertEqual(d2, d)

    def test_get(self):
        d = {}
        self.assertIs(d.get('c'), Nichts)
        self.assertEqual(d.get('c', 3), 3)
        d = {'a': 1, 'b': 2}
        self.assertIs(d.get('c'), Nichts)
        self.assertEqual(d.get('c', 3), 3)
        self.assertEqual(d.get('a'), 1)
        self.assertEqual(d.get('a', 3), 1)
        self.assertRaises(TypeError, d.get)
        self.assertRaises(TypeError, d.get, Nichts, Nichts, Nichts)

    def test_setdefault(self):
        # dict.setdefault()
        d = {}
        self.assertIs(d.setdefault('key0'), Nichts)
        d.setdefault('key0', [])
        self.assertIs(d.setdefault('key0'), Nichts)
        d.setdefault('key', []).append(3)
        self.assertEqual(d['key'][0], 3)
        d.setdefault('key', []).append(4)
        self.assertEqual(len(d['key']), 2)
        self.assertRaises(TypeError, d.setdefault)

        klasse Exc(Exception): pass

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    wirf Exc()
                sonst:
                    gib 42

        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.setdefault, x, [])

    def test_setdefault_atomic(self):
        # Issue #13521: setdefault() calls __hash__ und __eq__ only once.
        klasse Hashed(object):
            def __init__(self):
                self.hash_count = 0
                self.eq_count = 0
            def __hash__(self):
                self.hash_count += 1
                gib 42
            def __eq__(self, other):
                self.eq_count += 1
                gib id(self) == id(other)
        hashed1 = Hashed()
        y = {hashed1: 5}
        hashed2 = Hashed()
        y.setdefault(hashed2, [])
        self.assertEqual(hashed1.hash_count, 1)
        self.assertEqual(hashed2.hash_count, 1)
        self.assertEqual(hashed1.eq_count + hashed2.eq_count, 1)

    def test_setitem_atomic_at_resize(self):
        klasse Hashed(object):
            def __init__(self):
                self.hash_count = 0
                self.eq_count = 0
            def __hash__(self):
                self.hash_count += 1
                gib 42
            def __eq__(self, other):
                self.eq_count += 1
                gib id(self) == id(other)
        hashed1 = Hashed()
        # 5 items
        y = {hashed1: 5, 0: 0, 1: 1, 2: 2, 3: 3}
        hashed2 = Hashed()
        # 6th item forces a resize
        y[hashed2] = []
        self.assertEqual(hashed1.hash_count, 1)
        self.assertEqual(hashed2.hash_count, 1)
        self.assertEqual(hashed1.eq_count + hashed2.eq_count, 1)

    def test_popitem(self):
        # dict.popitem()
        fuer copymode in -1, +1:
            # -1: b has same structure als a
            # +1: b is a.copy()
            fuer log2size in range(12):
                size = 2**log2size
                a = {}
                b = {}
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
                    self.assertFalsch(copymode < 0 und ta != tb)
                self.assertFalsch(a)
                self.assertFalsch(b)

        d = {}
        self.assertRaises(KeyError, d.popitem)

    def test_pop(self):
        # Tests fuer pop mit specified key
        d = {}
        k, v = 'abc', 'def'
        d[k] = v
        self.assertRaises(KeyError, d.pop, 'ghi')

        self.assertEqual(d.pop(k), v)
        self.assertEqual(len(d), 0)

        self.assertRaises(KeyError, d.pop, k)

        self.assertEqual(d.pop(k, v), v)
        d[k] = v
        self.assertEqual(d.pop(k, 1), v)

        self.assertRaises(TypeError, d.pop)

        klasse Exc(Exception): pass

        klasse BadHash(object):
            fail = Falsch
            def __hash__(self):
                wenn self.fail:
                    wirf Exc()
                sonst:
                    gib 42

        x = BadHash()
        d[x] = 42
        x.fail = Wahr
        self.assertRaises(Exc, d.pop, x)

    def test_mutating_iteration(self):
        # changing dict size during iteration
        d = {}
        d[1] = 1
        mit self.assertRaises(RuntimeError):
            fuer i in d:
                d[i+1] = 1

    def test_mutating_iteration_delete(self):
        # change dict content during iteration
        d = {}
        d[0] = 0
        mit self.assertRaises(RuntimeError):
            fuer i in d:
                del d[0]
                d[0] = 0

    def test_mutating_iteration_delete_over_values(self):
        # change dict content during iteration
        d = {}
        d[0] = 0
        mit self.assertRaises(RuntimeError):
            fuer i in d.values():
                del d[0]
                d[0] = 0

    def test_mutating_iteration_delete_over_items(self):
        # change dict content during iteration
        d = {}
        d[0] = 0
        mit self.assertRaises(RuntimeError):
            fuer i in d.items():
                del d[0]
                d[0] = 0

    def test_mutating_lookup(self):
        # changing dict during a lookup (issue #14417)
        klasse NastyKey:
            mutate_dict = Nichts

            def __init__(self, value):
                self.value = value

            def __hash__(self):
                # hash collision!
                gib 1

            def __eq__(self, other):
                wenn NastyKey.mutate_dict:
                    mydict, key = NastyKey.mutate_dict
                    NastyKey.mutate_dict = Nichts
                    del mydict[key]
                gib self.value == other.value

        key1 = NastyKey(1)
        key2 = NastyKey(2)
        d = {key1: 1}
        NastyKey.mutate_dict = (d, key1)
        d[key2] = 2
        self.assertEqual(d, {key2: 2})

    def test_repr(self):
        d = {}
        self.assertEqual(repr(d), '{}')
        d[1] = 2
        self.assertEqual(repr(d), '{1: 2}')
        d = {}
        d[1] = d
        self.assertEqual(repr(d), '{1: {...}}')

        klasse Exc(Exception): pass

        klasse BadRepr(object):
            def __repr__(self):
                wirf Exc()

        d = {1: BadRepr()}
        self.assertRaises(Exc, repr, d)

    @support.skip_wasi_stack_overflow()
    @support.skip_emscripten_stack_overflow()
    def test_repr_deep(self):
        d = {}
        fuer i in range(support.exceeds_recursion_limit()):
            d = {1: d}
        self.assertRaises(RecursionError, repr, d)

    def test_eq(self):
        self.assertEqual({}, {})
        self.assertEqual({1: 2}, {1: 2})

        klasse Exc(Exception): pass

        klasse BadCmp(object):
            def __eq__(self, other):
                wirf Exc()
            def __hash__(self):
                gib 1

        d1 = {BadCmp(): 1}
        d2 = {1: 1}

        mit self.assertRaises(Exc):
            d1 == d2

    def test_keys_contained(self):
        self.helper_keys_contained(lambda x: x.keys())
        self.helper_keys_contained(lambda x: x.items())

    def helper_keys_contained(self, fn):
        # Test rich comparisons against dict key views, which should behave the
        # same als sets.
        empty = fn(dict())
        empty2 = fn(dict())
        smaller = fn({1:1, 2:2})
        larger = fn({1:1, 2:2, 3:3})
        larger2 = fn({1:1, 2:2, 3:3})
        larger3 = fn({4:1, 2:2, 3:3})

        self.assertWahr(smaller <  larger)
        self.assertWahr(smaller <= larger)
        self.assertWahr(larger >  smaller)
        self.assertWahr(larger >= smaller)

        self.assertFalsch(smaller >= larger)
        self.assertFalsch(smaller >  larger)
        self.assertFalsch(larger  <= smaller)
        self.assertFalsch(larger  <  smaller)

        self.assertFalsch(smaller <  larger3)
        self.assertFalsch(smaller <= larger3)
        self.assertFalsch(larger3 >  smaller)
        self.assertFalsch(larger3 >= smaller)

        # Inequality strictness
        self.assertWahr(larger2 >= larger)
        self.assertWahr(larger2 <= larger)
        self.assertFalsch(larger2 > larger)
        self.assertFalsch(larger2 < larger)

        self.assertWahr(larger == larger2)
        self.assertWahr(smaller != larger)

        # There is an optimization on the zero-element case.
        self.assertWahr(empty == empty2)
        self.assertFalsch(empty != empty2)
        self.assertFalsch(empty == smaller)
        self.assertWahr(empty != smaller)

        # With the same size, an elementwise compare happens
        self.assertWahr(larger != larger3)
        self.assertFalsch(larger == larger3)

    def test_errors_in_view_containment_check(self):
        klasse C:
            def __eq__(self, other):
                wirf RuntimeError

        d1 = {1: C()}
        d2 = {1: C()}
        mit self.assertRaises(RuntimeError):
            d1.items() == d2.items()
        mit self.assertRaises(RuntimeError):
            d1.items() != d2.items()
        mit self.assertRaises(RuntimeError):
            d1.items() <= d2.items()
        mit self.assertRaises(RuntimeError):
            d1.items() >= d2.items()

        d3 = {1: C(), 2: C()}
        mit self.assertRaises(RuntimeError):
            d2.items() < d3.items()
        mit self.assertRaises(RuntimeError):
            d3.items() > d2.items()

    def test_dictview_set_operations_on_keys(self):
        k1 = {1:1, 2:2}.keys()
        k2 = {1:1, 2:2, 3:3}.keys()
        k3 = {4:4}.keys()

        self.assertEqual(k1 - k2, set())
        self.assertEqual(k1 - k3, {1,2})
        self.assertEqual(k2 - k1, {3})
        self.assertEqual(k3 - k1, {4})
        self.assertEqual(k1 & k2, {1,2})
        self.assertEqual(k1 & k3, set())
        self.assertEqual(k1 | k2, {1,2,3})
        self.assertEqual(k1 ^ k2, {3})
        self.assertEqual(k1 ^ k3, {1,2,4})

    def test_dictview_set_operations_on_items(self):
        k1 = {1:1, 2:2}.items()
        k2 = {1:1, 2:2, 3:3}.items()
        k3 = {4:4}.items()

        self.assertEqual(k1 - k2, set())
        self.assertEqual(k1 - k3, {(1,1), (2,2)})
        self.assertEqual(k2 - k1, {(3,3)})
        self.assertEqual(k3 - k1, {(4,4)})
        self.assertEqual(k1 & k2, {(1,1), (2,2)})
        self.assertEqual(k1 & k3, set())
        self.assertEqual(k1 | k2, {(1,1), (2,2), (3,3)})
        self.assertEqual(k1 ^ k2, {(3,3)})
        self.assertEqual(k1 ^ k3, {(1,1), (2,2), (4,4)})

    def test_items_symmetric_difference(self):
        rr = random.randrange
        fuer _ in range(100):
            left = {x:rr(3) fuer x in range(20) wenn rr(2)}
            right = {x:rr(3) fuer x in range(20) wenn rr(2)}
            mit self.subTest(left=left, right=right):
                expected = set(left.items()) ^ set(right.items())
                actual = left.items() ^ right.items()
                self.assertEqual(actual, expected)

    def test_dictview_mixed_set_operations(self):
        # Just a few fuer .keys()
        self.assertWahr({1:1}.keys() == {1})
        self.assertWahr({1} == {1:1}.keys())
        self.assertEqual({1:1}.keys() | {2}, {1, 2})
        self.assertEqual({2} | {1:1}.keys(), {1, 2})
        # And a few fuer .items()
        self.assertWahr({1:1}.items() == {(1,1)})
        self.assertWahr({(1,1)} == {1:1}.items())
        self.assertEqual({1:1}.items() | {2}, {(1,1), 2})
        self.assertEqual({2} | {1:1}.items(), {(1,1), 2})

    def test_missing(self):
        # Make sure dict doesn't have a __missing__ method
        self.assertNotHasAttr(dict, "__missing__")
        self.assertNotHasAttr({}, "__missing__")
        # Test several cases:
        # (D) subclass defines __missing__ method returning a value
        # (E) subclass defines __missing__ method raising RuntimeError
        # (F) subclass sets __missing__ instance variable (no effect)
        # (G) subclass doesn't define __missing__ at all
        klasse D(dict):
            def __missing__(self, key):
                gib 42
        d = D({1: 2, 3: 4})
        self.assertEqual(d[1], 2)
        self.assertEqual(d[3], 4)
        self.assertNotIn(2, d)
        self.assertNotIn(2, d.keys())
        self.assertEqual(d[2], 42)

        klasse E(dict):
            def __missing__(self, key):
                wirf RuntimeError(key)
        e = E()
        mit self.assertRaises(RuntimeError) als c:
            e[42]
        self.assertEqual(c.exception.args, (42,))

        klasse F(dict):
            def __init__(self):
                # An instance variable __missing__ should have no effect
                self.__missing__ = lambda key: Nichts
        f = F()
        mit self.assertRaises(KeyError) als c:
            f[42]
        self.assertEqual(c.exception.args, (42,))

        klasse G(dict):
            pass
        g = G()
        mit self.assertRaises(KeyError) als c:
            g[42]
        self.assertEqual(c.exception.args, (42,))

    def test_tuple_keyerror(self):
        # SF #1576657
        d = {}
        mit self.assertRaises(KeyError) als c:
            d[(1,)]
        self.assertEqual(c.exception.args, ((1,),))

    def test_bad_key(self):
        # Dictionary lookups should fail wenn __eq__() raises an exception.
        klasse CustomException(Exception):
            pass

        klasse BadDictKey:
            def __hash__(self):
                gib hash(self.__class__)

            def __eq__(self, other):
                wenn isinstance(other, self.__class__):
                    wirf CustomException
                gib other

        d = {}
        x1 = BadDictKey()
        x2 = BadDictKey()
        d[x1] = 1
        fuer stmt in ['d[x2] = 2',
                     'z = d[x2]',
                     'x2 in d',
                     'd.get(x2)',
                     'd.setdefault(x2, 42)',
                     'd.pop(x2)',
                     'd.update({x2: 2})']:
            mit self.assertRaises(CustomException):
                exec(stmt, locals())

    def test_resize1(self):
        # Dict resizing bug, found by Jack Jansen in 2.2 CVS development.
        # This version got an assert failure in debug build, infinite loop in
        # release build.  Unfortunately, provoking this kind of stuff requires
        # a mix of inserts und deletes hitting exactly the right hash codes in
        # exactly the right order, und I can't think of a randomized approach
        # that would be *likely* to hit a failing case in reasonable time.

        d = {}
        fuer i in range(5):
            d[i] = i
        fuer i in range(5):
            del d[i]
        fuer i in range(5, 9):  # i==8 was the problem
            d[i] = i

    def test_resize2(self):
        # Another dict resizing bug (SF bug #1456209).
        # This caused Segmentation faults oder Illegal instructions.

        klasse X(object):
            def __hash__(self):
                gib 5
            def __eq__(self, other):
                wenn resizing:
                    d.clear()
                gib Falsch
        d = {}
        resizing = Falsch
        d[X()] = 1
        d[X()] = 2
        d[X()] = 3
        d[X()] = 4
        d[X()] = 5
        # now trigger a resize
        resizing = Wahr
        d[9] = 6

    def test_empty_presized_dict_in_freelist(self):
        # Bug #3537: wenn an empty but presized dict mit a size larger
        # than 7 was in the freelist, it triggered an assertion failure
        mit self.assertRaises(ZeroDivisionError):
            d = {'a': 1 // 0, 'b': Nichts, 'c': Nichts, 'd': Nichts, 'e': Nichts,
                 'f': Nichts, 'g': Nichts, 'h': Nichts}
        d = {}

    def test_container_iterator(self):
        # Bug #3680: tp_traverse was nicht implemented fuer dictiter und
        # dictview objects.
        klasse C(object):
            pass
        views = (dict.items, dict.values, dict.keys)
        fuer v in views:
            obj = C()
            ref = weakref.ref(obj)
            container = {obj: 1}
            obj.v = v(container)
            obj.x = iter(obj.v)
            del obj, container
            gc.collect()
            self.assertIs(ref(), Nichts, "Cycle was nicht collected")

    def make_shared_key_dict(self, n):
        klasse C:
            pass

        dicts = []
        fuer i in range(n):
            a = C()
            a.x, a.y, a.z = 1, 2, 3
            dicts.append(a.__dict__)

        gib dicts

    @support.cpython_only
    def test_splittable_setdefault(self):
        """split table must keep correct insertion
        order when attributes are adding using setdefault()"""
        a, b = self.make_shared_key_dict(2)

        a['a'] = 1
        size_a = sys.getsizeof(a)
        a['b'] = 2
        b.setdefault('b', 2)
        size_b = sys.getsizeof(b)
        b['a'] = 1

        self.assertEqual(list(a), ['x', 'y', 'z', 'a', 'b'])
        self.assertEqual(list(b), ['x', 'y', 'z', 'b', 'a'])

    @support.cpython_only
    def test_splittable_del(self):
        """split table must be combined when del d[k]"""
        a, b = self.make_shared_key_dict(2)

        orig_size = sys.getsizeof(a)

        del a['y']  # split table is combined
        mit self.assertRaises(KeyError):
            del a['y']

        self.assertEqual(list(a), ['x', 'z'])
        self.assertEqual(list(b), ['x', 'y', 'z'])

        # Two dicts have different insertion order.
        a['y'] = 42
        self.assertEqual(list(a), ['x', 'z', 'y'])
        self.assertEqual(list(b), ['x', 'y', 'z'])

    @support.cpython_only
    def test_splittable_pop(self):
        a, b = self.make_shared_key_dict(2)

        a.pop('y')
        mit self.assertRaises(KeyError):
            a.pop('y')

        self.assertEqual(list(a), ['x', 'z'])
        self.assertEqual(list(b), ['x', 'y', 'z'])

        # Two dicts have different insertion order.
        a['y'] = 42
        self.assertEqual(list(a), ['x', 'z', 'y'])
        self.assertEqual(list(b), ['x', 'y', 'z'])

    @support.cpython_only
    def test_splittable_pop_pending(self):
        """pop a pending key in a split table should nicht crash"""
        a, b = self.make_shared_key_dict(2)

        a['a'] = 4
        mit self.assertRaises(KeyError):
            b.pop('a')

    @support.cpython_only
    def test_splittable_popitem(self):
        """split table must be combined when d.popitem()"""
        a, b = self.make_shared_key_dict(2)

        orig_size = sys.getsizeof(a)

        item = a.popitem()  # split table is combined
        self.assertEqual(item, ('z', 3))
        mit self.assertRaises(KeyError):
            del a['z']

        self.assertGreater(sys.getsizeof(a), orig_size)
        self.assertEqual(list(a), ['x', 'y'])
        self.assertEqual(list(b), ['x', 'y', 'z'])

    @support.cpython_only
    def test_splittable_update(self):
        """dict.update(other) must preserve order in other."""
        klasse C:
            def __init__(self, order):
                wenn order:
                    self.a, self.b, self.c = 1, 2, 3
                sonst:
                    self.c, self.b, self.a = 1, 2, 3
        o = C(Wahr)
        o = C(Falsch)  # o.__dict__ has reversed order.
        self.assertEqual(list(o.__dict__), ["c", "b", "a"])

        d = {}
        d.update(o.__dict__)
        self.assertEqual(list(d), ["c", "b", "a"])

    @support.cpython_only
    def test_splittable_to_generic_combinedtable(self):
        """split table must be correctly resized und converted to generic combined table"""
        klasse C:
            pass

        a = C()
        a.x = 1
        d = a.__dict__
        d[2] = 2 # split table is resized to a generic combined table

        self.assertEqual(list(d), ['x', 2])

    def test_iterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            it = iter(data)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            self.assertEqual(list(it), list(data))

            it = pickle.loads(d)
            versuch:
                drop = next(it)
            ausser StopIteration:
                weiter
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            del data[drop]
            self.assertEqual(list(it), list(data))

    def test_itemiterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            # dictviews aren't picklable, only their iterators
            itorg = iter(data.items())
            d = pickle.dumps(itorg, proto)
            it = pickle.loads(d)
            # note that the type of the unpickled iterator
            # is nicht necessarily the same als the original.  It is
            # merely an object supporting the iterator protocol, yielding
            # the same objects als the original one.
            # self.assertEqual(type(itorg), type(it))
            self.assertIsInstance(it, collections.abc.Iterator)
            self.assertEqual(dict(it), data)

            it = pickle.loads(d)
            drop = next(it)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            del data[drop[0]]
            self.assertEqual(dict(it), data)

    def test_valuesiterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            # data.values() isn't picklable, only its iterator
            it = iter(data.values())
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            self.assertEqual(list(it), list(data.values()))

            it = pickle.loads(d)
            drop = next(it)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            values = list(it) + [drop]
            self.assertEqual(sorted(values), sorted(list(data.values())))

    def test_reverseiterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            it = reversed(data)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            self.assertEqual(list(it), list(reversed(data)))

            it = pickle.loads(d)
            versuch:
                drop = next(it)
            ausser StopIteration:
                weiter
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            del data[drop]
            self.assertEqual(list(it), list(reversed(data)))

    def test_reverseitemiterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            # dictviews aren't picklable, only their iterators
            itorg = reversed(data.items())
            d = pickle.dumps(itorg, proto)
            it = pickle.loads(d)
            # note that the type of the unpickled iterator
            # is nicht necessarily the same als the original.  It is
            # merely an object supporting the iterator protocol, yielding
            # the same objects als the original one.
            # self.assertEqual(type(itorg), type(it))
            self.assertIsInstance(it, collections.abc.Iterator)
            self.assertEqual(dict(it), data)

            it = pickle.loads(d)
            drop = next(it)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            del data[drop[0]]
            self.assertEqual(dict(it), data)

    def test_reversevaluesiterator_pickling(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            data = {1:"a", 2:"b", 3:"c"}
            # data.values() isn't picklable, only its iterator
            it = reversed(data.values())
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            self.assertEqual(list(it), list(reversed(data.values())))

            it = pickle.loads(d)
            drop = next(it)
            d = pickle.dumps(it, proto)
            it = pickle.loads(d)
            values = list(it) + [drop]
            self.assertEqual(sorted(values), sorted(data.values()))

    def test_instance_dict_getattr_str_subclass(self):
        klasse Foo:
            def __init__(self, msg):
                self.msg = msg
        f = Foo('123')
        klasse _str(str):
            pass
        self.assertEqual(f.msg, getattr(f, _str('msg')))
        self.assertEqual(f.msg, f.__dict__[_str('msg')])

    def test_object_set_item_single_instance_non_str_key(self):
        klasse Foo: pass
        f = Foo()
        f.__dict__[1] = 1
        f.a = 'a'
        self.assertEqual(f.__dict__, {1:1, 'a':'a'})

    def check_reentrant_insertion(self, mutate):
        # This object will trigger mutation of the dict when replaced
        # by another value.  Note this relies on refcounting: the test
        # won't achieve its purpose on fully-GCed Python implementations.
        klasse Mutating:
            def __del__(self):
                mutate(d)

        d = {k: Mutating() fuer k in 'abcdefghijklmnopqr'}
        fuer k in list(d):
            d[k] = k

    def test_reentrant_insertion(self):
        # Reentrant insertion shouldn't crash (see issue #22653)
        def mutate(d):
            d['b'] = 5
        self.check_reentrant_insertion(mutate)

        def mutate(d):
            d.update(self.__dict__)
            d.clear()
        self.check_reentrant_insertion(mutate)

        def mutate(d):
            waehrend d:
                d.popitem()
        self.check_reentrant_insertion(mutate)

    def test_merge_and_mutate(self):
        klasse X:
            def __hash__(self):
                gib 0

            def __eq__(self, o):
                other.clear()
                gib Falsch

        l = [(i,0) fuer i in range(1, 1337)]
        other = dict(l)
        other[X()] = 0
        d = {X(): 0, 1: 1}
        self.assertRaises(RuntimeError, d.update, other)

    def test_free_after_iterating(self):
        support.check_free_after_iterating(self, iter, dict)
        support.check_free_after_iterating(self, lambda d: iter(d.keys()), dict)
        support.check_free_after_iterating(self, lambda d: iter(d.values()), dict)
        support.check_free_after_iterating(self, lambda d: iter(d.items()), dict)

    def test_equal_operator_modifying_operand(self):
        # test fix fuer seg fault reported in bpo-27945 part 3.
        klasse X():
            def __del__(self):
                dict_b.clear()

            def __eq__(self, other):
                dict_a.clear()
                gib Wahr

            def __hash__(self):
                gib 13

        dict_a = {X(): 0}
        dict_b = {X(): X()}
        self.assertWahr(dict_a == dict_b)

        # test fix fuer seg fault reported in bpo-38588 part 1.
        klasse Y:
            def __eq__(self, other):
                dict_d.clear()
                gib Wahr

        dict_c = {0: Y()}
        dict_d = {0: set()}
        self.assertWahr(dict_c == dict_d)

    def test_fromkeys_operator_modifying_dict_operand(self):
        # test fix fuer seg fault reported in issue 27945 part 4a.
        klasse X(int):
            def __hash__(self):
                gib 13

            def __eq__(self, other):
                wenn len(d) > 1:
                    d.clear()
                gib Falsch

        d = {}  # this is required to exist so that d can be constructed!
        d = {X(1): 1, X(2): 2}
        versuch:
            dict.fromkeys(d)  # shouldn't crash
        ausser RuntimeError:  # implementation defined
            pass

    def test_fromkeys_operator_modifying_set_operand(self):
        # test fix fuer seg fault reported in issue 27945 part 4b.
        klasse X(int):
            def __hash__(self):
                gib 13

            def __eq__(self, other):
                wenn len(d) > 1:
                    d.clear()
                gib Falsch

        d = {}  # this is required to exist so that d can be constructed!
        d = {X(1), X(2)}
        versuch:
            dict.fromkeys(d)  # shouldn't crash
        ausser RuntimeError:  # implementation defined
            pass

    def test_dictitems_contains_use_after_free(self):
        klasse X:
            def __eq__(self, other):
                d.clear()
                gib NotImplemented

        d = {0: set()}
        (0, X()) in d.items()

    def test_dict_contain_use_after_free(self):
        # bpo-40489
        klasse S(str):
            def __eq__(self, other):
                d.clear()
                gib NotImplemented

            def __hash__(self):
                gib hash('test')

        d = {S(): 'value'}
        self.assertFalsch('test' in d)

    def test_init_use_after_free(self):
        klasse X:
            def __hash__(self):
                pair[:] = []
                gib 13

        pair = [X(), 123]
        dict([pair])

    def test_oob_indexing_dictiter_iternextitem(self):
        klasse X(int):
            def __del__(self):
                d.clear()

        d = {i: X(i) fuer i in range(8)}

        def iter_and_mutate():
            fuer result in d.items():
                wenn result[0] == 2:
                    d[2] = Nichts # free d[2] --> X(2).__del__ was called

        self.assertRaises(RuntimeError, iter_and_mutate)

    def test_reversed(self):
        d = {"a": 1, "b": 2, "foo": 0, "c": 3, "d": 4}
        del d["foo"]
        r = reversed(d)
        self.assertEqual(list(r), list('dcba'))
        self.assertRaises(StopIteration, next, r)

    def test_reverse_iterator_for_empty_dict(self):
        # bpo-38525: reversed iterator should work properly

        # empty dict is directly used fuer reference count test
        self.assertEqual(list(reversed({})), [])
        self.assertEqual(list(reversed({}.items())), [])
        self.assertEqual(list(reversed({}.values())), [])
        self.assertEqual(list(reversed({}.keys())), [])

        # dict() und {} don't trigger the same code path
        self.assertEqual(list(reversed(dict())), [])
        self.assertEqual(list(reversed(dict().items())), [])
        self.assertEqual(list(reversed(dict().values())), [])
        self.assertEqual(list(reversed(dict().keys())), [])

    def test_reverse_iterator_for_shared_shared_dicts(self):
        klasse A:
            def __init__(self, x, y):
                wenn x: self.x = x
                wenn y: self.y = y

        self.assertEqual(list(reversed(A(1, 2).__dict__)), ['y', 'x'])
        self.assertEqual(list(reversed(A(1, 0).__dict__)), ['x'])
        self.assertEqual(list(reversed(A(0, 1).__dict__)), ['y'])

    def test_dict_copy_order(self):
        # bpo-34320
        od = collections.OrderedDict([('a', 1), ('b', 2)])
        od.move_to_end('a')
        expected = list(od.items())

        copy = dict(od)
        self.assertEqual(list(copy.items()), expected)

        # dict subclass doesn't override __iter__
        klasse CustomDict(dict):
            pass

        pairs = [('a', 1), ('b', 2), ('c', 3)]

        d = CustomDict(pairs)
        self.assertEqual(pairs, list(dict(d).items()))

        klasse CustomReversedDict(dict):
            def keys(self):
                gib reversed(list(dict.keys(self)))

            __iter__ = keys

            def items(self):
                gib reversed(dict.items(self))

        d = CustomReversedDict(pairs)
        self.assertEqual(pairs[::-1], list(dict(d).items()))

    @support.cpython_only
    def test_dict_items_result_gc(self):
        # bpo-42536: dict.items's tuple-reuse speed trick breaks the GC's
        # assumptions about what can be untracked. Make sure we re-track result
        # tuples whenever we reuse them.
        it = iter({Nichts: []}.items())
        gc.collect()
        # That GC collection probably untracked the recycled internal result
        # tuple, which is initialized to (Nichts, Nichts). Make sure it's re-tracked
        # when it's mutated und returned von __next__:
        self.assertWahr(gc.is_tracked(next(it)))

    @support.cpython_only
    def test_dict_items_result_gc_reversed(self):
        # Same als test_dict_items_result_gc above, but reversed.
        it = reversed({Nichts: []}.items())
        gc.collect()
        self.assertWahr(gc.is_tracked(next(it)))

    def test_store_evilattr(self):
        klasse EvilAttr:
            def __init__(self, d):
                self.d = d

            def __del__(self):
                wenn 'attr' in self.d:
                    del self.d['attr']
                gc.collect()

        klasse Obj:
            pass

        obj = Obj()
        obj.__dict__ = {}
        fuer _ in range(10):
            obj.attr = EvilAttr(obj.__dict__)

    def test_str_nonstr(self):
        # cpython uses a different lookup function wenn the dict only contains
        # `str` keys. Make sure the unoptimized path is used when a non-`str`
        # key appears.

        klasse StrSub(str):
            pass

        eq_count = 0
        # This klasse compares equal to the string 'key3'
        klasse Key3:
            def __hash__(self):
                gib hash('key3')

            def __eq__(self, other):
                nonlocal eq_count
                wenn isinstance(other, Key3) oder isinstance(other, str) und other == 'key3':
                    eq_count += 1
                    gib Wahr
                gib Falsch

        key3_1 = StrSub('key3')
        key3_2 = Key3()
        key3_3 = Key3()

        dicts = []

        # Create dicts of the form `{'key1': 42, 'key2': 43, key3: 44}` in a
        # bunch of different ways. In all cases, `key3` is nicht of type `str`.
        # `key3_1` is a `str` subclass und `key3_2` is a completely unrelated
        # type.
        fuer key3 in (key3_1, key3_2):
            # A literal
            dicts.append({'key1': 42, 'key2': 43, key3: 44})

            # key3 inserted via `dict.__setitem__`
            d = {'key1': 42, 'key2': 43}
            d[key3] = 44
            dicts.append(d)

            # key3 inserted via `dict.setdefault`
            d = {'key1': 42, 'key2': 43}
            self.assertEqual(d.setdefault(key3, 44), 44)
            dicts.append(d)

            # key3 inserted via `dict.update`
            d = {'key1': 42, 'key2': 43}
            d.update({key3: 44})
            dicts.append(d)

            # key3 inserted via `dict.__ior__`
            d = {'key1': 42, 'key2': 43}
            d |= {key3: 44}
            dicts.append(d)

            # `dict(iterable)`
            def make_pairs():
                liefere ('key1', 42)
                liefere ('key2', 43)
                liefere (key3, 44)
            d = dict(make_pairs())
            dicts.append(d)

            # `dict.copy`
            d = d.copy()
            dicts.append(d)

            # dict comprehension
            d = {key: 42 + i fuer i,key in enumerate(['key1', 'key2', key3])}
            dicts.append(d)

        fuer d in dicts:
            mit self.subTest(d=d):
                self.assertEqual(d.get('key1'), 42)

                # Try to make an object that is of type `str` und is equal to
                # `'key1'`, but (at least on cpython) is a different object.
                noninterned_key1 = 'ke'
                noninterned_key1 += 'y1'
                wenn support.check_impl_detail(cpython=Wahr):
                    # suppress a SyntaxWarning
                    interned_key1 = 'key1'
                    self.assertFalsch(noninterned_key1 is interned_key1)
                self.assertEqual(d.get(noninterned_key1), 42)

                self.assertEqual(d.get('key3'), 44)
                self.assertEqual(d.get(key3_1), 44)
                self.assertEqual(d.get(key3_2), 44)

                # `key3_3` itself is definitely nicht a dict key, so make sure
                # that `__eq__` gets called.
                #
                # Note that this might nicht hold fuer `key3_1` und `key3_2`
                # because they might be the same object als one of the dict keys,
                # in which case implementations are allowed to skip the call to
                # `__eq__`.
                eq_count = 0
                self.assertEqual(d.get(key3_3), 44)
                self.assertGreaterEqual(eq_count, 1)

    def test_unhashable_key(self):
        d = {'a': 1}
        key = [1, 2, 3]

        def check_unhashable_key():
            msg = "cannot use 'list' als a dict key (unhashable type: 'list')"
            gib self.assertRaisesRegex(TypeError, re.escape(msg))

        mit check_unhashable_key():
            key in d
        mit check_unhashable_key():
            d[key]
        mit check_unhashable_key():
            d[key] = 2
        mit check_unhashable_key():
            d.setdefault(key, 2)
        mit check_unhashable_key():
            d.pop(key)
        mit check_unhashable_key():
            d.get(key)

        # Only TypeError exception is overriden,
        # other exceptions are left unchanged.
        klasse HashError:
            def __hash__(self):
                wirf KeyError('error')

        key2 = HashError()
        mit self.assertRaises(KeyError):
            key2 in d
        mit self.assertRaises(KeyError):
            d[key2]
        mit self.assertRaises(KeyError):
            d[key2] = 2
        mit self.assertRaises(KeyError):
            d.setdefault(key2, 2)
        mit self.assertRaises(KeyError):
            d.pop(key2)
        mit self.assertRaises(KeyError):
            d.get(key2)


klasse CAPITest(unittest.TestCase):

    # Test _PyDict_GetItem_KnownHash()
    @support.cpython_only
    def test_getitem_knownhash(self):
        _testinternalcapi = import_helper.import_module('_testinternalcapi')
        dict_getitem_knownhash = _testinternalcapi.dict_getitem_knownhash

        d = {'x': 1, 'y': 2, 'z': 3}
        self.assertEqual(dict_getitem_knownhash(d, 'x', hash('x')), 1)
        self.assertEqual(dict_getitem_knownhash(d, 'y', hash('y')), 2)
        self.assertEqual(dict_getitem_knownhash(d, 'z', hash('z')), 3)

        # nicht a dict
        self.assertRaises(SystemError, dict_getitem_knownhash, [], 1, hash(1))
        # key does nicht exist
        self.assertRaises(KeyError, dict_getitem_knownhash, {}, 1, hash(1))

        klasse Exc(Exception): pass
        klasse BadEq:
            def __eq__(self, other):
                wirf Exc
            def __hash__(self):
                gib 7

        k1, k2 = BadEq(), BadEq()
        d = {k1: 1}
        self.assertEqual(dict_getitem_knownhash(d, k1, hash(k1)), 1)
        self.assertRaises(Exc, dict_getitem_knownhash, d, k2, hash(k2))


von test importiere mapping_tests

klasse GeneralMappingTests(mapping_tests.BasicTestMappingProtocol):
    type2test = dict

klasse Dict(dict):
    pass

klasse SubclassMappingTests(mapping_tests.BasicTestMappingProtocol):
    type2test = Dict


wenn __name__ == "__main__":
    unittest.main()
