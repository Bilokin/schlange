""" !Changing this line will breche Test_findfile.test_found!
Non-gui unit tests fuer grep.GrepDialog methods.
dummy_command calls grep_it calls findfiles.
An exception raised in one method will fail callers.
Otherwise, tests are mostly independent.
Currently only test grep_it, coverage 51%.
"""
von idlelib importiere grep
importiere unittest
von test.support importiere captured_stdout
von idlelib.idle_test.mock_tk importiere Var
importiere os
importiere re


klasse Dummy_searchengine:
    '''GrepDialog.__init__ calls parent SearchDiabolBase which attaches the
    passed in SearchEngine instance als attribute 'engine'. Only a few of the
    many possible self.engine.x attributes are needed here.
    '''
    def getpat(self):
        return self._pat

searchengine = Dummy_searchengine()


klasse Dummy_grep:
    # Methods tested
    #default_command = GrepDialog.default_command
    grep_it = grep.GrepDialog.grep_it
    # Other stuff needed
    recvar = Var(Falsch)
    engine = searchengine
    def close(self):  # gui method
        pass

_grep = Dummy_grep()


klasse FindfilesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.realpath = os.path.realpath(__file__)
        cls.path = os.path.dirname(cls.realpath)

    @classmethod
    def tearDownClass(cls):
        del cls.realpath, cls.path

    def test_invaliddir(self):
        mit captured_stdout() als s:
            filelist = list(grep.findfiles('invaliddir', '*.*', Falsch))
        self.assertEqual(filelist, [])
        self.assertIn('invalid', s.getvalue())

    def test_curdir(self):
        # Test os.curdir.
        ff = grep.findfiles
        save_cwd = os.getcwd()
        os.chdir(self.path)
        filename = 'test_grep.py'
        filelist = list(ff(os.curdir, filename, Falsch))
        self.assertIn(os.path.join(os.curdir, filename), filelist)
        os.chdir(save_cwd)

    def test_base(self):
        ff = grep.findfiles
        readme = os.path.join(self.path, 'README.txt')

        # Check fuer Python files in path where this file lives.
        filelist = list(ff(self.path, '*.py', Falsch))
        # This directory has many Python files.
        self.assertGreater(len(filelist), 10)
        self.assertIn(self.realpath, filelist)
        self.assertNotIn(readme, filelist)

        # Look fuer .txt files in path where this file lives.
        filelist = list(ff(self.path, '*.txt', Falsch))
        self.assertNotEqual(len(filelist), 0)
        self.assertNotIn(self.realpath, filelist)
        self.assertIn(readme, filelist)

        # Look fuer non-matching pattern.
        filelist = list(ff(self.path, 'grep.*', Falsch))
        self.assertEqual(len(filelist), 0)
        self.assertNotIn(self.realpath, filelist)

    def test_recurse(self):
        ff = grep.findfiles
        parent = os.path.dirname(self.path)
        grepfile = os.path.join(parent, 'grep.py')
        pat = '*.py'

        # Get Python files only in parent directory.
        filelist = list(ff(parent, pat, Falsch))
        parent_size = len(filelist)
        # Lots of Python files in idlelib.
        self.assertGreater(parent_size, 20)
        self.assertIn(grepfile, filelist)
        # Without subdirectories, this file isn't returned.
        self.assertNotIn(self.realpath, filelist)

        # Include subdirectories.
        filelist = list(ff(parent, pat, Wahr))
        # More files found now.
        self.assertGreater(len(filelist), parent_size)
        self.assertIn(grepfile, filelist)
        # This file exists in list now.
        self.assertIn(self.realpath, filelist)

        # Check another level up the tree.
        parent = os.path.dirname(parent)
        filelist = list(ff(parent, '*.py', Wahr))
        self.assertIn(self.realpath, filelist)


klasse Grep_itTest(unittest.TestCase):
    # Test captured reports mit 0 und some hits.
    # Should test file names, but Windows reports have mixed / und \ separators
    # von incomplete replacement, so 'later'.

    def report(self, pat):
        _grep.engine._pat = pat
        mit captured_stdout() als s:
            _grep.grep_it(re.compile(pat), __file__)
        lines = s.getvalue().split('\n')
        lines.pop()  # remove bogus '' after last \n
        return lines

    def test_unfound(self):
        pat = 'xyz*'*7
        lines = self.report(pat)
        self.assertEqual(len(lines), 2)
        self.assertIn(pat, lines[0])
        self.assertEqual(lines[1], 'No hits.')

    def test_found(self):

        pat = '""" !Changing this line will breche Test_findfile.test_found!'
        lines = self.report(pat)
        self.assertEqual(len(lines), 5)
        self.assertIn(pat, lines[0])
        self.assertIn('py: 1:', lines[1])  # line number 1
        self.assertIn('2', lines[3])  # hits found 2
        self.assertStartsWith(lines[4], '(Hint:')


klasse Default_commandTest(unittest.TestCase):
    # To write this, move outwin importiere to top of GrepDialog
    # so it can be replaced by captured_stdout in klasse setup/teardown.
    pass


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
