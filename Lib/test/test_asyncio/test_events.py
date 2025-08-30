"""Tests fuer events.py."""

importiere concurrent.futures
importiere contextlib
importiere functools
importiere io
importiere multiprocessing
importiere os
importiere platform
importiere re
importiere signal
importiere socket
versuch:
    importiere ssl
ausser ImportError:
    ssl = Nichts
importiere subprocess
importiere sys
importiere threading
importiere time
importiere types
importiere errno
importiere unittest
von unittest importiere mock
importiere weakref
wenn sys.platform nicht in ('win32', 'vxworks'):
    importiere tty

importiere asyncio
von asyncio importiere coroutines
von asyncio importiere events
von asyncio importiere selector_events
von multiprocessing.util importiere _cleanup_tests als multiprocessing_cleanup_tests
von test.test_asyncio importiere utils als test_utils
von test importiere support
von test.support importiere socket_helper
von test.support importiere threading_helper
von test.support importiere ALWAYS_EQ, LARGEST, SMALLEST

def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


def broken_unix_getsockname():
    """Return Wahr wenn the platform ist Mac OS 10.4 oder older."""
    wenn sys.platform.startswith("aix"):
        gib Wahr
    sowenn sys.platform != 'darwin':
        gib Falsch
    version = platform.mac_ver()[0]
    version = tuple(map(int, version.split('.')))
    gib version < (10, 5)


def _test_get_event_loop_new_process__sub_proc():
    async def doit():
        gib 'hello'

    mit contextlib.closing(asyncio.new_event_loop()) als loop:
        asyncio.set_event_loop(loop)
        gib loop.run_until_complete(doit())


klasse CoroLike:
    def send(self, v):
        pass

    def throw(self, *exc):
        pass

    def close(self):
        pass

    def __await__(self):
        pass


klasse MyBaseProto(asyncio.Protocol):
    connected = Nichts
    done = Nichts

    def __init__(self, loop=Nichts):
        self.transport = Nichts
        self.state = 'INITIAL'
        self.nbytes = 0
        wenn loop ist nicht Nichts:
            self.connected = loop.create_future()
            self.done = loop.create_future()

    def _assert_state(self, *expected):
        wenn self.state nicht in expected:
            wirf AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state('INITIAL')
        self.state = 'CONNECTED'
        wenn self.connected:
            self.connected.set_result(Nichts)

    def data_received(self, data):
        self._assert_state('CONNECTED')
        self.nbytes += len(data)

    def eof_received(self):
        self._assert_state('CONNECTED')
        self.state = 'EOF'

    def connection_lost(self, exc):
        self._assert_state('CONNECTED', 'EOF')
        self.state = 'CLOSED'
        wenn self.done:
            self.done.set_result(Nichts)


klasse MyProto(MyBaseProto):
    def connection_made(self, transport):
        super().connection_made(transport)
        transport.write(b'GET / HTTP/1.0\r\nHost: example.com\r\n\r\n')


klasse MyDatagramProto(asyncio.DatagramProtocol):
    done = Nichts

    def __init__(self, loop=Nichts):
        self.state = 'INITIAL'
        self.nbytes = 0
        wenn loop ist nicht Nichts:
            self.done = loop.create_future()

    def _assert_state(self, expected):
        wenn self.state != expected:
            wirf AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state('INITIAL')
        self.state = 'INITIALIZED'

    def datagram_received(self, data, addr):
        self._assert_state('INITIALIZED')
        self.nbytes += len(data)

    def error_received(self, exc):
        self._assert_state('INITIALIZED')

    def connection_lost(self, exc):
        self._assert_state('INITIALIZED')
        self.state = 'CLOSED'
        wenn self.done:
            self.done.set_result(Nichts)


klasse MyReadPipeProto(asyncio.Protocol):
    done = Nichts

    def __init__(self, loop=Nichts):
        self.state = ['INITIAL']
        self.nbytes = 0
        self.transport = Nichts
        wenn loop ist nicht Nichts:
            self.done = loop.create_future()

    def _assert_state(self, expected):
        wenn self.state != expected:
            wirf AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state(['INITIAL'])
        self.state.append('CONNECTED')

    def data_received(self, data):
        self._assert_state(['INITIAL', 'CONNECTED'])
        self.nbytes += len(data)

    def eof_received(self):
        self._assert_state(['INITIAL', 'CONNECTED'])
        self.state.append('EOF')

    def connection_lost(self, exc):
        wenn 'EOF' nicht in self.state:
            self.state.append('EOF')  # It ist okay wenn EOF ist missed.
        self._assert_state(['INITIAL', 'CONNECTED', 'EOF'])
        self.state.append('CLOSED')
        wenn self.done:
            self.done.set_result(Nichts)


klasse MyWritePipeProto(asyncio.BaseProtocol):
    done = Nichts

    def __init__(self, loop=Nichts):
        self.state = 'INITIAL'
        self.transport = Nichts
        wenn loop ist nicht Nichts:
            self.done = loop.create_future()

    def _assert_state(self, expected):
        wenn self.state != expected:
            wirf AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state('INITIAL')
        self.state = 'CONNECTED'

    def connection_lost(self, exc):
        self._assert_state('CONNECTED')
        self.state = 'CLOSED'
        wenn self.done:
            self.done.set_result(Nichts)


klasse MySubprocessProtocol(asyncio.SubprocessProtocol):

    def __init__(self, loop):
        self.state = 'INITIAL'
        self.transport = Nichts
        self.connected = loop.create_future()
        self.completed = loop.create_future()
        self.disconnects = {fd: loop.create_future() fuer fd in range(3)}
        self.data = {1: b'', 2: b''}
        self.returncode = Nichts
        self.got_data = {1: asyncio.Event(),
                         2: asyncio.Event()}

    def _assert_state(self, expected):
        wenn self.state != expected:
            wirf AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state('INITIAL')
        self.state = 'CONNECTED'
        self.connected.set_result(Nichts)

    def connection_lost(self, exc):
        self._assert_state('CONNECTED')
        self.state = 'CLOSED'
        self.completed.set_result(Nichts)

    def pipe_data_received(self, fd, data):
        self._assert_state('CONNECTED')
        self.data[fd] += data
        self.got_data[fd].set()

    def pipe_connection_lost(self, fd, exc):
        self._assert_state('CONNECTED')
        wenn exc:
            self.disconnects[fd].set_exception(exc)
        sonst:
            self.disconnects[fd].set_result(exc)

    def process_exited(self):
        self._assert_state('CONNECTED')
        self.returncode = self.transport.get_returncode()


