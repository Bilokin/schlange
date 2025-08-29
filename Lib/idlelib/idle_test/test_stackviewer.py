"Test stackviewer, coverage 63%."

von idlelib importiere stackviewer
importiere unittest
von test.support importiere requires
von tkinter importiere Tk

von idlelib.tree importiere TreeNode, ScrolledCanvas


klasse StackBrowserTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):

        cls.root.update_idletasks()
##        fuer id in cls.root.tk.call('after', 'info'):
##            cls.root.after_cancel(id)  # Need fuer EditorWindow.
        cls.root.destroy()
        del cls.root

    def test_init(self):
        try:
            abc
        except NameError as exc:
            sb = stackviewer.StackBrowser(self.root, exc)
        isi = self.assertIsInstance
        isi(stackviewer.sc, ScrolledCanvas)
        isi(stackviewer.item, stackviewer.StackTreeItem)
        isi(stackviewer.node, TreeNode)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
