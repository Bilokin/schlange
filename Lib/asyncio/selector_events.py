"""Event loop using a selector und related classes.

A selector is a "notify-when-ready" multiplexer.  For a subclass which
also includes support fuer signal handling, see the unix_events sub-module.
"""

__all__ = 'BaseSelectorEventLoop',

importiere collections
importiere errno
importiere functools
importiere itertools
importiere os
importiere selectors
importiere socket
importiere warnings
importiere weakref
versuch:
    importiere ssl
ausser ImportError:  # pragma: no cover
    ssl = Nichts

von . importiere base_events
von . importiere constants
von . importiere events
von . importiere futures
von . importiere protocols
von . importiere sslproto
von . importiere transports
von . importiere trsock
von .log importiere logger

_HAS_SENDMSG = hasattr(socket.socket, 'sendmsg')

wenn _HAS_SENDMSG:
    versuch:
        SC_IOV_MAX = os.sysconf('SC_IOV_MAX')
    ausser OSError:
        # Fallback to send
        _HAS_SENDMSG = Falsch

def _test_selector_event(selector, fd, event):
    # Test wenn the selector is monitoring 'event' events
    # fuer the file descriptor 'fd'.
    versuch:
        key = selector.get_key(fd)
    ausser KeyError:
        gib Falsch
    sonst:
        gib bool(key.events & event)


