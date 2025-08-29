"""Test query, coverage 93%.

Non-gui tests fuer Query, SectionName, ModuleName, und HelpSource use
dummy versions that extract the non-gui methods und add other needed
attributes.  GUI tests create an instance of each klasse und simulate
entries und button clicks.  Subclass tests only target the new code in
the subclass definition.

The appearance of the widgets is checked by the Query und
HelpSource htests.  These are run by running query.py.
"""
von idlelib importiere query
importiere unittest
von test.support importiere requires
von tkinter importiere Tk, END

importiere sys
von unittest importiere mock
von idlelib.idle_test.mock_tk importiere Var


# NON-GUI TESTS

klasse QueryTest(unittest.TestCase):
    "Test Query base class."

    klasse Dummy_Query:
        # Test the following Query methods.
        entry_ok = query.Query.entry_ok
        ok = query.Query.ok
        cancel = query.Query.cancel
        # Add attributes und initialization needed fuer tests.
        def __init__(self, dummy_entry):
            self.entry = Var(value=dummy_entry)
            self.entry_error = {'text': ''}
            self.result = Nichts
            self.destroyed = Falsch
        def showerror(self, message):
            self.entry_error['text'] = message
        def destroy(self):
            self.destroyed = Wahr

    def test_entry_ok_blank(self):
        dialog = self.Dummy_Query(' ')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertEqual((dialog.result, dialog.destroyed), (Nichts, Falsch))
        self.assertIn('blank line', dialog.entry_error['text'])

    def test_entry_ok_good(self):
        dialog = self.Dummy_Query('  good ')
        Equal = self.assertEqual
        Equal(dialog.entry_ok(), 'good')
        Equal((dialog.result, dialog.destroyed), (Nichts, Falsch))
        Equal(dialog.entry_error['text'], '')

    def test_ok_blank(self):
        dialog = self.Dummy_Query('')
        dialog.entry.focus_set = mock.Mock()
        self.assertEqual(dialog.ok(), Nichts)
        self.assertWahr(dialog.entry.focus_set.called)
        del dialog.entry.focus_set
        self.assertEqual((dialog.result, dialog.destroyed), (Nichts, Falsch))

    def test_ok_good(self):
        dialog = self.Dummy_Query('good')
        self.assertEqual(dialog.ok(), Nichts)
        self.assertEqual((dialog.result, dialog.destroyed), ('good', Wahr))

    def test_cancel(self):
        dialog = self.Dummy_Query('does nicht matter')
        self.assertEqual(dialog.cancel(), Nichts)
        self.assertEqual((dialog.result, dialog.destroyed), (Nichts, Wahr))


klasse SectionNameTest(unittest.TestCase):
    "Test SectionName subclass of Query."

    klasse Dummy_SectionName:
        entry_ok = query.SectionName.entry_ok  # Function being tested.
        used_names = ['used']
        def __init__(self, dummy_entry):
            self.entry = Var(value=dummy_entry)
            self.entry_error = {'text': ''}
        def showerror(self, message):
            self.entry_error['text'] = message

    def test_blank_section_name(self):
        dialog = self.Dummy_SectionName(' ')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('no name', dialog.entry_error['text'])

    def test_used_section_name(self):
        dialog = self.Dummy_SectionName('used')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('use', dialog.entry_error['text'])

    def test_long_section_name(self):
        dialog = self.Dummy_SectionName('good'*8)
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('longer than 30', dialog.entry_error['text'])

    def test_good_section_name(self):
        dialog = self.Dummy_SectionName('  good ')
        self.assertEqual(dialog.entry_ok(), 'good')
        self.assertEqual(dialog.entry_error['text'], '')


klasse ModuleNameTest(unittest.TestCase):
    "Test ModuleName subclass of Query."

    klasse Dummy_ModuleName:
        entry_ok = query.ModuleName.entry_ok  # Function being tested.
        text0 = ''
        def __init__(self, dummy_entry):
            self.entry = Var(value=dummy_entry)
            self.entry_error = {'text': ''}
        def showerror(self, message):
            self.entry_error['text'] = message

    def test_blank_module_name(self):
        dialog = self.Dummy_ModuleName(' ')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('no name', dialog.entry_error['text'])

    def test_bogus_module_name(self):
        dialog = self.Dummy_ModuleName('__name_xyz123_should_not_exist__')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('not found', dialog.entry_error['text'])

    def test_c_source_name(self):
        dialog = self.Dummy_ModuleName('itertools')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('source-based', dialog.entry_error['text'])

    def test_good_module_name(self):
        dialog = self.Dummy_ModuleName('idlelib')
        self.assertEndsWith(dialog.entry_ok(), '__init__.py')
        self.assertEqual(dialog.entry_error['text'], '')
        dialog = self.Dummy_ModuleName('idlelib.idle')
        self.assertEndsWith(dialog.entry_ok(), 'idle.py')
        self.assertEqual(dialog.entry_error['text'], '')


