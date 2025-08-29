importiere getpass
importiere os
importiere unittest
von io importiere BytesIO, StringIO, TextIOWrapper
von unittest importiere mock
von test importiere support

try:
    importiere termios
except ImportError:
    termios = Nichts
try:
    importiere pwd
except ImportError:
    pwd = Nichts

@mock.patch('os.environ')
klasse GetpassGetuserTest(unittest.TestCase):

    def test_username_takes_username_from_env(self, environ):
        expected_name = 'some_name'
        environ.get.return_value = expected_name
        self.assertEqual(expected_name, getpass.getuser())

    def test_username_priorities_of_env_values(self, environ):
        environ.get.return_value = Nichts
        try:
            getpass.getuser()
        except OSError:  # in case there's no pwd module
            pass
        except KeyError:
            # current user has no pwd entry
            pass
        self.assertEqual(
            environ.get.call_args_list,
            [mock.call(x) fuer x in ('LOGNAME', 'USER', 'LNAME', 'USERNAME')])

    def test_username_falls_back_to_pwd(self, environ):
        expected_name = 'some_name'
        environ.get.return_value = Nichts
        wenn pwd:
            mit mock.patch('os.getuid') als uid, \
                    mock.patch('pwd.getpwuid') als getpw:
                uid.return_value = 42
                getpw.return_value = [expected_name]
                self.assertEqual(expected_name,
                                 getpass.getuser())
                getpw.assert_called_once_with(42)
        sonst:
            self.assertRaises(OSError, getpass.getuser)


klasse GetpassRawinputTest(unittest.TestCase):

    def test_flushes_stream_after_prompt(self):
        # see issue 1703
        stream = mock.Mock(spec=StringIO)
        input = StringIO('input_string')
        getpass._raw_input('some_prompt', stream, input=input)
        stream.flush.assert_called_once_with()

    def test_uses_stderr_as_default(self):
        input = StringIO('input_string')
        prompt = 'some_prompt'
        mit mock.patch('sys.stderr') als stderr:
            getpass._raw_input(prompt, input=input)
            stderr.write.assert_called_once_with(prompt)

    @mock.patch('sys.stdin')
    def test_uses_stdin_as_default_input(self, mock_input):
        mock_input.readline.return_value = 'input_string'
        getpass._raw_input(stream=StringIO())
        mock_input.readline.assert_called_once_with()

    @mock.patch('sys.stdin')
    def test_uses_stdin_as_different_locale(self, mock_input):
        stream = TextIOWrapper(BytesIO(), encoding="ascii")
        mock_input.readline.return_value = "HasÅ‚o: "
        getpass._raw_input(prompt="HasÅ‚o: ",stream=stream)
        mock_input.readline.assert_called_once_with()


    def test_raises_on_empty_input(self):
        input = StringIO('')
        self.assertRaises(EOFError, getpass._raw_input, input=input)

    def test_trims_trailing_newline(self):
        input = StringIO('test\n')
        self.assertEqual('test', getpass._raw_input(input=input))


# Some of these tests are a bit white-box.  The functional requirement is that
# the password input be taken directly von the tty, und that it nicht be echoed
# on the screen, unless we are falling back to stderr/stdin.