klasse BaseSelectorEventLoop(base_events.BaseEventLoop):
    """Selector event loop.

    See events.EventLoop fuer API specification.
    """

    def __init__(self, selector=Nichts):
        super().__init__()

        wenn selector is Nichts:
            selector = selectors.DefaultSelector()
        logger.debug('Using selector: %s', selector.__class__.__name__)
        self._selector = selector
        self._make_self_pipe()
        self._transports = weakref.WeakValueDictionary()

    def _make_socket_transport(self, sock, protocol, waiter=Nichts, *,
                               extra=Nichts, server=Nichts):
        self._ensure_fd_no_transport(sock)
        gib _SelectorSocketTransport(self, sock, protocol, waiter,
                                        extra, server)

    def _make_ssl_transport(
            self, rawsock, protocol, sslcontext, waiter=Nichts,
            *, server_side=Falsch, server_hostname=Nichts,
            extra=Nichts, server=Nichts,
            ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
            ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT,
    ):
        self._ensure_fd_no_transport(rawsock)
        ssl_protocol = sslproto.SSLProtocol(
            self, protocol, sslcontext, waiter,
            server_side, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout
        )
        _SelectorSocketTransport(self, rawsock, ssl_protocol,
                                 extra=extra, server=server)
        gib ssl_protocol._app_transport

    def _make_datagram_transport(self, sock, protocol,
                                 address=Nichts, waiter=Nichts, extra=Nichts):
        self._ensure_fd_no_transport(sock)
        gib _SelectorDatagramTransport(self, sock, protocol,
                                          address, waiter, extra)

    def close(self):
        wenn self.is_running():
            wirf RuntimeError("Cannot close a running event loop")
        wenn self.is_closed():
            gib
        self._close_self_pipe()
        super().close()
        wenn self._selector is nicht Nichts:
            self._selector.close()
            self._selector = Nichts

    def _close_self_pipe(self):
        self._remove_reader(self._ssock.fileno())
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
        self._add_reader(self._ssock.fileno(), self._read_from_self)

    def _process_self_data(self, data):
        pass

    def _read_from_self(self):
        waehrend Wahr:
            versuch:
                data = self._ssock.recv(4096)
                wenn nicht data:
                    breche
                self._process_self_data(data)
            ausser InterruptedError:
                weiter
            ausser BlockingIOError:
                breche

    def _write_to_self(self):
        # This may be called von a different thread, possibly after
        # _close_self_pipe() has been called oder even waehrend it is
        # running.  Guard fuer self._csock being Nichts oder closed.  When
        # a socket is closed, send() raises OSError (with errno set to
        # EBADF, but let's nicht rely on the exact error code).
        csock = self._csock
        wenn csock is Nichts:
            gib

        versuch:
            csock.send(b'\0')
        ausser OSError:
            wenn self._debug:
                logger.debug("Fail to write a null byte into the "
                             "self-pipe socket",
                             exc_info=Wahr)

    def _start_serving(self, protocol_factory, sock,
                       sslcontext=Nichts, server=Nichts, backlog=100,
                       ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
                       ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT):
        self._add_reader(sock.fileno(), self._accept_connection,
                         protocol_factory, sock, sslcontext, server, backlog,
                         ssl_handshake_timeout, ssl_shutdown_timeout)

    def _accept_connection(
            self, protocol_factory, sock,
            sslcontext=Nichts, server=Nichts, backlog=100,
            ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
            ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT):
        # This method is only called once fuer each event loop tick where the
        # listening socket has triggered an EVENT_READ. There may be multiple
        # connections waiting fuer an .accept() so it is called in a loop.
        # See https://bugs.python.org/issue27906 fuer more details.
        fuer _ in range(backlog + 1):
            versuch:
                conn, addr = sock.accept()
                wenn self._debug:
                    logger.debug("%r got a new connection von %r: %r",
                                 server, addr, conn)
                conn.setblocking(Falsch)
            ausser ConnectionAbortedError:
                # Discard connections that were aborted before accept().
                weiter
            ausser (BlockingIOError, InterruptedError):
                # Early exit because of a signal oder
                # the socket accept buffer is empty.
                gib
            ausser OSError als exc:
                # There's nowhere to send the error, so just log it.
                wenn exc.errno in (errno.EMFILE, errno.ENFILE,
                                 errno.ENOBUFS, errno.ENOMEM):
                    # Some platforms (e.g. Linux keep reporting the FD as
                    # ready, so we remove the read handler temporarily.
                    # We'll try again in a while.
                    self.call_exception_handler({
                        'message': 'socket.accept() out of system resource',
                        'exception': exc,
                        'socket': trsock.TransportSocket(sock),
                    })
                    self._remove_reader(sock.fileno())
                    self.call_later(constants.ACCEPT_RETRY_DELAY,
                                    self._start_serving,
                                    protocol_factory, sock, sslcontext, server,
                                    backlog, ssl_handshake_timeout,
                                    ssl_shutdown_timeout)
                sonst:
                    wirf  # The event loop will catch, log und ignore it.
            sonst:
                extra = {'peername': addr}
                accept = self._accept_connection2(
                    protocol_factory, conn, extra, sslcontext, server,
                    ssl_handshake_timeout, ssl_shutdown_timeout)
                self.create_task(accept)

    async def _accept_connection2(
            self, protocol_factory, conn, extra,
            sslcontext=Nichts, server=Nichts,
            ssl_handshake_timeout=constants.SSL_HANDSHAKE_TIMEOUT,
            ssl_shutdown_timeout=constants.SSL_SHUTDOWN_TIMEOUT):
        protocol = Nichts
        transport = Nichts
        versuch:
            protocol = protocol_factory()
            waiter = self.create_future()
            wenn sslcontext:
                transport = self._make_ssl_transport(
                    conn, protocol, sslcontext, waiter=waiter,
                    server_side=Wahr, extra=extra, server=server,
                    ssl_handshake_timeout=ssl_handshake_timeout,
                    ssl_shutdown_timeout=ssl_shutdown_timeout)
            sonst:
                transport = self._make_socket_transport(
                    conn, protocol, waiter=waiter, extra=extra,
                    server=server)

            versuch:
                await waiter
            ausser BaseException:
                transport.close()
                # gh-109534: When an exception is raised by the SSLProtocol object the
                # exception set in this future can keep the protocol object alive und
                # cause a reference cycle.
                waiter = Nichts
                wirf
                # It's now up to the protocol to handle the connection.

        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            wenn self._debug:
                context = {
                    'message':
                        'Error on transport creation fuer incoming connection',
                    'exception': exc,
                }
                wenn protocol is nicht Nichts:
                    context['protocol'] = protocol
                wenn transport is nicht Nichts:
                    context['transport'] = transport
                self.call_exception_handler(context)

    def _ensure_fd_no_transport(self, fd):
        fileno = fd
        wenn nicht isinstance(fileno, int):
            versuch:
                fileno = int(fileno.fileno())
            ausser (AttributeError, TypeError, ValueError):
                # This code matches selectors._fileobj_to_fd function.
                wirf ValueError(f"Invalid file object: {fd!r}") von Nichts
        transport = self._transports.get(fileno)
        wenn transport und nicht transport.is_closing():
            wirf RuntimeError(
                f'File descriptor {fd!r} is used by transport '
                f'{transport!r}')

    def _add_reader(self, fd, callback, *args):
        self._check_closed()
        handle = events.Handle(callback, args, self, Nichts)
        key = self._selector.get_map().get(fd)
        wenn key is Nichts:
            self._selector.register(fd, selectors.EVENT_READ,
                                    (handle, Nichts))
        sonst:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_READ,
                                  (handle, writer))
            wenn reader is nicht Nichts:
                reader.cancel()
        gib handle

    def _remove_reader(self, fd):
        wenn self.is_closed():
            gib Falsch
        key = self._selector.get_map().get(fd)
        wenn key is Nichts:
            gib Falsch
        mask, (reader, writer) = key.events, key.data
        mask &= ~selectors.EVENT_READ
        wenn nicht mask:
            self._selector.unregister(fd)
        sonst:
            self._selector.modify(fd, mask, (Nichts, writer))

        wenn reader is nicht Nichts:
            reader.cancel()
            gib Wahr
        sonst:
            gib Falsch

    def _add_writer(self, fd, callback, *args):
        self._check_closed()
        handle = events.Handle(callback, args, self, Nichts)
        key = self._selector.get_map().get(fd)
        wenn key is Nichts:
            self._selector.register(fd, selectors.EVENT_WRITE,
                                    (Nichts, handle))
        sonst:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_WRITE,
                                  (reader, handle))
            wenn writer is nicht Nichts:
                writer.cancel()
        gib handle

    def _remove_writer(self, fd):
        """Remove a writer callback."""
        wenn self.is_closed():
            gib Falsch
        key = self._selector.get_map().get(fd)
        wenn key is Nichts:
            gib Falsch
        mask, (reader, writer) = key.events, key.data
        # Remove both writer und connector.
        mask &= ~selectors.EVENT_WRITE
        wenn nicht mask:
            self._selector.unregister(fd)
        sonst:
            self._selector.modify(fd, mask, (reader, Nichts))

        wenn writer is nicht Nichts:
            writer.cancel()
            gib Wahr
        sonst:
            gib Falsch

    def add_reader(self, fd, callback, *args):
        """Add a reader callback."""
        self._ensure_fd_no_transport(fd)
        self._add_reader(fd, callback, *args)

    def remove_reader(self, fd):
        """Remove a reader callback."""
        self._ensure_fd_no_transport(fd)
        gib self._remove_reader(fd)

    def add_writer(self, fd, callback, *args):
        """Add a writer callback.."""
        self._ensure_fd_no_transport(fd)
        self._add_writer(fd, callback, *args)

    def remove_writer(self, fd):
        """Remove a writer callback."""
        self._ensure_fd_no_transport(fd)
        gib self._remove_writer(fd)

    async def sock_recv(self, sock, n):
        """Receive data von the socket.

        The gib value is a bytes object representing the data received.
        The maximum amount of data to be received at once is specified by
        nbytes.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        versuch:
            gib sock.recv(n)
        ausser (BlockingIOError, InterruptedError):
            pass
        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        handle = self._add_reader(fd, self._sock_recv, fut, sock, n)
        fut.add_done_callback(
            functools.partial(self._sock_read_done, fd, handle=handle))
        gib await fut

    def _sock_read_done(self, fd, fut, handle=Nichts):
        wenn handle is Nichts oder nicht handle.cancelled():
            self.remove_reader(fd)

    def _sock_recv(self, fut, sock, n):
        # _sock_recv() can add itself als an I/O callback wenn the operation can't
        # be done immediately. Don't use it directly, call sock_recv().
        wenn fut.done():
            gib
        versuch:
            data = sock.recv(n)
        ausser (BlockingIOError, InterruptedError):
            gib  # try again next time
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(data)

    async def sock_recv_into(self, sock, buf):
        """Receive data von the socket.

        The received data is written into *buf* (a writable buffer).
        The gib value is the number of bytes written.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        versuch:
            gib sock.recv_into(buf)
        ausser (BlockingIOError, InterruptedError):
            pass
        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        handle = self._add_reader(fd, self._sock_recv_into, fut, sock, buf)
        fut.add_done_callback(
            functools.partial(self._sock_read_done, fd, handle=handle))
        gib await fut

    def _sock_recv_into(self, fut, sock, buf):
        # _sock_recv_into() can add itself als an I/O callback wenn the operation
        # can't be done immediately. Don't use it directly, call
        # sock_recv_into().
        wenn fut.done():
            gib
        versuch:
            nbytes = sock.recv_into(buf)
        ausser (BlockingIOError, InterruptedError):
            gib  # try again next time
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(nbytes)

    async def sock_recvfrom(self, sock, bufsize):
        """Receive a datagram von a datagram socket.

        The gib value is a tuple of (bytes, address) representing the
        datagram received und the address it came from.
        The maximum amount of data to be received at once is specified by
        nbytes.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        versuch:
            gib sock.recvfrom(bufsize)
        ausser (BlockingIOError, InterruptedError):
            pass
        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        handle = self._add_reader(fd, self._sock_recvfrom, fut, sock, bufsize)
        fut.add_done_callback(
            functools.partial(self._sock_read_done, fd, handle=handle))
        gib await fut

    def _sock_recvfrom(self, fut, sock, bufsize):
        # _sock_recvfrom() can add itself als an I/O callback wenn the operation
        # can't be done immediately. Don't use it directly, call
        # sock_recvfrom().
        wenn fut.done():
            gib
        versuch:
            result = sock.recvfrom(bufsize)
        ausser (BlockingIOError, InterruptedError):
            gib  # try again next time
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(result)

    async def sock_recvfrom_into(self, sock, buf, nbytes=0):
        """Receive data von the socket.

        The received data is written into *buf* (a writable buffer).
        The gib value is a tuple of (number of bytes written, address).
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        wenn nicht nbytes:
            nbytes = len(buf)

        versuch:
            gib sock.recvfrom_into(buf, nbytes)
        ausser (BlockingIOError, InterruptedError):
            pass
        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        handle = self._add_reader(fd, self._sock_recvfrom_into, fut, sock, buf,
                                  nbytes)
        fut.add_done_callback(
            functools.partial(self._sock_read_done, fd, handle=handle))
        gib await fut

    def _sock_recvfrom_into(self, fut, sock, buf, bufsize):
        # _sock_recv_into() can add itself als an I/O callback wenn the operation
        # can't be done immediately. Don't use it directly, call
        # sock_recv_into().
        wenn fut.done():
            gib
        versuch:
            result = sock.recvfrom_into(buf, bufsize)
        ausser (BlockingIOError, InterruptedError):
            gib  # try again next time
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(result)

    async def sock_sendall(self, sock, data):
        """Send data to the socket.

        The socket must be connected to a remote socket. This method continues
        to send data von data until either all data has been sent oder an
        error occurs. Nichts is returned on success. On error, an exception is
        raised, und there is no way to determine how much data, wenn any, was
        successfully processed by the receiving end of the connection.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        versuch:
            n = sock.send(data)
        ausser (BlockingIOError, InterruptedError):
            n = 0

        wenn n == len(data):
            # all data sent
            gib

        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        # use a trick mit a list in closure to store a mutable state
        handle = self._add_writer(fd, self._sock_sendall, fut, sock,
                                  memoryview(data), [n])
        fut.add_done_callback(
            functools.partial(self._sock_write_done, fd, handle=handle))
        gib await fut

    def _sock_sendall(self, fut, sock, view, pos):
        wenn fut.done():
            # Future cancellation can be scheduled on previous loop iteration
            gib
        start = pos[0]
        versuch:
            n = sock.send(view[start:])
        ausser (BlockingIOError, InterruptedError):
            gib
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
            gib

        start += n

        wenn start == len(view):
            fut.set_result(Nichts)
        sonst:
            pos[0] = start

    async def sock_sendto(self, sock, data, address):
        """Send data to the socket.

        The socket must be connected to a remote socket. This method continues
        to send data von data until either all data has been sent oder an
        error occurs. Nichts is returned on success. On error, an exception is
        raised, und there is no way to determine how much data, wenn any, was
        successfully processed by the receiving end of the connection.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        versuch:
            gib sock.sendto(data, address)
        ausser (BlockingIOError, InterruptedError):
            pass

        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        # use a trick mit a list in closure to store a mutable state
        handle = self._add_writer(fd, self._sock_sendto, fut, sock, data,
                                  address)
        fut.add_done_callback(
            functools.partial(self._sock_write_done, fd, handle=handle))
        gib await fut

    def _sock_sendto(self, fut, sock, data, address):
        wenn fut.done():
            # Future cancellation can be scheduled on previous loop iteration
            gib
        versuch:
            n = sock.sendto(data, 0, address)
        ausser (BlockingIOError, InterruptedError):
            gib
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(n)

    async def sock_connect(self, sock, address):
        """Connect to a remote socket at address.

        This method is a coroutine.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")

        wenn sock.family == socket.AF_INET oder (
                base_events._HAS_IPv6 und sock.family == socket.AF_INET6):
            resolved = await self._ensure_resolved(
                address, family=sock.family, type=sock.type, proto=sock.proto,
                loop=self,
            )
            _, _, _, _, address = resolved[0]

        fut = self.create_future()
        self._sock_connect(fut, sock, address)
        versuch:
            gib await fut
        schliesslich:
            # Needed to breche cycles when an exception occurs.
            fut = Nichts

    def _sock_connect(self, fut, sock, address):
        fd = sock.fileno()
        versuch:
            sock.connect(address)
        ausser (BlockingIOError, InterruptedError):
            # Issue #23618: When the C function connect() fails mit EINTR, the
            # connection runs in background. We have to wait until the socket
            # becomes writable to be notified when the connection succeed oder
            # fails.
            self._ensure_fd_no_transport(fd)
            handle = self._add_writer(
                fd, self._sock_connect_cb, fut, sock, address)
            fut.add_done_callback(
                functools.partial(self._sock_write_done, fd, handle=handle))
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(Nichts)
        schliesslich:
            fut = Nichts

    def _sock_write_done(self, fd, fut, handle=Nichts):
        wenn handle is Nichts oder nicht handle.cancelled():
            self.remove_writer(fd)

    def _sock_connect_cb(self, fut, sock, address):
        wenn fut.done():
            gib

        versuch:
            err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            wenn err != 0:
                # Jump to any ausser clause below.
                wirf OSError(err, f'Connect call failed {address}')
        ausser (BlockingIOError, InterruptedError):
            # socket is still registered, the callback will be retried later
            pass
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result(Nichts)
        schliesslich:
            fut = Nichts

    async def sock_accept(self, sock):
        """Accept a connection.

        The socket must be bound to an address und listening fuer connections.
        The gib value is a pair (conn, address) where conn is a new socket
        object usable to send und receive data on the connection, und address
        is the address bound to the socket on the other end of the connection.
        """
        base_events._check_ssl_socket(sock)
        wenn self._debug und sock.gettimeout() != 0:
            wirf ValueError("the socket must be non-blocking")
        fut = self.create_future()
        self._sock_accept(fut, sock)
        gib await fut

    def _sock_accept(self, fut, sock):
        fd = sock.fileno()
        versuch:
            conn, address = sock.accept()
            conn.setblocking(Falsch)
        ausser (BlockingIOError, InterruptedError):
            self._ensure_fd_no_transport(fd)
            handle = self._add_reader(fd, self._sock_accept, fut, sock)
            fut.add_done_callback(
                functools.partial(self._sock_read_done, fd, handle=handle))
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            fut.set_exception(exc)
        sonst:
            fut.set_result((conn, address))

    async def _sendfile_native(self, transp, file, offset, count):
        del self._transports[transp._sock_fd]
        resume_reading = transp.is_reading()
        transp.pause_reading()
        await transp._make_empty_waiter()
        versuch:
            gib await self.sock_sendfile(transp._sock, file, offset, count,
                                            fallback=Falsch)
        schliesslich:
            transp._reset_empty_waiter()
            wenn resume_reading:
                transp.resume_reading()
            self._transports[transp._sock_fd] = transp

    def _process_events(self, event_list):
        fuer key, mask in event_list:
            fileobj, (reader, writer) = key.fileobj, key.data
            wenn mask & selectors.EVENT_READ und reader is nicht Nichts:
                wenn reader._cancelled:
                    self._remove_reader(fileobj)
                sonst:
                    self._add_callback(reader)
            wenn mask & selectors.EVENT_WRITE und writer is nicht Nichts:
                wenn writer._cancelled:
                    self._remove_writer(fileobj)
                sonst:
                    self._add_callback(writer)

    def _stop_serving(self, sock):
        self._remove_reader(sock.fileno())
        sock.close()


klasse _SelectorTransport(transports._FlowControlMixin,
                         transports.Transport):

    max_size = 256 * 1024  # Buffer size passed to recv().

    # Attribute used in the destructor: it must be set even wenn the constructor
    # is nicht called (see _SelectorSslTransport which may start by raising an
    # exception)
    _sock = Nichts

    def __init__(self, loop, sock, protocol, extra=Nichts, server=Nichts):
        super().__init__(extra, loop)
        self._extra['socket'] = trsock.TransportSocket(sock)
        versuch:
            self._extra['sockname'] = sock.getsockname()
        ausser OSError:
            self._extra['sockname'] = Nichts
        wenn 'peername' nicht in self._extra:
            versuch:
                self._extra['peername'] = sock.getpeername()
            ausser socket.error:
                self._extra['peername'] = Nichts
        self._sock = sock
        self._sock_fd = sock.fileno()

        self._protocol_connected = Falsch
        self.set_protocol(protocol)

        self._server = server
        self._buffer = collections.deque()
        self._conn_lost = 0  # Set when call to connection_lost scheduled.
        self._closing = Falsch  # Set when close() called.
        self._paused = Falsch  # Set when pause_reading() called

        wenn self._server is nicht Nichts:
            self._server._attach(self)
        loop._transports[self._sock_fd] = self

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self._sock is Nichts:
            info.append('closed')
        sowenn self._closing:
            info.append('closing')
        info.append(f'fd={self._sock_fd}')
        # test wenn the transport was closed
        wenn self._loop is nicht Nichts und nicht self._loop.is_closed():
            polling = _test_selector_event(self._loop._selector,
                                           self._sock_fd, selectors.EVENT_READ)
            wenn polling:
                info.append('read=polling')
            sonst:
                info.append('read=idle')

            polling = _test_selector_event(self._loop._selector,
                                           self._sock_fd,
                                           selectors.EVENT_WRITE)
            wenn polling:
                state = 'polling'
            sonst:
                state = 'idle'

            bufsize = self.get_write_buffer_size()
            info.append(f'write=<{state}, bufsize={bufsize}>')
        gib '<{}>'.format(' '.join(info))

    def abort(self):
        self._force_close(Nichts)

    def set_protocol(self, protocol):
        self._protocol = protocol
        self._protocol_connected = Wahr

    def get_protocol(self):
        gib self._protocol

    def is_closing(self):
        gib self._closing

    def is_reading(self):
        gib nicht self.is_closing() und nicht self._paused

    def pause_reading(self):
        wenn nicht self.is_reading():
            gib
        self._paused = Wahr
        self._loop._remove_reader(self._sock_fd)
        wenn self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self):
        wenn self._closing oder nicht self._paused:
            gib
        self._paused = Falsch
        self._add_reader(self._sock_fd, self._read_ready)
        wenn self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    def close(self):
        wenn self._closing:
            gib
        self._closing = Wahr
        self._loop._remove_reader(self._sock_fd)
        wenn nicht self._buffer:
            self._conn_lost += 1
            self._loop._remove_writer(self._sock_fd)
            self._loop.call_soon(self._call_connection_lost, Nichts)

    def __del__(self, _warn=warnings.warn):
        wenn self._sock is nicht Nichts:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self._sock.close()
            wenn self._server is nicht Nichts:
                self._server._detach(self)

    def _fatal_error(self, exc, message='Fatal error on transport'):
        # Should be called von exception handler only.
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
        self._force_close(exc)

    def _force_close(self, exc):
        wenn self._conn_lost:
            gib
        wenn self._buffer:
            self._buffer.clear()
            self._loop._remove_writer(self._sock_fd)
        wenn nicht self._closing:
            self._closing = Wahr
            self._loop._remove_reader(self._sock_fd)
        self._conn_lost += 1
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        versuch:
            wenn self._protocol_connected:
                self._protocol.connection_lost(exc)
        schliesslich:
            self._sock.close()
            self._sock = Nichts
            self._protocol = Nichts
            self._loop = Nichts
            server = self._server
            wenn server is nicht Nichts:
                server._detach(self)
                self._server = Nichts

    def get_write_buffer_size(self):
        gib sum(map(len, self._buffer))

    def _add_reader(self, fd, callback, *args):
        wenn nicht self.is_reading():
            gib
        self._loop._add_reader(fd, callback, *args)


klasse _SelectorSocketTransport(_SelectorTransport):

    _start_tls_compatible = Wahr
    _sendfile_compatible = constants._SendfileMode.TRY_NATIVE

    def __init__(self, loop, sock, protocol, waiter=Nichts,
                 extra=Nichts, server=Nichts):

        self._read_ready_cb = Nichts
        super().__init__(loop, sock, protocol, extra, server)
        self._eof = Falsch
        self._empty_waiter = Nichts
        wenn _HAS_SENDMSG:
            self._write_ready = self._write_sendmsg
        sonst:
            self._write_ready = self._write_send
        # Disable the Nagle algorithm -- small writes will be
        # sent without waiting fuer the TCP ACK.  This generally
        # decreases the latency (in some cases significantly.)
        base_events._set_nodelay(self._sock)

        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._add_reader,
                             self._sock_fd, self._read_ready)
        wenn waiter is nicht Nichts:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, Nichts)

    def set_protocol(self, protocol):
        wenn isinstance(protocol, protocols.BufferedProtocol):
            self._read_ready_cb = self._read_ready__get_buffer
        sonst:
            self._read_ready_cb = self._read_ready__data_received

        super().set_protocol(protocol)

    def _read_ready(self):
        self._read_ready_cb()

    def _read_ready__get_buffer(self):
        wenn self._conn_lost:
            gib

        versuch:
            buf = self._protocol.get_buffer(-1)
            wenn nicht len(buf):
                wirf RuntimeError('get_buffer() returned an empty buffer')
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.get_buffer() call failed.')
            gib

        versuch:
            nbytes = self._sock.recv_into(buf)
        ausser (BlockingIOError, InterruptedError):
            gib
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(exc, 'Fatal read error on socket transport')
            gib

        wenn nicht nbytes:
            self._read_ready__on_eof()
            gib

        versuch:
            self._protocol.buffer_updated(nbytes)
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.buffer_updated() call failed.')

    def _read_ready__data_received(self):
        wenn self._conn_lost:
            gib
        versuch:
            data = self._sock.recv(self.max_size)
        ausser (BlockingIOError, InterruptedError):
            gib
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(exc, 'Fatal read error on socket transport')
            gib

        wenn nicht data:
            self._read_ready__on_eof()
            gib

        versuch:
            self._protocol.data_received(data)
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.data_received() call failed.')

    def _read_ready__on_eof(self):
        wenn self._loop.get_debug():
            logger.debug("%r received EOF", self)

        versuch:
            keep_open = self._protocol.eof_received()
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(
                exc, 'Fatal error: protocol.eof_received() call failed.')
            gib

        wenn keep_open:
            # We're keeping the connection open so the
            # protocol can write more, but we still can't
            # receive more, so remove the reader callback.
            self._loop._remove_reader(self._sock_fd)
        sonst:
            self.close()

    def write(self, data):
        wenn nicht isinstance(data, (bytes, bytearray, memoryview)):
            wirf TypeError(f'data argument must be a bytes-like object, '
                            f'not {type(data).__name__!r}')
        wenn self._eof:
            wirf RuntimeError('Cannot call write() after write_eof()')
        wenn self._empty_waiter is nicht Nichts:
            wirf RuntimeError('unable to write; sendfile is in progress')
        wenn nicht data:
            gib

        wenn self._conn_lost:
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            gib

        wenn nicht self._buffer:
            # Optimization: try to send now.
            versuch:
                n = self._sock.send(data)
            ausser (BlockingIOError, InterruptedError):
                pass
            ausser (SystemExit, KeyboardInterrupt):
                wirf
            ausser BaseException als exc:
                self._fatal_error(exc, 'Fatal write error on socket transport')
                gib
            sonst:
                data = memoryview(data)[n:]
                wenn nicht data:
                    gib
            # Not all was written; register write handler.
            self._loop._add_writer(self._sock_fd, self._write_ready)

        # Add it to the buffer.
        self._buffer.append(data)
        self._maybe_pause_protocol()

    def _get_sendmsg_buffer(self):
        gib itertools.islice(self._buffer, SC_IOV_MAX)

    def _write_sendmsg(self):
        assert self._buffer, 'Data should nicht be empty'
        wenn self._conn_lost:
            gib
        versuch:
            nbytes = self._sock.sendmsg(self._get_sendmsg_buffer())
            self._adjust_leftover_buffer(nbytes)
        ausser (BlockingIOError, InterruptedError):
            pass
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._loop._remove_writer(self._sock_fd)
            self._buffer.clear()
            self._fatal_error(exc, 'Fatal write error on socket transport')
            wenn self._empty_waiter is nicht Nichts:
                self._empty_waiter.set_exception(exc)
        sonst:
            self._maybe_resume_protocol()  # May append to buffer.
            wenn nicht self._buffer:
                self._loop._remove_writer(self._sock_fd)
                wenn self._empty_waiter is nicht Nichts:
                    self._empty_waiter.set_result(Nichts)
                wenn self._closing:
                    self._call_connection_lost(Nichts)
                sowenn self._eof:
                    self._sock.shutdown(socket.SHUT_WR)

    def _adjust_leftover_buffer(self, nbytes: int) -> Nichts:
        buffer = self._buffer
        waehrend nbytes:
            b = buffer.popleft()
            b_len = len(b)
            wenn b_len <= nbytes:
                nbytes -= b_len
            sonst:
                buffer.appendleft(b[nbytes:])
                breche

    def _write_send(self):
        assert self._buffer, 'Data should nicht be empty'
        wenn self._conn_lost:
            gib
        versuch:
            buffer = self._buffer.popleft()
            n = self._sock.send(buffer)
            wenn n != len(buffer):
                # Not all data was written
                self._buffer.appendleft(buffer[n:])
        ausser (BlockingIOError, InterruptedError):
            pass
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._loop._remove_writer(self._sock_fd)
            self._buffer.clear()
            self._fatal_error(exc, 'Fatal write error on socket transport')
            wenn self._empty_waiter is nicht Nichts:
                self._empty_waiter.set_exception(exc)
        sonst:
            self._maybe_resume_protocol()  # May append to buffer.
            wenn nicht self._buffer:
                self._loop._remove_writer(self._sock_fd)
                wenn self._empty_waiter is nicht Nichts:
                    self._empty_waiter.set_result(Nichts)
                wenn self._closing:
                    self._call_connection_lost(Nichts)
                sowenn self._eof:
                    self._sock.shutdown(socket.SHUT_WR)

    def write_eof(self):
        wenn self._closing oder self._eof:
            gib
        self._eof = Wahr
        wenn nicht self._buffer:
            self._sock.shutdown(socket.SHUT_WR)

    def writelines(self, list_of_data):
        wenn self._eof:
            wirf RuntimeError('Cannot call writelines() after write_eof()')
        wenn self._empty_waiter is nicht Nichts:
            wirf RuntimeError('unable to writelines; sendfile is in progress')
        wenn nicht list_of_data:
            gib
        self._buffer.extend([memoryview(data) fuer data in list_of_data])
        self._write_ready()
        # If the entire buffer couldn't be written, register a write handler
        wenn self._buffer:
            self._loop._add_writer(self._sock_fd, self._write_ready)
            self._maybe_pause_protocol()

    def can_write_eof(self):
        gib Wahr

    def _call_connection_lost(self, exc):
        versuch:
            super()._call_connection_lost(exc)
        schliesslich:
            self._write_ready = Nichts
            wenn self._empty_waiter is nicht Nichts:
                self._empty_waiter.set_exception(
                    ConnectionError("Connection is closed by peer"))

    def _make_empty_waiter(self):
        wenn self._empty_waiter is nicht Nichts:
            wirf RuntimeError("Empty waiter is already set")
        self._empty_waiter = self._loop.create_future()
        wenn nicht self._buffer:
            self._empty_waiter.set_result(Nichts)
        gib self._empty_waiter

    def _reset_empty_waiter(self):
        self._empty_waiter = Nichts

    def close(self):
        self._read_ready_cb = Nichts
        super().close()


klasse _SelectorDatagramTransport(_SelectorTransport, transports.DatagramTransport):

    _buffer_factory = collections.deque
    _header_size = 8

    def __init__(self, loop, sock, protocol, address=Nichts,
                 waiter=Nichts, extra=Nichts):
        super().__init__(loop, sock, protocol, extra)
        self._address = address
        self._buffer_size = 0
        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._add_reader,
                             self._sock_fd, self._read_ready)
        wenn waiter is nicht Nichts:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, Nichts)

    def get_write_buffer_size(self):
        gib self._buffer_size

    def _read_ready(self):
        wenn self._conn_lost:
            gib
        versuch:
            data, addr = self._sock.recvfrom(self.max_size)
        ausser (BlockingIOError, InterruptedError):
            pass
        ausser OSError als exc:
            self._protocol.error_received(exc)
        ausser (SystemExit, KeyboardInterrupt):
            wirf
        ausser BaseException als exc:
            self._fatal_error(exc, 'Fatal read error on datagram transport')
        sonst:
            self._protocol.datagram_received(data, addr)

    def sendto(self, data, addr=Nichts):
        wenn nicht isinstance(data, (bytes, bytearray, memoryview)):
            wirf TypeError(f'data argument must be a bytes-like object, '
                            f'not {type(data).__name__!r}')

        wenn self._address:
            wenn addr nicht in (Nichts, self._address):
                wirf ValueError(
                    f'Invalid address: must be Nichts oder {self._address}')
            addr = self._address

        wenn self._conn_lost und self._address:
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            gib

        wenn nicht self._buffer:
            # Attempt to send it right away first.
            versuch:
                wenn self._extra['peername']:
                    self._sock.send(data)
                sonst:
                    self._sock.sendto(data, addr)
                gib
            ausser (BlockingIOError, InterruptedError):
                self._loop._add_writer(self._sock_fd, self._sendto_ready)
            ausser OSError als exc:
                self._protocol.error_received(exc)
                gib
            ausser (SystemExit, KeyboardInterrupt):
                wirf
            ausser BaseException als exc:
                self._fatal_error(
                    exc, 'Fatal write error on datagram transport')
                gib

        # Ensure that what we buffer is immutable.
        self._buffer.append((bytes(data), addr))
        self._buffer_size += len(data) + self._header_size
        self._maybe_pause_protocol()

    def _sendto_ready(self):
        waehrend self._buffer:
            data, addr = self._buffer.popleft()
            self._buffer_size -= len(data) + self._header_size
            versuch:
                wenn self._extra['peername']:
                    self._sock.send(data)
                sonst:
                    self._sock.sendto(data, addr)
            ausser (BlockingIOError, InterruptedError):
                self._buffer.appendleft((data, addr))  # Try again later.
                self._buffer_size += len(data) + self._header_size
                breche
            ausser OSError als exc:
                self._protocol.error_received(exc)
                gib
            ausser (SystemExit, KeyboardInterrupt):
                wirf
            ausser BaseException als exc:
                self._fatal_error(
                    exc, 'Fatal write error on datagram transport')
                gib

        self._maybe_resume_protocol()  # May append to buffer.
        wenn nicht self._buffer:
            self._loop._remove_writer(self._sock_fd)
            wenn self._closing:
                self._call_connection_lost(Nichts)
