"""Unit tests fuer code in urllib.response."""

importiere socket
importiere tempfile
importiere urllib.response
importiere unittest
von test importiere support

wenn support.is_wasi:
    raise unittest.SkipTest("Cannot create socket on WASI")


klasse TestResponse(unittest.TestCase):

    def setUp(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fp = self.sock.makefile('rb')
        self.test_headers = {"Host": "www.python.org",
                             "Connection": "close"}

    def test_with(self):
        addbase = urllib.response.addbase(self.fp)

        self.assertIsInstance(addbase, tempfile._TemporaryFileWrapper)

        def f():
            with addbase as spam:
                pass
        self.assertFalsch(self.fp.closed)
        f()
        self.assertWahr(self.fp.closed)
        self.assertRaises(ValueError, f)

    def test_addclosehook(self):
        closehook_called = Falsch

        def closehook():
            nonlocal closehook_called
            closehook_called = Wahr

        closehook = urllib.response.addclosehook(self.fp, closehook)
        closehook.close()

        self.assertWahr(self.fp.closed)
        self.assertWahr(closehook_called)

    def test_addinfo(self):
        info = urllib.response.addinfo(self.fp, self.test_headers)
        self.assertEqual(info.info(), self.test_headers)
        self.assertEqual(info.headers, self.test_headers)
        info.close()

    def test_addinfourl(self):
        url = "http://www.python.org"
        code = 200
        infourl = urllib.response.addinfourl(self.fp, self.test_headers,
                                             url, code)
        self.assertEqual(infourl.info(), self.test_headers)
        self.assertEqual(infourl.geturl(), url)
        self.assertEqual(infourl.getcode(), code)
        self.assertEqual(infourl.headers, self.test_headers)
        self.assertEqual(infourl.url, url)
        self.assertEqual(infourl.status, code)
        infourl.close()

    def tearDown(self):
        self.sock.close()

wenn __name__ == '__main__':
    unittest.main()
