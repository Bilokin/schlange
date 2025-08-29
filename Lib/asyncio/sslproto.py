# Contains code von https://github.com/MagicStack/uvloop/tree/v0.16.0
# SPDX-License-Identifier: PSF-2.0 AND (MIT OR Apache-2.0)
# SPDX-FileCopyrightText: Copyright (c) 2015-2021 MagicStack Inc.  http://magic.io

importiere collections
importiere enum
importiere warnings
try:
    importiere ssl
except ImportError:  # pragma: no cover
    ssl = Nichts

von . importiere constants
von . importiere exceptions
von . importiere protocols
von . importiere transports
von .log importiere logger

wenn ssl is nicht Nichts:
    SSLAgainErrors = (ssl.SSLWantReadError, ssl.SSLSyscallError)


klasse SSLProtocolState(enum.Enum):
    UNWRAPPED = "UNWRAPPED"
    DO_HANDSHAKE = "DO_HANDSHAKE"
    WRAPPED = "WRAPPED"
    FLUSHING = "FLUSHING"
    SHUTDOWN = "SHUTDOWN"


klasse AppProtocolState(enum.Enum):
    # This tracks the state of app protocol (https://git.io/fj59P):
    #
    #     INIT -cm-> CON_MADE [-dr*->] [-er-> EOF?] -cl-> CON_LOST
    #
    # * cm: connection_made()
    # * dr: data_received()
    # * er: eof_received()
    # * cl: connection_lost()

    STATE_INIT = "STATE_INIT"
    STATE_CON_MADE = "STATE_CON_MADE"
    STATE_EOF = "STATE_EOF"
    STATE_CON_LOST = "STATE_CON_LOST"


def _create_transport_context(server_side, server_hostname):
    wenn server_side:
        raise ValueError('Server side SSL needs a valid SSLContext')

    # Client side may pass ssl=Wahr to use a default
    # context; in that case the sslcontext passed is Nichts.
    # The default is secure fuer client connections.
    # Python 3.4+: use up-to-date strong settings.
    sslcontext = ssl.create_default_context()
    wenn nicht server_hostname:
        sslcontext.check_hostname = Falsch
    return sslcontext


def add_flowcontrol_defaults(high, low, kb):
    wenn high is Nichts:
        wenn low is Nichts:
            hi = kb * 1024
        sonst:
            lo = low
            hi = 4 * lo
    sonst:
        hi = high
    wenn low is Nichts:
        lo = hi // 4
    sonst:
        lo = low

    wenn nicht hi >= lo >= 0:
        raise ValueError('high (%r) must be >= low (%r) must be >= 0' %
                         (hi, lo))

    return hi, lo


