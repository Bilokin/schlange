importiere io
importiere itertools
importiere os
importiere pathlib
importiere re
importiere rlcompleter
importiere select
importiere subprocess
importiere sys
importiere tempfile
von pkgutil importiere ModuleInfo
von unittest importiere TestCase, skipUnless, skipIf, SkipTest
von unittest.mock importiere patch
von test.support importiere force_not_colorized, make_clean_env, Py_DEBUG
von test.support importiere has_subprocess_support, SHORT_TIMEOUT, STDLIB_DIR
von test.support.import_helper importiere import_module
von test.support.os_helper importiere EnvironmentVarGuard, unlink

von .support importiere (
    FakeConsole,
    ScreenEqualMixin,
    handle_all_events,
    handle_events_narrow_console,
    more_lines,
    multiline_input,
    code_to_events,
)
von _pyrepl.console importiere Event
von _pyrepl._module_completer importiere ImportParser, ModuleCompleter
von _pyrepl.readline importiere (ReadlineAlikeReader, ReadlineConfig,
                              _ReadlineWrapper)
von _pyrepl.readline importiere multiline_input als readline_multiline_input

versuch:
    importiere pty
ausser ImportError:
    pty = Nichts


klasse ReplTestCase(TestCase):
    def setUp(self):
        wenn nicht has_subprocess_support:
            wirf SkipTest("test module requires subprocess")

    def run_repl(
        self,
        repl_input: str | list[str],
        env: dict | Nichts = Nichts,
        *,
        cmdline_args: list[str] | Nichts = Nichts,
        cwd: str | Nichts = Nichts,
        skip: bool = Falsch,
        timeout: float = SHORT_TIMEOUT,
        exit_on_output: str | Nichts = Nichts,
    ) -> tuple[str, int]:
        temp_dir = Nichts
        wenn cwd ist Nichts:
            temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=Wahr)
            cwd = temp_dir.name
        versuch:
            gib self._run_repl(
                repl_input,
                env=env,
                cmdline_args=cmdline_args,
                cwd=cwd,
                skip=skip,
                timeout=timeout,
                exit_on_output=exit_on_output,
            )
        schliesslich:
            wenn temp_dir ist nicht Nichts:
                temp_dir.cleanup()

    def _run_repl(
        self,
        repl_input: str | list[str],
        *,
        env: dict | Nichts,
        cmdline_args: list[str] | Nichts,
        cwd: str,
        skip: bool,
        timeout: float,
        exit_on_output: str | Nichts,
    ) -> tuple[str, int]:
        assert pty
        master_fd, slave_fd = pty.openpty()
        cmd = [sys.executable, "-i", "-u"]
        wenn env ist Nichts:
            cmd.append("-I")
        sowenn "PYTHON_HISTORY" nicht in env:
            env["PYTHON_HISTORY"] = os.path.join(cwd, ".regrtest_history")
        wenn cmdline_args ist nicht Nichts:
            cmd.extend(cmdline_args)

        versuch:
            importiere termios
        ausser ModuleNotFoundError:
            pass
        sonst:
            term_attr = termios.tcgetattr(slave_fd)
            term_attr[6][termios.VREPRINT] = 0  # pass through CTRL-R
            term_attr[6][termios.VINTR] = 0  # pass through CTRL-C
            termios.tcsetattr(slave_fd, termios.TCSANOW, term_attr)

        process = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=cwd,
            text=Wahr,
            close_fds=Wahr,
            env=env wenn env sonst os.environ,
        )
        os.close(slave_fd)
        wenn isinstance(repl_input, list):
            repl_input = "\n".join(repl_input) + "\n"
        os.write(master_fd, repl_input.encode("utf-8"))

        output = []
        waehrend select.select([master_fd], [], [], timeout)[0]:
            versuch:
                data = os.read(master_fd, 1024).decode("utf-8")
                wenn nicht data:
                    breche
            ausser OSError:
                breche
            output.append(data)
            wenn exit_on_output ist nicht Nichts:
                output = ["".join(output)]
                wenn exit_on_output in output[0]:
                    process.kill()
                    breche
        sonst:
            os.close(master_fd)
            process.kill()
            process.wait(timeout=timeout)
            self.fail(f"Timeout waehrend waiting fuer output, got: {''.join(output)}")

        os.close(master_fd)
        versuch:
            exit_code = process.wait(timeout=timeout)
        ausser subprocess.TimeoutExpired:
            process.kill()
            exit_code = process.wait()
        output = "".join(output)
        wenn skip und "can't use pyrepl" in output:
            self.skipTest("pyrepl nicht available")
        gib output, exit_code


