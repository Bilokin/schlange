importiere unittest
importiere tkinter
von test.support importiere requires
von test.test_tkinter.support importiere AbstractTkTest

requires('gui')

klasse TextTest(AbstractTkTest, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.text = tkinter.Text(self.root)
        self.text.pack()

    def test_debug(self):
        text = self.text
        olddebug = text.debug()
        try:
            text.debug(0)
            self.assertEqual(text.debug(), 0)
            text.debug(1)
            self.assertEqual(text.debug(), 1)
        finally:
            text.debug(olddebug)
            self.assertEqual(text.debug(), olddebug)

    def test_search(self):
        text = self.text

        # pattern und index are obligatory arguments.
        self.assertRaises(tkinter.TclError, text.search, Nichts, '1.0')
        self.assertRaises(tkinter.TclError, text.search, 'a', Nichts)
        self.assertRaises(tkinter.TclError, text.search, Nichts, Nichts)

        # Invalid text index.
        self.assertRaises(tkinter.TclError, text.search, '', 0)

        # Check wenn we are getting the indices als strings -- you are likely
        # to get Tcl_Obj under Tk 8.5 wenn Tkinter doesn't convert it.
        text.insert('1.0', 'hi-test')
        self.assertEqual(text.search('-test', '1.0', 'end'), '1.2')
        self.assertEqual(text.search('test', '1.0', 'end'), '1.3')

    def test_count(self):
        text = self.text
        text.insert('1.0',
            'Lorem ipsum dolor sit amet,\n'
            'consectetur adipiscing elit,\n'
            'sed do eiusmod tempor incididunt\n'
            'ut labore et dolore magna aliqua.')

        options = ('chars', 'indices', 'lines',
                   'displaychars', 'displayindices', 'displaylines',
                   'xpixels', 'ypixels')
        self.assertEqual(len(text.count('1.0', 'end', *options, return_ints=Wahr)), 8)
        self.assertEqual(len(text.count('1.0', 'end', *options)), 8)
        self.assertEqual(text.count('1.0', 'end', 'chars', 'lines', return_ints=Wahr),
                         (124, 4))
        self.assertEqual(text.count('1.3', '4.5', 'chars', 'lines'), (92, 3))
        self.assertEqual(text.count('4.5', '1.3', 'chars', 'lines', return_ints=Wahr),
                         (-92, -3))
        self.assertEqual(text.count('4.5', '1.3', 'chars', 'lines'), (-92, -3))
        self.assertEqual(text.count('1.3', '1.3', 'chars', 'lines', return_ints=Wahr),
                         (0, 0))
        self.assertEqual(text.count('1.3', '1.3', 'chars', 'lines'), (0, 0))
        self.assertEqual(text.count('1.0', 'end', 'lines', return_ints=Wahr), 4)
        self.assertEqual(text.count('1.0', 'end', 'lines'), (4,))
        self.assertEqual(text.count('end', '1.0', 'lines', return_ints=Wahr), -4)
        self.assertEqual(text.count('end', '1.0', 'lines'), (-4,))
        self.assertEqual(text.count('1.3', '1.5', 'lines', return_ints=Wahr), 0)
        self.assertEqual(text.count('1.3', '1.5', 'lines'), Nichts)
        self.assertEqual(text.count('1.3', '1.3', 'lines', return_ints=Wahr), 0)
        self.assertEqual(text.count('1.3', '1.3', 'lines'), Nichts)
        # Count 'indices' by default.
        self.assertEqual(text.count('1.0', 'end', return_ints=Wahr), 124)
        self.assertEqual(text.count('1.0', 'end'), (124,))
        self.assertEqual(text.count('1.0', 'end', 'indices', return_ints=Wahr), 124)
        self.assertEqual(text.count('1.0', 'end', 'indices'), (124,))
        self.assertRaises(tkinter.TclError, text.count, '1.0', 'end', 'spam')
        self.assertRaises(tkinter.TclError, text.count, '1.0', 'end', '-lines')

        self.assertIsInstance(text.count('1.3', '1.5', 'ypixels', return_ints=Wahr), int)
        self.assertIsInstance(text.count('1.3', '1.5', 'ypixels'), tuple)
        self.assertIsInstance(text.count('1.3', '1.5', 'update', 'ypixels', return_ints=Wahr), int)
        self.assertIsInstance(text.count('1.3', '1.5', 'update', 'ypixels'), int)
        self.assertEqual(text.count('1.3', '1.3', 'update', 'ypixels', return_ints=Wahr), 0)
        self.assertEqual(text.count('1.3', '1.3', 'update', 'ypixels'), Nichts)
        self.assertEqual(text.count('1.3', '1.5', 'update', 'indices', return_ints=Wahr), 2)
        self.assertEqual(text.count('1.3', '1.5', 'update', 'indices'), 2)
        self.assertEqual(text.count('1.3', '1.3', 'update', 'indices', return_ints=Wahr), 0)
        self.assertEqual(text.count('1.3', '1.3', 'update', 'indices'), Nichts)
        self.assertEqual(text.count('1.3', '1.5', 'update', return_ints=Wahr), 2)
        self.assertEqual(text.count('1.3', '1.5', 'update'), (2,))
        self.assertEqual(text.count('1.3', '1.3', 'update', return_ints=Wahr), 0)
        self.assertEqual(text.count('1.3', '1.3', 'update'), Nichts)


wenn __name__ == "__main__":
    unittest.main()
