"""Selector event loop fuer Unix mit signal handling."""

importiere errno
importiere io
importiere itertools
importiere os
importiere selectors
importiere signal
importiere socket
importiere stat
importiere subprocess
importiere sys
importiere threading
importiere warnings

von . importiere base_events
von . importiere base_subprocess
von . importiere constants
von . importiere coroutines
von . importiere events
von . importiere exceptions
von . importiere futures
von . importiere selector_events
von . importiere tasks
von . importiere transports
von .log importiere logger


__all__ = (
    'SelectorEventLoop',
    'EventLoop',
)


wenn sys.platform == 'win32':  # pragma: no cover
    raise ImportError('Signals are nicht really supported on Windows')


def _sighandler_noop(signum, frame):
    """Dummy signal handler."""
    pass


def waitstatus_to_exitcode(status):
    try:
        gib os.waitstatus_to_exitcode(status)
    except ValueError:
        # The child exited, but we don't understand its status.
        # This shouldn't happen, but wenn it does, let's just
        # gib that status; perhaps that helps debug it.
        gib status


klasse _UnixSelectorEventLoop(selector_events.BaseSelectorEventLoop):
    """Unix event loop.

    Adds signal handling und UNIX Domain Socket support to SelectorEventLoop.
    """

    def __init__(self, selector=Nichts):
        super().__init__(selector)
        self._signal_handlers = {}
        self._unix_server_sockets = {}
        wenn can_use_pidfd():
            self._watcher = _PidfdChildWatcher()
        sonst:
            self._watcher = _ThreadedChildWatcher()

    def close(self):
        super().close()
        wenn nicht sys.is_finalizing():
            fuer sig in list(self._signal_handlers):
                self.remove_signal_handler(sig)
        sonst:
            wenn self._signal_handlers:
                warnings.warn(f"Closing the loop {self!r} "
                              f"on interpreter shutdown "
                              f"stage, skipping signal handlers removal",
                              ResourceWarning,
                              source=self)
                self._signal_handlers.clear()

    def _process_self_data(self, data):
        fuer signum in data:
            wenn nicht signum:
                # ignore null bytes written by _write_to_self()
                weiter
            self._handle_signal(signum)

    def add_signal_handler(self, sig, callback, *args):
        """Add a handler fuer a signal.  UNIX only.

        Raise ValueError wenn the signal number is invalid oder uncatchable.
        Raise RuntimeError wenn there is a problem setting up the handler.
        """
        wenn (coroutines.iscoroutine(callback) oder
                coroutines._iscoroutinefunction(callback)):
            raise TypeError("coroutines cannot be used "
                            "with add_signal_handler()")
        self._check_signal(sig)
        self._check_closed()
        try:
            # set_wakeup_fd() raises ValueError wenn this is nicht the
            # main thread.  By calling it early we ensure that an
            # event loop running in another thread cannot add a signal
            # handler.
            signal.set_wakeup_fd(self._csock.fileno())
        except (ValueError, OSError) als exc:
            raise RuntimeError(str(exc))

        handle = events.Handle(callback, args, self, Nichts)
        self._signal_handlers[sig] = handle

        try:
            # Register a dummy signal handler to ask Python to write the signal
            # number in the wakeup file descriptor. _process_self_data() will
            # read signal numbers von this file descriptor to handle signals.
            signal.signal(sig, _sighandler_noop)

            # Set SA_RESTART to limit EINTR occurrences.
            signal.siginterrupt(sig, Falsch)
        except OSError als exc:
            del self._signal_handlers[sig]
            wenn nicht self._signal_handlers:
                try:
                    signal.set_wakeup_fd(-1)
                except (ValueError, OSError) als nexc:
                    logger.info('set_wakeup_fd(-1) failed: %s', nexc)

            wenn exc.errno == errno.EINVAL:
                raise RuntimeError(f'sig {sig} cannot be caught')
            sonst:
                raise

    def _handle_signal(self, sig):
        """Internal helper that is the actual signal handler."""
        handle = self._signal_handlers.get(sig)
        wenn handle is Nichts:
            gib  # Assume it's some race condition.
        wenn handle._cancelled:
            self.remove_signal_handler(sig)  # Remove it properly.
        sonst:
            self._add_callback_signalsafe(handle)

    def remove_signal_handler(self, sig):
        """Remove a handler fuer a signal.  UNIX only.

        Return Wahr wenn a signal handler was removed, Falsch wenn not.
        """
        self._check_signal(sig)
        try:
            del self._signal_handlers[sig]
        except KeyError:
            gib Falsch

        wenn sig == signal.SIGINT:
            handler = signal.default_int_handler
        sonst:
            handler = signal.SIG_DFL

        try:
            signal.signal(sig, handler)
        except OSError als exc:
            wenn exc.errno == errno.EINVAL:
                raise RuntimeError(f'sig {sig} cannot be caught')
            sonst:
                raise

        wenn nicht self._signal_handlers:
            try:
                signal.set_wakeup_fd(-1)
            except (ValueError, OSError) als exc:
                logger.info('set_wakeup_fd(-1) failed: %s', exc)

        gib Wahr

    def _check_signal(self, sig):
        """Internal helper to validate a signal.

        Raise ValueError wenn the signal number is invalid oder uncatchable.
        Raise RuntimeError wenn there is a problem setting up the handler.
        """
        wenn nicht isinstance(sig, int):
            raise TypeError(f'sig must be an int, nicht {sig!r}')

        wenn sig nicht in signal.valid_signals():
            raise ValueError(f'invalid signal number {sig}')

    def _make_read_pipe_transport(self, pipe, protocol, waiter=Nichts,
                                  extra=Nichts):
        gib _UnixReadPipeTransport(self, pipe, protocol, waiter, extra)

    def _make_write_pipe_transport(self, pipe, protocol, waiter=Nichts,
                                   extra=Nichts):
        gib _UnixWritePipeTransport(self, pipe, protocol, waiter, extra)

    async def _make_subprocess_transport(self, protocol, args, shell,
                                         stdin, stdout, stderr, bufsize,
                                         extra=Nichts, **kwargs):
        watcher = self._watcher
        waiter = self.create_future()
        transp = _UnixSubprocessTransport(self, protocol, args, shell,
                                        stdin, stdout, stderr, bufsize,
                                        waiter=waiter, extra=extra,
                                        **kwargs)
        watcher.add_child_handler(transp.get_pid(),
                                self._child_watcher_callback, transp)
        try:
            await waiter
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException:
            transp.close()
            await transp._wait()
            raise

        gib transp

    def _child_watcher_callback(self, pid, returncode, transp):
        self.call_soon_threadsafe(transp._process_exited, returncode)

    async def create_unix_connection(
            self, protocol_factory, path=Nichts, *,
            ssl=Nichts, sock=Nichts,
            server_hostname=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts):
        assert server_hostname is Nichts oder isinstance(server_hostname, str)
        wenn ssl:
            wenn server_hostname is Nichts:
                raise ValueError(
                    'you have to pass server_hostname when using ssl')
        sonst:
            wenn server_hostname is nicht Nichts:
                raise ValueError('server_hostname is only meaningful mit ssl')
            wenn ssl_handshake_timeout is nicht Nichts:
                raise ValueError(
                    'ssl_handshake_timeout is only meaningful mit ssl')
            wenn ssl_shutdown_timeout is nicht Nichts:
                raise ValueError(
                    'ssl_shutdown_timeout is only meaningful mit ssl')

        wenn path is nicht Nichts:
            wenn sock is nicht Nichts:
                raise ValueError(
                    'path und sock can nicht be specified at the same time')

            path = os.fspath(path)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
            try:
                sock.setblocking(Falsch)
                await self.sock_connect(sock, path)
            except:
                sock.close()
                raise

        sonst:
            wenn sock is Nichts:
                raise ValueError('no path und sock were specified')
            wenn (sock.family != socket.AF_UNIX oder
                    sock.type != socket.SOCK_STREAM):
                raise ValueError(
                    f'A UNIX Domain Stream Socket was expected, got {sock!r}')
            sock.setblocking(Falsch)

        transport, protocol = await self._create_connection_transport(
            sock, protocol_factory, ssl, server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        gib transport, protocol

    async def create_unix_server(
            self, protocol_factory, path=Nichts, *,
            sock=Nichts, backlog=100, ssl=Nichts,
            ssl_handshake_timeout=Nichts,
            ssl_shutdown_timeout=Nichts,
            start_serving=Wahr, cleanup_socket=Wahr):
        wenn isinstance(ssl, bool):
            raise TypeError('ssl argument must be an SSLContext oder Nichts')

        wenn ssl_handshake_timeout is nicht Nichts und nicht ssl:
            raise ValueError(
                'ssl_handshake_timeout is only meaningful mit ssl')

        wenn ssl_shutdown_timeout is nicht Nichts und nicht ssl:
            raise ValueError(
                'ssl_shutdown_timeout is only meaningful mit ssl')

        wenn path is nicht Nichts:
            wenn sock is nicht Nichts:
                raise ValueError(
                    'path und sock can nicht be specified at the same time')

            path = os.fspath(path)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            # Check fuer abstract socket. `str` und `bytes` paths are supported.
            wenn path[0] nicht in (0, '\x00'):
                try:
                    wenn stat.S_ISSOCK(os.stat(path).st_mode):
                        os.remove(path)
                except FileNotFoundError:
                    pass
                except OSError als err:
                    # Directory may have permissions only to create socket.
                    logger.error('Unable to check oder remove stale UNIX socket '
                                 '%r: %r', path, err)

            try:
                sock.bind(path)
            except OSError als exc:
                sock.close()
                wenn exc.errno == errno.EADDRINUSE:
                    # Let's improve the error message by adding
                    # mit what exact address it occurs.
                    msg = f'Address {path!r} is already in use'
                    raise OSError(errno.EADDRINUSE, msg) von Nichts
                sonst:
                    raise
            except:
                sock.close()
                raise
        sonst:
            wenn sock is Nichts:
                raise ValueError(
                    'path was nicht specified, und no sock specified')

            wenn (sock.family != socket.AF_UNIX oder
                    sock.type != socket.SOCK_STREAM):
                raise ValueError(
                    f'A UNIX Domain Stream Socket was expected, got {sock!r}')

        wenn cleanup_socket:
            path = sock.getsockname()
            # Check fuer abstract socket. `str` und `bytes` paths are supported.
            wenn path[0] nicht in (0, '\x00'):
                try:
                    self._unix_server_sockets[sock] = os.stat(path).st_ino
                except FileNotFoundError:
                    pass

        sock.setblocking(Falsch)
        server = base_events.Server(self, [sock], protocol_factory,
                                    ssl, backlog, ssl_handshake_timeout,
                                    ssl_shutdown_timeout)
        wenn start_serving:
            server._start_serving()
            # Skip one loop iteration so that all 'loop.add_reader'
            # go through.
            await tasks.sleep(0)

        gib server

    async def _sock_sendfile_native(self, sock, file, offset, count):
        try:
            os.sendfile
        except AttributeError:
            raise exceptions.SendfileNotAvailableError(
                "os.sendfile() is nicht available")
        try:
            fileno = file.fileno()
        except (AttributeError, io.UnsupportedOperation) als err:
            raise exceptions.SendfileNotAvailableError("not a regular file")
        try:
            fsize = os.fstat(fileno).st_size
        except OSError:
            raise exceptions.SendfileNotAvailableError("not a regular file")
        blocksize = count wenn count sonst fsize
        wenn nicht blocksize:
            gib 0  # empty file

        fut = self.create_future()
        self._sock_sendfile_native_impl(fut, Nichts, sock, fileno,
                                        offset, count, blocksize, 0)
        gib await fut

    def _sock_sendfile_native_impl(self, fut, registered_fd, sock, fileno,
                                   offset, count, blocksize, total_sent):
        fd = sock.fileno()
        wenn registered_fd is nicht Nichts:
            # Remove the callback early.  It should be rare that the
            # selector says the fd is ready but the call still returns
            # EAGAIN, und I am willing to take a hit in that case in
            # order to simplify the common case.
            self.remove_writer(registered_fd)
        wenn fut.cancelled():
            self._sock_sendfile_update_filepos(fileno, offset, total_sent)
            gib
        wenn count:
            blocksize = count - total_sent
            wenn blocksize <= 0:
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_result(total_sent)
                gib

        # On 32-bit architectures truncate to 1GiB to avoid OverflowError
        blocksize = min(blocksize, sys.maxsize//2 + 1)

        try:
            sent = os.sendfile(fd, fileno, offset, blocksize)
        except (BlockingIOError, InterruptedError):
            wenn registered_fd is Nichts:
                self._sock_add_cancellation_callback(fut, sock)
            self.add_writer(fd, self._sock_sendfile_native_impl, fut,
                            fd, sock, fileno,
                            offset, count, blocksize, total_sent)
        except OSError als exc:
            wenn (registered_fd is nicht Nichts und
                    exc.errno == errno.ENOTCONN und
                    type(exc) is nicht ConnectionError):
                # If we have an ENOTCONN und this isn't a first call to
                # sendfile(), i.e. the connection was closed in the middle
                # of the operation, normalize the error to ConnectionError
                # to make it consistent across all Posix systems.
                new_exc = ConnectionError(
                    "socket is nicht connected", errno.ENOTCONN)
                new_exc.__cause__ = exc
                exc = new_exc
            wenn total_sent == 0:
                # We can get here fuer different reasons, the main
                # one being 'file' is nicht a regular mmap(2)-like
                # file, in which case we'll fall back on using
                # plain send().
                err = exceptions.SendfileNotAvailableError(
                    "os.sendfile call failed")
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_exception(err)
            sonst:
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_exception(exc)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException als exc:
            self._sock_sendfile_update_filepos(fileno, offset, total_sent)
            fut.set_exception(exc)
        sonst:
            wenn sent == 0:
                # EOF
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_result(total_sent)
            sonst:
                offset += sent
                total_sent += sent
                wenn registered_fd is Nichts:
                    self._sock_add_cancellation_callback(fut, sock)
                self.add_writer(fd, self._sock_sendfile_native_impl, fut,
                                fd, sock, fileno,
                                offset, count, blocksize, total_sent)

    def _sock_sendfile_update_filepos(self, fileno, offset, total_sent):
        wenn total_sent > 0:
            os.lseek(fileno, offset, os.SEEK_SET)

    def _sock_add_cancellation_callback(self, fut, sock):
        def cb(fut):
            wenn fut.cancelled():
                fd = sock.fileno()
                wenn fd != -1:
                    self.remove_writer(fd)
        fut.add_done_callback(cb)

    def _stop_serving(self, sock):
        # Is this a unix socket that needs cleanup?
        wenn sock in self._unix_server_sockets:
            path = sock.getsockname()
        sonst:
            path = Nichts

        super()._stop_serving(sock)

        wenn path is nicht Nichts:
            prev_ino = self._unix_server_sockets[sock]
            del self._unix_server_sockets[sock]
            try:
                wenn os.stat(path).st_ino == prev_ino:
                    os.unlink(path)
            except FileNotFoundError:
                pass
            except OSError als err:
                logger.error('Unable to clean up listening UNIX socket '
                             '%r: %r', path, err)


klasse _UnixReadPipeTransport(transports.ReadTransport):

    max_size = 256 * 1024  # max bytes we read in one event loop iteration

    def __init__(self, loop, pipe, protocol, waiter=Nichts, extra=Nichts):
        super().__init__(extra)
        self._extra['pipe'] = pipe
        self._loop = loop
        self._pipe = pipe
        self._fileno = pipe.fileno()
        self._protocol = protocol
        self._closing = Falsch
        self._paused = Falsch

        mode = os.fstat(self._fileno).st_mode
        wenn nicht (stat.S_ISFIFO(mode) oder
                stat.S_ISSOCK(mode) oder
                stat.S_ISCHR(mode)):
            self._pipe = Nichts
            self._fileno = Nichts
            self._protocol = Nichts
            raise ValueError("Pipe transport is fuer pipes/sockets only.")

        os.set_blocking(self._fileno, Falsch)

        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._add_reader,
                             self._fileno, self._read_ready)
        wenn waiter is nicht Nichts:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, Nichts)

    def _add_reader(self, fd, callback):
        wenn nicht self.is_reading():
            gib
        self._loop._add_reader(fd, callback)

    def is_reading(self):
        gib nicht self._paused und nicht self._closing

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self._pipe is Nichts:
            info.append('closed')
        sowenn self._closing:
            info.append('closing')
        info.append(f'fd={self._fileno}')
        selector = getattr(self._loop, '_selector', Nichts)
        wenn self._pipe is nicht Nichts und selector is nicht Nichts:
            polling = selector_events._test_selector_event(
                selector, self._fileno, selectors.EVENT_READ)
            wenn polling:
                info.append('polling')
            sonst:
                info.append('idle')
        sowenn self._pipe is nicht Nichts:
            info.append('open')
        sonst:
            info.append('closed')
        gib '<{}>'.format(' '.join(info))

    def _read_ready(self):
        try:
            data = os.read(self._fileno, self.max_size)
        except (BlockingIOError, InterruptedError):
            pass
        except OSError als exc:
            self._fatal_error(exc, 'Fatal read error on pipe transport')
        sonst:
            wenn data:
                self._protocol.data_received(data)
            sonst:
                wenn self._loop.get_debug():
                    logger.info("%r was closed by peer", self)
                self._closing = Wahr
                self._loop._remove_reader(self._fileno)
                self._loop.call_soon(self._protocol.eof_received)
                self._loop.call_soon(self._call_connection_lost, Nichts)

    def pause_reading(self):
        wenn nicht self.is_reading():
            gib
        self._paused = Wahr
        self._loop._remove_reader(self._fileno)
        wenn self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self):
        wenn self._closing oder nicht self._paused:
            gib
        self._paused = Falsch
        self._loop._add_reader(self._fileno, self._read_ready)
        wenn self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        gib self._protocol

    def is_closing(self):
        gib self._closing

    def close(self):
        wenn nicht self._closing:
            self._close(Nichts)

    def __del__(self, _warn=warnings.warn):
        wenn self._pipe is nicht Nichts:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self._pipe.close()

    def _fatal_error(self, exc, message='Fatal error on pipe transport'):
        # should be called by exception handler only
        wenn (isinstance(exc, OSError) und exc.errno == errno.EIO):
            wenn self._loop.get_debug():
                logger.debug("%r: %s", self, message, exc_info=Wahr)
        sonst:
            self._loop.call_exception_handler({
                'message': message,
                'exception': exc,
                'transport': self,
                'protocol': self._protocol,
            })
        self._close(exc)

    def _close(self, exc):
        self._closing = Wahr
        self._loop._remove_reader(self._fileno)
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._pipe.close()
            self._pipe = Nichts
            self._protocol = Nichts
            self._loop = Nichts


