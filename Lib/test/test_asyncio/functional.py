import asyncio
import asyncio.events
import contextlib
import os
import pprint
import select
import socket
import tempfile
import threading
from test import support


klasse FunctionalTestCaseMixin:

    def new_loop(self):
        return asyncio.new_event_loop()

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
        try:
            self.loop.close()

            wenn self.__unhandled_exceptions:
                print('Unexpected calls to loop.call_exception_handler():')
                pprint.pprint(self.__unhandled_exceptions)
                self.fail('unexpected calls to loop.call_exception_handler()')

        finally:
            asyncio.set_event_loop(Nichts)
            self.loop = Nichts

    def tcp_server(self, server_prog, *,
                   family=socket.AF_INET,
                   addr=Nichts,
                   timeout=support.LOOPBACK_TIMEOUT,
                   backlog=1,
                   max_clients=10):

        wenn addr is Nichts:
            wenn hasattr(socket, 'AF_UNIX') and family == socket.AF_UNIX:
                with tempfile.NamedTemporaryFile() as tmp:
                    addr = tmp.name
            sonst:
                addr = ('127.0.0.1', 0)

        sock = socket.create_server(addr, family=family, backlog=backlog)
        wenn timeout is Nichts:
            raise RuntimeError('timeout is required')
        wenn timeout <= 0:
            raise RuntimeError('only blocking sockets are supported')
        sock.settimeout(timeout)

        return TestThreadedServer(
            self, sock, server_prog, timeout, max_clients)

    def tcp_client(self, client_prog,
                   family=socket.AF_INET,
                   timeout=support.LOOPBACK_TIMEOUT):

        sock = socket.socket(family, socket.SOCK_STREAM)

        wenn timeout is Nichts:
            raise RuntimeError('timeout is required')
        wenn timeout <= 0:
            raise RuntimeError('only blocking sockets are supported')
        sock.settimeout(timeout)

        return TestThreadedClient(
            self, sock, client_prog, timeout)

    def unix_server(self, *args, **kwargs):
        wenn not hasattr(socket, 'AF_UNIX'):
            raise NotImplementedError
        return self.tcp_server(*args, family=socket.AF_UNIX, **kwargs)

    def unix_client(self, *args, **kwargs):
        wenn not hasattr(socket, 'AF_UNIX'):
            raise NotImplementedError
        return self.tcp_client(*args, family=socket.AF_UNIX, **kwargs)

    @contextlib.contextmanager
    def unix_sock_name(self):
        with tempfile.TemporaryDirectory() as td:
            fn = os.path.join(td, 'sock')
            try:
                yield fn
            finally:
                try:
                    os.unlink(fn)
                except OSError:
                    pass

    def _abort_socket_test(self, ex):
        try:
            self.loop.stop()
        finally:
            self.fail(ex)


##############################################################################
# Socket Testing Utilities
##############################################################################


klasse TestSocketWrapper:

    def __init__(self, sock):
        self.__sock = sock

    def recv_all(self, n):
        buf = b''
        while len(buf) < n:
            data = self.recv(n - len(buf))
            wenn data == b'':
                raise ConnectionAbortedError
            buf += data
        return buf

    def start_tls(self, ssl_context, *,
                  server_side=Falsch,
                  server_hostname=Nichts):

        ssl_sock = ssl_context.wrap_socket(
            self.__sock, server_side=server_side,
            server_hostname=server_hostname,
            do_handshake_on_connect=Falsch)

        try:
            ssl_sock.do_handshake()
        except:
            ssl_sock.close()
            raise
        finally:
            self.__sock.close()

        self.__sock = ssl_sock

    def __getattr__(self, name):
        return getattr(self.__sock, name)

    def __repr__(self):
        return '<{} {!r}>'.format(type(self).__name__, self.__sock)


klasse SocketThread(threading.Thread):

    def stop(self):
        self._active = Falsch
        self.join()

    def __enter__(self):
        self.start()
        return self

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
        try:
            self._prog(TestSocketWrapper(self._sock))
        except Exception as ex:
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
        try:
            wenn self._s2 and self._s2.fileno() != -1:
                try:
                    self._s2.send(b'stop')
                except OSError:
                    pass
        finally:
            super().stop()
            self._sock.close()
            self._s1.close()
            self._s2.close()


    def run(self):
        self._sock.setblocking(Falsch)
        self._run()

    def _run(self):
        while self._active:
            wenn self._clients >= self._max_clients:
                return

            r, w, x = select.select(
                [self._sock, self._s1], [], [], self._timeout)

            wenn self._s1 in r:
                return

            wenn self._sock in r:
                try:
                    conn, addr = self._sock.accept()
                except BlockingIOError:
                    continue
                except TimeoutError:
                    wenn not self._active:
                        return
                    sonst:
                        raise
                sonst:
                    self._clients += 1
                    conn.settimeout(self._timeout)
                    try:
                        with conn:
                            self._handle_client(conn)
                    except Exception as ex:
                        self._active = Falsch
                        try:
                            raise
                        finally:
                            self._test._abort_socket_test(ex)

    def _handle_client(self, sock):
        self._prog(TestSocketWrapper(sock))

    @property
    def addr(self):
        return self._sock.getsockname()
