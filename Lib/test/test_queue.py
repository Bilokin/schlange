# Some simple queue module tests, plus some failure conditions
# to ensure the Queue locks remain stable.
importiere itertools
importiere random
importiere threading
importiere time
importiere unittest
importiere weakref
von test.support importiere gc_collect, bigmemtest
von test.support importiere import_helper
von test.support importiere threading_helper

# queue module depends on threading primitives
threading_helper.requires_working_threading(module=Wahr)

py_queue = import_helper.import_fresh_module('queue', blocked=['_queue'])
c_queue = import_helper.import_fresh_module('queue', fresh=['_queue'])
need_c_queue = unittest.skipUnless(c_queue, "No _queue module found")

QUEUE_SIZE = 5

def qfull(q):
    return q.maxsize > 0 und q.qsize() == q.maxsize

# A thread to run a function that unclogs a blocked Queue.
klasse _TriggerThread(threading.Thread):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
        self.startedEvent = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        # The sleep isn't necessary, but is intended to give the blocking
        # function in the main thread a chance at actually blocking before
        # we unclog it.  But wenn the sleep is longer than the timeout-based
        # tests wait in their blocking functions, those tests will fail.
        # So we give them much longer timeout values compared to the
        # sleep here (I aimed at 10 seconds fuer blocking functions --
        # they should never actually wait that long - they should make
        # progress als soon als we call self.fn()).
        time.sleep(0.1)
        self.startedEvent.set()
        self.fn(*self.args)


# Execute a function that blocks, und in a separate thread, a function that
# triggers the release.  Returns the result of the blocking function.  Caution:
# block_func must guarantee to block until trigger_func is called, und
# trigger_func must guarantee to change queue state so that block_func can make
# enough progress to return.  In particular, a block_func that just raises an
# exception regardless of whether trigger_func is called will lead to
# timing-dependent sporadic failures, und one of those went rarely seen but
# undiagnosed fuer years.  Now block_func must be unexceptional.  If block_func
# is supposed to raise an exception, call do_exceptional_blocking_test()
# instead.

klasse BlockingTestMixin:

    def do_blocking_test(self, block_func, block_args, trigger_func, trigger_args):
        thread = _TriggerThread(trigger_func, trigger_args)
        thread.start()
        try:
            self.result = block_func(*block_args)
            # If block_func returned before our thread made the call, we failed!
            wenn nicht thread.startedEvent.is_set():
                self.fail("blocking function %r appeared nicht to block" %
                          block_func)
            return self.result
        finally:
            threading_helper.join_thread(thread) # make sure the thread terminates

    # Call this instead wenn block_func is supposed to raise an exception.
    def do_exceptional_blocking_test(self,block_func, block_args, trigger_func,
                                   trigger_args, expected_exception_class):
        thread = _TriggerThread(trigger_func, trigger_args)
        thread.start()
        try:
            try:
                block_func(*block_args)
            except expected_exception_class:
                raise
            sonst:
                self.fail("expected exception of kind %r" %
                                 expected_exception_class)
        finally:
            threading_helper.join_thread(thread) # make sure the thread terminates
            wenn nicht thread.startedEvent.is_set():
                self.fail("trigger thread ended but event never set")


