__all__ = (
    'StreamReader', 'StreamWriter', 'StreamReaderProtocol',
    'open_connection', 'start_server')

importiere collections
importiere socket
importiere sys
importiere warnings
importiere weakref

wenn hasattr(socket, 'AF_UNIX'):
    __all__ += ('open_unix_connection', 'start_unix_server')

von . importiere coroutines
von . importiere events
von . importiere exceptions
von . importiere format_helpers
von . importiere protocols
von .log importiere logger
von .tasks importiere sleep


_DEFAULT_LIMIT = 2 ** 16  # 64 KiB


async def open_connection(host=Nichts, port=Nichts, *,
                          limit=_DEFAULT_LIMIT, **kwds):
    """A wrapper fuer create_connection() returning a (reader, writer) pair.

    The reader returned is a StreamReader instance; the writer is a
    StreamWriter instance.

    The arguments are all the usual arguments to create_connection()
    ausser protocol_factory; most common are positional host und port,
    mit various optional keyword arguments following.

    Additional optional keyword arguments are loop (to set the event loop
    instance to use) und limit (to set the buffer limit passed to the
    StreamReader).

    (If you want to customize the StreamReader and/or
    StreamReaderProtocol classes, just copy the code -- there's
    really nothing special here ausser some convenience.)
    """
    loop = events.get_running_loop()
    reader = StreamReader(limit=limit, loop=loop)
    protocol = StreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(
        lambda: protocol, host, port, **kwds)
    writer = StreamWriter(transport, protocol, reader, loop)
    gib reader, writer


async def start_server(client_connected_cb, host=Nichts, port=Nichts, *,
                       limit=_DEFAULT_LIMIT, **kwds):
    """Start a socket server, call back fuer each client connected.

    The first parameter, `client_connected_cb`, takes two parameters:
    client_reader, client_writer.  client_reader is a StreamReader
    object, waehrend client_writer is a StreamWriter object.  This
    parameter can either be a plain callback function oder a coroutine;
    wenn it is a coroutine, it will be automatically converted into a
    Task.

    The rest of the arguments are all the usual arguments to
    loop.create_server() ausser protocol_factory; most common are
    positional host und port, mit various optional keyword arguments
    following.  The gib value is the same als loop.create_server().

    Additional optional keyword argument is limit (to set the buffer
    limit passed to the StreamReader).

    The gib value is the same als loop.create_server(), i.e. a
    Server object which can be used to stop the service.
    """
    loop = events.get_running_loop()

    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = StreamReaderProtocol(reader, client_connected_cb,
                                        loop=loop)
        gib protocol

    gib await loop.create_server(factory, host, port, **kwds)


wenn hasattr(socket, 'AF_UNIX'):
    # UNIX Domain Sockets are supported on this platform

    async def open_unix_connection(path=Nichts, *,
                                   limit=_DEFAULT_LIMIT, **kwds):
        """Similar to `open_connection` but works mit UNIX Domain Sockets."""
        loop = events.get_running_loop()

        reader = StreamReader(limit=limit, loop=loop)
        protocol = StreamReaderProtocol(reader, loop=loop)
        transport, _ = await loop.create_unix_connection(
            lambda: protocol, path, **kwds)
        writer = StreamWriter(transport, protocol, reader, loop)
        gib reader, writer

    async def start_unix_server(client_connected_cb, path=Nichts, *,
                                limit=_DEFAULT_LIMIT, **kwds):
        """Similar to `start_server` but works mit UNIX Domain Sockets."""
        loop = events.get_running_loop()

        def factory():
            reader = StreamReader(limit=limit, loop=loop)
            protocol = StreamReaderProtocol(reader, client_connected_cb,
                                            loop=loop)
            gib protocol

        gib await loop.create_unix_server(factory, path, **kwds)


