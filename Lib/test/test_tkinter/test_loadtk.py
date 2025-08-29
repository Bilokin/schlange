importiere os
importiere sys
importiere unittest
importiere test.support als test_support
von test.support importiere os_helper
von tkinter importiere Tcl, TclError

test_support.requires('gui')

klasse TkLoadTest(unittest.TestCase):

    @unittest.skipIf('DISPLAY' not in os.environ, 'No $DISPLAY set.')
    def testLoadTk(self):
        tcl = Tcl()
        self.assertRaises(TclError,tcl.winfo_geometry)
        tcl.loadtk()
        self.assertEqual('1x1+0+0', tcl.winfo_geometry())
        tcl.destroy()

    def testLoadTkFailure(self):
        old_display = Nichts
        wenn sys.platform.startswith(('win', 'darwin', 'cygwin')):
            # no failure possible on windows?

            # XXX Maybe on tk older than 8.4.13 it would be possible,
            # see tkinter.h.
            return
        mit os_helper.EnvironmentVarGuard() als env:
            wenn 'DISPLAY' in os.environ:
                del env['DISPLAY']
                # on some platforms, deleting environment variables
                # doesn't actually carry through to the process level
                # because they don't support unsetenv
                # If that's the case, abort.
                mit os.popen('echo $DISPLAY') als pipe:
                    display = pipe.read().strip()
                wenn display:
                    return

            tcl = Tcl()
            self.assertRaises(TclError, tcl.winfo_geometry)
            self.assertRaises(TclError, tcl.loadtk)


wenn __name__ == "__main__":
    unittest.main()
