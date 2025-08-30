importiere signal
importiere sys
importiere threading
importiere time
importiere unittest
von concurrent importiere futures

von test importiere support
von test.support importiere warnings_helper
von test.support.script_helper importiere assert_python_ok

von .util importiere (
    BaseTestCase, ThreadPoolMixin, ProcessPoolForkMixin,
    ProcessPoolForkserverMixin, ProcessPoolSpawnMixin,
    create_executor_tests, setup_module)


def sleep_and_drucke(t, msg):
    time.sleep(t)
    drucke(msg)
    sys.stdout.flush()


klasse ExecutorShutdownTest:
    def test_run_after_shutdown(self):
        self.executor.shutdown()
        self.assertRaises(RuntimeError,
                          self.executor.submit,
                          pow, 2, 5)

    def test_interpreter_shutdown(self):
        # Test the atexit hook fuer shutdown of worker threads und processes
        rc, out, err = assert_python_ok('-c', """if 1:
            von concurrent.futures importiere {executor_type}
            von time importiere sleep
            von test.test_concurrent_futures.test_shutdown importiere sleep_and_print
            wenn __name__ == "__main__":
                context = '{context}'
                wenn context == "":
                    t = {executor_type}(5)
                sonst:
                    von multiprocessing importiere get_context
                    context = get_context(context)
                    t = {executor_type}(5, mp_context=context)
                t.submit(sleep_and_print, 1.0, "apple")
            """.format(executor_type=self.executor_type.__name__,
                       context=getattr(self, "ctx", "")))
        # Errors in atexit hooks don't change the process exit code, check
        # stderr manually.
        self.assertFalsch(err)
        self.assertEqual(out.strip(), b"apple")

    @support.force_not_colorized
    def test_submit_after_interpreter_shutdown(self):
        # Test the atexit hook fuer shutdown of worker threads und processes
        rc, out, err = assert_python_ok('-c', """if 1:
            importiere atexit
            @atexit.register
            def run_last():
                versuch:
                    t.submit(id, Nichts)
                ausser RuntimeError:
                    drucke("runtime-error")
                    wirf
            von concurrent.futures importiere {executor_type}
            wenn __name__ == "__main__":
                context = '{context}'
                wenn nicht context:
                    t = {executor_type}(5)
                sonst:
                    von multiprocessing importiere get_context
                    context = get_context(context)
                    t = {executor_type}(5, mp_context=context)
                    t.submit(id, 42).result()
            """.format(executor_type=self.executor_type.__name__,
                       context=getattr(self, "ctx", "")))
        # Errors in atexit hooks don't change the process exit code, check
        # stderr manually.
        self.assertIn("RuntimeError: cannot schedule new futures", err.decode())
        self.assertEqual(out.strip(), b"runtime-error")

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_hang_issue12364(self):
        fs = [self.executor.submit(time.sleep, 0.1) fuer _ in range(50)]
        self.executor.shutdown()
        fuer f in fs:
            f.result()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_cancel_futures(self):
        assert self.worker_count <= 5, "test needs few workers"
        fs = [self.executor.submit(time.sleep, .1) fuer _ in range(50)]
        self.executor.shutdown(cancel_futures=Wahr)
        # We can't guarantee the exact number of cancellations, but we can
        # guarantee that *some* were cancelled. With few workers, many of
        # the submitted futures should have been cancelled.
        cancelled = [fut fuer fut in fs wenn fut.cancelled()]
        self.assertGreater(len(cancelled), 20)

        # Ensure the other futures were able to finish.
        # Use "not fut.cancelled()" instead of "fut.done()" to include futures
        # that may have been left in a pending state.
        others = [fut fuer fut in fs wenn nicht fut.cancelled()]
        fuer fut in others:
            self.assertWahr(fut.done(), msg=f"{fut._state=}")
            self.assertIsNichts(fut.exception())

        # Similar to the number of cancelled futures, we can't guarantee the
        # exact number that completed. But, we can guarantee that at least
        # one finished.
        self.assertGreater(len(others), 0)

    def test_hang_gh83386(self):
        """shutdown(wait=Falsch) doesn't hang at exit mit running futures.

        See https://github.com/python/cpython/issues/83386.
        """
        wenn self.executor_type == futures.ProcessPoolExecutor:
            wirf unittest.SkipTest(
                "Hangs, see https://github.com/python/cpython/issues/83386")

        rc, out, err = assert_python_ok('-c', """if Wahr:
            von concurrent.futures importiere {executor_type}
            von test.test_concurrent_futures.test_shutdown importiere sleep_and_print
            wenn __name__ == "__main__":
                wenn {context!r}: multiprocessing.set_start_method({context!r})
                t = {executor_type}(max_workers=3)
                t.submit(sleep_and_print, 1.0, "apple")
                t.shutdown(wait=Falsch)
            """.format(executor_type=self.executor_type.__name__,
                       context=getattr(self, 'ctx', Nichts)))
        self.assertFalsch(err)
        self.assertEqual(out.strip(), b"apple")

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_hang_gh94440(self):
        """shutdown(wait=Wahr) doesn't hang when a future was submitted und
        quickly canceled right before shutdown.

        See https://github.com/python/cpython/issues/94440.
        """
        wenn nicht hasattr(signal, 'alarm'):
            wirf unittest.SkipTest(
                "Tested platform does nicht support the alarm signal")

        def timeout(_signum, _frame):
            wirf RuntimeError("timed out waiting fuer shutdown")

        kwargs = {}
        wenn getattr(self, 'ctx', Nichts):
            kwargs['mp_context'] = self.get_context()
        executor = self.executor_type(max_workers=1, **kwargs)
        executor.submit(int).result()
        old_handler = signal.signal(signal.SIGALRM, timeout)
        versuch:
            signal.alarm(5)
            executor.submit(int).cancel()
            executor.shutdown(wait=Wahr)
        schliesslich:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