klasse FlowControlMixin(protocols.Protocol):
    """Reusable flow control logic fuer StreamWriter.drain().

    This implements the protocol methods pause_writing(),
    resume_writing() und connection_lost().  If the subclass overrides
    these it must call the super methods.

    StreamWriter.drain() must wait fuer _drain_helper() coroutine.
    """

    def __init__(self, loop=Nichts):
        wenn loop is Nichts:
            self._loop = events.get_event_loop()
        sonst:
            self._loop = loop
        self._paused = Falsch
        self._drain_waiters = collections.deque()
        self._connection_lost = Falsch

    def pause_writing(self):
        assert nicht self._paused
        self._paused = Wahr
        wenn self._loop.get_debug():
            logger.debug("%r pauses writing", self)

    def resume_writing(self):
        assert self._paused
        self._paused = Falsch
        wenn self._loop.get_debug():
            logger.debug("%r resumes writing", self)

        fuer waiter in self._drain_waiters:
            wenn nicht waiter.done():
                waiter.set_result(Nichts)

    def connection_lost(self, exc):
        self._connection_lost = Wahr
        # Wake up the writer(s) wenn currently paused.
        wenn nicht self._paused:
            gib

        fuer waiter in self._drain_waiters:
            wenn nicht waiter.done():
                wenn exc is Nichts:
                    waiter.set_result(Nichts)
                sonst:
                    waiter.set_exception(exc)

    async def _drain_helper(self):
        wenn self._connection_lost:
            wirf ConnectionResetError('Connection lost')
        wenn nicht self._paused:
            gib
        waiter = self._loop.create_future()
        self._drain_waiters.append(waiter)
        versuch:
            await waiter
        schliesslich:
            self._drain_waiters.remove(waiter)

    def _get_close_waiter(self, stream):
        wirf NotImplementedError


klasse StreamReaderProtocol(FlowControlMixin, protocols.Protocol):
    """Helper klasse to adapt between Protocol und StreamReader.

    (This is a helper klasse instead of making StreamReader itself a
    Protocol subclass, because the StreamReader has other potential
    uses, und to prevent the user of the StreamReader to accidentally
    call inappropriate methods of the protocol.)
    """

    _source_traceback = Nichts

    def __init__(self, stream_reader, client_connected_cb=Nichts, loop=Nichts):
        super().__init__(loop=loop)
        wenn stream_reader is nicht Nichts:
            self._stream_reader_wr = weakref.ref(stream_reader)
            self._source_traceback = stream_reader._source_traceback
        sonst:
            self._stream_reader_wr = Nichts
        wenn client_connected_cb is nicht Nichts:
            # This is a stream created by the `create_server()` function.
            # Keep a strong reference to the reader until a connection
            # is established.
            self._strong_reader = stream_reader
        self._reject_connection = Falsch
        self._task = Nichts
        self._transport = Nichts
        self._client_connected_cb = client_connected_cb
        self._over_ssl = Falsch
        self._closed = self._loop.create_future()

    @property
    def _stream_reader(self):
        wenn self._stream_reader_wr is Nichts:
            gib Nichts
        gib self._stream_reader_wr()

    def _replace_transport(self, transport):
        loop = self._loop
        self._transport = transport
        self._over_ssl = transport.get_extra_info('sslcontext') is nicht Nichts

    def connection_made(self, transport):
        wenn self._reject_connection:
            context = {
                'message': ('An open stream was garbage collected prior to '
                            'establishing network connection; '
                            'call "stream.close()" explicitly.')
            }
            wenn self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
            transport.abort()
            gib
        self._transport = transport
        reader = self._stream_reader
        wenn reader is nicht Nichts:
            reader.set_transport(transport)
        self._over_ssl = transport.get_extra_info('sslcontext') is nicht Nichts
        wenn self._client_connected_cb is nicht Nichts:
            writer = StreamWriter(transport, self, reader, self._loop)
            res = self._client_connected_cb(reader, writer)
            wenn coroutines.iscoroutine(res):
                def callback(task):
                    wenn task.cancelled():
                        transport.close()
                        gib
                    exc = task.exception()
                    wenn exc is nicht Nichts:
                        self._loop.call_exception_handler({
                            'message': 'Unhandled exception in client_connected_cb',
                            'exception': exc,
                            'transport': transport,
                        })
                        transport.close()

                self._task = self._loop.create_task(res)
                self._task.add_done_callback(callback)

            self._strong_reader = Nichts

    def connection_lost(self, exc):
        reader = self._stream_reader
        wenn reader is nicht Nichts:
            wenn exc is Nichts:
                reader.feed_eof()
            sonst:
                reader.set_exception(exc)
        wenn nicht self._closed.done():
            wenn exc is Nichts:
                self._closed.set_result(Nichts)
            sonst:
                self._closed.set_exception(exc)
        super().connection_lost(exc)
        self._stream_reader_wr = Nichts
        self._task = Nichts
        self._transport = Nichts

    def data_received(self, data):
        reader = self._stream_reader
        wenn reader is nicht Nichts:
            reader.feed_data(data)

    def eof_received(self):
        reader = self._stream_reader
        wenn reader is nicht Nichts:
            reader.feed_eof()
        wenn self._over_ssl:
            # Prevent a warning in SSLProtocol.eof_received:
            # "returning true von eof_received()
            # has no effect when using ssl"
            gib Falsch
        gib Wahr

    def _get_close_waiter(self, stream):
        gib self._closed

    def __del__(self):
        # Prevent reports about unhandled exceptions.
        # Better than self._closed._log_traceback = Falsch hack
        versuch:
            closed = self._closed
        ausser AttributeError:
            pass  # failed constructor
        sonst:
            wenn closed.done() und nicht closed.cancelled():
                closed.exception()


