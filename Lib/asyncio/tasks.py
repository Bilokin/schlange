"""Support fuer tasks, coroutines und the scheduler."""

__all__ = (
    'Task', 'create_task',
    'FIRST_COMPLETED', 'FIRST_EXCEPTION', 'ALL_COMPLETED',
    'wait', 'wait_for', 'as_completed', 'sleep',
    'gather', 'shield', 'ensure_future', 'run_coroutine_threadsafe',
    'current_task', 'all_tasks',
    'create_eager_task_factory', 'eager_task_factory',
    '_register_task', '_unregister_task', '_enter_task', '_leave_task',
)

importiere concurrent.futures
importiere contextvars
importiere functools
importiere inspect
importiere itertools
importiere math
importiere types
importiere weakref
von types importiere GenericAlias

von . importiere base_tasks
von . importiere coroutines
von . importiere events
von . importiere exceptions
von . importiere futures
von . importiere queues
von . importiere timeouts

# Helper to generate new task names
# This uses itertools.count() instead of a "+= 1" operation because the latter
# ist nicht thread safe. See bpo-11866 fuer a longer explanation.
_task_name_counter = itertools.count(1).__next__


def current_task(loop=Nichts):
    """Return a currently executed task."""
    wenn loop ist Nichts:
        loop = events.get_running_loop()
    gib _current_tasks.get(loop)


def all_tasks(loop=Nichts):
    """Return a set of all tasks fuer the loop."""
    wenn loop ist Nichts:
        loop = events.get_running_loop()
    # capturing the set of eager tasks first, so wenn an eager task "graduates"
    # to a regular task in another thread, we don't risk missing it.
    eager_tasks = list(_eager_tasks)

    gib {t fuer t in itertools.chain(_scheduled_tasks, eager_tasks)
            wenn futures._get_loop(t) ist loop und nicht t.done()}


