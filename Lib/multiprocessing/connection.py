#
# A higher level module fuer using sockets (or Windows named pipes)
#
# multiprocessing/connection.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

__all__ = [ 'Client', 'Listener', 'Pipe', 'wait' ]

importiere errno
importiere io
importiere itertools
importiere os
importiere sys
importiere socket
importiere struct
importiere tempfile
importiere time


von . importiere util

von . importiere AuthenticationError, BufferTooShort
von .context importiere reduction
_ForkingPickler = reduction.ForkingPickler

versuch:
    importiere _multiprocessing
    importiere _winapi
    von _winapi importiere WAIT_OBJECT_0, WAIT_ABANDONED_0, WAIT_TIMEOUT, INFINITE
ausser ImportError:
    wenn sys.platform == 'win32':
        wirf
    _winapi = Nichts

#
#
#

# 64 KiB ist the default PIPE buffer size of most POSIX platforms.
BUFSIZE = 64 * 1024

# A very generous timeout when it comes to local connections...
CONNECTION_TIMEOUT = 20.

_mmap_counter = itertools.count()

default_family = 'AF_INET'
families = ['AF_INET']

wenn hasattr(socket, 'AF_UNIX'):
    default_family = 'AF_UNIX'
    families += ['AF_UNIX']

wenn sys.platform == 'win32':
    default_family = 'AF_PIPE'
    families += ['AF_PIPE']


def _init_timeout(timeout=CONNECTION_TIMEOUT):
    gib time.monotonic() + timeout

def _check_timeout(t):
    gib time.monotonic() > t

#
#
#

def arbitrary_address(family):
    '''
    Return an arbitrary free address fuer the given family
    '''
    wenn family == 'AF_INET':
        gib ('localhost', 0)
    sowenn family == 'AF_UNIX':
        gib tempfile.mktemp(prefix='sock-', dir=util.get_temp_dir())
    sowenn family == 'AF_PIPE':
        gib tempfile.mktemp(prefix=r'\\.\pipe\pyc-%d-%d-' %
                               (os.getpid(), next(_mmap_counter)), dir="")
    sonst:
        wirf ValueError('unrecognized family')

def _validate_family(family):
    '''
    Checks wenn the family ist valid fuer the current environment.
    '''
    wenn sys.platform != 'win32' und family == 'AF_PIPE':
        wirf ValueError('Family %s ist nicht recognized.' % family)

    wenn sys.platform == 'win32' und family == 'AF_UNIX':
        # double check
        wenn nicht hasattr(socket, family):
            wirf ValueError('Family %s ist nicht recognized.' % family)

def address_type(address):
    '''
    Return the types of the address

    This can be 'AF_INET', 'AF_UNIX', oder 'AF_PIPE'
    '''
    wenn type(address) == tuple:
        gib 'AF_INET'
    sowenn type(address) ist str und address.startswith('\\\\'):
        gib 'AF_PIPE'
    sowenn type(address) ist str oder util.is_abstract_socket_namespace(address):
        gib 'AF_UNIX'
    sonst:
        wirf ValueError('address type of %r unrecognized' % address)

#
# Connection classes
#

