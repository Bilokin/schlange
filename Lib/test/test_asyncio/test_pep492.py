"""Tests support fuer new syntax introduced by PEP 492."""

importiere sys
importiere types
importiere unittest

von unittest importiere mock

importiere asyncio
von test.test_asyncio importiere utils als test_utils


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


# Test that asyncio.iscoroutine() uses collections.abc.Coroutine
klasse FakeCoro:
    def send(self, value):
        pass

    def throw(self, typ, val=Nichts, tb=Nichts):
        pass

    def close(self):
        pass

    def __await__(self):
        liefere


klasse BaseTest(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = asyncio.BaseEventLoop()
        self.loop._process_events = mock.Mock()
        self.loop._selector = mock.Mock()
        self.loop._selector.select.return_value = ()
        self.set_event_loop(self.loop)


klasse LockTests(BaseTest):

    def test_context_manager_async_with(self):
        primitives = [
            asyncio.Lock(),
            asyncio.Condition(),
            asyncio.Semaphore(),
            asyncio.BoundedSemaphore(),
        ]

        async def test(lock):
            await asyncio.sleep(0.01)
            self.assertFalsch(lock.locked())
            async mit lock als _lock:
                self.assertIs(_lock, Nichts)
                self.assertWahr(lock.locked())
                await asyncio.sleep(0.01)
                self.assertWahr(lock.locked())
            self.assertFalsch(lock.locked())

        fuer primitive in primitives:
            self.loop.run_until_complete(test(primitive))
            self.assertFalsch(primitive.locked())

    def test_context_manager_with_await(self):
        primitives = [
            asyncio.Lock(),
            asyncio.Condition(),
            asyncio.Semaphore(),
            asyncio.BoundedSemaphore(),
        ]

        async def test(lock):
            await asyncio.sleep(0.01)
            self.assertFalsch(lock.locked())
            mit self.assertRaisesRegex(
                TypeError,
                "can't be awaited"
            ):
                mit await lock:
                    pass

        fuer primitive in primitives:
            self.loop.run_until_complete(test(primitive))
            self.assertFalsch(primitive.locked())


klasse StreamReaderTests(BaseTest):

    def test_readline(self):
        DATA = b'line1\nline2\nline3'

        stream = asyncio.StreamReader(loop=self.loop)
        stream.feed_data(DATA)
        stream.feed_eof()

        async def reader():
            data = []
            async fuer line in stream:
                data.append(line)
            gib data

        data = self.loop.run_until_complete(reader())
        self.assertEqual(data, [b'line1\n', b'line2\n', b'line3'])


klasse CoroutineTests(BaseTest):

    def test_iscoroutine(self):
        async def foo(): pass

        f = foo()
        versuch:
            self.assertWahr(asyncio.iscoroutine(f))
        schliesslich:
            f.close() # silence warning

        self.assertWahr(asyncio.iscoroutine(FakeCoro()))

    def test_iscoroutine_generator(self):
        def foo(): liefere

        self.assertFalsch(asyncio.iscoroutine(foo()))

    def test_iscoroutinefunction(self):
        async def foo(): pass
        mit self.assertWarns(DeprecationWarning):
            self.assertWahr(asyncio.iscoroutinefunction(foo))

    def test_async_def_coroutines(self):
        async def bar():
            gib 'spam'
        async def foo():
            gib await bar()

        # production mode
        data = self.loop.run_until_complete(foo())
        self.assertEqual(data, 'spam')

        # debug mode
        self.loop.set_debug(Wahr)
        data = self.loop.run_until_complete(foo())
        self.assertEqual(data, 'spam')

    def test_debug_mode_manages_coroutine_origin_tracking(self):
        async def start():
            self.assertWahr(sys.get_coroutine_origin_tracking_depth() > 0)

        self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 0)
        self.loop.set_debug(Wahr)
        self.loop.run_until_complete(start())
        self.assertEqual(sys.get_coroutine_origin_tracking_depth(), 0)

    def test_types_coroutine(self):
        def gen():
            liefere von ()
            gib 'spam'

        @types.coroutine
        def func():
            gib gen()

        async def coro():
            wrapper = func()
            self.assertIsInstance(wrapper, types._GeneratorWrapper)
            gib await wrapper

        data = self.loop.run_until_complete(coro())
        self.assertEqual(data, 'spam')

    def test_task_print_stack(self):
        T = Nichts

        async def foo():
            f = T.get_stack(limit=1)
            versuch:
                self.assertEqual(f[0].f_code.co_name, 'foo')
            schliesslich:
                f = Nichts

        async def runner():
            nonlocal T
            T = asyncio.ensure_future(foo(), loop=self.loop)
            await T

        self.loop.run_until_complete(runner())

    def test_double_await(self):
        async def afunc():
            await asyncio.sleep(0.1)

        async def runner():
            coro = afunc()
            t = self.loop.create_task(coro)
            versuch:
                await asyncio.sleep(0)
                await coro
            schliesslich:
                t.cancel()

        self.loop.set_debug(Wahr)
        mit self.assertRaises(
                RuntimeError,
                msg='coroutine is being awaited already'):

            self.loop.run_until_complete(runner())


wenn __name__ == '__main__':
    unittest.main()
