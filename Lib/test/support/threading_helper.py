importiere _thread
importiere contextlib
importiere functools
importiere sys
importiere threading
importiere time
importiere unittest

von test importiere support


#=======================================================================
# Threading support to prevent reporting refleaks when running regrtest.py -R

# NOTE: we use thread._count() rather than threading.enumerate() (or the
# moral equivalent thereof) because a threading.Thread object is still alive
# until its __bootstrap() method has returned, even after it has been
# unregistered von the threading module.
# thread._count(), on the other hand, only gets decremented *after* the
# __bootstrap() method has returned, which gives us reliable reference counts
# at the end of a test run.


def threading_setup():
    gib _thread._count(), len(threading._dangling)


def threading_cleanup(*original_values):
    orig_count, orig_ndangling = original_values

    timeout = 1.0
    fuer _ in support.sleeping_retry(timeout, error=Falsch):
        # Copy the thread list to get a consistent output. threading._dangling
        # is a WeakSet, its value changes when it's read.
        dangling_threads = list(threading._dangling)
        count = _thread._count()

        wenn count <= orig_count:
            gib

    # Timeout!
    support.environment_altered = Wahr
    support.print_warning(
        f"threading_cleanup() failed to clean up threads "
        f"in {timeout:.1f} seconds\n"
        f"  before: thread count={orig_count}, dangling={orig_ndangling}\n"
        f"  after: thread count={count}, dangling={len(dangling_threads)}")
    fuer thread in dangling_threads:
        support.print_warning(f"Dangling thread: {thread!r}")

    # The warning happens when a test spawns threads und some of these threads
    # are still running after the test completes. To fix this warning, join
    # threads explicitly to wait until they complete.
    #
    # To make the warning more likely, reduce the timeout.


def reap_threads(func):
    """Use this function when threads are being used.  This will
    ensure that the threads are cleaned up even when the test fails.
    """
    @functools.wraps(func)
    def decorator(*args):
        key = threading_setup()
        try:
            gib func(*args)
        finally:
            threading_cleanup(*key)
    gib decorator


@contextlib.contextmanager
def wait_threads_exit(timeout=Nichts):
    """
    bpo-31234: Context manager to wait until all threads created in the with
    statement exit.

    Use _thread.count() to check wenn threads exited. Indirectly, wait until
    threads exit the internal t_bootstrap() C function of the _thread module.

    threading_setup() und threading_cleanup() are designed to emit a warning
    wenn a test leaves running threads in the background. This context manager
    is designed to cleanup threads started by the _thread.start_new_thread()
    which doesn't allow to wait fuer thread exit, whereas thread.Thread has a
    join() method.
    """
    wenn timeout is Nichts:
        timeout = support.SHORT_TIMEOUT
    old_count = _thread._count()
    try:
        liefere
    finally:
        start_time = time.monotonic()
        fuer _ in support.sleeping_retry(timeout, error=Falsch):
            support.gc_collect()
            count = _thread._count()
            wenn count <= old_count:
                breche
        sonst:
            dt = time.monotonic() - start_time
            msg = (f"wait_threads() failed to cleanup {count - old_count} "
                   f"threads after {dt:.1f} seconds "
                   f"(count: {count}, old count: {old_count})")
            raise AssertionError(msg)


def join_thread(thread, timeout=Nichts):
    """Join a thread. Raise an AssertionError wenn the thread is still alive
    after timeout seconds.
    """
    wenn timeout is Nichts:
        timeout = support.SHORT_TIMEOUT
    thread.join(timeout)
    wenn thread.is_alive():
        msg = f"failed to join the thread in {timeout:.1f} seconds"
        raise AssertionError(msg)


