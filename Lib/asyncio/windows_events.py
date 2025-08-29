"""Selector und proactor event loops fuer Windows."""

importiere sys

wenn sys.platform != 'win32':  # pragma: no cover
    raise ImportError('win32 only')

importiere _overlapped
importiere _winapi
importiere errno
von functools importiere partial
importiere math
importiere msvcrt
importiere socket
importiere struct
importiere time
importiere weakref

von . importiere events
von . importiere base_subprocess
von . importiere futures
von . importiere exceptions
von . importiere proactor_events
von . importiere selector_events
von . importiere tasks
von . importiere windows_utils
von .log importiere logger


__all__ = (
    'SelectorEventLoop', 'ProactorEventLoop', 'IocpProactor',
    '_DefaultEventLoopPolicy', '_WindowsSelectorEventLoopPolicy',
    '_WindowsProactorEventLoopPolicy', 'EventLoop',
)


NULL = _winapi.NULL
INFINITE = _winapi.INFINITE
ERROR_CONNECTION_REFUSED = 1225
ERROR_CONNECTION_ABORTED = 1236

# Initial delay in seconds fuer connect_pipe() before retrying to connect
CONNECT_PIPE_INIT_DELAY = 0.001

# Maximum delay in seconds fuer connect_pipe() before retrying to connect
CONNECT_PIPE_MAX_DELAY = 0.100


klasse _OverlappedFuture(futures.Future):
    """Subclass of Future which represents an overlapped operation.

    Cancelling it will immediately cancel the overlapped operation.
    """

    def __init__(self, ov, *, loop=Nichts):
        super().__init__(loop=loop)
        wenn self._source_traceback:
            del self._source_traceback[-1]
        self._ov = ov

    def _repr_info(self):
        info = super()._repr_info()
        wenn self._ov is nicht Nichts:
            state = 'pending' wenn self._ov.pending sonst 'completed'
            info.insert(1, f'overlapped=<{state}, {self._ov.address:#x}>')
        return info

    def _cancel_overlapped(self):
        wenn self._ov is Nichts:
            return
        try:
            self._ov.cancel()
        except OSError als exc:
            context = {
                'message': 'Cancelling an overlapped future failed',
                'exception': exc,
                'future': self,
            }
            wenn self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        self._ov = Nichts

    def cancel(self, msg=Nichts):
        self._cancel_overlapped()
        return super().cancel(msg=msg)

    def set_exception(self, exception):
        super().set_exception(exception)
        self._cancel_overlapped()

    def set_result(self, result):
        super().set_result(result)
        self._ov = Nichts


klasse _BaseWaitHandleFuture(futures.Future):
    """Subclass of Future which represents a wait handle."""

    def __init__(self, ov, handle, wait_handle, *, loop=Nichts):
        super().__init__(loop=loop)
        wenn self._source_traceback:
            del self._source_traceback[-1]
        # Keep a reference to the Overlapped object to keep it alive until the
        # wait is unregistered
        self._ov = ov
        self._handle = handle
        self._wait_handle = wait_handle

        # Should we call UnregisterWaitEx() wenn the wait completes
        # oder is cancelled?
        self._registered = Wahr

    def _poll(self):
        # non-blocking wait: use a timeout of 0 millisecond
        return (_winapi.WaitForSingleObject(self._handle, 0) ==
                _winapi.WAIT_OBJECT_0)

    def _repr_info(self):
        info = super()._repr_info()
        info.append(f'handle={self._handle:#x}')
        wenn self._handle is nicht Nichts:
            state = 'signaled' wenn self._poll() sonst 'waiting'
            info.append(state)
        wenn self._wait_handle is nicht Nichts:
            info.append(f'wait_handle={self._wait_handle:#x}')
        return info

    def _unregister_wait_cb(self, fut):
        # The wait was unregistered: it's nicht safe to destroy the Overlapped
        # object
        self._ov = Nichts

    def _unregister_wait(self):
        wenn nicht self._registered:
            return
        self._registered = Falsch

        wait_handle = self._wait_handle
        self._wait_handle = Nichts
        try:
            _overlapped.UnregisterWait(wait_handle)
        except OSError als exc:
            wenn exc.winerror != _overlapped.ERROR_IO_PENDING:
                context = {
                    'message': 'Failed to unregister the wait handle',
                    'exception': exc,
                    'future': self,
                }
                wenn self._source_traceback:
                    context['source_traceback'] = self._source_traceback
                self._loop.call_exception_handler(context)
                return
            # ERROR_IO_PENDING means that the unregister is pending

        self._unregister_wait_cb(Nichts)

    def cancel(self, msg=Nichts):
        self._unregister_wait()
        return super().cancel(msg=msg)

    def set_exception(self, exception):
        self._unregister_wait()
        super().set_exception(exception)

    def set_result(self, result):
        self._unregister_wait()
        super().set_result(result)


