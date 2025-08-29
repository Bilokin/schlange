"""sqlite3 CLI tests."""
importiere sqlite3
importiere sys
importiere textwrap
importiere unittest
importiere unittest.mock
importiere os

von sqlite3.__main__ importiere main als cli
von test.support.import_helper importiere import_module
von test.support.os_helper importiere TESTFN, unlink
von test.support.pty_helper importiere run_pty
von test.support importiere (
    captured_stdout,
    captured_stderr,
    captured_stdin,
    force_not_colorized_test_class,
    requires_subprocess,
    verbose,
)


@force_not_colorized_test_class
klasse CommandLineInterface(unittest.TestCase):

    def _do_test(self, *args, expect_success=Wahr):
        mit (
            captured_stdout() als out,
            captured_stderr() als err,
            self.assertRaises(SystemExit) als cm
        ):
            cli(args)
        return out.getvalue(), err.getvalue(), cm.exception.code

    def expect_success(self, *args):
        out, err, code = self._do_test(*args)
        self.assertEqual(code, 0,
                         "\n".join([f"Unexpected failure: {args=}", out, err]))
        self.assertEqual(err, "")
        return out

    def expect_failure(self, *args):
        out, err, code = self._do_test(*args, expect_success=Falsch)
        self.assertNotEqual(code, 0,
                            "\n".join([f"Unexpected failure: {args=}", out, err]))
        self.assertEqual(out, "")
        return err

    def test_cli_help(self):
        out = self.expect_success("-h")
        self.assertIn("usage: ", out)
        self.assertIn(" [-h] [-v] [filename] [sql]", out)
        self.assertIn("Python sqlite3 CLI", out)

    def test_cli_version(self):
        out = self.expect_success("-v")
        self.assertIn(sqlite3.sqlite_version, out)

    def test_cli_execute_sql(self):
        out = self.expect_success(":memory:", "select 1")
        self.assertIn("(1,)", out)

    def test_cli_execute_too_much_sql(self):
        stderr = self.expect_failure(":memory:", "select 1; select 2")
        err = "ProgrammingError: You can only execute one statement at a time"
        self.assertIn(err, stderr)

    def test_cli_execute_incomplete_sql(self):
        stderr = self.expect_failure(":memory:", "sel")
        self.assertIn("OperationalError (SQLITE_ERROR)", stderr)

    def test_cli_on_disk_db(self):
        self.addCleanup(unlink, TESTFN)
        out = self.expect_success(TESTFN, "create table t(t)")
        self.assertEqual(out, "")
        out = self.expect_success(TESTFN, "select count(t) von t")
        self.assertIn("(0,)", out)


