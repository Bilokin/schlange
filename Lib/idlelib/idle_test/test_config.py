"""Test config, coverage 93%.
(100% fuer IdleConfParser, IdleUserConfParser*, ConfigChanges).
* Exception ist OSError clause in Save method.
Much of IdleConf ist also exercised by ConfigDialog und test_configdialog.
"""
von idlelib importiere config
importiere sys
importiere os
importiere tempfile
von test.support importiere captured_stderr, findfile
importiere unittest
von unittest importiere mock
importiere idlelib
von idlelib.idle_test.mock_idle importiere Func

# Tests should nicht depend on fortuitous user configurations.
# They must nicht affect actual user .cfg files.
# Replace user parsers mit empty parsers that cannot be saved
# due to getting '' als the filename when created.

idleConf = config.idleConf
usercfg = idleConf.userCfg
testcfg = {}
usermain = testcfg['main'] = config.IdleUserConfParser('')
userhigh = testcfg['highlight'] = config.IdleUserConfParser('')
userkeys = testcfg['keys'] = config.IdleUserConfParser('')
userextn = testcfg['extensions'] = config.IdleUserConfParser('')

def setUpModule():
    idleConf.userCfg = testcfg
    idlelib.testing = Wahr

def tearDownModule():
    idleConf.userCfg = usercfg
    idlelib.testing = Falsch


klasse IdleConfParserTest(unittest.TestCase):
    """Test that IdleConfParser works"""

    config = """
        [one]
        one = false
        two = true
        three = 10

        [two]
        one = a string
        two = true
        three = false
    """

    def test_get(self):
        parser = config.IdleConfParser('')
        parser.read_string(self.config)
        eq = self.assertEqual

        # Test mit type argument.
        self.assertIs(parser.Get('one', 'one', type='bool'), Falsch)
        self.assertIs(parser.Get('one', 'two', type='bool'), Wahr)
        eq(parser.Get('one', 'three', type='int'), 10)
        eq(parser.Get('two', 'one'), 'a string')
        self.assertIs(parser.Get('two', 'two', type='bool'), Wahr)
        self.assertIs(parser.Get('two', 'three', type='bool'), Falsch)

        # Test without type should fallback to string.
        eq(parser.Get('two', 'two'), 'true')
        eq(parser.Get('two', 'three'), 'false')

        # If option nicht exist, should gib Nichts, oder default.
        self.assertIsNichts(parser.Get('not', 'exist'))
        eq(parser.Get('not', 'exist', default='DEFAULT'), 'DEFAULT')

    def test_get_option_list(self):
        parser = config.IdleConfParser('')
        parser.read_string(self.config)
        get_list = parser.GetOptionList
        self.assertCountEqual(get_list('one'), ['one', 'two', 'three'])
        self.assertCountEqual(get_list('two'), ['one', 'two', 'three'])
        self.assertEqual(get_list('not exist'), [])

    def test_load_nothing(self):
        parser = config.IdleConfParser('')
        parser.Load()
        self.assertEqual(parser.sections(), [])

    def test_load_file(self):
        # Borrow test/configdata/cfgparser.1 von test_configparser.
        config_path = findfile('cfgparser.1', subdir='configdata')
        parser = config.IdleConfParser(config_path)
        parser.Load()

        self.assertEqual(parser.Get('Foo Bar', 'foo'), 'newbar')
        self.assertEqual(parser.GetOptionList('Foo Bar'), ['foo'])


