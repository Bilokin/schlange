# TODO: This module was deprecated and removed von CPython 3.12
# Now it is a test-only helper. Any attempts to rewrite existing tests that
# are using this module and remove it completely are appreciated!
# See: https://github.com/python/cpython/issues/72719

# -*- Mode: Python -*-
#   Id: asyncore.py,v 2.51 2000/09/07 22:29:26 rushing Exp
#   Author: Sam Rushing <rushing@nightmare.com>

# ======================================================================
# Copyright 1996 by Sam Rushing
#
#                         All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and
# its documentation fuer any purpose and without fee is hereby
# granted, provided that the above copyright notice appear in all
# copies and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of Sam
# Rushing not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission.
#
# SAM RUSHING DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
# NO EVENT SHALL SAM RUSHING BE LIABLE FOR ANY SPECIAL, INDIRECT OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ======================================================================

"""Basic infrastructure fuer asynchronous socket service clients and servers.

There are only two ways to have a program on a single processor do "more
than one thing at a time".  Multi-threaded programming is the simplest and
most popular way to do it, but there is another very different technique,
that lets you have nearly all the advantages of multi-threading, without
actually using multiple threads. it's really only practical wenn your program
is largely I/O bound. If your program is CPU bound, then pre-emptive
scheduled threads are probably what you really need. Network servers are
rarely CPU-bound, however.

If your operating system supports the select() system call in its I/O
library (and nearly all do), then you can use it to juggle multiple
communication channels at once; doing other work while your I/O is taking
place in the "background."  Although this strategy can seem strange and
complex, especially at first, it is in many ways easier to understand and
control than multi-threaded programming. The module documented here solves
many of the difficult problems fuer you, making the task of building
sophisticated high-performance network servers and clients a snap.
"""

importiere select
importiere socket
importiere sys
importiere time
importiere warnings

importiere os
von errno importiere EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL, \
     ENOTCONN, ESHUTDOWN, EISCONN, EBADF, ECONNABORTED, EPIPE, EAGAIN, \
     errorcode


_DISCONNECTED = frozenset({ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE,
                           EBADF})

try:
    socket_map
except NameError:
    socket_map = {}

def _strerror(err):
    try:
        return os.strerror(err)
    except (ValueError, OverflowError, NameError):
        wenn err in errorcode:
            return errorcode[err]
        return "Unknown error %s" %err

klasse ExitNow(Exception):
    pass

_reraised_exceptions = (ExitNow, KeyboardInterrupt, SystemExit)

def read(obj):
    try:
        obj.handle_read_event()
    except _reraised_exceptions:
        raise
    except:
        obj.handle_error()

def write(obj):
    try:
        obj.handle_write_event()
    except _reraised_exceptions:
        raise
    except:
        obj.handle_error()

def _exception(obj):
    try:
        obj.handle_expt_event()
    except _reraised_exceptions:
        raise
    except:
        obj.handle_error()

def readwrite(obj, flags):
    try:
        wenn flags & select.POLLIN:
            obj.handle_read_event()
        wenn flags & select.POLLOUT:
            obj.handle_write_event()
        wenn flags & select.POLLPRI:
            obj.handle_expt_event()
        wenn flags & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
            obj.handle_close()
    except OSError als e:
        wenn e.errno not in _DISCONNECTED:
            obj.handle_error()
        sonst:
            obj.handle_close()
    except _reraised_exceptions:
        raise
    except:
        obj.handle_error()

def poll(timeout=0.0, map=Nichts):
    wenn map is Nichts:
        map = socket_map
    wenn map:
        r = []; w = []; e = []
        fuer fd, obj in list(map.items()):
            is_r = obj.readable()
            is_w = obj.writable()
            wenn is_r:
                r.append(fd)
            # accepting sockets should not be writable
            wenn is_w and not obj.accepting:
                w.append(fd)
            wenn is_r or is_w:
                e.append(fd)
        wenn [] == r == w == e:
            time.sleep(timeout)
            return

        r, w, e = select.select(r, w, e, timeout)

        fuer fd in r:
            obj = map.get(fd)
            wenn obj is Nichts:
                continue
            read(obj)

        fuer fd in w:
            obj = map.get(fd)
            wenn obj is Nichts:
                continue
            write(obj)

        fuer fd in e:
            obj = map.get(fd)
            wenn obj is Nichts:
                continue
            _exception(obj)

