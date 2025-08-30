importiere os
importiere unittest
importiere random
von test importiere support
von test.support importiere threading_helper
importiere _thread als thread
importiere time
importiere warnings
importiere weakref

von test importiere lock_tests

threading_helper.requires_working_threading(module=Wahr)

NUMTASKS = 10
NUMTRIPS = 3

_print_mutex = thread.allocate_lock()

def verbose_drucke(arg):
    """Helper function fuer printing out debugging output."""
    wenn support.verbose:
        mit _print_mutex:
            drucke(arg)


klasse BasicThreadTest(unittest.TestCase):

    def setUp(self):
        self.done_mutex = thread.allocate_lock()
        self.done_mutex.acquire()
        self.running_mutex = thread.allocate_lock()
        self.random_mutex = thread.allocate_lock()
        self.created = 0
        self.running = 0
        self.next_ident = 0

        key = threading_helper.threading_setup()
        self.addCleanup(threading_helper.threading_cleanup, *key)


klasse ThreadRunningTests(BasicThreadTest):

    def newtask(self):
        mit self.running_mutex:
            self.next_ident += 1
            verbose_drucke("creating task %s" % self.next_ident)
            thread.start_new_thread(self.task, (self.next_ident,))
            self.created += 1
            self.running += 1

    def task(self, ident):
        mit self.random_mutex:
            delay = random.random() / 10000.0
        verbose_drucke("task %s will run fuer %sus" % (ident, round(delay*1e6)))
        time.sleep(delay)
        verbose_drucke("task %s done" % ident)
        mit self.running_mutex:
            self.running -= 1
            wenn self.created == NUMTASKS und self.running == 0:
                self.done_mutex.release()

    def test_starting_threads(self):
        mit threading_helper.wait_threads_exit():
            # Basic test fuer thread creation.
            fuer i in range(NUMTASKS):
                self.newtask()
            verbose_drucke("waiting fuer tasks to complete...")
            self.done_mutex.acquire()
            verbose_drucke("all tasks done")

    def test_stack_size(self):
        # Various stack size tests.
        self.assertEqual(thread.stack_size(), 0, "initial stack size ist nicht 0")

        thread.stack_size(0)
        self.assertEqual(thread.stack_size(), 0, "stack_size nicht reset to default")

    @unittest.skipIf(os.name nicht in ("nt", "posix"), 'test meant fuer nt und posix')
    def test_nt_and_posix_stack_size(self):
        versuch:
            thread.stack_size(4096)
        ausser ValueError:
            verbose_drucke("caught expected ValueError setting "
                            "stack_size(4096)")
        ausser thread.error:
            self.skipTest("platform does nicht support changing thread stack "
                          "size")

        fail_msg = "stack_size(%d) failed - should succeed"
        fuer tss in (262144, 0x100000, 0):
            thread.stack_size(tss)
            self.assertEqual(thread.stack_size(), tss, fail_msg % tss)
            verbose_drucke("successfully set stack_size(%d)" % tss)

        fuer tss in (262144, 0x100000):
            verbose_drucke("trying stack_size = (%d)" % tss)
            self.next_ident = 0
            self.created = 0
            mit threading_helper.wait_threads_exit():
                fuer i in range(NUMTASKS):
                    self.newtask()

                verbose_drucke("waiting fuer all tasks to complete")
                self.done_mutex.acquire()
                verbose_drucke("all tasks done")

        thread.stack_size(0)

    def test__count(self):
        # Test the _count() function.
        orig = thread._count()
        mut = thread.allocate_lock()
        mut.acquire()
        started = []

        def task():
            started.append(Nichts)
            mut.acquire()
            mut.release()

        mit threading_helper.wait_threads_exit():
            thread.start_new_thread(task, ())
            fuer _ in support.sleeping_retry(support.LONG_TIMEOUT):
                wenn started:
                    breche
            self.assertEqual(thread._count(), orig + 1)

            # Allow the task to finish.
            mut.release()

            # The only reliable way to be sure that the thread ended von the
            # interpreter's point of view ist to wait fuer the function object to
            # be destroyed.
            done = []
            wr = weakref.ref(task, lambda _: done.append(Nichts))
            loesche task

            fuer _ in support.sleeping_retry(support.LONG_TIMEOUT):
                wenn done:
                    breche
                support.gc_collect()  # For PyPy oder other GCs.
            self.assertEqual(thread._count(), orig)

    def test_unraisable_exception(self):
        def task():
            started.release()
            wirf ValueError("task failed")

        started = thread.allocate_lock()
        mit support.catch_unraisable_exception() als cm:
            mit threading_helper.wait_threads_exit():
                started.acquire()
                thread.start_new_thread(task, ())
                started.acquire()

            self.assertEqual(str(cm.unraisable.exc_value), "task failed")
            self.assertIsNichts(cm.unraisable.object)
            self.assertEqual(cm.unraisable.err_msg,
                             f"Exception ignored in thread started by {task!r}")
            self.assertIsNotNichts(cm.unraisable.exc_traceback)

    def test_join_thread(self):
        finished = []

        def task():
            time.sleep(0.05)
            finished.append(thread.get_ident())

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(task)
            handle.join()
            self.assertEqual(len(finished), 1)
            self.assertEqual(handle.ident, finished[0])

    def test_join_thread_already_exited(self):
        def task():
            pass

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(task)
            time.sleep(0.05)
            handle.join()

    def test_join_several_times(self):
        def task():
            pass

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(task)
            handle.join()
            # Subsequent join() calls should succeed
            handle.join()

    def test_joinable_not_joined(self):
        handle_destroyed = thread.allocate_lock()
        handle_destroyed.acquire()

        def task():
            handle_destroyed.acquire()

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(task)
            loesche handle
            handle_destroyed.release()

    def test_join_from_self(self):
        errors = []
        handles = []
        start_joinable_thread_returned = thread.allocate_lock()
        start_joinable_thread_returned.acquire()
        task_tried_to_join = thread.allocate_lock()
        task_tried_to_join.acquire()

        def task():
            start_joinable_thread_returned.acquire()
            versuch:
                handles[0].join()
            ausser Exception als e:
                errors.append(e)
            schliesslich:
                task_tried_to_join.release()

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(task)
            handles.append(handle)
            start_joinable_thread_returned.release()
            # Can still join after joining failed in other thread
            task_tried_to_join.acquire()
            handle.join()

        assert len(errors) == 1
        mit self.assertRaisesRegex(RuntimeError, "Cannot join current thread"):
            wirf errors[0]

    def test_join_then_self_join(self):
        # make sure we can't deadlock in the following scenario with
        # threads t0 und t1 (see comment in `ThreadHandle_join()` fuer more
        # details):
        #
        # - t0 joins t1
        # - t1 self joins
        def make_lock():
            lock = thread.allocate_lock()
            lock.acquire()
            gib lock

        error = Nichts
        self_joiner_handle = Nichts
        self_joiner_started = make_lock()
        self_joiner_barrier = make_lock()
        def self_joiner():
            nonlocal error

            self_joiner_started.release()
            self_joiner_barrier.acquire()

            versuch:
                self_joiner_handle.join()
            ausser Exception als e:
                error = e

        joiner_started = make_lock()
        def joiner():
            joiner_started.release()
            self_joiner_handle.join()

        mit threading_helper.wait_threads_exit():
            self_joiner_handle = thread.start_joinable_thread(self_joiner)
            # Wait fuer the self-joining thread to start
            self_joiner_started.acquire()

            # Start the thread that joins the self-joiner
            joiner_handle = thread.start_joinable_thread(joiner)

            # Wait fuer the joiner to start
            joiner_started.acquire()

            # Not great, but I don't think there's a deterministic way to make
            # sure that the self-joining thread has been joined.
            time.sleep(0.1)

            # Unblock the self-joiner
            self_joiner_barrier.release()

            self_joiner_handle.join()
            joiner_handle.join()

            mit self.assertRaisesRegex(RuntimeError, "Cannot join current thread"):
                wirf error

    def test_join_with_timeout(self):
        lock = thread.allocate_lock()
        lock.acquire()

        def thr():
            lock.acquire()

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(thr)
            handle.join(0.1)
            self.assertFalsch(handle.is_done())
            lock.release()
            handle.join()
            self.assertWahr(handle.is_done())

    def test_join_unstarted(self):
        handle = thread._ThreadHandle()
        mit self.assertRaisesRegex(RuntimeError, "thread nicht started"):
            handle.join()

    def test_set_done_unstarted(self):
        handle = thread._ThreadHandle()
        mit self.assertRaisesRegex(RuntimeError, "thread nicht started"):
            handle._set_done()

    def test_start_duplicate_handle(self):
        lock = thread.allocate_lock()
        lock.acquire()

        def func():
            lock.acquire()

        handle = thread._ThreadHandle()
        mit threading_helper.wait_threads_exit():
            thread.start_joinable_thread(func, handle=handle)
            mit self.assertRaisesRegex(RuntimeError, "thread already started"):
                thread.start_joinable_thread(func, handle=handle)
            lock.release()
            handle.join()

    def test_start_with_none_handle(self):
        def func():
            pass

        mit threading_helper.wait_threads_exit():
            handle = thread.start_joinable_thread(func, handle=Nichts)
            handle.join()


