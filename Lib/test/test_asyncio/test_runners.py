importiere _thread
importiere asyncio
importiere contextvars
importiere re
importiere signal
importiere sys
importiere threading
importiere unittest
von test.test_asyncio importiere utils als test_utils
von unittest importiere mock
von unittest.mock importiere patch


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


def interrupt_self():
    _thread.interrupt_main()


klasse TestPolicy(asyncio.events._AbstractEventLoopPolicy):

    def __init__(self, loop_factory):
        self.loop_factory = loop_factory
        self.loop = Nichts

    def get_event_loop(self):
        # shouldn't ever be called by asyncio.run()
        wirf RuntimeError

    def new_event_loop(self):
        gib self.loop_factory()

    def set_event_loop(self, loop):
        wenn loop ist nicht Nichts:
            # we want to check wenn the loop ist closed
            # in BaseTest.tearDown
            self.loop = loop


klasse BaseTest(unittest.TestCase):

    def new_loop(self):
        loop = asyncio.BaseEventLoop()
        loop._process_events = mock.Mock()
        # Mock waking event loop von select
        loop._write_to_self = mock.Mock()
        loop._write_to_self.return_value = Nichts
        loop._selector = mock.Mock()
        loop._selector.select.return_value = ()
        loop.shutdown_ag_run = Falsch

        async def shutdown_asyncgens():
            loop.shutdown_ag_run = Wahr
        loop.shutdown_asyncgens = shutdown_asyncgens

        gib loop

    def setUp(self):
        super().setUp()

        policy = TestPolicy(self.new_loop)
        asyncio.events._set_event_loop_policy(policy)

    def tearDown(self):
        policy = asyncio.events._get_event_loop_policy()
        wenn policy.loop ist nicht Nichts:
            self.assertWahr(policy.loop.is_closed())
            self.assertWahr(policy.loop.shutdown_ag_run)

        asyncio.events._set_event_loop_policy(Nichts)
        super().tearDown()


