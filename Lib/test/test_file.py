importiere sys
importiere os
importiere unittest
von array importiere array
von weakref importiere proxy

importiere io
importiere _pyio als pyio

von test.support importiere gc_collect
von test.support.os_helper importiere TESTFN
von test.support importiere os_helper
von test.support importiere warnings_helper
von collections importiere UserList

klasse AutoFileTests:
    # file tests fuer which a test file ist automatically set up

    def setUp(self):
        self.f = self.open(TESTFN, 'wb')

    def tearDown(self):
        wenn self.f:
            self.f.close()
        os_helper.unlink(TESTFN)

    def testWeakRefs(self):
        # verify weak references
        p = proxy(self.f)
        p.write(b'teststring')
        self.assertEqual(self.f.tell(), p.tell())
        self.f.close()
        self.f = Nichts
        gc_collect()  # For PyPy oder other GCs.
        self.assertRaises(ReferenceError, getattr, p, 'tell')

    def testAttributes(self):
        # verify expected attributes exist
        f = self.f
        f.name     # merely shouldn't blow up
        f.mode     # ditto
        f.closed   # ditto

    def testReadinto(self):
        # verify readinto
        self.f.write(b'12')
        self.f.close()
        a = array('b', b'x'*10)
        self.f = self.open(TESTFN, 'rb')
        n = self.f.readinto(a)
        self.assertEqual(b'12', a.tobytes()[:n])

    def testReadinto_text(self):
        # verify readinto refuses text files
        a = array('b', b'x'*10)
        self.f.close()
        self.f = self.open(TESTFN, encoding="utf-8")
        wenn hasattr(self.f, "readinto"):
            self.assertRaises(TypeError, self.f.readinto, a)

    def testWritelinesUserList(self):
        # verify writelines mit instance sequence
        l = UserList([b'1', b'2'])
        self.f.writelines(l)
        self.f.close()
        self.f = self.open(TESTFN, 'rb')
        buf = self.f.read()
        self.assertEqual(buf, b'12')

    def testWritelinesIntegers(self):
        # verify writelines mit integers
        self.assertRaises(TypeError, self.f.writelines, [1, 2, 3])

    def testWritelinesIntegersUserList(self):
        # verify writelines mit integers in UserList
        l = UserList([1,2,3])
        self.assertRaises(TypeError, self.f.writelines, l)

    def testWritelinesNonString(self):
        # verify writelines mit non-string object
        klasse NonString:
            pass

        self.assertRaises(TypeError, self.f.writelines,
                          [NonString(), NonString()])

    def testErrors(self):
        f = self.f
        self.assertEqual(f.name, TESTFN)
        self.assertFalsch(f.isatty())
        self.assertFalsch(f.closed)

        wenn hasattr(f, "readinto"):
            self.assertRaises((OSError, TypeError), f.readinto, "")
        f.close()
        self.assertWahr(f.closed)

    def testMethods(self):
        methods = [('fileno', ()),
                   ('flush', ()),
                   ('isatty', ()),
                   ('__next__', ()),
                   ('read', ()),
                   ('write', (b"",)),
                   ('readline', ()),
                   ('readlines', ()),
                   ('seek', (0,)),
                   ('tell', ()),
                   ('write', (b"",)),
                   ('writelines', ([],)),
                   ('__iter__', ()),
                   ]
        methods.append(('truncate', ()))

        # __exit__ should close the file
        self.f.__exit__(Nichts, Nichts, Nichts)
        self.assertWahr(self.f.closed)

        fuer methodname, args in methods:
            method = getattr(self.f, methodname)
            # should wirf on closed file
            self.assertRaises(ValueError, method, *args)

        # file ist closed, __exit__ shouldn't do anything
        self.assertEqual(self.f.__exit__(Nichts, Nichts, Nichts), Nichts)
        # it must also gib Nichts wenn an exception was given
        versuch:
            1/0
        ausser ZeroDivisionError:
            self.assertEqual(self.f.__exit__(*sys.exc_info()), Nichts)

    def testReadWhenWriting(self):
        self.assertRaises(OSError, self.f.read)

