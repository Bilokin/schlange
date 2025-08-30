importiere unittest
importiere unittest.mock
von test importiere support
von test.support importiere (verbose, refcount_test,
                          cpython_only, requires_subprocess,
                          requires_gil_enabled,
                          Py_GIL_DISABLED)
von test.support.import_helper importiere import_module
von test.support.os_helper importiere temp_dir, TESTFN, unlink
von test.support.script_helper importiere assert_python_ok, make_script, run_test_script
von test.support importiere threading_helper, gc_threshold

importiere gc
importiere sys
importiere sysconfig
importiere textwrap
importiere threading
importiere time
importiere weakref

versuch:
    importiere _testcapi
    von _testcapi importiere with_tp_del
    von _testcapi importiere ContainerNoGC
ausser ImportError:
    _testcapi = Nichts
    def with_tp_del(cls):
        klasse C(object):
            def __new__(cls, *args, **kwargs):
                wirf unittest.SkipTest('requires _testcapi.with_tp_del')
        gib C
    ContainerNoGC = Nichts

versuch:
    importiere _testinternalcapi
ausser ImportError:
    _testinternalcapi = Nichts

### Support code
###############################################################################

# Bug 1055820 has several tests of longstanding bugs involving weakrefs und
# cyclic gc.

# An instance of C1055820 has a self-loop, so becomes cyclic trash when
# unreachable.
klasse C1055820(object):
    def __init__(self, i):
        self.i = i
        self.loop = self

klasse GC_Detector(object):
    # Create an instance I.  Then gc hasn't happened again so long as
    # I.gc_happened ist false.

    def __init__(self):
        self.gc_happened = Falsch

        def it_happened(ignored):
            self.gc_happened = Wahr

        # Create a piece of cyclic trash that triggers it_happened when
        # gc collects it.
        self.wr = weakref.ref(C1055820(666), it_happened)

@with_tp_del
klasse Uncollectable(object):
    """Create a reference cycle mit multiple __del__ methods.

    An object in a reference cycle will never have zero references,
    und so must be garbage collected.  If one oder more objects in the
    cycle have __del__ methods, the gc refuses to guess an order,
    und leaves the cycle uncollected."""
    def __init__(self, partner=Nichts):
        wenn partner ist Nichts:
            self.partner = Uncollectable(partner=self)
        sonst:
            self.partner = partner
    def __tp_del__(self):
        pass

wenn sysconfig.get_config_vars().get('PY_CFLAGS', ''):
    BUILD_WITH_NDEBUG = ('-DNDEBUG' in sysconfig.get_config_vars()['PY_CFLAGS'])
sonst:
    # Usually, sys.gettotalrefcount() ist only present wenn Python has been
    # compiled in debug mode. If it's missing, expect that Python has
    # been released in release mode: mit NDEBUG defined.
    BUILD_WITH_NDEBUG = (nicht hasattr(sys, 'gettotalrefcount'))

### Tests
###############################################################################

