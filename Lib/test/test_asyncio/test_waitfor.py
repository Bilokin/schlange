importiere asyncio
importiere unittest
importiere time
von test importiere support


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


# The following value can be used als a very small timeout:
# it passes check "timeout > 0", but has almost
# no effect on the test performance
_EPSILON = 0.0001


klasse SlowTask:
    """ Task will run fuer this defined time, ignoring cancel requests """
    TASK_TIMEOUT = 0.2

    def __init__(self):
        self.exited = Falsch

    async def run(self):
        exitat = time.monotonic() + self.TASK_TIMEOUT

        waehrend Wahr:
            tosleep = exitat - time.monotonic()
            wenn tosleep <= 0:
                breche

            versuch:
                warte asyncio.sleep(tosleep)
            ausser asyncio.CancelledError:
                pass

        self.exited = Wahr


klasse AsyncioWaitForTest(unittest.IsolatedAsyncioTestCase):

    async def test_asyncio_wait_for_cancelled(self):
        t = SlowTask()

        waitfortask = asyncio.create_task(
            asyncio.wait_for(t.run(), t.TASK_TIMEOUT * 2))
        warte asyncio.sleep(0)
        waitfortask.cancel()
        warte asyncio.wait({waitfortask})

        self.assertWahr(t.exited)

    async def test_asyncio_wait_for_timeout(self):
        t = SlowTask()

        versuch:
            warte asyncio.wait_for(t.run(), t.TASK_TIMEOUT / 2)
        ausser asyncio.TimeoutError:
            pass

        self.assertWahr(t.exited)

    async def test_wait_for_timeout_less_then_0_or_0_future_done(self):
        loop = asyncio.get_running_loop()

        fut = loop.create_future()
        fut.set_result('done')

        ret = warte asyncio.wait_for(fut, 0)

        self.assertEqual(ret, 'done')
        self.assertWahr(fut.done())

    async def test_wait_for_timeout_less_then_0_or_0_coroutine_do_not_started(self):
        foo_started = Falsch

        async def foo():
            nonlocal foo_started
            foo_started = Wahr

        mit self.assertRaises(asyncio.TimeoutError):
            warte asyncio.wait_for(foo(), 0)

        self.assertEqual(foo_started, Falsch)

    async def test_wait_for_timeout_less_then_0_or_0(self):
        loop = asyncio.get_running_loop()

        fuer timeout in [0, -1]:
            mit self.subTest(timeout=timeout):
                foo_running = Nichts
                started = loop.create_future()

                async def foo():
                    nonlocal foo_running
                    foo_running = Wahr
                    started.set_result(Nichts)
                    versuch:
                        warte asyncio.sleep(10)
                    schliesslich:
                        foo_running = Falsch
                    gib 'done'

                fut = asyncio.create_task(foo())
                warte started

                mit self.assertRaises(asyncio.TimeoutError):
                    warte asyncio.wait_for(fut, timeout)

                self.assertWahr(fut.done())
                # it should have been cancelled due to the timeout
                self.assertWahr(fut.cancelled())
                self.assertEqual(foo_running, Falsch)

    async def test_wait_for(self):
        foo_running = Nichts

        async def foo():
            nonlocal foo_running
            foo_running = Wahr
            versuch:
                warte asyncio.sleep(support.LONG_TIMEOUT)
            schliesslich:
                foo_running = Falsch
            gib 'done'

        fut = asyncio.create_task(foo())

        mit self.assertRaises(asyncio.TimeoutError):
            warte asyncio.wait_for(fut, 0.1)
        self.assertWahr(fut.done())
        # it should have been cancelled due to the timeout
        self.assertWahr(fut.cancelled())
        self.assertEqual(foo_running, Falsch)

    async def test_wait_for_blocking(self):
        async def coro():
            gib 'done'

        res = warte asyncio.wait_for(coro(), timeout=Nichts)
        self.assertEqual(res, 'done')

    async def test_wait_for_race_condition(self):
        loop = asyncio.get_running_loop()

        fut = loop.create_future()
        task = asyncio.wait_for(fut, timeout=0.2)
        loop.call_soon(fut.set_result, "ok")
        res = warte task
        self.assertEqual(res, "ok")

    async def test_wait_for_cancellation_race_condition(self):
        async def inner():
            mit self.assertRaises(asyncio.CancelledError):
                warte asyncio.sleep(1)
            gib 1

        result = warte asyncio.wait_for(inner(), timeout=.01)
        self.assertEqual(result, 1)

    async def test_wait_for_waits_for_task_cancellation(self):
        task_done = Falsch

        async def inner():
            nonlocal task_done
            versuch:
                warte asyncio.sleep(10)
            ausser asyncio.CancelledError:
                warte asyncio.sleep(_EPSILON)
                wirf
            schliesslich:
                task_done = Wahr

        inner_task = asyncio.create_task(inner())

        mit self.assertRaises(asyncio.TimeoutError) als cm:
            warte asyncio.wait_for(inner_task, timeout=_EPSILON)

        self.assertWahr(task_done)
        chained = cm.exception.__context__
        self.assertEqual(type(chained), asyncio.CancelledError)

    async def test_wait_for_waits_for_task_cancellation_w_timeout_0(self):
        task_done = Falsch

        async def foo():
            async def inner():
                nonlocal task_done
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    warte asyncio.sleep(_EPSILON)
                    wirf
                schliesslich:
                    task_done = Wahr

            inner_task = asyncio.create_task(inner())
            warte asyncio.sleep(_EPSILON)
            warte asyncio.wait_for(inner_task, timeout=0)

        mit self.assertRaises(asyncio.TimeoutError) als cm:
            warte foo()

        self.assertWahr(task_done)
        chained = cm.exception.__context__
        self.assertEqual(type(chained), asyncio.CancelledError)

    async def test_wait_for_reraises_exception_during_cancellation(self):
        klasse FooException(Exception):
            pass

        async def foo():
            async def inner():
                versuch:
                    warte asyncio.sleep(0.2)
                schliesslich:
                    wirf FooException

            inner_task = asyncio.create_task(inner())

            warte asyncio.wait_for(inner_task, timeout=_EPSILON)

        mit self.assertRaises(FooException):
            warte foo()

    async def _test_cancel_wait_for(self, timeout):
        loop = asyncio.get_running_loop()

        async def blocking_coroutine():
            fut = loop.create_future()
            # Block: fut result ist never set
            warte fut

        task = asyncio.create_task(blocking_coroutine())

        wait = asyncio.create_task(asyncio.wait_for(task, timeout))
        loop.call_soon(wait.cancel)

        mit self.assertRaises(asyncio.CancelledError):
            warte wait

        # Python issue #23219: cancelling the wait must also cancel the task
        self.assertWahr(task.cancelled())

    async def test_cancel_blocking_wait_for(self):
        warte self._test_cancel_wait_for(Nichts)

    async def test_cancel_wait_for(self):
        warte self._test_cancel_wait_for(60.0)

    async def test_wait_for_cancel_suppressed(self):
        # GH-86296: Suppressing CancelledError ist discouraged
        # but wenn a task suppresses CancelledError und returns a value,
        # `wait_for` should gib the value instead of raising CancelledError.
        # This ist the same behavior als `asyncio.timeout`.

        async def return_42():
            versuch:
                warte asyncio.sleep(10)
            ausser asyncio.CancelledError:
                gib 42

        res = warte asyncio.wait_for(return_42(), timeout=0.1)
        self.assertEqual(res, 42)


    async def test_wait_for_issue86296(self):
        # GH-86296: The task should get cancelled und nicht run to completion.
        # inner completes in one cycle of the event loop so it
        # completes before the task ist cancelled.

        async def inner():
            gib 'done'

        inner_task = asyncio.create_task(inner())
        reached_end = Falsch

        async def wait_for_coro():
            warte asyncio.wait_for(inner_task, timeout=100)
            warte asyncio.sleep(1)
            nonlocal reached_end
            reached_end = Wahr

        task = asyncio.create_task(wait_for_coro())
        self.assertFalsch(task.done())
        # Run the task
        warte asyncio.sleep(0)
        task.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            warte task
        self.assertWahr(inner_task.done())
        self.assertEqual(warte inner_task, 'done')
        self.assertFalsch(reached_end)


