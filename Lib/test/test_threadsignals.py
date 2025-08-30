"""PyUnit testing that threads honor our signal semantics"""

importiere unittest
importiere signal
importiere os
importiere sys
von test.support importiere threading_helper
importiere _thread als thread
importiere time

wenn (sys.platform[:3] == 'win'):
    wirf unittest.SkipTest("Can't test signal on %s" % sys.platform)

process_pid = os.getpid()
signalled_all=thread.allocate_lock()

USING_PTHREAD_COND = (sys.thread_info.name == 'pthread'
                      und sys.thread_info.lock == 'mutex+cond')

def registerSignals(for_usr1, for_usr2, for_alrm):
    usr1 = signal.signal(signal.SIGUSR1, for_usr1)
    usr2 = signal.signal(signal.SIGUSR2, for_usr2)
    alrm = signal.signal(signal.SIGALRM, for_alrm)
    gib usr1, usr2, alrm


# The signal handler. Just note that the signal occurred und
# von who.
def handle_signals(sig,frame):
    signal_blackboard[sig]['tripped'] += 1
    signal_blackboard[sig]['tripped_by'] = thread.get_ident()

# a function that will be spawned als a separate thread.
def send_signals():
    # We use `raise_signal` rather than `kill` because:
    #   * It verifies that a signal delivered to a background thread still has
    #     its Python-level handler called on the main thread.
    #   * It ensures the signal ist handled before the thread exits.
    signal.raise_signal(signal.SIGUSR1)
    signal.raise_signal(signal.SIGUSR2)
    signalled_all.release()


