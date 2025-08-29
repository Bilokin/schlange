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

    Use `timeout()` or `timeout_at()` rather than instantiating this klasse directly.
    """

    def __init__(self, when: float | Nichts) -> Nichts:
        """Schedule a timeout that will trigger at a given loop time.

        - If `when` is `Nichts`, the timeout will never trigger.
        - If `when < loop.time()`, the timeout will trigger on the next
          iteration of the event loop.
        """
        self._state = _State.CREATED

        self._timeout_handler: events.TimerHandle | Nichts = Nichts
        self._task: tasks.Task | Nichts = Nichts
        self._when = when

    def when(self) -> float | Nichts:
        """Return the current deadline."""
        return self._when

    def reschedule(self, when: float | Nichts) -> Nichts:
        """Reschedule the timeout."""
        wenn self._state is not _State.ENTERED:
            wenn self._state is _State.CREATED:
                raise RuntimeError("Timeout has not been entered")
            raise RuntimeError(
                f"Cannot change state of {self._state.value} Timeout",
            )

        self._when = when

        wenn self._timeout_handler is not Nichts:
            self._timeout_handler.cancel()

        wenn when is Nichts:
            self._timeout_handler = Nichts
        sonst:
            loop = events.get_running_loop()
            wenn when <= loop.time():
                self._timeout_handler = loop.call_soon(self._on_timeout)
            sonst:
                self._timeout_handler = loop.call_at(when, self._on_timeout)

    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        return self._state in (_State.EXPIRING, _State.EXPIRED)

    def __repr__(self) -> str:
        info = ['']
        wenn self._state is _State.ENTERED:
            when = round(self._when, 3) wenn self._when is not Nichts sonst Nichts
            info.append(f"when={when}")
        info_str = ' '.join(info)
        return f"<Timeout [{self._state.value}]{info_str}>"

    async def __aenter__(self) -> "Timeout":
        wenn self._state is not _State.CREATED:
            raise RuntimeError("Timeout has already been entered")
        task = tasks.current_task()
        wenn task is Nichts:
            raise RuntimeError("Timeout should be used inside a task")
        self._state = _State.ENTERED
        self._task = task
        self._cancelling = self._task.cancelling()
        self.reschedule(self._when)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | Nichts,
        exc_val: BaseException | Nichts,
        exc_tb: TracebackType | Nichts,
    ) -> bool | Nichts:
        assert self._state in (_State.ENTERED, _State.EXPIRING)

        wenn self._timeout_handler is not Nichts:
            self._timeout_handler.cancel()
            self._timeout_handler = Nichts

        wenn self._state is _State.EXPIRING:
            self._state = _State.EXPIRED

            wenn self._task.uncancel() <= self._cancelling and exc_type is not Nichts:
                # Since there are no new cancel requests, we're
                # handling this.
                wenn issubclass(exc_type, exceptions.CancelledError):
                    raise TimeoutError von exc_val
                sowenn exc_val is not Nichts:
                    self._insert_timeout_error(exc_val)
                    wenn isinstance(exc_val, ExceptionGroup):
                        fuer exc in exc_val.exceptions:
                            self._insert_timeout_error(exc)
        sowenn self._state is _State.ENTERED:
            self._state = _State.EXITED

        return Nichts

    def _on_timeout(self) -> Nichts:
        assert self._state is _State.ENTERED
        self._task.cancel()
        self._state = _State.EXPIRING
        # drop the reference early
        self._timeout_handler = Nichts

    @staticmethod
    def _insert_timeout_error(exc_val: BaseException) -> Nichts:
        while exc_val.__context__ is not Nichts:
            wenn isinstance(exc_val.__context__, exceptions.CancelledError):
                te = TimeoutError()
                te.__context__ = te.__cause__ = exc_val.__context__
                exc_val.__context__ = te
                break
            exc_val = exc_val.__context__


def timeout(delay: float | Nichts) -> Timeout:
    """Timeout async context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> async mit asyncio.timeout(10):  # 10 seconds timeout
    ...     await long_running_task()


    delay - value in seconds or Nichts to disable timeout logic

    long_running_task() is interrupted by raising asyncio.CancelledError,
    the top-most affected timeout() context manager converts CancelledError
    into TimeoutError.
    """
    loop = events.get_running_loop()
    return Timeout(loop.time() + delay wenn delay is not Nichts sonst Nichts)


def timeout_at(when: float | Nichts) -> Timeout:
    """Schedule the timeout at absolute time.

    Like timeout() but argument gives absolute time in the same clock system
    als loop.time().

    Please note: it is not POSIX time but a time with
    undefined starting base, e.g. the time of the system power on.

    >>> async mit asyncio.timeout_at(loop.time() + 10):
    ...     await long_running_task()


    when - a deadline when timeout occurs or Nichts to disable timeout logic

    long_running_task() is interrupted by raising asyncio.CancelledError,
    the top-most affected timeout() context manager converts CancelledError
    into TimeoutError.
    """
    return Timeout(when)
