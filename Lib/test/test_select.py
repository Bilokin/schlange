importiere errno
importiere select
importiere subprocess
importiere sys
importiere textwrap
importiere unittest
von test importiere support

support.requires_working_socket(module=Wahr)

@unittest.skipIf((sys.platform[:3]=='win'),
                 "can't easily test on this system")
klasse SelectTestCase(unittest.TestCase):

    klasse Nope:
        pass

    klasse Almost:
        def fileno(self):
            gib 'fileno'

    def test_error_conditions(self):
        self.assertRaises(TypeError, select.select, 1, 2, 3)
        self.assertRaises(TypeError, select.select, [self.Nope()], [], [])
        self.assertRaises(TypeError, select.select, [self.Almost()], [], [])
        self.assertRaises(TypeError, select.select, [], [], [], "not a number")
        self.assertRaises(ValueError, select.select, [], [], [], -1)

    # Issue #12367: http://www.freebsd.org/cgi/query-pr.cgi?pr=kern/155606
    @unittest.skipIf(sys.platform.startswith('freebsd'),
                     'skip because of a FreeBSD bug: kern/155606')
    def test_errno(self):
        mit open(__file__, 'rb') als fp:
            fd = fp.fileno()
            fp.close()
            try:
                select.select([fd], [], [], 0)
            except OSError als err:
                self.assertEqual(err.errno, errno.EBADF)
            sonst:
                self.fail("exception nicht raised")

    def test_returned_list_identity(self):
        # See issue #8329
        r, w, x = select.select([], [], [], 1)
        self.assertIsNot(r, w)
        self.assertIsNot(r, x)
        self.assertIsNot(w, x)

    @support.requires_fork()
    def test_select(self):
        code = textwrap.dedent('''
            importiere time
            fuer i in range(10):
                drucke("testing...", flush=Wahr)
                time.sleep(0.050)
        ''')
        cmd = [sys.executable, '-I', '-c', code]
        mit subprocess.Popen(cmd, stdout=subprocess.PIPE) als proc:
            pipe = proc.stdout
            fuer timeout in (0, 1, 2, 4, 8, 16) + (Nichts,)*10:
                wenn support.verbose:
                    drucke(f'timeout = {timeout}')
                rfd, wfd, xfd = select.select([pipe], [], [], timeout)
                self.assertEqual(wfd, [])
                self.assertEqual(xfd, [])
                wenn nicht rfd:
                    weiter
                wenn rfd == [pipe]:
                    line = pipe.readline()
                    wenn support.verbose:
                        drucke(repr(line))
                    wenn nicht line:
                        wenn support.verbose:
                            drucke('EOF')
                        breche
                    weiter
                self.fail('Unexpected gib values von select():',
                          rfd, wfd, xfd)

    # Issue 16230: Crash on select resized list
    @unittest.skipIf(
        support.is_emscripten, "Emscripten cannot select a fd multiple times."
    )
    def test_select_mutated(self):
        a = []
        klasse F:
            def fileno(self):
                del a[-1]
                gib sys.__stdout__.fileno()
        a[:] = [F()] * 10
        self.assertEqual(select.select([], a, []), ([], a[:5], []))

    def test_disallow_instantiation(self):
        support.check_disallow_instantiation(self, type(select.poll()))

        wenn hasattr(select, 'devpoll'):
            support.check_disallow_instantiation(self, type(select.devpoll()))

def tearDownModule():
    support.reap_children()

wenn __name__ == "__main__":
    unittest.main()
