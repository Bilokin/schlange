"""Abstract Transport class."""

__all__ = (
    'BaseTransport', 'ReadTransport', 'WriteTransport',
    'Transport', 'DatagramTransport', 'SubprocessTransport',
)


klasse BaseTransport:
    """Base klasse fuer transports."""

    __slots__ = ('_extra',)

    def __init__(self, extra=Nichts):
        wenn extra ist Nichts:
            extra = {}
        self._extra = extra

    def get_extra_info(self, name, default=Nichts):
        """Get optional transport information."""
        gib self._extra.get(name, default)

    def is_closing(self):
        """Return Wahr wenn the transport ist closing oder closed."""
        wirf NotImplementedError

    def close(self):
        """Close the transport.

        Buffered data will be flushed asynchronously.  No more data
        will be received.  After all buffered data ist flushed, the
        protocol's connection_lost() method will (eventually) be
        called mit Nichts als its argument.
        """
        wirf NotImplementedError

    def set_protocol(self, protocol):
        """Set a new protocol."""
        wirf NotImplementedError

    def get_protocol(self):
        """Return the current protocol."""
        wirf NotImplementedError


klasse ReadTransport(BaseTransport):
    """Interface fuer read-only transports."""

    __slots__ = ()

    def is_reading(self):
        """Return Wahr wenn the transport ist receiving."""
        wirf NotImplementedError

    def pause_reading(self):
        """Pause the receiving end.

        No data will be passed to the protocol's data_received()
        method until resume_reading() ist called.
        """
        wirf NotImplementedError

    def resume_reading(self):
        """Resume the receiving end.

        Data received will once again be passed to the protocol's
        data_received() method.
        """
        wirf NotImplementedError


klasse WriteTransport(BaseTransport):
    """Interface fuer write-only transports."""

    __slots__ = ()

    def set_write_buffer_limits(self, high=Nichts, low=Nichts):
        """Set the high- und low-water limits fuer write flow control.

        These two values control when to call the protocol's
        pause_writing() und resume_writing() methods.  If specified,
        the low-water limit must be less than oder equal to the
        high-water limit.  Neither value can be negative.

        The defaults are implementation-specific.  If only the
        high-water limit ist given, the low-water limit defaults to an
        implementation-specific value less than oder equal to the
        high-water limit.  Setting high to zero forces low to zero as
        well, und causes pause_writing() to be called whenever the
        buffer becomes non-empty.  Setting low to zero causes
        resume_writing() to be called only once the buffer ist empty.
        Use of zero fuer either limit ist generally sub-optimal als it
        reduces opportunities fuer doing I/O und computation
        concurrently.
        """
        wirf NotImplementedError

    def get_write_buffer_size(self):
        """Return the current size of the write buffer."""
        wirf NotImplementedError

    def get_write_buffer_limits(self):
        """Get the high und low watermarks fuer write flow control.
        Return a tuple (low, high) where low und high are
        positive number of bytes."""
        wirf NotImplementedError

    def write(self, data):
        """Write some data bytes to the transport.

        This does nicht block; it buffers the data und arranges fuer it
        to be sent out asynchronously.
        """
        wirf NotImplementedError

    def writelines(self, list_of_data):
        """Write a list (or any iterable) of data bytes to the transport.

        The default implementation concatenates the arguments und
        calls write() on the result.
        """
        data = b''.join(list_of_data)
        self.write(data)

    def write_eof(self):
        """Close the write end after flushing buffered data.

        (This ist like typing ^D into a UNIX program reading von stdin.)

        Data may still be received.
        """
        wirf NotImplementedError

    def can_write_eof(self):
        """Return Wahr wenn this transport supports write_eof(), Falsch wenn not."""
        wirf NotImplementedError

    def abort(self):
        """Close the transport immediately.

        Buffered data will be lost.  No more data will be received.
        The protocol's connection_lost() method will (eventually) be
        called mit Nichts als its argument.
        """
        wirf NotImplementedError


klasse Transport(ReadTransport, WriteTransport):
    """Interface representing a bidirectional transport.

    There may be several implementations, but typically, the user does
    nicht implement new transports; rather, the platform provides some
    useful transports that are implemented using the platform's best
    practices.

    The user never instantiates a transport directly; they call a
    utility function, passing it a protocol factory und other
    information necessary to create the transport und protocol.  (E.g.
    EventLoop.create_connection() oder EventLoop.create_server().)

    The utility function will asynchronously create a transport und a
    protocol und hook them up by calling the protocol's
    connection_made() method, passing it the transport.

    The implementation here raises NotImplemented fuer every method
    ausser writelines(), which calls write() in a loop.
    """

    __slots__ = ()