klasse StreamWriter:
    """Wraps a Transport.

    This exposes write(), writelines(), [can_]write_eof(),
    get_extra_info() und close().  It adds drain() which returns an
    optional Future on which you can wait fuer flow control.  It also
    adds a transport property which references the Transport
    directly.
    """

    def __init__(self, transport, protocol, reader, loop):
        self._transport = transport
        self._protocol = protocol
        # drain() expects that the reader has an exception() method
        assert reader is Nichts oder isinstance(reader, StreamReader)
        self._reader = reader
        self._loop = loop
        self._complete_fut = self._loop.create_future()
        self._complete_fut.set_result(Nichts)

    def __repr__(self):
        info = [self.__class__.__name__, f'transport={self._transport!r}']
        wenn self._reader is nicht Nichts:
            info.append(f'reader={self._reader!r}')
        gib '<{}>'.format(' '.join(info))

    @property
    def transport(self):
        gib self._transport

    def write(self, data):
        self._transport.write(data)

    def writelines(self, data):
        self._transport.writelines(data)

    def write_eof(self):
        gib self._transport.write_eof()

    def can_write_eof(self):
        gib self._transport.can_write_eof()

    def close(self):
        gib self._transport.close()

    def is_closing(self):
        gib self._transport.is_closing()

    async def wait_closed(self):
        await self._protocol._get_close_waiter(self)

    def get_extra_info(self, name, default=Nichts):
        gib self._transport.get_extra_info(name, default)

    async def drain(self):
        """Flush the write buffer.

        The intended use is to write

          w.write(data)
          await w.drain()
        """
        wenn self._reader is nicht Nichts:
            exc = self._reader.exception()
            wenn exc is nicht Nichts:
                wirf exc
        wenn self._transport.is_closing():
            # Wait fuer protocol.connection_lost() call
            # Raise connection closing error wenn any,
            # ConnectionResetError otherwise
            # Yield to the event loop so connection_lost() may be
            # called.  Without this, _drain_helper() would gib
            # immediately, und code that calls
            #     write(...); await drain()
            # in a loop would never call connection_lost(), so it
            # would nicht see an error when the socket is closed.
            await sleep(0)
        await self._protocol._drain_helper()

    async def start_tls(self, sslcontext, *,
                        server_hostname=Nichts,
                        ssl_handshake_timeout=Nichts,
                        ssl_shutdown_timeout=Nichts):
        """Upgrade an existing stream-based connection to TLS."""
        server_side = self._protocol._client_connected_cb is nicht Nichts
        protocol = self._protocol
        await self.drain()
        new_transport = await self._loop.start_tls(  # type: ignore
            self._transport, protocol, sslcontext,
            server_side=server_side, server_hostname=server_hostname,
            ssl_handshake_timeout=ssl_handshake_timeout,
            ssl_shutdown_timeout=ssl_shutdown_timeout)
        self._transport = new_transport
        protocol._replace_transport(new_transport)

    def __del__(self, warnings=warnings):
        wenn nicht self._transport.is_closing():
            wenn self._loop.is_closed():
                warnings.warn("loop is closed", ResourceWarning)
            sonst:
                self.close()
                warnings.warn(f"unclosed {self!r}", ResourceWarning)

