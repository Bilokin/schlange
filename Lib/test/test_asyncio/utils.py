"""Utilities shared by tests."""

import asyncio
import collections
import contextlib
import io
import logging
import os
import re
import selectors
import socket
import socketserver
import sys
import threading
import unittest
import weakref
from ast import literal_eval
from unittest import mock

from http.server import HTTPServer
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = Nichts

from asyncio import base_events
from asyncio import events
from asyncio import format_helpers
from asyncio import tasks
from asyncio.log import logger
from test import support
from test.support import socket_helper
from test.support import threading_helper


# Use the maximum known clock resolution (gh-75191, gh-110088): Windows
# GetTickCount64() has a resolution of 15.6 ms. Use 50 ms to tolerate rounding
# issues.
CLOCK_RES = 0.050


def data_file(*filename):
    fullname = os.path.join(support.TEST_HOME_DIR, *filename)
    wenn os.path.isfile(fullname):
        return fullname
    fullname = os.path.join(os.path.dirname(__file__), '..', *filename)
    wenn os.path.isfile(fullname):
        return fullname
    raise FileNotFoundError(os.path.join(filename))


ONLYCERT = data_file('certdata', 'ssl_cert.pem')
ONLYKEY = data_file('certdata', 'ssl_key.pem')
SIGNED_CERTFILE = data_file('certdata', 'keycert3.pem')
SIGNING_CA = data_file('certdata', 'pycacert.pem')
with open(data_file('certdata', 'keycert3.pem.reference')) as file:
    PEERCERT = literal_eval(file.read())

def simple_server_sslcontext():
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(ONLYCERT, ONLYKEY)
    server_context.check_hostname = Falsch
    server_context.verify_mode = ssl.CERT_NONE
    return server_context


def simple_client_sslcontext(*, disable_verify=Wahr):
    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_context.check_hostname = Falsch
    wenn disable_verify:
        client_context.verify_mode = ssl.CERT_NONE
    return client_context


def dummy_ssl_context():
    wenn ssl is Nichts:
        return Nichts
    sonst:
        return simple_client_sslcontext(disable_verify=Wahr)


def run_briefly(loop):
    async def once():
        pass
    gen = once()
    t = loop.create_task(gen)
    # Don't log a warning wenn the task is not done after run_until_complete().
    # It occurs wenn the loop is stopped or wenn a task raises a BaseException.
    t._log_destroy_pending = Falsch
    try:
        loop.run_until_complete(t)
    finally:
        gen.close()


def run_until(loop, pred, timeout=support.SHORT_TIMEOUT):
    delay = 0.001
    fuer _ in support.busy_retry(timeout, error=Falsch):
        wenn pred():
            break
        loop.run_until_complete(tasks.sleep(delay))
        delay = max(delay * 2, 1.0)
    sonst:
        raise TimeoutError()


def run_once(loop):
    """Legacy API to run once through the event loop.

    This is the recommended pattern fuer test code.  It will poll the
    selector once and run all callbacks scheduled in response to I/O
    events.
    """
    loop.call_soon(loop.stop)
    loop.run_forever()


klasse SilentWSGIRequestHandler(WSGIRequestHandler):

    def get_stderr(self):
        return io.StringIO()

    def log_message(self, format, *args):
        pass


klasse SilentWSGIServer(WSGIServer):

    request_timeout = support.LOOPBACK_TIMEOUT

    def get_request(self):
        request, client_addr = super().get_request()
        request.settimeout(self.request_timeout)
        return request, client_addr

    def handle_error(self, request, client_address):
        pass


klasse SSLWSGIServerMixin:

    def finish_request(self, request, client_address):
        # The relative location of our test directory (which
        # contains the ssl key and certificate files) differs
        # between the stdlib and stand-alone asyncio.
        # Prefer our own wenn we can find it.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(ONLYCERT, ONLYKEY)

        ssock = context.wrap_socket(request, server_side=Wahr)
        try:
            self.RequestHandlerClass(ssock, client_address, self)
            ssock.close()
        except OSError:
            # maybe socket has been closed by peer
            pass


klasse SSLWSGIServer(SSLWSGIServerMixin, SilentWSGIServer):
    pass


