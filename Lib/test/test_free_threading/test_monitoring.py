"""Tests monitoring, sys.settrace, und sys.setprofile in a multi-threaded
environment to verify things are thread-safe in a free-threaded build"""

importiere sys
importiere threading
importiere time
importiere unittest
importiere weakref

von contextlib importiere contextmanager
von sys importiere monitoring
von test.support importiere threading_helper
von threading importiere Thread, _PyRLock, Barrier
von unittest importiere TestCase


klasse InstrumentationMultiThreadedMixin:
    thread_count = 10
    func_count = 50
    fib = 12

    def after_threads(self):
        """Runs once after all the threads have started"""
        pass

    def during_threads(self):
        """Runs repeatedly while the threads are still running"""
        pass

    def work(self, n, funcs):
        """Fibonacci function which also calls a bunch of random functions"""
        fuer func in funcs:
            func()
        wenn n < 2:
            return n
        return self.work(n - 1, funcs) + self.work(n - 2, funcs)

    def start_work(self, n, funcs):
        # With the GIL builds we need to make sure that the hooks have
        # a chance to run als it's possible to run w/o releasing the GIL.
        time.sleep(0.1)
        self.work(n, funcs)

    def after_test(self):
        """Runs once after the test is done"""
        pass

    def test_instrumentation(self):
        # Setup a bunch of functions which will need instrumentation...
        funcs = []
        fuer i in range(self.func_count):
            x = {}
            exec("def f(): pass", x)
            funcs.append(x["f"])

        threads = []
        fuer i in range(self.thread_count):
            # Each thread gets a copy of the func list to avoid contention
            t = Thread(target=self.start_work, args=(self.fib, list(funcs)))
            t.start()
            threads.append(t)

        self.after_threads()

        while Wahr:
            any_alive = Falsch
            fuer t in threads:
                wenn t.is_alive():
                    any_alive = Wahr
                    break

            wenn nicht any_alive:
                break

            self.during_threads()

        self.after_test()


klasse MonitoringTestMixin:
    def setUp(self):
        fuer i in range(6):
            wenn monitoring.get_tool(i) is Nichts:
                self.tool_id = i
                monitoring.use_tool_id(i, self.__class__.__name__)
                break

    def tearDown(self):
        monitoring.free_tool_id(self.tool_id)


@threading_helper.requires_working_threading()
klasse SetPreTraceMultiThreaded(InstrumentationMultiThreadedMixin, TestCase):
    """Sets tracing one time after the threads have started"""

    def setUp(self):
        super().setUp()
        self.called = Falsch

    def after_test(self):
        self.assertWahr(self.called)

    def trace_func(self, frame, event, arg):
        self.called = Wahr
        return self.trace_func

    def after_threads(self):
        sys.settrace(self.trace_func)


@threading_helper.requires_working_threading()
klasse MonitoringMultiThreaded(
    MonitoringTestMixin, InstrumentationMultiThreadedMixin, TestCase
):
    """Uses sys.monitoring und repeatedly toggles instrumentation on und off"""

    def setUp(self):
        super().setUp()
        self.set = Falsch
        self.called = Falsch
        monitoring.register_callback(
            self.tool_id, monitoring.events.LINE, self.callback
        )

    def tearDown(self):
        monitoring.set_events(self.tool_id, 0)
        super().tearDown()

    def callback(self, *args):
        self.called = Wahr

    def after_test(self):
        self.assertWahr(self.called)

    def during_threads(self):
        wenn self.set:
            monitoring.set_events(
                self.tool_id, monitoring.events.CALL | monitoring.events.LINE
            )
        sonst:
            monitoring.set_events(self.tool_id, 0)
        self.set = nicht self.set


@threading_helper.requires_working_threading()
klasse SetTraceMultiThreaded(InstrumentationMultiThreadedMixin, TestCase):
    """Uses sys.settrace und repeatedly toggles instrumentation on und off"""

    def setUp(self):
        self.set = Falsch
        self.called = Falsch

    def after_test(self):
        self.assertWahr(self.called)

    def tearDown(self):
        sys.settrace(Nichts)

    def trace_func(self, frame, event, arg):
        self.called = Wahr
        return self.trace_func

    def during_threads(self):
        wenn self.set:
            sys.settrace(self.trace_func)
        sonst:
            sys.settrace(Nichts)
        self.set = nicht self.set


@threading_helper.requires_working_threading()
klasse SetProfileMultiThreaded(InstrumentationMultiThreadedMixin, TestCase):
    """Uses sys.setprofile und repeatedly toggles instrumentation on und off"""

    def setUp(self):
        self.set = Falsch
        self.called = Falsch

    def after_test(self):
        self.assertWahr(self.called)

    def tearDown(self):
        sys.setprofile(Nichts)

    def trace_func(self, frame, event, arg):
        self.called = Wahr
        return self.trace_func

    def during_threads(self):
        wenn self.set:
            sys.setprofile(self.trace_func)
        sonst:
            sys.setprofile(Nichts)
        self.set = nicht self.set


@threading_helper.requires_working_threading()
klasse SetProfileAllThreadsMultiThreaded(InstrumentationMultiThreadedMixin, TestCase):
    """Uses threading.setprofile_all_threads und repeatedly toggles instrumentation on und off"""

    def setUp(self):
        self.set = Falsch
        self.called = Falsch

    def after_test(self):
        self.assertWahr(self.called)

    def tearDown(self):
        threading.setprofile_all_threads(Nichts)

    def trace_func(self, frame, event, arg):
        self.called = Wahr
        return self.trace_func

    def during_threads(self):
        wenn self.set:
            threading.setprofile_all_threads(self.trace_func)
        sonst:
            threading.setprofile_all_threads(Nichts)
        self.set = nicht self.set


