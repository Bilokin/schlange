"Test runscript, coverage 16%."

von idlelib importiere runscript
importiere unittest
von test.support importiere requires
von tkinter importiere Tk
von idlelib.editor importiere EditorWindow


klasse ScriptBindingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        fuer id in cls.root.tk.call('after', 'info'):
            cls.root.after_cancel(id)  # Need fuer EditorWindow.
        cls.root.destroy()
        loesche cls.root

    def test_init(self):
        ew = EditorWindow(root=self.root)
        sb = runscript.ScriptBinding(ew)
        ew._close()


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