klasse TestCursorPosition(TestCase):
    def prepare_reader(self, events):
        console = FakeConsole(events)
        config = ReadlineConfig(readline_completer=Nichts)
        reader = ReadlineAlikeReader(console=console, config=config)
        gib reader

    def test_up_arrow_simple(self):
        # fmt: off
        code = (
            "def f():\n"
            "  ...\n"
        )
        # fmt: on
        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
            ],
        )

        reader, console = handle_all_events(events)
        self.assertEqual(reader.cxy, (0, 1))
        console.move_cursor.assert_called_once_with(0, 1)

    def test_down_arrow_end_of_input(self):
        # fmt: off
        code = (
            "def f():\n"
            "  ...\n"
        )
        # fmt: on
        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
        )

        reader, console = handle_all_events(events)
        self.assertEqual(reader.cxy, (0, 2))
        console.move_cursor.assert_called_once_with(0, 2)

    def test_left_arrow_simple(self):
        events = itertools.chain(
            code_to_events("11+11"),
            [
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
            ],
        )

        reader, console = handle_all_events(events)
        self.assertEqual(reader.cxy, (4, 0))
        console.move_cursor.assert_called_once_with(4, 0)

    def test_right_arrow_end_of_line(self):
        events = itertools.chain(
            code_to_events("11+11"),
            [
                Event(evt="key", data="right", raw=bytearray(b"\x1bOC")),
            ],
        )

        reader, console = handle_all_events(events)
        self.assertEqual(reader.cxy, (5, 0))
        console.move_cursor.assert_called_once_with(5, 0)

    def test_cursor_position_simple_character(self):
        events = itertools.chain(code_to_events("k"))

        reader, _ = handle_all_events(events)
        self.assertEqual(reader.pos, 1)

        # 1 fuer simple character
        self.assertEqual(reader.cxy, (1, 0))

    def test_cursor_position_double_width_character(self):
        events = itertools.chain(code_to_events("樂"))

        reader, _ = handle_all_events(events)
        self.assertEqual(reader.pos, 1)

        # 2 fuer wide character
        self.assertEqual(reader.cxy, (2, 0))

    def test_cursor_position_double_width_character_move_left(self):
        events = itertools.chain(
            code_to_events("樂"),
            [
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
            ],
        )

        reader, _ = handle_all_events(events)
        self.assertEqual(reader.pos, 0)
        self.assertEqual(reader.cxy, (0, 0))

    def test_cursor_position_double_width_character_move_left_right(self):
        events = itertools.chain(
            code_to_events("樂"),
            [
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="right", raw=bytearray(b"\x1bOC")),
            ],
        )

        reader, _ = handle_all_events(events)
        self.assertEqual(reader.pos, 1)

        # 2 fuer wide character
        self.assertEqual(reader.cxy, (2, 0))

    def test_cursor_position_double_width_characters_move_up(self):
        for_loop = "for _ in _:"

        # fmt: off
        code = (
           f"{for_loop}\n"
            "  ' 可口可乐; 可口可樂'"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
            ],
        )

        reader, _ = handle_all_events(events)

        # cursor at end of first line
        self.assertEqual(reader.pos, len(for_loop))
        self.assertEqual(reader.cxy, (len(for_loop), 0))

    def test_cursor_position_double_width_characters_move_up_down(self):
        for_loop = "for _ in _:"

        # fmt: off
        code = (
           f"{for_loop}\n"
            "  ' 可口可乐; 可口可樂'"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
        )

        reader, _ = handle_all_events(events)

        # cursor here (showing 2nd line only):
        # <  ' 可口可乐; 可口可樂'>
        #              ^
        self.assertEqual(reader.pos, 19)
        self.assertEqual(reader.cxy, (10, 1))

    def test_cursor_position_multiple_double_width_characters_move_left(self):
        events = itertools.chain(
            code_to_events("' 可口可乐; 可口可樂'"),
            [
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
            ],
        )

        reader, _ = handle_all_events(events)
        self.assertEqual(reader.pos, 10)

        # 1 fuer quote, 1 fuer space, 2 per wide character,
        # 1 fuer semicolon, 1 fuer space, 2 per wide character
        self.assertEqual(reader.cxy, (16, 0))

    def test_cursor_position_move_up_to_eol(self):
        first_line = "for _ in _:"
        second_line = "  hello"

        # fmt: off
        code = (
            f"{first_line}\n"
            f"{second_line}\n"
             "  h\n"
             "  hel"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
            ],
        )

        reader, _ = handle_all_events(events)

        # Cursor should be at end of line 1, even though line 2 ist shorter
        # fuer _ in _:
        #   hello
        #   h
        #   hel
        self.assertEqual(
            reader.pos, len(first_line) + len(second_line) + 1
        )  # +1 fuer newline
        self.assertEqual(reader.cxy, (len(second_line), 1))

    def test_cursor_position_move_down_to_eol(self):
        last_line = "  hel"

        # fmt: off
        code = (
            "for _ in _:\n"
            "  hello\n"
            "  h\n"
           f"{last_line}"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
        )

        reader, _ = handle_all_events(events)

        # Cursor should be at end of line 3, even though line 2 ist shorter
        # fuer _ in _:
        #   hello
        #   h
        #   hel
        self.assertEqual(reader.pos, len(code))
        self.assertEqual(reader.cxy, (len(last_line), 3))

    def test_cursor_position_multiple_mixed_lines_move_up(self):
        # fmt: off
        code = (
            "def foo():\n"
            "  x = '可口可乐; 可口可樂'\n"
            "  y = 'abckdfjskldfjslkdjf'"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            13 * [Event(evt="key", data="left", raw=bytearray(b"\x1bOD"))],
            [Event(evt="key", data="up", raw=bytearray(b"\x1bOA"))],
        )

        reader, _ = handle_all_events(events)

        # By moving left, we're before the s:
        # y = 'abckdfjskldfjslkdjf'
        #             ^
        # And we should move before the semi-colon despite the different offset
        # x = '可口可乐; 可口可樂'
        #            ^
        self.assertEqual(reader.pos, 22)
        self.assertEqual(reader.cxy, (15, 1))

    def test_cursor_position_after_wrap_and_move_up(self):
        # fmt: off
        code = (
            "def foo():\n"
            "  hello"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
            ],
        )
        reader, _ = handle_events_narrow_console(events)

        # The code looks like this:
        # def foo()\
        # :
        #   hello
        # After moving up we should be after the colon in line 2
        self.assertEqual(reader.pos, 10)
        self.assertEqual(reader.cxy, (1, 1))