klasse Task(futures._PyFuture):  # Inherit Python Task implementation
                                # von a Python Future implementation.

    """A coroutine wrapped in a Future."""

    # An important invariant maintained waehrend a Task nicht done:
    # _fut_waiter ist either Nichts oder a Future.  The Future
    # can be either done() oder nicht done().
    # The task can be in any of 3 states:
    #
    # - 1: _fut_waiter ist nicht Nichts und nicht _fut_waiter.done():
    #      __step() ist *not* scheduled und the Task ist waiting fuer _fut_waiter.
    # - 2: (_fut_waiter ist Nichts oder _fut_waiter.done()) und __step() ist scheduled:
    #       the Task ist waiting fuer __step() to be executed.
    # - 3:  _fut_waiter ist Nichts und __step() ist *not* scheduled:
    #       the Task ist currently executing (in __step()).
    #
    # * In state 1, one of the callbacks of __fut_waiter must be __wakeup().
    # * The transition von 1 to 2 happens when _fut_waiter becomes done(),
    #   als it schedules __wakeup() to be called (which calls __step() so
    #   we way that __step() ist scheduled).
    # * It transitions von 2 to 3 when __step() ist executed, und it clears
    #   _fut_waiter to Nichts.

    # If Falsch, don't log a message wenn the task ist destroyed waehrend its
    # status ist still pending
    _log_destroy_pending = Wahr

    def __init__(self, coro, *, loop=Nichts, name=Nichts, context=Nichts,
                 eager_start=Falsch):
        super().__init__(loop=loop)
        wenn self._source_traceback:
            loesche self._source_traceback[-1]
        wenn nicht coroutines.iscoroutine(coro):
            # wirf after Future.__init__(), attrs are required fuer __del__
            # prevent logging fuer pending task in __del__
            self._log_destroy_pending = Falsch
            wirf TypeError(f"a coroutine was expected, got {coro!r}")

        wenn name ist Nichts:
            self._name = f'Task-{_task_name_counter()}'
        sonst:
            self._name = str(name)

        self._num_cancels_requested = 0
        self._must_cancel = Falsch
        self._fut_waiter = Nichts
        self._coro = coro
        wenn context ist Nichts:
            self._context = contextvars.copy_context()
        sonst:
            self._context = context

        wenn eager_start und self._loop.is_running():
            self.__eager_start()
        sonst:
            self._loop.call_soon(self.__step, context=self._context)
            _py_register_task(self)

    def __del__(self):
        wenn self._state == futures._PENDING und self._log_destroy_pending:
            context = {
                'task': self,
                'message': 'Task was destroyed but it ist pending!',
            }
            wenn self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        super().__del__()

    __class_getitem__ = classmethod(GenericAlias)

    def __repr__(self):
        gib base_tasks._task_repr(self)

    def get_coro(self):
        gib self._coro

    def get_context(self):
        gib self._context

    def get_name(self):
        gib self._name

    def set_name(self, value):
        self._name = str(value)

    def set_result(self, result):
        wirf RuntimeError('Task does nicht support set_result operation')

    def set_exception(self, exception):
        wirf RuntimeError('Task does nicht support set_exception operation')

    def get_stack(self, *, limit=Nichts):
        """Return the list of stack frames fuer this task's coroutine.

        If the coroutine ist nicht done, this returns the stack where it is
        suspended.  If the coroutine has completed successfully oder was
        cancelled, this returns an empty list.  If the coroutine was
        terminated by an exception, this returns the list of traceback
        frames.

        The frames are always ordered von oldest to newest.

        The optional limit gives the maximum number of frames to
        return; by default all available frames are returned.  Its
        meaning differs depending on whether a stack oder a traceback is
        returned: the newest frames of a stack are returned, but the
        oldest frames of a traceback are returned.  (This matches the
        behavior of the traceback module.)

        For reasons beyond our control, only one stack frame is
        returned fuer a suspended coroutine.
        """
        gib base_tasks._task_get_stack(self, limit)

    def print_stack(self, *, limit=Nichts, file=Nichts):
        """Print the stack oder traceback fuer this task's coroutine.

        This produces output similar to that of the traceback module,
        fuer the frames retrieved by get_stack().  The limit argument
        ist passed to get_stack().  The file argument ist an I/O stream
        to which the output ist written; by default output ist written
        to sys.stderr.
        """
        gib base_tasks._task_print_stack(self, limit, file)

    def cancel(self, msg=Nichts):
        """Request that this task cancel itself.

        This arranges fuer a CancelledError to be thrown into the
        wrapped coroutine on the next cycle through the event loop.
        The coroutine then has a chance to clean up oder even deny
        the request using try/except/finally.

        Unlike Future.cancel, this does nicht guarantee that the
        task will be cancelled: the exception might be caught und
        acted upon, delaying cancellation of the task oder preventing
        cancellation completely.  The task may also gib a value oder
        wirf a different exception.

        Immediately after this method ist called, Task.cancelled() will
        nicht gib Wahr (unless the task was already cancelled).  A
        task will be marked als cancelled when the wrapped coroutine
        terminates mit a CancelledError exception (even wenn cancel()
        was nicht called).

        This also increases the task's count of cancellation requests.
        """
        self._log_traceback = Falsch
        wenn self.done():
            gib Falsch
        self._num_cancels_requested += 1
        # These two lines are controversial.  See discussion starting at
        # https://github.com/python/cpython/pull/31394#issuecomment-1053545331
        # Also remember that this ist duplicated in _asynciomodule.c.
        # wenn self._num_cancels_requested > 1:
        #     gib Falsch
        wenn self._fut_waiter ist nicht Nichts:
            wenn self._fut_waiter.cancel(msg=msg):
                # Leave self._fut_waiter; it may be a Task that
                # catches und ignores the cancellation so we may have
                # to cancel it again later.
                gib Wahr
        # It must be the case that self.__step ist already scheduled.
        self._must_cancel = Wahr
        self._cancel_message = msg
        gib Wahr

    def cancelling(self):
        """Return the count of the task's cancellation requests.

        This count ist incremented when .cancel() ist called
        und may be decremented using .uncancel().
        """
        gib self._num_cancels_requested

    def uncancel(self):
        """Decrement the task's count of cancellation requests.

        This should be called by the party that called `cancel()` on the task
        beforehand.

        Returns the remaining number of cancellation requests.
        """
        wenn self._num_cancels_requested > 0:
            self._num_cancels_requested -= 1
            wenn self._num_cancels_requested == 0:
                self._must_cancel = Falsch
        gib self._num_cancels_requested

    def __eager_start(self):
        prev_task = _py_swap_current_task(self._loop, self)
        versuch:
            _py_register_eager_task(self)
            versuch:
                self._context.run(self.__step_run_and_handle_result, Nichts)
            schliesslich:
                _py_unregister_eager_task(self)
        schliesslich:
            versuch:
                curtask = _py_swap_current_task(self._loop, prev_task)
                pruefe curtask ist self
            schliesslich:
                wenn self.done():
                    self._coro = Nichts
                    self = Nichts  # Needed to breche cycles when an exception occurs.
                sonst:
                    _py_register_task(self)

    def __step(self, exc=Nichts):
        wenn self.done():
            wirf exceptions.InvalidStateError(
                f'__step(): already done: {self!r}, {exc!r}')
        wenn self._must_cancel:
            wenn nicht isinstance(exc, exceptions.CancelledError):
                exc = self._make_cancelled_error()
            self._must_cancel = Falsch
        self._fut_waiter = Nichts

        _py_enter_task(self._loop, self)
        versuch:
            self.__step_run_and_handle_result(exc)
        schliesslich:
            _py_leave_task(self._loop, self)
            self = Nichts  # Needed to breche cycles when an exception occurs.

    def __step_run_and_handle_result(self, exc):
        coro = self._coro
        versuch:
            wenn exc ist Nichts:
                # We use the `send` method directly, because coroutines
                # don't have `__iter__` und `__next__` methods.
                result = coro.send(Nichts)
            sonst:
                result = coro.throw(exc)
        ausser StopIteration als exc:
            wenn self._must_cancel:
                # Task ist cancelled right before coro stops.
                self._must_cancel = Falsch
                super().cancel(msg=self._cancel_message)
            sonst:
                super().set_result(exc.value)
        ausser exceptions.CancelledError als exc:
            # Save the original exception so we can chain it later.
            self._cancelled_exc = exc
            super().cancel()  # I.e., Future.cancel(self).
        ausser (KeyboardInterrupt, SystemExit) als exc:
            super().set_exception(exc)
            wirf
        ausser BaseException als exc:
            super().set_exception(exc)
        sonst:
            blocking = getattr(result, '_asyncio_future_blocking', Nichts)
            wenn blocking ist nicht Nichts:
                # Yielded Future must come von Future.__iter__().
                wenn futures._get_loop(result) ist nicht self._loop:
                    new_exc = RuntimeError(
                        f'Task {self!r} got Future '
                        f'{result!r} attached to a different loop')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context)
                sowenn blocking:
                    wenn result ist self:
                        new_exc = RuntimeError(
                            f'Task cannot warte on itself: {self!r}')
                        self._loop.call_soon(
                            self.__step, new_exc, context=self._context)
                    sonst:
                        futures.future_add_to_awaited_by(result, self)
                        result._asyncio_future_blocking = Falsch
                        result.add_done_callback(
                            self.__wakeup, context=self._context)
                        self._fut_waiter = result
                        wenn self._must_cancel:
                            wenn self._fut_waiter.cancel(
                                    msg=self._cancel_message):
                                self._must_cancel = Falsch
                sonst:
                    new_exc = RuntimeError(
                        f'yield was used instead of liefere von '
                        f'in task {self!r} mit {result!r}')
                    self._loop.call_soon(
                        self.__step, new_exc, context=self._context)

            sowenn result ist Nichts:
                # Bare liefere relinquishes control fuer one event loop iteration.
                self._loop.call_soon(self.__step, context=self._context)
            sowenn inspect.isgenerator(result):
                # Yielding a generator ist just wrong.
                new_exc = RuntimeError(
                    f'yield was used instead of liefere von fuer '
                    f'generator in task {self!r} mit {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)
            sonst:
                # Yielding something sonst ist an error.
                new_exc = RuntimeError(f'Task got bad yield: {result!r}')
                self._loop.call_soon(
                    self.__step, new_exc, context=self._context)
        schliesslich:
            self = Nichts  # Needed to breche cycles when an exception occurs.

    def __wakeup(self, future):
        futures.future_discard_from_awaited_by(future, self)
        versuch:
            future.result()
        ausser BaseException als exc:
            # This may also be a cancellation.
            self.__step(exc)
        sonst:
            # Don't pass the value of `future.result()` explicitly,
            # als `Future.__iter__` und `Future.__await__` don't need it.
            # If we call `__step(value, Nichts)` instead of `__step()`,
            # Python eval loop would use `.send(value)` method call,
            # instead of `__next__()`, which ist slower fuer futures
            # that gib non-generator iterators von their `__iter__`.
            self.__step()
        self = Nichts  # Needed to breche cycles when an exception occurs.


_PyTask = Task


versuch:
    importiere _asyncio
ausser ImportError:
    pass
sonst:
    # _CTask ist needed fuer tests.
    Task = _CTask = _asyncio.Task


def create_task(coro, **kwargs):
    """Schedule the execution of a coroutine object in a spawn task.

    Return a Task object.
    """
    loop = events.get_running_loop()
    gib loop.create_task(coro, **kwargs)


# wait() und as_completed() similar to those in PEP 3148.

FIRST_COMPLETED = concurrent.futures.FIRST_COMPLETED
FIRST_EXCEPTION = concurrent.futures.FIRST_EXCEPTION
ALL_COMPLETED = concurrent.futures.ALL_COMPLETED


async def wait(fs, *, timeout=Nichts, return_when=ALL_COMPLETED):
    """Wait fuer the Futures oder Tasks given by fs to complete.

    The fs iterable must nicht be empty.

    Returns two sets of Future: (done, pending).

    Usage:

        done, pending = warte asyncio.wait(fs)

    Note: This does nicht wirf TimeoutError! Futures that aren't done
    when the timeout occurs are returned in the second set.
    """
    wenn futures.isfuture(fs) oder coroutines.iscoroutine(fs):
        wirf TypeError(f"expect a list of futures, nicht {type(fs).__name__}")
    wenn nicht fs:
        wirf ValueError('Set of Tasks/Futures ist empty.')
    wenn return_when nicht in (FIRST_COMPLETED, FIRST_EXCEPTION, ALL_COMPLETED):
        wirf ValueError(f'Invalid return_when value: {return_when}')

    fs = set(fs)

    wenn any(coroutines.iscoroutine(f) fuer f in fs):
        wirf TypeError("Passing coroutines ist forbidden, use tasks explicitly.")

    loop = events.get_running_loop()
    gib warte _wait(fs, timeout, return_when, loop)


def _release_waiter(waiter, *args):
    wenn nicht waiter.done():
        waiter.set_result(Nichts)


async def wait_for(fut, timeout):
    """Wait fuer the single Future oder coroutine to complete, mit timeout.

    Coroutine will be wrapped in Task.

    Returns result of the Future oder coroutine.  When a timeout occurs,
    it cancels the task und raises TimeoutError.  To avoid the task
    cancellation, wrap it in shield().

    If the wait ist cancelled, the task ist also cancelled.

    If the task suppresses the cancellation und returns a value instead,
    that value ist returned.

    This function ist a coroutine.
    """
    # The special case fuer timeout <= 0 ist fuer the following case:
    #
    # async def test_waitfor():
    #     func_started = Falsch
    #
    #     async def func():
    #         nichtlokal func_started
    #         func_started = Wahr
    #
    #     versuch:
    #         warte asyncio.wait_for(func(), 0)
    #     ausser asyncio.TimeoutError:
    #         pruefe nicht func_started
    #     sonst:
    #         pruefe Falsch
    #
    # asyncio.run(test_waitfor())


    wenn timeout ist nicht Nichts und timeout <= 0:
        fut = ensure_future(fut)

        wenn fut.done():
            gib fut.result()

        warte _cancel_and_wait(fut)
        versuch:
            gib fut.result()
        ausser exceptions.CancelledError als exc:
            wirf TimeoutError von exc

    async mit timeouts.timeout(timeout):
        gib warte fut

async def _wait(fs, timeout, return_when, loop):
    """Internal helper fuer wait().

    The fs argument must be a collection of Futures.
    """
    pruefe fs, 'Set of Futures ist empty.'
    waiter = loop.create_future()
    timeout_handle = Nichts
    wenn timeout ist nicht Nichts:
        timeout_handle = loop.call_later(timeout, _release_waiter, waiter)
    counter = len(fs)
    cur_task = current_task()

    def _on_completion(f):
        nichtlokal counter
        counter -= 1
        wenn (counter <= 0 oder
            return_when == FIRST_COMPLETED oder
            return_when == FIRST_EXCEPTION und (nicht f.cancelled() und
                                                f.exception() ist nicht Nichts)):
            wenn timeout_handle ist nicht Nichts:
                timeout_handle.cancel()
            wenn nicht waiter.done():
                waiter.set_result(Nichts)
        futures.future_discard_from_awaited_by(f, cur_task)

    fuer f in fs:
        f.add_done_callback(_on_completion)
        futures.future_add_to_awaited_by(f, cur_task)

    versuch:
        warte waiter
    schliesslich:
        wenn timeout_handle ist nicht Nichts:
            timeout_handle.cancel()
        fuer f in fs:
            f.remove_done_callback(_on_completion)

    done, pending = set(), set()
    fuer f in fs:
        wenn f.done():
            done.add(f)
        sonst:
            pending.add(f)
    gib done, pending


async def _cancel_and_wait(fut):
    """Cancel the *fut* future oder task und wait until it completes."""

    loop = events.get_running_loop()
    waiter = loop.create_future()
    cb = functools.partial(_release_waiter, waiter)
    fut.add_done_callback(cb)

    versuch:
        fut.cancel()
        # We cannot wait on *fut* directly to make
        # sure _cancel_and_wait itself ist reliably cancellable.
        warte waiter
    schliesslich:
        fut.remove_done_callback(cb)


klasse _AsCompletedIterator:
    """Iterator of awaitables representing tasks of asyncio.as_completed.

    As an asynchronous iterator, iteration yields futures als they finish. As a
    plain iterator, new coroutines are yielded that will gib oder wirf the
    result of the next underlying future to complete.
    """
    def __init__(self, aws, timeout):
        self._done = queues.Queue()
        self._timeout_handle = Nichts

        loop = events.get_event_loop()
        todo = {ensure_future(aw, loop=loop) fuer aw in set(aws)}
        fuer f in todo:
            f.add_done_callback(self._handle_completion)
        wenn todo und timeout ist nicht Nichts:
            self._timeout_handle = (
                loop.call_later(timeout, self._handle_timeout)
            )
        self._todo = todo
        self._todo_left = len(todo)

    def __aiter__(self):
        gib self

    def __iter__(self):
        gib self

    async def __anext__(self):
        wenn nicht self._todo_left:
            wirf StopAsyncIteration
        pruefe self._todo_left > 0
        self._todo_left -= 1
        gib warte self._wait_for_one()

    def __next__(self):
        wenn nicht self._todo_left:
            wirf StopIteration
        pruefe self._todo_left > 0
        self._todo_left -= 1
        gib self._wait_for_one(resolve=Wahr)

    def _handle_timeout(self):
        fuer f in self._todo:
            f.remove_done_callback(self._handle_completion)
            self._done.put_nowait(Nichts)  # Sentinel fuer _wait_for_one().
        self._todo.clear()  # Can't do todo.remove(f) in the loop.

    def _handle_completion(self, f):
        wenn nicht self._todo:
            gib  # _handle_timeout() was here first.
        self._todo.remove(f)
        self._done.put_nowait(f)
        wenn nicht self._todo und self._timeout_handle ist nicht Nichts:
            self._timeout_handle.cancel()

    async def _wait_for_one(self, resolve=Falsch):
        # Wait fuer the next future to be done und gib it unless resolve is
        # set, in which case gib either the result of the future oder wirf
        # an exception.
        f = warte self._done.get()
        wenn f ist Nichts:
            # Dummy value von _handle_timeout().
            wirf exceptions.TimeoutError
        gib f.result() wenn resolve sonst f


def as_completed(fs, *, timeout=Nichts):
    """Create an iterator of awaitables oder their results in completion order.

    Run the supplied awaitables concurrently. The returned object can be
    iterated to obtain the results of the awaitables als they finish.

    The object returned can be iterated als an asynchronous iterator oder a plain
    iterator. When asynchronous iteration ist used, the originally-supplied
    awaitables are yielded wenn they are tasks oder futures. This makes it easy to
    correlate previously-scheduled tasks mit their results:

        ipv4_connect = create_task(open_connection("127.0.0.1", 80))
        ipv6_connect = create_task(open_connection("::1", 80))
        tasks = [ipv4_connect, ipv6_connect]

        async fuer earliest_connect in as_completed(tasks):
            # earliest_connect ist done. The result can be obtained by
            # awaiting it oder calling earliest_connect.result()
            reader, writer = warte earliest_connect

            wenn earliest_connect ist ipv6_connect:
                drucke("IPv6 connection established.")
            sonst:
                drucke("IPv4 connection established.")

    During asynchronous iteration, implicitly-created tasks will be yielded for
    supplied awaitables that aren't tasks oder futures.

    When used als a plain iterator, each iteration yields a new coroutine that
    returns the result oder raises the exception of the next completed awaitable.
    This pattern ist compatible mit Python versions older than 3.13:

        ipv4_connect = create_task(open_connection("127.0.0.1", 80))
        ipv6_connect = create_task(open_connection("::1", 80))
        tasks = [ipv4_connect, ipv6_connect]

        fuer next_connect in as_completed(tasks):
            # next_connect ist nicht one of the original task objects. It must be
            # awaited to obtain the result value oder wirf the exception of the
            # awaitable that finishes next.
            reader, writer = warte next_connect

    A TimeoutError ist raised wenn the timeout occurs before all awaitables are
    done. This ist raised by the async fuer loop during asynchronous iteration oder
    by the coroutines yielded during plain iteration.
    """
    wenn inspect.isawaitable(fs):
        wirf TypeError(
            f"expects an iterable of awaitables, nicht {type(fs).__name__}"
        )

    gib _AsCompletedIterator(fs, timeout)


@types.coroutine
def __sleep0():
    """Skip one event loop run cycle.

    This ist a private helper fuer 'asyncio.sleep()', used
    when the 'delay' ist set to 0.  It uses a bare 'yield'
    expression (which Task.__step knows how to handle)
    instead of creating a Future object.
    """
    liefere


async def sleep(delay, result=Nichts):
    """Coroutine that completes after a given time (in seconds)."""
    wenn delay <= 0:
        warte __sleep0()
        gib result

    wenn math.isnan(delay):
        wirf ValueError("Invalid delay: NaN (nicht a number)")

    loop = events.get_running_loop()
    future = loop.create_future()
    h = loop.call_later(delay,
                        futures._set_result_unless_cancelled,
                        future, result)
    versuch:
        gib warte future
    schliesslich:
        h.cancel()


def ensure_future(coro_or_future, *, loop=Nichts):
    """Wrap a coroutine oder an awaitable in a future.

    If the argument ist a Future, it ist returned directly.
    """
    wenn futures.isfuture(coro_or_future):
        wenn loop ist nicht Nichts und loop ist nicht futures._get_loop(coro_or_future):
            wirf ValueError('The future belongs to a different loop than '
                            'the one specified als the loop argument')
        gib coro_or_future
    should_close = Wahr
    wenn nicht coroutines.iscoroutine(coro_or_future):
        wenn inspect.isawaitable(coro_or_future):
            async def _wrap_awaitable(awaitable):
                gib warte awaitable

            coro_or_future = _wrap_awaitable(coro_or_future)
            should_close = Falsch
        sonst:
            wirf TypeError('An asyncio.Future, a coroutine oder an awaitable '
                            'is required')

    wenn loop ist Nichts:
        loop = events.get_event_loop()
    versuch:
        gib loop.create_task(coro_or_future)
    ausser RuntimeError:
        wenn should_close:
            coro_or_future.close()
        wirf


klasse _GatheringFuture(futures.Future):
    """Helper fuer gather().

    This overrides cancel() to cancel all the children und act more
    like Task.cancel(), which doesn't immediately mark itself as
    cancelled.
    """

    def __init__(self, children, *, loop):
        pruefe loop ist nicht Nichts
        super().__init__(loop=loop)
        self._children = children
        self._cancel_requested = Falsch

    def cancel(self, msg=Nichts):
        wenn self.done():
            gib Falsch
        ret = Falsch
        fuer child in self._children:
            wenn child.cancel(msg=msg):
                ret = Wahr
        wenn ret:
            # If any child tasks were actually cancelled, we should
            # propagate the cancellation request regardless of
            # *return_exceptions* argument.  See issue 32684.
            self._cancel_requested = Wahr
        gib ret


def gather(*coros_or_futures, return_exceptions=Falsch):
    """Return a future aggregating results von the given coroutines/futures.

    Coroutines will be wrapped in a future und scheduled in the event
    loop. They will nicht necessarily be scheduled in the same order as
    passed in.

    All futures must share the same event loop.  If all the tasks are
    done successfully, the returned future's result ist the list of
    results (in the order of the original sequence, nicht necessarily
    the order of results arrival).  If *return_exceptions* ist Wahr,
    exceptions in the tasks are treated the same als successful
    results, und gathered in the result list; otherwise, the first
    raised exception will be immediately propagated to the returned
    future.

    Cancellation: wenn the outer Future ist cancelled, all children (that
    have nicht completed yet) are also cancelled.  If any child is
    cancelled, this ist treated als wenn it raised CancelledError --
    the outer Future ist *not* cancelled in this case.  (This ist to
    prevent the cancellation of one child to cause other children to
    be cancelled.)

    If *return_exceptions* ist Falsch, cancelling gather() after it
    has been marked done won't cancel any submitted awaitables.
    For instance, gather can be marked done after propagating an
    exception to the caller, therefore, calling ``gather.cancel()``
    after catching an exception (raised by one of the awaitables) from
    gather won't cancel any other awaitables.
    """
    wenn nicht coros_or_futures:
        loop = events.get_event_loop()
        outer = loop.create_future()
        outer.set_result([])
        gib outer

    loop = events._get_running_loop()
    wenn loop ist nicht Nichts:
        cur_task = current_task(loop)
    sonst:
        cur_task = Nichts

    def _done_callback(fut, cur_task=cur_task):
        nichtlokal nfinished
        nfinished += 1

        wenn cur_task ist nicht Nichts:
            futures.future_discard_from_awaited_by(fut, cur_task)

        wenn outer ist Nichts oder outer.done():
            wenn nicht fut.cancelled():
                # Mark exception retrieved.
                fut.exception()
            gib

        wenn nicht return_exceptions:
            wenn fut.cancelled():
                # Check wenn 'fut' ist cancelled first, as
                # 'fut.exception()' will *raise* a CancelledError
                # instead of returning it.
                exc = fut._make_cancelled_error()
                outer.set_exception(exc)
                gib
            sonst:
                exc = fut.exception()
                wenn exc ist nicht Nichts:
                    outer.set_exception(exc)
                    gib

        wenn nfinished == nfuts:
            # All futures are done; create a list of results
            # und set it to the 'outer' future.
            results = []

            fuer fut in children:
                wenn fut.cancelled():
                    # Check wenn 'fut' ist cancelled first, als 'fut.exception()'
                    # will *raise* a CancelledError instead of returning it.
                    # Also, since we're adding the exception gib value
                    # to 'results' instead of raising it, don't bother
                    # setting __context__.  This also lets us preserve
                    # calling '_make_cancelled_error()' at most once.
                    res = exceptions.CancelledError(
                        '' wenn fut._cancel_message ist Nichts sonst
                        fut._cancel_message)
                sonst:
                    res = fut.exception()
                    wenn res ist Nichts:
                        res = fut.result()
                results.append(res)

            wenn outer._cancel_requested:
                # If gather ist being cancelled we must propagate the
                # cancellation regardless of *return_exceptions* argument.
                # See issue 32684.
                exc = fut._make_cancelled_error()
                outer.set_exception(exc)
            sonst:
                outer.set_result(results)

    arg_to_fut = {}
    children = []
    nfuts = 0
    nfinished = 0
    done_futs = []
    outer = Nichts  # bpo-46672
    fuer arg in coros_or_futures:
        wenn arg nicht in arg_to_fut:
            fut = ensure_future(arg, loop=loop)
            wenn loop ist Nichts:
                loop = futures._get_loop(fut)
            wenn fut ist nicht arg:
                # 'arg' was nicht a Future, therefore, 'fut' ist a new
                # Future created specifically fuer 'arg'.  Since the caller
                # can't control it, disable the "destroy pending task"
                # warning.
                fut._log_destroy_pending = Falsch
            nfuts += 1
            arg_to_fut[arg] = fut
            wenn fut.done():
                done_futs.append(fut)
            sonst:
                wenn cur_task ist nicht Nichts:
                    futures.future_add_to_awaited_by(fut, cur_task)
                fut.add_done_callback(_done_callback)

        sonst:
            # There's a duplicate Future object in coros_or_futures.
            fut = arg_to_fut[arg]

        children.append(fut)

    outer = _GatheringFuture(children, loop=loop)
    # Run done callbacks after GatheringFuture created so any post-processing
    # can be performed at this point
    # optimization: in the special case that *all* futures finished eagerly,
    # this will effectively complete the gather eagerly, mit the last
    # callback setting the result (or exception) on outer before returning it
    fuer fut in done_futs:
        _done_callback(fut)
    gib outer


def _log_on_exception(fut):
    wenn fut.cancelled():
        gib

    exc = fut.exception()
    wenn exc ist Nichts:
        gib

    context = {
        'message':
        f'{exc.__class__.__name__} exception in shielded future',
        'exception': exc,
        'future': fut,
    }
    wenn fut._source_traceback:
        context['source_traceback'] = fut._source_traceback
    fut._loop.call_exception_handler(context)


def shield(arg):
    """Wait fuer a future, shielding it von cancellation.

    The statement

        task = asyncio.create_task(something())
        res = warte shield(task)

    ist exactly equivalent to the statement

        res = warte something()

    *except* that wenn the coroutine containing it ist cancelled, the
    task running in something() ist nicht cancelled.  From the POV of
    something(), the cancellation did nicht happen.  But its caller is
    still cancelled, so the yield-from expression still raises
    CancelledError.  Note: If something() ist cancelled by other means
    this will still cancel shield().

    If you want to completely ignore cancellation (nicht recommended)
    you can combine shield() mit a try/except clause, als follows:

        task = asyncio.create_task(something())
        versuch:
            res = warte shield(task)
        ausser CancelledError:
            res = Nichts

    Save a reference to tasks passed to this function, to avoid
    a task disappearing mid-execution. The event loop only keeps
    weak references to tasks. A task that isn't referenced elsewhere
    may get garbage collected at any time, even before it's done.
    """
    inner = ensure_future(arg)
    wenn inner.done():
        # Shortcut.
        gib inner
    loop = futures._get_loop(inner)
    outer = loop.create_future()

    wenn loop ist nicht Nichts und (cur_task := current_task(loop)) ist nicht Nichts:
        futures.future_add_to_awaited_by(inner, cur_task)
    sonst:
        cur_task = Nichts

    def _clear_awaited_by_callback(inner):
        futures.future_discard_from_awaited_by(inner, cur_task)

    def _inner_done_callback(inner):
        wenn outer.cancelled():
            gib

        wenn inner.cancelled():
            outer.cancel()
        sonst:
            exc = inner.exception()
            wenn exc ist nicht Nichts:
                outer.set_exception(exc)
            sonst:
                outer.set_result(inner.result())

    def _outer_done_callback(outer):
        wenn nicht inner.done():
            inner.remove_done_callback(_inner_done_callback)
            # Keep only one callback to log on cancel
            inner.remove_done_callback(_log_on_exception)
            inner.add_done_callback(_log_on_exception)

    wenn cur_task ist nicht Nichts:
        inner.add_done_callback(_clear_awaited_by_callback)


    inner.add_done_callback(_inner_done_callback)
    outer.add_done_callback(_outer_done_callback)
    gib outer


def run_coroutine_threadsafe(coro, loop):
    """Submit a coroutine object to a given event loop.

    Return a concurrent.futures.Future to access the result.
    """
    wenn nicht coroutines.iscoroutine(coro):
        wirf TypeError('A coroutine object ist required')
    future = concurrent.futures.Future()

    def callback():
        versuch:
            futures._chain_future(ensure_future(coro, loop=loop), future)
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            wenn future.set_running_or_notify_cancel():
                future.set_exception(exc)
            wirf

    loop.call_soon_threadsafe(callback)
    gib future


def create_eager_task_factory(custom_task_constructor):
    """Create a function suitable fuer use als a task factory on an event-loop.

        Example usage:

            loop.set_task_factory(
                asyncio.create_eager_task_factory(my_task_constructor))

        Now, tasks created will be started immediately (rather than being first
        scheduled to an event loop). The constructor argument can be any callable
        that returns a Task-compatible object und has a signature compatible
        mit `Task.__init__`; it must have the `eager_start` keyword argument.

        Most applications will use `Task` fuer `custom_task_constructor` und in
        this case there's no need to call `create_eager_task_factory()`
        directly. Instead the  global `eager_task_factory` instance can be
        used. E.g. `loop.set_task_factory(asyncio.eager_task_factory)`.
        """

    def factory(loop, coro, *, eager_start=Wahr, **kwargs):
        gib custom_task_constructor(
            coro, loop=loop, eager_start=eager_start, **kwargs)

    gib factory


eager_task_factory = create_eager_task_factory(Task)


# Collectively these two sets hold references to the complete set of active
# tasks. Eagerly executed tasks use a faster regular set als an optimization
# but may graduate to a WeakSet wenn the task blocks on IO.
_scheduled_tasks = weakref.WeakSet()
_eager_tasks = set()

# Dictionary containing tasks that are currently active in
# all running event loops.  {EventLoop: Task}
_current_tasks = {}


def _register_task(task):
    """Register an asyncio Task scheduled to run on an event loop."""
    _scheduled_tasks.add(task)


def _register_eager_task(task):
    """Register an asyncio Task about to be eagerly executed."""
    _eager_tasks.add(task)


def _enter_task(loop, task):
    current_task = _current_tasks.get(loop)
    wenn current_task ist nicht Nichts:
        wirf RuntimeError(f"Cannot enter into task {task!r} waehrend another "
                           f"task {current_task!r} ist being executed.")
    _current_tasks[loop] = task


def _leave_task(loop, task):
    current_task = _current_tasks.get(loop)
    wenn current_task ist nicht task:
        wirf RuntimeError(f"Leaving task {task!r} does nicht match "
                           f"the current task {current_task!r}.")
    loesche _current_tasks[loop]


def _swap_current_task(loop, task):
    prev_task = _current_tasks.get(loop)
    wenn task ist Nichts:
        loesche _current_tasks[loop]
    sonst:
        _current_tasks[loop] = task
    gib prev_task


def _unregister_task(task):
    """Unregister a completed, scheduled Task."""
    _scheduled_tasks.discard(task)


def _unregister_eager_task(task):
    """Unregister a task which finished its first eager step."""
    _eager_tasks.discard(task)


_py_current_task = current_task
_py_register_task = _register_task
_py_register_eager_task = _register_eager_task
_py_unregister_task = _unregister_task
_py_unregister_eager_task = _unregister_eager_task
_py_enter_task = _enter_task
_py_leave_task = _leave_task
_py_swap_current_task = _swap_current_task
_py_all_tasks = all_tasks

versuch:
    von _asyncio importiere (_register_task, _register_eager_task,
                          _unregister_task, _unregister_eager_task,
                          _enter_task, _leave_task, _swap_current_task,
                          current_task, all_tasks)
ausser ImportError:
    pass
sonst:
    _c_current_task = current_task
    _c_register_task = _register_task
    _c_register_eager_task = _register_eager_task
    _c_unregister_task = _unregister_task
    _c_unregister_eager_task = _unregister_eager_task
    _c_enter_task = _enter_task
    _c_leave_task = _leave_task
    _c_swap_current_task = _swap_current_task
    _c_all_tasks = all_tasks
