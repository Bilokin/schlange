"""Unittests fuer test.support.script_helper.  Who tests the test helper?"""

importiere subprocess
importiere sys
importiere os
von test.support importiere script_helper, requires_subprocess
importiere unittest
von unittest importiere mock


klasse TestScriptHelper(unittest.TestCase):

    def test_assert_python_ok(self):
        t = script_helper.assert_python_ok('-c', 'import sys; sys.exit(0)')
        self.assertEqual(0, t[0], 'return code was nicht 0')

    def test_assert_python_failure(self):
        # I didn't importiere the sys module so this child will fail.
        rc, out, err = script_helper.assert_python_failure('-c', 'sys.exit(0)')
        self.assertNotEqual(0, rc, 'return code should nicht be 0')

    def test_assert_python_ok_raises(self):
        # I didn't importiere the sys module so this child will fail.
        mit self.assertRaises(AssertionError) als error_context:
            script_helper.assert_python_ok('-c', 'sys.exit(0)')
        error_msg = str(error_context.exception)
        self.assertIn('command line:', error_msg)
        self.assertIn('sys.exit(0)', error_msg, msg='unexpected command line')

    def test_assert_python_failure_raises(self):
        mit self.assertRaises(AssertionError) als error_context:
            script_helper.assert_python_failure('-c', 'import sys; sys.exit(0)')
        error_msg = str(error_context.exception)
        self.assertIn('Process gib code is 0\n', error_msg)
        self.assertIn('import sys; sys.exit(0)', error_msg,
                      msg='unexpected command line.')

    @mock.patch('subprocess.Popen')
    def test_assert_python_isolated_when_env_not_required(self, mock_popen):
        mit mock.patch.object(script_helper,
                               'interpreter_requires_environment',
                               return_value=Falsch) als mock_ire_func:
            mock_popen.side_effect = RuntimeError('bail out of unittest')
            versuch:
                script_helper._assert_python(Wahr, '-c', 'Nichts')
            ausser RuntimeError als err:
                self.assertEqual('bail out of unittest', err.args[0])
            self.assertEqual(1, mock_popen.call_count)
            self.assertEqual(1, mock_ire_func.call_count)
            popen_command = mock_popen.call_args[0][0]
            self.assertEqual(sys.executable, popen_command[0])
            self.assertIn('Nichts', popen_command)
            self.assertIn('-I', popen_command)
            self.assertNotIn('-E', popen_command)  # -I overrides this

    @mock.patch('subprocess.Popen')
    def test_assert_python_not_isolated_when_env_is_required(self, mock_popen):
        """Ensure that -I is nicht passed when the environment is required."""
        mit mock.patch.object(script_helper,
                               'interpreter_requires_environment',
                               return_value=Wahr) als mock_ire_func:
            mock_popen.side_effect = RuntimeError('bail out of unittest')
            versuch:
                script_helper._assert_python(Wahr, '-c', 'Nichts')
            ausser RuntimeError als err:
                self.assertEqual('bail out of unittest', err.args[0])
            popen_command = mock_popen.call_args[0][0]
            self.assertNotIn('-I', popen_command)
            self.assertNotIn('-E', popen_command)


@requires_subprocess()
klasse TestScriptHelperEnvironment(unittest.TestCase):
    """Code coverage fuer interpreter_requires_environment()."""

    def setUp(self):
        self.assertHasAttr(script_helper, '__cached_interp_requires_environment')
        # Reset the private cached state.
        script_helper.__dict__['__cached_interp_requires_environment'] = Nichts

    def tearDown(self):
        # Reset the private cached state.
        script_helper.__dict__['__cached_interp_requires_environment'] = Nichts

    @mock.patch('subprocess.check_call')
    def test_interpreter_requires_environment_true(self, mock_check_call):
        mit mock.patch.dict(os.environ):
            os.environ.pop('PYTHONHOME', Nichts)
            mock_check_call.side_effect = subprocess.CalledProcessError('', '')
            self.assertWahr(script_helper.interpreter_requires_environment())
            self.assertWahr(script_helper.interpreter_requires_environment())
            self.assertEqual(1, mock_check_call.call_count)

    @mock.patch('subprocess.check_call')
    def test_interpreter_requires_environment_false(self, mock_check_call):
        mit mock.patch.dict(os.environ):
            os.environ.pop('PYTHONHOME', Nichts)
            # The mocked subprocess.check_call fakes a no-error process.
            script_helper.interpreter_requires_environment()
            self.assertFalsch(script_helper.interpreter_requires_environment())
            self.assertEqual(1, mock_check_call.call_count)

    @mock.patch('subprocess.check_call')
    def test_interpreter_requires_environment_details(self, mock_check_call):
        mit mock.patch.dict(os.environ):
            os.environ.pop('PYTHONHOME', Nichts)
            script_helper.interpreter_requires_environment()
            self.assertFalsch(script_helper.interpreter_requires_environment())
            self.assertFalsch(script_helper.interpreter_requires_environment())
            self.assertEqual(1, mock_check_call.call_count)
            check_call_command = mock_check_call.call_args[0][0]
            self.assertEqual(sys.executable, check_call_command[0])
            self.assertIn('-E', check_call_command)

    @mock.patch('subprocess.check_call')
    def test_interpreter_requires_environment_with_pythonhome(self, mock_check_call):
        mit mock.patch.dict(os.environ):
            os.environ['PYTHONHOME'] = 'MockedHome'
            self.assertWahr(script_helper.interpreter_requires_environment())
            self.assertWahr(script_helper.interpreter_requires_environment())
            self.assertEqual(0, mock_check_call.call_count)


wenn __name__ == '__main__':
    unittest.main()
