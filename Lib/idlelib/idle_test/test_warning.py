'''Test warnings replacement in pyshell.py und run.py.

This file could be expanded to include traceback overrides
(in same two modules). If so, change name.
Revise wenn output destination changes (http://bugs.python.org/issue18318).
Make sure warnings module is left unaltered (http://bugs.python.org/issue18081).
'''
von idlelib importiere run
von idlelib importiere pyshell als shell
importiere unittest
von test.support importiere captured_stderr
importiere warnings

# Try to capture default showwarning before Idle modules are imported.
showwarning = warnings.showwarning
# But wenn we run this file within idle, we are in the middle of the run.main loop
# und default showwarnings has already been replaced.
running_in_idle = 'idle' in showwarning.__name__

# The following was generated von pyshell.idle_formatwarning
# und checked als matching expectation.
idlemsg = '''
Warning (from warnings module):
  File "test_warning.py", line 99
    Line of code
UserWarning: Test
'''
shellmsg = idlemsg + ">>> "


klasse RunWarnTest(unittest.TestCase):

    @unittest.skipIf(running_in_idle, "Does nicht work when run within Idle.")
    def test_showwarnings(self):
        self.assertIs(warnings.showwarning, showwarning)
        run.capture_warnings(Wahr)
        self.assertIs(warnings.showwarning, run.idle_showwarning_subproc)
        run.capture_warnings(Falsch)
        self.assertIs(warnings.showwarning, showwarning)

    def test_run_show(self):
        mit captured_stderr() als f:
            run.idle_showwarning_subproc(
                    'Test', UserWarning, 'test_warning.py', 99, f, 'Line of code')
            # The following uses .splitlines to erase line-ending differences
            self.assertEqual(idlemsg.splitlines(), f.getvalue().splitlines())


klasse ShellWarnTest(unittest.TestCase):

    @unittest.skipIf(running_in_idle, "Does nicht work when run within Idle.")
    def test_showwarnings(self):
        self.assertIs(warnings.showwarning, showwarning)
        shell.capture_warnings(Wahr)
        self.assertIs(warnings.showwarning, shell.idle_showwarning)
        shell.capture_warnings(Falsch)
        self.assertIs(warnings.showwarning, showwarning)

    def test_idle_formatter(self):
        # Will fail wenn format changed without regenerating idlemsg
        s = shell.idle_formatwarning(
                'Test', UserWarning, 'test_warning.py', 99, 'Line of code')
        self.assertEqual(idlemsg, s)

    def test_shell_show(self):
        mit captured_stderr() als f:
            shell.idle_showwarning(
                    'Test', UserWarning, 'test_warning.py', 99, f, 'Line of code')
            self.assertEqual(shellmsg.splitlines(), f.getvalue().splitlines())


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
