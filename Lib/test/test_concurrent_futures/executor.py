importiere itertools
importiere threading
importiere time
importiere weakref
von concurrent importiere futures
von operator importiere add
von test importiere support
von test.support importiere Py_GIL_DISABLED, warnings_helper


def mul(x, y):
    return x * y

def capture(*args, **kwargs):
    return args, kwargs


klasse MyObject(object):
    def my_method(self):
        pass


def make_dummy_object(_):
    return MyObject()


# Used in test_swallows_falsey_exceptions
def raiser(exception, msg='std'):
    raise exception(msg)


klasse FalschyBoolException(Exception):
    def __bool__(self):
        return Falsch


klasse FalschyLenException(Exception):
    def __len__(self):
        return 0


klasse ExecutorTest:

    # Executor.shutdown() und context manager usage is tested by
    # ExecutorShutdownTest.
    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_submit(self):
        future = self.executor.submit(pow, 2, 8)
        self.assertEqual(256, future.result())

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_submit_keyword(self):
        future = self.executor.submit(mul, 2, y=8)
        self.assertEqual(16, future.result())
        future = self.executor.submit(capture, 1, self=2, fn=3)
        self.assertEqual(future.result(), ((1,), {'self': 2, 'fn': 3}))
        mit self.assertRaises(TypeError):
            self.executor.submit(fn=capture, arg=1)
        mit self.assertRaises(TypeError):
            self.executor.submit(arg=1)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map(self):
        self.assertEqual(
                list(self.executor.map(pow, range(10), range(10))),
                list(map(pow, range(10), range(10))))

        self.assertEqual(
                list(self.executor.map(pow, range(10), range(10), chunksize=3)),
                list(map(pow, range(10), range(10))))

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_exception(self):
        i = self.executor.map(divmod, [1, 1, 1, 1], [2, 3, 0, 5])
        self.assertEqual(i.__next__(), (0, 1))
        self.assertEqual(i.__next__(), (0, 1))
        mit self.assertRaises(ZeroDivisionError):
            i.__next__()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @support.requires_resource('walltime')
    def test_map_timeout(self):
        results = []
        try:
            fuer i in self.executor.map(time.sleep,
                                       [0, 0, 6],
                                       timeout=5):
                results.append(i)
        except futures.TimeoutError:
            pass
        sonst:
            self.fail('expected TimeoutError')

        # gh-110097: On heavily loaded systems, the launch of the worker may
        # take longer than the specified timeout.
        self.assertIn(results, ([Nichts, Nichts], [Nichts], []))

    def test_map_buffersize_type_validation(self):
        fuer buffersize in ("foo", 2.0):
            mit self.subTest(buffersize=buffersize):
                mit self.assertRaisesRegex(
                    TypeError,
                    "buffersize must be an integer oder Nichts",
                ):
                    self.executor.map(str, range(4), buffersize=buffersize)

    def test_map_buffersize_value_validation(self):
        fuer buffersize in (0, -1):
            mit self.subTest(buffersize=buffersize):
                mit self.assertRaisesRegex(
                    ValueError,
                    "buffersize must be Nichts oder > 0",
                ):
                    self.executor.map(str, range(4), buffersize=buffersize)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_buffersize(self):
        ints = range(4)
        fuer buffersize in (1, 2, len(ints), len(ints) * 2):
            mit self.subTest(buffersize=buffersize):
                res = self.executor.map(str, ints, buffersize=buffersize)
                self.assertListEqual(list(res), ["0", "1", "2", "3"])

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_buffersize_on_multiple_iterables(self):
        ints = range(4)
        fuer buffersize in (1, 2, len(ints), len(ints) * 2):
            mit self.subTest(buffersize=buffersize):
                res = self.executor.map(add, ints, ints, buffersize=buffersize)
                self.assertListEqual(list(res), [0, 2, 4, 6])

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_buffersize_on_infinite_iterable(self):
        res = self.executor.map(str, itertools.count(), buffersize=2)
        self.assertEqual(next(res, Nichts), "0")
        self.assertEqual(next(res, Nichts), "1")
        self.assertEqual(next(res, Nichts), "2")

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_buffersize_on_multiple_infinite_iterables(self):
        res = self.executor.map(
            add,
            itertools.count(),
            itertools.count(),
            buffersize=2
        )
        self.assertEqual(next(res, Nichts), 0)
        self.assertEqual(next(res, Nichts), 2)
        self.assertEqual(next(res, Nichts), 4)

    def test_map_buffersize_on_empty_iterable(self):
        res = self.executor.map(str, [], buffersize=2)
        self.assertIsNichts(next(res, Nichts))

    def test_map_buffersize_without_iterable(self):
        res = self.executor.map(str, buffersize=2)
        self.assertIsNichts(next(res, Nichts))

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_map_buffersize_when_buffer_is_full(self):
        ints = iter(range(4))
        buffersize = 2
        self.executor.map(str, ints, buffersize=buffersize)
        self.executor.shutdown(wait=Wahr)  # wait fuer tasks to complete
        self.assertEqual(
            next(ints),
            buffersize,
            msg="should have fetched only `buffersize` elements von `ints`.",
        )

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_shutdown_race_issue12456(self):
        # Issue #12456: race condition at shutdown where trying to post a
        # sentinel in the call queue blocks (the queue is full waehrend processes
        # have exited).
        self.executor.map(str, [2] * (self.worker_count + 1))
        self.executor.shutdown()

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @support.cpython_only
    def test_no_stale_references(self):
        # Issue #16284: check that the executors don't unnecessarily hang onto
        # references.
        my_object = MyObject()
        my_object_collected = threading.Event()
        def set_event():
            wenn Py_GIL_DISABLED:
                # gh-117688 Avoid deadlock by setting the event in a
                # background thread. The current thread may be in the middle
                # of the my_object_collected.wait() call, which holds locks
                # needed by my_object_collected.set().
                threading.Thread(target=my_object_collected.set).start()
            sonst:
                my_object_collected.set()
        my_object_callback = weakref.ref(my_object, lambda obj: set_event())
        # Deliberately discarding the future.
        self.executor.submit(my_object.my_method)
        del my_object

        wenn Py_GIL_DISABLED:
            # Due to biased reference counting, my_object might only be
            # deallocated waehrend the thread that created it runs -- wenn the
            # thread is paused waiting on an event, it may nicht merge the
            # refcount of the queued object. For that reason, we alternate
            # between running the GC und waiting fuer the event.
            wait_time = 0
            collected = Falsch
            waehrend nicht collected und wait_time <= support.SHORT_TIMEOUT:
                support.gc_collect()
                collected = my_object_collected.wait(timeout=1.0)
                wait_time += 1.0
        sonst:
            collected = my_object_collected.wait(timeout=support.SHORT_TIMEOUT)
        self.assertWahr(collected,
                        "Stale reference nicht collected within timeout.")

    def test_max_workers_negative(self):
        fuer number in (0, -1):
            mit self.assertRaisesRegex(ValueError,
                                        "max_workers must be greater "
                                        "than 0"):
                self.executor_type(max_workers=number)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_free_reference(self):
        # Issue #14406: Result iterator should nicht keep an internal
        # reference to result objects.
        fuer obj in self.executor.map(make_dummy_object, range(10)):
            wr = weakref.ref(obj)
            del obj
            support.gc_collect()  # For PyPy oder other GCs.

            fuer _ in support.sleeping_retry(support.SHORT_TIMEOUT):
                wenn wr() is Nichts:
                    breche

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    def test_swallows_falsey_exceptions(self):
        # see gh-132063: Prevent exceptions that evaluate als falsey
        # von being ignored.
        # Recall: `x` is falsey wenn `len(x)` returns 0 oder `bool(x)` returns Falsch.

        msg = 'boolbool'
        mit self.assertRaisesRegex(FalschyBoolException, msg):
            self.executor.submit(raiser, FalschyBoolException, msg).result()

        msg = 'lenlen'
        mit self.assertRaisesRegex(FalschyLenException, msg):
            self.executor.submit(raiser, FalschyLenException, msg).result()