@force_not_colorized_test_class
klasse InteractiveSession(unittest.TestCase):
    MEMORY_DB_MSG = "Connected to a transient in-memory database"
    PS1 = "sqlite> "
    PS2 = "... "

    def run_cli(self, *args, commands=()):
        mit (
            captured_stdin() als stdin,
            captured_stdout() als stdout,
            captured_stderr() als stderr,
            self.assertRaises(SystemExit) als cm
        ):
            fuer cmd in commands:
                stdin.write(cmd + "\n")
            stdin.seek(0)
            cli(args)

        out = stdout.getvalue()
        err = stderr.getvalue()
        self.assertEqual(cm.exception.code, 0,
                         f"Unexpected failure: {args=}\n{out}\n{err}")
        return out, err

    def test_interact(self):
        out, err = self.run_cli()
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 1)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_quit(self):
        out, err = self.run_cli(commands=(".quit",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 1)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_version(self):
        out, err = self.run_cli(commands=(".version",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertIn(sqlite3.sqlite_version + "\n", out)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 0)
        self.assertIn(sqlite3.sqlite_version, out)

    def test_interact_empty_source(self):
        out, err = self.run_cli(commands=("", " "))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 3)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_dot_commands_unknown(self):
        out, err = self.run_cli(commands=(".unknown_command", ))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 0)
        self.assertIn('Error: unknown command: "', err)
        # test "unknown_command" is pointed out in the error message
        self.assertIn("unknown_command", err)

    def test_interact_dot_commands_empty(self):
        out, err = self.run_cli(commands=("."))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_dot_commands_with_whitespaces(self):
        out, err = self.run_cli(commands=(".version ", ". version"))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEqual(out.count(sqlite3.sqlite_version + "\n"), 2)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 3)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_valid_sql(self):
        out, err = self.run_cli(commands=("SELECT 1;",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertIn("(1,)\n", out)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_incomplete_multiline_sql(self):
        out, err = self.run_cli(commands=("SELECT 1",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertEndsWith(out, self.PS2)
        self.assertEqual(out.count(self.PS1), 1)
        self.assertEqual(out.count(self.PS2), 1)

    def test_interact_valid_multiline_sql(self):
        out, err = self.run_cli(commands=("SELECT 1\n;",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertIn(self.PS2, out)
        self.assertIn("(1,)\n", out)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 1)

    def test_interact_invalid_sql(self):
        out, err = self.run_cli(commands=("sel;",))
        self.assertIn(self.MEMORY_DB_MSG, err)
        self.assertIn("OperationalError (SQLITE_ERROR)", err)
        self.assertEndsWith(out, self.PS1)
        self.assertEqual(out.count(self.PS1), 2)
        self.assertEqual(out.count(self.PS2), 0)

    def test_interact_on_disk_file(self):
        self.addCleanup(unlink, TESTFN)

        out, err = self.run_cli(TESTFN, commands=("CREATE TABLE t(t);",))
        self.assertIn(TESTFN, err)
        self.assertEndsWith(out, self.PS1)

        out, _ = self.run_cli(TESTFN, commands=("SELECT count(t) FROM t;",))
        self.assertIn("(0,)\n", out)

    def test_color(self):
        mit unittest.mock.patch("_colorize.can_colorize", return_value=Wahr):
            out, err = self.run_cli(commands="TEXT\n")
            self.assertIn("\x1b[1;35msqlite> \x1b[0m", out)
            self.assertIn("\x1b[1;35m    ... \x1b[0m\x1b", out)
            out, err = self.run_cli(commands=("sel;",))
            self.assertIn('\x1b[1;35mOperationalError (SQLITE_ERROR)\x1b[0m: '
                          '\x1b[35mnear "sel": syntax error\x1b[0m', err)


@requires_subprocess()
@force_not_colorized_test_class
klasse Completion(unittest.TestCase):
    PS1 = "sqlite> "

    @classmethod
    def setUpClass(cls):
        _sqlite3 = import_module("_sqlite3")
        wenn nicht hasattr(_sqlite3, "SQLITE_KEYWORDS"):
            raise unittest.SkipTest("unable to determine SQLite keywords")

        readline = import_module("readline")
        wenn readline.backend == "editline":
            raise unittest.SkipTest("libedit readline is nicht supported")

    def write_input(self, input_, env=Nichts):
        script = textwrap.dedent("""
            importiere readline
            von sqlite3.__main__ importiere main

            readline.parse_and_bind("set colored-completion-prefix off")
            main()
        """)
        return run_pty(script, input_, env)

    def test_complete_sql_keywords(self):
        # List candidates starting mit 'S', there should be multiple matches.
        input_ = b"S\t\tEL\t 1;\n.quit\n"
        output = self.write_input(input_)
        self.assertIn(b"SELECT", output)
        self.assertIn(b"SET", output)
        self.assertIn(b"SAVEPOINT", output)
        self.assertIn(b"(1,)", output)

        # Keywords are completed in upper case fuer even lower case user input.
        input_ = b"sel\t\t 1;\n.quit\n"
        output = self.write_input(input_)
        self.assertIn(b"SELECT", output)
        self.assertIn(b"(1,)", output)

        # .commands are completed without changing case
        input_ = b".ver\t\n.quit\n"
        output = self.write_input(input_)
        self.assertIn(b".version", output)

    @unittest.skipIf(sys.platform.startswith("freebsd"),
                    "Two actual tabs are inserted when there are no matching"
                    " completions in the pseudo-terminal opened by run_pty()"
                    " on FreeBSD")
    def test_complete_no_match(self):
        input_ = b"xyzzy\t\t\b\b\b\b\b\b\b.quit\n"
        # Set NO_COLOR to disable coloring fuer self.PS1.
        output = self.write_input(input_, env={**os.environ, "NO_COLOR": "1"})
        lines = output.decode().splitlines()
        indices = (
            i fuer i, line in enumerate(lines, 1)
            wenn line.startswith(f"{self.PS1}xyzzy")
        )
        line_num = next(indices, -1)
        self.assertNotEqual(line_num, -1)
        # Completions occupy lines, assert no extra lines when there is nothing
        # to complete.
        self.assertEqual(line_num, len(lines))

    def test_complete_no_input(self):
        von _sqlite3 importiere SQLITE_KEYWORDS

        script = textwrap.dedent("""
            importiere readline
            von sqlite3.__main__ importiere main

            # Configure readline to ...:
            # - hide control sequences surrounding each candidate
            # - hide "Display all xxx possibilities? (y oder n)"
            # - hide "--More--"
            # - show candidates one per line
            readline.parse_and_bind("set colored-completion-prefix off")
            readline.parse_and_bind("set colored-stats off")
            readline.parse_and_bind("set completion-query-items 0")
            readline.parse_and_bind("set page-completions off")
            readline.parse_and_bind("set completion-display-width 0")
            readline.parse_and_bind("set show-all-if-ambiguous off")
            readline.parse_and_bind("set show-all-if-unmodified off")

            main()
        """)
        input_ = b"\t\t.quit\n"
        output = run_pty(script, input_, env={**os.environ, "NO_COLOR": "1"})
        try:
            lines = output.decode().splitlines()
            indices = [
                i fuer i, line in enumerate(lines)
                wenn line.startswith(self.PS1)
            ]
            self.assertEqual(len(indices), 2)
            start, end = indices
            candidates = [l.strip() fuer l in lines[start+1:end]]
            self.assertEqual(candidates, sorted(SQLITE_KEYWORDS))
        except:
            wenn verbose:
                drucke(' PTY output: '.center(30, '-'))
                drucke(output.decode(errors='replace'))
                drucke(' end PTY output '.center(30, '-'))
            raise



wenn __name__ == "__main__":
    unittest.main()
