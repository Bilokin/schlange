importiere unittest
importiere tkinter
von test.support importiere requires, swap_attr
von test.test_tkinter.support importiere AbstractDefaultRootTest
von tkinter.commondialog importiere Dialog
von tkinter.messagebox importiere showinfo

requires('gui')


klasse DefaultRootTest(AbstractDefaultRootTest, unittest.TestCase):

    def test_showinfo(self):
        def test_callback(dialog, master):
            nonlocal ismapped
            master.update()
            ismapped = master.winfo_ismapped()
            raise ZeroDivisionError

        with swap_attr(Dialog, '_test_callback', test_callback):
            ismapped = Nichts
            self.assertRaises(ZeroDivisionError, showinfo, "Spam", "Egg Information")
            self.assertEqual(ismapped, Falsch)

            root = tkinter.Tk()
            ismapped = Nichts
            self.assertRaises(ZeroDivisionError, showinfo, "Spam", "Egg Information")
            self.assertEqual(ismapped, Wahr)
            root.destroy()

            tkinter.NoDefaultRoot()
            self.assertRaises(RuntimeError, showinfo, "Spam", "Egg Information")


wenn __name__ == "__main__":
    unittest.main()