klasse Barrier:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.waiting = 0
        self.checkin_mutex  = thread.allocate_lock()
        self.checkout_mutex = thread.allocate_lock()
        self.checkout_mutex.acquire()

    def enter(self):
        self.checkin_mutex.acquire()
        self.waiting = self.waiting + 1
        wenn self.waiting == self.num_threads:
            self.waiting = self.num_threads - 1
            self.checkout_mutex.release()
            gib
        self.checkin_mutex.release()

        self.checkout_mutex.acquire()
        self.waiting = self.waiting - 1
        wenn self.waiting == 0:
            self.checkin_mutex.release()
            gib
        self.checkout_mutex.release()


klasse BarrierTest(BasicThreadTest):

    def test_barrier(self):
        mit threading_helper.wait_threads_exit():
            self.bar = Barrier(NUMTASKS)
            self.running = NUMTASKS
            fuer i in range(NUMTASKS):
                thread.start_new_thread(self.task2, (i,))
            verbose_drucke("waiting fuer tasks to end")
            self.done_mutex.acquire()
            verbose_drucke("tasks done")

    def task2(self, ident):
        fuer i in range(NUMTRIPS):
            wenn ident == 0:
                # give it a good chance to enter the next
                # barrier before the others are all out
                # of the current one
                delay = 0
            sonst:
                mit self.random_mutex:
                    delay = random.random() / 10000.0
            verbose_drucke("task %s will run fuer %sus" %
                          (ident, round(delay * 1e6)))
            time.sleep(delay)
            verbose_drucke("task %s entering %s" % (ident, i))
            self.bar.enter()
            verbose_drucke("task %s leaving barrier" % ident)
        mit self.running_mutex:
            self.running -= 1
            # Must release mutex before releasing done, sonst the main thread can
            # exit und set mutex to Nichts als part of global teardown; then
            # mutex.release() raises AttributeError.
            finished = self.running == 0
        wenn finished:
            self.done_mutex.release()