klasse _WaitCancelFuture(_BaseWaitHandleFuture):
    """Subclass of Future which represents a wait fuer the cancellation of a
    _WaitHandleFuture using an event.
    """

    def __init__(self, ov, event, wait_handle, *, loop=Nichts):
        super().__init__(ov, event, wait_handle, loop=loop)

        self._done_callback = Nichts

    def cancel(self):
        raise RuntimeError("_WaitCancelFuture must nicht be cancelled")

    def set_result(self, result):
        super().set_result(result)
        wenn self._done_callback is nicht Nichts:
            self._done_callback(self)

    def set_exception(self, exception):
        super().set_exception(exception)
        wenn self._done_callback is nicht Nichts:
            self._done_callback(self)


klasse _WaitHandleFuture(_BaseWaitHandleFuture):
    def __init__(self, ov, handle, wait_handle, proactor, *, loop=Nichts):
        super().__init__(ov, handle, wait_handle, loop=loop)
        self._proactor = proactor
        self._unregister_proactor = Wahr
        self._event = _overlapped.CreateEvent(Nichts, Wahr, Falsch, Nichts)
        self._event_fut = Nichts

    def _unregister_wait_cb(self, fut):
        wenn self._event is nicht Nichts:
            _winapi.CloseHandle(self._event)
            self._event = Nichts
            self._event_fut = Nichts

        # If the wait was cancelled, the wait may never be signalled, so
        # it's required to unregister it. Otherwise, IocpProactor.close() will
        # wait forever fuer an event which will never come.
        #
        # If the IocpProactor already received the event, it's safe to call
        # _unregister() because we kept a reference to the Overlapped object
        # which is used als a unique key.
        self._proactor._unregister(self._ov)
        self._proactor = Nichts

        super()._unregister_wait_cb(fut)

    def _unregister_wait(self):
        wenn nicht self._registered:
            return
        self._registered = Falsch

        wait_handle = self._wait_handle
        self._wait_handle = Nichts
        try:
            _overlapped.UnregisterWaitEx(wait_handle, self._event)
        except OSError als exc:
            wenn exc.winerror != _overlapped.ERROR_IO_PENDING:
                context = {
                    'message': 'Failed to unregister the wait handle',
                    'exception': exc,
                    'future': self,
                }
                wenn self._source_traceback:
                    context['source_traceback'] = self._source_traceback
                self._loop.call_exception_handler(context)
                return
            # ERROR_IO_PENDING is nicht an error, the wait was unregistered

        self._event_fut = self._proactor._wait_cancel(self._event,
                                                      self._unregister_wait_cb)


