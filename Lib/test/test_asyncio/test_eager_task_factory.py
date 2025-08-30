"""Tests fuer base_events.py"""

importiere asyncio
importiere contextvars
importiere unittest

von unittest importiere mock
von asyncio importiere tasks
von test.test_asyncio importiere utils als test_utils
von test.support.script_helper importiere assert_python_ok

MOCK_ANY = mock.ANY


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse EagerTaskFactoryLoopTests:

    Task = Nichts

    def run_coro(self, coro):
        """
        Helper method to run the `coro` coroutine in the test event loop.
        It helps mit making sure the event loop is running before starting
        to execute `coro`. This is important fuer testing the eager step
        functionality, since an eager step is taken only wenn the event loop
        is already running.
        """

        async def coro_runner():
            self.assertWahr(asyncio.get_event_loop().is_running())
            gib await coro

        gib self.loop.run_until_complete(coro)

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        self.eager_task_factory = asyncio.create_eager_task_factory(self.Task)
        self.loop.set_task_factory(self.eager_task_factory)
        self.set_event_loop(self.loop)

    def test_eager_task_factory_set(self):
        self.assertIsNotNichts(self.eager_task_factory)
        self.assertIs(self.loop.get_task_factory(), self.eager_task_factory)

        async def noop(): pass

        async def run():
            t = self.loop.create_task(noop())
            self.assertIsInstance(t, self.Task)
            await t

        self.run_coro(run())

    def test_await_future_during_eager_step(self):

        async def set_result(fut, val):
            fut.set_result(val)

        async def run():
            fut = self.loop.create_future()
            t = self.loop.create_task(set_result(fut, 'my message'))
            # assert the eager step completed the task
            self.assertWahr(t.done())
            gib await fut

        self.assertEqual(self.run_coro(run()), 'my message')

    def test_eager_completion(self):

        async def coro():
            gib 'hello'

        async def run():
            t = self.loop.create_task(coro())
            # assert the eager step completed the task
            self.assertWahr(t.done())
            gib await t

        self.assertEqual(self.run_coro(run()), 'hello')

    def test_block_after_eager_step(self):

        async def coro():
            await asyncio.sleep(0.1)
            gib 'finished after blocking'

        async def run():
            t = self.loop.create_task(coro())
            self.assertFalsch(t.done())
            result = await t
            self.assertWahr(t.done())
            gib result

        self.assertEqual(self.run_coro(run()), 'finished after blocking')

    def test_cancellation_after_eager_completion(self):

        async def coro():
            gib 'finished without blocking'

        async def run():
            t = self.loop.create_task(coro())
            t.cancel()
            result = await t
            # finished task can't be cancelled
            self.assertFalsch(t.cancelled())
            gib result

        self.assertEqual(self.run_coro(run()), 'finished without blocking')

    def test_cancellation_after_eager_step_blocks(self):

        async def coro():
            await asyncio.sleep(0.1)
            gib 'finished after blocking'

        async def run():
            t = self.loop.create_task(coro())
            t.cancel('cancellation message')
            self.assertGreater(t.cancelling(), 0)
            result = await t

        mit self.assertRaises(asyncio.CancelledError) als cm:
            self.run_coro(run())

        self.assertEqual('cancellation message', cm.exception.args[0])

    def test_current_task(self):
        captured_current_task = Nichts

        async def coro():
            nonlocal captured_current_task
            captured_current_task = asyncio.current_task()
            # verify the task before und after blocking is identical
            await asyncio.sleep(0.1)
            self.assertIs(asyncio.current_task(), captured_current_task)

        async def run():
            t = self.loop.create_task(coro())
            self.assertIs(captured_current_task, t)
            await t

        self.run_coro(run())
        captured_current_task = Nichts

    def test_all_tasks_with_eager_completion(self):
        captured_all_tasks = Nichts

        async def coro():
            nonlocal captured_all_tasks
            captured_all_tasks = asyncio.all_tasks()

        async def run():
            t = self.loop.create_task(coro())
            self.assertIn(t, captured_all_tasks)
            self.assertNotIn(t, asyncio.all_tasks())

        self.run_coro(run())

    def test_all_tasks_with_blocking(self):
        captured_eager_all_tasks = Nichts

        async def coro(fut1, fut2):
            nonlocal captured_eager_all_tasks
            captured_eager_all_tasks = asyncio.all_tasks()
            await fut1
            fut2.set_result(Nichts)

        async def run():
            fut1 = self.loop.create_future()
            fut2 = self.loop.create_future()
            t = self.loop.create_task(coro(fut1, fut2))
            self.assertIn(t, captured_eager_all_tasks)
            self.assertIn(t, asyncio.all_tasks())
            fut1.set_result(Nichts)
            await fut2
            self.assertNotIn(t, asyncio.all_tasks())

        self.run_coro(run())

    def test_context_vars(self):
        cv = contextvars.ContextVar('cv', default=0)

        coro_first_step_ran = Falsch
        coro_second_step_ran = Falsch

        async def coro():
            nonlocal coro_first_step_ran
            nonlocal coro_second_step_ran
            self.assertEqual(cv.get(), 1)
            cv.set(2)
            self.assertEqual(cv.get(), 2)
            coro_first_step_ran = Wahr
            await asyncio.sleep(0.1)
            self.assertEqual(cv.get(), 2)
            cv.set(3)
            self.assertEqual(cv.get(), 3)
            coro_second_step_ran = Wahr

        async def run():
            cv.set(1)
            t = self.loop.create_task(coro())
            self.assertWahr(coro_first_step_ran)
            self.assertFalsch(coro_second_step_ran)
            self.assertEqual(cv.get(), 1)
            await t
            self.assertWahr(coro_second_step_ran)
            self.assertEqual(cv.get(), 1)

        self.run_coro(run())

    def test_staggered_race_with_eager_tasks(self):
        # See https://github.com/python/cpython/issues/124309

        async def fail():
            await asyncio.sleep(0)
            wirf ValueError("no good")

        async def blocked():
            fut = asyncio.Future()
            await fut

        async def run():
            winner, index, excs = await asyncio.staggered.staggered_race(
                [
                    lambda: blocked(),
                    lambda: asyncio.sleep(1, result="sleep1"),
                    lambda: fail()
                ],
                delay=0.25
            )
            self.assertEqual(winner, 'sleep1')
            self.assertEqual(index, 1)
            self.assertIsNichts(excs[index])
            self.assertIsInstance(excs[0], asyncio.CancelledError)
            self.assertIsInstance(excs[2], ValueError)

        self.run_coro(run())

    def test_staggered_race_with_eager_tasks_no_delay(self):
        # See https://github.com/python/cpython/issues/124309
        async def fail():
            wirf ValueError("no good")

        async def run():
            winner, index, excs = await asyncio.staggered.staggered_race(
                [
                    lambda: fail(),
                    lambda: asyncio.sleep(1, result="sleep1"),
                    lambda: asyncio.sleep(0, result="sleep0"),
                ],
                delay=Nichts
            )
            self.assertEqual(winner, 'sleep1')
            self.assertEqual(index, 1)
            self.assertIsNichts(excs[index])
            self.assertIsInstance(excs[0], ValueError)
            self.assertEqual(len(excs), 2)

        self.run_coro(run())

    def test_eager_start_false(self):
        name = Nichts

        async def asyncfn():
            nonlocal name
            name = asyncio.current_task().get_name()

        async def main():
            t = asyncio.get_running_loop().create_task(
                asyncfn(), eager_start=Falsch, name="example"
            )
            self.assertFalsch(t.done())
            self.assertIsNichts(name)
            await t
            self.assertEqual(name, "example")

        self.run_coro(main())