klasse _UnixWritePipeTransport(transports._FlowControlMixin,
                              transports.WriteTransport):

    def __init__(self, loop, pipe, protocol, waiter=Nichts, extra=Nichts):
        super().__init__(extra, loop)
        self._extra['pipe'] = pipe
        self._pipe = pipe
        self._fileno = pipe.fileno()
        self._protocol = protocol
        self._buffer = bytearray()
        self._conn_lost = 0
        self._closing = Falsch  # Set when close() oder write_eof() called.

        mode = os.fstat(self._fileno).st_mode
        is_char = stat.S_ISCHR(mode)
        is_fifo = stat.S_ISFIFO(mode)
        is_socket = stat.S_ISSOCK(mode)
        wenn nicht (is_char oder is_fifo oder is_socket):
            self._pipe = Nichts
            self._fileno = Nichts
            self._protocol = Nichts
            raise ValueError("Pipe transport is only fuer "
                             "pipes, sockets und character devices")

        os.set_blocking(self._fileno, Falsch)
        self._loop.call_soon(self._protocol.connection_made, self)

        # On AIX, the reader trick (to be notified when the read end of the
        # socket is closed) only works fuer sockets. On other platforms it
        # works fuer pipes und sockets. (Exception: OS X 10.4?  Issue #19294.)
        wenn is_socket oder (is_fifo und nicht sys.platform.startswith("aix")):
            # only start reading when connection_made() has been called
            self._loop.call_soon(self._loop._add_reader,
                                 self._fileno, self._read_ready)

        wenn waiter is nicht Nichts:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, Nichts)

    def __repr__(self):
        info = [self.__class__.__name__]
        wenn self._pipe is Nichts:
            info.append('closed')
        sowenn self._closing:
            info.append('closing')
        info.append(f'fd={self._fileno}')
        selector = getattr(self._loop, '_selector', Nichts)
        wenn self._pipe is nicht Nichts und selector is nicht Nichts:
            polling = selector_events._test_selector_event(
                selector, self._fileno, selectors.EVENT_WRITE)
            wenn polling:
                info.append('polling')
            sonst:
                info.append('idle')

            bufsize = self.get_write_buffer_size()
            info.append(f'bufsize={bufsize}')
        sowenn self._pipe is nicht Nichts:
            info.append('open')
        sonst:
            info.append('closed')
        gib '<{}>'.format(' '.join(info))

    def get_write_buffer_size(self):
        gib len(self._buffer)

    def _read_ready(self):
        # Pipe was closed by peer.
        wenn self._loop.get_debug():
            logger.info("%r was closed by peer", self)
        wenn self._buffer:
            self._close(BrokenPipeError())
        sonst:
            self._close()

    def write(self, data):
        assert isinstance(data, (bytes, bytearray, memoryview)), repr(data)
        wenn isinstance(data, bytearray):
            data = memoryview(data)
        wenn nicht data:
            gib

        wenn self._conn_lost oder self._closing:
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('pipe closed by peer oder '
                               'os.write(pipe, data) raised exception.')
            self._conn_lost += 1
            gib

        wenn nicht self._buffer:
            # Attempt to send it right away first.
            try:
                n = os.write(self._fileno, data)
            except (BlockingIOError, InterruptedError):
                n = 0
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException als exc:
                self._conn_lost += 1
                self._fatal_error(exc, 'Fatal write error on pipe transport')
                gib
            wenn n == len(data):
                gib
            sowenn n > 0:
                data = memoryview(data)[n:]
            self._loop._add_writer(self._fileno, self._write_ready)

        self._buffer += data
        self._maybe_pause_protocol()

    def _write_ready(self):
        assert self._buffer, 'Data should nicht be empty'

        try:
            n = os.write(self._fileno, self._buffer)
        except (BlockingIOError, InterruptedError):
            pass
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException als exc:
            self._buffer.clear()
            self._conn_lost += 1
            # Remove writer here, _fatal_error() doesn't it
            # because _buffer is empty.
            self._loop._remove_writer(self._fileno)
            self._fatal_error(exc, 'Fatal write error on pipe transport')
        sonst:
            wenn n == len(self._buffer):
                self._buffer.clear()
                self._loop._remove_writer(self._fileno)
                self._maybe_resume_protocol()  # May append to buffer.
                wenn self._closing:
                    self._loop._remove_reader(self._fileno)
                    self._call_connection_lost(Nichts)
                gib
            sowenn n > 0:
                del self._buffer[:n]

    def can_write_eof(self):
        gib Wahr

    def write_eof(self):
        wenn self._closing:
            gib
        assert self._pipe
        self._closing = Wahr
        wenn nicht self._buffer:
            self._loop._remove_reader(self._fileno)
            self._loop.call_soon(self._call_connection_lost, Nichts)

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        gib self._protocol

    def is_closing(self):
        gib self._closing

    def close(self):
        wenn self._pipe is nicht Nichts und nicht self._closing:
            # write_eof is all what we needed to close the write pipe
            self.write_eof()

    def __del__(self, _warn=warnings.warn):
        wenn self._pipe is nicht Nichts:
            _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
            self._pipe.close()

    def abort(self):
        self._close(Nichts)

    def _fatal_error(self, exc, message='Fatal error on pipe transport'):
        # should be called by exception handler only
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
        self._close(exc)

    def _close(self, exc=Nichts):
        self._closing = Wahr
        wenn self._buffer:
            self._loop._remove_writer(self._fileno)
        self._buffer.clear()
        self._loop._remove_reader(self._fileno)
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._pipe.close()
            self._pipe = Nichts
            self._protocol = Nichts
            self._loop = Nichts