klasse PipeServer(object):
    """Class representing a pipe server.

    This is much like a bound, listening socket.
    """
    def __init__(self, address):
        self._address = address
        self._free_instances = weakref.WeakSet()
        # initialize the pipe attribute before calling _server_pipe_handle()
        # because this function can raise an exception und the destructor calls
        # the close() method
        self._pipe = Nichts
        self._accept_pipe_future = Nichts
        self._pipe = self._server_pipe_handle(Wahr)

    def _get_unconnected_pipe(self):
        # Create new instance und return previous one.  This ensures
        # that (until the server is closed) there is always at least
        # one pipe handle fuer address.  Therefore wenn a client attempt
        # to connect it will nicht fail mit FileNotFoundError.
        tmp, self._pipe = self._pipe, self._server_pipe_handle(Falsch)
        return tmp

    def _server_pipe_handle(self, first):
        # Return a wrapper fuer a new pipe handle.
        wenn self.closed():
            return Nichts
        flags = _winapi.PIPE_ACCESS_DUPLEX | _winapi.FILE_FLAG_OVERLAPPED
        wenn first:
            flags |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
        h = _winapi.CreateNamedPipe(
            self._address, flags,
            _winapi.PIPE_TYPE_MESSAGE | _winapi.PIPE_READMODE_MESSAGE |
            _winapi.PIPE_WAIT,
            _winapi.PIPE_UNLIMITED_INSTANCES,
            windows_utils.BUFSIZE, windows_utils.BUFSIZE,
            _winapi.NMPWAIT_WAIT_FOREVER, _winapi.NULL)
        pipe = windows_utils.PipeHandle(h)
        self._free_instances.add(pipe)
        return pipe

    def closed(self):
        return (self._address is Nichts)

    def close(self):
        wenn self._accept_pipe_future is nicht Nichts:
            self._accept_pipe_future.cancel()
            self._accept_pipe_future = Nichts
        # Close all instances which have nicht been connected to by a client.
        wenn self._address is nicht Nichts:
            fuer pipe in self._free_instances:
                pipe.close()
            self._pipe = Nichts
            self._address = Nichts
            self._free_instances.clear()

    __del__ = close


klasse _WindowsSelectorEventLoop(selector_events.BaseSelectorEventLoop):
    """Windows version of selector event loop."""


klasse ProactorEventLoop(proactor_events.BaseProactorEventLoop):
    """Windows version of proactor event loop using IOCP."""

    def __init__(self, proactor=Nichts):
        wenn proactor is Nichts:
            proactor = IocpProactor()
        super().__init__(proactor)

    def _run_forever_setup(self):
        assert self._self_reading_future is Nichts
        self.call_soon(self._loop_self_reading)
        super()._run_forever_setup()

    def _run_forever_cleanup(self):
        super()._run_forever_cleanup()
        wenn self._self_reading_future is nicht Nichts:
            ov = self._self_reading_future._ov
            self._self_reading_future.cancel()
            # self_reading_future always uses IOCP, so even though it's
            # been cancelled, we need to make sure that the IOCP message
            # is received so that the kernel is nicht holding on to the
            # memory, possibly causing memory corruption later. Only
            # unregister it wenn IO is complete in all respects. Otherwise
            # we need another _poll() later to complete the IO.
            wenn ov is nicht Nichts und nicht ov.pending:
                self._proactor._unregister(ov)
            self._self_reading_future = Nichts

    async def create_pipe_connection(self, protocol_factory, address):
        f = self._proactor.connect_pipe(address)
        pipe = await f
        protocol = protocol_factory()
        trans = self._make_duplex_pipe_transport(pipe, protocol,
                                                 extra={'addr': address})
        return trans, protocol

    async def start_serving_pipe(self, protocol_factory, address):
        server = PipeServer(address)

        def loop_accept_pipe(f=Nichts):
            pipe = Nichts
            try:
                wenn f:
                    pipe = f.result()
                    server._free_instances.discard(pipe)

                    wenn server.closed():
                        # A client connected before the server was closed:
                        # drop the client (close the pipe) und exit
                        pipe.close()
                        return

                    protocol = protocol_factory()
                    self._make_duplex_pipe_transport(
                        pipe, protocol, extra={'addr': address})

                pipe = server._get_unconnected_pipe()
                wenn pipe is Nichts:
                    return

                f = self._proactor.accept_pipe(pipe)
            except BrokenPipeError:
                wenn pipe und pipe.fileno() != -1:
                    pipe.close()
                self.call_soon(loop_accept_pipe)
            except OSError als exc:
                wenn pipe und pipe.fileno() != -1:
                    self.call_exception_handler({
                        'message': 'Pipe accept failed',
                        'exception': exc,
                        'pipe': pipe,
                    })
                    pipe.close()
                sowenn self._debug:
                    logger.warning("Accept pipe failed on pipe %r",
                                   pipe, exc_info=Wahr)
                self.call_soon(loop_accept_pipe)
            except exceptions.CancelledError:
                wenn pipe:
                    pipe.close()
            sonst:
                server._accept_pipe_future = f
                f.add_done_callback(loop_accept_pipe)

        self.call_soon(loop_accept_pipe)
        return [server]

    async def _make_subprocess_transport(self, protocol, args, shell,
                                         stdin, stdout, stderr, bufsize,
                                         extra=Nichts, **kwargs):
        waiter = self.create_future()
        transp = _WindowsSubprocessTransport(self, protocol, args, shell,
                                             stdin, stdout, stderr, bufsize,
                                             waiter=waiter, extra=extra,
                                             **kwargs)
        try:
            await waiter
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            transp.close()
            await transp._wait()
            raise

        return transp