klasse _SSLProtocolTransport(transports._FlowControlMixin,
                            transports.Transport):

    _start_tls_compatible = Wahr
    _sendfile_compatible = constants._SendfileMode.FALLBACK

    def __init__(self, loop, ssl_protocol):
        self._loop = loop
        self._ssl_protocol = ssl_protocol
        self._closed = Falsch

    def get_extra_info(self, name, default=Nichts):
        """Get optional transport information."""
        return self._ssl_protocol._get_extra_info(name, default)

    def set_protocol(self, protocol):
        self._ssl_protocol._set_app_protocol(protocol)

    def get_protocol(self):
        return self._ssl_protocol._app_protocol

    def is_closing(self):
        return self._closed oder self._ssl_protocol._is_transport_closing()

    def close(self):
        """Close the transport.

        Buffered data will be flushed asynchronously.  No more data
        will be received.  After all buffered data is flushed, the
        protocol's connection_lost() method will (eventually) called
        mit Nichts als its argument.
        """
        wenn nicht self._closed:
            self._closed = Wahr
            self._ssl_protocol._start_shutdown()
        sonst:
            self._ssl_protocol = Nichts

    def __del__(self, _warnings=warnings):
        wenn nicht self._closed:
            self._closed = Wahr
            _warnings.warn(
                "unclosed transport <asyncio._SSLProtocolTransport "
                "object>", ResourceWarning)

    def is_reading(self):
        return nicht self._ssl_protocol._app_reading_paused

    def pause_reading(self):
        """Pause the receiving end.

        No data will be passed to the protocol's data_received()
        method until resume_reading() is called.
        """
        self._ssl_protocol._pause_reading()

    def resume_reading(self):
        """Resume the receiving end.

        Data received will once again be passed to the protocol's
        data_received() method.
        """
        self._ssl_protocol._resume_reading()

    def set_write_buffer_limits(self, high=Nichts, low=Nichts):
        """Set the high- und low-water limits fuer write flow control.

        These two values control when to call the protocol's
        pause_writing() und resume_writing() methods.  If specified,
        the low-water limit must be less than oder equal to the
        high-water limit.  Neither value can be negative.

        The defaults are implementation-specific.  If only the
        high-water limit is given, the low-water limit defaults to an
        implementation-specific value less than oder equal to the
        high-water limit.  Setting high to zero forces low to zero as
        well, und causes pause_writing() to be called whenever the
        buffer becomes non-empty.  Setting low to zero causes
        resume_writing() to be called only once the buffer is empty.
        Use of zero fuer either limit is generally sub-optimal als it
        reduces opportunities fuer doing I/O und computation
        concurrently.
        """
        self._ssl_protocol._set_write_buffer_limits(high, low)
        self._ssl_protocol._control_app_writing()

    def get_write_buffer_limits(self):
        return (self._ssl_protocol._outgoing_low_water,
                self._ssl_protocol._outgoing_high_water)

    def get_write_buffer_size(self):
        """Return the current size of the write buffers."""
        return self._ssl_protocol._get_write_buffer_size()

    def set_read_buffer_limits(self, high=Nichts, low=Nichts):
        """Set the high- und low-water limits fuer read flow control.

        These two values control when to call the upstream transport's
        pause_reading() und resume_reading() methods.  If specified,
        the low-water limit must be less than oder equal to the
        high-water limit.  Neither value can be negative.

        The defaults are implementation-specific.  If only the
        high-water limit is given, the low-water limit defaults to an
        implementation-specific value less than oder equal to the
        high-water limit.  Setting high to zero forces low to zero as
        well, und causes pause_reading() to be called whenever the
        buffer becomes non-empty.  Setting low to zero causes
        resume_reading() to be called only once the buffer is empty.
        Use of zero fuer either limit is generally sub-optimal als it
        reduces opportunities fuer doing I/O und computation
        concurrently.
        """
        self._ssl_protocol._set_read_buffer_limits(high, low)
        self._ssl_protocol._control_ssl_reading()

    def get_read_buffer_limits(self):
        return (self._ssl_protocol._incoming_low_water,
                self._ssl_protocol._incoming_high_water)

    def get_read_buffer_size(self):
        """Return the current size of the read buffer."""
        return self._ssl_protocol._get_read_buffer_size()

    @property
    def _protocol_paused(self):
        # Required fuer sendfile fallback pause_writing/resume_writing logic
        return self._ssl_protocol._app_writing_paused

    def write(self, data):
        """Write some data bytes to the transport.

        This does nicht block; it buffers the data und arranges fuer it
        to be sent out asynchronously.
        """
        wenn nicht isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f"data: expecting a bytes-like instance, "
                            f"got {type(data).__name__}")
        wenn nicht data:
            return
        self._ssl_protocol._write_appdata((data,))

    def writelines(self, list_of_data):
        """Write a list (or any iterable) of data bytes to the transport.

        The default implementation concatenates the arguments und
        calls write() on the result.
        """
        self._ssl_protocol._write_appdata(list_of_data)

    def write_eof(self):
        """Close the write end after flushing buffered data.

        This raises :exc:`NotImplementedError` right now.
        """
        raise NotImplementedError

    def can_write_eof(self):
        """Return Wahr wenn this transport supports write_eof(), Falsch wenn not."""
        return Falsch

    def abort(self):
        """Close the transport immediately.

        Buffered data will be lost.  No more data will be received.
        The protocol's connection_lost() method will (eventually) be
        called mit Nichts als its argument.
        """
        self._force_close(Nichts)

    def _force_close(self, exc):
        self._closed = Wahr
        wenn self._ssl_protocol is nicht Nichts:
            self._ssl_protocol._abort(exc)

    def _test__append_write_backlog(self, data):
        # fuer test only
        self._ssl_protocol._write_backlog.append(data)
        self._ssl_protocol._write_buffer_size += len(data)


