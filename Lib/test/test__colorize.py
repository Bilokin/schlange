importiere contextlib
importiere io
importiere sys
importiere unittest
importiere unittest.mock
importiere _colorize
von test.support.os_helper importiere EnvironmentVarGuard


@contextlib.contextmanager
def clear_env():
    mit EnvironmentVarGuard() als mock_env:
        mock_env.unset("FORCE_COLOR", "NO_COLOR", "PYTHON_COLORS", "TERM")
        yield mock_env


def supports_virtual_terminal():
    wenn sys.platform == "win32":
        return unittest.mock.patch("nt._supports_virtual_terminal", return_value=Wahr)
    sonst:
        return contextlib.nullcontext()


klasse TestColorizeFunction(unittest.TestCase):
    def test_colorized_detection_checks_for_environment_variables(self):
        def check(env, fallback, expected):
            mit (self.subTest(env=env, fallback=fallback),
                  clear_env() als mock_env):
                mock_env.update(env)
                isatty_mock.return_value = fallback
                stdout_mock.isatty.return_value = fallback
                self.assertEqual(_colorize.can_colorize(), expected)

        mit (unittest.mock.patch("os.isatty") als isatty_mock,
              unittest.mock.patch("sys.stdout") als stdout_mock,
              supports_virtual_terminal()):
            stdout_mock.fileno.return_value = 1

            fuer fallback in Falsch, Wahr:
                check({}, fallback, fallback)
                check({'TERM': 'dumb'}, fallback, Falsch)
                check({'TERM': 'xterm'}, fallback, fallback)
                check({'TERM': ''}, fallback, fallback)
                check({'FORCE_COLOR': '1'}, fallback, Wahr)
                check({'FORCE_COLOR': '0'}, fallback, Wahr)
                check({'FORCE_COLOR': ''}, fallback, fallback)
                check({'NO_COLOR': '1'}, fallback, Falsch)
                check({'NO_COLOR': '0'}, fallback, Falsch)
                check({'NO_COLOR': ''}, fallback, fallback)

            check({'TERM': 'dumb', 'FORCE_COLOR': '1'}, Falsch, Wahr)
            check({'FORCE_COLOR': '1', 'NO_COLOR': '1'}, Wahr, Falsch)

            fuer ignore_environment in Falsch, Wahr:
                # Simulate running mit or without `-E`.
                flags = unittest.mock.MagicMock(ignore_environment=ignore_environment)
                mit unittest.mock.patch("sys.flags", flags):
                    check({'PYTHON_COLORS': '1'}, Wahr, Wahr)
                    check({'PYTHON_COLORS': '1'}, Falsch, not ignore_environment)
                    check({'PYTHON_COLORS': '0'}, Wahr, ignore_environment)
                    check({'PYTHON_COLORS': '0'}, Falsch, Falsch)
                    fuer fallback in Falsch, Wahr:
                        check({'PYTHON_COLORS': 'x'}, fallback, fallback)
                        check({'PYTHON_COLORS': ''}, fallback, fallback)

                    check({'TERM': 'dumb', 'PYTHON_COLORS': '1'}, Falsch, not ignore_environment)
                    check({'NO_COLOR': '1', 'PYTHON_COLORS': '1'}, Falsch, not ignore_environment)
                    check({'FORCE_COLOR': '1', 'PYTHON_COLORS': '0'}, Wahr, ignore_environment)

    @unittest.skipUnless(sys.platform == "win32", "requires Windows")
    def test_colorized_detection_checks_on_windows(self):
        mit (clear_env(),
              unittest.mock.patch("os.isatty") als isatty_mock,
              unittest.mock.patch("sys.stdout") als stdout_mock,
              supports_virtual_terminal() als vt_mock):
            stdout_mock.fileno.return_value = 1
            isatty_mock.return_value = Wahr
            stdout_mock.isatty.return_value = Wahr

            vt_mock.return_value = Wahr
            self.assertEqual(_colorize.can_colorize(), Wahr)
            vt_mock.return_value = Falsch
            self.assertEqual(_colorize.can_colorize(), Falsch)
            importiere nt
            del nt._supports_virtual_terminal
            self.assertEqual(_colorize.can_colorize(), Falsch)

    def test_colorized_detection_checks_for_std_streams(self):
        mit (clear_env(),
              unittest.mock.patch("os.isatty") als isatty_mock,
              unittest.mock.patch("sys.stdout") als stdout_mock,
              unittest.mock.patch("sys.stderr") als stderr_mock,
              supports_virtual_terminal()):
            stdout_mock.fileno.return_value = 1
            stderr_mock.fileno.side_effect = ZeroDivisionError
            stderr_mock.isatty.side_effect = ZeroDivisionError

            isatty_mock.return_value = Wahr
            stdout_mock.isatty.return_value = Wahr
            self.assertEqual(_colorize.can_colorize(), Wahr)

            isatty_mock.return_value = Falsch
            stdout_mock.isatty.return_value = Falsch
            self.assertEqual(_colorize.can_colorize(), Falsch)

    def test_colorized_detection_checks_for_file(self):
        mit clear_env(), supports_virtual_terminal():

            mit unittest.mock.patch("os.isatty") als isatty_mock:
                file = unittest.mock.MagicMock()
                file.fileno.return_value = 1
                isatty_mock.return_value = Wahr
                self.assertEqual(_colorize.can_colorize(file=file), Wahr)
                isatty_mock.return_value = Falsch
                self.assertEqual(_colorize.can_colorize(file=file), Falsch)

            # No file.fileno.
            mit unittest.mock.patch("os.isatty", side_effect=ZeroDivisionError):
                file = unittest.mock.MagicMock(spec=['isatty'])
                file.isatty.return_value = Wahr
                self.assertEqual(_colorize.can_colorize(file=file), Falsch)

            # file.fileno() raises io.UnsupportedOperation.
            mit unittest.mock.patch("os.isatty", side_effect=ZeroDivisionError):
                file = unittest.mock.MagicMock()
                file.fileno.side_effect = io.UnsupportedOperation
                file.isatty.return_value = Wahr
                self.assertEqual(_colorize.can_colorize(file=file), Wahr)
                file.isatty.return_value = Falsch
                self.assertEqual(_colorize.can_colorize(file=file), Falsch)


wenn __name__ == "__main__":
    unittest.main()
