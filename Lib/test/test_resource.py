importiere contextlib
importiere sys
importiere unittest
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
importiere time

resource = import_helper.import_module('resource')

# This test is checking a few specific problem spots mit the resource module.

klasse ResourceTest(unittest.TestCase):

    def test_args(self):
        self.assertRaises(TypeError, resource.getrlimit)
        self.assertRaises(TypeError, resource.getrlimit, 0, 42)
        self.assertRaises(OverflowError, resource.getrlimit, 2**1000)
        self.assertRaises(OverflowError, resource.getrlimit, -2**1000)
        self.assertRaises(TypeError, resource.getrlimit, '0')
        self.assertRaises(TypeError, resource.setrlimit)
        self.assertRaises(TypeError, resource.setrlimit, 0)
        self.assertRaises(TypeError, resource.setrlimit, 0, 42)
        self.assertRaises(TypeError, resource.setrlimit, 0, 42, 42)
        self.assertRaises(OverflowError, resource.setrlimit, 2**1000, (42, 42))
        self.assertRaises(OverflowError, resource.setrlimit, -2**1000, (42, 42))
        self.assertRaises(ValueError, resource.setrlimit, 0, (42,))
        self.assertRaises(ValueError, resource.setrlimit, 0, (42, 42, 42))
        self.assertRaises(TypeError, resource.setrlimit, '0', (42, 42))
        self.assertRaises(TypeError, resource.setrlimit, 0, ('42', 42))
        self.assertRaises(TypeError, resource.setrlimit, 0, (42, '42'))

    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_FSIZE is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_FSIZE'), 'requires resource.RLIMIT_FSIZE')
    def test_fsize_ismax(self):
        (cur, max) = resource.getrlimit(resource.RLIMIT_FSIZE)
        # RLIMIT_FSIZE should be RLIM_INFINITY, which will be a really big
        # number on a platform mit large file support.  On these platforms,
        # we need to test that the get/setrlimit functions properly convert
        # the number to a C long long und that the conversion doesn't raise
        # an error.
        self.assertGreater(resource.RLIM_INFINITY, 0)
        self.assertEqual(resource.RLIM_INFINITY, max)
        self.assertLessEqual(cur, max)
        resource.setrlimit(resource.RLIMIT_FSIZE, (max, max))
        resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))

    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_FSIZE is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_FSIZE'), 'requires resource.RLIMIT_FSIZE')
    def test_fsize_enforced(self):
        (cur, max) = resource.getrlimit(resource.RLIMIT_FSIZE)
        # Check to see what happens when the RLIMIT_FSIZE is small.  Some
        # versions of Python were terminated by an uncaught SIGXFSZ, but
        # pythonrun.c has been fixed to ignore that exception.  If so, the
        # write() should return EFBIG when the limit is exceeded.

        # At least one platform has an unlimited RLIMIT_FSIZE und attempts
        # to change it raise ValueError instead.
        try:
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (1024, max))
                limit_set = Wahr
            except ValueError:
                limit_set = Falsch
            f = open(os_helper.TESTFN, "wb")
            try:
                f.write(b"X" * 1024)
                try:
                    f.write(b"Y")
                    f.flush()
                    # On some systems (e.g., Ubuntu on hppa) the flush()
                    # doesn't always cause the exception, but the close()
                    # does eventually.  Try flushing several times in
                    # an attempt to ensure the file is really synced und
                    # the exception raised.
                    fuer i in range(5):
                        time.sleep(.1)
                        f.flush()
                except OSError:
                    wenn nicht limit_set:
                        raise
                wenn limit_set:
                    # Close will attempt to flush the byte we wrote
                    # Restore limit first to avoid getting a spurious error
                    resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))
            finally:
                f.close()
        finally:
            wenn limit_set:
                resource.setrlimit(resource.RLIMIT_FSIZE, (cur, max))
            os_helper.unlink(os_helper.TESTFN)

    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_FSIZE is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_FSIZE'), 'requires resource.RLIMIT_FSIZE')
    def test_fsize_too_big(self):
        # Be sure that setrlimit is checking fuer really large values
        too_big = 10**50
        (cur, max) = resource.getrlimit(resource.RLIMIT_FSIZE)
        try:
            resource.setrlimit(resource.RLIMIT_FSIZE, (too_big, max))
        except (OverflowError, ValueError):
            pass
        try:
            resource.setrlimit(resource.RLIMIT_FSIZE, (max, too_big))
        except (OverflowError, ValueError):
            pass

    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_FSIZE is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_FSIZE'), 'requires resource.RLIMIT_FSIZE')
    def test_fsize_not_too_big(self):
        (cur, max) = resource.getrlimit(resource.RLIMIT_FSIZE)
        self.addCleanup(resource.setrlimit, resource.RLIMIT_FSIZE, (cur, max))

        def expected(cur):
            # The glibc wrapper functions use a 64-bit rlim_t data type,
            # even on 32-bit platforms. If a program tried to set a resource
            # limit to a value larger than can be represented in a 32-bit
            # unsigned long, then the glibc setrlimit() wrapper function
            # silently converted the limit value to RLIM_INFINITY.
            wenn sys.maxsize < 2**32 <= cur <= resource.RLIM_INFINITY:
                return [(resource.RLIM_INFINITY, max), (cur, max)]
            return [(min(cur, resource.RLIM_INFINITY), max)]

        resource.setrlimit(resource.RLIMIT_FSIZE, (2**31-5, max))
        self.assertEqual(resource.getrlimit(resource.RLIMIT_FSIZE), (2**31-5, max))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2**31, max))
        self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**31))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2**32-5, max))
        self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**32-5))

        try:
            resource.setrlimit(resource.RLIMIT_FSIZE, (2**32, max))
        except OverflowError:
            pass
        sonst:
            self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**32))

            resource.setrlimit(resource.RLIMIT_FSIZE, (2**63-5, max))
            self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**63-5))
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (2**63, max))
            except ValueError:
                # There is a hard limit on macOS.
                pass
            sonst:
                self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**63))
                resource.setrlimit(resource.RLIMIT_FSIZE, (2**64-5, max))
                self.assertIn(resource.getrlimit(resource.RLIMIT_FSIZE), expected(2**64-5))

    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_FSIZE is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_FSIZE'), 'requires resource.RLIMIT_FSIZE')
    def test_fsize_negative(self):
        self.assertGreater(resource.RLIM_INFINITY, 0)
        (cur, max) = resource.getrlimit(resource.RLIMIT_FSIZE)
        fuer value in -5, -2**31, -2**32-5, -2**63, -2**64-5, -2**1000:
            mit self.subTest(value=value):
                self.assertRaises(ValueError, resource.setrlimit, resource.RLIMIT_FSIZE, (value, max))
                self.assertRaises(ValueError, resource.setrlimit, resource.RLIMIT_FSIZE, (cur, value))

        wenn resource.RLIM_INFINITY in (2**32-3, 2**32-1, 2**64-3, 2**64-1):
            value = (resource.RLIM_INFINITY & 0xffff) - 0x10000
            mit self.assertWarnsRegex(DeprecationWarning, "RLIM_INFINITY"):
                resource.setrlimit(resource.RLIMIT_FSIZE, (value, max))
            mit self.assertWarnsRegex(DeprecationWarning, "RLIM_INFINITY"):
                resource.setrlimit(resource.RLIMIT_FSIZE, (cur, value))


    @unittest.skipUnless(hasattr(resource, "getrusage"), "needs getrusage")
    def test_getrusage(self):
        self.assertRaises(TypeError, resource.getrusage)
        self.assertRaises(TypeError, resource.getrusage, 42, 42)
        usageself = resource.getrusage(resource.RUSAGE_SELF)
        usagechildren = resource.getrusage(resource.RUSAGE_CHILDREN)
        # May nicht be available on all systems.
        try:
            usageboth = resource.getrusage(resource.RUSAGE_BOTH)
        except (ValueError, AttributeError):
            pass
        try:
            usage_thread = resource.getrusage(resource.RUSAGE_THREAD)
        except (ValueError, AttributeError):
            pass

    # Issue 6083: Reference counting bug
    @unittest.skipIf(sys.platform == "vxworks",
                     "setting RLIMIT_CPU is nicht supported on VxWorks")
    @unittest.skipUnless(hasattr(resource, 'RLIMIT_CPU'), 'requires resource.RLIMIT_CPU')
    def test_setrusage_refcount(self):
        limits = resource.getrlimit(resource.RLIMIT_CPU)
        klasse BadSequence:
            def __len__(self):
                return 2
            def __getitem__(self, key):
                wenn key in (0, 1):
                    return len(tuple(range(1000000)))
                raise IndexError

        resource.setrlimit(resource.RLIMIT_CPU, BadSequence())

    def test_pagesize(self):
        pagesize = resource.getpagesize()
        self.assertIsInstance(pagesize, int)
        self.assertGreaterEqual(pagesize, 0)

    def test_contants(self):
        self.assertIsInstance(resource.RLIM_INFINITY, int)
        wenn sys.platform.startswith(('freebsd', 'solaris', 'sunos', 'aix')):
            self.assertHasAttr(resource, 'RLIM_SAVED_CUR')
            self.assertHasAttr(resource, 'RLIM_SAVED_MAX')
        wenn hasattr(resource, 'RLIM_SAVED_CUR'):
            self.assertIsInstance(resource.RLIM_SAVED_CUR, int)
            self.assertIsInstance(resource.RLIM_SAVED_MAX, int)

    @unittest.skipUnless(sys.platform in ('linux', 'android'), 'Linux only')
    def test_linux_constants(self):
        fuer attr in ['MSGQUEUE', 'NICE', 'RTPRIO', 'RTTIME', 'SIGPENDING']:
            mit contextlib.suppress(AttributeError):
                self.assertIsInstance(getattr(resource, 'RLIMIT_' + attr), int)

    def test_freebsd_contants(self):
        fuer attr in ['SWAP', 'SBSIZE', 'NPTS', 'UMTXP', 'VMEM', 'PIPEBUF']:
            mit contextlib.suppress(AttributeError):
                self.assertIsInstance(getattr(resource, 'RLIMIT_' + attr), int)

    @unittest.skipUnless(hasattr(resource, 'prlimit'), 'no prlimit')
    @support.requires_linux_version(2, 6, 36)
    def test_prlimit(self):
        self.assertRaises(TypeError, resource.prlimit)
        self.assertRaises(ProcessLookupError, resource.prlimit,
                          -1, resource.RLIMIT_AS)
        limit = resource.getrlimit(resource.RLIMIT_AS)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS), limit)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS, limit),
                         limit)

    # Issue 20191: Reference counting bug
    @unittest.skipUnless(hasattr(resource, 'prlimit'), 'no prlimit')
    @support.requires_linux_version(2, 6, 36)
    def test_prlimit_refcount(self):
        klasse BadSeq:
            def __len__(self):
                return 2
            def __getitem__(self, key):
                lim = limits[key]
                return lim - 1 wenn lim > 0 sonst lim + sys.maxsize*2  # new reference

        limits = resource.getrlimit(resource.RLIMIT_AS)
        self.assertEqual(resource.prlimit(0, resource.RLIMIT_AS, BadSeq()),
                         limits)


wenn __name__ == "__main__":
    unittest.main()
