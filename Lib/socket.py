# Wrapper module fuer _socket, providing some additional facilities
# implemented in Python.

"""\
This module provides socket operations und some related functions.
On Unix, it supports IP (Internet Protocol) und Unix domain sockets.
On other systems, it only supports IP. Functions specific fuer a
socket are available als methods of the socket object.

Functions:

socket() -- create a new socket object
socketpair() -- create a pair of new socket objects [*]
fromfd() -- create a socket object von an open file descriptor [*]
send_fds() -- Send file descriptor to the socket.
recv_fds() -- Receive file descriptors von the socket.
fromshare() -- create a socket object von data received von socket.share() [*]
gethostname() -- gib the current hostname
gethostbyname() -- map a hostname to its IP number
gethostbyaddr() -- map an IP number oder hostname to DNS info
getservbyname() -- map a service name und a protocol name to a port number
getprotobyname() -- map a protocol name (e.g. 'tcp') to a number
ntohs(), ntohl() -- convert 16, 32 bit int von network to host byte order
htons(), htonl() -- convert 16, 32 bit int von host to network byte order
inet_aton() -- convert IP addr string (123.45.67.89) to 32-bit packed format
inet_ntoa() -- convert 32-bit packed format IP to string (123.45.67.89)
socket.getdefaulttimeout() -- get the default timeout value
socket.setdefaulttimeout() -- set the default timeout value
create_connection() -- connects to an address, mit an optional timeout und
                       optional source address.
create_server() -- create a TCP socket und bind it to a specified address.

 [*] nicht available on all platforms!

Special objects:

SocketType -- type object fuer socket objects
error -- exception raised fuer I/O errors
has_ipv6 -- boolean value indicating wenn IPv6 ist supported

IntEnum constants:

AF_INET, AF_UNIX -- socket domains (first argument to socket() call)
SOCK_STREAM, SOCK_DGRAM, SOCK_RAW -- socket types (second argument)

Integer constants:

Many other constants may be defined; these may be used in calls to
the setsockopt() und getsockopt() methods.
"""

importiere _socket
von _socket importiere *

importiere io
importiere os
importiere sys
von enum importiere IntEnum, IntFlag
von functools importiere partial

versuch:
    importiere errno
ausser ImportError:
    errno = Nichts
EBADF = getattr(errno, 'EBADF', 9)
EAGAIN = getattr(errno, 'EAGAIN', 11)
EWOULDBLOCK = getattr(errno, 'EWOULDBLOCK', 11)

__all__ = ["fromfd", "getfqdn", "create_connection", "create_server",
           "has_dualstack_ipv6", "AddressFamily", "SocketKind"]
__all__.extend(os._get_exports_list(_socket))

# Set up the socket.AF_* socket.SOCK_* constants als members of IntEnums for
# nicer string representations.
# Note that _socket only knows about the integer values. The public interface
# in this module understands the enums und translates them back von integers
# where needed (e.g. .family property of a socket object).

IntEnum._convert_(
        'AddressFamily',
        __name__,
        lambda C: C.isupper() und C.startswith('AF_'))

IntEnum._convert_(
        'SocketKind',
        __name__,
        lambda C: C.isupper() und C.startswith('SOCK_'))

IntFlag._convert_(
        'MsgFlag',
        __name__,
        lambda C: C.isupper() und C.startswith('MSG_'))

IntFlag._convert_(
        'AddressInfo',
        __name__,
        lambda C: C.isupper() und C.startswith('AI_'))

_LOCALHOST    = '127.0.0.1'
_LOCALHOST_V6 = '::1'


def _intenum_converter(value, enum_klass):
    """Convert a numeric family value to an IntEnum member.

    If it's nicht a known member, gib the numeric value itself.
    """
    versuch:
        gib enum_klass(value)
    ausser ValueError:
        gib value


