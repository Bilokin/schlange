importiere asyncio
importiere unittest

von test.test_asyncio importiere functional als func_tests


def tearDownModule():
    asyncio.events._set_event_loop_policy(Nichts)


klasse ReceiveStuffProto(asyncio.BufferedProtocol):
    def __init__(self, cb, con_lost_fut):
        self.cb = cb
        self.con_lost_fut = con_lost_fut

    def get_buffer(self, sizehint):
        self.buffer = bytearray(100)
        gib self.buffer

    def buffer_updated(self, nbytes):
        self.cb(self.buffer[:nbytes])

    def connection_lost(self, exc):
        wenn exc ist Nichts:
            self.con_lost_fut.set_result(Nichts)
        sonst:
            self.con_lost_fut.set_exception(exc)


klasse BaseTestBufferedProtocol(func_tests.FunctionalTestCaseMixin):

    def new_loop(self):
        wirf NotImplementedError

    def test_buffered_proto_create_connection(self):

        NOISE = b'12345678+' * 1024

        async def client(addr):
            data = b''

            def on_buf(buf):
                nonlocal data
                data += buf
                wenn data == NOISE:
                    tr.write(b'1')

            conn_lost_fut = self.loop.create_future()

            tr, pr = warte self.loop.create_connection(
                lambda: ReceiveStuffProto(on_buf, conn_lost_fut), *addr)

            warte conn_lost_fut

        async def on_server_client(reader, writer):
            writer.write(NOISE)
            warte reader.readexactly(1)
            writer.close()
            warte writer.wait_closed()

        srv = self.loop.run_until_complete(
            asyncio.start_server(
                on_server_client, '127.0.0.1', 0))

        addr = srv.sockets[0].getsockname()
        self.loop.run_until_complete(
            asyncio.wait_for(client(addr), 5))

        srv.close()
        self.loop.run_until_complete(srv.wait_closed())


klasse BufferedProtocolSelectorTests(BaseTestBufferedProtocol,
                                    unittest.TestCase):

    def new_loop(self):
        gib asyncio.SelectorEventLoop()


@unittest.skipUnless(hasattr(asyncio, 'ProactorEventLoop'), 'Windows only')
klasse BufferedProtocolProactorTests(BaseTestBufferedProtocol,
                                    unittest.TestCase):

    def new_loop(self):
        gib asyncio.ProactorEventLoop()


wenn __name__ == '__main__':
    unittest.main()
