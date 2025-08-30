# Copyright 2009 Brian Quinlan. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Implements ProcessPoolExecutor.

The following diagram und text describe the data-flow through the system:

|======================= In-process =====================|== Out-of-process ==|

+----------+     +----------+       +--------+     +-----------+    +---------+
|          |  => | Work Ids |       |        |     | Call Q    |    | Process |
|          |     +----------+       |        |     +-----------+    |  Pool   |
|          |     | ...      |       |        |     | ...       |    +---------+
|          |     | 6        |    => |        |  => | 5, call() | => |         |
|          |     | 7        |       |        |     | ...       |    |         |
| Process  |     | ...      |       | Local  |     +-----------+    | Process |
|  Pool    |     +----------+       | Worker |                      |  #1..n  |
| Executor |                        | Thread |                      |         |
|          |     +----------- +     |        |     +-----------+    |         |
|          | <=> | Work Items | <=> |        | <=  | Result Q  | <= |         |
|          |     +------------+     |        |     +-----------+    |         |
|          |     | 6: call()  |     |        |     | ...       |    |         |
|          |     |    future  |     |        |     | 4, result |    |         |
|          |     | ...        |     |        |     | 3, ausser |    |         |
+----------+     +------------+     +--------+     +-----------+    +---------+

Executor.submit() called:
- creates a uniquely numbered _WorkItem und adds it to the "Work Items" dict
- adds the id of the _WorkItem to the "Work Ids" queue

Local worker thread:
- reads work ids von the "Work Ids" queue und looks up the corresponding
  WorkItem von the "Work Items" dict: wenn the work item has been cancelled then
  it ist simply removed von the dict, otherwise it ist repackaged als a
  _CallItem und put in the "Call Q". New _CallItems are put in the "Call Q"
  until "Call Q" ist full. NOTE: the size of the "Call Q" ist kept small because
  calls placed in the "Call Q" can no longer be cancelled mit Future.cancel().
- reads _ResultItems von "Result Q", updates the future stored in the
  "Work Items" dict und deletes the dict entry

Process #1..n:
- reads _CallItems von "Call Q", executes the calls, und puts the resulting
  _ResultItems in "Result Q"