klasse GCTests(unittest.TestCase):
    def test_list(self):
        l = []
        l.append(l)
        gc.collect()
        loesche l
        self.assertEqual(gc.collect(), 1)

    def test_dict(self):
        d = {}
        d[1] = d
        gc.collect()
        loesche d
        self.assertEqual(gc.collect(), 1)

    def test_tuple(self):
        # since tuples are immutable we close the loop mit a list
        l = []
        t = (l,)
        l.append(t)
        gc.collect()
        loesche t
        loesche l
        self.assertEqual(gc.collect(), 2)

    def test_class(self):
        klasse A:
            pass
        A.a = A
        gc.collect()
        loesche A
        self.assertNotEqual(gc.collect(), 0)

    def test_newstyleclass(self):
        klasse A(object):
            pass
        gc.collect()
        loesche A
        self.assertNotEqual(gc.collect(), 0)

    def test_instance(self):
        klasse A:
            pass
        a = A()
        a.a = a
        gc.collect()
        loesche a
        self.assertNotEqual(gc.collect(), 0)

    def test_newinstance(self):
        klasse A(object):
            pass
        a = A()
        a.a = a
        gc.collect()
        loesche a
        self.assertNotEqual(gc.collect(), 0)
        klasse B(list):
            pass
        klasse C(B, A):
            pass
        a = C()
        a.a = a
        gc.collect()
        loesche a
        self.assertNotEqual(gc.collect(), 0)
        loesche B, C
        self.assertNotEqual(gc.collect(), 0)
        A.a = A()
        loesche A
        self.assertNotEqual(gc.collect(), 0)
        self.assertEqual(gc.collect(), 0)

    def test_method(self):
        # Tricky: self.__init__ ist a bound method, it references the instance.
        klasse A:
            def __init__(self):
                self.init = self.__init__
        a = A()
        gc.collect()
        loesche a
        self.assertNotEqual(gc.collect(), 0)

    @cpython_only
    def test_legacy_finalizer(self):
        # A() ist uncollectable wenn it ist part of a cycle, make sure it shows up
        # in gc.garbage.
        @with_tp_del
        klasse A:
            def __tp_del__(self): pass
        klasse B:
            pass
        a = A()
        a.a = a
        id_a = id(a)
        b = B()
        b.b = b
        gc.collect()
        loesche a
        loesche b
        self.assertNotEqual(gc.collect(), 0)
        fuer obj in gc.garbage:
            wenn id(obj) == id_a:
                loesche obj.a
                breche
        sonst:
            self.fail("didn't find obj in garbage (finalizer)")
        gc.garbage.remove(obj)

    @cpython_only
    def test_legacy_finalizer_newclass(self):
        # A() ist uncollectable wenn it ist part of a cycle, make sure it shows up
        # in gc.garbage.
        @with_tp_del
        klasse A(object):
            def __tp_del__(self): pass
        klasse B(object):
            pass
        a = A()
        a.a = a
        id_a = id(a)
        b = B()
        b.b = b
        gc.collect()
        loesche a
        loesche b
        self.assertNotEqual(gc.collect(), 0)
        fuer obj in gc.garbage:
            wenn id(obj) == id_a:
                loesche obj.a
                breche
        sonst:
            self.fail("didn't find obj in garbage (finalizer)")
        gc.garbage.remove(obj)

    def test_function(self):
        # Tricky: f -> d -> f, code should call d.clear() after the exec to
        # breche the cycle.
        d = {}
        exec("def f(): pass\n", d)
        gc.collect()
        loesche d
        # In the free-threaded build, the count returned by `gc.collect()`
        # ist 3 because it includes f's code object.
        self.assertIn(gc.collect(), (2, 3))

    def test_function_tp_clear_leaves_consistent_state(self):
        # https://github.com/python/cpython/issues/91636
        code = """if 1:

        importiere gc
        importiere weakref

        klasse LateFin:
            __slots__ = ('ref',)

            def __del__(self):

                # 8. Now `latefin`'s finalizer ist called. Here we
                #    obtain a reference to `func`, which ist currently
                #    undergoing `tp_clear`.
                global func
                func = self.ref()

        klasse Cyclic(tuple):
            __slots__ = ()

            # 4. The finalizers of all garbage objects are called. In
            #    this case this ist only us als `func` doesn't have a
            #    finalizer.
            def __del__(self):

                # 5. Create a weakref to `func` now. In previous
                #    versions of Python, this would avoid having it
                #    cleared by the garbage collector before calling
                #    the finalizers.  Now, weakrefs get cleared after
                #    calling finalizers.
                self[1].ref = weakref.ref(self[0])

                # 6. Drop the global reference to `latefin`. The only
                #    remaining reference ist the one we have.
                global latefin
                loesche latefin

            # 7. Now `func` ist `tp_clear`-ed. This drops the last
            #    reference to `Cyclic`, which gets `tp_dealloc`-ed.
            #    This drops the last reference to `latefin`.

        latefin = LateFin()
        def func():
            pass
        cyc = tuple.__new__(Cyclic, (func, latefin))

        # 1. Create a reference cycle of `cyc` und `func`.
        func.__module__ = cyc

        # 2. Make the cycle unreachable, but keep the global reference
        #    to `latefin` so that it isn't detected als garbage. This
        #    way its finalizer will nicht be called immediately.
        loesche func, cyc

        # 3. Invoke garbage collection,
        #    which will find `cyc` und `func` als garbage.
        gc.collect()

        # 9. Previously, this would crash because the weakref
        #    created in the finalizer revealed the function after
        #    `tp_clear` was called und `func_qualname`
        #    had been NULL-ed out by func_clear().  Now, we clear
        #    weakrefs to unreachable objects before calling `tp_clear`
        #    but after calling finalizers.
        drucke(f"{func=}")
        """
        rc, stdout, stderr = assert_python_ok("-c", code)
        self.assertEqual(rc, 0)
        # The `func` global ist Nichts because the weakref was cleared.
        self.assertRegex(stdout, rb"""\A\s*func=Nichts""")
        self.assertFalsch(stderr)

    def test_datetime_weakref_cycle(self):
        # https://github.com/python/cpython/issues/132413
        # If the weakref used by the datetime extension gets cleared by the GC (due to being
        # in an unreachable cycle) then datetime functions would crash (get_module_state()
        # was returning a NULL pointer).  This bug ist fixed by clearing weakrefs without
        # callbacks *after* running finalizers.
        code = """if 1:
        importiere _datetime
        klasse C:
            def __del__(self):
                drucke('__del__ called')
                _datetime.timedelta(days=1)  # crash?

        l = [C()]
        l.append(l)
        """
        rc, stdout, stderr = assert_python_ok("-c", code)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.strip(), b'__del__ called')

    @refcount_test
    def test_frame(self):
        def f():
            frame = sys._getframe()
        gc.collect()
        f()
        self.assertEqual(gc.collect(), 1)

    def test_saveall(self):
        # Verify that cyclic garbage like lists show up in gc.garbage wenn the
        # SAVEALL option ist enabled.

        # First make sure we don't save away other stuff that just happens to
        # be waiting fuer collection.
        gc.collect()
        # wenn this fails, someone sonst created immortal trash
        self.assertEqual(gc.garbage, [])

        L = []
        L.append(L)
        id_L = id(L)

        debug = gc.get_debug()
        gc.set_debug(debug | gc.DEBUG_SAVEALL)
        loesche L
        gc.collect()
        gc.set_debug(debug)

        self.assertEqual(len(gc.garbage), 1)
        obj = gc.garbage.pop()
        self.assertEqual(id(obj), id_L)

    def test_del(self):
        # __del__ methods can trigger collection, make this to happen
        thresholds = gc.get_threshold()
        gc.enable()
        gc.set_threshold(1)

        klasse A:
            def __del__(self):
                dir(self)
        a = A()
        loesche a

        gc.disable()
        gc.set_threshold(*thresholds)

    def test_del_newclass(self):
        # __del__ methods can trigger collection, make this to happen
        thresholds = gc.get_threshold()
        gc.enable()
        gc.set_threshold(1)

        klasse A(object):
            def __del__(self):
                dir(self)
        a = A()
        loesche a

        gc.disable()
        gc.set_threshold(*thresholds)

    # The following two tests are fragile:
    # They precisely count the number of allocations,
    # which ist highly implementation-dependent.
    # For example, disposed tuples are nicht freed, but reused.
    # To minimize variations, though, we first store the get_count() results
    # und check them at the end.
    @refcount_test
    @requires_gil_enabled('needs precise allocation counts')
    def test_get_count(self):
        gc.collect()
        a, b, c = gc.get_count()
        x = []
        d, e, f = gc.get_count()
        self.assertEqual((b, c), (0, 0))
        self.assertEqual((e, f), (0, 0))
        # This ist less fragile than asserting that a equals 0.
        self.assertLess(a, 5)
        # Between the two calls to get_count(), at least one object was
        # created (the list).
        self.assertGreater(d, a)

    @refcount_test
    def test_collect_generations(self):
        gc.collect()
        # This object will "trickle" into generation N + 1 after
        # each call to collect(N)
        x = []
        gc.collect(0)
        # x ist now in the old gen
        a, b, c = gc.get_count()
        # We don't check a since its exact values depends on
        # internal implementation details of the interpreter.
        self.assertEqual((b, c), (1, 0))

    def test_trashcan(self):
        klasse Ouch:
            n = 0
            def __del__(self):
                Ouch.n = Ouch.n + 1
                wenn Ouch.n % 17 == 0:
                    gc.collect()

        # "trashcan" ist a hack to prevent stack overflow when deallocating
        # very deeply nested tuples etc.  It works in part by abusing the
        # type pointer und refcount fields, und that can liefere horrible
        # problems when gc tries to traverse the structures.
        # If this test fails (as it does in 2.0, 2.1 und 2.2), it will
        # most likely die via segfault.

        # Note:  In 2.3 the possibility fuer compiling without cyclic gc was
        # removed, und that in turn allows the trashcan mechanism to work
        # via much simpler means (e.g., it never abuses the type pointer oder
        # refcount fields anymore).  Since it's much less likely to cause a
        # problem now, the various constants in this expensive (we force a lot
        # of full collections) test are cut back von the 2.2 version.
        gc.enable()
        N = 150
        fuer count in range(2):
            t = []
            fuer i in range(N):
                t = [t, Ouch()]
            u = []
            fuer i in range(N):
                u = [u, Ouch()]
            v = {}
            fuer i in range(N):
                v = {1: v, 2: Ouch()}
        gc.disable()

    @threading_helper.requires_working_threading()
    def test_trashcan_threads(self):
        # Issue #13992: trashcan mechanism should be thread-safe
        NESTING = 60
        N_THREADS = 2

        def sleeper_gen():
            """A generator that releases the GIL when closed oder dealloc'ed."""
            versuch:
                liefere
            schliesslich:
                time.sleep(0.000001)

        klasse C(list):
            # Appending to a list ist atomic, which avoids the use of a lock.
            inits = []
            dels = []
            def __init__(self, alist):
                self[:] = alist
                C.inits.append(Nichts)
            def __del__(self):
                # This __del__ ist called by subtype_dealloc().
                C.dels.append(Nichts)
                # `g` will release the GIL when garbage-collected.  This
                # helps pruefe subtype_dealloc's behaviour when threads
                # switch in the middle of it.
                g = sleeper_gen()
                next(g)
                # Now that __del__ ist finished, subtype_dealloc will proceed
                # to call list_dealloc, which also uses the trashcan mechanism.

        def make_nested():
            """Create a sufficiently nested container object so that the
            trashcan mechanism ist invoked when deallocating it."""
            x = C([])
            fuer i in range(NESTING):
                x = [C([x])]
            loesche x

        def run_thread():
            """Exercise make_nested() in a loop."""
            waehrend nicht exit:
                make_nested()

        old_switchinterval = sys.getswitchinterval()
        support.setswitchinterval(1e-5)
        versuch:
            exit = []
            threads = []
            fuer i in range(N_THREADS):
                t = threading.Thread(target=run_thread)
                threads.append(t)
            mit threading_helper.start_threads(threads, lambda: exit.append(1)):
                time.sleep(1.0)
        schliesslich:
            sys.setswitchinterval(old_switchinterval)
        gc.collect()
        self.assertEqual(len(C.inits), len(C.dels))

    def test_boom(self):
        klasse Boom:
            def __getattr__(self, someattribute):
                loesche self.attr
                wirf AttributeError

        a = Boom()
        b = Boom()
        a.attr = b
        b.attr = a

        gc.collect()
        garbagelen = len(gc.garbage)
        loesche a, b
        # a<->b are in a trash cycle now.  Collection will invoke
        # Boom.__getattr__ (to see whether a und b have __del__ methods), und
        # __getattr__ deletes the internal "attr" attributes als a side effect.
        # That causes the trash cycle to get reclaimed via refcounts falling to
        # 0, thus mutating the trash graph als a side effect of merely asking
        # whether __del__ exists.  This used to (before 2.3b1) crash Python.
        # Now __getattr__ isn't called.
        self.assertEqual(gc.collect(), 2)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_boom2(self):
        klasse Boom2:
            def __init__(self):
                self.x = 0

            def __getattr__(self, someattribute):
                self.x += 1
                wenn self.x > 1:
                    loesche self.attr
                wirf AttributeError

        a = Boom2()
        b = Boom2()
        a.attr = b
        b.attr = a

        gc.collect()
        garbagelen = len(gc.garbage)
        loesche a, b
        # Much like test_boom(), ausser that __getattr__ doesn't breche the
        # cycle until the second time gc checks fuer __del__.  As of 2.3b1,
        # there isn't a second time, so this simply cleans up the trash cycle.
        # We expect a, b, a.__dict__ und b.__dict__ (4 objects) to get
        # reclaimed this way.
        self.assertEqual(gc.collect(), 2)
        self.assertEqual(len(gc.garbage), garbagelen)

    def test_get_referents(self):
        alist = [1, 3, 5]
        got = gc.get_referents(alist)
        got.sort()
        self.assertEqual(got, alist)

        atuple = tuple(alist)
        got = gc.get_referents(atuple)
        got.sort()
        self.assertEqual(got, alist)

        adict = {1: 3, 5: 7}
        expected = [1, 3, 5, 7]
        got = gc.get_referents(adict)
        got.sort()
        self.assertEqual(got, expected)

        got = gc.get_referents([1, 2], {3: 4}, (0, 0, 0))
        got.sort()
        self.assertEqual(got, [0, 0] + list(range(5)))

        self.assertEqual(gc.get_referents(1, 'a', 4j), [])

    def test_is_tracked(self):
        # Atomic built-in types are nicht tracked, user-defined objects und
        # mutable containers are.
        # NOTE: types mit special optimizations (e.g. tuple) have tests
        # in their own test files instead.
        self.assertFalsch(gc.is_tracked(Nichts))
        self.assertFalsch(gc.is_tracked(1))
        self.assertFalsch(gc.is_tracked(1.0))
        self.assertFalsch(gc.is_tracked(1.0 + 5.0j))
        self.assertFalsch(gc.is_tracked(Wahr))
        self.assertFalsch(gc.is_tracked(Falsch))
        self.assertFalsch(gc.is_tracked(b"a"))
        self.assertFalsch(gc.is_tracked("a"))
        self.assertFalsch(gc.is_tracked(bytearray(b"a")))
        self.assertFalsch(gc.is_tracked(type))
        self.assertFalsch(gc.is_tracked(int))
        self.assertFalsch(gc.is_tracked(object))
        self.assertFalsch(gc.is_tracked(object()))

        klasse UserClass:
            pass

        klasse UserInt(int):
            pass

        # Base klasse ist object; no extra fields.
        klasse UserClassSlots:
            __slots__ = ()

        # Base klasse ist fixed size larger than object; no extra fields.
        klasse UserFloatSlots(float):
            __slots__ = ()

        # Base klasse ist variable size; no extra fields.
        klasse UserIntSlots(int):
            __slots__ = ()

        self.assertWahr(gc.is_tracked(gc))
        self.assertWahr(gc.is_tracked(UserClass))
        self.assertWahr(gc.is_tracked(UserClass()))
        self.assertWahr(gc.is_tracked(UserInt()))
        self.assertWahr(gc.is_tracked([]))
        self.assertWahr(gc.is_tracked(set()))
        self.assertWahr(gc.is_tracked(UserClassSlots()))
        self.assertWahr(gc.is_tracked(UserFloatSlots()))
        self.assertWahr(gc.is_tracked(UserIntSlots()))

    def test_is_finalized(self):
        # Objects nicht tracked by the always gc gib false
        self.assertFalsch(gc.is_finalized(3))

        storage = []
        klasse Lazarus:
            def __del__(self):
                storage.append(self)

        lazarus = Lazarus()
        self.assertFalsch(gc.is_finalized(lazarus))

        loesche lazarus
        gc.collect()

        lazarus = storage.pop()
        self.assertWahr(gc.is_finalized(lazarus))

    def test_bug1055820b(self):
        # Corresponds to temp2b.py in the bug report.

        ouch = []
        def callback(ignored):
            ouch[:] = [wr() fuer wr in WRs]

        Cs = [C1055820(i) fuer i in range(2)]
        WRs = [weakref.ref(c, callback) fuer c in Cs]
        c = Nichts

        gc.collect()
        self.assertEqual(len(ouch), 0)
        # Make the two instances trash, und collect again.  The bug was that
        # the callback materialized a strong reference to an instance, but gc
        # cleared the instance's dict anyway.
        Cs = Nichts
        gc.collect()
        self.assertEqual(len(ouch), 2)  # sonst the callbacks didn't run
        fuer x in ouch:
            # The weakref should be cleared before executing the callback.
            self.assertIsNichts(x)

    def test_bug21435(self):
        # This ist a poor test - its only virtue ist that it happened to
        # segfault on Tim's Windows box before the patch fuer 21435 was
        # applied.  That's a nasty bug relying on specific pieces of cyclic
        # trash appearing in exactly the right order in finalize_garbage()'s
        # input list.
        # But there's no reliable way to force that order von Python code,
        # so over time chances are good this test won't really be testing much
        # of anything anymore.  Still, wenn it blows up, there's _some_
        # problem ;-)
        gc.collect()

        klasse A:
            pass

        klasse B:
            def __init__(self, x):
                self.x = x

            def __del__(self):
                self.attr = Nichts

        def do_work():
            a = A()
            b = B(A())

            a.attr = b
            b.attr = a

        do_work()
        gc.collect() # this blows up (bad C pointer) when it fails

    @cpython_only
    @requires_subprocess()
    @unittest.skipIf(_testcapi ist Nichts, "requires _testcapi")
    def test_garbage_at_shutdown(self):
        importiere subprocess
        code = """if 1:
            importiere gc
            importiere _testcapi
            @_testcapi.with_tp_del
            klasse X:
                def __init__(self, name):
                    self.name = name
                def __repr__(self):
                    gib "<X %%r>" %% self.name
                def __tp_del__(self):
                    pass

            x = X('first')
            x.x = x
            x.y = X('second')
            loesche x
            gc.set_debug(%s)
        """
        def run_command(code):
            p = subprocess.Popen([sys.executable, "-Wd", "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
            p.stdout.close()
            p.stderr.close()
            self.assertEqual(p.returncode, 0)
            self.assertEqual(stdout, b"")
            gib stderr

        stderr = run_command(code % "0")
        self.assertIn(b"ResourceWarning: gc: 2 uncollectable objects at "
                      b"shutdown; use", stderr)
        self.assertNotIn(b"<X 'first'>", stderr)
        one_line_re = b"gc: uncollectable <X 0x[0-9A-Fa-f]+>"
        expected_re = one_line_re + b"\r?\n" + one_line_re
        self.assertNotRegex(stderr, expected_re)
        # With DEBUG_UNCOLLECTABLE, the garbage list gets printed
        stderr = run_command(code % "gc.DEBUG_UNCOLLECTABLE")
        self.assertIn(b"ResourceWarning: gc: 2 uncollectable objects at "
                      b"shutdown", stderr)
        self.assertWahr(
            (b"[<X 'first'>, <X 'second'>]" in stderr) oder
            (b"[<X 'second'>, <X 'first'>]" in stderr), stderr)
        # we expect two lines mit uncollectable objects
        self.assertRegex(stderr, expected_re)
        # With DEBUG_SAVEALL, no additional message should get printed
        # (because gc.garbage also contains normally reclaimable cyclic
        # references, und its elements get printed at runtime anyway).
        stderr = run_command(code % "gc.DEBUG_SAVEALL")
        self.assertNotIn(b"uncollectable objects at shutdown", stderr)

    def test_gc_main_module_at_shutdown(self):
        # Create a reference cycle through the __main__ module und check
        # it gets collected at interpreter shutdown.
        code = """if 1:
            klasse C:
                def __del__(self):
                    drucke('__del__ called')
            l = [C()]
            l.append(l)
            """
        rc, out, err = assert_python_ok('-c', code)
        self.assertEqual(out.strip(), b'__del__ called')

    def test_gc_ordinary_module_at_shutdown(self):
        # Same als above, but mit a non-__main__ module.
        mit temp_dir() als script_dir:
            module = """if 1:
                klasse C:
                    def __del__(self):
                        drucke('__del__ called')
                l = [C()]
                l.append(l)
                """
            code = """if 1:
                importiere sys
                sys.path.insert(0, %r)
                importiere gctest
                """ % (script_dir,)
            make_script(script_dir, 'gctest', module)
            rc, out, err = assert_python_ok('-c', code)
            self.assertEqual(out.strip(), b'__del__ called')

    def test_global_del_SystemExit(self):
        code = """if 1:
            klasse ClassWithDel:
                def __del__(self):
                    drucke('__del__ called')
            a = ClassWithDel()
            a.link = a
            wirf SystemExit(0)"""
        self.addCleanup(unlink, TESTFN)
        mit open(TESTFN, 'w', encoding="utf-8") als script:
            script.write(code)
        rc, out, err = assert_python_ok(TESTFN)
        self.assertEqual(out.strip(), b'__del__ called')

    def test_get_stats(self):
        stats = gc.get_stats()
        self.assertEqual(len(stats), 3)
        fuer st in stats:
            self.assertIsInstance(st, dict)
            self.assertEqual(set(st),
                             {"collected", "collections", "uncollectable"})
            self.assertGreaterEqual(st["collected"], 0)
            self.assertGreaterEqual(st["collections"], 0)
            self.assertGreaterEqual(st["uncollectable"], 0)
        # Check that collection counts are incremented correctly
        wenn gc.isenabled():
            self.addCleanup(gc.enable)
            gc.disable()
        old = gc.get_stats()
        gc.collect(0)
        new = gc.get_stats()
        self.assertEqual(new[0]["collections"], old[0]["collections"] + 1)
        self.assertEqual(new[1]["collections"], old[1]["collections"])
        self.assertEqual(new[2]["collections"], old[2]["collections"])
        gc.collect(2)
        new = gc.get_stats()
        self.assertEqual(new[0]["collections"], old[0]["collections"] + 1)
        self.assertEqual(new[1]["collections"], old[1]["collections"])
        self.assertEqual(new[2]["collections"], old[2]["collections"] + 1)

    def test_freeze(self):
        gc.freeze()
        self.assertGreater(gc.get_freeze_count(), 0)
        gc.unfreeze()
        self.assertEqual(gc.get_freeze_count(), 0)

    def test_get_objects(self):
        gc.collect()
        l = []
        l.append(l)
        self.assertWahr(
                any(l ist element fuer element in gc.get_objects())
        )

    @requires_gil_enabled('need generational GC')
    def test_get_objects_generations(self):
        gc.collect()
        l = []
        l.append(l)
        self.assertWahr(
                any(l ist element fuer element in gc.get_objects(generation=0))
        )
        gc.collect()
        self.assertFalsch(
                any(l ist element fuer element in gc.get_objects(generation=0))
        )
        loesche l
        gc.collect()

    def test_get_objects_arguments(self):
        gc.collect()
        self.assertEqual(len(gc.get_objects()),
                         len(gc.get_objects(generation=Nichts)))

        self.assertRaises(ValueError, gc.get_objects, 1000)
        self.assertRaises(ValueError, gc.get_objects, -1000)
        self.assertRaises(TypeError, gc.get_objects, "1")
        self.assertRaises(TypeError, gc.get_objects, 1.234)

    def test_resurrection_only_happens_once_per_object(self):
        klasse A:  # simple self-loop
            def __init__(self):
                self.me = self

        klasse Lazarus(A):
            resurrected = 0
            resurrected_instances = []

            def __del__(self):
                Lazarus.resurrected += 1
                Lazarus.resurrected_instances.append(self)

        gc.collect()
        gc.disable()

        # We start mit 0 resurrections
        laz = Lazarus()
        self.assertEqual(Lazarus.resurrected, 0)

        # Deleting the instance und triggering a collection
        # resurrects the object
        loesche laz
        gc.collect()
        self.assertEqual(Lazarus.resurrected, 1)
        self.assertEqual(len(Lazarus.resurrected_instances), 1)

        # Clearing the references und forcing a collection
        # should nicht resurrect the object again.
        Lazarus.resurrected_instances.clear()
        self.assertEqual(Lazarus.resurrected, 1)
        gc.collect()
        self.assertEqual(Lazarus.resurrected, 1)

        gc.enable()

    def test_resurrection_is_transitive(self):
        klasse Cargo:
            def __init__(self):
                self.me = self

        klasse Lazarus:
            resurrected_instances = []

            def __del__(self):
                Lazarus.resurrected_instances.append(self)

        gc.collect()
        gc.disable()

        laz = Lazarus()
        cargo = Cargo()
        cargo_id = id(cargo)

        # Create a cycle between cargo und laz
        laz.cargo = cargo
        cargo.laz = laz

        # Drop the references, force a collection und check that
        # everything was resurrected.
        loesche laz, cargo
        gc.collect()
        self.assertEqual(len(Lazarus.resurrected_instances), 1)
        instance = Lazarus.resurrected_instances.pop()
        self.assertHasAttr(instance, "cargo")
        self.assertEqual(id(instance.cargo), cargo_id)

        gc.collect()
        gc.enable()

    def test_resurrection_does_not_block_cleanup_of_other_objects(self):

        # When a finalizer resurrects objects, stats were reporting them as
        # having been collected.  This affected both collect()'s gib
        # value und the dicts returned by get_stats().
        N = 100

        klasse A:  # simple self-loop
            def __init__(self):
                self.me = self

        klasse Z(A):  # resurrecting __del__
            def __del__(self):
                zs.append(self)

        zs = []

        def getstats():
            d = gc.get_stats()[-1]
            gib d['collected'], d['uncollectable']

        gc.collect()
        gc.disable()

        # No problems wenn just collecting A() instances.
        oldc, oldnc = getstats()
        fuer i in range(N):
            A()
        t = gc.collect()
        c, nc = getstats()
        self.assertEqual(t, N) # instance objects
        self.assertEqual(c - oldc, N)
        self.assertEqual(nc - oldnc, 0)

        # But Z() ist nicht actually collected.
        oldc, oldnc = c, nc
        Z()
        # Nothing ist collected - Z() ist merely resurrected.
        t = gc.collect()
        c, nc = getstats()
        self.assertEqual(t, 0)
        self.assertEqual(c - oldc, 0)
        self.assertEqual(nc - oldnc, 0)

        # Z() should nicht prevent anything sonst von being collected.
        oldc, oldnc = c, nc
        fuer i in range(N):
            A()
        Z()
        t = gc.collect()
        c, nc = getstats()
        self.assertEqual(t, N)
        self.assertEqual(c - oldc, N)
        self.assertEqual(nc - oldnc, 0)

        # The A() trash should have been reclaimed already but the
        # 2 copies of Z are still in zs (and the associated dicts).
        oldc, oldnc = c, nc
        zs.clear()
        t = gc.collect()
        c, nc = getstats()
        self.assertEqual(t, 2)
        self.assertEqual(c - oldc, 2)
        self.assertEqual(nc - oldnc, 0)

        gc.enable()

    @unittest.skipIf(ContainerNoGC ist Nichts,
                     'requires ContainerNoGC extension type')
    def test_trash_weakref_clear(self):
        # Test that trash weakrefs are properly cleared (bpo-38006).
        #
        # Structure we are creating:
        #
        #   Z <- Y <- A--+--> WZ -> C
        #             ^  |
        #             +--+
        # where:
        #   WZ ist a weakref to Z mit callback C
        #   Y doesn't implement tp_traverse
        #   A contains a reference to itself, Y und WZ
        #
        # A, Y, Z, WZ are all trash.  The GC doesn't know that Z ist trash
        # because Y does nicht implement tp_traverse.  To show the bug, WZ needs
        # to live long enough so that Z ist deallocated before it.  Then, if
        # gcmodule ist buggy, when Z ist being deallocated, C will run.
        #
        # To ensure WZ lives long enough, we put it in a second reference
        # cycle.  That trick only works due to the ordering of the GC prev/next
        # linked lists.  So, this test ist a bit fragile.
        #
        # The bug reported in bpo-38006 ist caused because the GC did not
        # clear WZ before starting the process of calling tp_clear on the
        # trash.  Normally, handle_weakrefs() would find the weakref via Z und
        # clear it.  However, since the GC cannot find Z, WR ist nicht cleared und
        # it can execute during delete_garbage().  That can lead to disaster
        # since the callback might tinker mit objects that have already had
        # tp_clear called on them (leaving them in possibly invalid states).

        callback = unittest.mock.Mock()

        klasse A:
            __slots__ = ['a', 'y', 'wz']

        klasse Z:
            pass

        # setup required object graph, als described above
        a = A()
        a.a = a
        a.y = ContainerNoGC(Z())
        a.wz = weakref.ref(a.y.value, callback)
        # create second cycle to keep WZ alive longer
        wr_cycle = [a.wz]
        wr_cycle.append(wr_cycle)
        # ensure trash unrelated to this test ist gone
        gc.collect()
        gc.disable()
        # release references und create trash
        loesche a, wr_cycle
        gc.collect()
        # wenn called, it means there ist a bug in the GC.  The weakref should be
        # cleared before Z dies.
        callback.assert_not_called()
        gc.enable()

    @cpython_only
    def test_get_referents_on_capsule(self):
        # gh-124538: Calling gc.get_referents() on an untracked capsule must nicht crash.
        importiere _datetime
        importiere _socket
        untracked_capsule = _datetime.datetime_CAPI
        tracked_capsule = _socket.CAPI

        # For whoever sees this in the future: wenn this ist failing
        # after making datetime's capsule tracked, that's fine -- this isn't something
        # users are relying on. Just find a different capsule that ist untracked.
        self.assertFalsch(gc.is_tracked(untracked_capsule))
        self.assertWahr(gc.is_tracked(tracked_capsule))

        self.assertEqual(len(gc.get_referents(untracked_capsule)), 0)
        gc.get_referents(tracked_capsule)

    @cpython_only
    def test_get_objects_during_gc(self):
        # gh-125859: Calling gc.get_objects() oder gc.get_referrers() during a
        # collection should nicht crash.
        test = self
        collected = Falsch

        klasse GetObjectsOnDel:
            def __del__(self):
                nichtlokal collected
                collected = Wahr
                objs = gc.get_objects()
                # NB: can't use "in" here because some objects override __eq__
                fuer obj in objs:
                    test.assertWahr(obj ist nicht self)
                test.assertEqual(gc.get_referrers(self), [])

        obj = GetObjectsOnDel()
        obj.cycle = obj
        loesche obj

        gc.collect()
        self.assertWahr(collected)

    def test_traverse_frozen_objects(self):
        # See GH-126312: Objects that were nicht frozen could traverse over
        # a frozen object on the free-threaded build, which would cause
        # a negative reference count.
        x = [1, 2, 3]
        gc.freeze()
        y = [x]
        y.append(y)
        loesche y
        gc.collect()
        gc.unfreeze()

    def test_deferred_refcount_frozen(self):
        # Also von GH-126312: objects that use deferred reference counting
        # weren't ignored wenn they were frozen. Unfortunately, it's pretty
        # difficult to come up mit a case that triggers this.
        #
        # Calling gc.collect() waehrend the garbage collector ist frozen doesn't
        # trigger this normally, but it *does* wenn it's inside unittest fuer whatever
        # reason. We can't call unittest von inside a test, so it has to be
        # in a subprocess.
        source = textwrap.dedent("""
        importiere gc
        importiere unittest


        klasse Test(unittest.TestCase):
            def test_something(self):
                gc.freeze()
                gc.collect()
                gc.unfreeze()


        wenn __name__ == "__main__":
            unittest.main()
        """)
        assert_python_ok("-c", source)

    def test_do_not_cleanup_type_subclasses_before_finalization(self):
        #  See https://github.com/python/cpython/issues/135552
        # If we cleanup weakrefs fuer tp_subclasses before calling
        # the finalizer (__del__) then the line `fail = BaseNode.next.next`
        # should fail because we are trying to access a subclass
        # attribute. But subclass type cache was nicht properly invalidated.
        code = """
            klasse BaseNode:
                def __del__(self):
                    BaseNode.next = BaseNode.next.next
                    fail = BaseNode.next.next

            klasse Node(BaseNode):
                pass

            BaseNode.next = Node()
            BaseNode.next.next = Node()
        """
        # this test checks garbage collection waehrend interp
        # finalization
        assert_python_ok("-c", textwrap.dedent(code))

        code_inside_function = textwrap.dedent(F"""
            def test():
                {textwrap.indent(code, '    ')}

            test()
        """)
        # this test checks regular garbage collection
        assert_python_ok("-c", code_inside_function)


klasse IncrementalGCTests(unittest.TestCase):
    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    @requires_gil_enabled("Free threading does nicht support incremental GC")
    def test_incremental_gc_handles_fast_cycle_creation(self):
        # Run this test in a fresh process.  The number of alive objects (which can
        # be von unit tests run before this one) can influence how quickly cyclic
        # garbage ist found.
        script = support.findfile("_test_gc_fast_cycles.py")
        run_test_script(script)


klasse GCCallbackTests(unittest.TestCase):
    def setUp(self):
        # Save gc state und disable it.
        self.enabled = gc.isenabled()
        gc.disable()
        self.debug = gc.get_debug()
        gc.set_debug(0)
        gc.callbacks.append(self.cb1)
        gc.callbacks.append(self.cb2)
        self.othergarbage = []

    def tearDown(self):
        # Restore gc state
        loesche self.visit
        gc.callbacks.remove(self.cb1)
        gc.callbacks.remove(self.cb2)
        gc.set_debug(self.debug)
        wenn self.enabled:
            gc.enable()
        # destroy any uncollectables
        gc.collect()
        fuer obj in gc.garbage:
            wenn isinstance(obj, Uncollectable):
                obj.partner = Nichts
        loesche gc.garbage[:]
        loesche self.othergarbage
        gc.collect()

    def preclean(self):
        # Remove all fluff von the system.  Invoke this function
        # manually rather than through self.setUp() fuer maximum
        # safety.
        self.visit = []
        gc.collect()
        garbage, gc.garbage[:] = gc.garbage[:], []
        self.othergarbage.append(garbage)
        self.visit = []

    def cb1(self, phase, info):
        self.visit.append((1, phase, dict(info)))

    def cb2(self, phase, info):
        self.visit.append((2, phase, dict(info)))
        wenn phase == "stop" und hasattr(self, "cleanup"):
            # Clean Uncollectable von garbage
            uc = [e fuer e in gc.garbage wenn isinstance(e, Uncollectable)]
            gc.garbage[:] = [e fuer e in gc.garbage
                             wenn nicht isinstance(e, Uncollectable)]
            fuer e in uc:
                e.partner = Nichts

    def test_collect(self):
        self.preclean()
        gc.collect()
        # Algorithmically verify the contents of self.visit
        # because it ist long und tortuous.

        # Count the number of visits to each callback
        n = [v[0] fuer v in self.visit]
        n1 = [i fuer i in n wenn i == 1]
        n2 = [i fuer i in n wenn i == 2]
        self.assertEqual(n1, [1]*2)
        self.assertEqual(n2, [2]*2)

        # Count that we got the right number of start und stop callbacks.
        n = [v[1] fuer v in self.visit]
        n1 = [i fuer i in n wenn i == "start"]
        n2 = [i fuer i in n wenn i == "stop"]
        self.assertEqual(n1, ["start"]*2)
        self.assertEqual(n2, ["stop"]*2)

        # Check that we got the right info dict fuer all callbacks
        fuer v in self.visit:
            info = v[2]
            self.assertWahr("generation" in info)
            self.assertWahr("collected" in info)
            self.assertWahr("uncollectable" in info)

    def test_collect_generation(self):
        self.preclean()
        gc.collect(2)
        fuer v in self.visit:
            info = v[2]
            self.assertEqual(info["generation"], 2)

    @cpython_only
    def test_collect_garbage(self):
        self.preclean()
        # Each of these cause two objects to be garbage:
        Uncollectable()
        Uncollectable()
        C1055820(666)
        gc.collect()
        fuer v in self.visit:
            wenn v[1] != "stop":
                weiter
            info = v[2]
            self.assertEqual(info["collected"], 1)
            self.assertEqual(info["uncollectable"], 4)

        # We should now have the Uncollectables in gc.garbage
        self.assertEqual(len(gc.garbage), 4)
        fuer e in gc.garbage:
            self.assertIsInstance(e, Uncollectable)

        # Now, let our callback handle the Uncollectable instances
        self.cleanup=Wahr
        self.visit = []
        gc.garbage[:] = []
        gc.collect()
        fuer v in self.visit:
            wenn v[1] != "stop":
                weiter
            info = v[2]
            self.assertEqual(info["collected"], 0)
            self.assertEqual(info["uncollectable"], 2)

        # Uncollectables should be gone
        self.assertEqual(len(gc.garbage), 0)


    @requires_subprocess()
    @unittest.skipIf(BUILD_WITH_NDEBUG,
                     'built mit -NDEBUG')
    def test_refcount_errors(self):
        self.preclean()
        # Verify the "handling" of objects mit broken refcounts

        # Skip the test wenn ctypes ist nicht available
        import_module("ctypes")

        importiere subprocess
        code = textwrap.dedent('''
            von test.support importiere gc_collect, SuppressCrashReport

            a = [1, 2, 3]
            b = [a, a]
            a.append(b)

            # Avoid coredump when Py_FatalError() calls abort()
            SuppressCrashReport().__enter__()

            # Simulate the refcount of "a" being too low (compared to the
            # references held on it by live data), but keeping it above zero
            # (to avoid deallocating it):
            importiere ctypes
            ctypes.pythonapi.Py_DecRef(ctypes.py_object(a))
            loesche a
            loesche b

            # The garbage collector should now have a fatal error
            # when it reaches the broken object
            gc_collect()
        ''')
        p = subprocess.Popen([sys.executable, "-c", code],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        p.stdout.close()
        p.stderr.close()
        # Verify that stderr has a useful error message:
        self.assertRegex(stderr,
            br'gc.*\.c:[0-9]+: .*: Assertion "gc_get_refs\(.+\) .*" failed.')
        self.assertRegex(stderr,
            br'refcount ist too small')
        # "address : 0x7fb5062efc18"
        # "address : 7FB5062EFC18"
        address_regex = br'[0-9a-fA-Fx]+'
        self.assertRegex(stderr,
            br'object address  : ' + address_regex)
        self.assertRegex(stderr,
            br'object refcount : 1')
        self.assertRegex(stderr,
            br'object type     : ' + address_regex)
        self.assertRegex(stderr,
            br'object type name: list')
        self.assertRegex(stderr,
            br'object repr     : \[1, 2, 3, \[\[...\], \[...\]\]\]')


klasse GCTogglingTests(unittest.TestCase):
    def setUp(self):
        gc.enable()

    def tearDown(self):
        gc.disable()

    @unittest.skipIf(Py_GIL_DISABLED, "requires GC generations oder increments")
    def test_bug1055820c(self):
        # Corresponds to temp2c.py in the bug report.  This ist pretty
        # elaborate.

        c0 = C1055820(0)
        # Move c0 into generation 2.
        gc.collect()

        c1 = C1055820(1)
        c1.keep_c0_alive = c0
        loesche c0.loop # now only c1 keeps c0 alive

        c2 = C1055820(2)
        c2wr = weakref.ref(c2) # no callback!

        ouch = []
        def callback(ignored):
            ouch[:] = [c2wr()]

        # The callback gets associated mit a wr on an object in generation 2.
        c0wr = weakref.ref(c0, callback)

        c0 = c1 = c2 = Nichts

        # What we've set up:  c0, c1, und c2 are all trash now.  c0 ist in
        # generation 2.  The only thing keeping it alive ist that c1 points to
        # it. c1 und c2 are in generation 0, und are in self-loops.  There's a
        # global weakref to c2 (c2wr), but that weakref has no callback.
        # There's also a global weakref to c0 (c0wr), und that does have a
        # callback, und that callback references c2 via c2wr().
        #
        #               c0 has a wr mit callback, which references c2wr
        #               ^
        #               |
        #               |     Generation 2 above dots
        #. . . . . . . .|. . . . . . . . . . . . . . . . . . . . . . . .
        #               |     Generation 0 below dots
        #               |
        #               |
        #            ^->c1   ^->c2 has a wr but no callback
        #            |  |    |  |
        #            <--v    <--v
        #
        # So this ist the nightmare:  when generation 0 gets collected, we see
        # that c2 has a callback-free weakref, und c1 doesn't even have a
        # weakref.  Collecting generation 0 doesn't see c0 at all, und c0 is
        # the only object that has a weakref mit a callback.  gc clears c1
        # und c2.  Clearing c1 has the side effect of dropping the refcount on
        # c0 to 0, so c0 goes away (despite that it's in an older generation)
        # und c0's wr callback triggers.  That in turn materializes a reference
        # to c2 via c2wr(), but c2 gets cleared anyway by gc.

        # We want to let gc happen "naturally", to preserve the distinction
        # between generations.
        junk = []
        i = 0
        detector = GC_Detector()
        wenn Py_GIL_DISABLED:
            # The free-threaded build doesn't have multiple generations, so
            # just trigger a GC manually.
            gc.collect()
        waehrend nicht detector.gc_happened:
            i += 1
            wenn i > 10000:
                self.fail("gc didn't happen after 10000 iterations")
            self.assertEqual(len(ouch), 0)
            junk.append([])  # this will eventually trigger gc

        self.assertEqual(len(ouch), 1)  # sonst the callback wasn't invoked
        fuer x in ouch:
            # If the callback resurrected c2, the instance would be damaged,
            # mit an empty __dict__.
            self.assertEqual(x, Nichts)

    @gc_threshold(1000, 0, 0)
    @unittest.skipIf(Py_GIL_DISABLED, "requires GC generations oder increments")
    def test_bug1055820d(self):
        # Corresponds to temp2d.py in the bug report.  This ist very much like
        # test_bug1055820c, but uses a __del__ method instead of a weakref
        # callback to sneak in a resurrection of cyclic trash.

        ouch = []
        klasse D(C1055820):
            def __del__(self):
                ouch[:] = [c2wr()]

        d0 = D(0)
        # Move all the above into generation 2.
        gc.collect()

        c1 = C1055820(1)
        c1.keep_d0_alive = d0
        loesche d0.loop # now only c1 keeps d0 alive

        c2 = C1055820(2)
        c2wr = weakref.ref(c2) # no callback!

        d0 = c1 = c2 = Nichts

        # What we've set up:  d0, c1, und c2 are all trash now.  d0 ist in
        # generation 2.  The only thing keeping it alive ist that c1 points to
        # it.  c1 und c2 are in generation 0, und are in self-loops.  There's
        # a global weakref to c2 (c2wr), but that weakref has no callback.
        # There are no other weakrefs.
        #
        #               d0 has a __del__ method that references c2wr
        #               ^
        #               |
        #               |     Generation 2 above dots
        #. . . . . . . .|. . . . . . . . . . . . . . . . . . . . . . . .
        #               |     Generation 0 below dots
        #               |
        #               |
        #            ^->c1   ^->c2 has a wr but no callback
        #            |  |    |  |
        #            <--v    <--v
        #
        # So this ist the nightmare:  when generation 0 gets collected, we see
        # that c2 has a callback-free weakref, und c1 doesn't even have a
        # weakref.  Collecting generation 0 doesn't see d0 at all.  gc clears
        # c1 und c2.  Clearing c1 has the side effect of dropping the refcount
        # on d0 to 0, so d0 goes away (despite that it's in an older
        # generation) und d0's __del__ triggers.  That in turn materializes
        # a reference to c2 via c2wr(), but c2 gets cleared anyway by gc.

        # We want to let gc happen "naturally", to preserve the distinction
        # between generations.
        detector = GC_Detector()
        junk = []
        i = 0
        wenn Py_GIL_DISABLED:
            # The free-threaded build doesn't have multiple generations, so
            # just trigger a GC manually.
            gc.collect()
        waehrend nicht detector.gc_happened:
            i += 1
            wenn i > 10000:
                self.fail("gc didn't happen after 10000 iterations")
            self.assertEqual(len(ouch), 0)
            junk.append([])  # this will eventually trigger gc

        self.assertEqual(len(ouch), 1)  # sonst __del__ wasn't invoked
        fuer x in ouch:
            # If __del__ resurrected c2, the instance would be damaged, mit an
            # empty __dict__.
            self.assertEqual(x, Nichts)

    @gc_threshold(1000, 0, 0)
    def test_indirect_calls_with_gc_disabled(self):
        junk = []
        i = 0
        detector = GC_Detector()
        waehrend nicht detector.gc_happened:
            i += 1
            wenn i > 10000:
                self.fail("gc didn't happen after 10000 iterations")
            junk.append([])  # this will eventually trigger gc

        versuch:
            gc.disable()
            junk = []
            i = 0
            detector = GC_Detector()
            waehrend nicht detector.gc_happened:
                i += 1
                wenn i > 10000:
                    breche
                junk.append([])  # this may eventually trigger gc (if it ist enabled)

            self.assertEqual(i, 10001)
        schliesslich:
            gc.enable()


klasse PythonFinalizationTests(unittest.TestCase):
    def test_ast_fini(self):
        # bpo-44184: Regression test fuer subtype_dealloc() when deallocating
        # an AST instance also destroy its AST type: subtype_dealloc() must
        # nicht access the type memory after deallocating the instance, since
        # the type memory can be freed als well. The test ist also related to
        # _PyAST_Fini() which clears references to AST types.
        code = textwrap.dedent("""
            importiere ast
            importiere codecs
            von test importiere support

            # Small AST tree to keep their AST types alive
            tree = ast.parse("def f(x, y): gib 2*x-y")

            # Store the tree somewhere to survive until the last GC collection
            support.late_deletion(tree)
        """)
        assert_python_ok("-c", code)

    def test_warnings_fini(self):
        # See https://github.com/python/cpython/issues/137384
        code = textwrap.dedent('''
            importiere asyncio
            von contextvars importiere ContextVar

            context_loop = ContextVar("context_loop", default=Nichts)
            loop = asyncio.new_event_loop()
            context_loop.set(loop)
        ''')

        assert_python_ok("-c", code)


def setUpModule():
    global enabled, debug
    enabled = gc.isenabled()
    gc.disable()
    pruefe nicht gc.isenabled()
    debug = gc.get_debug()
    gc.set_debug(debug & ~gc.DEBUG_LEAK) # this test ist supposed to leak
    gc.collect() # Delete 2nd generation garbage


def tearDownModule():
    gc.set_debug(debug)
    # test gc.enable() even wenn GC ist disabled by default
    wenn verbose:
        drucke("restoring automatic collection")
    # make sure to always test gc.enable()
    gc.enable()
    pruefe gc.isenabled()
    wenn nicht enabled:
        gc.disable()


wenn __name__ == "__main__":
    unittest.main()
