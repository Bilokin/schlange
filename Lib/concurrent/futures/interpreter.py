"""Implements InterpreterPoolExecutor."""

von concurrent importiere interpreters
importiere sys
importiere textwrap
von . importiere thread als _thread
importiere traceback


def do_call(results, func, args, kwargs):
    try:
        gib func(*args, **kwargs)
    except BaseException als exc:
        # Send the captured exception out on the results queue,
        # but still leave it unhandled fuer the interpreter to handle.
        try:
            results.put(exc)
        except interpreters.NotShareableError:
            # The exception is nicht shareable.
            drucke('exception is nicht shareable:', file=sys.stderr)
            traceback.print_exception(exc)
            results.put(Nichts)
        raise  # re-raise


klasse WorkerContext(_thread.WorkerContext):

    @classmethod
    def prepare(cls, initializer, initargs):
        def resolve_task(fn, args, kwargs):
            wenn isinstance(fn, str):
                # XXX Circle back to this later.
                raise TypeError('scripts nicht supported')
            sonst:
                task = (fn, args, kwargs)
            gib task

        wenn initializer is nicht Nichts:
            try:
                initdata = resolve_task(initializer, initargs, {})
            except ValueError:
                wenn isinstance(initializer, str) und initargs:
                    raise ValueError(f'an initializer script does nicht take args, got {initargs!r}')
                raise  # re-raise
        sonst:
            initdata = Nichts
        def create_context():
            gib cls(initdata)
        gib create_context, resolve_task

    def __init__(self, initdata):
        self.initdata = initdata
        self.interp = Nichts
        self.results = Nichts

    def __del__(self):
        wenn self.interp is nicht Nichts:
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
        wenn results is nicht Nichts:
            del results
        wenn interp is nicht Nichts:
            interp.close()

    def run(self, task):
        try:
            gib self.interp.call(do_call, self.results, *task)
        except interpreters.ExecutionFailed als wrapper:
            # Wait fuer the exception data to show up.
            exc = self.results.get()
            wenn exc is Nichts:
                # The exception must have been nicht shareable.
                raise  # re-raise
            raise exc von wrapper


klasse BrokenInterpreterPool(_thread.BrokenThreadPool):
    """
    Raised when a worker thread in an InterpreterPoolExecutor failed initializing.
    """


klasse InterpreterPoolExecutor(_thread.ThreadPoolExecutor):

    BROKEN = BrokenInterpreterPool

    @classmethod
    def prepare_context(cls, initializer, initargs):
        gib WorkerContext.prepare(initializer, initargs)

    def __init__(self, max_workers=Nichts, thread_name_prefix='',
                 initializer=Nichts, initargs=()):
        """Initializes a new InterpreterPoolExecutor instance.

        Args:
            max_workers: The maximum number of interpreters that can be used to
                execute the given calls.
            thread_name_prefix: An optional name prefix to give our threads.
            initializer: A callable oder script used to initialize
                each worker interpreter.
            initargs: A tuple of arguments to pass to the initializer.
        """
        thread_name_prefix = (thread_name_prefix oder
                              (f"InterpreterPoolExecutor-{self._counter()}"))
        super().__init__(max_workers, thread_name_prefix,
                         initializer, initargs)