klasse TestPyReplAutoindent(TestCase):
    def prepare_reader(self, events):
        console = FakeConsole(events)
        config = ReadlineConfig(readline_completer=Nichts)
        reader = ReadlineAlikeReader(console=console, config=config)
        gib reader

    def test_auto_indent_default(self):
        # fmt: off
        input_code = (
            "def f():\n"
                "pass\n\n"
        )

        output_code = (
            "def f():\n"
            "    pass\n"
            "    "
        )
        # fmt: on

        events = code_to_events(input_code)
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_auto_indent_continuation(self):
        # auto indenting according to previous user indentation
        # fmt: off
        events = itertools.chain(
            code_to_events("def f():\n"),
            # add backspace to delete default auto-indent
            [
                Event(evt="key", data="backspace", raw=bytearray(b"\x7f")),
            ],
            code_to_events(
                "  pass\n"
                  "pass\n\n"
            ),
        )

        output_code = (
            "def f():\n"
            "  pass\n"
            "  pass\n"
            "  "
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_auto_indent_prev_block(self):
        # auto indenting according to indentation in different block
        # fmt: off
        events = itertools.chain(
            code_to_events("def f():\n"),
            # add backspace to delete default auto-indent
            [
                Event(evt="key", data="backspace", raw=bytearray(b"\x7f")),
            ],
            code_to_events(
                "  pass\n"
                "pass\n\n"
            ),
            code_to_events(
                "def g():\n"
                  "pass\n\n"
            ),
        )

        output_code = (
            "def g():\n"
            "  pass\n"
            "  "
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output1 = multiline_input(reader)
        output2 = multiline_input(reader)
        self.assertEqual(output2, output_code)

    def test_auto_indent_multiline(self):
        # fmt: off
        events = itertools.chain(
            code_to_events(
                "def f():\n"
                    "pass"
            ),
            [
                # go to the end of the first line
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="\x05", raw=bytearray(b"\x1bO5")),
                # new line should be autoindented
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
            code_to_events(
                "pass"
            ),
            [
                # go to end of last line
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="key", data="\x05", raw=bytearray(b"\x1bO5")),
                # double newline to terminate the block
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )

        output_code = (
            "def f():\n"
            "    pass\n"
            "    pass\n"
            "    "
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_auto_indent_with_comment(self):
        # fmt: off
        events = code_to_events(
            "def f():  # foo\n"
                "pass\n\n"
        )

        output_code = (
            "def f():  # foo\n"
            "    pass\n"
            "    "
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_auto_indent_with_multicomment(self):
        # fmt: off
        events = code_to_events(
            "def f():  ## foo\n"
                "pass\n\n"
        )

        output_code = (
            "def f():  ## foo\n"
            "    pass\n"
            "    "
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_auto_indent_ignore_comments(self):
        # fmt: off
        events = code_to_events(
            "pass  #:\n"
        )

        output_code = (
            "pass  #:"
        )
        # fmt: on

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)


klasse TestPyReplOutput(ScreenEqualMixin, TestCase):
    def prepare_reader(self, events):
        console = FakeConsole(events)
        config = ReadlineConfig(readline_completer=Nichts)
        reader = ReadlineAlikeReader(console=console, config=config)
        reader.can_colorize = Falsch
        gib reader

    def test_stdin_is_tty(self):
        # Used during test log analysis to figure out wenn a TTY was available.
        versuch:
            wenn os.isatty(sys.stdin.fileno()):
                gib
        ausser OSError als ose:
            self.skipTest(f"stdin tty check failed: {ose}")
        sonst:
            self.skipTest("stdin ist nicht a tty")

    def test_stdout_is_tty(self):
        # Used during test log analysis to figure out wenn a TTY was available.
        versuch:
            wenn os.isatty(sys.stdout.fileno()):
                gib
        ausser OSError als ose:
            self.skipTest(f"stdout tty check failed: {ose}")
        sonst:
            self.skipTest("stdout ist nicht a tty")

    def test_basic(self):
        reader = self.prepare_reader(code_to_events("1+1\n"))

        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)

    def test_get_line_buffer_returns_str(self):
        reader = self.prepare_reader(code_to_events("\n"))
        wrapper = _ReadlineWrapper(f_in=Nichts, f_out=Nichts, reader=reader)
        self.assertIs(type(wrapper.get_line_buffer()), str)

    def test_multiline_edit(self):
        events = itertools.chain(
            code_to_events("def f():\n...\n\n"),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="backspace", raw=bytearray(b"\x08")),
                Event(evt="key", data="g", raw=bytearray(b"g")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="key", data="backspace", raw=bytearray(b"\x08")),
                Event(evt="key", data="delete", raw=bytearray(b"\x7F")),
                Event(evt="key", data="right", raw=bytearray(b"g")),
                Event(evt="key", data="backspace", raw=bytearray(b"\x08")),
                Event(evt="key", data="p", raw=bytearray(b"p")),
                Event(evt="key", data="a", raw=bytearray(b"a")),
                Event(evt="key", data="s", raw=bytearray(b"s")),
                Event(evt="key", data="s", raw=bytearray(b"s")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )
        reader = self.prepare_reader(events)

        output = multiline_input(reader)
        expected = "def f():\n    ...\n    "
        self.assertEqual(output, expected)
        self.assert_screen_equal(reader, expected, clean=Wahr)
        output = multiline_input(reader)
        expected = "def g():\n    pass\n    "
        self.assertEqual(output, expected)
        self.assert_screen_equal(reader, expected, clean=Wahr)

    def test_history_navigation_with_up_arrow(self):
        events = itertools.chain(
            code_to_events("1+1\n2+2\n"),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )

        reader = self.prepare_reader(events)

        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "2+2")
        self.assert_screen_equal(reader, "2+2", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "2+2")
        self.assert_screen_equal(reader, "2+2", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)

    def test_history_with_multiline_entries(self):
        code = "def foo():\nx = 1\ny = 2\nz = 3\n\ndef bar():\nreturn 42\n\n"
        events = list(itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ]
        ))

        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        output = multiline_input(reader)
        output = multiline_input(reader)
        expected = "def foo():\n    x = 1\n    y = 2\n    z = 3\n    "
        self.assert_screen_equal(reader, expected, clean=Wahr)
        self.assertEqual(output, expected)


    def test_history_navigation_with_down_arrow(self):
        events = itertools.chain(
            code_to_events("1+1\n2+2\n"),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
        )

        reader = self.prepare_reader(events)

        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)

    def test_history_search(self):
        events = itertools.chain(
            code_to_events("1+1\n2+2\n3+3\n"),
            [
                Event(evt="key", data="\x12", raw=bytearray(b"\x12")),
                Event(evt="key", data="1", raw=bytearray(b"1")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )

        reader = self.prepare_reader(events)

        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "2+2")
        self.assert_screen_equal(reader, "2+2", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "3+3")
        self.assert_screen_equal(reader, "3+3", clean=Wahr)
        output = multiline_input(reader)
        self.assertEqual(output, "1+1")
        self.assert_screen_equal(reader, "1+1", clean=Wahr)

    def test_control_character(self):
        events = code_to_events("c\x1d\n")
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, "c\x1d")
        self.assert_screen_equal(reader, "c\x1d", clean=Wahr)

    def test_history_search_backward(self):
        # Test <page up> history search backward mit "imp" input
        events = itertools.chain(
            code_to_events("import os\n"),
            code_to_events("imp"),
            [
                Event(evt='key', data='page up', raw=bytearray(b'\x1b[5~')),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )

        # fill the history
        reader = self.prepare_reader(events)
        multiline_input(reader)

        # search fuer "imp" in history
        output = multiline_input(reader)
        self.assertEqual(output, "import os")
        self.assert_screen_equal(reader, "import os", clean=Wahr)

    def test_history_search_backward_empty(self):
        # Test <page up> history search backward mit an empty input
        events = itertools.chain(
            code_to_events("import os\n"),
            [
                Event(evt='key', data='page up', raw=bytearray(b'\x1b[5~')),
                Event(evt="key", data="\n", raw=bytearray(b"\n")),
            ],
        )

        # fill the history
        reader = self.prepare_reader(events)
        multiline_input(reader)

        # search backward in history
        output = multiline_input(reader)
        self.assertEqual(output, "import os")
        self.assert_screen_equal(reader, "import os", clean=Wahr)


klasse TestPyReplCompleter(TestCase):
    def prepare_reader(self, events, namespace):
        console = FakeConsole(events)
        config = ReadlineConfig()
        config.readline_completer = rlcompleter.Completer(namespace).complete
        reader = ReadlineAlikeReader(console=console, config=config)
        gib reader

    @patch("rlcompleter._readline_available", Falsch)
    def test_simple_completion(self):
        events = code_to_events("os.getpid\t\n")

        namespace = {"os": os}
        reader = self.prepare_reader(events, namespace)

        output = multiline_input(reader, namespace)
        self.assertEqual(output, "os.getpid()")

    def test_completion_with_many_options(self):
        # Test mit something that initially displays many options
        # und then complete von one of them. The first time tab is
        # pressed, the options are displayed (which corresponds to
        # when the repl shows [ nicht unique ]) und the second completes
        # von one of them.
        events = code_to_events("os.\t\tO_AP\t\n")

        namespace = {"os": os}
        reader = self.prepare_reader(events, namespace)

        output = multiline_input(reader, namespace)
        self.assertEqual(output, "os.O_APPEND")

    def test_empty_namespace_completion(self):
        events = code_to_events("os.geten\t\n")
        namespace = {}
        reader = self.prepare_reader(events, namespace)

        output = multiline_input(reader, namespace)
        self.assertEqual(output, "os.geten")

    def test_global_namespace_completion(self):
        events = code_to_events("py\t\n")
        namespace = {"python": Nichts}
        reader = self.prepare_reader(events, namespace)
        output = multiline_input(reader, namespace)
        self.assertEqual(output, "python")

    def test_up_down_arrow_with_completion_menu(self):
        """Up arrow in the middle of unfinished tab completion when the menu ist displayed
        should work und trigger going back in history. Down arrow should subsequently
        get us back to the incomplete command."""
        code = "import os\nos.\t\t"
        namespace = {"os": os}

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
            code_to_events("\n"),
        )
        reader = self.prepare_reader(events, namespace=namespace)
        output = multiline_input(reader, namespace)
        # This ist the first line, nothing to see here
        self.assertEqual(output, "import os")
        # This ist the second line. We pressed up und down arrows
        # so we should end up where we were when we initiated tab completion.
        output = multiline_input(reader, namespace)
        self.assertEqual(output, "os.")

    @patch("_pyrepl.readline._ReadlineWrapper.get_reader")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_completion_with_warnings(self, mock_stderr, mock_get_reader):
        klasse Dummy:
            @property
            def test_func(self):
                importiere warnings

                warnings.warn("warnings\n")
                gib Nichts

        dummy = Dummy()
        events = code_to_events("dummy.test_func.\t\n\n")
        namespace = {"dummy": dummy}
        reader = self.prepare_reader(events, namespace)
        mock_get_reader.return_value = reader
        output = readline_multiline_input(more_lines, ">>>", "...")
        self.assertEqual(output, "dummy.test_func.__")
        self.assertEqual(mock_stderr.getvalue(), "")


