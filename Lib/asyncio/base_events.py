"""Base implementation of event loop.

The event loop can be broken up into a multiplexer (the part
responsible fuer notifying us of I/O events) and the event loop proper,
which wraps a multiplexer with functionality fuer scheduling callbacks,
immediately or at a given time in the future.

Whenever a public API takes a callback, subsequent positional
arguments will be passed to the callback if/when it is called.  This
avoids the proliferation of trivial lambdas implementing closures.
Keyword arguments fuer the callback are not supported; this is a
conscious design decision, leaving the door open fuer keyword arguments
to modify the meaning of the API call itself.
"""

importiere collections
importiere collections.abc
importiere concurrent.futures
importiere errno
importiere heapq
importiere itertools
importiere os
importiere socket
importiere stat
importiere subprocess
importiere threading
importiere time
importiere traceback
importiere sys
importiere warnings
importiere weakref

try:
    importiere ssl
except ImportError:  # pragma: no cover
    ssl = Nichts

von . importiere constants
von . importiere coroutines
von . importiere events
von . importiere exceptions
von . importiere futures
von . importiere protocols
von . importiere sslproto
von . importiere staggered
von . importiere tasks
von . importiere timeouts
von . importiere transports
von . importiere trsock
von .log importiere logger


__all__ = 'BaseEventLoop','Server',


# Minimum number of _scheduled timer handles before cleanup of
# cancelled handles is performed.
_MIN_SCHEDULED_TIMER_HANDLES = 100

# Minimum fraction of _scheduled timer handles that are cancelled
# before cleanup of cancelled handles is performed.
_MIN_CANCELLED_TIMER_HANDLES_FRACTION = 0.5


_HAS_IPv6 = hasattr(socket, 'AF_INET6')

# Maximum timeout passed to select to avoid OS limitations
MAXIMUM_SELECT_TIMEOUT = 24 * 3600


def _format_handle(handle):
    cb = handle._callback
    wenn isinstance(getattr(cb, '__self__', Nichts), tasks.Task):
        # format the task
        return repr(cb.__self__)
    sonst:
        return str(handle)


def _format_pipe(fd):
    wenn fd == subprocess.PIPE:
        return '<pipe>'
    sowenn fd == subprocess.STDOUT:
        return '<stdout>'
    sonst:
        return repr(fd)


def _set_reuseport(sock):
    wenn not hasattr(socket, 'SO_REUSEPORT'):
        raise ValueError('reuse_port not supported by socket module')
    sonst:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            raise ValueError('reuse_port not supported by socket module, '
                             'SO_REUSEPORT defined but not implemented.')


def _ipaddr_info(host, port, family, type, proto, flowinfo=0, scopeid=0):
    # Try to skip getaddrinfo wenn "host" is already an IP. Users might have
    # handled name resolution in their own code and pass in resolved IPs.
    wenn not hasattr(socket, 'inet_pton'):
        return

    wenn proto not in {0, socket.IPPROTO_TCP, socket.IPPROTO_UDP} or \
            host is Nichts:
        return Nichts

    wenn type == socket.SOCK_STREAM:
        proto = socket.IPPROTO_TCP
    sowenn type == socket.SOCK_DGRAM:
        proto = socket.IPPROTO_UDP
    sonst:
        return Nichts

    wenn port is Nichts:
        port = 0
    sowenn isinstance(port, bytes) and port == b'':
        port = 0
    sowenn isinstance(port, str) and port == '':
        port = 0
    sonst:
        # If port's a service name like "http", don't skip getaddrinfo.
        try:
            port = int(port)
        except (TypeError, ValueError):
            return Nichts

    wenn family == socket.AF_UNSPEC:
        afs = [socket.AF_INET]
        wenn _HAS_IPv6:
            afs.append(socket.AF_INET6)
    sonst:
        afs = [family]

    wenn isinstance(host, bytes):
        host = host.decode('idna')
    wenn '%' in host:
        # Linux's inet_pton doesn't accept an IPv6 zone index after host,
        # like '::1%lo0'.
        return Nichts

    fuer af in afs:
        try:
            socket.inet_pton(af, host)
            # The host has already been resolved.
            wenn _HAS_IPv6 and af == socket.AF_INET6:
                return af, type, proto, '', (host, port, flowinfo, scopeid)
            sonst:
                return af, type, proto, '', (host, port)
        except OSError:
            pass

    # "host" is not an IP address.
    return Nichts


def _interleave_addrinfos(addrinfos, first_address_family_count=1):
    """Interleave list of addrinfo tuples by family."""
    # Group addresses by family
    addrinfos_by_family = collections.OrderedDict()
    fuer addr in addrinfos:
        family = addr[0]
        wenn family not in addrinfos_by_family:
            addrinfos_by_family[family] = []
        addrinfos_by_family[family].append(addr)
    addrinfos_lists = list(addrinfos_by_family.values())

    reordered = []
    wenn first_address_family_count > 1:
        reordered.extend(addrinfos_lists[0][:first_address_family_count - 1])
        del addrinfos_lists[0][:first_address_family_count - 1]
    reordered.extend(
        a fuer a in itertools.chain.from_iterable(
            itertools.zip_longest(*addrinfos_lists)
        ) wenn a is not Nichts)
    return reordered


def _run_until_complete_cb(fut):
    wenn not fut.cancelled():
        exc = fut.exception()
        wenn isinstance(exc, (SystemExit, KeyboardInterrupt)):
            # Issue #22429: run_forever() already finished, no need to
            # stop it.
            return
    futures._get_loop(fut).stop()


wenn hasattr(socket, 'TCP_NODELAY'):
    def _set_nodelay(sock):
        wenn (sock.family in {socket.AF_INET, socket.AF_INET6} and
                sock.type == socket.SOCK_STREAM and
                sock.proto == socket.IPPROTO_TCP):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sonst:
    def _set_nodelay(sock):
        pass


def _check_ssl_socket(sock):
    wenn ssl is not Nichts and isinstance(sock, ssl.SSLSocket):
        raise TypeError("Socket cannot be of type SSLSocket")


klasse _SendfileFallbackProtocol(protocols.Protocol):
    def __init__(self, transp):
        wenn not isinstance(transp, transports._FlowControlMixin):
            raise TypeError("transport should be _FlowControlMixin instance")
        self._transport = transp
        self._proto = transp.get_protocol()
        self._should_resume_reading = transp.is_reading()
        self._should_resume_writing = transp._protocol_paused
        transp.pause_reading()
        transp.set_protocol(self)
        wenn self._should_resume_writing:
            self._write_ready_fut = self._transport._loop.create_future()
        sonst:
            self._write_ready_fut = Nichts

    async def drain(self):
        wenn self._transport.is_closing():
            raise ConnectionError("Connection closed by peer")
        fut = self._write_ready_fut
        wenn fut is Nichts:
            return
        await fut

    def connection_made(self, transport):
        raise RuntimeError("Invalid state: "
                           "connection should have been established already.")

    def connection_lost(self, exc):
        wenn self._write_ready_fut is not Nichts:
            # Never happens wenn peer disconnects after sending the whole content
            # Thus disconnection is always an exception von user perspective
            wenn exc is Nichts:
                self._write_ready_fut.set_exception(
                    ConnectionError("Connection is closed by peer"))
            sonst:
                self._write_ready_fut.set_exception(exc)
        self._proto.connection_lost(exc)

    def pause_writing(self):
        wenn self._write_ready_fut is not Nichts:
            return
        self._write_ready_fut = self._transport._loop.create_future()

    def resume_writing(self):
        wenn self._write_ready_fut is Nichts:
            return
        self._write_ready_fut.set_result(Falsch)
        self._write_ready_fut = Nichts

    def data_received(self, data):
        raise RuntimeError("Invalid state: reading should be paused")

    def eof_received(self):
        raise RuntimeError("Invalid state: reading should be paused")

    async def restore(self):
        self._transport.set_protocol(self._proto)
        wenn self._should_resume_reading:
            self._transport.resume_reading()
        wenn self._write_ready_fut is not Nichts:
            # Cancel the future.
            # Basically it has no effect because protocol is switched back,
            # no code should wait fuer it anymore.
            self._write_ready_fut.cancel()
        wenn self._should_resume_writing:
            self._proto.resume_writing()