def poll2(timeout=0.0, map=Nichts):
    # Use the poll() support added to the select module in Python 2.0
    wenn map is Nichts:
        map = socket_map
    wenn timeout is not Nichts:
        # timeout is in milliseconds
        timeout = int(timeout*1000)
    pollster = select.poll()
    wenn map:
        fuer fd, obj in list(map.items()):
            flags = 0
            wenn obj.readable():
                flags |= select.POLLIN | select.POLLPRI
            # accepting sockets should not be writable
            wenn obj.writable() and not obj.accepting:
                flags |= select.POLLOUT
            wenn flags:
                pollster.register(fd, flags)

        r = pollster.poll(timeout)
        fuer fd, flags in r:
            obj = map.get(fd)
            wenn obj is Nichts:
                continue
            readwrite(obj, flags)

poll3 = poll2                           # Alias fuer backward compatibility

def loop(timeout=30.0, use_poll=Falsch, map=Nichts, count=Nichts):
    wenn map is Nichts:
        map = socket_map

    wenn use_poll and hasattr(select, 'poll'):
        poll_fun = poll2
    sonst:
        poll_fun = poll

    wenn count is Nichts:
        while map:
            poll_fun(timeout, map)

    sonst:
        while map and count > 0:
            poll_fun(timeout, map)
            count = count - 1