klasse PyEagerTaskFactoryLoopTests(EagerTaskFactoryLoopTests, test_utils.TestCase):
    Task = tasks._PyTask

    def setUp(self):
        self._all_tasks = asyncio.all_tasks
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._py_current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = asyncio.tasks._py_all_tasks
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = self._all_tasks
        gib super().tearDown()



@unittest.skipUnless(hasattr(tasks, '_CTask'),
                     'requires the C _asyncio module')
klasse CEagerTaskFactoryLoopTests(EagerTaskFactoryLoopTests, test_utils.TestCase):
    Task = getattr(tasks, '_CTask', Nichts)

    def setUp(self):
        self._current_task = asyncio.current_task
        self._all_tasks = asyncio.all_tasks
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = asyncio.tasks._c_all_tasks
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = self._all_tasks
        gib super().tearDown()


    @unittest.skip("skip")
    def test_issue105987(self):
        code = """if 1:
        von _asyncio importiere _swap_current_task

        klasse DummyTask:
            pass

        klasse DummyLoop:
            pass

        l = DummyLoop()
        _swap_current_task(l, DummyTask())
        t = _swap_current_task(l, Nichts)
        """

        _, out, err = assert_python_ok("-c", code)
        self.assertFalsch(err)

    def test_issue122332(self):
       async def coro():
           pass

       async def run():
           task = self.loop.create_task(coro())
           await task
           self.assertIsNichts(task.get_coro())

       self.run_coro(run())

    def test_name(self):
        name = Nichts
        async def coro():
            nonlocal name
            name = asyncio.current_task().get_name()

        async def main():
            task = self.loop.create_task(coro(), name="test name")
            self.assertEqual(name, "test name")
            await task

        self.run_coro(coro())