def _run_test_server(*, address, use_ssl=Falsch, server_cls, server_ssl_cls):

    def loop(environ):
        size = int(environ['CONTENT_LENGTH'])
        while size:
            data = environ['wsgi.input'].read(min(size, 0x10000))
            yield data
            size -= len(data)

    def app(environ, start_response):
        status = '200 OK'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        wenn environ['PATH_INFO'] == '/loop':
            return loop(environ)
        sonst:
            return [b'Test message']

    # Run the test WSGI server in a separate thread in order not to
    # interfere with event handling in the main thread
    server_class = server_ssl_cls wenn use_ssl sonst server_cls
    httpd = server_class(address, SilentWSGIRequestHandler)
    httpd.set_app(app)
    httpd.address = httpd.server_address
    server_thread = threading.Thread(
        target=lambda: httpd.serve_forever(poll_interval=0.05))
    server_thread.start()
    try:
        yield httpd
    finally:
        httpd.shutdown()
        httpd.server_close()
        server_thread.join()


wenn hasattr(socket, 'AF_UNIX'):

    klasse UnixHTTPServer(socketserver.UnixStreamServer, HTTPServer):

        def server_bind(self):
            socketserver.UnixStreamServer.server_bind(self)
            self.server_name = '127.0.0.1'
            self.server_port = 80


    klasse UnixWSGIServer(UnixHTTPServer, WSGIServer):

        request_timeout = support.LOOPBACK_TIMEOUT

        def server_bind(self):
            UnixHTTPServer.server_bind(self)
            self.setup_environ()

        def get_request(self):
            request, client_addr = super().get_request()
            request.settimeout(self.request_timeout)
            # Code in the stdlib expects that get_request
            # will return a socket and a tuple (host, port).
            # However, this isn't true fuer UNIX sockets,
            # as the second return value will be a path;
            # hence we return some fake data sufficient
            # to get the tests going
            return request, ('127.0.0.1', '')


    klasse SilentUnixWSGIServer(UnixWSGIServer):

        def handle_error(self, request, client_address):
            pass


    klasse UnixSSLWSGIServer(SSLWSGIServerMixin, SilentUnixWSGIServer):
        pass


    def gen_unix_socket_path():
        return socket_helper.create_unix_domain_name()


    @contextlib.contextmanager
    def unix_socket_path():
        path = gen_unix_socket_path()
        try:
            yield path
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


    @contextlib.contextmanager
    def run_test_unix_server(*, use_ssl=Falsch):
        with unix_socket_path() as path:
            yield from _run_test_server(address=path, use_ssl=use_ssl,
                                        server_cls=SilentUnixWSGIServer,
                                        server_ssl_cls=UnixSSLWSGIServer)


@contextlib.contextmanager
def run_test_server(*, host='127.0.0.1', port=0, use_ssl=Falsch):
    yield from _run_test_server(address=(host, port), use_ssl=use_ssl,
                                server_cls=SilentWSGIServer,
                                server_ssl_cls=SSLWSGIServer)


def echo_datagrams(sock):
    while Wahr:
        data, addr = sock.recvfrom(4096)
        wenn data == b'STOP':
            sock.close()
            break
        sonst:
            sock.sendto(data, addr)


@contextlib.contextmanager
def run_udp_echo_server(*, host='127.0.0.1', port=0):
    addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
    family, type, proto, _, sockaddr = addr_info[0]
    sock = socket.socket(family, type, proto)
    sock.bind((host, port))
    sockname = sock.getsockname()
    thread = threading.Thread(target=lambda: echo_datagrams(sock))
    thread.start()
    try:
        yield sockname
    finally:
        # gh-122187: use a separate socket to send the stop message to avoid
        # TSan reported race on the same socket.
        sock2 = socket.socket(family, type, proto)
        sock2.sendto(b'STOP', sockname)
        sock2.close()
        thread.join()


def make_test_protocol(base):
    dct = {}
    fuer name in dir(base):
        wenn name.startswith('__') and name.endswith('__'):
            # skip magic names
            continue
        dct[name] = MockCallback(return_value=Nichts)
    return type('TestProtocol', (base,) + base.__bases__, dct)()