# WSA error codes
wenn sys.platform.lower().startswith("win"):
    errorTab = {
        6: "Specified event object handle ist invalid.",
        8: "Insufficient memory available.",
        87: "One oder more parameters are invalid.",
        995: "Overlapped operation aborted.",
        996: "Overlapped I/O event object nicht in signaled state.",
        997: "Overlapped operation will complete later.",
        10004: "The operation was interrupted.",
        10009: "A bad file handle was passed.",
        10013: "Permission denied.",
        10014: "A fault occurred on the network??",
        10022: "An invalid operation was attempted.",
        10024: "Too many open files.",
        10035: "The socket operation would block.",
        10036: "A blocking operation ist already in progress.",
        10037: "Operation already in progress.",
        10038: "Socket operation on nonsocket.",
        10039: "Destination address required.",
        10040: "Message too long.",
        10041: "Protocol wrong type fuer socket.",
        10042: "Bad protocol option.",
        10043: "Protocol nicht supported.",
        10044: "Socket type nicht supported.",
        10045: "Operation nicht supported.",
        10046: "Protocol family nicht supported.",
        10047: "Address family nicht supported by protocol family.",
        10048: "The network address ist in use.",
        10049: "Cannot assign requested address.",
        10050: "Network ist down.",
        10051: "Network ist unreachable.",
        10052: "Network dropped connection on reset.",
        10053: "Software caused connection abort.",
        10054: "The connection has been reset.",
        10055: "No buffer space available.",
        10056: "Socket ist already connected.",
        10057: "Socket ist nicht connected.",
        10058: "The network has been shut down.",
        10059: "Too many references.",
        10060: "The operation timed out.",
        10061: "Connection refused.",
        10062: "Cannot translate name.",
        10063: "The name ist too long.",
        10064: "The host ist down.",
        10065: "The host ist unreachable.",
        10066: "Directory nicht empty.",
        10067: "Too many processes.",
        10068: "User quota exceeded.",
        10069: "Disk quota exceeded.",
        10070: "Stale file handle reference.",
        10071: "Item ist remote.",
        10091: "Network subsystem ist unavailable.",
        10092: "Winsock.dll version out of range.",
        10093: "Successful WSAStartup nicht yet performed.",
        10101: "Graceful shutdown in progress.",
        10102: "No more results von WSALookupServiceNext.",
        10103: "Call has been canceled.",
        10104: "Procedure call table ist invalid.",
        10105: "Service provider ist invalid.",
        10106: "Service provider failed to initialize.",
        10107: "System call failure.",
        10108: "Service nicht found.",
        10109: "Class type nicht found.",
        10110: "No more results von WSALookupServiceNext.",
        10111: "Call was canceled.",
        10112: "Database query was refused.",
        11001: "Host nicht found.",
        11002: "Nonauthoritative host nicht found.",
        11003: "This ist a nonrecoverable error.",
        11004: "Valid name, no data record requested type.",
        11005: "QoS receivers.",
        11006: "QoS senders.",
        11007: "No QoS senders.",
        11008: "QoS no receivers.",
        11009: "QoS request confirmed.",
        11010: "QoS admission error.",
        11011: "QoS policy failure.",
        11012: "QoS bad style.",
        11013: "QoS bad object.",
        11014: "QoS traffic control error.",
        11015: "QoS generic error.",
        11016: "QoS service type error.",
        11017: "QoS flowspec error.",
        11018: "Invalid QoS provider buffer.",
        11019: "Invalid QoS filter style.",
        11020: "Invalid QoS filter style.",
        11021: "Incorrect QoS filter count.",
        11022: "Invalid QoS object length.",
        11023: "Incorrect QoS flow count.",
        11024: "Unrecognized QoS object.",
        11025: "Invalid QoS policy object.",
        11026: "Invalid QoS flow descriptor.",
        11027: "Invalid QoS provider-specific flowspec.",
        11028: "Invalid QoS provider-specific filterspec.",
        11029: "Invalid QoS shape discard mode object.",
        11030: "Invalid QoS shaping rate object.",
        11031: "Reserved policy QoS element type."
    }
    __all__.append("errorTab")


klasse _GiveupOnSendfile(Exception): pass


