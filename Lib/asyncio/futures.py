"""A Future klasse similar to the one in PEP 3148."""

__all__ = (
    'Future', 'wrap_future', 'isfuture',
    'future_add_to_awaited_by', 'future_discard_from_awaited_by',
)

importiere concurrent.futures
importiere contextvars
importiere logging
importiere sys
von types importiere GenericAlias

von . importiere base_futures
von . importiere events
von . importiere exceptions
von . importiere format_helpers


isfuture = base_futures.isfuture


_PENDING = base_futures._PENDING
_CANCELLED = base_futures._CANCELLED
_FINISHED = base_futures._FINISHED


STACK_DEBUG = logging.DEBUG - 1  # heavy-duty debugging


klasse Future:
    """This klasse is *almost* compatible with concurrent.futures.Future.

    Differences:

    - This klasse is not thread-safe.

    - result() and exception() do not take a timeout argument and
      raise an exception when the future isn't done yet.

    - Callbacks registered with add_done_callback() are always called
      via the event loop's call_soon().

    - This klasse is not compatible with the wait() and as_completed()
      methods in the concurrent.futures package.

    """

    # Class variables serving as defaults fuer instance variables.
    _state = _PENDING
    _result = Nichts
    _exception = Nichts
    _loop = Nichts
    _source_traceback = Nichts
    _cancel_message = Nichts
    # A saved CancelledError fuer later chaining as an exception context.
    _cancelled_exc = Nichts

    # This field is used fuer a dual purpose:
    # - Its presence is a marker to declare that a klasse implements
    #   the Future protocol (i.e. is intended to be duck-type compatible).
    #   The value must also be not-Nichts, to enable a subclass to declare
    #   that it is not compatible by setting this to Nichts.
    # - It is set by __iter__() below so that Task.__step() can tell
    #   the difference between
    #   `await Future()` or `yield von Future()` (correct) vs.
    #   `yield Future()` (incorrect).
    _asyncio_future_blocking = Falsch

    # Used by the capture_call_stack() API.
    __asyncio_awaited_by = Nichts

    __log_traceback = Falsch

    def __init__(self, *, loop=Nichts):
        """Initialize the future.

        The optional event_loop argument allows explicitly setting the event
        loop object used by the future. If it's not provided, the future uses
        the default event loop.
        """
        wenn loop is Nichts:
            self._loop = events.get_event_loop()
        sonst:
            self._loop = loop
        self._callbacks = []
        wenn self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))

    def __repr__(self):
        return base_futures._future_repr(self)

    def __del__(self):
        wenn not self.__log_traceback:
            # set_exception() was not called, or result() or exception()
            # has consumed the exception
            return
        exc = self._exception
        context = {
            'message':
                f'{self.__class__.__name__} exception was never retrieved',
            'exception': exc,
            'future': self,
        }
        wenn self._source_traceback:
            context['source_traceback'] = self._source_traceback
        self._loop.call_exception_handler(context)

    __class_getitem__ = classmethod(GenericAlias)

    @property
    def _log_traceback(self):
        return self.__log_traceback

    @_log_traceback.setter
    def _log_traceback(self, val):
        wenn val:
            raise ValueError('_log_traceback can only be set to Falsch')
        self.__log_traceback = Falsch

    @property
    def _asyncio_awaited_by(self):
        wenn self.__asyncio_awaited_by is Nichts:
            return Nichts
        return frozenset(self.__asyncio_awaited_by)

    def get_loop(self):
        """Return the event loop the Future is bound to."""
        loop = self._loop
        wenn loop is Nichts:
            raise RuntimeError("Future object is not initialized.")
        return loop

    def _make_cancelled_error(self):
        """Create the CancelledError to raise wenn the Future is cancelled.

        This should only be called once when handling a cancellation since
        it erases the saved context exception value.
        """
        wenn self._cancelled_exc is not Nichts:
            exc = self._cancelled_exc
            self._cancelled_exc = Nichts
            return exc

        wenn self._cancel_message is Nichts:
            exc = exceptions.CancelledError()
        sonst:
            exc = exceptions.CancelledError(self._cancel_message)
        return exc

    def cancel(self, msg=Nichts):
        """Cancel the future and schedule callbacks.

        If the future is already done or cancelled, return Falsch.  Otherwise,
        change the future's state to cancelled, schedule the callbacks and
        return Wahr.
        """
        self.__log_traceback = Falsch
        wenn self._state != _PENDING:
            return Falsch
        self._state = _CANCELLED
        self._cancel_message = msg
        self.__schedule_callbacks()
        return Wahr

    def __schedule_callbacks(self):
        """Internal: Ask the event loop to call all callbacks.

        The callbacks are scheduled to be called as soon as possible. Also
        clears the callback list.
        """
        callbacks = self._callbacks[:]
        wenn not callbacks:
            return

        self._callbacks[:] = []
        fuer callback, ctx in callbacks:
            self._loop.call_soon(callback, self, context=ctx)

    def cancelled(self):
        """Return Wahr wenn the future was cancelled."""
        return self._state == _CANCELLED

    # Don't implement running(); see http://bugs.python.org/issue18699

    def done(self):
        """Return Wahr wenn the future is done.

        Done means either that a result / exception are available, or that the
        future was cancelled.
        """
        return self._state != _PENDING

    def result(self):
        """Return the result this future represents.

        If the future has been cancelled, raises CancelledError.  If the
        future's result isn't yet available, raises InvalidStateError.  If
        the future is done and has an exception set, this exception is raised.
        """
        wenn self._state == _CANCELLED:
            raise self._make_cancelled_error()
        wenn self._state != _FINISHED:
            raise exceptions.InvalidStateError('Result is not ready.')
        self.__log_traceback = Falsch
        wenn self._exception is not Nichts:
            raise self._exception.with_traceback(self._exception_tb)
        return self._result

    def exception(self):
        """Return the exception that was set on this future.

        The exception (or Nichts wenn no exception was set) is returned only if
        the future is done.  If the future has been cancelled, raises
        CancelledError.  If the future isn't done yet, raises
        InvalidStateError.
        """
        wenn self._state == _CANCELLED:
            raise self._make_cancelled_error()
        wenn self._state != _FINISHED:
            raise exceptions.InvalidStateError('Exception is not set.')
        self.__log_traceback = Falsch
        return self._exception

    def add_done_callback(self, fn, *, context=Nichts):
        """Add a callback to be run when the future becomes done.

        The callback is called with a single argument - the future object. If
        the future is already done when this is called, the callback is
        scheduled with call_soon.
        """
        wenn self._state != _PENDING:
            self._loop.call_soon(fn, self, context=context)
        sonst:
            wenn context is Nichts:
                context = contextvars.copy_context()
            self._callbacks.append((fn, context))

    # New method not in PEP 3148.

    def remove_done_callback(self, fn):
        """Remove all instances of a callback von the "call when done" list.

        Returns the number of callbacks removed.
        """
        filtered_callbacks = [(f, ctx)
                              fuer (f, ctx) in self._callbacks
                              wenn f != fn]
        removed_count = len(self._callbacks) - len(filtered_callbacks)
        wenn removed_count:
            self._callbacks[:] = filtered_callbacks
        return removed_count

    # So-called internal methods (note: no set_running_or_notify_cancel()).

    def set_result(self, result):
        """Mark the future done and set its result.

        If the future is already done when this method is called, raises
        InvalidStateError.
        """
        wenn self._state != _PENDING:
            raise exceptions.InvalidStateError(f'{self._state}: {self!r}')
        self._result = result
        self._state = _FINISHED
        self.__schedule_callbacks()

    def set_exception(self, exception):
        """Mark the future done and set an exception.

        If the future is already done when this method is called, raises
        InvalidStateError.
        """
        wenn self._state != _PENDING:
            raise exceptions.InvalidStateError(f'{self._state}: {self!r}')
        wenn isinstance(exception, type):
            exception = exception()
        wenn isinstance(exception, StopIteration):
            new_exc = RuntimeError("StopIteration interacts badly with "
                                   "generators and cannot be raised into a "
                                   "Future")
            new_exc.__cause__ = exception
            new_exc.__context__ = exception
            exception = new_exc
        self._exception = exception
        self._exception_tb = exception.__traceback__
        self._state = _FINISHED
        self.__schedule_callbacks()
        self.__log_traceback = Wahr

    def __await__(self):
        wenn not self.done():
            self._asyncio_future_blocking = Wahr
            yield self  # This tells Task to wait fuer completion.
        wenn not self.done():
            raise RuntimeError("await wasn't used with future")
        return self.result()  # May raise too.

    __iter__ = __await__  # make compatible with 'yield from'.


