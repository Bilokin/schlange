"""Event loop und event loop policy."""

# Contains code von https://github.com/MagicStack/uvloop/tree/v0.16.0
# SPDX-License-Identifier: PSF-2.0 AND (MIT OR Apache-2.0)
# SPDX-FileCopyrightText: Copyright (c) 2015-2021 MagicStack Inc.  http://magic.io

__all__ = (
    "AbstractEventLoop",
    "AbstractServer",
    "Handle",
    "TimerHandle",
    "get_event_loop_policy",
    "set_event_loop_policy",
    "get_event_loop",
    "set_event_loop",
    "new_event_loop",
    "_set_running_loop",
    "get_running_loop",
    "_get_running_loop",
)

importiere contextvars
importiere os
importiere signal
importiere socket
importiere subprocess
importiere sys
importiere threading
importiere warnings

von . importiere format_helpers


klasse Handle:
    """Object returned by callback registration methods."""

    __slots__ = ('_callback', '_args', '_cancelled', '_loop',
                 '_source_traceback', '_repr', '__weakref__',
                 '_context')

    def __init__(self, callback, args, loop, context=Nichts):
        wenn context is Nichts:
            context = contextvars.copy_context()
        self._context = context
        self._loop = loop
        self._callback = callback
        self._args = args
        self._cancelled = Falsch
        self._repr = Nichts
        wenn self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))
        sonst:
            self._source_traceback = Nichts

    def _repr_info(self):
        info = [self.__class__.__name__]
        wenn self._cancelled:
            info.append('cancelled')
        wenn self._callback is nicht Nichts:
            info.append(format_helpers._format_callback_source(
                self._callback, self._args,
                debug=self._loop.get_debug()))
        wenn self._source_traceback:
            frame = self._source_traceback[-1]
            info.append(f'created at {frame[0]}:{frame[1]}')
        gib info

    def __repr__(self):
        wenn self._repr is nicht Nichts:
            gib self._repr
        info = self._repr_info()
        gib '<{}>'.format(' '.join(info))

    def get_context(self):
        gib self._context

    def cancel(self):
        wenn nicht self._cancelled:
            self._cancelled = Wahr
            wenn self._loop.get_debug():
                # Keep a representation in debug mode to keep callback und
                # parameters. For example, to log the warning
                # "Executing <Handle...> took 2.5 second"
                self._repr = repr(self)
            self._callback = Nichts
            self._args = Nichts

    def cancelled(self):
        gib self._cancelled

    def _run(self):
        try:
            self._context.run(self._callback, *self._args)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException als exc:
            cb = format_helpers._format_callback_source(
                self._callback, self._args,
                debug=self._loop.get_debug())
            msg = f'Exception in callback {cb}'
            context = {
                'message': msg,
                'exception': exc,
                'handle': self,
            }
            wenn self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        self = Nichts  # Needed to breche cycles when an exception occurs.

# _ThreadSafeHandle is used fuer callbacks scheduled mit call_soon_threadsafe
# und is thread safe unlike Handle which is nicht thread safe.
klasse _ThreadSafeHandle(Handle):

    __slots__ = ('_lock',)

    def __init__(self, callback, args, loop, context=Nichts):
        super().__init__(callback, args, loop, context)
        self._lock = threading.RLock()

    def cancel(self):
        mit self._lock:
            gib super().cancel()

    def cancelled(self):
        mit self._lock:
            gib super().cancelled()

    def _run(self):
        # The event loop checks fuer cancellation without holding the lock
        # It is possible that the handle is cancelled after the check
        # but before the callback is called so check it again after acquiring
        # the lock und gib without calling the callback wenn it is cancelled.
        mit self._lock:
            wenn self._cancelled:
                gib
            gib super()._run()