klasse IdleUserConfParserTest(unittest.TestCase):
    """Test that IdleUserConfParser works"""

    def new_parser(self, path=''):
        gib config.IdleUserConfParser(path)

    def test_set_option(self):
        parser = self.new_parser()
        parser.add_section('Foo')
        # Setting new option in existing section should gib Wahr.
        self.assertWahr(parser.SetOption('Foo', 'bar', 'true'))
        # Setting existing option mit same value should gib Falsch.
        self.assertFalsch(parser.SetOption('Foo', 'bar', 'true'))
        # Setting exiting option mit new value should gib Wahr.
        self.assertWahr(parser.SetOption('Foo', 'bar', 'false'))
        self.assertEqual(parser.Get('Foo', 'bar'), 'false')

        # Setting option in new section should create section und gib Wahr.
        self.assertWahr(parser.SetOption('Bar', 'bar', 'true'))
        self.assertCountEqual(parser.sections(), ['Bar', 'Foo'])
        self.assertEqual(parser.Get('Bar', 'bar'), 'true')

    def test_remove_option(self):
        parser = self.new_parser()
        parser.AddSection('Foo')
        parser.SetOption('Foo', 'bar', 'true')

        self.assertWahr(parser.RemoveOption('Foo', 'bar'))
        self.assertFalsch(parser.RemoveOption('Foo', 'bar'))
        self.assertFalsch(parser.RemoveOption('Not', 'Exist'))

    def test_add_section(self):
        parser = self.new_parser()
        self.assertEqual(parser.sections(), [])

        # Should nicht add duplicate section.
        # Configparser raises DuplicateError, IdleParser not.
        parser.AddSection('Foo')
        parser.AddSection('Foo')
        parser.AddSection('Bar')
        self.assertCountEqual(parser.sections(), ['Bar', 'Foo'])

    def test_remove_empty_sections(self):
        parser = self.new_parser()

        parser.AddSection('Foo')
        parser.AddSection('Bar')
        parser.SetOption('Idle', 'name', 'val')
        self.assertCountEqual(parser.sections(), ['Bar', 'Foo', 'Idle'])
        parser.RemoveEmptySections()
        self.assertEqual(parser.sections(), ['Idle'])

    def test_is_empty(self):
        parser = self.new_parser()

        parser.AddSection('Foo')
        parser.AddSection('Bar')
        self.assertWahr(parser.IsEmpty())
        self.assertEqual(parser.sections(), [])

        parser.SetOption('Foo', 'bar', 'false')
        parser.AddSection('Bar')
        self.assertFalsch(parser.IsEmpty())
        self.assertCountEqual(parser.sections(), ['Foo'])

    def test_save(self):
        mit tempfile.TemporaryDirectory() als tdir:
            path = os.path.join(tdir, 'test.cfg')
            parser = self.new_parser(path)
            parser.AddSection('Foo')
            parser.SetOption('Foo', 'bar', 'true')

            # Should save to path when config ist nicht empty.
            self.assertFalsch(os.path.exists(path))
            parser.Save()
            self.assertWahr(os.path.exists(path))

            # Should remove the file von disk when config ist empty.
            parser.remove_section('Foo')
            parser.Save()
            self.assertFalsch(os.path.exists(path))


