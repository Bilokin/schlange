importiere gc
importiere sys
importiere doctest
importiere unittest
importiere collections
importiere weakref
importiere operator
importiere contextlib
importiere copy
importiere threading
importiere time
importiere random
importiere textwrap

von test importiere support
von test.support importiere script_helper, ALWAYS_EQ
von test.support importiere gc_collect
von test.support importiere import_helper
von test.support importiere threading_helper
von test.support importiere is_wasi, Py_DEBUG

# Used in ReferencesTestCase.test_ref_created_during_del() .
ref_from_del = Nichts

# Used by FinalizeTestCase als a global that may be replaced by Nichts
# when the interpreter shuts down.
_global_var = 'foobar'

klasse C:
    def method(self):
        pass


klasse Callable:
    bar = Nichts

    def __call__(self, x):
        self.bar = x


def create_function():
    def f(): pass
    gib f

def create_bound_method():
    gib C().method


klasse Object:
    def __init__(self, arg):
        self.arg = arg
    def __repr__(self):
        gib "<Object %r>" % self.arg
    def __eq__(self, other):
        wenn isinstance(other, Object):
            gib self.arg == other.arg
        gib NotImplemented
    def __lt__(self, other):
        wenn isinstance(other, Object):
            gib self.arg < other.arg
        gib NotImplemented
    def __hash__(self):
        gib hash(self.arg)
    def some_method(self):
        gib 4
    def other_method(self):
        gib 5


klasse RefCycle:
    def __init__(self):
        self.cycle = self


klasse TestBase(unittest.TestCase):

    def setUp(self):
        self.cbcalled = 0

    def callback(self, ref):
        self.cbcalled += 1


@contextlib.contextmanager
def collect_in_thread(period=0.005):
    """
    Ensure GC collections happen in a different thread, at a high frequency.
    """
    please_stop = Falsch

    def collect():
        waehrend nicht please_stop:
            time.sleep(period)
            gc.collect()

    mit support.disable_gc():
        t = threading.Thread(target=collect)
        t.start()
        try:
            liefere
        finally:
            please_stop = Wahr
            t.join()