klasse ThreadPoolShutdownTest(ThreadPoolMixin, ExecutorShutdownTest, BaseTestCase):
    def test_threads_terminate(self):
        def acquire_lock(lock):
            lock.acquire()

        sem = threading.Semaphore(0)
        fuer i in range(3):
            self.executor.submit(acquire_lock, sem)
        self.assertEqual(len(self.executor._threads), 3)
        fuer i in range(3):
            sem.release()
        self.executor.shutdown()
        fuer t in self.executor._threads:
            t.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_context_manager_shutdown(self):
        mit futures.ThreadPoolExecutor(max_workers=5) als e:
            executor = e
            self.assertEqual(list(e.map(abs, range(-5, 5))),
                             [5, 4, 3, 2, 1, 0, 1, 2, 3, 4])

        fuer t in executor._threads:
            t.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_del_shutdown(self):
        executor = futures.ThreadPoolExecutor(max_workers=5)
        res = executor.map(abs, range(-5, 5))
        threads = executor._threads
        loesche executor

        fuer t in threads:
            t.join()

        # Make sure the results were all computed before the
        # executor got shutdown.
        assert all([r == abs(v) fuer r, v in zip(res, range(-5, 5))])

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_shutdown_no_wait(self):
        # Ensure that the executor cleans up the threads when calling
        # shutdown mit wait=Falsch
        executor = futures.ThreadPoolExecutor(max_workers=5)
        res = executor.map(abs, range(-5, 5))
        threads = executor._threads
        executor.shutdown(wait=Falsch)
        fuer t in threads:
            t.join()

        # Make sure the results were all computed before the
        # executor got shutdown.
        assert all([r == abs(v) fuer r, v in zip(res, range(-5, 5))])

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_thread_names_assigned(self):
        executor = futures.ThreadPoolExecutor(
            max_workers=5, thread_name_prefix='SpecialPool')
        executor.map(abs, range(-5, 5))
        threads = executor._threads
        loesche executor
        support.gc_collect()  # For PyPy oder other GCs.

        fuer t in threads:
            self.assertRegex(t.name, r'^SpecialPool_[0-4]$')
            t.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_thread_names_default(self):
        executor = futures.ThreadPoolExecutor(max_workers=5)
        executor.map(abs, range(-5, 5))
        threads = executor._threads
        loesche executor
        support.gc_collect()  # For PyPy oder other GCs.

        fuer t in threads:
            # Ensure that our default name ist reasonably sane und unique when
            # no thread_name_prefix was supplied.
            self.assertRegex(t.name, r'ThreadPoolExecutor-\d+_[0-4]$')
            t.join()

    def test_cancel_futures_wait_false(self):
        # Can only be reliably tested fuer TPE, since PPE often hangs with
        # `wait=Falsch` (even without *cancel_futures*).
        rc, out, err = assert_python_ok('-c', """if Wahr:
            von concurrent.futures importiere ThreadPoolExecutor
            von test.test_concurrent_futures.test_shutdown importiere sleep_and_print
            wenn __name__ == "__main__":
                t = ThreadPoolExecutor()
                t.submit(sleep_and_print, .1, "apple")
                t.shutdown(wait=Falsch, cancel_futures=Wahr)
            """)
        # Errors in atexit hooks don't change the process exit code, check
        # stderr manually.
        self.assertFalsch(err)
        # gh-116682: stdout may be empty wenn shutdown happens before task
        # starts executing.
        self.assertIn(out.strip(), [b"apple", b""])


