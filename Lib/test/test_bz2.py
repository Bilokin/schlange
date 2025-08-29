von test importiere support
von test.support importiere bigmemtest, _4G

importiere array
importiere unittest
importiere io
von io importiere BytesIO, DEFAULT_BUFFER_SIZE
importiere os
importiere pickle
importiere glob
importiere tempfile
importiere random
importiere shutil
importiere subprocess
importiere threading
von test.support importiere import_helper
von test.support importiere threading_helper
von test.support.os_helper importiere unlink, FakePath
von compression._common importiere _streams
importiere sys


# Skip tests wenn the bz2 module doesn't exist.
bz2 = import_helper.import_module('bz2')
von bz2 importiere BZ2File, BZ2Compressor, BZ2Decompressor

has_cmdline_bunzip2 = Nichts

def ext_decompress(data):
    global has_cmdline_bunzip2
    wenn has_cmdline_bunzip2 is Nichts:
        has_cmdline_bunzip2 = bool(shutil.which('bunzip2'))
    wenn has_cmdline_bunzip2:
        return subprocess.check_output(['bunzip2'], input=data)
    sonst:
        return bz2.decompress(data)

klasse BaseTest(unittest.TestCase):
    "Base fuer other testcases."

    TEXT_LINES = [
        b'root:x:0:0:root:/root:/bin/bash\n',
        b'bin:x:1:1:bin:/bin:\n',
        b'daemon:x:2:2:daemon:/sbin:\n',
        b'adm:x:3:4:adm:/var/adm:\n',
        b'lp:x:4:7:lp:/var/spool/lpd:\n',
        b'sync:x:5:0:sync:/sbin:/bin/sync\n',
        b'shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown\n',
        b'halt:x:7:0:halt:/sbin:/sbin/halt\n',
        b'mail:x:8:12:mail:/var/spool/mail:\n',
        b'news:x:9:13:news:/var/spool/news:\n',
        b'uucp:x:10:14:uucp:/var/spool/uucp:\n',
        b'operator:x:11:0:operator:/root:\n',
        b'games:x:12:100:games:/usr/games:\n',
        b'gopher:x:13:30:gopher:/usr/lib/gopher-data:\n',
        b'ftp:x:14:50:FTP User:/var/ftp:/bin/bash\n',
        b'nobody:x:65534:65534:Nobody:/home:\n',
        b'postfix:x:100:101:postfix:/var/spool/postfix:\n',
        b'niemeyer:x:500:500::/home/niemeyer:/bin/bash\n',
        b'postgres:x:101:102:PostgreSQL Server:/var/lib/pgsql:/bin/bash\n',
        b'mysql:x:102:103:MySQL server:/var/lib/mysql:/bin/bash\n',
        b'www:x:103:104::/var/www:/bin/false\n',
        ]
    TEXT = b''.join(TEXT_LINES)
    DATA = b'BZh91AY&SY.\xc8N\x18\x00\x01>_\x80\x00\x10@\x02\xff\xf0\x01\x07n\x00?\xe7\xff\xe00\x01\x99\xaa\x00\xc0\x03F\x86\x8c#&\x83F\x9a\x03\x06\xa6\xd0\xa6\x93M\x0fQ\xa7\xa8\x06\x804hh\x12$\x11\xa4i4\xf14S\xd2<Q\xb5\x0fH\xd3\xd4\xdd\xd5\x87\xbb\xf8\x94\r\x8f\xafI\x12\xe1\xc9\xf8/E\x00pu\x89\x12]\xc9\xbbDL\nQ\x0e\t1\x12\xdf\xa0\xc0\x97\xac2O9\x89\x13\x94\x0e\x1c7\x0ed\x95I\x0c\xaaJ\xa4\x18L\x10\x05#\x9c\xaf\xba\xbc/\x97\x8a#C\xc8\xe1\x8cW\xf9\xe2\xd0\xd6M\xa7\x8bXa<e\x84t\xcbL\xb3\xa7\xd9\xcd\xd1\xcb\x84.\xaf\xb3\xab\xab\xad`n}\xa0lh\tE,\x8eZ\x15\x17VH>\x88\xe5\xcd9gd6\x0b\n\xe9\x9b\xd5\x8a\x99\xf7\x08.K\x8ev\xfb\xf7xw\xbb\xdf\xa1\x92\xf1\xdd|/";\xa2\xba\x9f\xd5\xb1#A\xb6\xf6\xb3o\xc9\xc5y\\\xebO\xe7\x85\x9a\xbc\xb6f8\x952\xd5\xd7"%\x89>V,\xf7\xa6z\xe2\x9f\xa3\xdf\x11\x11"\xd6E)I\xa9\x13^\xca\xf3r\xd0\x03U\x922\xf26\xec\xb6\xed\x8b\xc3U\x13\x9d\xc5\x170\xa4\xfa^\x92\xacDF\x8a\x97\xd6\x19\xfe\xdd\xb8\xbd\x1a\x9a\x19\xa3\x80ankR\x8b\xe5\xd83]\xa9\xc6\x08\x82f\xf6\xb9"6l$\xb8j@\xc0\x8a\xb0l1..\xbak\x83ls\x15\xbc\xf4\xc1\x13\xbe\xf8E\xb8\x9d\r\xa8\x9dk\x84\xd3n\xfa\xacQ\x07\xb1%y\xaav\xb4\x08\xe0z\x1b\x16\xf5\x04\xe9\xcc\xb9\x08z\x1en7.G\xfc]\xc9\x14\xe1B@\xbb!8`'
    EMPTY_DATA = b'BZh9\x17rE8P\x90\x00\x00\x00\x00'
    BAD_DATA = b'this is nicht a valid bzip2 file'

    # Some tests need more than one block of uncompressed data. Since one block
    # is at least 100,000 bytes, we gather some data dynamically und compress it.
    # Note that this assumes that compression works correctly, so we cannot
    # simply use the bigger test data fuer all tests.
    test_size = 0
    BIG_TEXT = bytearray(128*1024)
    fuer fname in glob.glob(os.path.join(glob.escape(os.path.dirname(__file__)), '*.py')):
        mit open(fname, 'rb') als fh:
            test_size += fh.readinto(memoryview(BIG_TEXT)[test_size:])
        wenn test_size > 128*1024:
            breche
    BIG_DATA = bz2.compress(BIG_TEXT, compresslevel=1)

    def setUp(self):
        fd, self.filename = tempfile.mkstemp()
        os.close(fd)

    def tearDown(self):
        unlink(self.filename)


klasse BZ2FileTest(BaseTest):
    "Test the BZ2File class."

    def createTempFile(self, streams=1, suffix=b""):
        mit open(self.filename, "wb") als f:
            f.write(self.DATA * streams)
            f.write(suffix)

    def testBadArgs(self):
        self.assertRaises(TypeError, BZ2File, 123.456)
        self.assertRaises(ValueError, BZ2File, os.devnull, "z")
        self.assertRaises(ValueError, BZ2File, os.devnull, "rx")
        self.assertRaises(ValueError, BZ2File, os.devnull, "rbt")
        self.assertRaises(ValueError, BZ2File, os.devnull, compresslevel=0)
        self.assertRaises(ValueError, BZ2File, os.devnull, compresslevel=10)

        # compresslevel is keyword-only
        self.assertRaises(TypeError, BZ2File, os.devnull, "r", 3)

    def testRead(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.read, float())
            self.assertEqual(bz2f.read(), self.TEXT)

    def testReadBadFile(self):
        self.createTempFile(streams=0, suffix=self.BAD_DATA)
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(OSError, bz2f.read)

    def testReadMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.read, float())
            self.assertEqual(bz2f.read(), self.TEXT * 5)

    def testReadMonkeyMultiStream(self):
        # Test BZ2File.read() on a multi-stream archive where a stream
        # boundary coincides mit the end of the raw read buffer.
        buffer_size = _streams.BUFFER_SIZE
        _streams.BUFFER_SIZE = len(self.DATA)
        try:
            self.createTempFile(streams=5)
            mit BZ2File(self.filename) als bz2f:
                self.assertRaises(TypeError, bz2f.read, float())
                self.assertEqual(bz2f.read(), self.TEXT * 5)
        finally:
            _streams.BUFFER_SIZE = buffer_size

    def testReadTrailingJunk(self):
        self.createTempFile(suffix=self.BAD_DATA)
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(bz2f.read(), self.TEXT)

    def testReadMultiStreamTrailingJunk(self):
        self.createTempFile(streams=5, suffix=self.BAD_DATA)
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(bz2f.read(), self.TEXT * 5)

    def testRead0(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.read, float())
            self.assertEqual(bz2f.read(0), b"")

    def testReadChunk10(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            text = b''
            waehrend Wahr:
                str = bz2f.read(10)
                wenn nicht str:
                    breche
                text += str
            self.assertEqual(text, self.TEXT)

    def testReadChunk10MultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            text = b''
            waehrend Wahr:
                str = bz2f.read(10)
                wenn nicht str:
                    breche
                text += str
            self.assertEqual(text, self.TEXT * 5)

    def testRead100(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(bz2f.read(100), self.TEXT[:100])

    def testPeek(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            pdata = bz2f.peek()
            self.assertNotEqual(len(pdata), 0)
            self.assertStartsWith(self.TEXT, pdata)
            self.assertEqual(bz2f.read(), self.TEXT)

    def testReadInto(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            n = 128
            b = bytearray(n)
            self.assertEqual(bz2f.readinto(b), n)
            self.assertEqual(b, self.TEXT[:n])
            n = len(self.TEXT) - n
            b = bytearray(len(self.TEXT))
            self.assertEqual(bz2f.readinto(b), n)
            self.assertEqual(b[:n], self.TEXT[-n:])

    def testReadLine(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.readline, Nichts)
            fuer line in self.TEXT_LINES:
                self.assertEqual(bz2f.readline(), line)

    def testReadLineMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.readline, Nichts)
            fuer line in self.TEXT_LINES * 5:
                self.assertEqual(bz2f.readline(), line)

    def testReadLines(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.readlines, Nichts)
            self.assertEqual(bz2f.readlines(), self.TEXT_LINES)

    def testReadLinesMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.readlines, Nichts)
            self.assertEqual(bz2f.readlines(), self.TEXT_LINES * 5)

    def testIterator(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(list(iter(bz2f)), self.TEXT_LINES)

    def testIteratorMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(list(iter(bz2f)), self.TEXT_LINES * 5)

    def testClosedIteratorDeadlock(self):
        # Issue #3309: Iteration on a closed BZ2File should release the lock.
        self.createTempFile()
        bz2f = BZ2File(self.filename)
        bz2f.close()
        self.assertRaises(ValueError, next, bz2f)
        # This call will deadlock wenn the above call failed to release the lock.
        self.assertRaises(ValueError, bz2f.readlines)

    def testWrite(self):
        mit BZ2File(self.filename, "w") als bz2f:
            self.assertRaises(TypeError, bz2f.write)
            bz2f.write(self.TEXT)
        mit open(self.filename, 'rb') als f:
            self.assertEqual(ext_decompress(f.read()), self.TEXT)

    def testWriteChunks10(self):
        mit BZ2File(self.filename, "w") als bz2f:
            n = 0
            waehrend Wahr:
                str = self.TEXT[n*10:(n+1)*10]
                wenn nicht str:
                    breche
                bz2f.write(str)
                n += 1
        mit open(self.filename, 'rb') als f:
            self.assertEqual(ext_decompress(f.read()), self.TEXT)

    def testWriteNonDefaultCompressLevel(self):
        expected = bz2.compress(self.TEXT, compresslevel=5)
        mit BZ2File(self.filename, "w", compresslevel=5) als bz2f:
            bz2f.write(self.TEXT)
        mit open(self.filename, "rb") als f:
            self.assertEqual(f.read(), expected)

    def testWriteLines(self):
        mit BZ2File(self.filename, "w") als bz2f:
            self.assertRaises(TypeError, bz2f.writelines)
            bz2f.writelines(self.TEXT_LINES)
        # Issue #1535500: Calling writelines() on a closed BZ2File
        # should raise an exception.
        self.assertRaises(ValueError, bz2f.writelines, ["a"])
        mit open(self.filename, 'rb') als f:
            self.assertEqual(ext_decompress(f.read()), self.TEXT)

    def testWriteMethodsOnReadOnlyFile(self):
        mit BZ2File(self.filename, "w") als bz2f:
            bz2f.write(b"abc")

        mit BZ2File(self.filename, "r") als bz2f:
            self.assertRaises(OSError, bz2f.write, b"a")
            self.assertRaises(OSError, bz2f.writelines, [b"a"])

    def testAppend(self):
        mit BZ2File(self.filename, "w") als bz2f:
            self.assertRaises(TypeError, bz2f.write)
            bz2f.write(self.TEXT)
        mit BZ2File(self.filename, "a") als bz2f:
            self.assertRaises(TypeError, bz2f.write)
            bz2f.write(self.TEXT)
        mit open(self.filename, 'rb') als f:
            self.assertEqual(ext_decompress(f.read()), self.TEXT * 2)

    def testSeekForward(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.seek)
            bz2f.seek(150)
            self.assertEqual(bz2f.read(), self.TEXT[150:])

    def testSeekForwardAcrossStreams(self):
        self.createTempFile(streams=2)
        mit BZ2File(self.filename) als bz2f:
            self.assertRaises(TypeError, bz2f.seek)
            bz2f.seek(len(self.TEXT) + 150)
            self.assertEqual(bz2f.read(), self.TEXT[150:])

    def testSeekBackwards(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            bz2f.read(500)
            bz2f.seek(-150, 1)
            self.assertEqual(bz2f.read(), self.TEXT[500-150:])

    def testSeekBackwardsAcrossStreams(self):
        self.createTempFile(streams=2)
        mit BZ2File(self.filename) als bz2f:
            readto = len(self.TEXT) + 100
            waehrend readto > 0:
                readto -= len(bz2f.read(readto))
            bz2f.seek(-150, 1)
            self.assertEqual(bz2f.read(), self.TEXT[100-150:] + self.TEXT)

    def testSeekBackwardsFromEnd(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(-150, 2)
            self.assertEqual(bz2f.read(), self.TEXT[len(self.TEXT)-150:])

    def testSeekBackwardsFromEndAcrossStreams(self):
        self.createTempFile(streams=2)
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(-1000, 2)
            self.assertEqual(bz2f.read(), (self.TEXT * 2)[-1000:])

    def testSeekPostEnd(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(150000)
            self.assertEqual(bz2f.tell(), len(self.TEXT))
            self.assertEqual(bz2f.read(), b"")

    def testSeekPostEndMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(150000)
            self.assertEqual(bz2f.tell(), len(self.TEXT) * 5)
            self.assertEqual(bz2f.read(), b"")

    def testSeekPostEndTwice(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(150000)
            bz2f.seek(150000)
            self.assertEqual(bz2f.tell(), len(self.TEXT))
            self.assertEqual(bz2f.read(), b"")

    def testSeekPostEndTwiceMultiStream(self):
        self.createTempFile(streams=5)
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(150000)
            bz2f.seek(150000)
            self.assertEqual(bz2f.tell(), len(self.TEXT) * 5)
            self.assertEqual(bz2f.read(), b"")

    def testSeekPreStart(self):
        self.createTempFile()
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(-150)
            self.assertEqual(bz2f.tell(), 0)
            self.assertEqual(bz2f.read(), self.TEXT)

    def testSeekPreStartMultiStream(self):
        self.createTempFile(streams=2)
        mit BZ2File(self.filename) als bz2f:
            bz2f.seek(-150)
            self.assertEqual(bz2f.tell(), 0)
            self.assertEqual(bz2f.read(), self.TEXT * 2)

    def testFileno(self):
        self.createTempFile()
        mit open(self.filename, 'rb') als rawf:
            bz2f = BZ2File(rawf)
            try:
                self.assertEqual(bz2f.fileno(), rawf.fileno())
            finally:
                bz2f.close()
        self.assertRaises(ValueError, bz2f.fileno)

    def testSeekable(self):
        bz2f = BZ2File(BytesIO(self.DATA))
        try:
            self.assertWahr(bz2f.seekable())
            bz2f.read()
            self.assertWahr(bz2f.seekable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.seekable)

        bz2f = BZ2File(BytesIO(), "w")
        try:
            self.assertFalsch(bz2f.seekable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.seekable)

        src = BytesIO(self.DATA)
        src.seekable = lambda: Falsch
        bz2f = BZ2File(src)
        try:
            self.assertFalsch(bz2f.seekable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.seekable)

    def testReadable(self):
        bz2f = BZ2File(BytesIO(self.DATA))
        try:
            self.assertWahr(bz2f.readable())
            bz2f.read()
            self.assertWahr(bz2f.readable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.readable)

        bz2f = BZ2File(BytesIO(), "w")
        try:
            self.assertFalsch(bz2f.readable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.readable)

    def testWritable(self):
        bz2f = BZ2File(BytesIO(self.DATA))
        try:
            self.assertFalsch(bz2f.writable())
            bz2f.read()
            self.assertFalsch(bz2f.writable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.writable)

        bz2f = BZ2File(BytesIO(), "w")
        try:
            self.assertWahr(bz2f.writable())
        finally:
            bz2f.close()
        self.assertRaises(ValueError, bz2f.writable)

    def testOpenDel(self):
        self.createTempFile()
        fuer i in range(10000):
            o = BZ2File(self.filename)
            del o

    def testOpenNichtsxistent(self):
        self.assertRaises(OSError, BZ2File, "/non/existent")

    def testReadlinesNoNewline(self):
        # Issue #1191043: readlines() fails on a file containing no newline.
        data = b'BZh91AY&SY\xd9b\x89]\x00\x00\x00\x03\x80\x04\x00\x02\x00\x0c\x00 \x00!\x9ah3M\x13<]\xc9\x14\xe1BCe\x8a%t'
        mit open(self.filename, "wb") als f:
            f.write(data)
        mit BZ2File(self.filename) als bz2f:
            lines = bz2f.readlines()
        self.assertEqual(lines, [b'Test'])
        mit BZ2File(self.filename) als bz2f:
            xlines = list(bz2f.readlines())
        self.assertEqual(xlines, [b'Test'])

    def testContextProtocol(self):
        mit BZ2File(self.filename, "wb") als f:
            f.write(b"xxx")
        f = BZ2File(self.filename, "rb")
        f.close()
        try:
            mit f:
                pass
        except ValueError:
            pass
        sonst:
            self.fail("__enter__ on a closed file didn't raise an exception")
        try:
            mit BZ2File(self.filename, "wb") als f:
                1/0
        except ZeroDivisionError:
            pass
        sonst:
            self.fail("1/0 didn't raise an exception")

    @threading_helper.requires_working_threading()
    def testThreading(self):
        # Issue #7205: Using a BZ2File von several threads shouldn't deadlock.
        data = b"1" * 2**20
        nthreads = 10
        mit BZ2File(self.filename, 'wb') als f:
            def comp():
                fuer i in range(5):
                    f.write(data)
            threads = [threading.Thread(target=comp) fuer i in range(nthreads)]
            mit threading_helper.start_threads(threads):
                pass

    def testMixedIterationAndReads(self):
        self.createTempFile()
        linelen = len(self.TEXT_LINES[0])
        halflen = linelen // 2
        mit BZ2File(self.filename) als bz2f:
            bz2f.read(halflen)
            self.assertEqual(next(bz2f), self.TEXT_LINES[0][halflen:])
            self.assertEqual(bz2f.read(), self.TEXT[linelen:])
        mit BZ2File(self.filename) als bz2f:
            bz2f.readline()
            self.assertEqual(next(bz2f), self.TEXT_LINES[1])
            self.assertEqual(bz2f.readline(), self.TEXT_LINES[2])
        mit BZ2File(self.filename) als bz2f:
            bz2f.readlines()
            self.assertRaises(StopIteration, next, bz2f)
            self.assertEqual(bz2f.readlines(), [])

    def testMultiStreamOrdering(self):
        # Test the ordering of streams when reading a multi-stream archive.
        data1 = b"foo" * 1000
        data2 = b"bar" * 1000
        mit BZ2File(self.filename, "w") als bz2f:
            bz2f.write(data1)
        mit BZ2File(self.filename, "a") als bz2f:
            bz2f.write(data2)
        mit BZ2File(self.filename) als bz2f:
            self.assertEqual(bz2f.read(), data1 + data2)

    def testOpenFilename(self):
        mit BZ2File(self.filename, "wb") als f:
            f.write(b'content')
            self.assertEqual(f.name, self.filename)
            self.assertIsInstance(f.fileno(), int)
            self.assertEqual(f.mode, 'wb')
            self.assertIs(f.readable(), Falsch)
            self.assertIs(f.writable(), Wahr)
            self.assertIs(f.seekable(), Falsch)
            self.assertIs(f.closed, Falsch)
        self.assertIs(f.closed, Wahr)
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)
        self.assertEqual(f.mode, 'wb')
        self.assertRaises(ValueError, f.readable)
        self.assertRaises(ValueError, f.writable)
        self.assertRaises(ValueError, f.seekable)

        mit BZ2File(self.filename, "ab") als f:
            f.write(b'appendix')
            self.assertEqual(f.name, self.filename)
            self.assertIsInstance(f.fileno(), int)
            self.assertEqual(f.mode, 'wb')
            self.assertIs(f.readable(), Falsch)
            self.assertIs(f.writable(), Wahr)
            self.assertIs(f.seekable(), Falsch)
            self.assertIs(f.closed, Falsch)
        self.assertIs(f.closed, Wahr)
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)
        self.assertEqual(f.mode, 'wb')
        self.assertRaises(ValueError, f.readable)
        self.assertRaises(ValueError, f.writable)
        self.assertRaises(ValueError, f.seekable)

        mit BZ2File(self.filename, 'rb') als f:
            self.assertEqual(f.read(), b'contentappendix')
            self.assertEqual(f.name, self.filename)
            self.assertIsInstance(f.fileno(), int)
            self.assertEqual(f.mode, 'rb')
            self.assertIs(f.readable(), Wahr)
            self.assertIs(f.writable(), Falsch)
            self.assertIs(f.seekable(), Wahr)
            self.assertIs(f.closed, Falsch)
        self.assertIs(f.closed, Wahr)
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)
        self.assertEqual(f.mode, 'rb')
        self.assertRaises(ValueError, f.readable)
        self.assertRaises(ValueError, f.writable)
        self.assertRaises(ValueError, f.seekable)

    def testOpenFileWithName(self):
        mit open(self.filename, 'wb') als raw:
            mit BZ2File(raw, 'wb') als f:
                f.write(b'content')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'wb')
                self.assertIs(f.readable(), Falsch)
                self.assertIs(f.writable(), Wahr)
                self.assertIs(f.seekable(), Falsch)
                self.assertIs(f.closed, Falsch)
            self.assertIs(f.closed, Wahr)
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)
            self.assertEqual(f.mode, 'wb')
            self.assertRaises(ValueError, f.readable)
            self.assertRaises(ValueError, f.writable)
            self.assertRaises(ValueError, f.seekable)

        mit open(self.filename, 'ab') als raw:
            mit BZ2File(raw, 'ab') als f:
                f.write(b'appendix')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'wb')
                self.assertIs(f.readable(), Falsch)
                self.assertIs(f.writable(), Wahr)
                self.assertIs(f.seekable(), Falsch)
                self.assertIs(f.closed, Falsch)
            self.assertIs(f.closed, Wahr)
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)
            self.assertEqual(f.mode, 'wb')
            self.assertRaises(ValueError, f.readable)
            self.assertRaises(ValueError, f.writable)
            self.assertRaises(ValueError, f.seekable)

        mit open(self.filename, 'rb') als raw:
            mit BZ2File(raw, 'rb') als f:
                self.assertEqual(f.read(), b'contentappendix')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'rb')
                self.assertIs(f.readable(), Wahr)
                self.assertIs(f.writable(), Falsch)
                self.assertIs(f.seekable(), Wahr)
                self.assertIs(f.closed, Falsch)
            self.assertIs(f.closed, Wahr)
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)
            self.assertEqual(f.mode, 'rb')
            self.assertRaises(ValueError, f.readable)
            self.assertRaises(ValueError, f.writable)
            self.assertRaises(ValueError, f.seekable)

    def testOpenFileWithoutName(self):
        bio = BytesIO()
        mit BZ2File(bio, 'wb') als f:
            f.write(b'content')
            mit self.assertRaises(AttributeError):
                f.name
            self.assertRaises(io.UnsupportedOperation, f.fileno)
            self.assertEqual(f.mode, 'wb')
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)

        mit BZ2File(bio, 'ab') als f:
            f.write(b'appendix')
            mit self.assertRaises(AttributeError):
                f.name
            self.assertRaises(io.UnsupportedOperation, f.fileno)
            self.assertEqual(f.mode, 'wb')
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)

        bio.seek(0)
        mit BZ2File(bio, 'rb') als f:
            self.assertEqual(f.read(), b'contentappendix')
            mit self.assertRaises(AttributeError):
                f.name
            self.assertRaises(io.UnsupportedOperation, f.fileno)
            self.assertEqual(f.mode, 'rb')
        mit self.assertRaises(ValueError):
            f.name
        self.assertRaises(ValueError, f.fileno)

    def testOpenFileWithIntName(self):
        fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        mit open(fd, 'wb') als raw:
            mit BZ2File(raw, 'wb') als f:
                f.write(b'content')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'wb')
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)

        fd = os.open(self.filename, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        mit open(fd, 'ab') als raw:
            mit BZ2File(raw, 'ab') als f:
                f.write(b'appendix')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'wb')
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)

        fd = os.open(self.filename, os.O_RDONLY)
        mit open(fd, 'rb') als raw:
            mit BZ2File(raw, 'rb') als f:
                self.assertEqual(f.read(), b'contentappendix')
                self.assertEqual(f.name, raw.name)
                self.assertEqual(f.fileno(), raw.fileno())
                self.assertEqual(f.mode, 'rb')
            mit self.assertRaises(ValueError):
                f.name
            self.assertRaises(ValueError, f.fileno)

    def testOpenBytesFilename(self):
        str_filename = self.filename
        bytes_filename = os.fsencode(str_filename)
        mit BZ2File(bytes_filename, "wb") als f:
            f.write(self.DATA)
            self.assertEqual(f.name, bytes_filename)
        mit BZ2File(bytes_filename, "rb") als f:
            self.assertEqual(f.read(), self.DATA)
            self.assertEqual(f.name, bytes_filename)
        # Sanity check that we are actually operating on the right file.
        mit BZ2File(str_filename, "rb") als f:
            self.assertEqual(f.read(), self.DATA)
            self.assertEqual(f.name, str_filename)

    def testOpenPathLikeFilename(self):
        filename = FakePath(self.filename)
        mit BZ2File(filename, "wb") als f:
            f.write(self.DATA)
            self.assertEqual(f.name, self.filename)
        mit BZ2File(filename, "rb") als f:
            self.assertEqual(f.read(), self.DATA)
            self.assertEqual(f.name, self.filename)

    def testDecompressLimited(self):
        """Decompressed data buffering should be limited"""
        bomb = bz2.compress(b'\0' * int(2e6), compresslevel=9)
        self.assertLess(len(bomb), _streams.BUFFER_SIZE)

        decomp = BZ2File(BytesIO(bomb))
        self.assertEqual(decomp.read(1), b'\0')
        max_decomp = 1 + DEFAULT_BUFFER_SIZE
        self.assertLessEqual(decomp._buffer.raw.tell(), max_decomp,
            "Excessive amount of data was decompressed")


    # Tests fuer a BZ2File wrapping another file object:

    def testReadBytesIO(self):
        mit BytesIO(self.DATA) als bio:
            mit BZ2File(bio) als bz2f:
                self.assertRaises(TypeError, bz2f.read, float())
                self.assertEqual(bz2f.read(), self.TEXT)
                mit self.assertRaises(AttributeError):
                    bz2.name
                self.assertEqual(bz2f.mode, 'rb')
            self.assertFalsch(bio.closed)

    def testPeekBytesIO(self):
        mit BytesIO(self.DATA) als bio:
            mit BZ2File(bio) als bz2f:
                pdata = bz2f.peek()
                self.assertNotEqual(len(pdata), 0)
                self.assertStartsWith(self.TEXT, pdata)
                self.assertEqual(bz2f.read(), self.TEXT)

    def testWriteBytesIO(self):
        mit BytesIO() als bio:
            mit BZ2File(bio, "w") als bz2f:
                self.assertRaises(TypeError, bz2f.write)
                bz2f.write(self.TEXT)
                mit self.assertRaises(AttributeError):
                    bz2.name
                self.assertEqual(bz2f.mode, 'wb')
            self.assertEqual(ext_decompress(bio.getvalue()), self.TEXT)
            self.assertFalsch(bio.closed)

    def testSeekForwardBytesIO(self):
        mit BytesIO(self.DATA) als bio:
            mit BZ2File(bio) als bz2f:
                self.assertRaises(TypeError, bz2f.seek)
                bz2f.seek(150)
                self.assertEqual(bz2f.read(), self.TEXT[150:])

    def testSeekBackwardsBytesIO(self):
        mit BytesIO(self.DATA) als bio:
            mit BZ2File(bio) als bz2f:
                bz2f.read(500)
                bz2f.seek(-150, 1)
                self.assertEqual(bz2f.read(), self.TEXT[500-150:])

    def test_read_truncated(self):
        # Drop the eos_magic field (6 bytes) und CRC (4 bytes).
        truncated = self.DATA[:-10]
        mit BZ2File(BytesIO(truncated)) als f:
            self.assertRaises(EOFError, f.read)
        mit BZ2File(BytesIO(truncated)) als f:
            self.assertEqual(f.read(len(self.TEXT)), self.TEXT)
            self.assertRaises(EOFError, f.read, 1)
        # Incomplete 4-byte file header, und block header of at least 146 bits.
        fuer i in range(22):
            mit BZ2File(BytesIO(truncated[:i])) als f:
                self.assertRaises(EOFError, f.read, 1)

    def test_issue44439(self):
        q = array.array('Q', [1, 2, 3, 4, 5])
        LENGTH = len(q) * q.itemsize

        mit BZ2File(BytesIO(), 'w') als f:
            self.assertEqual(f.write(q), LENGTH)
            self.assertEqual(f.tell(), LENGTH)