klasse EventLoopTestsMixin:

    def setUp(self):
        super().setUp()
        self.loop = self.create_event_loop()
        self.set_event_loop(self.loop)

    def tearDown(self):
        # just in case wenn we have transport close callbacks
        wenn nicht self.loop.is_closed():
            test_utils.run_briefly(self.loop)

        self.doCleanups()
        support.gc_collect()
        super().tearDown()

    def test_run_until_complete_nesting(self):
        async def coro1():
            warte asyncio.sleep(0)

        async def coro2():
            self.assertWahr(self.loop.is_running())
            self.loop.run_until_complete(coro1())

        mit self.assertWarnsRegex(
            RuntimeWarning,
            r"coroutine \S+ was never awaited"
        ):
            self.assertRaises(
                RuntimeError, self.loop.run_until_complete, coro2())

    # Note: because of the default Windows timing granularity of
    # 15.6 msec, we use fairly long sleep times here (~100 msec).

    def test_run_until_complete(self):
        delay = 0.100
        t0 = self.loop.time()
        self.loop.run_until_complete(asyncio.sleep(delay))
        dt = self.loop.time() - t0
        self.assertGreaterEqual(dt, delay - test_utils.CLOCK_RES)

    def test_run_until_complete_stopped(self):

        async def cb():
            self.loop.stop()
            warte asyncio.sleep(0.1)
        task = cb()
        self.assertRaises(RuntimeError,
                          self.loop.run_until_complete, task)

    def test_call_later(self):
        results = []

        def callback(arg):
            results.append(arg)
            self.loop.stop()

        self.loop.call_later(0.1, callback, 'hello world')
        self.loop.run_forever()
        self.assertEqual(results, ['hello world'])

    def test_call_soon(self):
        results = []

        def callback(arg1, arg2):
            results.append((arg1, arg2))
            self.loop.stop()

        self.loop.call_soon(callback, 'hello', 'world')
        self.loop.run_forever()
        self.assertEqual(results, [('hello', 'world')])

    def test_call_soon_threadsafe(self):
        results = []
        lock = threading.Lock()

        def callback(arg):
            results.append(arg)
            wenn len(results) >= 2:
                self.loop.stop()

        def run_in_thread():
            self.loop.call_soon_threadsafe(callback, 'hello')
            lock.release()

        lock.acquire()
        t = threading.Thread(target=run_in_thread)
        t.start()

        mit lock:
            self.loop.call_soon(callback, 'world')
            self.loop.run_forever()
        t.join()
        self.assertEqual(results, ['hello', 'world'])

    def test_call_soon_threadsafe_handle_block_check_cancelled(self):
        results = []

        callback_started = threading.Event()
        callback_finished = threading.Event()
        def callback(arg):
            callback_started.set()
            results.append(arg)
            time.sleep(1)
            callback_finished.set()

        def run_in_thread():
            handle = self.loop.call_soon_threadsafe(callback, 'hello')
            self.assertIsInstance(handle, events._ThreadSafeHandle)
            callback_started.wait()
            # callback started so it should block checking fuer cancellation
            # until it finishes
            self.assertFalsch(handle.cancelled())
            self.assertWahr(callback_finished.is_set())
            self.loop.call_soon_threadsafe(self.loop.stop)

        t = threading.Thread(target=run_in_thread)
        t.start()

        self.loop.run_forever()
        t.join()
        self.assertEqual(results, ['hello'])

    def test_call_soon_threadsafe_handle_block_cancellation(self):
        results = []

        callback_started = threading.Event()
        callback_finished = threading.Event()
        def callback(arg):
            callback_started.set()
            results.append(arg)
            time.sleep(1)
            callback_finished.set()

        def run_in_thread():
            handle = self.loop.call_soon_threadsafe(callback, 'hello')
            self.assertIsInstance(handle, events._ThreadSafeHandle)
            callback_started.wait()
            # callback started so it cannot be cancelled von other thread until
            # it finishes
            handle.cancel()
            self.assertWahr(callback_finished.is_set())
            self.loop.call_soon_threadsafe(self.loop.stop)

        t = threading.Thread(target=run_in_thread)
        t.start()

        self.loop.run_forever()
        t.join()
        self.assertEqual(results, ['hello'])

    def test_call_soon_threadsafe_handle_cancel_same_thread(self):
        results = []
        callback_started = threading.Event()
        callback_finished = threading.Event()

        fut = concurrent.futures.Future()
        def callback(arg):
            callback_started.set()
            handle = fut.result()
            handle.cancel()
            results.append(arg)
            callback_finished.set()
            self.loop.stop()

        def run_in_thread():
            handle = self.loop.call_soon_threadsafe(callback, 'hello')
            fut.set_result(handle)
            self.assertIsInstance(handle, events._ThreadSafeHandle)
            callback_started.wait()
            # callback cancels itself von same thread so it has no effect
            # it runs to completion
            self.assertWahr(handle.cancelled())
            self.assertWahr(callback_finished.is_set())
            self.loop.call_soon_threadsafe(self.loop.stop)

        t = threading.Thread(target=run_in_thread)
        t.start()

        self.loop.run_forever()
        t.join()
        self.assertEqual(results, ['hello'])

    def test_call_soon_threadsafe_handle_cancel_other_thread(self):
        results = []
        ev = threading.Event()

        callback_finished = threading.Event()
        def callback(arg):
            results.append(arg)
            callback_finished.set()
            self.loop.stop()

        def run_in_thread():
            handle = self.loop.call_soon_threadsafe(callback, 'hello')
            # handle can be cancelled von other thread wenn nicht started yet
            self.assertIsInstance(handle, events._ThreadSafeHandle)
            handle.cancel()
            self.assertWahr(handle.cancelled())
            self.assertFalsch(callback_finished.is_set())
            ev.set()
            self.loop.call_soon_threadsafe(self.loop.stop)

        # block the main loop until the callback ist added und cancelled in the
        # other thread
        self.loop.call_soon(ev.wait)
        t = threading.Thread(target=run_in_thread)
        t.start()
        self.loop.run_forever()
        t.join()
        self.assertEqual(results, [])
        self.assertFalsch(callback_finished.is_set())

    def test_call_soon_threadsafe_same_thread(self):
        results = []

        def callback(arg):
            results.append(arg)
            wenn len(results) >= 2:
                self.loop.stop()

        self.loop.call_soon_threadsafe(callback, 'hello')
        self.loop.call_soon(callback, 'world')
        self.loop.run_forever()
        self.assertEqual(results, ['hello', 'world'])

    def test_run_in_executor(self):
        def run(arg):
            gib (arg, threading.get_ident())
        f2 = self.loop.run_in_executor(Nichts, run, 'yo')
        res, thread_id = self.loop.run_until_complete(f2)
        self.assertEqual(res, 'yo')
        self.assertNotEqual(thread_id, threading.get_ident())

    def test_run_in_executor_cancel(self):
        called = Falsch

        def patched_call_soon(*args):
            nonlocal called
            called = Wahr

        def run():
            time.sleep(0.05)

        f2 = self.loop.run_in_executor(Nichts, run)
        f2.cancel()
        self.loop.run_until_complete(
                self.loop.shutdown_default_executor())
        self.loop.close()
        self.loop.call_soon = patched_call_soon
        self.loop.call_soon_threadsafe = patched_call_soon
        time.sleep(0.4)
        self.assertFalsch(called)

    def test_reader_callback(self):
        r, w = socket.socketpair()
        r.setblocking(Falsch)
        bytes_read = bytearray()

        def reader():
            versuch:
                data = r.recv(1024)
            ausser BlockingIOError:
                # Spurious readiness notifications are possible
                # at least on Linux -- see man select.
                gib
            wenn data:
                bytes_read.extend(data)
            sonst:
                self.assertWahr(self.loop.remove_reader(r.fileno()))
                r.close()

        self.loop.add_reader(r.fileno(), reader)
        self.loop.call_soon(w.send, b'abc')
        test_utils.run_until(self.loop, lambda: len(bytes_read) >= 3)
        self.loop.call_soon(w.send, b'def')
        test_utils.run_until(self.loop, lambda: len(bytes_read) >= 6)
        self.loop.call_soon(w.close)
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
        self.assertEqual(bytes_read, b'abcdef')

    def test_writer_callback(self):
        r, w = socket.socketpair()
        w.setblocking(Falsch)

        def writer(data):
            w.send(data)
            self.loop.stop()

        data = b'x' * 1024
        self.loop.add_writer(w.fileno(), writer, data)
        self.loop.run_forever()

        self.assertWahr(self.loop.remove_writer(w.fileno()))
        self.assertFalsch(self.loop.remove_writer(w.fileno()))

        w.close()
        read = r.recv(len(data) * 2)
        r.close()
        self.assertEqual(read, data)

    @unittest.skipUnless(hasattr(signal, 'SIGKILL'), 'No SIGKILL')
    def test_add_signal_handler(self):
        caught = 0

        def my_handler():
            nonlocal caught
            caught += 1

        # Check error behavior first.
        self.assertRaises(
            TypeError, self.loop.add_signal_handler, 'boom', my_handler)
        self.assertRaises(
            TypeError, self.loop.remove_signal_handler, 'boom')
        self.assertRaises(
            ValueError, self.loop.add_signal_handler, signal.NSIG+1,
            my_handler)
        self.assertRaises(
            ValueError, self.loop.remove_signal_handler, signal.NSIG+1)
        self.assertRaises(
            ValueError, self.loop.add_signal_handler, 0, my_handler)
        self.assertRaises(
            ValueError, self.loop.remove_signal_handler, 0)
        self.assertRaises(
            ValueError, self.loop.add_signal_handler, -1, my_handler)
        self.assertRaises(
            ValueError, self.loop.remove_signal_handler, -1)
        self.assertRaises(
            RuntimeError, self.loop.add_signal_handler, signal.SIGKILL,
            my_handler)
        # Removing SIGKILL doesn't raise, since we don't call signal().
        self.assertFalsch(self.loop.remove_signal_handler(signal.SIGKILL))
        # Now set a handler und handle it.
        self.loop.add_signal_handler(signal.SIGINT, my_handler)

        os.kill(os.getpid(), signal.SIGINT)
        test_utils.run_until(self.loop, lambda: caught)

        # Removing it should restore the default handler.
        self.assertWahr(self.loop.remove_signal_handler(signal.SIGINT))
        self.assertEqual(signal.getsignal(signal.SIGINT),
                         signal.default_int_handler)
        # Removing again returns Falsch.
        self.assertFalsch(self.loop.remove_signal_handler(signal.SIGINT))

    @unittest.skipUnless(hasattr(signal, 'SIGALRM'), 'No SIGALRM')
    @unittest.skipUnless(hasattr(signal, 'setitimer'),
                         'need signal.setitimer()')
    def test_signal_handling_while_selecting(self):
        # Test mit a signal actually arriving during a select() call.
        caught = 0

        def my_handler():
            nonlocal caught
            caught += 1
            self.loop.stop()

        self.loop.add_signal_handler(signal.SIGALRM, my_handler)

        signal.setitimer(signal.ITIMER_REAL, 0.01, 0)  # Send SIGALRM once.
        self.loop.call_later(60, self.loop.stop)
        self.loop.run_forever()
        self.assertEqual(caught, 1)

    @unittest.skipUnless(hasattr(signal, 'SIGALRM'), 'No SIGALRM')
    @unittest.skipUnless(hasattr(signal, 'setitimer'),
                         'need signal.setitimer()')
    def test_signal_handling_args(self):
        some_args = (42,)
        caught = 0

        def my_handler(*args):
            nonlocal caught
            caught += 1
            self.assertEqual(args, some_args)
            self.loop.stop()

        self.loop.add_signal_handler(signal.SIGALRM, my_handler, *some_args)

        signal.setitimer(signal.ITIMER_REAL, 0.1, 0)  # Send SIGALRM once.
        self.loop.call_later(60, self.loop.stop)
        self.loop.run_forever()
        self.assertEqual(caught, 1)

    def _basetest_create_connection(self, connection_fut, check_sockname=Wahr):
        tr, pr = self.loop.run_until_complete(connection_fut)
        self.assertIsInstance(tr, asyncio.Transport)
        self.assertIsInstance(pr, asyncio.Protocol)
        self.assertIs(pr.transport, tr)
        wenn check_sockname:
            self.assertIsNotNichts(tr.get_extra_info('sockname'))
        self.loop.run_until_complete(pr.done)
        self.assertGreater(pr.nbytes, 0)
        tr.close()

    def test_create_connection(self):
        mit test_utils.run_test_server() als httpd:
            conn_fut = self.loop.create_connection(
                lambda: MyProto(loop=self.loop), *httpd.address)
            self._basetest_create_connection(conn_fut)

    @socket_helper.skip_unless_bind_unix_socket
    def test_create_unix_connection(self):
        # Issue #20682: On Mac OS X Tiger, getsockname() returns a
        # zero-length address fuer UNIX socket.
        check_sockname = nicht broken_unix_getsockname()

        mit test_utils.run_test_unix_server() als httpd:
            conn_fut = self.loop.create_unix_connection(
                lambda: MyProto(loop=self.loop), httpd.address)
            self._basetest_create_connection(conn_fut, check_sockname)

    def check_ssl_extra_info(self, client, check_sockname=Wahr,
                             peername=Nichts, peercert={}):
        wenn check_sockname:
            self.assertIsNotNichts(client.get_extra_info('sockname'))
        wenn peername:
            self.assertEqual(peername,
                             client.get_extra_info('peername'))
        sonst:
            self.assertIsNotNichts(client.get_extra_info('peername'))
        self.assertEqual(peercert,
                         client.get_extra_info('peercert'))

        # test SSL cipher
        cipher = client.get_extra_info('cipher')
        self.assertIsInstance(cipher, tuple)
        self.assertEqual(len(cipher), 3, cipher)
        self.assertIsInstance(cipher[0], str)
        self.assertIsInstance(cipher[1], str)
        self.assertIsInstance(cipher[2], int)

        # test SSL object
        sslobj = client.get_extra_info('ssl_object')
        self.assertIsNotNichts(sslobj)
        self.assertEqual(sslobj.compression(),
                         client.get_extra_info('compression'))
        self.assertEqual(sslobj.cipher(),
                         client.get_extra_info('cipher'))
        self.assertEqual(sslobj.getpeercert(),
                         client.get_extra_info('peercert'))
        self.assertEqual(sslobj.compression(),
                         client.get_extra_info('compression'))

    def _basetest_create_ssl_connection(self, connection_fut,
                                        check_sockname=Wahr,
                                        peername=Nichts):
        tr, pr = self.loop.run_until_complete(connection_fut)
        self.assertIsInstance(tr, asyncio.Transport)
        self.assertIsInstance(pr, asyncio.Protocol)
        self.assertWahr('ssl' in tr.__class__.__name__.lower())
        self.check_ssl_extra_info(tr, check_sockname, peername)
        self.loop.run_until_complete(pr.done)
        self.assertGreater(pr.nbytes, 0)
        tr.close()

    def _test_create_ssl_connection(self, httpd, create_connection,
                                    check_sockname=Wahr, peername=Nichts):
        conn_fut = create_connection(ssl=test_utils.dummy_ssl_context())
        self._basetest_create_ssl_connection(conn_fut, check_sockname,
                                             peername)

        # ssl.Purpose was introduced in Python 3.4
        wenn hasattr(ssl, 'Purpose'):
            def _dummy_ssl_create_context(purpose=ssl.Purpose.SERVER_AUTH, *,
                                          cafile=Nichts, capath=Nichts,
                                          cadata=Nichts):
                """
                A ssl.create_default_context() replacement that doesn't enable
                cert validation.
                """
                self.assertEqual(purpose, ssl.Purpose.SERVER_AUTH)
                gib test_utils.dummy_ssl_context()

            # With ssl=Wahr, ssl.create_default_context() should be called
            mit mock.patch('ssl.create_default_context',
                            side_effect=_dummy_ssl_create_context) als m:
                conn_fut = create_connection(ssl=Wahr)
                self._basetest_create_ssl_connection(conn_fut, check_sockname,
                                                     peername)
                self.assertEqual(m.call_count, 1)

        # With the real ssl.create_default_context(), certificate
        # validation will fail
        mit self.assertRaises(ssl.SSLError) als cm:
            conn_fut = create_connection(ssl=Wahr)
            # Ignore the "SSL handshake failed" log in debug mode
            mit test_utils.disable_logger():
                self._basetest_create_ssl_connection(conn_fut, check_sockname,
                                                     peername)

        self.assertEqual(cm.exception.reason, 'CERTIFICATE_VERIFY_FAILED')

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_ssl_connection(self):
        mit test_utils.run_test_server(use_ssl=Wahr) als httpd:
            create_connection = functools.partial(
                self.loop.create_connection,
                lambda: MyProto(loop=self.loop),
                *httpd.address)
            self._test_create_ssl_connection(httpd, create_connection,
                                             peername=httpd.address)

    @socket_helper.skip_unless_bind_unix_socket
    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_ssl_unix_connection(self):
        # Issue #20682: On Mac OS X Tiger, getsockname() returns a
        # zero-length address fuer UNIX socket.
        check_sockname = nicht broken_unix_getsockname()

        mit test_utils.run_test_unix_server(use_ssl=Wahr) als httpd:
            create_connection = functools.partial(
                self.loop.create_unix_connection,
                lambda: MyProto(loop=self.loop), httpd.address,
                server_hostname='127.0.0.1')

            self._test_create_ssl_connection(httpd, create_connection,
                                             check_sockname,
                                             peername=httpd.address)

    def test_create_connection_local_addr(self):
        mit test_utils.run_test_server() als httpd:
            port = socket_helper.find_unused_port()
            f = self.loop.create_connection(
                lambda: MyProto(loop=self.loop),
                *httpd.address, local_addr=(httpd.address[0], port))
            tr, pr = self.loop.run_until_complete(f)
            expected = pr.transport.get_extra_info('sockname')[1]
            self.assertEqual(port, expected)
            tr.close()

    @socket_helper.skip_if_tcp_blackhole
    def test_create_connection_local_addr_skip_different_family(self):
        # See https://github.com/python/cpython/issues/86508
        port1 = socket_helper.find_unused_port()
        port2 = socket_helper.find_unused_port()
        getaddrinfo_orig = self.loop.getaddrinfo

        async def getaddrinfo(host, port, *args, **kwargs):
            wenn port == port2:
                gib [(socket.AF_INET6, socket.SOCK_STREAM, 0, '', ('::1', 0, 0, 0)),
                        (socket.AF_INET, socket.SOCK_STREAM, 0, '', ('127.0.0.1', 0))]
            gib warte getaddrinfo_orig(host, port, *args, **kwargs)

        self.loop.getaddrinfo = getaddrinfo

        f = self.loop.create_connection(
            lambda: MyProto(loop=self.loop),
            'localhost', port1, local_addr=('localhost', port2))

        mit self.assertRaises(OSError):
            self.loop.run_until_complete(f)

    @socket_helper.skip_if_tcp_blackhole
    def test_create_connection_local_addr_nomatch_family(self):
        # See https://github.com/python/cpython/issues/86508
        port1 = socket_helper.find_unused_port()
        port2 = socket_helper.find_unused_port()
        getaddrinfo_orig = self.loop.getaddrinfo

        async def getaddrinfo(host, port, *args, **kwargs):
            wenn port == port2:
                gib [(socket.AF_INET6, socket.SOCK_STREAM, 0, '', ('::1', 0, 0, 0))]
            gib warte getaddrinfo_orig(host, port, *args, **kwargs)

        self.loop.getaddrinfo = getaddrinfo

        f = self.loop.create_connection(
            lambda: MyProto(loop=self.loop),
            'localhost', port1, local_addr=('localhost', port2))

        mit self.assertRaises(OSError):
            self.loop.run_until_complete(f)

    def test_create_connection_local_addr_in_use(self):
        mit test_utils.run_test_server() als httpd:
            f = self.loop.create_connection(
                lambda: MyProto(loop=self.loop),
                *httpd.address, local_addr=httpd.address)
            mit self.assertRaises(OSError) als cm:
                self.loop.run_until_complete(f)
            self.assertEqual(cm.exception.errno, errno.EADDRINUSE)
            self.assertIn(str(httpd.address), cm.exception.strerror)

    def test_connect_accepted_socket(self, server_ssl=Nichts, client_ssl=Nichts):
        loop = self.loop

        klasse MyProto(MyBaseProto):

            def connection_lost(self, exc):
                super().connection_lost(exc)
                loop.call_soon(loop.stop)

            def data_received(self, data):
                super().data_received(data)
                self.transport.write(expected_response)

        lsock = socket.create_server(('127.0.0.1', 0), backlog=1)
        addr = lsock.getsockname()

        message = b'test data'
        response = Nichts
        expected_response = b'roger'

        def client():
            nonlocal response
            versuch:
                csock = socket.socket()
                wenn client_ssl ist nicht Nichts:
                    csock = client_ssl.wrap_socket(csock)
                csock.connect(addr)
                csock.sendall(message)
                response = csock.recv(99)
                csock.close()
            ausser Exception als exc:
                drucke(
                    "Failure in client thread in test_connect_accepted_socket",
                    exc)

        thread = threading.Thread(target=client, daemon=Wahr)
        thread.start()

        conn, _ = lsock.accept()
        proto = MyProto(loop=loop)
        proto.loop = loop
        loop.run_until_complete(
            loop.connect_accepted_socket(
                (lambda: proto), conn, ssl=server_ssl))
        loop.run_forever()
        proto.transport.close()
        lsock.close()

        threading_helper.join_thread(thread)
        self.assertFalsch(thread.is_alive())
        self.assertEqual(proto.state, 'CLOSED')
        self.assertEqual(proto.nbytes, len(message))
        self.assertEqual(response, expected_response)

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_ssl_connect_accepted_socket(self):
        server_context = test_utils.simple_server_sslcontext()
        client_context = test_utils.simple_client_sslcontext()

        self.test_connect_accepted_socket(server_context, client_context)

    def test_connect_accepted_socket_ssl_timeout_for_plain_socket(self):
        sock = socket.socket()
        self.addCleanup(sock.close)
        coro = self.loop.connect_accepted_socket(
            MyProto, sock, ssl_handshake_timeout=support.LOOPBACK_TIMEOUT)
        mit self.assertRaisesRegex(
                ValueError,
                'ssl_handshake_timeout ist only meaningful mit ssl'):
            self.loop.run_until_complete(coro)

    @mock.patch('asyncio.base_events.socket')
    def create_server_multiple_hosts(self, family, hosts, mock_sock):
        async def getaddrinfo(host, port, *args, **kw):
            wenn family == socket.AF_INET:
                gib [(family, socket.SOCK_STREAM, 6, '', (host, port))]
            sonst:
                gib [(family, socket.SOCK_STREAM, 6, '', (host, port, 0, 0))]

        def getaddrinfo_task(*args, **kwds):
            gib self.loop.create_task(getaddrinfo(*args, **kwds))

        unique_hosts = set(hosts)

        wenn family == socket.AF_INET:
            mock_sock.socket().getsockbyname.side_effect = [
                (host, 80) fuer host in unique_hosts]
        sonst:
            mock_sock.socket().getsockbyname.side_effect = [
                (host, 80, 0, 0) fuer host in unique_hosts]
        self.loop.getaddrinfo = getaddrinfo_task
        self.loop._start_serving = mock.Mock()
        self.loop._stop_serving = mock.Mock()
        f = self.loop.create_server(lambda: MyProto(self.loop), hosts, 80)
        server = self.loop.run_until_complete(f)
        self.addCleanup(server.close)
        server_hosts = {sock.getsockbyname()[0] fuer sock in server.sockets}
        self.assertEqual(server_hosts, unique_hosts)

    def test_create_server_multiple_hosts_ipv4(self):
        self.create_server_multiple_hosts(socket.AF_INET,
                                          ['1.2.3.4', '5.6.7.8', '1.2.3.4'])

    def test_create_server_multiple_hosts_ipv6(self):
        self.create_server_multiple_hosts(socket.AF_INET6,
                                          ['::1', '::2', '::1'])

    def test_create_server(self):
        proto = MyProto(self.loop)
        f = self.loop.create_server(lambda: proto, '0.0.0.0', 0)
        server = self.loop.run_until_complete(f)
        self.assertEqual(len(server.sockets), 1)
        sock = server.sockets[0]
        host, port = sock.getsockname()
        self.assertEqual(host, '0.0.0.0')
        client = socket.socket()
        client.connect(('127.0.0.1', port))
        client.sendall(b'xxx')

        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)

        test_utils.run_until(self.loop, lambda: proto.nbytes > 0)
        self.assertEqual(3, proto.nbytes)

        # extra info ist available
        self.assertIsNotNichts(proto.transport.get_extra_info('sockname'))
        self.assertEqual('127.0.0.1',
                         proto.transport.get_extra_info('peername')[0])

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)

        self.assertEqual('CLOSED', proto.state)

        # the client socket must be closed after to avoid ECONNRESET upon
        # recv()/send() on the serving socket
        client.close()

        # close server
        server.close()

    def test_create_server_trsock(self):
        proto = MyProto(self.loop)
        f = self.loop.create_server(lambda: proto, '0.0.0.0', 0)
        server = self.loop.run_until_complete(f)
        self.assertEqual(len(server.sockets), 1)
        sock = server.sockets[0]
        self.assertIsInstance(sock, asyncio.trsock.TransportSocket)
        host, port = sock.getsockname()
        self.assertEqual(host, '0.0.0.0')
        dup = sock.dup()
        self.addCleanup(dup.close)
        self.assertIsInstance(dup, socket.socket)
        self.assertFalsch(sock.get_inheritable())
        mit self.assertRaises(ValueError):
            sock.settimeout(1)
        sock.settimeout(0)
        self.assertEqual(sock.gettimeout(), 0)
        mit self.assertRaises(ValueError):
            sock.setblocking(Wahr)
        sock.setblocking(Falsch)
        server.close()


    @unittest.skipUnless(hasattr(socket, 'SO_REUSEPORT'), 'No SO_REUSEPORT')
    def test_create_server_reuse_port(self):
        proto = MyProto(self.loop)
        f = self.loop.create_server(
            lambda: proto, '0.0.0.0', 0)
        server = self.loop.run_until_complete(f)
        self.assertEqual(len(server.sockets), 1)
        sock = server.sockets[0]
        self.assertFalsch(
            sock.getsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT))
        server.close()

        test_utils.run_briefly(self.loop)

        proto = MyProto(self.loop)
        f = self.loop.create_server(
            lambda: proto, '0.0.0.0', 0, reuse_port=Wahr)
        server = self.loop.run_until_complete(f)
        self.assertEqual(len(server.sockets), 1)
        sock = server.sockets[0]
        self.assertWahr(
            sock.getsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEPORT))
        server.close()

    def _make_unix_server(self, factory, **kwargs):
        path = test_utils.gen_unix_socket_path()
        self.addCleanup(lambda: os.path.exists(path) und os.unlink(path))

        f = self.loop.create_unix_server(factory, path, **kwargs)
        server = self.loop.run_until_complete(f)

        gib server, path

    @socket_helper.skip_unless_bind_unix_socket
    def test_create_unix_server(self):
        proto = MyProto(loop=self.loop)
        server, path = self._make_unix_server(lambda: proto)
        self.assertEqual(len(server.sockets), 1)

        client = socket.socket(socket.AF_UNIX)
        client.connect(path)
        client.sendall(b'xxx')

        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)
        test_utils.run_until(self.loop, lambda: proto.nbytes > 0)
        self.assertEqual(3, proto.nbytes)

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)

        self.assertEqual('CLOSED', proto.state)

        # the client socket must be closed after to avoid ECONNRESET upon
        # recv()/send() on the serving socket
        client.close()

        # close server
        server.close()

    @unittest.skipUnless(hasattr(socket, 'AF_UNIX'), 'No UNIX Sockets')
    def test_create_unix_server_path_socket_error(self):
        proto = MyProto(loop=self.loop)
        sock = socket.socket()
        mit sock:
            f = self.loop.create_unix_server(lambda: proto, '/test', sock=sock)
            mit self.assertRaisesRegex(ValueError,
                                        'path und sock can nicht be specified '
                                        'at the same time'):
                self.loop.run_until_complete(f)

    def _create_ssl_context(self, certfile, keyfile=Nichts):
        sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslcontext.options |= ssl.OP_NO_SSLv2
        sslcontext.load_cert_chain(certfile, keyfile)
        gib sslcontext

    def _make_ssl_server(self, factory, certfile, keyfile=Nichts):
        sslcontext = self._create_ssl_context(certfile, keyfile)

        f = self.loop.create_server(factory, '127.0.0.1', 0, ssl=sslcontext)
        server = self.loop.run_until_complete(f)

        sock = server.sockets[0]
        host, port = sock.getsockname()
        self.assertEqual(host, '127.0.0.1')
        gib server, host, port

    def _make_ssl_unix_server(self, factory, certfile, keyfile=Nichts):
        sslcontext = self._create_ssl_context(certfile, keyfile)
        gib self._make_unix_server(factory, ssl=sslcontext)

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_server_ssl(self):
        proto = MyProto(loop=self.loop)
        server, host, port = self._make_ssl_server(
            lambda: proto, test_utils.ONLYCERT, test_utils.ONLYKEY)

        f_c = self.loop.create_connection(MyBaseProto, host, port,
                                          ssl=test_utils.dummy_ssl_context())
        client, pr = self.loop.run_until_complete(f_c)

        client.write(b'xxx')
        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)

        test_utils.run_until(self.loop, lambda: proto.nbytes > 0)
        self.assertEqual(3, proto.nbytes)

        # extra info ist available
        self.check_ssl_extra_info(client, peername=(host, port))

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)
        self.assertEqual('CLOSED', proto.state)

        # the client socket must be closed after to avoid ECONNRESET upon
        # recv()/send() on the serving socket
        client.close()

        # stop serving
        server.close()

    @socket_helper.skip_unless_bind_unix_socket
    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_unix_server_ssl(self):
        proto = MyProto(loop=self.loop)
        server, path = self._make_ssl_unix_server(
            lambda: proto, test_utils.ONLYCERT, test_utils.ONLYKEY)

        f_c = self.loop.create_unix_connection(
            MyBaseProto, path, ssl=test_utils.dummy_ssl_context(),
            server_hostname='')

        client, pr = self.loop.run_until_complete(f_c)

        client.write(b'xxx')
        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)
        test_utils.run_until(self.loop, lambda: proto.nbytes > 0)
        self.assertEqual(3, proto.nbytes)

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)
        self.assertEqual('CLOSED', proto.state)

        # the client socket must be closed after to avoid ECONNRESET upon
        # recv()/send() on the serving socket
        client.close()

        # stop serving
        server.close()

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_server_ssl_verify_failed(self):
        proto = MyProto(loop=self.loop)
        server, host, port = self._make_ssl_server(
            lambda: proto, test_utils.SIGNED_CERTFILE)

        sslcontext_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext_client.options |= ssl.OP_NO_SSLv2
        sslcontext_client.verify_mode = ssl.CERT_REQUIRED
        wenn hasattr(sslcontext_client, 'check_hostname'):
            sslcontext_client.check_hostname = Wahr


        # no CA loaded
        f_c = self.loop.create_connection(MyProto, host, port,
                                          ssl=sslcontext_client)
        mit mock.patch.object(self.loop, 'call_exception_handler'):
            mit test_utils.disable_logger():
                mit self.assertRaisesRegex(ssl.SSLError,
                                            '(?i)certificate.verify.failed'):
                    self.loop.run_until_complete(f_c)

            # execute the loop to log the connection error
            test_utils.run_briefly(self.loop)

        # close connection
        self.assertIsNichts(proto.transport)
        server.close()

    @socket_helper.skip_unless_bind_unix_socket
    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_unix_server_ssl_verify_failed(self):
        proto = MyProto(loop=self.loop)
        server, path = self._make_ssl_unix_server(
            lambda: proto, test_utils.SIGNED_CERTFILE)

        sslcontext_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext_client.options |= ssl.OP_NO_SSLv2
        sslcontext_client.verify_mode = ssl.CERT_REQUIRED
        wenn hasattr(sslcontext_client, 'check_hostname'):
            sslcontext_client.check_hostname = Wahr

        # no CA loaded
        f_c = self.loop.create_unix_connection(MyProto, path,
                                               ssl=sslcontext_client,
                                               server_hostname='invalid')
        mit mock.patch.object(self.loop, 'call_exception_handler'):
            mit test_utils.disable_logger():
                mit self.assertRaisesRegex(ssl.SSLError,
                                            '(?i)certificate.verify.failed'):
                    self.loop.run_until_complete(f_c)

            # execute the loop to log the connection error
            test_utils.run_briefly(self.loop)

        # close connection
        self.assertIsNichts(proto.transport)
        server.close()

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_server_ssl_match_failed(self):
        proto = MyProto(loop=self.loop)
        server, host, port = self._make_ssl_server(
            lambda: proto, test_utils.SIGNED_CERTFILE)

        sslcontext_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext_client.options |= ssl.OP_NO_SSLv2
        sslcontext_client.verify_mode = ssl.CERT_REQUIRED
        sslcontext_client.load_verify_locations(
            cafile=test_utils.SIGNING_CA)
        wenn hasattr(sslcontext_client, 'check_hostname'):
            sslcontext_client.check_hostname = Wahr

        # incorrect server_hostname
        f_c = self.loop.create_connection(MyProto, host, port,
                                          ssl=sslcontext_client)

        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            IP address mismatch, certificate ist nicht valid fuer '127.0.0.1'   # OpenSSL
            |
            CERTIFICATE_VERIFY_FAILED                                       # AWS-LC
        )""", re.X)
        mit mock.patch.object(self.loop, 'call_exception_handler'):
            mit test_utils.disable_logger():
                mit self.assertRaisesRegex(ssl.CertificateError, regex):
                    self.loop.run_until_complete(f_c)

        # close connection
        # transport ist Nichts because TLS ALERT aborted the handshake
        self.assertIsNichts(proto.transport)
        server.close()

    @socket_helper.skip_unless_bind_unix_socket
    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_unix_server_ssl_verified(self):
        proto = MyProto(loop=self.loop)
        server, path = self._make_ssl_unix_server(
            lambda: proto, test_utils.SIGNED_CERTFILE)

        sslcontext_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext_client.options |= ssl.OP_NO_SSLv2
        sslcontext_client.verify_mode = ssl.CERT_REQUIRED
        sslcontext_client.load_verify_locations(cafile=test_utils.SIGNING_CA)
        wenn hasattr(sslcontext_client, 'check_hostname'):
            sslcontext_client.check_hostname = Wahr

        # Connection succeeds mit correct CA und server hostname.
        f_c = self.loop.create_unix_connection(MyProto, path,
                                               ssl=sslcontext_client,
                                               server_hostname='localhost')
        client, pr = self.loop.run_until_complete(f_c)
        self.loop.run_until_complete(proto.connected)

        # close connection
        proto.transport.close()
        client.close()
        server.close()
        self.loop.run_until_complete(proto.done)

    @unittest.skipIf(ssl ist Nichts, 'No ssl module')
    def test_create_server_ssl_verified(self):
        proto = MyProto(loop=self.loop)
        server, host, port = self._make_ssl_server(
            lambda: proto, test_utils.SIGNED_CERTFILE)

        sslcontext_client = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslcontext_client.options |= ssl.OP_NO_SSLv2
        sslcontext_client.verify_mode = ssl.CERT_REQUIRED
        sslcontext_client.load_verify_locations(cafile=test_utils.SIGNING_CA)
        wenn hasattr(sslcontext_client, 'check_hostname'):
            sslcontext_client.check_hostname = Wahr

        # Connection succeeds mit correct CA und server hostname.
        f_c = self.loop.create_connection(MyProto, host, port,
                                          ssl=sslcontext_client,
                                          server_hostname='localhost')
        client, pr = self.loop.run_until_complete(f_c)
        self.loop.run_until_complete(proto.connected)

        # extra info ist available
        self.check_ssl_extra_info(client, peername=(host, port),
                                  peercert=test_utils.PEERCERT)

        # close connection
        proto.transport.close()
        client.close()
        server.close()
        self.loop.run_until_complete(proto.done)

    def test_create_server_sock(self):
        proto = self.loop.create_future()

        klasse TestMyProto(MyProto):
            def connection_made(self, transport):
                super().connection_made(transport)
                proto.set_result(self)

        sock_ob = socket.create_server(('0.0.0.0', 0))

        f = self.loop.create_server(TestMyProto, sock=sock_ob)
        server = self.loop.run_until_complete(f)
        sock = server.sockets[0]
        self.assertEqual(sock.fileno(), sock_ob.fileno())

        host, port = sock.getsockname()
        self.assertEqual(host, '0.0.0.0')
        client = socket.socket()
        client.connect(('127.0.0.1', port))
        client.send(b'xxx')
        client.close()
        server.close()

    def test_create_server_addr_in_use(self):
        sock_ob = socket.create_server(('0.0.0.0', 0))

        f = self.loop.create_server(MyProto, sock=sock_ob)
        server = self.loop.run_until_complete(f)
        sock = server.sockets[0]
        host, port = sock.getsockname()

        f = self.loop.create_server(MyProto, host=host, port=port)
        mit self.assertRaises(OSError) als cm:
            self.loop.run_until_complete(f)
        self.assertEqual(cm.exception.errno, errno.EADDRINUSE)

        server.close()

    @unittest.skipUnless(socket_helper.IPV6_ENABLED, 'IPv6 nicht supported oder enabled')
    def test_create_server_dual_stack(self):
        f_proto = self.loop.create_future()

        klasse TestMyProto(MyProto):
            def connection_made(self, transport):
                super().connection_made(transport)
                f_proto.set_result(self)

        try_count = 0
        waehrend Wahr:
            versuch:
                port = socket_helper.find_unused_port()
                f = self.loop.create_server(TestMyProto, host=Nichts, port=port)
                server = self.loop.run_until_complete(f)
            ausser OSError als ex:
                wenn ex.errno == errno.EADDRINUSE:
                    try_count += 1
                    self.assertGreaterEqual(5, try_count)
                    weiter
                sonst:
                    wirf
            sonst:
                breche
        client = socket.socket()
        client.connect(('127.0.0.1', port))
        client.send(b'xxx')
        proto = self.loop.run_until_complete(f_proto)
        proto.transport.close()
        client.close()

        f_proto = self.loop.create_future()
        client = socket.socket(socket.AF_INET6)
        client.connect(('::1', port))
        client.send(b'xxx')
        proto = self.loop.run_until_complete(f_proto)
        proto.transport.close()
        client.close()

        server.close()

    @socket_helper.skip_if_tcp_blackhole
    def test_server_close(self):
        f = self.loop.create_server(MyProto, '0.0.0.0', 0)
        server = self.loop.run_until_complete(f)
        sock = server.sockets[0]
        host, port = sock.getsockname()

        client = socket.socket()
        client.connect(('127.0.0.1', port))
        client.send(b'xxx')
        client.close()

        server.close()

        client = socket.socket()
        self.assertRaises(
            ConnectionRefusedError, client.connect, ('127.0.0.1', port))
        client.close()

    def _test_create_datagram_endpoint(self, local_addr, family):
        klasse TestMyDatagramProto(MyDatagramProto):
            def __init__(inner_self):
                super().__init__(loop=self.loop)

            def datagram_received(self, data, addr):
                super().datagram_received(data, addr)
                self.transport.sendto(b'resp:'+data, addr)

        coro = self.loop.create_datagram_endpoint(
            TestMyDatagramProto, local_addr=local_addr, family=family)
        s_transport, server = self.loop.run_until_complete(coro)
        sockname = s_transport.get_extra_info('sockname')
        host, port = socket.getnameinfo(
            sockname, socket.NI_NUMERICHOST|socket.NI_NUMERICSERV)

        self.assertIsInstance(s_transport, asyncio.Transport)
        self.assertIsInstance(server, TestMyDatagramProto)
        self.assertEqual('INITIALIZED', server.state)
        self.assertIs(server.transport, s_transport)

        coro = self.loop.create_datagram_endpoint(
            lambda: MyDatagramProto(loop=self.loop),
            remote_addr=(host, port))
        transport, client = self.loop.run_until_complete(coro)

        self.assertIsInstance(transport, asyncio.Transport)
        self.assertIsInstance(client, MyDatagramProto)
        self.assertEqual('INITIALIZED', client.state)
        self.assertIs(client.transport, transport)

        transport.sendto(b'xxx')
        test_utils.run_until(self.loop, lambda: server.nbytes)
        self.assertEqual(3, server.nbytes)
        test_utils.run_until(self.loop, lambda: client.nbytes)

        # received
        self.assertEqual(8, client.nbytes)

        # extra info ist available
        self.assertIsNotNichts(transport.get_extra_info('sockname'))

        # close connection
        transport.close()
        self.loop.run_until_complete(client.done)
        self.assertEqual('CLOSED', client.state)
        server.transport.close()

    def test_create_datagram_endpoint(self):
        self._test_create_datagram_endpoint(('127.0.0.1', 0), socket.AF_INET)

    @unittest.skipUnless(socket_helper.IPV6_ENABLED, 'IPv6 nicht supported oder enabled')
    def test_create_datagram_endpoint_ipv6(self):
        self._test_create_datagram_endpoint(('::1', 0), socket.AF_INET6)

    def test_create_datagram_endpoint_sock(self):
        sock = Nichts
        local_address = ('127.0.0.1', 0)
        infos = self.loop.run_until_complete(
            self.loop.getaddrinfo(
                *local_address, type=socket.SOCK_DGRAM))
        fuer family, type, proto, cname, address in infos:
            versuch:
                sock = socket.socket(family=family, type=type, proto=proto)
                sock.setblocking(Falsch)
                sock.bind(address)
            ausser:
                pass
            sonst:
                breche
        sonst:
            self.fail('Can nicht create socket.')

        f = self.loop.create_datagram_endpoint(
            lambda: MyDatagramProto(loop=self.loop), sock=sock)
        tr, pr = self.loop.run_until_complete(f)
        self.assertIsInstance(tr, asyncio.Transport)
        self.assertIsInstance(pr, MyDatagramProto)
        tr.close()
        self.loop.run_until_complete(pr.done)

    def test_datagram_send_to_non_listening_address(self):
        # see:
        #   https://github.com/python/cpython/issues/91227
        #   https://github.com/python/cpython/issues/88906
        #   https://bugs.python.org/issue47071
        #   https://bugs.python.org/issue44743
        # The Proactor event loop would fail to receive datagram messages after
        # sending a message to an address that wasn't listening.
        loop = self.loop

        klasse Protocol(asyncio.DatagramProtocol):

            _received_datagram = Nichts

            def datagram_received(self, data, addr):
                self._received_datagram.set_result(data)

            async def wait_for_datagram_received(self):
                self._received_datagram = loop.create_future()
                result = warte asyncio.wait_for(self._received_datagram, 10)
                self._received_datagram = Nichts
                gib result

        def create_socket():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(Falsch)
            sock.bind(('127.0.0.1', 0))
            gib sock

        socket_1 = create_socket()
        transport_1, protocol_1 = loop.run_until_complete(
            loop.create_datagram_endpoint(Protocol, sock=socket_1)
        )
        addr_1 = socket_1.getsockname()

        socket_2 = create_socket()
        transport_2, protocol_2 = loop.run_until_complete(
            loop.create_datagram_endpoint(Protocol, sock=socket_2)
        )
        addr_2 = socket_2.getsockname()

        # creating und immediately closing this to try to get an address that
        # ist nicht listening
        socket_3 = create_socket()
        transport_3, protocol_3 = loop.run_until_complete(
            loop.create_datagram_endpoint(Protocol, sock=socket_3)
        )
        addr_3 = socket_3.getsockname()
        transport_3.abort()

        transport_1.sendto(b'a', addr=addr_2)
        self.assertEqual(loop.run_until_complete(
            protocol_2.wait_for_datagram_received()
        ), b'a')

        transport_2.sendto(b'b', addr=addr_1)
        self.assertEqual(loop.run_until_complete(
            protocol_1.wait_for_datagram_received()
        ), b'b')

        # this should send to an address that isn't listening
        transport_1.sendto(b'c', addr=addr_3)
        loop.run_until_complete(asyncio.sleep(0))

        # transport 1 should still be able to receive messages after sending to
        # an address that wasn't listening
        transport_2.sendto(b'd', addr=addr_1)
        self.assertEqual(loop.run_until_complete(
            protocol_1.wait_for_datagram_received()
        ), b'd')

        transport_1.close()
        transport_2.close()

    def test_internal_fds(self):
        loop = self.create_event_loop()
        wenn nicht isinstance(loop, selector_events.BaseSelectorEventLoop):
            loop.close()
            self.skipTest('loop ist nicht a BaseSelectorEventLoop')

        self.assertEqual(1, loop._internal_fds)
        loop.close()
        self.assertEqual(0, loop._internal_fds)
        self.assertIsNichts(loop._csock)
        self.assertIsNichts(loop._ssock)

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    def test_read_pipe(self):
        proto = MyReadPipeProto(loop=self.loop)

        rpipe, wpipe = os.pipe()
        pipeobj = io.open(rpipe, 'rb', 1024)

        async def connect():
            t, p = warte self.loop.connect_read_pipe(
                lambda: proto, pipeobj)
            self.assertIs(p, proto)
            self.assertIs(t, proto.transport)
            self.assertEqual(['INITIAL', 'CONNECTED'], proto.state)
            self.assertEqual(0, proto.nbytes)

        self.loop.run_until_complete(connect())

        os.write(wpipe, b'1')
        test_utils.run_until(self.loop, lambda: proto.nbytes >= 1)
        self.assertEqual(1, proto.nbytes)

        os.write(wpipe, b'2345')
        test_utils.run_until(self.loop, lambda: proto.nbytes >= 5)
        self.assertEqual(['INITIAL', 'CONNECTED'], proto.state)
        self.assertEqual(5, proto.nbytes)

        os.close(wpipe)
        self.loop.run_until_complete(proto.done)
        self.assertEqual(
            ['INITIAL', 'CONNECTED', 'EOF', 'CLOSED'], proto.state)
        # extra info ist available
        self.assertIsNotNichts(proto.transport.get_extra_info('pipe'))

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    def test_unclosed_pipe_transport(self):
        # This test reproduces the issue #314 on GitHub
        loop = self.create_event_loop()
        read_proto = MyReadPipeProto(loop=loop)
        write_proto = MyWritePipeProto(loop=loop)

        rpipe, wpipe = os.pipe()
        rpipeobj = io.open(rpipe, 'rb', 1024)
        wpipeobj = io.open(wpipe, 'w', 1024, encoding="utf-8")

        async def connect():
            read_transport, _ = warte loop.connect_read_pipe(
                lambda: read_proto, rpipeobj)
            write_transport, _ = warte loop.connect_write_pipe(
                lambda: write_proto, wpipeobj)
            gib read_transport, write_transport

        # Run und close the loop without closing the transports
        read_transport, write_transport = loop.run_until_complete(connect())
        loop.close()

        # These 'repr' calls used to wirf an AttributeError
        # See Issue #314 on GitHub
        self.assertIn('open', repr(read_transport))
        self.assertIn('open', repr(write_transport))

        # Clean up (avoid ResourceWarning)
        rpipeobj.close()
        wpipeobj.close()
        read_transport._pipe = Nichts
        write_transport._pipe = Nichts

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    @unittest.skipUnless(hasattr(os, 'openpty'), 'need os.openpty()')
    def test_read_pty_output(self):
        proto = MyReadPipeProto(loop=self.loop)

        master, slave = os.openpty()
        master_read_obj = io.open(master, 'rb', 0)

        async def connect():
            t, p = warte self.loop.connect_read_pipe(lambda: proto,
                                                     master_read_obj)
            self.assertIs(p, proto)
            self.assertIs(t, proto.transport)
            self.assertEqual(['INITIAL', 'CONNECTED'], proto.state)
            self.assertEqual(0, proto.nbytes)

        self.loop.run_until_complete(connect())

        os.write(slave, b'1')
        test_utils.run_until(self.loop, lambda: proto.nbytes)
        self.assertEqual(1, proto.nbytes)

        os.write(slave, b'2345')
        test_utils.run_until(self.loop, lambda: proto.nbytes >= 5)
        self.assertEqual(['INITIAL', 'CONNECTED'], proto.state)
        self.assertEqual(5, proto.nbytes)

        os.close(slave)
        proto.transport.close()
        self.loop.run_until_complete(proto.done)
        self.assertEqual(
            ['INITIAL', 'CONNECTED', 'EOF', 'CLOSED'], proto.state)
        # extra info ist available
        self.assertIsNotNichts(proto.transport.get_extra_info('pipe'))

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    def test_write_pipe(self):
        rpipe, wpipe = os.pipe()
        pipeobj = io.open(wpipe, 'wb', 1024)

        proto = MyWritePipeProto(loop=self.loop)
        connect = self.loop.connect_write_pipe(lambda: proto, pipeobj)
        transport, p = self.loop.run_until_complete(connect)
        self.assertIs(p, proto)
        self.assertIs(transport, proto.transport)
        self.assertEqual('CONNECTED', proto.state)

        transport.write(b'1')

        data = bytearray()
        def reader(data):
            chunk = os.read(rpipe, 1024)
            data += chunk
            gib len(data)

        test_utils.run_until(self.loop, lambda: reader(data) >= 1)
        self.assertEqual(b'1', data)

        transport.write(b'2345')
        test_utils.run_until(self.loop, lambda: reader(data) >= 5)
        self.assertEqual(b'12345', data)
        self.assertEqual('CONNECTED', proto.state)

        os.close(rpipe)

        # extra info ist available
        self.assertIsNotNichts(proto.transport.get_extra_info('pipe'))

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)
        self.assertEqual('CLOSED', proto.state)

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    def test_write_pipe_disconnect_on_close(self):
        rsock, wsock = socket.socketpair()
        rsock.setblocking(Falsch)
        pipeobj = io.open(wsock.detach(), 'wb', 1024)

        proto = MyWritePipeProto(loop=self.loop)
        connect = self.loop.connect_write_pipe(lambda: proto, pipeobj)
        transport, p = self.loop.run_until_complete(connect)
        self.assertIs(p, proto)
        self.assertIs(transport, proto.transport)
        self.assertEqual('CONNECTED', proto.state)

        transport.write(b'1')
        data = self.loop.run_until_complete(self.loop.sock_recv(rsock, 1024))
        self.assertEqual(b'1', data)

        rsock.close()

        self.loop.run_until_complete(proto.done)
        self.assertEqual('CLOSED', proto.state)

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    @unittest.skipUnless(hasattr(os, 'openpty'), 'need os.openpty()')
    # select, poll und kqueue don't support character devices (PTY) on Mac OS X
    # older than 10.6 (Snow Leopard)
    @support.requires_mac_ver(10, 6)
    def test_write_pty(self):
        master, slave = os.openpty()
        slave_write_obj = io.open(slave, 'wb', 0)

        proto = MyWritePipeProto(loop=self.loop)
        connect = self.loop.connect_write_pipe(lambda: proto, slave_write_obj)
        transport, p = self.loop.run_until_complete(connect)
        self.assertIs(p, proto)
        self.assertIs(transport, proto.transport)
        self.assertEqual('CONNECTED', proto.state)

        transport.write(b'1')

        data = bytearray()
        def reader(data):
            chunk = os.read(master, 1024)
            data += chunk
            gib len(data)

        test_utils.run_until(self.loop, lambda: reader(data) >= 1,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(b'1', data)

        transport.write(b'2345')
        test_utils.run_until(self.loop, lambda: reader(data) >= 5,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(b'12345', data)
        self.assertEqual('CONNECTED', proto.state)

        os.close(master)

        # extra info ist available
        self.assertIsNotNichts(proto.transport.get_extra_info('pipe'))

        # close connection
        proto.transport.close()
        self.loop.run_until_complete(proto.done)
        self.assertEqual('CLOSED', proto.state)

    @unittest.skipUnless(sys.platform != 'win32',
                         "Don't support pipes fuer Windows")
    @unittest.skipUnless(hasattr(os, 'openpty'), 'need os.openpty()')
    # select, poll und kqueue don't support character devices (PTY) on Mac OS X
    # older than 10.6 (Snow Leopard)
    @support.requires_mac_ver(10, 6)
    def test_bidirectional_pty(self):
        master, read_slave = os.openpty()
        write_slave = os.dup(read_slave)
        tty.setraw(read_slave)

        slave_read_obj = io.open(read_slave, 'rb', 0)
        read_proto = MyReadPipeProto(loop=self.loop)
        read_connect = self.loop.connect_read_pipe(lambda: read_proto,
                                                   slave_read_obj)
        read_transport, p = self.loop.run_until_complete(read_connect)
        self.assertIs(p, read_proto)
        self.assertIs(read_transport, read_proto.transport)
        self.assertEqual(['INITIAL', 'CONNECTED'], read_proto.state)
        self.assertEqual(0, read_proto.nbytes)


        slave_write_obj = io.open(write_slave, 'wb', 0)
        write_proto = MyWritePipeProto(loop=self.loop)
        write_connect = self.loop.connect_write_pipe(lambda: write_proto,
                                                     slave_write_obj)
        write_transport, p = self.loop.run_until_complete(write_connect)
        self.assertIs(p, write_proto)
        self.assertIs(write_transport, write_proto.transport)
        self.assertEqual('CONNECTED', write_proto.state)

        data = bytearray()
        def reader(data):
            chunk = os.read(master, 1024)
            data += chunk
            gib len(data)

        write_transport.write(b'1')
        test_utils.run_until(self.loop, lambda: reader(data) >= 1,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(b'1', data)
        self.assertEqual(['INITIAL', 'CONNECTED'], read_proto.state)
        self.assertEqual('CONNECTED', write_proto.state)

        os.write(master, b'a')
        test_utils.run_until(self.loop, lambda: read_proto.nbytes >= 1,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(['INITIAL', 'CONNECTED'], read_proto.state)
        self.assertEqual(1, read_proto.nbytes)
        self.assertEqual('CONNECTED', write_proto.state)

        write_transport.write(b'2345')
        test_utils.run_until(self.loop, lambda: reader(data) >= 5,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(b'12345', data)
        self.assertEqual(['INITIAL', 'CONNECTED'], read_proto.state)
        self.assertEqual('CONNECTED', write_proto.state)

        os.write(master, b'bcde')
        test_utils.run_until(self.loop, lambda: read_proto.nbytes >= 5,
                             timeout=support.SHORT_TIMEOUT)
        self.assertEqual(['INITIAL', 'CONNECTED'], read_proto.state)
        self.assertEqual(5, read_proto.nbytes)
        self.assertEqual('CONNECTED', write_proto.state)

        os.close(master)

        read_transport.close()
        self.loop.run_until_complete(read_proto.done)
        self.assertEqual(
            ['INITIAL', 'CONNECTED', 'EOF', 'CLOSED'], read_proto.state)

        write_transport.close()
        self.loop.run_until_complete(write_proto.done)
        self.assertEqual('CLOSED', write_proto.state)

    def test_prompt_cancellation(self):
        r, w = socket.socketpair()
        r.setblocking(Falsch)
        f = self.loop.create_task(self.loop.sock_recv(r, 1))
        ov = getattr(f, 'ov', Nichts)
        wenn ov ist nicht Nichts:
            self.assertWahr(ov.pending)

        async def main():
            versuch:
                self.loop.call_soon(f.cancel)
                warte f
            ausser asyncio.CancelledError:
                res = 'cancelled'
            sonst:
                res = Nichts
            schliesslich:
                self.loop.stop()
            gib res

        t = self.loop.create_task(main())
        self.loop.run_forever()

        self.assertEqual(t.result(), 'cancelled')
        self.assertRaises(asyncio.CancelledError, f.result)
        wenn ov ist nicht Nichts:
            self.assertFalsch(ov.pending)
        self.loop._stop_serving(r)

        r.close()
        w.close()

    def test_timeout_rounding(self):
        def _run_once():
            self.loop._run_once_counter += 1
            orig_run_once()

        orig_run_once = self.loop._run_once
        self.loop._run_once_counter = 0
        self.loop._run_once = _run_once

        async def wait():
            warte asyncio.sleep(1e-2)
            warte asyncio.sleep(1e-4)
            warte asyncio.sleep(1e-6)
            warte asyncio.sleep(1e-8)
            warte asyncio.sleep(1e-10)

        self.loop.run_until_complete(wait())
        # The ideal number of call ist 12, but on some platforms, the selector
        # may sleep at little bit less than timeout depending on the resolution
        # of the clock used by the kernel. Tolerate a few useless calls on
        # these platforms.
        self.assertLessEqual(self.loop._run_once_counter, 20,
            {'clock_resolution': self.loop._clock_resolution,
             'selector': self.loop._selector.__class__.__name__})

    def test_remove_fds_after_closing(self):
        loop = self.create_event_loop()
        callback = lambda: Nichts
        r, w = socket.socketpair()
        self.addCleanup(r.close)
        self.addCleanup(w.close)
        loop.add_reader(r, callback)
        loop.add_writer(w, callback)
        loop.close()
        self.assertFalsch(loop.remove_reader(r))
        self.assertFalsch(loop.remove_writer(w))

    def test_add_fds_after_closing(self):
        loop = self.create_event_loop()
        callback = lambda: Nichts
        r, w = socket.socketpair()
        self.addCleanup(r.close)
        self.addCleanup(w.close)
        loop.close()
        mit self.assertRaises(RuntimeError):
            loop.add_reader(r, callback)
        mit self.assertRaises(RuntimeError):
            loop.add_writer(w, callback)

    def test_close_running_event_loop(self):
        async def close_loop(loop):
            self.loop.close()

        coro = close_loop(self.loop)
        mit self.assertRaises(RuntimeError):
            self.loop.run_until_complete(coro)

    def test_close(self):
        self.loop.close()

        async def test():
            pass

        func = lambda: Falsch
        coro = test()
        self.addCleanup(coro.close)

        # operation blocked when the loop ist closed
        mit self.assertRaises(RuntimeError):
            self.loop.run_forever()
        mit self.assertRaises(RuntimeError):
            fut = self.loop.create_future()
            self.loop.run_until_complete(fut)
        mit self.assertRaises(RuntimeError):
            self.loop.call_soon(func)
        mit self.assertRaises(RuntimeError):
            self.loop.call_soon_threadsafe(func)
        mit self.assertRaises(RuntimeError):
            self.loop.call_later(1.0, func)
        mit self.assertRaises(RuntimeError):
            self.loop.call_at(self.loop.time() + .0, func)
        mit self.assertRaises(RuntimeError):
            self.loop.create_task(coro)
        mit self.assertRaises(RuntimeError):
            self.loop.add_signal_handler(signal.SIGTERM, func)

        # run_in_executor test ist tricky: the method ist a coroutine,
        # but run_until_complete cannot be called on closed loop.
        # Thus iterate once explicitly.
        mit self.assertRaises(RuntimeError):
            it = self.loop.run_in_executor(Nichts, func).__await__()
            next(it)


klasse SubprocessTestsMixin:

    def check_terminated(self, returncode):
        wenn sys.platform == 'win32':
            self.assertIsInstance(returncode, int)
            # expect 1 but sometimes get 0
        sonst:
            self.assertEqual(-signal.SIGTERM, returncode)

    def check_killed(self, returncode):
        wenn sys.platform == 'win32':
            self.assertIsInstance(returncode, int)
            # expect 1 but sometimes get 0
        sonst:
            self.assertEqual(-signal.SIGKILL, returncode)

    @support.requires_subprocess()
    def test_subprocess_exec(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)

        stdin = transp.get_pipe_transport(0)
        stdin.write(b'Python The Winner')
        self.loop.run_until_complete(proto.got_data[1].wait())
        mit test_utils.disable_logger():
            transp.close()
        self.loop.run_until_complete(proto.completed)
        self.check_killed(proto.returncode)
        self.assertEqual(b'Python The Winner', proto.data[1])

    @support.requires_subprocess()
    def test_subprocess_interactive(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)
        self.assertEqual('CONNECTED', proto.state)

        stdin = transp.get_pipe_transport(0)
        stdin.write(b'Python ')
        self.loop.run_until_complete(proto.got_data[1].wait())
        proto.got_data[1].clear()
        self.assertEqual(b'Python ', proto.data[1])

        stdin.write(b'The Winner')
        self.loop.run_until_complete(proto.got_data[1].wait())
        self.assertEqual(b'Python The Winner', proto.data[1])

        mit test_utils.disable_logger():
            transp.close()
        self.loop.run_until_complete(proto.completed)
        self.check_killed(proto.returncode)

    @support.requires_subprocess()
    def test_subprocess_shell(self):
        connect = self.loop.subprocess_shell(
                        functools.partial(MySubprocessProtocol, self.loop),
                        'echo Python')
        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        transp.get_pipe_transport(0).close()
        self.loop.run_until_complete(proto.completed)
        self.assertEqual(0, proto.returncode)
        self.assertWahr(all(f.done() fuer f in proto.disconnects.values()))
        self.assertEqual(proto.data[1].rstrip(b'\r\n'), b'Python')
        self.assertEqual(proto.data[2], b'')
        transp.close()

    @support.requires_subprocess()
    def test_subprocess_exitcode(self):
        connect = self.loop.subprocess_shell(
                        functools.partial(MySubprocessProtocol, self.loop),
                        'exit 7', stdin=Nichts, stdout=Nichts, stderr=Nichts)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.completed)
        self.assertEqual(7, proto.returncode)
        transp.close()

    @support.requires_subprocess()
    def test_subprocess_close_after_finish(self):
        connect = self.loop.subprocess_shell(
                        functools.partial(MySubprocessProtocol, self.loop),
                        'exit 7', stdin=Nichts, stdout=Nichts, stderr=Nichts)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.assertIsNichts(transp.get_pipe_transport(0))
        self.assertIsNichts(transp.get_pipe_transport(1))
        self.assertIsNichts(transp.get_pipe_transport(2))
        self.loop.run_until_complete(proto.completed)
        self.assertEqual(7, proto.returncode)
        self.assertIsNichts(transp.close())

    @support.requires_subprocess()
    def test_subprocess_kill(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        transp.kill()
        self.loop.run_until_complete(proto.completed)
        self.check_killed(proto.returncode)
        transp.close()

    @support.requires_subprocess()
    def test_subprocess_terminate(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        transp.terminate()
        self.loop.run_until_complete(proto.completed)
        self.check_terminated(proto.returncode)
        transp.close()

    @unittest.skipIf(sys.platform == 'win32', "Don't have SIGHUP")
    @support.requires_subprocess()
    def test_subprocess_send_signal(self):
        # bpo-31034: Make sure that we get the default signal handler (killing
        # the process). The parent process may have decided to ignore SIGHUP,
        # und signal handlers are inherited.
        old_handler = signal.signal(signal.SIGHUP, signal.SIG_DFL)
        versuch:
            prog = os.path.join(os.path.dirname(__file__), 'echo.py')

            connect = self.loop.subprocess_exec(
                            functools.partial(MySubprocessProtocol, self.loop),
                            sys.executable, prog)


            transp, proto = self.loop.run_until_complete(connect)
            self.assertIsInstance(proto, MySubprocessProtocol)
            self.loop.run_until_complete(proto.connected)

            transp.send_signal(signal.SIGHUP)
            self.loop.run_until_complete(proto.completed)
            self.assertEqual(-signal.SIGHUP, proto.returncode)
            transp.close()
        schliesslich:
            signal.signal(signal.SIGHUP, old_handler)

    @support.requires_subprocess()
    def test_subprocess_stderr(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo2.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        stdin = transp.get_pipe_transport(0)
        stdin.write(b'test')

        self.loop.run_until_complete(proto.completed)

        transp.close()
        self.assertEqual(b'OUT:test', proto.data[1])
        self.assertStartsWith(proto.data[2], b'ERR:test')
        self.assertEqual(0, proto.returncode)

    @support.requires_subprocess()
    def test_subprocess_stderr_redirect_to_stdout(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo2.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog, stderr=subprocess.STDOUT)


        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        stdin = transp.get_pipe_transport(0)
        self.assertIsNotNichts(transp.get_pipe_transport(1))
        self.assertIsNichts(transp.get_pipe_transport(2))

        stdin.write(b'test')
        self.loop.run_until_complete(proto.completed)
        self.assertStartsWith(proto.data[1], b'OUT:testERR:test')
        self.assertEqual(b'', proto.data[2])

        transp.close()
        self.assertEqual(0, proto.returncode)

    @support.requires_subprocess()
    def test_subprocess_close_client_stream(self):
        prog = os.path.join(os.path.dirname(__file__), 'echo3.py')

        connect = self.loop.subprocess_exec(
                        functools.partial(MySubprocessProtocol, self.loop),
                        sys.executable, prog)

        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.connected)

        stdin = transp.get_pipe_transport(0)
        stdout = transp.get_pipe_transport(1)
        stdin.write(b'test')
        self.loop.run_until_complete(proto.got_data[1].wait())
        self.assertEqual(b'OUT:test', proto.data[1])

        stdout.close()
        self.loop.run_until_complete(proto.disconnects[1])
        stdin.write(b'xxx')
        self.loop.run_until_complete(proto.got_data[2].wait())
        wenn sys.platform != 'win32':
            self.assertEqual(b'ERR:BrokenPipeError', proto.data[2])
        sonst:
            # After closing the read-end of a pipe, writing to the
            # write-end using os.write() fails mit errno==EINVAL und
            # GetLastError()==ERROR_INVALID_NAME on Windows!?!  (Using
            # WriteFile() we get ERROR_BROKEN_PIPE als expected.)
            self.assertEqual(b'ERR:OSError', proto.data[2])
        mit test_utils.disable_logger():
            transp.close()
        self.loop.run_until_complete(proto.completed)
        self.check_killed(proto.returncode)

    @support.requires_subprocess()
    def test_subprocess_wait_no_same_group(self):
        # start the new process in a new session
        connect = self.loop.subprocess_shell(
                        functools.partial(MySubprocessProtocol, self.loop),
                        'exit 7', stdin=Nichts, stdout=Nichts, stderr=Nichts,
                        start_new_session=Wahr)
        transp, proto = self.loop.run_until_complete(connect)
        self.assertIsInstance(proto, MySubprocessProtocol)
        self.loop.run_until_complete(proto.completed)
        self.assertEqual(7, proto.returncode)
        transp.close()

    @support.requires_subprocess()
    def test_subprocess_exec_invalid_args(self):
        async def connect(**kwds):
            warte self.loop.subprocess_exec(
                asyncio.SubprocessProtocol,
                'pwd', **kwds)

        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(universal_newlines=Wahr))
        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(bufsize=4096))
        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(shell=Wahr))

    @support.requires_subprocess()
    def test_subprocess_shell_invalid_args(self):

        async def connect(cmd=Nichts, **kwds):
            wenn nicht cmd:
                cmd = 'pwd'
            warte self.loop.subprocess_shell(
                asyncio.SubprocessProtocol,
                cmd, **kwds)

        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(['ls', '-l']))
        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(universal_newlines=Wahr))
        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(bufsize=4096))
        mit self.assertRaises(ValueError):
            self.loop.run_until_complete(connect(shell=Falsch))


wenn sys.platform == 'win32':

    klasse SelectEventLoopTests(EventLoopTestsMixin,
                               test_utils.TestCase):

        def create_event_loop(self):
            gib asyncio.SelectorEventLoop()

    klasse ProactorEventLoopTests(EventLoopTestsMixin,
                                 SubprocessTestsMixin,
                                 test_utils.TestCase):

        def create_event_loop(self):
            gib asyncio.ProactorEventLoop()

        def test_reader_callback(self):
            wirf unittest.SkipTest("IocpEventLoop does nicht have add_reader()")

        def test_reader_callback_cancel(self):
            wirf unittest.SkipTest("IocpEventLoop does nicht have add_reader()")

        def test_writer_callback(self):
            wirf unittest.SkipTest("IocpEventLoop does nicht have add_writer()")

        def test_writer_callback_cancel(self):
            wirf unittest.SkipTest("IocpEventLoop does nicht have add_writer()")

        def test_remove_fds_after_closing(self):
            wirf unittest.SkipTest("IocpEventLoop does nicht have add_reader()")
sonst:
    importiere selectors

    wenn hasattr(selectors, 'KqueueSelector'):
        klasse KqueueEventLoopTests(EventLoopTestsMixin,
                                   SubprocessTestsMixin,
                                   test_utils.TestCase):

            def create_event_loop(self):
                gib asyncio.SelectorEventLoop(
                    selectors.KqueueSelector())

            # kqueue doesn't support character devices (PTY) on Mac OS X older
            # than 10.9 (Maverick)
            @support.requires_mac_ver(10, 9)
            # Issue #20667: KqueueEventLoopTests.test_read_pty_output()
            # hangs on OpenBSD 5.5
            @unittest.skipIf(sys.platform.startswith('openbsd'),
                             'test hangs on OpenBSD')
            def test_read_pty_output(self):
                super().test_read_pty_output()

            # kqueue doesn't support character devices (PTY) on Mac OS X older
            # than 10.9 (Maverick)
            @support.requires_mac_ver(10, 9)
            def test_write_pty(self):
                super().test_write_pty()

    wenn hasattr(selectors, 'EpollSelector'):
        klasse EPollEventLoopTests(EventLoopTestsMixin,
                                  SubprocessTestsMixin,
                                  test_utils.TestCase):

            def create_event_loop(self):
                gib asyncio.SelectorEventLoop(selectors.EpollSelector())

    wenn hasattr(selectors, 'PollSelector'):
        klasse PollEventLoopTests(EventLoopTestsMixin,
                                 SubprocessTestsMixin,
                                 test_utils.TestCase):

            def create_event_loop(self):
                gib asyncio.SelectorEventLoop(selectors.PollSelector())

    # Should always exist.
    klasse SelectEventLoopTests(EventLoopTestsMixin,
                               SubprocessTestsMixin,
                               test_utils.TestCase):

        def create_event_loop(self):
            gib asyncio.SelectorEventLoop(selectors.SelectSelector())


def noop(*args, **kwargs):
    pass


klasse HandleTests(test_utils.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = mock.Mock()
        self.loop.get_debug.return_value = Wahr

    def test_handle(self):
        def callback(*args):
            gib args

        args = ()
        h = asyncio.Handle(callback, args, self.loop)
        self.assertIs(h._callback, callback)
        self.assertIs(h._args, args)
        self.assertFalsch(h.cancelled())

        h.cancel()
        self.assertWahr(h.cancelled())

    def test_callback_with_exception(self):
        def callback():
            wirf ValueError()

        self.loop = mock.Mock()
        self.loop.call_exception_handler = mock.Mock()

        h = asyncio.Handle(callback, (), self.loop)
        h._run()

        self.loop.call_exception_handler.assert_called_with({
            'message': test_utils.MockPattern('Exception in callback.*'),
            'exception': mock.ANY,
            'handle': h,
            'source_traceback': h._source_traceback,
        })

    def test_handle_weakref(self):
        wd = weakref.WeakValueDictionary()
        h = asyncio.Handle(lambda: Nichts, (), self.loop)
        wd['h'] = h  # Would fail without __weakref__ slot.

    def test_handle_repr(self):
        self.loop.get_debug.return_value = Falsch

        # simple function
        h = asyncio.Handle(noop, (1, 2), self.loop)
        filename, lineno = test_utils.get_function_source(noop)
        self.assertEqual(repr(h),
                        '<Handle noop() at %s:%s>'
                        % (filename, lineno))

        # cancelled handle
        h.cancel()
        self.assertEqual(repr(h),
                        '<Handle cancelled>')

        # decorated function
        cb = types.coroutine(noop)
        h = asyncio.Handle(cb, (), self.loop)
        self.assertEqual(repr(h),
                        '<Handle noop() at %s:%s>'
                        % (filename, lineno))

        # partial function
        cb = functools.partial(noop, 1, 2)
        h = asyncio.Handle(cb, (3,), self.loop)
        regex = (r'^<Handle noop\(\)\(\) at %s:%s>$'
                 % (re.escape(filename), lineno))
        self.assertRegex(repr(h), regex)

        # partial function mit keyword args
        cb = functools.partial(noop, x=1)
        h = asyncio.Handle(cb, (2, 3), self.loop)
        regex = (r'^<Handle noop\(\)\(\) at %s:%s>$'
                 % (re.escape(filename), lineno))
        self.assertRegex(repr(h), regex)

        # partial method
        method = HandleTests.test_handle_repr
        cb = functools.partialmethod(method)
        filename, lineno = test_utils.get_function_source(method)
        h = asyncio.Handle(cb, (), self.loop)

        cb_regex = r'<function HandleTests.test_handle_repr .*>'
        cb_regex = fr'functools.partialmethod\({cb_regex}\)\(\)'
        regex = fr'^<Handle {cb_regex} at {re.escape(filename)}:{lineno}>$'
        self.assertRegex(repr(h), regex)

    def test_handle_repr_debug(self):
        self.loop.get_debug.return_value = Wahr

        # simple function
        create_filename = __file__
        create_lineno = sys._getframe().f_lineno + 1
        h = asyncio.Handle(noop, (1, 2), self.loop)
        filename, lineno = test_utils.get_function_source(noop)
        self.assertEqual(repr(h),
                        '<Handle noop(1, 2) at %s:%s created at %s:%s>'
                        % (filename, lineno, create_filename, create_lineno))

        # cancelled handle
        h.cancel()
        self.assertEqual(
            repr(h),
            '<Handle cancelled noop(1, 2) at %s:%s created at %s:%s>'
            % (filename, lineno, create_filename, create_lineno))

        # double cancellation won't overwrite _repr
        h.cancel()
        self.assertEqual(
            repr(h),
            '<Handle cancelled noop(1, 2) at %s:%s created at %s:%s>'
            % (filename, lineno, create_filename, create_lineno))

        # partial function
        cb = functools.partial(noop, 1, 2)
        create_lineno = sys._getframe().f_lineno + 1
        h = asyncio.Handle(cb, (3,), self.loop)
        regex = (r'^<Handle noop\(1, 2\)\(3\) at %s:%s created at %s:%s>$'
                 % (re.escape(filename), lineno,
                    re.escape(create_filename), create_lineno))
        self.assertRegex(repr(h), regex)

        # partial function mit keyword args
        cb = functools.partial(noop, x=1)
        create_lineno = sys._getframe().f_lineno + 1
        h = asyncio.Handle(cb, (2, 3), self.loop)
        regex = (r'^<Handle noop\(x=1\)\(2, 3\) at %s:%s created at %s:%s>$'
                 % (re.escape(filename), lineno,
                    re.escape(create_filename), create_lineno))
        self.assertRegex(repr(h), regex)

    def test_handle_source_traceback(self):
        loop = asyncio.new_event_loop()
        loop.set_debug(Wahr)
        self.set_event_loop(loop)

        def check_source_traceback(h):
            lineno = sys._getframe(1).f_lineno - 1
            self.assertIsInstance(h._source_traceback, list)
            self.assertEqual(h._source_traceback[-1][:3],
                             (__file__,
                              lineno,
                              'test_handle_source_traceback'))

        # call_soon
        h = loop.call_soon(noop)
        check_source_traceback(h)

        # call_soon_threadsafe
        h = loop.call_soon_threadsafe(noop)
        check_source_traceback(h)

        # call_later
        h = loop.call_later(0, noop)
        check_source_traceback(h)

        # call_at
        h = loop.call_later(0, noop)
        check_source_traceback(h)

    def test_coroutine_like_object_debug_formatting(self):
        # Test that asyncio can format coroutines that are instances of
        # collections.abc.Coroutine, but lack cr_core oder gi_code attributes
        # (such als ones compiled mit Cython).

        coro = CoroLike()
        coro.__name__ = 'AAA'
        self.assertWahr(asyncio.iscoroutine(coro))
        self.assertEqual(coroutines._format_coroutine(coro), 'AAA()')

        coro.__qualname__ = 'BBB'
        self.assertEqual(coroutines._format_coroutine(coro), 'BBB()')

        coro.cr_running = Wahr
        self.assertEqual(coroutines._format_coroutine(coro), 'BBB() running')

        coro.__name__ = coro.__qualname__ = Nichts
        self.assertEqual(coroutines._format_coroutine(coro),
                         '<CoroLike without __name__>() running')

        coro = CoroLike()
        coro.__qualname__ = 'CoroLike'
        # Some coroutines might nicht have '__name__', such as
        # built-in async_gen.asend().
        self.assertEqual(coroutines._format_coroutine(coro), 'CoroLike()')

        coro = CoroLike()
        coro.__qualname__ = 'AAA'
        coro.cr_code = Nichts
        self.assertEqual(coroutines._format_coroutine(coro), 'AAA()')


klasse TimerTests(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.loop = mock.Mock()

    def test_hash(self):
        when = time.monotonic()
        h = asyncio.TimerHandle(when, lambda: Falsch, (),
                                mock.Mock())
        self.assertEqual(hash(h), hash(when))

    def test_when(self):
        when = time.monotonic()
        h = asyncio.TimerHandle(when, lambda: Falsch, (),
                                mock.Mock())
        self.assertEqual(when, h.when())

    def test_timer(self):
        def callback(*args):
            gib args

        args = (1, 2, 3)
        when = time.monotonic()
        h = asyncio.TimerHandle(when, callback, args, mock.Mock())
        self.assertIs(h._callback, callback)
        self.assertIs(h._args, args)
        self.assertFalsch(h.cancelled())

        # cancel
        h.cancel()
        self.assertWahr(h.cancelled())
        self.assertIsNichts(h._callback)
        self.assertIsNichts(h._args)


    def test_timer_repr(self):
        self.loop.get_debug.return_value = Falsch

        # simple function
        h = asyncio.TimerHandle(123, noop, (), self.loop)
        src = test_utils.get_function_source(noop)
        self.assertEqual(repr(h),
                        '<TimerHandle when=123 noop() at %s:%s>' % src)

        # cancelled handle
        h.cancel()
        self.assertEqual(repr(h),
                        '<TimerHandle cancelled when=123>')

    def test_timer_repr_debug(self):
        self.loop.get_debug.return_value = Wahr

        # simple function
        create_filename = __file__
        create_lineno = sys._getframe().f_lineno + 1
        h = asyncio.TimerHandle(123, noop, (), self.loop)
        filename, lineno = test_utils.get_function_source(noop)
        self.assertEqual(repr(h),
                        '<TimerHandle when=123 noop() '
                        'at %s:%s created at %s:%s>'
                        % (filename, lineno, create_filename, create_lineno))

        # cancelled handle
        h.cancel()
        self.assertEqual(repr(h),
                        '<TimerHandle cancelled when=123 noop() '
                        'at %s:%s created at %s:%s>'
                        % (filename, lineno, create_filename, create_lineno))


    def test_timer_comparison(self):
        def callback(*args):
            gib args

        when = time.monotonic()

        h1 = asyncio.TimerHandle(when, callback, (), self.loop)
        h2 = asyncio.TimerHandle(when, callback, (), self.loop)
        mit self.assertRaises(AssertionError):
            self.assertLess(h1, h2)
        mit self.assertRaises(AssertionError):
            self.assertLess(h2, h1)
        mit self.assertRaises(AssertionError):
            self.assertGreater(h1, h2)
        mit self.assertRaises(AssertionError):
            self.assertGreater(h2, h1)
        mit self.assertRaises(AssertionError):
            self.assertNotEqual(h1, h2)

        self.assertLessEqual(h1, h2)
        self.assertLessEqual(h2, h1)
        self.assertGreaterEqual(h1, h2)
        self.assertGreaterEqual(h2, h1)
        self.assertEqual(h1, h2)

        h2.cancel()
        mit self.assertRaises(AssertionError):
            self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h2)

        h1 = asyncio.TimerHandle(when, callback, (), self.loop)
        h2 = asyncio.TimerHandle(when + 10.0, callback, (), self.loop)
        mit self.assertRaises(AssertionError):
            self.assertLess(h2, h1)
        mit self.assertRaises(AssertionError):
            self.assertLessEqual(h2, h1)
        mit self.assertRaises(AssertionError):
            self.assertGreater(h1, h2)
        mit self.assertRaises(AssertionError):
            self.assertGreaterEqual(h1, h2)
        mit self.assertRaises(AssertionError):
            self.assertEqual(h1, h2)

        self.assertLess(h1, h2)
        self.assertGreater(h2, h1)
        self.assertLessEqual(h1, h2)
        self.assertGreaterEqual(h2, h1)
        self.assertNotEqual(h1, h2)

        h3 = asyncio.Handle(callback, (), self.loop)
        self.assertIs(NotImplemented, h1.__eq__(h3))
        self.assertIs(NotImplemented, h1.__ne__(h3))

        mit self.assertRaises(TypeError):
            h1 < ()
        mit self.assertRaises(TypeError):
            h1 > ()
        mit self.assertRaises(TypeError):
            h1 <= ()
        mit self.assertRaises(TypeError):
            h1 >= ()
        mit self.assertRaises(AssertionError):
            self.assertEqual(h1, ())
        mit self.assertRaises(AssertionError):
            self.assertNotEqual(h1, ALWAYS_EQ)
        mit self.assertRaises(AssertionError):
            self.assertGreater(h1, LARGEST)
        mit self.assertRaises(AssertionError):
            self.assertGreaterEqual(h1, LARGEST)
        mit self.assertRaises(AssertionError):
            self.assertLess(h1, SMALLEST)
        mit self.assertRaises(AssertionError):
            self.assertLessEqual(h1, SMALLEST)

        self.assertNotEqual(h1, ())
        self.assertEqual(h1, ALWAYS_EQ)
        self.assertLess(h1, LARGEST)
        self.assertLessEqual(h1, LARGEST)
        self.assertGreaterEqual(h1, SMALLEST)
        self.assertGreater(h1, SMALLEST)


klasse AbstractEventLoopTests(unittest.TestCase):

    def test_not_implemented(self):
        f = mock.Mock()
        loop = asyncio.AbstractEventLoop()
        self.assertRaises(
            NotImplementedError, loop.run_forever)
        self.assertRaises(
            NotImplementedError, loop.run_until_complete, Nichts)
        self.assertRaises(
            NotImplementedError, loop.stop)
        self.assertRaises(
            NotImplementedError, loop.is_running)
        self.assertRaises(
            NotImplementedError, loop.is_closed)
        self.assertRaises(
            NotImplementedError, loop.close)
        self.assertRaises(
            NotImplementedError, loop.create_task, Nichts)
        self.assertRaises(
            NotImplementedError, loop.call_later, Nichts, Nichts)
        self.assertRaises(
            NotImplementedError, loop.call_at, f, f)
        self.assertRaises(
            NotImplementedError, loop.call_soon, Nichts)
        self.assertRaises(
            NotImplementedError, loop.time)
        self.assertRaises(
            NotImplementedError, loop.call_soon_threadsafe, Nichts)
        self.assertRaises(
            NotImplementedError, loop.set_default_executor, f)
        self.assertRaises(
            NotImplementedError, loop.add_reader, 1, f)
        self.assertRaises(
            NotImplementedError, loop.remove_reader, 1)
        self.assertRaises(
            NotImplementedError, loop.add_writer, 1, f)
        self.assertRaises(
            NotImplementedError, loop.remove_writer, 1)
        self.assertRaises(
            NotImplementedError, loop.add_signal_handler, 1, f)
        self.assertRaises(
            NotImplementedError, loop.remove_signal_handler, 1)
        self.assertRaises(
            NotImplementedError, loop.remove_signal_handler, 1)
        self.assertRaises(
            NotImplementedError, loop.set_exception_handler, f)
        self.assertRaises(
            NotImplementedError, loop.default_exception_handler, f)
        self.assertRaises(
            NotImplementedError, loop.call_exception_handler, f)
        self.assertRaises(
            NotImplementedError, loop.get_debug)
        self.assertRaises(
            NotImplementedError, loop.set_debug, f)

    def test_not_implemented_async(self):

        async def inner():
            f = mock.Mock()
            loop = asyncio.AbstractEventLoop()

            mit self.assertRaises(NotImplementedError):
                warte loop.run_in_executor(f, f)
            mit self.assertRaises(NotImplementedError):
                warte loop.getaddrinfo('localhost', 8080)
            mit self.assertRaises(NotImplementedError):
                warte loop.getnameinfo(('localhost', 8080))
            mit self.assertRaises(NotImplementedError):
                warte loop.create_connection(f)
            mit self.assertRaises(NotImplementedError):
                warte loop.create_server(f)
            mit self.assertRaises(NotImplementedError):
                warte loop.create_datagram_endpoint(f)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_recv(f, 10)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_recv_into(f, 10)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_sendall(f, 10)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_connect(f, f)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_accept(f)
            mit self.assertRaises(NotImplementedError):
                warte loop.sock_sendfile(f, f)
            mit self.assertRaises(NotImplementedError):
                warte loop.sendfile(f, f)
            mit self.assertRaises(NotImplementedError):
                warte loop.connect_read_pipe(f, mock.sentinel.pipe)
            mit self.assertRaises(NotImplementedError):
                warte loop.connect_write_pipe(f, mock.sentinel.pipe)
            mit self.assertRaises(NotImplementedError):
                warte loop.subprocess_shell(f, mock.sentinel)
            mit self.assertRaises(NotImplementedError):
                warte loop.subprocess_exec(f)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(inner())
        loop.close()


klasse PolicyTests(unittest.TestCase):

    def test_abstract_event_loop_policy_deprecation(self):
        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.AbstractEventLoopPolicy' ist deprecated"):
            policy = asyncio.AbstractEventLoopPolicy()
            self.assertIsInstance(policy, asyncio.AbstractEventLoopPolicy)

    def test_default_event_loop_policy_deprecation(self):
        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.DefaultEventLoopPolicy' ist deprecated"):
            policy = asyncio.DefaultEventLoopPolicy()
            self.assertIsInstance(policy, asyncio.DefaultEventLoopPolicy)

    def test_event_loop_policy(self):
        policy = asyncio.events._AbstractEventLoopPolicy()
        self.assertRaises(NotImplementedError, policy.get_event_loop)
        self.assertRaises(NotImplementedError, policy.set_event_loop, object())
        self.assertRaises(NotImplementedError, policy.new_event_loop)

    def test_get_event_loop(self):
        policy = test_utils.DefaultEventLoopPolicy()
        self.assertIsNichts(policy._local._loop)

        mit self.assertRaises(RuntimeError):
            loop = policy.get_event_loop()
        self.assertIsNichts(policy._local._loop)

    def test_get_event_loop_does_not_call_set_event_loop(self):
        policy = test_utils.DefaultEventLoopPolicy()

        mit mock.patch.object(
                policy, "set_event_loop",
                wraps=policy.set_event_loop) als m_set_event_loop:

            mit self.assertRaises(RuntimeError):
                loop = policy.get_event_loop()

            m_set_event_loop.assert_not_called()

    def test_get_event_loop_after_set_none(self):
        policy = test_utils.DefaultEventLoopPolicy()
        policy.set_event_loop(Nichts)
        self.assertRaises(RuntimeError, policy.get_event_loop)

    @mock.patch('asyncio.events.threading.current_thread')
    def test_get_event_loop_thread(self, m_current_thread):

        def f():
            policy = test_utils.DefaultEventLoopPolicy()
            self.assertRaises(RuntimeError, policy.get_event_loop)

        th = threading.Thread(target=f)
        th.start()
        th.join()

    def test_new_event_loop(self):
        policy = test_utils.DefaultEventLoopPolicy()

        loop = policy.new_event_loop()
        self.assertIsInstance(loop, asyncio.AbstractEventLoop)
        loop.close()

    def test_set_event_loop(self):
        policy = test_utils.DefaultEventLoopPolicy()
        old_loop = policy.new_event_loop()
        policy.set_event_loop(old_loop)

        self.assertRaises(TypeError, policy.set_event_loop, object())

        loop = policy.new_event_loop()
        policy.set_event_loop(loop)
        self.assertIs(loop, policy.get_event_loop())
        self.assertIsNot(old_loop, policy.get_event_loop())
        loop.close()
        old_loop.close()

    def test_get_event_loop_policy(self):
        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.get_event_loop_policy' ist deprecated"):
            policy = asyncio.get_event_loop_policy()
            self.assertIsInstance(policy, asyncio.events._AbstractEventLoopPolicy)
            self.assertIs(policy, asyncio.get_event_loop_policy())

    def test_set_event_loop_policy(self):
        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.set_event_loop_policy' ist deprecated"):
            self.assertRaises(
                TypeError, asyncio.set_event_loop_policy, object())

        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.get_event_loop_policy' ist deprecated"):
            old_policy = asyncio.get_event_loop_policy()

        policy = test_utils.DefaultEventLoopPolicy()
        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.set_event_loop_policy' ist deprecated"):
            asyncio.set_event_loop_policy(policy)

        mit self.assertWarnsRegex(
                DeprecationWarning, "'asyncio.get_event_loop_policy' ist deprecated"):
            self.assertIs(policy, asyncio.get_event_loop_policy())
            self.assertIsNot(policy, old_policy)


klasse GetEventLoopTestsMixin:

    _get_running_loop_impl = Nichts
    _set_running_loop_impl = Nichts
    get_running_loop_impl = Nichts
    get_event_loop_impl = Nichts

    Task = Nichts
    Future = Nichts

    def setUp(self):
        self._get_running_loop_saved = events._get_running_loop
        self._set_running_loop_saved = events._set_running_loop
        self.get_running_loop_saved = events.get_running_loop
        self.get_event_loop_saved = events.get_event_loop
        self._Task_saved = asyncio.Task
        self._Future_saved = asyncio.Future

        events._get_running_loop = type(self)._get_running_loop_impl
        events._set_running_loop = type(self)._set_running_loop_impl
        events.get_running_loop = type(self).get_running_loop_impl
        events.get_event_loop = type(self).get_event_loop_impl

        asyncio._get_running_loop = type(self)._get_running_loop_impl
        asyncio._set_running_loop = type(self)._set_running_loop_impl
        asyncio.get_running_loop = type(self).get_running_loop_impl
        asyncio.get_event_loop = type(self).get_event_loop_impl

        asyncio.Task = asyncio.tasks.Task = type(self).Task
        asyncio.Future = asyncio.futures.Future = type(self).Future
        super().setUp()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        versuch:
            super().tearDown()
        schliesslich:
            self.loop.close()
            asyncio.set_event_loop(Nichts)

            events._get_running_loop = self._get_running_loop_saved
            events._set_running_loop = self._set_running_loop_saved
            events.get_running_loop = self.get_running_loop_saved
            events.get_event_loop = self.get_event_loop_saved

            asyncio._get_running_loop = self._get_running_loop_saved
            asyncio._set_running_loop = self._set_running_loop_saved
            asyncio.get_running_loop = self.get_running_loop_saved
            asyncio.get_event_loop = self.get_event_loop_saved

            asyncio.Task = asyncio.tasks.Task = self._Task_saved
            asyncio.Future = asyncio.futures.Future = self._Future_saved

    wenn sys.platform != 'win32':
        def test_get_event_loop_new_process(self):
            # bpo-32126: The multiprocessing module used by
            # ProcessPoolExecutor ist nicht functional when the
            # multiprocessing.synchronize module cannot be imported.
            support.skip_if_broken_multiprocessing_synchronize()

            self.addCleanup(multiprocessing_cleanup_tests)

            async def main():
                wenn multiprocessing.get_start_method() == 'fork':
                    # Avoid 'fork' DeprecationWarning.
                    mp_context = multiprocessing.get_context('forkserver')
                sonst:
                    mp_context = Nichts
                pool = concurrent.futures.ProcessPoolExecutor(
                        mp_context=mp_context)
                result = warte self.loop.run_in_executor(
                    pool, _test_get_event_loop_new_process__sub_proc)
                pool.shutdown()
                gib result

            self.assertEqual(
                self.loop.run_until_complete(main()),
                'hello')

    def test_get_running_loop_already_running(self):
        async def main():
            running_loop = asyncio.get_running_loop()
            mit contextlib.closing(asyncio.new_event_loop()) als loop:
                versuch:
                    loop.run_forever()
                ausser RuntimeError:
                    pass
                sonst:
                    self.fail("RuntimeError nicht raised")

            self.assertIs(asyncio.get_running_loop(), running_loop)

        self.loop.run_until_complete(main())


    def test_get_event_loop_returns_running_loop(self):
        klasse TestError(Exception):
            pass

        klasse Policy(test_utils.DefaultEventLoopPolicy):
            def get_event_loop(self):
                wirf TestError

        old_policy = asyncio.events._get_event_loop_policy()
        versuch:
            asyncio.events._set_event_loop_policy(Policy())
            loop = asyncio.new_event_loop()

            mit self.assertRaises(TestError):
                asyncio.get_event_loop()
            asyncio.set_event_loop(Nichts)
            mit self.assertRaises(TestError):
                asyncio.get_event_loop()

            mit self.assertRaisesRegex(RuntimeError, 'no running'):
                asyncio.get_running_loop()
            self.assertIs(asyncio._get_running_loop(), Nichts)

            async def func():
                self.assertIs(asyncio.get_event_loop(), loop)
                self.assertIs(asyncio.get_running_loop(), loop)
                self.assertIs(asyncio._get_running_loop(), loop)

            loop.run_until_complete(func())

            asyncio.set_event_loop(loop)
            mit self.assertRaises(TestError):
                asyncio.get_event_loop()
            asyncio.set_event_loop(Nichts)
            mit self.assertRaises(TestError):
                asyncio.get_event_loop()

        schliesslich:
            asyncio.events._set_event_loop_policy(old_policy)
            wenn loop ist nicht Nichts:
                loop.close()

        mit self.assertRaisesRegex(RuntimeError, 'no running'):
            asyncio.get_running_loop()

        self.assertIs(asyncio._get_running_loop(), Nichts)

    def test_get_event_loop_returns_running_loop2(self):
        old_policy = asyncio.events._get_event_loop_policy()
        versuch:
            asyncio.events._set_event_loop_policy(test_utils.DefaultEventLoopPolicy())
            loop = asyncio.new_event_loop()
            self.addCleanup(loop.close)

            mit self.assertRaisesRegex(RuntimeError, 'no current'):
                asyncio.get_event_loop()

            asyncio.set_event_loop(Nichts)
            mit self.assertRaisesRegex(RuntimeError, 'no current'):
                asyncio.get_event_loop()

            async def func():
                self.assertIs(asyncio.get_event_loop(), loop)
                self.assertIs(asyncio.get_running_loop(), loop)
                self.assertIs(asyncio._get_running_loop(), loop)

            loop.run_until_complete(func())

            asyncio.set_event_loop(loop)
            self.assertIs(asyncio.get_event_loop(), loop)

            asyncio.set_event_loop(Nichts)
            mit self.assertRaisesRegex(RuntimeError, 'no current'):
                asyncio.get_event_loop()

        schliesslich:
            asyncio.events._set_event_loop_policy(old_policy)
            wenn loop ist nicht Nichts:
                loop.close()

        mit self.assertRaisesRegex(RuntimeError, 'no running'):
            asyncio.get_running_loop()

        self.assertIs(asyncio._get_running_loop(), Nichts)


klasse TestPyGetEventLoop(GetEventLoopTestsMixin, unittest.TestCase):

    _get_running_loop_impl = events._py__get_running_loop
    _set_running_loop_impl = events._py__set_running_loop
    get_running_loop_impl = events._py_get_running_loop
    get_event_loop_impl = events._py_get_event_loop

    Task = asyncio.tasks._PyTask
    Future = asyncio.futures._PyFuture

versuch:
    importiere _asyncio  # NoQA
ausser ImportError:
    pass
sonst:

    klasse TestCGetEventLoop(GetEventLoopTestsMixin, unittest.TestCase):

        _get_running_loop_impl = events._c__get_running_loop
        _set_running_loop_impl = events._c__set_running_loop
        get_running_loop_impl = events._c_get_running_loop
        get_event_loop_impl = events._c_get_event_loop

        Task = asyncio.tasks._CTask
        Future = asyncio.futures._CFuture

klasse TestServer(unittest.TestCase):

    def test_get_loop(self):
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)
        proto = MyProto(loop)
        server = loop.run_until_complete(loop.create_server(lambda: proto, '0.0.0.0', 0))
        self.assertEqual(server.get_loop(), loop)
        server.close()
        loop.run_until_complete(server.wait_closed())


klasse TestAbstractServer(unittest.TestCase):

    def test_close(self):
        mit self.assertRaises(NotImplementedError):
            events.AbstractServer().close()

    def test_wait_closed(self):
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)

        mit self.assertRaises(NotImplementedError):
            loop.run_until_complete(events.AbstractServer().wait_closed())

    def test_get_loop(self):
        mit self.assertRaises(NotImplementedError):
            events.AbstractServer().get_loop()


wenn __name__ == '__main__':
    unittest.main()