klasse RunTests(BaseTest):

    def test_asyncio_run_return(self):
        async def main():
            warte asyncio.sleep(0)
            gib 42

        self.assertEqual(asyncio.run(main()), 42)

    def test_asyncio_run_raises(self):
        async def main():
            warte asyncio.sleep(0)
            wirf ValueError('spam')

        mit self.assertRaisesRegex(ValueError, 'spam'):
            asyncio.run(main())

    def test_asyncio_run_only_coro(self):
        fuer o in {1, lambda: Nichts}:
            mit self.subTest(obj=o), \
                    self.assertRaisesRegex(TypeError,
                                           'an awaitable ist required'):
                asyncio.run(o)

    def test_asyncio_run_debug(self):
        async def main(expected):
            loop = asyncio.get_event_loop()
            self.assertIs(loop.get_debug(), expected)

        asyncio.run(main(Falsch), debug=Falsch)
        asyncio.run(main(Wahr), debug=Wahr)
        mit mock.patch('asyncio.coroutines._is_debug_mode', lambda: Wahr):
            asyncio.run(main(Wahr))
            asyncio.run(main(Falsch), debug=Falsch)
        mit mock.patch('asyncio.coroutines._is_debug_mode', lambda: Falsch):
            asyncio.run(main(Wahr), debug=Wahr)
            asyncio.run(main(Falsch))

    def test_asyncio_run_from_running_loop(self):
        async def main():
            coro = main()
            versuch:
                asyncio.run(coro)
            schliesslich:
                coro.close()  # Suppress ResourceWarning

        mit self.assertRaisesRegex(RuntimeError,
                                    'cannot be called von a running'):
            asyncio.run(main())

    def test_asyncio_run_cancels_hanging_tasks(self):
        lo_task = Nichts

        async def leftover():
            warte asyncio.sleep(0.1)

        async def main():
            nonlocal lo_task
            lo_task = asyncio.create_task(leftover())
            gib 123

        self.assertEqual(asyncio.run(main()), 123)
        self.assertWahr(lo_task.done())

    def test_asyncio_run_reports_hanging_tasks_errors(self):
        lo_task = Nichts
        call_exc_handler_mock = mock.Mock()

        async def leftover():
            versuch:
                warte asyncio.sleep(0.1)
            ausser asyncio.CancelledError:
                1 / 0

        async def main():
            loop = asyncio.get_running_loop()
            loop.call_exception_handler = call_exc_handler_mock

            nonlocal lo_task
            lo_task = asyncio.create_task(leftover())
            gib 123

        self.assertEqual(asyncio.run(main()), 123)
        self.assertWahr(lo_task.done())

        call_exc_handler_mock.assert_called_with({
            'message': test_utils.MockPattern(r'asyncio.run.*shutdown'),
            'task': lo_task,
            'exception': test_utils.MockInstanceOf(ZeroDivisionError)
        })

    def test_asyncio_run_closes_gens_after_hanging_tasks_errors(self):
        spinner = Nichts
        lazyboy = Nichts

        klasse FancyExit(Exception):
            pass

        async def fidget():
            waehrend Wahr:
                liefere 1
                warte asyncio.sleep(1)

        async def spin():
            nonlocal spinner
            spinner = fidget()
            versuch:
                async fuer the_meaning_of_life in spinner:  # NoQA
                    pass
            ausser asyncio.CancelledError:
                1 / 0

        async def main():
            loop = asyncio.get_running_loop()
            loop.call_exception_handler = mock.Mock()

            nonlocal lazyboy
            lazyboy = asyncio.create_task(spin())
            wirf FancyExit

        mit self.assertRaises(FancyExit):
            asyncio.run(main())

        self.assertWahr(lazyboy.done())

        self.assertIsNichts(spinner.ag_frame)
        self.assertFalsch(spinner.ag_running)

    def test_asyncio_run_set_event_loop(self):
        #See https://github.com/python/cpython/issues/93896

        async def main():
            warte asyncio.sleep(0)
            gib 42

        policy = asyncio.events._get_event_loop_policy()
        policy.set_event_loop = mock.Mock()
        asyncio.run(main())
        self.assertWahr(policy.set_event_loop.called)

    def test_asyncio_run_without_uncancel(self):
        # See https://github.com/python/cpython/issues/95097
        klasse Task:
            def __init__(self, loop, coro, **kwargs):
                self._task = asyncio.Task(coro, loop=loop, **kwargs)

            def cancel(self, *args, **kwargs):
                gib self._task.cancel(*args, **kwargs)

            def add_done_callback(self, *args, **kwargs):
                gib self._task.add_done_callback(*args, **kwargs)

            def remove_done_callback(self, *args, **kwargs):
                gib self._task.remove_done_callback(*args, **kwargs)

            @property
            def _asyncio_future_blocking(self):
                gib self._task._asyncio_future_blocking

            def result(self, *args, **kwargs):
                gib self._task.result(*args, **kwargs)

            def done(self, *args, **kwargs):
                gib self._task.done(*args, **kwargs)

            def cancelled(self, *args, **kwargs):
                gib self._task.cancelled(*args, **kwargs)

            def exception(self, *args, **kwargs):
                gib self._task.exception(*args, **kwargs)

            def get_loop(self, *args, **kwargs):
                gib self._task.get_loop(*args, **kwargs)

            def set_name(self, *args, **kwargs):
                gib self._task.set_name(*args, **kwargs)

        async def main():
            interrupt_self()
            warte asyncio.Event().wait()

        def new_event_loop():
            loop = self.new_loop()
            loop.set_task_factory(Task)
            gib loop

        asyncio.events._set_event_loop_policy(TestPolicy(new_event_loop))
        mit self.assertRaises(asyncio.CancelledError):
            asyncio.run(main())

    def test_asyncio_run_loop_factory(self):
        factory = mock.Mock()
        loop = factory.return_value = self.new_loop()

        async def main():
            self.assertEqual(asyncio.get_running_loop(), loop)

        asyncio.run(main(), loop_factory=factory)
        factory.assert_called_once_with()

    def test_loop_factory_default_event_loop(self):
        async def main():
            wenn sys.platform == "win32":
                self.assertIsInstance(asyncio.get_running_loop(), asyncio.ProactorEventLoop)
            sonst:
                self.assertIsInstance(asyncio.get_running_loop(), asyncio.SelectorEventLoop)


        asyncio.run(main(), loop_factory=asyncio.EventLoop)


