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
    versuch:
        liefere
    schliesslich:
        set_gc_state(enabled=was_enabled)


klasse BaseTestTaskGroup:

    async def test_taskgroup_01(self):

        async def foo1():
            warte asyncio.sleep(0.1)
            gib 42

        async def foo2():
            warte asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            t2 = g.create_task(foo2())

        self.assertEqual(t1.result(), 42)
        self.assertEqual(t2.result(), 11)

    async def test_taskgroup_02(self):

        async def foo1():
            warte asyncio.sleep(0.1)
            gib 42

        async def foo2():
            warte asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            warte asyncio.sleep(0.15)
            t2 = g.create_task(foo2())

        self.assertEqual(t1.result(), 42)
        self.assertEqual(t2.result(), 11)

    async def test_taskgroup_03(self):

        async def foo1():
            warte asyncio.sleep(1)
            gib 42

        async def foo2():
            warte asyncio.sleep(0.2)
            gib 11

        async mit taskgroups.TaskGroup() als g:
            t1 = g.create_task(foo1())
            warte asyncio.sleep(0.15)
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
            warte asyncio.sleep(0.1)
            1 / 0

        async def foo2():
            nichtlokal NUM, t2_cancel
            versuch:
                warte asyncio.sleep(1)
            ausser asyncio.CancelledError:
                t2_cancel = Wahr
                wirf
            NUM += 1

        async def runner():
            nichtlokal NUM, t2

            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                t2 = g.create_task(foo2())

            NUM += 10

        mit self.assertRaises(ExceptionGroup) als cm:
            warte asyncio.create_task(runner())

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
            warte asyncio.sleep(0.1)
            1 / 0

        async def foo2():
            nichtlokal NUM, t2_cancel
            versuch:
                warte asyncio.sleep(5)
            ausser asyncio.CancelledError:
                t2_cancel = Wahr
                wirf
            NUM += 1

        async def runner():
            nichtlokal NUM, runner_cancel

            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                g.create_task(foo1())
                g.create_task(foo1())
                g.create_task(foo2())
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    runner_cancel = Wahr
                    wirf

            NUM += 10

        # The 3 foo1 sub tasks can be racy when the host ist busy - wenn the
        # cancellation happens in the middle, we'll see partial sub errors here
        mit self.assertRaises(ExceptionGroup) als cm:
            warte asyncio.create_task(runner())

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})
        self.assertEqual(NUM, 0)
        self.assertWahr(t2_cancel)
        self.assertWahr(runner_cancel)

    async def test_cancellation(self):

        NUM = 0

        async def foo():
            nichtlokal NUM
            versuch:
                warte asyncio.sleep(5)
            ausser asyncio.CancelledError:
                NUM += 1
                wirf

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError) als cm:
            warte r

        self.assertEqual(NUM, 5)

    async def test_taskgroup_07(self):

        NUM = 0

        async def foo():
            nichtlokal NUM
            versuch:
                warte asyncio.sleep(5)
            ausser asyncio.CancelledError:
                NUM += 1
                wirf

        async def runner():
            nichtlokal NUM
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    NUM += 10
                    wirf

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            warte r

        self.assertEqual(NUM, 15)

    async def test_taskgroup_08(self):

        async def foo():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                fuer _ in range(5):
                    g.create_task(foo())

                warte asyncio.sleep(10)

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_09(self):

        t1 = t2 = Nichts

        async def foo1():
            warte asyncio.sleep(1)
            gib 42

        async def foo2():
            warte asyncio.sleep(2)
            gib 11

        async def runner():
            nichtlokal t1, t2
            async mit taskgroups.TaskGroup() als g:
                t1 = g.create_task(foo1())
                t2 = g.create_task(foo2())
                warte asyncio.sleep(0.1)
                1 / 0

        versuch:
            warte runner()
        ausser ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {ZeroDivisionError})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertWahr(t1.cancelled())
        self.assertWahr(t2.cancelled())

    async def test_taskgroup_10(self):

        t1 = t2 = Nichts

        async def foo1():
            warte asyncio.sleep(1)
            gib 42

        async def foo2():
            warte asyncio.sleep(2)
            gib 11

        async def runner():
            nichtlokal t1, t2
            async mit taskgroups.TaskGroup() als g:
                t1 = g.create_task(foo1())
                t2 = g.create_task(foo2())
                1 / 0

        versuch:
            warte runner()
        ausser ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {ZeroDivisionError})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertWahr(t1.cancelled())
        self.assertWahr(t2.cancelled())

    async def test_taskgroup_11(self):

        async def foo():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup():
                async mit taskgroups.TaskGroup() als g2:
                    fuer _ in range(5):
                        g2.create_task(foo())

                    warte asyncio.sleep(10)

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ZeroDivisionError})

    async def test_taskgroup_12(self):

        async def foo():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(asyncio.sleep(10))

                async mit taskgroups.TaskGroup() als g2:
                    fuer _ in range(5):
                        g2.create_task(foo())

                    warte asyncio.sleep(10)

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ZeroDivisionError})

    async def test_taskgroup_13(self):

        async def crash_after(t):
            warte asyncio.sleep(t)
            wirf ValueError(t)

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_after(0.1))

                async mit taskgroups.TaskGroup() als g2:
                    g2.create_task(crash_after(10))

        r = asyncio.create_task(runner())
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r

        self.assertEqual(get_error_types(cm.exception), {ValueError})

    async def test_taskgroup_14(self):

        async def crash_after(t):
            warte asyncio.sleep(t)
            wirf ValueError(t)

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_after(10))

                async mit taskgroups.TaskGroup() als g2:
                    g2.create_task(crash_after(0.1))

        r = asyncio.create_task(runner())
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r

        self.assertEqual(get_error_types(cm.exception), {ExceptionGroup})
        self.assertEqual(get_error_types(cm.exception.exceptions[0]), {ValueError})

    async def test_taskgroup_15(self):

        async def crash_soon():
            warte asyncio.sleep(0.3)
            1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_soon())
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    warte asyncio.sleep(0.5)
                    wirf

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_16(self):

        async def crash_soon():
            warte asyncio.sleep(0.3)
            1 / 0

        async def nested_runner():
            async mit taskgroups.TaskGroup() als g1:
                g1.create_task(crash_soon())
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    warte asyncio.sleep(0.5)
                    wirf

        async def runner():
            t = asyncio.create_task(nested_runner())
            warte t

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(ExceptionGroup) als cm:
            warte r
        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})

    async def test_taskgroup_17(self):
        NUM = 0

        async def runner():
            nichtlokal NUM
            async mit taskgroups.TaskGroup():
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    NUM += 10
                    wirf

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()
        mit self.assertRaises(asyncio.CancelledError):
            warte r

        self.assertEqual(NUM, 10)

    async def test_taskgroup_18(self):
        NUM = 0

        async def runner():
            nichtlokal NUM
            async mit taskgroups.TaskGroup():
                versuch:
                    warte asyncio.sleep(10)
                ausser asyncio.CancelledError:
                    NUM += 10
                    # This isn't a good idea, but we have to support
                    # this weird case.
                    wirf MyExc

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.1)

        self.assertFalsch(r.done())
        r.cancel()

        versuch:
            warte r
        ausser ExceptionGroup als t:
            self.assertEqual(get_error_types(t),{MyExc})
        sonst:
            self.fail('ExceptionGroup was nicht raised')

        self.assertEqual(NUM, 10)

    async def test_taskgroup_19(self):
        async def crash_soon():
            warte asyncio.sleep(0.1)
            1 / 0

        async def nested():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                wirf MyExc

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                warte nested()

        r = asyncio.create_task(runner())
        versuch:
            warte r
        ausser ExceptionGroup als t:
            self.assertEqual(get_error_types(t), {MyExc, ZeroDivisionError})
        sonst:
            self.fail('TasgGroupError was nicht raised')

    async def test_taskgroup_20(self):
        async def crash_soon():
            warte asyncio.sleep(0.1)
            1 / 0

        async def nested():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                wirf KeyboardInterrupt

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                warte nested()

        mit self.assertRaises(KeyboardInterrupt):
            warte runner()

    async def test_taskgroup_20a(self):
        async def crash_soon():
            warte asyncio.sleep(0.1)
            1 / 0

        async def nested():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                wirf MyBaseExc

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                warte nested()

        mit self.assertRaises(BaseExceptionGroup) als cm:
            warte runner()

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
            warte asyncio.sleep(0.1)
            wirf KeyboardInterrupt

        async def nested():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                wirf TypeError

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                warte nested()

        mit self.assertRaises(KeyboardInterrupt):
            warte runner()

    async def test_taskgroup_21a(self):

        async def crash_soon():
            warte asyncio.sleep(0.1)
            wirf MyBaseExc

        async def nested():
            versuch:
                warte asyncio.sleep(10)
            schliesslich:
                wirf TypeError

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(crash_soon())
                warte nested()

        mit self.assertRaises(BaseExceptionGroup) als cm:
            warte runner()

        self.assertEqual(get_error_types(cm.exception), {MyBaseExc, TypeError})

    async def test_taskgroup_22(self):

        async def foo1():
            warte asyncio.sleep(1)
            gib 42

        async def foo2():
            warte asyncio.sleep(2)
            gib 11

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(foo1())
                g.create_task(foo2())

        r = asyncio.create_task(runner())
        warte asyncio.sleep(0.05)
        r.cancel()

        mit self.assertRaises(asyncio.CancelledError):
            warte r

    async def test_taskgroup_23(self):

        async def do_job(delay):
            warte asyncio.sleep(delay)

        async mit taskgroups.TaskGroup() als g:
            fuer count in range(10):
                warte asyncio.sleep(0.1)
                g.create_task(do_job(0.3))
                wenn count == 5:
                    self.assertLess(len(g._tasks), 5)
            warte asyncio.sleep(1.35)
            self.assertEqual(len(g._tasks), 0)

    async def test_taskgroup_24(self):

        async def root(g):
            warte asyncio.sleep(0.1)
            g.create_task(coro1(0.1))
            g.create_task(coro1(0.2))

        async def coro1(delay):
            warte asyncio.sleep(delay)

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(root(g))

        warte runner()

    async def test_taskgroup_25(self):
        nhydras = 0

        async def hydra(g):
            nichtlokal nhydras
            nhydras += 1
            warte asyncio.sleep(0.01)
            g.create_task(hydra(g))
            g.create_task(hydra(g))

        async def hercules():
            waehrend nhydras < 10:
                warte asyncio.sleep(0.015)
            1 / 0

        async def runner():
            async mit taskgroups.TaskGroup() als g:
                g.create_task(hydra(g))
                g.create_task(hercules())

        mit self.assertRaises(ExceptionGroup) als cm:
            warte runner()

        self.assertEqual(get_error_types(cm.exception), {ZeroDivisionError})
        self.assertGreaterEqual(nhydras, 10)

    async def test_taskgroup_task_name(self):
        async def coro():
            warte asyncio.sleep(0)
        async mit taskgroups.TaskGroup() als g:
            t = g.create_task(coro(), name="yolo")
            self.assertEqual(t.get_name(), "yolo")

    async def test_taskgroup_task_context(self):
        cvar = contextvars.ContextVar('cvar')

        async def coro(val):
            warte asyncio.sleep(0)
            cvar.set(val)

        async mit taskgroups.TaskGroup() als g:
            ctx = contextvars.copy_context()
            self.assertIsNichts(ctx.get(cvar))
            t1 = g.create_task(coro(1), context=ctx)
            warte t1
            self.assertEqual(1, ctx.get(cvar))
            t2 = g.create_task(coro(2), context=ctx)
            warte t2
            self.assertEqual(2, ctx.get(cvar))

    async def test_taskgroup_no_create_task_after_failure(self):
        async def coro1():
            warte asyncio.sleep(0.001)
            1 / 0
        async def coro2(g):
            versuch:
                warte asyncio.sleep(1)
            ausser asyncio.CancelledError:
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
            wirf CustomException

        @contextlib.asynccontextmanager
        async def database():
            versuch:
                liefere
            schliesslich:
                wirf CustomException

        async def main():
            task = asyncio.current_task()
            versuch:
                async mit taskgroups.TaskGroup() als tg:
                    async mit database():
                        tg.create_task(raise_exc())
                        warte asyncio.sleep(1)
            except* CustomException als err:
                self.assertEqual(task.cancelling(), 0)
                self.assertEqual(len(err.exceptions), 2)

            sonst:
                self.fail('CustomException nicht raised')

        warte asyncio.create_task(main())

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
            warte create_task_after_tg_finish()
        self.assertEqual(len(w), 0)

    async def test_taskgroup_not_entered(self):
        tg = taskgroups.TaskGroup()
        coro = asyncio.sleep(0)
        mit self.assertRaisesRegex(RuntimeError, "has nicht been entered"):
            tg.create_task(coro)

    async def test_taskgroup_without_parent_task(self):
        tg = taskgroups.TaskGroup()
        mit self.assertRaisesRegex(RuntimeError, "parent task"):
            warte await_without_task(tg.__aenter__())
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

        warte run_coro_after_tg_closes()

    async def test_cancelling_level_preserved(self):
        async def raise_after(t, e):
            warte asyncio.sleep(t)
            wirf e()

        versuch:
            async mit asyncio.TaskGroup() als tg:
                tg.create_task(raise_after(0.0, RuntimeError))
        except* RuntimeError:
            pass
        self.assertEqual(asyncio.current_task().cancelling(), 0)

    async def test_nested_groups_both_cancelled(self):
        async def raise_after(t, e):
            warte asyncio.sleep(t)
            wirf e()

        versuch:
            async mit asyncio.TaskGroup() als outer_tg:
                versuch:
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
            warte asyncio.sleep(0)
            wirf RuntimeError()

        async def inner():
            versuch:
                async mit taskgroups.TaskGroup() als tg:
                    tg.create_task(raise_error())
                    warte asyncio.sleep(1)
                    self.fail("Sleep in group should have been cancelled")
            except* RuntimeError:
                self.assertEqual(asyncio.current_task().cancelling(), 1)
            self.assertEqual(asyncio.current_task().cancelling(), 1)
            warte asyncio.sleep(1)
            self.fail("Sleep after group should have been cancelled")

        async def outer():
            t = asyncio.create_task(inner())
            warte event.wait()
            self.assertEqual(t.cancelling(), 0)
            t.cancel()
            self.assertEqual(t.cancelling(), 1)
            mit self.assertRaises(asyncio.CancelledError):
                warte t
            self.assertWahr(t.cancelled())

        warte outer()

    async def test_exception_refcycles_direct(self):
        """Test that TaskGroup doesn't keep a reference to the raised ExceptionGroup"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        versuch:
            async mit tg:
                wirf _Done
        ausser ExceptionGroup als e:
            exc = e

        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())


    async def test_exception_refcycles_errors(self):
        """Test that TaskGroup deletes self._errors, und __aexit__ args"""
        tg = asyncio.TaskGroup()
        exc = Nichts

        klasse _Done(Exception):
            pass

        versuch:
            async mit tg:
                wirf _Done
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
                wirf _Done

        versuch:
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
                wirf _Done

        mit disable_gc():
            versuch:
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

        versuch:
            async mit asyncio.timeout(-1):
                async mit tg:
                    warte asyncio.sleep(0)
        ausser TimeoutError als e:
            exc = e.__cause__

        self.assertIsInstance(exc, asyncio.CancelledError)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())

    async def test_exception_refcycles_base_error(self):
        """Test that TaskGroup deletes self._base_error"""
        klasse MyKeyboardInterrupt(KeyboardInterrupt):
            pass

        tg = asyncio.TaskGroup()
        exc = Nichts

        versuch:
            async mit tg:
                wirf MyKeyboardInterrupt
        ausser MyKeyboardInterrupt als e:
            exc = e

        self.assertIsNotNichts(exc)
        self.assertListEqual(gc.get_referrers(exc), no_other_refs())

    async def test_name(self):
        name = Nichts

        async def asyncfn():
            nichtlokal name
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
        versuch:
            async mit asyncio.TaskGroup() als tg:
                async def third_task():
                    wirf MyError("third task failed")

                async def second_task():
                    nichtlokal ran
                    tg.create_task(third_task())
                    mit self.assertRaises(asyncio.CancelledError):
                        warte asyncio.sleep(0)  # eager tasks cancel here
                        warte asyncio.sleep(0)  # lazy tasks cancel here
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
            wirf MyError

        versuch:
            async mit asyncio.TaskGroup() als tg:
                tg.create_task(throw_error())
        except* MyError:
            pass
        sonst:
            self.fail("should have raised one MyError in group")

        # wenn this test fails this current task will be cancelled
        # outside the task group und inside unittest internals
        # we liefere to the event loop mit sleep(0) so that
        # cancellation happens here und error ist more understandable
        warte asyncio.sleep(0)


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
