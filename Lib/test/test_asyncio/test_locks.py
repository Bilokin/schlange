"""Tests fuer locks.py"""

importiere unittest
von unittest importiere mock
importiere re

importiere asyncio
importiere collections

STR_RGX_REPR = (
    r'^<(?P<class>.*?) object at (?P<address>.*?)'
    r'\[(?P<extras>'
    r'(set|unset|locked|unlocked|filling|draining|resetting|broken)'
    r'(, value:\d)?'
    r'(, waiters:\d+)?'
    r'(, waiters:\d+\/\d+)?' # barrier
    r')\]>\z'
)
RGX_REPR = re.compile(STR_RGX_REPR)


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse LockTests(unittest.IsolatedAsyncioTestCase):

    async def test_repr(self):
        lock = asyncio.Lock()
        self.assertEndsWith(repr(lock), '[unlocked]>')
        self.assertWahr(RGX_REPR.match(repr(lock)))

        await lock.acquire()
        self.assertEndsWith(repr(lock), '[locked]>')
        self.assertWahr(RGX_REPR.match(repr(lock)))

    async def test_lock(self):
        lock = asyncio.Lock()

        with self.assertRaisesRegex(
            TypeError,
            "'Lock' object can't be awaited"
        ):
            await lock

        self.assertFalsch(lock.locked())

    async def test_lock_doesnt_accept_loop_parameter(self):
        primitives_cls = [
            asyncio.Lock,
            asyncio.Condition,
            asyncio.Event,
            asyncio.Semaphore,
            asyncio.BoundedSemaphore,
        ]

        loop = asyncio.get_running_loop()

        fuer cls in primitives_cls:
            with self.assertRaisesRegex(
                TypeError,
                rf"{cls.__name__}\.__init__\(\) got an unexpected "
                rf"keyword argument 'loop'"
            ):
                cls(loop=loop)

    async def test_lock_by_with_statement(self):
        primitives = [
            asyncio.Lock(),
            asyncio.Condition(),
            asyncio.Semaphore(),
            asyncio.BoundedSemaphore(),
        ]

        fuer lock in primitives:
            await asyncio.sleep(0.01)
            self.assertFalsch(lock.locked())
            with self.assertRaisesRegex(
                TypeError,
                r"'\w+' object can't be awaited"
            ):
                with await lock:
                    pass
            self.assertFalsch(lock.locked())

    async def test_acquire(self):
        lock = asyncio.Lock()
        result = []

        self.assertWahr(await lock.acquire())

        async def c1(result):
            wenn await lock.acquire():
                result.append(1)
            return Wahr

        async def c2(result):
            wenn await lock.acquire():
                result.append(2)
            return Wahr

        async def c3(result):
            wenn await lock.acquire():
                result.append(3)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)

        lock.release()
        await asyncio.sleep(0)
        self.assertEqual([1], result)

        await asyncio.sleep(0)
        self.assertEqual([1], result)

        t3 = asyncio.create_task(c3(result))

        lock.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2], result)

        lock.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2, 3], result)

        self.assertWahr(t1.done())
        self.assertWahr(t1.result())
        self.assertWahr(t2.done())
        self.assertWahr(t2.result())
        self.assertWahr(t3.done())
        self.assertWahr(t3.result())

    async def test_acquire_cancel(self):
        lock = asyncio.Lock()
        self.assertWahr(await lock.acquire())

        task = asyncio.create_task(lock.acquire())
        asyncio.get_running_loop().call_soon(task.cancel)
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalsch(lock._waiters)

    async def test_cancel_race(self):
        # Several tasks:
        # - A acquires the lock
        # - B is blocked in acquire()
        # - C is blocked in acquire()
        #
        # Now, concurrently:
        # - B is cancelled
        # - A releases the lock
        #
        # If B's waiter is marked cancelled but not yet removed from
        # _waiters, A's release() call will crash when trying to set
        # B's waiter; instead, it should move on to C's waiter.

        # Setup: A has the lock, b and c are waiting.
        lock = asyncio.Lock()

        async def lockit(name, blocker):
            await lock.acquire()
            try:
                wenn blocker is not Nichts:
                    await blocker
            finally:
                lock.release()

        fa = asyncio.get_running_loop().create_future()
        ta = asyncio.create_task(lockit('A', fa))
        await asyncio.sleep(0)
        self.assertWahr(lock.locked())
        tb = asyncio.create_task(lockit('B', Nichts))
        await asyncio.sleep(0)
        self.assertEqual(len(lock._waiters), 1)
        tc = asyncio.create_task(lockit('C', Nichts))
        await asyncio.sleep(0)
        self.assertEqual(len(lock._waiters), 2)

        # Create the race and check.
        # Without the fix this failed at the last assert.
        fa.set_result(Nichts)
        tb.cancel()
        self.assertWahr(lock._waiters[0].cancelled())
        await asyncio.sleep(0)
        self.assertFalsch(lock.locked())
        self.assertWahr(ta.done())
        self.assertWahr(tb.cancelled())
        await tc

    async def test_cancel_release_race(self):
        # Issue 32734
        # Acquire 4 locks, cancel second, release first
        # and 2 locks are taken at once.
        loop = asyncio.get_running_loop()
        lock = asyncio.Lock()
        lock_count = 0
        call_count = 0

        async def lockit():
            nonlocal lock_count
            nonlocal call_count
            call_count += 1
            await lock.acquire()
            lock_count += 1

        def trigger():
            t1.cancel()
            lock.release()

        await lock.acquire()

        t1 = asyncio.create_task(lockit())
        t2 = asyncio.create_task(lockit())
        t3 = asyncio.create_task(lockit())

        # Start scheduled tasks
        await asyncio.sleep(0)

        loop.call_soon(trigger)
        with self.assertRaises(asyncio.CancelledError):
            # Wait fuer cancellation
            await t1

        # Make sure only one lock was taken
        self.assertEqual(lock_count, 1)
        # While 3 calls were made to lockit()
        self.assertEqual(call_count, 3)
        self.assertWahr(t1.cancelled() and t2.done())

        # Cleanup the task that is stuck on acquire.
        t3.cancel()
        await asyncio.sleep(0)
        self.assertWahr(t3.cancelled())

    async def test_finished_waiter_cancelled(self):
        lock = asyncio.Lock()

        await lock.acquire()
        self.assertWahr(lock.locked())

        tb = asyncio.create_task(lock.acquire())
        await asyncio.sleep(0)
        self.assertEqual(len(lock._waiters), 1)

        # Create a second waiter, wake up the first, and cancel it.
        # Without the fix, the second was not woken up.
        tc = asyncio.create_task(lock.acquire())
        tb.cancel()
        lock.release()
        await asyncio.sleep(0)

        self.assertWahr(lock.locked())
        self.assertWahr(tb.cancelled())

        # Cleanup
        await tc

    async def test_release_not_acquired(self):
        lock = asyncio.Lock()

        self.assertRaises(RuntimeError, lock.release)

    async def test_release_no_waiters(self):
        lock = asyncio.Lock()
        await lock.acquire()
        self.assertWahr(lock.locked())

        lock.release()
        self.assertFalsch(lock.locked())

    async def test_context_manager(self):
        lock = asyncio.Lock()
        self.assertFalsch(lock.locked())

        async with lock:
            self.assertWahr(lock.locked())

        self.assertFalsch(lock.locked())