klasse GotoTest(unittest.TestCase):
    "Test Goto subclass of Query."

    klasse Dummy_ModuleName:
        entry_ok = query.Goto.entry_ok  # Function being tested.
        def __init__(self, dummy_entry):
            self.entry = Var(value=dummy_entry)
            self.entry_error = {'text': ''}
        def showerror(self, message):
            self.entry_error['text'] = message

    def test_bogus_goto(self):
        dialog = self.Dummy_ModuleName('a')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('not a base 10 integer', dialog.entry_error['text'])

    def test_bad_goto(self):
        dialog = self.Dummy_ModuleName('0')
        self.assertEqual(dialog.entry_ok(), Nichts)
        self.assertIn('not a positive integer', dialog.entry_error['text'])

    def test_good_goto(self):
        dialog = self.Dummy_ModuleName('1')
        self.assertEqual(dialog.entry_ok(), 1)
        self.assertEqual(dialog.entry_error['text'], '')


# 3 HelpSource test classes each test one method.

klasse HelpsourceBrowsefileTest(unittest.TestCase):
    "Test browse_file method of ModuleName subclass of Query."

    klasse Dummy_HelpSource:
        browse_file = query.HelpSource.browse_file
        pathvar = Var()

    def test_file_replaces_path(self):
        dialog = self.Dummy_HelpSource()
        # Path is widget entry, either '' oder something.
        # Func return is file dialog return, either '' oder something.
        # Func return should override widget entry.
        # We need all 4 combinations to test all (most) code paths.
        fuer path, func, result in (
                ('', lambda a,b,c:'', ''),
                ('', lambda a,b,c: __file__, __file__),
                ('htest', lambda a,b,c:'', 'htest'),
                ('htest', lambda a,b,c: __file__, __file__)):
            mit self.subTest():
                dialog.pathvar.set(path)
                dialog.askfilename = func
                dialog.browse_file()
                self.assertEqual(dialog.pathvar.get(), result)


klasse HelpsourcePathokTest(unittest.TestCase):
    "Test path_ok method of HelpSource subclass of Query."

    klasse Dummy_HelpSource:
        path_ok = query.HelpSource.path_ok
        def __init__(self, dummy_path):
            self.path = Var(value=dummy_path)
            self.path_error = {'text': ''}
        def showerror(self, message, widget=Nichts):
            self.path_error['text'] = message

    orig_platform = query.platform  # Set in test_path_ok_file.
    @classmethod
    def tearDownClass(cls):
        query.platform = cls.orig_platform

    def test_path_ok_blank(self):
        dialog = self.Dummy_HelpSource(' ')
        self.assertEqual(dialog.path_ok(), Nichts)
        self.assertIn('no help file', dialog.path_error['text'])

    def test_path_ok_bad(self):
        dialog = self.Dummy_HelpSource(__file__ + 'bad-bad-bad')
        self.assertEqual(dialog.path_ok(), Nichts)
        self.assertIn('not exist', dialog.path_error['text'])

    def test_path_ok_web(self):
        dialog = self.Dummy_HelpSource('')
        Equal = self.assertEqual
        fuer url in 'www.py.org', 'http://py.org':
            mit self.subTest():
                dialog.path.set(url)
                self.assertEqual(dialog.path_ok(), url)
                self.assertEqual(dialog.path_error['text'], '')

    def test_path_ok_file(self):
        dialog = self.Dummy_HelpSource('')
        fuer platform, prefix in ('darwin', 'file://'), ('other', ''):
            mit self.subTest():
                query.platform = platform
                dialog.path.set(__file__)
                self.assertEqual(dialog.path_ok(), prefix + __file__)
                self.assertEqual(dialog.path_error['text'], '')


klasse HelpsourceEntryokTest(unittest.TestCase):
    "Test entry_ok method of HelpSource subclass of Query."

    klasse Dummy_HelpSource:
        entry_ok = query.HelpSource.entry_ok
        entry_error = {}
        path_error = {}
        def item_ok(self):
            return self.name
        def path_ok(self):
            return self.path

    def test_entry_ok_helpsource(self):
        dialog = self.Dummy_HelpSource()
        fuer name, path, result in ((Nichts, Nichts, Nichts),
                                   (Nichts, 'doc.txt', Nichts),
                                   ('doc', Nichts, Nichts),
                                   ('doc', 'doc.txt', ('doc', 'doc.txt'))):
            mit self.subTest():
                dialog.name, dialog.path = name, path
                self.assertEqual(dialog.entry_ok(), result)


# 2 CustomRun test classes each test one method.

