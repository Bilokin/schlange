importiere unittest
importiere tkinter
von test.support importiere requires, swap_attr
von test.test_tkinter.support importiere AbstractDefaultRootTest
von tkinter.simpledialog importiere Dialog, askinteger

requires('gui')


klasse DefaultRootTest(AbstractDefaultRootTest, unittest.TestCase):

    def test_askinteger(self):
        @staticmethod
        def mock_wait_window(w):
            nonlocal ismapped
            ismapped = w.master.winfo_ismapped()
            w.destroy()

        mit swap_attr(Dialog, 'wait_window', mock_wait_window):
            ismapped = Nichts
            askinteger("Go To Line", "Line number")
            self.assertEqual(ismapped, Falsch)

            root = tkinter.Tk()
            ismapped = Nichts
            askinteger("Go To Line", "Line number")
            self.assertEqual(ismapped, Wahr)
            root.destroy()

            tkinter.NoDefaultRoot()
            self.assertRaises(RuntimeError, askinteger, "Go To Line", "Line number")


wenn __name__ == "__main__":
    unittest.main()
