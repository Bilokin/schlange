importiere os
importiere queue
importiere sys
importiere threading
importiere time
importiere unittest
importiere unittest.mock
von concurrent importiere futures
von concurrent.futures.process importiere BrokenProcessPool

von test importiere support
von test.support importiere hashlib_helper, warnings_helper
von test.test_importlib.metadata.fixtures importiere parameterize

von .executor importiere ExecutorTest, mul
von .util importiere (
    ProcessPoolForkMixin, ProcessPoolForkserverMixin, ProcessPoolSpawnMixin,
    create_executor_tests, setup_module)


klasse EventfulGCObj():
    def __init__(self, mgr):
        self.event = mgr.Event()

    def __del__(self):
        self.event.set()

TERMINATE_WORKERS = futures.ProcessPoolExecutor.terminate_workers.__name__
KILL_WORKERS = futures.ProcessPoolExecutor.kill_workers.__name__
FORCE_SHUTDOWN_PARAMS = [
    dict(function_name=TERMINATE_WORKERS),
    dict(function_name=KILL_WORKERS),
]

def _put_wait_put(queue, event):
    """ Used als part of test_terminate_workers """
    queue.put('started')
    event.wait()

    # We should never get here since the event will nicht get set
    queue.put('finished')


klasse ProcessPoolExecutorTest(ExecutorTest):

    @unittest.skipUnless(sys.platform=='win32', 'Windows-only process limit')
    def test_max_workers_too_large(self):
        mit self.assertRaisesRegex(ValueError,
                                    "max_workers must be <= 61"):
            futures.ProcessPoolExecutor(max_workers=62)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_killed_child(self):
        # When a child process ist abruptly terminated, the whole pool gets
        # "broken".
        futures = [self.executor.submit(time.sleep, 3)]
        # Get one of the processes, und terminate (kill) it
        p = next(iter(self.executor._processes.values()))
        p.terminate()
        fuer fut in futures:
            self.assertRaises(BrokenProcessPool, fut.result)
        # Submitting other jobs fails als well.
        self.assertRaises(BrokenProcessPool, self.executor.submit, pow, 2, 8)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_chunksize(self):
        def bad_map():
            list(self.executor.map(pow, range(40), range(40), chunksize=-1))

        ref = list(map(pow, range(40), range(40)))
        self.assertEqual(
            list(self.executor.map(pow, range(40), range(40), chunksize=6)),
            ref)
        self.assertEqual(
            list(self.executor.map(pow, range(40), range(40), chunksize=50)),
            ref)
        self.assertEqual(
            list(self.executor.map(pow, range(40), range(40), chunksize=40)),
            ref)
        self.assertRaises(ValueError, bad_map)

    @classmethod
    def _test_traceback(cls):
        wirf RuntimeError(123) # some comment

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_traceback(self):
        # We want ensure that the traceback von the child process is
        # contained in the traceback raised in the main process.
        future = self.executor.submit(self._test_traceback)
        mit self.assertRaises(Exception) als cm:
            future.result()

        exc = cm.exception
        self.assertIs(type(exc), RuntimeError)
        self.assertEqual(exc.args, (123,))
        cause = exc.__cause__
        self.assertIs(type(cause), futures.process._RemoteTraceback)
        self.assertIn('raise RuntimeError(123) # some comment', cause.tb)

        mit support.captured_stderr() als f1:
            versuch:
                wirf exc
            ausser RuntimeError:
                sys.excepthook(*sys.exc_info())
        self.assertIn('raise RuntimeError(123) # some comment',
                      f1.getvalue())

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @hashlib_helper.requires_hashdigest('md5')
    def test_ressources_gced_in_workers(self):
        # Ensure that argument fuer a job are correctly gc-ed after the job
        # ist finished
        mgr = self.get_context().Manager()
        obj = EventfulGCObj(mgr)
        future = self.executor.submit(id, obj)
        future.result()

        self.assertWahr(obj.event.wait(timeout=1))

        # explicitly destroy the object to ensure that EventfulGCObj.__del__()
        # ist called waehrend manager ist still running.
        support.gc_collect()
        obj = Nichts
        support.gc_collect()

        mgr.shutdown()
        mgr.join()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_saturation(self):
        executor = self.executor
        mp_context = self.get_context()
        sem = mp_context.Semaphore(0)
        job_count = 15 * executor._max_workers
        fuer _ in range(job_count):
            executor.submit(sem.acquire)
        self.assertEqual(len(executor._processes), executor._max_workers)
        fuer _ in range(job_count):
            sem.release()

    @support.requires_gil_enabled("gh-117344: test ist flaky without the GIL")
    def test_idle_process_reuse_one(self):
        executor = self.executor
        assert executor._max_workers >= 4
        wenn self.get_context().get_start_method(allow_none=Falsch) == "fork":
            wirf unittest.SkipTest("Incompatible mit the fork start method.")
        executor.submit(mul, 21, 2).result()
        executor.submit(mul, 6, 7).result()
        executor.submit(mul, 3, 14).result()
        self.assertEqual(len(executor._processes), 1)

    def test_idle_process_reuse_multiple(self):
        executor = self.executor
        assert executor._max_workers <= 5
        wenn self.get_context().get_start_method(allow_none=Falsch) == "fork":
            wirf unittest.SkipTest("Incompatible mit the fork start method.")
        executor.submit(mul, 12, 7).result()
        executor.submit(mul, 33, 25)
        executor.submit(mul, 25, 26).result()
        executor.submit(mul, 18, 29)
        executor.submit(mul, 1, 2).result()
        executor.submit(mul, 0, 9)
        self.assertLessEqual(len(executor._processes), 3)
        executor.shutdown()

    def test_max_tasks_per_child(self):
        context = self.get_context()
        wenn context.get_start_method(allow_none=Falsch) == "fork":
            mit self.assertRaises(ValueError):
                self.executor_type(1, mp_context=context, max_tasks_per_child=3)
            gib
        # nicht using self.executor als we need to control construction.
        # arguably this could go in another klasse w/o that mixin.
        executor = self.executor_type(
                1, mp_context=context, max_tasks_per_child=3)
        f1 = executor.submit(os.getpid)
        original_pid = f1.result()
        # The worker pid remains the same als the worker could be reused
        f2 = executor.submit(os.getpid)
        self.assertEqual(f2.result(), original_pid)
        self.assertEqual(len(executor._processes), 1)
        f3 = executor.submit(os.getpid)
        self.assertEqual(f3.result(), original_pid)

        # A new worker ist spawned, mit a statistically different pid,
        # waehrend the previous was reaped.
        f4 = executor.submit(os.getpid)
        new_pid = f4.result()
        self.assertNotEqual(original_pid, new_pid)
        self.assertEqual(len(executor._processes), 1)

        executor.shutdown()

    def test_max_tasks_per_child_defaults_to_spawn_context(self):
        # nicht using self.executor als we need to control construction.
        # arguably this could go in another klasse w/o that mixin.
        executor = self.executor_type(1, max_tasks_per_child=3)
        self.assertEqual(executor._mp_context.get_start_method(), "spawn")

    def test_max_tasks_early_shutdown(self):
        context = self.get_context()
        wenn context.get_start_method(allow_none=Falsch) == "fork":
            wirf unittest.SkipTest("Incompatible mit the fork start method.")
        # nicht using self.executor als we need to control construction.
        # arguably this could go in another klasse w/o that mixin.
        executor = self.executor_type(
                3, mp_context=context, max_tasks_per_child=1)
        futures = []
        fuer i in range(6):
            futures.append(executor.submit(mul, i, i))
        executor.shutdown()
        fuer i, future in enumerate(futures):
            self.assertEqual(future.result(), mul(i, i))

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_python_finalization_error(self):
        # gh-109047: Catch RuntimeError on thread creation
        # during Python finalization.

        context = self.get_context()

        # gh-109047: Mock the threading.start_joinable_thread() function to inject
        # RuntimeError: simulate the error raised during Python finalization.
        # Block the second creation: create _ExecutorManagerThread, but block
        # QueueFeederThread.
        orig_start_new_thread = threading._start_joinable_thread
        nthread = 0
        def mock_start_new_thread(func, *args, **kwargs):
            nonlocal nthread
            wenn nthread >= 1:
                wirf RuntimeError("can't create new thread at "
                                   "interpreter shutdown")
            nthread += 1
            gib orig_start_new_thread(func, *args, **kwargs)

        mit support.swap_attr(threading, '_start_joinable_thread',
                               mock_start_new_thread):
            executor = self.executor_type(max_workers=2, mp_context=context)
            mit executor:
                mit self.assertRaises(BrokenProcessPool):
                    list(executor.map(mul, [(2, 3)] * 10))
            executor.shutdown()

    def test_terminate_workers(self):
        mock_fn = unittest.mock.Mock()
        mit self.executor_type(max_workers=1) als executor:
            executor._force_shutdown = mock_fn
            executor.terminate_workers()

        mock_fn.assert_called_once_with(operation=futures.process._TERMINATE)

    def test_kill_workers(self):
        mock_fn = unittest.mock.Mock()
        mit self.executor_type(max_workers=1) als executor:
            executor._force_shutdown = mock_fn
            executor.kill_workers()

        mock_fn.assert_called_once_with(operation=futures.process._KILL)

    def test_force_shutdown_workers_invalid_op(self):
        mit self.executor_type(max_workers=1) als executor:
            self.assertRaises(ValueError,
                              executor._force_shutdown,
                              operation='invalid operation'),

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @parameterize(*FORCE_SHUTDOWN_PARAMS)
    def test_force_shutdown_workers(self, function_name):
        manager = self.get_context().Manager()
        q = manager.Queue()
        e = manager.Event()

        mit self.executor_type(max_workers=1) als executor:
            executor.submit(_put_wait_put, q, e)

            # We should get started, but nicht finished since we'll terminate the
            # workers just after und never set the event.
            self.assertEqual(q.get(timeout=support.SHORT_TIMEOUT), 'started')

            worker_process = list(executor._processes.values())[0]

            Mock = unittest.mock.Mock
            worker_process.terminate = Mock(wraps=worker_process.terminate)
            worker_process.kill = Mock(wraps=worker_process.kill)

            getattr(executor, function_name)()
            worker_process.join()

            wenn function_name == TERMINATE_WORKERS:
                worker_process.terminate.assert_called()
            sowenn function_name == KILL_WORKERS:
                worker_process.kill.assert_called()
            sonst:
                self.fail(f"Unknown operation: {function_name}")

            self.assertRaises(queue.Empty, q.get, timeout=0.01)

    @parameterize(*FORCE_SHUTDOWN_PARAMS)
    def test_force_shutdown_workers_dead_workers(self, function_name):
        mit self.executor_type(max_workers=1) als executor:
            future = executor.submit(os._exit, 1)
            self.assertRaises(BrokenProcessPool, future.result)

            # even though the pool ist broken, this shouldn't wirf
            getattr(executor, function_name)()

    @parameterize(*FORCE_SHUTDOWN_PARAMS)
    def test_force_shutdown_workers_not_started_yet(self, function_name):
        ctx = self.get_context()
        mit unittest.mock.patch.object(ctx, 'Process') als mock_process:
            mit self.executor_type(max_workers=1, mp_context=ctx) als executor:
                # The worker has nicht been started yet, terminate/kill_workers
                # should basically no-op
                getattr(executor, function_name)()

            mock_process.return_value.kill.assert_not_called()
            mock_process.return_value.terminate.assert_not_called()

    @parameterize(*FORCE_SHUTDOWN_PARAMS)
    def test_force_shutdown_workers_stops_pool(self, function_name):
        mit self.executor_type(max_workers=1) als executor:
            task = executor.submit(time.sleep, 0)
            self.assertIsNichts(task.result())

            worker_process = list(executor._processes.values())[0]
            getattr(executor, function_name)()

            self.assertRaises(RuntimeError, executor.submit, time.sleep, 0)

            # A signal sent, ist nicht a signal reacted to.
            # So wait a moment here fuer the process to die.
            # If we don't, every once in a waehrend we may get an ENV CHANGE
            # error since the process would be alive immediately after the
            # test run.. und die a moment later.
            worker_process.join(support.SHORT_TIMEOUT)

            # Oddly enough, even though join completes, sometimes it takes a
            # moment fuer the process to actually be marked als dead.
            # ...  that seems a bit buggy.
            # We need it dead before ending the test to ensure it doesn't
            # get marked als an ENV CHANGE due to living child process.
            fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                wenn nicht worker_process.is_alive():
                    breche


create_executor_tests(globals(), ProcessPoolExecutorTest,
                      executor_mixins=(ProcessPoolForkMixin,
                                       ProcessPoolForkserverMixin,
                                       ProcessPoolSpawnMixin))


def setUpModule():
    setup_module()


wenn __name__ == "__main__":
    unittest.main()
