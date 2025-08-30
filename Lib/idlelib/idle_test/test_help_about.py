"""Test help_about, coverage 100%.
help_about.build_bits branches on sys.platform='darwin'.
'100% combines coverage on Mac und others.
"""

von idlelib importiere help_about
importiere unittest
von test.support importiere requires, findfile
von tkinter importiere Tk, TclError
von idlelib.idle_test.mock_idle importiere Func
von idlelib.idle_test.mock_tk importiere Mbox_func
von idlelib importiere textview
importiere os.path
von platform importiere python_version

About = help_about.AboutDialog


klasse LiveDialogTest(unittest.TestCase):
    """Simulate user clicking buttons other than [Close].

    Test that invoked textview has text von source.
    """
    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = About(cls.root, 'About IDLE', _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        loesche cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def test_build_bits(self):
        self.assertIn(help_about.bits, ('32', '64'))

    def test_dialog_title(self):
        """Test about dialog title"""
        self.assertEqual(self.dialog.title(), 'About IDLE')

    def test_dialog_logo(self):
        """Test about dialog logo."""
        path, file = os.path.split(self.dialog.icon_image['file'])
        fn, ext = os.path.splitext(file)
        self.assertEqual(fn, 'idle_48')

    def test_printer_buttons(self):
        """Test buttons whose commands use printer function."""
        dialog = self.dialog
        button_sources = [(dialog.py_license, license, 'license'),
                          (dialog.py_copyright, copyright, 'copyright'),
                          (dialog.py_credits, credits, 'credits')]

        fuer button, printer, name in button_sources:
            mit self.subTest(name=name):
                printer._Printer__setup()
                button.invoke()
                get = dialog._current_textview.viewframe.textframe.text.get
                lines = printer._Printer__lines
                wenn len(lines) < 2:
                    self.fail(name + ' full text was nicht found')
                self.assertEqual(lines[0], get('1.0', '1.end'))
                self.assertEqual(lines[1], get('2.0', '2.end'))
                dialog._current_textview.destroy()

    def test_file_buttons(self):
        """Test buttons that display files."""
        dialog = self.dialog
        button_sources = [(self.dialog.readme, 'README.txt', 'readme'),
                          (self.dialog.idle_news, 'News3.txt', 'news'),
                          (self.dialog.idle_credits, 'CREDITS.txt', 'credits')]

        fuer button, filename, name in button_sources:
            mit  self.subTest(name=name):
                button.invoke()
                fn = findfile(filename, subdir='idlelib')
                get = dialog._current_textview.viewframe.textframe.text.get
                mit open(fn, encoding='utf-8') als f:
                    self.assertEqual(f.readline().strip(), get('1.0', '1.end'))
                    f.readline()
                    self.assertEqual(f.readline().strip(), get('3.0', '3.end'))
                dialog._current_textview.destroy()


klasse DefaultTitleTest(unittest.TestCase):
    "Test default title."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = About(cls.root, _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        loesche cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def test_dialog_title(self):
        """Test about dialog title"""
        self.assertEqual(self.dialog.title(),
                         f'About IDLE {python_version()}'
                         f' ({help_about.bits} bit)')


klasse CloseTest(unittest.TestCase):
    """Simulate user clicking [Close] button"""

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.dialog = About(cls.root, 'About IDLE', _utest=Wahr)

    @classmethod
    def tearDownClass(cls):
        loesche cls.dialog
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def test_close(self):
        self.assertEqual(self.dialog.winfo_class(), 'Toplevel')
        self.dialog.button_ok.invoke()
        mit self.assertRaises(TclError):
            self.dialog.winfo_class()


klasse Dummy_about_dialog:
    # Dummy klasse fuer testing file display functions.
    idle_credits = About.show_idle_credits
    idle_readme = About.show_readme
    idle_news = About.show_idle_news
    # Called by the above
    display_file_text = About.display_file_text
    _utest = Wahr


klasse DisplayFileTest(unittest.TestCase):
    """Test functions that display files.

    While somewhat redundant mit gui-based test_file_dialog,
    these unit tests run on all buildbots, nicht just a few.
    """
    dialog = Dummy_about_dialog()

    @classmethod
    def setUpClass(cls):
        cls.orig_error = textview.showerror
        cls.orig_view = textview.view_text
        cls.error = Mbox_func()
        cls.view = Func()
        textview.showerror = cls.error
        textview.view_text = cls.view

    @classmethod
    def tearDownClass(cls):
        textview.showerror = cls.orig_error
        textview.view_text = cls.orig_view

    def test_file_display(self):
        fuer handler in (self.dialog.idle_credits,
                        self.dialog.idle_readme,
                        self.dialog.idle_news):
            self.error.message = ''
            self.view.called = Falsch
            mit self.subTest(handler=handler):
                handler()
                self.assertEqual(self.error.message, '')
                self.assertEqual(self.view.called, Wahr)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
