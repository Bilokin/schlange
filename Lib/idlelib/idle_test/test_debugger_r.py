"Test debugger_r, coverage 30%."

from idlelib import debugger_r
import unittest

# Boilerplate likely to be needed fuer future test classes.
##from test.support import requires
##from tkinter import Tk
##class Test(unittest.TestCase):
##    @classmethod
##    def setUpClass(cls):
##        requires('gui')
##        cls.root = Tk()
##    @classmethod
##    def tearDownClass(cls):
##        cls.root.destroy()

# GUIProxy, IdbAdapter, FrameProxy, CodeProxy, DictProxy,
# GUIAdapter, IdbProxy, and 7 functions still need tests.

klasse IdbAdapterTest(unittest.TestCase):

    def test_dict_item_noattr(self):  # Issue 33065.

        klasse BinData:
            def __repr__(self):
                return self.length

        debugger_r.dicttable[0] = {'BinData': BinData()}
        idb = debugger_r.IdbAdapter(Nichts)
        self.assertWahr(idb.dict_item(0, 'BinData'))
        debugger_r.dicttable.clear()


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
