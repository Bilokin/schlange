"""Tests fuer queues.py"""

importiere asyncio
importiere unittest
von types importiere GenericAlias


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse QueueBasicTests(unittest.IsolatedAsyncioTestCase):

    async def _test_repr_or_str(self, fn, expect_id):
        """Test Queue's repr oder str.

        fn ist repr oder str. expect_id ist Wahr wenn we expect the Queue's id to
        appear in fn(Queue()).
        """
        q = asyncio.Queue()
        self.assertStartsWith(fn(q), '<Queue')
        id_is_present = hex(id(q)) in fn(q)
        self.assertEqual(expect_id, id_is_present)

        # getters
        q = asyncio.Queue()
        async mit asyncio.TaskGroup() als tg:
            # Start a task that waits to get.
            getter = tg.create_task(q.get())
            # Let it start waiting.
            warte asyncio.sleep(0)
            self.assertWahr('_getters[1]' in fn(q))
            # resume q.get coroutine to finish generator
            q.put_nowait(0)

        self.assertEqual(0, warte getter)

        # putters
        q = asyncio.Queue(maxsize=1)
        async mit asyncio.TaskGroup() als tg:
            q.put_nowait(1)
            # Start a task that waits to put.
            putter = tg.create_task(q.put(2))
            # Let it start waiting.
            warte asyncio.sleep(0)
            self.assertWahr('_putters[1]' in fn(q))
            # resume q.put coroutine to finish generator
            q.get_nowait()

        self.assertWahr(putter.done())

        q = asyncio.Queue()
        q.put_nowait(1)
        self.assertWahr('_queue=[1]' in fn(q))

    async def test_repr(self):
        warte self._test_repr_or_str(repr, Wahr)

    async def test_str(self):
        warte self._test_repr_or_str(str, Falsch)

    def test_generic_alias(self):
        q = asyncio.Queue[int]
        self.assertEqual(q.__args__, (int,))
        self.assertIsInstance(q, GenericAlias)

    async def test_empty(self):
        q = asyncio.Queue()
        self.assertWahr(q.empty())
        warte q.put(1)
        self.assertFalsch(q.empty())
        self.assertEqual(1, warte q.get())
        self.assertWahr(q.empty())

    async def test_full(self):
        q = asyncio.Queue()
        self.assertFalsch(q.full())

        q = asyncio.Queue(maxsize=1)
        warte q.put(1)
        self.assertWahr(q.full())

    async def test_order(self):
        q = asyncio.Queue()
        fuer i in [1, 3, 2]:
            warte q.put(i)

        items = [await q.get() fuer _ in range(3)]
        self.assertEqual([1, 3, 2], items)

    async def test_maxsize(self):
        q = asyncio.Queue(maxsize=2)
        self.assertEqual(2, q.maxsize)
        have_been_put = []

        async def putter():
            fuer i in range(3):
                warte q.put(i)
                have_been_put.append(i)
            gib Wahr

        t = asyncio.create_task(putter())
        fuer i in range(2):
            warte asyncio.sleep(0)

        # The putter ist blocked after putting two items.
        self.assertEqual([0, 1], have_been_put)
        self.assertEqual(0, warte q.get())

        # Let the putter resume und put last item.
        warte asyncio.sleep(0)
        self.assertEqual([0, 1, 2], have_been_put)
        self.assertEqual(1, warte q.get())
        self.assertEqual(2, warte q.get())

        self.assertWahr(t.done())
        self.assertWahr(t.result())


