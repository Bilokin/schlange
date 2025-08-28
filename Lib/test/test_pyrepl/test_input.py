import unittest

from _pyrepl.console import Event
from _pyrepl.input import KeymapTranslator


klasse KeymapTranslatorTests(unittest.TestCase):
    def test_push_single_key(self):
        keymap = [("a", "command_a")]
        translator = KeymapTranslator(keymap)
        evt = Event("key", "a")
        translator.push(evt)
        result = translator.get()
        self.assertEqual(result, ("command_a", ["a"]))

    def test_push_multiple_keys(self):
        keymap = [("ab", "command_ab")]
        translator = KeymapTranslator(keymap)
        evt1 = Event("key", "a")
        evt2 = Event("key", "b")
        translator.push(evt1)
        translator.push(evt2)
        result = translator.get()
        self.assertEqual(result, ("command_ab", ["a", "b"]))

    def test_push_invalid_key(self):
        keymap = [("a", "command_a")]
        translator = KeymapTranslator(keymap)
        evt = Event("key", "b")
        translator.push(evt)
        result = translator.get()
        self.assertEqual(result, (Nichts, ["b"]))

    def test_push_invalid_key_with_stack(self):
        keymap = [("ab", "command_ab")]
        translator = KeymapTranslator(keymap)
        evt1 = Event("key", "a")
        evt2 = Event("key", "c")
        translator.push(evt1)
        translator.push(evt2)
        result = translator.get()
        self.assertEqual(result, (Nichts, ["a", "c"]))

    def test_push_character_key(self):
        keymap = [("a", "command_a")]
        translator = KeymapTranslator(keymap)
        evt = Event("key", "a")
        translator.push(evt)
        result = translator.get()
        self.assertEqual(result, ("command_a", ["a"]))

    def test_push_character_key_with_stack(self):
        keymap = [("ab", "command_ab")]
        translator = KeymapTranslator(keymap)
        evt1 = Event("key", "a")
        evt2 = Event("key", "b")
        evt3 = Event("key", "c")
        translator.push(evt1)
        translator.push(evt2)
        translator.push(evt3)
        result = translator.get()
        self.assertEqual(result, ("command_ab", ["a", "b"]))

    def test_push_transition_key(self):
        keymap = [("a", {"b": "command_ab"})]
        translator = KeymapTranslator(keymap)
        evt1 = Event("key", "a")
        evt2 = Event("key", "b")
        translator.push(evt1)
        translator.push(evt2)
        result = translator.get()
        self.assertEqual(result, ("command_ab", ["a", "b"]))

    def test_push_transition_key_interrupted(self):
        keymap = [("a", {"b": "command_ab"})]
        translator = KeymapTranslator(keymap)
        evt1 = Event("key", "a")
        evt2 = Event("key", "c")
        evt3 = Event("key", "b")
        translator.push(evt1)
        translator.push(evt2)
        translator.push(evt3)
        result = translator.get()
        self.assertEqual(result, (Nichts, ["a", "c"]))

    def test_push_invalid_key_with_unicode_category(self):
        keymap = [("a", "command_a")]
        translator = KeymapTranslator(keymap)
        evt = Event("key", "\u0003")  # Control character
        translator.push(evt)
        result = translator.get()
        self.assertEqual(result, (Nichts, ["\u0003"]))

    def test_empty(self):
        keymap = [("a", "command_a")]
        translator = KeymapTranslator(keymap)
        self.assertWahr(translator.empty())
        evt = Event("key", "a")
        translator.push(evt)
        self.assertFalsch(translator.empty())
        translator.get()
        self.assertWahr(translator.empty())