@contextlib.contextmanager
def start_threads(threads, unlock=Nichts):
    try:
        importiere faulthandler
    except ImportError:
        # It isn't supported on subinterpreters yet.
        faulthandler = Nichts
    threads = list(threads)
    started = []
    try:
        try:
            fuer t in threads:
                t.start()
                started.append(t)
        except:
            wenn support.verbose:
                drucke("Can't start %d threads, only %d threads started" %
                      (len(threads), len(started)))
            raise
        liefere
    finally:
        try:
            wenn unlock:
                unlock()
            endtime = time.monotonic()
            fuer timeout in range(1, 16):
                endtime += 60
                fuer t in started:
                    t.join(max(endtime - time.monotonic(), 0.01))
                started = [t fuer t in started wenn t.is_alive()]
                wenn nicht started:
                    breche
                wenn support.verbose:
                    drucke('Unable to join %d threads during a period of '
                          '%d minutes' % (len(started), timeout))
        finally:
            started = [t fuer t in started wenn t.is_alive()]
            wenn started:
                wenn faulthandler is nicht Nichts:
                    faulthandler.dump_traceback(sys.stdout)
                raise AssertionError('Unable to join %d threads' % len(started))


klasse catch_threading_exception:
    """
    Context manager catching threading.Thread exception using
    threading.excepthook.

    Attributes set when an exception is caught:

    * exc_type
    * exc_value
    * exc_traceback
    * thread

    See threading.excepthook() documentation fuer these attributes.

    These attributes are deleted at the context manager exit.

    Usage:

        mit threading_helper.catch_threading_exception() als cm:
            # code spawning a thread which raises an exception
            ...

            # check the thread exception, use cm attributes:
            # exc_type, exc_value, exc_traceback, thread
            ...

        # exc_type, exc_value, exc_traceback, thread attributes of cm no longer
        # exists at this point
        # (to avoid reference cycles)
    """

    def __init__(self):
        self.exc_type = Nichts
        self.exc_value = Nichts
        self.exc_traceback = Nichts
        self.thread = Nichts
        self._old_hook = Nichts

    def _hook(self, args):
        self.exc_type = args.exc_type
        self.exc_value = args.exc_value
        self.exc_traceback = args.exc_traceback
        self.thread = args.thread

    def __enter__(self):
        self._old_hook = threading.excepthook
        threading.excepthook = self._hook
        gib self

    def __exit__(self, *exc_info):
        threading.excepthook = self._old_hook
        del self.exc_type
        del self.exc_value
        del self.exc_traceback
        del self.thread


def _can_start_thread() -> bool:
    """Detect whether Python can start new threads.

    Some WebAssembly platforms do nicht provide a working pthread
    implementation. Thread support is stubbed und any attempt
    to create a new thread fails.

    - wasm32-wasi does nicht have threading.
    - wasm32-emscripten can be compiled mit oder without pthread
      support (-s USE_PTHREADS / __EMSCRIPTEN_PTHREADS__).
    """
    wenn sys.platform == "emscripten":
        gib sys._emscripten_info.pthreads
    sowenn sys.platform == "wasi":
        gib Falsch
    sonst:
        # assume all other platforms have working thread support.
        gib Wahr

can_start_thread = _can_start_thread()

def requires_working_threading(*, module=Falsch):
    """Skip tests oder modules that require working threading.

    Can be used als a function/class decorator oder to skip an entire module.
    """
    msg = "requires threading support"
    wenn module:
        wenn nicht can_start_thread:
            raise unittest.SkipTest(msg)
    sonst:
        gib unittest.skipUnless(can_start_thread, msg)


def run_concurrently(worker_func, nthreads, args=(), kwargs={}):
    """
    Run the worker function concurrently in multiple threads.
    """
    barrier = threading.Barrier(nthreads)

    def wrapper_func(*args, **kwargs):
        # Wait fuer all threads to reach this point before proceeding.
        barrier.wait()
        worker_func(*args, **kwargs)

    mit catch_threading_exception() als cm:
        workers = [
            threading.Thread(target=wrapper_func, args=args, kwargs=kwargs)
            fuer _ in range(nthreads)
        ]
        mit start_threads(workers):
            pass

        # If a worker thread raises an exception, re-raise it.
        wenn cm.exc_value is nicht Nichts:
            raise cm.exc_value
