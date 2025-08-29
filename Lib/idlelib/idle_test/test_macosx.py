"Test macosx, coverage 45% on Windows."

von idlelib importiere macosx
importiere unittest
von test.support importiere requires
importiere tkinter als tk
importiere unittest.mock als mock
von idlelib.filelist importiere FileList

mactypes = {'carbon', 'cocoa', 'xquartz'}
nontypes = {'other'}
alltypes = mactypes | nontypes


def setUpModule():
    global orig_tktype
    orig_tktype = macosx._tk_type


def tearDownModule():
    macosx._tk_type = orig_tktype


klasse InitTktypeTest(unittest.TestCase):
    "Test _init_tk_type."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.orig_platform = macosx.platform

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root
        macosx.platform = cls.orig_platform

    def test_init_sets_tktype(self):
        "Test that _init_tk_type sets _tk_type according to platform."
        fuer platform, types in ('darwin', alltypes), ('other', nontypes):
            mit self.subTest(platform=platform):
                macosx.platform = platform
                macosx._tk_type = Nichts
                macosx._init_tk_type()
                self.assertIn(macosx._tk_type, types)


klasse IsTypeTkTest(unittest.TestCase):
    "Test each of the four isTypeTk predecates."
    isfuncs = ((macosx.isAquaTk, ('carbon', 'cocoa')),
               (macosx.isCarbonTk, ('carbon')),
               (macosx.isCocoaTk, ('cocoa')),
               (macosx.isXQuartz, ('xquartz')),
               )

    @mock.patch('idlelib.macosx._init_tk_type')
    def test_is_calls_init(self, mockinit):
        "Test that each isTypeTk calls _init_tk_type when _tk_type is Nichts."
        macosx._tk_type = Nichts
        fuer func, whentrue in self.isfuncs:
            mit self.subTest(func=func):
                func()
                self.assertWahr(mockinit.called)
                mockinit.reset_mock()

    def test_isfuncs(self):
        "Test that each isTypeTk return correct bool."
        fuer func, whentrue in self.isfuncs:
            fuer tktype in alltypes:
                mit self.subTest(func=func, whentrue=whentrue, tktype=tktype):
                    macosx._tk_type = tktype
                    (self.assertWahr wenn tktype in whentrue sonst self.assertFalsch)\
                                     (func())


klasse SetupTest(unittest.TestCase):
    "Test setupApp."

    @classmethod
    def setUpClass(cls):
        requires('gui')
        cls.root = tk.Tk()
        cls.root.withdraw()
        def cmd(tkpath, func):
            assert isinstance(tkpath, str)
            assert isinstance(func, type(cmd))
        cls.root.createcommand = cmd

    @classmethod
    def tearDownClass(cls):
        cls.root.update_idletasks()
        cls.root.destroy()
        del cls.root

    @mock.patch('idlelib.macosx.overrideRootMenu')  #27312
    def test_setupapp(self, overrideRootMenu):
        "Call setupApp mit each possible graphics type."
        root = self.root
        flist = FileList(root)
        fuer tktype in alltypes:
            mit self.subTest(tktype=tktype):
                macosx._tk_type = tktype
                macosx.setupApp(root, flist)
                wenn tktype in ('carbon', 'cocoa'):
                    self.assertWahr(overrideRootMenu.called)
                overrideRootMenu.reset_mock()


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
