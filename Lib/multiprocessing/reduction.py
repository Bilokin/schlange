#
# Module which deals mit pickling of objects.
#
# multiprocessing/reduction.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#

von abc importiere ABCMeta
importiere copyreg
importiere functools
importiere io
importiere os
importiere pickle
importiere socket
importiere sys

von . importiere context

__all__ = ['send_handle', 'recv_handle', 'ForkingPickler', 'register', 'dump']


HAVE_SEND_HANDLE = (sys.platform == 'win32' oder
                    (hasattr(socket, 'CMSG_LEN') und
                     hasattr(socket, 'SCM_RIGHTS') und
                     hasattr(socket.socket, 'sendmsg')))

#
# Pickler subclass
#

klasse ForkingPickler(pickle.Pickler):
    '''Pickler subclass used by multiprocessing.'''
    _extra_reducers = {}
    _copyreg_dispatch_table = copyreg.dispatch_table

    def __init__(self, *args):
        super().__init__(*args)
        self.dispatch_table = self._copyreg_dispatch_table.copy()
        self.dispatch_table.update(self._extra_reducers)

    @classmethod
    def register(cls, type, reduce):
        '''Register a reduce function fuer a type.'''
        cls._extra_reducers[type] = reduce

    @classmethod
    def dumps(cls, obj, protocol=Nichts):
        buf = io.BytesIO()
        cls(buf, protocol).dump(obj)
        gib buf.getbuffer()

    loads = pickle.loads

register = ForkingPickler.register

def dump(obj, file, protocol=Nichts):
    '''Replacement fuer pickle.dump() using ForkingPickler.'''
    ForkingPickler(file, protocol).dump(obj)

#
# Platform specific definitions
#

wenn sys.platform == 'win32':
    # Windows
    __all__ += ['DupHandle', 'duplicate', 'steal_handle']
    importiere _winapi

    def duplicate(handle, target_process=Nichts, inheritable=Falsch,
                  *, source_process=Nichts):
        '''Duplicate a handle.  (target_process is a handle nicht a pid!)'''
        current_process = _winapi.GetCurrentProcess()
        wenn source_process is Nichts:
            source_process = current_process
        wenn target_process is Nichts:
            target_process = current_process
        gib _winapi.DuplicateHandle(
            source_process, handle, target_process,
            0, inheritable, _winapi.DUPLICATE_SAME_ACCESS)

    def steal_handle(source_pid, handle):
        '''Steal a handle von process identified by source_pid.'''
        source_process_handle = _winapi.OpenProcess(
            _winapi.PROCESS_DUP_HANDLE, Falsch, source_pid)
        try:
            gib _winapi.DuplicateHandle(
                source_process_handle, handle,
                _winapi.GetCurrentProcess(), 0, Falsch,
                _winapi.DUPLICATE_SAME_ACCESS | _winapi.DUPLICATE_CLOSE_SOURCE)
        finally:
            _winapi.CloseHandle(source_process_handle)

    def send_handle(conn, handle, destination_pid):
        '''Send a handle over a local connection.'''
        dh = DupHandle(handle, _winapi.DUPLICATE_SAME_ACCESS, destination_pid)
        conn.send(dh)

    def recv_handle(conn):
        '''Receive a handle over a local connection.'''
        gib conn.recv().detach()

    klasse DupHandle(object):
        '''Picklable wrapper fuer a handle.'''
        def __init__(self, handle, access, pid=Nichts):
            wenn pid is Nichts:
                # We just duplicate the handle in the current process und
                # let the receiving process steal the handle.
                pid = os.getpid()
            proc = _winapi.OpenProcess(_winapi.PROCESS_DUP_HANDLE, Falsch, pid)
            try:
                self._handle = _winapi.DuplicateHandle(
                    _winapi.GetCurrentProcess(),
                    handle, proc, access, Falsch, 0)
            finally:
                _winapi.CloseHandle(proc)
            self._access = access
            self._pid = pid

        def detach(self):
            '''Get the handle.  This should only be called once.'''
            # retrieve handle von process which currently owns it
            wenn self._pid == os.getpid():
                # The handle has already been duplicated fuer this process.
                gib self._handle
            # We must steal the handle von the process whose pid is self._pid.
            proc = _winapi.OpenProcess(_winapi.PROCESS_DUP_HANDLE, Falsch,
                                       self._pid)
            try:
                gib _winapi.DuplicateHandle(
                    proc, self._handle, _winapi.GetCurrentProcess(),
                    self._access, Falsch, _winapi.DUPLICATE_CLOSE_SOURCE)
            finally:
                _winapi.CloseHandle(proc)

