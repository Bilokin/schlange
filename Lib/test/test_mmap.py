von test.support importiere (
    requires, _2G, _4G, gc_collect, cpython_only, is_emscripten, is_apple,
    in_systemd_nspawn_sync_suppressed,
)
von test.support.import_helper importiere import_module
von test.support.os_helper importiere TESTFN, unlink
von test.support.script_helper importiere assert_python_ok
importiere unittest
importiere errno
importiere os
importiere re
importiere itertools
importiere random
importiere socket
importiere string
importiere sys
importiere textwrap
importiere weakref

# Skip test wenn we can't importiere mmap.
mmap = import_module('mmap')

PAGESIZE = mmap.PAGESIZE

tagname_prefix = f'python_{os.getpid()}_test_mmap'
def random_tagname(length=10):
    suffix = ''.join(random.choices(string.ascii_uppercase, k=length))
    gib f'{tagname_prefix}_{suffix}'

# Python's mmap module dup()s the file descriptor. Emscripten's FS layer
# does nicht materialize file changes through a dupped fd to a new mmap.
wenn is_emscripten:
    wirf unittest.SkipTest("incompatible mit Emscripten's mmap emulation.")


klasse MmapTests(unittest.TestCase):

    def setUp(self):
        wenn os.path.exists(TESTFN):
            os.unlink(TESTFN)

    def tearDown(self):
        versuch:
            os.unlink(TESTFN)
        ausser OSError:
            pass

    def test_basic(self):
        # Test mmap module on Unix systems und Windows

        # Create a file to be mmap'ed.
        f = open(TESTFN, 'bw+')
        versuch:
            # Write 2 pages worth of data to the file
            f.write(b'\0'* PAGESIZE)
            f.write(b'foo')
            f.write(b'\0'* (PAGESIZE-3) )
            f.flush()
            m = mmap.mmap(f.fileno(), 2 * PAGESIZE)
        schliesslich:
            f.close()

        # Simple sanity checks

        tp = str(type(m))  # SF bug 128713:  segfaulted on Linux
        self.assertEqual(m.find(b'foo'), PAGESIZE)

        self.assertEqual(len(m), 2*PAGESIZE)

        self.assertEqual(m[0], 0)
        self.assertEqual(m[0:3], b'\0\0\0')

        # Shouldn't crash on boundary (Issue #5292)
        self.assertRaises(IndexError, m.__getitem__, len(m))
        self.assertRaises(IndexError, m.__setitem__, len(m), b'\0')

        # Modify the file's content
        m[0] = b'3'[0]
        m[PAGESIZE +3: PAGESIZE +3+3] = b'bar'

        # Check that the modification worked
        self.assertEqual(m[0], b'3'[0])
        self.assertEqual(m[0:3], b'3\0\0')
        self.assertEqual(m[PAGESIZE-1 : PAGESIZE + 7], b'\0foobar\0')

        m.flush()

        # Test doing a regular expression match in an mmap'ed file
        match = re.search(b'[A-Za-z]+', m)
        wenn match ist Nichts:
            self.fail('regex match on mmap failed!')
        sonst:
            start, end = match.span(0)
            length = end - start

            self.assertEqual(start, PAGESIZE)
            self.assertEqual(end, PAGESIZE + 6)

        # test seeking around (try to overflow the seek implementation)
        self.assertWahr(m.seekable())
        self.assertEqual(m.seek(0, 0), 0)
        self.assertEqual(m.tell(), 0)
        self.assertEqual(m.seek(42, 1), 42)
        self.assertEqual(m.tell(), 42)
        self.assertEqual(m.seek(0, 2), len(m))
        self.assertEqual(m.tell(), len(m))

        # Try to seek to negative position...
        self.assertRaises(ValueError, m.seek, -1)

        # Try to seek beyond end of mmap...
        self.assertRaises(ValueError, m.seek, 1, 2)

        # Try to seek to negative position...
        self.assertRaises(ValueError, m.seek, -len(m)-1, 2)

        # Try resizing map
        versuch:
            m.resize(512)
        ausser SystemError:
            # resize() nicht supported
            # No messages are printed, since the output of this test suite
            # would then be different across platforms.
            pass
        sonst:
            # resize() ist supported
            self.assertEqual(len(m), 512)
            # Check that we can no longer seek beyond the new size.
            self.assertRaises(ValueError, m.seek, 513, 0)

            # Check that the underlying file ist truncated too
            # (bug #728515)
            f = open(TESTFN, 'rb')
            versuch:
                f.seek(0, 2)
                self.assertEqual(f.tell(), 512)
            schliesslich:
                f.close()
            self.assertEqual(m.size(), 512)

        m.close()

    def test_access_parameter(self):
        # Test fuer "access" keyword parameter
        mapsize = 10
        mit open(TESTFN, "wb") als fp:
            fp.write(b"a"*mapsize)
        mit open(TESTFN, "rb") als f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_READ)
            self.assertEqual(m[:], b'a'*mapsize, "Readonly memory map data incorrect.")

            # Ensuring that readonly mmap can't be slice assigned
            versuch:
                m[:] = b'b'*mapsize
            ausser TypeError:
                pass
            sonst:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be item assigned
            versuch:
                m[0] = b'b'
            ausser TypeError:
                pass
            sonst:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be write() to
            versuch:
                m.seek(0, 0)
                m.write(b'abc')
            ausser TypeError:
                pass
            sonst:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be write_byte() to
            versuch:
                m.seek(0, 0)
                m.write_byte(b'd')
            ausser TypeError:
                pass
            sonst:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be resized
            versuch:
                m.resize(2*mapsize)
            ausser SystemError:   # resize ist nicht universally supported
                pass
            ausser TypeError:
                pass
            sonst:
                self.fail("Able to resize readonly memory map")
            mit open(TESTFN, "rb") als fp:
                self.assertEqual(fp.read(), b'a'*mapsize,
                                 "Readonly memory map data file was modified")

        # Opening mmap mit size too big
        mit open(TESTFN, "r+b") als f:
            versuch:
                m = mmap.mmap(f.fileno(), mapsize+1)
            ausser ValueError:
                # we do nicht expect a ValueError on Windows
                # CAUTION:  This also changes the size of the file on disk, und
                # later tests assume that the length hasn't changed.  We need to
                # repair that.
                wenn sys.platform.startswith('win'):
                    self.fail("Opening mmap mit size+1 should work on Windows.")
            sonst:
                # we expect a ValueError on Unix, but nicht on Windows
                wenn nicht sys.platform.startswith('win'):
                    self.fail("Opening mmap mit size+1 should wirf ValueError.")
                m.close()
            wenn sys.platform.startswith('win'):
                # Repair damage von the resizing test.
                mit open(TESTFN, 'r+b') als f:
                    f.truncate(mapsize)

        # Opening mmap mit access=ACCESS_WRITE
        mit open(TESTFN, "r+b") als f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_WRITE)
            # Modifying write-through memory map
            m[:] = b'c'*mapsize
            self.assertEqual(m[:], b'c'*mapsize,
                   "Write-through memory map memory nicht updated properly.")
            m.flush()
            m.close()
        mit open(TESTFN, 'rb') als f:
            stuff = f.read()
        self.assertEqual(stuff, b'c'*mapsize,
               "Write-through memory map data file nicht updated properly.")

        # Opening mmap mit access=ACCESS_COPY
        mit open(TESTFN, "r+b") als f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_COPY)
            # Modifying copy-on-write memory map
            m[:] = b'd'*mapsize
            self.assertEqual(m[:], b'd' * mapsize,
                             "Copy-on-write memory map data nicht written correctly.")
            m.flush()
            mit open(TESTFN, "rb") als fp:
                self.assertEqual(fp.read(), b'c'*mapsize,
                                 "Copy-on-write test data file should nicht be modified.")
            # Ensuring copy-on-write maps cannot be resized
            self.assertRaises(TypeError, m.resize, 2*mapsize)
            m.close()

        # Ensuring invalid access parameter raises exception
        mit open(TESTFN, "r+b") als f:
            self.assertRaises(ValueError, mmap.mmap, f.fileno(), mapsize, access=4)

        wenn os.name == "posix":
            # Try incompatible flags, prot und access parameters.
            mit open(TESTFN, "r+b") als f:
                self.assertRaises(ValueError, mmap.mmap, f.fileno(), mapsize,
                                  flags=mmap.MAP_PRIVATE,
                                  prot=mmap.PROT_READ, access=mmap.ACCESS_WRITE)

            # Try writing mit PROT_EXEC und without PROT_WRITE
            prot = mmap.PROT_READ | getattr(mmap, 'PROT_EXEC', 0)
            mit open(TESTFN, "r+b") als f:
                versuch:
                    m = mmap.mmap(f.fileno(), mapsize, prot=prot)
                ausser PermissionError:
                    # on macOS 14, PROT_READ | PROT_EXEC ist nicht allowed
                    pass
                sonst:
                    self.assertRaises(TypeError, m.write, b"abcdef")
                    self.assertRaises(TypeError, m.write_byte, 0)
                    m.close()

    @unittest.skipIf(os.name == 'nt', 'trackfd nicht present on Windows')
    def test_trackfd_parameter(self):
        size = 64
        mit open(TESTFN, "wb") als f:
            f.write(b"a"*size)
        fuer close_original_fd in Wahr, Falsch:
            mit self.subTest(close_original_fd=close_original_fd):
                mit open(TESTFN, "r+b") als f:
                    mit mmap.mmap(f.fileno(), size, trackfd=Falsch) als m:
                        wenn close_original_fd:
                            f.close()
                        self.assertEqual(len(m), size)
                        mit self.assertRaises(OSError) als err_cm:
                            m.size()
                        self.assertEqual(err_cm.exception.errno, errno.EBADF)
                        mit self.assertRaises(ValueError):
                            m.resize(size * 2)
                        mit self.assertRaises(ValueError):
                            m.resize(size // 2)
                        self.assertEqual(m.closed, Falsch)

                        # Smoke-test other API
                        m.write_byte(ord('X'))
                        m[2] = ord('Y')
                        m.flush()
                        mit open(TESTFN, "rb") als f:
                            self.assertEqual(f.read(4), b'XaYa')
                        self.assertEqual(m.tell(), 1)
                        m.seek(0)
                        self.assertEqual(m.tell(), 0)
                        self.assertEqual(m.read_byte(), ord('X'))

                self.assertEqual(m.closed, Wahr)
                self.assertEqual(os.stat(TESTFN).st_size, size)

    @unittest.skipIf(os.name == 'nt', 'trackfd nicht present on Windows')
    def test_trackfd_neg1(self):
        size = 64
        mit mmap.mmap(-1, size, trackfd=Falsch) als m:
            mit self.assertRaises(OSError):
                m.size()
            mit self.assertRaises(ValueError):
                m.resize(size // 2)
            self.assertEqual(len(m), size)
            m[0] = ord('a')
            pruefe m[0] == ord('a')

    @unittest.skipIf(os.name != 'nt', 'trackfd only fails on Windows')
    def test_no_trackfd_parameter_on_windows(self):
        # 'trackffd' ist an invalid keyword argument fuer this function
        size = 64
        mit self.assertRaises(TypeError):
            mmap.mmap(-1, size, trackfd=Wahr)
        mit self.assertRaises(TypeError):
            mmap.mmap(-1, size, trackfd=Falsch)

    def test_bad_file_desc(self):
        # Try opening a bad file descriptor...
        self.assertRaises(OSError, mmap.mmap, -2, 4096)

    def test_tougher_find(self):
        # Do a tougher .find() test.  SF bug 515943 pointed out that, in 2.2,
        # searching fuer data mit embedded \0 bytes didn't work.
        mit open(TESTFN, 'wb+') als f:

            data = b'aabaac\x00deef\x00\x00aa\x00'
            n = len(data)
            f.write(data)
            f.flush()
            m = mmap.mmap(f.fileno(), n)

        fuer start in range(n+1):
            fuer finish in range(start, n+1):
                slice = data[start : finish]
                self.assertEqual(m.find(slice), data.find(slice))
                self.assertEqual(m.find(slice + b'x'), -1)
        m.close()

    def test_find_end(self):
        # test the new 'end' parameter works als expected
        mit open(TESTFN, 'wb+') als f:
            data = b'one two ones'
            n = len(data)
            f.write(data)
            f.flush()
            m = mmap.mmap(f.fileno(), n)

        self.assertEqual(m.find(b'one'), 0)
        self.assertEqual(m.find(b'ones'), 8)
        self.assertEqual(m.find(b'one', 0, -1), 0)
        self.assertEqual(m.find(b'one', 1), 8)
        self.assertEqual(m.find(b'one', 1, -1), 8)
        self.assertEqual(m.find(b'one', 1, -2), -1)
        self.assertEqual(m.find(bytearray(b'one')), 0)

        fuer i in range(-n-1, n+1):
            fuer j in range(-n-1, n+1):
                fuer p in [b"o", b"on", b"two", b"ones", b"s"]:
                    expected = data.find(p, i, j)
                    self.assertEqual(m.find(p, i, j), expected, (p, i, j))

    def test_find_does_not_access_beyond_buffer(self):
        versuch:
            flags = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS
            PAGESIZE = mmap.PAGESIZE
            PROT_NONE = 0
            PROT_READ = mmap.PROT_READ
        ausser AttributeError als e:
            wirf unittest.SkipTest("mmap flags unavailable") von e
        fuer i in range(0, 2049):
            mit mmap.mmap(-1, PAGESIZE * (i + 1),
                           flags=flags, prot=PROT_NONE) als guard:
                mit mmap.mmap(-1, PAGESIZE * (i + 2048),
                               flags=flags, prot=PROT_READ) als fm:
                    fm.find(b"fo", -2)


    def test_rfind(self):
        # test the new 'end' parameter works als expected
        mit open(TESTFN, 'wb+') als f:
            data = b'one two ones'
            n = len(data)
            f.write(data)
            f.flush()
            m = mmap.mmap(f.fileno(), n)

        self.assertEqual(m.rfind(b'one'), 8)
        self.assertEqual(m.rfind(b'one '), 0)
        self.assertEqual(m.rfind(b'one', 0, -1), 8)
        self.assertEqual(m.rfind(b'one', 0, -2), 0)
        self.assertEqual(m.rfind(b'one', 1, -1), 8)
        self.assertEqual(m.rfind(b'one', 1, -2), -1)
        self.assertEqual(m.rfind(bytearray(b'one')), 8)


    def test_double_close(self):
        # make sure a double close doesn't crash on Solaris (Bug# 665913)
        mit open(TESTFN, 'wb+') als f:
            f.write(2**16 * b'a') # Arbitrary character

        mit open(TESTFN, 'rb') als f:
            mf = mmap.mmap(f.fileno(), 2**16, access=mmap.ACCESS_READ)
            mf.close()
            mf.close()

    def test_entire_file(self):
        # test mapping of entire file by passing 0 fuer map length
        mit open(TESTFN, "wb+") als f:
            f.write(2**16 * b'm') # Arbitrary character

        mit open(TESTFN, "rb+") als f, \
             mmap.mmap(f.fileno(), 0) als mf:
            self.assertEqual(len(mf), 2**16, "Map size should equal file size.")
            self.assertEqual(mf.read(2**16), 2**16 * b"m")

    def test_length_0_offset(self):
        # Issue #10916: test mapping of remainder of file by passing 0 for
        # map length mit an offset doesn't cause a segfault.
        # NOTE: allocation granularity ist currently 65536 under Win64,
        # und therefore the minimum offset alignment.
        mit open(TESTFN, "wb") als f:
            f.write((65536 * 2) * b'm') # Arbitrary character

        mit open(TESTFN, "rb") als f:
            mit mmap.mmap(f.fileno(), 0, offset=65536, access=mmap.ACCESS_READ) als mf:
                self.assertRaises(IndexError, mf.__getitem__, 80000)

    def test_length_0_large_offset(self):
        # Issue #10959: test mapping of a file by passing 0 for
        # map length mit a large offset doesn't cause a segfault.
        mit open(TESTFN, "wb") als f:
            f.write(115699 * b'm') # Arbitrary character

        mit open(TESTFN, "w+b") als f:
            self.assertRaises(ValueError, mmap.mmap, f.fileno(), 0,
                              offset=2147418112)

    def test_move(self):
        # make move works everywhere (64-bit format problem earlier)
        mit open(TESTFN, 'wb+') als f:

            f.write(b"ABCDEabcde") # Arbitrary character
            f.flush()

            mf = mmap.mmap(f.fileno(), 10)
            mf.move(5, 0, 5)
            self.assertEqual(mf[:], b"ABCDEABCDE", "Map move should have duplicated front 5")
            mf.close()

        # more excessive test
        data = b"0123456789"
        fuer dest in range(len(data)):
            fuer src in range(len(data)):
                fuer count in range(len(data) - max(dest, src)):
                    expected = data[:dest] + data[src:src+count] + data[dest+count:]
                    m = mmap.mmap(-1, len(data))
                    m[:] = data
                    m.move(dest, src, count)
                    self.assertEqual(m[:], expected)
                    m.close()

        # segfault test (Issue 5387)
        m = mmap.mmap(-1, 100)
        offsets = [-100, -1, 0, 1, 100]
        fuer source, dest, size in itertools.product(offsets, offsets, offsets):
            versuch:
                m.move(source, dest, size)
            ausser ValueError:
                pass

        offsets = [(-1, -1, -1), (-1, -1, 0), (-1, 0, -1), (0, -1, -1),
                   (-1, 0, 0), (0, -1, 0), (0, 0, -1)]
        fuer source, dest, size in offsets:
            self.assertRaises(ValueError, m.move, source, dest, size)

        m.close()

        m = mmap.mmap(-1, 1) # single byte
        self.assertRaises(ValueError, m.move, 0, 0, 2)
        self.assertRaises(ValueError, m.move, 1, 0, 1)
        self.assertRaises(ValueError, m.move, 0, 1, 1)
        m.move(0, 0, 1)
        m.move(0, 0, 0)

    def test_anonymous(self):
        # anonymous mmap.mmap(-1, PAGE)
        m = mmap.mmap(-1, PAGESIZE)
        fuer x in range(PAGESIZE):
            self.assertEqual(m[x], 0,
                             "anonymously mmap'ed contents should be zero")

        fuer x in range(PAGESIZE):
            b = x & 0xff
            m[x] = b
            self.assertEqual(m[x], b)

    def test_read_all(self):
        m = mmap.mmap(-1, 16)
        self.addCleanup(m.close)

        # With no parameters, oder Nichts oder a negative argument, reads all
        m.write(bytes(range(16)))
        m.seek(0)
        self.assertEqual(m.read(), bytes(range(16)))
        m.seek(8)
        self.assertEqual(m.read(), bytes(range(8, 16)))
        m.seek(16)
        self.assertEqual(m.read(), b'')
        m.seek(3)
        self.assertEqual(m.read(Nichts), bytes(range(3, 16)))
        m.seek(4)
        self.assertEqual(m.read(-1), bytes(range(4, 16)))
        m.seek(5)
        self.assertEqual(m.read(-2), bytes(range(5, 16)))
        m.seek(9)
        self.assertEqual(m.read(-42), bytes(range(9, 16)))

    def test_read_invalid_arg(self):
        m = mmap.mmap(-1, 16)
        self.addCleanup(m.close)

        self.assertRaises(TypeError, m.read, 'foo')
        self.assertRaises(TypeError, m.read, 5.5)
        self.assertRaises(TypeError, m.read, [1, 2, 3])

    def test_extended_getslice(self):
        # Test extended slicing by comparing mit list slicing.
        s = bytes(reversed(range(256)))
        m = mmap.mmap(-1, len(s))
        m[:] = s
        self.assertEqual(m[:], s)
        indices = (0, Nichts, 1, 3, 19, 300, sys.maxsize, -1, -2, -31, -300)
        fuer start in indices:
            fuer stop in indices:
                # Skip step 0 (invalid)
                fuer step in indices[1:]:
                    self.assertEqual(m[start:stop:step],
                                     s[start:stop:step])

    def test_extended_set_del_slice(self):
        # Test extended slicing by comparing mit list slicing.
        s = bytes(reversed(range(256)))
        m = mmap.mmap(-1, len(s))
        indices = (0, Nichts, 1, 3, 19, 300, sys.maxsize, -1, -2, -31, -300)
        fuer start in indices:
            fuer stop in indices:
                # Skip invalid step 0
                fuer step in indices[1:]:
                    m[:] = s
                    self.assertEqual(m[:], s)
                    L = list(s)
                    # Make sure we have a slice of exactly the right length,
                    # but mit different data.
                    data = L[start:stop:step]
                    data = bytes(reversed(data))
                    L[start:stop:step] = data
                    m[start:stop:step] = data
                    self.assertEqual(m[:], bytes(L))

    def make_mmap_file (self, f, halfsize):
        # Write 2 pages worth of data to the file
        f.write (b'\0' * halfsize)
        f.write (b'foo')
        f.write (b'\0' * (halfsize - 3))
        f.flush ()
        gib mmap.mmap (f.fileno(), 0)

    def test_empty_file (self):
        f = open (TESTFN, 'w+b')
        f.close()
        mit open(TESTFN, "rb") als f :
            self.assertRaisesRegex(ValueError,
                                   "cannot mmap an empty file",
                                   mmap.mmap, f.fileno(), 0,
                                   access=mmap.ACCESS_READ)

    def test_offset (self):
        f = open (TESTFN, 'w+b')

        versuch: # unlink TESTFN no matter what
            halfsize = mmap.ALLOCATIONGRANULARITY
            m = self.make_mmap_file (f, halfsize)
            m.close ()
            f.close ()

            mapsize = halfsize * 2
            # Try invalid offset
            f = open(TESTFN, "r+b")
            fuer offset in [-2, -1, Nichts]:
                versuch:
                    m = mmap.mmap(f.fileno(), mapsize, offset=offset)
                    self.assertEqual(0, 1)
                ausser (ValueError, TypeError, OverflowError):
                    pass
                sonst:
                    self.assertEqual(0, 0)
            f.close()

            # Try valid offset, hopefully 8192 works on all OSes
            f = open(TESTFN, "r+b")
            m = mmap.mmap(f.fileno(), mapsize - halfsize, offset=halfsize)
            self.assertEqual(m[0:3], b'foo')
            f.close()

            # Try resizing map
            versuch:
                m.resize(512)
            ausser SystemError:
                pass
            sonst:
                # resize() ist supported
                self.assertEqual(len(m), 512)
                # Check that we can no longer seek beyond the new size.
                self.assertRaises(ValueError, m.seek, 513, 0)
                # Check that the content ist nicht changed
                self.assertEqual(m[0:3], b'foo')

                # Check that the underlying file ist truncated too
                f = open(TESTFN, 'rb')
                f.seek(0, 2)
                self.assertEqual(f.tell(), halfsize + 512)
                f.close()
                self.assertEqual(m.size(), halfsize + 512)

            m.close()

        schliesslich:
            f.close()
            versuch:
                os.unlink(TESTFN)
            ausser OSError:
                pass

    def test_subclass(self):
        klasse anon_mmap(mmap.mmap):
            def __new__(klass, *args, **kwargs):
                gib mmap.mmap.__new__(klass, -1, *args, **kwargs)
        anon_mmap(PAGESIZE)

    @unittest.skipUnless(hasattr(mmap, 'PROT_READ'), "needs mmap.PROT_READ")
    def test_prot_readonly(self):
        mapsize = 10
        mit open(TESTFN, "wb") als fp:
            fp.write(b"a"*mapsize)
        mit open(TESTFN, "rb") als f:
            m = mmap.mmap(f.fileno(), mapsize, prot=mmap.PROT_READ)
            self.assertRaises(TypeError, m.write, "foo")

    def test_error(self):
        self.assertIs(mmap.error, OSError)

    def test_io_methods(self):
        data = b"0123456789"
        mit open(TESTFN, "wb") als fp:
            fp.write(b"x"*len(data))
        mit open(TESTFN, "r+b") als f:
            m = mmap.mmap(f.fileno(), len(data))
        # Test write_byte()
        fuer i in range(len(data)):
            self.assertEqual(m.tell(), i)
            m.write_byte(data[i])
            self.assertEqual(m.tell(), i+1)
        self.assertRaises(ValueError, m.write_byte, b"x"[0])
        self.assertEqual(m[:], data)
        # Test read_byte()
        m.seek(0)
        fuer i in range(len(data)):
            self.assertEqual(m.tell(), i)
            self.assertEqual(m.read_byte(), data[i])
            self.assertEqual(m.tell(), i+1)
        self.assertRaises(ValueError, m.read_byte)
        # Test read()
        m.seek(3)
        self.assertEqual(m.read(3), b"345")
        self.assertEqual(m.tell(), 6)
        # Test write()
        m.seek(3)
        m.write(b"bar")
        self.assertEqual(m.tell(), 6)
        self.assertEqual(m[:], b"012bar6789")
        m.write(bytearray(b"baz"))
        self.assertEqual(m.tell(), 9)
        self.assertEqual(m[:], b"012barbaz9")
        self.assertRaises(ValueError, m.write, b"ba")

    def test_non_ascii_byte(self):
        fuer b in (129, 200, 255): # > 128
            m = mmap.mmap(-1, 1)
            m.write_byte(b)
            self.assertEqual(m[0], b)
            m.seek(0)
            self.assertEqual(m.read_byte(), b)
            m.close()

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_tagname(self):
        data1 = b"0123456789"
        data2 = b"abcdefghij"
        pruefe len(data1) == len(data2)
        tagname1 = random_tagname()
        tagname2 = random_tagname()

        # Test same tag
        m1 = mmap.mmap(-1, len(data1), tagname=tagname1)
        m1[:] = data1
        m2 = mmap.mmap(-1, len(data2), tagname=tagname1)
        m2[:] = data2
        self.assertEqual(m1[:], data2)
        self.assertEqual(m2[:], data2)
        m2.close()
        m1.close()

        # Test different tag
        m1 = mmap.mmap(-1, len(data1), tagname=tagname1)
        m1[:] = data1
        m2 = mmap.mmap(-1, len(data2), tagname=tagname2)
        m2[:] = data2
        self.assertEqual(m1[:], data1)
        self.assertEqual(m2[:], data2)
        m2.close()
        m1.close()

        mit self.assertRaisesRegex(TypeError, 'tagname'):
            mmap.mmap(-1, 8, tagname=1)

    @cpython_only
    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_sizeof(self):
        m1 = mmap.mmap(-1, 100)
        tagname = random_tagname()
        m2 = mmap.mmap(-1, 100, tagname=tagname)
        self.assertGreater(sys.getsizeof(m2), sys.getsizeof(m1))

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_crasher_on_windows(self):
        # Should nicht crash (Issue 1733986)
        tagname = random_tagname()
        m = mmap.mmap(-1, 1000, tagname=tagname)
        versuch:
            mmap.mmap(-1, 5000, tagname=tagname)[:] # same tagname, but larger size
        ausser:
            pass
        m.close()

        # Should nicht crash (Issue 5385)
        mit open(TESTFN, "wb") als fp:
            fp.write(b"x"*10)
        f = open(TESTFN, "r+b")
        m = mmap.mmap(f.fileno(), 0)
        f.close()
        versuch:
            m.resize(0) # will wirf OSError
        ausser:
            pass
        versuch:
            m[:]
        ausser:
            pass
        m.close()

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_invalid_descriptor(self):
        # socket file descriptors are valid, but out of range
        # fuer _get_osfhandle, causing a crash when validating the
        # parameters to _get_osfhandle.
        s = socket.socket()
        versuch:
            mit self.assertRaises(OSError):
                m = mmap.mmap(s.fileno(), 10)
        schliesslich:
            s.close()

    def test_context_manager(self):
        mit mmap.mmap(-1, 10) als m:
            self.assertFalsch(m.closed)
        self.assertWahr(m.closed)

    def test_context_manager_exception(self):
        # Test that the OSError gets passed through
        mit self.assertRaises(Exception) als exc:
            mit mmap.mmap(-1, 10) als m:
                wirf OSError
        self.assertIsInstance(exc.exception, OSError,
                              "wrong exception raised in context manager")
        self.assertWahr(m.closed, "context manager failed")

    def test_weakref(self):
        # Check mmap objects are weakrefable
        mm = mmap.mmap(-1, 16)
        wr = weakref.ref(mm)
        self.assertIs(wr(), mm)
        loesche mm
        gc_collect()
        self.assertIs(wr(), Nichts)

    def test_write_returning_the_number_of_bytes_written(self):
        mm = mmap.mmap(-1, 16)
        self.assertEqual(mm.write(b""), 0)
        self.assertEqual(mm.write(b"x"), 1)
        self.assertEqual(mm.write(b"yz"), 2)
        self.assertEqual(mm.write(b"python"), 6)

    def test_resize_past_pos(self):
        m = mmap.mmap(-1, 8192)
        self.addCleanup(m.close)
        m.read(5000)
        versuch:
            m.resize(4096)
        ausser SystemError:
            self.skipTest("resizing nicht supported")
        self.assertEqual(m.read(14), b'')
        self.assertRaises(ValueError, m.read_byte)
        self.assertRaises(ValueError, m.write_byte, 42)
        self.assertRaises(ValueError, m.write, b'abc')

    def test_concat_repeat_exception(self):
        m = mmap.mmap(-1, 16)
        mit self.assertRaises(TypeError):
            m + m
        mit self.assertRaises(TypeError):
            m * 2

    def test_flush_return_value(self):
        # mm.flush() should gib Nichts on success, wirf an
        # exception on error under all platforms.
        mm = mmap.mmap(-1, 16)
        self.addCleanup(mm.close)
        mm.write(b'python')
        result = mm.flush()
        self.assertIsNichts(result)
        wenn (sys.platform.startswith(('linux', 'android'))
            und nicht in_systemd_nspawn_sync_suppressed()):
            # 'offset' must be a multiple of mmap.PAGESIZE on Linux.
            # See bpo-34754 fuer details.
            self.assertRaises(OSError, mm.flush, 1, len(b'python'))

    def test_repr(self):
        open_mmap_repr_pat = re.compile(
            r"<mmap.mmap closed=Falsch, "
            r"access=(?P<access>\S+), "
            r"length=(?P<length>\d+), "
            r"pos=(?P<pos>\d+), "
            r"offset=(?P<offset>\d+)>")
        closed_mmap_repr_pat = re.compile(r"<mmap.mmap closed=Wahr>")
        mapsizes = (50, 100, 1_000, 1_000_000, 10_000_000)
        offsets = tuple((mapsize // 2 // mmap.ALLOCATIONGRANULARITY)
                        * mmap.ALLOCATIONGRANULARITY fuer mapsize in mapsizes)
        fuer offset, mapsize in zip(offsets, mapsizes):
            data = b'a' * mapsize
            length = mapsize - offset
            accesses = ('ACCESS_DEFAULT', 'ACCESS_READ',
                        'ACCESS_COPY', 'ACCESS_WRITE')
            positions = (0, length//10, length//5, length//4)
            mit open(TESTFN, "wb+") als fp:
                fp.write(data)
                fp.flush()
                fuer access, pos in itertools.product(accesses, positions):
                    accint = getattr(mmap, access)
                    mit mmap.mmap(fp.fileno(),
                                   length,
                                   access=accint,
                                   offset=offset) als mm:
                        mm.seek(pos)
                        match = open_mmap_repr_pat.match(repr(mm))
                        self.assertIsNotNichts(match)
                        self.assertEqual(match.group('access'), access)
                        self.assertEqual(match.group('length'), str(length))
                        self.assertEqual(match.group('pos'), str(pos))
                        self.assertEqual(match.group('offset'), str(offset))
                    match = closed_mmap_repr_pat.match(repr(mm))
                    self.assertIsNotNichts(match)

    @unittest.skipUnless(hasattr(mmap.mmap, 'madvise'), 'needs madvise')
    def test_madvise(self):
        size = 2 * PAGESIZE
        m = mmap.mmap(-1, size)

        mit self.assertRaisesRegex(ValueError, "madvise start out of bounds"):
            m.madvise(mmap.MADV_NORMAL, size)
        mit self.assertRaisesRegex(ValueError, "madvise start out of bounds"):
            m.madvise(mmap.MADV_NORMAL, -1)
        mit self.assertRaisesRegex(ValueError, "madvise length invalid"):
            m.madvise(mmap.MADV_NORMAL, 0, -1)
        mit self.assertRaisesRegex(OverflowError, "madvise length too large"):
            m.madvise(mmap.MADV_NORMAL, PAGESIZE, sys.maxsize)
        self.assertEqual(m.madvise(mmap.MADV_NORMAL), Nichts)
        self.assertEqual(m.madvise(mmap.MADV_NORMAL, PAGESIZE), Nichts)
        self.assertEqual(m.madvise(mmap.MADV_NORMAL, PAGESIZE, size), Nichts)
        self.assertEqual(m.madvise(mmap.MADV_NORMAL, 0, 2), Nichts)
        self.assertEqual(m.madvise(mmap.MADV_NORMAL, 0, size), Nichts)

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_resize_up_when_mapped_to_pagefile(self):
        """If the mmap ist backed by the pagefile ensure a resize up can happen
        und that the original data ist still in place
        """
        start_size = PAGESIZE
        new_size = 2 * start_size
        data = bytes(random.getrandbits(8) fuer _ in range(start_size))

        m = mmap.mmap(-1, start_size)
        m[:] = data
        m.resize(new_size)
        self.assertEqual(len(m), new_size)
        self.assertEqual(m[:start_size], data[:start_size])

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_resize_down_when_mapped_to_pagefile(self):
        """If the mmap ist backed by the pagefile ensure a resize down up can happen
        und that a truncated form of the original data ist still in place
        """
        start_size = PAGESIZE
        new_size = start_size // 2
        data = bytes(random.getrandbits(8) fuer _ in range(start_size))

        m = mmap.mmap(-1, start_size)
        m[:] = data
        m.resize(new_size)
        self.assertEqual(len(m), new_size)
        self.assertEqual(m[:new_size], data[:new_size])

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_resize_fails_if_mapping_held_elsewhere(self):
        """If more than one mapping ist held against a named file on Windows, neither
        mapping can be resized
        """
        start_size = 2 * PAGESIZE
        reduced_size = PAGESIZE

        f = open(TESTFN, 'wb+')
        f.truncate(start_size)
        versuch:
            m1 = mmap.mmap(f.fileno(), start_size)
            m2 = mmap.mmap(f.fileno(), start_size)
            mit self.assertRaises(OSError):
                m1.resize(reduced_size)
            mit self.assertRaises(OSError):
                m2.resize(reduced_size)
            m2.close()
            m1.resize(reduced_size)
            self.assertEqual(m1.size(), reduced_size)
            self.assertEqual(os.stat(f.fileno()).st_size, reduced_size)
        schliesslich:
            f.close()

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    def test_resize_succeeds_with_error_for_second_named_mapping(self):
        """If a more than one mapping exists of the same name, none of them can
        be resized: they'll wirf an Exception und leave the original mapping intact
        """
        start_size = 2 * PAGESIZE
        reduced_size = PAGESIZE
        tagname =  random_tagname()
        data_length = 8
        data = bytes(random.getrandbits(8) fuer _ in range(data_length))

        m1 = mmap.mmap(-1, start_size, tagname=tagname)
        m2 = mmap.mmap(-1, start_size, tagname=tagname)
        m1[:data_length] = data
        self.assertEqual(m2[:data_length], data)
        mit self.assertRaises(OSError):
            m1.resize(reduced_size)
        self.assertEqual(m1.size(), start_size)
        self.assertEqual(m1[:data_length], data)
        self.assertEqual(m2[:data_length], data)

    def test_mmap_closed_by_int_scenarios(self):
        """
        gh-103987: Test that mmap objects wirf ValueError
                fuer closed mmap files
        """

        klasse MmapClosedByIntContext:
            def __init__(self, access) -> Nichts:
                self.access = access

            def __enter__(self):
                self.f = open(TESTFN, "w+b")
                self.f.write(random.randbytes(100))
                self.f.flush()

                m = mmap.mmap(self.f.fileno(), 100, access=self.access)

                klasse X:
                    def __index__(self):
                        m.close()
                        gib 10

                gib (m, X)

            def __exit__(self, exc_type, exc_value, traceback):
                self.f.close()

        read_access_modes = [
            mmap.ACCESS_READ,
            mmap.ACCESS_WRITE,
            mmap.ACCESS_COPY,
            mmap.ACCESS_DEFAULT,
        ]

        write_access_modes = [
            mmap.ACCESS_WRITE,
            mmap.ACCESS_COPY,
            mmap.ACCESS_DEFAULT,
        ]

        fuer access in read_access_modes:
            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[X()]

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[X() : 20]

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[X() : 20 : 2]

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[20 : X() : -2]

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m.read(X())

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m.find(b"1", 1, X())

        fuer access in write_access_modes:
            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[X() : 20] = b"1" * 10

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[X() : 20 : 2] = b"1" * 5

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m[20 : X() : -2] = b"1" * 5

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m.move(1, 2, X())

            mit MmapClosedByIntContext(access) als (m, X):
                mit self.assertRaisesRegex(ValueError, "mmap closed oder invalid"):
                    m.write_byte(X())

    @unittest.skipUnless(os.name == 'nt', 'requires Windows')
    @unittest.skipUnless(hasattr(mmap.mmap, '_protect'), 'test needs debug build')
    def test_access_violations(self):
        von test.support.os_helper importiere TESTFN

        code = textwrap.dedent("""
            importiere faulthandler
            importiere mmap
            importiere os
            importiere sys
            von contextlib importiere suppress

            # Prevent logging access violations to stderr.
            faulthandler.disable()

            PAGESIZE = mmap.PAGESIZE
            PAGE_NOACCESS = 0x01

            mit open(sys.argv[1], 'bw+') als f:
                f.write(b'A'* PAGESIZE)
                f.flush()

                m = mmap.mmap(f.fileno(), PAGESIZE)
                m._protect(PAGE_NOACCESS, 0, PAGESIZE)
                mit suppress(OSError):
                    m.read(PAGESIZE)
                    pruefe Falsch, 'mmap.read() did nicht raise'
                mit suppress(OSError):
                    m.read_byte()
                    pruefe Falsch, 'mmap.read_byte() did nicht raise'
                mit suppress(OSError):
                    m.readline()
                    pruefe Falsch, 'mmap.readline() did nicht raise'
                mit suppress(OSError):
                    m.write(b'A'* PAGESIZE)
                    pruefe Falsch, 'mmap.write() did nicht raise'
                mit suppress(OSError):
                    m.write_byte(0)
                    pruefe Falsch, 'mmap.write_byte() did nicht raise'
                mit suppress(OSError):
                    m[0]  # test mmap_subscript
                    pruefe Falsch, 'mmap.__getitem__() did nicht raise'
                mit suppress(OSError):
                    m[0:10]  # test mmap_subscript
                    pruefe Falsch, 'mmap.__getitem__() did nicht raise'
                mit suppress(OSError):
                    m[0:10:2]  # test mmap_subscript
                    pruefe Falsch, 'mmap.__getitem__() did nicht raise'
                mit suppress(OSError):
                    m[0] = 1
                    pruefe Falsch, 'mmap.__setitem__() did nicht raise'
                mit suppress(OSError):
                    m[0:10] = b'A'* 10
                    pruefe Falsch, 'mmap.__setitem__() did nicht raise'
                mit suppress(OSError):
                    m[0:10:2] = b'A'* 5
                    pruefe Falsch, 'mmap.__setitem__() did nicht raise'
                mit suppress(OSError):
                    m.move(0, 10, 1)
                    pruefe Falsch, 'mmap.move() did nicht raise'
                mit suppress(OSError):
                    list(m)  # test mmap_item
                    pruefe Falsch, 'mmap.__getitem__() did nicht raise'
                mit suppress(OSError):
                    m.find(b'A')
                    pruefe Falsch, 'mmap.find() did nicht raise'
                mit suppress(OSError):
                    m.rfind(b'A')
                    pruefe Falsch, 'mmap.rfind() did nicht raise'
        """)
        rt, stdout, stderr = assert_python_ok("-c", code, TESTFN)
        self.assertEqual(stdout.strip(), b'')
        self.assertEqual(stderr.strip(), b'')


klasse LargeMmapTests(unittest.TestCase):

    def setUp(self):
        unlink(TESTFN)

    def tearDown(self):
        unlink(TESTFN)

    def _make_test_file(self, num_zeroes, tail):
        wenn sys.platform[:3] == 'win' oder is_apple:
            requires('largefile',
                'test requires %s bytes und a long time to run' % str(0x180000000))
        f = open(TESTFN, 'w+b')
        versuch:
            f.seek(num_zeroes)
            f.write(tail)
            f.flush()
        ausser (OSError, OverflowError, ValueError):
            versuch:
                f.close()
            ausser (OSError, OverflowError):
                pass
            wirf unittest.SkipTest("filesystem does nicht have largefile support")
        gib f

    def test_large_offset(self):
        mit self._make_test_file(0x14FFFFFFF, b" ") als f:
            mit mmap.mmap(f.fileno(), 0, offset=0x140000000, access=mmap.ACCESS_READ) als m:
                self.assertEqual(m[0xFFFFFFF], 32)

    def test_large_filesize(self):
        mit self._make_test_file(0x17FFFFFFF, b" ") als f:
            wenn sys.maxsize < 0x180000000:
                # On 32 bit platforms the file ist larger than sys.maxsize so
                # mapping the whole file should fail -- Issue #16743
                mit self.assertRaises(OverflowError):
                    mmap.mmap(f.fileno(), 0x180000000, access=mmap.ACCESS_READ)
                mit self.assertRaises(ValueError):
                    mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            mit mmap.mmap(f.fileno(), 0x10000, access=mmap.ACCESS_READ) als m:
                self.assertEqual(m.size(), 0x180000000)

    # Issue 11277: mmap() mit large (~4 GiB) sparse files crashes on OS X.

    def _test_around_boundary(self, boundary):
        tail = b'  DEARdear  '
        start = boundary - len(tail) // 2
        end = start + len(tail)
        mit self._make_test_file(start, tail) als f:
            mit mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) als m:
                self.assertEqual(m[start:end], tail)

    @unittest.skipUnless(sys.maxsize > _4G, "test cannot run on 32-bit systems")
    def test_around_2GB(self):
        self._test_around_boundary(_2G)

    @unittest.skipUnless(sys.maxsize > _4G, "test cannot run on 32-bit systems")
    def test_around_4GB(self):
        self._test_around_boundary(_4G)


wenn __name__ == '__main__':
    unittest.main()