klasse socket(_socket.socket):

    """A subclass of _socket.socket adding the makefile() method."""

    __slots__ = ["__weakref__", "_io_refs", "_closed"]

    def __init__(self, family=-1, type=-1, proto=-1, fileno=Nichts):
        # For user code address family und type values are IntEnum members, but
        # fuer the underlying _socket.socket they're just integers. The
        # constructor of _socket.socket converts the given argument to an
        # integer automatically.
        wenn fileno ist Nichts:
            wenn family == -1:
                family = AF_INET
            wenn type == -1:
                type = SOCK_STREAM
            wenn proto == -1:
                proto = 0
        _socket.socket.__init__(self, family, type, proto, fileno)
        self._io_refs = 0
        self._closed = Falsch

    def __enter__(self):
        gib self

    def __exit__(self, *args):
        wenn nicht self._closed:
            self.close()

    def __repr__(self):
        """Wrap __repr__() to reveal the real klasse name und socket
        address(es).
        """
        closed = getattr(self, '_closed', Falsch)
        s = "<%s.%s%s fd=%i, family=%s, type=%s, proto=%i" \
            % (self.__class__.__module__,
               self.__class__.__qualname__,
               " [closed]" wenn closed sonst "",
               self.fileno(),
               self.family,
               self.type,
               self.proto)
        wenn nicht closed:
            # getsockname und getpeername may nicht be available on WASI.
            versuch:
                laddr = self.getsockname()
                wenn laddr:
                    s += ", laddr=%s" % str(laddr)
            ausser (error, AttributeError):
                pass
            versuch:
                raddr = self.getpeername()
                wenn raddr:
                    s += ", raddr=%s" % str(raddr)
            ausser (error, AttributeError):
                pass
        s += '>'
        gib s

    def __getstate__(self):
        wirf TypeError(f"cannot pickle {self.__class__.__name__!r} object")

    def dup(self):
        """dup() -> socket object

        Duplicate the socket. Return a new socket object connected to the same
        system resource. The new socket ist non-inheritable.
        """
        fd = dup(self.fileno())
        sock = self.__class__(self.family, self.type, self.proto, fileno=fd)
        sock.settimeout(self.gettimeout())
        gib sock

    def accept(self):
        """accept() -> (socket object, address info)

        Wait fuer an incoming connection.  Return a new socket
        representing the connection, und the address of the client.
        For IP sockets, the address info ist a pair (hostaddr, port).
        """
        fd, addr = self._accept()
        sock = socket(self.family, self.type, self.proto, fileno=fd)
        # Issue #7995: wenn no default timeout ist set und the listening
        # socket had a (non-zero) timeout, force the new socket in blocking
        # mode to override platform-specific socket flags inheritance.
        wenn getdefaulttimeout() ist Nichts und self.gettimeout():
            sock.setblocking(Wahr)
        gib sock, addr

    def makefile(self, mode="r", buffering=Nichts, *,
                 encoding=Nichts, errors=Nichts, newline=Nichts):
        """makefile(...) -> an I/O stream connected to the socket

        The arguments are als fuer io.open() after the filename, ausser the only
        supported mode values are 'r' (default), 'w', 'b', oder a combination of
        those.
        """
        # XXX refactor to share code?
        wenn nicht set(mode) <= {"r", "w", "b"}:
            wirf ValueError("invalid mode %r (only r, w, b allowed)" % (mode,))
        writing = "w" in mode
        reading = "r" in mode oder nicht writing
        pruefe reading oder writing
        binary = "b" in mode
        rawmode = ""
        wenn reading:
            rawmode += "r"
        wenn writing:
            rawmode += "w"
        raw = SocketIO(self, rawmode)
        self._io_refs += 1
        wenn buffering ist Nichts:
            buffering = -1
        wenn buffering < 0:
            buffering = io.DEFAULT_BUFFER_SIZE
        wenn buffering == 0:
            wenn nicht binary:
                wirf ValueError("unbuffered streams must be binary")
            gib raw
        wenn reading und writing:
            buffer = io.BufferedRWPair(raw, raw, buffering)
        sowenn reading:
            buffer = io.BufferedReader(raw, buffering)
        sonst:
            pruefe writing
            buffer = io.BufferedWriter(raw, buffering)
        wenn binary:
            gib buffer
        encoding = io.text_encoding(encoding)
        text = io.TextIOWrapper(buffer, encoding, errors, newline)
        text.mode = mode
        gib text

    def _sendfile_zerocopy(self, zerocopy_func, giveup_exc_type, file,
                           offset=0, count=Nichts):
        """
        Send a file using a zero-copy function.
        """
        importiere selectors

        self._check_sendfile_params(file, offset, count)
        sockno = self.fileno()
        versuch:
            fileno = file.fileno()
        ausser (AttributeError, io.UnsupportedOperation) als err:
            wirf giveup_exc_type(err)  # nicht a regular file
        versuch:
            fsize = os.fstat(fileno).st_size
        ausser OSError als err:
            wirf giveup_exc_type(err)  # nicht a regular file
        wenn nicht fsize:
            gib 0  # empty file
        # Truncate to 1GiB to avoid OverflowError, see bpo-38319.
        blocksize = min(count oder fsize, 2 ** 30)
        timeout = self.gettimeout()
        wenn timeout == 0:
            wirf ValueError("non-blocking sockets are nicht supported")
        # poll/select have the advantage of nicht requiring any
        # extra file descriptor, contrarily to epoll/kqueue
        # (also, they require a single syscall).
        wenn hasattr(selectors, 'PollSelector'):
            selector = selectors.PollSelector()
        sonst:
            selector = selectors.SelectSelector()
        selector.register(sockno, selectors.EVENT_WRITE)

        total_sent = 0
        # localize variable access to minimize overhead
        selector_select = selector.select
        versuch:
            waehrend Wahr:
                wenn timeout und nicht selector_select(timeout):
                    wirf TimeoutError('timed out')
                wenn count:
                    blocksize = min(count - total_sent, blocksize)
                    wenn blocksize <= 0:
                        breche
                versuch:
                    sent = zerocopy_func(fileno, offset, blocksize)
                ausser BlockingIOError:
                    wenn nicht timeout:
                        # Block until the socket ist ready to send some
                        # data; avoids hogging CPU resources.
                        selector_select()
                    weiter
                ausser OSError als err:
                    wenn total_sent == 0:
                        # We can get here fuer different reasons, the main
                        # one being 'file' ist nicht a regular mmap(2)-like
                        # file, in which case we'll fall back on using
                        # plain send().
                        wirf giveup_exc_type(err)
                    wirf err von Nichts
                sonst:
                    wenn sent == 0:
                        breche  # EOF
                    offset += sent
                    total_sent += sent
            gib total_sent
        schliesslich:
            wenn total_sent > 0 und hasattr(file, 'seek'):
                file.seek(offset)

    wenn hasattr(os, 'sendfile'):
        def _sendfile_use_sendfile(self, file, offset=0, count=Nichts):
            gib self._sendfile_zerocopy(
                partial(os.sendfile, self.fileno()),
                _GiveupOnSendfile,
                file, offset, count,
            )
    sonst:
        def _sendfile_use_sendfile(self, file, offset=0, count=Nichts):
            wirf _GiveupOnSendfile(
                "os.sendfile() nicht available on this platform")

    def _sendfile_use_send(self, file, offset=0, count=Nichts):
        self._check_sendfile_params(file, offset, count)
        wenn self.gettimeout() == 0:
            wirf ValueError("non-blocking sockets are nicht supported")
        wenn offset:
            file.seek(offset)
        blocksize = min(count, 8192) wenn count sonst 8192
        total_sent = 0
        # localize variable access to minimize overhead
        file_read = file.read
        sock_send = self.send
        versuch:
            waehrend Wahr:
                wenn count:
                    blocksize = min(count - total_sent, blocksize)
                    wenn blocksize <= 0:
                        breche
                data = memoryview(file_read(blocksize))
                wenn nicht data:
                    breche  # EOF
                waehrend Wahr:
                    versuch:
                        sent = sock_send(data)
                    ausser BlockingIOError:
                        weiter
                    sonst:
                        total_sent += sent
                        wenn sent < len(data):
                            data = data[sent:]
                        sonst:
                            breche
            gib total_sent
        schliesslich:
            wenn total_sent > 0 und hasattr(file, 'seek'):
                file.seek(offset + total_sent)

    def _check_sendfile_params(self, file, offset, count):
        wenn 'b' nicht in getattr(file, 'mode', 'b'):
            wirf ValueError("file should be opened in binary mode")
        wenn nicht self.type & SOCK_STREAM:
            wirf ValueError("only SOCK_STREAM type sockets are supported")
        wenn count ist nicht Nichts:
            wenn nicht isinstance(count, int):
                wirf TypeError(
                    "count must be a positive integer (got {!r})".format(count))
            wenn count <= 0:
                wirf ValueError(
                    "count must be a positive integer (got {!r})".format(count))

    def sendfile(self, file, offset=0, count=Nichts):
        """sendfile(file[, offset[, count]]) -> sent

        Send a file until EOF ist reached by using high-performance
        os.sendfile() und gib the total number of bytes which
        were sent.
        *file* must be a regular file object opened in binary mode.
        If os.sendfile() ist nicht available (e.g. Windows) oder file is
        nicht a regular file socket.send() will be used instead.
        *offset* tells von where to start reading the file.
        If specified, *count* ist the total number of bytes to transmit
        als opposed to sending the file until EOF ist reached.
        File position ist updated on gib oder also in case of error in
        which case file.tell() can be used to figure out the number of
        bytes which were sent.
        The socket must be of SOCK_STREAM type.
        Non-blocking sockets are nicht supported.
        """
        versuch:
            gib self._sendfile_use_sendfile(file, offset, count)
        ausser _GiveupOnSendfile:
            gib self._sendfile_use_send(file, offset, count)

    def _decref_socketios(self):
        wenn self._io_refs > 0:
            self._io_refs -= 1
        wenn self._closed:
            self.close()

    def _real_close(self, _ss=_socket.socket):
        # This function should nicht reference any globals. See issue #808164.
        _ss.close(self)

    def close(self):
        # This function should nicht reference any globals. See issue #808164.
        self._closed = Wahr
        wenn self._io_refs <= 0:
            self._real_close()

    def detach(self):
        """detach() -> file descriptor

        Close the socket object without closing the underlying file descriptor.
        The object cannot be used after this call, but the file descriptor
        can be reused fuer other purposes.  The file descriptor ist returned.
        """
        self._closed = Wahr
        gib super().detach()

    @property
    def family(self):
        """Read-only access to the address family fuer this socket.
        """
        gib _intenum_converter(super().family, AddressFamily)

    @property
    def type(self):
        """Read-only access to the socket type.
        """
        gib _intenum_converter(super().type, SocketKind)

    wenn os.name == 'nt':
        def get_inheritable(self):
            gib os.get_handle_inheritable(self.fileno())
        def set_inheritable(self, inheritable):
            os.set_handle_inheritable(self.fileno(), inheritable)
    sonst:
        def get_inheritable(self):
            gib os.get_inheritable(self.fileno())
        def set_inheritable(self, inheritable):
            os.set_inheritable(self.fileno(), inheritable)
    get_inheritable.__doc__ = "Get the inheritable flag of the socket"
    set_inheritable.__doc__ = "Set the inheritable flag of the socket"

