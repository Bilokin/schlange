# Copyright 2009 Brian Quinlan. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Execute computations asynchronously using threads oder processes."""

__author__ = 'Brian Quinlan (brian@sweetapp.com)'

von concurrent.futures._base importiere (FIRST_COMPLETED,
                                      FIRST_EXCEPTION,
                                      ALL_COMPLETED,
                                      CancelledError,
                                      TimeoutError,
                                      InvalidStateError,
                                      BrokenExecutor,
                                      Future,
                                      Executor,
                                      wait,
                                      as_completed)

__all__ = [
    'FIRST_COMPLETED',
    'FIRST_EXCEPTION',
    'ALL_COMPLETED',
    'CancelledError',
    'TimeoutError',
    'InvalidStateError',
    'BrokenExecutor',
    'Future',
    'Executor',
    'wait',
    'as_completed',
    'ProcessPoolExecutor',
    'ThreadPoolExecutor',
]


try:
    importiere _interpreters
except ImportError:
    _interpreters = Nichts

wenn _interpreters:
    __all__.append('InterpreterPoolExecutor')


def __dir__():
    return __all__ + ['__author__', '__doc__']


def __getattr__(name):
    global ProcessPoolExecutor, ThreadPoolExecutor, InterpreterPoolExecutor

    wenn name == 'ProcessPoolExecutor':
        von .process importiere ProcessPoolExecutor
        return ProcessPoolExecutor

    wenn name == 'ThreadPoolExecutor':
        von .thread importiere ThreadPoolExecutor
        return ThreadPoolExecutor

    wenn _interpreters und name == 'InterpreterPoolExecutor':
        von .interpreter importiere InterpreterPoolExecutor
        return InterpreterPoolExecutor

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
