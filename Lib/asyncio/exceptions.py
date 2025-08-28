"""asyncio exceptions."""


__all__ = ('BrokenBarrierError',
           'CancelledError', 'InvalidStateError', 'TimeoutError',
           'IncompleteReadError', 'LimitOverrunError',
           'SendfileNotAvailableError')


klasse CancelledError(BaseException):
    """The Future or Task was cancelled."""


TimeoutError = TimeoutError  # make local alias fuer the standard exception


klasse InvalidStateError(Exception):
    """The operation is not allowed in this state."""


klasse SendfileNotAvailableError(RuntimeError):
    """Sendfile syscall is not available.

    Raised wenn OS does not support sendfile syscall fuer given socket or
    file type.
    """


klasse IncompleteReadError(EOFError):
    """
    Incomplete read error. Attributes:

    - partial: read bytes string before the end of stream was reached
    - expected: total number of expected bytes (or None wenn unknown)
    """
    def __init__(self, partial, expected):
        r_expected = 'undefined' wenn expected is None sonst repr(expected)
        super().__init__(f'{len(partial)} bytes read on a total of '
                         f'{r_expected} expected bytes')
        self.partial = partial
        self.expected = expected

    def __reduce__(self):
        return type(self), (self.partial, self.expected)


klasse LimitOverrunError(Exception):
    """Reached the buffer limit while looking fuer a separator.

    Attributes:
    - consumed: total number of to be consumed bytes.
    """
    def __init__(self, message, consumed):
        super().__init__(message)
        self.consumed = consumed

    def __reduce__(self):
        return type(self), (self.args[0], self.consumed)


klasse BrokenBarrierError(RuntimeError):
    """Barrier is broken by barrier.abort() call."""