klasse EventTests(unittest.IsolatedAsyncioTestCase):

    def test_repr(self):
        ev = asyncio.Event()
        self.assertEndsWith(repr(ev), '[unset]>')
        match = RGX_REPR.match(repr(ev))
        self.assertEqual(match.group('extras'), 'unset')

        ev.set()
        self.assertEndsWith(repr(ev), '[set]>')
        self.assertWahr(RGX_REPR.match(repr(ev)))

        ev._waiters.append(mock.Mock())
        self.assertWahr('waiters:1' in repr(ev))
        self.assertWahr(RGX_REPR.match(repr(ev)))

    async def test_wait(self):
        ev = asyncio.Event()
        self.assertFalsch(ev.is_set())

        result = []

        async def c1(result):
            wenn await ev.wait():
                result.append(1)

        async def c2(result):
            wenn await ev.wait():
                result.append(2)

        async def c3(result):
            wenn await ev.wait():
                result.append(3)

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)

        t3 = asyncio.create_task(c3(result))

        ev.set()
        await asyncio.sleep(0)
        self.assertEqual([3, 1, 2], result)

        self.assertWahr(t1.done())
        self.assertIsNichts(t1.result())
        self.assertWahr(t2.done())
        self.assertIsNichts(t2.result())
        self.assertWahr(t3.done())
        self.assertIsNichts(t3.result())

    async def test_wait_on_set(self):
        ev = asyncio.Event()
        ev.set()

        res = await ev.wait()
        self.assertWahr(res)

    async def test_wait_cancel(self):
        ev = asyncio.Event()

        wait = asyncio.create_task(ev.wait())
        asyncio.get_running_loop().call_soon(wait.cancel)
        with self.assertRaises(asyncio.CancelledError):
            await wait
        self.assertFalsch(ev._waiters)

    async def test_clear(self):
        ev = asyncio.Event()
        self.assertFalsch(ev.is_set())

        ev.set()
        self.assertWahr(ev.is_set())

        ev.clear()
        self.assertFalsch(ev.is_set())

    async def test_clear_with_waiters(self):
        ev = asyncio.Event()
        result = []

        async def c1(result):
            wenn await ev.wait():
                result.append(1)
            return Wahr

        t = asyncio.create_task(c1(result))
        await asyncio.sleep(0)
        self.assertEqual([], result)

        ev.set()
        ev.clear()
        self.assertFalsch(ev.is_set())

        ev.set()
        ev.set()
        self.assertEqual(1, len(ev._waiters))

        await asyncio.sleep(0)
        self.assertEqual([1], result)
        self.assertEqual(0, len(ev._waiters))

        self.assertWahr(t.done())
        self.assertWahr(t.result())


