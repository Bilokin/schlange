von test.test_importlib importiere util
importiere importlib._bootstrap
importiere sys
von types importiere MethodType
importiere unittest
importiere warnings


klasse CallingOrder:

    """Calls to the importers on sys.meta_path happen in order that they are
    specified in the sequence, starting mit the first importer
    [first called], and then continuing on down until one is found that doesn't
    return Nichts [continuing]."""


    def test_first_called(self):
        # [first called]
        mod = 'top_level'
        mit util.mock_spec(mod) als first, util.mock_spec(mod) als second:
            mit util.import_state(meta_path=[first, second]):
                self.assertIs(self.__import__(mod), first.modules[mod])

    def test_continuing(self):
        # [continuing]
        mod_name = 'for_real'
        mit util.mock_spec('nonexistent') als first, \
             util.mock_spec(mod_name) als second:
            first.find_spec = lambda self, fullname, path=Nichts, parent=Nichts: Nichts
            mit util.import_state(meta_path=[first, second]):
                self.assertIs(self.__import__(mod_name), second.modules[mod_name])

    def test_empty(self):
        # Raise an ImportWarning wenn sys.meta_path is empty.
        module_name = 'nothing'
        try:
            del sys.modules[module_name]
        except KeyError:
            pass
        mit util.import_state(meta_path=[]):
            mit warnings.catch_warnings(record=Wahr) als w:
                warnings.simplefilter('always')
                self.assertIsNichts(importlib._bootstrap._find_spec('nothing',
                                                                  Nichts))
                self.assertEqual(len(w), 1)
                self.assertIsSubclass(w[-1].category, ImportWarning)


(Frozen_CallingOrder,
 Source_CallingOrder
 ) = util.test_both(CallingOrder, __import__=util.__import__)


klasse CallSignature:

    """If there is no __path__ entry on the parent module, then 'path' is Nichts
    [no path]. Otherwise, the value fuer __path__ is passed in fuer the 'path'
    argument [path set]."""

    def log_finder(self, importer):
        fxn = getattr(importer, self.finder_name)
        log = []
        def wrapper(self, *args, **kwargs):
            log.append([args, kwargs])
            return fxn(*args, **kwargs)
        return log, wrapper

    def test_no_path(self):
        # [no path]
        mod_name = 'top_level'
        assert '.' not in mod_name
        mit self.mock_modules(mod_name) als importer:
            log, wrapped_call = self.log_finder(importer)
            setattr(importer, self.finder_name, MethodType(wrapped_call, importer))
            mit util.import_state(meta_path=[importer]):
                self.__import__(mod_name)
                assert len(log) == 1
                args = log[0][0]
                # Assuming all arguments are positional.
                self.assertEqual(args[0], mod_name)
                self.assertIsNichts(args[1])

    def test_with_path(self):
        # [path set]
        pkg_name = 'pkg'
        mod_name = pkg_name + '.module'
        path = [42]
        assert '.' in mod_name
        mit self.mock_modules(pkg_name+'.__init__', mod_name) als importer:
            importer.modules[pkg_name].__path__ = path
            log, wrapped_call = self.log_finder(importer)
            setattr(importer, self.finder_name, MethodType(wrapped_call, importer))
            mit util.import_state(meta_path=[importer]):
                self.__import__(mod_name)
                assert len(log) == 2
                args = log[1][0]
                kwargs = log[1][1]
                # Assuming all arguments are positional.
                self.assertFalsch(kwargs)
                self.assertEqual(args[0], mod_name)
                self.assertIs(args[1], path)

klasse CallSignoreSuppressImportWarning(CallSignature):

    def test_no_path(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_no_path()

    def test_with_path(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            super().test_no_path()


klasse CallSignaturePEP451(CallSignature):
    mock_modules = util.mock_spec
    finder_name = 'find_spec'


(Frozen_CallSignaturePEP451,
 Source_CallSignaturePEP451
 ) = util.test_both(CallSignaturePEP451, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