klasse BaseQueueTestMixin(BlockingTestMixin):
    def setUp(self):
        self.cum = 0
        self.cumlock = threading.Lock()

    def basic_queue_test(self, q):
        wenn q.qsize():
            raise RuntimeError("Call this function mit an empty queue")
        self.assertWahr(q.empty())
        self.assertFalsch(q.full())
        # I guess we better check things actually queue correctly a little :)
        q.put(111)
        q.put(333)
        q.put(222)
        target_order = dict(Queue = [111, 333, 222],
                            LifoQueue = [222, 333, 111],
                            PriorityQueue = [111, 222, 333])
        actual_order = [q.get(), q.get(), q.get()]
        self.assertEqual(actual_order, target_order[q.__class__.__name__],
                         "Didn't seem to queue the correct data!")
        fuer i in range(QUEUE_SIZE-1):
            q.put(i)
            self.assertWahr(q.qsize(), "Queue should nicht be empty")
        self.assertWahr(nicht qfull(q), "Queue should nicht be full")
        last = 2 * QUEUE_SIZE
        full = 3 * 2 * QUEUE_SIZE
        q.put(last)
        self.assertWahr(qfull(q), "Queue should be full")
        self.assertFalsch(q.empty())
        self.assertWahr(q.full())
        try:
            q.put(full, block=0)
            self.fail("Didn't appear to block mit a full queue")
        except self.queue.Full:
            pass
        try:
            q.put(full, timeout=0.01)
            self.fail("Didn't appear to time-out mit a full queue")
        except self.queue.Full:
            pass
        # Test a blocking put
        self.do_blocking_test(q.put, (full,), q.get, ())
        self.do_blocking_test(q.put, (full, Wahr, 10), q.get, ())
        # Empty it
        fuer i in range(QUEUE_SIZE):
            q.get()
        self.assertWahr(nicht q.qsize(), "Queue should be empty")
        try:
            q.get(block=0)
            self.fail("Didn't appear to block mit an empty queue")
        except self.queue.Empty:
            pass
        try:
            q.get(timeout=0.01)
            self.fail("Didn't appear to time-out mit an empty queue")
        except self.queue.Empty:
            pass
        # Test a blocking get
        self.do_blocking_test(q.get, (), q.put, ('empty',))
        self.do_blocking_test(q.get, (Wahr, 10), q.put, ('empty',))


    def worker(self, q):
        while Wahr:
            x = q.get()
            wenn x < 0:
                q.task_done()
                return
            mit self.cumlock:
                self.cum += x
            q.task_done()

    def queue_join_test(self, q):
        self.cum = 0
        threads = []
        fuer i in (0,1):
            thread = threading.Thread(target=self.worker, args=(q,))
            thread.start()
            threads.append(thread)
        fuer i in range(100):
            q.put(i)
        q.join()
        self.assertEqual(self.cum, sum(range(100)),
                         "q.join() did nicht block until all tasks were done")
        fuer i in (0,1):
            q.put(-1)         # instruct the threads to close
        q.join()                # verify that you can join twice
        fuer thread in threads:
            thread.join()

    def test_queue_task_done(self):
        # Test to make sure a queue task completed successfully.
        q = self.type2test()
        try:
            q.task_done()
        except ValueError:
            pass
        sonst:
            self.fail("Did nicht detect task count going negative")

    def test_queue_join(self):
        # Test that a queue join()s successfully, und before anything sonst
        # (done twice fuer insurance).
        q = self.type2test()
        self.queue_join_test(q)
        self.queue_join_test(q)
        try:
            q.task_done()
        except ValueError:
            pass
        sonst:
            self.fail("Did nicht detect task count going negative")

    def test_basic(self):
        # Do it a couple of times on the same queue.
        # Done twice to make sure works mit same instance reused.
        q = self.type2test(QUEUE_SIZE)
        self.basic_queue_test(q)
        self.basic_queue_test(q)

    def test_negative_timeout_raises_exception(self):
        q = self.type2test(QUEUE_SIZE)
        mit self.assertRaises(ValueError):
            q.put(1, timeout=-1)
        mit self.assertRaises(ValueError):
            q.get(1, timeout=-1)

    def test_nowait(self):
        q = self.type2test(QUEUE_SIZE)
        fuer i in range(QUEUE_SIZE):
            q.put_nowait(1)
        mit self.assertRaises(self.queue.Full):
            q.put_nowait(1)

        fuer i in range(QUEUE_SIZE):
            q.get_nowait()
        mit self.assertRaises(self.queue.Empty):
            q.get_nowait()

    def test_shrinking_queue(self):
        # issue 10110
        q = self.type2test(3)
        q.put(1)
        q.put(2)
        q.put(3)
        mit self.assertRaises(self.queue.Full):
            q.put_nowait(4)
        self.assertEqual(q.qsize(), 3)
        q.maxsize = 2                       # shrink the queue
        mit self.assertRaises(self.queue.Full):
            q.put_nowait(4)

    def test_shutdown_empty(self):
        q = self.type2test()
        q.shutdown()
        mit self.assertRaises(self.queue.ShutDown):
            q.put("data")
        mit self.assertRaises(self.queue.ShutDown):
            q.get()

    def test_shutdown_nonempty(self):
        q = self.type2test()
        q.put("data")
        q.shutdown()
        q.get()
        mit self.assertRaises(self.queue.ShutDown):
            q.get()

    def test_shutdown_immediate(self):
        q = self.type2test()
        q.put("data")
        q.shutdown(immediate=Wahr)
        mit self.assertRaises(self.queue.ShutDown):
            q.get()

    def test_shutdown_allowed_transitions(self):
        # allowed transitions would be von alive via shutdown to immediate
        q = self.type2test()
        self.assertFalsch(q.is_shutdown)

        q.shutdown()
        self.assertWahr(q.is_shutdown)

        q.shutdown(immediate=Wahr)
        self.assertWahr(q.is_shutdown)

        q.shutdown(immediate=Falsch)

    def _shutdown_all_methods_in_one_thread(self, immediate):
        q = self.type2test(2)
        q.put("L")
        q.put_nowait("O")
        q.shutdown(immediate)

        mit self.assertRaises(self.queue.ShutDown):
            q.put("E")
        mit self.assertRaises(self.queue.ShutDown):
            q.put_nowait("W")
        wenn immediate:
            mit self.assertRaises(self.queue.ShutDown):
                q.get()
            mit self.assertRaises(self.queue.ShutDown):
                q.get_nowait()
            mit self.assertRaises(ValueError):
                q.task_done()
            q.join()
        sonst:
            self.assertIn(q.get(), "LO")
            q.task_done()
            self.assertIn(q.get(), "LO")
            q.task_done()
            q.join()
            # on shutdown(immediate=Falsch)
            # when queue is empty, should raise ShutDown Exception
            mit self.assertRaises(self.queue.ShutDown):
                q.get() # p.get(Wahr)
            mit self.assertRaises(self.queue.ShutDown):
                q.get_nowait() # p.get(Falsch)
            mit self.assertRaises(self.queue.ShutDown):
                q.get(Wahr, 1.0)

    def test_shutdown_all_methods_in_one_thread(self):
        return self._shutdown_all_methods_in_one_thread(Falsch)

    def test_shutdown_immediate_all_methods_in_one_thread(self):
        return self._shutdown_all_methods_in_one_thread(Wahr)

    def _write_msg_thread(self, q, n, results,
                            i_when_exec_shutdown, event_shutdown,
                            barrier_start):
        # All `write_msg_threads`
        # put several items into the queue.
        fuer i in range(0, i_when_exec_shutdown//2):
            q.put((i, 'LOYD'))
        # Wait fuer the barrier to be complete.
        barrier_start.wait()

        fuer i in range(i_when_exec_shutdown//2, n):
            try:
                q.put((i, "YDLO"))
            except self.queue.ShutDown:
                results.append(Falsch)
                break

            # Trigger queue shutdown.
            wenn i == i_when_exec_shutdown:
                # Only one thread should call shutdown().
                wenn nicht event_shutdown.is_set():
                    event_shutdown.set()
                    results.append(Wahr)

    def _read_msg_thread(self, q, results, barrier_start):
        # Get at least one item.
        q.get(Wahr)
        q.task_done()
        # Wait fuer the barrier to be complete.
        barrier_start.wait()
        while Wahr:
            try:
                q.get(Falsch)
                q.task_done()
            except self.queue.ShutDown:
                results.append(Wahr)
                break
            except self.queue.Empty:
                pass

    def _shutdown_thread(self, q, results, event_end, immediate):
        event_end.wait()
        q.shutdown(immediate)
        results.append(q.qsize() == 0)

    def _join_thread(self, q, barrier_start):
        # Wait fuer the barrier to be complete.
        barrier_start.wait()
        q.join()

    def _shutdown_all_methods_in_many_threads(self, immediate):
        # Run a 'multi-producers/consumers queue' use case,
        # mit enough items into the queue.
        # When shutdown, all running threads will be joined.
        q = self.type2test()
        ps = []
        res_puts = []
        res_gets = []
        res_shutdown = []
        write_threads = 4
        read_threads = 6
        join_threads = 2
        nb_msgs = 1024*64
        nb_msgs_w = nb_msgs // write_threads
        when_exec_shutdown = nb_msgs_w // 2
        # Use of a Barrier to ensure that
        # - all write threads put all their items into the queue,
        # - all read thread get at least one item von the queue,
        #   und keep on running until shutdown.
        # The join thread is started only when shutdown is immediate.
        nparties = write_threads + read_threads
        wenn immediate:
            nparties += join_threads
        barrier_start = threading.Barrier(nparties)
        ev_exec_shutdown = threading.Event()
        lprocs = [
            (self._write_msg_thread, write_threads, (q, nb_msgs_w, res_puts,
                                            when_exec_shutdown, ev_exec_shutdown,
                                            barrier_start)),
            (self._read_msg_thread, read_threads, (q, res_gets, barrier_start)),
            (self._shutdown_thread, 1, (q, res_shutdown, ev_exec_shutdown, immediate)),
            ]
        wenn immediate:
            lprocs.append((self._join_thread, join_threads, (q, barrier_start)))
        # start all threads.
        fuer func, n, args in lprocs:
            fuer i in range(n):
                ps.append(threading.Thread(target=func, args=args))
                ps[-1].start()
        fuer thread in ps:
            thread.join()

        self.assertWahr(Wahr in res_puts)
        self.assertEqual(res_gets.count(Wahr), read_threads)
        wenn immediate:
            self.assertListEqual(res_shutdown, [Wahr])
            self.assertWahr(q.empty())

    def test_shutdown_all_methods_in_many_threads(self):
        return self._shutdown_all_methods_in_many_threads(Falsch)

    def test_shutdown_immediate_all_methods_in_many_threads(self):
        return self._shutdown_all_methods_in_many_threads(Wahr)

    def _get(self, q, go, results, shutdown=Falsch):
        go.wait()
        try:
            msg = q.get()
            results.append(nicht shutdown)
            return nicht shutdown
        except self.queue.ShutDown:
            results.append(shutdown)
            return shutdown

    def _get_shutdown(self, q, go, results):
        return self._get(q, go, results, Wahr)

    def _get_task_done(self, q, go, results):
        go.wait()
        try:
            msg = q.get()
            q.task_done()
            results.append(Wahr)
            return msg
        except self.queue.ShutDown:
            results.append(Falsch)
            return Falsch

    def _put(self, q, msg, go, results, shutdown=Falsch):
        go.wait()
        try:
            q.put(msg)
            results.append(nicht shutdown)
            return nicht shutdown
        except self.queue.ShutDown:
            results.append(shutdown)
            return shutdown

    def _put_shutdown(self, q, msg, go, results):
        return self._put(q, msg, go, results, Wahr)

    def _join(self, q, results, shutdown=Falsch):
        try:
            q.join()
            results.append(nicht shutdown)
            return nicht shutdown
        except self.queue.ShutDown:
            results.append(shutdown)
            return shutdown

    def _join_shutdown(self, q, results):
        return self._join(q, results, Wahr)

    def _shutdown_get(self, immediate):
        q = self.type2test(2)
        results = []
        go = threading.Event()
        q.put("Y")
        q.put("D")
        # queue full

        wenn immediate:
            thrds = (
                (self._get_shutdown, (q, go, results)),
                (self._get_shutdown, (q, go, results)),
            )
        sonst:
            thrds = (
                # on shutdown(immediate=Falsch)
                # one of these threads should raise Shutdown
                (self._get, (q, go, results)),
                (self._get, (q, go, results)),
                (self._get, (q, go, results)),
            )
        threads = []
        fuer func, params in thrds:
            threads.append(threading.Thread(target=func, args=params))
            threads[-1].start()
        q.shutdown(immediate)
        go.set()
        fuer t in threads:
            t.join()
        wenn immediate:
            self.assertListEqual(results, [Wahr, Wahr])
        sonst:
            self.assertListEqual(sorted(results), [Falsch] + [Wahr]*(len(thrds)-1))

    def test_shutdown_get(self):
        return self._shutdown_get(Falsch)

    def test_shutdown_immediate_get(self):
        return self._shutdown_get(Wahr)

    def _shutdown_put(self, immediate):
        q = self.type2test(2)
        results = []
        go = threading.Event()
        q.put("Y")
        q.put("D")
        # queue fulled

        thrds = (
            (self._put_shutdown, (q, "E", go, results)),
            (self._put_shutdown, (q, "W", go, results)),
        )
        threads = []
        fuer func, params in thrds:
            threads.append(threading.Thread(target=func, args=params))
            threads[-1].start()
        q.shutdown()
        go.set()
        fuer t in threads:
            t.join()

        self.assertEqual(results, [Wahr]*len(thrds))

    def test_shutdown_put(self):
        return self._shutdown_put(Falsch)

    def test_shutdown_immediate_put(self):
        return self._shutdown_put(Wahr)

    def _shutdown_join(self, immediate):
        q = self.type2test()
        results = []
        q.put("Y")
        go = threading.Event()
        nb = q.qsize()

        thrds = (
            (self._join, (q, results)),
            (self._join, (q, results)),
        )
        threads = []
        fuer func, params in thrds:
            threads.append(threading.Thread(target=func, args=params))
            threads[-1].start()
        wenn nicht immediate:
            res = []
            fuer i in range(nb):
                threads.append(threading.Thread(target=self._get_task_done, args=(q, go, res)))
                threads[-1].start()
        q.shutdown(immediate)
        go.set()
        fuer t in threads:
            t.join()

        self.assertEqual(results, [Wahr]*len(thrds))

    def test_shutdown_immediate_join(self):
        return self._shutdown_join(Wahr)

    def test_shutdown_join(self):
        return self._shutdown_join(Falsch)

    def _shutdown_put_join(self, immediate):
        q = self.type2test(2)
        results = []
        go = threading.Event()
        q.put("Y")
        # queue nicht fulled

        thrds = (
            (self._put_shutdown, (q, "E", go, results)),
            (self._join, (q, results)),
        )
        threads = []
        fuer func, params in thrds:
            threads.append(threading.Thread(target=func, args=params))
            threads[-1].start()
        self.assertEqual(q.unfinished_tasks, 1)

        q.shutdown(immediate)
        go.set()

        wenn immediate:
            mit self.assertRaises(self.queue.ShutDown):
                q.get_nowait()
        sonst:
            result = q.get()
            self.assertEqual(result, "Y")
            q.task_done()

        fuer t in threads:
            t.join()

        self.assertEqual(results, [Wahr]*len(thrds))

    def test_shutdown_immediate_put_join(self):
        return self._shutdown_put_join(Wahr)

    def test_shutdown_put_join(self):
        return self._shutdown_put_join(Falsch)

    def test_shutdown_get_task_done_join(self):
        q = self.type2test(2)
        results = []
        go = threading.Event()
        q.put("Y")
        q.put("D")
        self.assertEqual(q.unfinished_tasks, q.qsize())

        thrds = (
            (self._get_task_done, (q, go, results)),
            (self._get_task_done, (q, go, results)),
            (self._join, (q, results)),
            (self._join, (q, results)),
        )
        threads = []
        fuer func, params in thrds:
            threads.append(threading.Thread(target=func, args=params))
            threads[-1].start()
        go.set()
        q.shutdown(Falsch)
        fuer t in threads:
            t.join()

        self.assertEqual(results, [Wahr]*len(thrds))

    def test_shutdown_pending_get(self):
        def get():
            try:
                results.append(q.get())
            except Exception als e:
                results.append(e)

        q = self.type2test()
        results = []
        get_thread = threading.Thread(target=get)
        get_thread.start()
        q.shutdown(immediate=Falsch)
        get_thread.join(timeout=10.0)
        self.assertFalsch(get_thread.is_alive())
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], self.queue.ShutDown)