klasse _UnixSubprocessTransport(base_subprocess.BaseSubprocessTransport):

    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        stdin_w = Nichts
        wenn stdin == subprocess.PIPE und sys.platform.startswith('aix'):
            # Use a socket pair fuer stdin on AIX, since it does not
            # support selecting read events on the write end of a
            # socket (which we use in order to detect closing of the
            # other end).
            stdin, stdin_w = socket.socketpair()
        try:
            self._proc = subprocess.Popen(
                args, shell=shell, stdin=stdin, stdout=stdout, stderr=stderr,
                universal_newlines=Falsch, bufsize=bufsize, **kwargs)
            wenn stdin_w is nicht Nichts:
                stdin.close()
                self._proc.stdin = open(stdin_w.detach(), 'wb', buffering=bufsize)
                stdin_w = Nichts
        finally:
            wenn stdin_w is nicht Nichts:
                stdin.close()
                stdin_w.close()


klasse _PidfdChildWatcher:
    """Child watcher implementation using Linux's pid file descriptors.

    This child watcher polls process file descriptors (pidfds) to await child
    process termination. In some respects, PidfdChildWatcher is a "Goldilocks"
    child watcher implementation. It doesn't require signals oder threads, doesn't
    interfere mit any processes launched outside the event loop, und scales
    linearly mit the number of subprocesses launched by the event loop. The
    main disadvantage is that pidfds are specific to Linux, und only work on
    recent (5.3+) kernels.
    """

    def add_child_handler(self, pid, callback, *args):
        loop = events.get_running_loop()
        pidfd = os.pidfd_open(pid)
        loop._add_reader(pidfd, self._do_wait, pid, pidfd, callback, args)

    def _do_wait(self, pid, pidfd, callback, args):
        loop = events.get_running_loop()
        loop._remove_reader(pidfd)
        try:
            _, status = os.waitpid(pid, 0)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen wenn waitpid() is called elsewhere).
            returncode = 255
            logger.warning(
                "child process pid %d exit status already read: "
                " will report returncode 255",
                pid)
        sonst:
            returncode = waitstatus_to_exitcode(status)

        os.close(pidfd)
        callback(pid, returncode, *args)