klasse ReferencesTestCase(TestBase):

    def test_basic_ref(self):
        self.check_basic_ref(C)
        self.check_basic_ref(create_function)
        self.check_basic_ref(create_bound_method)

        # Just make sure the tp_repr handler doesn't raise an exception.
        # Live reference:
        o = C()
        wr = weakref.ref(o)
        repr(wr)
        # Dead reference:
        del o
        repr(wr)

    @support.cpython_only
    def test_ref_repr(self):
        obj = C()
        ref = weakref.ref(obj)
        regex = (
            rf"<weakref at 0x[0-9a-fA-F]+; "
            rf"to '{'' wenn __name__ == '__main__' sonst C.__module__ + '.'}{C.__qualname__}' "
            rf"at 0x[0-9a-fA-F]+>"
        )
        self.assertRegex(repr(ref), regex)

        obj = Nichts
        gc_collect()
        self.assertRegex(repr(ref),
                         rf'<weakref at 0x[0-9a-fA-F]+; dead>')

        # test type mit __name__
        klasse WithName:
            @property
            def __name__(self):
                gib "custom_name"

        obj2 = WithName()
        ref2 = weakref.ref(obj2)
        regex = (
            rf"<weakref at 0x[0-9a-fA-F]+; "
            rf"to '{'' wenn __name__ == '__main__' sonst WithName.__module__ + '.'}"
            rf"{WithName.__qualname__}' "
            rf"at 0x[0-9a-fA-F]+ +\(custom_name\)>"
        )
        self.assertRegex(repr(ref2), regex)

    def test_repr_failure_gh99184(self):
        klasse MyConfig(dict):
            def __getattr__(self, x):
                gib self[x]

        obj = MyConfig(offset=5)
        obj_weakref = weakref.ref(obj)

        self.assertIn('MyConfig', repr(obj_weakref))
        self.assertIn('MyConfig', str(obj_weakref))

    def test_basic_callback(self):
        self.check_basic_callback(C)
        self.check_basic_callback(create_function)
        self.check_basic_callback(create_bound_method)

    @support.cpython_only
    def test_cfunction(self):
        _testcapi = import_helper.import_module("_testcapi")
        create_cfunction = _testcapi.create_cfunction
        f = create_cfunction()
        wr = weakref.ref(f)
        self.assertIs(wr(), f)
        del f
        self.assertIsNichts(wr())
        self.check_basic_ref(create_cfunction)
        self.check_basic_callback(create_cfunction)

    def test_multiple_callbacks(self):
        o = C()
        ref1 = weakref.ref(o, self.callback)
        ref2 = weakref.ref(o, self.callback)
        del o
        gc_collect()  # For PyPy oder other GCs.
        self.assertIsNichts(ref1(), "expected reference to be invalidated")
        self.assertIsNichts(ref2(), "expected reference to be invalidated")
        self.assertEqual(self.cbcalled, 2,
                     "callback nicht called the right number of times")

    def test_multiple_selfref_callbacks(self):
        # Make sure all references are invalidated before callbacks are called
        #
        # What's important here is that we're using the first
        # reference in the callback invoked on the second reference
        # (the most recently created ref is cleaned up first).  This
        # tests that all references to the object are invalidated
        # before any of the callbacks are invoked, so that we only
        # have one invocation of _weakref.c:cleanup_helper() active
        # fuer a particular object at a time.
        #
        def callback(object, self=self):
            self.ref()
        c = C()
        self.ref = weakref.ref(c, callback)
        ref1 = weakref.ref(c, callback)
        del c

    def test_constructor_kwargs(self):
        c = C()
        self.assertRaises(TypeError, weakref.ref, c, callback=Nichts)

    def test_proxy_ref(self):
        o = C()
        o.bar = 1
        ref1 = weakref.proxy(o, self.callback)
        ref2 = weakref.proxy(o, self.callback)
        del o
        gc_collect()  # For PyPy oder other GCs.

        def check(proxy):
            proxy.bar

        self.assertRaises(ReferenceError, check, ref1)
        self.assertRaises(ReferenceError, check, ref2)
        ref3 = weakref.proxy(C())
        gc_collect()  # For PyPy oder other GCs.
        self.assertRaises(ReferenceError, bool, ref3)
        self.assertEqual(self.cbcalled, 2)

    @support.cpython_only
    def test_proxy_repr(self):
        obj = C()
        ref = weakref.proxy(obj, self.callback)
        regex = (
            rf"<weakproxy at 0x[0-9a-fA-F]+; "
            rf"to '{'' wenn __name__ == '__main__' sonst C.__module__ + '.'}{C.__qualname__}' "
            rf"at 0x[0-9a-fA-F]+>"
        )
        self.assertRegex(repr(ref), regex)

        obj = Nichts
        gc_collect()
        self.assertRegex(repr(ref),
                         rf'<weakproxy at 0x[0-9a-fA-F]+; dead>')

    def check_basic_ref(self, factory):
        o = factory()
        ref = weakref.ref(o)
        self.assertIsNotNichts(ref(),
                     "weak reference to live object should be live")
        o2 = ref()
        self.assertIs(o, o2,
                     "<ref>() should gib original object wenn live")

    def check_basic_callback(self, factory):
        self.cbcalled = 0
        o = factory()
        ref = weakref.ref(o, self.callback)
        del o
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(self.cbcalled, 1,
                     "callback did nicht properly set 'cbcalled'")
        self.assertIsNichts(ref(),
                     "ref2 should be dead after deleting object reference")

    def test_ref_reuse(self):
        o = C()
        ref1 = weakref.ref(o)
        # create a proxy to make sure that there's an intervening creation
        # between these two; it should make no difference
        proxy = weakref.proxy(o)
        ref2 = weakref.ref(o)
        self.assertIs(ref1, ref2,
                     "reference object w/out callback should be re-used")

        o = C()
        proxy = weakref.proxy(o)
        ref1 = weakref.ref(o)
        ref2 = weakref.ref(o)
        self.assertIs(ref1, ref2,
                     "reference object w/out callback should be re-used")
        self.assertEqual(weakref.getweakrefcount(o), 2,
                     "wrong weak ref count fuer object")
        del proxy
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(weakref.getweakrefcount(o), 1,
                     "wrong weak ref count fuer object after deleting proxy")

    def test_proxy_reuse(self):
        o = C()
        proxy1 = weakref.proxy(o)
        ref = weakref.ref(o)
        proxy2 = weakref.proxy(o)
        self.assertIs(proxy1, proxy2,
                     "proxy object w/out callback should have been re-used")

    def test_basic_proxy(self):
        o = C()
        self.check_proxy(o, weakref.proxy(o))

        L = collections.UserList()
        p = weakref.proxy(L)
        self.assertFalsch(p, "proxy fuer empty UserList should be false")
        p.append(12)
        self.assertEqual(len(L), 1)
        self.assertWahr(p, "proxy fuer non-empty UserList should be true")
        p[:] = [2, 3]
        self.assertEqual(len(L), 2)
        self.assertEqual(len(p), 2)
        self.assertIn(3, p, "proxy didn't support __contains__() properly")
        p[1] = 5
        self.assertEqual(L[1], 5)
        self.assertEqual(p[1], 5)
        L2 = collections.UserList(L)
        p2 = weakref.proxy(L2)
        self.assertEqual(p, p2)
        ## self.assertEqual(repr(L2), repr(p2))
        L3 = collections.UserList(range(10))
        p3 = weakref.proxy(L3)
        self.assertEqual(L3[:], p3[:])
        self.assertEqual(L3[5:], p3[5:])
        self.assertEqual(L3[:5], p3[:5])
        self.assertEqual(L3[2:5], p3[2:5])

    def test_proxy_unicode(self):
        # See bug 5037
        klasse C(object):
            def __str__(self):
                gib "string"
            def __bytes__(self):
                gib b"bytes"
        instance = C()
        self.assertIn("__bytes__", dir(weakref.proxy(instance)))
        self.assertEqual(bytes(weakref.proxy(instance)), b"bytes")

    def test_proxy_index(self):
        klasse C:
            def __index__(self):
                gib 10
        o = C()
        p = weakref.proxy(o)
        self.assertEqual(operator.index(p), 10)

    def test_proxy_div(self):
        klasse C:
            def __floordiv__(self, other):
                gib 42
            def __ifloordiv__(self, other):
                gib 21
        o = C()
        p = weakref.proxy(o)
        self.assertEqual(p // 5, 42)
        p //= 5
        self.assertEqual(p, 21)

    def test_proxy_matmul(self):
        klasse C:
            def __matmul__(self, other):
                gib 1729
            def __rmatmul__(self, other):
                gib -163
            def __imatmul__(self, other):
                gib 561
        o = C()
        p = weakref.proxy(o)
        self.assertEqual(p @ 5, 1729)
        self.assertEqual(5 @ p, -163)
        p @= 5
        self.assertEqual(p, 561)

    # The PyWeakref_* C API is documented als allowing either NULL oder
    # Nichts als the value fuer the callback, where either means "no
    # callback".  The "no callback" ref und proxy objects are supposed
    # to be shared so long als they exist by all callers so long as
    # they are active.  In Python 2.3.3 und earlier, this guarantee
    # was nicht honored, und was broken in different ways for
    # PyWeakref_NewRef() und PyWeakref_NewProxy().  (Two tests.)

    def test_shared_ref_without_callback(self):
        self.check_shared_without_callback(weakref.ref)

    def test_shared_proxy_without_callback(self):
        self.check_shared_without_callback(weakref.proxy)

    def check_shared_without_callback(self, makeref):
        o = Object(1)
        p1 = makeref(o, Nichts)
        p2 = makeref(o, Nichts)
        self.assertIs(p1, p2, "both callbacks were Nichts in the C API")
        del p1, p2
        p1 = makeref(o)
        p2 = makeref(o, Nichts)
        self.assertIs(p1, p2, "callbacks were NULL, Nichts in the C API")
        del p1, p2
        p1 = makeref(o)
        p2 = makeref(o)
        self.assertIs(p1, p2, "both callbacks were NULL in the C API")
        del p1, p2
        p1 = makeref(o, Nichts)
        p2 = makeref(o)
        self.assertIs(p1, p2, "callbacks were Nichts, NULL in the C API")

    def test_callable_proxy(self):
        o = Callable()
        ref1 = weakref.proxy(o)

        self.check_proxy(o, ref1)

        self.assertIs(type(ref1), weakref.CallableProxyType,
                     "proxy is nicht of callable type")
        ref1('twinkies!')
        self.assertEqual(o.bar, 'twinkies!',
                     "call through proxy nicht passed through to original")
        ref1(x='Splat.')
        self.assertEqual(o.bar, 'Splat.',
                     "call through proxy nicht passed through to original")

        # expect due to too few args
        self.assertRaises(TypeError, ref1)

        # expect due to too many args
        self.assertRaises(TypeError, ref1, 1, 2, 3)

    def check_proxy(self, o, proxy):
        o.foo = 1
        self.assertEqual(proxy.foo, 1,
                     "proxy does nicht reflect attribute addition")
        o.foo = 2
        self.assertEqual(proxy.foo, 2,
                     "proxy does nicht reflect attribute modification")
        del o.foo
        self.assertNotHasAttr(proxy, 'foo',
                     "proxy does nicht reflect attribute removal")

        proxy.foo = 1
        self.assertEqual(o.foo, 1,
                     "object does nicht reflect attribute addition via proxy")
        proxy.foo = 2
        self.assertEqual(o.foo, 2,
            "object does nicht reflect attribute modification via proxy")
        del proxy.foo
        self.assertNotHasAttr(o, 'foo',
                     "object does nicht reflect attribute removal via proxy")

    def test_proxy_deletion(self):
        # Test clearing of SF bug #762891
        klasse Foo:
            result = Nichts
            def __delitem__(self, accessor):
                self.result = accessor
        g = Foo()
        f = weakref.proxy(g)
        del f[0]
        self.assertEqual(f.result, 0)

    def test_proxy_bool(self):
        # Test clearing of SF bug #1170766
        klasse List(list): pass
        lyst = List()
        self.assertEqual(bool(weakref.proxy(lyst)), bool(lyst))

    def test_proxy_iter(self):
        # Test fails mit a debug build of the interpreter
        # (see bpo-38395).

        obj = Nichts

        klasse MyObj:
            def __iter__(self):
                nonlocal obj
                del obj
                gib NotImplemented

        obj = MyObj()
        p = weakref.proxy(obj)
        mit self.assertRaises(TypeError):
            # "blech" in p calls MyObj.__iter__ through the proxy,
            # without keeping a reference to the real object, so it
            # can be killed in the middle of the call
            "blech" in p

    def test_proxy_next(self):
        arr = [4, 5, 6]
        def iterator_func():
            liefere von arr
        it = iterator_func()

        klasse IteratesWeakly:
            def __iter__(self):
                gib weakref.proxy(it)

        weak_it = IteratesWeakly()

        # Calls proxy.__next__
        self.assertEqual(list(weak_it), [4, 5, 6])

    def test_proxy_bad_next(self):
        # bpo-44720: PyIter_Next() shouldn't be called wenn the reference
        # isn't an iterator.

        not_an_iterator = lambda: 0

        klasse A:
            def __iter__(self):
                gib weakref.proxy(not_an_iterator)
        a = A()

        msg = "Weakref proxy referenced a non-iterator"
        mit self.assertRaisesRegex(TypeError, msg):
            list(a)

    def test_proxy_reversed(self):
        klasse MyObj:
            def __len__(self):
                gib 3
            def __reversed__(self):
                gib iter('cba')

        obj = MyObj()
        self.assertEqual("".join(reversed(weakref.proxy(obj))), "cba")

    def test_proxy_hash(self):
        klasse MyObj:
            def __hash__(self):
                gib 42

        obj = MyObj()
        mit self.assertRaises(TypeError):
            hash(weakref.proxy(obj))

        klasse MyObj:
            __hash__ = Nichts

        obj = MyObj()
        mit self.assertRaises(TypeError):
            hash(weakref.proxy(obj))

    def test_getweakrefcount(self):
        o = C()
        ref1 = weakref.ref(o)
        ref2 = weakref.ref(o, self.callback)
        self.assertEqual(weakref.getweakrefcount(o), 2,
                     "got wrong number of weak reference objects")

        proxy1 = weakref.proxy(o)
        proxy2 = weakref.proxy(o, self.callback)
        self.assertEqual(weakref.getweakrefcount(o), 4,
                     "got wrong number of weak reference objects")

        del ref1, ref2, proxy1, proxy2
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(weakref.getweakrefcount(o), 0,
                     "weak reference objects nicht unlinked from"
                     " referent when discarded.")

        # assumes ints do nicht support weakrefs
        self.assertEqual(weakref.getweakrefcount(1), 0,
                     "got wrong number of weak reference objects fuer int")

    def test_getweakrefs(self):
        o = C()
        ref1 = weakref.ref(o, self.callback)
        ref2 = weakref.ref(o, self.callback)
        del ref1
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(weakref.getweakrefs(o), [ref2],
                     "list of refs does nicht match")

        o = C()
        ref1 = weakref.ref(o, self.callback)
        ref2 = weakref.ref(o, self.callback)
        del ref2
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(weakref.getweakrefs(o), [ref1],
                     "list of refs does nicht match")

        del ref1
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(weakref.getweakrefs(o), [],
                     "list of refs nicht cleared")

        # assumes ints do nicht support weakrefs
        self.assertEqual(weakref.getweakrefs(1), [],
                     "list of refs does nicht match fuer int")

    def test_newstyle_number_ops(self):
        klasse F(float):
            pass
        f = F(2.0)
        p = weakref.proxy(f)
        self.assertEqual(p + 1.0, 3.0)
        self.assertEqual(1.0 + p, 3.0)  # this used to SEGV

    def test_callbacks_protected(self):
        # Callbacks protected von already-set exceptions?
        # Regression test fuer SF bug #478534.
        klasse BogusError(Exception):
            pass
        data = {}
        def remove(k):
            del data[k]
        def encapsulate():
            f = lambda : ()
            data[weakref.ref(f, remove)] = Nichts
            raise BogusError
        try:
            encapsulate()
        except BogusError:
            pass
        sonst:
            self.fail("exception nicht properly restored")
        try:
            encapsulate()
        except BogusError:
            pass
        sonst:
            self.fail("exception nicht properly restored")

    def test_sf_bug_840829(self):
        # "weakref callbacks und gc corrupt memory"
        # subtype_dealloc erroneously exposed a new-style instance
        # already in the process of getting deallocated to gc,
        # causing double-deallocation wenn the instance had a weakref
        # callback that triggered gc.
        # If the bug exists, there probably won't be an obvious symptom
        # in a release build.  In a debug build, a segfault will occur
        # when the second attempt to remove the instance von the "list
        # of all objects" occurs.

        importiere gc

        klasse C(object):
            pass

        c = C()
        wr = weakref.ref(c, lambda ignore: gc.collect())
        del c

        # There endeth the first part.  It gets worse.
        del wr

        c1 = C()
        c1.i = C()
        wr = weakref.ref(c1.i, lambda ignore: gc.collect())

        c2 = C()
        c2.c1 = c1
        del c1  # still alive because c2 points to it

        # Now when subtype_dealloc gets called on c2, it's nicht enough just
        # that c2 is immune von gc waehrend the weakref callbacks associated
        # mit c2 execute (there are none in this 2nd half of the test, btw).
        # subtype_dealloc goes on to call the base classes' deallocs too,
        # so any gc triggered by weakref callbacks associated mit anything
        # torn down by a base klasse dealloc can also trigger double
        # deallocation of c2.
        del c2

    def test_callback_in_cycle(self):
        importiere gc

        klasse J(object):
            pass

        klasse II(object):
            def acallback(self, ignore):
                self.J

        I = II()
        I.J = J
        I.wr = weakref.ref(J, I.acallback)

        # Now J und II are each in a self-cycle (as all new-style class
        # objects are, since their __mro__ points back to them).  I holds
        # both a weak reference (I.wr) und a strong reference (I.J) to class
        # J.  I is also in a cycle (I.wr points to a weakref that references
        # I.acallback).  When we del these three, they all become trash, but
        # the cycles prevent any of them von getting cleaned up immediately.
        # Instead they have to wait fuer cyclic gc to deduce that they're
        # trash.
        #
        # gc used to call tp_clear on all of them, und the order in which
        # it does that is pretty accidental.  The exact order in which we
        # built up these things manages to provoke gc into running tp_clear
        # in just the right order (I last).  Calling tp_clear on II leaves
        # behind an insane klasse object (its __mro__ becomes NULL).  Calling
        # tp_clear on J breaks its self-cycle, but J doesn't get deleted
        # just then because of the strong reference von I.J.  Calling
        # tp_clear on I starts to clear I's __dict__, und just happens to
        # clear I.J first -- I.wr is still intact.  That removes the last
        # reference to J, which triggers the weakref callback.  The callback
        # tries to do "self.J", und instances of new-style classes look up
        # attributes ("J") in the klasse dict first.  The klasse (II) wants to
        # search II.__mro__, but that's NULL.   The result was a segfault in
        # a release build, und an assert failure in a debug build.
        del I, J, II
        gc.collect()

    def test_callback_reachable_one_way(self):
        importiere gc

        # This one broke the first patch that fixed the previous test. In this case,
        # the objects reachable von the callback aren't also reachable
        # von the object (c1) *triggering* the callback:  you can get to
        # c1 von c2, but nicht vice-versa.  The result was that c2's __dict__
        # got tp_clear'ed by the time the c2.cb callback got invoked.

        klasse C:
            def cb(self, ignore):
                self.me
                self.c1
                self.wr

        c1, c2 = C(), C()

        c2.me = c2
        c2.c1 = c1
        c2.wr = weakref.ref(c1, c2.cb)

        del c1, c2
        gc.collect()

    def test_callback_different_classes(self):
        importiere gc

        # Like test_callback_reachable_one_way, except c2 und c1 have different
        # classes.  c2's klasse (C) isn't reachable von c1 then, so protecting
        # objects reachable von the dying object (c1) isn't enough to stop
        # c2's klasse (C) von getting tp_clear'ed before c2.cb is invoked.
        # The result was a segfault (C.__mro__ was NULL when the callback
        # tried to look up self.me).

        klasse C(object):
            def cb(self, ignore):
                self.me
                self.c1
                self.wr

        klasse D:
            pass

        c1, c2 = D(), C()

        c2.me = c2
        c2.c1 = c1
        c2.wr = weakref.ref(c1, c2.cb)

        del c1, c2, C, D
        gc.collect()

    def test_callback_in_cycle_resurrection(self):
        importiere gc

        # Do something nasty in a weakref callback:  resurrect objects
        # von dead cycles.  For this to be attempted, the weakref und
        # its callback must also be part of the cyclic trash (else the
        # objects reachable via the callback couldn't be in cyclic trash
        # to begin mit -- the callback would act like an external root).
        # But gc clears trash weakrefs mit callbacks early now, which
        # disables the callbacks, so the callbacks shouldn't get called
        # at all (and so nothing actually gets resurrected).

        alist = []
        klasse C(object):
            def __init__(self, value):
                self.attribute = value

            def acallback(self, ignore):
                alist.append(self.c)

        c1, c2 = C(1), C(2)
        c1.c = c2
        c2.c = c1
        c1.wr = weakref.ref(c2, c1.acallback)
        c2.wr = weakref.ref(c1, c2.acallback)

        def C_went_away(ignore):
            alist.append("C went away")
        wr = weakref.ref(C, C_went_away)

        del c1, c2, C   # make them all trash
        self.assertEqual(alist, [])  # del isn't enough to reclaim anything

        gc.collect()
        # c1.wr und c2.wr were part of the cyclic trash, so should have
        # been cleared without their callbacks executing.  OTOH, the weakref
        # to C is bound to a function local (wr), und wasn't trash, so that
        # callback should have been invoked when C went away.
        self.assertEqual(alist, ["C went away"])
        # The remaining weakref should be dead now (its callback ran).
        self.assertEqual(wr(), Nichts)

        del alist[:]
        gc.collect()
        self.assertEqual(alist, [])

    def test_callbacks_on_callback(self):
        importiere gc

        # Set up weakref callbacks *on* weakref callbacks.
        alist = []
        def safe_callback(ignore):
            alist.append("safe_callback called")

        klasse C(object):
            def cb(self, ignore):
                alist.append("cb called")

        c, d = C(), C()
        c.other = d
        d.other = c
        callback = c.cb
        c.wr = weakref.ref(d, callback)     # this won't trigger
        d.wr = weakref.ref(callback, d.cb)  # ditto
        external_wr = weakref.ref(callback, safe_callback)  # but this will
        self.assertIs(external_wr(), callback)

        # The weakrefs attached to c und d should get cleared, so that
        # C.cb is never called.  But external_wr isn't part of the cyclic
        # trash, und no cyclic trash is reachable von it, so safe_callback
        # should get invoked when the bound method object callback (c.cb)
        # -- which is itself a callback, und also part of the cyclic trash --
        # gets reclaimed at the end of gc.

        del callback, c, d, C
        self.assertEqual(alist, [])  # del isn't enough to clean up cycles
        gc.collect()
        self.assertEqual(alist, ["safe_callback called"])
        self.assertEqual(external_wr(), Nichts)

        del alist[:]
        gc.collect()
        self.assertEqual(alist, [])

    def test_gc_during_ref_creation(self):
        self.check_gc_during_creation(weakref.ref)

    def test_gc_during_proxy_creation(self):
        self.check_gc_during_creation(weakref.proxy)

    def check_gc_during_creation(self, makeref):
        thresholds = gc.get_threshold()
        gc.set_threshold(1, 1, 1)
        gc.collect()
        klasse A:
            pass

        def callback(*args):
            pass

        referenced = A()

        a = A()
        a.a = a
        a.wr = makeref(referenced)

        try:
            # now make sure the object und the ref get labeled as
            # cyclic trash:
            a = A()
            weakref.ref(referenced, callback)

        finally:
            gc.set_threshold(*thresholds)

    def test_ref_created_during_del(self):
        # Bug #1377858
        # A weakref created in an object's __del__() would crash the
        # interpreter when the weakref was cleaned up since it would refer to
        # non-existent memory.  This test should nicht segfault the interpreter.
        klasse Target(object):
            def __del__(self):
                global ref_from_del
                ref_from_del = weakref.ref(self)

        w = Target()

    def test_init(self):
        # Issue 3634
        # <weakref to class>.__init__() doesn't check errors correctly
        r = weakref.ref(Exception)
        self.assertRaises(TypeError, r.__init__, 0, 0, 0, 0, 0)
        # No exception should be raised here
        gc.collect()

    def test_classes(self):
        # Check that classes are weakrefable.
        klasse A(object):
            pass
        l = []
        weakref.ref(int)
        a = weakref.ref(A, l.append)
        A = Nichts
        gc.collect()
        self.assertEqual(a(), Nichts)
        self.assertEqual(l, [a])

    def test_equality(self):
        # Alive weakrefs defer equality testing to their underlying object.
        x = Object(1)
        y = Object(1)
        z = Object(2)
        a = weakref.ref(x)
        b = weakref.ref(y)
        c = weakref.ref(z)
        d = weakref.ref(x)
        # Note how we directly test the operators here, to stress both
        # __eq__ und __ne__.
        self.assertWahr(a == b)
        self.assertFalsch(a != b)
        self.assertFalsch(a == c)
        self.assertWahr(a != c)
        self.assertWahr(a == d)
        self.assertFalsch(a != d)
        self.assertFalsch(a == x)
        self.assertWahr(a != x)
        self.assertWahr(a == ALWAYS_EQ)
        self.assertFalsch(a != ALWAYS_EQ)
        del x, y, z
        gc.collect()
        fuer r in a, b, c:
            # Sanity check
            self.assertIs(r(), Nichts)
        # Dead weakrefs compare by identity: whether `a` und `d` are the
        # same weakref object is an implementation detail, since they pointed
        # to the same original object und didn't have a callback.
        # (see issue #16453).
        self.assertFalsch(a == b)
        self.assertWahr(a != b)
        self.assertFalsch(a == c)
        self.assertWahr(a != c)
        self.assertEqual(a == d, a is d)
        self.assertEqual(a != d, a is nicht d)

    def test_ordering(self):
        # weakrefs cannot be ordered, even wenn the underlying objects can.
        ops = [operator.lt, operator.gt, operator.le, operator.ge]
        x = Object(1)
        y = Object(1)
        a = weakref.ref(x)
        b = weakref.ref(y)
        fuer op in ops:
            self.assertRaises(TypeError, op, a, b)
        # Same when dead.
        del x, y
        gc.collect()
        fuer op in ops:
            self.assertRaises(TypeError, op, a, b)

    def test_hashing(self):
        # Alive weakrefs hash the same als the underlying object
        x = Object(42)
        y = Object(42)
        a = weakref.ref(x)
        b = weakref.ref(y)
        self.assertEqual(hash(a), hash(42))
        del x, y
        gc.collect()
        # Dead weakrefs:
        # - retain their hash is they were hashed when alive;
        # - otherwise, cannot be hashed.
        self.assertEqual(hash(a), hash(42))
        self.assertRaises(TypeError, hash, b)

    @unittest.skipIf(is_wasi und Py_DEBUG, "requires deep stack")
    def test_trashcan_16602(self):
        # Issue #16602: when a weakref's target was part of a long
        # deallocation chain, the trashcan mechanism could delay clearing
        # of the weakref und make the target object visible von outside
        # code even though its refcount had dropped to 0.  A crash ensued.
        klasse C:
            def __init__(self, parent):
                wenn nicht parent:
                    gib
                wself = weakref.ref(self)
                def cb(wparent):
                    o = wself()
                self.wparent = weakref.ref(parent, cb)

        d = weakref.WeakKeyDictionary()
        root = c = C(Nichts)
        fuer n in range(100):
            d[c] = c = C(c)
        del root
        gc.collect()

    def test_callback_attribute(self):
        x = Object(1)
        callback = lambda ref: Nichts
        ref1 = weakref.ref(x, callback)
        self.assertIs(ref1.__callback__, callback)

        ref2 = weakref.ref(x)
        self.assertIsNichts(ref2.__callback__)

    def test_callback_attribute_after_deletion(self):
        x = Object(1)
        ref = weakref.ref(x, self.callback)
        self.assertIsNotNichts(ref.__callback__)
        del x
        support.gc_collect()
        self.assertIsNichts(ref.__callback__)

    def test_set_callback_attribute(self):
        x = Object(1)
        callback = lambda ref: Nichts
        ref1 = weakref.ref(x, callback)
        mit self.assertRaises(AttributeError):
            ref1.__callback__ = lambda ref: Nichts

    def test_callback_gcs(self):
        klasse ObjectWithDel(Object):
            def __del__(self): pass
        x = ObjectWithDel(1)
        ref1 = weakref.ref(x, lambda ref: support.gc_collect())
        del x
        support.gc_collect()

    @support.cpython_only
    def test_no_memory_when_clearing(self):
        # gh-118331: Make sure we do nicht raise an exception von the destructor
        # when clearing weakrefs wenn allocating the intermediate tuple fails.
        code = textwrap.dedent("""
        importiere _testcapi
        importiere weakref

        klasse TestObj:
            pass

        def callback(obj):
            pass

        obj = TestObj()
        # The choice of 50 is arbitrary, but must be large enough to ensure
        # the allocation won't be serviced by the free list.
        wrs = [weakref.ref(obj, callback) fuer _ in range(50)]
        _testcapi.set_nomemory(0)
        del obj
        """).strip()
        res, _ = script_helper.run_python_until_end("-c", code)
        stderr = res.err.decode("ascii", "backslashreplace")
        self.assertNotRegex(stderr, "_Py_Dealloc: Deallocator of type 'TestObj'")

    def test_clearing_weakrefs_in_gc(self):
        # This test checks that when finalizers are called:
        # 1. weakrefs mit callbacks have been cleared
        # 2. weakrefs without callbacks have nicht been cleared
        errors = []
        def test():
            klasse Class:
                def __init__(self):
                    self._self = self
                    self.wr1 = weakref.ref(Class, lambda x: Nichts)
                    self.wr2 = weakref.ref(Class)

                def __del__(self):
                    # we can't use assert* here, because gc will swallow
                    # exceptions
                    wenn self.wr1() is nicht Nichts:
                        errors.append("weakref mit callback als cleared")
                    wenn self.wr2() is nicht Class:
                        errors.append("weakref without callback was cleared")

            Class()

        test()
        gc.collect()
        self.assertEqual(errors, [])


klasse SubclassableWeakrefTestCase(TestBase):

    def test_subclass_refs(self):
        klasse MyRef(weakref.ref):
            def __init__(self, ob, callback=Nichts, value=42):
                self.value = value
                super().__init__(ob, callback)
            def __call__(self):
                self.called = Wahr
                gib super().__call__()
        o = Object("foo")
        mr = MyRef(o, value=24)
        self.assertIs(mr(), o)
        self.assertWahr(mr.called)
        self.assertEqual(mr.value, 24)
        del o
        gc_collect()  # For PyPy oder other GCs.
        self.assertIsNichts(mr())
        self.assertWahr(mr.called)

    def test_subclass_refs_dont_replace_standard_refs(self):
        klasse MyRef(weakref.ref):
            pass
        o = Object(42)
        r1 = MyRef(o)
        r2 = weakref.ref(o)
        self.assertIsNot(r1, r2)
        self.assertEqual(weakref.getweakrefs(o), [r2, r1])
        self.assertEqual(weakref.getweakrefcount(o), 2)
        r3 = MyRef(o)
        self.assertEqual(weakref.getweakrefcount(o), 3)
        refs = weakref.getweakrefs(o)
        self.assertEqual(len(refs), 3)
        self.assertIs(r2, refs[0])
        self.assertIn(r1, refs[1:])
        self.assertIn(r3, refs[1:])

    def test_subclass_refs_dont_conflate_callbacks(self):
        klasse MyRef(weakref.ref):
            pass
        o = Object(42)
        r1 = MyRef(o, id)
        r2 = MyRef(o, str)
        self.assertIsNot(r1, r2)
        refs = weakref.getweakrefs(o)
        self.assertIn(r1, refs)
        self.assertIn(r2, refs)

    def test_subclass_refs_with_slots(self):
        klasse MyRef(weakref.ref):
            __slots__ = "slot1", "slot2"
            def __new__(type, ob, callback, slot1, slot2):
                gib weakref.ref.__new__(type, ob, callback)
            def __init__(self, ob, callback, slot1, slot2):
                self.slot1 = slot1
                self.slot2 = slot2
            def meth(self):
                gib self.slot1 + self.slot2
        o = Object(42)
        r = MyRef(o, Nichts, "abc", "def")
        self.assertEqual(r.slot1, "abc")
        self.assertEqual(r.slot2, "def")
        self.assertEqual(r.meth(), "abcdef")
        self.assertNotHasAttr(r, "__dict__")

    def test_subclass_refs_with_cycle(self):
        """Confirm https://bugs.python.org/issue3100 is fixed."""
        # An instance of a weakref subclass can have attributes.
        # If such a weakref holds the only strong reference to the object,
        # deleting the weakref will delete the object. In this case,
        # the callback must nicht be called, because the ref object is
        # being deleted.
        klasse MyRef(weakref.ref):
            pass

        # Use a local callback, fuer "regrtest -R::"
        # to detect refcounting problems
        def callback(w):
            self.cbcalled += 1

        o = C()
        r1 = MyRef(o, callback)
        r1.o = o
        del o

        del r1 # Used to crash here

        self.assertEqual(self.cbcalled, 0)

        # Same test, mit two weakrefs to the same object
        # (since code paths are different)
        o = C()
        r1 = MyRef(o, callback)
        r2 = MyRef(o, callback)
        r1.r = r2
        r2.o = o
        del o
        del r2

        del r1 # Used to crash here

        self.assertEqual(self.cbcalled, 0)


klasse WeakMethodTestCase(unittest.TestCase):

    def _subclass(self):
        """Return an Object subclass overriding `some_method`."""
        klasse C(Object):
            def some_method(self):
                gib 6
        gib C

    def test_alive(self):
        o = Object(1)
        r = weakref.WeakMethod(o.some_method)
        self.assertIsInstance(r, weakref.ReferenceType)
        self.assertIsInstance(r(), type(o.some_method))
        self.assertIs(r().__self__, o)
        self.assertIs(r().__func__, o.some_method.__func__)
        self.assertEqual(r()(), 4)

    def test_object_dead(self):
        o = Object(1)
        r = weakref.WeakMethod(o.some_method)
        del o
        gc.collect()
        self.assertIs(r(), Nichts)

    def test_method_dead(self):
        C = self._subclass()
        o = C(1)
        r = weakref.WeakMethod(o.some_method)
        del C.some_method
        gc.collect()
        self.assertIs(r(), Nichts)

    def test_callback_when_object_dead(self):
        # Test callback behaviour when object dies first.
        C = self._subclass()
        calls = []
        def cb(arg):
            calls.append(arg)
        o = C(1)
        r = weakref.WeakMethod(o.some_method, cb)
        del o
        gc.collect()
        self.assertEqual(calls, [r])
        # Callback is only called once.
        C.some_method = Object.some_method
        gc.collect()
        self.assertEqual(calls, [r])

    def test_callback_when_method_dead(self):
        # Test callback behaviour when method dies first.
        C = self._subclass()
        calls = []
        def cb(arg):
            calls.append(arg)
        o = C(1)
        r = weakref.WeakMethod(o.some_method, cb)
        del C.some_method
        gc.collect()
        self.assertEqual(calls, [r])
        # Callback is only called once.
        del o
        gc.collect()
        self.assertEqual(calls, [r])

    @support.cpython_only
    def test_no_cycles(self):
        # A WeakMethod doesn't create any reference cycle to itself.
        o = Object(1)
        def cb(_):
            pass
        r = weakref.WeakMethod(o.some_method, cb)
        wr = weakref.ref(r)
        del r
        self.assertIs(wr(), Nichts)

    def test_equality(self):
        def _eq(a, b):
            self.assertWahr(a == b)
            self.assertFalsch(a != b)
        def _ne(a, b):
            self.assertWahr(a != b)
            self.assertFalsch(a == b)
        x = Object(1)
        y = Object(1)
        a = weakref.WeakMethod(x.some_method)
        b = weakref.WeakMethod(y.some_method)
        c = weakref.WeakMethod(x.other_method)
        d = weakref.WeakMethod(y.other_method)
        # Objects equal, same method
        _eq(a, b)
        _eq(c, d)
        # Objects equal, different method
        _ne(a, c)
        _ne(a, d)
        _ne(b, c)
        _ne(b, d)
        # Objects unequal, same oder different method
        z = Object(2)
        e = weakref.WeakMethod(z.some_method)
        f = weakref.WeakMethod(z.other_method)
        _ne(a, e)
        _ne(a, f)
        _ne(b, e)
        _ne(b, f)
        # Compare mit different types
        _ne(a, x.some_method)
        _eq(a, ALWAYS_EQ)
        del x, y, z
        gc.collect()
        # Dead WeakMethods compare by identity
        refs = a, b, c, d, e, f
        fuer q in refs:
            fuer r in refs:
                self.assertEqual(q == r, q is r)
                self.assertEqual(q != r, q is nicht r)

    def test_hashing(self):
        # Alive WeakMethods are hashable wenn the underlying object is
        # hashable.
        x = Object(1)
        y = Object(1)
        a = weakref.WeakMethod(x.some_method)
        b = weakref.WeakMethod(y.some_method)
        c = weakref.WeakMethod(y.other_method)
        # Since WeakMethod objects are equal, the hashes should be equal.
        self.assertEqual(hash(a), hash(b))
        ha = hash(a)
        # Dead WeakMethods retain their old hash value
        del x, y
        gc.collect()
        self.assertEqual(hash(a), ha)
        self.assertEqual(hash(b), ha)
        # If it wasn't hashed when alive, a dead WeakMethod cannot be hashed.
        self.assertRaises(TypeError, hash, c)


klasse MappingTestCase(TestBase):

    COUNT = 10

    wenn support.check_sanitizer(thread=Wahr) und support.Py_GIL_DISABLED:
        # Reduce iteration count to get acceptable latency
        NUM_THREADED_ITERATIONS = 1000
    sonst:
        NUM_THREADED_ITERATIONS = 100000

    def check_len_cycles(self, dict_type, cons):
        N = 20
        items = [RefCycle() fuer i in range(N)]
        dct = dict_type(cons(o) fuer o in items)
        # Keep an iterator alive
        it = dct.items()
        try:
            next(it)
        except StopIteration:
            pass
        del items
        gc.collect()
        n1 = len(dct)
        del it
        gc.collect()
        n2 = len(dct)
        # one item may be kept alive inside the iterator
        self.assertIn(n1, (0, 1))
        self.assertEqual(n2, 0)

    def test_weak_keyed_len_cycles(self):
        self.check_len_cycles(weakref.WeakKeyDictionary, lambda k: (k, 1))

    def test_weak_valued_len_cycles(self):
        self.check_len_cycles(weakref.WeakValueDictionary, lambda k: (1, k))

    def check_len_race(self, dict_type, cons):
        # Extended sanity checks fuer len() in the face of cyclic collection
        self.addCleanup(gc.set_threshold, *gc.get_threshold())
        fuer th in range(1, 100):
            N = 20
            gc.collect(0)
            gc.set_threshold(th, th, th)
            items = [RefCycle() fuer i in range(N)]
            dct = dict_type(cons(o) fuer o in items)
            del items
            # All items will be collected at next garbage collection pass
            it = dct.items()
            try:
                next(it)
            except StopIteration:
                pass
            n1 = len(dct)
            del it
            n2 = len(dct)
            self.assertGreaterEqual(n1, 0)
            self.assertLessEqual(n1, N)
            self.assertGreaterEqual(n2, 0)
            self.assertLessEqual(n2, n1)

    def test_weak_keyed_len_race(self):
        self.check_len_race(weakref.WeakKeyDictionary, lambda k: (k, 1))

    def test_weak_valued_len_race(self):
        self.check_len_race(weakref.WeakValueDictionary, lambda k: (1, k))

    def test_weak_values(self):
        #
        #  This exercises d.copy(), d.items(), d[], del d[], len(d).
        #
        dict, objects = self.make_weak_valued_dict()
        fuer o in objects:
            self.assertEqual(weakref.getweakrefcount(o), 1)
            self.assertIs(o, dict[o.arg],
                         "wrong object returned by weak dict!")
        items1 = list(dict.items())
        items2 = list(dict.copy().items())
        items1.sort()
        items2.sort()
        self.assertEqual(items1, items2,
                     "cloning of weak-valued dictionary did nicht work!")
        del items1, items2
        self.assertEqual(len(dict), self.COUNT)
        del objects[0]
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(dict), self.COUNT - 1,
                     "deleting object did nicht cause dictionary update")
        del objects, o
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(dict), 0,
                     "deleting the values did nicht clear the dictionary")
        # regression on SF bug #447152:
        dict = weakref.WeakValueDictionary()
        self.assertRaises(KeyError, dict.__getitem__, 1)
        dict[2] = C()
        gc_collect()  # For PyPy oder other GCs.
        self.assertRaises(KeyError, dict.__getitem__, 2)

    def test_weak_keys(self):
        #
        #  This exercises d.copy(), d.items(), d[] = v, d[], del d[],
        #  len(d), k in d.
        #
        dict, objects = self.make_weak_keyed_dict()
        fuer o in objects:
            self.assertEqual(weakref.getweakrefcount(o), 1,
                         "wrong number of weak references to %r!" % o)
            self.assertIs(o.arg, dict[o],
                         "wrong object returned by weak dict!")
        items1 = dict.items()
        items2 = dict.copy().items()
        self.assertEqual(set(items1), set(items2),
                     "cloning of weak-keyed dictionary did nicht work!")
        del items1, items2
        self.assertEqual(len(dict), self.COUNT)
        del objects[0]
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(dict), (self.COUNT - 1),
                     "deleting object did nicht cause dictionary update")
        del objects, o
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(dict), 0,
                     "deleting the keys did nicht clear the dictionary")
        o = Object(42)
        dict[o] = "What is the meaning of the universe?"
        self.assertIn(o, dict)
        self.assertNotIn(34, dict)

    def test_weak_keyed_iters(self):
        dict, objects = self.make_weak_keyed_dict()
        self.check_iters(dict)

        # Test keyrefs()
        refs = dict.keyrefs()
        self.assertEqual(len(refs), len(objects))
        objects2 = list(objects)
        fuer wr in refs:
            ob = wr()
            self.assertIn(ob, dict)
            self.assertIn(ob, dict)
            self.assertEqual(ob.arg, dict[ob])
            objects2.remove(ob)
        self.assertEqual(len(objects2), 0)

        # Test iterkeyrefs()
        objects2 = list(objects)
        self.assertEqual(len(list(dict.keyrefs())), len(objects))
        fuer wr in dict.keyrefs():
            ob = wr()
            self.assertIn(ob, dict)
            self.assertIn(ob, dict)
            self.assertEqual(ob.arg, dict[ob])
            objects2.remove(ob)
        self.assertEqual(len(objects2), 0)

    def test_weak_valued_iters(self):
        dict, objects = self.make_weak_valued_dict()
        self.check_iters(dict)

        # Test valuerefs()
        refs = dict.valuerefs()
        self.assertEqual(len(refs), len(objects))
        objects2 = list(objects)
        fuer wr in refs:
            ob = wr()
            self.assertEqual(ob, dict[ob.arg])
            self.assertEqual(ob.arg, dict[ob.arg].arg)
            objects2.remove(ob)
        self.assertEqual(len(objects2), 0)

        # Test itervaluerefs()
        objects2 = list(objects)
        self.assertEqual(len(list(dict.itervaluerefs())), len(objects))
        fuer wr in dict.itervaluerefs():
            ob = wr()
            self.assertEqual(ob, dict[ob.arg])
            self.assertEqual(ob.arg, dict[ob.arg].arg)
            objects2.remove(ob)
        self.assertEqual(len(objects2), 0)

    def check_iters(self, dict):
        # item iterator:
        items = list(dict.items())
        fuer item in dict.items():
            items.remove(item)
        self.assertFalsch(items, "items() did nicht touch all items")

        # key iterator, via __iter__():
        keys = list(dict.keys())
        fuer k in dict:
            keys.remove(k)
        self.assertFalsch(keys, "__iter__() did nicht touch all keys")

        # key iterator, via iterkeys():
        keys = list(dict.keys())
        fuer k in dict.keys():
            keys.remove(k)
        self.assertFalsch(keys, "iterkeys() did nicht touch all keys")

        # value iterator:
        values = list(dict.values())
        fuer v in dict.values():
            values.remove(v)
        self.assertFalsch(values,
                     "itervalues() did nicht touch all values")

    def check_weak_destroy_while_iterating(self, dict, objects, iter_name):
        n = len(dict)
        it = iter(getattr(dict, iter_name)())
        next(it)             # Trigger internal iteration
        # Destroy an object
        del objects[-1]
        gc.collect()    # just in case
        # We have removed either the first consumed object, oder another one
        self.assertIn(len(list(it)), [len(objects), len(objects) - 1])
        del it
        # The removal has been committed
        self.assertEqual(len(dict), n - 1)

    def check_weak_destroy_and_mutate_while_iterating(self, dict, testcontext):
        # Check that we can explicitly mutate the weak dict without
        # interfering mit delayed removal.
        # `testcontext` should create an iterator, destroy one of the
        # weakref'ed objects und then gib a new key/value pair corresponding
        # to the destroyed object.
        mit testcontext() als (k, v):
            self.assertNotIn(k, dict)
        mit testcontext() als (k, v):
            self.assertRaises(KeyError, dict.__delitem__, k)
        self.assertNotIn(k, dict)
        mit testcontext() als (k, v):
            self.assertRaises(KeyError, dict.pop, k)
        self.assertNotIn(k, dict)
        mit testcontext() als (k, v):
            dict[k] = v
        self.assertEqual(dict[k], v)
        ddict = copy.copy(dict)
        mit testcontext() als (k, v):
            dict.update(ddict)
        self.assertEqual(dict, ddict)
        mit testcontext() als (k, v):
            dict.clear()
        self.assertEqual(len(dict), 0)

    def check_weak_del_and_len_while_iterating(self, dict, testcontext):
        # Check that len() works when both iterating und removing keys
        # explicitly through various means (.pop(), .clear()...), while
        # implicit mutation is deferred because an iterator is alive.
        # (each call to testcontext() should schedule one item fuer removal
        #  fuer this test to work properly)
        o = Object(123456)
        mit testcontext():
            n = len(dict)
            # Since underlying dict is ordered, first item is popped
            dict.pop(next(dict.keys()))
            self.assertEqual(len(dict), n - 1)
            dict[o] = o
            self.assertEqual(len(dict), n)
        # last item in objects is removed von dict in context shutdown
        mit testcontext():
            self.assertEqual(len(dict), n - 1)
            # Then, (o, o) is popped
            dict.popitem()
            self.assertEqual(len(dict), n - 2)
        mit testcontext():
            self.assertEqual(len(dict), n - 3)
            del dict[next(dict.keys())]
            self.assertEqual(len(dict), n - 4)
        mit testcontext():
            self.assertEqual(len(dict), n - 5)
            dict.popitem()
            self.assertEqual(len(dict), n - 6)
        mit testcontext():
            dict.clear()
            self.assertEqual(len(dict), 0)
        self.assertEqual(len(dict), 0)

    def test_weak_keys_destroy_while_iterating(self):
        # Issue #7105: iterators shouldn't crash when a key is implicitly removed
        dict, objects = self.make_weak_keyed_dict()
        self.check_weak_destroy_while_iterating(dict, objects, 'keys')
        self.check_weak_destroy_while_iterating(dict, objects, 'items')
        self.check_weak_destroy_while_iterating(dict, objects, 'values')
        self.check_weak_destroy_while_iterating(dict, objects, 'keyrefs')
        dict, objects = self.make_weak_keyed_dict()
        @contextlib.contextmanager
        def testcontext():
            try:
                it = iter(dict.items())
                next(it)
                # Schedule a key/value fuer removal und recreate it
                v = objects.pop().arg
                gc.collect()      # just in case
                liefere Object(v), v
            finally:
                it = Nichts           # should commit all removals
                gc.collect()
        self.check_weak_destroy_and_mutate_while_iterating(dict, testcontext)
        # Issue #21173: len() fragile when keys are both implicitly und
        # explicitly removed.
        dict, objects = self.make_weak_keyed_dict()
        self.check_weak_del_and_len_while_iterating(dict, testcontext)

    def test_weak_values_destroy_while_iterating(self):
        # Issue #7105: iterators shouldn't crash when a key is implicitly removed
        dict, objects = self.make_weak_valued_dict()
        self.check_weak_destroy_while_iterating(dict, objects, 'keys')
        self.check_weak_destroy_while_iterating(dict, objects, 'items')
        self.check_weak_destroy_while_iterating(dict, objects, 'values')
        self.check_weak_destroy_while_iterating(dict, objects, 'itervaluerefs')
        self.check_weak_destroy_while_iterating(dict, objects, 'valuerefs')
        dict, objects = self.make_weak_valued_dict()
        @contextlib.contextmanager
        def testcontext():
            try:
                it = iter(dict.items())
                next(it)
                # Schedule a key/value fuer removal und recreate it
                k = objects.pop().arg
                gc.collect()      # just in case
                liefere k, Object(k)
            finally:
                it = Nichts           # should commit all removals
                gc.collect()
        self.check_weak_destroy_and_mutate_while_iterating(dict, testcontext)
        dict, objects = self.make_weak_valued_dict()
        self.check_weak_del_and_len_while_iterating(dict, testcontext)

    def test_make_weak_keyed_dict_from_dict(self):
        o = Object(3)
        dict = weakref.WeakKeyDictionary({o:364})
        self.assertEqual(dict[o], 364)

    def test_make_weak_keyed_dict_from_weak_keyed_dict(self):
        o = Object(3)
        dict = weakref.WeakKeyDictionary({o:364})
        dict2 = weakref.WeakKeyDictionary(dict)
        self.assertEqual(dict[o], 364)

    def make_weak_keyed_dict(self):
        dict = weakref.WeakKeyDictionary()
        objects = list(map(Object, range(self.COUNT)))
        fuer o in objects:
            dict[o] = o.arg
        gib dict, objects

    def test_make_weak_valued_dict_from_dict(self):
        o = Object(3)
        dict = weakref.WeakValueDictionary({364:o})
        self.assertEqual(dict[364], o)

    def test_make_weak_valued_dict_from_weak_valued_dict(self):
        o = Object(3)
        dict = weakref.WeakValueDictionary({364:o})
        dict2 = weakref.WeakValueDictionary(dict)
        self.assertEqual(dict[364], o)

    def test_make_weak_valued_dict_misc(self):
        # errors
        self.assertRaises(TypeError, weakref.WeakValueDictionary.__init__)
        self.assertRaises(TypeError, weakref.WeakValueDictionary, {}, {})
        self.assertRaises(TypeError, weakref.WeakValueDictionary, (), ())
        # special keyword arguments
        o = Object(3)
        fuer kw in 'self', 'dict', 'other', 'iterable':
            d = weakref.WeakValueDictionary(**{kw: o})
            self.assertEqual(list(d.keys()), [kw])
            self.assertEqual(d[kw], o)

    def make_weak_valued_dict(self):
        dict = weakref.WeakValueDictionary()
        objects = list(map(Object, range(self.COUNT)))
        fuer o in objects:
            dict[o.arg] = o
        gib dict, objects

    def check_popitem(self, klass, key1, value1, key2, value2):
        weakdict = klass()
        weakdict[key1] = value1
        weakdict[key2] = value2
        self.assertEqual(len(weakdict), 2)
        k, v = weakdict.popitem()
        self.assertEqual(len(weakdict), 1)
        wenn k is key1:
            self.assertIs(v, value1)
        sonst:
            self.assertIs(v, value2)
        k, v = weakdict.popitem()
        self.assertEqual(len(weakdict), 0)
        wenn k is key1:
            self.assertIs(v, value1)
        sonst:
            self.assertIs(v, value2)

    def test_weak_valued_dict_popitem(self):
        self.check_popitem(weakref.WeakValueDictionary,
                           "key1", C(), "key2", C())

    def test_weak_keyed_dict_popitem(self):
        self.check_popitem(weakref.WeakKeyDictionary,
                           C(), "value 1", C(), "value 2")

    def check_setdefault(self, klass, key, value1, value2):
        self.assertIsNot(value1, value2,
                     "invalid test"
                     " -- value parameters must be distinct objects")
        weakdict = klass()
        o = weakdict.setdefault(key, value1)
        self.assertIs(o, value1)
        self.assertIn(key, weakdict)
        self.assertIs(weakdict.get(key), value1)
        self.assertIs(weakdict[key], value1)

        o = weakdict.setdefault(key, value2)
        self.assertIs(o, value1)
        self.assertIn(key, weakdict)
        self.assertIs(weakdict.get(key), value1)
        self.assertIs(weakdict[key], value1)

    def test_weak_valued_dict_setdefault(self):
        self.check_setdefault(weakref.WeakValueDictionary,
                              "key", C(), C())

    def test_weak_keyed_dict_setdefault(self):
        self.check_setdefault(weakref.WeakKeyDictionary,
                              C(), "value 1", "value 2")

    def check_update(self, klass, dict):
        #
        #  This exercises d.update(), len(d), d.keys(), k in d,
        #  d.get(), d[].
        #
        weakdict = klass()
        weakdict.update(dict)
        self.assertEqual(len(weakdict), len(dict))
        fuer k in weakdict.keys():
            self.assertIn(k, dict, "mysterious new key appeared in weak dict")
            v = dict.get(k)
            self.assertIs(v, weakdict[k])
            self.assertIs(v, weakdict.get(k))
        fuer k in dict.keys():
            self.assertIn(k, weakdict, "original key disappeared in weak dict")
            v = dict[k]
            self.assertIs(v, weakdict[k])
            self.assertIs(v, weakdict.get(k))

    def test_weak_valued_dict_update(self):
        self.check_update(weakref.WeakValueDictionary,
                          {1: C(), 'a': C(), C(): C()})
        # errors
        self.assertRaises(TypeError, weakref.WeakValueDictionary.update)
        d = weakref.WeakValueDictionary()
        self.assertRaises(TypeError, d.update, {}, {})
        self.assertRaises(TypeError, d.update, (), ())
        self.assertEqual(list(d.keys()), [])
        # special keyword arguments
        o = Object(3)
        fuer kw in 'self', 'dict', 'other', 'iterable':
            d = weakref.WeakValueDictionary()
            d.update(**{kw: o})
            self.assertEqual(list(d.keys()), [kw])
            self.assertEqual(d[kw], o)

    def test_weak_valued_union_operators(self):
        a = C()
        b = C()
        c = C()
        wvd1 = weakref.WeakValueDictionary({1: a})
        wvd2 = weakref.WeakValueDictionary({1: b, 2: a})
        wvd3 = wvd1.copy()
        d1 = {1: c, 3: b}
        pairs = [(5, c), (6, b)]

        tmp1 = wvd1 | wvd2 # Between two WeakValueDictionaries
        self.assertEqual(dict(tmp1), dict(wvd1) | dict(wvd2))
        self.assertIs(type(tmp1), weakref.WeakValueDictionary)
        wvd1 |= wvd2
        self.assertEqual(wvd1, tmp1)

        tmp2 = wvd2 | d1 # Between WeakValueDictionary und mapping
        self.assertEqual(dict(tmp2), dict(wvd2) | d1)
        self.assertIs(type(tmp2), weakref.WeakValueDictionary)
        wvd2 |= d1
        self.assertEqual(wvd2, tmp2)

        tmp3 = wvd3.copy() # Between WeakValueDictionary und iterable key, value
        tmp3 |= pairs
        self.assertEqual(dict(tmp3), dict(wvd3) | dict(pairs))
        self.assertIs(type(tmp3), weakref.WeakValueDictionary)

        tmp4 = d1 | wvd3 # Testing .__ror__
        self.assertEqual(dict(tmp4), d1 | dict(wvd3))
        self.assertIs(type(tmp4), weakref.WeakValueDictionary)

        del a
        self.assertNotIn(2, tmp1)
        self.assertNotIn(2, tmp2)
        self.assertNotIn(1, tmp3)
        self.assertNotIn(1, tmp4)

    def test_weak_keyed_dict_update(self):
        self.check_update(weakref.WeakKeyDictionary,
                          {C(): 1, C(): 2, C(): 3})

    def test_weak_keyed_delitem(self):
        d = weakref.WeakKeyDictionary()
        o1 = Object('1')
        o2 = Object('2')
        d[o1] = 'something'
        d[o2] = 'something'
        self.assertEqual(len(d), 2)
        del d[o1]
        self.assertEqual(len(d), 1)
        self.assertEqual(list(d.keys()), [o2])

    def test_weak_keyed_union_operators(self):
        o1 = C()
        o2 = C()
        o3 = C()
        wkd1 = weakref.WeakKeyDictionary({o1: 1, o2: 2})
        wkd2 = weakref.WeakKeyDictionary({o3: 3, o1: 4})
        wkd3 = wkd1.copy()
        d1 = {o2: '5', o3: '6'}
        pairs = [(o2, 7), (o3, 8)]

        tmp1 = wkd1 | wkd2 # Between two WeakKeyDictionaries
        self.assertEqual(dict(tmp1), dict(wkd1) | dict(wkd2))
        self.assertIs(type(tmp1), weakref.WeakKeyDictionary)
        wkd1 |= wkd2
        self.assertEqual(wkd1, tmp1)

        tmp2 = wkd2 | d1 # Between WeakKeyDictionary und mapping
        self.assertEqual(dict(tmp2), dict(wkd2) | d1)
        self.assertIs(type(tmp2), weakref.WeakKeyDictionary)
        wkd2 |= d1
        self.assertEqual(wkd2, tmp2)

        tmp3 = wkd3.copy() # Between WeakKeyDictionary und iterable key, value
        tmp3 |= pairs
        self.assertEqual(dict(tmp3), dict(wkd3) | dict(pairs))
        self.assertIs(type(tmp3), weakref.WeakKeyDictionary)

        tmp4 = d1 | wkd3 # Testing .__ror__
        self.assertEqual(dict(tmp4), d1 | dict(wkd3))
        self.assertIs(type(tmp4), weakref.WeakKeyDictionary)

        del o1
        self.assertNotIn(4, tmp1.values())
        self.assertNotIn(4, tmp2.values())
        self.assertNotIn(1, tmp3.values())
        self.assertNotIn(1, tmp4.values())

    def test_weak_valued_delitem(self):
        d = weakref.WeakValueDictionary()
        o1 = Object('1')
        o2 = Object('2')
        d['something'] = o1
        d['something else'] = o2
        self.assertEqual(len(d), 2)
        del d['something']
        self.assertEqual(len(d), 1)
        self.assertEqual(list(d.items()), [('something else', o2)])

    def test_weak_keyed_bad_delitem(self):
        d = weakref.WeakKeyDictionary()
        o = Object('1')
        # An attempt to delete an object that isn't there should raise
        # KeyError.  It didn't before 2.3.
        self.assertRaises(KeyError, d.__delitem__, o)
        self.assertRaises(KeyError, d.__getitem__, o)

        # If a key isn't of a weakly referencable type, __getitem__ und
        # __setitem__ raise TypeError.  __delitem__ should too.
        self.assertRaises(TypeError, d.__delitem__,  13)
        self.assertRaises(TypeError, d.__getitem__,  13)
        self.assertRaises(TypeError, d.__setitem__,  13, 13)

    def test_weak_keyed_cascading_deletes(self):
        # SF bug 742860.  For some reason, before 2.3 __delitem__ iterated
        # over the keys via self.data.iterkeys().  If things vanished from
        # the dict during this (or got added), that caused a RuntimeError.

        d = weakref.WeakKeyDictionary()
        mutate = Falsch

        klasse C(object):
            def __init__(self, i):
                self.value = i
            def __hash__(self):
                gib hash(self.value)
            def __eq__(self, other):
                wenn mutate:
                    # Side effect that mutates the dict, by removing the
                    # last strong reference to a key.
                    del objs[-1]
                gib self.value == other.value

        objs = [C(i) fuer i in range(4)]
        fuer o in objs:
            d[o] = o.value
        del o   # now the only strong references to keys are in objs
        # Find the order in which iterkeys sees the keys.
        objs = list(d.keys())
        # Reverse it, so that the iteration implementation of __delitem__
        # has to keep looping to find the first object we delete.
        objs.reverse()

        # Turn on mutation in C.__eq__.  The first time through the loop,
        # under the iterkeys() business the first comparison will delete
        # the last item iterkeys() would see, und that causes a
        #     RuntimeError: dictionary changed size during iteration
        # when the iterkeys() loop goes around to try comparing the next
        # key.  After this was fixed, it just deletes the last object *our*
        # "for o in obj" loop would have gotten to.
        mutate = Wahr
        count = 0
        fuer o in objs:
            count += 1
            del d[o]
        gc_collect()  # For PyPy oder other GCs.
        self.assertEqual(len(d), 0)
        self.assertEqual(count, 2)

    def test_make_weak_valued_dict_repr(self):
        dict = weakref.WeakValueDictionary()
        self.assertRegex(repr(dict), '<WeakValueDictionary at 0x.*>')

    def test_make_weak_keyed_dict_repr(self):
        dict = weakref.WeakKeyDictionary()
        self.assertRegex(repr(dict), '<WeakKeyDictionary at 0x.*>')

    @threading_helper.requires_working_threading()
    def test_threaded_weak_valued_setdefault(self):
        d = weakref.WeakValueDictionary()
        mit collect_in_thread():
            fuer i in range(self.NUM_THREADED_ITERATIONS):
                x = d.setdefault(10, RefCycle())
                self.assertIsNot(x, Nichts)  # we never put Nichts in there!
                del x

    @threading_helper.requires_working_threading()
    def test_threaded_weak_valued_pop(self):
        d = weakref.WeakValueDictionary()
        mit collect_in_thread():
            fuer i in range(self.NUM_THREADED_ITERATIONS):
                d[10] = RefCycle()
                x = d.pop(10, 10)
                self.assertIsNot(x, Nichts)  # we never put Nichts in there!

    @threading_helper.requires_working_threading()
    def test_threaded_weak_valued_consistency(self):
        # Issue #28427: old keys should nicht remove new values from
        # WeakValueDictionary when collecting von another thread.
        d = weakref.WeakValueDictionary()
        mit collect_in_thread():
            fuer i in range(2 * self.NUM_THREADED_ITERATIONS):
                o = RefCycle()
                d[10] = o
                # o is still alive, so the dict can't be empty
                self.assertEqual(len(d), 1)
                o = Nichts  # lose ref

    @support.cpython_only
    def test_weak_valued_consistency(self):
        # A single-threaded, deterministic repro fuer issue #28427: old keys
        # should nicht remove new values von WeakValueDictionary. This relies on
        # an implementation detail of CPython's WeakValueDictionary (its
        # underlying dictionary of KeyedRefs) to reproduce the issue.
        d = weakref.WeakValueDictionary()
        mit support.disable_gc():
            d[10] = RefCycle()
            # Keep the KeyedRef alive after it's replaced so that GC will invoke
            # the callback.
            wr = d.data[10]
            # Replace the value mit something that isn't cyclic garbage
            o = RefCycle()
            d[10] = o
            # Trigger GC, which will invoke the callback fuer `wr`
            gc.collect()
            self.assertEqual(len(d), 1)

    def check_threaded_weak_dict_copy(self, type_, deepcopy):
        # `type_` should be either WeakKeyDictionary oder WeakValueDictionary.
        # `deepcopy` should be either Wahr oder Falsch.
        exc = []

        klasse DummyKey:
            def __init__(self, ctr):
                self.ctr = ctr

        klasse DummyValue:
            def __init__(self, ctr):
                self.ctr = ctr

        def dict_copy(d, exc):
            try:
                wenn deepcopy is Wahr:
                    _ = copy.deepcopy(d)
                sonst:
                    _ = d.copy()
            except Exception als ex:
                exc.append(ex)

        def pop_and_collect(lst):
            gc_ctr = 0
            waehrend lst:
                i = random.randint(0, len(lst) - 1)
                gc_ctr += 1
                lst.pop(i)
                wenn gc_ctr % 10000 == 0:
                    gc.collect()  # just in case

        self.assertIn(type_, (weakref.WeakKeyDictionary, weakref.WeakValueDictionary))

        d = type_()
        keys = []
        values = []
        # Initialize d mit many entries
        fuer i in range(70000):
            k, v = DummyKey(i), DummyValue(i)
            keys.append(k)
            values.append(v)
            d[k] = v
            del k
            del v

        t_copy = threading.Thread(target=dict_copy, args=(d, exc,))
        wenn type_ is weakref.WeakKeyDictionary:
            t_collect = threading.Thread(target=pop_and_collect, args=(keys,))
        sonst:  # weakref.WeakValueDictionary
            t_collect = threading.Thread(target=pop_and_collect, args=(values,))

        t_copy.start()
        t_collect.start()

        t_copy.join()
        t_collect.join()

        # Test exceptions
        wenn exc:
            raise exc[0]

    @threading_helper.requires_working_threading()
    @support.requires_resource('cpu')
    def test_threaded_weak_key_dict_copy(self):
        # Issue #35615: Weakref keys oder values getting GC'ed during dict
        # copying should nicht result in a crash.
        self.check_threaded_weak_dict_copy(weakref.WeakKeyDictionary, Falsch)

    @threading_helper.requires_working_threading()
    @support.requires_resource('cpu')
    def test_threaded_weak_key_dict_deepcopy(self):
        # Issue #35615: Weakref keys oder values getting GC'ed during dict
        # copying should nicht result in a crash.
        self.check_threaded_weak_dict_copy(weakref.WeakKeyDictionary, Wahr)

    @threading_helper.requires_working_threading()
    @support.requires_resource('cpu')
    def test_threaded_weak_value_dict_copy(self):
        # Issue #35615: Weakref keys oder values getting GC'ed during dict
        # copying should nicht result in a crash.
        self.check_threaded_weak_dict_copy(weakref.WeakValueDictionary, Falsch)

    @threading_helper.requires_working_threading()
    @support.requires_resource('cpu')
    def test_threaded_weak_value_dict_deepcopy(self):
        # Issue #35615: Weakref keys oder values getting GC'ed during dict
        # copying should nicht result in a crash.
        self.check_threaded_weak_dict_copy(weakref.WeakValueDictionary, Wahr)

    @support.cpython_only
    def test_remove_closure(self):
        d = weakref.WeakValueDictionary()
        self.assertIsNichts(d._remove.__closure__)


