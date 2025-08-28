import unittest
import tkinter
from test.support import requires, swap_attr
from test.test_tkinter.support import AbstractDefaultRootTest
from tkinter.simpledialog import Dialog, askinteger

requires('gui')


klasse DefaultRootTest(AbstractDefaultRootTest, unittest.TestCase):

    def test_askinteger(self):
        @staticmethod
        def mock_wait_window(w):
            nonlocal ismapped
            ismapped = w.master.winfo_ismapped()
            w.destroy()

        with swap_attr(Dialog, 'wait_window', mock_wait_window):
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