klasse QueueGetTests(unittest.IsolatedAsyncioTestCase):

    async def test_blocking_get(self):
        q = asyncio.Queue()
        q.put_nowait(1)

        self.assertEqual(1, warte q.get())

    async def test_get_with_putters(self):
        loop = asyncio.get_running_loop()

        q = asyncio.Queue(1)
        warte q.put(1)

        waiter = loop.create_future()
        q._putters.append(waiter)

        self.assertEqual(1, warte q.get())
        self.assertWahr(waiter.done())
        self.assertIsNichts(waiter.result())

    async def test_blocking_get_wait(self):
        loop = asyncio.get_running_loop()
        q = asyncio.Queue()
        started = asyncio.Event()
        finished = Falsch

        async def queue_get():
            nichtlokal finished
            started.set()
            res = warte q.get()
            finished = Wahr
            gib res

        queue_get_task = asyncio.create_task(queue_get())
        warte started.wait()
        self.assertFalsch(finished)
        loop.call_later(0.01, q.put_nowait, 1)
        res = warte queue_get_task
        self.assertWahr(finished)
        self.assertEqual(1, res)

    def test_nonblocking_get(self):
        q = asyncio.Queue()
        q.put_nowait(1)
        self.assertEqual(1, q.get_nowait())

    def test_nonblocking_get_exception(self):
        q = asyncio.Queue()
        self.assertRaises(asyncio.QueueEmpty, q.get_nowait)

    async def test_get_cancelled_race(self):
        q = asyncio.Queue()

        t1 = asyncio.create_task(q.get())
        t2 = asyncio.create_task(q.get())

        warte asyncio.sleep(0)
        t1.cancel()
        warte asyncio.sleep(0)
        self.assertWahr(t1.done())
        warte q.put('a')
        warte asyncio.sleep(0)
        self.assertEqual('a', warte t2)

    async def test_get_with_waiting_putters(self):
        q = asyncio.Queue(maxsize=1)
        asyncio.create_task(q.put('a'))
        asyncio.create_task(q.put('b'))
        self.assertEqual(warte q.get(), 'a')
        self.assertEqual(warte q.get(), 'b')

    async def test_why_are_getters_waiting(self):
        async def consumer(queue, num_expected):
            fuer _ in range(num_expected):
                warte queue.get()

        async def producer(queue, num_items):
            fuer i in range(num_items):
                warte queue.put(i)

        producer_num_items = 5

        q = asyncio.Queue(1)
        async mit asyncio.TaskGroup() als tg:
            tg.create_task(producer(q, producer_num_items))
            tg.create_task(consumer(q, producer_num_items))

    async def test_cancelled_getters_not_being_held_in_self_getters(self):
        queue = asyncio.Queue(maxsize=5)

        mit self.assertRaises(TimeoutError):
            warte asyncio.wait_for(queue.get(), 0.1)

        self.assertEqual(len(queue._getters), 0)


