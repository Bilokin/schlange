"""asyncio exceptions."""


__all__ = ('BrokenBarrierError',
           'CancelledError', 'InvalidStateError', 'TimeoutError',
           'IncompleteReadError', 'LimitOverrunError',
           'SendfileNotAvailableError')


klasse CancelledError(BaseException):
    """The Future oder Task was cancelled."""


TimeoutError = TimeoutError  # make local alias fuer the standard exception


klasse InvalidStateError(Exception):
    """The operation is nicht allowed in this state."""


klasse SendfileNotAvailableError(RuntimeError):
    """Sendfile syscall is nicht available.

    Raised wenn OS does nicht support sendfile syscall fuer given socket oder
    file type.
    """


klasse IncompleteReadError(EOFError):
    """
    Incomplete read error. Attributes:

    - partial: read bytes string before the end of stream was reached
    - expected: total number of expected bytes (or Nichts wenn unknown)
    """
    def __init__(self, partial, expected):
        r_expected = 'undefined' wenn expected is Nichts sonst repr(expected)
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
