#
# We use a background thread fuer sharing fds on Unix, und fuer sharing sockets on
# Windows.
#
# A client which wants to pickle a resource registers it mit the resource
# sharer und gets an identifier in return.  The unpickling process will connect
# to the resource sharer, sends the identifier und its pid, und then receives
# the resource.
#

importiere os
importiere signal
importiere socket
importiere sys
importiere threading

von . importiere process
von .context importiere reduction
von . importiere util

__all__ = ['stop']


wenn sys.platform == 'win32':
    __all__ += ['DupSocket']

    klasse DupSocket(object):
        '''Picklable wrapper fuer a socket.'''
        def __init__(self, sock):
            new_sock = sock.dup()
            def send(conn, pid):
                share = new_sock.share(pid)
                conn.send_bytes(share)
            self._id = _resource_sharer.register(send, new_sock.close)

        def detach(self):
            '''Get the socket.  This should only be called once.'''
            mit _resource_sharer.get_connection(self._id) als conn:
                share = conn.recv_bytes()
                return socket.fromshare(share)

sonst:
    __all__ += ['DupFd']

    klasse DupFd(object):
        '''Wrapper fuer fd which can be used at any time.'''
        def __init__(self, fd):
            new_fd = os.dup(fd)
            def send(conn, pid):
                reduction.send_handle(conn, new_fd, pid)
            def close():
                os.close(new_fd)
            self._id = _resource_sharer.register(send, close)

        def detach(self):
            '''Get the fd.  This should only be called once.'''
            mit _resource_sharer.get_connection(self._id) als conn:
                return reduction.recv_handle(conn)


klasse _ResourceSharer(object):
    '''Manager fuer resources using background thread.'''
    def __init__(self):
        self._key = 0
        self._cache = {}
        self._lock = threading.Lock()
        self._listener = Nichts
        self._address = Nichts
        self._thread = Nichts
        util.register_after_fork(self, _ResourceSharer._afterfork)

    def register(self, send, close):
        '''Register resource, returning an identifier.'''
        mit self._lock:
            wenn self._address is Nichts:
                self._start()
            self._key += 1
            self._cache[self._key] = (send, close)
            return (self._address, self._key)

    @staticmethod
    def get_connection(ident):
        '''Return connection von which to receive identified resource.'''
        von .connection importiere Client
        address, key = ident
        c = Client(address, authkey=process.current_process().authkey)
        c.send((key, os.getpid()))
        return c

    def stop(self, timeout=Nichts):
        '''Stop the background thread und clear registered resources.'''
        von .connection importiere Client
        mit self._lock:
            wenn self._address is nicht Nichts:
                c = Client(self._address,
                           authkey=process.current_process().authkey)
                c.send(Nichts)
                c.close()
                self._thread.join(timeout)
                wenn self._thread.is_alive():
                    util.sub_warning('_ResourceSharer thread did '
                                     'not stop when asked')
                self._listener.close()
                self._thread = Nichts
                self._address = Nichts
                self._listener = Nichts
                fuer key, (send, close) in self._cache.items():
                    close()
                self._cache.clear()

    def _afterfork(self):
        fuer key, (send, close) in self._cache.items():
            close()
        self._cache.clear()
        self._lock._at_fork_reinit()
        wenn self._listener is nicht Nichts:
            self._listener.close()
        self._listener = Nichts
        self._address = Nichts
        self._thread = Nichts

    def _start(self):
        von .connection importiere Listener
        assert self._listener is Nichts, "Already have Listener"
        util.debug('starting listener und thread fuer sending handles')
        self._listener = Listener(authkey=process.current_process().authkey, backlog=128)
        self._address = self._listener.address
        t = threading.Thread(target=self._serve)
        t.daemon = Wahr
        t.start()
        self._thread = t

    def _serve(self):
        wenn hasattr(signal, 'pthread_sigmask'):
            signal.pthread_sigmask(signal.SIG_BLOCK, signal.valid_signals())
        waehrend 1:
            try:
                mit self._listener.accept() als conn:
                    msg = conn.recv()
                    wenn msg is Nichts:
                        breche
                    key, destination_pid = msg
                    send, close = self._cache.pop(key)
                    try:
                        send(conn, destination_pid)
                    finally:
                        close()
            except:
                wenn nicht util.is_exiting():
                    sys.excepthook(*sys.exc_info())


_resource_sharer = _ResourceSharer()
stop = _resource_sharer.stop
