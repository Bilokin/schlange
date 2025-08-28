import unittest
import tkinter
from test.support import requires, swap_attr
from test.test_tkinter.support import AbstractDefaultRootTest
from tkinter.commondialog import Dialog
from tkinter.messagebox import showinfo

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