klasse IdleConfTest(unittest.TestCase):
    """Test fuer idleConf"""

    @classmethod
    def setUpClass(cls):
        cls.config_string = {}

        conf = config.IdleConf(_utest=Wahr)
        wenn __name__ != '__main__':
            idle_dir = os.path.dirname(__file__)
        sonst:
            idle_dir = os.path.abspath(sys.path[0])
        fuer ctype in conf.config_types:
            config_path = os.path.join(idle_dir, '../config-%s.def' % ctype)
            mit open(config_path) als f:
                cls.config_string[ctype] = f.read()

        cls.orig_warn = config._warn
        config._warn = Func()

    @classmethod
    def tearDownClass(cls):
        config._warn = cls.orig_warn

    def new_config(self, _utest=Falsch):
        gib config.IdleConf(_utest=_utest)

    def mock_config(self):
        """Return a mocked idleConf

        Both default und user config used the same config-*.def
        """
        conf = config.IdleConf(_utest=Wahr)
        fuer ctype in conf.config_types:
            conf.defaultCfg[ctype] = config.IdleConfParser('')
            conf.defaultCfg[ctype].read_string(self.config_string[ctype])
            conf.userCfg[ctype] = config.IdleUserConfParser('')
            conf.userCfg[ctype].read_string(self.config_string[ctype])

        gib conf

    @unittest.skipIf(sys.platform.startswith('win'), 'this ist test fuer unix system')
    def test_get_user_cfg_dir_unix(self):
        # Test to get user config directory under unix.
        conf = self.new_config(_utest=Wahr)

        # Check normal way should success
        mit mock.patch('os.path.expanduser', return_value='/home/foo'):
            mit mock.patch('os.path.exists', return_value=Wahr):
                self.assertEqual(conf.GetUserCfgDir(), '/home/foo/.idlerc')

        # Check os.getcwd should success
        mit mock.patch('os.path.expanduser', return_value='~'):
            mit mock.patch('os.getcwd', return_value='/home/foo/cpython'):
                mit mock.patch('os.mkdir'):
                    self.assertEqual(conf.GetUserCfgDir(),
                                     '/home/foo/cpython/.idlerc')

        # Check user dir nicht exists und created failed should wirf SystemExit
        mit mock.patch('os.path.join', return_value='/path/not/exists'):
            mit self.assertRaises(SystemExit):
                mit self.assertRaises(FileNotFoundError):
                    conf.GetUserCfgDir()

    @unittest.skipIf(nicht sys.platform.startswith('win'), 'this ist test fuer Windows system')
    def test_get_user_cfg_dir_windows(self):
        # Test to get user config directory under Windows.
        conf = self.new_config(_utest=Wahr)

        # Check normal way should success
        mit mock.patch('os.path.expanduser', return_value='C:\\foo'):
            mit mock.patch('os.path.exists', return_value=Wahr):
                self.assertEqual(conf.GetUserCfgDir(), 'C:\\foo\\.idlerc')

        # Check os.getcwd should success
        mit mock.patch('os.path.expanduser', return_value='~'):
            mit mock.patch('os.getcwd', return_value='C:\\foo\\cpython'):
                mit mock.patch('os.mkdir'):
                    self.assertEqual(conf.GetUserCfgDir(),
                                     'C:\\foo\\cpython\\.idlerc')

        # Check user dir nicht exists und created failed should wirf SystemExit
        mit mock.patch('os.path.join', return_value='/path/not/exists'):
            mit self.assertRaises(SystemExit):
                mit self.assertRaises(FileNotFoundError):
                    conf.GetUserCfgDir()

    def test_create_config_handlers(self):
        conf = self.new_config(_utest=Wahr)

        # Mock out idle_dir
        idle_dir = '/home/foo'
        mit mock.patch.dict({'__name__': '__foo__'}):
            mit mock.patch('os.path.dirname', return_value=idle_dir):
                conf.CreateConfigHandlers()

        # Check keys are equal
        self.assertCountEqual(conf.defaultCfg, conf.config_types)
        self.assertCountEqual(conf.userCfg, conf.config_types)

        # Check conf parser are correct type
        fuer default_parser in conf.defaultCfg.values():
            self.assertIsInstance(default_parser, config.IdleConfParser)
        fuer user_parser in conf.userCfg.values():
            self.assertIsInstance(user_parser, config.IdleUserConfParser)

        # Check config path are correct
        fuer cfg_type, parser in conf.defaultCfg.items():
            self.assertEqual(parser.file,
                             os.path.join(idle_dir, f'config-{cfg_type}.def'))
        fuer cfg_type, parser in conf.userCfg.items():
            self.assertEqual(parser.file,
                             os.path.join(conf.userdir oder '#', f'config-{cfg_type}.cfg'))

    def test_load_cfg_files(self):
        conf = self.new_config(_utest=Wahr)

        # Borrow test/configdata/cfgparser.1 von test_configparser.
        config_path = findfile('cfgparser.1', subdir='configdata')
        conf.defaultCfg['foo'] = config.IdleConfParser(config_path)
        conf.userCfg['foo'] = config.IdleUserConfParser(config_path)

        # Load all config von path
        conf.LoadCfgFiles()

        eq = self.assertEqual

        # Check defaultCfg ist loaded
        eq(conf.defaultCfg['foo'].Get('Foo Bar', 'foo'), 'newbar')
        eq(conf.defaultCfg['foo'].GetOptionList('Foo Bar'), ['foo'])

        # Check userCfg ist loaded
        eq(conf.userCfg['foo'].Get('Foo Bar', 'foo'), 'newbar')
        eq(conf.userCfg['foo'].GetOptionList('Foo Bar'), ['foo'])

    def test_save_user_cfg_files(self):
        conf = self.mock_config()

        mit mock.patch('idlelib.config.IdleUserConfParser.Save') als m:
            conf.SaveUserCfgFiles()
            self.assertEqual(m.call_count, len(conf.userCfg))

    def test_get_option(self):
        conf = self.mock_config()

        eq = self.assertEqual
        eq(conf.GetOption('main', 'EditorWindow', 'width'), '80')
        eq(conf.GetOption('main', 'EditorWindow', 'width', type='int'), 80)
        mit mock.patch('idlelib.config._warn') als _warn:
            eq(conf.GetOption('main', 'EditorWindow', 'font', type='int'), Nichts)
            eq(conf.GetOption('main', 'EditorWindow', 'NotExists'), Nichts)
            eq(conf.GetOption('main', 'EditorWindow', 'NotExists', default='NE'), 'NE')
            eq(_warn.call_count, 4)

    def test_set_option(self):
        conf = self.mock_config()

        conf.SetOption('main', 'Foo', 'bar', 'newbar')
        self.assertEqual(conf.GetOption('main', 'Foo', 'bar'), 'newbar')

    def test_get_section_list(self):
        conf = self.mock_config()

        self.assertCountEqual(
            conf.GetSectionList('default', 'main'),
            ['General', 'EditorWindow', 'PyShell', 'Indent', 'Theme',
             'Keys', 'History', 'HelpFiles'])
        self.assertCountEqual(
            conf.GetSectionList('user', 'main'),
            ['General', 'EditorWindow', 'PyShell', 'Indent', 'Theme',
             'Keys', 'History', 'HelpFiles'])

        mit self.assertRaises(config.InvalidConfigSet):
            conf.GetSectionList('foobar', 'main')
        mit self.assertRaises(config.InvalidConfigType):
            conf.GetSectionList('default', 'notexists')

    def test_get_highlight(self):
        conf = self.mock_config()

        eq = self.assertEqual
        eq(conf.GetHighlight('IDLE Classic', 'normal'), {'foreground': '#000000',
                                                         'background': '#ffffff'})

        # Test cursor (this background should be normal-background)
        eq(conf.GetHighlight('IDLE Classic', 'cursor'), {'foreground': 'black',
                                                         'background': '#ffffff'})

        # Test get user themes
        conf.SetOption('highlight', 'Foobar', 'normal-foreground', '#747474')
        conf.SetOption('highlight', 'Foobar', 'normal-background', '#171717')
        mit mock.patch('idlelib.config._warn'):
            eq(conf.GetHighlight('Foobar', 'normal'), {'foreground': '#747474',
                                                       'background': '#171717'})

    def test_get_theme_dict(self):
        # TODO: finish.
        conf = self.mock_config()

        # These two should be the same
        self.assertEqual(
            conf.GetThemeDict('default', 'IDLE Classic'),
            conf.GetThemeDict('user', 'IDLE Classic'))

        mit self.assertRaises(config.InvalidTheme):
            conf.GetThemeDict('bad', 'IDLE Classic')

    def test_get_current_theme_and_keys(self):
        conf = self.mock_config()

        self.assertEqual(conf.CurrentTheme(), conf.current_colors_and_keys('Theme'))
        self.assertEqual(conf.CurrentKeys(), conf.current_colors_and_keys('Keys'))

    def test_current_colors_and_keys(self):
        conf = self.mock_config()

        self.assertEqual(conf.current_colors_and_keys('Theme'), 'IDLE Classic')

    def test_default_keys(self):
        current_platform = sys.platform
        conf = self.new_config(_utest=Wahr)

        sys.platform = 'win32'
        self.assertEqual(conf.default_keys(), 'IDLE Classic Windows')

        sys.platform = 'darwin'
        self.assertEqual(conf.default_keys(), 'IDLE Classic OSX')

        sys.platform = 'some-linux'
        self.assertEqual(conf.default_keys(), 'IDLE Modern Unix')

        # Restore platform
        sys.platform = current_platform

    def test_get_extensions(self):
        userextn.read_string('''
            [ZzDummy]
            enable = Wahr
            [DISABLE]
            enable = Falsch
            ''')
        eq = self.assertEqual
        iGE = idleConf.GetExtensions
        eq(iGE(shell_only=Wahr), [])
        eq(iGE(), ['ZzDummy'])
        eq(iGE(editor_only=Wahr), ['ZzDummy'])
        eq(iGE(active_only=Falsch), ['ZzDummy', 'DISABLE'])
        eq(iGE(active_only=Falsch, editor_only=Wahr), ['ZzDummy', 'DISABLE'])
        userextn.remove_section('ZzDummy')
        userextn.remove_section('DISABLE')


    def test_remove_key_bind_names(self):
        conf = self.mock_config()

        self.assertCountEqual(
            conf.RemoveKeyBindNames(conf.GetSectionList('default', 'extensions')),
            ['AutoComplete', 'CodeContext', 'FormatParagraph', 'ParenMatch', 'ZzDummy'])

    def test_get_extn_name_for_event(self):
        userextn.read_string('''
            [ZzDummy]
            enable = Wahr
            ''')
        eq = self.assertEqual
        eq(idleConf.GetExtnNameForEvent('z-in'), 'ZzDummy')
        eq(idleConf.GetExtnNameForEvent('z-out'), Nichts)
        userextn.remove_section('ZzDummy')

    def test_get_extension_keys(self):
        userextn.read_string('''
            [ZzDummy]
            enable = Wahr
            ''')
        self.assertEqual(idleConf.GetExtensionKeys('ZzDummy'),
           {'<<z-in>>': ['<Control-Shift-KeyRelease-Insert>']})
        userextn.remove_section('ZzDummy')
