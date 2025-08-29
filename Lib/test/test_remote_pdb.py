importiere io
importiere itertools
importiere json
importiere os
importiere re
importiere signal
importiere socket
importiere subprocess
importiere sys
importiere textwrap
importiere unittest
importiere unittest.mock
von contextlib importiere closing, contextmanager, redirect_stdout, redirect_stderr, ExitStack
von test.support importiere is_wasi, cpython_only, force_color, requires_subprocess, SHORT_TIMEOUT, subTests
von test.support.os_helper importiere TESTFN, unlink
von typing importiere List

importiere pdb
von pdb importiere _PdbServer, _PdbClient


wenn nicht sys.is_remote_debug_enabled():
    raise unittest.SkipTest('remote debugging is disabled')


@contextmanager
def kill_on_error(proc):
    """Context manager killing the subprocess wenn a Python exception is raised."""
    mit proc:
        try:
            liefere proc
        except:
            proc.kill()
            raise


klasse MockSocketFile:
    """Mock socket file fuer testing _PdbServer without actual socket connections."""

    def __init__(self):
        self.input_queue = []
        self.output_buffer = []

    def write(self, data: bytes) -> Nichts:
        """Simulate write to socket."""
        self.output_buffer.append(data)

    def flush(self) -> Nichts:
        """No-op flush implementation."""
        pass

    def readline(self) -> bytes:
        """Read a line von the prepared input queue."""
        wenn nicht self.input_queue:
            gib b""
        gib self.input_queue.pop(0)

    def close(self) -> Nichts:
        """Close the mock socket file."""
        pass

    def add_input(self, data: dict) -> Nichts:
        """Add input that will be returned by readline."""
        self.input_queue.append(json.dumps(data).encode() + b"\n")

    def get_output(self) -> List[dict]:
        """Get the output that was written by the object being tested."""
        results = []
        fuer data in self.output_buffer:
            wenn isinstance(data, bytes) und data.endswith(b"\n"):
                try:
                    results.append(json.loads(data.decode().strip()))
                except json.JSONDecodeError:
                    pass  # Ignore non-JSON output
        self.output_buffer = []
        gib results


