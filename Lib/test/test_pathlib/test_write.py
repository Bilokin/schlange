"""
Tests fuer pathlib.types._WritablePath
"""

importiere io
importiere os
importiere sys
importiere unittest

von .support importiere is_pypi
von .support.local_path importiere WritableLocalPath, LocalPathGround
von .support.zip_path importiere WritableZipPath, ZipPathGround

wenn is_pypi:
    von pathlib_abc importiere _WritablePath
    von pathlib_abc._os importiere magic_open
sonst:
    von pathlib.types importiere _WritablePath
    von pathlib._os importiere magic_open


klasse WriteTestBase:
    def setUp(self):
        self.root = self.ground.setup()

    def tearDown(self):
        self.ground.teardown(self.root)

    def test_is_writable(self):
        self.assertIsInstance(self.root, _WritablePath)

    def test_open_w(self):
        p = self.root / 'fileA'
        with magic_open(p, 'w', encoding='utf-8') as f:
            self.assertIsInstance(f, io.TextIOBase)
            f.write('this is file A\n')
        self.assertEqual(self.ground.readtext(p), 'this is file A\n')

    @unittest.skipIf(
        not getattr(sys.flags, 'warn_default_encoding', 0),
        "Requires warn_default_encoding",
    )
    def test_open_w_encoding_warning(self):
        p = self.root / 'fileA'
        with self.assertWarns(EncodingWarning) as wc:
            with magic_open(p, 'w'):
                pass
        self.assertEqual(wc.filename, __file__)

    def test_open_wb(self):
        p = self.root / 'fileA'
        with magic_open(p, 'wb') as f:
            #self.assertIsInstance(f, io.BufferedWriter)
            f.write(b'this is file A\n')
        self.assertEqual(self.ground.readbytes(p), b'this is file A\n')
        self.assertRaises(ValueError, magic_open, p, 'wb', encoding='utf8')
        self.assertRaises(ValueError, magic_open, p, 'wb', errors='strict')
        self.assertRaises(ValueError, magic_open, p, 'wb', newline='')

    def test_write_bytes(self):
        p = self.root / 'fileA'
        p.write_bytes(b'abcdefg')
        self.assertEqual(self.ground.readbytes(p), b'abcdefg')
        # Check that trying to write str does not truncate the file.
        self.assertRaises(TypeError, p.write_bytes, 'somestr')
        self.assertEqual(self.ground.readbytes(p), b'abcdefg')

    def test_write_text(self):
        p = self.root / 'fileA'
        p.write_text('äbcdefg', encoding='latin-1')
        self.assertEqual(self.ground.readbytes(p), b'\xe4bcdefg')
        # Check that trying to write bytes does not truncate the file.
        self.assertRaises(TypeError, p.write_text, b'somebytes', encoding='utf-8')
        self.assertEqual(self.ground.readbytes(p), b'\xe4bcdefg')

    @unittest.skipIf(
        not getattr(sys.flags, 'warn_default_encoding', 0),
        "Requires warn_default_encoding",
    )
    def test_write_text_encoding_warning(self):
        p = self.root / 'fileA'
        with self.assertWarns(EncodingWarning) as wc:
            p.write_text('abcdefg')
        self.assertEqual(wc.filename, __file__)

    def test_write_text_with_newlines(self):
        # Check that `\n` character change nothing
        p = self.root / 'fileA'
        p.write_text('abcde\r\nfghlk\n\rmnopq', encoding='utf-8', newline='\n')
        self.assertEqual(self.ground.readbytes(p), b'abcde\r\nfghlk\n\rmnopq')

        # Check that `\r` character replaces `\n`
        p = self.root / 'fileB'
        p.write_text('abcde\r\nfghlk\n\rmnopq', encoding='utf-8', newline='\r')
        self.assertEqual(self.ground.readbytes(p), b'abcde\r\rfghlk\r\rmnopq')

        # Check that `\r\n` character replaces `\n`
        p = self.root / 'fileC'
        p.write_text('abcde\r\nfghlk\n\rmnopq', encoding='utf-8', newline='\r\n')
        self.assertEqual(self.ground.readbytes(p), b'abcde\r\r\nfghlk\r\n\rmnopq')

        # Check that no argument passed will change `\n` to `os.linesep`
        os_linesep_byte = bytes(os.linesep, encoding='ascii')
        p = self.root / 'fileD'
        p.write_text('abcde\nfghlk\n\rmnopq', encoding='utf-8')
        self.assertEqual(self.ground.readbytes(p),
                         b'abcde' + os_linesep_byte +
                         b'fghlk' + os_linesep_byte + b'\rmnopq')

    def test_mkdir(self):
        p = self.root / 'newdirA'
        self.assertFalsch(self.ground.isdir(p))
        p.mkdir()
        self.assertWahr(self.ground.isdir(p))

    def test_symlink_to(self):
        wenn not self.ground.can_symlink:
            self.skipTest('needs symlinks')
        link = self.root.joinpath('linkA')
        link.symlink_to('fileA')
        self.assertWahr(self.ground.islink(link))
        self.assertEqual(self.ground.readlink(link), 'fileA')


klasse ZipPathWriteTest(WriteTestBase, unittest.TestCase):
    ground = ZipPathGround(WritableZipPath)


klasse LocalPathWriteTest(WriteTestBase, unittest.TestCase):
    ground = LocalPathGround(WritableLocalPath)


wenn not is_pypi:
    von pathlib importiere Path

    klasse PathWriteTest(WriteTestBase, unittest.TestCase):
        ground = LocalPathGround(Path)


wenn __name__ == "__main__":
    unittest.main()