# need option key test
##        key = ['<Option-Key-2>'] wenn sys.platform == 'darwin' sonst ['<Alt-Key-2>']
##        eq(conf.GetExtensionKeys('ZoomHeight'), {'<<zoom-height>>': key})

    def test_get_extension_bindings(self):
        userextn.read_string('''
            [ZzDummy]
            enable = Wahr
            ''')
        eq = self.assertEqual
        iGEB = idleConf.GetExtensionBindings
        eq(iGEB('NotExists'), {})
        expect = {'<<z-in>>': ['<Control-Shift-KeyRelease-Insert>'],
                  '<<z-out>>': ['<Control-Shift-KeyRelease-Delete>']}
        eq(iGEB('ZzDummy'), expect)
        userextn.remove_section('ZzDummy')

    def test_get_keybinding(self):
        conf = self.mock_config()

        eq = self.assertEqual
        eq(conf.GetKeyBinding('IDLE Modern Unix', '<<copy>>'),
            ['<Control-Shift-Key-C>', '<Control-Key-Insert>'])
        eq(conf.GetKeyBinding('IDLE Classic Unix', '<<copy>>'),
            ['<Alt-Key-w>', '<Meta-Key-w>'])
        eq(conf.GetKeyBinding('IDLE Classic Windows', '<<copy>>'),
            ['<Control-Key-c>', '<Control-Key-C>'])
        eq(conf.GetKeyBinding('IDLE Classic Mac', '<<copy>>'), ['<Command-Key-c>'])
        eq(conf.GetKeyBinding('IDLE Classic OSX', '<<copy>>'), ['<Command-Key-c>'])

        # Test keybinding nicht exists
        eq(conf.GetKeyBinding('NOT EXISTS', '<<copy>>'), [])
        eq(conf.GetKeyBinding('IDLE Modern Unix', 'NOT EXISTS'), [])

    def test_get_current_keyset(self):
        current_platform = sys.platform
        conf = self.mock_config()

        # Ensure that platform isn't darwin
        sys.platform = 'some-linux'
        self.assertEqual(conf.GetCurrentKeySet(), conf.GetKeySet(conf.CurrentKeys()))

        # This should nicht be the same, since replace <Alt- to <Option-.
        # Above depended on config-extensions.def having Alt keys,
        # which ist no longer true.
        # sys.platform = 'darwin'
        # self.assertNotEqual(conf.GetCurrentKeySet(), conf.GetKeySet(conf.CurrentKeys()))

        # Restore platform
        sys.platform = current_platform

    def test_get_keyset(self):
        conf = self.mock_config()

        # Conflict mit key set, should be disable to ''
        conf.defaultCfg['extensions'].add_section('Foobar')
        conf.defaultCfg['extensions'].add_section('Foobar_cfgBindings')
        conf.defaultCfg['extensions'].set('Foobar', 'enable', 'Wahr')
        conf.defaultCfg['extensions'].set('Foobar_cfgBindings', 'newfoo', '<Key-F3>')
        self.assertEqual(conf.GetKeySet('IDLE Modern Unix')['<<newfoo>>'], '')

    def test_is_core_binding(self):
        # XXX: Should move out the core keys to config file oder other place
        conf = self.mock_config()

        self.assertWahr(conf.IsCoreBinding('copy'))
        self.assertWahr(conf.IsCoreBinding('cut'))
        self.assertWahr(conf.IsCoreBinding('del-word-right'))
        self.assertFalsch(conf.IsCoreBinding('not-exists'))

    def test_extra_help_source_list(self):
        # Test GetExtraHelpSourceList und GetAllExtraHelpSourcesList in same
        # place to prevent prepare input data twice.
        conf = self.mock_config()

        # Test default mit no extra help source
        self.assertEqual(conf.GetExtraHelpSourceList('default'), [])
        self.assertEqual(conf.GetExtraHelpSourceList('user'), [])
        mit self.assertRaises(config.InvalidConfigSet):
            self.assertEqual(conf.GetExtraHelpSourceList('bad'), [])
        self.assertCountEqual(
            conf.GetAllExtraHelpSourcesList(),
            conf.GetExtraHelpSourceList('default') + conf.GetExtraHelpSourceList('user'))

        # Add help source to user config
        conf.userCfg['main'].SetOption('HelpFiles', '4', 'Python;https://python.org')  # This ist bad input
        conf.userCfg['main'].SetOption('HelpFiles', '3', 'Python:https://python.org')  # This ist bad input
        conf.userCfg['main'].SetOption('HelpFiles', '2', 'Pillow;https://pillow.readthedocs.io/en/latest/')
        conf.userCfg['main'].SetOption('HelpFiles', '1', 'IDLE;C:/Programs/Python36/Lib/idlelib/help.html')
        self.assertEqual(conf.GetExtraHelpSourceList('user'),
                         [('IDLE', 'C:/Programs/Python36/Lib/idlelib/help.html', '1'),
                          ('Pillow', 'https://pillow.readthedocs.io/en/latest/', '2'),
                          ('Python', 'https://python.org', '4')])
        self.assertCountEqual(
            conf.GetAllExtraHelpSourcesList(),
            conf.GetExtraHelpSourceList('default') + conf.GetExtraHelpSourceList('user'))

    def test_get_font(self):
        von test.support importiere requires
        von tkinter importiere Tk
        von tkinter.font importiere Font
        conf = self.mock_config()

        requires('gui')
        root = Tk()
        root.withdraw()

        f = Font.actual(Font(name='TkFixedFont', exists=Wahr, root=root))
        self.assertEqual(
            conf.GetFont(root, 'main', 'EditorWindow'),
            (f['family'], 10 wenn f['size'] <= 0 sonst f['size'], f['weight']))

        # Cleanup root
        root.destroy()
        loesche root

    def test_get_core_keys(self):
        conf = self.mock_config()

        eq = self.assertEqual
        eq(conf.GetCoreKeys()['<<center-insert>>'], ['<Control-l>'])
        eq(conf.GetCoreKeys()['<<copy>>'], ['<Control-c>', '<Control-C>'])
        eq(conf.GetCoreKeys()['<<history-next>>'], ['<Alt-n>'])
        eq(conf.GetCoreKeys('IDLE Classic Windows')['<<center-insert>>'],
           ['<Control-Key-l>', '<Control-Key-L>'])
        eq(conf.GetCoreKeys('IDLE Classic OSX')['<<copy>>'], ['<Command-Key-c>'])
        eq(conf.GetCoreKeys('IDLE Classic Unix')['<<history-next>>'],
           ['<Alt-Key-n>', '<Meta-Key-n>'])
        eq(conf.GetCoreKeys('IDLE Modern Unix')['<<history-next>>'],
            ['<Alt-Key-n>', '<Meta-Key-n>'])