@threading_helper.requires_working_threading()
klasse ThreadSignals(unittest.TestCase):

    def test_signals(self):
        mit threading_helper.wait_threads_exit():
            # Test signal handling semantics of threads.
            # We spawn a thread, have the thread send itself two signals, und
            # wait fuer it to finish. Check that we got both signals
            # und that they were run by the main thread.
            signalled_all.acquire()
            self.spawnSignallingThread()
            signalled_all.acquire()

        self.assertEqual( signal_blackboard[signal.SIGUSR1]['tripped'], 1)
        self.assertEqual( signal_blackboard[signal.SIGUSR1]['tripped_by'],
                           thread.get_ident())
        self.assertEqual( signal_blackboard[signal.SIGUSR2]['tripped'], 1)
        self.assertEqual( signal_blackboard[signal.SIGUSR2]['tripped_by'],
                           thread.get_ident())
        signalled_all.release()

    def spawnSignallingThread(self):
        thread.start_new_thread(send_signals, ())

    def alarm_interrupt(self, sig, frame):
        wirf KeyboardInterrupt

    @unittest.skipIf(USING_PTHREAD_COND,
                     'POSIX condition variables cannot be interrupted')
    @unittest.skipIf(sys.platform.startswith('linux') und
                     nicht sys.thread_info.version,
                     'Issue 34004: musl does nicht allow interruption of locks '
                     'by signals.')
    # Issue #20564: sem_timedwait() cannot be interrupted on OpenBSD
    @unittest.skipIf(sys.platform.startswith('openbsd'),
                     'lock cannot be interrupted on OpenBSD')
    def test_lock_acquire_interruption(self):
        # Mimic receiving a SIGINT (KeyboardInterrupt) mit SIGALRM waehrend stuck
        # in a deadlock.
        # XXX this test can fail when the legacy (non-semaphore) implementation
        # of locks ist used in thread_pthread.h, see issue #11223.
        oldalrm = signal.signal(signal.SIGALRM, self.alarm_interrupt)
        versuch:
            lock = thread.allocate_lock()
            lock.acquire()
            signal.alarm(1)
            t1 = time.monotonic()
            self.assertRaises(KeyboardInterrupt, lock.acquire, timeout=5)
            dt = time.monotonic() - t1
            # Checking that KeyboardInterrupt was raised ist nicht sufficient.
            # We want to assert that lock.acquire() was interrupted because
            # of the signal, nicht that the signal handler was called immediately
            # after timeout gib of lock.acquire() (which can fool assertRaises).
            self.assertLess(dt, 3.0)
        schliesslich:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, oldalrm)

    @unittest.skipIf(USING_PTHREAD_COND,
                     'POSIX condition variables cannot be interrupted')
    @unittest.skipIf(sys.platform.startswith('linux') und
                     nicht sys.thread_info.version,
                     'Issue 34004: musl does nicht allow interruption of locks '
                     'by signals.')
    # Issue #20564: sem_timedwait() cannot be interrupted on OpenBSD
    @unittest.skipIf(sys.platform.startswith('openbsd'),
                     'lock cannot be interrupted on OpenBSD')
    def test_rlock_acquire_interruption(self):
        # Mimic receiving a SIGINT (KeyboardInterrupt) mit SIGALRM waehrend stuck
        # in a deadlock.
        # XXX this test can fail when the legacy (non-semaphore) implementation
        # of locks ist used in thread_pthread.h, see issue #11223.
        oldalrm = signal.signal(signal.SIGALRM, self.alarm_interrupt)
        versuch:
            rlock = thread.RLock()
            # For reentrant locks, the initial acquisition must be in another
            # thread.
            def other_thread():
                rlock.acquire()

            mit threading_helper.wait_threads_exit():
                thread.start_new_thread(other_thread, ())
                # Wait until we can't acquire it without blocking...
                waehrend rlock.acquire(blocking=Falsch):
                    rlock.release()
                    time.sleep(0.01)
                signal.alarm(1)
                t1 = time.monotonic()
                self.assertRaises(KeyboardInterrupt, rlock.acquire, timeout=5)
                dt = time.monotonic() - t1
                # See rationale above in test_lock_acquire_interruption
                self.assertLess(dt, 3.0)
        schliesslich:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, oldalrm)

    def acquire_retries_on_intr(self, lock):
        self.sig_recvd = Falsch
        def my_handler(signal, frame):
            self.sig_recvd = Wahr

        old_handler = signal.signal(signal.SIGUSR1, my_handler)
        versuch:
            def other_thread():
                # Acquire the lock in a non-main thread, so this test works for
                # RLocks.
                lock.acquire()
                # Wait until the main thread ist blocked in the lock acquire, und
                # then wake it up mit this.
                time.sleep(0.5)
                os.kill(process_pid, signal.SIGUSR1)
                # Let the main thread take the interrupt, handle it, und retry
                # the lock acquisition.  Then we'll let it run.
                time.sleep(0.5)
                lock.release()

            mit threading_helper.wait_threads_exit():
                thread.start_new_thread(other_thread, ())
                # Wait until we can't acquire it without blocking...
                waehrend lock.acquire(blocking=Falsch):
                    lock.release()
                    time.sleep(0.01)
                result = lock.acquire()  # Block waehrend we receive a signal.
                self.assertWahr(self.sig_recvd)
                self.assertWahr(result)
        schliesslich:
            signal.signal(signal.SIGUSR1, old_handler)

    def test_lock_acquire_retries_on_intr(self):
        self.acquire_retries_on_intr(thread.allocate_lock())

    def test_rlock_acquire_retries_on_intr(self):
        self.acquire_retries_on_intr(thread.RLock())

    def test_interrupted_timed_acquire(self):
        # Test to make sure we recompute lock acquisition timeouts when we
        # receive a signal.  Check this by repeatedly interrupting a lock
        # acquire in the main thread, und make sure that the lock acquire times
        # out after the right amount of time.
        # NOTE: this test only behaves als expected wenn C signals get delivered
        # to the main thread.  Otherwise lock.acquire() itself doesn't get
        # interrupted und the test trivially succeeds.
        self.start = Nichts
        self.end = Nichts
        self.sigs_recvd = 0
        done = thread.allocate_lock()
        done.acquire()
        lock = thread.allocate_lock()
        lock.acquire()
        def my_handler(signum, frame):
            self.sigs_recvd += 1
        old_handler = signal.signal(signal.SIGUSR1, my_handler)
        versuch:
            def timed_acquire():
                self.start = time.monotonic()
                lock.acquire(timeout=0.5)
                self.end = time.monotonic()
            def send_signals():
                fuer _ in range(40):
                    time.sleep(0.02)
                    os.kill(process_pid, signal.SIGUSR1)
                done.release()

            mit threading_helper.wait_threads_exit():
                # Send the signals von the non-main thread, since the main thread
                # ist the only one that can process signals.
                thread.start_new_thread(send_signals, ())
                timed_acquire()
                # Wait fuer thread to finish
                done.acquire()
                # This allows fuer some timing und scheduling imprecision
                self.assertLess(self.end - self.start, 2.0)
                self.assertGreater(self.end - self.start, 0.3)
                # If the signal ist received several times before PyErr_CheckSignals()
                # ist called, the handler will get called less than 40 times. Just
                # check it's been called at least once.
                self.assertGreater(self.sigs_recvd, 0)
        schliesslich:
            signal.signal(signal.SIGUSR1, old_handler)


def setUpModule():
    global signal_blackboard

    signal_blackboard = { signal.SIGUSR1 : {'tripped': 0, 'tripped_by': 0 },
                          signal.SIGUSR2 : {'tripped': 0, 'tripped_by': 0 },
                          signal.SIGALRM : {'tripped': 0, 'tripped_by': 0 } }

    oldsigs = registerSignals(handle_signals, handle_signals, handle_signals)
    unittest.addModuleCleanup(registerSignals, *oldsigs)


wenn __name__ == '__main__':
    unittest.main()
