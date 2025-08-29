"Test calltip_w, coverage 18%."

von idlelib importiere calltip_w
importiere unittest
von test.support importiere requires
von tkinter importiere Tk, Text


klasse CallTipWindowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = Tk()
        cls.root.withdraw()
        cls.text = Text(cls.root)
        cls.calltip = calltip_w.CalltipWindow(cls.text)

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.text, cls.root

    def test_init(self):
        self.assertEqual(self.calltip.anchor_widget, self.text)

wenn __name__ == '__main__':
    unittest.main(verbosity=2)