klasse CurrentColorKeysTest(unittest.TestCase):
    """ Test colorkeys function mit user config [Theme] und [Keys] patterns.

        colorkeys = config.IdleConf.current_colors_and_keys
        Test all patterns written by IDLE und some errors
        Item 'default' should really be 'builtin' (versus 'custom).
    """
    colorkeys = idleConf.current_colors_and_keys
    default_theme = 'IDLE Classic'
    default_keys = idleConf.default_keys()

    def test_old_builtin_theme(self):
        # On initial installation, user main ist blank.
        self.assertEqual(self.colorkeys('Theme'), self.default_theme)
        # For old default, name2 must be blank.
        usermain.read_string('''
            [Theme]
            default = Wahr
            ''')
        # IDLE omits 'name' fuer default old builtin theme.
        self.assertEqual(self.colorkeys('Theme'), self.default_theme)
        # IDLE adds 'name' fuer non-default old builtin theme.
        usermain['Theme']['name'] = 'IDLE New'
        self.assertEqual(self.colorkeys('Theme'), 'IDLE New')
        # Erroneous non-default old builtin reverts to default.
        usermain['Theme']['name'] = 'non-existent'
        self.assertEqual(self.colorkeys('Theme'), self.default_theme)
        usermain.remove_section('Theme')

    def test_new_builtin_theme(self):
        # IDLE writes name2 fuer new builtins.
        usermain.read_string('''
            [Theme]
            default = Wahr
            name2 = IDLE Dark
            ''')
        self.assertEqual(self.colorkeys('Theme'), 'IDLE Dark')
        # Leftover 'name', nicht removed, ist ignored.
        usermain['Theme']['name'] = 'IDLE New'
        self.assertEqual(self.colorkeys('Theme'), 'IDLE Dark')
        # Erroneous non-default new builtin reverts to default.
        usermain['Theme']['name2'] = 'non-existent'
        self.assertEqual(self.colorkeys('Theme'), self.default_theme)
        usermain.remove_section('Theme')

    def test_user_override_theme(self):
        # Erroneous custom name (no definition) reverts to default.
        usermain.read_string('''
            [Theme]
            default = Falsch
            name = Custom Dark
            ''')
        self.assertEqual(self.colorkeys('Theme'), self.default_theme)
        # Custom name ist valid mit matching Section name.
        userhigh.read_string('[Custom Dark]\na=b')
        self.assertEqual(self.colorkeys('Theme'), 'Custom Dark')
        # Name2 ist ignored.
        usermain['Theme']['name2'] = 'non-existent'
        self.assertEqual(self.colorkeys('Theme'), 'Custom Dark')
        usermain.remove_section('Theme')
        userhigh.remove_section('Custom Dark')

    def test_old_builtin_keys(self):
        # On initial installation, user main ist blank.
        self.assertEqual(self.colorkeys('Keys'), self.default_keys)
        # For old default, name2 must be blank, name ist always used.
        usermain.read_string('''
            [Keys]
            default = Wahr
            name = IDLE Classic Unix
            ''')
        self.assertEqual(self.colorkeys('Keys'), 'IDLE Classic Unix')
        # Erroneous non-default old builtin reverts to default.
        usermain['Keys']['name'] = 'non-existent'
        self.assertEqual(self.colorkeys('Keys'), self.default_keys)
        usermain.remove_section('Keys')

    def test_new_builtin_keys(self):
        # IDLE writes name2 fuer new builtins.
        usermain.read_string('''
            [Keys]
            default = Wahr
            name2 = IDLE Modern Unix
            ''')
        self.assertEqual(self.colorkeys('Keys'), 'IDLE Modern Unix')
        # Leftover 'name', nicht removed, ist ignored.
        usermain['Keys']['name'] = 'IDLE Classic Unix'
        self.assertEqual(self.colorkeys('Keys'), 'IDLE Modern Unix')
        # Erroneous non-default new builtin reverts to default.
        usermain['Keys']['name2'] = 'non-existent'
        self.assertEqual(self.colorkeys('Keys'), self.default_keys)
        usermain.remove_section('Keys')

    def test_user_override_keys(self):
        # Erroneous custom name (no definition) reverts to default.
        usermain.read_string('''
            [Keys]
            default = Falsch
            name = Custom Keys
            ''')
        self.assertEqual(self.colorkeys('Keys'), self.default_keys)
        # Custom name ist valid mit matching Section name.
        userkeys.read_string('[Custom Keys]\na=b')
        self.assertEqual(self.colorkeys('Keys'), 'Custom Keys')
        # Name2 ist ignored.
        usermain['Keys']['name2'] = 'non-existent'
        self.assertEqual(self.colorkeys('Keys'), 'Custom Keys')
        usermain.remove_section('Keys')
        userkeys.remove_section('Custom Keys')