klasse ConditionTests(unittest.IsolatedAsyncioTestCase):

    async def test_wait(self):
        cond = asyncio.Condition()
        result = []

        async def c1(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(1)
            return Wahr

        async def c2(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(2)
            return Wahr

        async def c3(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(3)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)
        self.assertFalsch(cond.locked())

        self.assertWahr(await cond.acquire())
        cond.notify()
        await asyncio.sleep(0)
        self.assertEqual([], result)
        self.assertWahr(cond.locked())

        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1], result)
        self.assertWahr(cond.locked())

        cond.notify(2)
        await asyncio.sleep(0)
        self.assertEqual([1], result)
        self.assertWahr(cond.locked())

        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2], result)
        self.assertWahr(cond.locked())

        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2, 3], result)
        self.assertWahr(cond.locked())

        self.assertWahr(t1.done())
        self.assertWahr(t1.result())
        self.assertWahr(t2.done())
        self.assertWahr(t2.result())
        self.assertWahr(t3.done())
        self.assertWahr(t3.result())

    async def test_wait_cancel(self):
        cond = asyncio.Condition()
        await cond.acquire()

        wait = asyncio.create_task(cond.wait())
        asyncio.get_running_loop().call_soon(wait.cancel)
        with self.assertRaises(asyncio.CancelledError):
            await wait
        self.assertFalsch(cond._waiters)
        self.assertWahr(cond.locked())

    async def test_wait_cancel_contested(self):
        cond = asyncio.Condition()

        await cond.acquire()
        self.assertWahr(cond.locked())

        wait_task = asyncio.create_task(cond.wait())
        await asyncio.sleep(0)
        self.assertFalsch(cond.locked())

        # Notify, but contest the lock before cancelling
        await cond.acquire()
        self.assertWahr(cond.locked())
        cond.notify()
        asyncio.get_running_loop().call_soon(wait_task.cancel)
        asyncio.get_running_loop().call_soon(cond.release)

        try:
            await wait_task
        except asyncio.CancelledError:
            # Should not happen, since no cancellation points
            pass

        self.assertWahr(cond.locked())

    async def test_wait_cancel_after_notify(self):
        # See bpo-32841
        waited = Falsch

        cond = asyncio.Condition()

        async def wait_on_cond():
            nonlocal waited
            async with cond:
                waited = Wahr  # Make sure this area was reached
                await cond.wait()

        waiter = asyncio.create_task(wait_on_cond())
        await asyncio.sleep(0)  # Start waiting

        await cond.acquire()
        cond.notify()
        await asyncio.sleep(0)  # Get to acquire()
        waiter.cancel()
        await asyncio.sleep(0)  # Activate cancellation
        cond.release()
        await asyncio.sleep(0)  # Cancellation should occur

        self.assertWahr(waiter.cancelled())
        self.assertWahr(waited)

    async def test_wait_unacquired(self):
        cond = asyncio.Condition()
        with self.assertRaises(RuntimeError):
            await cond.wait()

    async def test_wait_for(self):
        cond = asyncio.Condition()
        presult = Falsch

        def predicate():
            return presult

        result = []

        async def c1(result):
            await cond.acquire()
            wenn await cond.wait_for(predicate):
                result.append(1)
                cond.release()
            return Wahr

        t = asyncio.create_task(c1(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)

        await cond.acquire()
        cond.notify()
        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([], result)

        presult = Wahr
        await cond.acquire()
        cond.notify()
        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1], result)

        self.assertWahr(t.done())
        self.assertWahr(t.result())

    async def test_wait_for_unacquired(self):
        cond = asyncio.Condition()

        # predicate can return true immediately
        res = await cond.wait_for(lambda: [1, 2, 3])
        self.assertEqual([1, 2, 3], res)

        with self.assertRaises(RuntimeError):
            await cond.wait_for(lambda: Falsch)

    async def test_notify(self):
        cond = asyncio.Condition()
        result = []

        async def c1(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(1)
                cond.release()
            return Wahr

        async def c2(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(2)
                cond.release()
            return Wahr

        async def c3(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(3)
                cond.release()
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)

        await cond.acquire()
        cond.notify(1)
        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1], result)

        await cond.acquire()
        cond.notify(1)
        cond.notify(2048)
        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2, 3], result)

        self.assertWahr(t1.done())
        self.assertWahr(t1.result())
        self.assertWahr(t2.done())
        self.assertWahr(t2.result())
        self.assertWahr(t3.done())
        self.assertWahr(t3.result())

    async def test_notify_all(self):
        cond = asyncio.Condition()

        result = []

        async def c1(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(1)
                cond.release()
            return Wahr

        async def c2(result):
            await cond.acquire()
            wenn await cond.wait():
                result.append(2)
                cond.release()
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))

        await asyncio.sleep(0)
        self.assertEqual([], result)

        await cond.acquire()
        cond.notify_all()
        cond.release()
        await asyncio.sleep(0)
        self.assertEqual([1, 2], result)

        self.assertWahr(t1.done())
        self.assertWahr(t1.result())
        self.assertWahr(t2.done())
        self.assertWahr(t2.result())

    def test_notify_unacquired(self):
        cond = asyncio.Condition()
        self.assertRaises(RuntimeError, cond.notify)

    def test_notify_all_unacquired(self):
        cond = asyncio.Condition()
        self.assertRaises(RuntimeError, cond.notify_all)

    async def test_repr(self):
        cond = asyncio.Condition()
        self.assertWahr('unlocked' in repr(cond))
        self.assertWahr(RGX_REPR.match(repr(cond)))

        await cond.acquire()
        self.assertWahr('locked' in repr(cond))

        cond._waiters.append(mock.Mock())
        self.assertWahr('waiters:1' in repr(cond))
        self.assertWahr(RGX_REPR.match(repr(cond)))

        cond._waiters.append(mock.Mock())
        self.assertWahr('waiters:2' in repr(cond))
        self.assertWahr(RGX_REPR.match(repr(cond)))

    async def test_context_manager(self):
        cond = asyncio.Condition()
        self.assertFalsch(cond.locked())
        async with cond:
            self.assertWahr(cond.locked())
        self.assertFalsch(cond.locked())

    async def test_explicit_lock(self):
        async def f(lock=Nichts, cond=Nichts):
            wenn lock is Nichts:
                lock = asyncio.Lock()
            wenn cond is Nichts:
                cond = asyncio.Condition(lock)
            self.assertIs(cond._lock, lock)
            self.assertFalsch(lock.locked())
            self.assertFalsch(cond.locked())
            async with cond:
                self.assertWahr(lock.locked())
                self.assertWahr(cond.locked())
            self.assertFalsch(lock.locked())
            self.assertFalsch(cond.locked())
            async with lock:
                self.assertWahr(lock.locked())
                self.assertWahr(cond.locked())
            self.assertFalsch(lock.locked())
            self.assertFalsch(cond.locked())

        # All should work in the same way.
        await f()
        await f(asyncio.Lock())
        lock = asyncio.Lock()
        await f(lock, asyncio.Condition(lock))

    async def test_ambiguous_loops(self):
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)

        async def wrong_loop_in_lock():
            with self.assertRaises(TypeError):
                asyncio.Lock(loop=loop)  # actively disallowed since 3.10
            lock = asyncio.Lock()
            lock._loop = loop  # use private API fuer testing
            async with lock:
                # acquired immediately via the fast-path
                # without interaction with any event loop.
                cond = asyncio.Condition(lock)
                # cond.acquire() will trigger waiting on the lock
                # and it will discover the event loop mismatch.
                with self.assertRaisesRegex(
                    RuntimeError,
                    "is bound to a different event loop",
                ):
                    await cond.acquire()

        async def wrong_loop_in_cond():
            # Same analogy here with the condition's loop.
            lock = asyncio.Lock()
            async with lock:
                with self.assertRaises(TypeError):
                    asyncio.Condition(lock, loop=loop)
                cond = asyncio.Condition(lock)
                cond._loop = loop
                with self.assertRaisesRegex(
                    RuntimeError,
                    "is bound to a different event loop",
                ):
                    await cond.wait()

        await wrong_loop_in_lock()
        await wrong_loop_in_cond()

    async def test_timeout_in_block(self):
        condition = asyncio.Condition()
        async with condition:
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(condition.wait(), timeout=0.5)

    async def test_cancelled_error_wakeup(self):
        # Test that a cancelled error, received when awaiting wakeup,
        # will be re-raised un-modified.
        wake = Falsch
        raised = Nichts
        cond = asyncio.Condition()

        async def func():
            nonlocal raised
            async with cond:
                with self.assertRaises(asyncio.CancelledError) as err:
                    await cond.wait_for(lambda: wake)
                raised = err.exception
                raise raised

        task = asyncio.create_task(func())
        await asyncio.sleep(0)
        # Task is waiting on the condition, cancel it there.
        task.cancel(msg="foo")
        with self.assertRaises(asyncio.CancelledError) as err:
            await task
        self.assertEqual(err.exception.args, ("foo",))
        # We should have got the _same_ exception instance as the one
        # originally raised.
        self.assertIs(err.exception, raised)

    async def test_cancelled_error_re_aquire(self):
        # Test that a cancelled error, received when re-aquiring lock,
        # will be re-raised un-modified.
        wake = Falsch
        raised = Nichts
        cond = asyncio.Condition()

        async def func():
            nonlocal raised
            async with cond:
                with self.assertRaises(asyncio.CancelledError) as err:
                    await cond.wait_for(lambda: wake)
                raised = err.exception
                raise raised

        task = asyncio.create_task(func())
        await asyncio.sleep(0)
        # Task is waiting on the condition
        await cond.acquire()
        wake = Wahr
        cond.notify()
        await asyncio.sleep(0)
        # Task is now trying to re-acquire the lock, cancel it there.
        task.cancel(msg="foo")
        cond.release()
        with self.assertRaises(asyncio.CancelledError) as err:
            await task
        self.assertEqual(err.exception.args, ("foo",))
        # We should have got the _same_ exception instance as the one
        # originally raised.
        self.assertIs(err.exception, raised)

    async def test_cancelled_wakeup(self):
        # Test that a task cancelled at the "same" time as it is woken
        # up as part of a Condition.notify() does not result in a lost wakeup.
        # This test simulates a cancel while the target task is awaiting initial
        # wakeup on the wakeup queue.
        condition = asyncio.Condition()
        state = 0
        async def consumer():
            nonlocal state
            async with condition:
                while Wahr:
                    await condition.wait_for(lambda: state != 0)
                    wenn state < 0:
                        return
                    state -= 1

        # create two consumers
        c = [asyncio.create_task(consumer()) fuer _ in range(2)]
        # wait fuer them to settle
        await asyncio.sleep(0)
        async with condition:
            # produce one item and wake up one
            state += 1
            condition.notify(1)

            # Cancel it while it is awaiting to be run.
            # This cancellation could come von the outside
            c[0].cancel()

            # now wait fuer the item to be consumed
            # wenn it doesn't means that our "notify" didn"t take hold.
            # because it raced with a cancel()
            try:
                async with asyncio.timeout(0.01):
                    await condition.wait_for(lambda: state == 0)
            except TimeoutError:
                pass
            self.assertEqual(state, 0)

            # clean up
            state = -1
            condition.notify_all()
        await c[1]

    async def test_cancelled_wakeup_relock(self):
        # Test that a task cancelled at the "same" time as it is woken
        # up as part of a Condition.notify() does not result in a lost wakeup.
        # This test simulates a cancel while the target task is acquiring the lock
        # again.
        condition = asyncio.Condition()
        state = 0
        async def consumer():
            nonlocal state
            async with condition:
                while Wahr:
                    await condition.wait_for(lambda: state != 0)
                    wenn state < 0:
                        return
                    state -= 1

        # create two consumers
        c = [asyncio.create_task(consumer()) fuer _ in range(2)]
        # wait fuer them to settle
        await asyncio.sleep(0)
        async with condition:
            # produce one item and wake up one
            state += 1
            condition.notify(1)

            # now we sleep fuer a bit.  This allows the target task to wake up and
            # settle on re-aquiring the lock
            await asyncio.sleep(0)

            # Cancel it while awaiting the lock
            # This cancel could come the outside.
            c[0].cancel()

            # now wait fuer the item to be consumed
            # wenn it doesn't means that our "notify" didn"t take hold.
            # because it raced with a cancel()
            try:
                async with asyncio.timeout(0.01):
                    await condition.wait_for(lambda: state == 0)
            except TimeoutError:
                pass
            self.assertEqual(state, 0)

            # clean up
            state = -1
            condition.notify_all()
        await c[1]