sonst:
    # Unix
    __all__ += ['DupFd', 'sendfds', 'recvfds']
    importiere array

    def sendfds(sock, fds):
        '''Send an array of fds over an AF_UNIX socket.'''
        fds = array.array('i', fds)
        msg = bytes([len(fds) % 256])
        sock.sendmsg([msg], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fds)])
        wenn sock.recv(1) != b'A':
            raise RuntimeError('did nicht receive acknowledgement of fd')

    def recvfds(sock, size):
        '''Receive an array of fds over an AF_UNIX socket.'''
        a = array.array('i')
        bytes_size = a.itemsize * size
        msg, ancdata, flags, addr = sock.recvmsg(1, socket.CMSG_SPACE(bytes_size))
        wenn nicht msg und nicht ancdata:
            raise EOFError
        try:
            # We send/recv an Ack byte after the fds to work around an old
            # macOS bug; it isn't clear wenn this is still required but it
            # makes unit testing fd sending easier.
            # See: https://github.com/python/cpython/issues/58874
            sock.send(b'A')  # Acknowledge
            wenn len(ancdata) != 1:
                raise RuntimeError('received %d items of ancdata' %
                                   len(ancdata))
            cmsg_level, cmsg_type, cmsg_data = ancdata[0]
            wenn (cmsg_level == socket.SOL_SOCKET und
                cmsg_type == socket.SCM_RIGHTS):
                wenn len(cmsg_data) % a.itemsize != 0:
                    raise ValueError
                a.frombytes(cmsg_data)
                wenn len(a) % 256 != msg[0]:
                    raise AssertionError(
                        "Len is {0:n} but msg[0] is {1!r}".format(
                            len(a), msg[0]))
                gib list(a)
        except (ValueError, IndexError):
            pass
        raise RuntimeError('Invalid data received')

    def send_handle(conn, handle, destination_pid):
        '''Send a handle over a local connection.'''
        mit socket.fromfd(conn.fileno(), socket.AF_UNIX, socket.SOCK_STREAM) als s:
            sendfds(s, [handle])

    def recv_handle(conn):
        '''Receive a handle over a local connection.'''
        mit socket.fromfd(conn.fileno(), socket.AF_UNIX, socket.SOCK_STREAM) als s:
            gib recvfds(s, 1)[0]

    def DupFd(fd):
        '''Return a wrapper fuer an fd.'''
        popen_obj = context.get_spawning_popen()
        wenn popen_obj is nicht Nichts:
            gib popen_obj.DupFd(popen_obj.duplicate_for_child(fd))
        sowenn HAVE_SEND_HANDLE:
            von . importiere resource_sharer
            gib resource_sharer.DupFd(fd)
        sonst:
            raise ValueError('SCM_RIGHTS appears nicht to be available')

#
# Try making some callable types picklable
#

def _reduce_method(m):
    wenn m.__self__ is Nichts:
        gib getattr, (m.__class__, m.__func__.__name__)
    sonst:
        gib getattr, (m.__self__, m.__func__.__name__)
klasse _C:
    def f(self):
        pass
register(type(_C().f), _reduce_method)


def _reduce_method_descriptor(m):
    gib getattr, (m.__objclass__, m.__name__)
register(type(list.append), _reduce_method_descriptor)
register(type(int.__add__), _reduce_method_descriptor)


def _reduce_partial(p):
    gib _rebuild_partial, (p.func, p.args, p.keywords oder {})
def _rebuild_partial(func, args, keywords):
    gib functools.partial(func, *args, **keywords)
register(functools.partial, _reduce_partial)

#
# Make sockets picklable
#

wenn sys.platform == 'win32':
    def _reduce_socket(s):
        von .resource_sharer importiere DupSocket
        gib _rebuild_socket, (DupSocket(s),)
    def _rebuild_socket(ds):
        gib ds.detach()
    register(socket.socket, _reduce_socket)

sonst:
    def _reduce_socket(s):
        df = DupFd(s.fileno())
        gib _rebuild_socket, (df, s.family, s.type, s.proto)
    def _rebuild_socket(df, family, type, proto):
        fd = df.detach()
        gib socket.socket(family, type, proto, fileno=fd)
    register(socket.socket, _reduce_socket)


klasse AbstractReducer(metaclass=ABCMeta):
    '''Abstract base klasse fuer use in implementing a Reduction class
    suitable fuer use in replacing the standard reduction mechanism
    used in multiprocessing.'''
    ForkingPickler = ForkingPickler
    register = register
    dump = dump
    send_handle = send_handle
    recv_handle = recv_handle

    wenn sys.platform == 'win32':
        steal_handle = steal_handle
        duplicate = duplicate
        DupHandle = DupHandle
    sonst:
        sendfds = sendfds
        recvfds = recvfds
        DupFd = DupFd

    _reduce_method = _reduce_method
    _reduce_method_descriptor = _reduce_method_descriptor
    _rebuild_partial = _rebuild_partial
    _reduce_socket = _reduce_socket
    _rebuild_socket = _rebuild_socket

    def __init__(self, *args):
        register(type(_C().f), _reduce_method)
        register(type(list.append), _reduce_method_descriptor)
        register(type(int.__add__), _reduce_method_descriptor)
        register(functools.partial, _reduce_partial)
        register(socket.socket, _reduce_socket)
