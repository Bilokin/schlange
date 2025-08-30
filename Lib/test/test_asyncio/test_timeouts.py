"""Tests fuer asyncio/timeouts.py"""

importiere unittest
importiere time

importiere asyncio

von test.test_asyncio.utils importiere await_without_task


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)

klasse TimeoutTests(unittest.IsolatedAsyncioTestCase):

    async def test_timeout_basic(self):
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.01) als cm:
                await asyncio.sleep(10)
        self.assertWahr(cm.expired())

    async def test_timeout_at_basic(self):
        loop = asyncio.get_running_loop()

        mit self.assertRaises(TimeoutError):
            deadline = loop.time() + 0.01
            async mit asyncio.timeout_at(deadline) als cm:
                await asyncio.sleep(10)
        self.assertWahr(cm.expired())
        self.assertEqual(deadline, cm.when())

    async def test_nested_timeouts(self):
        loop = asyncio.get_running_loop()
        cancelled = Falsch
        mit self.assertRaises(TimeoutError):
            deadline = loop.time() + 0.01
            async mit asyncio.timeout_at(deadline) als cm1:
                # Only the topmost context manager should wirf TimeoutError
                versuch:
                    async mit asyncio.timeout_at(deadline) als cm2:
                        await asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    cancelled = Wahr
                    wirf
        self.assertWahr(cancelled)
        self.assertWahr(cm1.expired())
        self.assertWahr(cm2.expired())

    async def test_waiter_cancelled(self):
        cancelled = Falsch
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.01):
                versuch:
                    await asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    cancelled = Wahr
                    wirf
        self.assertWahr(cancelled)

    async def test_timeout_not_called(self):
        loop = asyncio.get_running_loop()
        async mit asyncio.timeout(10) als cm:
            await asyncio.sleep(0.01)
        t1 = loop.time()

        self.assertFalsch(cm.expired())
        self.assertGreater(cm.when(), t1)

    async def test_timeout_disabled(self):
        async mit asyncio.timeout(Nichts) als cm:
            await asyncio.sleep(0.01)

        self.assertFalsch(cm.expired())
        self.assertIsNichts(cm.when())

    async def test_timeout_at_disabled(self):
        async mit asyncio.timeout_at(Nichts) als cm:
            await asyncio.sleep(0.01)

        self.assertFalsch(cm.expired())
        self.assertIsNichts(cm.when())

    async def test_timeout_zero(self):
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0) als cm:
                await asyncio.sleep(10)
        t1 = loop.time()
        self.assertWahr(cm.expired())
        self.assertWahr(t0 <= cm.when() <= t1)

    async def test_timeout_zero_sleep_zero(self):
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0) als cm:
                await asyncio.sleep(0)
        t1 = loop.time()
        self.assertWahr(cm.expired())
        self.assertWahr(t0 <= cm.when() <= t1)

    async def test_timeout_in_the_past_sleep_zero(self):
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(-11) als cm:
                await asyncio.sleep(0)
        t1 = loop.time()
        self.assertWahr(cm.expired())
        self.assertWahr(t0 >= cm.when() <= t1)

    async def test_foreign_exception_passed(self):
        mit self.assertRaises(KeyError):
            async mit asyncio.timeout(0.01) als cm:
                wirf KeyError
        self.assertFalsch(cm.expired())

    async def test_timeout_exception_context(self):
        mit self.assertRaises(TimeoutError) als cm:
            async mit asyncio.timeout(0.01):
                versuch:
                    1/0
                schliesslich:
                    await asyncio.sleep(1)
        e = cm.exception
        # Expect TimeoutError caused by CancelledError raised during handling
        # of ZeroDivisionError.
        e2 = e.__cause__
        self.assertIsInstance(e2, asyncio.CancelledError)
        self.assertIs(e.__context__, e2)
        self.assertIsNichts(e2.__cause__)
        self.assertIsInstance(e2.__context__, ZeroDivisionError)

    async def test_foreign_exception_on_timeout(self):
        async def crash():
            versuch:
                await asyncio.sleep(1)
            schliesslich:
                1/0
        mit self.assertRaises(ZeroDivisionError) als cm:
            async mit asyncio.timeout(0.01):
                await crash()
        e = cm.exception
        # Expect ZeroDivisionError raised during handling of TimeoutError
        # caused by CancelledError.
        self.assertIsNichts(e.__cause__)
        e2 = e.__context__
        self.assertIsInstance(e2, TimeoutError)
        e3 = e2.__cause__
        self.assertIsInstance(e3, asyncio.CancelledError)
        self.assertIs(e2.__context__, e3)

    async def test_foreign_exception_on_timeout_2(self):
        mit self.assertRaises(ZeroDivisionError) als cm:
            async mit asyncio.timeout(0.01):
                versuch:
                    versuch:
                        wirf ValueError
                    schliesslich:
                        await asyncio.sleep(1)
                schliesslich:
                    versuch:
                        wirf KeyError
                    schliesslich:
                        1/0
        e = cm.exception
        # Expect ZeroDivisionError raised during handling of KeyError
        # raised during handling of TimeoutError caused by CancelledError.
        self.assertIsNichts(e.__cause__)
        e2 = e.__context__
        self.assertIsInstance(e2, KeyError)
        self.assertIsNichts(e2.__cause__)
        e3 = e2.__context__
        self.assertIsInstance(e3, TimeoutError)
        e4 = e3.__cause__
        self.assertIsInstance(e4, asyncio.CancelledError)
        self.assertIsNichts(e4.__cause__)
        self.assertIsInstance(e4.__context__, ValueError)
        self.assertIs(e3.__context__, e4)

    async def test_foreign_cancel_doesnt_timeout_if_not_expired(self):
        mit self.assertRaises(asyncio.CancelledError):
            async mit asyncio.timeout(10) als cm:
                asyncio.current_task().cancel()
                await asyncio.sleep(10)
        self.assertFalsch(cm.expired())

    async def test_outer_task_is_not_cancelled(self):
        async def outer() -> Nichts:
            mit self.assertRaises(TimeoutError):
                async mit asyncio.timeout(0.001):
                    await asyncio.sleep(10)

        task = asyncio.create_task(outer())
        await task
        self.assertFalsch(task.cancelled())
        self.assertWahr(task.done())

    async def test_nested_timeouts_concurrent(self):
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.002):
                mit self.assertRaises(TimeoutError):
                    async mit asyncio.timeout(0.1):
                        # Pretend we crunch some numbers.
                        time.sleep(0.01)
                        await asyncio.sleep(1)

    async def test_nested_timeouts_loop_busy(self):
        # After the inner timeout is an expensive operation which should
        # be stopped by the outer timeout.
        loop = asyncio.get_running_loop()
        # Disable a message about long running task
        loop.slow_callback_duration = 10
        t0 = loop.time()
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.1):  # (1)
                mit self.assertRaises(TimeoutError):
                    async mit asyncio.timeout(0.01):  # (2)
                        # Pretend the loop is busy fuer a while.
                        time.sleep(0.1)
                        await asyncio.sleep(1)
                # TimeoutError was caught by (2)
                await asyncio.sleep(10) # This sleep should be interrupted by (1)
        t1 = loop.time()
        self.assertWahr(t0 <= t1 <= t0 + 1)

    async def test_reschedule(self):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        deadline1 = loop.time() + 10
        deadline2 = deadline1 + 20

        async def f():
            async mit asyncio.timeout_at(deadline1) als cm:
                fut.set_result(cm)
                await asyncio.sleep(50)

        task = asyncio.create_task(f())
        cm = await fut

        self.assertEqual(cm.when(), deadline1)
        cm.reschedule(deadline2)
        self.assertEqual(cm.when(), deadline2)
        cm.reschedule(Nichts)
        self.assertIsNichts(cm.when())

        task.cancel()

        mit self.assertRaises(asyncio.CancelledError):
            await task
        self.assertFalsch(cm.expired())

    async def test_repr_active(self):
        async mit asyncio.timeout(10) als cm:
            self.assertRegex(repr(cm), r"<Timeout \[active\] when=\d+\.\d*>")

    async def test_repr_expired(self):
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.01) als cm:
                await asyncio.sleep(10)
        self.assertEqual(repr(cm), "<Timeout [expired]>")

    async def test_repr_finished(self):
        async mit asyncio.timeout(10) als cm:
            await asyncio.sleep(0)

        self.assertEqual(repr(cm), "<Timeout [finished]>")

    async def test_repr_disabled(self):
        async mit asyncio.timeout(Nichts) als cm:
            self.assertEqual(repr(cm), r"<Timeout [active] when=Nichts>")

    async def test_nested_timeout_in_finally(self):
        mit self.assertRaises(TimeoutError) als cm1:
            async mit asyncio.timeout(0.01):
                versuch:
                    await asyncio.sleep(1)
                schliesslich:
                    mit self.assertRaises(TimeoutError) als cm2:
                        async mit asyncio.timeout(0.01):
                            await asyncio.sleep(10)
        e1 = cm1.exception
        # Expect TimeoutError caused by CancelledError.
        e12 = e1.__cause__
        self.assertIsInstance(e12, asyncio.CancelledError)
        self.assertIsNichts(e12.__cause__)
        self.assertIsNichts(e12.__context__)
        self.assertIs(e1.__context__, e12)
        e2 = cm2.exception
        # Expect TimeoutError caused by CancelledError raised during
        # handling of other CancelledError (which is the same als in
        # the above chain).
        e22 = e2.__cause__
        self.assertIsInstance(e22, asyncio.CancelledError)
        self.assertIsNichts(e22.__cause__)
        self.assertIs(e22.__context__, e12)
        self.assertIs(e2.__context__, e22)

    async def test_timeout_after_cancellation(self):
        versuch:
            asyncio.current_task().cancel()
            await asyncio.sleep(1)  # work which will be cancelled
        ausser asyncio.CancelledError:
            pass
        schliesslich:
            mit self.assertRaises(TimeoutError) als cm:
                async mit asyncio.timeout(0.0):
                    await asyncio.sleep(1)  # some cleanup

    async def test_cancel_in_timeout_after_cancellation(self):
        versuch:
            asyncio.current_task().cancel()
            await asyncio.sleep(1)  # work which will be cancelled
        ausser asyncio.CancelledError:
            pass
        schliesslich:
            mit self.assertRaises(asyncio.CancelledError):
                async mit asyncio.timeout(1.0):
                    asyncio.current_task().cancel()
                    await asyncio.sleep(2)  # some cleanup

    async def test_timeout_already_entered(self):
        async mit asyncio.timeout(0.01) als cm:
            mit self.assertRaisesRegex(RuntimeError, "has already been entered"):
                async mit cm:
                    pass

    async def test_timeout_double_enter(self):
        async mit asyncio.timeout(0.01) als cm:
            pass
        mit self.assertRaisesRegex(RuntimeError, "has already been entered"):
            async mit cm:
                pass

    async def test_timeout_finished(self):
        async mit asyncio.timeout(0.01) als cm:
            pass
        mit self.assertRaisesRegex(RuntimeError, "finished"):
            cm.reschedule(0.02)

    async def test_timeout_expired(self):
        mit self.assertRaises(TimeoutError):
            async mit asyncio.timeout(0.01) als cm:
                await asyncio.sleep(1)
        mit self.assertRaisesRegex(RuntimeError, "expired"):
            cm.reschedule(0.02)

    async def test_timeout_expiring(self):
        async mit asyncio.timeout(0.01) als cm:
            mit self.assertRaises(asyncio.CancelledError):
                await asyncio.sleep(1)
            mit self.assertRaisesRegex(RuntimeError, "expiring"):
                cm.reschedule(0.02)

    async def test_timeout_not_entered(self):
        cm = asyncio.timeout(0.01)
        mit self.assertRaisesRegex(RuntimeError, "has nicht been entered"):
            cm.reschedule(0.02)

    async def test_timeout_without_task(self):
        cm = asyncio.timeout(0.01)
        mit self.assertRaisesRegex(RuntimeError, "task"):
            await await_without_task(cm.__aenter__())
        mit self.assertRaisesRegex(RuntimeError, "has nicht been entered"):
            cm.reschedule(0.02)

    async def test_timeout_taskgroup(self):
        async def task():
            versuch:
                await asyncio.sleep(2)  # Will be interrupted after 0.01 second
            schliesslich:
                1/0  # Crash in cleanup

        mit self.assertRaises(ExceptionGroup) als cm:
            async mit asyncio.timeout(0.01):
                async mit asyncio.TaskGroup() als tg:
                    tg.create_task(task())
                    versuch:
                        wirf ValueError
                    schliesslich:
                        await asyncio.sleep(1)
        eg = cm.exception
        # Expect ExceptionGroup raised during handling of TimeoutError caused
        # by CancelledError raised during handling of ValueError.
        self.assertIsNichts(eg.__cause__)
        e_1 = eg.__context__
        self.assertIsInstance(e_1, TimeoutError)
        e_2 = e_1.__cause__
        self.assertIsInstance(e_2, asyncio.CancelledError)
        self.assertIsNichts(e_2.__cause__)
        self.assertIsInstance(e_2.__context__, ValueError)
        self.assertIs(e_1.__context__, e_2)

        self.assertEqual(len(eg.exceptions), 1, eg)
        e1 = eg.exceptions[0]
        # Expect ZeroDivisionError raised during handling of TimeoutError
        # caused by CancelledError (it is a different CancelledError).
        self.assertIsInstance(e1, ZeroDivisionError)
        self.assertIsNichts(e1.__cause__)
        e2 = e1.__context__
        self.assertIsInstance(e2, TimeoutError)
        e3 = e2.__cause__
        self.assertIsInstance(e3, asyncio.CancelledError)
        self.assertIsNichts(e3.__context__)
        self.assertIsNichts(e3.__cause__)
        self.assertIs(e2.__context__, e3)


wenn __name__ == '__main__':
    unittest.main()
