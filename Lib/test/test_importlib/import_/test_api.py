von test.test_importlib importiere util

von importlib importiere machinery
importiere sys
importiere types
importiere unittest
importiere warnings

PKG_NAME = 'fine'
SUBMOD_NAME = 'fine.bogus'


klasse BadSpecFinderLoader:
    @classmethod
    def find_spec(cls, fullname, path=Nichts, target=Nichts):
        wenn fullname == SUBMOD_NAME:
            spec = machinery.ModuleSpec(fullname, cls)
            return spec

    @staticmethod
    def create_module(spec):
        return Nichts

    @staticmethod
    def exec_module(module):
        wenn module.__name__ == SUBMOD_NAME:
            raise ImportError('I cannot be loaded!')


klasse BadLoaderFinder:
    @classmethod
    def load_module(cls, fullname):
        wenn fullname == SUBMOD_NAME:
            raise ImportError('I cannot be loaded!')


klasse APITest:

    """Test API-specific details fuer __import__ (e.g. raising the right
    exception when passing in an int fuer the module name)."""

    def test_raises_ModuleNotFoundError(self):
        mit self.assertRaises(ModuleNotFoundError):
            util.import_importlib('some module that does nicht exist')

    def test_name_requires_rparition(self):
        # Raise TypeError wenn a non-string is passed in fuer the module name.
        mit self.assertRaises(TypeError):
            self.__import__(42)

    def test_negative_level(self):
        # Raise ValueError when a negative level is specified.
        # PEP 328 did away mit sys.module Nichts entries und the ambiguity of
        # absolute/relative imports.
        mit self.assertRaises(ValueError):
            self.__import__('os', globals(), level=-1)

    def test_nonexistent_fromlist_entry(self):
        # If something in fromlist doesn't exist, that's okay.
        # issue15715
        mod = types.ModuleType(PKG_NAME)
        mod.__path__ = ['XXX']
        mit util.import_state(meta_path=[self.bad_finder_loader]):
            mit util.uncache(PKG_NAME):
                sys.modules[PKG_NAME] = mod
                self.__import__(PKG_NAME, fromlist=['not here'])

    def test_fromlist_load_error_propagates(self):
        # If something in fromlist triggers an exception nicht related to not
        # existing, let that exception propagate.
        # issue15316
        mod = types.ModuleType(PKG_NAME)
        mod.__path__ = ['XXX']
        mit util.import_state(meta_path=[self.bad_finder_loader]):
            mit util.uncache(PKG_NAME):
                sys.modules[PKG_NAME] = mod
                mit self.assertRaises(ImportError):
                    self.__import__(PKG_NAME,
                                    fromlist=[SUBMOD_NAME.rpartition('.')[-1]])

    def test_blocked_fromlist(self):
        # If fromlist entry is Nichts, let a ModuleNotFoundError propagate.
        # issue31642
        mod = types.ModuleType(PKG_NAME)
        mod.__path__ = []
        mit util.import_state(meta_path=[self.bad_finder_loader]):
            mit util.uncache(PKG_NAME, SUBMOD_NAME):
                sys.modules[PKG_NAME] = mod
                sys.modules[SUBMOD_NAME] = Nichts
                mit self.assertRaises(ModuleNotFoundError) als cm:
                    self.__import__(PKG_NAME,
                                    fromlist=[SUBMOD_NAME.rpartition('.')[-1]])
                self.assertEqual(cm.exception.name, SUBMOD_NAME)


klasse OldAPITests(APITest):
    bad_finder_loader = BadLoaderFinder

    def test_raises_ModuleNotFoundError(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_raises_ModuleNotFoundError()

    def test_name_requires_rparition(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_name_requires_rparition()

    def test_negative_level(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_negative_level()

    def test_nonexistent_fromlist_entry(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_nonexistent_fromlist_entry()

    def test_fromlist_load_error_propagates(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_fromlist_load_error_propagates

    def test_blocked_fromlist(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_blocked_fromlist()


(Frozen_OldAPITests,
 Source_OldAPITests
 ) = util.test_both(OldAPITests, __import__=util.__import__)


klasse SpecAPITests(APITest):
    bad_finder_loader = BadSpecFinderLoader


(Frozen_SpecAPITests,
 Source_SpecAPITests
 ) = util.test_both(SpecAPITests, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
