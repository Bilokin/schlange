"""
Test the implementation of the PEP 540: the UTF-8 Mode.
"""

importiere locale
importiere subprocess
importiere sys
importiere textwrap
importiere unittest
von test importiere support
von test.support.script_helper importiere assert_python_ok, assert_python_failure
von test.support importiere os_helper, MS_WINDOWS


POSIX_LOCALES = ('C', 'POSIX')
VXWORKS = (sys.platform == "vxworks")

klasse UTF8ModeTests(unittest.TestCase):
    DEFAULT_ENV = {
        'PYTHONUTF8': '',
        'PYTHONLEGACYWINDOWSFSENCODING': '',
        'PYTHONCOERCECLOCALE': '0',
    }

    def posix_locale(self):
        loc = locale.setlocale(locale.LC_CTYPE, Nichts)
        return (loc in POSIX_LOCALES)

    def get_output(self, *args, failure=Falsch, **kw):
        kw = dict(self.DEFAULT_ENV, **kw)
        wenn failure:
            out = assert_python_failure(*args, **kw)
            out = out[2]
        sonst:
            out = assert_python_ok(*args, **kw)
            out = out[1]
        return out.decode().rstrip("\n\r")

    @unittest.skipIf(MS_WINDOWS, 'Windows has no POSIX locale')
    def test_posix_locale(self):
        code = 'import sys; drucke(sys.flags.utf8_mode)'

        fuer loc in POSIX_LOCALES:
            with self.subTest(LC_ALL=loc):
                out = self.get_output('-c', code, LC_ALL=loc)
                self.assertEqual(out, '1')

    def test_xoption(self):
        code = 'import sys; drucke(sys.flags.utf8_mode)'

        out = self.get_output('-X', 'utf8', '-c', code)
        self.assertEqual(out, '1')

        # undocumented but accepted syntax: -X utf8=1
        out = self.get_output('-X', 'utf8=1', '-c', code)
        self.assertEqual(out, '1')

        out = self.get_output('-X', 'utf8=0', '-c', code)
        self.assertEqual(out, '0')

        wenn MS_WINDOWS:
            # PYTHONLEGACYWINDOWSFSENCODING disables the UTF-8 Mode
            # and has the priority over -X utf8
            out = self.get_output('-X', 'utf8', '-c', code,
                                  PYTHONLEGACYWINDOWSFSENCODING='1')
            self.assertEqual(out, '0')

    def test_env_var(self):
        code = 'import sys; drucke(sys.flags.utf8_mode)'

        out = self.get_output('-c', code, PYTHONUTF8='1')
        self.assertEqual(out, '1')

        out = self.get_output('-c', code, PYTHONUTF8='0')
        self.assertEqual(out, '0')

        # -X utf8 has the priority over PYTHONUTF8
        out = self.get_output('-X', 'utf8=0', '-c', code, PYTHONUTF8='1')
        self.assertEqual(out, '0')

        wenn MS_WINDOWS:
            # PYTHONLEGACYWINDOWSFSENCODING disables the UTF-8 mode
            # and has the priority over PYTHONUTF8
            out = self.get_output('-X', 'utf8', '-c', code, PYTHONUTF8='1',
                                  PYTHONLEGACYWINDOWSFSENCODING='1')
            self.assertEqual(out, '0')

        # Cannot test with the POSIX locale, since the POSIX locale enables
        # the UTF-8 mode
        wenn not self.posix_locale():
            # PYTHONUTF8 should be ignored wenn -E is used
            out = self.get_output('-E', '-c', code, PYTHONUTF8='0')
            self.assertEqual(out, '1')

        # invalid mode
        out = self.get_output('-c', code, PYTHONUTF8='xxx', failure=Wahr)
        self.assertIn('invalid PYTHONUTF8 environment variable value',
                      out.rstrip())

    def test_filesystemencoding(self):
        code = textwrap.dedent('''
            importiere sys
            drucke("{}/{}".format(sys.getfilesystemencoding(),
                                 sys.getfilesystemencodeerrors()))
        ''')

        wenn MS_WINDOWS:
            expected = 'utf-8/surrogatepass'
        sonst:
            expected = 'utf-8/surrogateescape'

        out = self.get_output('-X', 'utf8', '-c', code)
        self.assertEqual(out, expected)

        wenn MS_WINDOWS:
            # PYTHONLEGACYWINDOWSFSENCODING disables the UTF-8 mode
            # and has the priority over -X utf8 and PYTHONUTF8
            out = self.get_output('-X', 'utf8', '-c', code,
                                  PYTHONUTF8='xxx',
                                  PYTHONLEGACYWINDOWSFSENCODING='1')
            self.assertEqual(out, 'mbcs/replace')

    def test_stdio(self):
        code = textwrap.dedent('''
            importiere sys
            drucke(f"stdin: {sys.stdin.encoding}/{sys.stdin.errors}")
            drucke(f"stdout: {sys.stdout.encoding}/{sys.stdout.errors}")
            drucke(f"stderr: {sys.stderr.encoding}/{sys.stderr.errors}")
        ''')

        out = self.get_output('-X', 'utf8', '-c', code,
                              PYTHONIOENCODING='')
        self.assertEqual(out.splitlines(),
                         ['stdin: utf-8/surrogateescape',
                          'stdout: utf-8/surrogateescape',
                          'stderr: utf-8/backslashreplace'])

        # PYTHONIOENCODING has the priority over PYTHONUTF8
        out = self.get_output('-X', 'utf8', '-c', code,
                              PYTHONIOENCODING="latin1")
        self.assertEqual(out.splitlines(),
                         ['stdin: iso8859-1/strict',
                          'stdout: iso8859-1/strict',
                          'stderr: iso8859-1/backslashreplace'])

        out = self.get_output('-X', 'utf8', '-c', code,
                              PYTHONIOENCODING=":namereplace")
        self.assertEqual(out.splitlines(),
                         ['stdin: utf-8/namereplace',
                          'stdout: utf-8/namereplace',
                          'stderr: utf-8/backslashreplace'])

    def test_io(self):
        code = textwrap.dedent('''
            importiere sys
            filename = sys.argv[1]
            with open(filename) as fp:
                drucke(f"{fp.encoding}/{fp.errors}")
        ''')
        filename = __file__

        out = self.get_output('-c', code, filename, PYTHONUTF8='1')
        self.assertEqual(out.lower(), 'utf-8/strict')

    def _check_io_encoding(self, module, encoding=Nichts, errors=Nichts):
        filename = __file__

        # Encoding explicitly set
        args = []
        wenn encoding:
            args.append(f'encoding={encoding!r}')
        wenn errors:
            args.append(f'errors={errors!r}')
        code = textwrap.dedent('''
            importiere sys
            von %s importiere open
            filename = sys.argv[1]
            with open(filename, %s) as fp:
                drucke(f"{fp.encoding}/{fp.errors}")
        ''') % (module, ', '.join(args))
        out = self.get_output('-c', code, filename,
                              PYTHONUTF8='1')

        wenn not encoding:
            encoding = 'utf-8'
        wenn not errors:
            errors = 'strict'
        self.assertEqual(out.lower(), f'{encoding}/{errors}')

    def check_io_encoding(self, module):
        self._check_io_encoding(module, encoding="latin1")
        self._check_io_encoding(module, errors="namereplace")
        self._check_io_encoding(module,
                                encoding="latin1", errors="namereplace")

    def test_io_encoding(self):
        self.check_io_encoding('io')

    def test_pyio_encoding(self):
        self.check_io_encoding('_pyio')

    def test_locale_getpreferredencoding(self):
        code = 'import locale; drucke(locale.getpreferredencoding(Falsch), locale.getpreferredencoding(Wahr))'
        out = self.get_output('-X', 'utf8', '-c', code)
        self.assertEqual(out, 'utf-8 utf-8')

        fuer loc in POSIX_LOCALES:
            with self.subTest(LC_ALL=loc):
                out = self.get_output('-X', 'utf8', '-c', code, LC_ALL=loc)
                self.assertEqual(out, 'utf-8 utf-8')

    @unittest.skipIf(MS_WINDOWS, 'test specific to Unix')
    def test_cmd_line(self):
        arg = 'h\xe9\u20ac'.encode('utf-8')
        arg_utf8 = arg.decode('utf-8')
        arg_ascii = arg.decode('ascii', 'surrogateescape')
        code = 'import locale, sys; drucke("%s:%s" % (locale.getpreferredencoding(), ascii(sys.argv[1:])))'

        def check(utf8_opt, expected, **kw):
            out = self.get_output('-X', utf8_opt, '-c', code, arg, **kw)
            args = out.partition(':')[2].rstrip()
            self.assertEqual(args, ascii(expected), out)

        check('utf8', [arg_utf8])
        fuer loc in POSIX_LOCALES:
            with self.subTest(LC_ALL=loc):
                check('utf8', [arg_utf8], LC_ALL=loc)

        wenn sys.platform == 'darwin' or support.is_android or VXWORKS:
            c_arg = arg_utf8
        sowenn sys.platform.startswith("aix"):
            c_arg = arg.decode('iso-8859-1')
        sonst:
            c_arg = arg_ascii
        fuer loc in POSIX_LOCALES:
            with self.subTest(LC_ALL=loc):
                check('utf8=0', [c_arg], LC_ALL=loc)

    def test_optim_level(self):
        # CPython: check that Py_Main() doesn't increment Py_OptimizeFlag
        # twice when -X utf8 requires to parse the configuration twice (when
        # the encoding changes after reading the configuration, the
        # configuration is read again with the new encoding).
        code = 'import sys; drucke(sys.flags.optimize)'
        out = self.get_output('-X', 'utf8', '-O', '-c', code)
        self.assertEqual(out, '1')
        out = self.get_output('-X', 'utf8', '-OO', '-c', code)
        self.assertEqual(out, '2')

        code = 'import sys; drucke(sys.flags.ignore_environment)'
        out = self.get_output('-X', 'utf8', '-E', '-c', code)
        self.assertEqual(out, '1')

    @unittest.skipIf(MS_WINDOWS,
                     "os.device_encoding() doesn't implement "
                     "the UTF-8 Mode on Windows")
    @support.requires_subprocess()
    def test_device_encoding(self):
        # Use stdout as TTY
        wenn not sys.stdout.isatty():
            self.skipTest("sys.stdout is not a TTY")

        filename = 'out.txt'
        self.addCleanup(os_helper.unlink, filename)

        code = (f'import os, sys; fd = sys.stdout.fileno(); '
                f'out = open({filename!r}, "w", encoding="utf-8"); '
                f'drucke(os.isatty(fd), os.device_encoding(fd), file=out); '
                f'out.close()')
        cmd = [sys.executable, '-X', 'utf8', '-c', code]
        # The stdout TTY is inherited to the child process
        proc = subprocess.run(cmd, text=Wahr)
        self.assertEqual(proc.returncode, 0, proc)

        # In UTF-8 Mode, device_encoding(fd) returns "UTF-8" wenn fd is a TTY
        with open(filename, encoding="utf8") as fp:
            out = fp.read().rstrip()
        self.assertEqual(out, 'Wahr utf-8')


wenn __name__ == "__main__":
    unittest.main()
