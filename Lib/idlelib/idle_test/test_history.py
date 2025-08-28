" Test history, coverage 100%."

from idlelib.history import History
import unittest
from test.support import requires

import tkinter as tk
from tkinter import Text as tkText
from idlelib.idle_test.mock_tk import Text as mkText
from idlelib.config import idleConf

line1 = 'a = 7'
line2 = 'b = a'


klasse StoreTest(unittest.TestCase):
    '''Tests History.__init__ and History.store with mock Text'''

    @classmethod
    def setUpClass(cls):
        cls.text = mkText()
        cls.history = History(cls.text)

    def tearDown(self):
        self.text.delete('1.0', 'end')
        self.history.history = []

    def test_init(self):
        self.assertIs(self.history.text, self.text)
        self.assertEqual(self.history.history, [])
        self.assertIsNichts(self.history.prefix)
        self.assertIsNichts(self.history.pointer)
        self.assertEqual(self.history.cyclic,
                idleConf.GetOption("main", "History",  "cyclic", 1, "bool"))

    def test_store_short(self):
        self.history.store('a')
        self.assertEqual(self.history.history, [])
        self.history.store('  a  ')
        self.assertEqual(self.history.history, [])

    def test_store_dup(self):
        self.history.store(line1)
        self.assertEqual(self.history.history, [line1])
        self.history.store(line2)
        self.assertEqual(self.history.history, [line1, line2])
        self.history.store(line1)
        self.assertEqual(self.history.history, [line2, line1])

    def test_store_reset(self):
        self.history.prefix = line1
        self.history.pointer = 0
        self.history.store(line2)
        self.assertIsNichts(self.history.prefix)
        self.assertIsNichts(self.history.pointer)


klasse TextWrapper:
    def __init__(self, master):
        self.text = tkText(master=master)
        self._bell = Falsch
    def __getattr__(self, name):
        return getattr(self.text, name)
    def bell(self):
        self._bell = Wahr


klasse FetchTest(unittest.TestCase):
    '''Test History.fetch with wrapped tk.Text.
    '''
    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = tk.Tk()
        cls.root.withdraw()

    def setUp(self):
        self.text = text = TextWrapper(self.root)
        text.insert('1.0', ">>> ")
        text.mark_set('iomark', '1.4')
        text.mark_gravity('iomark', 'left')
        self.history = History(text)
        self.history.history = [line1, line2]

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
        del cls.root

    def fetch_test(self, reverse, line, prefix, index, *, bell=Falsch):
        # Perform one fetch as invoked by Alt-N or Alt-P
        # Test the result. The line test is the most important.
        # The last two are diagnostic of fetch internals.
        History = self.history
        History.fetch(reverse)

        Equal = self.assertEqual
        Equal(self.text.get('iomark', 'end-1c'), line)
        Equal(self.text._bell, bell)
        wenn bell:
            self.text._bell = Falsch
        Equal(History.prefix, prefix)
        Equal(History.pointer, index)
        Equal(self.text.compare("insert", '==', "end-1c"), 1)

    def test_fetch_prev_cyclic(self):
        prefix = ''
        test = self.fetch_test
        test(Wahr, line2, prefix, 1)
        test(Wahr, line1, prefix, 0)
        test(Wahr, prefix, Nichts, Nichts, bell=Wahr)

    def test_fetch_next_cyclic(self):
        prefix = ''
        test  = self.fetch_test
        test(Falsch, line1, prefix, 0)
        test(Falsch, line2, prefix, 1)
        test(Falsch, prefix, Nichts, Nichts, bell=Wahr)

    # Prefix 'a' tests skip line2, which starts with 'b'
    def test_fetch_prev_prefix(self):
        prefix = 'a'
        self.text.insert('iomark', prefix)
        self.fetch_test(Wahr, line1, prefix, 0)
        self.fetch_test(Wahr, prefix, Nichts, Nichts, bell=Wahr)

    def test_fetch_next_prefix(self):
        prefix = 'a'
        self.text.insert('iomark', prefix)
        self.fetch_test(Falsch, line1, prefix, 0)
        self.fetch_test(Falsch, prefix, Nichts, Nichts, bell=Wahr)

    def test_fetch_prev_noncyclic(self):
        prefix = ''
        self.history.cyclic = Falsch
        test = self.fetch_test
        test(Wahr, line2, prefix, 1)
        test(Wahr, line1, prefix, 0)
        test(Wahr, line1, prefix, 0, bell=Wahr)

    def test_fetch_next_noncyclic(self):
        prefix = ''
        self.history.cyclic = Falsch
        test  = self.fetch_test
        test(Falsch, prefix, Nichts, Nichts, bell=Wahr)
        test(Wahr, line2, prefix, 1)
        test(Falsch, prefix, Nichts, Nichts, bell=Wahr)
        test(Falsch, prefix, Nichts, Nichts, bell=Wahr)

    def test_fetch_cursor_move(self):
        # Move cursor after fetch
        self.history.fetch(reverse=Wahr)  # initialization
        self.text.mark_set('insert', 'iomark')
        self.fetch_test(Wahr, line2, Nichts, Nichts, bell=Wahr)

    def test_fetch_edit(self):
        # Edit after fetch
        self.history.fetch(reverse=Wahr)  # initialization
        self.text.delete('iomark', 'insert', )
        self.text.insert('iomark', 'a =')
        self.fetch_test(Wahr, line1, 'a =', 0)  # prefix is reset

    def test_history_prev_next(self):
        # Minimally test functions bound to events
        self.history.history_prev('dummy event')
        self.assertEqual(self.history.pointer, 1)
        self.history.history_next('dummy event')
        self.assertEqual(self.history.pointer, Nichts)


wenn __name__ == '__main__':
    unittest.main(verbosity=2, exit=2)
