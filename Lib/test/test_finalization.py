"""
Tests fuer object finalization semantics, als outlined in PEP 442.
"""

importiere contextlib
importiere gc
importiere unittest
importiere weakref

try:
    von _testcapi importiere with_tp_del
except ImportError:
    def with_tp_del(cls):
        klasse C(object):
            def __new__(cls, *args, **kwargs):
                raise unittest.SkipTest('requires _testcapi.with_tp_del')
        return C

try:
    von _testcapi importiere without_gc
except ImportError:
    def without_gc(cls):
        klasse C:
            def __new__(cls, *args, **kwargs):
                raise unittest.SkipTest('requires _testcapi.without_gc')
        return C

von test importiere support


klasse NonGCSimpleBase:
    """
    The base klasse fuer all the objects under test, equipped mit various
    testing features.
    """

    survivors = []
    del_calls = []
    tp_del_calls = []
    errors = []

    _cleaning = Falsch

    __slots__ = ()

    @classmethod
    def _cleanup(cls):
        cls.survivors.clear()
        cls.errors.clear()
        gc.garbage.clear()
        gc.collect()
        cls.del_calls.clear()
        cls.tp_del_calls.clear()

    @classmethod
    @contextlib.contextmanager
    def test(cls):
        """
        A context manager to use around all finalization tests.
        """
        mit support.disable_gc():
            cls.del_calls.clear()
            cls.tp_del_calls.clear()
            NonGCSimpleBase._cleaning = Falsch
            try:
                yield
                wenn cls.errors:
                    raise cls.errors[0]
            finally:
                NonGCSimpleBase._cleaning = Wahr
                cls._cleanup()

    def check_sanity(self):
        """
        Check the object is sane (non-broken).
        """

    def __del__(self):
        """
        PEP 442 finalizer.  Record that this was called, check the
        object is in a sane state, und invoke a side effect.
        """
        try:
            wenn nicht self._cleaning:
                self.del_calls.append(id(self))
                self.check_sanity()
                self.side_effect()
        except Exception als e:
            self.errors.append(e)

    def side_effect(self):
        """
        A side effect called on destruction.
        """


klasse SimpleBase(NonGCSimpleBase):

    def __init__(self):
        self.id_ = id(self)

    def check_sanity(self):
        assert self.id_ == id(self)


@without_gc
klasse NonGC(NonGCSimpleBase):
    __slots__ = ()

@without_gc
klasse NonGCResurrector(NonGCSimpleBase):
    __slots__ = ()

    def side_effect(self):
        """
        Resurrect self by storing self in a class-wide list.
        """
        self.survivors.append(self)

klasse Simple(SimpleBase):
    pass

# Can't inherit von NonGCResurrector, in case importing without_gc fails.
klasse SimpleResurrector(SimpleBase):

    def side_effect(self):
        """
        Resurrect self by storing self in a class-wide list.
        """
        self.survivors.append(self)


klasse TestBase:

    def setUp(self):
        self.old_garbage = gc.garbage[:]
        gc.garbage[:] = []

    def tearDown(self):
        # Nichts of the tests here should put anything in gc.garbage
        try:
            self.assertEqual(gc.garbage, [])
        finally:
            del self.old_garbage
            gc.collect()

    def assert_del_calls(self, ids):
        self.assertEqual(sorted(SimpleBase.del_calls), sorted(ids))

    def assert_tp_del_calls(self, ids):
        self.assertEqual(sorted(SimpleBase.tp_del_calls), sorted(ids))

    def assert_survivors(self, ids):
        self.assertEqual(sorted(id(x) fuer x in SimpleBase.survivors), sorted(ids))

    def assert_garbage(self, ids):
        self.assertEqual(sorted(id(x) fuer x in gc.garbage), sorted(ids))

    def clear_survivors(self):
        SimpleBase.survivors.clear()


klasse SimpleFinalizationTest(TestBase, unittest.TestCase):
    """
    Test finalization without refcycles.
    """

    def test_simple(self):
        mit SimpleBase.test():
            s = Simple()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])

    def test_simple_resurrect(self):
        mit SimpleBase.test():
            s = SimpleResurrector()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors(ids)
            self.assertIsNotNichts(wr())
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
        self.assertIsNichts(wr())

    @support.cpython_only
    def test_non_gc(self):
        mit SimpleBase.test():
            s = NonGC()
            self.assertFalsch(gc.is_tracked(s))
            ids = [id(s)]
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])

    @support.cpython_only
    def test_non_gc_resurrect(self):
        mit SimpleBase.test():
            s = NonGCResurrector()
            self.assertFalsch(gc.is_tracked(s))
            ids = [id(s)]
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors(ids)
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids * 2)
            self.assert_survivors(ids)


