"""Tests fuer unix_events.py."""

importiere contextlib
importiere errno
importiere io
importiere multiprocessing
von multiprocessing.util importiere _cleanup_tests als multiprocessing_cleanup_tests
importiere os
importiere signal
importiere socket
importiere stat
importiere sys
importiere time
importiere unittest
von unittest importiere mock

von test importiere support
von test.support importiere os_helper, warnings_helper
von test.support importiere socket_helper
von test.support importiere wait_process
von test.support importiere hashlib_helper

wenn sys.platform == 'win32':
    raise unittest.SkipTest('UNIX only')


importiere asyncio
von asyncio importiere unix_events
von test.test_asyncio importiere utils als test_utils


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


MOCK_ANY = mock.ANY


def EXITCODE(exitcode):
    gib 32768 + exitcode


def SIGNAL(signum):
    wenn nicht 1 <= signum <= 68:
        raise AssertionError(f'invalid signum {signum}')
    gib 32768 - signum


def close_pipe_transport(transport):
    # Don't call transport.close() because the event loop und the selector
    # are mocked
    wenn transport._pipe is Nichts:
        gib
    transport._pipe.close()
    transport._pipe = Nichts


@unittest.skipUnless(signal, 'Signals are nicht supported')
klasse SelectorEventLoopSignalTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = asyncio.SelectorEventLoop()
        self.set_event_loop(self.loop)

    def test_check_signal(self):
        self.assertRaises(
            TypeError, self.loop._check_signal, '1')
        self.assertRaises(
            ValueError, self.loop._check_signal, signal.NSIG + 1)

    def test_handle_signal_no_handler(self):
        self.loop._handle_signal(signal.NSIG + 1)

    def test_handle_signal_cancelled_handler(self):
        h = asyncio.Handle(mock.Mock(), (),
                           loop=mock.Mock())
        h.cancel()
        self.loop._signal_handlers[signal.NSIG + 1] = h
        self.loop.remove_signal_handler = mock.Mock()
        self.loop._handle_signal(signal.NSIG + 1)
        self.loop.remove_signal_handler.assert_called_with(signal.NSIG + 1)

    @mock.patch('asyncio.unix_events.signal')
    def test_add_signal_handler_setup_error(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals
        m_signal.set_wakeup_fd.side_effect = ValueError

        self.assertRaises(
            RuntimeError,
            self.loop.add_signal_handler,
            signal.SIGINT, lambda: Wahr)

    @mock.patch('asyncio.unix_events.signal')
    def test_add_signal_handler_coroutine_error(self, m_signal):
        m_signal.NSIG = signal.NSIG

        async def simple_coroutine():
            pass

        # callback must nicht be a coroutine function
        coro_func = simple_coroutine
        coro_obj = coro_func()
        self.addCleanup(coro_obj.close)
        fuer func in (coro_func, coro_obj):
            self.assertRaisesRegex(
                TypeError, 'coroutines cannot be used mit add_signal_handler',
                self.loop.add_signal_handler,
                signal.SIGINT, func)

    @mock.patch('asyncio.unix_events.signal')
    def test_add_signal_handler(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        cb = lambda: Wahr
        self.loop.add_signal_handler(signal.SIGHUP, cb)
        h = self.loop._signal_handlers.get(signal.SIGHUP)
        self.assertIsInstance(h, asyncio.Handle)
        self.assertEqual(h._callback, cb)

    @mock.patch('asyncio.unix_events.signal')
    def test_add_signal_handler_install_error(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        def set_wakeup_fd(fd):
            wenn fd == -1:
                raise ValueError()
        m_signal.set_wakeup_fd = set_wakeup_fd

        klasse Err(OSError):
            errno = errno.EFAULT
        m_signal.signal.side_effect = Err

        self.assertRaises(
            Err,
            self.loop.add_signal_handler,
            signal.SIGINT, lambda: Wahr)

    @mock.patch('asyncio.unix_events.signal')
    @mock.patch('asyncio.base_events.logger')
    def test_add_signal_handler_install_error2(self, m_logging, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        klasse Err(OSError):
            errno = errno.EINVAL
        m_signal.signal.side_effect = Err

        self.loop._signal_handlers[signal.SIGHUP] = lambda: Wahr
        self.assertRaises(
            RuntimeError,
            self.loop.add_signal_handler,
            signal.SIGINT, lambda: Wahr)
        self.assertFalsch(m_logging.info.called)
        self.assertEqual(1, m_signal.set_wakeup_fd.call_count)

    @mock.patch('asyncio.unix_events.signal')
    @mock.patch('asyncio.base_events.logger')
    def test_add_signal_handler_install_error3(self, m_logging, m_signal):
        klasse Err(OSError):
            errno = errno.EINVAL
        m_signal.signal.side_effect = Err
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        self.assertRaises(
            RuntimeError,
            self.loop.add_signal_handler,
            signal.SIGINT, lambda: Wahr)
        self.assertFalsch(m_logging.info.called)
        self.assertEqual(2, m_signal.set_wakeup_fd.call_count)

    @mock.patch('asyncio.unix_events.signal')
    def test_remove_signal_handler(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)

        self.assertWahr(
            self.loop.remove_signal_handler(signal.SIGHUP))
        self.assertWahr(m_signal.set_wakeup_fd.called)
        self.assertWahr(m_signal.signal.called)
        self.assertEqual(
            (signal.SIGHUP, m_signal.SIG_DFL), m_signal.signal.call_args[0])

    @mock.patch('asyncio.unix_events.signal')
    def test_remove_signal_handler_2(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.SIGINT = signal.SIGINT
        m_signal.valid_signals = signal.valid_signals

        self.loop.add_signal_handler(signal.SIGINT, lambda: Wahr)
        self.loop._signal_handlers[signal.SIGHUP] = object()
        m_signal.set_wakeup_fd.reset_mock()

        self.assertWahr(
            self.loop.remove_signal_handler(signal.SIGINT))
        self.assertFalsch(m_signal.set_wakeup_fd.called)
        self.assertWahr(m_signal.signal.called)
        self.assertEqual(
            (signal.SIGINT, m_signal.default_int_handler),
            m_signal.signal.call_args[0])

    @mock.patch('asyncio.unix_events.signal')
    @mock.patch('asyncio.base_events.logger')
    def test_remove_signal_handler_cleanup_error(self, m_logging, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals
        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)

        m_signal.set_wakeup_fd.side_effect = ValueError

        self.loop.remove_signal_handler(signal.SIGHUP)
        self.assertWahr(m_logging.info)

    @mock.patch('asyncio.unix_events.signal')
    def test_remove_signal_handler_error(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals
        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)

        m_signal.signal.side_effect = OSError

        self.assertRaises(
            OSError, self.loop.remove_signal_handler, signal.SIGHUP)

    @mock.patch('asyncio.unix_events.signal')
    def test_remove_signal_handler_error2(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals
        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)

        klasse Err(OSError):
            errno = errno.EINVAL
        m_signal.signal.side_effect = Err

        self.assertRaises(
            RuntimeError, self.loop.remove_signal_handler, signal.SIGHUP)

    @mock.patch('asyncio.unix_events.signal')
    def test_close(self, m_signal):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals

        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)
        self.loop.add_signal_handler(signal.SIGCHLD, lambda: Wahr)

        self.assertEqual(len(self.loop._signal_handlers), 2)

        m_signal.set_wakeup_fd.reset_mock()

        self.loop.close()

        self.assertEqual(len(self.loop._signal_handlers), 0)
        m_signal.set_wakeup_fd.assert_called_once_with(-1)

    @mock.patch('asyncio.unix_events.sys')
    @mock.patch('asyncio.unix_events.signal')
    def test_close_on_finalizing(self, m_signal, m_sys):
        m_signal.NSIG = signal.NSIG
        m_signal.valid_signals = signal.valid_signals
        self.loop.add_signal_handler(signal.SIGHUP, lambda: Wahr)

        self.assertEqual(len(self.loop._signal_handlers), 1)
        m_sys.is_finalizing.return_value = Wahr
        m_signal.signal.reset_mock()

        mit self.assertWarnsRegex(ResourceWarning,
                                   "skipping signal handlers removal"):
            self.loop.close()

        self.assertEqual(len(self.loop._signal_handlers), 0)
        self.assertFalsch(m_signal.signal.called)


@unittest.skipUnless(hasattr(socket, 'AF_UNIX'),
                     'UNIX Sockets are nicht supported')
klasse SelectorEventLoopUnixSocketTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = asyncio.SelectorEventLoop()
        self.set_event_loop(self.loop)

    @socket_helper.skip_unless_bind_unix_socket
    def test_create_unix_server_existing_path_sock(self):
        mit test_utils.unix_socket_path() als path:
            sock = socket.socket(socket.AF_UNIX)
            sock.bind(path)
            sock.listen(1)
            sock.close()

            coro = self.loop.create_unix_server(lambda: Nichts, path)
            srv = self.loop.run_until_complete(coro)
            srv.close()
            self.loop.run_until_complete(srv.wait_closed())

    @socket_helper.skip_unless_bind_unix_socket
    def test_create_unix_server_pathlike(self):
        mit test_utils.unix_socket_path() als path:
            path = os_helper.FakePath(path)
            srv_coro = self.loop.create_unix_server(lambda: Nichts, path)
            srv = self.loop.run_until_complete(srv_coro)
            srv.close()
            self.loop.run_until_complete(srv.wait_closed())

    def test_create_unix_connection_pathlike(self):
        mit test_utils.unix_socket_path() als path:
            path = os_helper.FakePath(path)
            coro = self.loop.create_unix_connection(lambda: Nichts, path)
            mit self.assertRaises(FileNotFoundError):
                # If path-like object weren't supported, the exception would be
                # different.
                self.loop.run_until_complete(coro)

    def test_create_unix_server_existing_path_nonsock(self):
        path = test_utils.gen_unix_socket_path()
        self.addCleanup(os_helper.unlink, path)
        # create the file
        open(path, "wb").close()

        coro = self.loop.create_unix_server(lambda: Nichts, path)
        mit self.assertRaisesRegex(OSError,
                                    'Address.*is already in use'):
            self.loop.run_until_complete(coro)

    def test_create_unix_server_ssl_bool(self):
        coro = self.loop.create_unix_server(lambda: Nichts, path='spam',
                                            ssl=Wahr)
        mit self.assertRaisesRegex(TypeError,
                                    'ssl argument must be an SSLContext'):
            self.loop.run_until_complete(coro)

    def test_create_unix_server_nopath_nosock(self):
        coro = self.loop.create_unix_server(lambda: Nichts, path=Nichts)
        mit self.assertRaisesRegex(ValueError,
                                    'path was nicht specified, und no sock'):
            self.loop.run_until_complete(coro)

    def test_create_unix_server_path_inetsock(self):
        sock = socket.socket()
        mit sock:
            coro = self.loop.create_unix_server(lambda: Nichts, path=Nichts,
                                                sock=sock)
            mit self.assertRaisesRegex(ValueError,
                                        'A UNIX Domain Stream.*was expected'):
                self.loop.run_until_complete(coro)

    def test_create_unix_server_path_dgram(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        mit sock:
            coro = self.loop.create_unix_server(lambda: Nichts, path=Nichts,
                                                sock=sock)
            mit self.assertRaisesRegex(ValueError,
                                        'A UNIX Domain Stream.*was expected'):
                self.loop.run_until_complete(coro)

    @unittest.skipUnless(hasattr(socket, 'SOCK_NONBLOCK'),
                         'no socket.SOCK_NONBLOCK (linux only)')
    @socket_helper.skip_unless_bind_unix_socket
    def test_create_unix_server_path_stream_bittype(self):
        fn = test_utils.gen_unix_socket_path()
        self.addCleanup(os_helper.unlink, fn)

        sock = socket.socket(socket.AF_UNIX,
                             socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
        mit sock:
            sock.bind(fn)
            coro = self.loop.create_unix_server(lambda: Nichts, path=Nichts,
                                                sock=sock)
            srv = self.loop.run_until_complete(coro)
            srv.close()
            self.loop.run_until_complete(srv.wait_closed())

    def test_create_unix_server_ssl_timeout_with_plain_sock(self):
        coro = self.loop.create_unix_server(lambda: Nichts, path='spam',
                                            ssl_handshake_timeout=1)
        mit self.assertRaisesRegex(
                ValueError,
                'ssl_handshake_timeout is only meaningful mit ssl'):
            self.loop.run_until_complete(coro)

    def test_create_unix_connection_path_inetsock(self):
        sock = socket.socket()
        mit sock:
            coro = self.loop.create_unix_connection(lambda: Nichts,
                                                    sock=sock)
            mit self.assertRaisesRegex(ValueError,
                                        'A UNIX Domain Stream.*was expected'):
                self.loop.run_until_complete(coro)

    @mock.patch('asyncio.unix_events.socket')
    def test_create_unix_server_bind_error(self, m_socket):
        # Ensure that the socket is closed on any bind error
        sock = mock.Mock()
        m_socket.socket.return_value = sock

        sock.bind.side_effect = OSError
        coro = self.loop.create_unix_server(lambda: Nichts, path="/test")
        mit self.assertRaises(OSError):
            self.loop.run_until_complete(coro)
        self.assertWahr(sock.close.called)

        sock.bind.side_effect = MemoryError
        coro = self.loop.create_unix_server(lambda: Nichts, path="/test")
        mit self.assertRaises(MemoryError):
            self.loop.run_until_complete(coro)
        self.assertWahr(sock.close.called)

    def test_create_unix_connection_path_sock(self):
        coro = self.loop.create_unix_connection(
            lambda: Nichts, os.devnull, sock=object())
        mit self.assertRaisesRegex(ValueError, 'path und sock can nicht be'):
            self.loop.run_until_complete(coro)

    def test_create_unix_connection_nopath_nosock(self):
        coro = self.loop.create_unix_connection(
            lambda: Nichts, Nichts)
        mit self.assertRaisesRegex(ValueError,
                                    'no path und sock were specified'):
            self.loop.run_until_complete(coro)

    def test_create_unix_connection_nossl_serverhost(self):
        coro = self.loop.create_unix_connection(
            lambda: Nichts, os.devnull, server_hostname='spam')
        mit self.assertRaisesRegex(ValueError,
                                    'server_hostname is only meaningful'):
            self.loop.run_until_complete(coro)

    def test_create_unix_connection_ssl_noserverhost(self):
        coro = self.loop.create_unix_connection(
            lambda: Nichts, os.devnull, ssl=Wahr)

        mit self.assertRaisesRegex(
            ValueError, 'you have to pass server_hostname when using ssl'):

            self.loop.run_until_complete(coro)

    def test_create_unix_connection_ssl_timeout_with_plain_sock(self):
        coro = self.loop.create_unix_connection(lambda: Nichts, path='spam',
                                            ssl_handshake_timeout=1)
        mit self.assertRaisesRegex(
                ValueError,
                'ssl_handshake_timeout is only meaningful mit ssl'):
            self.loop.run_until_complete(coro)


@unittest.skipUnless(hasattr(os, 'sendfile'),
                     'sendfile is nicht supported')
klasse SelectorEventLoopUnixSockSendfileTests(test_utils.TestCase):
    DATA = b"12345abcde" * 16 * 1024  # 160 KiB

    klasse MyProto(asyncio.Protocol):

        def __init__(self, loop):
            self.started = Falsch
            self.closed = Falsch
            self.data = bytearray()
            self.fut = loop.create_future()
            self.transport = Nichts
            self._ready = loop.create_future()

        def connection_made(self, transport):
            self.started = Wahr
            self.transport = transport
            self._ready.set_result(Nichts)

        def data_received(self, data):
            self.data.extend(data)

        def connection_lost(self, exc):
            self.closed = Wahr
            self.fut.set_result(Nichts)

        async def wait_closed(self):
            await self.fut

    @classmethod
    def setUpClass(cls):
        mit open(os_helper.TESTFN, 'wb') als fp:
            fp.write(cls.DATA)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        os_helper.unlink(os_helper.TESTFN)
        super().tearDownClass()

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.set_event_loop(self.loop)
        self.file = open(os_helper.TESTFN, 'rb')
        self.addCleanup(self.file.close)
        super().setUp()

    def make_socket(self, cleanup=Wahr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(Falsch)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
        wenn cleanup:
            self.addCleanup(sock.close)
        gib sock

    def run_loop(self, coro):
        gib self.loop.run_until_complete(coro)

    def prepare(self):
        sock = self.make_socket()
        proto = self.MyProto(self.loop)
        port = socket_helper.find_unused_port()
        srv_sock = self.make_socket(cleanup=Falsch)
        srv_sock.bind((socket_helper.HOST, port))
        server = self.run_loop(self.loop.create_server(
            lambda: proto, sock=srv_sock))
        self.run_loop(self.loop.sock_connect(sock, (socket_helper.HOST, port)))
        self.run_loop(proto._ready)

        def cleanup():
            proto.transport.close()
            self.run_loop(proto.wait_closed())

            server.close()
            self.run_loop(server.wait_closed())

        self.addCleanup(cleanup)

        gib sock, proto

    def test_sock_sendfile_not_available(self):
        sock, proto = self.prepare()
        mit mock.patch('asyncio.unix_events.os', spec=[]):
            mit self.assertRaisesRegex(asyncio.SendfileNotAvailableError,
                                        "os[.]sendfile[(][)] is nicht available"):
                self.run_loop(self.loop._sock_sendfile_native(sock, self.file,
                                                              0, Nichts))
        self.assertEqual(self.file.tell(), 0)

    def test_sock_sendfile_not_a_file(self):
        sock, proto = self.prepare()
        f = object()
        mit self.assertRaisesRegex(asyncio.SendfileNotAvailableError,
                                    "not a regular file"):
            self.run_loop(self.loop._sock_sendfile_native(sock, f,
                                                          0, Nichts))
        self.assertEqual(self.file.tell(), 0)

    def test_sock_sendfile_iobuffer(self):
        sock, proto = self.prepare()
        f = io.BytesIO()
        mit self.assertRaisesRegex(asyncio.SendfileNotAvailableError,
                                    "not a regular file"):
            self.run_loop(self.loop._sock_sendfile_native(sock, f,
                                                          0, Nichts))
        self.assertEqual(self.file.tell(), 0)

    def test_sock_sendfile_not_regular_file(self):
        sock, proto = self.prepare()
        f = mock.Mock()
        f.fileno.return_value = -1
        mit self.assertRaisesRegex(asyncio.SendfileNotAvailableError,
                                    "not a regular file"):
            self.run_loop(self.loop._sock_sendfile_native(sock, f,
                                                          0, Nichts))
        self.assertEqual(self.file.tell(), 0)

    def test_sock_sendfile_cancel1(self):
        sock, proto = self.prepare()

        fut = self.loop.create_future()
        fileno = self.file.fileno()
        self.loop._sock_sendfile_native_impl(fut, Nichts, sock, fileno,
                                             0, Nichts, len(self.DATA), 0)
        fut.cancel()
        mit contextlib.suppress(asyncio.CancelledError):
            self.run_loop(fut)
        mit self.assertRaises(KeyError):
            self.loop._selector.get_key(sock)

    def test_sock_sendfile_cancel2(self):
        sock, proto = self.prepare()

        fut = self.loop.create_future()
        fileno = self.file.fileno()
        self.loop._sock_sendfile_native_impl(fut, Nichts, sock, fileno,
                                             0, Nichts, len(self.DATA), 0)
        fut.cancel()
        self.loop._sock_sendfile_native_impl(fut, sock.fileno(), sock, fileno,
                                             0, Nichts, len(self.DATA), 0)
        mit self.assertRaises(KeyError):
            self.loop._selector.get_key(sock)

    def test_sock_sendfile_blocking_error(self):
        sock, proto = self.prepare()

        fileno = self.file.fileno()
        fut = mock.Mock()
        fut.cancelled.return_value = Falsch
        mit mock.patch('os.sendfile', side_effect=BlockingIOError()):
            self.loop._sock_sendfile_native_impl(fut, Nichts, sock, fileno,
                                                 0, Nichts, len(self.DATA), 0)
        key = self.loop._selector.get_key(sock)
        self.assertIsNotNichts(key)
        fut.add_done_callback.assert_called_once_with(mock.ANY)

    def test_sock_sendfile_os_error_first_call(self):
        sock, proto = self.prepare()

        fileno = self.file.fileno()
        fut = self.loop.create_future()
        mit mock.patch('os.sendfile', side_effect=OSError()):
            self.loop._sock_sendfile_native_impl(fut, Nichts, sock, fileno,
                                                 0, Nichts, len(self.DATA), 0)
        mit self.assertRaises(KeyError):
            self.loop._selector.get_key(sock)
        exc = fut.exception()
        self.assertIsInstance(exc, asyncio.SendfileNotAvailableError)
        self.assertEqual(0, self.file.tell())

    def test_sock_sendfile_os_error_next_call(self):
        sock, proto = self.prepare()

        fileno = self.file.fileno()
        fut = self.loop.create_future()
        err = OSError()
        mit mock.patch('os.sendfile', side_effect=err):
            self.loop._sock_sendfile_native_impl(fut, sock.fileno(),
                                                 sock, fileno,
                                                 1000, Nichts, len(self.DATA),
                                                 1000)
        mit self.assertRaises(KeyError):
            self.loop._selector.get_key(sock)
        exc = fut.exception()
        self.assertIs(exc, err)
        self.assertEqual(1000, self.file.tell())

    def test_sock_sendfile_exception(self):
        sock, proto = self.prepare()

        fileno = self.file.fileno()
        fut = self.loop.create_future()
        err = asyncio.SendfileNotAvailableError()
        mit mock.patch('os.sendfile', side_effect=err):
            self.loop._sock_sendfile_native_impl(fut, sock.fileno(),
                                                 sock, fileno,
                                                 1000, Nichts, len(self.DATA),
                                                 1000)
        mit self.assertRaises(KeyError):
            self.loop._selector.get_key(sock)
        exc = fut.exception()
        self.assertIs(exc, err)
        self.assertEqual(1000, self.file.tell())


klasse UnixReadPipeTransportTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.protocol = test_utils.make_test_protocol(asyncio.Protocol)
        self.pipe = mock.Mock(spec_set=io.RawIOBase)
        self.pipe.fileno.return_value = 5

        blocking_patcher = mock.patch('os.set_blocking')
        blocking_patcher.start()
        self.addCleanup(blocking_patcher.stop)

        fstat_patcher = mock.patch('os.fstat')
        m_fstat = fstat_patcher.start()
        st = mock.Mock()
        st.st_mode = stat.S_IFIFO
        m_fstat.return_value = st
        self.addCleanup(fstat_patcher.stop)

    def read_pipe_transport(self, waiter=Nichts):
        transport = unix_events._UnixReadPipeTransport(self.loop, self.pipe,
                                                       self.protocol,
                                                       waiter=waiter)
        self.addCleanup(close_pipe_transport, transport)
        gib transport

    def test_ctor(self):
        waiter = self.loop.create_future()
        tr = self.read_pipe_transport(waiter=waiter)
        self.loop.run_until_complete(waiter)

        self.protocol.connection_made.assert_called_with(tr)
        self.loop.assert_reader(5, tr._read_ready)
        self.assertIsNichts(waiter.result())

    @mock.patch('os.read')
    def test__read_ready(self, m_read):
        tr = self.read_pipe_transport()
        m_read.return_value = b'data'
        tr._read_ready()

        m_read.assert_called_with(5, tr.max_size)
        self.protocol.data_received.assert_called_with(b'data')

    @mock.patch('os.read')
    def test__read_ready_eof(self, m_read):
        tr = self.read_pipe_transport()
        m_read.return_value = b''
        tr._read_ready()

        m_read.assert_called_with(5, tr.max_size)
        self.assertFalsch(self.loop.readers)
        test_utils.run_briefly(self.loop)
        self.protocol.eof_received.assert_called_with()
        self.protocol.connection_lost.assert_called_with(Nichts)

    @mock.patch('os.read')
    def test__read_ready_blocked(self, m_read):
        tr = self.read_pipe_transport()
        m_read.side_effect = BlockingIOError
        tr._read_ready()

        m_read.assert_called_with(5, tr.max_size)
        test_utils.run_briefly(self.loop)
        self.assertFalsch(self.protocol.data_received.called)

    @mock.patch('asyncio.log.logger.error')
    @mock.patch('os.read')
    def test__read_ready_error(self, m_read, m_logexc):
        tr = self.read_pipe_transport()
        err = OSError()
        m_read.side_effect = err
        tr._close = mock.Mock()
        tr._read_ready()

        m_read.assert_called_with(5, tr.max_size)
        tr._close.assert_called_with(err)
        m_logexc.assert_called_with(
            test_utils.MockPattern(
                'Fatal read error on pipe transport'
                '\nprotocol:.*\ntransport:.*'),
            exc_info=(OSError, MOCK_ANY, MOCK_ANY))

    @mock.patch('os.read')
    def test_pause_reading(self, m_read):
        tr = self.read_pipe_transport()
        m = mock.Mock()
        self.loop.add_reader(5, m)
        tr.pause_reading()
        self.assertFalsch(self.loop.readers)

    @mock.patch('os.read')
    def test_resume_reading(self, m_read):
        tr = self.read_pipe_transport()
        tr.pause_reading()
        tr.resume_reading()
        self.loop.assert_reader(5, tr._read_ready)

    @mock.patch('os.read')
    def test_close(self, m_read):
        tr = self.read_pipe_transport()
        tr._close = mock.Mock()
        tr.close()
        tr._close.assert_called_with(Nichts)

    @mock.patch('os.read')
    def test_close_already_closing(self, m_read):
        tr = self.read_pipe_transport()
        tr._closing = Wahr
        tr._close = mock.Mock()
        tr.close()
        self.assertFalsch(tr._close.called)

    @mock.patch('os.read')
    def test__close(self, m_read):
        tr = self.read_pipe_transport()
        err = object()
        tr._close(err)
        self.assertWahr(tr.is_closing())
        self.assertFalsch(self.loop.readers)
        test_utils.run_briefly(self.loop)
        self.protocol.connection_lost.assert_called_with(err)

    def test__call_connection_lost(self):
        tr = self.read_pipe_transport()
        self.assertIsNotNichts(tr._protocol)
        self.assertIsNotNichts(tr._loop)

        err = Nichts
        tr._call_connection_lost(err)
        self.protocol.connection_lost.assert_called_with(err)
        self.pipe.close.assert_called_with()

        self.assertIsNichts(tr._protocol)
        self.assertIsNichts(tr._loop)

    def test__call_connection_lost_with_err(self):
        tr = self.read_pipe_transport()
        self.assertIsNotNichts(tr._protocol)
        self.assertIsNotNichts(tr._loop)

        err = OSError()
        tr._call_connection_lost(err)
        self.protocol.connection_lost.assert_called_with(err)
        self.pipe.close.assert_called_with()

        self.assertIsNichts(tr._protocol)
        self.assertIsNichts(tr._loop)

    def test_pause_reading_on_closed_pipe(self):
        tr = self.read_pipe_transport()
        tr.close()
        test_utils.run_briefly(self.loop)
        self.assertIsNichts(tr._loop)
        tr.pause_reading()

    def test_pause_reading_on_paused_pipe(self):
        tr = self.read_pipe_transport()
        tr.pause_reading()
        # the second call should do nothing
        tr.pause_reading()

    def test_resume_reading_on_closed_pipe(self):
        tr = self.read_pipe_transport()
        tr.close()
        test_utils.run_briefly(self.loop)
        self.assertIsNichts(tr._loop)
        tr.resume_reading()

    def test_resume_reading_on_paused_pipe(self):
        tr = self.read_pipe_transport()
        # the pipe is nicht paused
        # resuming should do nothing
        tr.resume_reading()


klasse UnixWritePipeTransportTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = self.new_test_loop()
        self.protocol = test_utils.make_test_protocol(asyncio.BaseProtocol)
        self.pipe = mock.Mock(spec_set=io.RawIOBase)
        self.pipe.fileno.return_value = 5

        blocking_patcher = mock.patch('os.set_blocking')
        blocking_patcher.start()
        self.addCleanup(blocking_patcher.stop)

        fstat_patcher = mock.patch('os.fstat')
        m_fstat = fstat_patcher.start()
        st = mock.Mock()
        st.st_mode = stat.S_IFSOCK
        m_fstat.return_value = st
        self.addCleanup(fstat_patcher.stop)

    def write_pipe_transport(self, waiter=Nichts):
        transport = unix_events._UnixWritePipeTransport(self.loop, self.pipe,
                                                        self.protocol,
                                                        waiter=waiter)
        self.addCleanup(close_pipe_transport, transport)
        gib transport

    def test_ctor(self):
        waiter = self.loop.create_future()
        tr = self.write_pipe_transport(waiter=waiter)
        self.loop.run_until_complete(waiter)

        self.protocol.connection_made.assert_called_with(tr)
        self.loop.assert_reader(5, tr._read_ready)
        self.assertEqual(Nichts, waiter.result())

    def test_can_write_eof(self):
        tr = self.write_pipe_transport()
        self.assertWahr(tr.can_write_eof())

    @mock.patch('os.write')
    def test_write(self, m_write):
        tr = self.write_pipe_transport()
        m_write.return_value = 4
        tr.write(b'data')
        m_write.assert_called_with(5, b'data')
        self.assertFalsch(self.loop.writers)
        self.assertEqual(bytearray(), tr._buffer)

    @mock.patch('os.write')
    def test_write_no_data(self, m_write):
        tr = self.write_pipe_transport()
        tr.write(b'')
        self.assertFalsch(m_write.called)
        self.assertFalsch(self.loop.writers)
        self.assertEqual(bytearray(b''), tr._buffer)

    @mock.patch('os.write')
    def test_write_partial(self, m_write):
        tr = self.write_pipe_transport()
        m_write.return_value = 2
        tr.write(b'data')
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'ta'), tr._buffer)

    @mock.patch('os.write')
    def test_write_buffer(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'previous')
        tr.write(b'data')
        self.assertFalsch(m_write.called)
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'previousdata'), tr._buffer)

    @mock.patch('os.write')
    def test_write_again(self, m_write):
        tr = self.write_pipe_transport()
        m_write.side_effect = BlockingIOError()
        tr.write(b'data')
        m_write.assert_called_with(5, bytearray(b'data'))
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'data'), tr._buffer)

    @mock.patch('asyncio.unix_events.logger')
    @mock.patch('os.write')
    def test_write_err(self, m_write, m_log):
        tr = self.write_pipe_transport()
        err = OSError()
        m_write.side_effect = err
        tr._fatal_error = mock.Mock()
        tr.write(b'data')
        m_write.assert_called_with(5, b'data')
        self.assertFalsch(self.loop.writers)
        self.assertEqual(bytearray(), tr._buffer)
        tr._fatal_error.assert_called_with(
                            err,
                            'Fatal write error on pipe transport')
        self.assertEqual(1, tr._conn_lost)

        tr.write(b'data')
        self.assertEqual(2, tr._conn_lost)
        tr.write(b'data')
        tr.write(b'data')
        tr.write(b'data')
        tr.write(b'data')
        # This is a bit overspecified. :-(
        m_log.warning.assert_called_with(
            'pipe closed by peer oder os.write(pipe, data) raised exception.')
        tr.close()

    @mock.patch('os.write')
    def test_write_close(self, m_write):
        tr = self.write_pipe_transport()
        tr._read_ready()  # pipe was closed by peer

        tr.write(b'data')
        self.assertEqual(tr._conn_lost, 1)
        tr.write(b'data')
        self.assertEqual(tr._conn_lost, 2)

    def test__read_ready(self):
        tr = self.write_pipe_transport()
        tr._read_ready()
        self.assertFalsch(self.loop.readers)
        self.assertFalsch(self.loop.writers)
        self.assertWahr(tr.is_closing())
        test_utils.run_briefly(self.loop)
        self.protocol.connection_lost.assert_called_with(Nichts)

    @mock.patch('os.write')
    def test__write_ready(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'data')
        m_write.return_value = 4
        tr._write_ready()
        self.assertFalsch(self.loop.writers)
        self.assertEqual(bytearray(), tr._buffer)

    @mock.patch('os.write')
    def test__write_ready_partial(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'data')
        m_write.return_value = 3
        tr._write_ready()
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'a'), tr._buffer)

    @mock.patch('os.write')
    def test__write_ready_again(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'data')
        m_write.side_effect = BlockingIOError()
        tr._write_ready()
        m_write.assert_called_with(5, bytearray(b'data'))
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'data'), tr._buffer)

    @mock.patch('os.write')
    def test__write_ready_empty(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'data')
        m_write.return_value = 0
        tr._write_ready()
        m_write.assert_called_with(5, bytearray(b'data'))
        self.loop.assert_writer(5, tr._write_ready)
        self.assertEqual(bytearray(b'data'), tr._buffer)

    @mock.patch('asyncio.log.logger.error')
    @mock.patch('os.write')
    def test__write_ready_err(self, m_write, m_logexc):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._buffer = bytearray(b'data')
        m_write.side_effect = err = OSError()
        tr._write_ready()
        self.assertFalsch(self.loop.writers)
        self.assertFalsch(self.loop.readers)
        self.assertEqual(bytearray(), tr._buffer)
        self.assertWahr(tr.is_closing())
        m_logexc.assert_not_called()
        self.assertEqual(1, tr._conn_lost)
        test_utils.run_briefly(self.loop)
        self.protocol.connection_lost.assert_called_with(err)

    @mock.patch('os.write')
    def test__write_ready_closing(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        tr._closing = Wahr
        tr._buffer = bytearray(b'data')
        m_write.return_value = 4
        tr._write_ready()
        self.assertFalsch(self.loop.writers)
        self.assertFalsch(self.loop.readers)
        self.assertEqual(bytearray(), tr._buffer)
        self.protocol.connection_lost.assert_called_with(Nichts)
        self.pipe.close.assert_called_with()

    @mock.patch('os.write')
    def test_abort(self, m_write):
        tr = self.write_pipe_transport()
        self.loop.add_writer(5, tr._write_ready)
        self.loop.add_reader(5, tr._read_ready)
        tr._buffer = [b'da', b'ta']
        tr.abort()
        self.assertFalsch(m_write.called)
        self.assertFalsch(self.loop.readers)
        self.assertFalsch(self.loop.writers)
        self.assertEqual([], tr._buffer)
        self.assertWahr(tr.is_closing())
        test_utils.run_briefly(self.loop)
        self.protocol.connection_lost.assert_called_with(Nichts)

    def test__call_connection_lost(self):
        tr = self.write_pipe_transport()
        self.assertIsNotNichts(tr._protocol)
        self.assertIsNotNichts(tr._loop)

        err = Nichts
        tr._call_connection_lost(err)
        self.protocol.connection_lost.assert_called_with(err)
        self.pipe.close.assert_called_with()

        self.assertIsNichts(tr._protocol)
        self.assertIsNichts(tr._loop)

    def test__call_connection_lost_with_err(self):
        tr = self.write_pipe_transport()
        self.assertIsNotNichts(tr._protocol)
        self.assertIsNotNichts(tr._loop)

        err = OSError()
        tr._call_connection_lost(err)
        self.protocol.connection_lost.assert_called_with(err)
        self.pipe.close.assert_called_with()

        self.assertIsNichts(tr._protocol)
        self.assertIsNichts(tr._loop)

    def test_close(self):
        tr = self.write_pipe_transport()
        tr.write_eof = mock.Mock()
        tr.close()
        tr.write_eof.assert_called_with()

        # closing the transport twice must nicht fail
        tr.close()

    def test_close_closing(self):
        tr = self.write_pipe_transport()
        tr.write_eof = mock.Mock()
        tr._closing = Wahr
        tr.close()
        self.assertFalsch(tr.write_eof.called)

    def test_write_eof(self):
        tr = self.write_pipe_transport()
        tr.write_eof()
        self.assertWahr(tr.is_closing())
        self.assertFalsch(self.loop.readers)
        test_utils.run_briefly(self.loop)
        self.protocol.connection_lost.assert_called_with(Nichts)

    def test_write_eof_pending(self):
        tr = self.write_pipe_transport()
        tr._buffer = [b'data']
        tr.write_eof()
        self.assertWahr(tr.is_closing())
        self.assertFalsch(self.protocol.connection_lost.called)


klasse TestFunctional(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        asyncio.set_event_loop(Nichts)

    def test_add_reader_invalid_argument(self):
        def assert_raises():
            gib self.assertRaisesRegex(ValueError, r'Invalid file object')

        cb = lambda: Nichts

        mit assert_raises():
            self.loop.add_reader(object(), cb)
        mit assert_raises():
            self.loop.add_writer(object(), cb)

        mit assert_raises():
            self.loop.remove_reader(object())
        mit assert_raises():
            self.loop.remove_writer(object())

    def test_add_reader_or_writer_transport_fd(self):
        def assert_raises():
            gib self.assertRaisesRegex(
                RuntimeError,
                r'File descriptor .* is used by transport')

        async def runner():
            tr, pr = await self.loop.create_connection(
                lambda: asyncio.Protocol(), sock=rsock)

            try:
                cb = lambda: Nichts

                mit assert_raises():
                    self.loop.add_reader(rsock, cb)
                mit assert_raises():
                    self.loop.add_reader(rsock.fileno(), cb)

                mit assert_raises():
                    self.loop.remove_reader(rsock)
                mit assert_raises():
                    self.loop.remove_reader(rsock.fileno())

                mit assert_raises():
                    self.loop.add_writer(rsock, cb)
                mit assert_raises():
                    self.loop.add_writer(rsock.fileno(), cb)

                mit assert_raises():
                    self.loop.remove_writer(rsock)
                mit assert_raises():
                    self.loop.remove_writer(rsock.fileno())

            finally:
                tr.close()

        rsock, wsock = socket.socketpair()
        try:
            self.loop.run_until_complete(runner())
        finally:
            rsock.close()
            wsock.close()


@support.requires_fork()
klasse TestFork(unittest.IsolatedAsyncioTestCase):

    async def test_fork_not_share_event_loop(self):
        mit warnings_helper.ignore_fork_in_thread_deprecation_warnings():
            # The forked process should nicht share the event loop mit the parent
            loop = asyncio.get_running_loop()
            r, w = os.pipe()
            self.addCleanup(os.close, r)
            self.addCleanup(os.close, w)
            pid = os.fork()
            wenn pid == 0:
                # child
                try:
                    loop = asyncio.get_event_loop()
                    os.write(w, b'LOOP:' + str(id(loop)).encode())
                except RuntimeError:
                    os.write(w, b'NO LOOP')
                except BaseException als e:
                    os.write(w, b'ERROR:' + ascii(e).encode())
                finally:
                    os._exit(0)
            sonst:
                # parent
                result = os.read(r, 100)
                self.assertEqual(result, b'NO LOOP')
                wait_process(pid, exitcode=0)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @hashlib_helper.requires_hashdigest('md5')
    @support.skip_if_sanitizer("TSAN doesn't support threads after fork", thread=Wahr)
    def test_fork_signal_handling(self):
        self.addCleanup(multiprocessing_cleanup_tests)

        # Sending signal to the forked process should nicht affect the parent
        # process
        ctx = multiprocessing.get_context('fork')
        manager = ctx.Manager()
        self.addCleanup(manager.shutdown)
        child_started = manager.Event()
        child_handled = manager.Event()
        parent_handled = manager.Event()

        def child_main():
            def on_sigterm(*args):
                child_handled.set()
                sys.exit()

            signal.signal(signal.SIGTERM, on_sigterm)
            child_started.set()
            waehrend Wahr:
                time.sleep(1)

        async def main():
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGTERM, lambda *args: parent_handled.set())

            process = ctx.Process(target=child_main)
            process.start()
            child_started.wait()
            os.kill(process.pid, signal.SIGTERM)
            process.join(timeout=support.SHORT_TIMEOUT)

            async def func():
                await asyncio.sleep(0.1)
                gib 42

            # Test parent's loop is still functional
            self.assertEqual(await asyncio.create_task(func()), 42)

        asyncio.run(main())

        child_handled.wait(timeout=support.SHORT_TIMEOUT)
        self.assertFalsch(parent_handled.is_set())
        self.assertWahr(child_handled.is_set())

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @hashlib_helper.requires_hashdigest('md5')
    @support.skip_if_sanitizer("TSAN doesn't support threads after fork", thread=Wahr)
    def test_fork_asyncio_run(self):
        self.addCleanup(multiprocessing_cleanup_tests)

        ctx = multiprocessing.get_context('fork')
        manager = ctx.Manager()
        self.addCleanup(manager.shutdown)
        result = manager.Value('i', 0)

        async def child_main():
            await asyncio.sleep(0.1)
            result.value = 42

        process = ctx.Process(target=lambda: asyncio.run(child_main()))
        process.start()
        process.join()

        self.assertEqual(result.value, 42)

    @warnings_helper.ignore_fork_in_thread_deprecation_warnings()
    @hashlib_helper.requires_hashdigest('md5')
    @support.skip_if_sanitizer("TSAN doesn't support threads after fork", thread=Wahr)
    def test_fork_asyncio_subprocess(self):
        self.addCleanup(multiprocessing_cleanup_tests)

        ctx = multiprocessing.get_context('fork')
        manager = ctx.Manager()
        self.addCleanup(manager.shutdown)
        result = manager.Value('i', 1)

        async def child_main():
            proc = await asyncio.create_subprocess_exec(sys.executable, '-c', 'pass')
            result.value = await proc.wait()

        process = ctx.Process(target=lambda: asyncio.run(child_main()))
        process.start()
        process.join()

        self.assertEqual(result.value, 0)

wenn __name__ == '__main__':
    unittest.main()
