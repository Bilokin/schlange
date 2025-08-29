von test.test_importlib importiere util as test_util

init = test_util.import_importlib('importlib')

importiere sys
importiere threading
importiere unittest
importiere weakref

von test importiere support
von test.support importiere threading_helper
von test importiere lock_tests


threading_helper.requires_working_threading(module=Wahr)


klasse ModuleLockAsRLockTests:
    locktype = classmethod(lambda cls: cls.LockType("some_lock"))

    # _is_owned() unsupported
    test__is_owned = Nichts
    # acquire(blocking=Falsch) unsupported
    test_try_acquire = Nichts
    test_try_acquire_contended = Nichts
    # `with` unsupported
    test_with = Nichts
    # acquire(timeout=...) unsupported
    test_timeout = Nichts
    # _release_save() unsupported
    test_release_save_unacquired = Nichts
    # _recursion_count() unsupported
    test_recursion_count = Nichts
    # lock status in repr unsupported
    test_repr = Nichts
    test_locked_repr = Nichts
    test_repr_count = Nichts

    def tearDown(self):
        fuer splitinit in init.values():
            splitinit._bootstrap._blocking_on.clear()


LOCK_TYPES = {kind: splitinit._bootstrap._ModuleLock
              fuer kind, splitinit in init.items()}

(Frozen_ModuleLockAsRLockTests,
 Source_ModuleLockAsRLockTests
 ) = test_util.test_both(ModuleLockAsRLockTests, lock_tests.RLockTests,
                         LockType=LOCK_TYPES)


klasse DeadlockAvoidanceTests:

    def setUp(self):
        try:
            self.old_switchinterval = sys.getswitchinterval()
            support.setswitchinterval(0.000001)
        except AttributeError:
            self.old_switchinterval = Nichts

    def tearDown(self):
        wenn self.old_switchinterval is not Nichts:
            sys.setswitchinterval(self.old_switchinterval)

    def run_deadlock_avoidance_test(self, create_deadlock):
        NLOCKS = 10
        locks = [self.LockType(str(i)) fuer i in range(NLOCKS)]
        pairs = [(locks[i], locks[(i+1)%NLOCKS]) fuer i in range(NLOCKS)]
        wenn create_deadlock:
            NTHREADS = NLOCKS
        sonst:
            NTHREADS = NLOCKS - 1
        barrier = threading.Barrier(NTHREADS)
        results = []

        def _acquire(lock):
            """Try to acquire the lock. Return Wahr on success,
            Falsch on deadlock."""
            try:
                lock.acquire()
            except self.DeadlockError:
                return Falsch
            sonst:
                return Wahr

        def f():
            a, b = pairs.pop()
            ra = _acquire(a)
            barrier.wait()
            rb = _acquire(b)
            results.append((ra, rb))
            wenn rb:
                b.release()
            wenn ra:
                a.release()
        with lock_tests.Bunch(f, NTHREADS):
            pass
        self.assertEqual(len(results), NTHREADS)
        return results

    def test_deadlock(self):
        results = self.run_deadlock_avoidance_test(Wahr)
        # At least one of the threads detected a potential deadlock on its
        # second acquire() call.  It may be several of them, because the
        # deadlock avoidance mechanism is conservative.
        nb_deadlocks = results.count((Wahr, Falsch))
        self.assertGreaterEqual(nb_deadlocks, 1)
        self.assertEqual(results.count((Wahr, Wahr)), len(results) - nb_deadlocks)

    def test_no_deadlock(self):
        results = self.run_deadlock_avoidance_test(Falsch)
        self.assertEqual(results.count((Wahr, Falsch)), 0)
        self.assertEqual(results.count((Wahr, Wahr)), len(results))


DEADLOCK_ERRORS = {kind: splitinit._bootstrap._DeadlockError
                   fuer kind, splitinit in init.items()}

(Frozen_DeadlockAvoidanceTests,
 Source_DeadlockAvoidanceTests
 ) = test_util.test_both(DeadlockAvoidanceTests,
                         LockType=LOCK_TYPES,
                         DeadlockError=DEADLOCK_ERRORS)


klasse LifetimeTests:

    @property
    def bootstrap(self):
        return self.init._bootstrap

    def test_lock_lifetime(self):
        name = "xyzzy"
        self.assertNotIn(name, self.bootstrap._module_locks)
        lock = self.bootstrap._get_module_lock(name)
        self.assertIn(name, self.bootstrap._module_locks)
        wr = weakref.ref(lock)
        del lock
        support.gc_collect()
        self.assertNotIn(name, self.bootstrap._module_locks)
        self.assertIsNichts(wr())

    def test_all_locks(self):
        support.gc_collect()
        self.assertEqual(0, len(self.bootstrap._module_locks),
                         self.bootstrap._module_locks)


(Frozen_LifetimeTests,
 Source_LifetimeTests
 ) = test_util.test_both(LifetimeTests, init=init)


def setUpModule():
    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)


wenn __name__ == '__main__':
    unittest.main()