klasse PdbClientTestCase(unittest.TestCase):
    """Tests fuer the _PdbClient class."""

    def do_test(
        self,
        *,
        incoming,
        simulate_send_failure=Falsch,
        simulate_sigint_during_stdout_write=Falsch,
        use_interrupt_socket=Falsch,
        expected_outgoing=Nichts,
        expected_outgoing_signals=Nichts,
        expected_completions=Nichts,
        expected_exception=Nichts,
        expected_stdout="",
        expected_stdout_substring="",
        expected_state=Nichts,
    ):
        wenn expected_outgoing is Nichts:
            expected_outgoing = []
        wenn expected_outgoing_signals is Nichts:
            expected_outgoing_signals = []
        wenn expected_completions is Nichts:
            expected_completions = []
        wenn expected_state is Nichts:
            expected_state = {}

        expected_state.setdefault("write_failed", Falsch)
        messages = [m fuer source, m in incoming wenn source == "server"]
        prompts = [m["prompt"] fuer source, m in incoming wenn source == "user"]

        input_iter = (m fuer source, m in incoming wenn source == "user")
        completions = []

        def mock_input(prompt):
            message = next(input_iter, Nichts)
            wenn message is Nichts:
                raise EOFError

            wenn req := message.get("completion_request"):
                readline_mock = unittest.mock.Mock()
                readline_mock.get_line_buffer.return_value = req["line"]
                readline_mock.get_begidx.return_value = req["begidx"]
                readline_mock.get_endidx.return_value = req["endidx"]
                unittest.mock.seal(readline_mock)
                mit unittest.mock.patch.dict(sys.modules, {"readline": readline_mock}):
                    fuer param in itertools.count():
                        prefix = req["line"][req["begidx"] : req["endidx"]]
                        completion = client.complete(prefix, param)
                        wenn completion is Nichts:
                            breche
                        completions.append(completion)

            reply = message["input"]
            wenn isinstance(reply, BaseException):
                raise reply
            wenn isinstance(reply, str):
                gib reply
            gib reply()

        mit ExitStack() als stack:
            client_sock, server_sock = socket.socketpair()
            stack.enter_context(closing(client_sock))
            stack.enter_context(closing(server_sock))

            server_sock = unittest.mock.Mock(wraps=server_sock)

            client_sock.sendall(
                b"".join(
                    (m wenn isinstance(m, bytes) sonst json.dumps(m).encode()) + b"\n"
                    fuer m in messages
                )
            )
            client_sock.shutdown(socket.SHUT_WR)

            wenn simulate_send_failure:
                server_sock.sendall = unittest.mock.Mock(
                    side_effect=OSError("sendall failed")
                )
                client_sock.shutdown(socket.SHUT_RD)

            stdout = io.StringIO()

            wenn simulate_sigint_during_stdout_write:
                orig_stdout_write = stdout.write

                def sigint_stdout_write(s):
                    signal.raise_signal(signal.SIGINT)
                    gib orig_stdout_write(s)

                stdout.write = sigint_stdout_write

            input_mock = stack.enter_context(
                unittest.mock.patch("pdb.input", side_effect=mock_input)
            )
            stack.enter_context(redirect_stdout(stdout))

            wenn use_interrupt_socket:
                interrupt_sock = unittest.mock.Mock(spec=socket.socket)
                mock_kill = Nichts
            sonst:
                interrupt_sock = Nichts
                mock_kill = stack.enter_context(
                    unittest.mock.patch("os.kill", spec=os.kill)
                )

            client = _PdbClient(
                pid=12345,
                server_socket=server_sock,
                interrupt_sock=interrupt_sock,
            )

            wenn expected_exception is nicht Nichts:
                exception = expected_exception["exception"]
                msg = expected_exception["msg"]
                stack.enter_context(self.assertRaises(exception, msg=msg))

            client.cmdloop()

        sent_msgs = [msg.args[0] fuer msg in server_sock.sendall.mock_calls]
        fuer msg in sent_msgs:
            assert msg.endswith(b"\n")
        actual_outgoing = [json.loads(msg) fuer msg in sent_msgs]

        self.assertEqual(actual_outgoing, expected_outgoing)
        self.assertEqual(completions, expected_completions)
        wenn expected_stdout_substring und nicht expected_stdout:
            self.assertIn(expected_stdout_substring, stdout.getvalue())
        sonst:
            self.assertEqual(stdout.getvalue(), expected_stdout)
        input_mock.assert_has_calls([unittest.mock.call(p) fuer p in prompts])
        actual_state = {k: getattr(client, k) fuer k in expected_state}
        self.assertEqual(actual_state, expected_state)

        wenn use_interrupt_socket:
            outgoing_signals = [
                signal.Signals(int.from_bytes(call.args[0]))
                fuer call in interrupt_sock.sendall.call_args_list
            ]
        sonst:
            assert mock_kill is nicht Nichts
            outgoing_signals = []
            fuer call in mock_kill.call_args_list:
                pid, signum = call.args
                self.assertEqual(pid, 12345)
                outgoing_signals.append(signal.Signals(signum))
        self.assertEqual(outgoing_signals, expected_outgoing_signals)

    def test_remote_immediately_closing_the_connection(self):
        """Test the behavior when the remote closes the connection immediately."""
        incoming = []
        expected_outgoing = []
        self.do_test(
            incoming=incoming,
            expected_outgoing=expected_outgoing,
        )

    def test_handling_command_list(self):
        """Test handling the command_list message."""
        incoming = [
            ("server", {"command_list": ["help", "list", "continue"]}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_state={
                "pdb_commands": {"help", "list", "continue"},
            },
        )

    def test_handling_info_message(self):
        """Test handling a message payload mit type='info'."""
        incoming = [
            ("server", {"message": "Some message oder other\n", "type": "info"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout="Some message oder other\n",
        )

    def test_handling_error_message(self):
        """Test handling a message payload mit type='error'."""
        incoming = [
            ("server", {"message": "Some message oder other.", "type": "error"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout="*** Some message oder other.\n",
        )

    def test_handling_other_message(self):
        """Test handling a message payload mit an unrecognized type."""
        incoming = [
            ("server", {"message": "Some message.\n", "type": "unknown"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout="Some message.\n",
        )

    @unittest.skipIf(sys.flags.optimize >= 2, "Help nicht available fuer -OO")
    @subTests(
        "help_request,expected_substring",
        [
            # a request to display help fuer a command
            ({"help": "ll"}, "Usage: ll | longlist"),
            # a request to display a help overview
            ({"help": ""}, "type help <topic>"),
            # a request to display the full PDB manual
            ({"help": "pdb"}, ">>> importiere pdb"),
        ],
    )
    def test_handling_help_when_available(self, help_request, expected_substring):
        """Test handling help requests when help is available."""
        incoming = [
            ("server", help_request),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout_substring=expected_substring,
        )

    @unittest.skipIf(sys.flags.optimize < 2, "Needs -OO")
    @subTests(
        "help_request,expected_substring",
        [
            # a request to display help fuer a command
            ({"help": "ll"}, "No help fuer 'll'"),
            # a request to display a help overview
            ({"help": ""}, "Undocumented commands"),
            # a request to display the full PDB manual
            ({"help": "pdb"}, "No help fuer 'pdb'"),
        ],
    )
    def test_handling_help_when_not_available(self, help_request, expected_substring):
        """Test handling help requests when help is nicht available."""
        incoming = [
            ("server", help_request),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout_substring=expected_substring,
        )

    def test_handling_pdb_prompts(self):
        """Test responding to pdb's normal prompts."""
        incoming = [
            ("server", {"command_list": ["b"]}),
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": "lst ["}),
            ("user", {"prompt": "...   ", "input": "0 ]"}),
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": ""}),
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": "b ["}),
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": "! b ["}),
            ("user", {"prompt": "...   ", "input": "b ]"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "lst [\n0 ]"},
                {"reply": ""},
                {"reply": "b ["},
                {"reply": "!b [\nb ]"},
            ],
            expected_state={"state": "pdb"},
        )

    def test_handling_interact_prompts(self):
        """Test responding to pdb's interact mode prompts."""
        incoming = [
            ("server", {"command_list": ["b"]}),
            ("server", {"prompt": ">>> ", "state": "interact"}),
            ("user", {"prompt": ">>> ", "input": "lst ["}),
            ("user", {"prompt": "... ", "input": "0 ]"}),
            ("server", {"prompt": ">>> ", "state": "interact"}),
            ("user", {"prompt": ">>> ", "input": ""}),
            ("server", {"prompt": ">>> ", "state": "interact"}),
            ("user", {"prompt": ">>> ", "input": "b ["}),
            ("user", {"prompt": "... ", "input": "b ]"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "lst [\n0 ]"},
                {"reply": ""},
                {"reply": "b [\nb ]"},
            ],
            expected_state={"state": "interact"},
        )

    def test_retry_pdb_prompt_on_syntax_error(self):
        """Test re-prompting after a SyntaxError in a Python expression."""
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": " lst ["}),
            ("user", {"prompt": "(Pdb) ", "input": "lst ["}),
            ("user", {"prompt": "...   ", "input": " 0 ]"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "lst [\n 0 ]"},
            ],
            expected_stdout_substring="*** IndentationError",
            expected_state={"state": "pdb"},
        )

    def test_retry_interact_prompt_on_syntax_error(self):
        """Test re-prompting after a SyntaxError in a Python expression."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            ("user", {"prompt": ">>> ", "input": "!lst ["}),
            ("user", {"prompt": ">>> ", "input": "lst ["}),
            ("user", {"prompt": "... ", "input": " 0 ]"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "lst [\n 0 ]"},
            ],
            expected_stdout_substring="*** SyntaxError",
            expected_state={"state": "interact"},
        )

    def test_handling_unrecognized_prompt_type(self):
        """Test fallback to "dumb" single-line mode fuer unknown states."""
        incoming = [
            ("server", {"prompt": "Do it? ", "state": "confirm"}),
            ("user", {"prompt": "Do it? ", "input": "! ["}),
            ("server", {"prompt": "Do it? ", "state": "confirm"}),
            ("user", {"prompt": "Do it? ", "input": "echo hello"}),
            ("server", {"prompt": "Do it? ", "state": "confirm"}),
            ("user", {"prompt": "Do it? ", "input": ""}),
            ("server", {"prompt": "Do it? ", "state": "confirm"}),
            ("user", {"prompt": "Do it? ", "input": "echo goodbye"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "! ["},
                {"reply": "echo hello"},
                {"reply": ""},
                {"reply": "echo goodbye"},
            ],
            expected_state={"state": "dumb"},
        )

    def test_sigint_at_prompt(self):
        """Test signaling when a prompt gets interrupted."""
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            (
                "user",
                {
                    "prompt": "(Pdb) ",
                    "input": lambda: signal.raise_signal(signal.SIGINT),
                },
            ),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"signal": "INT"},
            ],
            expected_state={"state": "pdb"},
        )

    def test_sigint_at_continuation_prompt(self):
        """Test signaling when a continuation prompt gets interrupted."""
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": "if Wahr:"}),
            (
                "user",
                {
                    "prompt": "...   ",
                    "input": lambda: signal.raise_signal(signal.SIGINT),
                },
            ),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"signal": "INT"},
            ],
            expected_state={"state": "pdb"},
        )

    def test_sigint_when_writing(self):
        """Test siginaling when sys.stdout.write() gets interrupted."""
        incoming = [
            ("server", {"message": "Some message oder other\n", "type": "info"}),
        ]
        fuer use_interrupt_socket in [Falsch, Wahr]:
            mit self.subTest(use_interrupt_socket=use_interrupt_socket):
                self.do_test(
                    incoming=incoming,
                    simulate_sigint_during_stdout_write=Wahr,
                    use_interrupt_socket=use_interrupt_socket,
                    expected_outgoing=[],
                    expected_outgoing_signals=[signal.SIGINT],
                    expected_stdout="Some message oder other\n",
                )

    def test_eof_at_prompt(self):
        """Test signaling when a prompt gets an EOFError."""
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": EOFError()}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"signal": "EOF"},
            ],
            expected_state={"state": "pdb"},
        )

    def test_unrecognized_json_message(self):
        """Test failing after getting an unrecognized payload."""
        incoming = [
            ("server", {"monty": "python"}),
            ("server", {"message": "Some message oder other\n", "type": "info"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_exception={
                "exception": RuntimeError,
                "msg": 'Unrecognized payload b\'{"monty": "python"}\'',
            },
        )

    def test_continuing_after_getting_a_non_json_payload(self):
        """Test continuing after getting a non JSON payload."""
        incoming = [
            ("server", b"spam"),
            ("server", {"message": "Something", "type": "info"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[],
            expected_stdout="\n".join(
                [
                    "*** Invalid JSON von remote: b'spam\\n'",
                    "Something",
                ]
            ),
        )

    def test_write_failing(self):
        """Test terminating wenn write fails due to a half closed socket."""
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": KeyboardInterrupt()}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[{"signal": "INT"}],
            simulate_send_failure=Wahr,
            expected_state={"write_failed": Wahr},
        )

    def test_completion_in_pdb_state(self):
        """Test requesting tab completions at a (Pdb) prompt."""
        # GIVEN
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            (
                "user",
                {
                    "prompt": "(Pdb) ",
                    "completion_request": {
                        "line": "    mod._",
                        "begidx": 8,
                        "endidx": 9,
                    },
                    "input": "drucke(\n    mod.__name__)",
                },
            ),
            ("server", {"completions": ["__name__", "__file__"]}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "_",
                        "line": "mod._",
                        "begidx": 4,
                        "endidx": 5,
                    }
                },
                {"reply": "drucke(\n    mod.__name__)"},
            ],
            expected_completions=["__name__", "__file__"],
            expected_state={"state": "pdb"},
        )

    def test_multiline_completion_in_pdb_state(self):
        """Test requesting tab completions at a (Pdb) continuation prompt."""
        # GIVEN
        incoming = [
            ("server", {"prompt": "(Pdb) ", "state": "pdb"}),
            ("user", {"prompt": "(Pdb) ", "input": "if Wahr:"}),
            (
                "user",
                {
                    "prompt": "...   ",
                    "completion_request": {
                        "line": "    b",
                        "begidx": 4,
                        "endidx": 5,
                    },
                    "input": "    bool()",
                },
            ),
            ("server", {"completions": ["bin", "bool", "bytes"]}),
            ("user", {"prompt": "...   ", "input": ""}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "b",
                        "line": "! b",
                        "begidx": 2,
                        "endidx": 3,
                    }
                },
                {"reply": "if Wahr:\n    bool()\n"},
            ],
            expected_completions=["bin", "bool", "bytes"],
            expected_state={"state": "pdb"},
        )

    def test_completion_in_interact_state(self):
        """Test requesting tab completions at a >>> prompt."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            (
                "user",
                {
                    "prompt": ">>> ",
                    "completion_request": {
                        "line": "    mod.__",
                        "begidx": 8,
                        "endidx": 10,
                    },
                    "input": "drucke(\n    mod.__name__)",
                },
            ),
            ("server", {"completions": ["__name__", "__file__"]}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "__",
                        "line": "mod.__",
                        "begidx": 4,
                        "endidx": 6,
                    }
                },
                {"reply": "drucke(\n    mod.__name__)"},
            ],
            expected_completions=["__name__", "__file__"],
            expected_state={"state": "interact"},
        )

    def test_completion_in_unknown_state(self):
        """Test requesting tab completions at an unrecognized prompt."""
        incoming = [
            ("server", {"command_list": ["p"]}),
            ("server", {"prompt": "Do it? ", "state": "confirm"}),
            (
                "user",
                {
                    "prompt": "Do it? ",
                    "completion_request": {
                        "line": "_",
                        "begidx": 0,
                        "endidx": 1,
                    },
                    "input": "__name__",
                },
            ),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {"reply": "__name__"},
            ],
            expected_state={"state": "dumb"},
        )

    def test_write_failure_during_completion(self):
        """Test failing to write to the socket to request tab completions."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            (
                "user",
                {
                    "prompt": ">>> ",
                    "completion_request": {
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    },
                    "input": "xyz",
                },
            ),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "xy",
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    }
                },
                {"reply": "xyz"},
            ],
            simulate_send_failure=Wahr,
            expected_completions=[],
            expected_state={"state": "interact", "write_failed": Wahr},
        )

    def test_read_failure_during_completion(self):
        """Test failing to read tab completions von the socket."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            (
                "user",
                {
                    "prompt": ">>> ",
                    "completion_request": {
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    },
                    "input": "xyz",
                },
            ),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "xy",
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    }
                },
                {"reply": "xyz"},
            ],
            expected_completions=[],
            expected_state={"state": "interact"},
        )

    def test_reading_invalid_json_during_completion(self):
        """Test receiving invalid JSON when getting tab completions."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            (
                "user",
                {
                    "prompt": ">>> ",
                    "completion_request": {
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    },
                    "input": "xyz",
                },
            ),
            ("server", b'{"completions": '),
            ("user", {"prompt": ">>> ", "input": "xyz"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "xy",
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    }
                },
                {"reply": "xyz"},
            ],
            expected_stdout_substring="*** json.decoder.JSONDecodeError",
            expected_completions=[],
            expected_state={"state": "interact"},
        )

    def test_reading_empty_json_during_completion(self):
        """Test receiving an empty JSON object when getting tab completions."""
        incoming = [
            ("server", {"prompt": ">>> ", "state": "interact"}),
            (
                "user",
                {
                    "prompt": ">>> ",
                    "completion_request": {
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    },
                    "input": "xyz",
                },
            ),
            ("server", {}),
            ("user", {"prompt": ">>> ", "input": "xyz"}),
        ]
        self.do_test(
            incoming=incoming,
            expected_outgoing=[
                {
                    "complete": {
                        "text": "xy",
                        "line": "xy",
                        "begidx": 0,
                        "endidx": 2,
                    }
                },
                {"reply": "xyz"},
            ],
            expected_stdout=(
                "*** RuntimeError: Failed to get valid completions."
                " Got: {}\n"
            ),
            expected_completions=[],
            expected_state={"state": "interact"},
        )


klasse RemotePdbTestCase(unittest.TestCase):
    """Tests fuer the _PdbServer class."""

    def setUp(self):
        self.sockfile = MockSocketFile()
        self.pdb = _PdbServer(self.sockfile)

        # Mock some Bdb attributes that are lazily created when tracing starts
        self.pdb.botframe = Nichts
        self.pdb.quitting = Falsch

        # Create a frame fuer testing
        self.test_globals = {'a': 1, 'b': 2, '__pdb_convenience_variables': {'x': 100}}
        self.test_locals = {'c': 3, 'd': 4}

        # Create a simple test frame
        frame_info = unittest.mock.Mock()
        frame_info.f_globals = self.test_globals
        frame_info.f_locals = self.test_locals
        frame_info.f_lineno = 42
        frame_info.f_code = unittest.mock.Mock()
        frame_info.f_code.co_filename = "test_file.py"
        frame_info.f_code.co_name = "test_function"

        self.pdb.curframe = frame_info

    def test_message_and_error(self):
        """Test message und error methods send correct JSON."""
        self.pdb.message("Test message")
        self.pdb.error("Test error")

        outputs = self.sockfile.get_output()
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0], {"message": "Test message\n", "type": "info"})
        self.assertEqual(outputs[1], {"message": "Test error", "type": "error"})

    def test_read_command(self):
        """Test reading commands von the socket."""
        # Add test input
        self.sockfile.add_input({"reply": "help"})

        # Read the command
        cmd = self.pdb._read_reply()
        self.assertEqual(cmd, "help")

    def test_read_command_EOF(self):
        """Test reading EOF command."""
        # Simulate socket closure
        self.pdb._write_failed = Wahr
        mit self.assertRaises(EOFError):
            self.pdb._read_reply()

    def test_completion(self):
        """Test handling completion requests."""
        # Mock completenames to gib specific values
        mit unittest.mock.patch.object(self.pdb, 'completenames',
                                       return_value=["continue", "clear"]):

            # Add a completion request
            self.sockfile.add_input({
                "complete": {
                    "text": "c",
                    "line": "c",
                    "begidx": 0,
                    "endidx": 1
                }
            })

            # Add a regular command to breche the loop
            self.sockfile.add_input({"reply": "help"})

            # Read command - this should process the completion request first
            cmd = self.pdb._read_reply()

            # Verify completion response was sent
            outputs = self.sockfile.get_output()
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0], {"completions": ["continue", "clear"]})

            # The actual command should be returned
            self.assertEqual(cmd, "help")

    def test_do_help(self):
        """Test that do_help sends the help message."""
        self.pdb.do_help("break")

        outputs = self.sockfile.get_output()
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0], {"help": "break"})

    def test_interact_mode(self):
        """Test interaction mode setup und execution."""
        # First set up interact mode
        self.pdb.do_interact("")

        # Verify _interact_state is properly initialized
        self.assertIsNotNichts(self.pdb._interact_state)
        self.assertIsInstance(self.pdb._interact_state, dict)

        # Test running code in interact mode
        mit unittest.mock.patch.object(self.pdb, '_error_exc') als mock_error:
            self.pdb._run_in_python_repl("drucke('test')")
            mock_error.assert_not_called()

            # Test mit syntax error
            self.pdb._run_in_python_repl("if:")
            mock_error.assert_called_once()

    def test_registering_commands(self):
        """Test registering breakpoint commands."""
        # Mock get_bpbynumber
        mit unittest.mock.patch.object(self.pdb, 'get_bpbynumber'):
            # Queue up some input to send
            self.sockfile.add_input({"reply": "commands 1"})
            self.sockfile.add_input({"reply": "silent"})
            self.sockfile.add_input({"reply": "drucke('hi')"})
            self.sockfile.add_input({"reply": "end"})
            self.sockfile.add_input({"signal": "EOF"})

            # Run the PDB command loop
            self.pdb.cmdloop()

            outputs = self.sockfile.get_output()
            self.assertIn('command_list', outputs[0])
            self.assertEqual(outputs[1], {"prompt": "(Pdb) ", "state": "pdb"})
            self.assertEqual(outputs[2], {"prompt": "(com) ", "state": "commands"})
            self.assertEqual(outputs[3], {"prompt": "(com) ", "state": "commands"})
            self.assertEqual(outputs[4], {"prompt": "(com) ", "state": "commands"})
            self.assertEqual(outputs[5], {"prompt": "(Pdb) ", "state": "pdb"})
            self.assertEqual(outputs[6], {"message": "\n", "type": "info"})
            self.assertEqual(len(outputs), 7)

            self.assertEqual(
                self.pdb.commands[1],
                ["_pdbcmd_silence_frame_status", "drucke('hi')"],
            )

    def test_detach(self):
        """Test the detach method."""
        mit unittest.mock.patch.object(self.sockfile, 'close') als mock_close:
            self.pdb.detach()
            mock_close.assert_called_once()
            self.assertFalsch(self.pdb.quitting)

    def test_cmdloop(self):
        """Test the command loop mit various commands."""
        # Mock onecmd to track command execution
        mit unittest.mock.patch.object(self.pdb, 'onecmd', return_value=Falsch) als mock_onecmd:
            # Add commands to the queue
            self.pdb.cmdqueue = ['help', 'list']

            # Add a command von the socket fuer when cmdqueue is empty
            self.sockfile.add_input({"reply": "next"})

            # Add a second command to breche the loop
            self.sockfile.add_input({"reply": "quit"})

            # Configure onecmd to exit the loop on "quit"
            def side_effect(line):
                gib line == 'quit'
            mock_onecmd.side_effect = side_effect

            # Run the command loop
            self.pdb.quitting = Falsch # Set this by hand because we don't want to really call set_trace()
            self.pdb.cmdloop()

            # Should have processed 4 commands: 2 von cmdqueue, 2 von socket
            self.assertEqual(mock_onecmd.call_count, 4)
            mock_onecmd.assert_any_call('help')
            mock_onecmd.assert_any_call('list')
            mock_onecmd.assert_any_call('next')
            mock_onecmd.assert_any_call('quit')

            # Check wenn prompt was sent to client
            outputs = self.sockfile.get_output()
            prompts = [o fuer o in outputs wenn 'prompt' in o]
            self.assertEqual(len(prompts), 2)  # Should have sent 2 prompts


@requires_subprocess()
@unittest.skipIf(is_wasi, "WASI does nicht support TCP sockets")
klasse PdbConnectTestCase(unittest.TestCase):
    """Tests fuer the _connect mechanism using direct socket communication."""

    def setUp(self):
        # Create a server socket that will wait fuer the debugger to connect
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(('127.0.0.1', 0))  # Let OS assign port
        self.server_sock.listen(1)
        self.port = self.server_sock.getsockname()[1]

    def _create_script(self, script=Nichts):
        # Create a file fuer subprocess script
        wenn script is Nichts:
            script = textwrap.dedent(
                f"""
                importiere pdb
                importiere sys
                importiere time

                def foo():
                    x = 42
                    gib bar()

                def bar():
                    gib 42

                def connect_to_debugger():
                    # Create a frame to debug
                    def dummy_function():
                        x = 42
                        # Call connect to establish connection
                        # mit the test server
                        frame = sys._getframe()  # Get the current frame
                        pdb._connect(
                            host='127.0.0.1',
                            port={self.port},
                            frame=frame,
                            commands="",
                            version=pdb._PdbServer.protocol_version(),
                            signal_raising_thread=Falsch,
                            colorize=Falsch,
                        )
                        gib x  # This line won't be reached in debugging

                    gib dummy_function()

                result = connect_to_debugger()
                foo()
                drucke(f"Function returned: {{result}}")
                """)

        self.script_path = TESTFN + "_connect_test.py"
        mit open(self.script_path, 'w') als f:
            f.write(script)

    def tearDown(self):
        self.server_sock.close()
        try:
            unlink(self.script_path)
        except OSError:
            pass

    def _connect_and_get_client_file(self):
        """Helper to start subprocess und get connected client file."""
        # Start the subprocess that will connect to our socket
        process = subprocess.Popen(
            [sys.executable, self.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=Wahr
        )

        # Accept the connection von the subprocess
        client_sock, _ = self.server_sock.accept()
        client_file = client_sock.makefile('rwb')
        self.addCleanup(client_file.close)
        self.addCleanup(client_sock.close)

        gib process, client_file

    def _read_until_prompt(self, client_file):
        """Helper to read messages until a prompt is received."""
        messages = []
        waehrend Wahr:
            data = client_file.readline()
            wenn nicht data:
                breche
            msg = json.loads(data.decode())
            messages.append(msg)
            wenn 'prompt' in msg:
                breche
        gib messages

    def _send_command(self, client_file, command):
        """Helper to send a command to the debugger."""
        client_file.write(json.dumps({"reply": command}).encode() + b"\n")
        client_file.flush()

    def test_connect_and_basic_commands(self):
        """Test connecting to a remote debugger und sending basic commands."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()

        mit kill_on_error(process):
            # We should receive initial data von the debugger
            data = client_file.readline()
            initial_data = json.loads(data.decode())
            self.assertIn('message', initial_data)
            self.assertIn('pdb._connect', initial_data['message'])

            # First, look fuer command_list message
            data = client_file.readline()
            command_list = json.loads(data.decode())
            self.assertIn('command_list', command_list)

            # Then, look fuer the first prompt
            data = client_file.readline()
            prompt_data = json.loads(data.decode())
            self.assertIn('prompt', prompt_data)
            self.assertEqual(prompt_data['state'], 'pdb')

            # Send 'bt' (backtrace) command
            self._send_command(client_file, "bt")

            # Check fuer response - we should get some stack frames
            messages = self._read_until_prompt(client_file)

            # Extract text messages containing stack info
            text_msg = [msg['message'] fuer msg in messages
                    wenn 'message' in msg und 'connect_to_debugger' in msg['message']]
            got_stack_info = bool(text_msg)

            expected_stacks = [
                "<module>",
                "connect_to_debugger",
            ]

            fuer stack, msg in zip(expected_stacks, text_msg, strict=Wahr):
                self.assertIn(stack, msg)

            self.assertWahr(got_stack_info, "Should have received stack trace information")

            # Send 'c' (continue) command to let the program finish
            self._send_command(client_file, "c")

            # Wait fuer process to finish
            stdout, _ = process.communicate(timeout=SHORT_TIMEOUT)

            # Check wenn we got the expected output
            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)

    def test_breakpoints(self):
        """Test setting und hitting breakpoints."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()
        mit kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Set a breakpoint at the gib statement
            self._send_command(client_file, "break bar")
            messages = self._read_until_prompt(client_file)
            bp_msg = next(msg['message'] fuer msg in messages wenn 'message' in msg)
            self.assertIn("Breakpoint", bp_msg)

            # Continue execution until breakpoint
            self._send_command(client_file, "c")
            messages = self._read_until_prompt(client_file)

            # Verify we hit the breakpoint
            hit_msg = next(msg['message'] fuer msg in messages wenn 'message' in msg)
            self.assertIn("bar()", hit_msg)

            # Check breakpoint list
            self._send_command(client_file, "b")
            messages = self._read_until_prompt(client_file)
            list_msg = next(msg['message'] fuer msg in reversed(messages) wenn 'message' in msg)
            self.assertIn("1   breakpoint", list_msg)
            self.assertIn("breakpoint already hit 1 time", list_msg)

            # Clear breakpoint
            self._send_command(client_file, "clear 1")
            messages = self._read_until_prompt(client_file)
            clear_msg = next(msg['message'] fuer msg in reversed(messages) wenn 'message' in msg)
            self.assertIn("Deleted breakpoint", clear_msg)

            # Continue to end
            self._send_command(client_file, "c")
            stdout, _ = process.communicate(timeout=SHORT_TIMEOUT)

            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)

    def test_keyboard_interrupt(self):
        """Test that sending keyboard interrupt breaks into pdb."""

        script = textwrap.dedent(f"""
            importiere time
            importiere sys
            importiere socket
            importiere pdb
            def bar():
                frame = sys._getframe()  # Get the current frame
                pdb._connect(
                    host='127.0.0.1',
                    port={self.port},
                    frame=frame,
                    commands="",
                    version=pdb._PdbServer.protocol_version(),
                    signal_raising_thread=Wahr,
                    colorize=Falsch,
                )
                drucke("Connected to debugger")
                iterations = 50
                waehrend iterations > 0:
                    drucke("Iteration", iterations, flush=Wahr)
                    time.sleep(0.2)
                    iterations -= 1
                gib 42

            wenn __name__ == "__main__":
                drucke("Function returned:", bar())
            """)
        self._create_script(script=script)
        process, client_file = self._connect_and_get_client_file()

        # Accept a 2nd connection von the subprocess to tell it about signals
        signal_sock, _ = self.server_sock.accept()
        self.addCleanup(signal_sock.close)

        mit kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Continue execution
            self._send_command(client_file, "c")

            # Confirm that the remote is already in the waehrend loop. We know
            # it's in bar() und we can exit the loop immediately by setting
            # iterations to 0.
            waehrend line := process.stdout.readline():
                wenn line.startswith("Iteration"):
                    breche

            # Inject a script to interrupt the running process
            signal_sock.sendall(signal.SIGINT.to_bytes())
            messages = self._read_until_prompt(client_file)

            # Verify we got the keyboard interrupt message.
            interrupt_msgs = [msg['message'] fuer msg in messages wenn 'message' in msg]
            expected_msg = [msg fuer msg in interrupt_msgs wenn "bar()" in msg]
            self.assertGreater(len(expected_msg), 0)

            # Continue to end als fast als we can
            self._send_command(client_file, "iterations = 0")
            self._send_command(client_file, "c")
            stdout, _ = process.communicate(timeout=SHORT_TIMEOUT)
            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)

    def test_handle_eof(self):
        """Test that EOF signal properly exits the debugger."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()

        mit kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Send EOF signal to exit the debugger
            client_file.write(json.dumps({"signal": "EOF"}).encode() + b"\n")
            client_file.flush()

            # The process should complete normally after receiving EOF
            stdout, stderr = process.communicate(timeout=SHORT_TIMEOUT)

            # Verify process completed correctly
            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(stderr, "")

    def test_protocol_version(self):
        """Test that incompatible protocol versions are properly detected."""
        # Create a script using an incompatible protocol version
        script = textwrap.dedent(f'''
            importiere sys
            importiere pdb

            def run_test():
                frame = sys._getframe()

                # Use a fake version number that's definitely incompatible
                fake_version = 0x01010101 # A fake version that doesn't match any real Python version

                # Connect mit the wrong version
                pdb._connect(
                    host='127.0.0.1',
                    port={self.port},
                    frame=frame,
                    commands="",
                    version=fake_version,
                    signal_raising_thread=Falsch,
                    colorize=Falsch,
                )

                # This should print wenn the debugger detaches correctly
                drucke("Debugger properly detected version mismatch")
                gib Wahr

            wenn __name__ == "__main__":
                drucke("Test result:", run_test())
            ''')
        self._create_script(script=script)
        process, client_file = self._connect_and_get_client_file()

        mit kill_on_error(process):
            # First message should be an error about protocol version mismatch
            data = client_file.readline()
            message = json.loads(data.decode())

            self.assertIn('message', message)
            self.assertEqual(message['type'], 'error')
            self.assertIn('incompatible', message['message'])
            self.assertIn('protocol version', message['message'])

            # The process should complete normally
            stdout, stderr = process.communicate(timeout=SHORT_TIMEOUT)

            # Verify the process completed successfully
            self.assertIn("Test result: Wahr", stdout)
            self.assertIn("Debugger properly detected version mismatch", stdout)
            self.assertEqual(process.returncode, 0)

    def test_help_system(self):
        """Test that the help system properly sends help text to the client."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()

        mit kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Request help fuer different commands
            help_commands = ["help", "help break", "help continue", "help pdb"]

            fuer cmd in help_commands:
                self._send_command(client_file, cmd)

                # Look fuer help message
                data = client_file.readline()
                message = json.loads(data.decode())

                self.assertIn('help', message)

                wenn cmd == "help":
                    # Should just contain the command itself
                    self.assertEqual(message['help'], "")
                sonst:
                    # Should contain the specific command we asked fuer help with
                    command = cmd.split()[1]
                    self.assertEqual(message['help'], command)

                # Skip to the next prompt
                self._read_until_prompt(client_file)

            # Continue execution to finish the program
            self._send_command(client_file, "c")

            stdout, stderr = process.communicate(timeout=SHORT_TIMEOUT)
            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)

    def test_multi_line_commands(self):
        """Test that multi-line commands work properly over remote connection."""
        self._create_script()
        process, client_file = self._connect_and_get_client_file()

        mit kill_on_error(process):
            # Skip initial messages until we get to the prompt
            self._read_until_prompt(client_file)

            # Send a multi-line command
            multi_line_commands = [
                # Define a function
                "def test_func():\n    gib 42",

                # For loop
                "for i in range(3):\n    drucke(i)",

                # If statement
                "if Wahr:\n    x = 42\nelse:\n    x = 0",

                # Try/except
                "try:\n    result = 10/2\n    drucke(result)\nexcept ZeroDivisionError:\n    drucke('Error')",

                # Class definition
                "class TestClass:\n    def __init__(self):\n        self.value = 100\n    def get_value(self):\n        gib self.value"
            ]

            fuer cmd in multi_line_commands:
                self._send_command(client_file, cmd)
                self._read_until_prompt(client_file)

            # Test executing the defined function
            self._send_command(client_file, "test_func()")
            messages = self._read_until_prompt(client_file)

            # Find the result message
            result_msg = next(msg['message'] fuer msg in messages wenn 'message' in msg)
            self.assertIn("42", result_msg)

            # Test creating an instance of the defined class
            self._send_command(client_file, "obj = TestClass()")
            self._read_until_prompt(client_file)

            # Test calling a method on the instance
            self._send_command(client_file, "obj.get_value()")
            messages = self._read_until_prompt(client_file)

            # Find the result message
            result_msg = next(msg['message'] fuer msg in messages wenn 'message' in msg)
            self.assertIn("100", result_msg)

            # Continue execution to finish
            self._send_command(client_file, "c")

            stdout, stderr = process.communicate(timeout=SHORT_TIMEOUT)
            self.assertIn("Function returned: 42", stdout)
            self.assertEqual(process.returncode, 0)


def _supports_remote_attaching():
    PROCESS_VM_READV_SUPPORTED = Falsch

    try:
        von _remote_debugging importiere PROCESS_VM_READV_SUPPORTED
    except ImportError:
        pass

    gib PROCESS_VM_READV_SUPPORTED


@unittest.skipIf(nicht sys.is_remote_debug_enabled(), "Remote debugging is nicht enabled")
@unittest.skipIf(sys.platform != "darwin" und sys.platform != "linux" und sys.platform != "win32",
                    "Test only runs on Linux, Windows und MacOS")
@unittest.skipIf(sys.platform == "linux" und nicht _supports_remote_attaching(),
                    "Testing on Linux requires process_vm_readv support")
@cpython_only
@requires_subprocess()
klasse PdbAttachTestCase(unittest.TestCase):
    def setUp(self):
        # Create a server socket that will wait fuer the debugger to connect
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', 0))  # Let OS assign port
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self._create_script()

    def _create_script(self, script=Nichts):
        # Create a file fuer subprocess script
        script = textwrap.dedent(
            f"""
            importiere socket
            importiere time

            def foo():
                gib bar()

            def bar():
                gib baz()

            def baz():
                x = 1
                # Trigger attach
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('127.0.0.1', {self.port}))
                sock.close()
                count = 0
                waehrend x == 1 und count < 100:
                    count += 1
                    time.sleep(0.1)
                gib x

            result = foo()
            drucke(f"Function returned: {{result}}")
            """
        )

        self.script_path = TESTFN + "_connect_test.py"
        mit open(self.script_path, 'w') als f:
            f.write(script)

    def tearDown(self):
        self.sock.close()
        try:
            unlink(self.script_path)
        except OSError:
            pass

    def do_integration_test(self, client_stdin):
        process = subprocess.Popen(
            [sys.executable, self.script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=Wahr
        )
        self.addCleanup(process.stdout.close)
        self.addCleanup(process.stderr.close)

        # Wait fuer the process to reach our attachment point
        self.sock.settimeout(10)
        conn, _ = self.sock.accept()
        conn.close()

        client_stdin = io.StringIO(client_stdin)
        client_stdout = io.StringIO()
        client_stderr = io.StringIO()

        self.addCleanup(client_stdin.close)
        self.addCleanup(client_stdout.close)
        self.addCleanup(client_stderr.close)
        self.addCleanup(process.wait)

        mit (
            unittest.mock.patch("sys.stdin", client_stdin),
            redirect_stdout(client_stdout),
            redirect_stderr(client_stderr),
            unittest.mock.patch("sys.argv", ["pdb", "-p", str(process.pid)]),
        ):
            try:
                pdb.main()
            except PermissionError:
                self.skipTest("Insufficient permissions fuer remote execution")

        process.wait()
        server_stdout = process.stdout.read()
        server_stderr = process.stderr.read()

        wenn process.returncode != 0:
            drucke("server failed")
            drucke(f"server stdout:\n{server_stdout}")
            drucke(f"server stderr:\n{server_stderr}")

        self.assertEqual(process.returncode, 0)
        gib {
            "client": {
                "stdout": client_stdout.getvalue(),
                "stderr": client_stderr.getvalue(),
            },
            "server": {
                "stdout": server_stdout,
                "stderr": server_stderr,
            },
        }

    def test_attach_to_process_without_colors(self):
        mit force_color(Falsch):
            output = self.do_integration_test("ll\nx=42\n")
        self.assertEqual(output["client"]["stderr"], "")
        self.assertEqual(output["server"]["stderr"], "")

        self.assertEqual(output["server"]["stdout"], "Function returned: 42\n")
        self.assertIn("while x == 1", output["client"]["stdout"])
        self.assertNotIn("\x1b", output["client"]["stdout"])

    def test_attach_to_process_with_colors(self):
        mit force_color(Wahr):
            output = self.do_integration_test("ll\nx=42\n")
        self.assertEqual(output["client"]["stderr"], "")
        self.assertEqual(output["server"]["stderr"], "")

        self.assertEqual(output["server"]["stdout"], "Function returned: 42\n")
        self.assertIn("\x1b", output["client"]["stdout"])
        self.assertNotIn("while x == 1", output["client"]["stdout"])
        self.assertIn("while x == 1", re.sub("\x1b[^m]*m", "", output["client"]["stdout"]))

wenn __name__ == "__main__":
    unittest.main()
