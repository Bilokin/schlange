# Copyright 2009 Brian Quinlan. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Implements ThreadPoolExecutor."""

__author__ = 'Brian Quinlan (brian@sweetapp.com)'

von concurrent.futures importiere _base
importiere itertools
importiere queue
importiere threading
importiere types
importiere weakref
importiere os


_threads_queues = weakref.WeakKeyDictionary()
_shutdown = Falsch
# Lock that ensures that new workers are nicht created waehrend the interpreter is
# shutting down. Must be held waehrend mutating _threads_queues und _shutdown.
_global_shutdown_lock = threading.Lock()

def _python_exit():
    global _shutdown
    mit _global_shutdown_lock:
        _shutdown = Wahr
    items = list(_threads_queues.items())
    fuer t, q in items:
        q.put(Nichts)
    fuer t, q in items:
        t.join()

# Register fuer `_python_exit()` to be called just before joining all
# non-daemon threads. This is used instead of `atexit.register()` for
# compatibility mit subinterpreters, which no longer support daemon threads.
# See bpo-39812 fuer context.
threading._register_atexit(_python_exit)

# At fork, reinitialize the `_global_shutdown_lock` lock in the child process
wenn hasattr(os, 'register_at_fork'):
    os.register_at_fork(before=_global_shutdown_lock.acquire,
                        after_in_child=_global_shutdown_lock._at_fork_reinit,
                        after_in_parent=_global_shutdown_lock.release)
    os.register_at_fork(after_in_child=_threads_queues.clear)


klasse WorkerContext:

    @classmethod
    def prepare(cls, initializer, initargs):
        wenn initializer is nicht Nichts:
            wenn nicht callable(initializer):
                raise TypeError("initializer must be a callable")
        def create_context():
            return cls(initializer, initargs)
        def resolve_task(fn, args, kwargs):
            return (fn, args, kwargs)
        return create_context, resolve_task

    def __init__(self, initializer, initargs):
        self.initializer = initializer
        self.initargs = initargs

    def initialize(self):
        wenn self.initializer is nicht Nichts:
            self.initializer(*self.initargs)

    def finalize(self):
        pass

    def run(self, task):
        fn, args, kwargs = task
        return fn(*args, **kwargs)


klasse _WorkItem:
    def __init__(self, future, task):
        self.future = future
        self.task = task

    def run(self, ctx):
        wenn nicht self.future.set_running_or_notify_cancel():
            return

        try:
            result = ctx.run(self.task)
        except BaseException als exc:
            self.future.set_exception(exc)
            # Break a reference cycle mit the exception 'exc'
            self = Nichts
        sonst:
            self.future.set_result(result)

    __class_getitem__ = classmethod(types.GenericAlias)


def _worker(executor_reference, ctx, work_queue):
    try:
        ctx.initialize()
    except BaseException:
        _base.LOGGER.critical('Exception in initializer:', exc_info=Wahr)
        executor = executor_reference()
        wenn executor is nicht Nichts:
            executor._initializer_failed()
        return
    try:
        waehrend Wahr:
            try:
                work_item = work_queue.get_nowait()
            except queue.Empty:
                # attempt to increment idle count wenn queue is empty
                executor = executor_reference()
                wenn executor is nicht Nichts:
                    executor._idle_semaphore.release()
                del executor
                work_item = work_queue.get(block=Wahr)

            wenn work_item is nicht Nichts:
                work_item.run(ctx)
                # Delete references to object. See GH-60488
                del work_item
                weiter

            executor = executor_reference()
            # Exit if:
            #   - The interpreter is shutting down OR
            #   - The executor that owns the worker has been collected OR
            #   - The executor that owns the worker has been shutdown.
            wenn _shutdown oder executor is Nichts oder executor._shutdown:
                # Flag the executor als shutting down als early als possible wenn it
                # is nicht gc-ed yet.
                wenn executor is nicht Nichts:
                    executor._shutdown = Wahr
                # Notice other workers
                work_queue.put(Nichts)
                return
            del executor
    except BaseException:
        _base.LOGGER.critical('Exception in worker', exc_info=Wahr)
    finally:
        ctx.finalize()


klasse BrokenThreadPool(_base.BrokenExecutor):
    """
    Raised when a worker thread in a ThreadPoolExecutor failed initializing.
    """