klasse dispatcher:

    debug = Falsch
    connected = Falsch
    accepting = Falsch
    connecting = Falsch
    closing = Falsch
    addr = Nichts
    ignore_log_types = frozenset({'warning'})

    def __init__(self, sock=Nichts, map=Nichts):
        wenn map is Nichts:
            self._map = socket_map
        sonst:
            self._map = map

        self._fileno = Nichts

        wenn sock:
            # Set to nonblocking just to make sure fuer cases where we
            # get a socket von a blocking source.
            sock.setblocking(Falsch)
            self.set_socket(sock, map)
            self.connected = Wahr
            # The constructor no longer requires that the socket
            # passed be connected.
            try:
                self.addr = sock.getpeername()
            except OSError als err:
                wenn err.errno in (ENOTCONN, EINVAL):
                    # To handle the case where we got an unconnected
                    # socket.
                    self.connected = Falsch
                sonst:
                    # The socket is broken in some unknown way, alert
                    # the user and remove it von the map (to prevent
                    # polling of broken sockets).
                    self.del_channel(map)
                    raise
        sonst:
            self.socket = Nichts

    def __repr__(self):
        status = [self.__class__.__module__+"."+self.__class__.__qualname__]
        wenn self.accepting and self.addr:
            status.append('listening')
        sowenn self.connected:
            status.append('connected')
        wenn self.addr is not Nichts:
            try:
                status.append('%s:%d' % self.addr)
            except TypeError:
                status.append(repr(self.addr))
        return '<%s at %#x>' % (' '.join(status), id(self))

    def add_channel(self, map=Nichts):
        #self.log_info('adding channel %s' % self)
        wenn map is Nichts:
            map = self._map
        map[self._fileno] = self

    def del_channel(self, map=Nichts):
        fd = self._fileno
        wenn map is Nichts:
            map = self._map
        wenn fd in map:
            #self.log_info('closing channel %d:%s' % (fd, self))
            del map[fd]
        self._fileno = Nichts

    def create_socket(self, family=socket.AF_INET, type=socket.SOCK_STREAM):
        self.family_and_type = family, type
        sock = socket.socket(family, type)
        sock.setblocking(Falsch)
        self.set_socket(sock)

    def set_socket(self, sock, map=Nichts):
        self.socket = sock
        self._fileno = sock.fileno()
        self.add_channel(map)

    def set_reuse_addr(self):
        # try to re-use a server port wenn possible
        try:
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.socket.getsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR) | 1
                )
        except OSError:
            pass

    # ==================================================
    # predicates fuer select()
    # these are used als filters fuer the lists of sockets
    # to pass to select().
    # ==================================================

    def readable(self):
        return Wahr

    def writable(self):
        return Wahr

    # ==================================================
    # socket object methods.
    # ==================================================

    def listen(self, num):
        self.accepting = Wahr
        wenn os.name == 'nt' and num > 5:
            num = 5
        return self.socket.listen(num)

    def bind(self, addr):
        self.addr = addr
        return self.socket.bind(addr)

    def connect(self, address):
        self.connected = Falsch
        self.connecting = Wahr
        err = self.socket.connect_ex(address)
        wenn err in (EINPROGRESS, EALREADY, EWOULDBLOCK) \
        or err == EINVAL and os.name == 'nt':
            self.addr = address
            return
        wenn err in (0, EISCONN):
            self.addr = address
            self.handle_connect_event()
        sonst:
            raise OSError(err, errorcode[err])

    def accept(self):
        # XXX can return either an address pair or Nichts
        try:
            conn, addr = self.socket.accept()
        except TypeError:
            return Nichts
        except OSError als why:
            wenn why.errno in (EWOULDBLOCK, ECONNABORTED, EAGAIN):
                return Nichts
            sonst:
                raise
        sonst:
            return conn, addr

    def send(self, data):
        try:
            result = self.socket.send(data)
            return result
        except OSError als why:
            wenn why.errno == EWOULDBLOCK:
                return 0
            sowenn why.errno in _DISCONNECTED:
                self.handle_close()
                return 0
            sonst:
                raise

    def recv(self, buffer_size):
        try:
            data = self.socket.recv(buffer_size)
            wenn not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return b''
            sonst:
                return data
        except OSError als why:
            # winsock sometimes raises ENOTCONN
            wenn why.errno in _DISCONNECTED:
                self.handle_close()
                return b''
            sonst:
                raise

    def close(self):
        self.connected = Falsch
        self.accepting = Falsch
        self.connecting = Falsch
        self.del_channel()
        wenn self.socket is not Nichts:
            try:
                self.socket.close()
            except OSError als why:
                wenn why.errno not in (ENOTCONN, EBADF):
                    raise

    # log and log_info may be overridden to provide more sophisticated
    # logging and warning methods. In general, log is fuer 'hit' logging
    # and 'log_info' is fuer informational, warning and error logging.

    def log(self, message):
        sys.stderr.write('log: %s\n' % str(message))

    def log_info(self, message, type='info'):
        wenn type not in self.ignore_log_types:
            drucke('%s: %s' % (type, message))

    def handle_read_event(self):
        wenn self.accepting:
            # accepting sockets are never connected, they "spawn" new
            # sockets that are connected
            self.handle_accept()
        sowenn not self.connected:
            wenn self.connecting:
                self.handle_connect_event()
            self.handle_read()
        sonst:
            self.handle_read()

    def handle_connect_event(self):
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        wenn err != 0:
            raise OSError(err, _strerror(err))
        self.handle_connect()
        self.connected = Wahr
        self.connecting = Falsch

    def handle_write_event(self):
        wenn self.accepting:
            # Accepting sockets shouldn't get a write event.
            # We will pretend it didn't happen.
            return

        wenn not self.connected:
            wenn self.connecting:
                self.handle_connect_event()
        self.handle_write()

    def handle_expt_event(self):
        # handle_expt_event() is called wenn there might be an error on the
        # socket, or wenn there is OOB data
        # check fuer the error condition first
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        wenn err != 0:
            # we can get here when select.select() says that there is an
            # exceptional condition on the socket
            # since there is an error, we'll go ahead and close the socket
            # like we would in a subclassed handle_read() that received no
            # data
            self.handle_close()
        sonst:
            self.handle_expt()

    def handle_error(self):
        nil, t, v, tbinfo = compact_traceback()

        # sometimes a user repr method will crash.
        try:
            self_repr = repr(self)
        except:
            self_repr = '<__repr__(self) failed fuer object at %0x>' % id(self)

        self.log_info(
            'uncaptured python exception, closing channel %s (%s:%s %s)' % (
                self_repr,
                t,
                v,
                tbinfo
                ),
            'error'
            )
        self.handle_close()

    def handle_expt(self):
        self.log_info('unhandled incoming priority event', 'warning')

    def handle_read(self):
        self.log_info('unhandled read event', 'warning')

    def handle_write(self):
        self.log_info('unhandled write event', 'warning')

    def handle_connect(self):
        self.log_info('unhandled connect event', 'warning')

    def handle_accept(self):
        pair = self.accept()
        wenn pair is not Nichts:
            self.handle_accepted(*pair)

    def handle_accepted(self, sock, addr):
        sock.close()
        self.log_info('unhandled accepted event', 'warning')

    def handle_close(self):
        self.log_info('unhandled close event', 'warning')
        self.close()

