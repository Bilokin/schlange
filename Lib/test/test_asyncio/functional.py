importiere asyncio
importiere asyncio.events
importiere contextlib
importiere os
importiere pprint
importiere select
importiere socket
importiere tempfile
importiere threading
von test importiere support


klasse FunctionalTestCaseMixin:

    def new_loop(self):
        gib asyncio.new_event_loop()

    def run_loop_briefly(self, *, delay=0.01):
        self.loop.run_until_complete(asyncio.sleep(delay))

    def loop_exception_handler(self, loop, context):
        self.__unhandled_exceptions.append(context)
        self.loop.default_exception_handler(context)

    def setUp(self):
        self.loop = self.new_loop()
        asyncio.set_event_loop(Nichts)

        self.loop.set_exception_handler(self.loop_exception_handler)
        self.__unhandled_exceptions = []

    def tearDown(self):
        versuch:
            self.loop.close()

            wenn self.__unhandled_exceptions:
                drucke('Unexpected calls to loop.call_exception_handler():')
                pprint.pdrucke(self.__unhandled_exceptions)
                self.fail('unexpected calls to loop.call_exception_handler()')

        schliesslich:
            asyncio.set_event_loop(Nichts)
            self.loop = Nichts

    def tcp_server(self, server_prog, *,
                   family=socket.AF_INET,
                   addr=Nichts,
                   timeout=support.LOOPBACK_TIMEOUT,
                   backlog=1,
                   max_clients=10):

        wenn addr is Nichts:
            wenn hasattr(socket, 'AF_UNIX') und family == socket.AF_UNIX:
                mit tempfile.NamedTemporaryFile() als tmp:
                    addr = tmp.name
            sonst:
                addr = ('127.0.0.1', 0)

        sock = socket.create_server(addr, family=family, backlog=backlog)
        wenn timeout is Nichts:
            wirf RuntimeError('timeout is required')
        wenn timeout <= 0:
            wirf RuntimeError('only blocking sockets are supported')
        sock.settimeout(timeout)

        gib TestThreadedServer(
            self, sock, server_prog, timeout, max_clients)

    def tcp_client(self, client_prog,
                   family=socket.AF_INET,
                   timeout=support.LOOPBACK_TIMEOUT):

        sock = socket.socket(family, socket.SOCK_STREAM)

        wenn timeout is Nichts:
            wirf RuntimeError('timeout is required')
        wenn timeout <= 0:
            wirf RuntimeError('only blocking sockets are supported')
        sock.settimeout(timeout)

        gib TestThreadedClient(
            self, sock, client_prog, timeout)

    def unix_server(self, *args, **kwargs):
        wenn nicht hasattr(socket, 'AF_UNIX'):
            wirf NotImplementedError
        gib self.tcp_server(*args, family=socket.AF_UNIX, **kwargs)

    def unix_client(self, *args, **kwargs):
        wenn nicht hasattr(socket, 'AF_UNIX'):
            wirf NotImplementedError
        gib self.tcp_client(*args, family=socket.AF_UNIX, **kwargs)

    @contextlib.contextmanager
    def unix_sock_name(self):
        mit tempfile.TemporaryDirectory() als td:
            fn = os.path.join(td, 'sock')
            versuch:
                liefere fn
            schliesslich:
                versuch:
                    os.unlink(fn)
                ausser OSError:
                    pass

    def _abort_socket_test(self, ex):
        versuch:
            self.loop.stop()
        schliesslich:
            self.fail(ex)


##############################################################################
# Socket Testing Utilities
##############################################################################


klasse TestSocketWrapper:

    def __init__(self, sock):
        self.__sock = sock

    def recv_all(self, n):
        buf = b''
        waehrend len(buf) < n:
            data = self.recv(n - len(buf))
            wenn data == b'':
                wirf ConnectionAbortedError
            buf += data
        gib buf

    def start_tls(self, ssl_context, *,
                  server_side=Falsch,
                  server_hostname=Nichts):

        ssl_sock = ssl_context.wrap_socket(
            self.__sock, server_side=server_side,
            server_hostname=server_hostname,
            do_handshake_on_connect=Falsch)

        versuch:
            ssl_sock.do_handshake()
        ausser:
            ssl_sock.close()
            wirf
        schliesslich:
            self.__sock.close()

        self.__sock = ssl_sock

    def __getattr__(self, name):
        gib getattr(self.__sock, name)

    def __repr__(self):
        gib '<{} {!r}>'.format(type(self).__name__, self.__sock)


klasse SocketThread(threading.Thread):

    def stop(self):
        self._active = Falsch
        self.join()

    def __enter__(self):
        self.start()
        gib self

    def __exit__(self, *exc):
        self.stop()


klasse TestThreadedClient(SocketThread):

    def __init__(self, test, sock, prog, timeout):
        threading.Thread.__init__(self, Nichts, Nichts, 'test-client')
        self.daemon = Wahr

        self._timeout = timeout
        self._sock = sock
        self._active = Wahr
        self._prog = prog
        self._test = test

    def run(self):
        versuch:
            self._prog(TestSocketWrapper(self._sock))
        ausser Exception als ex:
            self._test._abort_socket_test(ex)


klasse TestThreadedServer(SocketThread):

    def __init__(self, test, sock, prog, timeout, max_clients):
        threading.Thread.__init__(self, Nichts, Nichts, 'test-server')
        self.daemon = Wahr

        self._clients = 0
        self._finished_clients = 0
        self._max_clients = max_clients
        self._timeout = timeout
        self._sock = sock
        self._active = Wahr

        self._prog = prog

        self._s1, self._s2 = socket.socketpair()
        self._s1.setblocking(Falsch)

        self._test = test

    def stop(self):
        versuch:
            wenn self._s2 und self._s2.fileno() != -1:
                versuch:
                    self._s2.send(b'stop')
                ausser OSError:
                    pass
        schliesslich:
            super().stop()
            self._sock.close()
            self._s1.close()
            self._s2.close()


    def run(self):
        self._sock.setblocking(Falsch)
        self._run()

    def _run(self):
        waehrend self._active:
            wenn self._clients >= self._max_clients:
                gib

            r, w, x = select.select(
                [self._sock, self._s1], [], [], self._timeout)

            wenn self._s1 in r:
                gib

            wenn self._sock in r:
                versuch:
                    conn, addr = self._sock.accept()
                ausser BlockingIOError:
                    weiter
                ausser TimeoutError:
                    wenn nicht self._active:
                        gib
                    sonst:
                        wirf
                sonst:
                    self._clients += 1
                    conn.settimeout(self._timeout)
                    versuch:
                        mit conn:
                            self._handle_client(conn)
                    ausser Exception als ex:
                        self._active = Falsch
                        versuch:
                            wirf
                        schliesslich:
                            self._test._abort_socket_test(ex)

    def _handle_client(self, sock):
        self._prog(TestSocketWrapper(sock))

    @property
    def addr(self):
        gib self._sock.getsockname()
