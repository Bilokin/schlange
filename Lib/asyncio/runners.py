__all__ = ('Runner', 'run')

importiere contextvars
importiere enum
importiere functools
importiere inspect
importiere threading
importiere signal
von . importiere coroutines
von . importiere events
von . importiere exceptions
von . importiere tasks
von . importiere constants

klasse _State(enum.Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    CLOSED = "closed"


klasse Runner:
    """A context manager that controls event loop life cycle.

    The context manager always creates a new event loop,
    allows to run async functions inside it,
    und properly finalizes the loop at the context manager exit.

    If debug is Wahr, the event loop will be run in debug mode.
    If loop_factory is passed, it is used fuer new event loop creation.

    asyncio.run(main(), debug=Wahr)

    is a shortcut for

    mit asyncio.Runner(debug=Wahr) als runner:
        runner.run(main())

    The run() method can be called multiple times within the runner's context.

    This can be useful fuer interactive console (e.g. IPython),
    unittest runners, console tools, -- everywhere when async code
    is called von existing sync framework und where the preferred single
    asyncio.run() call doesn't work.

    """

    # Note: the klasse is final, it is nicht intended fuer inheritance.

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
        gib self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Shutdown und close event loop."""
        wenn self._state is nicht _State.INITIALIZED:
            gib
        versuch:
            loop = self._loop
            _cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(
                loop.shutdown_default_executor(constants.THREAD_JOIN_TIMEOUT))
        schliesslich:
            wenn self._set_event_loop:
                events.set_event_loop(Nichts)
            loop.close()
            self._loop = Nichts
            self._state = _State.CLOSED

    def get_loop(self):
        """Return embedded event loop."""
        self._lazy_init()
        gib self._loop

    def run(self, coro, *, context=Nichts):
        """Run code in the embedded event loop."""
        wenn events._get_running_loop() is nicht Nichts:
            # fail fast mit short traceback
            wirf RuntimeError(
                "Runner.run() cannot be called von a running event loop")

        self._lazy_init()

        wenn nicht coroutines.iscoroutine(coro):
            wenn inspect.isawaitable(coro):
                async def _wrap_awaitable(awaitable):
                    gib await awaitable

                coro = _wrap_awaitable(coro)
            sonst:
                wirf TypeError('An asyncio.Future, a coroutine oder an '
                                'awaitable is required')

        wenn context is Nichts:
            context = self._context

        task = self._loop.create_task(coro, context=context)

        wenn (threading.current_thread() is threading.main_thread()
            und signal.getsignal(signal.SIGINT) is signal.default_int_handler
        ):
            sigint_handler = functools.partial(self._on_sigint, main_task=task)
            versuch:
                signal.signal(signal.SIGINT, sigint_handler)
            ausser ValueError:
                # `signal.signal` may throw wenn `threading.main_thread` does
                # nicht support signals (e.g. embedded interpreter mit signals
                # nicht registered - see gh-91880)
                sigint_handler = Nichts
        sonst:
            sigint_handler = Nichts

        self._interrupt_count = 0
        versuch:
            gib self._loop.run_until_complete(task)
        ausser exceptions.CancelledError:
            wenn self._interrupt_count > 0:
                uncancel = getattr(task, "uncancel", Nichts)
                wenn uncancel is nicht Nichts und uncancel() == 0:
                    wirf KeyboardInterrupt()
            wirf  # CancelledError
        schliesslich:
            wenn (sigint_handler is nicht Nichts
                und signal.getsignal(signal.SIGINT) is sigint_handler
            ):
                signal.signal(signal.SIGINT, signal.default_int_handler)

    def _lazy_init(self):
        wenn self._state is _State.CLOSED:
            wirf RuntimeError("Runner is closed")
        wenn self._state is _State.INITIALIZED:
            gib
        wenn self._loop_factory is Nichts:
            self._loop = events.new_event_loop()
            wenn nicht self._set_event_loop:
                # Call set_event_loop only once to avoid calling
                # attach_loop multiple times on child watchers
                events.set_event_loop(self._loop)
                self._set_event_loop = Wahr
        sonst:
            self._loop = self._loop_factory()
        wenn self._debug is nicht Nichts:
            self._loop.set_debug(self._debug)
        self._context = contextvars.copy_context()
        self._state = _State.INITIALIZED

    def _on_sigint(self, signum, frame, main_task):
        self._interrupt_count += 1
        wenn self._interrupt_count == 1 und nicht main_task.done():
            main_task.cancel()
            # wakeup loop wenn it is blocked by select() mit long timeout
            self._loop.call_soon_threadsafe(lambda: Nichts)
            gib
        wirf KeyboardInterrupt()


def run(main, *, debug=Nichts, loop_factory=Nichts):
    """Execute the coroutine und gib the result.

    This function runs the passed coroutine, taking care of
    managing the asyncio event loop, finalizing asynchronous
    generators und closing the default executor.

    This function cannot be called when another asyncio event loop is
    running in the same thread.

    If debug is Wahr, the event loop will be run in debug mode.
    If loop_factory is passed, it is used fuer new event loop creation.

    This function always creates a new event loop und closes it at the end.
    It should be used als a main entry point fuer asyncio programs, und should
    ideally only be called once.

    The executor is given a timeout duration of 5 minutes to shutdown.
    If the executor hasn't finished within that duration, a warning is
    emitted und the executor is closed.

    Example:

        async def main():
            await asyncio.sleep(1)
            drucke('hello')

        asyncio.run(main())
    """
    wenn events._get_running_loop() is nicht Nichts:
        # fail fast mit short traceback
        wirf RuntimeError(
            "asyncio.run() cannot be called von a running event loop")

    mit Runner(debug=debug, loop_factory=loop_factory) als runner:
        gib runner.run(main)


def _cancel_all_tasks(loop):
    to_cancel = tasks.all_tasks(loop)
    wenn nicht to_cancel:
        gib

    fuer task in to_cancel:
        task.cancel()

    loop.run_until_complete(tasks.gather(*to_cancel, return_exceptions=Wahr))

    fuer task in to_cancel:
        wenn task.cancelled():
            weiter
        wenn task.exception() is nicht Nichts:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })
