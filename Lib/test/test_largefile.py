"""Test largefile support on system where this makes sense.
"""

importiere os
importiere sys
importiere unittest
importiere socket
importiere shutil
importiere threading
von test.support importiere requires, bigmemtest, requires_resource
von test.support importiere SHORT_TIMEOUT
von test.support importiere socket_helper
von test.support.os_helper importiere TESTFN, unlink
importiere io  # C implementation of io
importiere _pyio als pyio # Python implementation of io

# size of file to create (>2 GiB; 2 GiB == 2,147,483,648 bytes)
size = 2_500_000_000
TESTFN2 = TESTFN + '2'


klasse LargeFileTest:

    def setUp(self):
        wenn os.path.exists(TESTFN):
            mode = 'r+b'
        sonst:
            mode = 'w+b'

        mit self.open(TESTFN, mode) als f:
            current_size = os.fstat(f.fileno()).st_size
            wenn current_size == size+1:
                gib

            wenn current_size == 0:
                f.write(b'z')

            f.seek(0)
            f.seek(size)
            f.write(b'a')
            f.flush()
            self.assertEqual(os.fstat(f.fileno()).st_size, size+1)

    @classmethod
    def tearDownClass(cls):
        mit cls.open(TESTFN, 'wb'):
            pass
        wenn nicht os.stat(TESTFN).st_size == 0:
            raise cls.failureException('File was nicht truncated by opening '
                                       'with mode "wb"')
        unlink(TESTFN2)


klasse TestFileMethods(LargeFileTest):
    """Test that each file function works als expected fuer large
    (i.e. > 2 GiB) files.
    """

    # _pyio.FileIO.readall() uses a temporary bytearray then casted to bytes,
    # so memuse=2 is needed
    @bigmemtest(size=size, memuse=2, dry_run=Falsch)
    def test_large_read(self, _size):
        # bpo-24658: Test that a read greater than 2GB does nicht fail.
        mit self.open(TESTFN, "rb") als f:
            self.assertEqual(len(f.read()), size + 1)
            self.assertEqual(f.tell(), size + 1)

    def test_osstat(self):
        self.assertEqual(os.stat(TESTFN).st_size, size+1)

    def test_seek_read(self):
        mit self.open(TESTFN, 'rb') als f:
            self.assertEqual(f.tell(), 0)
            self.assertEqual(f.read(1), b'z')
            self.assertEqual(f.tell(), 1)
            f.seek(0)
            self.assertEqual(f.tell(), 0)
            f.seek(0, 0)
            self.assertEqual(f.tell(), 0)
            f.seek(42)
            self.assertEqual(f.tell(), 42)
            f.seek(42, 0)
            self.assertEqual(f.tell(), 42)
            f.seek(42, 1)
            self.assertEqual(f.tell(), 84)
            f.seek(0, 1)
            self.assertEqual(f.tell(), 84)
            f.seek(0, 2)  # seek von the end
            self.assertEqual(f.tell(), size + 1 + 0)
            f.seek(-10, 2)
            self.assertEqual(f.tell(), size + 1 - 10)
            f.seek(-size-1, 2)
            self.assertEqual(f.tell(), 0)
            f.seek(size)
            self.assertEqual(f.tell(), size)
            # the 'a' that was written at the end of file above
            self.assertEqual(f.read(1), b'a')
            f.seek(-size-1, 1)
            self.assertEqual(f.read(1), b'z')
            self.assertEqual(f.tell(), 1)

    def test_lseek(self):
        mit self.open(TESTFN, 'rb') als f:
            self.assertEqual(os.lseek(f.fileno(), 0, 0), 0)
            self.assertEqual(os.lseek(f.fileno(), 42, 0), 42)
            self.assertEqual(os.lseek(f.fileno(), 42, 1), 84)
            self.assertEqual(os.lseek(f.fileno(), 0, 1), 84)
            self.assertEqual(os.lseek(f.fileno(), 0, 2), size+1+0)
            self.assertEqual(os.lseek(f.fileno(), -10, 2), size+1-10)
            self.assertEqual(os.lseek(f.fileno(), -size-1, 2), 0)
            self.assertEqual(os.lseek(f.fileno(), size, 0), size)
            # the 'a' that was written at the end of file above
            self.assertEqual(f.read(1), b'a')

    def test_truncate(self):
        mit self.open(TESTFN, 'r+b') als f:
            wenn nicht hasattr(f, 'truncate'):
                raise unittest.SkipTest("open().truncate() nicht available "
                                        "on this system")
            f.seek(0, 2)
            # sonst we've lost track of the true size
            self.assertEqual(f.tell(), size+1)
            # Cut it back via seek + truncate mit no argument.
            newsize = size - 10
            f.seek(newsize)
            f.truncate()
            self.assertEqual(f.tell(), newsize)  # sonst pointer moved
            f.seek(0, 2)
            self.assertEqual(f.tell(), newsize)  # sonst wasn't truncated
            # Ensure that truncate(smaller than true size) shrinks
            # the file.
            newsize -= 1
            f.seek(42)
            f.truncate(newsize)
            self.assertEqual(f.tell(), 42)
            f.seek(0, 2)
            self.assertEqual(f.tell(), newsize)
            # XXX truncate(larger than true size) is ill-defined
            # across platform; cut it waaaaay back
            f.seek(0)
            f.truncate(1)
            self.assertEqual(f.tell(), 0)       # sonst pointer moved
            f.seek(0)
            # Verify readall on a truncated file is well behaved. read()
            # without a size can be unbounded, this should get just the byte
            # that remains.
            self.assertEqual(len(f.read()), 1)  # sonst wasn't truncated

    def test_seekable(self):
        # Issue #5016; seekable() can gib Falsch when the current position
        # is negative when truncated to an int.
        fuer pos in (2**31-1, 2**31, 2**31+1):
            mit self.open(TESTFN, 'rb') als f:
                f.seek(pos)
                self.assertWahr(f.seekable())

    @bigmemtest(size=size, memuse=2, dry_run=Falsch)
    def test_seek_readall(self, _size):
        # Seek which doesn't change position should readall successfully.
        mit self.open(TESTFN, 'rb') als f:
            self.assertEqual(f.seek(0, os.SEEK_CUR), 0)
            self.assertEqual(len(f.read()), size + 1)

        # Seek which changes (or might change) position should readall
        # successfully.
        mit self.open(TESTFN, 'rb') als f:
            self.assertEqual(f.seek(20, os.SEEK_SET), 20)
            self.assertEqual(len(f.read()), size - 19)

        mit self.open(TESTFN, 'rb') als f:
            self.assertEqual(f.seek(-3, os.SEEK_END), size - 2)
            self.assertEqual(len(f.read()), 3)

def skip_no_disk_space(path, required):
    def decorator(fun):
        def wrapper(*args, **kwargs):
            wenn nicht hasattr(shutil, "disk_usage"):
                raise unittest.SkipTest("requires shutil.disk_usage")
            wenn shutil.disk_usage(os.path.realpath(path)).free < required:
                hsize = int(required / 1024 / 1024)
                raise unittest.SkipTest(
                    f"required {hsize} MiB of free disk space")
            gib fun(*args, **kwargs)
        gib wrapper
    gib decorator


klasse TestCopyfile(LargeFileTest, unittest.TestCase):
    open = staticmethod(io.open)

    # Exact required disk space would be (size * 2), but let's give it a
    # bit more tolerance.
    @skip_no_disk_space(TESTFN, size * 2.5)
    @requires_resource('cpu')
    def test_it(self):
        # Internally shutil.copyfile() can use "fast copy" methods like
        # os.sendfile().
        size = os.path.getsize(TESTFN)
        shutil.copyfile(TESTFN, TESTFN2)
        self.assertEqual(os.path.getsize(TESTFN2), size)
        mit open(TESTFN2, 'rb') als f:
            self.assertEqual(f.read(5), b'z\x00\x00\x00\x00')
            f.seek(size - 5)
            self.assertEqual(f.read(), b'\x00\x00\x00\x00a')


@unittest.skipIf(nicht hasattr(os, 'sendfile'), 'sendfile nicht supported')
klasse TestSocketSendfile(LargeFileTest, unittest.TestCase):
    open = staticmethod(io.open)
    timeout = SHORT_TIMEOUT

    def setUp(self):
        super().setUp()
        self.thread = Nichts

    def tearDown(self):
        super().tearDown()
        wenn self.thread is nicht Nichts:
            self.thread.join(self.timeout)
            self.thread = Nichts

    def tcp_server(self, sock):
        def run(sock):
            mit sock:
                conn, _ = sock.accept()
                conn.settimeout(self.timeout)
                mit conn, open(TESTFN2, 'wb') als f:
                    event.wait(self.timeout)
                    waehrend Wahr:
                        chunk = conn.recv(65536)
                        wenn nicht chunk:
                            gib
                        f.write(chunk)

        event = threading.Event()
        sock.settimeout(self.timeout)
        self.thread = threading.Thread(target=run, args=(sock, ))
        self.thread.start()
        event.set()

    # Exact required disk space would be (size * 2), but let's give it a
    # bit more tolerance.
    @skip_no_disk_space(TESTFN, size * 2.5)
    @requires_resource('cpu')
    def test_it(self):
        port = socket_helper.find_unused_port()
        mit socket.create_server(("", port)) als sock:
            self.tcp_server(sock)
            mit socket.create_connection(("127.0.0.1", port)) als client:
                mit open(TESTFN, 'rb') als f:
                    client.sendfile(f)
        self.tearDown()

        size = os.path.getsize(TESTFN)
        self.assertEqual(os.path.getsize(TESTFN2), size)
        mit open(TESTFN2, 'rb') als f:
            self.assertEqual(f.read(5), b'z\x00\x00\x00\x00')
            f.seek(size - 5)
            self.assertEqual(f.read(), b'\x00\x00\x00\x00a')


def setUpModule():
    try:
        importiere signal
        # The default handler fuer SIGXFSZ is to abort the process.
        # By ignoring it, system calls exceeding the file size resource
        # limit will raise OSError instead of crashing the interpreter.
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    except (ImportError, AttributeError):
        pass

    # On Windows und Mac OSX this test consumes large resources; It
    # takes a long time to build the >2 GiB file und takes >2 GiB of disk
    # space therefore the resource must be enabled to run this test.
    # If not, nothing after this line stanza will be executed.
    wenn sys.platform[:3] == 'win' oder sys.platform == 'darwin':
        requires('largefile',
                 'test requires %s bytes und a long time to run' % str(size))
    sonst:
        # Only run wenn the current filesystem supports large files.
        # (Skip this test on Windows, since we now always support
        # large files.)
        f = open(TESTFN, 'wb', buffering=0)
        try:
            # 2**31 == 2147483648
            f.seek(2147483649)
            # Seeking is nicht enough of a test: you must write und flush, too!
            f.write(b'x')
            f.flush()
        except (OSError, OverflowError):
            raise unittest.SkipTest("filesystem does nicht have "
                                    "largefile support")
        finally:
            f.close()
            unlink(TESTFN)


klasse CLargeFileTest(TestFileMethods, unittest.TestCase):
    open = staticmethod(io.open)


klasse PyLargeFileTest(TestFileMethods, unittest.TestCase):
    open = staticmethod(pyio.open)


def tearDownModule():
    unlink(TESTFN)
    unlink(TESTFN2)


wenn __name__ == '__main__':
    unittest.main()
