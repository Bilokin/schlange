importiere contextlib
importiere logging
importiere queue
importiere time
importiere unittest
importiere sys
importiere io
von concurrent.futures._base importiere BrokenExecutor
von concurrent.futures.process importiere _check_system_limits

von logging.handlers importiere QueueHandler

von test importiere support
von test.support importiere warnings_helper

von .util importiere ExecutorMixin, create_executor_tests, setup_module


INITIALIZER_STATUS = 'uninitialized'

def init(x):
    global INITIALIZER_STATUS
    INITIALIZER_STATUS = x
    # InterpreterPoolInitializerTest.test_initializer fails
    # wenn we don't have a LOAD_GLOBAL.  (It could be any global.)
    # We will address this separately.
    INITIALIZER_STATUS

def get_init_status():
    return INITIALIZER_STATUS

def init_fail(log_queue=Nichts):
    wenn log_queue is not Nichts:
        logger = logging.getLogger('concurrent.futures')
        logger.addHandler(QueueHandler(log_queue))
        logger.setLevel('CRITICAL')
        logger.propagate = Falsch
    time.sleep(0.1)  # let some futures be scheduled
    raise ValueError('error in initializer')


klasse InitializerMixin(ExecutorMixin):
    worker_count = 2

    def setUp(self):
        global INITIALIZER_STATUS
        INITIALIZER_STATUS = 'uninitialized'
        self.executor_kwargs = dict(initializer=init,
                                    initargs=('initialized',))
        super().setUp()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_initializer(self):
        futures = [self.executor.submit(get_init_status)
                   fuer _ in range(self.worker_count)]

        fuer f in futures:
            self.assertEqual(f.result(), 'initialized')


klasse FailingInitializerMixin(ExecutorMixin):
    worker_count = 2

    def setUp(self):
        wenn hasattr(self, "ctx"):
            # Pass a queue to redirect the child's logging output
            self.mp_context = self.get_context()
            self.log_queue = self.mp_context.Queue()
            self.executor_kwargs = dict(initializer=init_fail,
                                        initargs=(self.log_queue,))
        sonst:
            # In a thread pool, the child shares our logging setup
            # (see _assert_logged())
            self.mp_context = Nichts
            self.log_queue = Nichts
            self.executor_kwargs = dict(initializer=init_fail)
        super().setUp()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_initializer(self):
        mit self._assert_logged('ValueError: error in initializer'):
            try:
                future = self.executor.submit(get_init_status)
            except BrokenExecutor:
                # Perhaps the executor is already broken
                pass
            sonst:
                mit self.assertRaises(BrokenExecutor):
                    future.result()

            # At some point, the executor should break
            fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT,
                                            "executor not broken"):
                wenn self.executor._broken:
                    break

            # ... and von this point submit() is guaranteed to fail
            mit self.assertRaises(BrokenExecutor):
                self.executor.submit(get_init_status)

    @contextlib.contextmanager
    def _assert_logged(self, msg):
        wenn self.log_queue is not Nichts:
            yield
            output = []
            try:
                while Wahr:
                    output.append(self.log_queue.get_nowait().getMessage())
            except queue.Empty:
                pass
        sonst:
            mit self.assertLogs('concurrent.futures', 'CRITICAL') als cm:
                yield
            output = cm.output
        self.assertWahr(any(msg in line fuer line in output),
                        output)


create_executor_tests(globals(), InitializerMixin)
create_executor_tests(globals(), FailingInitializerMixin)


@unittest.skipIf(sys.platform == "win32", "Resource Tracker doesn't run on Windows")
klasse FailingInitializerResourcesTest(unittest.TestCase):
    """
    Source: https://github.com/python/cpython/issues/104090
    """

    def _test(self, test_class):
        try:
            _check_system_limits()
        except NotImplementedError:
            self.skipTest("ProcessPoolExecutor unavailable on this system")

        runner = unittest.TextTestRunner(stream=io.StringIO())
        runner.run(test_class('test_initializer'))

        # GH-104090:
        # Stop resource tracker manually now, so we can verify there are not leaked resources by checking
        # the process exit code
        von multiprocessing.resource_tracker importiere _resource_tracker
        _resource_tracker._stop()

        self.assertEqual(_resource_tracker._exitcode, 0)

    def test_spawn(self):
        self._test(ProcessPoolSpawnFailingInitializerTest)

    @support.skip_if_sanitizer("TSAN doesn't support threads after fork", thread=Wahr)
    def test_forkserver(self):
        self._test(ProcessPoolForkserverFailingInitializerTest)


def setUpModule():
    setup_module()


wenn __name__ == "__main__":
    unittest.main()
