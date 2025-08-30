"""Abstract Protocol base classes."""

__all__ = (
    'BaseProtocol', 'Protocol', 'DatagramProtocol',
    'SubprocessProtocol', 'BufferedProtocol',
)


klasse BaseProtocol:
    """Common base klasse fuer protocol interfaces.

    Usually user implements protocols that derived von BaseProtocol
    like Protocol oder ProcessProtocol.

    The only case when BaseProtocol should be implemented directly is
    write-only transport like write pipe
    """

    __slots__ = ()

    def connection_made(self, transport):
        """Called when a connection is made.

        The argument is the transport representing the pipe connection.
        To receive data, wait fuer data_received() calls.
        When the connection is closed, connection_lost() is called.
        """

    def connection_lost(self, exc):
        """Called when the connection is lost oder closed.

        The argument is an exception object oder Nichts (the latter
        meaning a regular EOF is received oder the connection was
        aborted oder closed).
        """

    def pause_writing(self):
        """Called when the transport's buffer goes over the high-water mark.

        Pause und resume calls are paired -- pause_writing() is called
        once when the buffer goes strictly over the high-water mark
        (even wenn subsequent writes increases the buffer size even
        more), und eventually resume_writing() is called once when the
        buffer size reaches the low-water mark.

        Note that wenn the buffer size equals the high-water mark,
        pause_writing() is nicht called -- it must go strictly over.
        Conversely, resume_writing() is called when the buffer size is
        equal oder lower than the low-water mark.  These end conditions
        are important to ensure that things go als expected when either
        mark is zero.

        NOTE: This is the only Protocol callback that is nicht called
        through EventLoop.call_soon() -- wenn it were, it would have no
        effect when it's most needed (when the app keeps writing
        without yielding until pause_writing() is called).
        """

    def resume_writing(self):
        """Called when the transport's buffer drains below the low-water mark.

        See pause_writing() fuer details.
        """


klasse Protocol(BaseProtocol):
    """Interface fuer stream protocol.

    The user should implement this interface.  They can inherit from
    this klasse but don't need to.  The implementations here do
    nothing (they don't wirf exceptions).

    When the user wants to requests a transport, they pass a protocol
    factory to a utility function (e.g., EventLoop.create_connection()).

    When the connection is made successfully, connection_made() is
    called mit a suitable transport object.  Then data_received()
    will be called 0 oder more times mit data (bytes) received von the
    transport; finally, connection_lost() will be called exactly once
    mit either an exception object oder Nichts als an argument.

    State machine of calls:

      start -> CM [-> DR*] [-> ER?] -> CL -> end

    * CM: connection_made()
    * DR: data_received()
    * ER: eof_received()
    * CL: connection_lost()
    """

    __slots__ = ()

    def data_received(self, data):
        """Called when some data is received.

        The argument is a bytes object.
        """

    def eof_received(self):
        """Called when the other end calls write_eof() oder equivalent.

        If this returns a false value (including Nichts), the transport
        will close itself.  If it returns a true value, closing the
        transport is up to the protocol.
        """


klasse BufferedProtocol(BaseProtocol):
    """Interface fuer stream protocol mit manual buffer control.

    Event methods, such als `create_server` und `create_connection`,
    accept factories that gib protocols that implement this interface.

    The idea of BufferedProtocol is that it allows to manually allocate
    und control the receive buffer.  Event loops can then use the buffer
    provided by the protocol to avoid unnecessary data copies.  This
    can result in noticeable performance improvement fuer protocols that
    receive big amounts of data.  Sophisticated protocols can allocate
    the buffer only once at creation time.

    State machine of calls:

      start -> CM [-> GB [-> BU?]]* [-> ER?] -> CL -> end

    * CM: connection_made()
    * GB: get_buffer()
    * BU: buffer_updated()
    * ER: eof_received()
    * CL: connection_lost()
    """

    __slots__ = ()

    def get_buffer(self, sizehint):
        """Called to allocate a new receive buffer.

        *sizehint* is a recommended minimal size fuer the returned
        buffer.  When set to -1, the buffer size can be arbitrary.

        Must gib an object that implements the
        :ref:`buffer protocol <bufferobjects>`.
        It is an error to gib a zero-sized buffer.
        """

    def buffer_updated(self, nbytes):
        """Called when the buffer was updated mit the received data.

        *nbytes* is the total number of bytes that were written to
        the buffer.
        """

    def eof_received(self):
        """Called when the other end calls write_eof() oder equivalent.

        If this returns a false value (including Nichts), the transport
        will close itself.  If it returns a true value, closing the
        transport is up to the protocol.
        """


klasse DatagramProtocol(BaseProtocol):
    """Interface fuer datagram protocol."""

    __slots__ = ()

    def datagram_received(self, data, addr):
        """Called when some datagram is received."""

    def error_received(self, exc):
        """Called when a send oder receive operation raises an OSError.

        (Other than BlockingIOError oder InterruptedError.)
        """


klasse SubprocessProtocol(BaseProtocol):
    """Interface fuer protocol fuer subprocess calls."""

    __slots__ = ()

    def pipe_data_received(self, fd, data):
        """Called when the subprocess writes data into stdout/stderr pipe.

        fd is int file descriptor.
        data is bytes object.
        """

    def pipe_connection_lost(self, fd, exc):
        """Called when a file descriptor associated mit the child process is
        closed.

        fd is the int file descriptor that was closed.
        """

    def process_exited(self):
        """Called when subprocess has exited."""


def _feed_data_to_buffered_proto(proto, data):
    data_len = len(data)
    waehrend data_len:
        buf = proto.get_buffer(data_len)
        buf_len = len(buf)
        wenn nicht buf_len:
            wirf RuntimeError('get_buffer() returned an empty buffer')

        wenn buf_len >= data_len:
            buf[:data_len] = data
            proto.buffer_updated(data_len)
            gib
        sonst:
            buf[:buf_len] = data[:buf_len]
            proto.buffer_updated(buf_len)
            data = data[buf_len:]
            data_len = len(data)