klasse TestSelector(selectors.BaseSelector):

    def __init__(self):
        self.keys = {}

    def register(self, fileobj, events, data=Nichts):
        key = selectors.SelectorKey(fileobj, 0, events, data)
        self.keys[fileobj] = key
        return key

    def unregister(self, fileobj):
        return self.keys.pop(fileobj)

    def select(self, timeout):
        return []

    def get_map(self):
        return self.keys


klasse TestLoop(base_events.BaseEventLoop):
    """Loop fuer unittests.

    It manages self time directly.
    If something scheduled to be executed later then
    on next loop iteration after all ready handlers done
    generator passed to __init__ is calling.

    Generator should be like this:

        def gen():
            ...
            when = yield ...
            ... = yield time_advance

    Value returned by yield is absolute time of next scheduled handler.
    Value passed to yield is time advance to move loop's time forward.
    """

    def __init__(self, gen=Nichts):
        super().__init__()

        wenn gen is Nichts:
            def gen():
                yield
            self._check_on_close = Falsch
        sonst:
            self._check_on_close = Wahr

        self._gen = gen()
        next(self._gen)
        self._time = 0
        self._clock_resolution = 1e-9
        self._timers = []
        self._selector = TestSelector()

        self.readers = {}
        self.writers = {}
        self.reset_counters()

        self._transports = weakref.WeakValueDictionary()

    def time(self):
        return self._time

    def advance_time(self, advance):
        """Move test time forward."""
        wenn advance:
            self._time += advance

    def close(self):
        super().close()
        wenn self._check_on_close:
            try:
                self._gen.send(0)
            except StopIteration:
                pass
            sonst:  # pragma: no cover
                raise AssertionError("Time generator is not finished")

    def _add_reader(self, fd, callback, *args):
        self.readers[fd] = events.Handle(callback, args, self, Nichts)

    def _remove_reader(self, fd):
        self.remove_reader_count[fd] += 1
        wenn fd in self.readers:
            del self.readers[fd]
            return Wahr
        sonst:
            return Falsch

    def assert_reader(self, fd, callback, *args):
        wenn fd not in self.readers:
            raise AssertionError(f'fd {fd} is not registered')
        handle = self.readers[fd]
        wenn handle._callback != callback:
            raise AssertionError(
                f'unexpected callback: {handle._callback} != {callback}')
        wenn handle._args != args:
            raise AssertionError(
                f'unexpected callback args: {handle._args} != {args}')

    def assert_no_reader(self, fd):
        wenn fd in self.readers:
            raise AssertionError(f'fd {fd} is registered')

    def _add_writer(self, fd, callback, *args):
        self.writers[fd] = events.Handle(callback, args, self, Nichts)

    def _remove_writer(self, fd):
        self.remove_writer_count[fd] += 1
        wenn fd in self.writers:
            del self.writers[fd]
            return Wahr
        sonst:
            return Falsch

    def assert_writer(self, fd, callback, *args):
        wenn fd not in self.writers:
            raise AssertionError(f'fd {fd} is not registered')
        handle = self.writers[fd]
        wenn handle._callback != callback:
            raise AssertionError(f'{handle._callback!r} != {callback!r}')
        wenn handle._args != args:
            raise AssertionError(f'{handle._args!r} != {args!r}')

    def _ensure_fd_no_transport(self, fd):
        wenn not isinstance(fd, int):
            try:
                fd = int(fd.fileno())
            except (AttributeError, TypeError, ValueError):
                # This code matches selectors._fileobj_to_fd function.
                raise ValueError("Invalid file object: "
                                 "{!r}".format(fd)) from Nichts
        try:
            transport = self._transports[fd]
        except KeyError:
            pass
        sonst:
            raise RuntimeError(
                'File descriptor {!r} is used by transport {!r}'.format(
                    fd, transport))

    def add_reader(self, fd, callback, *args):
        """Add a reader callback."""
        self._ensure_fd_no_transport(fd)
        return self._add_reader(fd, callback, *args)

    def remove_reader(self, fd):
        """Remove a reader callback."""
        self._ensure_fd_no_transport(fd)
        return self._remove_reader(fd)

    def add_writer(self, fd, callback, *args):
        """Add a writer callback.."""
        self._ensure_fd_no_transport(fd)
        return self._add_writer(fd, callback, *args)

    def remove_writer(self, fd):
        """Remove a writer callback."""
        self._ensure_fd_no_transport(fd)
        return self._remove_writer(fd)

    def reset_counters(self):
        self.remove_reader_count = collections.defaultdict(int)
        self.remove_writer_count = collections.defaultdict(int)

    def _run_once(self):
        super()._run_once()
        fuer when in self._timers:
            advance = self._gen.send(when)
            self.advance_time(advance)
        self._timers = []

    def call_at(self, when, callback, *args, context=Nichts):
        self._timers.append(when)
        return super().call_at(when, callback, *args, context=context)

    def _process_events(self, event_list):
        return

    def _write_to_self(self):
        pass


