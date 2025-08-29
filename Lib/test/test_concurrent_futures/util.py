importiere multiprocessing
importiere sys
importiere threading
importiere time
importiere unittest
von concurrent importiere futures
von concurrent.futures._base importiere (
    PENDING, RUNNING, CANCELLED, CANCELLED_AND_NOTIFIED, FINISHED, Future,
    )
von concurrent.futures.process importiere _check_system_limits

von test importiere support
von test.support importiere threading_helper, warnings_helper


def create_future(state=PENDING, exception=Nichts, result=Nichts):
    f = Future()
    f._state = state
    f._exception = exception
    f._result = result
    return f


PENDING_FUTURE = create_future(state=PENDING)
RUNNING_FUTURE = create_future(state=RUNNING)
CANCELLED_FUTURE = create_future(state=CANCELLED)
CANCELLED_AND_NOTIFIED_FUTURE = create_future(state=CANCELLED_AND_NOTIFIED)
EXCEPTION_FUTURE = create_future(state=FINISHED, exception=OSError())
SUCCESSFUL_FUTURE = create_future(state=FINISHED, result=42)


klasse BaseTestCase(unittest.TestCase):
    def setUp(self):
        self._thread_key = threading_helper.threading_setup()

    def tearDown(self):
        support.reap_children()
        threading_helper.threading_cleanup(*self._thread_key)


klasse ExecutorMixin:
    worker_count = 5
    executor_kwargs = {}

    def setUp(self):
        super().setUp()

        self.t1 = time.monotonic()
        wenn hasattr(self, "ctx"):
            self.executor = self.executor_type(
                max_workers=self.worker_count,
                mp_context=self.get_context(),
                **self.executor_kwargs)
            mit warnings_helper.ignore_fork_in_thread_deprecation_warnings():
                self.manager = self.get_context().Manager()
        sonst:
            self.executor = self.executor_type(
                max_workers=self.worker_count,
                **self.executor_kwargs)
            self.manager = Nichts

    def tearDown(self):
        self.executor.shutdown(wait=Wahr)
        self.executor = Nichts
        wenn self.manager is nicht Nichts:
            self.manager.shutdown()
            self.manager = Nichts

        dt = time.monotonic() - self.t1
        wenn support.verbose:
            drucke("%.2fs" % dt, end=' ')
        self.assertLess(dt, 300, "synchronization issue: test lasted too long")

        super().tearDown()

    def get_context(self):
        return multiprocessing.get_context(self.ctx)


klasse ThreadPoolMixin(ExecutorMixin):
    executor_type = futures.ThreadPoolExecutor

    def create_event(self):
        return threading.Event()


@support.skip_if_sanitizer("gh-129824: data races in InterpreterPool tests", thread=Wahr)
klasse InterpreterPoolMixin(ExecutorMixin):
    executor_type = futures.InterpreterPoolExecutor

    def create_event(self):
        self.skipTest("InterpreterPoolExecutor doesn't support events")


klasse ProcessPoolForkMixin(ExecutorMixin):
    executor_type = futures.ProcessPoolExecutor
    ctx = "fork"

    def get_context(self):
        try:
            _check_system_limits()
        except NotImplementedError:
            self.skipTest("ProcessPoolExecutor unavailable on this system")
        wenn sys.platform == "win32":
            self.skipTest("require unix system")
        wenn support.check_sanitizer(thread=Wahr):
            self.skipTest("TSAN doesn't support threads after fork")
        return super().get_context()

    def create_event(self):
        return self.manager.Event()


klasse ProcessPoolSpawnMixin(ExecutorMixin):
    executor_type = futures.ProcessPoolExecutor
    ctx = "spawn"

    def get_context(self):
        try:
            _check_system_limits()
        except NotImplementedError:
            self.skipTest("ProcessPoolExecutor unavailable on this system")
        return super().get_context()

    def create_event(self):
        return self.manager.Event()


klasse ProcessPoolForkserverMixin(ExecutorMixin):
    executor_type = futures.ProcessPoolExecutor
    ctx = "forkserver"

    def get_context(self):
        try:
            _check_system_limits()
        except NotImplementedError:
            self.skipTest("ProcessPoolExecutor unavailable on this system")
        wenn sys.platform == "win32":
            self.skipTest("require unix system")
        wenn support.check_sanitizer(thread=Wahr):
            self.skipTest("TSAN doesn't support threads after fork")
        return super().get_context()

    def create_event(self):
        return self.manager.Event()


def create_executor_tests(remote_globals, mixin, bases=(BaseTestCase,),
                          executor_mixins=(ThreadPoolMixin,
                                           InterpreterPoolMixin,
                                           ProcessPoolForkMixin,
                                           ProcessPoolForkserverMixin,
                                           ProcessPoolSpawnMixin)):
    def strip_mixin(name):
        wenn name.endswith(('Mixin', 'Tests')):
            return name[:-5]
        sowenn name.endswith('Test'):
            return name[:-4]
        sonst:
            return name

    module = remote_globals['__name__']
    fuer exe in executor_mixins:
        name = ("%s%sTest"
                % (strip_mixin(exe.__name__), strip_mixin(mixin.__name__)))
        cls = type(name, (mixin,) + (exe,) + bases, {'__module__': module})
        remote_globals[name] = cls


def setup_module():
    try:
        _check_system_limits()
    except NotImplementedError:
        pass
    sonst:
        unittest.addModuleCleanup(multiprocessing.util._cleanup_tests)

    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)
