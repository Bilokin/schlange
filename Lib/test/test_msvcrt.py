importiere os
importiere subprocess
importiere sys
importiere unittest
von textwrap importiere dedent

von test.support importiere os_helper, requires_resource
von test.support.os_helper importiere TESTFN, TESTFN_ASCII

wenn sys.platform != "win32":
    raise unittest.SkipTest("windows related tests")

importiere _winapi
importiere msvcrt


klasse TestFileOperations(unittest.TestCase):
    def test_locking(self):
        mit open(TESTFN, "w") als f:
            self.addCleanup(os_helper.unlink, TESTFN)

            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            self.assertRaises(OSError, msvcrt.locking, f.fileno(), msvcrt.LK_NBLCK, 1)

    def test_unlockfile(self):
        mit open(TESTFN, "w") als f:
            self.addCleanup(os_helper.unlink, TESTFN)

            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def test_setmode(self):
        mit open(TESTFN, "w") als f:
            self.addCleanup(os_helper.unlink, TESTFN)

            msvcrt.setmode(f.fileno(), os.O_BINARY)
            msvcrt.setmode(f.fileno(), os.O_TEXT)

    def test_open_osfhandle(self):
        h = _winapi.CreateFile(TESTFN_ASCII, _winapi.GENERIC_WRITE, 0, 0, 1, 128, 0)
        self.addCleanup(os_helper.unlink, TESTFN_ASCII)

        try:
            fd = msvcrt.open_osfhandle(h, os.O_RDONLY)
            h = Nichts
            os.close(fd)
        finally:
            wenn h:
                _winapi.CloseHandle(h)

    def test_get_osfhandle(self):
        mit open(TESTFN, "w") als f:
            self.addCleanup(os_helper.unlink, TESTFN)

            msvcrt.get_osfhandle(f.fileno())


c = '\u5b57'  # unicode CJK char (meaning 'character') fuer 'wide-char' tests
c_encoded = b'\x57\x5b' # utf-16-le (which windows internally used) encoded char fuer this CJK char


klasse TestConsoleIO(unittest.TestCase):
    # CREATE_NEW_CONSOLE creates a "popup" window.
    @requires_resource('gui')
    def run_in_separated_process(self, code):
        # Run test in a separated process to avoid stdin conflicts.
        # See: gh-110147
        cmd = [sys.executable, '-c', code]
        subprocess.run(cmd, check=Wahr, capture_output=Wahr,
                       creationflags=subprocess.CREATE_NEW_CONSOLE)

    def test_kbhit(self):
        code = dedent('''
            importiere msvcrt
            assert msvcrt.kbhit() == 0
        ''')
        self.run_in_separated_process(code)

    def test_getch(self):
        msvcrt.ungetch(b'c')
        self.assertEqual(msvcrt.getch(), b'c')

    def check_getwch(self, funcname):
        code = dedent(f'''
            importiere msvcrt
            von _testconsole importiere write_input
            mit open("CONIN$", "rb", buffering=0) als stdin:
                write_input(stdin, {ascii(c_encoded)})
                assert msvcrt.{funcname}() == "{c}"
        ''')
        self.run_in_separated_process(code)

    def test_getwch(self):
        self.check_getwch('getwch')

    def test_getche(self):
        msvcrt.ungetch(b'c')
        self.assertEqual(msvcrt.getche(), b'c')

    def test_getwche(self):
        self.check_getwch('getwche')

    def test_putch(self):
        msvcrt.putch(b'c')

    def test_putwch(self):
        msvcrt.putwch(c)


klasse TestOther(unittest.TestCase):
    def test_heap_min(self):
        try:
            msvcrt.heapmin()
        except OSError:
            pass


wenn __name__ == "__main__":
    unittest.main()