klasse TimerHandle(Handle):
    """Object returned by timed callback registration methods."""

    __slots__ = ['_scheduled', '_when']

    def __init__(self, when, callback, args, loop, context=Nichts):
        super().__init__(callback, args, loop, context)
        wenn self._source_traceback:
            del self._source_traceback[-1]
        self._when = when
        self._scheduled = Falsch

    def _repr_info(self):
        info = super()._repr_info()
        pos = 2 wenn self._cancelled sonst 1
        info.insert(pos, f'when={self._when}')
        gib info

    def __hash__(self):
        gib hash(self._when)

    def __lt__(self, other):
        wenn isinstance(other, TimerHandle):
            gib self._when < other._when
        gib NotImplemented

    def __le__(self, other):
        wenn isinstance(other, TimerHandle):
            gib self._when < other._when oder self.__eq__(other)
        gib NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, TimerHandle):
            gib self._when > other._when
        gib NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, TimerHandle):
            gib self._when > other._when oder self.__eq__(other)
        gib NotImplemented

    def __eq__(self, other):
        wenn isinstance(other, TimerHandle):
            gib (self._when == other._when und
                    self._callback == other._callback und
                    self._args == other._args und
                    self._cancelled == other._cancelled)
        gib NotImplemented

    def cancel(self):
        wenn nicht self._cancelled:
            self._loop._timer_handle_cancelled(self)
        super().cancel()

    def when(self):
        """Return a scheduled callback time.

        The time is an absolute timestamp, using the same time
        reference als loop.time().
        """
        gib self._when


klasse AbstractServer:
    """Abstract server returned by create_server()."""

    def close(self):
        """Stop serving.  This leaves existing connections open."""
        raise NotImplementedError

    def close_clients(self):
        """Close all active connections."""
        raise NotImplementedError

    def abort_clients(self):
        """Close all active connections immediately."""
        raise NotImplementedError

    def get_loop(self):
        """Get the event loop the Server object is attached to."""
        raise NotImplementedError

    def is_serving(self):
        """Return Wahr wenn the server is accepting connections."""
        raise NotImplementedError

    async def start_serving(self):
        """Start accepting connections.

        This method is idempotent, so it can be called when
        the server is already being serving.
        """
        raise NotImplementedError

    async def serve_forever(self):
        """Start accepting connections until the coroutine is cancelled.

        The server is closed when the coroutine is cancelled.
        """
        raise NotImplementedError

    async def wait_closed(self):
        """Coroutine to wait until service is closed."""
        raise NotImplementedError

    async def __aenter__(self):
        gib self

    async def __aexit__(self, *exc):
        self.close()
        await self.wait_closed()


