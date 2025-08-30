importiere queue
importiere sched
importiere threading
importiere time
importiere unittest
von test importiere support
von test.support importiere threading_helper


TIMEOUT = support.SHORT_TIMEOUT


klasse Timer:
    def __init__(self):
        self._cond = threading.Condition()
        self._time = 0
        self._stop = 0

    def time(self):
        mit self._cond:
            gib self._time

    # increase the time but nicht beyond the established limit
    def sleep(self, t):
        pruefe t >= 0
        mit self._cond:
            t += self._time
            waehrend self._stop < t:
                self._time = self._stop
                self._cond.wait()
            self._time = t

    # advance time limit fuer user code
    def advance(self, t):
        pruefe t >= 0
        mit self._cond:
            self._stop += t
            self._cond.notify_all()


klasse TestCase(unittest.TestCase):

    def test_enter(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        fuer x in [0.5, 0.4, 0.3, 0.2, 0.1]:
            z = scheduler.enter(x, 1, fun, (x,))
        scheduler.run()
        self.assertEqual(l, [0.1, 0.2, 0.3, 0.4, 0.5])

    def test_enterabs(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        fuer x in [0.05, 0.04, 0.03, 0.02, 0.01]:
            z = scheduler.enterabs(x, 1, fun, (x,))
        scheduler.run()
        self.assertEqual(l, [0.01, 0.02, 0.03, 0.04, 0.05])

    @threading_helper.requires_working_threading()
    def test_enter_concurrent(self):
        q = queue.Queue()
        fun = q.put
        timer = Timer()
        scheduler = sched.scheduler(timer.time, timer.sleep)
        scheduler.enter(1, 1, fun, (1,))
        scheduler.enter(3, 1, fun, (3,))
        t = threading.Thread(target=scheduler.run)
        t.start()
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 1)
        self.assertWahr(q.empty())
        fuer x in [4, 5, 2]:
            z = scheduler.enter(x - 1, 1, fun, (x,))
        timer.advance(2)
        self.assertEqual(q.get(timeout=TIMEOUT), 2)
        self.assertEqual(q.get(timeout=TIMEOUT), 3)
        self.assertWahr(q.empty())
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 4)
        self.assertWahr(q.empty())
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 5)
        self.assertWahr(q.empty())
        timer.advance(1000)
        threading_helper.join_thread(t)
        self.assertWahr(q.empty())
        self.assertEqual(timer.time(), 5)

    def test_priority(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)

        cases = [
            ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
            ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
            ([2, 5, 3, 1, 4], [1, 2, 3, 4, 5]),
            ([1, 2, 3, 2, 1], [1, 1, 2, 2, 3]),
        ]
        fuer priorities, expected in cases:
            mit self.subTest(priorities=priorities, expected=expected):
                fuer priority in priorities:
                    scheduler.enterabs(0.01, priority, fun, (priority,))
                scheduler.run()
                self.assertEqual(l, expected)

                # Cleanup:
                self.assertWahr(scheduler.empty())
                l.clear()

    def test_cancel(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        now = time.time()
        event1 = scheduler.enterabs(now + 0.01, 1, fun, (0.01,))
        event2 = scheduler.enterabs(now + 0.02, 1, fun, (0.02,))
        event3 = scheduler.enterabs(now + 0.03, 1, fun, (0.03,))
        event4 = scheduler.enterabs(now + 0.04, 1, fun, (0.04,))
        event5 = scheduler.enterabs(now + 0.05, 1, fun, (0.05,))
        scheduler.cancel(event1)
        scheduler.cancel(event5)
        scheduler.run()
        self.assertEqual(l, [0.02, 0.03, 0.04])

    @threading_helper.requires_working_threading()
    def test_cancel_concurrent(self):
        q = queue.Queue()
        fun = q.put
        timer = Timer()
        scheduler = sched.scheduler(timer.time, timer.sleep)
        now = timer.time()
        event1 = scheduler.enterabs(now + 1, 1, fun, (1,))
        event2 = scheduler.enterabs(now + 2, 1, fun, (2,))
        event4 = scheduler.enterabs(now + 4, 1, fun, (4,))
        event5 = scheduler.enterabs(now + 5, 1, fun, (5,))
        event3 = scheduler.enterabs(now + 3, 1, fun, (3,))
        t = threading.Thread(target=scheduler.run)
        t.start()
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 1)
        self.assertWahr(q.empty())
        scheduler.cancel(event2)
        scheduler.cancel(event5)
        timer.advance(1)
        self.assertWahr(q.empty())
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 3)
        self.assertWahr(q.empty())
        timer.advance(1)
        self.assertEqual(q.get(timeout=TIMEOUT), 4)
        self.assertWahr(q.empty())
        timer.advance(1000)
        threading_helper.join_thread(t)
        self.assertWahr(q.empty())
        self.assertEqual(timer.time(), 4)

    def test_cancel_correct_event(self):
        # bpo-19270
        events = []
        scheduler = sched.scheduler()
        scheduler.enterabs(1, 1, events.append, ("a",))
        b = scheduler.enterabs(1, 1, events.append, ("b",))
        scheduler.enterabs(1, 1, events.append, ("c",))
        scheduler.cancel(b)
        scheduler.run()
        self.assertEqual(events, ["a", "c"])

    def test_empty(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        self.assertWahr(scheduler.empty())
        fuer x in [0.05, 0.04, 0.03, 0.02, 0.01]:
            z = scheduler.enterabs(x, 1, fun, (x,))
        self.assertFalsch(scheduler.empty())
        scheduler.run()
        self.assertWahr(scheduler.empty())

    def test_queue(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        now = time.time()
        e5 = scheduler.enterabs(now + 0.05, 1, fun)
        e1 = scheduler.enterabs(now + 0.01, 1, fun)
        e2 = scheduler.enterabs(now + 0.02, 1, fun)
        e4 = scheduler.enterabs(now + 0.04, 1, fun)
        e3 = scheduler.enterabs(now + 0.03, 1, fun)
        # queue property ist supposed to gib an order list of
        # upcoming events
        self.assertEqual(scheduler.queue, [e1, e2, e3, e4, e5])

    def test_args_kwargs(self):
        seq = []
        def fun(*a, **b):
            seq.append((a, b))

        now = time.time()
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enterabs(now, 1, fun)
        scheduler.enterabs(now, 1, fun, argument=(1, 2))
        scheduler.enterabs(now, 1, fun, argument=('a', 'b'))
        scheduler.enterabs(now, 1, fun, argument=(1, 2), kwargs={"foo": 3})
        scheduler.run()
        self.assertCountEqual(seq, [
            ((), {}),
            ((1, 2), {}),
            (('a', 'b'), {}),
            ((1, 2), {'foo': 3})
        ])

    def test_run_non_blocking(self):
        l = []
        fun = lambda x: l.append(x)
        scheduler = sched.scheduler(time.time, time.sleep)
        fuer x in [10, 9, 8, 7, 6]:
            scheduler.enter(x, 1, fun, (x,))
        scheduler.run(blocking=Falsch)
        self.assertEqual(l, [])


wenn __name__ == "__main__":
    unittest.main()