klasse Server(events.AbstractServer):

    def __init__(self, loop, sockets, protocol_factory, ssl_context, backlog,
                 ssl_handshake_timeout, ssl_shutdown_timeout=Nichts):
        self._loop = loop
        self._sockets = sockets
        # Weak references so we don't break Transport's ability to
        # detect abandoned transports
        self._clients = weakref.WeakSet()
        self._waiters = []
        self._protocol_factory = protocol_factory
        self._backlog = backlog
        self._ssl_context = ssl_context
        self._ssl_handshake_timeout = ssl_handshake_timeout
        self._ssl_shutdown_timeout = ssl_shutdown_timeout
        self._serving = Falsch
        self._serving_forever_fut = Nichts

    def __repr__(self):
        return f'<{self.__class__.__name__} sockets={self.sockets!r}>'

    def _attach(self, transport):
        assert self._sockets is not Nichts
        self._clients.add(transport)

    def _detach(self, transport):
        self._clients.discard(transport)
        wenn len(self._clients) == 0 and self._sockets is Nichts:
            self._wakeup()

    def _wakeup(self):
        waiters = self._waiters
        self._waiters = Nichts
        fuer waiter in waiters:
            wenn not waiter.done():
                waiter.set_result(Nichts)

    def _start_serving(self):
        wenn self._serving:
            return
        self._serving = Wahr
        fuer sock in self._sockets:
            sock.listen(self._backlog)
            self._loop._start_serving(
                self._protocol_factory, sock, self._ssl_context,
                self, self._backlog, self._ssl_handshake_timeout,
                self._ssl_shutdown_timeout)

    def get_loop(self):
        return self._loop

    def is_serving(self):
        return self._serving

    @property
    def sockets(self):
        wenn self._sockets is Nichts:
            return ()
        return tuple(trsock.TransportSocket(s) fuer s in self._sockets)

    def close(self):
        sockets = self._sockets
        wenn sockets is Nichts:
            return
        self._sockets = Nichts

        fuer sock in sockets:
            self._loop._stop_serving(sock)

        self._serving = Falsch

        wenn (self._serving_forever_fut is not Nichts and
                not self._serving_forever_fut.done()):
            self._serving_forever_fut.cancel()
            self._serving_forever_fut = Nichts

        wenn len(self._clients) == 0:
            self._wakeup()

    def close_clients(self):
        fuer transport in self._clients.copy():
            transport.close()

    def abort_clients(self):
        fuer transport in self._clients.copy():
            transport.abort()

    async def start_serving(self):
        self._start_serving()
        # Skip one loop iteration so that all 'loop.add_reader'
        # go through.
        await tasks.sleep(0)

    async def serve_forever(self):
        wenn self._serving_forever_fut is not Nichts:
            raise RuntimeError(
                f'server {self!r} is already being awaited on serve_forever()')
        wenn self._sockets is Nichts:
            raise RuntimeError(f'server {self!r} is closed')

        self._start_serving()
        self._serving_forever_fut = self._loop.create_future()

        try:
            await self._serving_forever_fut
        except exceptions.CancelledError:
            try:
                self.close()
                await self.wait_closed()
            finally:
                raise
        finally:
            self._serving_forever_fut = Nichts

    async def wait_closed(self):
        """Wait until server is closed and all connections are dropped.

        - If the server is not closed, wait.
        - If it is closed, but there are still active connections, wait.

        Anyone waiting here will be unblocked once both conditions
        (server is closed and all connections have been dropped)
        have become true, in either order.

        Historical note: In 3.11 and before, this was broken, returning
        immediately wenn the server was already closed, even wenn there
        were still active connections. An attempted fix in 3.12.0 was
        still broken, returning immediately wenn the server was still
        open and there were no active connections. Hopefully in 3.12.1
        we have it right.
        """
        # Waiters are unblocked by self._wakeup(), which is called
        # von two places: self.close() and self._detach(), but only
        # when both conditions have become true. To signal that this
        # has happened, self._wakeup() sets self._waiters to Nichts.
        wenn self._waiters is Nichts:
            return
        waiter = self._loop.create_future()
        self._waiters.append(waiter)
        await waiter