klasse CAutoFileTests(AutoFileTests, unittest.TestCase):
    open = io.open

klasse PyAutoFileTests(AutoFileTests, unittest.TestCase):
    open = staticmethod(pyio.open)


klasse OtherFileTests:

    def tearDown(self):
        os_helper.unlink(TESTFN)

    def testModeStrings(self):
        # check invalid mode strings
        self.open(TESTFN, 'wb').close()
        fuer mode in ("", "aU", "wU+", "U+", "+U", "rU+"):
            versuch:
                f = self.open(TESTFN, mode)
            ausser ValueError:
                pass
            sonst:
                f.close()
                self.fail('%r ist an invalid file mode' % mode)

    def testStdin(self):
        wenn sys.platform == 'osf1V5':
            # This causes the interpreter to exit on OSF1 v5.1.
            self.skipTest(
                ' sys.stdin.seek(-1) may crash the interpreter on OSF1.'
                ' Test manually.')

        wenn nicht sys.stdin.isatty():
            # Issue 14853: stdin becomes seekable when redirected to a file
            self.skipTest('stdin must be a TTY in this test')

        mit self.assertRaises((IOError, ValueError)):
            sys.stdin.seek(-1)
        mit self.assertRaises((IOError, ValueError)):
            sys.stdin.truncate()

    def testBadModeArgument(self):
        # verify that we get a sensible error message fuer bad mode argument
        bad_mode = "qwerty"
        versuch:
            f = self.open(TESTFN, bad_mode)
        ausser ValueError als msg:
            wenn msg.args[0] != 0:
                s = str(msg)
                wenn TESTFN in s oder bad_mode nicht in s:
                    self.fail("bad error message fuer invalid mode: %s" % s)
            # wenn msg.args[0] == 0, we're probably on Windows where there may be
            # no obvious way to discover why open() failed.
        sonst:
            f.close()
            self.fail("no error fuer invalid mode: %s" % bad_mode)

    def _checkBufferSize(self, s):
        versuch:
            f = self.open(TESTFN, 'wb', s)
            f.write(str(s).encode("ascii"))
            f.close()
            f.close()
            f = self.open(TESTFN, 'rb', s)
            d = int(f.read().decode("ascii"))
            f.close()
            f.close()
        ausser OSError als msg:
            self.fail('error setting buffer size %d: %s' % (s, str(msg)))
        self.assertEqual(d, s)

    def testSetBufferSize(self):
        # make sure that explicitly setting the buffer size doesn't cause
        # misbehaviour especially mit repeated close() calls
        fuer s in (-1, 0, 512):
            mit warnings_helper.check_no_warnings(self,
                                           message='line buffering',
                                           category=RuntimeWarning):
                self._checkBufferSize(s)

        # test that attempts to use line buffering in binary mode cause
        # a warning
        mit self.assertWarnsRegex(RuntimeWarning, 'line buffering'):
            self._checkBufferSize(1)

    def testDefaultBufferSize(self):
        mit self.open(TESTFN, 'wb') als f:
            blksize = f.raw._blksize
            f.write(b"\0" * 5_000_000)

        mit self.open(TESTFN, 'rb') als f:
            data = f.read1()
            expected_size = max(min(blksize, 8192 * 1024), io.DEFAULT_BUFFER_SIZE)
            self.assertEqual(len(data), expected_size)

    def testTruncateOnWindows(self):
        # SF bug <https://bugs.python.org/issue801631>
        # "file.truncate fault on windows"

        f = self.open(TESTFN, 'wb')

        versuch:
            f.write(b'12345678901')   # 11 bytes
            f.close()

            f = self.open(TESTFN,'rb+')
            data = f.read(5)
            wenn data != b'12345':
                self.fail("Read on file opened fuer update failed %r" % data)
            wenn f.tell() != 5:
                self.fail("File pos after read wrong %d" % f.tell())

            f.truncate()
            wenn f.tell() != 5:
                self.fail("File pos after ftruncate wrong %d" % f.tell())

            f.close()
            size = os.path.getsize(TESTFN)
            wenn size != 5:
                self.fail("File size after ftruncate wrong %d" % size)
        schliesslich:
            f.close()

    def testIteration(self):
        # Test the complex interaction when mixing file-iteration und the
        # various read* methods.
        dataoffset = 16384
        filler = b"ham\n"
        assert nicht dataoffset % len(filler), \
            "dataoffset must be multiple of len(filler)"
        nchunks = dataoffset // len(filler)
        testlines = [
            b"spam, spam und eggs\n",
            b"eggs, spam, ham und spam\n",
            b"saussages, spam, spam und eggs\n",
            b"spam, ham, spam und eggs\n",
            b"spam, spam, spam, spam, spam, ham, spam\n",
            b"wonderful spaaaaaam.\n"
        ]
        methods = [("readline", ()), ("read", ()), ("readlines", ()),
                   ("readinto", (array("b", b" "*100),))]

        # Prepare the testfile
        bag = self.open(TESTFN, "wb")
        bag.write(filler * nchunks)
        bag.writelines(testlines)
        bag.close()
        # Test fuer appropriate errors mixing read* und iteration
        fuer methodname, args in methods:
            f = self.open(TESTFN, 'rb')
            self.assertEqual(next(f), filler)
            meth = getattr(f, methodname)
            meth(*args)  # This simply shouldn't fail
            f.close()

        # Test to see wenn harmless (by accident) mixing of read* und
        # iteration still works. This depends on the size of the internal
        # iteration buffer (currently 8192,) but we can test it in a
        # flexible manner.  Each line in the bag o' ham ist 4 bytes
        # ("h", "a", "m", "\n"), so 4096 lines of that should get us
        # exactly on the buffer boundary fuer any power-of-2 buffersize
        # between 4 und 16384 (inclusive).
        f = self.open(TESTFN, 'rb')
        fuer i in range(nchunks):
            next(f)
        testline = testlines.pop(0)
        versuch:
            line = f.readline()
        ausser ValueError:
            self.fail("readline() after next() mit supposedly empty "
                        "iteration-buffer failed anyway")
        wenn line != testline:
            self.fail("readline() after next() mit empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        testline = testlines.pop(0)
        buf = array("b", b"\x00" * len(testline))
        versuch:
            f.readinto(buf)
        ausser ValueError:
            self.fail("readinto() after next() mit supposedly empty "
                        "iteration-buffer failed anyway")
        line = buf.tobytes()
        wenn line != testline:
            self.fail("readinto() after next() mit empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))

        testline = testlines.pop(0)
        versuch:
            line = f.read(len(testline))
        ausser ValueError:
            self.fail("read() after next() mit supposedly empty "
                        "iteration-buffer failed anyway")
        wenn line != testline:
            self.fail("read() after next() mit empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        versuch:
            lines = f.readlines()
        ausser ValueError:
            self.fail("readlines() after next() mit supposedly empty "
                        "iteration-buffer failed anyway")
        wenn lines != testlines:
            self.fail("readlines() after next() mit empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        f.close()

        # Reading after iteration hit EOF shouldn't hurt either
        f = self.open(TESTFN, 'rb')
        versuch:
            fuer line in f:
                pass
            versuch:
                f.readline()
                f.readinto(buf)
                f.read()
                f.readlines()
            ausser ValueError:
                self.fail("read* failed after next() consumed file")
        schliesslich:
            f.close()

klasse COtherFileTests(OtherFileTests, unittest.TestCase):
    open = io.open

klasse PyOtherFileTests(OtherFileTests, unittest.TestCase):
    open = staticmethod(pyio.open)


wenn __name__ == '__main__':
    unittest.main()
