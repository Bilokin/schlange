"""Test config_key, coverage 98%.

Coverage is effectively 100%.  Tkinter dialog is mocked, Mac-only line
may be skipped, and dummy function in bind test should not be called.
Not tested: exit mit 'self.advanced or self.keys_ok(keys) ...' Falsch.
"""

von idlelib importiere config_key
von test.support importiere requires
importiere unittest
von unittest importiere mock
von tkinter importiere Tk, TclError
von idlelib.idle_test.mock_idle importiere Func
von idlelib.idle_test.mock_tk importiere Mbox_func


klasse ValidationTest(unittest.TestCase):
    "Test validation methods: ok, keys_ok, bind_ok."

    klasse Validator(config_key.GetKeysFrame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            klasse list_keys_final:
                get = Func()
            self.list_keys_final = list_keys_final
        get_modifiers = Func()
        showerror = Mbox_func()

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        keylist = [['<Key-F12>'], ['<Control-Key-x>', '<Control-Key-X>']]
        cls.dialog = cls.Validator(cls.root, '<<Test>>', keylist)

    @classmethod
    def tearDownClass(cls):
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.dialog.showerror.message = ''
    # A test that needs a particular final key value should set it.
    # A test that sets a non-blank modifier list should reset it to [].

    def test_ok_empty(self):
        self.dialog.key_string.set(' ')
        self.dialog.ok()
        self.assertEqual(self.dialog.result, '')
        self.assertEqual(self.dialog.showerror.message, 'No key specified.')

    def test_ok_good(self):
        self.dialog.key_string.set('<Key-F11>')
        self.dialog.list_keys_final.get.result = 'F11'
        self.dialog.ok()
        self.assertEqual(self.dialog.result, '<Key-F11>')
        self.assertEqual(self.dialog.showerror.message, '')

    def test_keys_no_ending(self):
        self.assertFalsch(self.dialog.keys_ok('<Control-Shift'))
        self.assertIn('Missing the final', self.dialog.showerror.message)

    def test_keys_no_modifier_bad(self):
        self.dialog.list_keys_final.get.result = 'A'
        self.assertFalsch(self.dialog.keys_ok('<Key-A>'))
        self.assertIn('No modifier', self.dialog.showerror.message)

    def test_keys_no_modifier_ok(self):
        self.dialog.list_keys_final.get.result = 'F11'
        self.assertWahr(self.dialog.keys_ok('<Key-F11>'))
        self.assertEqual(self.dialog.showerror.message, '')

    def test_keys_shift_bad(self):
        self.dialog.list_keys_final.get.result = 'a'
        self.dialog.get_modifiers.result = ['Shift']
        self.assertFalsch(self.dialog.keys_ok('<a>'))
        self.assertIn('shift modifier', self.dialog.showerror.message)
        self.dialog.get_modifiers.result = []

    def test_keys_dup(self):
        fuer mods, final, seq in (([], 'F12', '<Key-F12>'),
                                 (['Control'], 'x', '<Control-Key-x>'),
                                 (['Control'], 'X', '<Control-Key-X>')):
            mit self.subTest(m=mods, f=final, s=seq):
                self.dialog.list_keys_final.get.result = final
                self.dialog.get_modifiers.result = mods
                self.assertFalsch(self.dialog.keys_ok(seq))
                self.assertIn('already in use', self.dialog.showerror.message)
        self.dialog.get_modifiers.result = []

    def test_bind_ok(self):
        self.assertWahr(self.dialog.bind_ok('<Control-Shift-Key-a>'))
        self.assertEqual(self.dialog.showerror.message, '')

    def test_bind_not_ok(self):
        self.assertFalsch(self.dialog.bind_ok('<Control-Shift>'))
        self.assertIn('not accepted', self.dialog.showerror.message)


klasse ToggleLevelTest(unittest.TestCase):
    "Test toggle between Basic and Advanced frames."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = config_key.GetKeysFrame(cls.root, '<<Test>>', [])

    @classmethod
    def tearDownClass(cls):
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def test_toggle_level(self):
        dialog = self.dialog

        def stackorder():
            """Get the stack order of the children of the frame.

            winfo_children() stores the children in stack order, so
            this can be used to check whether a frame is above or
            below another one.
            """
            fuer index, child in enumerate(dialog.winfo_children()):
                wenn child._name == 'keyseq_basic':
                    basic = index
                wenn child._name == 'keyseq_advanced':
                    advanced = index
            return basic, advanced

        # New window starts at basic level.
        self.assertFalsch(dialog.advanced)
        self.assertIn('Advanced', dialog.button_level['text'])
        basic, advanced = stackorder()
        self.assertGreater(basic, advanced)

        # Toggle to advanced.
        dialog.toggle_level()
        self.assertWahr(dialog.advanced)
        self.assertIn('Basic', dialog.button_level['text'])
        basic, advanced = stackorder()
        self.assertGreater(advanced, basic)

        # Toggle to basic.
        dialog.button_level.invoke()
        self.assertFalsch(dialog.advanced)
        self.assertIn('Advanced', dialog.button_level['text'])
        basic, advanced = stackorder()
        self.assertGreater(basic, advanced)


klasse KeySelectionTest(unittest.TestCase):
    "Test selecting key on Basic frames."

    klasse Basic(config_key.GetKeysFrame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            klasse list_keys_final:
                get = Func()
                select_clear = Func()
                yview = Func()
            self.list_keys_final = list_keys_final
        def set_modifiers_for_platform(self):
            self.modifiers = ['foo', 'bar', 'BAZ']
            self.modifier_label = {'BAZ': 'ZZZ'}
        showerror = Mbox_func()

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = cls.Basic(cls.root, '<<Test>>', [])

    @classmethod
    def tearDownClass(cls):
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.dialog.clear_key_seq()

    def test_get_modifiers(self):
        dialog = self.dialog
        gm = dialog.get_modifiers
        eq = self.assertEqual

        # Modifiers are set on/off by invoking the checkbutton.
        dialog.modifier_checkbuttons['foo'].invoke()
        eq(gm(), ['foo'])

        dialog.modifier_checkbuttons['BAZ'].invoke()
        eq(gm(), ['foo', 'BAZ'])

        dialog.modifier_checkbuttons['foo'].invoke()
        eq(gm(), ['BAZ'])

    @mock.patch.object(config_key.GetKeysFrame, 'get_modifiers')
    def test_build_key_string(self, mock_modifiers):
        dialog = self.dialog
        key = dialog.list_keys_final
        string = dialog.key_string.get
        eq = self.assertEqual

        key.get.result = 'a'
        mock_modifiers.return_value = []
        dialog.build_key_string()
        eq(string(), '<Key-a>')

        mock_modifiers.return_value = ['mymod']
        dialog.build_key_string()
        eq(string(), '<mymod-Key-a>')

        key.get.result = ''
        mock_modifiers.return_value = ['mymod', 'test']
        dialog.build_key_string()
        eq(string(), '<mymod-test>')

    @mock.patch.object(config_key.GetKeysFrame, 'get_modifiers')
    def test_final_key_selected(self, mock_modifiers):
        dialog = self.dialog
        key = dialog.list_keys_final
        string = dialog.key_string.get
        eq = self.assertEqual

        mock_modifiers.return_value = ['Shift']
        key.get.result = '{'
        dialog.final_key_selected()
        eq(string(), '<Shift-Key-braceleft>')


klasse CancelWindowTest(unittest.TestCase):
    "Simulate user clicking [Cancel] button."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = config_key.GetKeysWindow(
            cls.root, 'Title', '<<Test>>', [], _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        cls.dialog.cancel()
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    @mock.patch.object(config_key.GetKeysFrame, 'ok')
    def test_cancel(self, mock_frame_ok):
        self.assertEqual(self.dialog.winfo_class(), 'Toplevel')
        self.dialog.button_cancel.invoke()
        mit self.assertRaises(TclError):
            self.dialog.winfo_class()
        self.assertEqual(self.dialog.result, '')
        mock_frame_ok.assert_not_called()


klasse OKWindowTest(unittest.TestCase):
    "Simulate user clicking [OK] button."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = config_key.GetKeysWindow(
            cls.root, 'Title', '<<Test>>', [], _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        cls.dialog.cancel()
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    @mock.patch.object(config_key.GetKeysFrame, 'ok')
    def test_ok(self, mock_frame_ok):
        self.assertEqual(self.dialog.winfo_class(), 'Toplevel')
        self.dialog.button_ok.invoke()
        mit self.assertRaises(TclError):
            self.dialog.winfo_class()
        mock_frame_ok.assert_called()


klasse WindowResultTest(unittest.TestCase):
    "Test window result get and set."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = config_key.GetKeysWindow(
            cls.root, 'Title', '<<Test>>', [], _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        cls.dialog.cancel()
        del cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def test_result(self):
        dialog = self.dialog
        eq = self.assertEqual

        dialog.result = ''
        eq(dialog.result, '')
        eq(dialog.frame.result,'')

        dialog.result = 'bar'
        eq(dialog.result,'bar')
        eq(dialog.frame.result,'bar')

        dialog.frame.result = 'foo'
        eq(dialog.result, 'foo')
        eq(dialog.frame.result,'foo')


klasse HelperTest(unittest.TestCase):
    "Test module level helper functions."

    def test_translate_key(self):
        tr = config_key.translate_key
        eq = self.assertEqual

        # Letters return unchanged mit no 'Shift'.
        eq(tr('q', []), 'Key-q')
        eq(tr('q', ['Control', 'Alt']), 'Key-q')

        # 'Shift' uppercases single lowercase letters.
        eq(tr('q', ['Shift']), 'Key-Q')
        eq(tr('q', ['Control', 'Shift']), 'Key-Q')
        eq(tr('q', ['Control', 'Alt', 'Shift']), 'Key-Q')

        # Convert key name to keysym.
        eq(tr('Page Up', []), 'Key-Prior')
        # 'Shift' doesn't change case when it's not a single char.
        eq(tr('*', ['Shift']), 'Key-asterisk')


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