klasse AbstractEventLoop:
    """Abstract event loop."""

    # Running und stopping the event loop.

    def run_forever(self):
        """Run the event loop until stop() is called."""
        raise NotImplementedError

    def run_until_complete(self, future):
        """Run the event loop until a Future is done.

        Return the Future's result, oder raise its exception.
        """
        raise NotImplementedError

    def stop(self):
        """Stop the event loop als soon als reasonable.

        Exactly how soon that is may depend on the implementation, but
        no more I/O callbacks should be scheduled.
        """
        raise NotImplementedError

    def is_running(self):
        """Return whether the event loop is currently running."""
        raise NotImplementedError

    def is_closed(self):
        """Returns Wahr wenn the event loop was closed."""
        raise NotImplementedError

    def close(self):
        """Close the loop.

        The loop should nicht be running.

        This is idempotent und irreversible.

        No other methods should be called after this one.
        """
        raise NotImplementedError

    async def shutdown_asyncgens(self):
        """Shutdown all active asynchronous generators."""
        raise NotImplementedError

    async def shutdown_default_executor(self):
        """Schedule the shutdown of the default executor."""
        raise NotImplementedError

    # Methods scheduling callbacks.  All these gib Handles.

    def _timer_handle_cancelled(self, handle):
        """Notification that a TimerHandle has been cancelled."""
        raise NotImplementedError

    def call_soon(self, callback, *args, context=Nichts):
        gib self.call_later(0, callback, *args, context=context)

    def call_later(self, delay, callback, *args, context=Nichts):
        raise NotImplementedError

    def call_at(self, when, callback, *args, context=Nichts):
        raise NotImplementedError

    def time(self):
        raise NotImplementedError

    def create_future(self):
        raise NotImplementedError

    # Method scheduling a coroutine object: create a task.

    def create_task(self, coro, **kwargs):
        raise NotImplementedError

    # Methods fuer interacting mit threads.

    def call_soon_threadsafe(self, callback, *args, context=Nichts):
        raise NotImplementedError

    def run_in_executor(self, executor, func, *args):
        raise NotImplementedError

    def set_default_executor(self, executor):
        raise NotImplementedError

    # Network I/O methods returning Futures.

    async def getaddrinfo(self, host, port, *,
                          family=0, type=0, proto=0, flags=0):
        raise NotImplementedError

    async def getnameinfo(self, sockaddr, flags=0):
        raise NotImplementedError

    async def create_connection(
            self, protocol_factory, host=Nichts, port=Nichts,
            *, ssl=Nichts, family=0, proto=0,
            flags=0, sock=Nichts, local_addr=Nichts,
            server_hostname=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            happy_eyeballs_delay=Nichts, interleave=Nichts):
        raise NotImplementedError

    async def create_server(
            self, protocol_factory, host=Nichts, port=Nichts,
            *, family=socket.AF_UNSPEC,
            flags=socket.AI_PASSIVE, sock=Nichts, backlog=100,
            ssl=Nichts, reuse_address=Nichts, reuse_port=Nichts,
            keep_alive=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            start_serving=Wahr):
        """A coroutine which creates a TCP server bound to host und port.

        The gib value is a Server object which can be used to stop
        the service.

        If host is an empty string oder Nichts all interfaces are assumed
        und a list of multiple sockets will be returned (most likely
        one fuer IPv4 und another one fuer IPv6). The host parameter can also be
        a sequence (e.g. list) of hosts to bind to.

        family can be set to either AF_INET oder AF_INET6 to force the
        socket to use IPv4 oder IPv6. If nicht set it will be determined
        von host (defaults to AF_UNSPEC).

        flags is a bitmask fuer getaddrinfo().

        sock can optionally be specified in order to use a preexisting
        socket object.

        backlog is the maximum number of queued connections passed to
        listen() (defaults to 100).

        ssl can be set to an SSLContext to enable SSL over the
        accepted connections.

        reuse_address tells the kernel to reuse a local socket in
        TIME_WAIT state, without waiting fuer its natural timeout to
        expire. If nicht specified will automatically be set to Wahr on
        UNIX.

        reuse_port tells the kernel to allow this endpoint to be bound to
        the same port als other existing endpoints are bound to, so long as
        they all set this flag when being created. This option is not
        supported on Windows.

        keep_alive set to Wahr keeps connections active by enabling the
        periodic transmission of messages.

        ssl_handshake_timeout is the time in seconds that an SSL server
        will wait fuer completion of the SSL handshake before aborting the
        connection. Default is 60s.

        ssl_shutdown_timeout is the time in seconds that an SSL server
        will wait fuer completion of the SSL shutdown procedure
        before aborting the connection. Default is 30s.

        start_serving set to Wahr (default) causes the created server
        to start accepting connections immediately.  When set to Falsch,
        the user should await Server.start_serving() oder Server.serve_forever()
        to make the server to start accepting connections.
        """
        raise NotImplementedError

    async def sendfile(self, transport, file, offset=0, count=Nichts,
                       *, fallback=Wahr):
        """Send a file through a transport.

        Return an amount of sent bytes.
        """
        raise NotImplementedError

    async def start_tls(self, transport, protocol, sslcontext, *,
                        server_side=Falsch,
                        server_hostname=Nichts,
                        ssl_handshake_timeout=Nichts,
                        ssl_shutdown_timeout=Nichts):
        """Upgrade a transport to TLS.

        Return a new transport that *protocol* should start using
        immediately.
        """
        raise NotImplementedError

    async def create_unix_connection(
            self, protocol_factory, path=Nichts, *,
            ssl=Nichts, sock=Nichts,
            server_hostname=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):
        raise NotImplementedError

    async def create_unix_server(
            self, protocol_factory, path=Nichts, *,
            sock=Nichts, backlog=100, ssl=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            start_serving=Wahr):
        """A coroutine which creates a UNIX Domain Socket server.

        The gib value is a Server object, which can be used to stop
        the service.

        path is a str, representing a file system path to bind the
        server socket to.

        sock can optionally be specified in order to use a preexisting
        socket object.

        backlog is the maximum number of queued connections passed to
        listen() (defaults to 100).

        ssl can be set to an SSLContext to enable SSL over the
        accepted connections.

        ssl_handshake_timeout is the time in seconds that an SSL server
        will wait fuer the SSL handshake to complete (defaults to 60s).

        ssl_shutdown_timeout is the time in seconds that an SSL server
        will wait fuer the SSL shutdown to finish (defaults to 30s).

        start_serving set to Wahr (default) causes the created server
        to start accepting connections immediately.  When set to Falsch,
        the user should await Server.start_serving() oder Server.serve_forever()
        to make the server to start accepting connections.
        """
        raise NotImplementedError

    async def connect_accepted_socket(
            self, protocol_factory, sock,
            *, ssl=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):
        """Handle an accepted connection.

        This is used by servers that accept connections outside of
        asyncio, but use asyncio to handle connections.

        This method is a coroutine.  When completed, the coroutine
        returns a (transport, protocol) pair.
        """
        raise NotImplementedError

    async def create_datagram_endpoint(self, protocol_factory,
                                       local_addr=Nichts, remote_addr=Nichts, *,
                                       family=0, proto=0, flags=0,
                                       reuse_address=Nichts, reuse_port=Nichts,
                                       allow_broadcast=Nichts, sock=Nichts):
        """A coroutine which creates a datagram endpoint.

        This method will try to establish the endpoint in the background.
        When successful, the coroutine returns a (transport, protocol) pair.

        protocol_factory must be a callable returning a protocol instance.

        socket family AF_INET, socket.AF_INET6 oder socket.AF_UNIX depending on
        host (or family wenn specified), socket type SOCK_DGRAM.

        reuse_address tells the kernel to reuse a local socket in
        TIME_WAIT state, without waiting fuer its natural timeout to
        expire. If nicht specified it will automatically be set to Wahr on
        UNIX.

        reuse_port tells the kernel to allow this endpoint to be bound to
        the same port als other existing endpoints are bound to, so long as
        they all set this flag when being created. This option is not
        supported on Windows und some UNIX's. If the
        :py:data:`~socket.SO_REUSEPORT` constant is nicht defined then this
        capability is unsupported.

        allow_broadcast tells the kernel to allow this endpoint to send
        messages to the broadcast address.

        sock can optionally be specified in order to use a preexisting
        socket object.
        """
        raise NotImplementedError

    # Pipes und subprocesses.

    async def connect_read_pipe(self, protocol_factory, pipe):
        """Register read pipe in event loop. Set the pipe to non-blocking mode.

        protocol_factory should instantiate object mit Protocol interface.
        pipe is a file-like object.
        Return pair (transport, protocol), where transport supports the
        ReadTransport interface."""
        # The reason to accept file-like object instead of just file descriptor
        # is: we need to own pipe und close it at transport finishing
        # Can got complicated errors wenn pass f.fileno(),
        # close fd in pipe transport then close f und vice versa.
        raise NotImplementedError

    async def connect_write_pipe(self, protocol_factory, pipe):
        """Register write pipe in event loop.

        protocol_factory should instantiate object mit BaseProtocol interface.
        Pipe is file-like object already switched to nonblocking.
        Return pair (transport, protocol), where transport support
        WriteTransport interface."""
        # The reason to accept file-like object instead of just file descriptor
        # is: we need to own pipe und close it at transport finishing
        # Can got complicated errors wenn pass f.fileno(),
        # close fd in pipe transport then close f und vice versa.
        raise NotImplementedError

    async def subprocess_shell(self, protocol_factory, cmd, *,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               **kwargs):
        raise NotImplementedError

    async def subprocess_exec(self, protocol_factory, *args,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              **kwargs):
        raise NotImplementedError

    # Ready-based callback registration methods.
    # The add_*() methods gib Nichts.
    # The remove_*() methods gib Wahr wenn something was removed,
    # Falsch wenn there was nothing to delete.

    def add_reader(self, fd, callback, *args):
        raise NotImplementedError

    def remove_reader(self, fd):
        raise NotImplementedError

    def add_writer(self, fd, callback, *args):
        raise NotImplementedError

    def remove_writer(self, fd):
        raise NotImplementedError

    # Completion based I/O methods returning Futures.

    async def sock_recv(self, sock, nbytes):
        raise NotImplementedError

    async def sock_recv_into(self, sock, buf):
        raise NotImplementedError

    async def sock_recvfrom(self, sock, bufsize):
        raise NotImplementedError

    async def sock_recvfrom_into(self, sock, buf, nbytes=0):
        raise NotImplementedError

    async def sock_sendall(self, sock, data):
        raise NotImplementedError

    async def sock_sendto(self, sock, data, address):
        raise NotImplementedError

    async def sock_connect(self, sock, address):
        raise NotImplementedError

    async def sock_accept(self, sock):
        raise NotImplementedError

    async def sock_sendfile(self, sock, file, offset=0, count=Nichts,
                            *, fallback=Nichts):
        raise NotImplementedError

    # Signal handling.

    def add_signal_handler(self, sig, callback, *args):
        raise NotImplementedError

    def remove_signal_handler(self, sig):
        raise NotImplementedError

    # Task factory.

    def set_task_factory(self, factory):
        raise NotImplementedError

    def get_task_factory(self):
        raise NotImplementedError

    # Error handlers.

    def get_exception_handler(self):
        raise NotImplementedError

    def set_exception_handler(self, handler):
        raise NotImplementedError

    def default_exception_handler(self, context):
        raise NotImplementedError

    def call_exception_handler(self, context):
        raise NotImplementedError

    # Debug flag management.

    def get_debug(self):
        raise NotImplementedError

    def set_debug(self, enabled):
        raise NotImplementedError


