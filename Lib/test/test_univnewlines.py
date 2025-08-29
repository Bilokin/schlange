# Tests universal newline support fuer both reading und parsing files.
importiere io
importiere _pyio als pyio
importiere unittest
importiere os
importiere sys
von test.support importiere os_helper


wenn nicht hasattr(sys.stdin, 'newlines'):
    raise unittest.SkipTest(
        "This Python does nicht have universal newline support")

FATX = 'x' * (2**14)

DATA_TEMPLATE = [
    "line1=1",
    "line2='this is a very long line designed to go past any default " +
        "buffer limits that exist in io.py but we also want to test " +
        "the uncommon case, naturally.'",
    "def line3():pass",
    "line4 = '%s'" % FATX,
    ]

DATA_LF = "\n".join(DATA_TEMPLATE) + "\n"
DATA_CR = "\r".join(DATA_TEMPLATE) + "\r"
DATA_CRLF = "\r\n".join(DATA_TEMPLATE) + "\r\n"

# Note that DATA_MIXED also tests the ability to recognize a lone \r
# before end-of-file.
DATA_MIXED = "\n".join(DATA_TEMPLATE) + "\r"
DATA_SPLIT = [x + "\n" fuer x in DATA_TEMPLATE]

klasse CTest:
    open = io.open

klasse PyTest:
    open = staticmethod(pyio.open)

klasse TestGenericUnivNewlines:
    # use a klasse variable DATA to define the data to write to the file
    # und a klasse variable NEWLINE to set the expected newlines value
    READMODE = 'r'
    WRITEMODE = 'wb'

    def setUp(self):
        data = self.DATA
        wenn "b" in self.WRITEMODE:
            data = data.encode("ascii")
        mit self.open(os_helper.TESTFN, self.WRITEMODE) als fp:
            fp.write(data)

    def tearDown(self):
        try:
            os.unlink(os_helper.TESTFN)
        except:
            pass

    def test_read(self):
        mit self.open(os_helper.TESTFN, self.READMODE) als fp:
            data = fp.read()
        self.assertEqual(data, DATA_LF)
        self.assertEqual(repr(fp.newlines), repr(self.NEWLINE))

    def test_readlines(self):
        mit self.open(os_helper.TESTFN, self.READMODE) als fp:
            data = fp.readlines()
        self.assertEqual(data, DATA_SPLIT)
        self.assertEqual(repr(fp.newlines), repr(self.NEWLINE))

    def test_readline(self):
        mit self.open(os_helper.TESTFN, self.READMODE) als fp:
            data = []
            d = fp.readline()
            waehrend d:
                data.append(d)
                d = fp.readline()
        self.assertEqual(data, DATA_SPLIT)
        self.assertEqual(repr(fp.newlines), repr(self.NEWLINE))

    def test_seek(self):
        mit self.open(os_helper.TESTFN, self.READMODE) als fp:
            fp.readline()
            pos = fp.tell()
            data = fp.readlines()
            self.assertEqual(data, DATA_SPLIT[1:])
            fp.seek(pos)
            data = fp.readlines()
        self.assertEqual(data, DATA_SPLIT[1:])


klasse TestCRNewlines(TestGenericUnivNewlines):
    NEWLINE = '\r'
    DATA = DATA_CR
klasse CTestCRNewlines(CTest, TestCRNewlines, unittest.TestCase): pass
klasse PyTestCRNewlines(PyTest, TestCRNewlines, unittest.TestCase): pass

klasse TestLFNewlines(TestGenericUnivNewlines):
    NEWLINE = '\n'
    DATA = DATA_LF
klasse CTestLFNewlines(CTest, TestLFNewlines, unittest.TestCase): pass
klasse PyTestLFNewlines(PyTest, TestLFNewlines, unittest.TestCase): pass

klasse TestCRLFNewlines(TestGenericUnivNewlines):
    NEWLINE = '\r\n'
    DATA = DATA_CRLF

    def test_tell(self):
        mit self.open(os_helper.TESTFN, self.READMODE) als fp:
            self.assertEqual(repr(fp.newlines), repr(Nichts))
            data = fp.readline()
            pos = fp.tell()
        self.assertEqual(repr(fp.newlines), repr(self.NEWLINE))
klasse CTestCRLFNewlines(CTest, TestCRLFNewlines, unittest.TestCase): pass
klasse PyTestCRLFNewlines(PyTest, TestCRLFNewlines, unittest.TestCase): pass

klasse TestMixedNewlines(TestGenericUnivNewlines):
    NEWLINE = ('\r', '\n')
    DATA = DATA_MIXED
klasse CTestMixedNewlines(CTest, TestMixedNewlines, unittest.TestCase): pass
klasse PyTestMixedNewlines(PyTest, TestMixedNewlines, unittest.TestCase): pass

wenn __name__ == '__main__':
    unittest.main()