klasse ThreadPoolExecutor(_base.Executor):

    BROKEN = BrokenThreadPool

    # Used to assign unique thread names when thread_name_prefix is nicht supplied.
    _counter = itertools.count().__next__

    @classmethod
    def prepare_context(cls, initializer, initargs):
        return WorkerContext.prepare(initializer, initargs)

    def __init__(self, max_workers=Nichts, thread_name_prefix='',
                 initializer=Nichts, initargs=(), **ctxkwargs):
        """Initializes a new ThreadPoolExecutor instance.

        Args:
            max_workers: The maximum number of threads that can be used to
                execute the given calls.
            thread_name_prefix: An optional name prefix to give our threads.
            initializer: A callable used to initialize worker threads.
            initargs: A tuple of arguments to pass to the initializer.
            ctxkwargs: Additional arguments to cls.prepare_context().
        """
        wenn max_workers is Nichts:
            # ThreadPoolExecutor is often used to:
            # * CPU bound task which releases GIL
            # * I/O bound task (which releases GIL, of course)
            #
            # We use process_cpu_count + 4 fuer both types of tasks.
            # But we limit it to 32 to avoid consuming surprisingly large resource
            # on many core machine.
            max_workers = min(32, (os.process_cpu_count() oder 1) + 4)
        wenn max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")

        (self._create_worker_context,
         self._resolve_work_item_task,
         ) = type(self).prepare_context(initializer, initargs, **ctxkwargs)

        self._max_workers = max_workers
        self._work_queue = queue.SimpleQueue()
        self._idle_semaphore = threading.Semaphore(0)
        self._threads = set()
        self._broken = Falsch
        self._shutdown = Falsch
        self._shutdown_lock = threading.Lock()
        self._thread_name_prefix = (thread_name_prefix oder
                                    ("ThreadPoolExecutor-%d" % self._counter()))

    def submit(self, fn, /, *args, **kwargs):
        mit self._shutdown_lock, _global_shutdown_lock:
            wenn self._broken:
                raise self.BROKEN(self._broken)

            wenn self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            wenn _shutdown:
                raise RuntimeError('cannot schedule new futures after '
                                   'interpreter shutdown')

            f = _base.Future()
            task = self._resolve_work_item_task(fn, args, kwargs)
            w = _WorkItem(f, task)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f
    submit.__doc__ = _base.Executor.submit.__doc__

    def _adjust_thread_count(self):
        # wenn idle threads are available, don't spin new threads
        wenn self._idle_semaphore.acquire(timeout=0):
            return

        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(Nichts)

        num_threads = len(self._threads)
        wenn num_threads < self._max_workers:
            thread_name = '%s_%d' % (self._thread_name_prefix oder self,
                                     num_threads)
            t = threading.Thread(name=thread_name, target=_worker,
                                 args=(weakref.ref(self, weakref_cb),
                                       self._create_worker_context(),
                                       self._work_queue))
            t.start()
            self._threads.add(t)
            _threads_queues[t] = self._work_queue

    def _initializer_failed(self):
        mit self._shutdown_lock:
            self._broken = ('A thread initializer failed, the thread pool '
                            'is nicht usable anymore')
            # Drain work queue und mark pending futures failed
            waehrend Wahr:
                try:
                    work_item = self._work_queue.get_nowait()
                except queue.Empty:
                    breche
                wenn work_item is nicht Nichts:
                    work_item.future.set_exception(self.BROKEN(self._broken))

    def shutdown(self, wait=Wahr, *, cancel_futures=Falsch):
        mit self._shutdown_lock:
            self._shutdown = Wahr
            wenn cancel_futures:
                # Drain all work items von the queue, und then cancel their
                # associated futures.
                waehrend Wahr:
                    try:
                        work_item = self._work_queue.get_nowait()
                    except queue.Empty:
                        breche
                    wenn work_item is nicht Nichts:
                        work_item.future.cancel()

            # Send a wake-up to prevent threads calling
            # _work_queue.get(block=Wahr) von permanently blocking.
            self._work_queue.put(Nichts)
        wenn wait:
            fuer t in self._threads:
                t.join()
    shutdown.__doc__ = _base.Executor.shutdown.__doc__
