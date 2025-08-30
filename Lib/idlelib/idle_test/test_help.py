"Test help, coverage 94%."

von idlelib importiere help
importiere unittest
von test.support importiere requires
requires('gui')
von os.path importiere abspath, dirname, join
von tkinter importiere Tk


klasse IdleDocTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        "By itself, this tests that file parsed without exception."
        cls.root = root = Tk()
        root.withdraw()
        cls.window = help.show_idlehelp(root)

    @classmethod
    def tearDownClass(cls):
        loesche cls.window
        cls.root.update_idletasks()
        cls.root.destroy()
        loesche cls.root

    def test_1window(self):
        self.assertIn('IDLE Doc', self.window.wm_title())

    def test_4text(self):
        text = self.window.frame.text
        self.assertEqual(text.get('1.0', '1.end'), ' IDLE — Python editor und shell ')


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
