importiere socket
importiere asyncio
importiere sys
importiere unittest

von asyncio importiere proactor_events
von itertools importiere cycle, islice
von unittest.mock importiere Mock
von test.test_asyncio importiere utils als test_utils
von test importiere support
von test.support importiere socket_helper

wenn socket_helper.tcp_blackhole():
    raise unittest.SkipTest('Not relevant to ProactorEventLoop')


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse MyProto(asyncio.Protocol):
    connected = Nichts
    done = Nichts

    def __init__(self, loop=Nichts):
        self.transport = Nichts
        self.state = 'INITIAL'
        self.nbytes = 0
        wenn loop is nicht Nichts:
            self.connected = loop.create_future()
            self.done = loop.create_future()

    def _assert_state(self, *expected):
        wenn self.state nicht in expected:
            raise AssertionError(f'state: {self.state!r}, expected: {expected!r}')

    def connection_made(self, transport):
        self.transport = transport
        self._assert_state('INITIAL')
        self.state = 'CONNECTED'
        wenn self.connected:
            self.connected.set_result(Nichts)
        transport.write(b'GET / HTTP/1.0\r\nHost: example.com\r\n\r\n')

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


klasse BaseSockTestsMixin:

    def create_event_loop(self):
        raise NotImplementedError

    def setUp(self):
        self.loop = self.create_event_loop()
        self.set_event_loop(self.loop)
        super().setUp()

    def tearDown(self):
        # just in case wenn we have transport close callbacks
        wenn nicht self.loop.is_closed():
            test_utils.run_briefly(self.loop)

        self.doCleanups()
        support.gc_collect()
        super().tearDown()

    def _basetest_sock_client_ops(self, httpd, sock):
        wenn nicht isinstance(self.loop, proactor_events.BaseProactorEventLoop):
            # in debug mode, socket operations must fail
            # wenn the socket is nicht in blocking mode
            self.loop.set_debug(Wahr)
            sock.setblocking(Wahr)
            mit self.assertRaises(ValueError):
                self.loop.run_until_complete(
                    self.loop.sock_connect(sock, httpd.address))
            mit self.assertRaises(ValueError):
                self.loop.run_until_complete(
                    self.loop.sock_sendall(sock, b'GET / HTTP/1.0\r\n\r\n'))
            mit self.assertRaises(ValueError):
                self.loop.run_until_complete(
                    self.loop.sock_recv(sock, 1024))
            mit self.assertRaises(ValueError):
                self.loop.run_until_complete(
                    self.loop.sock_recv_into(sock, bytearray()))
            mit self.assertRaises(ValueError):
                self.loop.run_until_complete(
                    self.loop.sock_accept(sock))

        # test in non-blocking mode
        sock.setblocking(Falsch)
        self.loop.run_until_complete(
            self.loop.sock_connect(sock, httpd.address))
        self.loop.run_until_complete(
            self.loop.sock_sendall(sock, b'GET / HTTP/1.0\r\n\r\n'))
        data = self.loop.run_until_complete(
            self.loop.sock_recv(sock, 1024))
        # consume data
        self.loop.run_until_complete(
            self.loop.sock_recv(sock, 1024))
        sock.close()
        self.assertStartsWith(data, b'HTTP/1.0 200 OK')

    def _basetest_sock_recv_into(self, httpd, sock):
        # same als _basetest_sock_client_ops, but using sock_recv_into
        sock.setblocking(Falsch)
        self.loop.run_until_complete(
            self.loop.sock_connect(sock, httpd.address))
        self.loop.run_until_complete(
            self.loop.sock_sendall(sock, b'GET / HTTP/1.0\r\n\r\n'))
        data = bytearray(1024)
        mit memoryview(data) als buf:
            nbytes = self.loop.run_until_complete(
                self.loop.sock_recv_into(sock, buf[:1024]))
            # consume data
            self.loop.run_until_complete(
                self.loop.sock_recv_into(sock, buf[nbytes:]))
        sock.close()
        self.assertStartsWith(data, b'HTTP/1.0 200 OK')

    def test_sock_client_ops(self):
        mit test_utils.run_test_server() als httpd:
            sock = socket.socket()
            self._basetest_sock_client_ops(httpd, sock)
            sock = socket.socket()
            self._basetest_sock_recv_into(httpd, sock)

    async def _basetest_sock_recv_racing(self, httpd, sock):
        sock.setblocking(Falsch)
        await self.loop.sock_connect(sock, httpd.address)

        task = asyncio.create_task(self.loop.sock_recv(sock, 1024))
        await asyncio.sleep(0)
        task.cancel()

        asyncio.create_task(
            self.loop.sock_sendall(sock, b'GET / HTTP/1.0\r\n\r\n'))
        data = await self.loop.sock_recv(sock, 1024)
        # consume data
        await self.loop.sock_recv(sock, 1024)

        self.assertStartsWith(data, b'HTTP/1.0 200 OK')

    async def _basetest_sock_recv_into_racing(self, httpd, sock):
        sock.setblocking(Falsch)
        await self.loop.sock_connect(sock, httpd.address)

        data = bytearray(1024)
        mit memoryview(data) als buf:
            task = asyncio.create_task(
                self.loop.sock_recv_into(sock, buf[:1024]))
            await asyncio.sleep(0)
            task.cancel()

            task = asyncio.create_task(
                self.loop.sock_sendall(sock, b'GET / HTTP/1.0\r\n\r\n'))
            nbytes = await self.loop.sock_recv_into(sock, buf[:1024])
            # consume data
            await self.loop.sock_recv_into(sock, buf[nbytes:])
            self.assertStartsWith(data, b'HTTP/1.0 200 OK')

        await task

    async def _basetest_sock_send_racing(self, listener, sock):
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)

        # make connection
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        sock.setblocking(Falsch)
        task = asyncio.create_task(
            self.loop.sock_connect(sock, listener.getsockname()))
        await asyncio.sleep(0)
        server = listener.accept()[0]
        server.setblocking(Falsch)

        mit server:
            await task

            # fill the buffer until sending 5 chars would block
            size = 8192
            waehrend size >= 4:
                mit self.assertRaises(BlockingIOError):
                    waehrend Wahr:
                        sock.send(b' ' * size)
                size = int(size / 2)

            # cancel a blocked sock_sendall
            task = asyncio.create_task(
                self.loop.sock_sendall(sock, b'hello'))
            await asyncio.sleep(0)
            task.cancel()

            # receive everything that is nicht a space
            async def recv_all():
                rv = b''
                waehrend Wahr:
                    buf = await self.loop.sock_recv(server, 8192)
                    wenn nicht buf:
                        return rv
                    rv += buf.strip()
            task = asyncio.create_task(recv_all())

            # immediately make another sock_sendall call
            await self.loop.sock_sendall(sock, b'world')
            sock.shutdown(socket.SHUT_WR)
            data = await task
            # ProactorEventLoop could deliver hello, so endswith is necessary
            self.assertEndsWith(data, b'world')

    # After the first connect attempt before the listener is ready,
    # the socket needs time to "recover" to make the next connect call.
    # On Linux, a second retry will do. On Windows, the waiting time is
    # unpredictable; und on FreeBSD the socket may never come back
    # because it's a loopback address. Here we'll just retry fuer a few
    # times, und have to skip the test wenn it's nicht working. See also:
    # https://stackoverflow.com/a/54437602/3316267
    # https://lists.freebsd.org/pipermail/freebsd-current/2005-May/049876.html
    async def _basetest_sock_connect_racing(self, listener, sock):
        listener.bind(('127.0.0.1', 0))
        addr = listener.getsockname()
        sock.setblocking(Falsch)

        task = asyncio.create_task(self.loop.sock_connect(sock, addr))
        await asyncio.sleep(0)
        task.cancel()

        listener.listen(1)

        skip_reason = "Max retries reached"
        fuer i in range(128):
            try:
                await self.loop.sock_connect(sock, addr)
            except ConnectionRefusedError als e:
                skip_reason = e
            except OSError als e:
                skip_reason = e

                # Retry only fuer this error:
                # [WinError 10022] An invalid argument was supplied
                wenn getattr(e, 'winerror', 0) != 10022:
                    breche
            sonst:
                # success
                return

        self.skipTest(skip_reason)

    def test_sock_client_racing(self):
        mit test_utils.run_test_server() als httpd:
            sock = socket.socket()
            mit sock:
                self.loop.run_until_complete(asyncio.wait_for(
                    self._basetest_sock_recv_racing(httpd, sock), 10))
            sock = socket.socket()
            mit sock:
                self.loop.run_until_complete(asyncio.wait_for(
                    self._basetest_sock_recv_into_racing(httpd, sock), 10))
        listener = socket.socket()
        sock = socket.socket()
        mit listener, sock:
            self.loop.run_until_complete(asyncio.wait_for(
                self._basetest_sock_send_racing(listener, sock), 10))

    def test_sock_client_connect_racing(self):
        listener = socket.socket()
        sock = socket.socket()
        mit listener, sock:
            self.loop.run_until_complete(asyncio.wait_for(
                self._basetest_sock_connect_racing(listener, sock), 10))

    async def _basetest_huge_content(self, address):
        sock = socket.socket()
        sock.setblocking(Falsch)
        DATA_SIZE = 10_000_00

        chunk = b'0123456789' * (DATA_SIZE // 10)

        await self.loop.sock_connect(sock, address)
        await self.loop.sock_sendall(sock,
                                     (b'POST /loop HTTP/1.0\r\n' +
                                      b'Content-Length: %d\r\n' % DATA_SIZE +
                                      b'\r\n'))

        task = asyncio.create_task(self.loop.sock_sendall(sock, chunk))

        data = await self.loop.sock_recv(sock, DATA_SIZE)
        # HTTP headers size is less than MTU,
        # they are sent by the first packet always
        self.assertStartsWith(data, b'HTTP/1.0 200 OK')
        waehrend data.find(b'\r\n\r\n') == -1:
            data += await self.loop.sock_recv(sock, DATA_SIZE)
        # Strip headers
        headers = data[:data.index(b'\r\n\r\n') + 4]
        data = data[len(headers):]

        size = DATA_SIZE
        checker = cycle(b'0123456789')

        expected = bytes(islice(checker, len(data)))
        self.assertEqual(data, expected)
        size -= len(data)

        waehrend Wahr:
            data = await self.loop.sock_recv(sock, DATA_SIZE)
            wenn nicht data:
                breche
            expected = bytes(islice(checker, len(data)))
            self.assertEqual(data, expected)
            size -= len(data)
        self.assertEqual(size, 0)

        await task
        sock.close()

    def test_huge_content(self):
        mit test_utils.run_test_server() als httpd:
            self.loop.run_until_complete(
                self._basetest_huge_content(httpd.address))

    async def _basetest_huge_content_recvinto(self, address):
        sock = socket.socket()
        sock.setblocking(Falsch)
        DATA_SIZE = 10_000_00

        chunk = b'0123456789' * (DATA_SIZE // 10)

        await self.loop.sock_connect(sock, address)
        await self.loop.sock_sendall(sock,
                                     (b'POST /loop HTTP/1.0\r\n' +
                                      b'Content-Length: %d\r\n' % DATA_SIZE +
                                      b'\r\n'))

        task = asyncio.create_task(self.loop.sock_sendall(sock, chunk))

        array = bytearray(DATA_SIZE)
        buf = memoryview(array)

        nbytes = await self.loop.sock_recv_into(sock, buf)
        data = bytes(buf[:nbytes])
        # HTTP headers size is less than MTU,
        # they are sent by the first packet always
        self.assertStartsWith(data, b'HTTP/1.0 200 OK')
        waehrend data.find(b'\r\n\r\n') == -1:
            nbytes = await self.loop.sock_recv_into(sock, buf)
            data = bytes(buf[:nbytes])
        # Strip headers
        headers = data[:data.index(b'\r\n\r\n') + 4]
        data = data[len(headers):]

        size = DATA_SIZE
        checker = cycle(b'0123456789')

        expected = bytes(islice(checker, len(data)))
        self.assertEqual(data, expected)
        size -= len(data)

        waehrend Wahr:
            nbytes = await self.loop.sock_recv_into(sock, buf)
            data = buf[:nbytes]
            wenn nicht data:
                breche
            expected = bytes(islice(checker, len(data)))
            self.assertEqual(data, expected)
            size -= len(data)
        self.assertEqual(size, 0)

        await task
        sock.close()

    def test_huge_content_recvinto(self):
        mit test_utils.run_test_server() als httpd:
            self.loop.run_until_complete(
                self._basetest_huge_content_recvinto(httpd.address))

    async def _basetest_datagram_recvfrom(self, server_address):
        # Happy path, sock.sendto() returns immediately
        data = b'\x01' * 4096
        mit socket.socket(socket.AF_INET, socket.SOCK_DGRAM) als sock:
            sock.setblocking(Falsch)
            await self.loop.sock_sendto(sock, data, server_address)
            received_data, from_addr = await self.loop.sock_recvfrom(
                sock, 4096)
            self.assertEqual(received_data, data)
            self.assertEqual(from_addr, server_address)

    def test_recvfrom(self):
        mit test_utils.run_udp_echo_server() als server_address:
            self.loop.run_until_complete(
                self._basetest_datagram_recvfrom(server_address))

    async def _basetest_datagram_recvfrom_into(self, server_address):
        # Happy path, sock.sendto() returns immediately
        mit socket.socket(socket.AF_INET, socket.SOCK_DGRAM) als sock:
            sock.setblocking(Falsch)

            buf = bytearray(4096)
            data = b'\x01' * 4096
            await self.loop.sock_sendto(sock, data, server_address)
            num_bytes, from_addr = await self.loop.sock_recvfrom_into(
                sock, buf)
            self.assertEqual(num_bytes, 4096)
            self.assertEqual(buf, data)
            self.assertEqual(from_addr, server_address)

            buf = bytearray(8192)
            await self.loop.sock_sendto(sock, data, server_address)
            num_bytes, from_addr = await self.loop.sock_recvfrom_into(
                sock, buf, 4096)
            self.assertEqual(num_bytes, 4096)
            self.assertEqual(buf[:4096], data[:4096])
            self.assertEqual(from_addr, server_address)

    def test_recvfrom_into(self):
        mit test_utils.run_udp_echo_server() als server_address:
            self.loop.run_until_complete(
                self._basetest_datagram_recvfrom_into(server_address))

    async def _basetest_datagram_sendto_blocking(self, server_address):
        # Sad path, sock.sendto() raises BlockingIOError
        # This involves patching sock.sendto() to raise BlockingIOError but
        # sendto() is nicht used by the proactor event loop
        data = b'\x01' * 4096
        mit socket.socket(socket.AF_INET, socket.SOCK_DGRAM) als sock:
            sock.setblocking(Falsch)
            mock_sock = Mock(sock)
            mock_sock.gettimeout = sock.gettimeout
            mock_sock.sendto.configure_mock(side_effect=BlockingIOError)
            mock_sock.fileno = sock.fileno
            self.loop.call_soon(
                lambda: setattr(mock_sock, 'sendto', sock.sendto)
            )
            await self.loop.sock_sendto(mock_sock, data, server_address)

            received_data, from_addr = await self.loop.sock_recvfrom(
                sock, 4096)
            self.assertEqual(received_data, data)
            self.assertEqual(from_addr, server_address)

    def test_sendto_blocking(self):
        wenn sys.platform == 'win32':
            wenn isinstance(self.loop, asyncio.ProactorEventLoop):
                raise unittest.SkipTest('Not relevant to ProactorEventLoop')

        mit test_utils.run_udp_echo_server() als server_address:
            self.loop.run_until_complete(
                self._basetest_datagram_sendto_blocking(server_address))

    @socket_helper.skip_unless_bind_unix_socket
    def test_unix_sock_client_ops(self):
        mit test_utils.run_test_unix_server() als httpd:
            sock = socket.socket(socket.AF_UNIX)
            self._basetest_sock_client_ops(httpd, sock)
            sock = socket.socket(socket.AF_UNIX)
            self._basetest_sock_recv_into(httpd, sock)

    def test_sock_client_fail(self):
        # Make sure that we will get an unused port
        address = Nichts
        try:
            s = socket.socket()
            s.bind(('127.0.0.1', 0))
            address = s.getsockname()
        finally:
            s.close()

        sock = socket.socket()
        sock.setblocking(Falsch)
        mit self.assertRaises(ConnectionRefusedError):
            self.loop.run_until_complete(
                self.loop.sock_connect(sock, address))
        sock.close()

    def test_sock_accept(self):
        listener = socket.socket()
        listener.setblocking(Falsch)
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        client = socket.socket()
        client.connect(listener.getsockname())

        f = self.loop.sock_accept(listener)
        conn, addr = self.loop.run_until_complete(f)
        self.assertEqual(conn.gettimeout(), 0)
        self.assertEqual(addr, client.getsockname())
        self.assertEqual(client.getpeername(), listener.getsockname())
        client.close()
        conn.close()
        listener.close()

    def test_cancel_sock_accept(self):
        listener = socket.socket()
        listener.setblocking(Falsch)
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        sockaddr = listener.getsockname()
        f = asyncio.wait_for(self.loop.sock_accept(listener), 0.1)
        mit self.assertRaises(asyncio.TimeoutError):
            self.loop.run_until_complete(f)

        listener.close()
        client = socket.socket()
        client.setblocking(Falsch)
        f = self.loop.sock_connect(client, sockaddr)
        mit self.assertRaises(ConnectionRefusedError):
            self.loop.run_until_complete(f)

        client.close()

    def test_create_connection_sock(self):
        mit test_utils.run_test_server() als httpd:
            sock = Nichts
            infos = self.loop.run_until_complete(
                self.loop.getaddrinfo(
                    *httpd.address, type=socket.SOCK_STREAM))
            fuer family, type, proto, cname, address in infos:
                try:
                    sock = socket.socket(family=family, type=type, proto=proto)
                    sock.setblocking(Falsch)
                    self.loop.run_until_complete(
                        self.loop.sock_connect(sock, address))
                except BaseException:
                    pass
                sonst:
                    breche
            sonst:
                self.fail('Can nicht create socket.')

            f = self.loop.create_connection(
                lambda: MyProto(loop=self.loop), sock=sock)
            tr, pr = self.loop.run_until_complete(f)
            self.assertIsInstance(tr, asyncio.Transport)
            self.assertIsInstance(pr, asyncio.Protocol)
            self.loop.run_until_complete(pr.done)
            self.assertGreater(pr.nbytes, 0)
            tr.close()


wenn sys.platform == 'win32':

    klasse SelectEventLoopTests(BaseSockTestsMixin,
                               test_utils.TestCase):

        def create_event_loop(self):
            return asyncio.SelectorEventLoop()


    klasse ProactorEventLoopTests(BaseSockTestsMixin,
                                 test_utils.TestCase):

        def create_event_loop(self):
            return asyncio.ProactorEventLoop()


        async def _basetest_datagram_send_to_non_listening_address(self,
                                                                   recvfrom):
            # see:
            #   https://github.com/python/cpython/issues/91227
            #   https://github.com/python/cpython/issues/88906
            #   https://bugs.python.org/issue47071
            #   https://bugs.python.org/issue44743
            # The Proactor event loop would fail to receive datagram messages
            # after sending a message to an address that wasn't listening.

            def create_socket():
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(Falsch)
                sock.bind(('127.0.0.1', 0))
                return sock

            socket_1 = create_socket()
            addr_1 = socket_1.getsockname()

            socket_2 = create_socket()
            addr_2 = socket_2.getsockname()

            # creating und immediately closing this to try to get an address
            # that is nicht listening
            socket_3 = create_socket()
            addr_3 = socket_3.getsockname()
            socket_3.shutdown(socket.SHUT_RDWR)
            socket_3.close()

            socket_1_recv_task = self.loop.create_task(recvfrom(socket_1))
            socket_2_recv_task = self.loop.create_task(recvfrom(socket_2))
            await asyncio.sleep(0)

            await self.loop.sock_sendto(socket_1, b'a', addr_2)
            self.assertEqual(await socket_2_recv_task, b'a')

            await self.loop.sock_sendto(socket_2, b'b', addr_1)
            self.assertEqual(await socket_1_recv_task, b'b')
            socket_1_recv_task = self.loop.create_task(recvfrom(socket_1))
            await asyncio.sleep(0)

            # this should send to an address that isn't listening
            await self.loop.sock_sendto(socket_1, b'c', addr_3)
            self.assertEqual(await socket_1_recv_task, b'')
            socket_1_recv_task = self.loop.create_task(recvfrom(socket_1))
            await asyncio.sleep(0)

            # socket 1 should still be able to receive messages after sending
            # to an address that wasn't listening
            socket_2.sendto(b'd', addr_1)
            self.assertEqual(await socket_1_recv_task, b'd')

            socket_1.shutdown(socket.SHUT_RDWR)
            socket_1.close()
            socket_2.shutdown(socket.SHUT_RDWR)
            socket_2.close()


        def test_datagram_send_to_non_listening_address_recvfrom(self):
            async def recvfrom(socket):
                data, _ = await self.loop.sock_recvfrom(socket, 4096)
                return data

            self.loop.run_until_complete(
                self._basetest_datagram_send_to_non_listening_address(
                    recvfrom))


        def test_datagram_send_to_non_listening_address_recvfrom_into(self):
            async def recvfrom_into(socket):
                buf = bytearray(4096)
                length, _ = await self.loop.sock_recvfrom_into(socket, buf,
                                                               4096)
                return buf[:length]

            self.loop.run_until_complete(
                self._basetest_datagram_send_to_non_listening_address(
                    recvfrom_into))

sonst:
    importiere selectors

    wenn hasattr(selectors, 'KqueueSelector'):
        klasse KqueueEventLoopTests(BaseSockTestsMixin,
                                   test_utils.TestCase):

            def create_event_loop(self):
                return asyncio.SelectorEventLoop(
                    selectors.KqueueSelector())

    wenn hasattr(selectors, 'EpollSelector'):
        klasse EPollEventLoopTests(BaseSockTestsMixin,
                                  test_utils.TestCase):

            def create_event_loop(self):
                return asyncio.SelectorEventLoop(selectors.EpollSelector())

    wenn hasattr(selectors, 'PollSelector'):
        klasse PollEventLoopTests(BaseSockTestsMixin,
                                 test_utils.TestCase):

            def create_event_loop(self):
                return asyncio.SelectorEventLoop(selectors.PollSelector())

    # Should always exist.
    klasse SelectEventLoopTests(BaseSockTestsMixin,
                               test_utils.TestCase):

        def create_event_loop(self):
            return asyncio.SelectorEventLoop(selectors.SelectSelector())


wenn __name__ == '__main__':
    unittest.main()
