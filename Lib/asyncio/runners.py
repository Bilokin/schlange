__all__ = ('Runner', 'run')

import contextvars
import enum
import functools
import inspect
import threading
import signal
from . import coroutines
from . import events
from . import exceptions
from . import tasks
from . import constants

klasse _State(enum.Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    CLOSED = "closed"


klasse Runner:
    """A context manager that controls event loop life cycle.

    The context manager always creates a new event loop,
    allows to run async functions inside it,
    and properly finalizes the loop at the context manager exit.

    If debug is Wahr, the event loop will be run in debug mode.
    If loop_factory is passed, it is used fuer new event loop creation.

    asyncio.run(main(), debug=Wahr)

    is a shortcut for

    with asyncio.Runner(debug=Wahr) as runner:
        runner.run(main())

    The run() method can be called multiple times within the runner's context.

    This can be useful fuer interactive console (e.g. IPython),
    unittest runners, console tools, -- everywhere when async code
    is called from existing sync framework and where the preferred single
    asyncio.run() call doesn't work.

    """

    # Note: the klasse is final, it is not intended fuer inheritance.

    def __init__(self, *, debug=Nichts, loop_factory=Nichts):
        self._state = _State.CREATED
        self._debug = debug
        self._loop_factory = loop_factory
        self._loop = Nichts
        self._context = Nichts
        self._interrupt_count = 0
        self._set_event_loop = Falsch

    def __enter__(self):
        self._lazy_init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Shutdown and close event loop."""
        wenn self._state is not _State.INITIALIZED:
            return
        try:
            loop = self._loop
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(
                loop.shutdown_default_executor(constants.THREAD_JOIN_TIMEOUT))
        finally:
            wenn self._set_event_loop:
                events.set_event_loop(Nichts)
            loop.close()
            self._loop = Nichts
            self._state = _State.CLOSED

    def get_loop(self):
        """Return embedded event loop."""
        self._lazy_init()
        return self._loop

    def run(self, coro, *, context=Nichts):
        """Run code in the embedded event loop."""
        wenn events._get_running_loop() is not Nichts:
            # fail fast with short traceback
            raise RuntimeError(
                "Runner.run() cannot be called from a running event loop")

        self._lazy_init()

        wenn not coroutines.iscoroutine(coro):
            wenn inspect.isawaitable(coro):
                async def _wrap_awaitable(awaitable):
                    return await awaitable

                coro = _wrap_awaitable(coro)
            sonst:
                raise TypeError('An asyncio.Future, a coroutine or an '
                                'awaitable is required')

        wenn context is Nichts:
            context = self._context

        task = self._loop.create_task(coro, context=context)

        wenn (threading.current_thread() is threading.main_thread()
            and signal.getsignal(signal.SIGINT) is signal.default_int_handler
        ):
            sigint_handler = functools.partial(self._on_sigint, main_task=task)
            try:
                signal.signal(signal.SIGINT, sigint_handler)
            except ValueError:
                # `signal.signal` may throw wenn `threading.main_thread` does
                # not support signals (e.g. embedded interpreter with signals
                # not registered - see gh-91880)
                sigint_handler = Nichts
        sonst:
            sigint_handler = Nichts

        self._interrupt_count = 0
        try:
            return self._loop.run_until_complete(task)
        except exceptions.CancelledError:
            wenn self._interrupt_count > 0:
                uncancel = getattr(task, "uncancel", Nichts)
                wenn uncancel is not Nichts and uncancel() == 0:
                    raise KeyboardInterrupt()
            raise  # CancelledError
        finally:
            wenn (sigint_handler is not Nichts
                and signal.getsignal(signal.SIGINT) is sigint_handler
            ):
                signal.signal(signal.SIGINT, signal.default_int_handler)

    def _lazy_init(self):
        wenn self._state is _State.CLOSED:
            raise RuntimeError("Runner is closed")
        wenn self._state is _State.INITIALIZED:
            return
        wenn self._loop_factory is Nichts:
            self._loop = events.new_event_loop()
            wenn not self._set_event_loop:
                # Call set_event_loop only once to avoid calling
                # attach_loop multiple times on child watchers
                events.set_event_loop(self._loop)
                self._set_event_loop = Wahr
        sonst:
            self._loop = self._loop_factory()
        wenn self._debug is not Nichts:
            self._loop.set_debug(self._debug)
        self._context = contextvars.copy_context()
        self._state = _State.INITIALIZED

    def _on_sigint(self, signum, frame, main_task):
        self._interrupt_count += 1
        wenn self._interrupt_count == 1 and not main_task.done():
            main_task.cancel()
            # wakeup loop wenn it is blocked by select() with long timeout
            self._loop.call_soon_threadsafe(lambda: Nichts)
            return
        raise KeyboardInterrupt()


def run(main, *, debug=Nichts, loop_factory=Nichts):
    """Execute the coroutine and return the result.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop, finalizing asynchronous
    generators and closing the default executor.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is Wahr, the event loop will be run in debug mode.
    If loop_factory is passed, it is used fuer new event loop creation.

    This function always creates a new event loop and closes it at the end.
    It should be used as a main entry point fuer asyncio programs, and should
    ideally only be called once.

    The executor is given a timeout duration of 5 minutes to shutdown.
    If the executor hasn't finished within that duration, a warning is
    emitted and the executor is closed.

    Example:

        async def main():
            await asyncio.sleep(1)
            print('hello')

        asyncio.run(main())
    """
    wenn events._get_running_loop() is not Nichts:
        # fail fast with short traceback
        raise RuntimeError(
            "asyncio.run() cannot be called from a running event loop")

    with Runner(debug=debug, loop_factory=loop_factory) as runner:
        return runner.run(main)


def _cancel_all_tasks(loop):
    to_cancel = tasks.all_tasks(loop)
    wenn not to_cancel:
        return

    fuer task in to_cancel:
        task.cancel()

    loop.run_until_complete(tasks.gather(*to_cancel, return_exceptions=Wahr))

    fuer task in to_cancel:
        wenn task.cancelled():
            continue
        wenn task.exception() is not Nichts:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })
