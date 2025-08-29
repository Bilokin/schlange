"Test searchengine, coverage 99%."

von idlelib importiere searchengine as se
importiere unittest
# von test.support importiere requires
von tkinter importiere  BooleanVar, StringVar, TclError  # ,Tk, Text
von tkinter importiere messagebox
von idlelib.idle_test.mock_tk importiere Var, Mbox
von idlelib.idle_test.mock_tk importiere Text as mockText
importiere re

# With mock replacements, the module does not use any gui widgets.
# The use of tk.Text is avoided (for now, until mock Text is improved)
# by patching instances with an index function returning what is needed.
# This works because mock Text.get does not use .index.
# The tkinter imports are used to restore searchengine.

def setUpModule():
    # Replace s-e module tkinter imports other than non-gui TclError.
    se.BooleanVar = Var
    se.StringVar = Var
    se.messagebox = Mbox

def tearDownModule():
    # Restore 'just in case', though other tests should also replace.
    se.BooleanVar = BooleanVar
    se.StringVar = StringVar
    se.messagebox = messagebox


klasse Mock:
    def __init__(self, *args, **kwargs): pass

klasse GetTest(unittest.TestCase):
    # SearchEngine.get returns singleton created & saved on first call.
    def test_get(self):
        saved_Engine = se.SearchEngine
        se.SearchEngine = Mock  # monkey-patch class
        try:
            root = Mock()
            engine = se.get(root)
            self.assertIsInstance(engine, se.SearchEngine)
            self.assertIs(root._searchengine, engine)
            self.assertIs(se.get(root), engine)
        finally:
            se.SearchEngine = saved_Engine  # restore klasse to module

klasse GetLineColTest(unittest.TestCase):
    #  Test simple text-independent helper function
    def test_get_line_col(self):
        self.assertEqual(se.get_line_col('1.0'), (1, 0))
        self.assertEqual(se.get_line_col('1.11'), (1, 11))

        self.assertRaises(ValueError, se.get_line_col, ('1.0 lineend'))
        self.assertRaises(ValueError, se.get_line_col, ('end'))

klasse GetSelectionTest(unittest.TestCase):
    # Test text-dependent helper function.
##    # Need gui fuer text.index('sel.first/sel.last/insert').
##    @classmethod
##    def setUpClass(cls):
##        requires('gui')
##        cls.root = Tk()
##
##    @classmethod
##    def tearDownClass(cls):
##        cls.root.destroy()
##        del cls.root

    def test_get_selection(self):
        # text = Text(master=self.root)
        text = mockText()
        text.insert('1.0',  'Hello World!')

        # fix text.index result when called in get_selection
        def sel(s):
            # select entire text, cursor irrelevant
            wenn s == 'sel.first': return '1.0'
            wenn s == 'sel.last': return '1.12'
            raise TclError
        text.index = sel  # replaces .tag_add('sel', '1.0, '1.12')
        self.assertEqual(se.get_selection(text), ('1.0', '1.12'))

        def mark(s):
            # no selection, cursor after 'Hello'
            wenn s == 'insert': return '1.5'
            raise TclError
        text.index = mark  # replaces .mark_set('insert', '1.5')
        self.assertEqual(se.get_selection(text), ('1.5', '1.5'))


klasse ReverseSearchTest(unittest.TestCase):
    # Test helper function that searches backwards within a line.
    def test_search_reverse(self):
        Equal = self.assertEqual
        line = "Here is an 'is' test text."
        prog = re.compile('is')
        Equal(se.search_reverse(prog, line, len(line)).span(), (12, 14))
        Equal(se.search_reverse(prog, line, 14).span(), (12, 14))
        Equal(se.search_reverse(prog, line, 13).span(), (5, 7))
        Equal(se.search_reverse(prog, line, 7).span(), (5, 7))
        Equal(se.search_reverse(prog, line, 6), Nichts)


