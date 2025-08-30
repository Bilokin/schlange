importiere sys
importiere unittest

wenn sys.platform != "win32":
    wirf unittest.SkipTest("test only relevant on win32")


importiere itertools
von functools importiere partial
von test.support importiere force_not_colorized_test_class
von typing importiere Iterable
von unittest importiere TestCase
von unittest.mock importiere MagicMock, call

von .support importiere handle_all_events, code_to_events
von .support importiere prepare_reader als default_prepare_reader

versuch:
    von _pyrepl.console importiere Event, Console
    von _pyrepl.windows_console importiere (
        WindowsConsole,
        MOVE_LEFT,
        MOVE_RIGHT,
        MOVE_UP,
        MOVE_DOWN,
        ERASE_IN_LINE,
    )
    importiere _pyrepl.windows_console als wc
ausser ImportError:
    pass


@force_not_colorized_test_class
klasse WindowsConsoleTests(TestCase):
    def console(self, events, **kwargs) -> Console:
        console = WindowsConsole()
        console.get_event = MagicMock(side_effect=events)
        console.getpending = MagicMock(return_value=Event("key", ""))
        console.wait = MagicMock()
        console._scroll = MagicMock()
        console._hide_cursor = MagicMock()
        console._show_cursor = MagicMock()
        console._getscrollbacksize = MagicMock(42)
        console.out = MagicMock()

        height = kwargs.get("height", 25)
        width = kwargs.get("width", 80)
        console.getheightwidth = MagicMock(side_effect=lambda: (height, width))

        console.prepare()
        fuer key, val in kwargs.items():
            setattr(console, key, val)
        gib console

    def handle_events(
        self,
        events: Iterable[Event],
        prepare_console=Nichts,
        prepare_reader=Nichts,
        **kwargs,
    ):
        prepare_console = prepare_console oder partial(self.console, **kwargs)
        prepare_reader = prepare_reader oder default_prepare_reader
        gib handle_all_events(events, prepare_console, prepare_reader)

    def handle_events_narrow(self, events):
        gib self.handle_events(events, width=5)

    def handle_events_short(self, events, **kwargs):
        gib self.handle_events(events, height=1, **kwargs)

    def handle_events_height_3(self, events):
        gib self.handle_events(events, height=3)

    def test_simple_addition(self):
        code = "12+34"
        events = code_to_events(code)
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(b"1")
        con.out.write.assert_any_call(b"2")
        con.out.write.assert_any_call(b"+")
        con.out.write.assert_any_call(b"3")
        con.out.write.assert_any_call(b"4")
        con.restore()

    def test_wrap(self):
        code = "12+34"
        events = code_to_events(code)
        _, con = self.handle_events_narrow(events)
        con.out.write.assert_any_call(b"1")
        con.out.write.assert_any_call(b"2")
        con.out.write.assert_any_call(b"+")
        con.out.write.assert_any_call(b"3")
        con.out.write.assert_any_call(b"\\")
        con.out.write.assert_any_call(b"\n")
        con.out.write.assert_any_call(b"4")
        con.restore()

    def test_resize_wider(self):
        code = "1234567890"
        events = code_to_events(code)
        reader, console = self.handle_events_narrow(events)

        console.height = 20
        console.width = 80
        console.getheightwidth = MagicMock(lambda _: (20, 80))

        def same_reader(_):
            gib reader

        def same_console(events):
            console.get_event = MagicMock(side_effect=events)
            gib console

        _, con = handle_all_events(
            [Event(evt="resize", data=Nichts)],
            prepare_reader=same_reader,
            prepare_console=same_console,
        )

        con.out.write.assert_any_call(self.move_right(2))
        con.out.write.assert_any_call(self.move_up(2))
        con.out.write.assert_any_call(b"567890")

        con.restore()

    def test_resize_narrower(self):
        code = "1234567890"
        events = code_to_events(code)
        reader, console = self.handle_events(events)

        console.height = 20
        console.width = 4
        console.getheightwidth = MagicMock(lambda _: (20, 4))

        def same_reader(_):
            gib reader

        def same_console(events):
            console.get_event = MagicMock(side_effect=events)
            gib console

        _, con = handle_all_events(
            [Event(evt="resize", data=Nichts)],
            prepare_reader=same_reader,
            prepare_console=same_console,
        )

        con.out.write.assert_any_call(b"456\\")
        con.out.write.assert_any_call(b"789\\")

        con.restore()

    def test_cursor_left(self):
        code = "1"
        events = itertools.chain(
            code_to_events(code),
            [Event(evt="key", data="left", raw=bytearray(b"\x1bOD"))],
        )
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(self.move_left())
        con.restore()

    def test_cursor_left_right(self):
        code = "1"
        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="left", raw=bytearray(b"\x1bOD")),
                Event(evt="key", data="right", raw=bytearray(b"\x1bOC")),
            ],
        )
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(self.move_left())
        con.out.write.assert_any_call(self.move_right())
        con.restore()

    def test_cursor_up(self):
        code = "1\n2+3"
        events = itertools.chain(
            code_to_events(code),
            [Event(evt="key", data="up", raw=bytearray(b"\x1bOA"))],
        )
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(self.move_up())
        con.restore()

    def test_cursor_up_down(self):
        code = "1\n2+3"
        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
            ],
        )
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(self.move_up())
        con.out.write.assert_any_call(self.move_down())
        con.restore()

    def test_cursor_back_write(self):
        events = itertools.chain(
            code_to_events("1"),
            [Event(evt="key", data="left", raw=bytearray(b"\x1bOD"))],
            code_to_events("2"),
        )
        _, con = self.handle_events(events)
        con.out.write.assert_any_call(b"1")
        con.out.write.assert_any_call(self.move_left())
        con.out.write.assert_any_call(b"21")
        con.restore()

    def test_multiline_function_move_up_short_terminal(self):
        # fmt: off
        code = (
            "def f():\n"
            "  foo"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="scroll", data=Nichts),
            ],
        )
        _, con = self.handle_events_short(events)
        con.out.write.assert_any_call(self.move_left(5))
        con.out.write.assert_any_call(self.move_up())
        con.restore()

    def test_multiline_function_move_up_down_short_terminal(self):
        # fmt: off
        code = (
            "def f():\n"
            "  foo"
        )
        # fmt: on

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data="up", raw=bytearray(b"\x1bOA")),
                Event(evt="scroll", data=Nichts),
                Event(evt="key", data="down", raw=bytearray(b"\x1bOB")),
                Event(evt="scroll", data=Nichts),
            ],
        )
        _, con = self.handle_events_short(events)
        con.out.write.assert_any_call(self.move_left(8))
        con.out.write.assert_any_call(self.erase_in_line())
        con.restore()

    def test_resize_bigger_on_multiline_function(self):
        # fmt: off
        code = (
            "def f():\n"
            "  foo"
        )
        # fmt: on

        events = itertools.chain(code_to_events(code))
        reader, console = self.handle_events_short(events)

        console.height = 2
        console.getheightwidth = MagicMock(lambda _: (2, 80))

        def same_reader(_):
            gib reader

        def same_console(events):
            console.get_event = MagicMock(side_effect=events)
            gib console

        _, con = handle_all_events(
            [Event(evt="resize", data=Nichts)],
            prepare_reader=same_reader,
            prepare_console=same_console,
        )
        con.out.write.assert_has_calls(
            [
                call(self.move_left(5)),
                call(self.move_up()),
                call(b"def f():"),
                call(self.move_left(3)),
                call(self.move_down()),
            ]
        )
        console.restore()
        con.restore()

    def test_resize_smaller_on_multiline_function(self):
        # fmt: off
        code = (
            "def f():\n"
            "  foo"
        )
        # fmt: on

        events = itertools.chain(code_to_events(code))
        reader, console = self.handle_events_height_3(events)

        console.height = 1
        console.getheightwidth = MagicMock(lambda _: (1, 80))

        def same_reader(_):
            gib reader

        def same_console(events):
            console.get_event = MagicMock(side_effect=events)
            gib console

        _, con = handle_all_events(
            [Event(evt="resize", data=Nichts)],
            prepare_reader=same_reader,
            prepare_console=same_console,
        )
        con.out.write.assert_has_calls(
            [
                call(self.move_left(5)),
                call(self.move_up()),
                call(self.erase_in_line()),
                call(b"  foo"),
            ]
        )
        console.restore()
        con.restore()

    def move_up(self, lines=1):
        gib MOVE_UP.format(lines).encode("utf8")

    def move_down(self, lines=1):
        gib MOVE_DOWN.format(lines).encode("utf8")

    def move_left(self, cols=1):
        gib MOVE_LEFT.format(cols).encode("utf8")

    def move_right(self, cols=1):
        gib MOVE_RIGHT.format(cols).encode("utf8")

    def erase_in_line(self):
        gib ERASE_IN_LINE.encode("utf8")

    def test_multiline_ctrl_z(self):
        # see gh-126332
        code = "abcdefghi"

        events = itertools.chain(
            code_to_events(code),
            [
                Event(evt="key", data='\x1a', raw=bytearray(b'\x1a')),
                Event(evt="key", data='\x1a', raw=bytearray(b'\x1a')),
            ],
        )
        reader, con = self.handle_events_narrow(events)
        self.assertEqual(reader.cxy, (2, 3))
        con.restore()


