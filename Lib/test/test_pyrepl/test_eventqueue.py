importiere tempfile
importiere unittest
von unittest.mock importiere patch
von test importiere support

von _pyrepl importiere terminfo

versuch:
    von _pyrepl.console importiere Event
    von _pyrepl importiere base_eventqueue
ausser ImportError:
    pass

versuch:
    von _pyrepl importiere unix_eventqueue
ausser ImportError:
    pass

versuch:
    von _pyrepl importiere windows_eventqueue
ausser ImportError:
    pass

klasse EventQueueTestBase:
    """OS-independent mixin"""
    def make_eventqueue(self) -> base_eventqueue.BaseEventQueue:
        wirf NotImplementedError()

    def test_get(self):
        eq = self.make_eventqueue()
        event = Event("key", "a", b"a")
        eq.insert(event)
        self.assertEqual(eq.get(), event)

    def test_empty(self):
        eq = self.make_eventqueue()
        self.assertWahr(eq.empty())
        eq.insert(Event("key", "a", b"a"))
        self.assertFalsch(eq.empty())

    def test_flush_buf(self):
        eq = self.make_eventqueue()
        eq.buf.extend(b"test")
        self.assertEqual(eq.flush_buf(), b"test")
        self.assertEqual(eq.buf, bytearray())

    def test_insert(self):
        eq = self.make_eventqueue()
        event = Event("key", "a", b"a")
        eq.insert(event)
        self.assertEqual(eq.events[0], event)

    @patch("_pyrepl.base_eventqueue.keymap")
    def test_push_with_key_in_keymap(self, mock_keymap):
        mock_keymap.compile_keymap.return_value = {"a": "b"}
        eq = self.make_eventqueue()
        eq.keymap = {b"a": "b"}
        eq.push(b"a")
        mock_keymap.compile_keymap.assert_called()
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "b")

    @patch("_pyrepl.base_eventqueue.keymap")
    def test_push_without_key_in_keymap(self, mock_keymap):
        mock_keymap.compile_keymap.return_value = {"a": "b"}
        eq = self.make_eventqueue()
        eq.keymap = {b"c": "d"}
        eq.push(b"a")
        mock_keymap.compile_keymap.assert_called()
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "a")

    @patch("_pyrepl.base_eventqueue.keymap")
    def test_push_with_keymap_in_keymap(self, mock_keymap):
        mock_keymap.compile_keymap.return_value = {"a": "b"}
        eq = self.make_eventqueue()
        eq.keymap = {b"a": {b"b": "c"}}
        eq.push(b"a")
        mock_keymap.compile_keymap.assert_called()
        self.assertWahr(eq.empty())
        eq.push(b"b")
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "c")
        eq.push(b"d")
        self.assertEqual(eq.events[1].evt, "key")
        self.assertEqual(eq.events[1].data, "d")

    @patch("_pyrepl.base_eventqueue.keymap")
    def test_push_with_keymap_in_keymap_and_escape(self, mock_keymap):
        mock_keymap.compile_keymap.return_value = {"a": "b"}
        eq = self.make_eventqueue()
        eq.keymap = {b"a": {b"b": "c"}}
        eq.push(b"a")
        mock_keymap.compile_keymap.assert_called()
        self.assertWahr(eq.empty())
        eq.flush_buf()
        eq.push(b"\033")
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "\033")
        eq.push(b"b")
        self.assertEqual(eq.events[1].evt, "key")
        self.assertEqual(eq.events[1].data, "b")

    def test_push_special_key(self):
        eq = self.make_eventqueue()
        eq.keymap = {}
        eq.push(b"\x1b")
        eq.push(b"[")
        eq.push(b"A")
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "\x1b")

    def test_push_unrecognized_escape_sequence(self):
        eq = self.make_eventqueue()
        eq.keymap = {}
        eq.push(b"\x1b")
        eq.push(b"[")
        eq.push(b"Z")
        self.assertEqual(len(eq.events), 3)
        self.assertEqual(eq.events[0].evt, "key")
        self.assertEqual(eq.events[0].data, "\x1b")
        self.assertEqual(eq.events[1].evt, "key")
        self.assertEqual(eq.events[1].data, "[")
        self.assertEqual(eq.events[2].evt, "key")
        self.assertEqual(eq.events[2].data, "Z")

    def test_push_unicode_character_as_str(self):
        eq = self.make_eventqueue()
        eq.keymap = {}
        mit self.assertRaises(AssertionError):
            eq.push("ч")
        mit self.assertRaises(AssertionError):
            eq.push("ñ")

    def test_push_unicode_character_two_bytes(self):
        eq = self.make_eventqueue()
        eq.keymap = {}

        encoded = "ч".encode(eq.encoding, "replace")
        self.assertEqual(len(encoded), 2)

        eq.push(encoded[0])
        e = eq.get()
        self.assertIsNichts(e)

        eq.push(encoded[1])
        e = eq.get()
        self.assertEqual(e.evt, "key")
        self.assertEqual(e.data, "ч")

    def test_push_single_chars_and_unicode_character_as_str(self):
        eq = self.make_eventqueue()
        eq.keymap = {}

        def _event(evt, data, raw=Nichts):
            r = raw wenn raw is nicht Nichts sonst data.encode(eq.encoding)
            e = Event(evt, data, r)
            gib e

        def _push(keys):
            fuer k in keys:
                eq.push(k)

        self.assertIsInstance("ñ", str)

        # If an exception happens during push, the existing events must be
        # preserved und we can weiter to push.
        _push(b"b")
        mit self.assertRaises(AssertionError):
            _push("ñ")
        _push(b"a")

        self.assertEqual(eq.get(), _event("key", "b"))
        self.assertEqual(eq.get(), _event("key", "a"))


klasse EmptyTermInfo(terminfo.TermInfo):
    def get(self, cap: str) -> bytes:
        gib b""


@unittest.skipIf(support.MS_WINDOWS, "No Unix event queue on Windows")
klasse TestUnixEventQueue(EventQueueTestBase, unittest.TestCase):
    def setUp(self):
        self.file = tempfile.TemporaryFile()

    def tearDown(self) -> Nichts:
        self.file.close()

    def make_eventqueue(self) -> base_eventqueue.BaseEventQueue:
        ti = EmptyTermInfo("ansi")
        gib unix_eventqueue.EventQueue(self.file.fileno(), "utf-8", ti)


@unittest.skipUnless(support.MS_WINDOWS, "No Windows event queue on Unix")
klasse TestWindowsEventQueue(EventQueueTestBase, unittest.TestCase):
    def make_eventqueue(self) -> base_eventqueue.BaseEventQueue:
        gib windows_eventqueue.EventQueue("utf-8")