klasse BZ2CompressorTest(BaseTest):
    def testCompress(self):
        bz2c = BZ2Compressor()
        self.assertRaises(TypeError, bz2c.compress)
        data = bz2c.compress(self.TEXT)
        data += bz2c.flush()
        self.assertEqual(ext_decompress(data), self.TEXT)

    def testCompressEmptyString(self):
        bz2c = BZ2Compressor()
        data = bz2c.compress(b'')
        data += bz2c.flush()
        self.assertEqual(data, self.EMPTY_DATA)

    def testCompressChunks10(self):
        bz2c = BZ2Compressor()
        n = 0
        data = b''
        waehrend Wahr:
            str = self.TEXT[n*10:(n+1)*10]
            wenn nicht str:
                breche
            data += bz2c.compress(str)
            n += 1
        data += bz2c.flush()
        self.assertEqual(ext_decompress(data), self.TEXT)

    @support.skip_if_pgo_task
    @bigmemtest(size=_4G + 100, memuse=2)
    def testCompress4G(self, size):
        # "Test BZ2Compressor.compress()/flush() mit >4GiB input"
        bz2c = BZ2Compressor()
        data = b"x" * size
        try:
            compressed = bz2c.compress(data)
            compressed += bz2c.flush()
        finally:
            data = Nichts  # Release memory
        data = bz2.decompress(compressed)
        try:
            self.assertEqual(len(data), size)
            self.assertEqual(len(data.strip(b"x")), 0)
        finally:
            data = Nichts

    def testPickle(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.assertRaises(TypeError):
                pickle.dumps(BZ2Compressor(), proto)


klasse BZ2DecompressorTest(BaseTest):
    def test_Constructor(self):
        self.assertRaises(TypeError, BZ2Decompressor, 42)

    def testDecompress(self):
        bz2d = BZ2Decompressor()
        self.assertRaises(TypeError, bz2d.decompress)
        text = bz2d.decompress(self.DATA)
        self.assertEqual(text, self.TEXT)

    def testDecompressChunks10(self):
        bz2d = BZ2Decompressor()
        text = b''
        n = 0
        waehrend Wahr:
            str = self.DATA[n*10:(n+1)*10]
            wenn nicht str:
                breche
            text += bz2d.decompress(str)
            n += 1
        self.assertEqual(text, self.TEXT)

    def testDecompressUnusedData(self):
        bz2d = BZ2Decompressor()
        unused_data = b"this is unused data"
        text = bz2d.decompress(self.DATA+unused_data)
        self.assertEqual(text, self.TEXT)
        self.assertEqual(bz2d.unused_data, unused_data)

    def testEOFError(self):
        bz2d = BZ2Decompressor()
        text = bz2d.decompress(self.DATA)
        self.assertRaises(EOFError, bz2d.decompress, b"anything")
        self.assertRaises(EOFError, bz2d.decompress, b"")

    @support.skip_if_pgo_task
    @bigmemtest(size=_4G + 100, memuse=3.3)
    def testDecompress4G(self, size):
        # "Test BZ2Decompressor.decompress() mit >4GiB input"
        blocksize = min(10 * 1024 * 1024, size)
        block = random.randbytes(blocksize)
        try:
            data = block * ((size-1) // blocksize + 1)
            compressed = bz2.compress(data)
            bz2d = BZ2Decompressor()
            decompressed = bz2d.decompress(compressed)
            self.assertWahr(decompressed == data)
        finally:
            data = Nichts
            compressed = Nichts
            decompressed = Nichts

    def testPickle(self):
        fuer proto in range(pickle.HIGHEST_PROTOCOL + 1):
            mit self.assertRaises(TypeError):
                pickle.dumps(BZ2Decompressor(), proto)

    def testDecompressorChunksMaxsize(self):
        bzd = BZ2Decompressor()
        max_length = 100
        out = []

        # Feed some input
        len_ = len(self.BIG_DATA) - 64
        out.append(bzd.decompress(self.BIG_DATA[:len_],
                                  max_length=max_length))
        self.assertFalsch(bzd.needs_input)
        self.assertEqual(len(out[-1]), max_length)

        # Retrieve more data without providing more input
        out.append(bzd.decompress(b'', max_length=max_length))
        self.assertFalsch(bzd.needs_input)
        self.assertEqual(len(out[-1]), max_length)

        # Retrieve more data waehrend providing more input
        out.append(bzd.decompress(self.BIG_DATA[len_:],
                                  max_length=max_length))
        self.assertLessEqual(len(out[-1]), max_length)

        # Retrieve remaining uncompressed data
        waehrend nicht bzd.eof:
            out.append(bzd.decompress(b'', max_length=max_length))
            self.assertLessEqual(len(out[-1]), max_length)

        out = b"".join(out)
        self.assertEqual(out, self.BIG_TEXT)
        self.assertEqual(bzd.unused_data, b"")

    def test_decompressor_inputbuf_1(self):
        # Test reusing input buffer after moving existing
        # contents to beginning
        bzd = BZ2Decompressor()
        out = []

        # Create input buffer und fill it
        self.assertEqual(bzd.decompress(self.DATA[:100],
                                        max_length=0), b'')

        # Retrieve some results, freeing capacity at beginning
        # of input buffer
        out.append(bzd.decompress(b'', 2))

        # Add more data that fits into input buffer after
        # moving existing data to beginning
        out.append(bzd.decompress(self.DATA[100:105], 15))

        # Decompress rest of data
        out.append(bzd.decompress(self.DATA[105:]))
        self.assertEqual(b''.join(out), self.TEXT)

    def test_decompressor_inputbuf_2(self):
        # Test reusing input buffer by appending data at the
        # end right away
        bzd = BZ2Decompressor()
        out = []

        # Create input buffer und empty it
        self.assertEqual(bzd.decompress(self.DATA[:200],
                                        max_length=0), b'')
        out.append(bzd.decompress(b''))

        # Fill buffer mit new data
        out.append(bzd.decompress(self.DATA[200:280], 2))

        # Append some more data, nicht enough to require resize
        out.append(bzd.decompress(self.DATA[280:300], 2))

        # Decompress rest of data
        out.append(bzd.decompress(self.DATA[300:]))
        self.assertEqual(b''.join(out), self.TEXT)

    def test_decompressor_inputbuf_3(self):
        # Test reusing input buffer after extending it

        bzd = BZ2Decompressor()
        out = []

        # Create almost full input buffer
        out.append(bzd.decompress(self.DATA[:200], 5))

        # Add even more data to it, requiring resize
        out.append(bzd.decompress(self.DATA[200:300], 5))

        # Decompress rest of data
        out.append(bzd.decompress(self.DATA[300:]))
        self.assertEqual(b''.join(out), self.TEXT)

    def test_failure(self):
        bzd = BZ2Decompressor()
        self.assertRaises(Exception, bzd.decompress, self.BAD_DATA * 30)
        # Previously, a second call could crash due to internal inconsistency
        self.assertRaises(Exception, bzd.decompress, self.BAD_DATA * 30)

    @support.refcount_test
    def test_refleaks_in___init__(self):
        gettotalrefcount = support.get_attribute(sys, 'gettotalrefcount')
        bzd = BZ2Decompressor()
        refs_before = gettotalrefcount()
        fuer i in range(100):
            bzd.__init__()
        self.assertAlmostEqual(gettotalrefcount() - refs_before, 0, delta=10)

    def test_uninitialized_BZ2Decompressor_crash(self):
        self.assertEqual(BZ2Decompressor.__new__(BZ2Decompressor).
                         decompress(bytes()), b'')


klasse CompressDecompressTest(BaseTest):
    def testCompress(self):
        data = bz2.compress(self.TEXT)
        self.assertEqual(ext_decompress(data), self.TEXT)

    def testCompressEmptyString(self):
        text = bz2.compress(b'')
        self.assertEqual(text, self.EMPTY_DATA)

    def testDecompress(self):
        text = bz2.decompress(self.DATA)
        self.assertEqual(text, self.TEXT)

    def testDecompressEmpty(self):
        text = bz2.decompress(b"")
        self.assertEqual(text, b"")

    def testDecompressToEmptyString(self):
        text = bz2.decompress(self.EMPTY_DATA)
        self.assertEqual(text, b'')

    def testDecompressIncomplete(self):
        self.assertRaises(ValueError, bz2.decompress, self.DATA[:-10])

    def testDecompressBadData(self):
        self.assertRaises(OSError, bz2.decompress, self.BAD_DATA)

    def testDecompressMultiStream(self):
        text = bz2.decompress(self.DATA * 5)
        self.assertEqual(text, self.TEXT * 5)

    def testDecompressTrailingJunk(self):
        text = bz2.decompress(self.DATA + self.BAD_DATA)
        self.assertEqual(text, self.TEXT)

    def testDecompressMultiStreamTrailingJunk(self):
        text = bz2.decompress(self.DATA * 5 + self.BAD_DATA)
        self.assertEqual(text, self.TEXT * 5)


klasse OpenTest(BaseTest):
    "Test the open function."

    def open(self, *args, **kwargs):
        return bz2.open(*args, **kwargs)

    def test_binary_modes(self):
        fuer mode in ("wb", "xb"):
            wenn mode == "xb":
                unlink(self.filename)
            mit self.open(self.filename, mode) als f:
                f.write(self.TEXT)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read())
                self.assertEqual(file_data, self.TEXT)
            mit self.open(self.filename, "rb") als f:
                self.assertEqual(f.read(), self.TEXT)
            mit self.open(self.filename, "ab") als f:
                f.write(self.TEXT)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read())
                self.assertEqual(file_data, self.TEXT * 2)

    def test_implicit_binary_modes(self):
        # Test implicit binary modes (no "b" oder "t" in mode string).
        fuer mode in ("w", "x"):
            wenn mode == "x":
                unlink(self.filename)
            mit self.open(self.filename, mode) als f:
                f.write(self.TEXT)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read())
                self.assertEqual(file_data, self.TEXT)
            mit self.open(self.filename, "r") als f:
                self.assertEqual(f.read(), self.TEXT)
            mit self.open(self.filename, "a") als f:
                f.write(self.TEXT)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read())
                self.assertEqual(file_data, self.TEXT * 2)

    def test_text_modes(self):
        text = self.TEXT.decode("ascii")
        text_native_eol = text.replace("\n", os.linesep)
        fuer mode in ("wt", "xt"):
            wenn mode == "xt":
                unlink(self.filename)
            mit self.open(self.filename, mode, encoding="ascii") als f:
                f.write(text)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read()).decode("ascii")
                self.assertEqual(file_data, text_native_eol)
            mit self.open(self.filename, "rt", encoding="ascii") als f:
                self.assertEqual(f.read(), text)
            mit self.open(self.filename, "at", encoding="ascii") als f:
                f.write(text)
            mit open(self.filename, "rb") als f:
                file_data = ext_decompress(f.read()).decode("ascii")
                self.assertEqual(file_data, text_native_eol * 2)

    def test_x_mode(self):
        fuer mode in ("x", "xb", "xt"):
            unlink(self.filename)
            encoding = "utf-8" wenn "t" in mode sonst Nichts
            mit self.open(self.filename, mode, encoding=encoding) als f:
                pass
            mit self.assertRaises(FileExistsError):
                mit self.open(self.filename, mode) als f:
                    pass

    def test_fileobj(self):
        mit self.open(BytesIO(self.DATA), "r") als f:
            self.assertEqual(f.read(), self.TEXT)
        mit self.open(BytesIO(self.DATA), "rb") als f:
            self.assertEqual(f.read(), self.TEXT)
        text = self.TEXT.decode("ascii")
        mit self.open(BytesIO(self.DATA), "rt", encoding="utf-8") als f:
            self.assertEqual(f.read(), text)

    def test_bad_params(self):
        # Test invalid parameter combinations.
        self.assertRaises(ValueError,
                          self.open, self.filename, "wbt")
        self.assertRaises(ValueError,
                          self.open, self.filename, "xbt")
        self.assertRaises(ValueError,
                          self.open, self.filename, "rb", encoding="utf-8")
        self.assertRaises(ValueError,
                          self.open, self.filename, "rb", errors="ignore")
        self.assertRaises(ValueError,
                          self.open, self.filename, "rb", newline="\n")

    def test_encoding(self):
        # Test non-default encoding.
        text = self.TEXT.decode("ascii")
        text_native_eol = text.replace("\n", os.linesep)
        mit self.open(self.filename, "wt", encoding="utf-16-le") als f:
            f.write(text)
        mit open(self.filename, "rb") als f:
            file_data = ext_decompress(f.read()).decode("utf-16-le")
            self.assertEqual(file_data, text_native_eol)
        mit self.open(self.filename, "rt", encoding="utf-16-le") als f:
            self.assertEqual(f.read(), text)

    def test_encoding_error_handler(self):
        # Test mit non-default encoding error handler.
        mit self.open(self.filename, "wb") als f:
            f.write(b"foo\xffbar")
        mit self.open(self.filename, "rt", encoding="ascii", errors="ignore") \
                als f:
            self.assertEqual(f.read(), "foobar")

    def test_newline(self):
        # Test mit explicit newline (universal newline mode disabled).
        text = self.TEXT.decode("ascii")
        mit self.open(self.filename, "wt", encoding="utf-8", newline="\n") als f:
            f.write(text)
        mit self.open(self.filename, "rt", encoding="utf-8", newline="\r") als f:
            self.assertEqual(f.readlines(), [text])


def tearDownModule():
    support.reap_children()


wenn __name__ == '__main__':
    unittest.main()