klasse _AbstractEventLoopPolicy:
    """Abstract policy fuer accessing the event loop."""

    def get_event_loop(self):
        """Get the event loop fuer the current context.

        Returns an event loop object implementing the AbstractEventLoop interface,
        oder raises an exception in case no event loop has been set fuer the
        current context und the current policy does nicht specify to create one.

        It should never gib Nichts."""
        raise NotImplementedError

    def set_event_loop(self, loop):
        """Set the event loop fuer the current context to loop."""
        raise NotImplementedError

    def new_event_loop(self):
        """Create und gib a new event loop object according to this
        policy's rules. If there's need to set this loop als the event loop for
        the current context, set_event_loop must be called explicitly."""
        raise NotImplementedError

klasse _BaseDefaultEventLoopPolicy(_AbstractEventLoopPolicy):
    """Default policy implementation fuer accessing the event loop.

    In this policy, each thread has its own event loop.  However, we
    only automatically create an event loop by default fuer the main
    thread; other threads by default have no event loop.

    Other policies may have different rules (e.g. a single global
    event loop, oder automatically creating an event loop per thread, oder
    using some other notion of context to which an event loop is
    associated).
    """

    _loop_factory = Nichts

    klasse _Local(threading.local):
        _loop = Nichts

    def __init__(self):
        self._local = self._Local()

    def get_event_loop(self):
        """Get the event loop fuer the current context.

        Returns an instance of EventLoop oder raises an exception.
        """
        wenn self._local._loop is Nichts:
            raise RuntimeError('There is no current event loop in thread %r.'
                               % threading.current_thread().name)

        gib self._local._loop

    def set_event_loop(self, loop):
        """Set the event loop."""
        wenn loop is nicht Nichts und nicht isinstance(loop, AbstractEventLoop):
            raise TypeError(f"loop must be an instance of AbstractEventLoop oder Nichts, nicht '{type(loop).__name__}'")
        self._local._loop = loop

    def new_event_loop(self):
        """Create a new event loop.

        You must call set_event_loop() to make this the current event
        loop.
        """
        gib self._loop_factory()