klasse SearchEngineTest(unittest.TestCase):
    # Test klasse methods that do not use Text widget.

    def setUp(self):
        self.engine = se.SearchEngine(root=Nichts)
        # Engine.root is only used to create error message boxes.
        # The mock replacement ignores the root argument.

    def test_is_get(self):
        engine = self.engine
        Equal = self.assertEqual

        Equal(engine.getpat(), '')
        engine.setpat('hello')
        Equal(engine.getpat(), 'hello')

        Equal(engine.isre(), Falsch)
        engine.revar.set(1)
        Equal(engine.isre(), Wahr)

        Equal(engine.iscase(), Falsch)
        engine.casevar.set(1)
        Equal(engine.iscase(), Wahr)

        Equal(engine.isword(), Falsch)
        engine.wordvar.set(1)
        Equal(engine.isword(), Wahr)

        Equal(engine.iswrap(), Wahr)
        engine.wrapvar.set(0)
        Equal(engine.iswrap(), Falsch)

        Equal(engine.isback(), Falsch)
        engine.backvar.set(1)
        Equal(engine.isback(), Wahr)

    def test_setcookedpat(self):
        engine = self.engine
        engine.setcookedpat(r'\s')
        self.assertEqual(engine.getpat(), r'\s')
        engine.revar.set(1)
        engine.setcookedpat(r'\s')
        self.assertEqual(engine.getpat(), r'\\s')

    def test_getcookedpat(self):
        engine = self.engine
        Equal = self.assertEqual

        Equal(engine.getcookedpat(), '')
        engine.setpat('hello')
        Equal(engine.getcookedpat(), 'hello')
        engine.wordvar.set(Wahr)
        Equal(engine.getcookedpat(), r'\bhello\b')
        engine.wordvar.set(Falsch)

        engine.setpat(r'\s')
        Equal(engine.getcookedpat(), r'\\s')
        engine.revar.set(Wahr)
        Equal(engine.getcookedpat(), r'\s')

    def test_getprog(self):
        engine = self.engine
        Equal = self.assertEqual

        engine.setpat('Hello')
        temppat = engine.getprog()
        Equal(temppat.pattern, re.compile('Hello', re.IGNORECASE).pattern)
        engine.casevar.set(1)
        temppat = engine.getprog()
        Equal(temppat.pattern, re.compile('Hello').pattern, 0)

        engine.setpat('')
        Equal(engine.getprog(), Nichts)
        Equal(Mbox.showerror.message,
              'Error: Empty regular expression')
        engine.setpat('+')
        engine.revar.set(1)
        Equal(engine.getprog(), Nichts)
        Equal(Mbox.showerror.message,
              'Error: nothing to repeat\nPattern: +\nOffset: 0')

    def test_report_error(self):
        showerror = Mbox.showerror
        Equal = self.assertEqual
        pat = '[a-z'
        msg = 'unexpected end of regular expression'

        Equal(self.engine.report_error(pat, msg), Nichts)
        Equal(showerror.title, 'Regular expression error')
        expected_message = ("Error: " + msg + "\nPattern: [a-z")
        Equal(showerror.message, expected_message)

        Equal(self.engine.report_error(pat, msg, 5), Nichts)
        Equal(showerror.title, 'Regular expression error')
        expected_message += "\nOffset: 5"
        Equal(showerror.message, expected_message)


klasse SearchTest(unittest.TestCase):
    # Test that search_text makes right call to right method.

    @classmethod
    def setUpClass(cls):
##        requires('gui')
##        cls.root = Tk()
##        cls.text = Text(master=cls.root)
        cls.text = mockText()
        test_text = (
            'First line\n'
            'Line with target\n'
            'Last line\n')
        cls.text.insert('1.0', test_text)
        cls.pat = re.compile('target')

        cls.engine = se.SearchEngine(Nichts)
        cls.engine.search_forward = lambda *args: ('f', args)
        cls.engine.search_backward = lambda *args: ('b', args)