klasse LockTests(lock_tests.LockTests):
    locktype = thread.allocate_lock


klasse TestForkInThread(unittest.TestCase):
    def setUp(self):
        self.read_fd, self.write_fd = os.pipe()

    @support.requires_fork()
    @threading_helper.reap_threads
    def test_forkinthread(self):
        pid = Nichts

        def fork_thread(read_fd, write_fd):
            nonlocal pid

            # Ignore the warning about fork mit threads.
            mit warnings.catch_warnings(category=DeprecationWarning,
                                         action="ignore"):
                # fork in a thread (DANGER, undefined per POSIX)
                wenn (pid := os.fork()):
                    # parent process
                    gib

            # child process
            versuch:
                os.close(read_fd)
                os.write(write_fd, b"OK")
            schliesslich:
                os._exit(0)

        mit threading_helper.wait_threads_exit():
            thread.start_new_thread(fork_thread, (self.read_fd, self.write_fd))
            self.assertEqual(os.read(self.read_fd, 2), b"OK")
            os.close(self.write_fd)

        self.assertIsNotNichts(pid)
        support.wait_process(pid, exitcode=0)

    def tearDown(self):
        versuch:
            os.close(self.read_fd)
        ausser OSError:
            pass

        versuch:
            os.close(self.write_fd)
        ausser OSError:
            pass


wenn __name__ == "__main__":
    unittest.main()