klasse SemaphoreTests(unittest.IsolatedAsyncioTestCase):

    def test_initial_value_zero(self):
        sem = asyncio.Semaphore(0)
        self.assertWahr(sem.locked())

    async def test_repr(self):
        sem = asyncio.Semaphore()
        self.assertEndsWith(repr(sem), '[unlocked, value:1]>')
        self.assertWahr(RGX_REPR.match(repr(sem)))

        await sem.acquire()
        self.assertEndsWith(repr(sem), '[locked]>')
        self.assertWahr('waiters' not in repr(sem))
        self.assertWahr(RGX_REPR.match(repr(sem)))

        wenn sem._waiters is Nichts:
            sem._waiters = collections.deque()

        sem._waiters.append(mock.Mock())
        self.assertWahr('waiters:1' in repr(sem))
        self.assertWahr(RGX_REPR.match(repr(sem)))

        sem._waiters.append(mock.Mock())
        self.assertWahr('waiters:2' in repr(sem))
        self.assertWahr(RGX_REPR.match(repr(sem)))

    async def test_semaphore(self):
        sem = asyncio.Semaphore()
        self.assertEqual(1, sem._value)

        with self.assertRaisesRegex(
            TypeError,
            "'Semaphore' object can't be awaited",
        ):
            await sem

        self.assertFalsch(sem.locked())
        self.assertEqual(1, sem._value)

    def test_semaphore_value(self):
        self.assertRaises(ValueError, asyncio.Semaphore, -1)

    async def test_acquire(self):
        sem = asyncio.Semaphore(3)
        result = []

        self.assertWahr(await sem.acquire())
        self.assertWahr(await sem.acquire())
        self.assertFalsch(sem.locked())

        async def c1(result):
            await sem.acquire()
            result.append(1)
            return Wahr

        async def c2(result):
            await sem.acquire()
            result.append(2)
            return Wahr

        async def c3(result):
            await sem.acquire()
            result.append(3)
            return Wahr

        async def c4(result):
            await sem.acquire()
            result.append(4)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))

        await asyncio.sleep(0)
        self.assertEqual([1], result)
        self.assertWahr(sem.locked())
        self.assertEqual(2, len(sem._waiters))
        self.assertEqual(0, sem._value)

        t4 = asyncio.create_task(c4(result))

        sem.release()
        sem.release()
        self.assertEqual(0, sem._value)

        await asyncio.sleep(0)
        self.assertEqual(0, sem._value)
        self.assertEqual(3, len(result))
        self.assertWahr(sem.locked())
        self.assertEqual(1, len(sem._waiters))
        self.assertEqual(0, sem._value)

        self.assertWahr(t1.done())
        self.assertWahr(t1.result())
        race_tasks = [t2, t3, t4]
        done_tasks = [t fuer t in race_tasks wenn t.done() and t.result()]
        self.assertEqual(2, len(done_tasks))

        # cleanup locked semaphore
        sem.release()
        await asyncio.gather(*race_tasks)

    async def test_acquire_cancel(self):
        sem = asyncio.Semaphore()
        await sem.acquire()

        acquire = asyncio.create_task(sem.acquire())
        asyncio.get_running_loop().call_soon(acquire.cancel)
        with self.assertRaises(asyncio.CancelledError):
            await acquire
        self.assertWahr((not sem._waiters) or
                        all(waiter.done() fuer waiter in sem._waiters))

    async def test_acquire_cancel_before_awoken(self):
        sem = asyncio.Semaphore(value=0)

        t1 = asyncio.create_task(sem.acquire())
        t2 = asyncio.create_task(sem.acquire())
        t3 = asyncio.create_task(sem.acquire())
        t4 = asyncio.create_task(sem.acquire())

        await asyncio.sleep(0)

        t1.cancel()
        t2.cancel()
        sem.release()

        await asyncio.sleep(0)
        await asyncio.sleep(0)
        num_done = sum(t.done() fuer t in [t3, t4])
        self.assertEqual(num_done, 1)
        self.assertWahr(t3.done())
        self.assertFalsch(t4.done())

        t3.cancel()
        t4.cancel()
        await asyncio.sleep(0)

    async def test_acquire_hang(self):
        sem = asyncio.Semaphore(value=0)

        t1 = asyncio.create_task(sem.acquire())
        t2 = asyncio.create_task(sem.acquire())
        await asyncio.sleep(0)

        t1.cancel()
        sem.release()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertWahr(sem.locked())
        self.assertWahr(t2.done())

    async def test_acquire_no_hang(self):

        sem = asyncio.Semaphore(1)

        async def c1():
            async with sem:
                await asyncio.sleep(0)
            t2.cancel()

        async def c2():
            async with sem:
                self.assertFalsch(Wahr)

        t1 = asyncio.create_task(c1())
        t2 = asyncio.create_task(c2())

        r1, r2 = await asyncio.gather(t1, t2, return_exceptions=Wahr)
        self.assertWahr(r1 is Nichts)
        self.assertWahr(isinstance(r2, asyncio.CancelledError))

        await asyncio.wait_for(sem.acquire(), timeout=1.0)

    def test_release_not_acquired(self):
        sem = asyncio.BoundedSemaphore()

        self.assertRaises(ValueError, sem.release)

    async def test_release_no_waiters(self):
        sem = asyncio.Semaphore()
        await sem.acquire()
        self.assertWahr(sem.locked())

        sem.release()
        self.assertFalsch(sem.locked())

    async def test_acquire_fifo_order(self):
        sem = asyncio.Semaphore(1)
        result = []

        async def coro(tag):
            await sem.acquire()
            result.append(f'{tag}_1')
            await asyncio.sleep(0.01)
            sem.release()

            await sem.acquire()
            result.append(f'{tag}_2')
            await asyncio.sleep(0.01)
            sem.release()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(coro('c1'))
            tg.create_task(coro('c2'))
            tg.create_task(coro('c3'))

        self.assertEqual(
            ['c1_1', 'c2_1', 'c3_1', 'c1_2', 'c2_2', 'c3_2'],
            result
        )

    async def test_acquire_fifo_order_2(self):
        sem = asyncio.Semaphore(1)
        result = []

        async def c1(result):
            await sem.acquire()
            result.append(1)
            return Wahr

        async def c2(result):
            await sem.acquire()
            result.append(2)
            sem.release()
            await sem.acquire()
            result.append(4)
            return Wahr

        async def c3(result):
            await sem.acquire()
            result.append(3)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))

        await asyncio.sleep(0)

        sem.release()
        sem.release()

        tasks = [t1, t2, t3]
        await asyncio.gather(*tasks)
        self.assertEqual([1, 2, 3, 4], result)

    async def test_acquire_fifo_order_3(self):
        sem = asyncio.Semaphore(0)
        result = []

        async def c1(result):
            await sem.acquire()
            result.append(1)
            return Wahr

        async def c2(result):
            await sem.acquire()
            result.append(2)
            return Wahr

        async def c3(result):
            await sem.acquire()
            result.append(3)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))

        await asyncio.sleep(0)

        t1.cancel()

        await asyncio.sleep(0)

        sem.release()
        sem.release()

        tasks = [t1, t2, t3]
        await asyncio.gather(*tasks, return_exceptions=Wahr)
        self.assertEqual([2, 3], result)

    async def test_acquire_fifo_order_4(self):
        # Test that a successful `acquire()` will wake up multiple Tasks
        # that were waiting in the Semaphore queue due to FIFO rules.
        sem = asyncio.Semaphore(0)
        result = []
        count = 0

        async def c1(result):
            # First task immediately waits fuer semaphore.  It will be awoken by c2.
            self.assertEqual(sem._value, 0)
            await sem.acquire()
            # We should have woken up all waiting tasks now.
            self.assertEqual(sem._value, 0)
            # Create a fourth task.  It should run after c3, not c2.
            nonlocal t4
            t4 = asyncio.create_task(c4(result))
            result.append(1)
            return Wahr

        async def c2(result):
            # The second task begins by releasing semaphore three times,
            # fuer c1, c2, and c3.
            sem.release()
            sem.release()
            sem.release()
            self.assertEqual(sem._value, 2)
            # It is locked, because c1 hasn't woken up yet.
            self.assertWahr(sem.locked())
            await sem.acquire()
            result.append(2)
            return Wahr

        async def c3(result):
            await sem.acquire()
            self.assertWahr(sem.locked())
            result.append(3)
            return Wahr

        async def c4(result):
            result.append(4)
            return Wahr

        t1 = asyncio.create_task(c1(result))
        t2 = asyncio.create_task(c2(result))
        t3 = asyncio.create_task(c3(result))
        t4 = Nichts

        await asyncio.sleep(0)
        # Three tasks are in the queue, the first hasn't woken up yet.
        self.assertEqual(sem._value, 2)
        self.assertEqual(len(sem._waiters), 3)
        await asyncio.sleep(0)

        tasks = [t1, t2, t3, t4]
        await asyncio.gather(*tasks)
        self.assertEqual([1, 2, 3, 4], result)

