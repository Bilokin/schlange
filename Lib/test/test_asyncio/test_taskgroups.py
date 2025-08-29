# Adapted mit permission von the EdgeDB project;
# license: PSFL.

importiere weakref
importiere sys
importiere gc
importiere asyncio
importiere contextvars
importiere contextlib
von asyncio importiere taskgroups
importiere unittest
importiere warnings

von test.test_asyncio.utils importiere await_without_task

# To prevent a warning "test altered the execution environment"
def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse MyExc(Exception):
    pass


klasse MyBaseExc(BaseException):
    pass


def get_error_types(eg):
    gib {type(exc) fuer exc in eg.exceptions}


def no_other_refs():
    # due to gh-124392 coroutines now refer to their locals
    coro = asyncio.current_task().get_coro()
    frame = sys._getframe(1)
    waehrend coro.cr_frame != frame:
        coro = coro.cr_await
    gib [coro]


def set_gc_state(enabled):
    was_enabled = gc.isenabled()
    wenn enabled:
        gc.enable()
    sonst:
        gc.disable()
    gib was_enabled


@contextlib.contextmanager
def disable_gc():
    was_enabled = set_gc_state(enabled=Falsch)
    try:
        liefere
    finally:
        set_gc_state(enabled=was_enabled)


klasse BaseTestTaskGroup:

    async def test_taskgroup_01(self):

        async def foo1():
            await asyncio.sleep(0.1)
            gib 42

        async def foo2():
            await asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            t2 = g.create_task(foo2())

        self.assertEqual(t1.result(), 42)
        self.assertEqual(t2.result(), 11)

    async def test_taskgroup_02(self):

        async def foo1():
            await asyncio.sleep(0.1)
            gib 42

        async def foo2():
            await asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            await asyncio.sleep(0.15)
            t2 = g.create_task(foo2())

        self.assertEqual(t1.result(), 42)
        self.assertEqual(t2.result(), 11)

    async def test_taskgroup_03(self):

        async def foo1():
            await asyncio.sleep(1)
            gib 42

        async def foo2():
            await asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            await asyncio.sleep(0.15)
            # cancel t1 explicitly, i.e. everything should weiter
            # working als expected.
            t1.cancel()

            t2 = g.create_task(foo2())

        self.assertWahr(t1.cancelled())
        self.assertEqual(t2.result(), 11)

    async def test_taskgroup_04(self):

        NUM = 0
        t2_cancel = Falsch
        t2 = Nichts

        async def foo1():
            await asyncio.sleep(0.1)
            1 / 0

        async def foo2():
            nonlocal NUM, t2_cancel
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                t2_cancel = Wahr
                raise
            NUM += 1

        async def runner():
            nonlocal NUM, t2

            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                t2 = g.create_task(foo2())

            NUM += 10

        mit self.assertRaises(ExceptionGroup) als cm:
            await asyncio.create_task(runner())

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

        self.assertEqual(NUM, 0)
        self.assertWahr(t2_cancel)
        self.assertWahr(t2.cancelled())

    async def test_cancel_children_on_child_error(self):
        # When a child task raises an error, the rest of the children
        # are cancelled und the errors are gathered into an EG.

        NUM = 0
        t2_cancel = Falsch
        runner_cancel = Falsch

        async def foo1():
            await asyncio.sleep(0.1)
            1 / 0

        async def foo2():
            nonlocal NUM, t2_cancel
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                t2_cancel = Wahr
                raise
            NUM += 1

        async def runner():
            nonlocal NUM, runner_cancel

            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                g.create_task(foo1())
                g.create_task(foo1())
                g.create_task(foo2())
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    runner_cancel = Wahr
                    raise

            NUM += 10

        # The 3 foo1 sub tasks can be racy when the host is busy - wenn the
        # cancellation happens in the middle, we'll see partial sub errors here
        mit self.assertRaises(ExceptionGroup) als cm:
            await asyncio.create_task(runner())

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})
        self.assertEqual(NUM, 0)
        self.assertWahr(t2_cancel)
        self.assertWahr(runner_cancel)

    async def test_cancellation(self):

        NUM = 0

        async def foo():
            nonlocal NUM
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                NUM += 1
                raise

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError) als cm:
            await r

        self.assertEqual(NUM, 5)

    async def test_taskgroup_07(self):

        NUM = 0

        async def foo():
            nonlocal NUM
            try:
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                NUM += 1
                raise

        async def runner():
            nonlocal NUM
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    NUM += 10
                    raise

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            await r

        self.assertEqual(NUM, 15)

    async def test_taskgroup_08(self):

        async def foo():
            try:
                await asyncio.sleep(10)
            finally:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

                await asyncio.sleep(10)

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            await r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_09(self):

        t1 = t2 = Nichts

        async def foo1():
            await asyncio.sleep(1)
            gib 42

        async def foo2():
            await asyncio.sleep(2)
            gib 11

        async def runner():
            nonlocal t1, t2
            async mit taskgroups.TaskGroup() als g:
                t1 = g.create_task(foo1())
                t2 = g.create_task(foo2())
                await asyncio.sleep(0.1)
                1 / 0

        try:
            await runner()
        except ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {ZeroDivisionError})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertWahr(t1.cancelled())
        self.assertWahr(t2.cancelled())

    async def test_taskgroup_10(self):

        t1 = t2 = Nichts

        async def foo1():
            await asyncio.sleep(1)
            gib 42

        async def foo2():
            await asyncio.sleep(2)
            gib 11

        async def runner():
            nonlocal t1, t2
            async mit taskgroups.TaskGroup() als g:
                t1 = g.create_task(foo1())
                t2 = g.create_task(foo2())
                1 / 0

        try:
            await runner()
        except ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {ZeroDivisionError})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertWahr(t1.cancelled())
        self.assertWahr(t2.cancelled())

    async def test_taskgroup_11(self):

        async def foo():
            try:
                await asyncio.sleep(10)
            finally:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup():
                async mit taskgroups.TaskGroup() als g2:
                    fuer _ in range(5):
                        g2.create_task(foo())

                    await asyncio.sleep(10)

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            await r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ZeroDivisionError})

    async def test_taskgroup_12(self):

        async def foo():
            try:
                await asyncio.sleep(10)
            finally:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(asyncio.sleep(10))

                async mit taskgroups.TaskGroup() als g2:
                    fuer _ in range(5):
                        g2.create_task(foo())

                    await asyncio.sleep(10)

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            await r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ZeroDivisionError})

    async def test_taskgroup_13(self):

        async def crash_after(t):
            await asyncio.sleep(t)
            raise ValueError(t)

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_after(0.1))

                async mit taskgroups.TaskGroup() als g2:
                    g2.create_task(crash_after(10))

        r = asyncio.create_task(runner())
        mit self.assertRaises(ExceptionGroup) als cm:
            await r

        self.assertEqual(get_error_types(cm.exception), {ValueError})

    async def test_taskgroup_14(self):

        async def crash_after(t):
            await asyncio.sleep(t)
            raise ValueError(t)

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_after(10))

                async mit taskgroups.TaskGroup() als g2:
                    g2.create_task(crash_after(0.1))

        r = asyncio.create_task(runner())
        mit self.assertRaises(ExceptionGroup) als cm:
            await r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ValueError})

    async def test_taskgroup_15(self):

        async def crash_soon():
            await asyncio.sleep(0.3)
            1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_soon())
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    await asyncio.sleep(0.5)
                    raise

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            await r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_16(self):

        async def crash_soon():
            await asyncio.sleep(0.3)
            1 / 0

        async def nested_runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_soon())
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    await asyncio.sleep(0.5)
                    raise

        async def runner():
            t = asyncio.create_task(nested_runner())
            await t

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            await r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_17(self):
        NUM = 0

        async def runner():
            nonlocal NUM
            async mit taskgroups.TaskGroup():
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    NUM += 10
                    raise

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            await r

        self.assertEqual(NUM, 10)

    async def test_taskgroup_18(self):
        NUM = 0

        async def runner():
            nonlocal NUM
            async mit taskgroups.TaskGroup():
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    NUM += 10
                    # This isn't a good idea, but we have to support
                    # this weird case.
                    raise MyExc

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()

        try:
            await r
        except ExceptionGroup als t:
            self.assertEqual(get_error_types(t),{MyExc})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertEqual(NUM, 10)

    async def test_taskgroup_19(self):
        async def crash_soon():
            await asyncio.sleep(0.1)
            1 / 0

        async def nested():
            try:
                await asyncio.sleep(10)
            finally:
                raise MyExc

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                await nested()

        r = asyncio.create_task(runner())
        try:
            await r
        except ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {MyExc, ZeroDivisionError})
        sonst:
            self.fail('TasgGroupError was nicht raised')

    async def test_taskgroup_20(self):
        async def crash_soon():
            await asyncio.sleep(0.1)
            1 / 0

        async def nested():
            try:
                await asyncio.sleep(10)
            finally:
                raise KeyboardInterrupt

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                await nested()

        mit self.assertRaises(KeyboardInterrupt):
            await runner()

    async def test_taskgroup_20a(self):
        async def crash_soon():
            await asyncio.sleep(0.1)
            1 / 0

        async def nested():
            try:
                await asyncio.sleep(10)
            finally:
                raise MyBaseExc

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                await nested()

        mit self.assertRaises(BaseExceptionGroup) als cm:
            await runner()

        self.assertEqual(
            get_error_types(cm.exception), {MyBaseExc, ZeroDivisionError}
        )

    async def _test_taskgroup_21(self):
        # This test doesn't work als asyncio, currently, doesn't
        # correctly propagate KeyboardInterrupt (or SystemExit) --
        # those cause the event loop itself to crash.
        # (Compare to the previous (passing) test -- that one raises
        # a plain exception but raises KeyboardInterrupt in nested();
        # this test does it the other way around.)

        async def crash_soon():
            await asyncio.sleep(0.1)
            raise KeyboardInterrupt

        async def nested():
            try:
                await asyncio.sleep(10)
            finally:
                raise TypeError

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                await nested()

        mit self.assertRaises(KeyboardInterrupt):
            await runner()

    async def test_taskgroup_21a(self):

        async def crash_soon():
            await asyncio.sleep(0.1)
            raise MyBaseExc

        async def nested():
            try:
                await asyncio.sleep(10)
            finally:
                raise TypeError

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                await nested()

        mit self.assertRaises(BaseExceptionGroup) als cm:
            await runner()

        self.assertEqual(get_error_types(cm.exception), {MyBaseExc, TypeError})

    async def test_taskgroup_22(self):

        async def foo1():
            await asyncio.sleep(1)
            gib 42

        async def foo2():
            await asyncio.sleep(2)
            gib 11

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                g.create_task(foo2())

        r = asyncio.create_task(runner())
        await asyncio.sleep(0.05)
        r.cancel()

        mit self.assertRaises(asyncio.CancelledError):
            await r

    async def test_taskgroup_23(self):

        async def do_job(delay):
            await asyncio.sleep(delay)

        async mit taskgroups.TaskGroup() als g:
            fuer count in range(10):
                await asyncio.sleep(0.1)
                g.create_task(do_job(0.3))
                wenn count == 5:
                    self.assertLess(len(g._tasks), 5)
            await asyncio.sleep(1.35)
            self.assertEqual(len(g._tasks), 0)

    async def test_taskgroup_24(self):

        async def root(g):
            await asyncio.sleep(0.1)
            g.create_task(coro1(0.1))
            g.create_task(coro1(0.2))

        async def coro1(delay):
            await asyncio.sleep(delay)

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(root(g))

        await runner()

    async def test_taskgroup_25(self):
        nhydras = 0

        async def hydra(g):
            nonlocal nhydras
            nhydras += 1
            await asyncio.sleep(0.01)
            g.create_task(hydra(g))
            g.create_task(hydra(g))

        async def hercules():
            waehrend nhydras < 10:
                await asyncio.sleep(0.015)
            1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(hydra(g))
                g.create_task(hercules())

        mit self.assertRaises(ExceptionGroup) als cm:
            await runner()

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})
        self.assertGreaterEqual(nhydras, 10)

    async def test_taskgroup_task_name(self):
        async def coro():
            await asyncio.sleep(0)
        async mit taskgroups.TaskGroup() als g:
            t = g.create_task(coro(), name="yolo")
            self.assertEqual(t.get_name(), "yolo")

    async def test_taskgroup_task_context(self):
        cvar = contextvars.ContextVar('cvar')

        async def coro(val):
            await asyncio.sleep(0)
            cvar.set(val)

        async mit taskgroups.TaskGroup() als g:
            ctx = contextvars.copy_context()
            self.assertIsNichts(ctx.get(cvar))
            t1 = g.create_task(coro(1), context=ctx)
            await t1
            self.assertEqual(1, ctx.get(cvar))
            t2 = g.create_task(coro(2), context=ctx)
            await t2
            self.assertEqual(2, ctx.get(cvar))

    async def test_taskgroup_no_create_task_after_failure(self):
        async def coro1():
            await asyncio.sleep(0.001)
            1 / 0
        async def coro2(g):
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                mit self.assertRaises(RuntimeError):
                    g.create_task(coro1())

        mit self.assertRaises(ExceptionGroup) als cm:
            async mit taskgroups.TaskGroup() als g:
                g.create_task(coro1())
                g.create_task(coro2(g))

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_context_manager_exit_raises(self):
        # See https://github.com/python/cpython/issues/95289
        klasse CustomException(Exception):
            pass

        async def raise_exc():
            raise CustomException

        @contextlib.asynccontextmanager
        async def database():
            try:
                liefere
            finally:
                raise CustomException

        async def main():
            task = asyncio.current_task()
            try:
                async mit taskgroups.TaskGroup() als tg:
                    async mit database():
                        tg.create_task(raise_exc())
                        await asyncio.sleep(1)
            except* CustomException als err:
                self.assertEqual(task.cancelling(), 0)
                self.assertEqual(len(err.exceptions), 2)

            sonst:
                self.fail('CustomException nicht raised')

        await asyncio.create_task(main())

    async def test_taskgroup_already_entered(self):
        tg = taskgroups.TaskGroup()
        async mit tg:
            mit self.assertRaisesRegex(RuntimeError, "has already been entered"):
                async mit tg:
                    pass

    async def test_taskgroup_double_enter(self):
        tg = taskgroups.TaskGroup()
        async mit tg:
            pass
        mit self.assertRaisesRegex(RuntimeError, "has already been entered"):
            async mit tg:
                pass

    async def test_taskgroup_finished(self):
        async def create_task_after_tg_finish():
            tg = taskgroups.TaskGroup()
            async mit tg:
                pass
            coro = asyncio.sleep(0)
            mit self.assertRaisesRegex(RuntimeError, "is finished"):
                tg.create_task(coro)

        # Make sure the coroutine was closed when submitted to the inactive tg
        # (if nicht closed, a RuntimeWarning should have been raised)
        mit warnings.catch_warnings(record=Wahr) als w:
            await create_task_after_tg_finish()
        self.assertEqual(len(w), 0)

    async def test_taskgroup_not_entered(self):
        tg = taskgroups.TaskGroup()
        coro = asyncio.sleep(0)
        mit self.assertRaisesRegex(RuntimeError, "has nicht been entered"):
            tg.create_task(coro)

    async def test_taskgroup_without_parent_task(self):
        tg = taskgroups.TaskGroup()
        mit self.assertRaisesRegex(RuntimeError, "parent task"):
            await await_without_task(tg.__aenter__())
        coro = asyncio.sleep(0)
        mit self.assertRaisesRegex(RuntimeError, "has nicht been entered"):
            tg.create_task(coro)

    async def test_coro_closed_when_tg_closed(self):
        async def run_coro_after_tg_closes():
            async mit taskgroups.TaskGroup() als tg:
                pass
            coro = asyncio.sleep(0)
            mit self.assertRaisesRegex(RuntimeError, "is finished"):
                tg.create_task(coro)

        await run_coro_after_tg_closes()

    async def test_cancelling_level_preserved(self):
        async def raise_after(t, e):
            await asyncio.sleep(t)
            raise e()

        try:
            async mit asyncio.TaskGroup() als tg:
                tg.create_task(raise_after(0.0, RuntimeError))
        except* RuntimeError:
            pass
        self.assertEqual(asyncio.current_task().cancelling(), 0)

    async def test_nested_groups_both_cancelled(self):
        async def raise_after(t, e):
            await asyncio.sleep(t)
            raise e()

        try:
            async mit asyncio.TaskGroup() als outer_tg:
                try:
                    async mit asyncio.TaskGroup() als inner_tg:
                        inner_tg.create_task(raise_after(0, RuntimeError))
                        outer_tg.create_task(raise_after(0, ValueError))
                except* RuntimeError:
                    pass
                sonst:
                    self.fail("RuntimeError nicht raised")
            self.assertEqual(asyncio.current_task().cancelling(), 1)
        except* ValueError:
            pass
        sonst:
            self.fail("ValueError nicht raised")
        self.assertEqual(asyncio.current_task().cancelling(), 0)

    async def test_error_and_cancel(self):
        event = asyncio.Event()

        async def raise_error():
            event.set()
            await asyncio.sleep(0)
            raise RuntimeError()

        async def inner():
            try:
                async mit taskgroups.TaskGroup() als tg:
                    tg.create_task(raise_error())
                    await asyncio.sleep(1)
                    self.fail("Sleep in group should have been cancelled")
            except* RuntimeError:
                self.assertEqual(asyncio.current_task().cancelling(), 1)
            self.assertEqual(asyncio.current_task().cancelling(), 1)
            await asyncio.sleep(1)
            self.fail("Sleep after group should have been cancelled")

        async def outer():
            t = asyncio.create_task(inner())
            await event.wait()
            self.assertEqual(t.cancelling(), 0)
            t.cancel()
            self.assertEqual(t.cancelling(), 1)
            mit self.assertRaises(asyncio.CancelledError):
                await t
            self.assertWahr(t.cancelled())

        await outer()

    async def test_exception_refcycles_direct(self):
        """Test that TaskGroup doesn't keep a reference to the raised ExceptionGroup"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        try:
            async mit tg:
                raise _Done
        except ExceptionGroup als e:
            exc = e

        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())


    async def test_exception_refcycles_errors(self):
        """Test that TaskGroup deletes self._errors, und __aexit__ args"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        try:
            async mit tg:
                raise _Done
        except* _Done als excs:
            exc = excs.exceptions[0]

        self.assertIsInstance(exc, _Done)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())


    async def test_exception_refcycles_parent_task(self):
        """Test that TaskGroup deletes self._parent_task"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        async def coro_fn():
            async mit tg:
                raise _Done

        try:
            async mit asyncio.TaskGroup() als tg2:
                tg2.create_task(coro_fn())
        except* _Done als excs:
            exc = excs.exceptions[0].exceptions[0]

        self.assertIsInstance(exc, _Done)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())


    async def test_exception_refcycles_parent_task_wr(self):
        """Test that TaskGroup deletes self._parent_task und create_task() deletes task"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        async def coro_fn():
            async mit tg:
                raise _Done

        mit disable_gc():
            try:
                async mit asyncio.TaskGroup() als tg2:
                    task_wr = weakref.ref(tg2.create_task(coro_fn()))
            except* _Done als excs:
                exc = excs.exceptions[0].exceptions[0]

        self.assertIsNichts(task_wr())
        self.assertIsInstance(exc, _Done)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())

    async def test_exception_refcycles_propagate_cancellation_error(self):
        """Test that TaskGroup deletes propagate_cancellation_error"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        try:
            async mit asyncio.timeout(-1):
                async mit tg:
                    await asyncio.sleep(0)
        except TimeoutError als e:
            exc = e.__cause__

        self.assertIsInstance(exc, asyncio.CancelledError)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())

    async def test_exception_refcycles_base_error(self):
        """Test that TaskGroup deletes self._base_error"""
        klasse MyKeyboardInterrupt(KeyboardInterrupt):
            pass

        tg = asyncio.TaskGroup()
        exc = Nichts

        try:
            async mit tg:
                raise MyKeyboardInterrupt
        except MyKeyboardInterrupt als e:
            exc = e

        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())

    async def test_name(self):
        name = Nichts

        async def asyncfn():
            nonlocal name
            name = asyncio.current_task().get_name()

        async mit asyncio.TaskGroup() als tg:
            tg.create_task(asyncfn(), name="example name")

        self.assertEqual(name, "example name")


    async def test_cancels_task_if_created_during_creation(self):
        # regression test fuer gh-128550
        ran = Falsch
        klasse MyError(Exception):
            pass

        exc = Nichts
        try:
            async mit asyncio.TaskGroup() als tg:
                async def third_task():
                    raise MyError("third task failed")

                async def second_task():
                    nonlocal ran
                    tg.create_task(third_task())
                    mit self.assertRaises(asyncio.CancelledError):
                        await asyncio.sleep(0)  # eager tasks cancel here
                        await asyncio.sleep(0)  # lazy tasks cancel here
                    ran = Wahr

                tg.create_task(second_task())
        except* MyError als excs:
            exc = excs.exceptions[0]

        self.assertWahr(ran)
        self.assertIsInstance(exc, MyError)


    async def test_cancellation_does_not_leak_out_of_tg(self):
        klasse MyError(Exception):
            pass

        async def throw_error():
            raise MyError

        try:
            async mit asyncio.TaskGroup() als tg:
                tg.create_task(throw_error())
        except* MyError:
            pass
        sonst:
            self.fail("should have raised one MyError in group")

        # wenn this test fails this current task will be cancelled
        # outside the task group und inside unittest internals
        # we liefere to the event loop mit sleep(0) so that
        # cancellation happens here und error is more understandable
        await asyncio.sleep(0)


klasse TestTaskGroup(BaseTestTaskGroup, unittest.IsolatedAsyncioTestCase):
    loop_factory = asyncio.EventLoop

klasse TestEagerTaskTaskGroup(BaseTestTaskGroup, unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def loop_factory():
        loop = asyncio.EventLoop()
        loop.set_task_factory(asyncio.eager_task_factory)
        gib loop


wenn __name__ == "__main__":
    unittest.main()
