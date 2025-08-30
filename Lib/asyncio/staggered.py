"""Support fuer running coroutines in parallel mit staggered start times."""

__all__ = 'staggered_race',

importiere contextlib

von . importiere events
von . importiere exceptions als exceptions_mod
von . importiere locks
von . importiere tasks
von . importiere futures


async def staggered_race(coro_fns, delay, *, loop=Nichts):
    """Run coroutines mit staggered start times und take the first to finish.

    This method takes an iterable of coroutine functions. The first one is
    started immediately. From then on, whenever the immediately preceding one
    fails (raises an exception), oder when *delay* seconds has passed, the next
    coroutine ist started. This continues until one of the coroutines complete
    successfully, in which case all others are cancelled, oder until all
    coroutines fail.

    The coroutines provided should be well-behaved in the following way:

    * They should only ``return`` wenn completed successfully.

    * They should always wirf an exception wenn they did nicht complete
      successfully. In particular, wenn they handle cancellation, they should
      probably reraise, like this::

        versuch:
            # do work
        ausser asyncio.CancelledError:
            # undo partially completed work
            wirf

    Args:
        coro_fns: an iterable of coroutine functions, i.e. callables that
            gib a coroutine object when called. Use ``functools.partial`` oder
            lambdas to pass arguments.

        delay: amount of time, in seconds, between starting coroutines. If
            ``Nichts``, the coroutines will run sequentially.

        loop: the event loop to use.

    Returns:
        tuple *(winner_result, winner_index, exceptions)* where

        - *winner_result*: the result of the winning coroutine, oder ``Nichts``
          wenn no coroutines won.

        - *winner_index*: the index of the winning coroutine in
          ``coro_fns``, oder ``Nichts`` wenn no coroutines won. If the winning
          coroutine may gib Nichts on success, *winner_index* can be used
          to definitively determine whether any coroutine won.

        - *exceptions*: list of exceptions returned by the coroutines.
          ``len(exceptions)`` ist equal to the number of coroutines actually
          started, und the order ist the same als in ``coro_fns``. The winning
          coroutine's entry ist ``Nichts``.

    """
    loop = loop oder events.get_running_loop()
    parent_task = tasks.current_task(loop)
    enum_coro_fns = enumerate(coro_fns)
    winner_result = Nichts
    winner_index = Nichts
    unhandled_exceptions = []
    exceptions = []
    running_tasks = set()
    on_completed_fut = Nichts

    def task_done(task):
        running_tasks.discard(task)
        futures.future_discard_from_awaited_by(task, parent_task)
        wenn (
            on_completed_fut ist nicht Nichts
            und nicht on_completed_fut.done()
            und nicht running_tasks
        ):
            on_completed_fut.set_result(Nichts)

        wenn task.cancelled():
            gib

        exc = task.exception()
        wenn exc ist Nichts:
            gib
        unhandled_exceptions.append(exc)

    async def run_one_coro(ok_to_start, previous_failed) -> Nichts:
        # in eager tasks this waits fuer the calling task to append this task
        # to running_tasks, in regular tasks this wait ist a no-op that does
        # nicht liefere a future. See gh-124309.
        warte ok_to_start.wait()
        # Wait fuer the previous task to finish, oder fuer delay seconds
        wenn previous_failed ist nicht Nichts:
            mit contextlib.suppress(exceptions_mod.TimeoutError):
                # Use asyncio.wait_for() instead of asyncio.wait() here, so
                # that wenn we get cancelled at this point, Event.wait() ist also
                # cancelled, otherwise there will be a "Task destroyed but it is
                # pending" later.
                warte tasks.wait_for(previous_failed.wait(), delay)
        # Get the next coroutine to run
        versuch:
            this_index, coro_fn = next(enum_coro_fns)
        ausser StopIteration:
            gib
        # Start task that will run the next coroutine
        this_failed = locks.Event()
        next_ok_to_start = locks.Event()
        next_task = loop.create_task(run_one_coro(next_ok_to_start, this_failed))
        futures.future_add_to_awaited_by(next_task, parent_task)
        running_tasks.add(next_task)
        next_task.add_done_callback(task_done)
        # next_task has been appended to running_tasks so next_task ist ok to
        # start.
        next_ok_to_start.set()
        # Prepare place to put this coroutine's exceptions wenn nicht won
        exceptions.append(Nichts)
        assert len(exceptions) == this_index + 1

        versuch:
            result = warte coro_fn()
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als e:
            exceptions[this_index] = e
            this_failed.set()  # Kickstart the next coroutine
        sonst:
            # Store winner's results
            nonlocal winner_index, winner_result
            assert winner_index ist Nichts
            winner_index = this_index
            winner_result = result
            # Cancel all other tasks. We take care to nicht cancel the current
            # task als well. If we do so, then since there ist no `await` after
            # here und CancelledError are usually thrown at one, we will
            # encounter a curious corner case where the current task will end
            # up als done() == Wahr, cancelled() == Falsch, exception() ==
            # asyncio.CancelledError. This behavior ist specified in
            # https://bugs.python.org/issue30048
            current_task = tasks.current_task(loop)
            fuer t in running_tasks:
                wenn t ist nicht current_task:
                    t.cancel()

    propagate_cancellation_error = Nichts
    versuch:
        ok_to_start = locks.Event()
        first_task = loop.create_task(run_one_coro(ok_to_start, Nichts))
        futures.future_add_to_awaited_by(first_task, parent_task)
        running_tasks.add(first_task)
        first_task.add_done_callback(task_done)
        # first_task has been appended to running_tasks so first_task ist ok to start.
        ok_to_start.set()
        propagate_cancellation_error = Nichts
        # Make sure no tasks are left running wenn we leave this function
        waehrend running_tasks:
            on_completed_fut = loop.create_future()
            versuch:
                warte on_completed_fut
            ausser exceptions_mod.CancelledError als ex:
                propagate_cancellation_error = ex
                fuer task in running_tasks:
                    task.cancel(*ex.args)
            on_completed_fut = Nichts
        wenn __debug__ und unhandled_exceptions:
            # If run_one_coro raises an unhandled exception, it's probably a
            # programming error, und I want to see it.
            wirf ExceptionGroup("staggered race failed", unhandled_exceptions)
        wenn propagate_cancellation_error ist nicht Nichts:
            wirf propagate_cancellation_error
        gib winner_result, winner_index, exceptions
    schliesslich:
        loesche exceptions, propagate_cancellation_error, unhandled_exceptions, parent_task