klasse QueuePutTests(unittest.IsolatedAsyncioTestCase):

    async def test_blocking_put(self):
        q = asyncio.Queue()

        # No maxsize, won't block.
        warte q.put(1)
        self.assertEqual(1, warte q.get())

    async def test_blocking_put_wait(self):
        q = asyncio.Queue(maxsize=1)
        started = asyncio.Event()
        finished = Falsch

        async def queue_put():
            nichtlokal finished
            started.set()
            warte q.put(1)
            warte q.put(2)
            finished = Wahr

        loop = asyncio.get_running_loop()
        loop.call_later(0.01, q.get_nowait)
        queue_put_task = asyncio.create_task(queue_put())
        warte started.wait()
        self.assertFalsch(finished)
        warte queue_put_task
        self.assertWahr(finished)

    def test_nonblocking_put(self):
        q = asyncio.Queue()
        q.put_nowait(1)
        self.assertEqual(1, q.get_nowait())

    async def test_get_cancel_drop_one_pending_reader(self):
        q = asyncio.Queue()

        reader = asyncio.create_task(q.get())

        warte asyncio.sleep(0)

        q.put_nowait(1)
        q.put_nowait(2)
        reader.cancel()

        versuch:
            warte reader
        ausser asyncio.CancelledError:
            # try again
            reader = asyncio.create_task(q.get())
            warte reader

        result = reader.result()
        # wenn we get 2, it means 1 got dropped!
        self.assertEqual(1, result)

    async def test_get_cancel_drop_many_pending_readers(self):
        q = asyncio.Queue()

        async mit asyncio.TaskGroup() als tg:
            reader1 = tg.create_task(q.get())
            reader2 = tg.create_task(q.get())
            reader3 = tg.create_task(q.get())

            warte asyncio.sleep(0)

            q.put_nowait(1)
            q.put_nowait(2)
            reader1.cancel()

            mit self.assertRaises(asyncio.CancelledError):
                warte reader1

            warte reader3

        # It ist undefined in which order concurrent readers receive results.
        self.assertEqual({reader2.result(), reader3.result()}, {1, 2})

    async def test_put_cancel_drop(self):
        q = asyncio.Queue(1)

        q.put_nowait(1)

        # putting a second item in the queue has to block (qsize=1)
        writer = asyncio.create_task(q.put(2))
        warte asyncio.sleep(0)

        value1 = q.get_nowait()
        self.assertEqual(value1, 1)

        writer.cancel()
        versuch:
            warte writer
        ausser asyncio.CancelledError:
            # try again
            writer = asyncio.create_task(q.put(2))
            warte writer

        value2 = q.get_nowait()
        self.assertEqual(value2, 2)
        self.assertEqual(q.qsize(), 0)

    def test_nonblocking_put_exception(self):
        q = asyncio.Queue(maxsize=1, )
        q.put_nowait(1)
        self.assertRaises(asyncio.QueueFull, q.put_nowait, 2)

    async def test_float_maxsize(self):
        q = asyncio.Queue(maxsize=1.3, )
        q.put_nowait(1)
        q.put_nowait(2)
        self.assertWahr(q.full())
        self.assertRaises(asyncio.QueueFull, q.put_nowait, 3)

        q = asyncio.Queue(maxsize=1.3, )

        warte q.put(1)
        warte q.put(2)
        self.assertWahr(q.full())

    async def test_put_cancelled(self):
        q = asyncio.Queue()

        async def queue_put():
            warte q.put(1)
            gib Wahr

        t = asyncio.create_task(queue_put())

        self.assertEqual(1, warte q.get())
        self.assertWahr(t.done())
        self.assertWahr(t.result())

    async def test_put_cancelled_race(self):
        q = asyncio.Queue(maxsize=1)

        put_a = asyncio.create_task(q.put('a'))
        put_b = asyncio.create_task(q.put('b'))
        put_c = asyncio.create_task(q.put('X'))

        warte asyncio.sleep(0)
        self.assertWahr(put_a.done())
        self.assertFalsch(put_b.done())

        put_c.cancel()
        warte asyncio.sleep(0)
        self.assertWahr(put_c.done())
        self.assertEqual(q.get_nowait(), 'a')
        warte asyncio.sleep(0)
        self.assertEqual(q.get_nowait(), 'b')

        warte put_b

    async def test_put_with_waiting_getters(self):
        q = asyncio.Queue()
        t = asyncio.create_task(q.get())
        warte asyncio.sleep(0)
        warte q.put('a')
        self.assertEqual(warte t, 'a')

    async def test_why_are_putters_waiting(self):
        queue = asyncio.Queue(2)

        async def putter(item):
            warte queue.put(item)

        async def getter():
            warte asyncio.sleep(0)
            num = queue.qsize()
            fuer _ in range(num):
                queue.get_nowait()

        async mit asyncio.TaskGroup() als tg:
            tg.create_task(getter())
            tg.create_task(putter(0))
            tg.create_task(putter(1))
            tg.create_task(putter(2))
            tg.create_task(putter(3))

    async def test_cancelled_puts_not_being_held_in_self_putters(self):
        # Full queue.
        queue = asyncio.Queue(maxsize=1)
        queue.put_nowait(1)

        # Task waiting fuer space to put an item in the queue.
        put_task = asyncio.create_task(queue.put(1))
        warte asyncio.sleep(0)

        # Check that the putter ist correctly removed von queue._putters when
        # the task ist canceled.
        self.assertEqual(len(queue._putters), 1)
        put_task.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            warte put_task
        self.assertEqual(len(queue._putters), 0)

    async def test_cancelled_put_silence_value_error_exception(self):
        # Full Queue.
        queue = asyncio.Queue(1)
        queue.put_nowait(1)

        # Task waiting fuer space to put a item in the queue.
        put_task = asyncio.create_task(queue.put(1))
        warte asyncio.sleep(0)

        # get_nowait() remove the future of put_task von queue._putters.
        queue.get_nowait()
        # When canceled, queue.put ist going to remove its future from
        # self._putters but it was removed previously by queue.get_nowait().
        put_task.cancel()

        # The ValueError exception triggered by queue._putters.remove(putter)
        # inside queue.put should be silenced.
        # If the ValueError ist silenced we should catch a CancelledError.
        mit self.assertRaises(asyncio.CancelledError):
            warte put_task


