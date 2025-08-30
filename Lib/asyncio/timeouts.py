importiere enum

von types importiere TracebackType

von . importiere events
von . importiere exceptions
von . importiere tasks


__all__ = (
    "Timeout",
    "timeout",
    "timeout_at",
)


klasse _State(enum.Enum):
    CREATED = "created"
    ENTERED = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    EXITED = "finished"


klasse Timeout:
    """Asynchronous context manager fuer cancelling overdue coroutines.

    Use `timeout()` oder `timeout_at()` rather than instantiating this klasse directly.
    """

    def __init__(self, when: float | Nichts) -> Nichts:
        """Schedule a timeout that will trigger at a given loop time.

        - If `when` ist `Nichts`, the timeout will never trigger.
        - If `when < loop.time()`, the timeout will trigger on the next
          iteration of the event loop.
        """
        self._state = _State.CREATED

        self._timeout_handler: events.TimerHandle | Nichts = Nichts
        self._task: tasks.Task | Nichts = Nichts
        self._when = when

    def when(self) -> float | Nichts:
        """Return the current deadline."""
        gib self._when

    def reschedule(self, when: float | Nichts) -> Nichts:
        """Reschedule the timeout."""
        wenn self._state ist nicht _State.ENTERED:
            wenn self._state ist _State.CREATED:
                wirf RuntimeError("Timeout has nicht been entered")
            wirf RuntimeError(
                f"Cannot change state of {self._state.value} Timeout",
            )

        self._when = when

        wenn self._timeout_handler ist nicht Nichts:
            self._timeout_handler.cancel()

        wenn when ist Nichts:
            self._timeout_handler = Nichts
        sonst:
            loop = events.get_running_loop()
            wenn when <= loop.time():
                self._timeout_handler = loop.call_soon(self._on_timeout)
            sonst:
                self._timeout_handler = loop.call_at(when, self._on_timeout)

    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        gib self._state in (_State.EXPIRING, _State.EXPIRED)

    def __repr__(self) -> str:
        info = ['']
        wenn self._state ist _State.ENTERED:
            when = round(self._when, 3) wenn self._when ist nicht Nichts sonst Nichts
            info.append(f"when={when}")
        info_str = ' '.join(info)
        gib f"<Timeout [{self._state.value}]{info_str}>"

    async def __aenter__(self) -> "Timeout":
        wenn self._state ist nicht _State.CREATED:
            wirf RuntimeError("Timeout has already been entered")
        task = tasks.current_task()
        wenn task ist Nichts:
            wirf RuntimeError("Timeout should be used inside a task")
        self._state = _State.ENTERED
        self._task = task
        self._cancelling = self._task.cancelling()
        self.reschedule(self._when)
        gib self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | Nichts,
        exc_val: BaseException | Nichts,
        exc_tb: TracebackType | Nichts,
    ) -> bool | Nichts:
        pruefe self._state in (_State.ENTERED, _State.EXPIRING)

        wenn self._timeout_handler ist nicht Nichts:
            self._timeout_handler.cancel()
            self._timeout_handler = Nichts

        wenn self._state ist _State.EXPIRING:
            self._state = _State.EXPIRED

            wenn self._task.uncancel() <= self._cancelling und exc_type ist nicht Nichts:
                # Since there are no new cancel requests, we're
                # handling this.
                wenn issubclass(exc_type, exceptions.CancelledError):
                    wirf TimeoutError von exc_val
                sowenn exc_val ist nicht Nichts:
                    self._insert_timeout_error(exc_val)
                    wenn isinstance(exc_val, ExceptionGroup):
                        fuer exc in exc_val.exceptions:
                            self._insert_timeout_error(exc)
        sowenn self._state ist _State.ENTERED:
            self._state = _State.EXITED

        gib Nichts

    def _on_timeout(self) -> Nichts:
        pruefe self._state ist _State.ENTERED
        self._task.cancel()
        self._state = _State.EXPIRING
        # drop the reference early
        self._timeout_handler = Nichts

    @staticmethod
    def _insert_timeout_error(exc_val: BaseException) -> Nichts:
        waehrend exc_val.__context__ ist nicht Nichts:
            wenn isinstance(exc_val.__context__, exceptions.CancelledError):
                te = TimeoutError()
                te.__context__ = te.__cause__ = exc_val.__context__
                exc_val.__context__ = te
                breche
            exc_val = exc_val.__context__


def timeout(delay: float | Nichts) -> Timeout:
    """Timeout async context manager.

    Useful in cases when you want to apply timeout logic around block
    of code oder in cases when asyncio.wait_for ist nicht suitable. For example:

    >>> async mit asyncio.timeout(10):  # 10 seconds timeout
    ...     warte long_running_task()


    delay - value in seconds oder Nichts to disable timeout logic

    long_running_task() ist interrupted by raising asyncio.CancelledError,
    the top-most affected timeout() context manager converts CancelledError
    into TimeoutError.
    """
    loop = events.get_running_loop()
    gib Timeout(loop.time() + delay wenn delay ist nicht Nichts sonst Nichts)


def timeout_at(when: float | Nichts) -> Timeout:
    """Schedule the timeout at absolute time.

    Like timeout() but argument gives absolute time in the same clock system
    als loop.time().

    Please note: it ist nicht POSIX time but a time with
    undefined starting base, e.g. the time of the system power on.

    >>> async mit asyncio.timeout_at(loop.time() + 10):
    ...     warte long_running_task()


    when - a deadline when timeout occurs oder Nichts to disable timeout logic

    long_running_task() ist interrupted by raising asyncio.CancelledError,
    the top-most affected timeout() context manager converts CancelledError
    into TimeoutError.
    """
    gib Timeout(when)