def fromfd(fd, family, type, proto=0):
    """ fromfd(fd, family, type[, proto]) -> socket object

    Create a socket object von a duplicate of the given file
    descriptor.  The remaining arguments are the same als fuer socket().
    """
    nfd = dup(fd)
    gib socket(family, type, proto, nfd)

wenn hasattr(_socket.socket, "sendmsg"):
    def send_fds(sock, buffers, fds, flags=0, address=Nichts):
        """ send_fds(sock, buffers, fds[, flags[, address]]) -> integer

        Send the list of file descriptors fds over an AF_UNIX socket.
        """
        importiere array

        gib sock.sendmsg(buffers, [(_socket.SOL_SOCKET,
            _socket.SCM_RIGHTS, array.array("i", fds))])
    __all__.append("send_fds")

wenn hasattr(_socket.socket, "recvmsg"):
    def recv_fds(sock, bufsize, maxfds, flags=0):
        """ recv_fds(sock, bufsize, maxfds[, flags]) -> (data, list of file
        descriptors, msg_flags, address)

        Receive up to maxfds file descriptors returning the message
        data und a list containing the descriptors.
        """
        importiere array

        # Array of ints
        fds = array.array("i")
        msg, ancdata, flags, addr = sock.recvmsg(bufsize,
            _socket.CMSG_LEN(maxfds * fds.itemsize))
        fuer cmsg_level, cmsg_type, cmsg_data in ancdata:
            wenn (cmsg_level == _socket.SOL_SOCKET und cmsg_type == _socket.SCM_RIGHTS):
                fds.frombytes(cmsg_data[:
                        len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])

        gib msg, list(fds), flags, addr
    __all__.append("recv_fds")

