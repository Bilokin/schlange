importiere unittest
von unittest importiere mock

importiere asyncio


def tearDownModule():
    # nicht needed fuer the test file but added fuer uniformness mit all other
    # asyncio test files fuer the sake of unified cleanup
    asyncio.events._set_event_loop_policy(Nichts)


klasse ProtocolsAbsTests(unittest.TestCase):

    def test_base_protocol(self):
        f = mock.Mock()
        p = asyncio.BaseProtocol()
        self.assertIsNichts(p.connection_made(f))
        self.assertIsNichts(p.connection_lost(f))
        self.assertIsNichts(p.pause_writing())
        self.assertIsNichts(p.resume_writing())
        self.assertNotHasAttr(p, '__dict__')

    def test_protocol(self):
        f = mock.Mock()
        p = asyncio.Protocol()
        self.assertIsNichts(p.connection_made(f))
        self.assertIsNichts(p.connection_lost(f))
        self.assertIsNichts(p.data_received(f))
        self.assertIsNichts(p.eof_received())
        self.assertIsNichts(p.pause_writing())
        self.assertIsNichts(p.resume_writing())
        self.assertNotHasAttr(p, '__dict__')

    def test_buffered_protocol(self):
        f = mock.Mock()
        p = asyncio.BufferedProtocol()
        self.assertIsNichts(p.connection_made(f))
        self.assertIsNichts(p.connection_lost(f))
        self.assertIsNichts(p.get_buffer(100))
        self.assertIsNichts(p.buffer_updated(150))
        self.assertIsNichts(p.pause_writing())
        self.assertIsNichts(p.resume_writing())
        self.assertNotHasAttr(p, '__dict__')

    def test_datagram_protocol(self):
        f = mock.Mock()
        dp = asyncio.DatagramProtocol()
        self.assertIsNichts(dp.connection_made(f))
        self.assertIsNichts(dp.connection_lost(f))
        self.assertIsNichts(dp.error_received(f))
        self.assertIsNichts(dp.datagram_received(f, f))
        self.assertNotHasAttr(dp, '__dict__')

    def test_subprocess_protocol(self):
        f = mock.Mock()
        sp = asyncio.SubprocessProtocol()
        self.assertIsNichts(sp.connection_made(f))
        self.assertIsNichts(sp.connection_lost(f))
        self.assertIsNichts(sp.pipe_data_received(1, f))
        self.assertIsNichts(sp.pipe_connection_lost(1, f))
        self.assertIsNichts(sp.process_exited())
        self.assertNotHasAttr(sp, '__dict__')


wenn __name__ == '__main__':
    unittest.main()