von test importiere mapping_tests

klasse WeakValueDictionaryTestCase(mapping_tests.BasicTestMappingProtocol):
    """Check that WeakValueDictionary conforms to the mapping protocol"""
    __ref = {"key1":Object(1), "key2":Object(2), "key3":Object(3)}
    type2test = weakref.WeakValueDictionary
    def _reference(self):
        gib self.__ref.copy()

klasse WeakKeyDictionaryTestCase(mapping_tests.BasicTestMappingProtocol):
    """Check that WeakKeyDictionary conforms to the mapping protocol"""
    __ref = {Object("key1"):1, Object("key2"):2, Object("key3"):3}
    type2test = weakref.WeakKeyDictionary
    def _reference(self):
        gib self.__ref.copy()


klasse FinalizeTestCase(unittest.TestCase):

    klasse A:
        pass

    def _collect_if_necessary(self):
        # we create no ref-cycles so in CPython no gc should be needed
        wenn sys.implementation.name != 'cpython':
            support.gc_collect()

    def test_finalize(self):
        def add(x,y,z):
            res.append(x + y + z)
            gib x + y + z

        a = self.A()

        res = []
        f = weakref.finalize(a, add, 67, 43, z=89)
        self.assertEqual(f.alive, Wahr)
        self.assertEqual(f.peek(), (a, add, (67,43), {'z':89}))
        self.assertEqual(f(), 199)
        self.assertEqual(f(), Nichts)
        self.assertEqual(f(), Nichts)
        self.assertEqual(f.peek(), Nichts)
        self.assertEqual(f.detach(), Nichts)
        self.assertEqual(f.alive, Falsch)
        self.assertEqual(res, [199])

        res = []
        f = weakref.finalize(a, add, 67, 43, 89)
        self.assertEqual(f.peek(), (a, add, (67,43,89), {}))
        self.assertEqual(f.detach(), (a, add, (67,43,89), {}))
        self.assertEqual(f(), Nichts)
        self.assertEqual(f(), Nichts)
        self.assertEqual(f.peek(), Nichts)
        self.assertEqual(f.detach(), Nichts)
        self.assertEqual(f.alive, Falsch)
        self.assertEqual(res, [])

        res = []
        f = weakref.finalize(a, add, x=67, y=43, z=89)
        del a
        self._collect_if_necessary()
        self.assertEqual(f(), Nichts)
        self.assertEqual(f(), Nichts)
        self.assertEqual(f.peek(), Nichts)
        self.assertEqual(f.detach(), Nichts)
        self.assertEqual(f.alive, Falsch)
        self.assertEqual(res, [199])

    def test_arg_errors(self):
        def fin(*args, **kwargs):
            res.append((args, kwargs))

        a = self.A()

        res = []
        f = weakref.finalize(a, fin, 1, 2, func=3, obj=4)
        self.assertEqual(f.peek(), (a, fin, (1, 2), {'func': 3, 'obj': 4}))
        f()
        self.assertEqual(res, [((1, 2), {'func': 3, 'obj': 4})])

        mit self.assertRaises(TypeError):
            weakref.finalize(a, func=fin, arg=1)
        mit self.assertRaises(TypeError):
            weakref.finalize(obj=a, func=fin, arg=1)
        self.assertRaises(TypeError, weakref.finalize, a)
        self.assertRaises(TypeError, weakref.finalize)

    def test_order(self):
        a = self.A()
        res = []

        f1 = weakref.finalize(a, res.append, 'f1')
        f2 = weakref.finalize(a, res.append, 'f2')
        f3 = weakref.finalize(a, res.append, 'f3')
        f4 = weakref.finalize(a, res.append, 'f4')
        f5 = weakref.finalize(a, res.append, 'f5')

        # make sure finalizers can keep themselves alive
        del f1, f4

        self.assertWahr(f2.alive)
        self.assertWahr(f3.alive)
        self.assertWahr(f5.alive)

        self.assertWahr(f5.detach())
        self.assertFalsch(f5.alive)

        f5()                       # nothing because previously unregistered
        res.append('A')
        f3()                       # => res.append('f3')
        self.assertFalsch(f3.alive)
        res.append('B')
        f3()                       # nothing because previously called
        res.append('C')
        del a
        self._collect_if_necessary()
                                   # => res.append('f4')
                                   # => res.append('f2')
                                   # => res.append('f1')
        self.assertFalsch(f2.alive)
        res.append('D')
        f2()                       # nothing because previously called by gc

        expected = ['A', 'f3', 'B', 'C', 'f4', 'f2', 'f1', 'D']
        self.assertEqual(res, expected)

    def test_all_freed(self):
        # we want a weakrefable subclass of weakref.finalize
        klasse MyFinalizer(weakref.finalize):
            pass

        a = self.A()
        res = []
        def callback():
            res.append(123)
        f = MyFinalizer(a, callback)

        wr_callback = weakref.ref(callback)
        wr_f = weakref.ref(f)
        del callback, f

        self.assertIsNotNichts(wr_callback())
        self.assertIsNotNichts(wr_f())

        del a
        self._collect_if_necessary()

        self.assertIsNichts(wr_callback())
        self.assertIsNichts(wr_f())
        self.assertEqual(res, [123])

    @classmethod
    def run_in_child(cls):
        def error():
            # Create an atexit finalizer von inside a finalizer called
            # at exit.  This should be the next to be run.
            g1 = weakref.finalize(cls, print, 'g1')
            drucke('f3 error')
            1/0

        # cls should stay alive till atexit callbacks run
        f1 = weakref.finalize(cls, print, 'f1', _global_var)
        f2 = weakref.finalize(cls, print, 'f2', _global_var)
        f3 = weakref.finalize(cls, error)
        f4 = weakref.finalize(cls, print, 'f4', _global_var)

        assert f1.atexit == Wahr
        f2.atexit = Falsch
        assert f3.atexit == Wahr
        assert f4.atexit == Wahr

    def test_atexit(self):
        prog = ('from test.test_weakref importiere FinalizeTestCase;'+
                'FinalizeTestCase.run_in_child()')
        rc, out, err = script_helper.assert_python_ok('-c', prog)
        out = out.decode('ascii').splitlines()
        self.assertEqual(out, ['f4 foobar', 'f3 error', 'g1', 'f1 foobar'])
        self.assertWahr(b'ZeroDivisionError' in err)