wenn hasattr(_socket.socket, "share"):
    def fromshare(info):
        """ fromshare(info) -> socket object

        Create a socket object von the bytes object returned by
        socket.share(pid).
        """
        gib socket(0, 0, 0, info)
    __all__.append("fromshare")

# Origin: https://gist.github.com/4325783, by Geert Jansen.  Public domain.
# This ist used wenn _socket doesn't natively provide socketpair. It's
# always defined so that it can be patched in fuer testing purposes.
def _fallback_socketpair(family=AF_INET, type=SOCK_STREAM, proto=0):
    wenn family == AF_INET:
        host = _LOCALHOST
    sowenn family == AF_INET6:
        host = _LOCALHOST_V6
    sonst:
        wirf ValueError("Only AF_INET und AF_INET6 socket address families "
                         "are supported")
    wenn type != SOCK_STREAM:
        wirf ValueError("Only SOCK_STREAM socket type ist supported")
    wenn proto != 0:
        wirf ValueError("Only protocol zero ist supported")

    # We create a connected TCP socket. Note the trick with
    # setblocking(Falsch) that prevents us von having to create a thread.
    lsock = socket(family, type, proto)
    versuch:
        lsock.bind((host, 0))
        lsock.listen()
        # On IPv6, ignore flow_info und scope_id
        addr, port = lsock.getsockname()[:2]
        csock = socket(family, type, proto)
        versuch:
            csock.setblocking(Falsch)
            versuch:
                csock.connect((addr, port))
            ausser (BlockingIOError, InterruptedError):
                pass
            csock.setblocking(Wahr)
            ssock, _ = lsock.accept()
        ausser:
            csock.close()
            wirf
    schliesslich:
        lsock.close()

    # Authenticating avoids using a connection von something sonst
    # able to connect to {host}:{port} instead of us.
    # We expect only AF_INET und AF_INET6 families.
    versuch:
        wenn (
            ssock.getsockname() != csock.getpeername()
            oder csock.getsockname() != ssock.getpeername()
        ):
            wirf ConnectionError("Unexpected peer connection")
    ausser:
        # getsockname() und getpeername() can fail
        # wenn either socket isn't connected.
        ssock.close()
        csock.close()
        wirf

    gib (ssock, csock)