klasse BaseEventLoop(events.AbstractEventLoop):

    def __init__(self):
        self._timer_cancelled_count = 0
        self._closed = Falsch
        self._stopping = Falsch
        self._ready = collections.deque()
        self._scheduled = []
        self._default_executor = Nichts
        self._internal_fds = 0
        # Identifier of the thread running the event loop, or Nichts wenn the
        # event loop is not running
        self._thread_id = Nichts
        self._clock_resolution = time.get_clock_info('monotonic').resolution
        self._exception_handler = Nichts
        self.set_debug(coroutines._is_debug_mode())
        # The preserved state of async generator hooks.
        self._old_agen_hooks = Nichts
        # In debug mode, wenn the execution of a callback or a step of a task
        # exceed this duration in seconds, the slow callback/task is logged.
        self.slow_callback_duration = 0.1
        self._current_handle = Nichts
        self._task_factory = Nichts
        self._coroutine_origin_tracking_enabled = Falsch
        self._coroutine_origin_tracking_saved_depth = Nichts

        # A weak set of all asynchronous generators that are
        # being iterated by the loop.
        self._asyncgens = weakref.WeakSet()
        # Set to Wahr when `loop.shutdown_asyncgens` is called.
        self._asyncgens_shutdown_called = Falsch
        # Set to Wahr when `loop.shutdown_default_executor` is called.
        self._executor_shutdown_called = Falsch

    def __repr__(self):
        return (
            f'<{self.__class__.__name__} running={self.is_running()} '
            f'closed={self.is_closed()} debug={self.get_debug()}>'
        )

    def create_future(self):
        """Create a Future object attached to the loop."""
        return futures.Future(loop=self)

    def create_task(self, coro, **kwargs):
        """Schedule or begin executing a coroutine object.

        Return a task object.
        """
        self._check_closed()
        wenn self._task_factory is not Nichts:
            return self._task_factory(self, coro, **kwargs)

        task = tasks.Task(coro, loop=self, **kwargs)
        wenn task._source_traceback:
            del task._source_traceback[-1]
        try:
            return task
        finally:
            # gh-128552: prevent a refcycle of
            # task.exception().__traceback__->BaseEventLoop.create_task->task
            del task

    def set_task_factory(self, factory):
        """Set a task factory that will be used by loop.create_task().

        If factory is Nichts the default task factory will be set.

        If factory is a callable, it should have a signature matching
        '(loop, coro, **kwargs)', where 'loop' will be a reference to the active
        event loop, 'coro' will be a coroutine object, and **kwargs will be
        arbitrary keyword arguments that should be passed on to Task.
        The callable must return a Task.
        """
        wenn factory is not Nichts and not callable(factory):
            raise TypeError('task factory must be a callable or Nichts')
        self._task_factory = factory

    def get_task_factory(self):
        """Return a task factory, or Nichts wenn the default one is in use."""
        return self._task_factory

    def _make_socket_transport(self, sock, protocol, waiter=Nichts, *,
                               extra=Nichts, server=Nichts):
        """Create socket transport."""
        raise NotImplementedError

    def _make_ssl_transport(
            self, rawsock, protocol, sslcontext, waiter=Nichts,
            *, server_side=Falsch, server_hostname=Nichts,
            extra=Nichts, server=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            call_connection_made=Wahr):
        """Create SSL transport."""
        raise NotImplementedError

    def _make_datagram_transport(self, sock, protocol,
                                 address=Nichts, waiter=Nichts, extra=Nichts):
        """Create datagram transport."""
        raise NotImplementedError

    def _make_read_pipe_transport(self, pipe, protocol, waiter=Nichts,
                                  extra=Nichts):
        """Create read pipe transport."""
        raise NotImplementedError

    def _make_write_pipe_transport(self, pipe, protocol, waiter=Nichts,
                                   extra=Nichts):
        """Create write pipe transport."""
        raise NotImplementedError

    async def _make_subprocess_transport(self, protocol, args, shell,
                                         stdin, stdout, stderr, bufsize,
                                         extra=Nichts, **kwargs):
        """Create subprocess transport."""
        raise NotImplementedError

    def _write_to_self(self):
        """Write a byte to self-pipe, to wake up the event loop.

        This may be called von a different thread.

        The subclass is responsible fuer implementing the self-pipe.
        """
        raise NotImplementedError

    def _process_events(self, event_list):
        """Process selector events."""
        raise NotImplementedError

    def _check_closed(self):
        wenn self._closed:
            raise RuntimeError('Event loop is closed')

    def _check_default_executor(self):
        wenn self._executor_shutdown_called:
            raise RuntimeError('Executor shutdown has been called')

    def _asyncgen_finalizer_hook(self, agen):
        self._asyncgens.discard(agen)
        wenn not self.is_closed():
            self.call_soon_threadsafe(self.create_task, agen.aclose())

    def _asyncgen_firstiter_hook(self, agen):
        wenn self._asyncgens_shutdown_called:
            warnings.warn(
                f"asynchronous generator {agen!r} was scheduled after "
                f"loop.shutdown_asyncgens() call",
                ResourceWarning, source=self)

        self._asyncgens.add(agen)

    async def shutdown_asyncgens(self):
        """Shutdown all active asynchronous generators."""
        self._asyncgens_shutdown_called = Wahr

        wenn not len(self._asyncgens):
            # If Python version is <3.6 or we don't have any asynchronous
            # generators alive.
            return

        closing_agens = list(self._asyncgens)
        self._asyncgens.clear()

        results = await tasks.gather(
            *[ag.aclose() fuer ag in closing_agens],
            return_exceptions=Wahr)

        fuer result, agen in zip(results, closing_agens):
            wenn isinstance(result, Exception):
                self.call_exception_handler({
                    'message': f'an error occurred during closing of '
                               f'asynchronous generator {agen!r}',
                    'exception': result,
                    'asyncgen': agen
                })

    async def shutdown_default_executor(self, timeout=Nichts):
        """Schedule the shutdown of the default executor.

        The timeout parameter specifies the amount of time the executor will
        be given to finish joining. The default value is Nichts, which means
        that the executor will be given an unlimited amount of time.
        """
        self._executor_shutdown_called = Wahr
        wenn self._default_executor is Nichts:
            return
        future = self.create_future()
        thread = threading.Thread(target=self._do_shutdown, args=(future,))
        thread.start()
        try:
            async with timeouts.timeout(timeout):
                await future
        except TimeoutError:
            warnings.warn("The executor did not finishing joining "
                          f"its threads within {timeout} seconds.",
                          RuntimeWarning, stacklevel=2)
            self._default_executor.shutdown(wait=Falsch)
        sonst:
            thread.join()

    def _do_shutdown(self, future):
        try:
            self._default_executor.shutdown(wait=Wahr)
            wenn not self.is_closed():
                self.call_soon_threadsafe(futures._set_result_unless_cancelled,
                                          future, Nichts)
        except Exception as ex:
            wenn not self.is_closed() and not future.cancelled():
                self.call_soon_threadsafe(future.set_exception, ex)

    def _check_running(self):
        wenn self.is_running():
            raise RuntimeError('This event loop is already running')
        wenn events._get_running_loop() is not Nichts:
            raise RuntimeError(
                'Cannot run the event loop while another loop is running')

    def _run_forever_setup(self):
        """Prepare the run loop to process events.

        This method exists so that custom event loop subclasses (e.g., event loops
        that integrate a GUI event loop with Python's event loop) have access to all the
        loop setup logic.
        """
        self._check_closed()
        self._check_running()
        self._set_coroutine_origin_tracking(self._debug)

        self._old_agen_hooks = sys.get_asyncgen_hooks()
        self._thread_id = threading.get_ident()
        sys.set_asyncgen_hooks(
            firstiter=self._asyncgen_firstiter_hook,
            finalizer=self._asyncgen_finalizer_hook
        )

        events._set_running_loop(self)

    def _run_forever_cleanup(self):
        """Clean up after an event loop finishes the looping over events.

        This method exists so that custom event loop subclasses (e.g., event loops
        that integrate a GUI event loop with Python's event loop) have access to all the
        loop cleanup logic.
        """
        self._stopping = Falsch
        self._thread_id = Nichts
        events._set_running_loop(Nichts)
        self._set_coroutine_origin_tracking(Falsch)
        # Restore any pre-existing async generator hooks.
        wenn self._old_agen_hooks is not Nichts:
            sys.set_asyncgen_hooks(*self._old_agen_hooks)
            self._old_agen_hooks = Nichts

    def run_forever(self):
        """Run until stop() is called."""
        self._run_forever_setup()
        try:
            while Wahr:
                self._run_once()
                wenn self._stopping:
                    break
        finally:
            self._run_forever_cleanup()

    def run_until_complete(self, future):
        """Run until the Future is done.

        If the argument is a coroutine, it is wrapped in a Task.

        WARNING: It would be disastrous to call run_until_complete()
        with the same coroutine twice -- it would wrap it in two
        different Tasks and that can't be good.

        Return the Future's result, or raise its exception.
        """
        self._check_closed()
        self._check_running()

        new_task = not futures.isfuture(future)
        future = tasks.ensure_future(future, loop=self)
        wenn new_task:
            # An exception is raised wenn the future didn't complete, so there
            # is no need to log the "destroy pending task" message
            future._log_destroy_pending = Falsch

        future.add_done_callback(_run_until_complete_cb)
        try:
            self.run_forever()
        except:
            wenn new_task and future.done() and not future.cancelled():
                # The coroutine raised a BaseException. Consume the exception
                # to not log a warning, the caller doesn't have access to the
                # local task.
                future.exception()
            raise
        finally:
            future.remove_done_callback(_run_until_complete_cb)
        wenn not future.done():
            raise RuntimeError('Event loop stopped before Future completed.')

        return future.result()

    def stop(self):
        """Stop running the event loop.

        Every callback already scheduled will still run.  This simply informs
        run_forever to stop looping after a complete iteration.
        """
        self._stopping = Wahr

    def close(self):
        """Close the event loop.

        This clears the queues and shuts down the executor,
        but does not wait fuer the executor to finish.

        The event loop must not be running.
        """
        wenn self.is_running():
            raise RuntimeError("Cannot close a running event loop")
        wenn self._closed:
            return
        wenn self._debug:
            logger.debug("Close %r", self)
        self._closed = Wahr
        self._ready.clear()
        self._scheduled.clear()
        self._executor_shutdown_called = Wahr
        executor = self._default_executor
        wenn executor is not Nichts:
            self._default_executor = Nichts
            executor.shutdown(wait=Falsch)

    def is_closed(self):
        """Returns Wahr wenn the event loop was closed."""
        return self._closed

    def __del__(self, _warn=warnings.warn):
        wenn not self.is_closed():
            _warn(f"unclosed event loop {self!r}", ResourceWarning, source=self)
            wenn not self.is_running():
                self.close()

    def is_running(self):
        """Returns Wahr wenn the event loop is running."""
        return (self._thread_id is not Nichts)

    def time(self):
        """Return the time according to the event loop's clock.

        This is a float expressed in seconds since an epoch, but the
        epoch, precision, accuracy and drift are unspecified and may
        differ per event loop.
        """
        return time.monotonic()

    def call_later(self, delay, callback, *args, context=Nichts):
        """Arrange fuer a callback to be called at a given time.

        Return a Handle: an opaque object with a cancel() method that
        can be used to cancel the call.

        The delay can be an int or float, expressed in seconds.  It is
        always relative to the current time.

        Each callback will be called exactly once.  If two callbacks
        are scheduled fuer exactly the same time, it is undefined which
        will be called first.

        Any positional arguments after the callback will be passed to
        the callback when it is called.
        """
        wenn delay is Nichts:
            raise TypeError('delay must not be Nichts')
        timer = self.call_at(self.time() + delay, callback, *args,
                             context=context)
        wenn timer._source_traceback:
            del timer._source_traceback[-1]
        return timer

    def call_at(self, when, callback, *args, context=Nichts):
        """Like call_later(), but uses an absolute time.

        Absolute time corresponds to the event loop's time() method.
        """
        wenn when is Nichts:
            raise TypeError("when cannot be Nichts")
        self._check_closed()
        wenn self._debug:
            self._check_thread()
            self._check_callback(callback, 'call_at')
        timer = events.TimerHandle(when, callback, args, self, context)
        wenn timer._source_traceback:
            del timer._source_traceback[-1]
        heapq.heappush(self._scheduled, timer)
        timer._scheduled = Wahr
        return timer

    def call_soon(self, callback, *args, context=Nichts):
        """Arrange fuer a callback to be called as soon as possible.

        This operates as a FIFO queue: callbacks are called in the
        order in which they are registered.  Each callback will be
        called exactly once.

        Any positional arguments after the callback will be passed to
        the callback when it is called.
        """
        self._check_closed()
        wenn self._debug:
            self._check_thread()
            self._check_callback(callback, 'call_soon')
        handle = self._call_soon(callback, args, context)
        wenn handle._source_traceback:
            del handle._source_traceback[-1]
        return handle

    def _check_callback(self, callback, method):
        wenn (coroutines.iscoroutine(callback) or
                coroutines._iscoroutinefunction(callback)):
            raise TypeError(
                f"coroutines cannot be used with {method}()")
        wenn not callable(callback):
            raise TypeError(
                f'a callable object was expected by {method}(), '
                f'got {callback!r}')

    def _call_soon(self, callback, args, context):
        handle = events.Handle(callback, args, self, context)
        wenn handle._source_traceback:
            del handle._source_traceback[-1]
        self._ready.append(handle)
        return handle

    def _check_thread(self):
        """Check that the current thread is the thread running the event loop.

        Non-thread-safe methods of this klasse make this assumption and will
        likely behave incorrectly when the assumption is violated.

        Should only be called when (self._debug == Wahr).  The caller is
        responsible fuer checking this condition fuer performance reasons.
        """
        wenn self._thread_id is Nichts:
            return
        thread_id = threading.get_ident()
        wenn thread_id != self._thread_id:
            raise RuntimeError(
                "Non-thread-safe operation invoked on an event loop other "
                "than the current one")

    def call_soon_threadsafe(self, callback, *args, context=Nichts):
        """Like call_soon(), but thread-safe."""
        self._check_closed()
        wenn self._debug:
            self._check_callback(callback, 'call_soon_threadsafe')
        handle = events._ThreadSafeHandle(callback, args, self, context)
        self._ready.append(handle)
        wenn handle._source_traceback:
            del handle._source_traceback[-1]
        wenn handle._source_traceback:
            del handle._source_traceback[-1]
        self._write_to_self()
        return handle

    def run_in_executor(self, executor, func, *args):
        self._check_closed()
        wenn self._debug:
            self._check_callback(func, 'run_in_executor')
        wenn executor is Nichts:
            executor = self._default_executor
            # Only check when the default executor is being used
            self._check_default_executor()
            wenn executor is Nichts:
                executor = concurrent.futures.ThreadPoolExecutor(
                    thread_name_prefix='asyncio'
                )
                self._default_executor = executor
        return futures.wrap_future(
            executor.submit(func, *args), loop=self)

    def set_default_executor(self, executor):
        wenn not isinstance(executor, concurrent.futures.ThreadPoolExecutor):
            raise TypeError('executor must be ThreadPoolExecutor instance')
        self._default_executor = executor

    def _getaddrinfo_debug(self, host, port, family, type, proto, flags):
        msg = [f"{host}:{port!r}"]
        wenn family:
            msg.append(f'family={family!r}')
        wenn type:
            msg.append(f'type={type!r}')
        wenn proto:
            msg.append(f'proto={proto!r}')
        wenn flags:
            msg.append(f'flags={flags!r}')
        msg = ', '.join(msg)
        logger.debug('Get address info %s', msg)

        t0 = self.time()
        addrinfo = socket.getaddrinfo(host, port, family, type, proto, flags)
        dt = self.time() - t0

        msg = f'Getting address info {msg} took {dt * 1e3:.3f}ms: {addrinfo!r}'
        wenn dt >= self.slow_callback_duration:
            logger.info(msg)
        sonst:
            logger.debug(msg)
        return addrinfo

    async def getaddrinfo(self, host, port, *,
                          family=0, type=0, proto=0, flags=0):
        wenn self._debug:
            getaddr_func = self._getaddrinfo_debug
        sonst:
            getaddr_func = socket.getaddrinfo

        return await self.run_in_executor(
            Nichts, getaddr_func, host, port, family, type, proto, flags)

    async def getnameinfo(self, sockaddr, flags=0):
        return await self.run_in_executor(
            Nichts, socket.getnameinfo, sockaddr, flags)

    async def sock_sendfile(self, sock, file, offset=0, count=Nichts,
                            *, fallback=Wahr):
        wenn self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        _check_ssl_socket(sock)
        self._check_sendfile_params(sock, file, offset, count)
        try:
            return await self._sock_sendfile_native(sock, file,
                                                    offset, count)
        except exceptions.SendfileNotAvailableError as exc:
            wenn not fallback:
                raise
        return await self._sock_sendfile_fallback(sock, file,
                                                  offset, count)

    async def _sock_sendfile_native(self, sock, file, offset, count):
        # NB: sendfile syscall is not supported fuer SSL sockets and
        # non-mmap files even wenn sendfile is supported by OS
        raise exceptions.SendfileNotAvailableError(
            f"syscall sendfile is not available fuer socket {sock!r} "
            f"and file {file!r} combination")

    async def _sock_sendfile_fallback(self, sock, file, offset, count):
        wenn offset:
            file.seek(offset)
        blocksize = (
            min(count, constants.SENDFILE_FALLBACK_READBUFFER_SIZE)
            wenn count sonst constants.SENDFILE_FALLBACK_READBUFFER_SIZE
        )
        buf = bytearray(blocksize)
        total_sent = 0
        try:
            while Wahr:
                wenn count:
                    blocksize = min(count - total_sent, blocksize)
                    wenn blocksize <= 0:
                        break
                view = memoryview(buf)[:blocksize]
                read = await self.run_in_executor(Nichts, file.readinto, view)
                wenn not read:
                    break  # EOF
                await self.sock_sendall(sock, view[:read])
                total_sent += read
            return total_sent
        finally:
            wenn total_sent > 0 and hasattr(file, 'seek'):
                file.seek(offset + total_sent)

    def _check_sendfile_params(self, sock, file, offset, count):
        wenn 'b' not in getattr(file, 'mode', 'b'):
            raise ValueError("file should be opened in binary mode")
        wenn not sock.type == socket.SOCK_STREAM:
            raise ValueError("only SOCK_STREAM type sockets are supported")
        wenn count is not Nichts:
            wenn not isinstance(count, int):
                raise TypeError(
                    "count must be a positive integer (got {!r})".format(count))
            wenn count <= 0:
                raise ValueError(
                    "count must be a positive integer (got {!r})".format(count))
        wenn not isinstance(offset, int):
            raise TypeError(
                "offset must be a non-negative integer (got {!r})".format(
                    offset))
        wenn offset < 0:
            raise ValueError(
                "offset must be a non-negative integer (got {!r})".format(
                    offset))

    async def _connect_sock(self, exceptions, addr_info, local_addr_infos=Nichts):
        """Create, bind and connect one socket."""
        my_exceptions = []
        exceptions.append(my_exceptions)
        family, type_, proto, _, address = addr_info
        sock = Nichts
        try:
            try:
                sock = socket.socket(family=family, type=type_, proto=proto)
                sock.setblocking(Falsch)
                wenn local_addr_infos is not Nichts:
                    fuer lfamily, _, _, _, laddr in local_addr_infos:
                        # skip local addresses of different family
                        wenn lfamily != family:
                            continue
                        try:
                            sock.bind(laddr)
                            break
                        except OSError as exc:
                            msg = (
                                f'error while attempting to bind on '
                                f'address {laddr!r}: {str(exc).lower()}'
                            )
                            exc = OSError(exc.errno, msg)
                            my_exceptions.append(exc)
                    sonst:  # all bind attempts failed
                        wenn my_exceptions:
                            raise my_exceptions.pop()
                        sonst:
                            raise OSError(f"no matching local address with {family=} found")
                await self.sock_connect(sock, address)
                return sock
            except OSError as exc:
                my_exceptions.append(exc)
                raise
        except:
            wenn sock is not Nichts:
                try:
                    sock.close()
                except OSError:
                    # An error when closing a newly created socket is
                    # not important, but it can overwrite more important
                    # non-OSError error. So ignore it.
                    pass
            raise
        finally:
            exceptions = my_exceptions = Nichts

    async def create_connection(
            self, protocol_factory, host=Nichts, port=Nichts,
            *, ssl=Nichts, family=0,
            proto=0, flags=0, sock=Nichts,
            local_addr=Nichts, server_hostname=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            happy_eyeballs_delay=Nichts, interleave=Nichts,
            all_errors=Falsch):
        """Connect to a TCP server.

        Create a streaming transport connection to a given internet host and
        port: socket family AF_INET or socket.AF_INET6 depending on host (or
        family wenn specified), socket type SOCK_STREAM. protocol_factory must be
        a callable returning a protocol instance.

        This method is a coroutine which will try to establish the connection
        in the background.  When successful, the coroutine returns a
        (transport, protocol) pair.
        """
        wenn server_hostname is not Nichts and not ssl:
            raise ValueError('server_hostname is only meaningful with ssl')

        wenn server_hostname is Nichts and ssl:
            # Use host as default fuer server_hostname.  It is an error
            # wenn host is empty or not set, e.g. when an
            # already-connected socket was passed or when only a port
            # is given.  To avoid this error, you can pass
            # server_hostname='' -- this will bypass the hostname
            # check.  (This also means that wenn host is a numeric
            # IP/IPv6 address, we will attempt to verify that exact
            # address; this will probably fail, but it is possible to
            # create a certificate fuer a specific IP address, so we
            # don't judge it here.)
            wenn not host:
                raise ValueError('You must set server_hostname '
                                 'when using ssl without a host')
            server_hostname = host

        wenn ssl_handshake_timeout is not Nichts and not ssl:
            raise ValueError(
                'ssl_handshake_timeout is only meaningful with ssl')

        wenn ssl_shutdown_timeout is not Nichts and not ssl:
            raise ValueError(
                'ssl_shutdown_timeout is only meaningful with ssl')

        wenn sock is not Nichts:
            _check_ssl_socket(sock)

        wenn happy_eyeballs_delay is not Nichts and interleave is Nichts:
            # If using happy eyeballs, default to interleave addresses by family
            interleave = 1

        wenn host is not Nichts or port is not Nichts:
            wenn sock is not Nichts:
                raise ValueError(
                    'host/port and sock can not be specified at the same time')

            infos = await self._ensure_resolved(
                (host, port), family=family,
                type=socket.SOCK_STREAM, proto=proto, flags=flags, loop=self)
            wenn not infos:
                raise OSError('getaddrinfo() returned empty list')

            wenn local_addr is not Nichts:
                laddr_infos = await self._ensure_resolved(
                    local_addr, family=family,
                    type=socket.SOCK_STREAM, proto=proto,
                    flags=flags, loop=self)
                wenn not laddr_infos:
                    raise OSError('getaddrinfo() returned empty list')
            sonst:
                laddr_infos = Nichts

            wenn interleave:
                infos = _interleave_addrinfos(infos, interleave)

            exceptions = []
            wenn happy_eyeballs_delay is Nichts:
                # not using happy eyeballs
                fuer addrinfo in infos:
                    try:
                        sock = await self._connect_sock(
                            exceptions, addrinfo, laddr_infos)
                        break
                    except OSError:
                        continue
            sonst:  # using happy eyeballs
                sock = (await staggered.staggered_race(
                    (
                        # can't use functools.partial as it keeps a reference
                        # to exceptions
                        lambda addrinfo=addrinfo: self._connect_sock(
                            exceptions, addrinfo, laddr_infos
                        )
                        fuer addrinfo in infos
                    ),
                    happy_eyeballs_delay,
                    loop=self,
                ))[0]  # can't use sock, _, _ as it keeks a reference to exceptions

            wenn sock is Nichts:
                exceptions = [exc fuer sub in exceptions fuer exc in sub]
                try:
                    wenn all_errors:
                        raise ExceptionGroup("create_connection failed", exceptions)
                    wenn len(exceptions) == 1:
                        raise exceptions[0]
                    sowenn exceptions:
                        # If they all have the same str(), raise one.
                        model = str(exceptions[0])
                        wenn all(str(exc) == model fuer exc in exceptions):
                            raise exceptions[0]
                        # Raise a combined exception so the user can see all
                        # the various error messages.
                        raise OSError('Multiple exceptions: {}'.format(
                            ', '.join(str(exc) fuer exc in exceptions)))
                    sonst:
                        # No exceptions were collected, raise a timeout error
                        raise TimeoutError('create_connection failed')
                finally:
                    exceptions = Nichts

        sonst:
            wenn sock is Nichts:
                raise ValueError(
                    'host and port was not specified and no sock specified')
            wenn sock.type != socket.SOCK_STREAM:
                # We allow AF_INET, AF_INET6, AF_UNIX as long as they
                # are SOCK_STREAM.
                # We support passing AF_UNIX sockets even though we have
                # a dedicated API fuer that: create_unix_connection.
                # Disallowing AF_UNIX in this method, breaks backwards
                # compatibility.
                raise ValueError(
                    f'A Stream Socket was expected, got {sock!r}')

        transport, protocol = await self._create_connection_transport(
            sock, protocol_factory, ssl, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        wenn self._debug:
            # Get the socket von the transport because SSL transport closes
            # the old socket and creates a new SSL socket
            sock = transport.get_extra_info('socket')
            logger.debug("%r connected to %s:%r: (%r, %r)",
                         sock, host, port, transport, protocol)
        return transport, protocol

    async def _create_connection_transport(
            self, sock, protocol_factory, ssl,
            server_hostname, server_side=Falsch,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):

        sock.setblocking(Falsch)

        protocol = protocol_factory()
        waiter = self.create_future()
        wenn ssl:
            sslcontext = Nichts wenn isinstance(ssl, bool) sonst ssl
            transport = self._make_ssl_transport(
                sock, protocol, sslcontext, waiter,
                server_side=server_side, server_hostname=server_hostname,
                ssl_handshake_timeout=ssl_handshake_timeout,
                ssl_shutdown_timeout=ssl_shutdown_timeout)
        sonst:
            transport = self._make_socket_transport(sock, protocol, waiter)

        try:
            await waiter
        except:
            transport.close()
            raise

        return transport, protocol

    async def sendfile(self, transport, file, offset=0, count=Nichts,
                       *, fallback=Wahr):
        """Send a file to transport.

        Return the total number of bytes which were sent.

        The method uses high-performance os.sendfile wenn available.

        file must be a regular file object opened in binary mode.

        offset tells von where to start reading the file. If specified,
        count is the total number of bytes to transmit as opposed to
        sending the file until EOF is reached. File position is updated on
        return or also in case of error in which case file.tell()
        can be used to figure out the number of bytes
        which were sent.

        fallback set to Wahr makes asyncio to manually read and send
        the file when the platform does not support the sendfile syscall
        (e.g. Windows or SSL socket on Unix).

        Raise SendfileNotAvailableError wenn the system does not support
        sendfile syscall and fallback is Falsch.
        """
        wenn transport.is_closing():
            raise RuntimeError("Transport is closing")
        mode = getattr(transport, '_sendfile_compatible',
                       constants._SendfileMode.UNSUPPORTED)
        wenn mode is constants._SendfileMode.UNSUPPORTED:
            raise RuntimeError(
                f"sendfile is not supported fuer transport {transport!r}")
        wenn mode is constants._SendfileMode.TRY_NATIVE:
            try:
                return await self._sendfile_native(transport, file,
                                                   offset, count)
            except exceptions.SendfileNotAvailableError as exc:
                wenn not fallback:
                    raise

        wenn not fallback:
            raise RuntimeError(
                f"fallback is disabled and native sendfile is not "
                f"supported fuer transport {transport!r}")

        return await self._sendfile_fallback(transport, file,
                                             offset, count)

    async def _sendfile_native(self, transp, file, offset, count):
        raise exceptions.SendfileNotAvailableError(
            "sendfile syscall is not supported")

    async def _sendfile_fallback(self, transp, file, offset, count):
        wenn offset:
            file.seek(offset)
        blocksize = min(count, 16384) wenn count sonst 16384
        buf = bytearray(blocksize)
        total_sent = 0
        proto = _SendfileFallbackProtocol(transp)
        try:
            while Wahr:
                wenn count:
                    blocksize = min(count - total_sent, blocksize)
                    wenn blocksize <= 0:
                        return total_sent
                view = memoryview(buf)[:blocksize]
                read = await self.run_in_executor(Nichts, file.readinto, view)
                wenn not read:
                    return total_sent  # EOF
                transp.write(view[:read])
                await proto.drain()
                total_sent += read
        finally:
            wenn total_sent > 0 and hasattr(file, 'seek'):
                file.seek(offset + total_sent)
            await proto.restore()

    async def start_tls(self, transport, protocol, sslcontext, *,
                        server_side=Falsch,
                        server_hostname=Nichts,
                        ssl_handshake_timeout=Nichts,
                        ssl_shutdown_timeout=Nichts):
        """Upgrade transport to TLS.

        Return a new transport that *protocol* should start using
        immediately.
        """
        wenn ssl is Nichts:
            raise RuntimeError('Python ssl module is not available')

        wenn not isinstance(sslcontext, ssl.SSLContext):
            raise TypeError(
                f'sslcontext is expected to be an instance of ssl.SSLContext, '
                f'got {sslcontext!r}')

        wenn not getattr(transport, '_start_tls_compatible', Falsch):
            raise TypeError(
                f'transport {transport!r} is not supported by start_tls()')

        waiter = self.create_future()
        ssl_protocol = sslproto.SSLProtocol(
            self, protocol, sslcontext, waiter,
            server_side, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout,
            call_connection_made=Falsch)

        # Pause early so that "ssl_protocol.data_received()" doesn't
        # have a chance to get called before "ssl_protocol.connection_made()".
        transport.pause_reading()

        transport.set_protocol(ssl_protocol)
        conmade_cb = self.call_soon(ssl_protocol.connection_made, transport)
        resume_cb = self.call_soon(transport.resume_reading)

        try:
            await waiter
        except BaseException:
            transport.close()
            conmade_cb.cancel()
            resume_cb.cancel()
            raise

        return ssl_protocol._app_transport

    async def create_datagram_endpoint(self, protocol_factory,
                                       local_addr=Nichts, remote_addr=Nichts, *,
                                       family=0, proto=0, flags=0,
                                       reuse_port=Nichts,
                                       allow_broadcast=Nichts, sock=Nichts):
        """Create datagram connection."""
        wenn sock is not Nichts:
            wenn sock.type == socket.SOCK_STREAM:
                raise ValueError(
                    f'A datagram socket was expected, got {sock!r}')
            wenn (local_addr or remote_addr or
                    family or proto or flags or
                    reuse_port or allow_broadcast):
                # show the problematic kwargs in exception msg
                opts = dict(local_addr=local_addr, remote_addr=remote_addr,
                            family=family, proto=proto, flags=flags,
                            reuse_port=reuse_port,
                            allow_broadcast=allow_broadcast)
                problems = ', '.join(f'{k}={v}' fuer k, v in opts.items() wenn v)
                raise ValueError(
                    f'socket modifier keyword arguments can not be used '
                    f'when sock is specified. ({problems})')
            sock.setblocking(Falsch)
            r_addr = Nichts
        sonst:
            wenn not (local_addr or remote_addr):
                wenn family == 0:
                    raise ValueError('unexpected address family')
                addr_pairs_info = (((family, proto), (Nichts, Nichts)),)
            sowenn hasattr(socket, 'AF_UNIX') and family == socket.AF_UNIX:
                fuer addr in (local_addr, remote_addr):
                    wenn addr is not Nichts and not isinstance(addr, str):
                        raise TypeError('string is expected')

                wenn local_addr and local_addr[0] not in (0, '\x00'):
                    try:
                        wenn stat.S_ISSOCK(os.stat(local_addr).st_mode):
                            os.remove(local_addr)
                    except FileNotFoundError:
                        pass
                    except OSError as err:
                        # Directory may have permissions only to create socket.
                        logger.error('Unable to check or remove stale UNIX '
                                     'socket %r: %r',
                                     local_addr, err)

                addr_pairs_info = (((family, proto),
                                    (local_addr, remote_addr)), )
            sonst:
                # join address by (family, protocol)
                addr_infos = {}  # Using order preserving dict
                fuer idx, addr in ((0, local_addr), (1, remote_addr)):
                    wenn addr is not Nichts:
                        wenn not (isinstance(addr, tuple) and len(addr) == 2):
                            raise TypeError('2-tuple is expected')

                        infos = await self._ensure_resolved(
                            addr, family=family, type=socket.SOCK_DGRAM,
                            proto=proto, flags=flags, loop=self)
                        wenn not infos:
                            raise OSError('getaddrinfo() returned empty list')

                        fuer fam, _, pro, _, address in infos:
                            key = (fam, pro)
                            wenn key not in addr_infos:
                                addr_infos[key] = [Nichts, Nichts]
                            addr_infos[key][idx] = address

                # each addr has to have info fuer each (family, proto) pair
                addr_pairs_info = [
                    (key, addr_pair) fuer key, addr_pair in addr_infos.items()
                    wenn not ((local_addr and addr_pair[0] is Nichts) or
                            (remote_addr and addr_pair[1] is Nichts))]

                wenn not addr_pairs_info:
                    raise ValueError('can not get address information')

            exceptions = []

            fuer ((family, proto),
                 (local_address, remote_address)) in addr_pairs_info:
                sock = Nichts
                r_addr = Nichts
                try:
                    sock = socket.socket(
                        family=family, type=socket.SOCK_DGRAM, proto=proto)
                    wenn reuse_port:
                        _set_reuseport(sock)
                    wenn allow_broadcast:
                        sock.setsockopt(
                            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.setblocking(Falsch)

                    wenn local_addr:
                        sock.bind(local_address)
                    wenn remote_addr:
                        wenn not allow_broadcast:
                            await self.sock_connect(sock, remote_address)
                        r_addr = remote_address
                except OSError as exc:
                    wenn sock is not Nichts:
                        sock.close()
                    exceptions.append(exc)
                except:
                    wenn sock is not Nichts:
                        sock.close()
                    raise
                sonst:
                    break
            sonst:
                raise exceptions[0]

        protocol = protocol_factory()
        waiter = self.create_future()
        transport = self._make_datagram_transport(
            sock, protocol, r_addr, waiter)
        wenn self._debug:
            wenn local_addr:
                logger.info("Datagram endpoint local_addr=%r remote_addr=%r "
                            "created: (%r, %r)",
                            local_addr, remote_addr, transport, protocol)
            sonst:
                logger.debug("Datagram endpoint remote_addr=%r created: "
                             "(%r, %r)",
                             remote_addr, transport, protocol)

        try:
            await waiter
        except:
            transport.close()
            raise

        return transport, protocol

    async def _ensure_resolved(self, address, *,
                               family=0, type=socket.SOCK_STREAM,
                               proto=0, flags=0, loop):
        host, port = address[:2]
        info = _ipaddr_info(host, port, family, type, proto, *address[2:])
        wenn info is not Nichts:
            # "host" is already a resolved IP.
            return [info]
        sonst:
            return await loop.getaddrinfo(host, port, family=family, type=type,
                                          proto=proto, flags=flags)

    async def _create_server_getaddrinfo(self, host, port, family, flags):
        infos = await self._ensure_resolved((host, port), family=family,
                                            type=socket.SOCK_STREAM,
                                            flags=flags, loop=self)
        wenn not infos:
            raise OSError(f'getaddrinfo({host!r}) returned empty list')
        return infos

    async def create_server(
            self, protocol_factory, host=Nichts, port=Nichts,
            *,
            family=socket.AF_UNSPEC,
            flags=socket.AI_PASSIVE,
            sock=Nichts,
            backlog=100,
            ssl=Nichts,
            reuse_address=Nichts,
            reuse_port=Nichts,
            keep_alive=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            start_serving=Wahr):
        """Create a TCP server.

        The host parameter can be a string, in that case the TCP server is
        bound to host and port.

        The host parameter can also be a sequence of strings and in that case
        the TCP server is bound to all hosts of the sequence. If a host
        appears multiple times (possibly indirectly e.g. when hostnames
        resolve to the same IP address), the server is only bound once to that
        host.

        Return a Server object which can be used to stop the service.

        This method is a coroutine.
        """
        wenn isinstance(ssl, bool):
            raise TypeError('ssl argument must be an SSLContext or Nichts')

        wenn ssl_handshake_timeout is not Nichts and ssl is Nichts:
            raise ValueError(
                'ssl_handshake_timeout is only meaningful with ssl')

        wenn ssl_shutdown_timeout is not Nichts and ssl is Nichts:
            raise ValueError(
                'ssl_shutdown_timeout is only meaningful with ssl')

        wenn sock is not Nichts:
            _check_ssl_socket(sock)

        wenn host is not Nichts or port is not Nichts:
            wenn sock is not Nichts:
                raise ValueError(
                    'host/port and sock can not be specified at the same time')

            wenn reuse_address is Nichts:
                reuse_address = os.name == "posix" and sys.platform != "cygwin"
            sockets = []
            wenn host == '':
                hosts = [Nichts]
            sowenn (isinstance(host, str) or
                  not isinstance(host, collections.abc.Iterable)):
                hosts = [host]
            sonst:
                hosts = host

            fs = [self._create_server_getaddrinfo(host, port, family=family,
                                                  flags=flags)
                  fuer host in hosts]
            infos = await tasks.gather(*fs)
            infos = set(itertools.chain.from_iterable(infos))

            completed = Falsch
            try:
                fuer res in infos:
                    af, socktype, proto, canonname, sa = res
                    try:
                        sock = socket.socket(af, socktype, proto)
                    except socket.error:
                        # Assume it's a bad family/type/protocol combination.
                        wenn self._debug:
                            logger.warning('create_server() failed to create '
                                           'socket.socket(%r, %r, %r)',
                                           af, socktype, proto, exc_info=Wahr)
                        continue
                    sockets.append(sock)
                    wenn reuse_address:
                        sock.setsockopt(
                            socket.SOL_SOCKET, socket.SO_REUSEADDR, Wahr)
                    # Since Linux 6.12.9, SO_REUSEPORT is not allowed
                    # on other address families than AF_INET/AF_INET6.
                    wenn reuse_port and af in (socket.AF_INET, socket.AF_INET6):
                        _set_reuseport(sock)
                    wenn keep_alive:
                        sock.setsockopt(
                            socket.SOL_SOCKET, socket.SO_KEEPALIVE, Wahr)
                    # Disable IPv4/IPv6 dual stack support (enabled by
                    # default on Linux) which makes a single socket
                    # listen on both address families.
                    wenn (_HAS_IPv6 and
                            af == socket.AF_INET6 and
                            hasattr(socket, 'IPPROTO_IPV6')):
                        sock.setsockopt(socket.IPPROTO_IPV6,
                                        socket.IPV6_V6ONLY,
                                        Wahr)
                    try:
                        sock.bind(sa)
                    except OSError as err:
                        msg = ('error while attempting '
                               'to bind on address %r: %s'
                               % (sa, str(err).lower()))
                        wenn err.errno == errno.EADDRNOTAVAIL:
                            # Assume the family is not enabled (bpo-30945)
                            sockets.pop()
                            sock.close()
                            wenn self._debug:
                                logger.warning(msg)
                            continue
                        raise OSError(err.errno, msg) von Nichts

                wenn not sockets:
                    raise OSError('could not bind on any address out of %r'
                                  % ([info[4] fuer info in infos],))

                completed = Wahr
            finally:
                wenn not completed:
                    fuer sock in sockets:
                        sock.close()
        sonst:
            wenn sock is Nichts:
                raise ValueError('Neither host/port nor sock were specified')
            wenn sock.type != socket.SOCK_STREAM:
                raise ValueError(f'A Stream Socket was expected, got {sock!r}')
            sockets = [sock]

        fuer sock in sockets:
            sock.setblocking(Falsch)

        server = Server(self, sockets, protocol_factory,
                        ssl, backlog, ssl_handshake_timeout,
                        ssl_shutdown_timeout)
        wenn start_serving:
            server._start_serving()
            # Skip one loop iteration so that all 'loop.add_reader'
            # go through.
            await tasks.sleep(0)

        wenn self._debug:
            logger.info("%r is serving", server)
        return server

    async def connect_accepted_socket(
            self, protocol_factory, sock,
            *, ssl=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):
        wenn sock.type != socket.SOCK_STREAM:
            raise ValueError(f'A Stream Socket was expected, got {sock!r}')

        wenn ssl_handshake_timeout is not Nichts and not ssl:
            raise ValueError(
                'ssl_handshake_timeout is only meaningful with ssl')

        wenn ssl_shutdown_timeout is not Nichts and not ssl:
            raise ValueError(
                'ssl_shutdown_timeout is only meaningful with ssl')

        _check_ssl_socket(sock)

        transport, protocol = await self._create_connection_transport(
            sock, protocol_factory, ssl, '', server_side=Wahr,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        wenn self._debug:
            # Get the socket von the transport because SSL transport closes
            # the old socket and creates a new SSL socket
            sock = transport.get_extra_info('socket')
            logger.debug("%r handled: (%r, %r)", sock, transport, protocol)
        return transport, protocol

    async def connect_read_pipe(self, protocol_factory, pipe):
        protocol = protocol_factory()
        waiter = self.create_future()
        transport = self._make_read_pipe_transport(pipe, protocol, waiter)

        try:
            await waiter
        except:
            transport.close()
            raise

        wenn self._debug:
            logger.debug('Read pipe %r connected: (%r, %r)',
                         pipe.fileno(), transport, protocol)
        return transport, protocol

    async def connect_write_pipe(self, protocol_factory, pipe):
        protocol = protocol_factory()
        waiter = self.create_future()
        transport = self._make_write_pipe_transport(pipe, protocol, waiter)

        try:
            await waiter
        except:
            transport.close()
            raise

        wenn self._debug:
            logger.debug('Write pipe %r connected: (%r, %r)',
                         pipe.fileno(), transport, protocol)
        return transport, protocol

    def _log_subprocess(self, msg, stdin, stdout, stderr):
        info = [msg]
        wenn stdin is not Nichts:
            info.append(f'stdin={_format_pipe(stdin)}')
        wenn stdout is not Nichts and stderr == subprocess.STDOUT:
            info.append(f'stdout=stderr={_format_pipe(stdout)}')
        sonst:
            wenn stdout is not Nichts:
                info.append(f'stdout={_format_pipe(stdout)}')
            wenn stderr is not Nichts:
                info.append(f'stderr={_format_pipe(stderr)}')
        logger.debug(' '.join(info))

    async def subprocess_shell(self, protocol_factory, cmd, *,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=Falsch,
                               shell=Wahr, bufsize=0,
                               encoding=Nichts, errors=Nichts, text=Nichts,
                               **kwargs):
        wenn not isinstance(cmd, (bytes, str)):
            raise ValueError("cmd must be a string")
        wenn universal_newlines:
            raise ValueError("universal_newlines must be Falsch")
        wenn not shell:
            raise ValueError("shell must be Wahr")
        wenn bufsize != 0:
            raise ValueError("bufsize must be 0")
        wenn text:
            raise ValueError("text must be Falsch")
        wenn encoding is not Nichts:
            raise ValueError("encoding must be Nichts")
        wenn errors is not Nichts:
            raise ValueError("errors must be Nichts")

        protocol = protocol_factory()
        debug_log = Nichts
        wenn self._debug:
            # don't log parameters: they may contain sensitive information
            # (password) and may be too long
            debug_log = 'run shell command %r' % cmd
            self._log_subprocess(debug_log, stdin, stdout, stderr)
        transport = await self._make_subprocess_transport(
            protocol, cmd, Wahr, stdin, stdout, stderr, bufsize, **kwargs)
        wenn self._debug and debug_log is not Nichts:
            logger.info('%s: %r', debug_log, transport)
        return transport, protocol

    async def subprocess_exec(self, protocol_factory, program, *args,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=Falsch,
                              shell=Falsch, bufsize=0,
                              encoding=Nichts, errors=Nichts, text=Nichts,
                              **kwargs):
        wenn universal_newlines:
            raise ValueError("universal_newlines must be Falsch")
        wenn shell:
            raise ValueError("shell must be Falsch")
        wenn bufsize != 0:
            raise ValueError("bufsize must be 0")
        wenn text:
            raise ValueError("text must be Falsch")
        wenn encoding is not Nichts:
            raise ValueError("encoding must be Nichts")
        wenn errors is not Nichts:
            raise ValueError("errors must be Nichts")

        popen_args = (program,) + args
        protocol = protocol_factory()
        debug_log = Nichts
        wenn self._debug:
            # don't log parameters: they may contain sensitive information
            # (password) and may be too long
            debug_log = f'execute program {program!r}'
            self._log_subprocess(debug_log, stdin, stdout, stderr)
        transport = await self._make_subprocess_transport(
            protocol, popen_args, Falsch, stdin, stdout, stderr,
            bufsize, **kwargs)
        wenn self._debug and debug_log is not Nichts:
            logger.info('%s: %r', debug_log, transport)
        return transport, protocol

    def get_exception_handler(self):
        """Return an exception handler, or Nichts wenn the default one is in use.
        """
        return self._exception_handler

    def set_exception_handler(self, handler):
        """Set handler as the new event loop exception handler.

        If handler is Nichts, the default exception handler will
        be set.

        If handler is a callable object, it should have a
        signature matching '(loop, context)', where 'loop'
        will be a reference to the active event loop, 'context'
        will be a dict object (see `call_exception_handler()`
        documentation fuer details about context).
        """
        wenn handler is not Nichts and not callable(handler):
            raise TypeError(f'A callable object or Nichts is expected, '
                            f'got {handler!r}')
        self._exception_handler = handler

    def default_exception_handler(self, context):
        """Default exception handler.

        This is called when an exception occurs and no exception
        handler is set, and can be called by a custom exception
        handler that wants to defer to the default behavior.

        This default handler logs the error message and other
        context-dependent information.  In debug mode, a truncated
        stack trace is also appended showing where the given object
        (e.g. a handle or future or task) was created, wenn any.

        The context parameter has the same meaning as in
        `call_exception_handler()`.
        """
        message = context.get('message')
        wenn not message:
            message = 'Unhandled exception in event loop'

        exception = context.get('exception')
        wenn exception is not Nichts:
            exc_info = (type(exception), exception, exception.__traceback__)
        sonst:
            exc_info = Falsch

        wenn ('source_traceback' not in context and
                self._current_handle is not Nichts and
                self._current_handle._source_traceback):
            context['handle_traceback'] = \
                self._current_handle._source_traceback

        log_lines = [message]
        fuer key in sorted(context):
            wenn key in {'message', 'exception'}:
                continue
            value = context[key]
            wenn key == 'source_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Object created at (most recent call last):\n'
                value += tb.rstrip()
            sowenn key == 'handle_traceback':
                tb = ''.join(traceback.format_list(value))
                value = 'Handle created at (most recent call last):\n'
                value += tb.rstrip()
            sonst:
                value = repr(value)
            log_lines.append(f'{key}: {value}')

        logger.error('\n'.join(log_lines), exc_info=exc_info)

    def call_exception_handler(self, context):
        """Call the current event loop's exception handler.

        The context argument is a dict containing the following keys:

        - 'message': Error message;
        - 'exception' (optional): Exception object;
        - 'future' (optional): Future instance;
        - 'task' (optional): Task instance;
        - 'handle' (optional): Handle instance;
        - 'protocol' (optional): Protocol instance;
        - 'transport' (optional): Transport instance;
        - 'socket' (optional): Socket instance;
        - 'source_traceback' (optional): Traceback of the source;
        - 'handle_traceback' (optional): Traceback of the handle;
        - 'asyncgen' (optional): Asynchronous generator that caused
                                 the exception.

        New keys maybe introduced in the future.

        Note: do not overload this method in an event loop subclass.
        For custom exception handling, use the
        `set_exception_handler()` method.
        """
        wenn self._exception_handler is Nichts:
            try:
                self.default_exception_handler(context)
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException:
                # Second protection layer fuer unexpected errors
                # in the default implementation, as well as fuer subclassed
                # event loops with overloaded "default_exception_handler".
                logger.error('Exception in default exception handler',
                             exc_info=Wahr)
        sonst:
            try:
                ctx = Nichts
                thing = context.get("task")
                wenn thing is Nichts:
                    # Even though Futures don't have a context,
                    # Task is a subclass of Future,
                    # and sometimes the 'future' key holds a Task.
                    thing = context.get("future")
                wenn thing is Nichts:
                    # Handles also have a context.
                    thing = context.get("handle")
                wenn thing is not Nichts and hasattr(thing, "get_context"):
                    ctx = thing.get_context()
                wenn ctx is not Nichts and hasattr(ctx, "run"):
                    ctx.run(self._exception_handler, self, context)
                sonst:
                    self._exception_handler(self, context)
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                # Exception in the user set custom exception handler.
                try:
                    # Let's try default handler.
                    self.default_exception_handler({
                        'message': 'Unhandled error in exception handler',
                        'exception': exc,
                        'context': context,
                    })
                except (SystemExit, KeyboardInterrupt):
                    raise
                except BaseException:
                    # Guard 'default_exception_handler' in case it is
                    # overloaded.
                    logger.error('Exception in default exception handler '
                                 'while handling an unexpected error '
                                 'in custom exception handler',
                                 exc_info=Wahr)

    def _add_callback(self, handle):
        """Add a Handle to _ready."""
        wenn not handle._cancelled:
            self._ready.append(handle)

    def _add_callback_signalsafe(self, handle):
        """Like _add_callback() but called von a signal handler."""
        self._add_callback(handle)
        self._write_to_self()

    def _timer_handle_cancelled(self, handle):
        """Notification that a TimerHandle has been cancelled."""
        wenn handle._scheduled:
            self._timer_cancelled_count += 1

    def _run_once(self):
        """Run one full iteration of the event loop.

        This calls all currently ready callbacks, polls fuer I/O,
        schedules the resulting callbacks, and finally schedules
        'call_later' callbacks.
        """

        sched_count = len(self._scheduled)
        wenn (sched_count > _MIN_SCHEDULED_TIMER_HANDLES and
            self._timer_cancelled_count / sched_count >
                _MIN_CANCELLED_TIMER_HANDLES_FRACTION):
            # Remove delayed calls that were cancelled wenn their number
            # is too high
            new_scheduled = []
            fuer handle in self._scheduled:
                wenn handle._cancelled:
                    handle._scheduled = Falsch
                sonst:
                    new_scheduled.append(handle)

            heapq.heapify(new_scheduled)
            self._scheduled = new_scheduled
            self._timer_cancelled_count = 0
        sonst:
            # Remove delayed calls that were cancelled von head of queue.
            while self._scheduled and self._scheduled[0]._cancelled:
                self._timer_cancelled_count -= 1
                handle = heapq.heappop(self._scheduled)
                handle._scheduled = Falsch

        timeout = Nichts
        wenn self._ready or self._stopping:
            timeout = 0
        sowenn self._scheduled:
            # Compute the desired timeout.
            timeout = self._scheduled[0]._when - self.time()
            wenn timeout > MAXIMUM_SELECT_TIMEOUT:
                timeout = MAXIMUM_SELECT_TIMEOUT
            sowenn timeout < 0:
                timeout = 0

        event_list = self._selector.select(timeout)
        self._process_events(event_list)
        # Needed to break cycles when an exception occurs.
        event_list = Nichts

        # Handle 'later' callbacks that are ready.
        end_time = self.time() + self._clock_resolution
        while self._scheduled:
            handle = self._scheduled[0]
            wenn handle._when >= end_time:
                break
            handle = heapq.heappop(self._scheduled)
            handle._scheduled = Falsch
            self._ready.append(handle)

        # This is the only place where callbacks are actually *called*.
        # All other places just add them to ready.
        # Note: We run all currently scheduled callbacks, but not any
        # callbacks scheduled by callbacks run this time around --
        # they will be run the next time (after another I/O poll).
        # Use an idiom that is thread-safe without using locks.
        ntodo = len(self._ready)
        fuer i in range(ntodo):
            handle = self._ready.popleft()
            wenn handle._cancelled:
                continue
            wenn self._debug:
                try:
                    self._current_handle = handle
                    t0 = self.time()
                    handle._run()
                    dt = self.time() - t0
                    wenn dt >= self.slow_callback_duration:
                        logger.warning('Executing %s took %.3f seconds',
                                       _format_handle(handle), dt)
                finally:
                    self._current_handle = Nichts
            sonst:
                handle._run()
        handle = Nichts  # Needed to break cycles when an exception occurs.

    def _set_coroutine_origin_tracking(self, enabled):
        wenn bool(enabled) == bool(self._coroutine_origin_tracking_enabled):
            return

        wenn enabled:
            self._coroutine_origin_tracking_saved_depth = (
                sys.get_coroutine_origin_tracking_depth())
            sys.set_coroutine_origin_tracking_depth(
                constants.DEBUG_STACK_DEPTH)
        sonst:
            sys.set_coroutine_origin_tracking_depth(
                self._coroutine_origin_tracking_saved_depth)

        self._coroutine_origin_tracking_enabled = enabled

    def get_debug(self):
        return self._debug

    def set_debug(self, enabled):
        self._debug = enabled

        wenn self.is_running():
            self.call_soon_threadsafe(self._set_coroutine_origin_tracking, enabled)