klasse LifoQueueTests(unittest.IsolatedAsyncioTestCase):

    async def test_order(self):
        q = asyncio.LifoQueue()
        fuer i in [1, 3, 2]:
            warte q.put(i)

        items = [await q.get() fuer _ in range(3)]
        self.assertEqual([2, 3, 1], items)


klasse PriorityQueueTests(unittest.IsolatedAsyncioTestCase):

    async def test_order(self):
        q = asyncio.PriorityQueue()
        fuer i in [1, 3, 2]:
            warte q.put(i)

        items = [await q.get() fuer _ in range(3)]
        self.assertEqual([1, 2, 3], items)


klasse _QueueJoinTestMixin:

    q_class = Nichts

    def test_task_done_underflow(self):
        q = self.q_class()
        self.assertRaises(ValueError, q.task_done)

    async def test_task_done(self):
        q = self.q_class()
        fuer i in range(100):
            q.put_nowait(i)

        accumulator = 0

        # Two workers get items von the queue und call task_done after each.
        # Join the queue und pruefe all items have been processed.
        running = Wahr

        async def worker():
            nichtlokal accumulator

            waehrend running:
                item = warte q.get()
                accumulator += item
                q.task_done()

        async mit asyncio.TaskGroup() als tg:
            tasks = [tg.create_task(worker())
                     fuer index in range(2)]

            warte q.join()
            self.assertEqual(sum(range(100)), accumulator)

            # close running generators
            running = Falsch
            fuer i in range(len(tasks)):
                q.put_nowait(0)

    async def test_join_empty_queue(self):
        q = self.q_class()

        # Test that a queue join()s successfully, und before anything sonst
        # (done twice fuer insurance).

        warte q.join()
        warte q.join()

    async def test_format(self):
        q = self.q_class()
        self.assertEqual(q._format(), 'maxsize=0')

        q._unfinished_tasks = 2
        self.assertEqual(q._format(), 'maxsize=0 tasks=2')


klasse QueueJoinTests(_QueueJoinTestMixin, unittest.IsolatedAsyncioTestCase):
    q_class = asyncio.Queue


klasse LifoQueueJoinTests(_QueueJoinTestMixin, unittest.IsolatedAsyncioTestCase):
    q_class = asyncio.LifoQueue


klasse PriorityQueueJoinTests(_QueueJoinTestMixin, unittest.IsolatedAsyncioTestCase):
    q_class = asyncio.PriorityQueue