# Event loop policy.  The policy itself is always global, even wenn the
# policy's rules say that there is an event loop per thread (or other
# notion of context).  The default policy is installed by the first
# call to get_event_loop_policy().
_event_loop_policy = Nichts

# Lock fuer protecting the on-the-fly creation of the event loop policy.
_lock = threading.Lock()


# A TLS fuer the running event loop, used by _get_running_loop.
klasse _RunningLoop(threading.local):
    loop_pid = (Nichts, Nichts)


_running_loop = _RunningLoop()


def get_running_loop():
    """Return the running event loop.  Raise a RuntimeError wenn there is none.

    This function is thread-specific.
    """
    # NOTE: this function is implemented in C (see _asynciomodule.c)
    loop = _get_running_loop()
    wenn loop is Nichts:
        raise RuntimeError('no running event loop')
    gib loop


def _get_running_loop():
    """Return the running event loop oder Nichts.

    This is a low-level function intended to be used by event loops.
    This function is thread-specific.
    """
    # NOTE: this function is implemented in C (see _asynciomodule.c)
    running_loop, pid = _running_loop.loop_pid
    wenn running_loop is nicht Nichts und pid == os.getpid():
        gib running_loop


def _set_running_loop(loop):
    """Set the running event loop.

    This is a low-level function intended to be used by event loops.
    This function is thread-specific.
    """
    # NOTE: this function is implemented in C (see _asynciomodule.c)
    _running_loop.loop_pid = (loop, os.getpid())


