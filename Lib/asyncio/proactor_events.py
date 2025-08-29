"""Event loop using a proactor and related classes.

A proactor is a "notify-on-completion" multiplexer.  Currently a
proactor is only implemented on Windows with IOCP.
"""

__all__ = 'BaseProactorEventLoop',

importiere io
importiere os
importiere socket
importiere warnings
importiere signal
importiere threading
importiere collections

von . importiere base_events
von . importiere constants
von . importiere futures
von . importiere exceptions
von . importiere protocols
von . importiere sslproto
von . importiere transports
von . importiere trsock
von .log importiere logger


def _set_socket_extra(transport, sock):
    transport._extra['socket'] = trsock.TransportSocket(sock)

    try:
        transport._extra['sockname'] = sock.getsockname()
    except socket.error:
        wenn transport._loop.get_debug():
            logger.warning(
                "getsockname() failed on %r", sock, exc_info=Wahr)

    wenn 'peername' not in transport._extra:
        try:
            transport._extra['peername'] = sock.getpeername()
        except socket.error:
            # UDP sockets may not have a peer name
            transport._extra['peername'] = Nichts


klasse _ProactorBasePipeTransport(transports._FlowControlMixin,
                                 transports.BaseTransport):
    """Base klasse fuer pipe and socket transports."""

    def __init__(self, loop, sock, protocol, waiter=Nichts,
                 extra=Nichts, server=Nichts):
        super().__init__(extra, loop)
        self._set_extra(sock)
        self._sock = sock
        self.set_protocol(protocol)
        self._server = server
        self._buffer = Nichts  # Nichts or bytearray.
        self._read_fut = Nichts
        self._write_fut = Nichts
        self._pending_write = 0
        self._conn_lost = 0
        self._closing = Falsch  # Set when close() called.
        self._called_connection_lost = Falsch
        self._eof_written = Falsch
        wenn self._server is not Nichts:
            self._server._attach(self)
        self._loop.call_soon(self._protocol.connection_made, self)
        wenn waiter is not Nichts:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, Nichts)

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self._sock is Nichts:
            info.append('closed')
        sowenn self._closing:
            info.append('closing')
        wenn self._sock is not Nichts:
            info.append(f'fd={self._sock.fileno()}')
        wenn self._read_fut is not Nichts:
            info.append(f'read={self._read_fut!r}')
        wenn self._write_fut is not Nichts:
            info.append(f'write={self._write_fut!r}')
        wenn self._buffer:
            info.append(f'write_bufsize={len(self._buffer)}')
        wenn self._eof_written:
            info.append('EOF written')
        return '<{}>'.format(' '.join(info))

    def _set_extra(self, sock):
        self._extra['pipe'] = sock

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        return self._protocol

    def is_closing(self):
        return self._closing

    def close(self):
        wenn self._closing:
            return
        self._closing = Wahr
        self._conn_lost += 1
        wenn not self._buffer and self._write_fut is Nichts:
            self._loop.call_soon(self._call_connection_lost, Nichts)
        wenn self._read_fut is not Nichts:
            self._read_fut.cancel()
            self._read_fut = Nichts

    def __del__(self, _warn=warnings.warn):
        wenn self._sock is not Nichts:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self._sock.close()

    def _fatal_error(self, exc, message='Fatal error on pipe transport'):
        try:
            wenn isinstance(exc, OSError):
                wenn self._loop.get_debug():
                    logger.debug("%r: %s", self, message, exc_info=Wahr)
            sonst:
                self._loop.call_exception_handler({
                    'message': message,
                    'exception': exc,
                    'transport': self,
                    'protocol': self._protocol,
                })
        finally:
            self._force_close(exc)

    def _force_close(self, exc):
        wenn self._empty_waiter is not Nichts and not self._empty_waiter.done():
            wenn exc is Nichts:
                self._empty_waiter.set_result(Nichts)
            sonst:
                self._empty_waiter.set_exception(exc)
        wenn self._closing and self._called_connection_lost:
            return
        self._closing = Wahr
        self._conn_lost += 1
        wenn self._write_fut:
            self._write_fut.cancel()
            self._write_fut = Nichts
        wenn self._read_fut:
            self._read_fut.cancel()
            self._read_fut = Nichts
        self._pending_write = 0
        self._buffer = Nichts
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        wenn self._called_connection_lost:
            return
        try:
            self._protocol.connection_lost(exc)
        finally:
            # XXX If there is a pending overlapped read on the other
            # end then it may fail with ERROR_NETNAME_DELETED wenn we
            # just close our end.  First calling shutdown() seems to
            # cure it, but maybe using DisconnectEx() would be better.
            wenn hasattr(self._sock, 'shutdown') and self._sock.fileno() != -1:
                self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = Nichts
            server = self._server
            wenn server is not Nichts:
                server._detach(self)
                self._server = Nichts
            self._called_connection_lost = Wahr

    def get_write_buffer_size(self):
        size = self._pending_write
        wenn self._buffer is not Nichts:
            size += len(self._buffer)
        return size


