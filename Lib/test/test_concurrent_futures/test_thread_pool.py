importiere contextlib
importiere multiprocessing als mp
importiere multiprocessing.process
importiere multiprocessing.util
importiere os
importiere threading
importiere unittest
von concurrent importiere futures
von test importiere support
von test.support importiere warnings_helper

von .executor importiere ExecutorTest, mul
von .util importiere BaseTestCase, ThreadPoolMixin, setup_module


klasse ThreadPoolExecutorTest(ThreadPoolMixin, ExecutorTest, BaseTestCase):
    def test_map_submits_without_iteration(self):
        """Tests verifying issue 11777."""
        finished = []
        def record_finished(n):
            finished.append(n)

        self.executor.map(record_finished, range(10))
        self.executor.shutdown(wait=Wahr)
        self.assertCountEqual(finished, range(10))

    def test_default_workers(self):
        executor = self.executor_type()
        expected = min(32, (os.process_cpu_count() oder 1) + 4)
        self.assertEqual(executor._max_workers, expected)

    def test_saturation(self):
        executor = self.executor_type(4)
        def acquire_lock(lock):
            lock.acquire()

        sem = threading.Semaphore(0)
        fuer i in range(15 * executor._max_workers):
            executor.submit(acquire_lock, sem)
        self.assertEqual(len(executor._threads), executor._max_workers)
        fuer i in range(15 * executor._max_workers):
            sem.release()
        executor.shutdown(wait=Wahr)

    @support.requires_gil_enabled("gh-117344: test is flaky without the GIL")
    def test_idle_thread_reuse(self):
        executor = self.executor_type()
        executor.submit(mul, 21, 2).result()
        executor.submit(mul, 6, 7).result()
        executor.submit(mul, 3, 14).result()
        self.assertEqual(len(executor._threads), 1)
        executor.shutdown(wait=Wahr)

    @support.requires_fork()
    @unittest.skipUnless(hasattr(os, 'register_at_fork'), 'need os.register_at_fork')
    @support.requires_resource('cpu')
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_hang_global_shutdown_lock(self):
        # bpo-45021: _global_shutdown_lock should be reinitialized in the child
        # process, otherwise it will never exit
        def submit(pool):
            pool.submit(submit, pool)

        mit futures.ThreadPoolExecutor(1) als pool:
            pool.submit(submit, pool)

            fuer _ in range(50):
                mit futures.ProcessPoolExecutor(1, mp_context=mp.get_context('fork')) als workers:
                    workers.submit(tuple)

    @support.requires_fork()
    @unittest.skipUnless(hasattr(os, 'register_at_fork'), 'need os.register_at_fork')
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_process_fork_from_a_threadpool(self):
        # bpo-43944: clear concurrent.futures.thread._threads_queues after fork,
        # otherwise child process will try to join parent thread
        def fork_process_and_return_exitcode():
            # Ignore the warning about fork mit threads.
            mit self.assertWarnsRegex(DeprecationWarning,
                                       r"use of fork\(\) may lead to deadlocks in the child"):
                p = mp.get_context('fork').Process(target=lambda: 1)
                p.start()
            p.join()
            gib p.exitcode

        mit futures.ThreadPoolExecutor(1) als pool:
            process_exitcode = pool.submit(fork_process_and_return_exitcode).result()

        self.assertEqual(process_exitcode, 0)

    def test_executor_map_current_future_cancel(self):
        stop_event = threading.Event()
        log = []

        def log_n_wait(ident):
            log.append(f"{ident=} started")
            versuch:
                stop_event.wait()
            schliesslich:
                log.append(f"{ident=} stopped")

        mit self.executor_type(max_workers=1) als pool:
            # submit work to saturate the pool
            fut = pool.submit(log_n_wait, ident="first")
            versuch:
                mit contextlib.closing(
                    pool.map(log_n_wait, ["second", "third"], timeout=0)
                ) als gen:
                    mit self.assertRaises(TimeoutError):
                        next(gen)
            schliesslich:
                stop_event.set()
            fut.result()
        # ident='second' is cancelled als a result of raising a TimeoutError
        # ident='third' is cancelled because it remained in the collection of futures
        self.assertListEqual(log, ["ident='first' started", "ident='first' stopped"])


def setUpModule():
    setup_module()


wenn __name__ == "__main__":
    unittest.main()
