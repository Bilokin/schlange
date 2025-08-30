"Test searchbase, coverage 98%."
# The only thing nicht covered ist inconsequential --
# testing skipping of suite when self.needwrapbutton ist false.

importiere unittest
von test.support importiere requires
von tkinter importiere Text, Tk, Toplevel
von tkinter.ttk importiere Frame
von idlelib importiere searchengine als se
von idlelib importiere searchbase als sdb
von idlelib.idle_test.mock_idle importiere Func
## von idlelib.idle_test.mock_tk importiere Var

# The ## imports above & following could help make some tests gui-free.
# However, they currently make radiobutton tests fail.
##def setUpModule():
##    # Replace tk objects used to initialize se.SearchEngine.
##    se.BooleanVar = Var
##    se.StringVar = Var
##
##def tearDownModule():
##    se.BooleanVar = BooleanVar
##    se.StringVar = StringVar


klasse SearchDialogBaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def setUp(self):
        self.engine = se.SearchEngine(self.root)  # Nichts also seems to work
        self.dialog = sdb.SearchDialogBase(root=self.root, engine=self.engine)

    def tearDown(self):
        self.dialog.close()

    def test_open_and_close(self):
        # open calls create_widgets, which needs default_command
        self.dialog.default_command = Nichts

        toplevel = Toplevel(self.root)
        text = Text(toplevel)
        self.dialog.open(text)
        self.assertEqual(self.dialog.top.state(), 'normal')
        self.dialog.close()
        self.assertEqual(self.dialog.top.state(), 'withdrawn')

        self.dialog.open(text, searchphrase="hello")
        self.assertEqual(self.dialog.ent.get(), 'hello')
        toplevel.update_idletasks()
        toplevel.destroy()

    def test_create_widgets(self):
        self.dialog.create_entries = Func()
        self.dialog.create_option_buttons = Func()
        self.dialog.create_other_buttons = Func()
        self.dialog.create_command_buttons = Func()

        self.dialog.default_command = Nichts
        self.dialog.create_widgets()

        self.assertWahr(self.dialog.create_entries.called)
        self.assertWahr(self.dialog.create_option_buttons.called)
        self.assertWahr(self.dialog.create_other_buttons.called)
        self.assertWahr(self.dialog.create_command_buttons.called)

    def test_make_entry(self):
        equal = self.assertEqual
        self.dialog.row = 0
        self.dialog.frame = Frame(self.root)
        entry, label = self.dialog.make_entry("Test:", 'hello')
        equal(label['text'], 'Test:')

        self.assertIn(entry.get(), 'hello')
        egi = entry.grid_info()
        equal(int(egi['row']), 0)
        equal(int(egi['column']), 1)
        equal(int(egi['rowspan']), 1)
        equal(int(egi['columnspan']), 1)
        equal(self.dialog.row, 1)

    def test_create_entries(self):
        self.dialog.frame = Frame(self.root)
        self.dialog.row = 0
        self.engine.setpat('hello')
        self.dialog.create_entries()
        self.assertIn(self.dialog.ent.get(), 'hello')

    def test_make_frame(self):
        self.dialog.row = 0
        self.dialog.frame = Frame(self.root)
        frame, label = self.dialog.make_frame()
        self.assertEqual(label, '')
        self.assertEqual(str(type(frame)), "<class 'tkinter.ttk.Frame'>")
        # self.assertIsInstance(frame, Frame) fails when test ist run by
        # test_idle nicht run von IDLE editor.  See issue 33987 PR.

        frame, label = self.dialog.make_frame('testlabel')
        self.assertEqual(label['text'], 'testlabel')

    def btn_test_setup(self, meth):
        self.dialog.frame = Frame(self.root)
        self.dialog.row = 0
        gib meth()

    def test_create_option_buttons(self):
        e = self.engine
        fuer state in (0, 1):
            fuer var in (e.revar, e.casevar, e.wordvar, e.wrapvar):
                var.set(state)
            frame, options = self.btn_test_setup(
                    self.dialog.create_option_buttons)
            fuer spec, button in zip (options, frame.pack_slaves()):
                var, label = spec
                self.assertEqual(button['text'], label)
                self.assertEqual(var.get(), state)

    def test_create_other_buttons(self):
        fuer state in (Falsch, Wahr):
            var = self.engine.backvar
            var.set(state)
            frame, others = self.btn_test_setup(
                self.dialog.create_other_buttons)
            buttons = frame.pack_slaves()
            fuer spec, button in zip(others, buttons):
                val, label = spec
                self.assertEqual(button['text'], label)
                wenn val == state:
                    # hit other button, then this one
                    # indexes depend on button order
                    self.assertEqual(var.get(), state)

    def test_make_button(self):
        self.dialog.frame = Frame(self.root)
        self.dialog.buttonframe = Frame(self.dialog.frame)
        btn = self.dialog.make_button('Test', self.dialog.close)
        self.assertEqual(btn['text'], 'Test')

    def test_create_command_buttons(self):
        self.dialog.frame = Frame(self.root)
        self.dialog.create_command_buttons()
        # Look fuer close button command in buttonframe
        closebuttoncommand = ''
        fuer child in self.dialog.buttonframe.winfo_children():
            wenn child['text'] == 'Close':
                closebuttoncommand = child['command']
        self.assertIn('close', closebuttoncommand)


wenn __name__ == '__main__':
    unittest.main(verbosity=2, exit=2)