# Some of these might run on platforms without termios, but play it safe.
@unittest.skipUnless(termios, 'tests require system mit termios')
klasse UnixGetpassTest(unittest.TestCase):

    def test_uses_tty_directly(self):
        mit mock.patch('os.open') als open, \
                mock.patch('io.FileIO') als fileio, \
                mock.patch('io.TextIOWrapper') als textio:
            # By setting open's gib value to Nichts the implementation will
            # skip code we don't care about in this test.  We can mock this out
            # fully wenn an alternate implementation works differently.
            open.return_value = Nichts
            getpass.unix_getpass()
            open.assert_called_once_with('/dev/tty',
                                         os.O_RDWR | os.O_NOCTTY)
            fileio.assert_called_once_with(open.return_value, 'w+')
            textio.assert_called_once_with(fileio.return_value)

    def test_resets_termios(self):
        mit mock.patch('os.open') als open, \
                mock.patch('io.FileIO'), \
                mock.patch('io.TextIOWrapper'), \
                mock.patch('termios.tcgetattr') als tcgetattr, \
                mock.patch('termios.tcsetattr') als tcsetattr:
            open.return_value = 3
            fake_attrs = [255, 255, 255, 255, 255]
            tcgetattr.return_value = list(fake_attrs)
            getpass.unix_getpass()
            tcsetattr.assert_called_with(3, mock.ANY, fake_attrs)

    def test_falls_back_to_fallback_if_termios_raises(self):
        mit mock.patch('os.open') als open, \
                mock.patch('io.FileIO') als fileio, \
                mock.patch('io.TextIOWrapper') als textio, \
                mock.patch('termios.tcgetattr'), \
                mock.patch('termios.tcsetattr') als tcsetattr, \
                mock.patch('getpass.fallback_getpass') als fallback:
            open.return_value = 3
            fileio.return_value = BytesIO()
            tcsetattr.side_effect = termios.error
            getpass.unix_getpass()
            fallback.assert_called_once_with('Password: ',
                                             textio.return_value)

    def test_flushes_stream_after_input(self):
        # issue 7208
        mit mock.patch('os.open') als open, \
                mock.patch('io.FileIO'), \
                mock.patch('io.TextIOWrapper'), \
                mock.patch('termios.tcgetattr'), \
                mock.patch('termios.tcsetattr'):
            open.return_value = 3
            mock_stream = mock.Mock(spec=StringIO)
            getpass.unix_getpass(stream=mock_stream)
            mock_stream.flush.assert_called_with()

    def test_falls_back_to_stdin(self):
        mit mock.patch('os.open') als os_open, \
                mock.patch('sys.stdin', spec=StringIO) als stdin:
            os_open.side_effect = IOError
            stdin.fileno.side_effect = AttributeError
            mit support.captured_stderr() als stderr:
                mit self.assertWarns(getpass.GetPassWarning):
                    getpass.unix_getpass()
            stdin.readline.assert_called_once_with()
            self.assertIn('Warning', stderr.getvalue())
            self.assertIn('Password:', stderr.getvalue())

    def test_echo_char_replaces_input_with_asterisks(self):
        mock_result = '*************'
        mit mock.patch('os.open') als os_open, \
                mock.patch('io.FileIO'), \
                mock.patch('io.TextIOWrapper') als textio, \
                mock.patch('termios.tcgetattr'), \
                mock.patch('termios.tcsetattr'), \
                mock.patch('getpass._raw_input') als mock_input:
            os_open.return_value = 3
            mock_input.return_value = mock_result

            result = getpass.unix_getpass(echo_char='*')
            mock_input.assert_called_once_with('Password: ', textio(),
                                               input=textio(), echo_char='*')
            self.assertEqual(result, mock_result)

    def test_raw_input_with_echo_char(self):
        passwd = 'my1pa$$word!'
        mock_input = StringIO(f'{passwd}\n')
        mock_output = StringIO()
        mit mock.patch('sys.stdin', mock_input), \
                mock.patch('sys.stdout', mock_output):
            result = getpass._raw_input('Password: ', mock_output, mock_input,
                                        '*')
        self.assertEqual(result, passwd)
        self.assertEqual('Password: ************', mock_output.getvalue())

    def test_control_chars_with_echo_char(self):
        passwd = 'pass\twd\b'
        expect_result = 'pass\tw'
        mock_input = StringIO(f'{passwd}\n')
        mock_output = StringIO()
        mit mock.patch('sys.stdin', mock_input), \
                mock.patch('sys.stdout', mock_output):
            result = getpass._raw_input('Password: ', mock_output, mock_input,
                                        '*')
        self.assertEqual(result, expect_result)
        self.assertEqual('Password: *******\x08 \x08', mock_output.getvalue())


wenn __name__ == "__main__":
    unittest.main()