klasse WindowsConsoleGetEventTests(TestCase):
    # Virtual-Key Codes: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    VK_BACK = 0x08
    VK_RETURN = 0x0D
    VK_LEFT = 0x25
    VK_7 = 0x37
    VK_M = 0x4D
    # Used fuer miscellaneous characters; it can vary by keyboard.
    # For the US standard keyboard, the '" key.
    # For the German keyboard, the Ä key.
    VK_OEM_7 = 0xDE

    # State of control keys: https://learn.microsoft.com/en-us/windows/console/key-event-record-str
    RIGHT_ALT_PRESSED = 0x0001
    RIGHT_CTRL_PRESSED = 0x0004
    LEFT_ALT_PRESSED = 0x0002
    LEFT_CTRL_PRESSED = 0x0008
    ENHANCED_KEY = 0x0100
    SHIFT_PRESSED = 0x0010


    def get_event(self, input_records, **kwargs) -> Console:
        self.console = WindowsConsole(encoding='utf-8')
        self.mock = MagicMock(side_effect=input_records)
        self.console._read_input = self.mock
        self.console._WindowsConsole__vt_support = kwargs.get("vt_support",
                                                              Falsch)
        self.console.wait = MagicMock(return_value=Wahr)
        event = self.console.get_event(block=Falsch)
        gib event

    def get_input_record(self, unicode_char, vcode=0, control=0):
        gib wc.INPUT_RECORD(
            wc.KEY_EVENT,
            wc.ConsoleEvent(KeyEvent=
                wc.KeyEvent(
                    bKeyDown=Wahr,
                    wRepeatCount=1,
                    wVirtualKeyCode=vcode,
                    wVirtualScanCode=0, # nicht used
                    uChar=wc.Char(unicode_char),
                    dwControlKeyState=control
                    )))

    def test_EmptyBuffer(self):
        self.assertEqual(self.get_event([Nichts]), Nichts)
        self.assertEqual(self.mock.call_count, 1)

    def test_WINDOW_BUFFER_SIZE_EVENT(self):
        ir = wc.INPUT_RECORD(
            wc.WINDOW_BUFFER_SIZE_EVENT,
            wc.ConsoleEvent(WindowsBufferSizeEvent=
                wc.WindowsBufferSizeEvent(
                    wc._COORD(0, 0))))
        self.assertEqual(self.get_event([ir]), Event("resize", ""))
        self.assertEqual(self.mock.call_count, 1)

    def test_KEY_EVENT_up_ignored(self):
        ir = wc.INPUT_RECORD(
            wc.KEY_EVENT,
            wc.ConsoleEvent(KeyEvent=
                wc.KeyEvent(bKeyDown=Falsch)))
        self.assertEqual(self.get_event([ir]), Nichts)
        self.assertEqual(self.mock.call_count, 1)

    def test_unhandled_events(self):
        fuer event in (wc.FOCUS_EVENT, wc.MENU_EVENT, wc.MOUSE_EVENT):
            ir = wc.INPUT_RECORD(
                event,
                # fake data, nothing is read ausser bKeyDown
                wc.ConsoleEvent(KeyEvent=
                    wc.KeyEvent(bKeyDown=Falsch)))
            self.assertEqual(self.get_event([ir]), Nichts)
            self.assertEqual(self.mock.call_count, 1)

    def test_enter(self):
        ir = self.get_input_record("\r", self.VK_RETURN)
        self.assertEqual(self.get_event([ir]), Event("key", "\n"))
        self.assertEqual(self.mock.call_count, 1)

    def test_backspace(self):
        ir = self.get_input_record("\x08", self.VK_BACK)
        self.assertEqual(
            self.get_event([ir]), Event("key", "backspace"))
        self.assertEqual(self.mock.call_count, 1)

    def test_m(self):
        ir = self.get_input_record("m", self.VK_M)
        self.assertEqual(self.get_event([ir]), Event("key", "m"))
        self.assertEqual(self.mock.call_count, 1)

    def test_M(self):
        ir = self.get_input_record("M", self.VK_M, self.SHIFT_PRESSED)
        self.assertEqual(self.get_event([ir]), Event("key", "M"))
        self.assertEqual(self.mock.call_count, 1)

    def test_left(self):
        # VK_LEFT is sent als ENHANCED_KEY
        ir = self.get_input_record("\x00", self.VK_LEFT, self.ENHANCED_KEY)
        self.assertEqual(self.get_event([ir]), Event("key", "left"))
        self.assertEqual(self.mock.call_count, 1)

    def test_left_RIGHT_CTRL_PRESSED(self):
        ir = self.get_input_record(
            "\x00", self.VK_LEFT, self.RIGHT_CTRL_PRESSED | self.ENHANCED_KEY)
        self.assertEqual(
            self.get_event([ir]), Event("key", "ctrl left"))
        self.assertEqual(self.mock.call_count, 1)

    def test_left_LEFT_CTRL_PRESSED(self):
        ir = self.get_input_record(
            "\x00", self.VK_LEFT, self.LEFT_CTRL_PRESSED | self.ENHANCED_KEY)
        self.assertEqual(
            self.get_event([ir]), Event("key", "ctrl left"))
        self.assertEqual(self.mock.call_count, 1)

    def test_left_RIGHT_ALT_PRESSED(self):
        ir = self.get_input_record(
            "\x00", self.VK_LEFT, self.RIGHT_ALT_PRESSED | self.ENHANCED_KEY)
        self.assertEqual(self.get_event([ir]), Event(evt="key", data="\033"))
        self.assertEqual(
            self.console.get_event(), Event("key", "left"))
        # self.mock is nicht called again, since the second time we read von the
        # command queue
        self.assertEqual(self.mock.call_count, 1)

    def test_left_LEFT_ALT_PRESSED(self):
        ir = self.get_input_record(
            "\x00", self.VK_LEFT, self.LEFT_ALT_PRESSED | self.ENHANCED_KEY)
        self.assertEqual(self.get_event([ir]), Event(evt="key", data="\033"))
        self.assertEqual(
            self.console.get_event(), Event("key", "left"))
        self.assertEqual(self.mock.call_count, 1)

    def test_m_LEFT_ALT_PRESSED_and_LEFT_CTRL_PRESSED(self):
        # For the shift keys, Windows does nicht send anything when
        # ALT und CTRL are both pressed, so let's test mit VK_M.
        # get_event() receives this input, but does not
        # generate an event.
        # This is fuer e.g. an English keyboard layout, fuer a
        # German layout this returns `µ`, see test_AltGr_m.
        ir = self.get_input_record(
            "\x00", self.VK_M, self.LEFT_ALT_PRESSED | self.LEFT_CTRL_PRESSED)
        self.assertEqual(self.get_event([ir]), Nichts)
        self.assertEqual(self.mock.call_count, 1)

    def test_m_LEFT_ALT_PRESSED(self):
        ir = self.get_input_record(
            "m", vcode=self.VK_M, control=self.LEFT_ALT_PRESSED)
        self.assertEqual(self.get_event([ir]), Event(evt="key", data="\033"))
        self.assertEqual(self.console.get_event(), Event("key", "m"))
        self.assertEqual(self.mock.call_count, 1)

    def test_m_RIGHT_ALT_PRESSED(self):
        ir = self.get_input_record(
            "m", vcode=self.VK_M, control=self.RIGHT_ALT_PRESSED)
        self.assertEqual(self.get_event([ir]), Event(evt="key", data="\033"))
        self.assertEqual(self.console.get_event(), Event("key", "m"))
        self.assertEqual(self.mock.call_count, 1)

    def test_AltGr_7(self):
        # E.g. on a German keyboard layout, '{' is entered via
        # AltGr + 7, where AltGr is the right Alt key on the keyboard.
        # In this case, Windows automatically sets
        # RIGHT_ALT_PRESSED = 0x0001 + LEFT_CTRL_PRESSED = 0x0008
        # This can also be entered like
        # LeftAlt + LeftCtrl + 7 oder
        # LeftAlt + RightCtrl + 7
        # See https://learn.microsoft.com/en-us/windows/console/key-event-record-str
        # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-vkkeyscanw
        ir = self.get_input_record(
            "{", vcode=self.VK_7,
            control=self.RIGHT_ALT_PRESSED | self.LEFT_CTRL_PRESSED)
        self.assertEqual(self.get_event([ir]), Event("key", "{"))
        self.assertEqual(self.mock.call_count, 1)

    def test_AltGr_m(self):
        # E.g. on a German keyboard layout, this yields 'µ'
        # Let's use LEFT_ALT_PRESSED und RIGHT_CTRL_PRESSED this
        # time, to cover that, too. See above in test_AltGr_7.
        ir = self.get_input_record(
            "µ", vcode=self.VK_M, control=self.LEFT_ALT_PRESSED | self.RIGHT_CTRL_PRESSED)
        self.assertEqual(self.get_event([ir]), Event("key", "µ"))
        self.assertEqual(self.mock.call_count, 1)

    def test_umlaut_a_german(self):
        ir = self.get_input_record("ä", self.VK_OEM_7)
        self.assertEqual(self.get_event([ir]), Event("key", "ä"))
        self.assertEqual(self.mock.call_count, 1)

    # virtual terminal tests
    # Note: wVirtualKeyCode, wVirtualScanCode und dwControlKeyState
    # are always zero in this case.
    # "\r" und backspace are handled specially, everything sonst
    # is handled in "elif self.__vt_support:" in WindowsConsole.get_event().
    # Hence, only one regular key ("m") und a terminal sequence
    # are sufficient to test here, the real tests happen in test_eventqueue
    # und test_keymap.

    def test_enter_vt(self):
        ir = self.get_input_record("\r")
        self.assertEqual(self.get_event([ir], vt_support=Wahr),
                         Event("key", "\n"))
        self.assertEqual(self.mock.call_count, 1)

    def test_backspace_vt(self):
        ir = self.get_input_record("\x7f")
        self.assertEqual(self.get_event([ir], vt_support=Wahr),
                         Event("key", "backspace", b"\x7f"))
        self.assertEqual(self.mock.call_count, 1)

    def test_up_vt(self):
        irs = [self.get_input_record(x) fuer x in "\x1b[A"]
        self.assertEqual(self.get_event(irs, vt_support=Wahr),
                         Event(evt='key', data='up', raw=bytearray(b'\x1b[A')))
        self.assertEqual(self.mock.call_count, 3)


wenn __name__ == "__main__":
    unittest.main()