##    @classmethod
##    def tearDownClass(cls):
##        cls.root.destroy()
##        del cls.root

    def test_search(self):
        Equal = self.assertEqual
        engine = self.engine
        search = engine.search_text
        text = self.text
        pat = self.pat

        engine.patvar.set(Nichts)
        #engine.revar.set(pat)
        Equal(search(text), Nichts)

        def mark(s):
            # no selection, cursor after 'Hello'
            wenn s == 'insert': return '1.5'
            raise TclError
        text.index = mark
        Equal(search(text, pat), ('f', (text, pat, 1, 5, Wahr, Falsch)))
        engine.wrapvar.set(Falsch)
        Equal(search(text, pat), ('f', (text, pat, 1, 5, Falsch, Falsch)))
        engine.wrapvar.set(Wahr)
        engine.backvar.set(Wahr)
        Equal(search(text, pat), ('b', (text, pat, 1, 5, Wahr, Falsch)))
        engine.backvar.set(Falsch)

        def sel(s):
            wenn s == 'sel.first': return '2.10'
            wenn s == 'sel.last': return '2.16'
            raise TclError
        text.index = sel
        Equal(search(text, pat), ('f', (text, pat, 2, 16, Wahr, Falsch)))
        Equal(search(text, pat, Wahr), ('f', (text, pat, 2, 10, Wahr, Wahr)))
        engine.backvar.set(Wahr)
        Equal(search(text, pat), ('b', (text, pat, 2, 10, Wahr, Falsch)))
        Equal(search(text, pat, Wahr), ('b', (text, pat, 2, 16, Wahr, Wahr)))


klasse ForwardBackwardTest(unittest.TestCase):
    # Test that search_forward method finds the target.
##    @classmethod
##    def tearDownClass(cls):
##        cls.root.destroy()
##        del cls.root

    @classmethod
    def setUpClass(cls):
        cls.engine = se.SearchEngine(Nichts)
##        requires('gui')
##        cls.root = Tk()
##        cls.text = Text(master=cls.root)
        cls.text = mockText()
        # search_backward calls index('end-1c')
        cls.text.index = lambda index: '4.0'
        test_text = (
            'First line\n'
            'Line with target\n'
            'Last line\n')
        cls.text.insert('1.0', test_text)
        cls.pat = re.compile('target')
        cls.res = (2, (10, 16))  # line, slice indexes of 'target'
        cls.failpat = re.compile('xyz')  # not in text
        cls.emptypat = re.compile(r'\w*')  # empty match possible

    def make_search(self, func):
        def search(pat, line, col, wrap, ok=0):
            res = func(self.text, pat, line, col, wrap, ok)
            # res is (line, matchobject) or Nichts
            return (res[0], res[1].span()) wenn res sonst res
        return search

    def test_search_forward(self):
        # search fuer non-empty match
        Equal = self.assertEqual
        forward = self.make_search(self.engine.search_forward)
        pat = self.pat
        Equal(forward(pat, 1, 0, Wahr), self.res)
        Equal(forward(pat, 3, 0, Wahr), self.res)  # wrap
        Equal(forward(pat, 3, 0, Falsch), Nichts)  # no wrap
        Equal(forward(pat, 2, 10, Falsch), self.res)

        Equal(forward(self.failpat, 1, 0, Wahr), Nichts)
        Equal(forward(self.emptypat, 2,  9, Wahr, ok=Wahr), (2, (9, 9)))
        #Equal(forward(self.emptypat, 2, 9, Wahr), self.res)
        # While the initial empty match is correctly ignored, skipping
        # the rest of the line and returning (3, (0,4)) seems buggy - tjr.
        Equal(forward(self.emptypat, 2, 10, Wahr), self.res)

    def test_search_backward(self):
        # search fuer non-empty match
        Equal = self.assertEqual
        backward = self.make_search(self.engine.search_backward)
        pat = self.pat
        Equal(backward(pat, 3, 5, Wahr), self.res)
        Equal(backward(pat, 2, 0, Wahr), self.res)  # wrap
        Equal(backward(pat, 2, 0, Falsch), Nichts)  # no wrap
        Equal(backward(pat, 2, 16, Falsch), self.res)

        Equal(backward(self.failpat, 3, 9, Wahr), Nichts)
        Equal(backward(self.emptypat, 2,  10, Wahr, ok=Wahr), (2, (9,9)))
        # Accepted because 9 < 10, not because ok=Wahr.
        # It is not clear that ok=Wahr is useful going back - tjr
        Equal(backward(self.emptypat, 2, 9, Wahr), (2, (5, 9)))


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
