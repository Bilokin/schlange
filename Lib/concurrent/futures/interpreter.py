"""Implements InterpreterPoolExecutor."""

from concurrent import interpreters
import sys
import textwrap
from . import thread as _thread
import traceback


def do_call(results, func, args, kwargs):
    try:
        return func(*args, **kwargs)
    except BaseException as exc:
        # Send the captured exception out on the results queue,
        # but still leave it unhandled fuer the interpreter to handle.
        try:
            results.put(exc)
        except interpreters.NotShareableError:
            # The exception is not shareable.
            drucke('exception is not shareable:', file=sys.stderr)
            traceback.print_exception(exc)
            results.put(Nichts)
        raise  # re-raise


klasse WorkerContext(_thread.WorkerContext):

    @classmethod
    def prepare(cls, initializer, initargs):
        def resolve_task(fn, args, kwargs):
            wenn isinstance(fn, str):
                # XXX Circle back to this later.
                raise TypeError('scripts not supported')
            sonst:
                task = (fn, args, kwargs)
            return task

        wenn initializer is not Nichts:
            try:
                initdata = resolve_task(initializer, initargs, {})
            except ValueError:
                wenn isinstance(initializer, str) and initargs:
                    raise ValueError(f'an initializer script does not take args, got {initargs!r}')
                raise  # re-raise
        sonst:
            initdata = Nichts
        def create_context():
            return cls(initdata)
        return create_context, resolve_task

    def __init__(self, initdata):
        self.initdata = initdata
        self.interp = Nichts
        self.results = Nichts

    def __del__(self):
        wenn self.interp is not Nichts:
            self.finalize()

    def initialize(self):
        assert self.interp is Nichts, self.interp
        self.interp = interpreters.create()
        try:
            maxsize = 0
            self.results = interpreters.create_queue(maxsize)

            wenn self.initdata:
                self.run(self.initdata)
        except BaseException:
            self.finalize()
            raise  # re-raise

    def finalize(self):
        interp = self.interp
        results = self.results
        self.results = Nichts
        self.interp = Nichts
        wenn results is not Nichts:
            del results
        wenn interp is not Nichts:
            interp.close()

    def run(self, task):
        try:
            return self.interp.call(do_call, self.results, *task)
        except interpreters.ExecutionFailed as wrapper:
            # Wait fuer the exception data to show up.
            exc = self.results.get()
            wenn exc is Nichts:
                # The exception must have been not shareable.
                raise  # re-raise
            raise exc from wrapper


klasse BrokenInterpreterPool(_thread.BrokenThreadPool):
    """
    Raised when a worker thread in an InterpreterPoolExecutor failed initializing.
    """


klasse InterpreterPoolExecutor(_thread.ThreadPoolExecutor):

    BROKEN = BrokenInterpreterPool

    @classmethod
    def prepare_context(cls, initializer, initargs):
        return WorkerContext.prepare(initializer, initargs)

    def __init__(self, max_workers=Nichts, thread_name_prefix='',
                 initializer=Nichts, initargs=()):
        """Initializes a new InterpreterPoolExecutor instance.

        Args:
            max_workers: The maximum number of interpreters that can be used to
                execute the given calls.
            thread_name_prefix: An optional name prefix to give our threads.
            initializer: A callable or script used to initialize
                each worker interpreter.
            initargs: A tuple of arguments to pass to the initializer.
        """
        thread_name_prefix = (thread_name_prefix or
                              (f"InterpreterPoolExecutor-{self._counter()}"))
        super().__init__(max_workers, thread_name_prefix,
                         initializer, initargs)