klasse _ProactorReadPipeTransport(_ProactorBasePipeTransport,
                                 transports.ReadTransport):
    """Transport fuer read pipes."""

    def __init__(self, loop, sock, protocol, waiter=Nichts,
                 extra=Nichts, server=Nichts, buffer_size=65536):
        self._pending_data_length = -1
        self._paused = Wahr
        super().__init__(loop, sock, protocol, waiter, extra, server)

        self._data = bytearray(buffer_size)
        self._loop.call_soon(self._loop_reading)
        self._paused = Falsch

    def is_reading(self):
        return not self._paused and not self._closing

    def pause_reading(self):
        wenn self._closing or self._paused:
            return
        self._paused = Wahr

        # bpo-33694: Don't cancel self._read_fut because cancelling an
        # overlapped WSASend() loss silently data with the current proactor
        # implementation.
        #
        # If CancelIoEx() fails with ERROR_NOT_FOUND, it means that WSASend()
        # completed (even wenn HasOverlappedIoCompleted() returns 0), but
        # Overlapped.cancel() currently silently ignores the ERROR_NOT_FOUND
        # error. Once the overlapped is ignored, the IOCP loop will ignores the
        # completion I/O event and so not read the result of the overlapped
        # WSARecv().

        wenn self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self):
        wenn self._closing or not self._paused:
            return

        self._paused = Falsch
        wenn self._read_fut is Nichts:
            self._loop.call_soon(self._loop_reading, Nichts)

        length = self._pending_data_length
        self._pending_data_length = -1
        wenn length > -1:
            # Call the protocol method after calling _loop_reading(),
            # since the protocol can decide to pause reading again.
            self._loop.call_soon(self._data_received, self._data[:length], length)

        wenn self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    def _eof_received(self):
        wenn self._loop.get_debug():
            logger.debug("%r received EOF", self)

        try:
            keep_open = self._protocol.eof_received()
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.eof_received() call failed.')
            return

        wenn not keep_open:
            self.close()

    def _data_received(self, data, length):
        wenn self._paused:
            # Don't call any protocol method while reading is paused.
            # The protocol will be called on resume_reading().
            assert self._pending_data_length == -1
            self._pending_data_length = length
            return

        wenn length == 0:
            self._eof_received()
            return

        wenn isinstance(self._protocol, protocols.BufferedProtocol):
            try:
                protocols._feed_data_to_buffered_proto(self._protocol, data)
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException as exc:
                self._fatal_error(exc,
                                  'Fatal error: protocol.buffer_updated() '
                                  'call failed.')
                return
        sonst:
            self._protocol.data_received(data)

    def _loop_reading(self, fut=Nichts):
        length = -1
        data = Nichts
        try:
            wenn fut is not Nichts:
                assert self._read_fut is fut or (self._read_fut is Nichts and
                                                 self._closing)
                self._read_fut = Nichts
                wenn fut.done():
                    # deliver data later in "finally" clause
                    length = fut.result()
                    wenn length == 0:
                        # we got end-of-file so no need to reschedule a new read
                        return

                    # It's a new slice so make it immutable so protocols upstream don't have problems
                    data = bytes(memoryview(self._data)[:length])
                sonst:
                    # the future will be replaced by next proactor.recv call
                    fut.cancel()

            wenn self._closing:
                # since close() has been called we ignore any read data
                return

            # bpo-33694: buffer_updated() has currently no fast path because of
            # a data loss issue caused by overlapped WSASend() cancellation.

            wenn not self._paused:
                # reschedule a new read
                self._read_fut = self._loop._proactor.recv_into(self._sock, self._data)
        except ConnectionAbortedError as exc:
            wenn not self._closing:
                self._fatal_error(exc, 'Fatal read error on pipe transport')
            sowenn self._loop.get_debug():
                logger.debug("Read error on pipe transport while closing",
                             exc_info=Wahr)
        except ConnectionResetError as exc:
            self._force_close(exc)
        except OSError as exc:
            self._fatal_error(exc, 'Fatal read error on pipe transport')
        except exceptions.CancelledError:
            wenn not self._closing:
                raise
        sonst:
            wenn not self._paused:
                self._read_fut.add_done_callback(self._loop_reading)
        finally:
            wenn length > -1:
                self._data_received(data, length)