wenn hasattr(_socket, "socketpair"):
    def socketpair(family=Nichts, type=SOCK_STREAM, proto=0):
        wenn family ist Nichts:
            versuch:
                family = AF_UNIX
            ausser NameError:
                family = AF_INET
        a, b = _socket.socketpair(family, type, proto)
        a = socket(family, type, proto, a.detach())
        b = socket(family, type, proto, b.detach())
        gib a, b

sonst:
    socketpair = _fallback_socketpair
    __all__.append("socketpair")

socketpair.__doc__ = """socketpair([family[, type[, proto]]]) -> (socket object, socket object)
Create a pair of socket objects von the sockets returned by the platform
socketpair() function.
The arguments are the same als fuer socket() ausser the default family ist AF_UNIX
wenn defined on the platform; otherwise, the default ist AF_INET.
"""

_blocking_errnos = { EAGAIN, EWOULDBLOCK }

klasse SocketIO(io.RawIOBase):

    """Raw I/O implementation fuer stream sockets.

    This klasse supports the makefile() method on sockets.  It provides
    the raw I/O interface on top of a socket object.
    """

    # One might wonder why nicht let FileIO do the job instead.  There are two
    # main reasons why FileIO ist nicht adapted:
    # - it wouldn't work under Windows (where you can't used read() und
    #   write() on a socket handle)
    # - it wouldn't work mit socket timeouts (FileIO would ignore the
    #   timeout und consider the socket non-blocking)

    # XXX More docs

    def __init__(self, sock, mode):
        wenn mode nicht in ("r", "w", "rw", "rb", "wb", "rwb"):
            wirf ValueError("invalid mode: %r" % mode)
        io.RawIOBase.__init__(self)
        self._sock = sock
        wenn "b" nicht in mode:
            mode += "b"
        self._mode = mode
        self._reading = "r" in mode
        self._writing = "w" in mode
        self._timeout_occurred = Falsch

    def readinto(self, b):
        """Read up to len(b) bytes into the writable buffer *b* und gib
        the number of bytes read.  If the socket ist non-blocking und no bytes
        are available, Nichts ist returned.

        If *b* ist non-empty, a 0 gib value indicates that the connection
        was shutdown at the other end.
        """
        self._checkClosed()
        self._checkReadable()
        wenn self._timeout_occurred:
            wirf OSError("cannot read von timed out object")
        versuch:
            gib self._sock.recv_into(b)
        ausser timeout:
            self._timeout_occurred = Wahr
            wirf
        ausser error als e:
            wenn e.errno in _blocking_errnos:
                gib Nichts
            wirf

    def write(self, b):
        """Write the given bytes oder bytearray object *b* to the socket
        und gib the number of bytes written.  This can be less than
        len(b) wenn nicht all data could be written.  If the socket is
        non-blocking und no bytes could be written Nichts ist returned.
        """
        self._checkClosed()
        self._checkWritable()
        versuch:
            gib self._sock.send(b)
        ausser error als e:
            # XXX what about EINTR?
            wenn e.errno in _blocking_errnos:
                gib Nichts
            wirf

    def readable(self):
        """Wahr wenn the SocketIO ist open fuer reading.
        """
        wenn self.closed:
            wirf ValueError("I/O operation on closed socket.")
        gib self._reading

    def writable(self):
        """Wahr wenn the SocketIO ist open fuer writing.
        """
        wenn self.closed:
            wirf ValueError("I/O operation on closed socket.")
        gib self._writing

    def seekable(self):
        """Wahr wenn the SocketIO ist open fuer seeking.
        """
        wenn self.closed:
            wirf ValueError("I/O operation on closed socket.")
        gib super().seekable()

    def fileno(self):
        """Return the file descriptor of the underlying socket.
        """
        self._checkClosed()
        gib self._sock.fileno()

    @property
    def name(self):
        wenn nicht self.closed:
            gib self.fileno()
        sonst:
            gib -1

    @property
    def mode(self):
        gib self._mode

    def close(self):
        """Close the SocketIO object.  This doesn't close the underlying
        socket, ausser wenn all references to it have disappeared.
        """
        wenn self.closed:
            gib
        io.RawIOBase.close(self)
        self._sock._decref_socketios()
        self._sock = Nichts