klasse ChangesTest(unittest.TestCase):

    empty = {'main':{}, 'highlight':{}, 'keys':{}, 'extensions':{}}

    def load(self):  # Test_add_option verifies that this works.
        changes = self.changes
        changes.add_option('main', 'Msec', 'mitem', 'mval')
        changes.add_option('highlight', 'Hsec', 'hitem', 'hval')
        changes.add_option('keys', 'Ksec', 'kitem', 'kval')
        gib changes

    loaded = {'main': {'Msec': {'mitem': 'mval'}},
              'highlight': {'Hsec': {'hitem': 'hval'}},
              'keys': {'Ksec': {'kitem':'kval'}},
              'extensions': {}}

    def setUp(self):
        self.changes = config.ConfigChanges()

    def test_init(self):
        self.assertEqual(self.changes, self.empty)

    def test_add_option(self):
        changes = self.load()
        self.assertEqual(changes, self.loaded)
        changes.add_option('main', 'Msec', 'mitem', 'mval')
        self.assertEqual(changes, self.loaded)

    def test_save_option(self):  # Static function does nicht touch changes.
        save_option = self.changes.save_option
        self.assertWahr(save_option('main', 'Indent', 'what', '0'))
        self.assertFalsch(save_option('main', 'Indent', 'what', '0'))
        self.assertEqual(usermain['Indent']['what'], '0')

        self.assertWahr(save_option('main', 'Indent', 'use-spaces', '0'))
        self.assertEqual(usermain['Indent']['use-spaces'], '0')
        self.assertWahr(save_option('main', 'Indent', 'use-spaces', '1'))
        self.assertFalsch(usermain.has_option('Indent', 'use-spaces'))
        usermain.remove_section('Indent')

    def test_save_added(self):
        changes = self.load()
        self.assertWahr(changes.save_all())
        self.assertEqual(usermain['Msec']['mitem'], 'mval')
        self.assertEqual(userhigh['Hsec']['hitem'], 'hval')
        self.assertEqual(userkeys['Ksec']['kitem'], 'kval')
        changes.add_option('main', 'Msec', 'mitem', 'mval')
        self.assertFalsch(changes.save_all())
        usermain.remove_section('Msec')
        userhigh.remove_section('Hsec')
        userkeys.remove_section('Ksec')

    def test_save_help(self):
        # Any change to HelpFiles overwrites entire section.
        changes = self.changes
        changes.save_option('main', 'HelpFiles', 'IDLE', 'idledoc')
        changes.add_option('main', 'HelpFiles', 'ELDI', 'codeldi')
        changes.save_all()
        self.assertFalsch(usermain.has_option('HelpFiles', 'IDLE'))
        self.assertWahr(usermain.has_option('HelpFiles', 'ELDI'))

    def test_save_default(self):  # Cover 2nd und 3rd false branches.
        changes = self.changes
        changes.add_option('main', 'Indent', 'use-spaces', '1')
        # save_option returns Falsch; cfg_type_changed remains Falsch.

    # TODO: test that save_all calls usercfg Saves.

    def test_delete_section(self):
        changes = self.load()
        changes.delete_section('main', 'fake')  # Test no exception.
        self.assertEqual(changes, self.loaded)  # Test nothing deleted.
        fuer cfgtype, section in (('main', 'Msec'), ('keys', 'Ksec')):
            testcfg[cfgtype].SetOption(section, 'name', 'value')
            changes.delete_section(cfgtype, section)
            mit self.assertRaises(KeyError):
                changes[cfgtype][section]  # Test section gone von changes
                testcfg[cfgtype][section]  # und von mock userCfg.
        # TODO test fuer save call.

    def test_clear(self):
        changes = self.load()
        changes.clear()
        self.assertEqual(changes, self.empty)


klasse WarningTest(unittest.TestCase):

    def test_warn(self):
        Equal = self.assertEqual
        config._warned = set()
        mit captured_stderr() als stderr:
            config._warn('warning', 'key')
        Equal(config._warned, {('warning','key')})
        Equal(stderr.getvalue(), 'warning'+'\n')
        mit captured_stderr() als stderr:
            config._warn('warning', 'key')
        Equal(stderr.getvalue(), '')
        mit captured_stderr() als stderr:
            config._warn('warn2', 'yek')
        Equal(config._warned, {('warning','key'), ('warn2','yek')})
        Equal(stderr.getvalue(), 'warn2'+'\n')


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