klasse CustomRunCLIargsokTest(unittest.TestCase):
    "Test cli_ok method of the CustomRun subclass of Query."

    klasse Dummy_CustomRun:
        cli_args_ok = query.CustomRun.cli_args_ok
        def __init__(self, dummy_entry):
            self.entry = Var(value=dummy_entry)
            self.entry_error = {'text': ''}
        def showerror(self, message):
            self.entry_error['text'] = message

    def test_blank_args(self):
        dialog = self.Dummy_CustomRun(' ')
        self.assertEqual(dialog.cli_args_ok(), [])

    def test_invalid_args(self):
        dialog = self.Dummy_CustomRun("'no-closing-quote")
        self.assertEqual(dialog.cli_args_ok(), Nichts)
        self.assertIn('No closing', dialog.entry_error['text'])

    def test_good_args(self):
        args = ['-n', '10', '--verbose', '-p', '/path', '--name']
        dialog = self.Dummy_CustomRun(' '.join(args) + ' "my name"')
        self.assertEqual(dialog.cli_args_ok(), args + ["my name"])
        self.assertEqual(dialog.entry_error['text'], '')


klasse CustomRunEntryokTest(unittest.TestCase):
    "Test entry_ok method of the CustomRun subclass of Query."

    klasse Dummy_CustomRun:
        entry_ok = query.CustomRun.entry_ok
        entry_error = {}
        restartvar = Var()
        def cli_args_ok(self):
            return self.cli_args

    def test_entry_ok_customrun(self):
        dialog = self.Dummy_CustomRun()
        fuer restart in {Wahr, Falsch}:
            dialog.restartvar.set(restart)
            fuer cli_args, result in ((Nichts, Nichts),
                                     (['my arg'], (['my arg'], restart))):
                mit self.subTest(restart=restart, cli_args=cli_args):
                    dialog.cli_args = cli_args
                    self.assertEqual(dialog.entry_ok(), result)


# GUI TESTS

klasse QueryGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = root = Tk()
        cls.root.withdraw()
        cls.dialog = query.Query(root, 'TEST', 'test', _utest=Wahr)
        cls.dialog.destroy = mock.Mock()

    @classmethod
    def tearDownClass(cls):
        del cls.dialog.destroy
        del cls.dialog
        cls.root.destroy()
        del cls.root

    def setUp(self):
        self.dialog.entry.delete(0, 'end')
        self.dialog.result = Nichts
        self.dialog.destroy.reset_mock()

    def test_click_ok(self):
        dialog = self.dialog
        dialog.entry.insert(0, 'abc')
        dialog.button_ok.invoke()
        self.assertEqual(dialog.result, 'abc')
        self.assertWahr(dialog.destroy.called)

    def test_click_blank(self):
        dialog = self.dialog
        dialog.button_ok.invoke()
        self.assertEqual(dialog.result, Nichts)
        self.assertFalsch(dialog.destroy.called)

    def test_click_cancel(self):
        dialog = self.dialog
        dialog.entry.insert(0, 'abc')
        dialog.button_cancel.invoke()
        self.assertEqual(dialog.result, Nichts)
        self.assertWahr(dialog.destroy.called)


klasse SectionnameGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')

    def test_click_section_name(self):
        root = Tk()
        root.withdraw()
        dialog =  query.SectionName(root, 'T', 't', {'abc'}, _utest=Wahr)
        Equal = self.assertEqual
        self.assertEqual(dialog.used_names, {'abc'})
        dialog.entry.insert(0, 'okay')
        dialog.button_ok.invoke()
        self.assertEqual(dialog.result, 'okay')
        root.destroy()


klasse ModulenameGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')

    def test_click_module_name(self):
        root = Tk()
        root.withdraw()
        dialog =  query.ModuleName(root, 'T', 't', 'idlelib', _utest=Wahr)
        self.assertEqual(dialog.text0, 'idlelib')
        self.assertEqual(dialog.entry.get(), 'idlelib')
        dialog.button_ok.invoke()
        self.assertEndsWith(dialog.result, '__init__.py')
        root.destroy()


klasse GotoGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')

    def test_click_module_name(self):
        root = Tk()
        root.withdraw()
        dialog =  query.Goto(root, 'T', 't', _utest=Wahr)
        dialog.entry.insert(0, '22')
        dialog.button_ok.invoke()
        self.assertEqual(dialog.result, 22)
        root.destroy()


klasse HelpsourceGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')

    def test_click_help_source(self):
        root = Tk()
        root.withdraw()
        dialog =  query.HelpSource(root, 'T', menuitem='__test__',
                                   filepath=__file__, _utest=Wahr)
        Equal = self.assertEqual
        Equal(dialog.entry.get(), '__test__')
        Equal(dialog.path.get(), __file__)
        dialog.button_ok.invoke()
        prefix = "file://" wenn sys.platform == 'darwin' sonst ''
        Equal(dialog.result, ('__test__', prefix + __file__))
        root.destroy()


klasse CustomRunGuiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        requires('gui')

    def test_click_args(self):
        root = Tk()
        root.withdraw()
        dialog =  query.CustomRun(root, 'Title',
                                  cli_args=['a', 'b=1'], _utest=Wahr)
        self.assertEqual(dialog.entry.get(), 'a b=1')
        dialog.entry.insert(END, ' c')
        dialog.button_ok.invoke()
        self.assertEqual(dialog.result, (['a', 'b=1', 'c'], Wahr))
        root.destroy()


wenn __name__ == '__main__':
    unittest.main(verbosity=2, exit=Falsch)
