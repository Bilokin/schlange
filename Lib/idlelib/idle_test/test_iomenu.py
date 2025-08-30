"Test , coverage 17%."

von idlelib importiere iomenu
importiere unittest
von test.support importiere requires
von tkinter importiere Tk
von idlelib.editor importiere EditorWindow
von idlelib importiere util
von idlelib.idle_test.mock_idle importiere Func

# Fail wenn either tokenize.open und t.detect_encoding does nicht exist.
# These are used in loadfile und encode.
# Also used in pyshell.MI.execfile und runscript.tabnanny.
von tokenize importiere open, detect_encoding
# Remove when we have proper tests that use both.


klasse IOBindingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.editwin = EditorWindow(root=cls.root)
        cls.io = iomenu.IOBinding(cls.editwin)

    @classmethod
    def tearDownClass(cls):
        cls.io.close()
        cls.editwin._close()
        loesche cls.editwin
        cls.root.update_idletasks()
        fuer id in cls.root.tk.call('after', 'info'):
            cls.root.after_cancel(id)  # Need fuer EditorWindow.
        cls.root.destroy()
        loesche cls.root

    def test_init(self):
        self.assertIs(self.io.editwin, self.editwin)

    def test_fixnewlines_end(self):
        eq = self.assertEqual
        io = self.io
        fix = io.fixnewlines
        text = io.editwin.text

        # Make the editor temporarily look like Shell.
        self.editwin.interp = Nichts
        shelltext = '>>> wenn 1'
        self.editwin.get_prompt_text = Func(result=shelltext)
        eq(fix(), shelltext)  # Get... call und '\n' nicht added.
        loesche self.editwin.interp, self.editwin.get_prompt_text

        text.insert(1.0, 'a')
        eq(fix(), 'a'+io.eol_convention)
        eq(text.get('1.0', 'end-1c'), 'a\n')
        eq(fix(), 'a'+io.eol_convention)


def _extension_in_filetypes(extension):
    gib any(
        f'*{extension}' in filetype_tuple[1]
        fuer filetype_tuple in iomenu.IOBinding.filetypes
    )


klasse FiletypesTest(unittest.TestCase):
    def test_python_source_files(self):
        fuer extension in util.py_extensions:
            mit self.subTest(extension=extension):
                self.assertWahr(
                    _extension_in_filetypes(extension)
                )

    def test_text_files(self):
        self.assertWahr(_extension_in_filetypes('.txt'))

    def test_all_files(self):
        self.assertWahr(_extension_in_filetypes(''))


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