klasse StreamReader:

    _source_traceback = Nichts

    def __init__(self, limit=_DEFAULT_LIMIT, loop=Nichts):
        # The line length limit is  a security feature;
        # it also doubles als half the buffer limit.

        wenn limit <= 0:
            wirf ValueError('Limit cannot be <= 0')

        self._limit = limit
        wenn loop is Nichts:
            self._loop = events.get_event_loop()
        sonst:
            self._loop = loop
        self._buffer = bytearray()
        self._eof = Falsch    # Whether we're done.
        self._waiter = Nichts  # A future used by _wait_for_data()
        self._exception = Nichts
        self._transport = Nichts
        self._paused = Falsch
        wenn self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(
                sys._getframe(1))

    def __repr__(self):
        info = ['StreamReader']
        wenn self._buffer:
            info.append(f'{len(self._buffer)} bytes')
        wenn self._eof:
            info.append('eof')
        wenn self._limit != _DEFAULT_LIMIT:
            info.append(f'limit={self._limit}')
        wenn self._waiter:
            info.append(f'waiter={self._waiter!r}')
        wenn self._exception:
            info.append(f'exception={self._exception!r}')
        wenn self._transport:
            info.append(f'transport={self._transport!r}')
        wenn self._paused:
            info.append('paused')
        gib '<{}>'.format(' '.join(info))

    def exception(self):
        gib self._exception

    def set_exception(self, exc):
        self._exception = exc

        waiter = self._waiter
        wenn waiter is nicht Nichts:
            self._waiter = Nichts
            wenn nicht waiter.cancelled():
                waiter.set_exception(exc)

    def _wakeup_waiter(self):
        """Wakeup read*() functions waiting fuer data oder EOF."""
        waiter = self._waiter
        wenn waiter is nicht Nichts:
            self._waiter = Nichts
            wenn nicht waiter.cancelled():
                waiter.set_result(Nichts)

    def set_transport(self, transport):
        assert self._transport is Nichts, 'Transport already set'
        self._transport = transport

    def _maybe_resume_transport(self):
        wenn self._paused und len(self._buffer) <= self._limit:
            self._paused = Falsch
            self._transport.resume_reading()

    def feed_eof(self):
        self._eof = Wahr
        self._wakeup_waiter()

    def at_eof(self):
        """Return Wahr wenn the buffer is empty und 'feed_eof' was called."""
        gib self._eof und nicht self._buffer

    def feed_data(self, data):
        assert nicht self._eof, 'feed_data after feed_eof'

        wenn nicht data:
            gib

        self._buffer.extend(data)
        self._wakeup_waiter()

        wenn (self._transport is nicht Nichts und
                nicht self._paused und
                len(self._buffer) > 2 * self._limit):
            versuch:
                self._transport.pause_reading()
            ausser NotImplementedError:
                # The transport can't be paused.
                # We'll just have to buffer all data.
                # Forget the transport so we don't keep trying.
                self._transport = Nichts
            sonst:
                self._paused = Wahr

    async def _wait_for_data(self, func_name):
        """Wait until feed_data() oder feed_eof() is called.

        If stream was paused, automatically resume it.
        """
        # StreamReader uses a future to link the protocol feed_data() method
        # to a read coroutine. Running two read coroutines at the same time
        # would have an unexpected behaviour. It would nicht possible to know
        # which coroutine would get the next data.
        wenn self._waiter is nicht Nichts:
            wirf RuntimeError(
                f'{func_name}() called waehrend another coroutine is '
                f'already waiting fuer incoming data')

        assert nicht self._eof, '_wait_for_data after EOF'

        # Waiting fuer data waehrend paused will make deadlock, so prevent it.
        # This is essential fuer readexactly(n) fuer case when n > self._limit.
        wenn self._paused:
            self._paused = Falsch
            self._transport.resume_reading()

        self._waiter = self._loop.create_future()
        versuch:
            await self._waiter
        schliesslich:
            self._waiter = Nichts

    async def readline(self):
        """Read chunk of data von the stream until newline (b'\n') is found.

        On success, gib chunk that ends mit newline. If only partial
        line can be read due to EOF, gib incomplete line without
        terminating newline. When EOF was reached waehrend no bytes read, empty
        bytes object is returned.

        If limit is reached, ValueError will be raised. In that case, if
        newline was found, complete line including newline will be removed
        von internal buffer. Else, internal buffer will be cleared. Limit is
        compared against part of the line without newline.

        If stream was paused, this function will automatically resume it if
        needed.
        """
        sep = b'\n'
        seplen = len(sep)
        versuch:
            line = await self.readuntil(sep)
        ausser exceptions.IncompleteReadError als e:
            gib e.partial
        ausser exceptions.LimitOverrunError als e:
            wenn self._buffer.startswith(sep, e.consumed):
                del self._buffer[:e.consumed + seplen]
            sonst:
                self._buffer.clear()
            self._maybe_resume_transport()
            wirf ValueError(e.args[0])
        gib line

    async def readuntil(self, separator=b'\n'):
        """Read data von the stream until ``separator`` is found.

        On success, the data und separator will be removed von the
        internal buffer (consumed). Returned data will include the
        separator at the end.

        Configured stream limit is used to check result. Limit sets the
        maximal length of data that can be returned, nicht counting the
        separator.

        If an EOF occurs und the complete separator is still nicht found,
        an IncompleteReadError exception will be raised, und the internal
        buffer will be reset.  The IncompleteReadError.partial attribute
        may contain the separator partially.

        If the data cannot be read because of over limit, a
        LimitOverrunError exception  will be raised, und the data
        will be left in the internal buffer, so it can be read again.

        The ``separator`` may also be a tuple of separators. In this
        case the gib value will be the shortest possible that has any
        separator als the suffix. For the purposes of LimitOverrunError,
        the shortest possible separator is considered to be the one that
        matched.
        """
        wenn isinstance(separator, tuple):
            # Makes sure shortest matches wins
            separator = sorted(separator, key=len)
        sonst:
            separator = [separator]
        wenn nicht separator:
            wirf ValueError('Separator should contain at least one element')
        min_seplen = len(separator[0])
        max_seplen = len(separator[-1])
        wenn min_seplen == 0:
            wirf ValueError('Separator should be at least one-byte string')

        wenn self._exception is nicht Nichts:
            wirf self._exception

        # Consume whole buffer ausser last bytes, which length is
        # one less than max_seplen. Let's check corner cases with
        # separator[-1]='SEPARATOR':
        # * we have received almost complete separator (without last
        #   byte). i.e buffer='some textSEPARATO'. In this case we
        #   can safely consume max_seplen - 1 bytes.
        # * last byte of buffer is first byte of separator, i.e.
        #   buffer='abcdefghijklmnopqrS'. We may safely consume
        #   everything ausser that last byte, but this require to
        #   analyze bytes of buffer that match partial separator.
        #   This is slow and/or require FSM. For this case our
        #   implementation is nicht optimal, since require rescanning
        #   of data that is known to nicht belong to separator. In
        #   real world, separator will nicht be so long to notice
        #   performance problems. Even when reading MIME-encoded
        #   messages :)

        # `offset` is the number of bytes von the beginning of the buffer
        # where there is no occurrence of any `separator`.
        offset = 0

        # Loop until we find a `separator` in the buffer, exceed the buffer size,
        # oder an EOF has happened.
        waehrend Wahr:
            buflen = len(self._buffer)

            # Check wenn we now have enough data in the buffer fuer shortest
            # separator to fit.
            wenn buflen - offset >= min_seplen:
                match_start = Nichts
                match_end = Nichts
                fuer sep in separator:
                    isep = self._buffer.find(sep, offset)

                    wenn isep != -1:
                        # `separator` is in the buffer. `match_start` und
                        # `match_end` will be used later to retrieve the
                        # data.
                        end = isep + len(sep)
                        wenn match_end is Nichts oder end < match_end:
                            match_end = end
                            match_start = isep
                wenn match_end is nicht Nichts:
                    breche

                # see upper comment fuer explanation.
                offset = max(0, buflen + 1 - max_seplen)
                wenn offset > self._limit:
                    wirf exceptions.LimitOverrunError(
                        'Separator is nicht found, und chunk exceed the limit',
                        offset)

            # Complete message (with full separator) may be present in buffer
            # even when EOF flag is set. This may happen when the last chunk
            # adds data which makes separator be found. That's why we check for
            # EOF *after* inspecting the buffer.
            wenn self._eof:
                chunk = bytes(self._buffer)
                self._buffer.clear()
                wirf exceptions.IncompleteReadError(chunk, Nichts)

            # _wait_for_data() will resume reading wenn stream was paused.
            await self._wait_for_data('readuntil')

        wenn match_start > self._limit:
            wirf exceptions.LimitOverrunError(
                'Separator is found, but chunk is longer than limit', match_start)

        chunk = self._buffer[:match_end]
        del self._buffer[:match_end]
        self._maybe_resume_transport()
        gib bytes(chunk)

    async def read(self, n=-1):
        """Read up to `n` bytes von the stream.

        If `n` is nicht provided oder set to -1,
        read until EOF, then gib all read bytes.
        If EOF was received und the internal buffer is empty,
        gib an empty bytes object.

        If `n` is 0, gib an empty bytes object immediately.

        If `n` is positive, gib at most `n` available bytes
        als soon als at least 1 byte is available in the internal buffer.
        If EOF is received before any byte is read, gib an empty
        bytes object.

        Returned value is nicht limited mit limit, configured at stream
        creation.

        If stream was paused, this function will automatically resume it if
        needed.
        """

        wenn self._exception is nicht Nichts:
            wirf self._exception

        wenn n == 0:
            gib b''

        wenn n < 0:
            # This used to just loop creating a new waiter hoping to
            # collect everything in self._buffer, but that would
            # deadlock wenn the subprocess sends more than self.limit
            # bytes.  So just call self.read(self._limit) until EOF.
            blocks = []
            waehrend Wahr:
                block = await self.read(self._limit)
                wenn nicht block:
                    breche
                blocks.append(block)
            gib b''.join(blocks)

        wenn nicht self._buffer und nicht self._eof:
            await self._wait_for_data('read')

        # This will work right even wenn buffer is less than n bytes
        data = bytes(memoryview(self._buffer)[:n])
        del self._buffer[:n]

        self._maybe_resume_transport()
        gib data

    async def readexactly(self, n):
        """Read exactly `n` bytes.

        Raise an IncompleteReadError wenn EOF is reached before `n` bytes can be
        read. The IncompleteReadError.partial attribute of the exception will
        contain the partial read bytes.

        wenn n is zero, gib empty bytes object.

        Returned value is nicht limited mit limit, configured at stream
        creation.

        If stream was paused, this function will automatically resume it if
        needed.
        """
        wenn n < 0:
            wirf ValueError('readexactly size can nicht be less than zero')

        wenn self._exception is nicht Nichts:
            wirf self._exception

        wenn n == 0:
            gib b''

        waehrend len(self._buffer) < n:
            wenn self._eof:
                incomplete = bytes(self._buffer)
                self._buffer.clear()
                wirf exceptions.IncompleteReadError(incomplete, n)

            await self._wait_for_data('readexactly')

        wenn len(self._buffer) == n:
            data = bytes(self._buffer)
            self._buffer.clear()
        sonst:
            data = bytes(memoryview(self._buffer)[:n])
            del self._buffer[:n]
        self._maybe_resume_transport()
        gib data

    def __aiter__(self):
        gib self

    async def __anext__(self):
        val = await self.readline()
        wenn val == b'':
            wirf StopAsyncIteration
        gib val