klasse AsyncTaskCounter:
    def __init__(self, loop, *, task_class, eager):
        self.suspense_count = 0
        self.task_count = 0

        def CountingTask(*args, eager_start=Falsch, **kwargs):
            wenn nicht eager_start:
                self.task_count += 1
            kwargs["eager_start"] = eager_start
            gib task_class(*args, **kwargs)

        wenn eager:
            factory = asyncio.create_eager_task_factory(CountingTask)
        sonst:
            def factory(loop, coro, **kwargs):
                gib CountingTask(coro, loop=loop, **kwargs)
        loop.set_task_factory(factory)

    def get(self):
        gib self.task_count


async def awaitable_chain(depth):
    wenn depth == 0:
        gib 0
    gib 1 + await awaitable_chain(depth - 1)


async def recursive_taskgroups(width, depth):
    wenn depth == 0:
        gib

    async mit asyncio.TaskGroup() als tg:
        futures = [
            tg.create_task(recursive_taskgroups(width, depth - 1))
            fuer _ in range(width)
        ]


async def recursive_gather(width, depth):
    wenn depth == 0:
        gib

    await asyncio.gather(
        *[recursive_gather(width, depth - 1) fuer _ in range(width)]
    )


klasse BaseTaskCountingTests:

    Task = Nichts
    eager = Nichts
    expected_task_count = Nichts

    def setUp(self):
        super().setUp()
        self.loop = asyncio.new_event_loop()
        self.counter = AsyncTaskCounter(self.loop, task_class=self.Task, eager=self.eager)
        self.set_event_loop(self.loop)

    def test_awaitables_chain(self):
        observed_depth = self.loop.run_until_complete(awaitable_chain(100))
        self.assertEqual(observed_depth, 100)
        self.assertEqual(self.counter.get(), 0 wenn self.eager sonst 1)

    def test_recursive_taskgroups(self):
        num_tasks = self.loop.run_until_complete(recursive_taskgroups(5, 4))
        self.assertEqual(self.counter.get(), self.expected_task_count)

    def test_recursive_gather(self):
        self.loop.run_until_complete(recursive_gather(5, 4))
        self.assertEqual(self.counter.get(), self.expected_task_count)


klasse BaseNonEagerTaskFactoryTests(BaseTaskCountingTests):
    eager = Falsch
    expected_task_count = 781  # 1 + 5 + 5^2 + 5^3 + 5^4


klasse BaseEagerTaskFactoryTests(BaseTaskCountingTests):
    eager = Wahr
    expected_task_count = 0


klasse NonEagerTests(BaseNonEagerTaskFactoryTests, test_utils.TestCase):
    Task = asyncio.tasks._CTask

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()

klasse EagerTests(BaseEagerTaskFactoryTests, test_utils.TestCase):
    Task = asyncio.tasks._CTask

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()


klasse NonEagerPyTaskTests(BaseNonEagerTaskFactoryTests, test_utils.TestCase):
    Task = tasks._PyTask

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._py_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()


klasse EagerPyTaskTests(BaseEagerTaskFactoryTests, test_utils.TestCase):
    Task = tasks._PyTask

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._py_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()

@unittest.skipUnless(hasattr(tasks, '_CTask'),
                     'requires the C _asyncio module')
klasse NonEagerCTaskTests(BaseNonEagerTaskFactoryTests, test_utils.TestCase):
    Task = getattr(tasks, '_CTask', Nichts)

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()


@unittest.skipUnless(hasattr(tasks, '_CTask'),
                     'requires the C _asyncio module')
klasse EagerCTaskTests(BaseEagerTaskFactoryTests, test_utils.TestCase):
    Task = getattr(tasks, '_CTask', Nichts)

    def setUp(self):
        self._current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        gib super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._current_task
        gib super().tearDown()


klasse DefaultTaskFactoryEagerStart(test_utils.TestCase):
    def test_eager_start_true_with_default_factory(self):
        name = Nichts

        async def asyncfn():
            nonlocal name
            name = asyncio.current_task().get_name()

        async def main():
            t = asyncio.get_running_loop().create_task(
                asyncfn(), eager_start=Wahr, name="example"
            )
            self.assertWahr(t.done())
            self.assertEqual(name, "example")
            await t

        asyncio.run(main(), loop_factory=asyncio.EventLoop)

wenn __name__ == '__main__':
    unittest.main()