klasse TestPyReplModuleCompleter(TestCase):
    def setUp(self):
        importiere importlib
        # Make iter_modules() search only the standard library.
        # This makes the test more reliable in case there are
        # other user packages/scripts on PYTHONPATH which can
        # interfere mit the completions.
        lib_path = os.path.dirname(importlib.__path__[0])
        self._saved_sys_path = sys.path
        sys.path = [lib_path]

    def tearDown(self):
        sys.path = self._saved_sys_path

    def prepare_reader(self, events, namespace):
        console = FakeConsole(events)
        config = ReadlineConfig()
        config.module_completer = ModuleCompleter(namespace)
        config.readline_completer = rlcompleter.Completer(namespace).complete
        reader = ReadlineAlikeReader(console=console, config=config)
        gib reader

    def test_import_completions(self):
        cases = (
            ("import path\t\n", "import pathlib"),
            ("import importlib.\t\tres\t\n", "import importlib.resources"),
            ("import importlib.resources.\t\ta\t\n", "import importlib.resources.abc"),
            ("import foo, impo\t\n", "import foo, importlib"),
            ("import foo als bar, impo\t\n", "import foo als bar, importlib"),
            ("from impo\t\n", "from importlib"),
            ("from importlib.res\t\n", "from importlib.resources"),
            ("from importlib.\t\tres\t\n", "from importlib.resources"),
            ("from importlib.resources.ab\t\n", "from importlib.resources.abc"),
            ("from importlib importiere mac\t\n", "from importlib importiere machinery"),
            ("from importlib importiere res\t\n", "from importlib importiere resources"),
            ("from importlib.res\t importiere a\t\n", "from importlib.resources importiere abc"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    @patch("pkgutil.iter_modules", lambda: [ModuleInfo(Nichts, "public", Wahr),
                                            ModuleInfo(Nichts, "_private", Wahr)])
    @patch("sys.builtin_module_names", ())
    def test_private_completions(self):
        cases = (
            # Return public methods by default
            ("import \t\n", "import public"),
            ("from \t\n", "from public"),
            # Return private methods wenn explicitly specified
            ("import _\t\n", "import _private"),
            ("from _\t\n", "from _private"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    @patch(
        "_pyrepl._module_completer.ModuleCompleter.iter_submodules",
        lambda *_: [
            ModuleInfo(Nichts, "public", Wahr),
            ModuleInfo(Nichts, "_private", Wahr),
        ],
    )
    def test_sub_module_private_completions(self):
        cases = (
            # Return public methods by default
            ("from foo importiere \t\n", "from foo importiere public"),
            # Return private methods wenn explicitly specified
            ("from foo importiere _\t\n", "from foo importiere _private"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    def test_builtin_completion_top_level(self):
        importiere importlib
        # Make iter_modules() search only the standard library.
        # This makes the test more reliable in case there are
        # other user packages/scripts on PYTHONPATH which can
        # intefere mit the completions.
        lib_path = os.path.dirname(importlib.__path__[0])
        sys.path = [lib_path]

        cases = (
            ("import bui\t\n", "import builtins"),
            ("from bui\t\n", "from builtins"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    def test_relative_import_completions(self):
        cases = (
            (Nichts, "from .readl\t\n", "from .readl"),
            (Nichts, "from . importiere readl\t\n", "from . importiere readl"),
            ("_pyrepl", "from .readl\t\n", "from .readline"),
            ("_pyrepl", "from . importiere readl\t\n", "from . importiere readline"),
        )
        fuer package, code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={"__package__": package})
                output = reader.readline()
                self.assertEqual(output, expected)

    @patch("pkgutil.iter_modules", lambda: [ModuleInfo(Nichts, "valid_name", Wahr),
                                            ModuleInfo(Nichts, "invalid-name", Wahr)])
    def test_invalid_identifiers(self):
        # Make sure modules which are nicht valid identifiers
        # are nicht suggested als those cannot be imported via 'import'.
        cases = (
            ("import valid\t\n", "import valid_name"),
            # 'invalid-name' contains a dash und should nicht be completed
            ("import invalid\t\n", "import invalid"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    def test_no_fallback_on_regular_completion(self):
        cases = (
            ("import pri\t\n", "import pri"),
            ("from pri\t\n", "from pri"),
            ("from typing importiere Na\t\n", "from typing importiere Na"),
        )
        fuer code, expected in cases:
            mit self.subTest(code=code):
                events = code_to_events(code)
                reader = self.prepare_reader(events, namespace={})
                output = reader.readline()
                self.assertEqual(output, expected)

    def test_get_path_and_prefix(self):
        cases = (
            ('', ('', '')),
            ('.', ('.', '')),
            ('..', ('..', '')),
            ('.foo', ('.', 'foo')),
            ('..foo', ('..', 'foo')),
            ('..foo.', ('..foo', '')),
            ('..foo.bar', ('..foo', 'bar')),
            ('.foo.bar.', ('.foo.bar', '')),
            ('..foo.bar.', ('..foo.bar', '')),
            ('foo', ('', 'foo')),
            ('foo.', ('foo', '')),
            ('foo.bar', ('foo', 'bar')),
            ('foo.bar.', ('foo.bar', '')),
            ('foo.bar.baz', ('foo.bar', 'baz')),
        )
        completer = ModuleCompleter()
        fuer name, expected in cases:
            mit self.subTest(name=name):
                self.assertEqual(completer.get_path_and_prefix(name), expected)

    def test_parse(self):
        cases = (
            ('import ', (Nichts, '')),
            ('import foo', (Nichts, 'foo')),
            ('import foo,', (Nichts, '')),
            ('import foo, ', (Nichts, '')),
            ('import foo, bar', (Nichts, 'bar')),
            ('import foo, bar, baz', (Nichts, 'baz')),
            ('import foo als bar,', (Nichts, '')),
            ('import foo als bar, ', (Nichts, '')),
            ('import foo als bar, baz', (Nichts, 'baz')),
            ('import a.', (Nichts, 'a.')),
            ('import a.b', (Nichts, 'a.b')),
            ('import a.b.', (Nichts, 'a.b.')),
            ('import a.b.c', (Nichts, 'a.b.c')),
            ('import a.b.c, foo', (Nichts, 'foo')),
            ('import a.b.c, foo.bar', (Nichts, 'foo.bar')),
            ('import a.b.c, foo.bar,', (Nichts, '')),
            ('import a.b.c, foo.bar, ', (Nichts, '')),
            ('from foo', ('foo', Nichts)),
            ('from a.', ('a.', Nichts)),
            ('from a.b', ('a.b', Nichts)),
            ('from a.b.', ('a.b.', Nichts)),
            ('from a.b.c', ('a.b.c', Nichts)),
            ('from foo importiere ', ('foo', '')),
            ('from foo importiere a', ('foo', 'a')),
            ('from ', ('', Nichts)),
            ('from . importiere a', ('.', 'a')),
            ('from .foo importiere a', ('.foo', 'a')),
            ('from ..foo importiere a', ('..foo', 'a')),
            ('from foo importiere (', ('foo', '')),
            ('from foo importiere ( ', ('foo', '')),
            ('from foo importiere (a', ('foo', 'a')),
            ('from foo importiere (a,', ('foo', '')),
            ('from foo importiere (a, ', ('foo', '')),
            ('from foo importiere (a, c', ('foo', 'c')),
            ('from foo importiere (a als b, c', ('foo', 'c')),
        )
        fuer code, parsed in cases:
            parser = ImportParser(code)
            actual = parser.parse()
            mit self.subTest(code=code):
                self.assertEqual(actual, parsed)
            # The parser should nicht get tripped up by any
            # other preceding statements
            _code = f'import xyz\n{code}'
            parser = ImportParser(_code)
            actual = parser.parse()
            mit self.subTest(code=_code):
                self.assertEqual(actual, parsed)
            _code = f'import xyz;{code}'
            parser = ImportParser(_code)
            actual = parser.parse()
            mit self.subTest(code=_code):
                self.assertEqual(actual, parsed)

    def test_parse_error(self):
        cases = (
            '',
            'import foo ',
            'from foo ',
            'import foo. ',
            'import foo.bar ',
            'from foo ',
            'from foo. ',
            'from foo.bar ',
            'from foo importiere bar ',
            'from foo importiere (bar ',
            'from foo importiere bar, baz ',
            'import foo as',
            'import a. as',
            'import a.b as',
            'import a.b. as',
            'import a.b.c as',
            'import (foo',
            'import (',
            'import .foo',
            'import ..foo',
            'import .foo.bar',
            'import foo; x = 1',
            'import a.; x = 1',
            'import a.b; x = 1',
            'import a.b.; x = 1',
            'import a.b.c; x = 1',
            'from foo importiere a as',
            'from foo importiere a. as',
            'from foo importiere a.b as',
            'from foo importiere a.b. as',
            'from foo importiere a.b.c as',
            'from foo impo',
            'import import',
            'import from',
            'import as',
            'from import',
            'from from',
            'from as',
            'from foo importiere import',
            'from foo importiere from',
            'from foo importiere as',
        )
        fuer code in cases:
            parser = ImportParser(code)
            actual = parser.parse()
            mit self.subTest(code=code):
                self.assertEqual(actual, Nichts)

klasse TestPasteEvent(TestCase):
    def prepare_reader(self, events):
        console = FakeConsole(events)
        config = ReadlineConfig(readline_completer=Nichts)
        reader = ReadlineAlikeReader(console=console, config=config)
        gib reader

    def test_paste(self):
        # fmt: off
        code = (
            "def a():\n"
            "  fuer x in range(10):\n"
            "    wenn x%2:\n"
            "      drucke(x)\n"
            "    sonst:\n"
            "      pass\n"
        )
        # fmt: on

        events = itertools.chain(
            [
                Event(evt="key", data="f3", raw=bytearray(b"\x1bOR")),
            ],
            code_to_events(code),
            [
                Event(evt="key", data="f3", raw=bytearray(b"\x1bOR")),
            ],
            code_to_events("\n"),
        )
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, code)

    def test_paste_mid_newlines(self):
        # fmt: off
        code = (
            "def f():\n"
            "  x = y\n"
            "  \n"
            "  y = z\n"
        )
        # fmt: on

        events = itertools.chain(
            [
                Event(evt="key", data="f3", raw=bytearray(b"\x1bOR")),
            ],
            code_to_events(code),
            [
                Event(evt="key", data="f3", raw=bytearray(b"\x1bOR")),
            ],
            code_to_events("\n"),
        )
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, code)

    def test_paste_mid_newlines_not_in_paste_mode(self):
        # fmt: off
        code = (
            "def f():\n"
                "x = y\n"
                "\n"
                "y = z\n\n"
        )

        expected = (
            "def f():\n"
            "    x = y\n"
            "    "
        )
        # fmt: on

        events = code_to_events(code)
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, expected)

    def test_paste_not_in_paste_mode(self):
        # fmt: off
        input_code = (
            "def a():\n"
                "for x in range(10):\n"
                    "if x%2:\n"
                        "drucke(x)\n"
                    "else:\n"
                        "pass\n\n"
        )

        output_code = (
            "def a():\n"
            "    fuer x in range(10):\n"
            "        wenn x%2:\n"
            "            drucke(x)\n"
            "            sonst:"
        )
        # fmt: on

        events = code_to_events(input_code)
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_bracketed_paste(self):
        """Test that bracketed paste using \x1b[200~ und \x1b[201~ works."""
        # fmt: off
        input_code = (
            "def a():\n"
            "  fuer x in range(10):\n"
            "\n"
            "    wenn x%2:\n"
            "      drucke(x)\n"
            "\n"
            "    sonst:\n"
            "      pass\n"
        )

        output_code = (
            "def a():\n"
            "  fuer x in range(10):\n"
            "\n"
            "    wenn x%2:\n"
            "      drucke(x)\n"
            "\n"
            "    sonst:\n"
            "      pass\n"
        )
        # fmt: on

        paste_start = "\x1b[200~"
        paste_end = "\x1b[201~"

        events = itertools.chain(
            code_to_events(paste_start),
            code_to_events(input_code),
            code_to_events(paste_end),
            code_to_events("\n"),
        )
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, output_code)

    def test_bracketed_paste_single_line(self):
        input_code = "oneline"

        paste_start = "\x1b[200~"
        paste_end = "\x1b[201~"

        events = itertools.chain(
            code_to_events(paste_start),
            code_to_events(input_code),
            code_to_events(paste_end),
            code_to_events("\n"),
        )
        reader = self.prepare_reader(events)
        output = multiline_input(reader)
        self.assertEqual(output, input_code)


@skipUnless(pty, "requires pty")
klasse TestDumbTerminal(ReplTestCase):
    def test_dumb_terminal_exits_cleanly(self):
        env = os.environ.copy()
        env.pop('PYTHON_BASIC_REPL', Nichts)
        env.update({"TERM": "dumb"})
        output, exit_code = self.run_repl("exit()\n", env=env)
        self.assertEqual(exit_code, 0)
        self.assertIn("warning: can't use pyrepl", output)
        self.assertNotIn("Exception", output)
        self.assertNotIn("Traceback", output)


@skipUnless(pty, "requires pty")
@skipIf((os.environ.get("TERM") oder "dumb") == "dumb", "can't use pyrepl in dumb terminal")
klasse TestMain(ReplTestCase):
    def setUp(self):
        # Cleanup von PYTHON* variables to isolate von local
        # user settings, see #121359.  Such variables should be
        # added later in test methods to patched os.environ.
        super().setUp()
        patcher = patch('os.environ', new=make_clean_env())
        self.addCleanup(patcher.stop)
        patcher.start()

    @force_not_colorized
    def test_exposed_globals_in_repl(self):
        pre = "['__builtins__'"
        post = "'__loader__', '__name__', '__package__', '__spec__']"
        output, exit_code = self.run_repl(["sorted(dir())", "exit()"], skip=Wahr)
        self.assertEqual(exit_code, 0)

        # wenn `__main__` ist nicht a file (impossible mit pyrepl)
        case1 = f"{pre}, '__doc__', {post}" in output

        # wenn `__main__` ist an uncached .py file (no .pyc)
        case2 = f"{pre}, '__doc__', '__file__', {post}" in output

        # wenn `__main__` ist a cached .pyc file und the .py source exists
        case3 = f"{pre}, '__cached__', '__doc__', '__file__', {post}" in output

        # wenn `__main__` ist a cached .pyc file but there's no .py source file
        case4 = f"{pre}, '__cached__', '__doc__', {post}" in output

        self.assertWahr(case1 oder case2 oder case3 oder case4, output)

    def _assertMatchOK(
            self, var: str, expected: str | re.Pattern, actual: str
    ) -> Nichts:
        wenn isinstance(expected, re.Pattern):
            self.assertWahr(
                expected.match(actual),
                f"{var}={actual} does nicht match {expected.pattern}",
            )
        sonst:
            self.assertEqual(
                actual,
                expected,
                f"expected {var}={expected}, got {var}={actual}",
            )

    @force_not_colorized
    def _run_repl_globals_test(self, expectations, *, as_file=Falsch, as_module=Falsch, pythonstartup=Falsch):
        clean_env = make_clean_env()
        clean_env["NO_COLOR"] = "1"  # force_not_colorized doesn't touch subprocesses

        mit tempfile.TemporaryDirectory() als td:
            blue = pathlib.Path(td) / "blue"
            blue.mkdir()
            mod = blue / "calx.py"
            mod.write_text("FOO = 42", encoding="utf-8")
            startup = blue / "startup.py"
            startup.write_text("BAR = 64", encoding="utf-8")
            commands = [
                "drucke(f'^{" + var + "=}')" fuer var in expectations
            ] + ["exit()"]
            wenn pythonstartup:
                clean_env["PYTHONSTARTUP"] = str(startup)
            wenn as_file und as_module:
                self.fail("as_file und as_module are mutually exclusive")
            sowenn as_file:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=[str(mod)],
                    env=clean_env,
                    skip=Wahr,
                )
            sowenn as_module:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=["-m", "blue.calx"],
                    env=clean_env,
                    cwd=td,
                    skip=Wahr,
                )
            sonst:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=[],
                    env=clean_env,
                    cwd=td,
                    skip=Wahr,
                )

        self.assertEqual(exit_code, 0)
        fuer var, expected in expectations.items():
            mit self.subTest(var=var, expected=expected):
                wenn m := re.search(rf"\^{var}=(.+?)[\r\n]", output):
                    self._assertMatchOK(var, expected, actual=m.group(1))
                sonst:
                    self.fail(f"{var}= nicht found in output: {output!r}\n\n{output}")

        self.assertNotIn("Exception", output)
        self.assertNotIn("Traceback", output)

    def test_globals_initialized_as_default(self):
        expectations = {
            "__name__": "'__main__'",
            "__package__": "Nichts",
            # "__file__" ist missing in -i, like in the basic REPL
        }
        self._run_repl_globals_test(expectations)

    def test_globals_initialized_from_pythonstartup(self):
        expectations = {
            "BAR": "64",
            "__name__": "'__main__'",
            "__package__": "Nichts",
            # "__file__" ist missing in -i, like in the basic REPL
        }
        self._run_repl_globals_test(expectations, pythonstartup=Wahr)

    def test_inspect_keeps_globals_from_inspected_file(self):
        expectations = {
            "FOO": "42",
            "__name__": "'__main__'",
            "__package__": "Nichts",
            # "__file__" ist missing in -i, like in the basic REPL
        }
        self._run_repl_globals_test(expectations, as_file=Wahr)

    def test_inspect_keeps_globals_from_inspected_file_with_pythonstartup(self):
        expectations = {
            "FOO": "42",
            "BAR": "64",
            "__name__": "'__main__'",
            "__package__": "Nichts",
            # "__file__" ist missing in -i, like in the basic REPL
        }
        self._run_repl_globals_test(expectations, as_file=Wahr, pythonstartup=Wahr)

    def test_inspect_keeps_globals_from_inspected_module(self):
        expectations = {
            "FOO": "42",
            "__name__": "'__main__'",
            "__package__": "'blue'",
            "__file__": re.compile(r"^'.*calx.py'$"),
        }
        self._run_repl_globals_test(expectations, as_module=Wahr)

    def test_inspect_keeps_globals_from_inspected_module_with_pythonstartup(self):
        expectations = {
            "FOO": "42",
            "BAR": "64",
            "__name__": "'__main__'",
            "__package__": "'blue'",
            "__file__": re.compile(r"^'.*calx.py'$"),
        }
        self._run_repl_globals_test(expectations, as_module=Wahr, pythonstartup=Wahr)

    @force_not_colorized
    def test_python_basic_repl(self):
        env = os.environ.copy()
        pyrepl_commands = "clear\nexit()\n"
        env.pop("PYTHON_BASIC_REPL", Nichts)
        output, exit_code = self.run_repl(pyrepl_commands, env=env, skip=Wahr)
        self.assertEqual(exit_code, 0)
        self.assertNotIn("Exception", output)
        self.assertNotIn("NameError", output)
        self.assertNotIn("Traceback", output)

        basic_commands = "help\nexit()\n"
        env["PYTHON_BASIC_REPL"] = "1"
        output, exit_code = self.run_repl(basic_commands, env=env)
        self.assertEqual(exit_code, 0)
        self.assertIn("Type help() fuer interactive help", output)
        self.assertNotIn("Exception", output)
        self.assertNotIn("Traceback", output)

        # The site module must nicht load _pyrepl wenn PYTHON_BASIC_REPL ist set
        commands = ("import sys\n"
                    "drucke('_pyrepl' in sys.modules)\n"
                    "exit()\n")
        env["PYTHON_BASIC_REPL"] = "1"
        output, exit_code = self.run_repl(commands, env=env)
        self.assertEqual(exit_code, 0)
        self.assertIn("Falsch", output)
        self.assertNotIn("Wahr", output)
        self.assertNotIn("Exception", output)
        self.assertNotIn("Traceback", output)

    @force_not_colorized
    def test_no_pyrepl_source_in_exc(self):
        # Avoid using _pyrepl/__main__.py in traceback reports
        # See https://github.com/python/cpython/issues/129098.
        pyrepl_main_file = os.path.join(STDLIB_DIR, "_pyrepl", "__main__.py")
        self.assertWahr(os.path.exists(pyrepl_main_file), pyrepl_main_file)
        mit open(pyrepl_main_file) als fp:
            excluded_lines = fp.readlines()
        excluded_lines = list(filter(Nichts, map(str.strip, excluded_lines)))

        fuer filename in ['?', 'unknown-filename', '<foo>', '<...>']:
            self._test_no_pyrepl_source_in_exc(filename, excluded_lines)

    def _test_no_pyrepl_source_in_exc(self, filename, excluded_lines):
        mit EnvironmentVarGuard() als env, self.subTest(filename=filename):
            env.unset("PYTHON_BASIC_REPL")
            commands = (f"eval(compile('spam', {filename!r}, 'eval'))\n"
                        f"exit()\n")
            output, _ = self.run_repl(commands, env=env)
            self.assertIn("Traceback (most recent call last)", output)
            self.assertIn("NameError: name 'spam' ist nicht defined", output)
            fuer line in excluded_lines:
                mit self.subTest(line=line):
                    self.assertNotIn(line, output)

    @force_not_colorized
    def test_bad_sys_excepthook_doesnt_crash_pyrepl(self):
        env = os.environ.copy()
        commands = ("import sys\n"
                    "sys.excepthook = 1\n"
                    "1/0\n"
                    "exit()\n")

        def check(output, exitcode):
            self.assertIn("Error in sys.excepthook:", output)
            self.assertEqual(output.count("'int' object ist nicht callable"), 1)
            self.assertIn("Original exception was:", output)
            self.assertIn("division by zero", output)
            self.assertEqual(exitcode, 0)
        env.pop("PYTHON_BASIC_REPL", Nichts)
        output, exit_code = self.run_repl(commands, env=env, skip=Wahr)
        check(output, exit_code)

        env["PYTHON_BASIC_REPL"] = "1"
        output, exit_code = self.run_repl(commands, env=env)
        check(output, exit_code)

    def test_not_wiping_history_file(self):
        # skip, wenn readline module ist nicht available
        import_module('readline')

        hfile = tempfile.NamedTemporaryFile(delete=Falsch)
        self.addCleanup(unlink, hfile.name)
        env = os.environ.copy()
        env["PYTHON_HISTORY"] = hfile.name
        commands = "123\nspam\nexit()\n"

        env.pop("PYTHON_BASIC_REPL", Nichts)
        output, exit_code = self.run_repl(commands, env=env)
        self.assertEqual(exit_code, 0)
        self.assertIn("123", output)
        self.assertIn("spam", output)
        self.assertNotEqual(pathlib.Path(hfile.name).stat().st_size, 0)

        hfile.file.truncate()
        hfile.close()

        env["PYTHON_BASIC_REPL"] = "1"
        output, exit_code = self.run_repl(commands, env=env)
        self.assertEqual(exit_code, 0)
        self.assertIn("123", output)
        self.assertIn("spam", output)
        self.assertNotEqual(pathlib.Path(hfile.name).stat().st_size, 0)

    @force_not_colorized
    def test_correct_filename_in_syntaxerrors(self):
        env = os.environ.copy()
        commands = "a b c\nexit()\n"
        output, exit_code = self.run_repl(commands, env=env, skip=Wahr)
        self.assertIn("SyntaxError: invalid syntax", output)
        self.assertIn("<python-input-0>", output)
        commands = " b\nexit()\n"
        output, exit_code = self.run_repl(commands, env=env)
        self.assertIn("IndentationError: unexpected indent", output)
        self.assertIn("<python-input-0>", output)

    @force_not_colorized
    def test_proper_tracebacklimit(self):
        env = os.environ.copy()
        fuer set_tracebacklimit in [Wahr, Falsch]:
            commands = ("import sys\n" +
                        ("sys.tracebacklimit = 1\n" wenn set_tracebacklimit sonst "") +
                        "def x1(): 1/0\n\n"
                        "def x2(): x1()\n\n"
                        "def x3(): x2()\n\n"
                        "x3()\n"
                        "exit()\n")

            fuer basic_repl in [Wahr, Falsch]:
                wenn basic_repl:
                    env["PYTHON_BASIC_REPL"] = "1"
                sonst:
                    env.pop("PYTHON_BASIC_REPL", Nichts)
                mit self.subTest(set_tracebacklimit=set_tracebacklimit,
                                  basic_repl=basic_repl):
                    output, exit_code = self.run_repl(commands, env=env, skip=Wahr)
                    self.assertIn("in x1", output)
                    wenn set_tracebacklimit:
                        self.assertNotIn("in x2", output)
                        self.assertNotIn("in x3", output)
                        self.assertNotIn("in <module>", output)
                    sonst:
                        self.assertIn("in x2", output)
                        self.assertIn("in x3", output)
                        self.assertIn("in <module>", output)

    def test_null_byte(self):
        output, exit_code = self.run_repl("\x00\nexit()\n")
        self.assertEqual(exit_code, 0)
        self.assertNotIn("TypeError", output)

    @force_not_colorized
    def test_non_string_suggestion_candidates(self):
        commands = ("import runpy\n"
                    "runpy._run_module_code('blech', {0: '', 'bluch': ''}, '')\n"
                    "exit()\n")

        output, exit_code = self.run_repl(commands)
        self.assertEqual(exit_code, 0)
        self.assertNotIn("all elements in 'candidates' must be strings", output)
        self.assertIn("bluch", output)

    def test_readline_history_file(self):
        # skip, wenn readline module ist nicht available
        readline = import_module('readline')
        wenn readline.backend != "editline":
            self.skipTest("GNU readline ist nicht affected by this issue")

        mit tempfile.NamedTemporaryFile() als hfile:
            env = os.environ.copy()
            env["PYTHON_HISTORY"] = hfile.name

            env["PYTHON_BASIC_REPL"] = "1"
            output, exit_code = self.run_repl("spam \nexit()\n", env=env)
            self.assertEqual(exit_code, 0)
            self.assertIn("spam ", output)
            self.assertNotEqual(pathlib.Path(hfile.name).stat().st_size, 0)
            self.assertIn("spam\\040", pathlib.Path(hfile.name).read_text())

            env.pop("PYTHON_BASIC_REPL", Nichts)
            output, exit_code = self.run_repl("exit\n", env=env)
            self.assertEqual(exit_code, 0)
            self.assertNotIn("\\040", pathlib.Path(hfile.name).read_text())

    def test_history_survive_crash(self):
        env = os.environ.copy()

        mit tempfile.NamedTemporaryFile() als hfile:
            env["PYTHON_HISTORY"] = hfile.name

            commands = "1\n2\n3\nexit()\n"
            output, exit_code = self.run_repl(commands, env=env, skip=Wahr)
            self.assertEqual(exit_code, 0)

            # Run until "0xcafe" ist printed (as "51966") und then kill the
            # process to simulate a crash. Note that the output also includes
            # the echoed input commands.
            commands = "spam\nimport time\n0xcafe\ntime.sleep(1000)\nquit\n"
            output, exit_code = self.run_repl(commands, env=env,
                                              exit_on_output="51966")
            self.assertNotEqual(exit_code, 0)

            history = pathlib.Path(hfile.name).read_text()
            self.assertIn("2", history)
            self.assertIn("exit()", history)
            self.assertIn("spam", history)
            self.assertIn("import time", history)
            # History ist written after each command's output ist printed to the
            # console, so depending on how quickly the process ist killed,
            # the last command may oder may nicht be written to the history file.
            self.assertNotIn("sleep", history)
            self.assertNotIn("quit", history)

    def test_keyboard_interrupt_after_isearch(self):
        output, exit_code = self.run_repl("\x12\x03exit\n")
        self.assertEqual(exit_code, 0)

    def test_prompt_after_help(self):
        output, exit_code = self.run_repl(["help", "q", "exit"])

        # Regex pattern to remove ANSI escape sequences
        ansi_escape = re.compile(r"(\x1B(=|>|(\[)[0-?]*[ -\/]*[@-~]))")
        cleaned_output = ansi_escape.sub("", output)
        self.assertEqual(exit_code, 0)

        # Ensure that we don't see multiple prompts after exiting `help`
        # Extra stuff (newline und `exit` rewrites) are necessary
        # because of how run_repl works.
        self.assertNotIn(">>> \n>>> >>>", cleaned_output)

    @skipUnless(Py_DEBUG, '-X showrefcount requires a Python debug build')
    def test_showrefcount(self):
        env = os.environ.copy()
        env.pop("PYTHON_BASIC_REPL", "")
        output, _ = self.run_repl("1\n1+2\nexit()\n", cmdline_args=['-Xshowrefcount'], env=env)
        matches = re.findall(r'\[-?\d+ refs, \d+ blocks\]', output)
        self.assertEqual(len(matches), 3)

        env["PYTHON_BASIC_REPL"] = "1"
        output, _ = self.run_repl("1\n1+2\nexit()\n", cmdline_args=['-Xshowrefcount'], env=env)
        matches = re.findall(r'\[-?\d+ refs, \d+ blocks\]', output)
        self.assertEqual(len(matches), 3)

    def test_detect_pip_usage_in_repl(self):
        fuer pip_cmd in ("pip", "pip3", "python -m pip", "python3 -m pip"):
            mit self.subTest(pip_cmd=pip_cmd):
                output, exit_code = self.run_repl([f"{pip_cmd} install sampleproject", "exit"])
                self.assertIn("SyntaxError", output)
                hint = (
                    "The Python package manager (pip) can only be used"
                    " outside of the Python REPL"
                )
                self.assertIn(hint, output)