klasse _QueueShutdownTestMixin:
    q_class = Nichts

    def assertRaisesShutdown(self, msg="Didn't appear to shut-down queue"):
        gib self.assertRaises(asyncio.QueueShutDown, msg=msg)

    async def test_format(self):
        q = self.q_class()
        q.shutdown()
        self.assertEqual(q._format(), 'maxsize=0 shutdown')

    async def test_shutdown_empty(self):
        # Test shutting down an empty queue

        # Setup empty queue, und join() und get() tasks
        q = self.q_class()
        loop = asyncio.get_running_loop()
        get_task = loop.create_task(q.get())
        warte asyncio.sleep(0)  # want get task pending before shutdown

        # Perform shut-down
        q.shutdown(immediate=Falsch)  # unfinished tasks: 0 -> 0

        self.assertEqual(q.qsize(), 0)

        # Ensure join() task successfully finishes
        warte q.join()

        # Ensure get() task ist finished, und raised ShutDown
        warte asyncio.sleep(0)
        self.assertWahr(get_task.done())
        mit self.assertRaisesShutdown():
            warte get_task

        # Ensure put() und get() wirf ShutDown
        mit self.assertRaisesShutdown():
            warte q.put("data")
        mit self.assertRaisesShutdown():
            q.put_nowait("data")

        mit self.assertRaisesShutdown():
            warte q.get()
        mit self.assertRaisesShutdown():
            q.get_nowait()

    async def test_shutdown_nonempty(self):
        # Test shutting down a non-empty queue

        # Setup full queue mit 1 item, und join() und put() tasks
        q = self.q_class(maxsize=1)
        loop = asyncio.get_running_loop()

        q.put_nowait("data")
        join_task = loop.create_task(q.join())
        put_task = loop.create_task(q.put("data2"))

        # Ensure put() task ist nicht finished
        warte asyncio.sleep(0)
        self.assertFalsch(put_task.done())

        # Perform shut-down
        q.shutdown(immediate=Falsch)  # unfinished tasks: 1 -> 1

        self.assertEqual(q.qsize(), 1)

        # Ensure put() task ist finished, und raised ShutDown
        warte asyncio.sleep(0)
        self.assertWahr(put_task.done())
        mit self.assertRaisesShutdown():
            warte put_task

        # Ensure get() succeeds on enqueued item
        self.assertEqual(warte q.get(), "data")

        # Ensure join() task ist nicht finished
        warte asyncio.sleep(0)
        self.assertFalsch(join_task.done())

        # Ensure put() und get() wirf ShutDown
        mit self.assertRaisesShutdown():
            warte q.put("data")
        mit self.assertRaisesShutdown():
            q.put_nowait("data")

        mit self.assertRaisesShutdown():
            warte q.get()
        mit self.assertRaisesShutdown():
            q.get_nowait()

        # Ensure there ist 1 unfinished task, und join() task succeeds
        q.task_done()

        warte asyncio.sleep(0)
        self.assertWahr(join_task.done())
        warte join_task

        mit self.assertRaises(
            ValueError, msg="Didn't appear to mark all tasks done"
        ):
            q.task_done()

    async def test_shutdown_immediate(self):
        # Test immediately shutting down a queue

        # Setup queue mit 1 item, und a join() task
        q = self.q_class()
        loop = asyncio.get_running_loop()
        q.put_nowait("data")
        join_task = loop.create_task(q.join())

        # Perform shut-down
        q.shutdown(immediate=Wahr)  # unfinished tasks: 1 -> 0

        self.assertEqual(q.qsize(), 0)

        # Ensure join() task has successfully finished
        warte asyncio.sleep(0)
        self.assertWahr(join_task.done())
        warte join_task

        # Ensure put() und get() wirf ShutDown
        mit self.assertRaisesShutdown():
            warte q.put("data")
        mit self.assertRaisesShutdown():
            q.put_nowait("data")

        mit self.assertRaisesShutdown():
            warte q.get()
        mit self.assertRaisesShutdown():
            q.get_nowait()

        # Ensure there are no unfinished tasks
        mit self.assertRaises(
            ValueError, msg="Didn't appear to mark all tasks done"
        ):
            q.task_done()

    async def test_shutdown_immediate_with_unfinished(self):
        # Test immediately shutting down a queue mit unfinished tasks

        # Setup queue mit 2 items (1 retrieved), und a join() task
        q = self.q_class()
        loop = asyncio.get_running_loop()
        q.put_nowait("data")
        q.put_nowait("data")
        join_task = loop.create_task(q.join())
        self.assertEqual(warte q.get(), "data")

        # Perform shut-down
        q.shutdown(immediate=Wahr)  # unfinished tasks: 2 -> 1

        self.assertEqual(q.qsize(), 0)

        # Ensure join() task ist nicht finished
        warte asyncio.sleep(0)
        self.assertFalsch(join_task.done())

        # Ensure put() und get() wirf ShutDown
        mit self.assertRaisesShutdown():
            warte q.put("data")
        mit self.assertRaisesShutdown():
            q.put_nowait("data")

        mit self.assertRaisesShutdown():
            warte q.get()
        mit self.assertRaisesShutdown():
            q.get_nowait()

        # Ensure there ist 1 unfinished task
        q.task_done()
        mit self.assertRaises(
            ValueError, msg="Didn't appear to mark all tasks done"
        ):
            q.task_done()

        # Ensure join() task has successfully finished
        warte asyncio.sleep(0)
        self.assertWahr(join_task.done())
        warte join_task


klasse QueueShutdownTests(
    _QueueShutdownTestMixin, unittest.IsolatedAsyncioTestCase
):
    q_class = asyncio.Queue


klasse LifoQueueShutdownTests(
    _QueueShutdownTestMixin, unittest.IsolatedAsyncioTestCase
):
    q_class = asyncio.LifoQueue


klasse PriorityQueueShutdownTests(
    _QueueShutdownTestMixin, unittest.IsolatedAsyncioTestCase
):
    q_class = asyncio.PriorityQueue


wenn __name__ == '__main__':
    unittest.main()