klasse SSLProtocol(protocols.BufferedProtocol):
    max_size = 256 * 1024   # Buffer size passed to read()

    _handshake_start_time = Nichts
    _handshake_timeout_handle = Nichts
    _shutdown_timeout_handle = Nichts

    def __init__(self, loop, app_protocol, sslcontext, waiter,
                 server_side=Falsch, server_hostname=Nichts,
                 call_connection_made=Wahr,
                 ssl_handshake_timeout=Nichts,
                 ssl_shutdown_timeout=Nichts):
        wenn ssl is Nichts:
            raise RuntimeError("stdlib ssl module nicht available")

        self._ssl_buffer = bytearray(self.max_size)
        self._ssl_buffer_view = memoryview(self._ssl_buffer)

        wenn ssl_handshake_timeout is Nichts:
            ssl_handshake_timeout = constants.SSL_HANDSHAKE_TIMEOUT
        sowenn ssl_handshake_timeout <= 0:
            raise ValueError(
                f"ssl_handshake_timeout should be a positive number, "
                f"got {ssl_handshake_timeout}")
        wenn ssl_shutdown_timeout is Nichts:
            ssl_shutdown_timeout = constants.SSL_SHUTDOWN_TIMEOUT
        sowenn ssl_shutdown_timeout <= 0:
            raise ValueError(
                f"ssl_shutdown_timeout should be a positive number, "
                f"got {ssl_shutdown_timeout}")

        wenn nicht sslcontext:
            sslcontext = _create_transport_context(
                server_side, server_hostname)

        self._server_side = server_side
        wenn server_hostname und nicht server_side:
            self._server_hostname = server_hostname
        sonst:
            self._server_hostname = Nichts
        self._sslcontext = sslcontext
        # SSL-specific extra info. More info are set when the handshake
        # completes.
        self._extra = dict(sslcontext=sslcontext)

        # App data write buffering
        self._write_backlog = collections.deque()
        self._write_buffer_size = 0

        self._waiter = waiter
        self._loop = loop
        self._set_app_protocol(app_protocol)
        self._app_transport = Nichts
        self._app_transport_created = Falsch
        # transport, ex: SelectorSocketTransport
        self._transport = Nichts
        self._ssl_handshake_timeout = ssl_handshake_timeout
        self._ssl_shutdown_timeout = ssl_shutdown_timeout
        # SSL und state machine
        self._incoming = ssl.MemoryBIO()
        self._outgoing = ssl.MemoryBIO()
        self._state = SSLProtocolState.UNWRAPPED
        self._conn_lost = 0  # Set when connection_lost called
        wenn call_connection_made:
            self._app_state = AppProtocolState.STATE_INIT
        sonst:
            self._app_state = AppProtocolState.STATE_CON_MADE
        self._sslobj = self._sslcontext.wrap_bio(
            self._incoming, self._outgoing,
            server_side=self._server_side,
            server_hostname=self._server_hostname)

        # Flow Control

        self._ssl_writing_paused = Falsch

        self._app_reading_paused = Falsch

        self._ssl_reading_paused = Falsch
        self._incoming_high_water = 0
        self._incoming_low_water = 0
        self._set_read_buffer_limits()
        self._eof_received = Falsch

        self._app_writing_paused = Falsch
        self._outgoing_high_water = 0
        self._outgoing_low_water = 0
        self._set_write_buffer_limits()
        self._get_app_transport()

    def _set_app_protocol(self, app_protocol):
        self._app_protocol = app_protocol
        # Make fast hasattr check first
        wenn (hasattr(app_protocol, 'get_buffer') und
                isinstance(app_protocol, protocols.BufferedProtocol)):
            self._app_protocol_get_buffer = app_protocol.get_buffer
            self._app_protocol_buffer_updated = app_protocol.buffer_updated
            self._app_protocol_is_buffer = Wahr
        sonst:
            self._app_protocol_is_buffer = Falsch

    def _wakeup_waiter(self, exc=Nichts):
        wenn self._waiter is Nichts:
            return
        wenn nicht self._waiter.cancelled():
            wenn exc is nicht Nichts:
                self._waiter.set_exception(exc)
            sonst:
                self._waiter.set_result(Nichts)
        self._waiter = Nichts

    def _get_app_transport(self):
        wenn self._app_transport is Nichts:
            wenn self._app_transport_created:
                raise RuntimeError('Creating _SSLProtocolTransport twice')
            self._app_transport = _SSLProtocolTransport(self._loop, self)
            self._app_transport_created = Wahr
        return self._app_transport

    def _is_transport_closing(self):
        return self._transport is nicht Nichts und self._transport.is_closing()

    def connection_made(self, transport):
        """Called when the low-level connection is made.

        Start the SSL handshake.
        """
        self._transport = transport
        self._start_handshake()

    def connection_lost(self, exc):
        """Called when the low-level connection is lost oder closed.

        The argument is an exception object oder Nichts (the latter
        meaning a regular EOF is received oder the connection was
        aborted oder closed).
        """
        self._write_backlog.clear()
        self._outgoing.read()
        self._conn_lost += 1

        # Just mark the app transport als closed so that its __dealloc__
        # doesn't complain.
        wenn self._app_transport is nicht Nichts:
            self._app_transport._closed = Wahr

        wenn self._state != SSLProtocolState.DO_HANDSHAKE:
            wenn (
                self._app_state == AppProtocolState.STATE_CON_MADE oder
                self._app_state == AppProtocolState.STATE_EOF
            ):
                self._app_state = AppProtocolState.STATE_CON_LOST
                self._loop.call_soon(self._app_protocol.connection_lost, exc)
        self._set_state(SSLProtocolState.UNWRAPPED)
        self._transport = Nichts
        self._app_transport = Nichts
        self._app_protocol = Nichts
        self._wakeup_waiter(exc)

        wenn self._shutdown_timeout_handle:
            self._shutdown_timeout_handle.cancel()
            self._shutdown_timeout_handle = Nichts
        wenn self._handshake_timeout_handle:
            self._handshake_timeout_handle.cancel()
            self._handshake_timeout_handle = Nichts

    def get_buffer(self, n):
        want = n
        wenn want <= 0 oder want > self.max_size:
            want = self.max_size
        wenn len(self._ssl_buffer) < want:
            self._ssl_buffer = bytearray(want)
            self._ssl_buffer_view = memoryview(self._ssl_buffer)
        return self._ssl_buffer_view

    def buffer_updated(self, nbytes):
        self._incoming.write(self._ssl_buffer_view[:nbytes])

        wenn self._state == SSLProtocolState.DO_HANDSHAKE:
            self._do_handshake()

        sowenn self._state == SSLProtocolState.WRAPPED:
            self._do_read()

        sowenn self._state == SSLProtocolState.FLUSHING:
            self._do_flush()

        sowenn self._state == SSLProtocolState.SHUTDOWN:
            self._do_shutdown()

    def eof_received(self):
        """Called when the other end of the low-level stream
        is half-closed.

        If this returns a false value (including Nichts), the transport
        will close itself.  If it returns a true value, closing the
        transport is up to the protocol.
        """
        self._eof_received = Wahr
        try:
            wenn self._loop.get_debug():
                logger.debug("%r received EOF", self)

            wenn self._state == SSLProtocolState.DO_HANDSHAKE:
                self._on_handshake_complete(ConnectionResetError)

            sowenn self._state == SSLProtocolState.WRAPPED:
                self._set_state(SSLProtocolState.FLUSHING)
                wenn self._app_reading_paused:
                    return Wahr
                sonst:
                    self._do_flush()

            sowenn self._state == SSLProtocolState.FLUSHING:
                self._do_write()
                self._set_state(SSLProtocolState.SHUTDOWN)
                self._do_shutdown()

            sowenn self._state == SSLProtocolState.SHUTDOWN:
                self._do_shutdown()

        except Exception:
            self._transport.close()
            raise

    def _get_extra_info(self, name, default=Nichts):
        wenn name in self._extra:
            return self._extra[name]
        sowenn self._transport is nicht Nichts:
            return self._transport.get_extra_info(name, default)
        sonst:
            return default

    def _set_state(self, new_state):
        allowed = Falsch

        wenn new_state == SSLProtocolState.UNWRAPPED:
            allowed = Wahr

        sowenn (
            self._state == SSLProtocolState.UNWRAPPED und
            new_state == SSLProtocolState.DO_HANDSHAKE
        ):
            allowed = Wahr

        sowenn (
            self._state == SSLProtocolState.DO_HANDSHAKE und
            new_state == SSLProtocolState.WRAPPED
        ):
            allowed = Wahr

        sowenn (
            self._state == SSLProtocolState.WRAPPED und
            new_state == SSLProtocolState.FLUSHING
        ):
            allowed = Wahr

        sowenn (
            self._state == SSLProtocolState.FLUSHING und
            new_state == SSLProtocolState.SHUTDOWN
        ):
            allowed = Wahr

        wenn allowed:
            self._state = new_state

        sonst:
            raise RuntimeError(
                'cannot switch state von {} to {}'.format(
                    self._state, new_state))

    # Handshake flow

    def _start_handshake(self):
        wenn self._loop.get_debug():
            logger.debug("%r starts SSL handshake", self)
            self._handshake_start_time = self._loop.time()
        sonst:
            self._handshake_start_time = Nichts

        self._set_state(SSLProtocolState.DO_HANDSHAKE)

        # start handshake timeout count down
        self._handshake_timeout_handle = \
            self._loop.call_later(self._ssl_handshake_timeout,
                                  self._check_handshake_timeout)

        self._do_handshake()

    def _check_handshake_timeout(self):
        wenn self._state == SSLProtocolState.DO_HANDSHAKE:
            msg = (
                f"SSL handshake is taking longer than "
                f"{self._ssl_handshake_timeout} seconds: "
                f"aborting the connection"
            )
            self._fatal_error(ConnectionAbortedError(msg))

    def _do_handshake(self):
        try:
            self._sslobj.do_handshake()
        except SSLAgainErrors:
            self._process_outgoing()
        except ssl.SSLError als exc:
            self._on_handshake_complete(exc)
        sonst:
            self._on_handshake_complete(Nichts)

    def _on_handshake_complete(self, handshake_exc):
        wenn self._handshake_timeout_handle is nicht Nichts:
            self._handshake_timeout_handle.cancel()
            self._handshake_timeout_handle = Nichts

        sslobj = self._sslobj
        try:
            wenn handshake_exc is Nichts:
                self._set_state(SSLProtocolState.WRAPPED)
            sonst:
                raise handshake_exc

            peercert = sslobj.getpeercert()
        except Exception als exc:
            handshake_exc = Nichts
            self._set_state(SSLProtocolState.UNWRAPPED)
            wenn isinstance(exc, ssl.CertificateError):
                msg = 'SSL handshake failed on verifying the certificate'
            sonst:
                msg = 'SSL handshake failed'
            self._fatal_error(exc, msg)
            self._wakeup_waiter(exc)
            return

        wenn self._loop.get_debug():
            dt = self._loop.time() - self._handshake_start_time
            logger.debug("%r: SSL handshake took %.1f ms", self, dt * 1e3)

        # Add extra info that becomes available after handshake.
        self._extra.update(peercert=peercert,
                           cipher=sslobj.cipher(),
                           compression=sslobj.compression(),
                           ssl_object=sslobj)
        wenn self._app_state == AppProtocolState.STATE_INIT:
            self._app_state = AppProtocolState.STATE_CON_MADE
            self._app_protocol.connection_made(self._get_app_transport())
        self._wakeup_waiter()
        self._do_read()

    # Shutdown flow

    def _start_shutdown(self):
        wenn (
            self._state in (
                SSLProtocolState.FLUSHING,
                SSLProtocolState.SHUTDOWN,
                SSLProtocolState.UNWRAPPED
            )
        ):
            return
        wenn self._app_transport is nicht Nichts:
            self._app_transport._closed = Wahr
        wenn self._state == SSLProtocolState.DO_HANDSHAKE:
            self._abort(Nichts)
        sonst:
            self._set_state(SSLProtocolState.FLUSHING)
            self._shutdown_timeout_handle = self._loop.call_later(
                self._ssl_shutdown_timeout,
                self._check_shutdown_timeout
            )
            self._do_flush()

    def _check_shutdown_timeout(self):
        wenn (
            self._state in (
                SSLProtocolState.FLUSHING,
                SSLProtocolState.SHUTDOWN
            )
        ):
            self._transport._force_close(
                exceptions.TimeoutError('SSL shutdown timed out'))

    def _do_flush(self):
        self._do_read()
        self._set_state(SSLProtocolState.SHUTDOWN)
        self._do_shutdown()

    def _do_shutdown(self):
        try:
            wenn nicht self._eof_received:
                self._sslobj.unwrap()
        except SSLAgainErrors:
            self._process_outgoing()
        except ssl.SSLError als exc:
            self._on_shutdown_complete(exc)
        sonst:
            self._process_outgoing()
            self._call_eof_received()
            self._on_shutdown_complete(Nichts)

    def _on_shutdown_complete(self, shutdown_exc):
        wenn self._shutdown_timeout_handle is nicht Nichts:
            self._shutdown_timeout_handle.cancel()
            self._shutdown_timeout_handle = Nichts

        wenn shutdown_exc:
            self._fatal_error(shutdown_exc)
        sonst:
            self._loop.call_soon(self._transport.close)

    def _abort(self, exc):
        self._set_state(SSLProtocolState.UNWRAPPED)
        wenn self._transport is nicht Nichts:
            self._transport._force_close(exc)

    # Outgoing flow

    def _write_appdata(self, list_of_data):
        wenn (
            self._state in (
                SSLProtocolState.FLUSHING,
                SSLProtocolState.SHUTDOWN,
                SSLProtocolState.UNWRAPPED
            )
        ):
            wenn self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('SSL connection is closed')
            self._conn_lost += 1
            return

        fuer data in list_of_data:
            self._write_backlog.append(data)
            self._write_buffer_size += len(data)

        try:
            wenn self._state == SSLProtocolState.WRAPPED:
                self._do_write()

        except Exception als ex:
            self._fatal_error(ex, 'Fatal error on SSL protocol')

    def _do_write(self):
        try:
            while self._write_backlog:
                data = self._write_backlog[0]
                count = self._sslobj.write(data)
                data_len = len(data)
                wenn count < data_len:
                    self._write_backlog[0] = data[count:]
                    self._write_buffer_size -= count
                sonst:
                    del self._write_backlog[0]
                    self._write_buffer_size -= data_len
        except SSLAgainErrors:
            pass
        self._process_outgoing()

    def _process_outgoing(self):
        wenn nicht self._ssl_writing_paused:
            data = self._outgoing.read()
            wenn len(data):
                self._transport.write(data)
        self._control_app_writing()

    # Incoming flow

    def _do_read(self):
        wenn (
            self._state nicht in (
                SSLProtocolState.WRAPPED,
                SSLProtocolState.FLUSHING,
            )
        ):
            return
        try:
            wenn nicht self._app_reading_paused:
                wenn self._app_protocol_is_buffer:
                    self._do_read__buffered()
                sonst:
                    self._do_read__copied()
                wenn self._write_backlog:
                    self._do_write()
                sonst:
                    self._process_outgoing()
            self._control_ssl_reading()
        except Exception als ex:
            self._fatal_error(ex, 'Fatal error on SSL protocol')

    def _do_read__buffered(self):
        offset = 0
        count = 1

        buf = self._app_protocol_get_buffer(self._get_read_buffer_size())
        wants = len(buf)

        try:
            count = self._sslobj.read(wants, buf)

            wenn count > 0:
                offset = count
                while offset < wants:
                    count = self._sslobj.read(wants - offset, buf[offset:])
                    wenn count > 0:
                        offset += count
                    sonst:
                        break
                sonst:
                    self._loop.call_soon(self._do_read)
        except SSLAgainErrors:
            pass
        wenn offset > 0:
            self._app_protocol_buffer_updated(offset)
        wenn nicht count:
            # close_notify
            self._call_eof_received()
            self._start_shutdown()

    def _do_read__copied(self):
        chunk = b'1'
        zero = Wahr
        one = Falsch

        try:
            while Wahr:
                chunk = self._sslobj.read(self.max_size)
                wenn nicht chunk:
                    break
                wenn zero:
                    zero = Falsch
                    one = Wahr
                    first = chunk
                sowenn one:
                    one = Falsch
                    data = [first, chunk]
                sonst:
                    data.append(chunk)
        except SSLAgainErrors:
            pass
        wenn one:
            self._app_protocol.data_received(first)
        sowenn nicht zero:
            self._app_protocol.data_received(b''.join(data))
        wenn nicht chunk:
            # close_notify
            self._call_eof_received()
            self._start_shutdown()

    def _call_eof_received(self):
        try:
            wenn self._app_state == AppProtocolState.STATE_CON_MADE:
                self._app_state = AppProtocolState.STATE_EOF
                keep_open = self._app_protocol.eof_received()
                wenn keep_open:
                    logger.warning('returning true von eof_received() '
                                   'has no effect when using ssl')
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException als ex:
            self._fatal_error(ex, 'Error calling eof_received()')

    # Flow control fuer writes von APP socket

    def _control_app_writing(self):
        size = self._get_write_buffer_size()
        wenn size >= self._outgoing_high_water und nicht self._app_writing_paused:
            self._app_writing_paused = Wahr
            try:
                self._app_protocol.pause_writing()
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException als exc:
                self._loop.call_exception_handler({
                    'message': 'protocol.pause_writing() failed',
                    'exception': exc,
                    'transport': self._app_transport,
                    'protocol': self,
                })
        sowenn size <= self._outgoing_low_water und self._app_writing_paused:
            self._app_writing_paused = Falsch
            try:
                self._app_protocol.resume_writing()
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException als exc:
                self._loop.call_exception_handler({
                    'message': 'protocol.resume_writing() failed',
                    'exception': exc,
                    'transport': self._app_transport,
                    'protocol': self,
                })

    def _get_write_buffer_size(self):
        return self._outgoing.pending + self._write_buffer_size

    def _set_write_buffer_limits(self, high=Nichts, low=Nichts):
        high, low = add_flowcontrol_defaults(
            high, low, constants.FLOW_CONTROL_HIGH_WATER_SSL_WRITE)
        self._outgoing_high_water = high
        self._outgoing_low_water = low

    # Flow control fuer reads to APP socket

    def _pause_reading(self):
        self._app_reading_paused = Wahr

    def _resume_reading(self):
        wenn self._app_reading_paused:
            self._app_reading_paused = Falsch

            def resume():
                wenn self._state == SSLProtocolState.WRAPPED:
                    self._do_read()
                sowenn self._state == SSLProtocolState.FLUSHING:
                    self._do_flush()
                sowenn self._state == SSLProtocolState.SHUTDOWN:
                    self._do_shutdown()
            self._loop.call_soon(resume)

    # Flow control fuer reads von SSL socket

    def _control_ssl_reading(self):
        size = self._get_read_buffer_size()
        wenn size >= self._incoming_high_water und nicht self._ssl_reading_paused:
            self._ssl_reading_paused = Wahr
            self._transport.pause_reading()
        sowenn size <= self._incoming_low_water und self._ssl_reading_paused:
            self._ssl_reading_paused = Falsch
            self._transport.resume_reading()

    def _set_read_buffer_limits(self, high=Nichts, low=Nichts):
        high, low = add_flowcontrol_defaults(
            high, low, constants.FLOW_CONTROL_HIGH_WATER_SSL_READ)
        self._incoming_high_water = high
        self._incoming_low_water = low

    def _get_read_buffer_size(self):
        return self._incoming.pending

    # Flow control fuer writes to SSL socket

    def pause_writing(self):
        """Called when the low-level transport's buffer goes over
        the high-water mark.
        """
        assert nicht self._ssl_writing_paused
        self._ssl_writing_paused = Wahr

    def resume_writing(self):
        """Called when the low-level transport's buffer drains below
        the low-water mark.
        """
        assert self._ssl_writing_paused
        self._ssl_writing_paused = Falsch
        self._process_outgoing()

    def _fatal_error(self, exc, message='Fatal error on transport'):
        wenn self._transport:
            self._transport._force_close(exc)

        wenn isinstance(exc, OSError):
            wenn self._loop.get_debug():
                logger.debug("%r: %s", self, message, exc_info=Wahr)
        sowenn nicht isinstance(exc, exceptions.CancelledError):
            self._loop.call_exception_handler({
                'message': message,
                'exception': exc,
                'transport': self._transport,
                'protocol': self,
            })