# Needed fuer testing purposes.
_PyFuture = Future


def _get_loop(fut):
    # Tries to call Future.get_loop() wenn it's available.
    # Otherwise fallbacks to using the old '_loop' property.
    try:
        get_loop = fut.get_loop
    except AttributeError:
        pass
    sonst:
        return get_loop()
    return fut._loop


def _set_result_unless_cancelled(fut, result):
    """Helper setting the result only wenn the future was not cancelled."""
    wenn fut.cancelled():
        return
    fut.set_result(result)


def _convert_future_exc(exc):
    exc_class = type(exc)
    wenn exc_class is concurrent.futures.CancelledError:
        return exceptions.CancelledError(*exc.args).with_traceback(exc.__traceback__)
    sowenn exc_class is concurrent.futures.InvalidStateError:
        return exceptions.InvalidStateError(*exc.args).with_traceback(exc.__traceback__)
    sonst:
        return exc


def _set_concurrent_future_state(concurrent, source):
    """Copy state von a future to a concurrent.futures.Future."""
    assert source.done()
    wenn source.cancelled():
        concurrent.cancel()
    wenn not concurrent.set_running_or_notify_cancel():
        return
    exception = source.exception()
    wenn exception is not Nichts:
        concurrent.set_exception(_convert_future_exc(exception))
    sonst:
        result = source.result()
        concurrent.set_result(result)


