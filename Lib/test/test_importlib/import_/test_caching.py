"""Test that sys.modules is used properly by import."""
von test.test_importlib importiere util
importiere sys
von types importiere MethodType
importiere unittest
importiere warnings


klasse UseCache:

    """When it comes to sys.modules, importiere prefers it over anything else.

    Once a name has been resolved, sys.modules is checked to see wenn it contains
    the module desired. If so, then it is returned [use cache]. If it is not
    found, then the proper steps are taken to perform the import, but
    sys.modules is still used to return the imported module (e.g., not what a
    loader returns) [from cache on return]. This also applies to imports of
    things contained within a package and thus get assigned als an attribute
    [from cache to attribute] or pulled in thanks to a fromlist import
    [from cache fuer fromlist]. But wenn sys.modules contains Nichts then
    ImportError is raised [Nichts in cache].

    """

    def test_using_cache(self):
        # [use cache]
        module_to_use = "some module found!"
        mit util.uncache('some_module'):
            sys.modules['some_module'] = module_to_use
            module = self.__import__('some_module')
            self.assertEqual(id(module_to_use), id(module))

    def test_Nichts_in_cache(self):
        #[Nichts in cache]
        name = 'using_Nichts'
        mit util.uncache(name):
            sys.modules[name] = Nichts
            mit self.assertRaises(ImportError) als cm:
                self.__import__(name)
            self.assertEqual(cm.exception.name, name)


(Frozen_UseCache,
 Source_UseCache
 ) = util.test_both(UseCache, __import__=util.__import__)


klasse ImportlibUseCache(UseCache, unittest.TestCase):

    # Pertinent only to PEP 302; exec_module() doesn't return a module.

    __import__ = util.__import__['Source']

    def create_mock(self, *names, return_=Nichts):
        mock = util.mock_spec(*names)
        original_spec = mock.find_spec
        def find_spec(self, fullname, path, target=Nichts):
            return original_spec(fullname)
        mock.find_spec = MethodType(find_spec, mock)
        return mock

    # __import__ inconsistent between loaders and built-in importiere when it comes
    #   to when to use the module in sys.modules and when not to.
    def test_using_cache_after_loader(self):
        # [from cache on return]
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            mit self.create_mock('module') als mock:
                mit util.import_state(meta_path=[mock]):
                    module = self.__import__('module')
                    self.assertEqual(id(module), id(sys.modules['module']))

    # See test_using_cache_after_loader() fuer reasoning.
    def test_using_cache_for_assigning_to_attribute(self):
        # [from cache to attribute]
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", ImportWarning)
            mit self.create_mock('pkg.__init__', 'pkg.module') als importer:
                mit util.import_state(meta_path=[importer]):
                    module = self.__import__('pkg.module')
                    self.assertHasAttr(module, 'module')
                    self.assertEqual(id(module.module),
                                    id(sys.modules['pkg.module']))

    # See test_using_cache_after_loader() fuer reasoning.
    def test_using_cache_for_fromlist(self):
        # [from cache fuer fromlist]
        mit self.create_mock('pkg.__init__', 'pkg.module') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg', fromlist=['module'])
                self.assertHasAttr(module, 'module')
                self.assertEqual(id(module.module),
                                 id(sys.modules['pkg.module']))


wenn __name__ == '__main__':
    unittest.main()