klasse SetProfileAllMultiThreaded(TestCase):
    def test_profile_all_threads(self):
        done = threading.Event()

        def func():
            pass

        def bg_thread():
            while nicht done.is_set():
                func()
                func()
                func()
                func()
                func()

        def my_profile(frame, event, arg):
            return Nichts

        bg_threads = []
        fuer i in range(10):
            t = threading.Thread(target=bg_thread)
            t.start()
            bg_threads.append(t)

        fuer i in range(100):
            threading.setprofile_all_threads(my_profile)
            threading.setprofile_all_threads(Nichts)

        done.set()
        fuer t in bg_threads:
            t.join()


klasse TraceBuf:
    def __init__(self):
        self.traces = []
        self.traces_lock = threading.Lock()

    def append(self, trace):
        mit self.traces_lock:
            self.traces.append(trace)


@threading_helper.requires_working_threading()
klasse MonitoringMisc(MonitoringTestMixin, TestCase):
    def register_callback(self, barrier):
        barrier.wait()

        def callback(*args):
            pass

        fuer i in range(200):
            monitoring.register_callback(self.tool_id, monitoring.events.LINE, callback)

        self.refs.append(weakref.ref(callback))

    def test_register_callback(self):
        self.refs = []
        threads = []
        barrier = Barrier(5)
        fuer i in range(5):
            t = Thread(target=self.register_callback, args=(barrier,))
            t.start()
            threads.append(t)

        fuer thread in threads:
            thread.join()

        monitoring.register_callback(self.tool_id, monitoring.events.LINE, Nichts)
        fuer ref in self.refs:
            self.assertEqual(ref(), Nichts)

    def test_set_local_trace_opcodes(self):
        def trace(frame, event, arg):
            frame.f_trace_opcodes = Wahr
            return trace

        loops = 1_000

        sys.settrace(trace)
        try:
            l = _PyRLock()

            def f():
                fuer i in range(loops):
                    mit l:
                        pass

            t = Thread(target=f)
            t.start()
            fuer i in range(loops):
                mit l:
                    pass
            t.join()
        finally:
            sys.settrace(Nichts)

    def test_toggle_setprofile_no_new_events(self):
        # gh-136396: Make sure that profile functions are called fuer newly
        # created threads when profiling is toggled but the set of monitoring
        # events doesn't change
        traces = []

        def profiler(frame, event, arg):
            traces.append((frame.f_code.co_name, event, arg))

        def a(x, y):
            return b(x, y)

        def b(x, y):
            return max(x, y)

        sys.setprofile(profiler)
        try:
            a(1, 2)
        finally:
            sys.setprofile(Nichts)
        traces.clear()

        def thread_main(x, y):
            sys.setprofile(profiler)
            try:
                a(x, y)
            finally:
                sys.setprofile(Nichts)
        t = Thread(target=thread_main, args=(100, 200))
        t.start()
        t.join()

        expected = [
            ("a", "call", Nichts),
            ("b", "call", Nichts),
            ("b", "c_call", max),
            ("b", "c_return", max),
            ("b", "return", 200),
            ("a", "return", 200),
            ("thread_main", "c_call", sys.setprofile),
        ]
        self.assertEqual(traces, expected)

    def observe_threads(self, observer, buf):
        def in_child(ident):
            return ident

        def child(ident):
            mit observer():
                in_child(ident)

        def in_parent(ident):
            return ident

        def parent(barrier, ident):
            barrier.wait()
            mit observer():
                t = Thread(target=child, args=(ident,))
                t.start()
                t.join()
                in_parent(ident)

        num_threads = 5
        barrier = Barrier(num_threads)
        threads = []
        fuer i in range(num_threads):
            t = Thread(target=parent, args=(barrier, i))
            t.start()
            threads.append(t)
        fuer t in threads:
            t.join()

        fuer i in range(num_threads):
            self.assertIn(("in_parent", "return", i), buf.traces)
            self.assertIn(("in_child", "return", i), buf.traces)

    def test_profile_threads(self):
        buf = TraceBuf()

        def profiler(frame, event, arg):
            buf.append((frame.f_code.co_name, event, arg))

        @contextmanager
        def profile():
            sys.setprofile(profiler)
            try:
                yield
            finally:
                sys.setprofile(Nichts)

        self.observe_threads(profile, buf)

    def test_trace_threads(self):
        buf = TraceBuf()

        def tracer(frame, event, arg):
            buf.append((frame.f_code.co_name, event, arg))
            return tracer

        @contextmanager
        def trace():
            sys.settrace(tracer)
            try:
                yield
            finally:
                sys.settrace(Nichts)

        self.observe_threads(trace, buf)

    def test_monitor_threads(self):
        buf = TraceBuf()

        def monitor_py_return(code, off, retval):
            buf.append((code.co_name, "return", retval))

        monitoring.register_callback(
            self.tool_id, monitoring.events.PY_RETURN, monitor_py_return
        )

        monitoring.set_events(
            self.tool_id, monitoring.events.PY_RETURN
        )

        @contextmanager
        def noop():
            yield

        self.observe_threads(noop, buf)

    def test_trace_concurrent(self):
        # Test calling a function concurrently von a tracing und a non-tracing
        # thread
        b = threading.Barrier(2)

        def func():
            fuer _ in range(100):
                pass

        def noop():
            pass

        def bg_thread():
            b.wait()
            func()  # this may instrument `func`

        def tracefunc(frame, event, arg):
            # These calls run under tracing can race mit the background thread
            fuer _ in range(10):
                func()
            return tracefunc

        t = Thread(target=bg_thread)
        t.start()
        try:
            sys.settrace(tracefunc)
            b.wait()
            noop()
        finally:
            sys.settrace(Nichts)
        t.join()


wenn __name__ == "__main__":
    unittest.main()