klasse _ProactorBaseWritePipeTransport(_ProactorBasePipeTransport,
                                      transports.WriteTransport):
    """Transport fuer write pipes."""

    _start_tls_compatible = Wahr

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._empty_waiter = Nichts

    def write(self, data):
        wenn not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(
                f"data argument must be a bytes-like object, "
                f"not {type(data).__name__}")
        wenn self._eof_written:
            raise RuntimeError('write_eof() already called')
        wenn self._empty_waiter is not Nichts:
            raise RuntimeError('unable to write; sendfile is in progress')

        wenn not data:
            return

        wenn self._conn_lost:
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        # Observable states:
        # 1. IDLE: _write_fut and _buffer both Nichts
        # 2. WRITING: _write_fut set; _buffer Nichts
        # 3. BACKED UP: _write_fut set; _buffer a bytearray
        # We always copy the data, so the caller can't modify it
        # while we're still waiting fuer the I/O to happen.
        wenn self._write_fut is Nichts:  # IDLE -> WRITING
            assert self._buffer is Nichts
            # Pass a copy, except wenn it's already immutable.
            self._loop_writing(data=bytes(data))
        sowenn not self._buffer:  # WRITING -> BACKED UP
            # Make a mutable copy which we can extend.
            self._buffer = bytearray(data)
            self._maybe_pause_protocol()
        sonst:  # BACKED UP
            # Append to buffer (also copies).
            self._buffer.extend(data)
            self._maybe_pause_protocol()

    def _loop_writing(self, f=Nichts, data=Nichts):
        try:
            wenn f is not Nichts and self._write_fut is Nichts and self._closing:
                # XXX most likely self._force_close() has been called, and
                # it has set self._write_fut to Nichts.
                return
            assert f is self._write_fut
            self._write_fut = Nichts
            self._pending_write = 0
            wenn f:
                f.result()
            wenn data is Nichts:
                data = self._buffer
                self._buffer = Nichts
            wenn not data:
                wenn self._closing:
                    self._loop.call_soon(self._call_connection_lost, Nichts)
                wenn self._eof_written:
                    self._sock.shutdown(socket.SHUT_WR)
                # Now that we've reduced the buffer size, tell the
                # protocol to resume writing wenn it was paused.  Note that
                # we do this last since the callback is called immediately
                # and it may add more data to the buffer (even causing the
                # protocol to be paused again).
                self._maybe_resume_protocol()
            sonst:
                self._write_fut = self._loop._proactor.send(self._sock, data)
                wenn not self._write_fut.done():
                    assert self._pending_write == 0
                    self._pending_write = len(data)
                    self._write_fut.add_done_callback(self._loop_writing)
                    self._maybe_pause_protocol()
                sonst:
                    self._write_fut.add_done_callback(self._loop_writing)
            wenn self._empty_waiter is not Nichts and self._write_fut is Nichts:
                self._empty_waiter.set_result(Nichts)
        except ConnectionResetError as exc:
            self._force_close(exc)
        except OSError as exc:
            self._fatal_error(exc, 'Fatal write error on pipe transport')

    def can_write_eof(self):
        return Wahr

    def write_eof(self):
        self.close()

    def abort(self):
        self._force_close(Nichts)

    def _make_empty_waiter(self):
        wenn self._empty_waiter is not Nichts:
            raise RuntimeError("Empty waiter is already set")
        self._empty_waiter = self._loop.create_future()
        wenn self._write_fut is Nichts:
            self._empty_waiter.set_result(Nichts)
        return self._empty_waiter

    def _reset_empty_waiter(self):
        self._empty_waiter = Nichts


