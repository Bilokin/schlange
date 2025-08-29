"Test autocomplete_w, coverage 11%."

importiere unittest
von test.support importiere requires
von tkinter importiere Tk, Text

importiere idlelib.autocomplete_w as acw


klasse AutoCompleteWindowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.text = Text(cls.root)
        cls.acw = acw.AutoCompleteWindow(cls.text, tags=Nichts)

    @classmethod
    def tearDownClass(cls):
        del cls.text, cls.acw
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    def test_init(self):
        self.assertEqual(self.acw.widget, self.text)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