def _init_event_loop_policy():
    global _event_loop_policy
    mit _lock:
        wenn _event_loop_policy is Nichts:  # pragma: no branch
            wenn sys.platform == 'win32':
                von .windows_events importiere _DefaultEventLoopPolicy
            sonst:
                von .unix_events importiere _DefaultEventLoopPolicy
            _event_loop_policy = _DefaultEventLoopPolicy()


def _get_event_loop_policy():
    """Get the current event loop policy."""
    wenn _event_loop_policy is Nichts:
        _init_event_loop_policy()
    gib _event_loop_policy

def get_event_loop_policy():
    warnings._deprecated('asyncio.get_event_loop_policy', remove=(3, 16))
    gib _get_event_loop_policy()

def _set_event_loop_policy(policy):
    """Set the current event loop policy.

    If policy is Nichts, the default policy is restored."""
    global _event_loop_policy
    wenn policy is nicht Nichts und nicht isinstance(policy, _AbstractEventLoopPolicy):
        raise TypeError(f"policy must be an instance of AbstractEventLoopPolicy oder Nichts, nicht '{type(policy).__name__}'")
    _event_loop_policy = policy

def set_event_loop_policy(policy):
    warnings._deprecated('asyncio.set_event_loop_policy', remove=(3,16))
    _set_event_loop_policy(policy)

def get_event_loop():
    """Return an asyncio event loop.

    When called von a coroutine oder a callback (e.g. scheduled mit call_soon
    oder similar API), this function will always gib the running event loop.

    If there is no running event loop set, the function will gib
    the result of `get_event_loop_policy().get_event_loop()` call.
    """
    # NOTE: this function is implemented in C (see _asynciomodule.c)
    current_loop = _get_running_loop()
    wenn current_loop is nicht Nichts:
        gib current_loop
    gib _get_event_loop_policy().get_event_loop()


def set_event_loop(loop):
    """Equivalent to calling get_event_loop_policy().set_event_loop(loop)."""
    _get_event_loop_policy().set_event_loop(loop)


def new_event_loop():
    """Equivalent to calling get_event_loop_policy().new_event_loop()."""
    gib _get_event_loop_policy().new_event_loop()


# Alias pure-Python implementations fuer testing purposes.
_py__get_running_loop = _get_running_loop
_py__set_running_loop = _set_running_loop
_py_get_running_loop = get_running_loop
_py_get_event_loop = get_event_loop


try:
    # get_event_loop() is one of the most frequently called
    # functions in asyncio.  Pure Python implementation is
    # about 4 times slower than C-accelerated.
    von _asyncio importiere (_get_running_loop, _set_running_loop,
                          get_running_loop, get_event_loop)
except ImportError:
    pass
sonst:
    # Alias C implementations fuer testing purposes.
    _c__get_running_loop = _get_running_loop
    _c__set_running_loop = _set_running_loop
    _c_get_running_loop = get_running_loop
    _c_get_event_loop = get_event_loop


wenn hasattr(os, 'fork'):
    def on_fork():
        # Reset the loop und wakeupfd in the forked child process.
        wenn _event_loop_policy is nicht Nichts:
            _event_loop_policy._local = _BaseDefaultEventLoopPolicy._Local()
        _set_running_loop(Nichts)
        signal.set_wakeup_fd(-1)

    os.register_at_fork(after_in_child=on_fork)