klasse _ProactorWritePipeTransport(_ProactorBaseWritePipeTransport):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._read_fut = self._loop._proactor.recv(self._sock, 16)
        self._read_fut.add_done_callback(self._pipe_closed)

    def _pipe_closed(self, fut):
        wenn fut.cancelled():
            # the transport has been closed
            return
        assert fut.result() == b''
        wenn self._closing:
            assert self._read_fut is Nichts
            return
        assert fut is self._read_fut, (fut, self._read_fut)
        self._read_fut = Nichts
        wenn self._write_fut is not Nichts:
            self._force_close(BrokenPipeError())
        sonst:
            self.close()


klasse _ProactorDatagramTransport(_ProactorBasePipeTransport,
                                 transports.DatagramTransport):
    max_size = 256 * 1024
    _header_size = 8

    def __init__(self, loop, sock, protocol, address=Nichts,
                 waiter=Nichts, extra=Nichts):
        self._address = address
        self._empty_waiter = Nichts
        self._buffer_size = 0
        # We don't need to call _protocol.connection_made() since our base
        # constructor does it fuer us.
        super().__init__(loop, sock, protocol, waiter=waiter, extra=extra)

        # The base constructor sets _buffer = Nichts, so we set it here
        self._buffer = collections.deque()
        self._loop.call_soon(self._loop_reading)

    def _set_extra(self, sock):
        _set_socket_extra(self, sock)

    def get_write_buffer_size(self):
        return self._buffer_size

    def abort(self):
        self._force_close(Nichts)

    def sendto(self, data, addr=Nichts):
        wenn not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError('data argument must be bytes-like object (%r)',
                            type(data))

        wenn self._address is not Nichts and addr not in (Nichts, self._address):
            raise ValueError(
                f'Invalid address: must be Nichts or {self._address}')

        wenn self._conn_lost and self._address:
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.sendto() raised exception.')
            self._conn_lost += 1
            return

        # Ensure that what we buffer is immutable.
        self._buffer.append((bytes(data), addr))
        self._buffer_size += len(data) + self._header_size

        wenn self._write_fut is Nichts:
            # No current write operations are active, kick one off
            self._loop_writing()
        # sonst: A write operation is already kicked off

        self._maybe_pause_protocol()

    def _loop_writing(self, fut=Nichts):
        try:
            wenn self._conn_lost:
                return

            assert fut is self._write_fut
            self._write_fut = Nichts
            wenn fut:
                # We are in a _loop_writing() done callback, get the result
                fut.result()

            wenn not self._buffer or (self._conn_lost and self._address):
                # The connection has been closed
                wenn self._closing:
                    self._loop.call_soon(self._call_connection_lost, Nichts)
                return

            data, addr = self._buffer.popleft()
            self._buffer_size -= len(data) + self._header_size
            wenn self._address is not Nichts:
                self._write_fut = self._loop._proactor.send(self._sock,
                                                            data)
            sonst:
                self._write_fut = self._loop._proactor.sendto(self._sock,
                                                              data,
                                                              addr=addr)
        except OSError as exc:
            self._protocol.error_received(exc)
        except Exception as exc:
            self._fatal_error(exc, 'Fatal write error on datagram transport')
        sonst:
            self._write_fut.add_done_callback(self._loop_writing)
            self._maybe_resume_protocol()

    def _loop_reading(self, fut=Nichts):
        data = Nichts
        try:
            wenn self._conn_lost:
                return

            assert self._read_fut is fut or (self._read_fut is Nichts and
                                             self._closing)

            self._read_fut = Nichts
            wenn fut is not Nichts:
                res = fut.result()

                wenn self._closing:
                    # since close() has been called we ignore any read data
                    data = Nichts
                    return

                wenn self._address is not Nichts:
                    data, addr = res, self._address
                sonst:
                    data, addr = res

            wenn self._conn_lost:
                return
            wenn self._address is not Nichts:
                self._read_fut = self._loop._proactor.recv(self._sock,
                                                           self.max_size)
            sonst:
                self._read_fut = self._loop._proactor.recvfrom(self._sock,
                                                               self.max_size)
        except OSError as exc:
            self._protocol.error_received(exc)
        except exceptions.CancelledError:
            wenn not self._closing:
                raise
        sonst:
            wenn self._read_fut is not Nichts:
                self._read_fut.add_done_callback(self._loop_reading)
        finally:
            wenn data:
                self._protocol.datagram_received(data, addr)