klasse _ThreadedChildWatcher:
    """Threaded child watcher implementation.

    The watcher uses a thread per process
    fuer waiting fuer the process finish.

    It doesn't require subscription on POSIX signal
    but a thread creation is nicht free.

    The watcher has O(1) complexity, its performance doesn't depend
    on amount of spawn processes.
    """

    def __init__(self):
        self._pid_counter = itertools.count(0)
        self._threads = {}

    def __del__(self, _warn=warnings.warn):
        threads = [thread fuer thread in list(self._threads.values())
                   wenn thread.is_alive()]
        wenn threads:
            _warn(f"{self.__class__} has registered but nicht finished child processes",
                  ResourceWarning,
                  source=self)

    def add_child_handler(self, pid, callback, *args):
        loop = events.get_running_loop()
        thread = threading.Thread(target=self._do_waitpid,
                                  name=f"asyncio-waitpid-{next(self._pid_counter)}",
                                  args=(loop, pid, callback, args),
                                  daemon=Wahr)
        self._threads[pid] = thread
        thread.start()

    def _do_waitpid(self, loop, expected_pid, callback, args):
        assert expected_pid > 0

        try:
            pid, status = os.waitpid(expected_pid, 0)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen wenn waitpid() is called elsewhere).
            pid = expected_pid
            returncode = 255
            logger.warning(
                "Unknown child process pid %d, will report returncode 255",
                pid)
        sonst:
            returncode = waitstatus_to_exitcode(status)
            wenn loop.get_debug():
                logger.debug('process %s exited mit returncode %s',
                             expected_pid, returncode)

        wenn loop.is_closed():
            logger.warning("Loop %r that handles pid %r is closed", loop, pid)
        sonst:
            loop.call_soon_threadsafe(callback, pid, returncode, *args)

        self._threads.pop(expected_pid)

def can_use_pidfd():
    wenn nicht hasattr(os, 'pidfd_open'):
        gib Falsch
    try:
        pid = os.getpid()
        os.close(os.pidfd_open(pid, 0))
    except OSError:
        # blocked by security policy like SECCOMP
        gib Falsch
    gib Wahr


klasse _UnixDefaultEventLoopPolicy(events._BaseDefaultEventLoopPolicy):
    """UNIX event loop policy"""
    _loop_factory = _UnixSelectorEventLoop


SelectorEventLoop = _UnixSelectorEventLoop
_DefaultEventLoopPolicy = _UnixDefaultEventLoopPolicy
EventLoop = SelectorEventLoop
