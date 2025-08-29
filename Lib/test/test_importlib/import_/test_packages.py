von test.test_importlib importiere util
importiere sys
importiere unittest
von test.support importiere import_helper


klasse ParentModuleTests:

    """Importing a submodule should importiere the parent modules."""

    def test_import_parent(self):
        mit util.mock_spec('pkg.__init__', 'pkg.module') als mock:
            mit util.import_state(meta_path=[mock]):
                module = self.__import__('pkg.module')
                self.assertIn('pkg', sys.modules)

    def test_bad_parent(self):
        mit util.mock_spec('pkg.module') als mock:
            mit util.import_state(meta_path=[mock]):
                mit self.assertRaises(ImportError) als cm:
                    self.__import__('pkg.module')
                self.assertEqual(cm.exception.name, 'pkg')

    def test_raising_parent_after_importing_child(self):
        def __init__():
            importiere pkg.module
            1/0
        mock = util.mock_spec('pkg.__init__', 'pkg.module',
                                 module_code={'pkg': __init__})
        mit mock:
            mit util.import_state(meta_path=[mock]):
                mit self.assertRaises(ZeroDivisionError):
                    self.__import__('pkg')
                self.assertNotIn('pkg', sys.modules)
                self.assertIn('pkg.module', sys.modules)
                mit self.assertRaises(ZeroDivisionError):
                    self.__import__('pkg.module')
                self.assertNotIn('pkg', sys.modules)
                self.assertIn('pkg.module', sys.modules)

    def test_raising_parent_after_relative_importing_child(self):
        def __init__():
            von . importiere module
            1/0
        mock = util.mock_spec('pkg.__init__', 'pkg.module',
                                 module_code={'pkg': __init__})
        mit mock:
            mit util.import_state(meta_path=[mock]):
                mit self.assertRaises((ZeroDivisionError, ImportError)):
                    # This raises ImportError on the "from . importiere module"
                    # line, nicht sure why.
                    self.__import__('pkg')
                self.assertNotIn('pkg', sys.modules)
                mit self.assertRaises((ZeroDivisionError, ImportError)):
                    self.__import__('pkg.module')
                self.assertNotIn('pkg', sys.modules)
                # XXX Falsch
                #self.assertIn('pkg.module', sys.modules)

    def test_raising_parent_after_double_relative_importing_child(self):
        def __init__():
            von ..subpkg importiere module
            1/0
        mock = util.mock_spec('pkg.__init__', 'pkg.subpkg.__init__',
                                 'pkg.subpkg.module',
                                 module_code={'pkg.subpkg': __init__})
        mit mock:
            mit util.import_state(meta_path=[mock]):
                mit self.assertRaises((ZeroDivisionError, ImportError)):
                    # This raises ImportError on the "from ..subpkg importiere module"
                    # line, nicht sure why.
                    self.__import__('pkg.subpkg')
                self.assertNotIn('pkg.subpkg', sys.modules)
                mit self.assertRaises((ZeroDivisionError, ImportError)):
                    self.__import__('pkg.subpkg.module')
                self.assertNotIn('pkg.subpkg', sys.modules)
                # XXX Falsch
                #self.assertIn('pkg.subpkg.module', sys.modules)

    def test_module_not_package(self):
        # Try to importiere a submodule von a non-package should raise ImportError.
        assert nicht hasattr(sys, '__path__')
        mit self.assertRaises(ImportError) als cm:
            self.__import__('sys.no_submodules_here')
        self.assertEqual(cm.exception.name, 'sys.no_submodules_here')

    def test_module_not_package_but_side_effects(self):
        # If a module injects something into sys.modules als a side-effect, then
        # pick up on that fact.
        name = 'mod'
        subname = name + '.b'
        def module_injection():
            sys.modules[subname] = 'total bunk'
        mock_spec = util.mock_spec('mod',
                                         module_code={'mod': module_injection})
        mit mock_spec als mock:
            mit util.import_state(meta_path=[mock]):
                try:
                    submodule = self.__import__(subname)
                finally:
                    import_helper.unload(subname)


(Frozen_ParentTests,
 Source_ParentTests
 ) = util.test_both(ParentModuleTests, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