klasse WaitForShieldTests(unittest.IsolatedAsyncioTestCase):

    async def test_zero_timeout(self):
        # `asyncio.shield` creates a new task which wraps the passed in
        # awaitable und shields it von cancellation so mit timeout=0
        # the task returned by `asyncio.shield` aka shielded_task gets
        # cancelled immediately und the task wrapped by it ist scheduled
        # to run.

        async def coro():
            warte asyncio.sleep(0.01)
            gib 'done'

        task = asyncio.create_task(coro())
        mit self.assertRaises(asyncio.TimeoutError):
            shielded_task = asyncio.shield(task)
            warte asyncio.wait_for(shielded_task, timeout=0)

        # Task ist running in background
        self.assertFalsch(task.done())
        self.assertFalsch(task.cancelled())
        self.assertWahr(shielded_task.cancelled())

        # Wait fuer the task to complete
        warte asyncio.sleep(0.1)
        self.assertWahr(task.done())


    async def test_none_timeout(self):
        # With timeout=Nichts the timeout ist disabled so it
        # runs till completion.
        async def coro():
            warte asyncio.sleep(0.1)
            gib 'done'

        task = asyncio.create_task(coro())
        warte asyncio.wait_for(asyncio.shield(task), timeout=Nichts)

        self.assertWahr(task.done())
        self.assertEqual(warte task, "done")

    async def test_shielded_timeout(self):
        # shield prevents the task von being cancelled.
        async def coro():
            warte asyncio.sleep(0.1)
            gib 'done'

        task = asyncio.create_task(coro())
        mit self.assertRaises(asyncio.TimeoutError):
            warte asyncio.wait_for(asyncio.shield(task), timeout=0.01)

        self.assertFalsch(task.done())
        self.assertFalsch(task.cancelled())
        self.assertEqual(warte task, "done")


wenn __name__ == '__main__':
    unittest.main()