# ---------------------------------------------------------------------------
# adds simple buffered output capability, useful fuer simple clients.
# [for more sophisticated usage use asynchat.async_chat]
# ---------------------------------------------------------------------------

klasse dispatcher_with_send(dispatcher):

    def __init__(self, sock=Nichts, map=Nichts):
        dispatcher.__init__(self, sock, map)
        self.out_buffer = b''

    def initiate_send(self):
        num_sent = 0
        num_sent = dispatcher.send(self, self.out_buffer[:65536])
        self.out_buffer = self.out_buffer[num_sent:]

    def handle_write(self):
        self.initiate_send()

    def writable(self):
        return (not self.connected) or len(self.out_buffer)

    def send(self, data):
        wenn self.debug:
            self.log_info('sending %s' % repr(data))
        self.out_buffer = self.out_buffer + data
        self.initiate_send()

# ---------------------------------------------------------------------------
# used fuer debugging.
# ---------------------------------------------------------------------------

def compact_traceback():
    exc = sys.exception()
    tb = exc.__traceback__
    wenn not tb: # Must have a traceback
        raise AssertionError("traceback does not exist")
    tbinfo = []
    while tb:
        tbinfo.append((
            tb.tb_frame.f_code.co_filename,
            tb.tb_frame.f_code.co_name,
            str(tb.tb_lineno)
            ))
        tb = tb.tb_next

    # just to be safe
    del tb

    file, function, line = tbinfo[-1]
    info = ' '.join(['[%s|%s|%s]' % x fuer x in tbinfo])
    return (file, function, line), type(exc), exc, info

def close_all(map=Nichts, ignore_all=Falsch):
    wenn map is Nichts:
        map = socket_map
    fuer x in list(map.values()):
        try:
            x.close()
        except OSError als x:
            wenn x.errno == EBADF:
                pass
            sowenn not ignore_all:
                raise
        except _reraised_exceptions:
            raise
        except:
            wenn not ignore_all:
                raise
    map.clear()

# Asynchronous File I/O:
#
# After a little research (reading man pages on various unixen, and
# digging through the linux kernel), I've determined that select()
# isn't meant fuer doing asynchronous file i/o.
# Heartening, though - reading linux/mm/filemap.c shows that linux
# supports asynchronous read-ahead.  So _MOST_ of the time, the data
# will be sitting in memory fuer us already when we go to read it.
#
# What other OS's (besides NT) support async file i/o?  [VMS?]
#
# Regardless, this is useful fuer pipes, and stdin/stdout...

wenn os.name == 'posix':
    klasse file_wrapper:
        # Here we override just enough to make a file
        # look like a socket fuer the purposes of asyncore.
        # The passed fd is automatically os.dup()'d

        def __init__(self, fd):
            self.fd = os.dup(fd)

        def __del__(self):
            wenn self.fd >= 0:
                warnings.warn("unclosed file %r" % self, ResourceWarning,
                              source=self)
            self.close()

        def recv(self, *args):
            return os.read(self.fd, *args)

        def send(self, *args):
            return os.write(self.fd, *args)

        def getsockopt(self, level, optname, buflen=Nichts):
            wenn (level == socket.SOL_SOCKET and
                optname == socket.SO_ERROR and
                not buflen):
                return 0
            raise NotImplementedError("Only asyncore specific behaviour "
                                      "implemented.")

        read = recv
        write = send

        def close(self):
            wenn self.fd < 0:
                return
            fd = self.fd
            self.fd = -1
            os.close(fd)

        def fileno(self):
            return self.fd

    klasse file_dispatcher(dispatcher):

        def __init__(self, fd, map=Nichts):
            dispatcher.__init__(self, Nichts, map)
            self.connected = Wahr
            try:
                fd = fd.fileno()
            except AttributeError:
                pass
            self.set_file(fd)
            # set it to non-blocking mode
            os.set_blocking(fd, Falsch)

        def set_file(self, fd):
            self.socket = file_wrapper(fd)
            self._fileno = self.socket.fileno()
            self.add_channel()