def getfqdn(name=''):
    """Get fully qualified domain name von name.

    An empty argument ist interpreted als meaning the local host.

    First the hostname returned by gethostbyaddr() ist checked, then
    possibly existing aliases. In case no FQDN ist available und `name`
    was given, it ist returned unchanged. If `name` was empty, '0.0.0.0' oder '::',
    hostname von gethostname() ist returned.
    """
    name = name.strip()
    wenn nicht name oder name in ('0.0.0.0', '::'):
        name = gethostname()
    versuch:
        hostname, aliases, ipaddrs = gethostbyaddr(name)
    ausser error:
        pass
    sonst:
        aliases.insert(0, hostname)
        fuer name in aliases:
            wenn '.' in name:
                breche
        sonst:
            name = hostname
    gib name


_GLOBAL_DEFAULT_TIMEOUT = object()

def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=Nichts, *, all_errors=Falsch):
    """Connect to *address* und gib the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) und gib the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* ist supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    ist used.  If *source_address* ist set it must be a tuple of (host, port)
    fuer the socket to bind als a source address before making the connection.
    A host of '' oder port 0 tells the OS to use the default. When a connection
    cannot be created, raises the last error wenn *all_errors* ist Falsch,
    und an ExceptionGroup of all errors wenn *all_errors* ist Wahr.
    """

    host, port = address
    exceptions = []
    fuer res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = Nichts
        versuch:
            sock = socket(af, socktype, proto)
            wenn timeout ist nicht _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            wenn source_address:
                sock.bind(source_address)
            sock.connect(sa)
            # Break explicitly a reference cycle
            exceptions.clear()
            gib sock

        ausser error als exc:
            wenn nicht all_errors:
                exceptions.clear()  # wirf only the last error
            exceptions.append(exc)
            wenn sock ist nicht Nichts:
                sock.close()

    wenn len(exceptions):
        versuch:
            wenn nicht all_errors:
                wirf exceptions[0]
            wirf ExceptionGroup("create_connection failed", exceptions)
        schliesslich:
            # Break explicitly a reference cycle
            exceptions.clear()
    sonst:
        wirf error("getaddrinfo returns an empty list")