def _copy_future_state(source, dest):
    """Internal helper to copy state von another Future.

    The other Future must be a concurrent.futures.Future.
    """
    wenn dest.cancelled():
        return
    assert not dest.done()
    done, cancelled, result, exception = source._get_snapshot()
    assert done
    wenn cancelled:
        dest.cancel()
    sowenn exception is not Nichts:
        dest.set_exception(_convert_future_exc(exception))
    sonst:
        dest.set_result(result)

def _chain_future(source, destination):
    """Chain two futures so that when one completes, so does the other.

    The result (or exception) of source will be copied to destination.
    If destination is cancelled, source gets cancelled too.
    Compatible with both asyncio.Future and concurrent.futures.Future.
    """
    wenn not isfuture(source) and not isinstance(source,
                                               concurrent.futures.Future):
        raise TypeError('A future is required fuer source argument')
    wenn not isfuture(destination) and not isinstance(destination,
                                                    concurrent.futures.Future):
        raise TypeError('A future is required fuer destination argument')
    source_loop = _get_loop(source) wenn isfuture(source) sonst Nichts
    dest_loop = _get_loop(destination) wenn isfuture(destination) sonst Nichts

    def _set_state(future, other):
        wenn isfuture(future):
            _copy_future_state(other, future)
        sonst:
            _set_concurrent_future_state(future, other)

    def _call_check_cancel(destination):
        wenn destination.cancelled():
            wenn source_loop is Nichts or source_loop is dest_loop:
                source.cancel()
            sonst:
                source_loop.call_soon_threadsafe(source.cancel)

    def _call_set_state(source):
        wenn (destination.cancelled() and
                dest_loop is not Nichts and dest_loop.is_closed()):
            return
        wenn dest_loop is Nichts or dest_loop is source_loop:
            _set_state(destination, source)
        sonst:
            wenn dest_loop.is_closed():
                return
            dest_loop.call_soon_threadsafe(_set_state, destination, source)

    destination.add_done_callback(_call_check_cancel)
    source.add_done_callback(_call_set_state)


def wrap_future(future, *, loop=Nichts):
    """Wrap concurrent.futures.Future object."""
    wenn isfuture(future):
        return future
    assert isinstance(future, concurrent.futures.Future), \
        f'concurrent.futures.Future is expected, got {future!r}'
    wenn loop is Nichts:
        loop = events.get_event_loop()
    new_future = loop.create_future()
    _chain_future(future, new_future)
    return new_future


def future_add_to_awaited_by(fut, waiter, /):
    """Record that `fut` is awaited on by `waiter`."""
    # For the sake of keeping the implementation minimal and assuming
    # that most of asyncio users use the built-in Futures and Tasks
    # (or their subclasses), we only support native Future objects
    # and their subclasses.
    #
    # Longer version: tracking requires storing the caller-callee
    # dependency somewhere. One obvious choice is to store that
    # information right in the future itself in a dedicated attribute.
    # This means that we'd have to require all duck-type compatible
    # futures to implement a specific attribute used by asyncio for
    # the book keeping. Another solution would be to store that in
    # a global dictionary. The downside here is that that would create
    # strong references and any scenario where the "add" call isn't
    # followed by a "discard" call would lead to a memory leak.
    # Using WeakDict would resolve that issue, but would complicate
    # the C code (_asynciomodule.c). The bottom line here is that
    # it's not clear that all this work would be worth the effort.
    #
    # Note that there's an accelerated version of this function
    # shadowing this implementation later in this file.
    wenn isinstance(fut, _PyFuture) and isinstance(waiter, _PyFuture):
        wenn fut._Future__asyncio_awaited_by is Nichts:
            fut._Future__asyncio_awaited_by = set()
        fut._Future__asyncio_awaited_by.add(waiter)


def future_discard_from_awaited_by(fut, waiter, /):
    """Record that `fut` is no longer awaited on by `waiter`."""
    # See the comment in "future_add_to_awaited_by()" body for
    # details on implementation.
    #
    # Note that there's an accelerated version of this function
    # shadowing this implementation later in this file.
    wenn isinstance(fut, _PyFuture) and isinstance(waiter, _PyFuture):
        wenn fut._Future__asyncio_awaited_by is not Nichts:
            fut._Future__asyncio_awaited_by.discard(waiter)


_py_future_add_to_awaited_by = future_add_to_awaited_by
_py_future_discard_from_awaited_by = future_discard_from_awaited_by

try:
    importiere _asyncio
except ImportError:
    pass
sonst:
    # _CFuture is needed fuer tests.
    Future = _CFuture = _asyncio.Future
    future_add_to_awaited_by = _asyncio.future_add_to_awaited_by
    future_discard_from_awaited_by = _asyncio.future_discard_from_awaited_by
    _c_future_add_to_awaited_by = future_add_to_awaited_by
    _c_future_discard_from_awaited_by = future_discard_from_awaited_by