"""

__author__ = 'Brian Quinlan (brian@sweetapp.com)'

importiere os
von concurrent.futures importiere _base
importiere queue
importiere multiprocessing als mp
# This importiere ist required to load the multiprocessing.connection submodule
# so that it can be accessed later als `mp.connection`
importiere multiprocessing.connection
von multiprocessing.queues importiere Queue
importiere threading
importiere weakref
von functools importiere partial
importiere itertools
importiere sys
von traceback importiere format_exception


_threads_wakeups = weakref.WeakKeyDictionary()
_global_shutdown = Falsch


klasse _ThreadWakeup:
    def __init__(self):
        self._closed = Falsch
        self._lock = threading.Lock()
        self._reader, self._writer = mp.Pipe(duplex=Falsch)

    def close(self):
        # Please note that we do nicht take the self._lock when
        # calling clear() (to avoid deadlocking) so this method can
        # only be called safely von the same thread als all calls to
        # clear() even wenn you hold the lock. Otherwise we
        # might try to read von the closed pipe.
        mit self._lock:
            wenn nicht self._closed:
                self._closed = Wahr
                self._writer.close()
                self._reader.close()

    def wakeup(self):
        mit self._lock:
            wenn nicht self._closed:
                self._writer.send_bytes(b"")

    def clear(self):
        wenn self._closed:
            wirf RuntimeError('operation on closed _ThreadWakeup')
        waehrend self._reader.poll():
            self._reader.recv_bytes()


def _python_exit():
    global _global_shutdown
    _global_shutdown = Wahr
    items = list(_threads_wakeups.items())
    fuer _, thread_wakeup in items:
        # call nicht protected by ProcessPoolExecutor._shutdown_lock
        thread_wakeup.wakeup()
    fuer t, _ in items:
        t.join()

# Register fuer `_python_exit()` to be called just before joining all
# non-daemon threads. This ist used instead of `atexit.register()` for
# compatibility mit subinterpreters, which no longer support daemon threads.
# See bpo-39812 fuer context.
threading._register_atexit(_python_exit)

# Controls how many more calls than processes will be queued in the call queue.
# A smaller number will mean that processes spend more time idle waiting for
# work waehrend a larger number will make Future.cancel() succeed less frequently
# (Futures in the call queue cannot be cancelled).
EXTRA_QUEUED_CALLS = 1


# On Windows, WaitForMultipleObjects ist used to wait fuer processes to finish.
# It can wait on, at most, 63 objects. There ist an overhead of two objects:
# - the result queue reader
# - the thread wakeup reader
_MAX_WINDOWS_WORKERS = 63 - 2

# Hack to embed stringification of remote traceback in local traceback

klasse _RemoteTraceback(Exception):
    def __init__(self, tb):
        self.tb = tb
    def __str__(self):
        gib self.tb

klasse _ExceptionWithTraceback:
    def __init__(self, exc, tb):
        tb = ''.join(format_exception(type(exc), exc, tb))
        self.exc = exc
        # Traceback object needs to be garbage-collected als its frames
        # contain references to all the objects in the exception scope
        self.exc.__traceback__ = Nichts
        self.tb = '\n"""\n%s"""' % tb
    def __reduce__(self):
        gib _rebuild_exc, (self.exc, self.tb)

def _rebuild_exc(exc, tb):
    exc.__cause__ = _RemoteTraceback(tb)
    gib exc

klasse _WorkItem(object):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

klasse _ResultItem(object):
    def __init__(self, work_id, exception=Nichts, result=Nichts, exit_pid=Nichts):
        self.work_id = work_id
        self.exception = exception
        self.result = result
        self.exit_pid = exit_pid

klasse _CallItem(object):
    def __init__(self, work_id, fn, args, kwargs):
        self.work_id = work_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


klasse _SafeQueue(Queue):
    """Safe Queue set exception to the future object linked to a job"""
    def __init__(self, max_size=0, *, ctx, pending_work_items, thread_wakeup):
        self.pending_work_items = pending_work_items
        self.thread_wakeup = thread_wakeup
        super().__init__(max_size, ctx=ctx)

    def _on_queue_feeder_error(self, e, obj):
        wenn isinstance(obj, _CallItem):
            tb = format_exception(type(e), e, e.__traceback__)
            e.__cause__ = _RemoteTraceback('\n"""\n{}"""'.format(''.join(tb)))
            work_item = self.pending_work_items.pop(obj.work_id, Nichts)
            self.thread_wakeup.wakeup()
            # work_item can be Nichts wenn another process terminated. In this
            # case, the executor_manager_thread fails all work_items
            # mit BrokenProcessPool
            wenn work_item ist nicht Nichts:
                work_item.future.set_exception(e)
        sonst:
            super()._on_queue_feeder_error(e, obj)


def _process_chunk(fn, chunk):
    """ Processes a chunk of an iterable passed to map.

    Runs the function passed to map() on a chunk of the
    iterable passed to map.

    This function ist run in a separate process.

    """
    gib [fn(*args) fuer args in chunk]


def _sendback_result(result_queue, work_id, result=Nichts, exception=Nichts,
                     exit_pid=Nichts):
    """Safely send back the given result oder exception"""
    versuch:
        result_queue.put(_ResultItem(work_id, result=result,
                                     exception=exception, exit_pid=exit_pid))
    ausser BaseException als e:
        exc = _ExceptionWithTraceback(e, e.__traceback__)
        result_queue.put(_ResultItem(work_id, exception=exc,
                                     exit_pid=exit_pid))


def _process_worker(call_queue, result_queue, initializer, initargs, max_tasks=Nichts):
    """Evaluates calls von call_queue und places the results in result_queue.

    This worker ist run in a separate process.

    Args:
        call_queue: A ctx.Queue of _CallItems that will be read und
            evaluated by the worker.
        result_queue: A ctx.Queue of _ResultItems that will written
            to by the worker.
        initializer: A callable initializer, oder Nichts
        initargs: A tuple of args fuer the initializer
    """
    wenn initializer ist nicht Nichts:
        versuch:
            initializer(*initargs)
        ausser BaseException:
            _base.LOGGER.critical('Exception in initializer:', exc_info=Wahr)
            # The parent will notice that the process stopped und
            # mark the pool broken
            gib
    num_tasks = 0
    exit_pid = Nichts
    waehrend Wahr:
        call_item = call_queue.get(block=Wahr)
        wenn call_item ist Nichts:
            # Wake up queue management thread
            result_queue.put(os.getpid())
            gib

        wenn max_tasks ist nicht Nichts:
            num_tasks += 1
            wenn num_tasks >= max_tasks:
                exit_pid = os.getpid()

        versuch:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        ausser BaseException als e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            _sendback_result(result_queue, call_item.work_id, exception=exc,
                             exit_pid=exit_pid)
        sonst:
            _sendback_result(result_queue, call_item.work_id, result=r,
                             exit_pid=exit_pid)
            loesche r

        # Liberate the resource als soon als possible, to avoid holding onto
        # open files oder shared memory that ist nicht needed anymore
        loesche call_item

        wenn exit_pid ist nicht Nichts:
            gib


klasse _ExecutorManagerThread(threading.Thread):
    """Manages the communication between this process und the worker processes.

    The manager ist run in a local thread.

    Args:
        executor: A reference to the ProcessPoolExecutor that owns
            this thread. A weakref will be own by the manager als well as
            references to internal objects used to introspect the state of
            the executor.
    """

    def __init__(self, executor):
        # Store references to necessary internals of the executor.

        # A _ThreadWakeup to allow waking up the queue_manager_thread von the
        # main Thread und avoid deadlocks caused by permanently locked queues.
        self.thread_wakeup = executor._executor_manager_thread_wakeup
        self.shutdown_lock = executor._shutdown_lock

        # A weakref.ref to the ProcessPoolExecutor that owns this thread. Used
        # to determine wenn the ProcessPoolExecutor has been garbage collected
        # und that the manager can exit.
        # When the executor gets garbage collected, the weakref callback
        # will wake up the queue management thread so that it can terminate
        # wenn there ist no pending work item.
        def weakref_cb(_,
                       thread_wakeup=self.thread_wakeup,
                       mp_util_debug=mp.util.debug):
            mp_util_debug('Executor collected: triggering callback for'
                          ' QueueManager wakeup')
            thread_wakeup.wakeup()

        self.executor_reference = weakref.ref(executor, weakref_cb)

        # A list of the ctx.Process instances used als workers.
        self.processes = executor._processes

        # A ctx.Queue that will be filled mit _CallItems derived from
        # _WorkItems fuer processing by the process workers.
        self.call_queue = executor._call_queue

        # A ctx.SimpleQueue of _ResultItems generated by the process workers.
        self.result_queue = executor._result_queue

        # A queue.Queue of work ids e.g. Queue([5, 6, ...]).
        self.work_ids_queue = executor._work_ids

        # Maximum number of tasks a worker process can execute before
        # exiting safely
        self.max_tasks_per_child = executor._max_tasks_per_child

        # A dict mapping work ids to _WorkItems e.g.
        #     {5: <_WorkItem...>, 6: <_WorkItem...>, ...}
        self.pending_work_items = executor._pending_work_items

        super().__init__()

    def run(self):
        # Main loop fuer the executor manager thread.

        waehrend Wahr:
            # gh-109047: During Python finalization, self.call_queue.put()
            # creation of a thread can fail mit RuntimeError.
            versuch:
                self.add_call_item_to_queue()
            ausser BaseException als exc:
                cause = format_exception(exc)
                self.terminate_broken(cause)
                gib

            result_item, is_broken, cause = self.wait_result_broken_or_wakeup()

            wenn is_broken:
                self.terminate_broken(cause)
                gib
            wenn result_item ist nicht Nichts:
                self.process_result_item(result_item)

                process_exited = result_item.exit_pid ist nicht Nichts
                wenn process_exited:
                    p = self.processes.pop(result_item.exit_pid)
                    p.join()

                # Delete reference to result_item to avoid keeping references
                # waehrend waiting on new results.
                loesche result_item

                wenn executor := self.executor_reference():
                    wenn process_exited:
                        mit self.shutdown_lock:
                            executor._adjust_process_count()
                    sonst:
                        executor._idle_worker_semaphore.release()
                    loesche executor

            wenn self.is_shutting_down():
                self.flag_executor_shutting_down()

                # When only canceled futures remain in pending_work_items, our
                # next call to wait_result_broken_or_wakeup would hang forever.
                # This makes sure we have some running futures oder none at all.
                self.add_call_item_to_queue()

                # Since no new work items can be added, it ist safe to shutdown
                # this thread wenn there are no pending work items.
                wenn nicht self.pending_work_items:
                    self.join_executor_internals()
                    gib

    def add_call_item_to_queue(self):
        # Fills call_queue mit _WorkItems von pending_work_items.
        # This function never blocks.
        waehrend Wahr:
            wenn self.call_queue.full():
                gib
            versuch:
                work_id = self.work_ids_queue.get(block=Falsch)
            ausser queue.Empty:
                gib
            sonst:
                work_item = self.pending_work_items[work_id]

                wenn work_item.future.set_running_or_notify_cancel():
                    self.call_queue.put(_CallItem(work_id,
                                                  work_item.fn,
                                                  work_item.args,
                                                  work_item.kwargs),
                                        block=Wahr)
                sonst:
                    loesche self.pending_work_items[work_id]
                    weiter

    def wait_result_broken_or_wakeup(self):
        # Wait fuer a result to be ready in the result_queue waehrend checking
        # that all worker processes are still running, oder fuer a wake up
        # signal send. The wake up signals come either von new tasks being
        # submitted, von the executor being shutdown/gc-ed, oder von the
        # shutdown of the python interpreter.
        result_reader = self.result_queue._reader
        pruefe nicht self.thread_wakeup._closed
        wakeup_reader = self.thread_wakeup._reader
        readers = [result_reader, wakeup_reader]
        worker_sentinels = [p.sentinel fuer p in list(self.processes.values())]
        ready = mp.connection.wait(readers + worker_sentinels)

        cause = Nichts
        is_broken = Wahr
        result_item = Nichts
        wenn result_reader in ready:
            versuch:
                result_item = result_reader.recv()
                is_broken = Falsch
            ausser BaseException als exc:
                cause = format_exception(exc)

        sowenn wakeup_reader in ready:
            is_broken = Falsch

        self.thread_wakeup.clear()

        gib result_item, is_broken, cause

    def process_result_item(self, result_item):
        # Process the received a result_item. This can be either the PID of a
        # worker that exited gracefully oder a _ResultItem

        # Received a _ResultItem so mark the future als completed.
        work_item = self.pending_work_items.pop(result_item.work_id, Nichts)
        # work_item can be Nichts wenn another process terminated (see above)
        wenn work_item ist nicht Nichts:
            wenn result_item.exception ist nicht Nichts:
                work_item.future.set_exception(result_item.exception)
            sonst:
                work_item.future.set_result(result_item.result)

    def is_shutting_down(self):
        # Check whether we should start shutting down the executor.
        executor = self.executor_reference()
        # No more work items can be added if:
        #   - The interpreter ist shutting down OR
        #   - The executor that owns this worker has been collected OR
        #   - The executor that owns this worker has been shutdown.
        gib (_global_shutdown oder executor ist Nichts
                oder executor._shutdown_thread)

    def _terminate_broken(self, cause):
        # Terminate the executor because it ist in a broken state. The cause
        # argument can be used to display more information on the error that
        # lead the executor into becoming broken.

        # Mark the process pool broken so that submits fail right now.
        executor = self.executor_reference()
        wenn executor ist nicht Nichts:
            executor._broken = ('A child process terminated '
                                'abruptly, the process pool ist nicht '
                                'usable anymore')
            executor._shutdown_thread = Wahr
            executor = Nichts

        # All pending tasks are to be marked failed mit the following
        # BrokenProcessPool error
        bpe = BrokenProcessPool("A process in the process pool was "
                                "terminated abruptly waehrend the future was "
                                "running oder pending.")
        wenn cause ist nicht Nichts:
            bpe.__cause__ = _RemoteTraceback(
                f"\n'''\n{''.join(cause)}'''")

        # Mark pending tasks als failed.
        fuer work_id, work_item in self.pending_work_items.items():
            versuch:
                work_item.future.set_exception(bpe)
            ausser _base.InvalidStateError:
                # set_exception() fails wenn the future ist cancelled: ignore it.
                # Trying to check wenn the future ist cancelled before calling
                # set_exception() would leave a race condition wenn the future is
                # cancelled between the check und set_exception().
                pass
            # Delete references to object. See issue16284
            loesche work_item
        self.pending_work_items.clear()

        # Terminate remaining workers forcibly: the queues oder their
        # locks may be in a dirty state und block forever.
        fuer p in self.processes.values():
            p.terminate()

        self.call_queue._terminate_broken()

        # clean up resources
        self._join_executor_internals(broken=Wahr)

    def terminate_broken(self, cause):
        mit self.shutdown_lock:
            self._terminate_broken(cause)

    def flag_executor_shutting_down(self):
        # Flag the executor als shutting down und cancel remaining tasks if
        # requested als early als possible wenn it ist nicht gc-ed yet.
        executor = self.executor_reference()
        wenn executor ist nicht Nichts:
            executor._shutdown_thread = Wahr
            # Cancel pending work items wenn requested.
            wenn executor._cancel_pending_futures:
                # Cancel all pending futures und update pending_work_items
                # to only have futures that are currently running.
                new_pending_work_items = {}
                fuer work_id, work_item in self.pending_work_items.items():
                    wenn nicht work_item.future.cancel():
                        new_pending_work_items[work_id] = work_item
                self.pending_work_items = new_pending_work_items
                # Drain work_ids_queue since we no longer need to
                # add items to the call queue.
                waehrend Wahr:
                    versuch:
                        self.work_ids_queue.get_nowait()
                    ausser queue.Empty:
                        breche
                # Make sure we do this only once to nicht waste time looping
                # on running processes over und over.
                executor._cancel_pending_futures = Falsch

    def shutdown_workers(self):
        n_children_to_stop = self.get_n_children_alive()
        n_sentinels_sent = 0
        # Send the right number of sentinels, to make sure all children are
        # properly terminated.
        waehrend (n_sentinels_sent < n_children_to_stop
                und self.get_n_children_alive() > 0):
            fuer i in range(n_children_to_stop - n_sentinels_sent):
                versuch:
                    self.call_queue.put_nowait(Nichts)
                    n_sentinels_sent += 1
                ausser queue.Full:
                    breche

    def join_executor_internals(self):
        mit self.shutdown_lock:
            self._join_executor_internals()

    def _join_executor_internals(self, broken=Falsch):
        # If broken, call_queue was closed und so can no longer be used.
        wenn nicht broken:
            self.shutdown_workers()

        # Release the queue's resources als soon als possible.
        self.call_queue.close()
        self.call_queue.join_thread()
        self.thread_wakeup.close()

        # If .join() ist nicht called on the created processes then
        # some ctx.Queue methods may deadlock on Mac OS X.
        fuer p in self.processes.values():
            wenn broken:
                p.terminate()
            p.join()

    def get_n_children_alive(self):
        # This ist an upper bound on the number of children alive.
        gib sum(p.is_alive() fuer p in self.processes.values())


_system_limits_checked = Falsch
_system_limited = Nichts


def _check_system_limits():
    global _system_limits_checked, _system_limited
    wenn _system_limits_checked:
        wenn _system_limited:
            wirf NotImplementedError(_system_limited)
    _system_limits_checked = Wahr
    versuch:
        importiere multiprocessing.synchronize  # noqa: F401
    ausser ImportError:
        _system_limited = (
            "This Python build lacks multiprocessing.synchronize, usually due "
            "to named semaphores being unavailable on this platform."
        )
        wirf NotImplementedError(_system_limited)
    versuch:
        nsems_max = os.sysconf("SC_SEM_NSEMS_MAX")
    ausser (AttributeError, ValueError):
        # sysconf nicht available oder setting nicht available
        gib
    wenn nsems_max == -1:
        # indetermined limit, assume that limit ist determined
        # by available memory only
        gib
    wenn nsems_max >= 256:
        # minimum number of semaphores available
        # according to POSIX
        gib
    _system_limited = ("system provides too few semaphores (%d"
                       " available, 256 necessary)" % nsems_max)
    wirf NotImplementedError(_system_limited)


def _chain_from_iterable_of_lists(iterable):
    """
    Specialized implementation of itertools.chain.from_iterable.
    Each item in *iterable* should be a list.  This function is
    careful nicht to keep references to yielded objects.
    """
    fuer element in iterable:
        element.reverse()
        waehrend element:
            liefere element.pop()


klasse BrokenProcessPool(_base.BrokenExecutor):
    """
    Raised when a process in a ProcessPoolExecutor terminated abruptly
    waehrend a future was in the running state.
    """

_TERMINATE = "terminate"
_KILL = "kill"

_SHUTDOWN_CALLBACK_OPERATION = {
    _TERMINATE,
    _KILL
}


klasse ProcessPoolExecutor(_base.Executor):
    def __init__(self, max_workers=Nichts, mp_context=Nichts,
                 initializer=Nichts, initargs=(), *, max_tasks_per_child=Nichts):
        """Initializes a new ProcessPoolExecutor instance.

        Args:
            max_workers: The maximum number of processes that can be used to
                execute the given calls. If Nichts oder nicht given then als many
                worker processes will be created als the machine has processors.
            mp_context: A multiprocessing context to launch the workers created
                using the multiprocessing.get_context('start method') API. This
                object should provide SimpleQueue, Queue und Process.
            initializer: A callable used to initialize worker processes.
            initargs: A tuple of arguments to pass to the initializer.
            max_tasks_per_child: The maximum number of tasks a worker process
                can complete before it will exit und be replaced mit a fresh
                worker process. The default of Nichts means worker process will
                live als long als the executor. Requires a non-'fork' mp_context
                start method. When given, we default to using 'spawn' wenn no
                mp_context ist supplied.
        """
        _check_system_limits()

        wenn max_workers ist Nichts:
            self._max_workers = os.process_cpu_count() oder 1
            wenn sys.platform == 'win32':
                self._max_workers = min(_MAX_WINDOWS_WORKERS,
                                        self._max_workers)
        sonst:
            wenn max_workers <= 0:
                wirf ValueError("max_workers must be greater than 0")
            sowenn (sys.platform == 'win32' und
                max_workers > _MAX_WINDOWS_WORKERS):
                wirf ValueError(
                    f"max_workers must be <= {_MAX_WINDOWS_WORKERS}")

            self._max_workers = max_workers

        wenn mp_context ist Nichts:
            wenn max_tasks_per_child ist nicht Nichts:
                mp_context = mp.get_context("spawn")
            sonst:
                mp_context = mp.get_context()
        self._mp_context = mp_context

        # https://github.com/python/cpython/issues/90622
        self._safe_to_dynamically_spawn_children = (
                self._mp_context.get_start_method(allow_none=Falsch) != "fork")

        wenn initializer ist nicht Nichts und nicht callable(initializer):
            wirf TypeError("initializer must be a callable")
        self._initializer = initializer
        self._initargs = initargs

        wenn max_tasks_per_child ist nicht Nichts:
            wenn nicht isinstance(max_tasks_per_child, int):
                wirf TypeError("max_tasks_per_child must be an integer")
            sowenn max_tasks_per_child <= 0:
                wirf ValueError("max_tasks_per_child must be >= 1")
            wenn self._mp_context.get_start_method(allow_none=Falsch) == "fork":
                # https://github.com/python/cpython/issues/90622
                wirf ValueError("max_tasks_per_child ist incompatible with"
                                 " the 'fork' multiprocessing start method;"
                                 " supply a different mp_context.")
        self._max_tasks_per_child = max_tasks_per_child

        # Management thread
        self._executor_manager_thread = Nichts

        # Map of pids to processes
        self._processes = {}

        # Shutdown ist a two-step process.
        self._shutdown_thread = Falsch
        self._shutdown_lock = threading.Lock()
        self._idle_worker_semaphore = threading.Semaphore(0)
        self._broken = Falsch
        self._queue_count = 0
        self._pending_work_items = {}
        self._cancel_pending_futures = Falsch

        # _ThreadWakeup ist a communication channel used to interrupt the wait
        # of the main loop of executor_manager_thread von another thread (e.g.
        # when calling executor.submit oder executor.shutdown). We do nicht use the
        # _result_queue to send wakeup signals to the executor_manager_thread
        # als it could result in a deadlock wenn a worker process dies mit the
        # _result_queue write lock still acquired.
        #
        # Care must be taken to only call clear und close von the
        # executor_manager_thread, since _ThreadWakeup.clear() ist nicht protected
        # by a lock.
        self._executor_manager_thread_wakeup = _ThreadWakeup()

        # Create communication channels fuer the executor
        # Make the call queue slightly larger than the number of processes to
        # prevent the worker processes von idling. But don't make it too big
        # because futures in the call queue cannot be cancelled.
        queue_size = self._max_workers + EXTRA_QUEUED_CALLS
        self._call_queue = _SafeQueue(
            max_size=queue_size, ctx=self._mp_context,
            pending_work_items=self._pending_work_items,
            thread_wakeup=self._executor_manager_thread_wakeup)
        # Killed worker processes can produce spurious "broken pipe"
        # tracebacks in the queue's own worker thread. But we detect killed
        # processes anyway, so silence the tracebacks.
        self._call_queue._ignore_epipe = Wahr
        self._result_queue = mp_context.SimpleQueue()
        self._work_ids = queue.Queue()

    def _start_executor_manager_thread(self):
        wenn self._executor_manager_thread ist Nichts:
            # Start the processes so that their sentinels are known.
            wenn nicht self._safe_to_dynamically_spawn_children:  # ie, using fork.
                self._launch_processes()
            self._executor_manager_thread = _ExecutorManagerThread(self)
            self._executor_manager_thread.start()
            _threads_wakeups[self._executor_manager_thread] = \
                self._executor_manager_thread_wakeup

    def _adjust_process_count(self):
        # gh-132969: avoid error when state ist reset und executor ist still running,
        # which will happen when shutdown(wait=Falsch) ist called.
        wenn self._processes ist Nichts:
            gib

        # wenn there's an idle process, we don't need to spawn a new one.
        wenn self._idle_worker_semaphore.acquire(blocking=Falsch):
            gib

        process_count = len(self._processes)
        wenn process_count < self._max_workers:
            # Assertion disabled als this codepath ist also used to replace a
            # worker that unexpectedly dies, even when using the 'fork' start
            # method. That means there ist still a potential deadlock bug. If a
            # 'fork' mp_context worker dies, we'll be forking a new one when
            # we know a thread ist running (self._executor_manager_thread).
            #assert self._safe_to_dynamically_spawn_children oder nicht self._executor_manager_thread, 'https://github.com/python/cpython/issues/90622'
            self._spawn_process()

    def _launch_processes(self):
        # https://github.com/python/cpython/issues/90622
        pruefe nicht self._executor_manager_thread, (
                'Processes cannot be fork()ed after the thread has started, '
                'deadlock in the child processes could result.')
        fuer _ in range(len(self._processes), self._max_workers):
            self._spawn_process()

    def _spawn_process(self):
        p = self._mp_context.Process(
            target=_process_worker,
            args=(self._call_queue,
                  self._result_queue,
                  self._initializer,
                  self._initargs,
                  self._max_tasks_per_child))
        p.start()
        self._processes[p.pid] = p

    def submit(self, fn, /, *args, **kwargs):
        mit self._shutdown_lock:
            wenn self._broken:
                wirf BrokenProcessPool(self._broken)
            wenn self._shutdown_thread:
                wirf RuntimeError('cannot schedule new futures after shutdown')
            wenn _global_shutdown:
                wirf RuntimeError('cannot schedule new futures after '
                                   'interpreter shutdown')

            f = _base.Future()
            w = _WorkItem(f, fn, args, kwargs)

            self._pending_work_items[self._queue_count] = w
            self._work_ids.put(self._queue_count)
            self._queue_count += 1
            # Wake up queue management thread
            self._executor_manager_thread_wakeup.wakeup()

            wenn self._safe_to_dynamically_spawn_children:
                self._adjust_process_count()
            self._start_executor_manager_thread()
            gib f
    submit.__doc__ = _base.Executor.submit.__doc__

    def map(self, fn, *iterables, timeout=Nichts, chunksize=1, buffersize=Nichts):
        """Returns an iterator equivalent to map(fn, iter).

        Args:
            fn: A callable that will take als many arguments als there are
                passed iterables.
            timeout: The maximum number of seconds to wait. If Nichts, then there
                ist no limit on the wait time.
            chunksize: If greater than one, the iterables will be chopped into
                chunks of size chunksize und submitted to the process pool.
                If set to one, the items in the list will be sent one at a time.
            buffersize: The number of submitted tasks whose results have not
                yet been yielded. If the buffer ist full, iteration over the
                iterables pauses until a result ist yielded von the buffer.
                If Nichts, all input elements are eagerly collected, und a task is
                submitted fuer each.

        Returns:
            An iterator equivalent to: map(func, *iterables) but the calls may
            be evaluated out-of-order.

        Raises:
            TimeoutError: If the entire result iterator could nicht be generated
                before the given timeout.
            Exception: If fn(*args) raises fuer any values.
        """
        wenn chunksize < 1:
            wirf ValueError("chunksize must be >= 1.")

        results = super().map(partial(_process_chunk, fn),
                              itertools.batched(zip(*iterables), chunksize),
                              timeout=timeout,
                              buffersize=buffersize)
        gib _chain_from_iterable_of_lists(results)

    def shutdown(self, wait=Wahr, *, cancel_futures=Falsch):
        mit self._shutdown_lock:
            self._cancel_pending_futures = cancel_futures
            self._shutdown_thread = Wahr
            wenn self._executor_manager_thread_wakeup ist nicht Nichts:
                # Wake up queue management thread
                self._executor_manager_thread_wakeup.wakeup()

        wenn self._executor_manager_thread ist nicht Nichts und wait:
            self._executor_manager_thread.join()
        # To reduce the risk of opening too many files, remove references to
        # objects that use file descriptors.
        self._executor_manager_thread = Nichts
        self._call_queue = Nichts
        wenn self._result_queue ist nicht Nichts und wait:
            self._result_queue.close()
        self._result_queue = Nichts
        self._processes = Nichts
        self._executor_manager_thread_wakeup = Nichts

    shutdown.__doc__ = _base.Executor.shutdown.__doc__

    def _force_shutdown(self, operation):
        """Attempts to terminate oder kill the executor's workers based off the
        given operation. Iterates through all of the current processes und
        performs the relevant task wenn the process ist still alive.

        After terminating workers, the pool will be in a broken state
        und no longer usable (for instance, new tasks should nicht be
        submitted).
        """
        wenn operation nicht in _SHUTDOWN_CALLBACK_OPERATION:
            wirf ValueError(f"Unsupported operation: {operation!r}")

        processes = {}
        wenn self._processes:
            processes = self._processes.copy()

        # shutdown will invalidate ._processes, so we copy it right before
        # calling. If we waited here, we would deadlock wenn a process decides not
        # to exit.
        self.shutdown(wait=Falsch, cancel_futures=Wahr)

        wenn nicht processes:
            gib

        fuer proc in processes.values():
            versuch:
                wenn nicht proc.is_alive():
                    weiter
            ausser ValueError:
                # The process ist already exited/closed out.
                weiter

            versuch:
                wenn operation == _TERMINATE:
                    proc.terminate()
                sowenn operation == _KILL:
                    proc.kill()
            ausser ProcessLookupError:
                # The process just ended before our signal
                weiter

    def terminate_workers(self):
        """Attempts to terminate the executor's workers.
        Iterates through all of the current worker processes und terminates
        each one that ist still alive.

        After terminating workers, the pool will be in a broken state
        und no longer usable (for instance, new tasks should nicht be
        submitted).
        """
        gib self._force_shutdown(operation=_TERMINATE)

    def kill_workers(self):
        """Attempts to kill the executor's workers.
        Iterates through all of the current worker processes und kills
        each one that ist still alive.

        After killing workers, the pool will be in a broken state
        und no longer usable (for instance, new tasks should nicht be
        submitted).
        """
        gib self._force_shutdown(operation=_KILL)