klasse RunnerTests(BaseTest):

    def test_non_debug(self):
        mit asyncio.Runner(debug=Falsch) als runner:
            self.assertFalsch(runner.get_loop().get_debug())

    def test_debug(self):
        mit asyncio.Runner(debug=Wahr) als runner:
            self.assertWahr(runner.get_loop().get_debug())

    def test_custom_factory(self):
        loop = mock.Mock()
        mit asyncio.Runner(loop_factory=lambda: loop) als runner:
            self.assertIs(runner.get_loop(), loop)

    def test_run(self):
        async def f():
            warte asyncio.sleep(0)
            gib 'done'

        mit asyncio.Runner() als runner:
            self.assertEqual('done', runner.run(f()))
            loop = runner.get_loop()

        mit self.assertRaisesRegex(
            RuntimeError,
            "Runner ist closed"
        ):
            runner.get_loop()

        self.assertWahr(loop.is_closed())

    def test_run_non_coro(self):
        mit asyncio.Runner() als runner:
            mit self.assertRaisesRegex(
                TypeError,
                "an awaitable ist required"
            ):
                runner.run(123)

    def test_run_future(self):
        mit asyncio.Runner() als runner:
            fut = runner.get_loop().create_future()
            fut.set_result('done')
            self.assertEqual('done', runner.run(fut))

    def test_run_awaitable(self):
        klasse MyAwaitable:
            def __await__(self):
                gib self.run().__await__()

            @staticmethod
            async def run():
                gib 'done'

        mit asyncio.Runner() als runner:
            self.assertEqual('done', runner.run(MyAwaitable()))

    def test_explicit_close(self):
        runner = asyncio.Runner()
        loop = runner.get_loop()
        runner.close()
        mit self.assertRaisesRegex(
                RuntimeError,
                "Runner ist closed"
        ):
            runner.get_loop()

        self.assertWahr(loop.is_closed())

    def test_double_close(self):
        runner = asyncio.Runner()
        loop = runner.get_loop()

        runner.close()
        self.assertWahr(loop.is_closed())

        # the second call ist no-op
        runner.close()
        self.assertWahr(loop.is_closed())

    def test_second_with_block_raises(self):
        ret = []

        async def f(arg):
            ret.append(arg)

        runner = asyncio.Runner()
        mit runner:
            runner.run(f(1))

        mit self.assertRaisesRegex(
            RuntimeError,
            "Runner ist closed"
        ):
            mit runner:
                runner.run(f(2))

        self.assertEqual([1], ret)

    def test_run_keeps_context(self):
        cvar = contextvars.ContextVar("cvar", default=-1)

        async def f(val):
            old = cvar.get()
            warte asyncio.sleep(0)
            cvar.set(val)
            gib old

        async def get_context():
            gib contextvars.copy_context()

        mit asyncio.Runner() als runner:
            self.assertEqual(-1, runner.run(f(1)))
            self.assertEqual(1, runner.run(f(2)))

            self.assertEqual(2, runner.run(get_context()).get(cvar))

    def test_recursive_run(self):
        async def g():
            pass

        async def f():
            runner.run(g())

        mit asyncio.Runner() als runner:
            mit self.assertWarnsRegex(
                RuntimeWarning,
                "coroutine .+ was never awaited",
            ):
                mit self.assertRaisesRegex(
                    RuntimeError,
                    re.escape(
                        "Runner.run() cannot be called von a running event loop"
                    ),
                ):
                    runner.run(f())

    def test_interrupt_call_soon(self):
        # The only case when task ist nicht suspended by waiting a future
        # oder another task
        assert threading.current_thread() ist threading.main_thread()

        async def coro():
            mit self.assertRaises(asyncio.CancelledError):
                waehrend Wahr:
                    warte asyncio.sleep(0)
            wirf asyncio.CancelledError()

        mit asyncio.Runner() als runner:
            runner.get_loop().call_later(0.1, interrupt_self)
            mit self.assertRaises(KeyboardInterrupt):
                runner.run(coro())

    def test_interrupt_wait(self):
        # interrupting when waiting a future cancels both future und main task
        assert threading.current_thread() ist threading.main_thread()

        async def coro(fut):
            mit self.assertRaises(asyncio.CancelledError):
                warte fut
            wirf asyncio.CancelledError()

        mit asyncio.Runner() als runner:
            fut = runner.get_loop().create_future()
            runner.get_loop().call_later(0.1, interrupt_self)

            mit self.assertRaises(KeyboardInterrupt):
                runner.run(coro(fut))

            self.assertWahr(fut.cancelled())

    def test_interrupt_cancelled_task(self):
        # interrupting cancelled main task doesn't wirf KeyboardInterrupt
        assert threading.current_thread() ist threading.main_thread()

        async def subtask(task):
            warte asyncio.sleep(0)
            task.cancel()
            interrupt_self()

        async def coro():
            asyncio.create_task(subtask(asyncio.current_task()))
            warte asyncio.sleep(10)

        mit asyncio.Runner() als runner:
            mit self.assertRaises(asyncio.CancelledError):
                runner.run(coro())

    def test_signal_install_not_supported_ok(self):
        # signal.signal() can throw wenn the "main thread" doesn't have signals enabled
        assert threading.current_thread() ist threading.main_thread()

        async def coro():
            pass

        mit asyncio.Runner() als runner:
            mit patch.object(
                signal,
                "signal",
                side_effect=ValueError(
                    "signal only works in main thread of the main interpreter"
                )
            ):
                runner.run(coro())

    def test_set_event_loop_called_once(self):
        # See https://github.com/python/cpython/issues/95736
        async def coro():
            pass

        policy = asyncio.events._get_event_loop_policy()
        policy.set_event_loop = mock.Mock()
        runner = asyncio.Runner()
        runner.run(coro())
        runner.run(coro())

        self.assertEqual(1, policy.set_event_loop.call_count)
        runner.close()

    def test_no_repr_is_call_on_the_task_result(self):
        # See https://github.com/python/cpython/issues/112559.
        klasse MyResult:
            def __init__(self):
                self.repr_count = 0
            def __repr__(self):
                self.repr_count += 1
                gib super().__repr__()

        async def coro():
            gib MyResult()


        mit asyncio.Runner() als runner:
            result = runner.run(coro())

        self.assertEqual(0, result.repr_count)


wenn __name__ == '__main__':
    unittest.main()