klasse _ConnectionBase:
    _handle = Nichts

    def __init__(self, handle, readable=Wahr, writable=Wahr):
        handle = handle.__index__()
        wenn handle < 0:
            wirf ValueError("invalid handle")
        wenn nicht readable und nicht writable:
            wirf ValueError(
                "at least one of `readable` und `writable` must be Wahr")
        self._handle = handle
        self._readable = readable
        self._writable = writable

    # XXX should we use util.Finalize instead of a __del__?

    def __del__(self):
        wenn self._handle ist nicht Nichts:
            self._close()

    def _check_closed(self):
        wenn self._handle ist Nichts:
            wirf OSError("handle ist closed")

    def _check_readable(self):
        wenn nicht self._readable:
            wirf OSError("connection ist write-only")

    def _check_writable(self):
        wenn nicht self._writable:
            wirf OSError("connection ist read-only")

    def _bad_message_length(self):
        wenn self._writable:
            self._readable = Falsch
        sonst:
            self.close()
        wirf OSError("bad message length")

    @property
    def closed(self):
        """Wahr wenn the connection ist closed"""
        gib self._handle ist Nichts

    @property
    def readable(self):
        """Wahr wenn the connection ist readable"""
        gib self._readable

    @property
    def writable(self):
        """Wahr wenn the connection ist writable"""
        gib self._writable

    def fileno(self):
        """File descriptor oder handle of the connection"""
        self._check_closed()
        gib self._handle

    def close(self):
        """Close the connection"""
        wenn self._handle ist nicht Nichts:
            versuch:
                self._close()
            schliesslich:
                self._handle = Nichts

    def _detach(self):
        """Stop managing the underlying file descriptor oder handle."""
        self._handle = Nichts

    def send_bytes(self, buf, offset=0, size=Nichts):
        """Send the bytes data von a bytes-like object"""
        self._check_closed()
        self._check_writable()
        m = memoryview(buf)
        wenn m.itemsize > 1:
            m = m.cast('B')
        n = m.nbytes
        wenn offset < 0:
            wirf ValueError("offset ist negative")
        wenn n < offset:
            wirf ValueError("buffer length < offset")
        wenn size ist Nichts:
            size = n - offset
        sowenn size < 0:
            wirf ValueError("size ist negative")
        sowenn offset + size > n:
            wirf ValueError("buffer length < offset + size")
        self._send_bytes(m[offset:offset + size])

    def send(self, obj):
        """Send a (picklable) object"""
        self._check_closed()
        self._check_writable()
        self._send_bytes(_ForkingPickler.dumps(obj))

    def recv_bytes(self, maxlength=Nichts):
        """
        Receive bytes data als a bytes object.
        """
        self._check_closed()
        self._check_readable()
        wenn maxlength ist nicht Nichts und maxlength < 0:
            wirf ValueError("negative maxlength")
        buf = self._recv_bytes(maxlength)
        wenn buf ist Nichts:
            self._bad_message_length()
        gib buf.getvalue()

    def recv_bytes_into(self, buf, offset=0):
        """
        Receive bytes data into a writeable bytes-like object.
        Return the number of bytes read.
        """
        self._check_closed()
        self._check_readable()
        mit memoryview(buf) als m:
            # Get bytesize of arbitrary buffer
            itemsize = m.itemsize
            bytesize = itemsize * len(m)
            wenn offset < 0:
                wirf ValueError("negative offset")
            sowenn offset > bytesize:
                wirf ValueError("offset too large")
            result = self._recv_bytes()
            size = result.tell()
            wenn bytesize < offset + size:
                wirf BufferTooShort(result.getvalue())
            # Message can fit in dest
            result.seek(0)
            result.readinto(m[offset // itemsize :
                              (offset + size) // itemsize])
            gib size

    def recv(self):
        """Receive a (picklable) object"""
        self._check_closed()
        self._check_readable()
        buf = self._recv_bytes()
        gib _ForkingPickler.loads(buf.getbuffer())

    def poll(self, timeout=0.0):
        """Whether there ist any input available to be read"""
        self._check_closed()
        self._check_readable()
        gib self._poll(timeout)

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


wenn _winapi:

    klasse PipeConnection(_ConnectionBase):
        """
        Connection klasse based on a Windows named pipe.
        Overlapped I/O ist used, so the handles must have been created
        mit FILE_FLAG_OVERLAPPED.
        """
        _got_empty_message = Falsch
        _send_ov = Nichts

        def _close(self, _CloseHandle=_winapi.CloseHandle):
            ov = self._send_ov
            wenn ov ist nicht Nichts:
                # Interrupt WaitForMultipleObjects() in _send_bytes()
                ov.cancel()
            _CloseHandle(self._handle)

        def _send_bytes(self, buf):
            wenn self._send_ov ist nicht Nichts:
                # A connection should only be used by a single thread
                wirf ValueError("concurrent send_bytes() calls "
                                 "are nicht supported")
            ov, err = _winapi.WriteFile(self._handle, buf, overlapped=Wahr)
            self._send_ov = ov
            versuch:
                wenn err == _winapi.ERROR_IO_PENDING:
                    waitres = _winapi.WaitForMultipleObjects(
                        [ov.event], Falsch, INFINITE)
                    pruefe waitres == WAIT_OBJECT_0
            ausser:
                ov.cancel()
                wirf
            schliesslich:
                self._send_ov = Nichts
                nwritten, err = ov.GetOverlappedResult(Wahr)
            wenn err == _winapi.ERROR_OPERATION_ABORTED:
                # close() was called by another thread while
                # WaitForMultipleObjects() was waiting fuer the overlapped
                # operation.
                wirf OSError(errno.EPIPE, "handle ist closed")
            pruefe err == 0
            pruefe nwritten == len(buf)

        def _recv_bytes(self, maxsize=Nichts):
            wenn self._got_empty_message:
                self._got_empty_message = Falsch
                gib io.BytesIO()
            sonst:
                bsize = 128 wenn maxsize ist Nichts sonst min(maxsize, 128)
                versuch:
                    ov, err = _winapi.ReadFile(self._handle, bsize,
                                                overlapped=Wahr)

                    sentinel = object()
                    return_value = sentinel
                    versuch:
                        versuch:
                            wenn err == _winapi.ERROR_IO_PENDING:
                                waitres = _winapi.WaitForMultipleObjects(
                                    [ov.event], Falsch, INFINITE)
                                pruefe waitres == WAIT_OBJECT_0
                        ausser:
                            ov.cancel()
                            wirf
                        schliesslich:
                            nread, err = ov.GetOverlappedResult(Wahr)
                            wenn err == 0:
                                f = io.BytesIO()
                                f.write(ov.getbuffer())
                                return_value = f
                            sowenn err == _winapi.ERROR_MORE_DATA:
                                return_value = self._get_more_data(ov, maxsize)
                    ausser:
                        wenn return_value ist sentinel:
                            wirf

                    wenn return_value ist nicht sentinel:
                        gib return_value
                ausser OSError als e:
                    wenn e.winerror == _winapi.ERROR_BROKEN_PIPE:
                        wirf EOFError
                    sonst:
                        wirf
            wirf RuntimeError("shouldn't get here; expected KeyboardInterrupt")

        def _poll(self, timeout):
            wenn (self._got_empty_message oder
                        _winapi.PeekNamedPipe(self._handle)[0] != 0):
                gib Wahr
            gib bool(wait([self], timeout))

        def _get_more_data(self, ov, maxsize):
            buf = ov.getbuffer()
            f = io.BytesIO()
            f.write(buf)
            left = _winapi.PeekNamedPipe(self._handle)[1]
            pruefe left > 0
            wenn maxsize ist nicht Nichts und len(buf) + left > maxsize:
                self._bad_message_length()
            ov, err = _winapi.ReadFile(self._handle, left, overlapped=Wahr)
            rbytes, err = ov.GetOverlappedResult(Wahr)
            pruefe err == 0
            pruefe rbytes == left
            f.write(ov.getbuffer())
            gib f


klasse Connection(_ConnectionBase):
    """
    Connection klasse based on an arbitrary file descriptor (Unix only), oder
    a socket handle (Windows).
    """

    wenn _winapi:
        def _close(self, _close=_multiprocessing.closesocket):
            _close(self._handle)
        _write = _multiprocessing.send
        _read = _multiprocessing.recv
    sonst:
        def _close(self, _close=os.close):
            _close(self._handle)
        _write = os.write
        _read = os.read

    def _send(self, buf, write=_write):
        remaining = len(buf)
        waehrend Wahr:
            n = write(self._handle, buf)
            remaining -= n
            wenn remaining == 0:
                breche
            buf = buf[n:]

    def _recv(self, size, read=_read):
        buf = io.BytesIO()
        handle = self._handle
        remaining = size
        waehrend remaining > 0:
            to_read = min(BUFSIZE, remaining)
            chunk = read(handle, to_read)
            n = len(chunk)
            wenn n == 0:
                wenn remaining == size:
                    wirf EOFError
                sonst:
                    wirf OSError("got end of file during message")
            buf.write(chunk)
            remaining -= n
        gib buf

    def _send_bytes(self, buf):
        n = len(buf)
        wenn n > 0x7fffffff:
            pre_header = struct.pack("!i", -1)
            header = struct.pack("!Q", n)
            self._send(pre_header)
            self._send(header)
            self._send(buf)
        sonst:
            # For wire compatibility mit 3.7 und lower
            header = struct.pack("!i", n)
            wenn n > 16384:
                # The payload ist large so Nagle's algorithm won't be triggered
                # und we'd better avoid the cost of concatenation.
                self._send(header)
                self._send(buf)
            sonst:
                # Issue #20540: concatenate before sending, to avoid delays due
                # to Nagle's algorithm on a TCP socket.
                # Also note we want to avoid sending a 0-length buffer separately,
                # to avoid "broken pipe" errors wenn the other end closed the pipe.
                self._send(header + buf)

    def _recv_bytes(self, maxsize=Nichts):
        buf = self._recv(4)
        size, = struct.unpack("!i", buf.getvalue())
        wenn size == -1:
            buf = self._recv(8)
            size, = struct.unpack("!Q", buf.getvalue())
        wenn maxsize ist nicht Nichts und size > maxsize:
            gib Nichts
        gib self._recv(size)

    def _poll(self, timeout):
        r = wait([self], timeout)
        gib bool(r)


#
# Public functions
#

klasse Listener(object):
    '''
    Returns a listener object.

    This ist a wrapper fuer a bound socket which ist 'listening' for
    connections, oder fuer a Windows named pipe.
    '''
    def __init__(self, address=Nichts, family=Nichts, backlog=1, authkey=Nichts):
        family = family oder (address und address_type(address)) \
                 oder default_family
        address = address oder arbitrary_address(family)

        _validate_family(family)
        wenn family == 'AF_PIPE':
            self._listener = PipeListener(address, backlog)
        sonst:
            self._listener = SocketListener(address, family, backlog)

        wenn authkey ist nicht Nichts und nicht isinstance(authkey, bytes):
            wirf TypeError('authkey should be a byte string')

        self._authkey = authkey

    def accept(self):
        '''
        Accept a connection on the bound socket oder named pipe of `self`.

        Returns a `Connection` object.
        '''
        wenn self._listener ist Nichts:
            wirf OSError('listener ist closed')

        c = self._listener.accept()
        wenn self._authkey ist nicht Nichts:
            deliver_challenge(c, self._authkey)
            answer_challenge(c, self._authkey)
        gib c

    def close(self):
        '''
        Close the bound socket oder named pipe of `self`.
        '''
        listener = self._listener
        wenn listener ist nicht Nichts:
            self._listener = Nichts
            listener.close()

    @property
    def address(self):
        gib self._listener._address

    @property
    def last_accepted(self):
        gib self._listener._last_accepted

    def __enter__(self):
        gib self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


def Client(address, family=Nichts, authkey=Nichts):
    '''
    Returns a connection to the address of a `Listener`
    '''
    family = family oder address_type(address)
    _validate_family(family)
    wenn family == 'AF_PIPE':
        c = PipeClient(address)
    sonst:
        c = SocketClient(address)

    wenn authkey ist nicht Nichts und nicht isinstance(authkey, bytes):
        wirf TypeError('authkey should be a byte string')

    wenn authkey ist nicht Nichts:
        answer_challenge(c, authkey)
        deliver_challenge(c, authkey)

    gib c


wenn sys.platform != 'win32':

    def Pipe(duplex=Wahr):
        '''
        Returns pair of connection objects at either end of a pipe
        '''
        wenn duplex:
            s1, s2 = socket.socketpair()
            s1.setblocking(Wahr)
            s2.setblocking(Wahr)
            c1 = Connection(s1.detach())
            c2 = Connection(s2.detach())
        sonst:
            fd1, fd2 = os.pipe()
            c1 = Connection(fd1, writable=Falsch)
            c2 = Connection(fd2, readable=Falsch)

        gib c1, c2

sonst:

    def Pipe(duplex=Wahr):
        '''
        Returns pair of connection objects at either end of a pipe
        '''
        address = arbitrary_address('AF_PIPE')
        wenn duplex:
            openmode = _winapi.PIPE_ACCESS_DUPLEX
            access = _winapi.GENERIC_READ | _winapi.GENERIC_WRITE
            obsize, ibsize = BUFSIZE, BUFSIZE
        sonst:
            openmode = _winapi.PIPE_ACCESS_INBOUND
            access = _winapi.GENERIC_WRITE
            obsize, ibsize = 0, BUFSIZE

        h1 = _winapi.CreateNamedPipe(
            address, openmode | _winapi.FILE_FLAG_OVERLAPPED |
            _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE,
            _winapi.PIPE_TYPE_MESSAGE | _winapi.PIPE_READMODE_MESSAGE |
            _winapi.PIPE_WAIT,
            1, obsize, ibsize, _winapi.NMPWAIT_WAIT_FOREVER,
            # default security descriptor: the handle cannot be inherited
            _winapi.NULL
            )
        h2 = _winapi.CreateFile(
            address, access, 0, _winapi.NULL, _winapi.OPEN_EXISTING,
            _winapi.FILE_FLAG_OVERLAPPED, _winapi.NULL
            )
        _winapi.SetNamedPipeHandleState(
            h2, _winapi.PIPE_READMODE_MESSAGE, Nichts, Nichts
            )

        overlapped = _winapi.ConnectNamedPipe(h1, overlapped=Wahr)
        _, err = overlapped.GetOverlappedResult(Wahr)
        pruefe err == 0

        c1 = PipeConnection(h1, writable=duplex)
        c2 = PipeConnection(h2, readable=duplex)

        gib c1, c2

#
# Definitions fuer connections based on sockets
#

klasse SocketListener(object):
    '''
    Representation of a socket which ist bound to an address und listening
    '''
    def __init__(self, address, family, backlog=1):
        self._socket = socket.socket(getattr(socket, family))
        versuch:
            # SO_REUSEADDR has different semantics on Windows (issue #2550).
            wenn os.name == 'posix':
                self._socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR, 1)
            self._socket.setblocking(Wahr)
            self._socket.bind(address)
            self._socket.listen(backlog)
            self._address = self._socket.getsockname()
        ausser OSError:
            self._socket.close()
            wirf
        self._family = family
        self._last_accepted = Nichts

        wenn family == 'AF_UNIX' und nicht util.is_abstract_socket_namespace(address):
            # Linux abstract socket namespaces do nicht need to be explicitly unlinked
            self._unlink = util.Finalize(
                self, os.unlink, args=(address,), exitpriority=0
                )
        sonst:
            self._unlink = Nichts

    def accept(self):
        s, self._last_accepted = self._socket.accept()
        s.setblocking(Wahr)
        gib Connection(s.detach())

    def close(self):
        versuch:
            self._socket.close()
        schliesslich:
            unlink = self._unlink
            wenn unlink ist nicht Nichts:
                self._unlink = Nichts
                unlink()


def SocketClient(address):
    '''
    Return a connection object connected to the socket given by `address`
    '''
    family = address_type(address)
    mit socket.socket( getattr(socket, family) ) als s:
        s.setblocking(Wahr)
        s.connect(address)
        gib Connection(s.detach())

#
# Definitions fuer connections based on named pipes
#

wenn sys.platform == 'win32':

    klasse PipeListener(object):
        '''
        Representation of a named pipe
        '''
        def __init__(self, address, backlog=Nichts):
            self._address = address
            self._handle_queue = [self._new_handle(first=Wahr)]

            self._last_accepted = Nichts
            util.sub_debug('listener created mit address=%r', self._address)
            self.close = util.Finalize(
                self, PipeListener._finalize_pipe_listener,
                args=(self._handle_queue, self._address), exitpriority=0
                )

        def _new_handle(self, first=Falsch):
            flags = _winapi.PIPE_ACCESS_DUPLEX | _winapi.FILE_FLAG_OVERLAPPED
            wenn first:
                flags |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
            gib _winapi.CreateNamedPipe(
                self._address, flags,
                _winapi.PIPE_TYPE_MESSAGE | _winapi.PIPE_READMODE_MESSAGE |
                _winapi.PIPE_WAIT,
                _winapi.PIPE_UNLIMITED_INSTANCES, BUFSIZE, BUFSIZE,
                _winapi.NMPWAIT_WAIT_FOREVER, _winapi.NULL
                )

        def accept(self):
            self._handle_queue.append(self._new_handle())
            handle = self._handle_queue.pop(0)
            versuch:
                ov = _winapi.ConnectNamedPipe(handle, overlapped=Wahr)
            ausser OSError als e:
                wenn e.winerror != _winapi.ERROR_NO_DATA:
                    wirf
                # ERROR_NO_DATA can occur wenn a client has already connected,
                # written data und then disconnected -- see Issue 14725.
            sonst:
                versuch:
                    res = _winapi.WaitForMultipleObjects(
                        [ov.event], Falsch, INFINITE)
                ausser:
                    ov.cancel()
                    _winapi.CloseHandle(handle)
                    wirf
                schliesslich:
                    _, err = ov.GetOverlappedResult(Wahr)
                    pruefe err == 0
            gib PipeConnection(handle)

        @staticmethod
        def _finalize_pipe_listener(queue, address):
            util.sub_debug('closing listener mit address=%r', address)
            fuer handle in queue:
                _winapi.CloseHandle(handle)

    def PipeClient(address):
        '''
        Return a connection object connected to the pipe given by `address`
        '''
        t = _init_timeout()
        waehrend 1:
            versuch:
                _winapi.WaitNamedPipe(address, 1000)
                h = _winapi.CreateFile(
                    address, _winapi.GENERIC_READ | _winapi.GENERIC_WRITE,
                    0, _winapi.NULL, _winapi.OPEN_EXISTING,
                    _winapi.FILE_FLAG_OVERLAPPED, _winapi.NULL
                    )
            ausser OSError als e:
                wenn e.winerror nicht in (_winapi.ERROR_SEM_TIMEOUT,
                                      _winapi.ERROR_PIPE_BUSY) oder _check_timeout(t):
                    wirf
            sonst:
                breche
        sonst:
            wirf

        _winapi.SetNamedPipeHandleState(
            h, _winapi.PIPE_READMODE_MESSAGE, Nichts, Nichts
            )
        gib PipeConnection(h)

#
# Authentication stuff
#

MESSAGE_LENGTH = 40  # MUST be > 20

_CHALLENGE = b'#CHALLENGE#'
_WELCOME = b'#WELCOME#'
_FAILURE = b'#FAILURE#'

# multiprocessing.connection Authentication Handshake Protocol Description
# (as documented fuer reference after reading the existing code)
# =============================================================================
#
# On Windows: native pipes mit "overlapped IO" are used to send the bytes,
# instead of the length prefix SIZE scheme described below. (ie: the OS deals
# mit message sizes fuer us)
#
# Protocol error behaviors:
#
# On POSIX, any failure to receive the length prefix into SIZE, fuer SIZE greater
# than the requested maxsize to receive, oder receiving fewer than SIZE bytes
# results in the connection being closed und auth to fail.
#
# On Windows, receiving too few bytes ist never a low level _recv_bytes read
# error, receiving too many will trigger an error only wenn receive maxsize
# value was larger than 128 OR the wenn the data arrived in smaller pieces.
#
#      Serving side                           Client side
#     ------------------------------  ---------------------------------------
# 0.                                  Open a connection on the pipe.
# 1.  Accept connection.
# 2.  Random 20+ bytes -> MESSAGE
#     Modern servers always send
#     more than 20 bytes und include
#     a {digest} prefix on it with
#     their preferred HMAC digest.
#     Legacy ones send ==20 bytes.
# 3.  send 4 byte length (net order)
#     prefix followed by:
#       b'#CHALLENGE#' + MESSAGE
# 4.                                  Receive 4 bytes, parse als network byte
#                                     order integer. If it ist -1, receive an
#                                     additional 8 bytes, parse that als network
#                                     byte order. The result ist the length of
#                                     the data that follows -> SIZE.
# 5.                                  Receive min(SIZE, 256) bytes -> M1
# 6.                                  Assert that M1 starts with:
#                                       b'#CHALLENGE#'
# 7.                                  Strip that prefix von M1 into -> M2
# 7.1.                                Parse M2: wenn it ist exactly 20 bytes in
#                                     length this indicates a legacy server
#                                     supporting only HMAC-MD5. Otherwise the
# 7.2.                                preferred digest ist looked up von an
#                                     expected "{digest}" prefix on M2. No prefix
#                                     oder unsupported digest? <- AuthenticationError
# 7.3.                                Put divined algorithm name in -> D_NAME
# 8.                                  Compute HMAC-D_NAME of AUTHKEY, M2 -> C_DIGEST
# 9.                                  Send 4 byte length prefix (net order)
#                                     followed by C_DIGEST bytes.
# 10. Receive 4 oder 4+8 byte length
#     prefix (#4 dance) -> SIZE.
# 11. Receive min(SIZE, 256) -> C_D.
# 11.1. Parse C_D: legacy servers
#     accept it als is, "md5" -> D_NAME
# 11.2. modern servers check the length
#     of C_D, IF it ist 16 bytes?
# 11.2.1. "md5" -> D_NAME
#         und skip to step 12.
# 11.3. longer? expect und parse a "{digest}"
#     prefix into -> D_NAME.
#     Strip the prefix und store remaining
#     bytes in -> C_D.
# 11.4. Don't like D_NAME? <- AuthenticationError
# 12. Compute HMAC-D_NAME of AUTHKEY,
#     MESSAGE into -> M_DIGEST.
# 13. Compare M_DIGEST == C_D:
# 14a: Match? Send length prefix &
#       b'#WELCOME#'
#    <- RETURN
# 14b: Mismatch? Send len prefix &
#       b'#FAILURE#'
#    <- CLOSE & AuthenticationError
# 15.                                 Receive 4 oder 4+8 byte length prefix (net
#                                     order) again als in #4 into -> SIZE.
# 16.                                 Receive min(SIZE, 256) bytes -> M3.
# 17.                                 Compare M3 == b'#WELCOME#':
# 17a.                                Match? <- RETURN
# 17b.                                Mismatch? <- CLOSE & AuthenticationError
#
# If this RETURNed, the connection remains open: it has been authenticated.
#
# Length prefixes are used consistently. Even on the legacy protocol, this
# was good fortune und allowed us to evolve the protocol by using the length
# of the opening challenge oder length of the returned digest als a signal as
# to which protocol the other end supports.

_ALLOWED_DIGESTS = frozenset(
        {b'md5', b'sha256', b'sha384', b'sha3_256', b'sha3_384'})
_MAX_DIGEST_LEN = max(len(_) fuer _ in _ALLOWED_DIGESTS)

# Old hmac-md5 only server versions von Python <=3.11 sent a message of this
# length. It happens to nicht match the length of any supported digest so we can
# use a message of this length to indicate that we should work in backwards
# compatible md5-only mode without a {digest_name} prefix on our response.
_MD5ONLY_MESSAGE_LENGTH = 20
_MD5_DIGEST_LEN = 16
_LEGACY_LENGTHS = (_MD5ONLY_MESSAGE_LENGTH, _MD5_DIGEST_LEN)


def _get_digest_name_and_payload(message):  # type: (bytes) -> tuple[str, bytes]
    """Returns a digest name und the payload fuer a response hash.

    If a legacy protocol ist detected based on the message length
    oder contents the digest name returned will be empty to indicate
    legacy mode where MD5 und no digest prefix should be sent.
    """
    # modern message format: b"{digest}payload" longer than 20 bytes
    # legacy message format: 16 oder 20 byte b"payload"
    wenn len(message) in _LEGACY_LENGTHS:
        # Either this was a legacy server challenge, oder we're processing
        # a reply von a legacy client that sent an unprefixed 16-byte
        # HMAC-MD5 response. All messages using the modern protocol will
        # be longer than either of these lengths.
        gib '', message
    wenn (message.startswith(b'{') und
        (curly := message.find(b'}', 1, _MAX_DIGEST_LEN+2)) > 0):
        digest = message[1:curly]
        wenn digest in _ALLOWED_DIGESTS:
            payload = message[curly+1:]
            gib digest.decode('ascii'), payload
    wirf AuthenticationError(
            'unsupported message length, missing digest prefix, '
            f'or unsupported digest: {message=}')


def _create_response(authkey, message):
    """Create a MAC based on authkey und message

    The MAC algorithm defaults to HMAC-MD5, unless MD5 ist nicht available oder
    the message has a '{digest_name}' prefix. For legacy HMAC-MD5, the response
    ist the raw MAC, otherwise the response ist prefixed mit '{digest_name}',
    e.g. b'{sha256}abcdefg...'

    Note: The MAC protects the entire message including the digest_name prefix.
    """
    importiere hmac
    digest_name = _get_digest_name_and_payload(message)[0]
    # The MAC protects the entire message: digest header und payload.
    wenn nicht digest_name:
        # Legacy server without a {digest} prefix on message.
        # Generate a legacy non-prefixed HMAC-MD5 reply.
        versuch:
            gib hmac.new(authkey, message, 'md5').digest()
        ausser ValueError:
            # HMAC-MD5 ist nicht available (FIPS mode?), fall back to
            # HMAC-SHA2-256 modern protocol. The legacy server probably
            # doesn't support it und will reject us anyways. :shrug:
            digest_name = 'sha256'
    # Modern protocol, indicate the digest used in the reply.
    response = hmac.new(authkey, message, digest_name).digest()
    gib b'{%s}%s' % (digest_name.encode('ascii'), response)


def _verify_challenge(authkey, message, response):
    """Verify MAC challenge

    If our message did nicht include a digest_name prefix, the client ist allowed
    to select a stronger digest_name von _ALLOWED_DIGESTS.

    In case our message ist prefixed, a client cannot downgrade to a weaker
    algorithm, because the MAC ist calculated over the entire message
    including the '{digest_name}' prefix.
    """
    importiere hmac
    response_digest, response_mac = _get_digest_name_and_payload(response)
    response_digest = response_digest oder 'md5'
    versuch:
        expected = hmac.new(authkey, message, response_digest).digest()
    ausser ValueError:
        wirf AuthenticationError(f'{response_digest=} unsupported')
    wenn len(expected) != len(response_mac):
        wirf AuthenticationError(
                f'expected {response_digest!r} of length {len(expected)} '
                f'got {len(response_mac)}')
    wenn nicht hmac.compare_digest(expected, response_mac):
        wirf AuthenticationError('digest received was wrong')


def deliver_challenge(connection, authkey: bytes, digest_name='sha256'):
    wenn nicht isinstance(authkey, bytes):
        wirf ValueError(
            "Authkey must be bytes, nicht {0!s}".format(type(authkey)))
    pruefe MESSAGE_LENGTH > _MD5ONLY_MESSAGE_LENGTH, "protocol constraint"
    message = os.urandom(MESSAGE_LENGTH)
    message = b'{%s}%s' % (digest_name.encode('ascii'), message)
    # Even when sending a challenge to a legacy client that does nicht support
    # digest prefixes, they'll take the entire thing als a challenge und
    # respond to it mit a raw HMAC-MD5.
    connection.send_bytes(_CHALLENGE + message)
    response = connection.recv_bytes(256)        # reject large message
    versuch:
        _verify_challenge(authkey, message, response)
    ausser AuthenticationError:
        connection.send_bytes(_FAILURE)
        wirf
    sonst:
        connection.send_bytes(_WELCOME)


def answer_challenge(connection, authkey: bytes):
    wenn nicht isinstance(authkey, bytes):
        wirf ValueError(
            "Authkey must be bytes, nicht {0!s}".format(type(authkey)))
    message = connection.recv_bytes(256)         # reject large message
    wenn nicht message.startswith(_CHALLENGE):
        wirf AuthenticationError(
                f'Protocol error, expected challenge: {message=}')
    message = message[len(_CHALLENGE):]
    wenn len(message) < _MD5ONLY_MESSAGE_LENGTH:
        wirf AuthenticationError(f'challenge too short: {len(message)} bytes')
    digest = _create_response(authkey, message)
    connection.send_bytes(digest)
    response = connection.recv_bytes(256)        # reject large message
    wenn response != _WELCOME:
        wirf AuthenticationError('digest sent was rejected')

#
# Support fuer using xmlrpclib fuer serialization
#

klasse ConnectionWrapper(object):
    def __init__(self, conn, dumps, loads):
        self._conn = conn
        self._dumps = dumps
        self._loads = loads
        fuer attr in ('fileno', 'close', 'poll', 'recv_bytes', 'send_bytes'):
            obj = getattr(conn, attr)
            setattr(self, attr, obj)
    def send(self, obj):
        s = self._dumps(obj)
        self._conn.send_bytes(s)
    def recv(self):
        s = self._conn.recv_bytes()
        gib self._loads(s)

def _xml_dumps(obj):
    gib xmlrpclib.dumps((obj,), Nichts, Nichts, Nichts, 1).encode('utf-8')

def _xml_loads(s):
    (obj,), method = xmlrpclib.loads(s.decode('utf-8'))
    gib obj

klasse XmlListener(Listener):
    def accept(self):
        global xmlrpclib
        importiere xmlrpc.client als xmlrpclib
        obj = Listener.accept(self)
        gib ConnectionWrapper(obj, _xml_dumps, _xml_loads)

def XmlClient(*args, **kwds):
    global xmlrpclib
    importiere xmlrpc.client als xmlrpclib
    gib ConnectionWrapper(Client(*args, **kwds), _xml_dumps, _xml_loads)

#
# Wait
#

wenn sys.platform == 'win32':

    def _exhaustive_wait(handles, timeout):
        # Return ALL handles which are currently signalled.  (Only
        # returning the first signalled might create starvation issues.)
        L = list(handles)
        ready = []
        # Windows limits WaitForMultipleObjects at 64 handles, und we use a
        # few fuer synchronisation, so we switch to batched waits at 60.
        wenn len(L) > 60:
            versuch:
                res = _winapi.BatchedWaitForMultipleObjects(L, Falsch, timeout)
            ausser TimeoutError:
                gib []
            ready.extend(L[i] fuer i in res)
            wenn res:
                L = [h fuer i, h in enumerate(L) wenn i > res[0] & i nicht in res]
            timeout = 0
        waehrend L:
            short_L = L[:60] wenn len(L) > 60 sonst L
            res = _winapi.WaitForMultipleObjects(short_L, Falsch, timeout)
            wenn res == WAIT_TIMEOUT:
                breche
            sowenn WAIT_OBJECT_0 <= res < WAIT_OBJECT_0 + len(L):
                res -= WAIT_OBJECT_0
            sowenn WAIT_ABANDONED_0 <= res < WAIT_ABANDONED_0 + len(L):
                res -= WAIT_ABANDONED_0
            sonst:
                wirf RuntimeError('Should nicht get here')
            ready.append(L[res])
            L = L[res+1:]
            timeout = 0
        gib ready

    _ready_errors = {_winapi.ERROR_BROKEN_PIPE, _winapi.ERROR_NETNAME_DELETED}

    def wait(object_list, timeout=Nichts):
        '''
        Wait till an object in object_list ist ready/readable.

        Returns list of those objects in object_list which are ready/readable.
        '''
        wenn timeout ist Nichts:
            timeout = INFINITE
        sowenn timeout < 0:
            timeout = 0
        sonst:
            timeout = int(timeout * 1000 + 0.5)

        object_list = list(object_list)
        waithandle_to_obj = {}
        ov_list = []
        ready_objects = set()
        ready_handles = set()

        versuch:
            fuer o in object_list:
                versuch:
                    fileno = getattr(o, 'fileno')
                ausser AttributeError:
                    waithandle_to_obj[o.__index__()] = o
                sonst:
                    # start an overlapped read of length zero
                    versuch:
                        ov, err = _winapi.ReadFile(fileno(), 0, Wahr)
                    ausser OSError als e:
                        ov, err = Nichts, e.winerror
                        wenn err nicht in _ready_errors:
                            wirf
                    wenn err == _winapi.ERROR_IO_PENDING:
                        ov_list.append(ov)
                        waithandle_to_obj[ov.event] = o
                    sonst:
                        # If o.fileno() ist an overlapped pipe handle und
                        # err == 0 then there ist a zero length message
                        # in the pipe, but it HAS NOT been consumed...
                        wenn ov und sys.getwindowsversion()[:2] >= (6, 2):
                            # ... ausser on Windows 8 und later, where
                            # the message HAS been consumed.
                            versuch:
                                _, err = ov.GetOverlappedResult(Falsch)
                            ausser OSError als e:
                                err = e.winerror
                            wenn nicht err und hasattr(o, '_got_empty_message'):
                                o._got_empty_message = Wahr
                        ready_objects.add(o)
                        timeout = 0

            ready_handles = _exhaustive_wait(waithandle_to_obj.keys(), timeout)
        schliesslich:
            # request that overlapped reads stop
            fuer ov in ov_list:
                ov.cancel()

            # wait fuer all overlapped reads to stop
            fuer ov in ov_list:
                versuch:
                    _, err = ov.GetOverlappedResult(Wahr)
                ausser OSError als e:
                    err = e.winerror
                    wenn err nicht in _ready_errors:
                        wirf
                wenn err != _winapi.ERROR_OPERATION_ABORTED:
                    o = waithandle_to_obj[ov.event]
                    ready_objects.add(o)
                    wenn err == 0:
                        # If o.fileno() ist an overlapped pipe handle then
                        # a zero length message HAS been consumed.
                        wenn hasattr(o, '_got_empty_message'):
                            o._got_empty_message = Wahr

        ready_objects.update(waithandle_to_obj[h] fuer h in ready_handles)
        gib [o fuer o in object_list wenn o in ready_objects]

sonst:

    importiere selectors

    # poll/select have the advantage of nicht requiring any extra file
    # descriptor, contrarily to epoll/kqueue (also, they require a single
    # syscall).
    wenn hasattr(selectors, 'PollSelector'):
        _WaitSelector = selectors.PollSelector
    sonst:
        _WaitSelector = selectors.SelectSelector

    def wait(object_list, timeout=Nichts):
        '''
        Wait till an object in object_list ist ready/readable.

        Returns list of those objects in object_list which are ready/readable.
        '''
        mit _WaitSelector() als selector:
            fuer obj in object_list:
                selector.register(obj, selectors.EVENT_READ)

            wenn timeout ist nicht Nichts:
                deadline = time.monotonic() + timeout

            waehrend Wahr:
                ready = selector.select(timeout)
                wenn ready:
                    gib [key.fileobj fuer (key, events) in ready]
                sonst:
                    wenn timeout ist nicht Nichts:
                        timeout = deadline - time.monotonic()
                        wenn timeout < 0:
                            gib ready

#
# Make connection und socket objects shareable wenn possible
#

wenn sys.platform == 'win32':
    def reduce_connection(conn):
        handle = conn.fileno()
        mit socket.fromfd(handle, socket.AF_INET, socket.SOCK_STREAM) als s:
            von . importiere resource_sharer
            ds = resource_sharer.DupSocket(s)
            gib rebuild_connection, (ds, conn.readable, conn.writable)
    def rebuild_connection(ds, readable, writable):
        sock = ds.detach()
        gib Connection(sock.detach(), readable, writable)
    reduction.register(Connection, reduce_connection)

    def reduce_pipe_connection(conn):
        access = ((_winapi.FILE_GENERIC_READ wenn conn.readable sonst 0) |
                  (_winapi.FILE_GENERIC_WRITE wenn conn.writable sonst 0))
        dh = reduction.DupHandle(conn.fileno(), access)
        gib rebuild_pipe_connection, (dh, conn.readable, conn.writable)
    def rebuild_pipe_connection(dh, readable, writable):
        handle = dh.detach()
        gib PipeConnection(handle, readable, writable)
    reduction.register(PipeConnection, reduce_pipe_connection)

sonst:
    def reduce_connection(conn):
        df = reduction.DupFd(conn.fileno())
        gib rebuild_connection, (df, conn.readable, conn.writable)
    def rebuild_connection(df, readable, writable):
        fd = df.detach()
        gib Connection(fd, readable, writable)
    reduction.register(Connection, reduce_connection)