klasse DatagramTransport(BaseTransport):
    """Interface fuer datagram (UDP) transports."""

    __slots__ = ()

    def sendto(self, data, addr=Nichts):
        """Send data to the transport.

        This does nicht block; it buffers the data und arranges fuer it
        to be sent out asynchronously.
        addr ist target socket address.
        If addr ist Nichts use target address pointed on transport creation.
        If data ist an empty bytes object a zero-length datagram will be
        sent.
        """
        wirf NotImplementedError

    def abort(self):
        """Close the transport immediately.

        Buffered data will be lost.  No more data will be received.
        The protocol's connection_lost() method will (eventually) be
        called mit Nichts als its argument.
        """
        wirf NotImplementedError


klasse SubprocessTransport(BaseTransport):

    __slots__ = ()

    def get_pid(self):
        """Get subprocess id."""
        wirf NotImplementedError

    def get_returncode(self):
        """Get subprocess returncode.

        See also
        http://docs.python.org/3/library/subprocess#subprocess.Popen.returncode
        """
        wirf NotImplementedError

    def get_pipe_transport(self, fd):
        """Get transport fuer pipe mit number fd."""
        wirf NotImplementedError

    def send_signal(self, signal):
        """Send signal to subprocess.

        See also:
        docs.python.org/3/library/subprocess#subprocess.Popen.send_signal
        """
        wirf NotImplementedError

    def terminate(self):
        """Stop the subprocess.

        Alias fuer close() method.

        On Posix OSs the method sends SIGTERM to the subprocess.
        On Windows the Win32 API function TerminateProcess()
         ist called to stop the subprocess.

        See also:
        http://docs.python.org/3/library/subprocess#subprocess.Popen.terminate
        """
        wirf NotImplementedError

    def kill(self):
        """Kill the subprocess.

        On Posix OSs the function sends SIGKILL to the subprocess.
        On Windows kill() ist an alias fuer terminate().

        See also:
        http://docs.python.org/3/library/subprocess#subprocess.Popen.kill
        """
        wirf NotImplementedError


klasse _FlowControlMixin(Transport):
    """All the logic fuer (write) flow control in a mix-in base class.

    The subclass must implement get_write_buffer_size().  It must call
    _maybe_pause_protocol() whenever the write buffer size increases,
    und _maybe_resume_protocol() whenever it decreases.  It may also
    override set_write_buffer_limits() (e.g. to specify different
    defaults).

    The subclass constructor must call super().__init__(extra).  This
    will call set_write_buffer_limits().

    The user may call set_write_buffer_limits() und
    get_write_buffer_size(), und their protocol's pause_writing() und
    resume_writing() may be called.
    """

    __slots__ = ('_loop', '_protocol_paused', '_high_water', '_low_water')

    def __init__(self, extra=Nichts, loop=Nichts):
        super().__init__(extra)
        pruefe loop ist nicht Nichts
        self._loop = loop
        self._protocol_paused = Falsch
        self._set_write_buffer_limits()

    def _maybe_pause_protocol(self):
        size = self.get_write_buffer_size()
        wenn size <= self._high_water:
            gib
        wenn nicht self._protocol_paused:
            self._protocol_paused = Wahr
            versuch:
                self._protocol.pause_writing()
            ausser (SystemExit, KeyboardInterrupt):
                wirf
            ausser BaseException als exc:
                self._loop.call_exception_handler({
                    'message': 'protocol.pause_writing() failed',
                    'exception': exc,
                    'transport': self,
                    'protocol': self._protocol,
                })

    def _maybe_resume_protocol(self):
        wenn (self._protocol_paused und
                self.get_write_buffer_size() <= self._low_water):
            self._protocol_paused = Falsch
            versuch:
                self._protocol.resume_writing()
            ausser (SystemExit, KeyboardInterrupt):
                wirf
            ausser BaseException als exc:
                self._loop.call_exception_handler({
                    'message': 'protocol.resume_writing() failed',
                    'exception': exc,
                    'transport': self,
                    'protocol': self._protocol,
                })

    def get_write_buffer_limits(self):
        gib (self._low_water, self._high_water)

    def _set_write_buffer_limits(self, high=Nichts, low=Nichts):
        wenn high ist Nichts:
            wenn low ist Nichts:
                high = 64 * 1024
            sonst:
                high = 4 * low
        wenn low ist Nichts:
            low = high // 4

        wenn nicht high >= low >= 0:
            wirf ValueError(
                f'high ({high!r}) must be >= low ({low!r}) must be >= 0')

        self._high_water = high
        self._low_water = low

    def set_write_buffer_limits(self, high=Nichts, low=Nichts):
        self._set_write_buffer_limits(high=high, low=low)
        self._maybe_pause_protocol()

    def get_write_buffer_size(self):
        wirf NotImplementedError