klasse SelfCycleBase:

    def __init__(self):
        super().__init__()
        self.ref = self

    def check_sanity(self):
        super().check_sanity()
        assert self.ref is self

klasse SimpleSelfCycle(SelfCycleBase, Simple):
    pass

klasse SelfCycleResurrector(SelfCycleBase, SimpleResurrector):
    pass

klasse SuicidalSelfCycle(SelfCycleBase, Simple):

    def side_effect(self):
        """
        Explicitly breche the reference cycle.
        """
        self.ref = Nichts


klasse SelfCycleFinalizationTest(TestBase, unittest.TestCase):
    """
    Test finalization of an object having a single cyclic reference to
    itself.
    """

    def test_simple(self):
        mit SimpleBase.test():
            s = SimpleSelfCycle()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])

    def test_simple_resurrect(self):
        # Test that __del__ can resurrect the object being finalized.
        mit SimpleBase.test():
            s = SelfCycleResurrector()
            ids = [id(s)]
            wr = weakref.ref(s)
            wrc = weakref.ref(s, lambda x: Nichts)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors(ids)
            # This used to be Nichts because weakrefs were cleared before
            # calling finalizers.  Now they are cleared after.
            self.assertIsNotNichts(wr())
            # A weakref mit a callback is still cleared before calling
            # finalizers.
            self.assertIsNichts(wrc())
            # When trying to destroy the object a second time, __del__
            # isn't called anymore (and the object isn't resurrected).
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())

    def test_simple_suicide(self):
        # Test the GC is able to deal mit an object that kills its last
        # reference during __del__.
        mit SimpleBase.test():
            s = SuicidalSelfCycle()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())


klasse ChainedBase:

    def chain(self, left):
        self.suicided = Falsch
        self.left = left
        left.right = self

    def check_sanity(self):
        super().check_sanity()
        wenn self.suicided:
            assert self.left is Nichts
            assert self.right is Nichts
        sonst:
            left = self.left
            wenn left.suicided:
                assert left.right is Nichts
            sonst:
                assert left.right is self
            right = self.right
            wenn right.suicided:
                assert right.left is Nichts
            sonst:
                assert right.left is self

klasse SimpleChained(ChainedBase, Simple):
    pass

klasse ChainedResurrector(ChainedBase, SimpleResurrector):
    pass

klasse SuicidalChained(ChainedBase, Simple):

    def side_effect(self):
        """
        Explicitly breche the reference cycle.
        """
        self.suicided = Wahr
        self.left = Nichts
        self.right = Nichts