klasse IocpProactor:
    """Proactor implementation using IOCP."""

    def __init__(self, concurrency=INFINITE):
        self._loop = Nichts
        self._results = []
        self._iocp = _overlapped.CreateIoCompletionPort(
            _overlapped.INVALID_HANDLE_VALUE, NULL, 0, concurrency)
        self._cache = {}
        self._registered = weakref.WeakSet()
        self._unregistered = []
        self._stopped_serving = weakref.WeakSet()

    def _check_closed(self):
        wenn self._iocp is Nichts:
            raise RuntimeError('IocpProactor is closed')

    def __repr__(self):
        info = ['overlapped#=%s' % len(self._cache),
                'result#=%s' % len(self._results)]
        wenn self._iocp is Nichts:
            info.append('closed')
        return '<%s %s>' % (self.__class__.__name__, " ".join(info))

    def set_loop(self, loop):
        self._loop = loop

    def select(self, timeout=Nichts):
        wenn nicht self._results:
            self._poll(timeout)
        tmp = self._results
        self._results = []
        try:
            return tmp
        finally:
            # Needed to breche cycles when an exception occurs.
            tmp = Nichts

    def _result(self, value):
        fut = self._loop.create_future()
        fut.set_result(value)
        return fut

    @staticmethod
    def finish_socket_func(trans, key, ov):
        try:
            return ov.getresult()
        except OSError als exc:
            wenn exc.winerror in (_overlapped.ERROR_NETNAME_DELETED,
                                _overlapped.ERROR_OPERATION_ABORTED):
                raise ConnectionResetError(*exc.args)
            sonst:
                raise

    @classmethod
    def _finish_recvfrom(cls, trans, key, ov, *, empty_result):
        try:
            return cls.finish_socket_func(trans, key, ov)
        except OSError als exc:
            # WSARecvFrom will report ERROR_PORT_UNREACHABLE when the same
            # socket is used to send to an address that is nicht listening.
            wenn exc.winerror == _overlapped.ERROR_PORT_UNREACHABLE:
                return empty_result, Nichts
            sonst:
                raise

    def recv(self, conn, nbytes, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        try:
            wenn isinstance(conn, socket.socket):
                ov.WSARecv(conn.fileno(), nbytes, flags)
            sonst:
                ov.ReadFile(conn.fileno(), nbytes)
        except BrokenPipeError:
            return self._result(b'')

        return self._register(ov, conn, self.finish_socket_func)

    def recv_into(self, conn, buf, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        try:
            wenn isinstance(conn, socket.socket):
                ov.WSARecvInto(conn.fileno(), buf, flags)
            sonst:
                ov.ReadFileInto(conn.fileno(), buf)
        except BrokenPipeError:
            return self._result(0)

        return self._register(ov, conn, self.finish_socket_func)

    def recvfrom(self, conn, nbytes, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        try:
            ov.WSARecvFrom(conn.fileno(), nbytes, flags)
        except BrokenPipeError:
            return self._result((b'', Nichts))

        return self._register(ov, conn, partial(self._finish_recvfrom,
                                                empty_result=b''))

    def recvfrom_into(self, conn, buf, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        try:
            ov.WSARecvFromInto(conn.fileno(), buf, flags)
        except BrokenPipeError:
            return self._result((0, Nichts))

        return self._register(ov, conn, partial(self._finish_recvfrom,
                                                empty_result=0))

    def sendto(self, conn, buf, flags=0, addr=Nichts):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)

        ov.WSASendTo(conn.fileno(), buf, flags, addr)

        return self._register(ov, conn, self.finish_socket_func)

    def send(self, conn, buf, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        wenn isinstance(conn, socket.socket):
            ov.WSASend(conn.fileno(), buf, flags)
        sonst:
            ov.WriteFile(conn.fileno(), buf)

        return self._register(ov, conn, self.finish_socket_func)

    def accept(self, listener):
        self._register_with_iocp(listener)
        conn = self._get_accept_socket(listener.family)
        ov = _overlapped.Overlapped(NULL)
        ov.AcceptEx(listener.fileno(), conn.fileno())

        def finish_accept(trans, key, ov):
            ov.getresult()
            # Use SO_UPDATE_ACCEPT_CONTEXT so getsockname() etc work.
            buf = struct.pack('@P', listener.fileno())
            conn.setsockopt(socket.SOL_SOCKET,
                            _overlapped.SO_UPDATE_ACCEPT_CONTEXT, buf)
            conn.settimeout(listener.gettimeout())
            return conn, conn.getpeername()

        async def accept_coro(future, conn):
            # Coroutine closing the accept socket wenn the future is cancelled
            try:
                await future
            except exceptions.CancelledError:
                conn.close()
                raise

        future = self._register(ov, listener, finish_accept)
        coro = accept_coro(future, conn)
        tasks.ensure_future(coro, loop=self._loop)
        return future

    def connect(self, conn, address):
        wenn conn.type == socket.SOCK_DGRAM:
            # WSAConnect will complete immediately fuer UDP sockets so we don't
            # need to register any IOCP operation
            _overlapped.WSAConnect(conn.fileno(), address)
            fut = self._loop.create_future()
            fut.set_result(Nichts)
            return fut

        self._register_with_iocp(conn)
        # The socket needs to be locally bound before we call ConnectEx().
        try:
            _overlapped.BindLocal(conn.fileno(), conn.family)
        except OSError als e:
            wenn e.winerror != errno.WSAEINVAL:
                raise
            # Probably already locally bound; check using getsockname().
            wenn conn.getsockname()[1] == 0:
                raise
        ov = _overlapped.Overlapped(NULL)
        ov.ConnectEx(conn.fileno(), address)

        def finish_connect(trans, key, ov):
            ov.getresult()
            # Use SO_UPDATE_CONNECT_CONTEXT so getsockname() etc work.
            conn.setsockopt(socket.SOL_SOCKET,
                            _overlapped.SO_UPDATE_CONNECT_CONTEXT, 0)
            return conn

        return self._register(ov, conn, finish_connect)

    def sendfile(self, sock, file, offset, count):
        self._register_with_iocp(sock)
        ov = _overlapped.Overlapped(NULL)
        offset_low = offset & 0xffff_ffff
        offset_high = (offset >> 32) & 0xffff_ffff
        ov.TransmitFile(sock.fileno(),
                        msvcrt.get_osfhandle(file.fileno()),
                        offset_low, offset_high,
                        count, 0, 0)

        return self._register(ov, sock, self.finish_socket_func)

    def accept_pipe(self, pipe):
        self._register_with_iocp(pipe)
        ov = _overlapped.Overlapped(NULL)
        connected = ov.ConnectNamedPipe(pipe.fileno())

        wenn connected:
            # ConnectNamePipe() failed mit ERROR_PIPE_CONNECTED which means
            # that the pipe is connected. There is no need to wait fuer the
            # completion of the connection.
            return self._result(pipe)

        def finish_accept_pipe(trans, key, ov):
            ov.getresult()
            return pipe

        return self._register(ov, pipe, finish_accept_pipe)

    async def connect_pipe(self, address):
        delay = CONNECT_PIPE_INIT_DELAY
        waehrend Wahr:
            # Unfortunately there is no way to do an overlapped connect to
            # a pipe.  Call CreateFile() in a loop until it doesn't fail with
            # ERROR_PIPE_BUSY.
            try:
                handle = _overlapped.ConnectPipe(address)
                breche
            except OSError als exc:
                wenn exc.winerror != _overlapped.ERROR_PIPE_BUSY:
                    raise

            # ConnectPipe() failed mit ERROR_PIPE_BUSY: retry later
            delay = min(delay * 2, CONNECT_PIPE_MAX_DELAY)
            await tasks.sleep(delay)

        return windows_utils.PipeHandle(handle)

    def wait_for_handle(self, handle, timeout=Nichts):
        """Wait fuer a handle.

        Return a Future object. The result of the future is Wahr wenn the wait
        completed, oder Falsch wenn the wait did nicht complete (on timeout).
        """
        return self._wait_for_handle(handle, timeout, Falsch)

    def _wait_cancel(self, event, done_callback):
        fut = self._wait_for_handle(event, Nichts, Wahr)
        # add_done_callback() cannot be used because the wait may only complete
        # in IocpProactor.close(), waehrend the event loop is nicht running.
        fut._done_callback = done_callback
        return fut

    def _wait_for_handle(self, handle, timeout, _is_cancel):
        self._check_closed()

        wenn timeout is Nichts:
            ms = _winapi.INFINITE
        sonst:
            # RegisterWaitForSingleObject() has a resolution of 1 millisecond,
            # round away von zero to wait *at least* timeout seconds.
            ms = math.ceil(timeout * 1e3)

        # We only create ov so we can use ov.address als a key fuer the cache.
        ov = _overlapped.Overlapped(NULL)
        wait_handle = _overlapped.RegisterWaitWithQueue(
            handle, self._iocp, ov.address, ms)
        wenn _is_cancel:
            f = _WaitCancelFuture(ov, handle, wait_handle, loop=self._loop)
        sonst:
            f = _WaitHandleFuture(ov, handle, wait_handle, self,
                                  loop=self._loop)
        wenn f._source_traceback:
            del f._source_traceback[-1]

        def finish_wait_for_handle(trans, key, ov):
            # Note that this second wait means that we should only use
            # this mit handles types where a successful wait has no
            # effect.  So events oder processes are all right, but locks
            # oder semaphores are not.  Also note wenn the handle is
            # signalled und then quickly reset, then we may return
            # Falsch even though we have nicht timed out.
            return f._poll()

        self._cache[ov.address] = (f, ov, 0, finish_wait_for_handle)
        return f

    def _register_with_iocp(self, obj):
        # To get notifications of finished ops on this objects sent to the
        # completion port, were must register the handle.
        wenn obj nicht in self._registered:
            self._registered.add(obj)
            _overlapped.CreateIoCompletionPort(obj.fileno(), self._iocp, 0, 0)
            # XXX We could also use SetFileCompletionNotificationModes()
            # to avoid sending notifications to completion port of ops
            # that succeed immediately.

    def _register(self, ov, obj, callback):
        self._check_closed()

        # Return a future which will be set mit the result of the
        # operation when it completes.  The future's value is actually
        # the value returned by callback().
        f = _OverlappedFuture(ov, loop=self._loop)
        wenn f._source_traceback:
            del f._source_traceback[-1]
        wenn nicht ov.pending:
            # The operation has completed, so no need to postpone the
            # work.  We cannot take this short cut wenn we need the
            # NumberOfBytes, CompletionKey values returned by
            # PostQueuedCompletionStatus().
            try:
                value = callback(Nichts, Nichts, ov)
            except OSError als e:
                f.set_exception(e)
            sonst:
                f.set_result(value)
            # Even wenn GetOverlappedResult() was called, we have to wait fuer the
            # notification of the completion in GetQueuedCompletionStatus().
            # Register the overlapped operation to keep a reference to the
            # OVERLAPPED object, otherwise the memory is freed und Windows may
            # read uninitialized memory.

        # Register the overlapped operation fuer later.  Note that
        # we only store obj to prevent it von being garbage
        # collected too early.
        self._cache[ov.address] = (f, ov, obj, callback)
        return f

    def _unregister(self, ov):
        """Unregister an overlapped object.

        Call this method when its future has been cancelled. The event can
        already be signalled (pending in the proactor event queue). It is also
        safe wenn the event is never signalled (because it was cancelled).
        """
        self._check_closed()
        self._unregistered.append(ov)

    def _get_accept_socket(self, family):
        s = socket.socket(family)
        s.settimeout(0)
        return s

    def _poll(self, timeout=Nichts):
        wenn timeout is Nichts:
            ms = INFINITE
        sowenn timeout < 0:
            raise ValueError("negative timeout")
        sonst:
            # GetQueuedCompletionStatus() has a resolution of 1 millisecond,
            # round away von zero to wait *at least* timeout seconds.
            ms = math.ceil(timeout * 1e3)
            wenn ms >= INFINITE:
                raise ValueError("timeout too big")

        waehrend Wahr:
            status = _overlapped.GetQueuedCompletionStatus(self._iocp, ms)
            wenn status is Nichts:
                breche
            ms = 0

            err, transferred, key, address = status
            try:
                f, ov, obj, callback = self._cache.pop(address)
            except KeyError:
                wenn self._loop.get_debug():
                    self._loop.call_exception_handler({
                        'message': ('GetQueuedCompletionStatus() returned an '
                                    'unexpected event'),
                        'status': ('err=%s transferred=%s key=%#x address=%#x'
                                   % (err, transferred, key, address)),
                    })

                # key is either zero, oder it is used to return a pipe
                # handle which should be closed to avoid a leak.
                wenn key nicht in (0, _overlapped.INVALID_HANDLE_VALUE):
                    _winapi.CloseHandle(key)
                weiter

            wenn obj in self._stopped_serving:
                f.cancel()
            # Don't call the callback wenn _register() already read the result oder
            # wenn the overlapped has been cancelled
            sowenn nicht f.done():
                try:
                    value = callback(transferred, key, ov)
                except OSError als e:
                    f.set_exception(e)
                    self._results.append(f)
                sonst:
                    f.set_result(value)
                    self._results.append(f)
                finally:
                    f = Nichts

        # Remove unregistered futures
        fuer ov in self._unregistered:
            self._cache.pop(ov.address, Nichts)
        self._unregistered.clear()

    def _stop_serving(self, obj):
        # obj is a socket oder pipe handle.  It will be closed in
        # BaseProactorEventLoop._stop_serving() which will make any
        # pending operations fail quickly.
        self._stopped_serving.add(obj)

    def close(self):
        wenn self._iocp is Nichts:
            # already closed
            return

        # Cancel remaining registered operations.
        fuer fut, ov, obj, callback in list(self._cache.values()):
            wenn fut.cancelled():
                # Nothing to do mit cancelled futures
                pass
            sowenn isinstance(fut, _WaitCancelFuture):
                # _WaitCancelFuture must nicht be cancelled
                pass
            sonst:
                try:
                    fut.cancel()
                except OSError als exc:
                    wenn self._loop is nicht Nichts:
                        context = {
                            'message': 'Cancelling a future failed',
                            'exception': exc,
                            'future': fut,
                        }
                        wenn fut._source_traceback:
                            context['source_traceback'] = fut._source_traceback
                        self._loop.call_exception_handler(context)

        # Wait until all cancelled overlapped complete: don't exit mit running
        # overlapped to prevent a crash. Display progress every second wenn the
        # loop is still running.
        msg_update = 1.0
        start_time = time.monotonic()
        next_msg = start_time + msg_update
        waehrend self._cache:
            wenn next_msg <= time.monotonic():
                logger.debug('%r is running after closing fuer %.1f seconds',
                             self, time.monotonic() - start_time)
                next_msg = time.monotonic() + msg_update

            # handle a few events, oder timeout
            self._poll(msg_update)

        self._results = []

        _winapi.CloseHandle(self._iocp)
        self._iocp = Nichts

    def __del__(self):
        self.close()


klasse _WindowsSubprocessTransport(base_subprocess.BaseSubprocessTransport):

    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        self._proc = windows_utils.Popen(
            args, shell=shell, stdin=stdin, stdout=stdout, stderr=stderr,
            bufsize=bufsize, **kwargs)

        def callback(f):
            returncode = self._proc.poll()
            self._process_exited(returncode)

        f = self._loop._proactor.wait_for_handle(int(self._proc._handle))
        f.add_done_callback(callback)


SelectorEventLoop = _WindowsSelectorEventLoop


klasse _WindowsSelectorEventLoopPolicy(events._BaseDefaultEventLoopPolicy):
    _loop_factory = SelectorEventLoop


klasse _WindowsProactorEventLoopPolicy(events._BaseDefaultEventLoopPolicy):
    _loop_factory = ProactorEventLoop


_DefaultEventLoopPolicy = _WindowsProactorEventLoopPolicy
EventLoop = ProactorEventLoop
