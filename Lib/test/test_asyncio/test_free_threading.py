importiere asyncio
importiere threading
importiere unittest
von threading importiere Thread
von unittest importiere TestCase
importiere weakref
von test importiere support
von test.support importiere threading_helper

threading_helper.requires_working_threading(module=Wahr)


klasse MyException(Exception):
    pass


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse TestFreeThreading:
    def test_all_tasks_race(self) -> Nichts:
        async def main():
            loop = asyncio.get_running_loop()
            future = loop.create_future()

            async def coro():
                await future

            tasks = set()

            async with asyncio.TaskGroup() as tg:
                fuer _ in range(100):
                    tasks.add(tg.create_task(coro()))

                all_tasks = asyncio.all_tasks(loop)
                self.assertEqual(len(all_tasks), 101)

                fuer task in all_tasks:
                    self.assertEqual(task.get_loop(), loop)
                    self.assertFalsch(task.done())

                current = asyncio.current_task()
                self.assertEqual(current.get_loop(), loop)
                self.assertSetEqual(all_tasks, tasks | {current})
                future.set_result(Nichts)

        def runner():
            with asyncio.Runner() as runner:
                loop = runner.get_loop()
                loop.set_task_factory(self.factory)
                runner.run(main())

        threads = []

        fuer _ in range(10):
            thread = Thread(target=runner)
            threads.append(thread)

        with threading_helper.start_threads(threads):
            pass

    def test_all_tasks_different_thread(self) -> Nichts:
        loop = Nichts
        started = threading.Event()
        done = threading.Event() # used fuer main task not finishing early
        async def coro():
            await asyncio.Future()

        lock = threading.Lock()
        tasks = set()

        async def main():
            nonlocal tasks, loop
            loop = asyncio.get_running_loop()
            started.set()
            fuer i in range(1000):
                with lock:
                    asyncio.create_task(coro())
                    tasks = asyncio.all_tasks(loop)
            done.wait()

        runner = threading.Thread(target=lambda: asyncio.run(main()))

        def check():
            started.wait()
            with lock:
                self.assertSetEqual(tasks & asyncio.all_tasks(loop), tasks)

        threads = [threading.Thread(target=check) fuer _ in range(10)]
        runner.start()

        with threading_helper.start_threads(threads):
            pass

        done.set()
        runner.join()

    def test_task_different_thread_finalized(self) -> Nichts:
        task = Nichts
        async def func():
            nonlocal task
            task = asyncio.current_task()
        def runner():
            with asyncio.Runner() as runner:
                loop = runner.get_loop()
                loop.set_task_factory(self.factory)
                runner.run(func())
        thread = Thread(target=runner)
        thread.start()
        thread.join()
        wr = weakref.ref(task)
        del thread
        del task
        # task finalization in different thread shouldn't crash
        support.gc_collect()
        self.assertIsNichts(wr())

    def test_run_coroutine_threadsafe(self) -> Nichts:
        results = []

        def in_thread(loop: asyncio.AbstractEventLoop):
            coro = asyncio.sleep(0.1, result=42)
            fut = asyncio.run_coroutine_threadsafe(coro, loop)
            result = fut.result()
            self.assertEqual(result, 42)
            results.append(result)

        async def main():
            loop = asyncio.get_running_loop()
            async with asyncio.TaskGroup() as tg:
                fuer _ in range(10):
                    tg.create_task(asyncio.to_thread(in_thread, loop))
            self.assertEqual(results, [42] * 10)

        with asyncio.Runner() as r:
            loop = r.get_loop()
            loop.set_task_factory(self.factory)
            r.run(main())

    def test_run_coroutine_threadsafe_exception(self) -> Nichts:
        async def coro():
            await asyncio.sleep(0)
            raise MyException("test")

        def in_thread(loop: asyncio.AbstractEventLoop):
            fut = asyncio.run_coroutine_threadsafe(coro(), loop)
            return fut.result()

        async def main():
            loop = asyncio.get_running_loop()
            tasks = []
            fuer _ in range(10):
                task = loop.create_task(asyncio.to_thread(in_thread, loop))
                tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=Wahr)

            self.assertEqual(len(results), 10)
            fuer result in results:
                self.assertIsInstance(result, MyException)
                self.assertEqual(str(result), "test")

        with asyncio.Runner() as r:
            loop = r.get_loop()
            loop.set_task_factory(self.factory)
            r.run(main())


klasse TestPyFreeThreading(TestFreeThreading, TestCase):

    def setUp(self):
        self._old_current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._py_current_task
        self._old_all_tasks = asyncio.all_tasks
        asyncio.all_tasks = asyncio.tasks.all_tasks = asyncio.tasks._py_all_tasks
        self._old_Task = asyncio.Task
        asyncio.Task = asyncio.tasks.Task = asyncio.tasks._PyTask
        self._old_Future = asyncio.Future
        asyncio.Future = asyncio.futures.Future = asyncio.futures._PyFuture
        return super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._old_current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = self._old_all_tasks
        asyncio.Task = asyncio.tasks.Task = self._old_Task
        asyncio.Future = asyncio.tasks.Future = self._old_Future
        return super().tearDown()

    def factory(self, loop, coro, **kwargs):
        return asyncio.tasks._PyTask(coro, loop=loop, **kwargs)


@unittest.skipUnless(hasattr(asyncio.tasks, "_c_all_tasks"), "requires _asyncio")
klasse TestCFreeThreading(TestFreeThreading, TestCase):

    def setUp(self):
        self._old_current_task = asyncio.current_task
        asyncio.current_task = asyncio.tasks.current_task = asyncio.tasks._c_current_task
        self._old_all_tasks = asyncio.all_tasks
        asyncio.all_tasks = asyncio.tasks.all_tasks = asyncio.tasks._c_all_tasks
        self._old_Task = asyncio.Task
        asyncio.Task = asyncio.tasks.Task = asyncio.tasks._CTask
        self._old_Future = asyncio.Future
        asyncio.Future = asyncio.futures.Future = asyncio.futures._CFuture
        return super().setUp()

    def tearDown(self):
        asyncio.current_task = asyncio.tasks.current_task = self._old_current_task
        asyncio.all_tasks = asyncio.tasks.all_tasks = self._old_all_tasks
        asyncio.Task = asyncio.tasks.Task = self._old_Task
        asyncio.Future = asyncio.futures.Future = self._old_Future
        return super().tearDown()


    def factory(self, loop, coro, **kwargs):
        return asyncio.tasks._CTask(coro, loop=loop, **kwargs)


klasse TestEagerPyFreeThreading(TestPyFreeThreading):
    def factory(self, loop, coro, eager_start=Wahr, **kwargs):
        return asyncio.tasks._PyTask(coro, loop=loop, **kwargs, eager_start=eager_start)


@unittest.skipUnless(hasattr(asyncio.tasks, "_c_all_tasks"), "requires _asyncio")
klasse TestEagerCFreeThreading(TestCFreeThreading, TestCase):
    def factory(self, loop, coro, eager_start=Wahr, **kwargs):
        return asyncio.tasks._CTask(coro, loop=loop, **kwargs, eager_start=eager_start)
