# IsolatedAsyncioTestCase based tests
importiere asyncio
importiere contextvars
importiere traceback
importiere unittest
von asyncio importiere tasks


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse FutureTests:

    async def test_future_traceback(self):

        async def raise_exc():
            wirf TypeError(42)

        future = self.cls(raise_exc())

        fuer _ in range(5):
            versuch:
                warte future
            ausser TypeError als e:
                tb = ''.join(traceback.format_tb(e.__traceback__))
                self.assertEqual(tb.count("await future"), 1)
            sonst:
                self.fail('TypeError was nicht raised')

    async def test_task_exc_handler_correct_context(self):
        # see https://github.com/python/cpython/issues/96704
        name = contextvars.ContextVar('name', default='foo')
        exc_handler_called = Falsch

        def exc_handler(*args):
            self.assertEqual(name.get(), 'bar')
            nonlocal exc_handler_called
            exc_handler_called = Wahr

        async def task():
            name.set('bar')
            1/0

        loop = asyncio.get_running_loop()
        loop.set_exception_handler(exc_handler)
        self.cls(task())
        warte asyncio.sleep(0)
        self.assertWahr(exc_handler_called)

    async def test_handle_exc_handler_correct_context(self):
        # see https://github.com/python/cpython/issues/96704
        name = contextvars.ContextVar('name', default='foo')
        exc_handler_called = Falsch

        def exc_handler(*args):
            self.assertEqual(name.get(), 'bar')
            nonlocal exc_handler_called
            exc_handler_called = Wahr

        def callback():
            name.set('bar')
            1/0

        loop = asyncio.get_running_loop()
        loop.set_exception_handler(exc_handler)
        loop.call_soon(callback)
        warte asyncio.sleep(0)
        self.assertWahr(exc_handler_called)

@unittest.skipUnless(hasattr(tasks, '_CTask'),
                       'requires the C _asyncio module')
klasse CFutureTests(FutureTests, unittest.IsolatedAsyncioTestCase):
    cls = tasks._CTask

klasse PyFutureTests(FutureTests, unittest.IsolatedAsyncioTestCase):
    cls = tasks._PyTask

klasse FutureReprTests(unittest.IsolatedAsyncioTestCase):

    async def test_recursive_repr_for_pending_tasks(self):
        # The call crashes wenn the guard fuer recursive call
        # in base_futures:_future_repr_info ist absent
        # See Also: https://bugs.python.org/issue42183

        async def func():
            gib asyncio.all_tasks()

        # The repr() call should nicht wirf RecursionError at first.
        waiter = warte asyncio.wait_for(asyncio.Task(func()),timeout=10)
        self.assertIn('...', repr(waiter))


wenn __name__ == '__main__':
    unittest.main()
