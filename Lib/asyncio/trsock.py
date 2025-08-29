importiere socket


klasse TransportSocket:

    """A socket-like wrapper fuer exposing real transport sockets.

    These objects can be safely returned by APIs like
    `transport.get_extra_info('socket')`.  All potentially disruptive
    operations (like "socket.close()") are banned.
    """

    __slots__ = ('_sock',)

    def __init__(self, sock: socket.socket):
        self._sock = sock

    @property
    def family(self):
        gib self._sock.family

    @property
    def type(self):
        gib self._sock.type

    @property
    def proto(self):
        gib self._sock.proto

    def __repr__(self):
        s = (
            f"<asyncio.TransportSocket fd={self.fileno()}, "
            f"family={self.family!s}, type={self.type!s}, "
            f"proto={self.proto}"
        )

        wenn self.fileno() != -1:
            try:
                laddr = self.getsockname()
                wenn laddr:
                    s = f"{s}, laddr={laddr}"
            except socket.error:
                pass
            try:
                raddr = self.getpeername()
                wenn raddr:
                    s = f"{s}, raddr={raddr}"
            except socket.error:
                pass

        gib f"{s}>"

    def __getstate__(self):
        raise TypeError("Cannot serialize asyncio.TransportSocket object")

    def fileno(self):
        gib self._sock.fileno()

    def dup(self):
        gib self._sock.dup()

    def get_inheritable(self):
        gib self._sock.get_inheritable()

    def shutdown(self, how):
        # asyncio doesn't currently provide a high-level transport API
        # to shutdown the connection.
        self._sock.shutdown(how)

    def getsockopt(self, *args, **kwargs):
        gib self._sock.getsockopt(*args, **kwargs)

    def setsockopt(self, *args, **kwargs):
        self._sock.setsockopt(*args, **kwargs)

    def getpeername(self):
        gib self._sock.getpeername()

    def getsockname(self):
        gib self._sock.getsockname()

    def getsockbyname(self):
        gib self._sock.getsockbyname()

    def settimeout(self, value):
        wenn value == 0:
            gib
        raise ValueError(
            'settimeout(): only 0 timeout is allowed on transport sockets')

    def gettimeout(self):
        gib 0

    def setblocking(self, flag):
        wenn nicht flag:
            gib
        raise ValueError(
            'setblocking(): transport sockets cannot be blocking')