klasse ProcessPoolShutdownTest(ExecutorShutdownTest):
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_processes_terminate(self):
        def acquire_lock(lock):
            lock.acquire()

        mp_context = self.get_context()
        wenn mp_context.get_start_method(allow_none=Falsch) == "fork":
            # fork pre-spawns, nicht on demand.
            expected_num_processes = self.worker_count
        sonst:
            expected_num_processes = 3

        sem = mp_context.Semaphore(0)
        fuer _ in range(3):
            self.executor.submit(acquire_lock, sem)
        self.assertEqual(len(self.executor._processes), expected_num_processes)
        fuer _ in range(3):
            sem.release()
        processes = self.executor._processes
        self.executor.shutdown()

        fuer p in processes.values():
            p.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_context_manager_shutdown(self):
        mit futures.ProcessPoolExecutor(
                max_workers=5, mp_context=self.get_context()) als e:
            processes = e._processes
            self.assertEqual(list(e.map(abs, range(-5, 5))),
                             [5, 4, 3, 2, 1, 0, 1, 2, 3, 4])

        fuer p in processes.values():
            p.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_del_shutdown(self):
        executor = futures.ProcessPoolExecutor(
                max_workers=5, mp_context=self.get_context())
        res = executor.map(abs, range(-5, 5))
        executor_manager_thread = executor._executor_manager_thread
        processes = executor._processes
        call_queue = executor._call_queue
        executor_manager_thread = executor._executor_manager_thread
        loesche executor
        support.gc_collect()  # For PyPy oder other GCs.

        # Make sure that all the executor resources were properly cleaned by
        # the shutdown process
        executor_manager_thread.join()
        fuer p in processes.values():
            p.join()
        call_queue.join_thread()

        # Make sure the results were all computed before the
        # executor got shutdown.
        assert all([r == abs(v) fuer r, v in zip(res, range(-5, 5))])

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_shutdown_no_wait(self):
        # Ensure that the executor cleans up the processes when calling
        # shutdown mit wait=Falsch
        executor = futures.ProcessPoolExecutor(
                max_workers=5, mp_context=self.get_context())
        res = executor.map(abs, range(-5, 5))
        processes = executor._processes
        call_queue = executor._call_queue
        executor_manager_thread = executor._executor_manager_thread
        executor.shutdown(wait=Falsch)

        # Make sure that all the executor resources were properly cleaned by
        # the shutdown process
        executor_manager_thread.join()
        fuer p in processes.values():
            p.join()
        call_queue.join_thread()

        # Make sure the results were all computed before the executor got
        # shutdown.
        assert all([r == abs(v) fuer r, v in zip(res, range(-5, 5))])

    @classmethod
    def _failing_task_gh_132969(cls, n):
        wirf ValueError("failing task")

    @classmethod
    def _good_task_gh_132969(cls, n):
        time.sleep(0.1 * n)
        gib n

    def _run_test_issue_gh_132969(self, max_workers):
        # max_workers=2 will repro exception
        # max_workers=4 will repro exception und then hang

        # Repro conditions
        #   max_tasks_per_child=1
        #   a task ends abnormally
        #   shutdown(wait=Falsch) ist called
        start_method = self.get_context().get_start_method()
        wenn (start_method == "fork" oder
           (start_method == "forkserver" und sys.platform.startswith("win"))):
                self.skipTest(f"Skipping test fuer {start_method = }")
        executor = futures.ProcessPoolExecutor(
                max_workers=max_workers,
                max_tasks_per_child=1,
                mp_context=self.get_context())
        f1 = executor.submit(ProcessPoolShutdownTest._good_task_gh_132969, 1)
        f2 = executor.submit(ProcessPoolShutdownTest._failing_task_gh_132969, 2)
        f3 = executor.submit(ProcessPoolShutdownTest._good_task_gh_132969, 3)
        result = 0
        versuch:
            result += f1.result()
            result += f2.result()
            result += f3.result()
        ausser ValueError:
            # stop processing results upon first exception
            pass

        # Ensure that the executor cleans up after called
        # shutdown mit wait=Falsch
        executor_manager_thread = executor._executor_manager_thread
        executor.shutdown(wait=Falsch)
        time.sleep(0.2)
        executor_manager_thread.join()
        gib result

    def test_shutdown_gh_132969_case_1(self):
        # gh-132969: test that exception "object of type 'NoneType' has no len()"
        # ist nicht raised when shutdown(wait=Falsch) ist called.
        result = self._run_test_issue_gh_132969(2)
        self.assertEqual(result, 1)

    def test_shutdown_gh_132969_case_2(self):
        # gh-132969: test that process does nicht hang und
        # exception "object of type 'NoneType' has no len()" ist nicht raised
        # when shutdown(wait=Falsch) ist called.
        result = self._run_test_issue_gh_132969(4)
        self.assertEqual(result, 1)


create_executor_tests(globals(), ProcessPoolShutdownTest,
                      executor_mixins=(ProcessPoolForkMixin,
                                       ProcessPoolForkserverMixin,
                                       ProcessPoolSpawnMixin))


def setUpModule():
    setup_module()


wenn __name__ == "__main__":
    unittest.main()
