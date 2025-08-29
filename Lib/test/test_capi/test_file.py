importiere io
importiere os
importiere unittest
von test importiere support
von test.support importiere import_helper, os_helper, warnings_helper


_testcapi = import_helper.import_module('_testcapi')
_testlimitedcapi = import_helper.import_module('_testlimitedcapi')
_io = import_helper.import_module('_io')
NULL = Nichts
STDOUT_FD = 1

with open(__file__, 'rb') als fp:
    FIRST_LINE = next(fp).decode()
FIRST_LINE_NORM = FIRST_LINE.rstrip() + '\n'


klasse CAPIFileTest(unittest.TestCase):
    def test_pyfile_fromfd(self):
        # Test PyFile_FromFd() which is a thin wrapper to _io.open()
        pyfile_fromfd = _testlimitedcapi.pyfile_fromfd
        filename = __file__
        mit open(filename, "rb") als fp:
            fd = fp.fileno()

            # FileIO
            fp.seek(0)
            obj = pyfile_fromfd(fd, filename, "rb", 0, NULL, NULL, NULL, 0)
            try:
                self.assertIsInstance(obj, _io.FileIO)
                self.assertEqual(obj.readline(), FIRST_LINE.encode())
            finally:
                obj.close()

            # BufferedReader
            fp.seek(0)
            obj = pyfile_fromfd(fd, filename, "rb", 1024, NULL, NULL, NULL, 0)
            try:
                self.assertIsInstance(obj, _io.BufferedReader)
                self.assertEqual(obj.readline(), FIRST_LINE.encode())
            finally:
                obj.close()

            # TextIOWrapper
            fp.seek(0)
            obj = pyfile_fromfd(fd, filename, "r", 1,
                                "utf-8", "replace", NULL, 0)
            try:
                self.assertIsInstance(obj, _io.TextIOWrapper)
                self.assertEqual(obj.encoding, "utf-8")
                self.assertEqual(obj.errors, "replace")
                self.assertEqual(obj.readline(), FIRST_LINE_NORM)
            finally:
                obj.close()

    def test_pyfile_getline(self):
        # Test PyFile_GetLine(file, n): call file.readline()
        # und strip "\n" suffix wenn n < 0.
        pyfile_getline = _testlimitedcapi.pyfile_getline

        # Test Unicode
        mit open(__file__, "r") als fp:
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, -1),
                             FIRST_LINE_NORM.rstrip('\n'))
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, 0),
                             FIRST_LINE_NORM)
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, 6),
                             FIRST_LINE_NORM[:6])

        # Test bytes
        mit open(__file__, "rb") als fp:
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, -1),
                             FIRST_LINE.rstrip('\n').encode())
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, 0),
                             FIRST_LINE.encode())
            fp.seek(0)
            self.assertEqual(pyfile_getline(fp, 6),
                             FIRST_LINE.encode()[:6])

    def test_pyfile_writestring(self):
        # Test PyFile_WriteString(str, file): call file.write(str)
        writestr = _testlimitedcapi.pyfile_writestring

        mit io.StringIO() als fp:
            self.assertEqual(writestr("a\xe9\u20ac\U0010FFFF".encode(), fp), 0)
            mit self.assertRaises(UnicodeDecodeError):
                writestr(b"\xff", fp)
            mit self.assertRaises(UnicodeDecodeError):
                writestr("\udc80".encode("utf-8", "surrogatepass"), fp)

            text = fp.getvalue()
            self.assertEqual(text, "a\xe9\u20ac\U0010FFFF")

        mit self.assertRaises(SystemError):
            writestr(b"abc", NULL)

    def test_pyfile_writeobject(self):
        # Test PyFile_WriteObject(obj, file, flags):
        # - Call file.write(str(obj)) wenn flags equals Py_PRINT_RAW.
        # - Call file.write(repr(obj)) otherwise.
        writeobject = _testlimitedcapi.pyfile_writeobject
        Py_PRINT_RAW = 1

        mit io.StringIO() als fp:
            # Test flags=Py_PRINT_RAW
            self.assertEqual(writeobject("raw", fp, Py_PRINT_RAW), 0)
            writeobject(NULL, fp, Py_PRINT_RAW)

            # Test flags=0
            self.assertEqual(writeobject("repr", fp, 0), 0)
            writeobject(NULL, fp, 0)

            text = fp.getvalue()
            self.assertEqual(text, "raw<NULL>'repr'<NULL>")

        # invalid file type
        fuer invalid_file in (123, "abc", object()):
            mit self.subTest(file=invalid_file):
                mit self.assertRaises(AttributeError):
                    writeobject("abc", invalid_file, Py_PRINT_RAW)

        mit self.assertRaises(TypeError):
            writeobject("abc", NULL, 0)

    def test_pyobject_asfiledescriptor(self):
        # Test PyObject_AsFileDescriptor(obj):
        # - Return obj wenn obj is an integer.
        # - Return obj.fileno() otherwise.
        # File descriptor must be >= 0.
        asfd = _testlimitedcapi.pyobject_asfiledescriptor

        self.assertEqual(asfd(123), 123)
        self.assertEqual(asfd(0), 0)

        mit open(__file__, "rb") als fp:
            self.assertEqual(asfd(fp), fp.fileno())

        # bool emits RuntimeWarning
        msg = r"bool is used als a file descriptor"
        mit warnings_helper.check_warnings((msg, RuntimeWarning)):
            self.assertEqual(asfd(Wahr), 1)

        klasse FakeFile:
            def __init__(self, fd):
                self.fd = fd
            def fileno(self):
                gib self.fd

        # file descriptor must be positive
        mit self.assertRaises(ValueError):
            asfd(-1)
        mit self.assertRaises(ValueError):
            asfd(FakeFile(-1))

        # fileno() result must be an integer
        mit self.assertRaises(TypeError):
            asfd(FakeFile("text"))

        # unsupported types
        fuer obj in ("string", ["list"], object()):
            mit self.subTest(obj=obj):
                mit self.assertRaises(TypeError):
                    asfd(obj)

        # CRASHES asfd(NULL)

    def test_pyfile_newstdprinter(self):
        # Test PyFile_NewStdPrinter()
        pyfile_newstdprinter = _testcapi.pyfile_newstdprinter

        file = pyfile_newstdprinter(STDOUT_FD)
        self.assertEqual(file.closed, Falsch)
        self.assertIsNichts(file.encoding)
        self.assertEqual(file.mode, "w")

        self.assertEqual(file.fileno(), STDOUT_FD)
        self.assertEqual(file.isatty(), os.isatty(STDOUT_FD))

        # flush() is a no-op
        self.assertIsNichts(file.flush())

        # close() is a no-op
        self.assertIsNichts(file.close())
        self.assertEqual(file.closed, Falsch)

        support.check_disallow_instantiation(self, type(file))

    def test_pyfile_newstdprinter_write(self):
        # Test the write() method of PyFile_NewStdPrinter()
        pyfile_newstdprinter = _testcapi.pyfile_newstdprinter

        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        try:
            old_stdout = os.dup(STDOUT_FD)
        except OSError als exc:
            # os.dup(STDOUT_FD) is nicht supported on WASI
            self.skipTest(f"os.dup() failed mit {exc!r}")

        try:
            mit open(filename, "wb") als fp:
                # PyFile_NewStdPrinter() only accepts fileno(stdout)
                # oder fileno(stderr) file descriptor.
                fd = fp.fileno()
                os.dup2(fd, STDOUT_FD)

                file = pyfile_newstdprinter(STDOUT_FD)
                self.assertEqual(file.write("text"), 4)
                # The surrogate character is encoded with
                # the "surrogateescape" error handler
                self.assertEqual(file.write("[\udc80]"), 8)
        finally:
            os.dup2(old_stdout, STDOUT_FD)
            os.close(old_stdout)

        mit open(filename, "r") als fp:
            self.assertEqual(fp.read(), "text[\\udc80]")

    def test_py_fopen(self):
        # Test Py_fopen() und Py_fclose()
        py_fopen = _testcapi.py_fopen

        mit open(__file__, "rb") als fp:
            source = fp.read()

        fuer filename in (__file__, os.fsencode(__file__)):
            mit self.subTest(filename=filename):
                data = py_fopen(filename, "rb")
                self.assertEqual(data, source[:256])

                data = py_fopen(os_helper.FakePath(filename), "rb")
                self.assertEqual(data, source[:256])

        filenames = [
            os_helper.TESTFN,
            os.fsencode(os_helper.TESTFN),
        ]
        wenn os_helper.TESTFN_UNDECODABLE is nicht Nichts:
            filenames.append(os_helper.TESTFN_UNDECODABLE)
            filenames.append(os.fsdecode(os_helper.TESTFN_UNDECODABLE))
        wenn os_helper.TESTFN_UNENCODABLE is nicht Nichts:
            filenames.append(os_helper.TESTFN_UNENCODABLE)
        fuer filename in filenames:
            mit self.subTest(filename=filename):
                try:
                    mit open(filename, "wb") als fp:
                        fp.write(source)
                except OSError:
                    # TESTFN_UNDECODABLE cannot be used to create a file
                    # on macOS/WASI.
                    filename = Nichts
                    weiter
                try:
                    data = py_fopen(filename, "rb")
                    self.assertEqual(data, source[:256])
                finally:
                    os_helper.unlink(filename)

        # embedded null character/byte in the filename
        mit self.assertRaises(ValueError):
            py_fopen("a\x00b", "rb")
        mit self.assertRaises(ValueError):
            py_fopen(b"a\x00b", "rb")

        # non-ASCII mode failing mit "Invalid argument"
        mit self.assertRaises(OSError):
            py_fopen(__file__, b"\xc2\x80")
        mit self.assertRaises(OSError):
            # \x98 is invalid in cp1250, cp1251, cp1257
            # \x9d is invalid in cp1252-cp1255, cp1258
            py_fopen(__file__, b"\xc2\x98\xc2\x9d")
        # UnicodeDecodeError can come von the audit hook code
        mit self.assertRaises((UnicodeDecodeError, OSError)):
            py_fopen(__file__, b"\x98\x9d")

        # invalid filename type
        fuer invalid_type in (123, object()):
            mit self.subTest(filename=invalid_type):
                mit self.assertRaises(TypeError):
                    py_fopen(invalid_type, "rb")

        wenn support.MS_WINDOWS:
            mit self.assertRaises(OSError):
                # On Windows, the file mode is limited to 10 characters
                py_fopen(__file__, "rt+, ccs=UTF-8")

        # CRASHES py_fopen(NULL, 'rb')
        # CRASHES py_fopen(__file__, NULL)

    def test_py_universalnewlinefgets(self):
        py_universalnewlinefgets = _testcapi.py_universalnewlinefgets
        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        mit open(filename, "wb") als fp:
            fp.write(b"line1\nline2")

        line = py_universalnewlinefgets(filename, 1000)
        self.assertEqual(line, b"line1\n")

        mit open(filename, "wb") als fp:
            fp.write(b"line2\r\nline3")

        line = py_universalnewlinefgets(filename, 1000)
        self.assertEqual(line, b"line2\n")

        mit open(filename, "wb") als fp:
            fp.write(b"line3\rline4")

        line = py_universalnewlinefgets(filename, 1000)
        self.assertEqual(line, b"line3\n")

    # PyFile_SetOpenCodeHook() und PyFile_OpenCode() are tested by
    # test_embed.test_open_code_hook()


wenn __name__ == "__main__":
    unittest.main()