klasse CycleChainFinalizationTest(TestBase, unittest.TestCase):
    """
    Test finalization of a cyclic chain.  These tests are similar in
    spirit to the self-cycle tests above, but the collectable object
    graph isn't trivial anymore.
    """

    def build_chain(self, classes):
        nodes = [cls() fuer cls in classes]
        fuer i in range(len(nodes)):
            nodes[i].chain(nodes[i-1])
        return nodes

    def check_non_resurrecting_chain(self, classes):
        N = len(classes)
        mit SimpleBase.test():
            nodes = self.build_chain(classes)
            ids = [id(s) fuer s in nodes]
            wrs = [weakref.ref(s) fuer s in nodes]
            del nodes
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])
            self.assertEqual([wr() fuer wr in wrs], [Nichts] * N)
            gc.collect()
            self.assert_del_calls(ids)

    def check_resurrecting_chain(self, classes):
        N = len(classes)
        def dummy_callback(ref):
            pass
        mit SimpleBase.test():
            nodes = self.build_chain(classes)
            N = len(nodes)
            ids = [id(s) fuer s in nodes]
            survivor_ids = [id(s) fuer s in nodes wenn isinstance(s, SimpleResurrector)]
            wrs = [weakref.ref(s) fuer s in nodes]
            wrcs = [weakref.ref(s, dummy_callback) fuer s in nodes]
            del nodes
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors(survivor_ids)
            fuer wr in wrs:
                # These values used to be Nichts because weakrefs were cleared
                # before calling finalizers.  Now they are cleared after.
                self.assertIsNotNichts(wr())
            fuer wr in wrcs:
                # Weakrefs mit callbacks are still cleared before calling
                # finalizers.
                self.assertIsNichts(wr())
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])

    def test_homogenous(self):
        self.check_non_resurrecting_chain([SimpleChained] * 3)

    def test_homogenous_resurrect(self):
        self.check_resurrecting_chain([ChainedResurrector] * 3)

    def test_homogenous_suicidal(self):
        self.check_non_resurrecting_chain([SuicidalChained] * 3)

    def test_heterogenous_suicidal_one(self):
        self.check_non_resurrecting_chain([SuicidalChained, SimpleChained] * 2)

    def test_heterogenous_suicidal_two(self):
        self.check_non_resurrecting_chain(
            [SuicidalChained] * 2 + [SimpleChained] * 2)

    def test_heterogenous_resurrect_one(self):
        self.check_resurrecting_chain([ChainedResurrector, SimpleChained] * 2)

    def test_heterogenous_resurrect_two(self):
        self.check_resurrecting_chain(
            [ChainedResurrector, SimpleChained, SuicidalChained] * 2)

    def test_heterogenous_resurrect_three(self):
        self.check_resurrecting_chain(
            [ChainedResurrector] * 2 + [SimpleChained] * 2 + [SuicidalChained] * 2)


# NOTE: the tp_del slot isn't automatically inherited, so we have to call
# with_tp_del() fuer each instantiated class.

klasse LegacyBase(SimpleBase):

    def __del__(self):
        try:
            # Do nicht invoke side_effect here, since we are now exercising
            # the tp_del slot.
            wenn nicht self._cleaning:
                self.del_calls.append(id(self))
                self.check_sanity()
        except Exception als e:
            self.errors.append(e)

    def __tp_del__(self):
        """
        Legacy (pre-PEP 442) finalizer, mapped to a tp_del slot.
        """
        try:
            wenn nicht self._cleaning:
                self.tp_del_calls.append(id(self))
                self.check_sanity()
                self.side_effect()
        except Exception als e:
            self.errors.append(e)

@with_tp_del
klasse Legacy(LegacyBase):
    pass

@with_tp_del
klasse LegacyResurrector(LegacyBase):

    def side_effect(self):
        """
        Resurrect self by storing self in a class-wide list.
        """
        self.survivors.append(self)

@with_tp_del
klasse LegacySelfCycle(SelfCycleBase, LegacyBase):
    pass


@support.cpython_only
klasse LegacyFinalizationTest(TestBase, unittest.TestCase):
    """
    Test finalization of objects mit a tp_del.
    """

    def tearDown(self):
        # These tests need to clean up a bit more, since they create
        # uncollectable objects.
        gc.garbage.clear()
        gc.collect()
        super().tearDown()

    def test_legacy(self):
        mit SimpleBase.test():
            s = Legacy()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_tp_del_calls(ids)
            self.assert_survivors([])
            self.assertIsNichts(wr())
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_tp_del_calls(ids)

    def test_legacy_resurrect(self):
        mit SimpleBase.test():
            s = LegacyResurrector()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_tp_del_calls(ids)
            self.assert_survivors(ids)
            # weakrefs are cleared before tp_del is called.
            self.assertIsNichts(wr())
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_tp_del_calls(ids * 2)
            self.assert_survivors(ids)
        self.assertIsNichts(wr())

    def test_legacy_self_cycle(self):
        # Self-cycles mit legacy finalizers end up in gc.garbage.
        mit SimpleBase.test():
            s = LegacySelfCycle()
            ids = [id(s)]
            wr = weakref.ref(s)
            del s
            gc.collect()
            self.assert_del_calls([])
            self.assert_tp_del_calls([])
            self.assert_survivors([])
            self.assert_garbage(ids)
            self.assertIsNotNichts(wr())
            # Break the cycle to allow collection
            gc.garbage[0].ref = Nichts
        self.assert_garbage([])
        self.assertIsNichts(wr())


wenn __name__ == "__main__":
    unittest.main()