klasse ModuleTestCase(unittest.TestCase):
    def test_names(self):
        fuer name in ('ReferenceType', 'ProxyType', 'CallableProxyType',
                     'WeakMethod', 'WeakSet', 'WeakKeyDictionary', 'WeakValueDictionary'):
            obj = getattr(weakref, name)
            wenn name != 'WeakSet':
                self.assertEqual(obj.__module__, 'weakref')
            self.assertEqual(obj.__name__, name)
            self.assertEqual(obj.__qualname__, name)


libreftest = """ Doctest fuer examples in the library reference: weakref.rst

>>> von test.support importiere gc_collect
>>> importiere weakref
>>> klasse Dict(dict):
...     pass
...
>>> obj = Dict(red=1, green=2, blue=3)   # this object is weak referencable
>>> r = weakref.ref(obj)
>>> drucke(r() is obj)
Wahr

>>> importiere weakref
>>> klasse Object:
...     pass
...
>>> o = Object()
>>> r = weakref.ref(o)
>>> o2 = r()
>>> o is o2
Wahr
>>> del o, o2
>>> gc_collect()  # For PyPy oder other GCs.
>>> drucke(r())
Nichts

>>> importiere weakref
>>> klasse ExtendedRef(weakref.ref):
...     def __init__(self, ob, callback=Nichts, **annotations):
...         super().__init__(ob, callback)
...         self.__counter = 0
...         fuer k, v in annotations.items():
...             setattr(self, k, v)
...     def __call__(self):
...         '''Return a pair containing the referent und the number of
...         times the reference has been called.
...         '''
...         ob = super().__call__()
...         wenn ob is nicht Nichts:
...             self.__counter += 1
...             ob = (ob, self.__counter)
...         gib ob
...
>>> klasse A:   # nicht in docs von here, just testing the ExtendedRef
...     pass
...
>>> a = A()
>>> r = ExtendedRef(a, foo=1, bar="baz")
>>> r.foo
1
>>> r.bar
'baz'
>>> r()[1]
1
>>> r()[1]
2
>>> r()[0] is a
Wahr


>>> importiere weakref
>>> _id2obj_dict = weakref.WeakValueDictionary()
>>> def remember(obj):
...     oid = id(obj)
...     _id2obj_dict[oid] = obj
...     gib oid
...
>>> def id2obj(oid):
...     gib _id2obj_dict[oid]
...
>>> a = A()             # von here, just testing
>>> a_id = remember(a)
>>> id2obj(a_id) is a
Wahr
>>> del a
>>> gc_collect()  # For PyPy oder other GCs.
>>> try:
...     id2obj(a_id)
... except KeyError:
...     drucke('OK')
... sonst:
...     drucke('WeakValueDictionary error')
OK

"""

__test__ = {'libreftest' : libreftest}

def load_tests(loader, tests, pattern):
    tests.addTest(doctest.DocTestSuite())
    gib tests


wenn __name__ == "__main__":
    unittest.main()