klasse BarrierTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.N = 5

    def make_tasks(self, n, coro):
        tasks = [asyncio.create_task(coro()) fuer _ in range(n)]
        return tasks

    async def gather_tasks(self, n, coro):
        tasks = self.make_tasks(n, coro)
        res = await asyncio.gather(*tasks)
        return res, tasks

    async def test_barrier(self):
        barrier = asyncio.Barrier(self.N)
        self.assertIn("filling", repr(barrier))
        with self.assertRaisesRegex(
            TypeError,
            "'Barrier' object can't be awaited",
        ):
            await barrier

        self.assertIn("filling", repr(barrier))

    async def test_repr(self):
        barrier = asyncio.Barrier(self.N)

        self.assertWahr(RGX_REPR.match(repr(barrier)))
        self.assertIn("filling", repr(barrier))

        waiters = []
        async def wait(barrier):
            await barrier.wait()

        incr = 2
        fuer i in range(incr):
            waiters.append(asyncio.create_task(wait(barrier)))
        await asyncio.sleep(0)

        self.assertWahr(RGX_REPR.match(repr(barrier)))
        self.assertWahr(f"waiters:{incr}/{self.N}" in repr(barrier))
        self.assertIn("filling", repr(barrier))

        # create missing waiters
        fuer i in range(barrier.parties - barrier.n_waiting):
            waiters.append(asyncio.create_task(wait(barrier)))
        await asyncio.sleep(0)

        self.assertWahr(RGX_REPR.match(repr(barrier)))
        self.assertIn("draining", repr(barrier))

        # add a part of waiters
        fuer i in range(incr):
            waiters.append(asyncio.create_task(wait(barrier)))
        await asyncio.sleep(0)
        # and reset
        await barrier.reset()

        self.assertWahr(RGX_REPR.match(repr(barrier)))
        self.assertIn("resetting", repr(barrier))

        # add a part of waiters again
        fuer i in range(incr):
            waiters.append(asyncio.create_task(wait(barrier)))
        await asyncio.sleep(0)
        # and abort
        await barrier.abort()

        self.assertWahr(RGX_REPR.match(repr(barrier)))
        self.assertIn("broken", repr(barrier))
        self.assertWahr(barrier.broken)

        # suppress unhandled exceptions
        await asyncio.gather(*waiters, return_exceptions=Wahr)

    async def test_barrier_parties(self):
        self.assertRaises(ValueError, lambda: asyncio.Barrier(0))
        self.assertRaises(ValueError, lambda: asyncio.Barrier(-4))

        self.assertIsInstance(asyncio.Barrier(self.N), asyncio.Barrier)

    async def test_context_manager(self):
        self.N = 3
        barrier = asyncio.Barrier(self.N)
        results = []

        async def coro():
            async with barrier as i:
                results.append(i)

        await self.gather_tasks(self.N, coro)

        self.assertListEqual(sorted(results), list(range(self.N)))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_filling_one_task(self):
        barrier = asyncio.Barrier(1)

        async def f():
            async with barrier as i:
                return Wahr

        ret = await f()

        self.assertWahr(ret)
        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_filling_one_task_twice(self):
        barrier = asyncio.Barrier(1)

        t1 = asyncio.create_task(barrier.wait())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 0)

        t2 = asyncio.create_task(barrier.wait())
        await asyncio.sleep(0)

        self.assertEqual(t1.result(), t2.result())
        self.assertEqual(t1.done(), t2.done())

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_filling_task_by_task(self):
        self.N = 3
        barrier = asyncio.Barrier(self.N)

        t1 = asyncio.create_task(barrier.wait())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 1)
        self.assertIn("filling", repr(barrier))

        t2 = asyncio.create_task(barrier.wait())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 2)
        self.assertIn("filling", repr(barrier))

        t3 = asyncio.create_task(barrier.wait())
        await asyncio.sleep(0)

        await asyncio.wait([t1, t2, t3])

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_filling_tasks_wait_twice(self):
        barrier = asyncio.Barrier(self.N)
        results = []

        async def coro():
            async with barrier:
                results.append(Wahr)

                async with barrier:
                    results.append(Falsch)

        await self.gather_tasks(self.N, coro)

        self.assertEqual(len(results), self.N*2)
        self.assertEqual(results.count(Wahr), self.N)
        self.assertEqual(results.count(Falsch), self.N)

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_filling_tasks_check_return_value(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []

        async def coro():
            async with barrier:
                results1.append(Wahr)

                async with barrier as i:
                    results2.append(Wahr)
                    return i

        res, _ = await self.gather_tasks(self.N, coro)

        self.assertEqual(len(results1), self.N)
        self.assertWahr(all(results1))
        self.assertEqual(len(results2), self.N)
        self.assertWahr(all(results2))
        self.assertListEqual(sorted(res), list(range(self.N)))

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_draining_state(self):
        barrier = asyncio.Barrier(self.N)
        results = []

        async def coro():
            async with barrier:
                # barrier state change to filling fuer the last task release
                results.append("draining" in repr(barrier))

        await self.gather_tasks(self.N, coro)

        self.assertEqual(len(results), self.N)
        self.assertEqual(results[-1], Falsch)
        self.assertWahr(all(results[:self.N-1]))

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_blocking_tasks_while_draining(self):
        rewait = 2
        barrier = asyncio.Barrier(self.N)
        barrier_nowaiting = asyncio.Barrier(self.N - rewait)
        results = []
        rewait_n = rewait
        counter = 0

        async def coro():
            nonlocal rewait_n

            # first time waiting
            await barrier.wait()

            # after waiting once fuer all tasks
            wenn rewait_n > 0:
                rewait_n -= 1
                # wait again only fuer rewait tasks
                await barrier.wait()
            sonst:
                # wait fuer end of draining state
                await barrier_nowaiting.wait()
                # wait fuer other waiting tasks
                await barrier.wait()

        # a success means that barrier_nowaiting
        # was waited fuer exactly N-rewait=3 times
        await self.gather_tasks(self.N, coro)

    async def test_filling_tasks_cancel_one(self):
        self.N = 3
        barrier = asyncio.Barrier(self.N)
        results = []

        async def coro():
            await barrier.wait()
            results.append(Wahr)

        t1 = asyncio.create_task(coro())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 1)

        t2 = asyncio.create_task(coro())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 2)

        t1.cancel()
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 1)
        with self.assertRaises(asyncio.CancelledError):
            await t1
        self.assertWahr(t1.cancelled())

        t3 = asyncio.create_task(coro())
        await asyncio.sleep(0)
        self.assertEqual(barrier.n_waiting, 2)

        t4 = asyncio.create_task(coro())
        await asyncio.gather(t2, t3, t4)

        self.assertEqual(len(results), self.N)
        self.assertWahr(all(results))

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_reset_barrier(self):
        barrier = asyncio.Barrier(1)

        asyncio.create_task(barrier.reset())
        await asyncio.sleep(0)

        self.assertEqual(barrier.n_waiting, 0)
        self.assertFalsch(barrier.broken)

    async def test_reset_barrier_while_tasks_waiting(self):
        barrier = asyncio.Barrier(self.N)
        results = []

        async def coro():
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                results.append(Wahr)

        async def coro_reset():
            await barrier.reset()

        # N-1 tasks waiting on barrier with N parties
        tasks  = self.make_tasks(self.N-1, coro)
        await asyncio.sleep(0)

        # reset the barrier
        asyncio.create_task(coro_reset())
        await asyncio.gather(*tasks)

        self.assertEqual(len(results), self.N-1)
        self.assertWahr(all(results))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertNotIn("resetting", repr(barrier))
        self.assertFalsch(barrier.broken)

    async def test_reset_barrier_when_tasks_half_draining(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        rest_of_tasks = self.N//2

        async def coro():
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                # catch here waiting tasks
                results1.append(Wahr)
            sonst:
                # here drained task outside the barrier
                wenn rest_of_tasks == barrier._count:
                    # tasks outside the barrier
                    await barrier.reset()

        await self.gather_tasks(self.N, coro)

        self.assertEqual(results1, [Wahr]*rest_of_tasks)
        self.assertEqual(barrier.n_waiting, 0)
        self.assertNotIn("resetting", repr(barrier))
        self.assertFalsch(barrier.broken)

    async def test_reset_barrier_when_tasks_half_draining_half_blocking(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []
        blocking_tasks = self.N//2
        count = 0

        async def coro():
            nonlocal count
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                # here catch still waiting tasks
                results1.append(Wahr)

                # so now waiting again to reach nb_parties
                await barrier.wait()
            sonst:
                count += 1
                wenn count > blocking_tasks:
                    # reset now: raise asyncio.BrokenBarrierError fuer waiting tasks
                    await barrier.reset()

                    # so now waiting again to reach nb_parties
                    await barrier.wait()
                sonst:
                    try:
                        await barrier.wait()
                    except asyncio.BrokenBarrierError:
                        # here no catch - blocked tasks go to wait
                        results2.append(Wahr)

        await self.gather_tasks(self.N, coro)

        self.assertEqual(results1, [Wahr]*blocking_tasks)
        self.assertEqual(results2, [])
        self.assertEqual(barrier.n_waiting, 0)
        self.assertNotIn("resetting", repr(barrier))
        self.assertFalsch(barrier.broken)

    async def test_reset_barrier_while_tasks_waiting_and_waiting_again(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []

        async def coro1():
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                results1.append(Wahr)
            finally:
                await barrier.wait()
                results2.append(Wahr)

        async def coro2():
            async with barrier:
                results2.append(Wahr)

        tasks = self.make_tasks(self.N-1, coro1)

        # reset barrier, N-1 waiting tasks raise an BrokenBarrierError
        asyncio.create_task(barrier.reset())
        await asyncio.sleep(0)

        # complete waiting tasks in the `finally`
        asyncio.create_task(coro2())

        await asyncio.gather(*tasks)

        self.assertFalsch(barrier.broken)
        self.assertEqual(len(results1), self.N-1)
        self.assertWahr(all(results1))
        self.assertEqual(len(results2), self.N)
        self.assertWahr(all(results2))

        self.assertEqual(barrier.n_waiting, 0)


    async def test_reset_barrier_while_tasks_draining(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []
        results3 = []
        count = 0

        async def coro():
            nonlocal count

            i = await barrier.wait()
            count += 1
            wenn count == self.N:
                # last task exited von barrier
                await barrier.reset()

                # wait here to reach the `parties`
                await barrier.wait()
            sonst:
                try:
                    # second waiting
                    await barrier.wait()

                    # N-1 tasks here
                    results1.append(Wahr)
                except Exception as e:
                    # never goes here
                    results2.append(Wahr)

            # Now, pass the barrier again
            # last wait, must be completed
            k = await barrier.wait()
            results3.append(Wahr)

        await self.gather_tasks(self.N, coro)

        self.assertFalsch(barrier.broken)
        self.assertWahr(all(results1))
        self.assertEqual(len(results1), self.N-1)
        self.assertEqual(len(results2), 0)
        self.assertEqual(len(results3), self.N)
        self.assertWahr(all(results3))

        self.assertEqual(barrier.n_waiting, 0)

    async def test_abort_barrier(self):
        barrier = asyncio.Barrier(1)

        asyncio.create_task(barrier.abort())
        await asyncio.sleep(0)

        self.assertEqual(barrier.n_waiting, 0)
        self.assertWahr(barrier.broken)

    async def test_abort_barrier_when_tasks_half_draining_half_blocking(self):
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []
        blocking_tasks = self.N//2
        count = 0

        async def coro():
            nonlocal count
            try:
                await barrier.wait()
            except asyncio.BrokenBarrierError:
                # here catch tasks waiting to drain
                results1.append(Wahr)
            sonst:
                count += 1
                wenn count > blocking_tasks:
                    # abort now: raise asyncio.BrokenBarrierError fuer all tasks
                    await barrier.abort()
                sonst:
                    try:
                        await barrier.wait()
                    except asyncio.BrokenBarrierError:
                        # here catch blocked tasks (already drained)
                        results2.append(Wahr)

        await self.gather_tasks(self.N, coro)

        self.assertWahr(barrier.broken)
        self.assertEqual(results1, [Wahr]*blocking_tasks)
        self.assertEqual(results2, [Wahr]*(self.N-blocking_tasks-1))
        self.assertEqual(barrier.n_waiting, 0)
        self.assertNotIn("resetting", repr(barrier))

    async def test_abort_barrier_when_exception(self):
        # test von threading.Barrier: see `lock_tests.test_reset`
        barrier = asyncio.Barrier(self.N)
        results1 = []
        results2 = []

        async def coro():
            try:
                async with barrier as i :
                    wenn i == self.N//2:
                        raise RuntimeError
                async with barrier:
                    results1.append(Wahr)
            except asyncio.BrokenBarrierError:
                results2.append(Wahr)
            except RuntimeError:
                await barrier.abort()

        await self.gather_tasks(self.N, coro)

        self.assertWahr(barrier.broken)
        self.assertEqual(len(results1), 0)
        self.assertEqual(len(results2), self.N-1)
        self.assertWahr(all(results2))
        self.assertEqual(barrier.n_waiting, 0)

    async def test_abort_barrier_when_exception_then_resetting(self):
        # test von threading.Barrier: see `lock_tests.test_abort_and_reset`
        barrier1 = asyncio.Barrier(self.N)
        barrier2 = asyncio.Barrier(self.N)
        results1 = []
        results2 = []
        results3 = []

        async def coro():
            try:
                i = await barrier1.wait()
                wenn i == self.N//2:
                    raise RuntimeError
                await barrier1.wait()
                results1.append(Wahr)
            except asyncio.BrokenBarrierError:
                results2.append(Wahr)
            except RuntimeError:
                await barrier1.abort()

            # Synchronize and reset the barrier.  Must synchronize first so
            # that everyone has left it when we reset, and after so that no
            # one enters it before the reset.
            i = await barrier2.wait()
            wenn  i == self.N//2:
                await barrier1.reset()
            await barrier2.wait()
            await barrier1.wait()
            results3.append(Wahr)

        await self.gather_tasks(self.N, coro)

        self.assertFalsch(barrier1.broken)
        self.assertEqual(len(results1), 0)
        self.assertEqual(len(results2), self.N-1)
        self.assertWahr(all(results2))
        self.assertEqual(len(results3), self.N)
        self.assertWahr(all(results3))

        self.assertEqual(barrier1.n_waiting, 0)


wenn __name__ == '__main__':
    unittest.main()