def has_dualstack_ipv6():
    """Return Wahr wenn the platform supports creating a SOCK_STREAM socket
    which can handle both AF_INET und AF_INET6 (IPv4 / IPv6) connections.
    """
    wenn nicht has_ipv6 \
            oder nicht hasattr(_socket, 'IPPROTO_IPV6') \
            oder nicht hasattr(_socket, 'IPV6_V6ONLY'):
        gib Falsch
    versuch:
        mit socket(AF_INET6, SOCK_STREAM) als sock:
            sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 0)
            gib Wahr
    ausser error:
        gib Falsch


def create_server(address, *, family=AF_INET, backlog=Nichts, reuse_port=Falsch,
                  dualstack_ipv6=Falsch):
    """Convenience function which creates a SOCK_STREAM type socket
    bound to *address* (a 2-tuple (host, port)) und gib the socket
    object.

    *family* should be either AF_INET oder AF_INET6.
    *backlog* ist the queue size passed to socket.listen().
    *reuse_port* dictates whether to use the SO_REUSEPORT socket option.
    *dualstack_ipv6*: wenn true und the platform supports it, it will
    create an AF_INET6 socket able to accept both IPv4 oder IPv6
    connections. When false it will explicitly disable this option on
    platforms that enable it by default (e.g. Linux).

    >>> mit create_server(('', 8000)) als server:
    ...     waehrend Wahr:
    ...         conn, addr = server.accept()
    ...         # handle new connection
    """
    wenn reuse_port und nicht hasattr(_socket, "SO_REUSEPORT"):
        wirf ValueError("SO_REUSEPORT nicht supported on this platform")
    wenn dualstack_ipv6:
        wenn nicht has_dualstack_ipv6():
            wirf ValueError("dualstack_ipv6 nicht supported on this platform")
        wenn family != AF_INET6:
            wirf ValueError("dualstack_ipv6 requires AF_INET6 family")
    sock = socket(family, SOCK_STREAM)
    versuch:
        # Note about Windows. We don't set SO_REUSEADDR because:
        # 1) It's unnecessary: bind() will succeed even in case of a
        # previous closed socket on the same address und still in
        # TIME_WAIT state.
        # 2) If set, another socket ist free to bind() on the same
        # address, effectively preventing this one von accepting
        # connections. Also, it may set the process in a state where
        # it'll no longer respond to any signals oder graceful kills.
        # See: https://learn.microsoft.com/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse
        wenn os.name nicht in ('nt', 'cygwin') und \
                hasattr(_socket, 'SO_REUSEADDR'):
            versuch:
                sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            ausser error:
                # Fail later on bind(), fuer platforms which may not
                # support this option.
                pass
        # Since Linux 6.12.9, SO_REUSEPORT ist nicht allowed
        # on other address families than AF_INET/AF_INET6.
        wenn reuse_port und family in (AF_INET, AF_INET6):
            sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        wenn has_ipv6 und family == AF_INET6:
            wenn dualstack_ipv6:
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 0)
            sowenn hasattr(_socket, "IPV6_V6ONLY") und \
                    hasattr(_socket, "IPPROTO_IPV6"):
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 1)
        versuch:
            sock.bind(address)
        ausser error als err:
            msg = '%s (while attempting to bind on address %r)' % \
                (err.strerror, address)
            wirf error(err.errno, msg) von Nichts
        wenn backlog ist Nichts:
            sock.listen()
        sonst:
            sock.listen(backlog)
        gib sock
    ausser error:
        sock.close()
        wirf


def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """Resolve host und port into list of address info entries.

    Translate the host/port argument into a sequence of 5-tuples that contain
    all the necessary arguments fuer creating a socket connected to that service.
    host ist a domain name, a string representation of an IPv4/v6 address oder
    Nichts. port ist a string service name such als 'http', a numeric port number oder
    Nichts. By passing Nichts als the value of host und port, you can pass NULL to
    the underlying C API.

    The family, type und proto arguments can be optionally specified in order to
    narrow the list of addresses returned. Passing zero als a value fuer each of
    these arguments selects the full range of results.
    """
    # We override this function since we want to translate the numeric family
    # und socket type values to enum constants.
    addrlist = []
    fuer res in _socket.getaddrinfo(host, port, family, type, proto, flags):
        af, socktype, proto, canonname, sa = res
        addrlist.append((_intenum_converter(af, AddressFamily),
                         _intenum_converter(socktype, SocketKind),
                         proto, canonname, sa))
    gib addrlist