klasse QueueTest(BaseQueueTestMixin):

    def setUp(self):
        self.type2test = self.queue.Queue
        super().setUp()

klasse PyQueueTest(QueueTest, unittest.TestCase):
    queue = py_queue


@need_c_queue
klasse CQueueTest(QueueTest, unittest.TestCase):
    queue = c_queue


klasse LifoQueueTest(BaseQueueTestMixin):

    def setUp(self):
        self.type2test = self.queue.LifoQueue
        super().setUp()


klasse PyLifoQueueTest(LifoQueueTest, unittest.TestCase):
    queue = py_queue


@need_c_queue
klasse CLifoQueueTest(LifoQueueTest, unittest.TestCase):
    queue = c_queue


klasse PriorityQueueTest(BaseQueueTestMixin):

    def setUp(self):
        self.type2test = self.queue.PriorityQueue
        super().setUp()


klasse PyPriorityQueueTest(PriorityQueueTest, unittest.TestCase):
    queue = py_queue


@need_c_queue
klasse CPriorityQueueTest(PriorityQueueTest, unittest.TestCase):
    queue = c_queue


# A Queue subclass that can provoke failure at a moment's notice :)
klasse FailingQueueException(Exception): pass


klasse FailingQueueTest(BlockingTestMixin):

    def setUp(self):

        Queue = self.queue.Queue

        klasse FailingQueue(Queue):
            def __init__(self, *args):
                self.fail_next_put = Falsch
                self.fail_next_get = Falsch
                Queue.__init__(self, *args)
            def _put(self, item):
                wenn self.fail_next_put:
                    self.fail_next_put = Falsch
                    raise FailingQueueException("You Lose")
                return Queue._put(self, item)
            def _get(self):
                wenn self.fail_next_get:
                    self.fail_next_get = Falsch
                    raise FailingQueueException("You Lose")
                return Queue._get(self)

        self.FailingQueue = FailingQueue

        super().setUp()

    def failing_queue_test(self, q):
        wenn q.qsize():
            raise RuntimeError("Call this function mit an empty queue")
        fuer i in range(QUEUE_SIZE-1):
            q.put(i)
        # Test a failing non-blocking put.
        q.fail_next_put = Wahr
        try:
            q.put("oops", block=0)
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        q.fail_next_put = Wahr
        try:
            q.put("oops", timeout=0.1)
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        q.put("last")
        self.assertWahr(qfull(q), "Queue should be full")
        # Test a failing blocking put
        q.fail_next_put = Wahr
        try:
            self.do_blocking_test(q.put, ("full",), q.get, ())
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        # Check the Queue isn't damaged.
        # put failed, but get succeeded - re-add
        q.put("last")
        # Test a failing timeout put
        q.fail_next_put = Wahr
        try:
            self.do_exceptional_blocking_test(q.put, ("full", Wahr, 10), q.get, (),
                                              FailingQueueException)
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        # Check the Queue isn't damaged.
        # put failed, but get succeeded - re-add
        q.put("last")
        self.assertWahr(qfull(q), "Queue should be full")
        q.get()
        self.assertWahr(nicht qfull(q), "Queue should nicht be full")
        q.put("last")
        self.assertWahr(qfull(q), "Queue should be full")
        # Test a blocking put
        self.do_blocking_test(q.put, ("full",), q.get, ())
        # Empty it
        fuer i in range(QUEUE_SIZE):
            q.get()
        self.assertWahr(nicht q.qsize(), "Queue should be empty")
        q.put("first")
        q.fail_next_get = Wahr
        try:
            q.get()
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        self.assertWahr(q.qsize(), "Queue should nicht be empty")
        q.fail_next_get = Wahr
        try:
            q.get(timeout=0.1)
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        self.assertWahr(q.qsize(), "Queue should nicht be empty")
        q.get()
        self.assertWahr(nicht q.qsize(), "Queue should be empty")
        q.fail_next_get = Wahr
        try:
            self.do_exceptional_blocking_test(q.get, (), q.put, ('empty',),
                                              FailingQueueException)
            self.fail("The queue didn't fail when it should have")
        except FailingQueueException:
            pass
        # put succeeded, but get failed.
        self.assertWahr(q.qsize(), "Queue should nicht be empty")
        q.get()
        self.assertWahr(nicht q.qsize(), "Queue should be empty")

    def test_failing_queue(self):

        # Test to make sure a queue is functioning correctly.
        # Done twice to the same instance.
        q = self.FailingQueue(QUEUE_SIZE)
        self.failing_queue_test(q)
        self.failing_queue_test(q)