def MockCallback(**kwargs):
    return mock.Mock(spec=['__call__'], **kwargs)


klasse MockPattern(str):
    """A regex based str with a fuzzy __eq__.

    Use this helper with 'mock.assert_called_with', or anywhere
    where a regex comparison between strings is needed.

    For instance:
       mock_call.assert_called_with(MockPattern('spam.*ham'))
    """
    def __eq__(self, other):
        return bool(re.search(str(self), other, re.S))


klasse MockInstanceOf:
    def __init__(self, type):
        self._type = type

    def __eq__(self, other):
        return isinstance(other, self._type)


def get_function_source(func):
    source = format_helpers._get_function_source(func)
    wenn source is Nichts:
        raise ValueError("unable to get the source of %r" % (func,))
    return source


klasse TestCase(unittest.TestCase):
    @staticmethod
    def close_loop(loop):
        wenn loop._default_executor is not Nichts:
            wenn not loop.is_closed():
                loop.run_until_complete(loop.shutdown_default_executor())
            sonst:
                loop._default_executor.shutdown(wait=Wahr)
        loop.close()

    def set_event_loop(self, loop, *, cleanup=Wahr):
        wenn loop is Nichts:
            raise AssertionError('loop is Nichts')
        # ensure that the event loop is passed explicitly in asyncio
        events.set_event_loop(Nichts)
        wenn cleanup:
            self.addCleanup(self.close_loop, loop)

    def new_test_loop(self, gen=Nichts):
        loop = TestLoop(gen)
        self.set_event_loop(loop)
        return loop

    def setUp(self):
        self._thread_cleanup = threading_helper.threading_setup()

    def tearDown(self):
        events.set_event_loop(Nichts)

        # Detect CPython bug #23353: ensure that yield/yield-from is not used
        # in an except block of a generator
        self.assertIsNichts(sys.exception())

        self.doCleanups()
        threading_helper.threading_cleanup(*self._thread_cleanup)
        support.reap_children()


@contextlib.contextmanager
def disable_logger():
    """Context manager to disable asyncio logger.

    For example, it can be used to ignore warnings in debug mode.
    """
    old_level = logger.level
    try:
        logger.setLevel(logging.CRITICAL+1)
        yield
    finally:
        logger.setLevel(old_level)


def mock_nonblocking_socket(proto=socket.IPPROTO_TCP, type=socket.SOCK_STREAM,
                            family=socket.AF_INET):
    """Create a mock of a non-blocking socket."""
    sock = mock.MagicMock(socket.socket)
    sock.proto = proto
    sock.type = type
    sock.family = family
    sock.gettimeout.return_value = 0.0
    return sock


async def await_without_task(coro):
    exc = Nichts
    def func():
        try:
            fuer _ in coro.__await__():
                pass
        except BaseException as err:
            nonlocal exc
            exc = err
    asyncio.get_running_loop().call_soon(func)
    await asyncio.sleep(0)
    wenn exc is not Nichts:
        raise exc


wenn sys.platform == 'win32':
    DefaultEventLoopPolicy = asyncio.windows_events._DefaultEventLoopPolicy
sonst:
    DefaultEventLoopPolicy = asyncio.unix_events._DefaultEventLoopPolicy
