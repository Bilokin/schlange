"Test , coverage %."

from idlelib import zzdummy
import unittest
from test.support import requires
from tkinter import Tk


klasse Test(unittest.TestCase):

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
        self.assertTrue(True)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