klasse _ProactorDuplexPipeTransport(_ProactorReadPipeTransport,
                                   _ProactorBaseWritePipeTransport,
                                   transports.Transport):
    """Transport fuer duplex pipes."""

    def can_write_eof(self):
        return Falsch

    def write_eof(self):
        raise NotImplementedError


klasse _ProactorSocketTransport(_ProactorReadPipeTransport,
                               _ProactorBaseWritePipeTransport,
                               transports.Transport):
    """Transport fuer connected sockets."""

    _sendfile_compatible = constants._SendfileMode.TRY_NATIVE

    def __init__(self, loop, sock, protocol, waiter=Nichts,
                 extra=Nichts, server=Nichts):
        super().__init__(loop, sock, protocol, waiter, extra, server)
        base_events._set_nodelay(sock)

    def _set_extra(self, sock):
        _set_socket_extra(self, sock)

    def can_write_eof(self):
        return Wahr

    def write_eof(self):
        wenn self._closing or self._eof_written:
            return
        self._eof_written = Wahr
        wenn self._write_fut is Nichts:
            self._sock.shutdown(socket.SHUT_WR)


klasse BaseProactorEventLoop(base_events.BaseEventLoop):

    def __init__(self, proactor):
        super().__init__()
        logger.debug('Using proactor: %s', proactor.__class__.__name__)
        self._proactor = proactor
        self._selector = proactor   # convenient alias
        self._self_reading_future = Nichts
        self._accept_futures = {}   # socket file descriptor => Future
        proactor.set_loop(self)
        self._make_self_pipe()
        wenn threading.current_thread() is threading.main_thread():
            # wakeup fd can only be installed to a file descriptor von the main thread
            signal.set_wakeup_fd(self._csock.fileno())

    def _make_socket_transport(self, sock, protocol, waiter=Nichts,
                               extra=Nichts, server=Nichts):
        return _ProactorSocketTransport(self, sock, protocol, waiter,
                                        extra, server)

    def _make_ssl_transport(
            self, rawsock, protocol, sslcontext, waiter=Nichts,
            *, server_side=Falsch, server_hostname=Nichts,
            extra=Nichts, server=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):
        ssl_protocol = sslproto.SSLProtocol(
                self, protocol, sslcontext, waiter,
                server_side, server_hostname,
                ssl_handshake_timeout=ssl_handshake_timeout,
                ssl_shutdown_timeout=ssl_shutdown_timeout)
        _ProactorSocketTransport(self, rawsock, ssl_protocol,
                                 extra=extra, server=server)
        return ssl_protocol._app_transport

    def _make_datagram_transport(self, sock, protocol,
                                 address=Nichts, waiter=Nichts, extra=Nichts):
        return _ProactorDatagramTransport(self, sock, protocol, address,
                                          waiter, extra)

    def _make_duplex_pipe_transport(self, sock, protocol, waiter=Nichts,
                                    extra=Nichts):
        return _ProactorDuplexPipeTransport(self,
                                            sock, protocol, waiter, extra)

    def _make_read_pipe_transport(self, sock, protocol, waiter=Nichts,
                                  extra=Nichts):
        return _ProactorReadPipeTransport(self, sock, protocol, waiter, extra)

    def _make_write_pipe_transport(self, sock, protocol, waiter=Nichts,
                                   extra=Nichts):
        # We want connection_lost() to be called when other end closes
        return _ProactorWritePipeTransport(self,
                                           sock, protocol, waiter, extra)

    def close(self):
        wenn self.is_running():
            raise RuntimeError("Cannot close a running event loop")
        wenn self.is_closed():
            return

        wenn threading.current_thread() is threading.main_thread():
            signal.set_wakeup_fd(-1)
        # Call these methods before closing the event loop (before calling
        # BaseEventLoop.close), because they can schedule callbacks with
        # call_soon(), which is forbidden when the event loop is closed.
        self._stop_accept_futures()
        self._close_self_pipe()
        self._proactor.close()
        self._proactor = Nichts
        self._selector = Nichts

        # Close the event loop
        super().close()

    async def sock_recv(self, sock, n):
        return await self._proactor.recv(sock, n)

    async def sock_recv_into(self, sock, buf):
        return await self._proactor.recv_into(sock, buf)

    async def sock_recvfrom(self, sock, bufsize):
        return await self._proactor.recvfrom(sock, bufsize)

    async def sock_recvfrom_into(self, sock, buf, nbytes=0):
        wenn not nbytes:
            nbytes = len(buf)

        return await self._proactor.recvfrom_into(sock, buf, nbytes)

    async def sock_sendall(self, sock, data):
        return await self._proactor.send(sock, data)

    async def sock_sendto(self, sock, data, address):
        return await self._proactor.sendto(sock, data, 0, address)

    async def sock_connect(self, sock, address):
        wenn self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        return await self._proactor.connect(sock, address)

    async def sock_accept(self, sock):
        return await self._proactor.accept(sock)

    async def _sock_sendfile_native(self, sock, file, offset, count):
        try:
            fileno = file.fileno()
        except (AttributeError, io.UnsupportedOperation) as err:
            raise exceptions.SendfileNotAvailableError("not a regular file")
        try:
            fsize = os.fstat(fileno).st_size
        except OSError:
            raise exceptions.SendfileNotAvailableError("not a regular file")
        blocksize = count wenn count sonst fsize
        wenn not blocksize:
            return 0  # empty file

        blocksize = min(blocksize, 0xffff_ffff)
        end_pos = min(offset + count, fsize) wenn count sonst fsize
        offset = min(offset, fsize)
        total_sent = 0
        try:
            while Wahr:
                blocksize = min(end_pos - offset, blocksize)
                wenn blocksize <= 0:
                    return total_sent
                await self._proactor.sendfile(sock, file, offset, blocksize)
                offset += blocksize
                total_sent += blocksize
        finally:
            wenn total_sent > 0:
                file.seek(offset)

    async def _sendfile_native(self, transp, file, offset, count):
        resume_reading = transp.is_reading()
        transp.pause_reading()
        await transp._make_empty_waiter()
        try:
            return await self.sock_sendfile(transp._sock, file, offset, count,
                                            fallback=Falsch)
        finally:
            transp._reset_empty_waiter()
            wenn resume_reading:
                transp.resume_reading()

    def _close_self_pipe(self):
        wenn self._self_reading_future is not Nichts:
            self._self_reading_future.cancel()
            self._self_reading_future = Nichts
        self._ssock.close()
        self._ssock = Nichts
        self._csock.close()
        self._csock = Nichts
        self._internal_fds -= 1

    def _make_self_pipe(self):
        # A self-socket, really. :-)
        self._ssock, self._csock = socket.socketpair()
        self._ssock.setblocking(Falsch)
        self._csock.setblocking(Falsch)
        self._internal_fds += 1

    def _loop_self_reading(self, f=Nichts):
        try:
            wenn f is not Nichts:
                f.result()  # may raise
            wenn self._self_reading_future is not f:
                # When we scheduled this Future, we assigned it to
                # _self_reading_future. If it's not there now, something has
                # tried to cancel the loop while this callback was still in the
                # queue (see windows_events.ProactorEventLoop.run_forever). In
                # that case stop here instead of continuing to schedule a new
                # iteration.
                return
            f = self._proactor.recv(self._ssock, 4096)
        except exceptions.CancelledError:
            # _close_self_pipe() has been called, stop waiting fuer data
            return
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self.call_exception_handler({
                'message': 'Error on reading von the event loop self pipe',
                'exception': exc,
                'loop': self,
            })
        sonst:
            self._self_reading_future = f
            f.add_done_callback(self._loop_self_reading)

    def _write_to_self(self):
        # This may be called von a different thread, possibly after
        # _close_self_pipe() has been called or even while it is
        # running.  Guard fuer self._csock being Nichts or closed.  When
        # a socket is closed, send() raises OSError (with errno set to
        # EBADF, but let's not rely on the exact error code).
        csock = self._csock
        wenn csock is Nichts:
            return

        try:
            csock.send(b'\0')
        except OSError:
            wenn self._debug:
                logger.debug("Fail to write a null byte into the "
                             "self-pipe socket",
                             exc_info=Wahr)

    def _start_serving(self, protocol_factory, sock,
                       sslcontext=Nichts, server=Nichts, backlog=100,
                       ssl_handshake_timeout=Nichts,
                       ssl_shutdown_timeout=Nichts):

        def loop(f=Nichts):
            try:
                wenn f is not Nichts:
                    conn, addr = f.result()
                    wenn self._debug:
                        logger.debug("%r got a new connection von %r: %r",
                                     server, addr, conn)
                    protocol = protocol_factory()
                    wenn sslcontext is not Nichts:
                        self._make_ssl_transport(
                            conn, protocol, sslcontext, server_side=Wahr,
                            extra={'peername': addr}, server=server,
                            ssl_handshake_timeout=ssl_handshake_timeout,
                            ssl_shutdown_timeout=ssl_shutdown_timeout)
                    sonst:
                        self._make_socket_transport(
                            conn, protocol,
                            extra={'peername': addr}, server=server)
                wenn self.is_closed():
                    return
                f = self._proactor.accept(sock)
            except OSError as exc:
                wenn sock.fileno() != -1:
                    self.call_exception_handler({
                        'message': 'Accept failed on a socket',
                        'exception': exc,
                        'socket': trsock.TransportSocket(sock),
                    })
                    sock.close()
                sowenn self._debug:
                    logger.debug("Accept failed on socket %r",
                                 sock, exc_info=Wahr)
            except exceptions.CancelledError:
                sock.close()
            sonst:
                self._accept_futures[sock.fileno()] = f
                f.add_done_callback(loop)

        self.call_soon(loop)

    def _process_events(self, event_list):
        # Events are processed in the IocpProactor._poll() method
        pass

    def _stop_accept_futures(self):
        fuer future in self._accept_futures.values():
            future.cancel()
        self._accept_futures.clear()

    def _stop_serving(self, sock):
        future = self._accept_futures.pop(sock.fileno(), Nichts)
        wenn future:
            future.cancel()
        self._proactor._stop_serving(sock)
        sock.close()