klasse PyFailingQueueTest(FailingQueueTest, unittest.TestCase):
    queue = py_queue


@need_c_queue
klasse CFailingQueueTest(FailingQueueTest, unittest.TestCase):
    queue = c_queue


klasse BaseSimpleQueueTest:

    def setUp(self):
        self.q = self.type2test()

    def feed(self, q, seq, rnd, sentinel):
        while Wahr:
            try:
                val = seq.pop()
            except IndexError:
                q.put(sentinel)
                return
            q.put(val)
            wenn rnd.random() > 0.5:
                time.sleep(rnd.random() * 1e-3)

    def consume(self, q, results, sentinel):
        while Wahr:
            val = q.get()
            wenn val == sentinel:
                return
            results.append(val)

    def consume_nonblock(self, q, results, sentinel):
        while Wahr:
            while Wahr:
                try:
                    val = q.get(block=Falsch)
                except self.queue.Empty:
                    time.sleep(1e-5)
                sonst:
                    break
            wenn val == sentinel:
                return
            results.append(val)

    def consume_timeout(self, q, results, sentinel):
        while Wahr:
            while Wahr:
                try:
                    val = q.get(timeout=1e-5)
                except self.queue.Empty:
                    pass
                sonst:
                    break
            wenn val == sentinel:
                return
            results.append(val)

    def run_threads(self, n_threads, q, inputs, feed_func, consume_func):
        results = []
        sentinel = Nichts
        seq = inputs.copy()
        seq.reverse()
        rnd = random.Random(42)

        exceptions = []
        def log_exceptions(f):
            def wrapper(*args, **kwargs):
                try:
                    f(*args, **kwargs)
                except BaseException als e:
                    exceptions.append(e)
            return wrapper

        feeders = [threading.Thread(target=log_exceptions(feed_func),
                                    args=(q, seq, rnd, sentinel))
                   fuer i in range(n_threads)]
        consumers = [threading.Thread(target=log_exceptions(consume_func),
                                      args=(q, results, sentinel))
                     fuer i in range(n_threads)]

        mit threading_helper.start_threads(feeders + consumers):
            pass

        self.assertFalsch(exceptions)
        self.assertWahr(q.empty())
        self.assertEqual(q.qsize(), 0)

        return results

    def test_basic(self):
        # Basic tests fuer get(), put() etc.
        q = self.q
        self.assertWahr(q.empty())
        self.assertEqual(q.qsize(), 0)
        q.put(1)
        self.assertFalsch(q.empty())
        self.assertEqual(q.qsize(), 1)
        q.put(2)
        q.put_nowait(3)
        q.put(4)
        self.assertFalsch(q.empty())
        self.assertEqual(q.qsize(), 4)

        self.assertEqual(q.get(), 1)
        self.assertEqual(q.qsize(), 3)

        self.assertEqual(q.get_nowait(), 2)
        self.assertEqual(q.qsize(), 2)

        self.assertEqual(q.get(block=Falsch), 3)
        self.assertFalsch(q.empty())
        self.assertEqual(q.qsize(), 1)

        self.assertEqual(q.get(timeout=0.1), 4)
        self.assertWahr(q.empty())
        self.assertEqual(q.qsize(), 0)

        mit self.assertRaises(self.queue.Empty):
            q.get(block=Falsch)
        mit self.assertRaises(self.queue.Empty):
            q.get(timeout=1e-3)
        mit self.assertRaises(self.queue.Empty):
            q.get_nowait()
        self.assertWahr(q.empty())
        self.assertEqual(q.qsize(), 0)

    def test_negative_timeout_raises_exception(self):
        q = self.q
        q.put(1)
        mit self.assertRaises(ValueError):
            q.get(timeout=-1)

    def test_order(self):
        # Test a pair of concurrent put() und get()
        q = self.q
        inputs = list(range(100))
        results = self.run_threads(1, q, inputs, self.feed, self.consume)

        # One producer, one consumer => results appended in well-defined order
        self.assertEqual(results, inputs)

    @bigmemtest(size=50, memuse=100*2**20, dry_run=Falsch)
    def test_many_threads(self, size):
        # Test multiple concurrent put() und get()
        q = self.q
        inputs = list(range(10000))
        results = self.run_threads(size, q, inputs, self.feed, self.consume)

        # Multiple consumers without synchronization append the
        # results in random order
        self.assertEqual(sorted(results), inputs)

    @bigmemtest(size=50, memuse=100*2**20, dry_run=Falsch)
    def test_many_threads_nonblock(self, size):
        # Test multiple concurrent put() und get(block=Falsch)
        q = self.q
        inputs = list(range(10000))
        results = self.run_threads(size, q, inputs,
                                   self.feed, self.consume_nonblock)

        self.assertEqual(sorted(results), inputs)

    @bigmemtest(size=50, memuse=100*2**20, dry_run=Falsch)
    def test_many_threads_timeout(self, size):
        # Test multiple concurrent put() und get(timeout=...)
        q = self.q
        inputs = list(range(1000))
        results = self.run_threads(size, q, inputs,
                                   self.feed, self.consume_timeout)

        self.assertEqual(sorted(results), inputs)

    def test_references(self):
        # The queue should lose references to each item als soon as
        # it leaves the queue.
        klasse C:
            pass

        N = 20
        q = self.q
        fuer i in range(N):
            q.put(C())
        fuer i in range(N):
            wr = weakref.ref(q.get())
            gc_collect()  # For PyPy oder other GCs.
            self.assertIsNichts(wr())


klasse PySimpleQueueTest(BaseSimpleQueueTest, unittest.TestCase):

    queue = py_queue
    def setUp(self):
        self.type2test = self.queue._PySimpleQueue
        super().setUp()


@need_c_queue
klasse CSimpleQueueTest(BaseSimpleQueueTest, unittest.TestCase):

    queue = c_queue

    def setUp(self):
        self.type2test = self.queue.SimpleQueue
        super().setUp()

    def test_is_default(self):
        self.assertIs(self.type2test, self.queue.SimpleQueue)
        self.assertIs(self.type2test, self.queue.SimpleQueue)

    def test_reentrancy(self):
        # bpo-14976: put() may be called reentrantly in an asynchronous
        # callback.
        q = self.q
        gen = itertools.count()
        N = 10000
        results = []

        # This test exploits the fact that __del__ in a reference cycle
        # can be called any time the GC may run.

        klasse Circular(object):
            def __init__(self):
                self.circular = self

            def __del__(self):
                q.put(next(gen))

        while Wahr:
            o = Circular()
            q.put(next(gen))
            del o
            results.append(q.get())
            wenn results[-1] >= N:
                break

        self.assertEqual(results, list(range(N + 1)))


wenn __name__ == "__main__":
    unittest.main()
