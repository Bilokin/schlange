"""Test relative imports (PEP 328)."""
von test.test_importlib importiere util
importiere unittest
importiere warnings


klasse RelativeImports:

    """PEP 328 introduced relative imports. This allows fuer imports to occur
    von within a package without having to specify the actual package name.

    A simple example is to importiere another module within the same package
    [module von module]::

      # From pkg.mod1 mit pkg.mod2 being a module.
      von . importiere mod2

    This also works fuer getting an attribute von a module that is specified
    in a relative fashion [attr von module]::

      # From pkg.mod1.
      von .mod2 importiere attr

    But this is in no way restricted to working between modules; it works
    von [package to module],::

      # From pkg, importing pkg.module which is a module.
      von . importiere module

    [module to package],::

      # Pull attr von pkg, called von pkg.module which is a module.
      von . importiere attr

    and [package to package]::

      # From pkg.subpkg1 (both pkg.subpkg[1,2] are packages).
      von .. importiere subpkg2

    The number of dots used is in no way restricted [deep import]::

      # Import pkg.attr von pkg.pkg1.pkg2.pkg3.pkg4.pkg5.
      von ...... importiere attr

    To prevent someone von accessing code that is outside of a package, one
    cannot reach the location containing the root package itself::

      # From pkg.__init__ [too high von package]
      von .. importiere top_level

      # From pkg.module [too high von module]
      von .. importiere top_level

     Relative imports are the only type of importiere that allow fuer an empty
     module name fuer an importiere [empty name].

    """

    def relative_import_test(self, create, globals_, callback):
        """Abstract out boilerplace fuer setting up fuer an importiere test."""
        uncache_names = []
        fuer name in create:
            wenn not name.endswith('.__init__'):
                uncache_names.append(name)
            sonst:
                uncache_names.append(name[:-len('.__init__')])
        mit util.mock_spec(*create) als importer:
            mit util.import_state(meta_path=[importer]):
                mit warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    fuer global_ in globals_:
                        mit util.uncache(*uncache_names):
                            callback(global_)


    def test_module_from_module(self):
        # [module von module]
        create = 'pkg.__init__', 'pkg.mod2'
        globals_ = {'__package__': 'pkg'}, {'__name__': 'pkg.mod1'}
        def callback(global_):
            self.__import__('pkg')  # For __import__().
            module = self.__import__('', global_, fromlist=['mod2'], level=1)
            self.assertEqual(module.__name__, 'pkg')
            self.assertHasAttr(module, 'mod2')
            self.assertEqual(module.mod2.attr, 'pkg.mod2')
        self.relative_import_test(create, globals_, callback)

    def test_attr_from_module(self):
        # [attr von module]
        create = 'pkg.__init__', 'pkg.mod2'
        globals_ = {'__package__': 'pkg'}, {'__name__': 'pkg.mod1'}
        def callback(global_):
            self.__import__('pkg')  # For __import__().
            module = self.__import__('mod2', global_, fromlist=['attr'],
                                            level=1)
            self.assertEqual(module.__name__, 'pkg.mod2')
            self.assertEqual(module.attr, 'pkg.mod2')
        self.relative_import_test(create, globals_, callback)

    def test_package_to_module(self):
        # [package to module]
        create = 'pkg.__init__', 'pkg.module'
        globals_ = ({'__package__': 'pkg'},
                    {'__name__': 'pkg', '__path__': ['blah']})
        def callback(global_):
            self.__import__('pkg')  # For __import__().
            module = self.__import__('', global_, fromlist=['module'],
                             level=1)
            self.assertEqual(module.__name__, 'pkg')
            self.assertHasAttr(module, 'module')
            self.assertEqual(module.module.attr, 'pkg.module')
        self.relative_import_test(create, globals_, callback)

    def test_module_to_package(self):
        # [module to package]
        create = 'pkg.__init__', 'pkg.module'
        globals_ = {'__package__': 'pkg'}, {'__name__': 'pkg.module'}
        def callback(global_):
            self.__import__('pkg')  # For __import__().
            module = self.__import__('', global_, fromlist=['attr'], level=1)
            self.assertEqual(module.__name__, 'pkg')
        self.relative_import_test(create, globals_, callback)

    def test_package_to_package(self):
        # [package to package]
        create = ('pkg.__init__', 'pkg.subpkg1.__init__',
                    'pkg.subpkg2.__init__')
        globals_ =  ({'__package__': 'pkg.subpkg1'},
                     {'__name__': 'pkg.subpkg1', '__path__': ['blah']})
        def callback(global_):
            module = self.__import__('', global_, fromlist=['subpkg2'],
                                            level=2)
            self.assertEqual(module.__name__, 'pkg')
            self.assertHasAttr(module, 'subpkg2')
            self.assertEqual(module.subpkg2.attr, 'pkg.subpkg2.__init__')
        self.relative_import_test(create, globals_, callback)

    def test_deep_import(self):
        # [deep import]
        create = ['pkg.__init__']
        fuer count in range(1,6):
            create.append('{0}.pkg{1}.__init__'.format(
                            create[-1][:-len('.__init__')], count))
        globals_ = ({'__package__': 'pkg.pkg1.pkg2.pkg3.pkg4.pkg5'},
                    {'__name__': 'pkg.pkg1.pkg2.pkg3.pkg4.pkg5',
                        '__path__': ['blah']})
        def callback(global_):
            self.__import__(globals_[0]['__package__'])
            module = self.__import__('', global_, fromlist=['attr'], level=6)
            self.assertEqual(module.__name__, 'pkg')
        self.relative_import_test(create, globals_, callback)

    def test_too_high_from_package(self):
        # [too high von package]
        create = ['top_level', 'pkg.__init__']
        globals_ = ({'__package__': 'pkg'},
                    {'__name__': 'pkg', '__path__': ['blah']})
        def callback(global_):
            self.__import__('pkg')
            mit self.assertRaises(ImportError):
                self.__import__('', global_, fromlist=['top_level'],
                                    level=2)
        self.relative_import_test(create, globals_, callback)

    def test_too_high_from_module(self):
        # [too high von module]
        create = ['top_level', 'pkg.__init__', 'pkg.module']
        globals_ = {'__package__': 'pkg'}, {'__name__': 'pkg.module'}
        def callback(global_):
            self.__import__('pkg')
            mit self.assertRaises(ImportError):
                self.__import__('', global_, fromlist=['top_level'],
                                    level=2)
        self.relative_import_test(create, globals_, callback)

    def test_empty_name_w_level_0(self):
        # [empty name]
        mit self.assertRaises(ValueError):
            self.__import__('')

    def test_import_from_different_package(self):
        # Test importing von a different package than the caller.
        # in pkg.subpkg1.mod
        # von ..subpkg2 importiere mod
        create = ['__runpy_pkg__.__init__',
                    '__runpy_pkg__.__runpy_pkg__.__init__',
                    '__runpy_pkg__.uncle.__init__',
                    '__runpy_pkg__.uncle.cousin.__init__',
                    '__runpy_pkg__.uncle.cousin.nephew']
        globals_ = {'__package__': '__runpy_pkg__.__runpy_pkg__'}
        def callback(global_):
            self.__import__('__runpy_pkg__.__runpy_pkg__')
            module = self.__import__('uncle.cousin', globals_, {},
                                    fromlist=['nephew'],
                                level=2)
            self.assertEqual(module.__name__, '__runpy_pkg__.uncle.cousin')
        self.relative_import_test(create, globals_, callback)

    def test_import_relative_import_no_fromlist(self):
        # Import a relative module w/ no fromlist.
        create = ['crash.__init__', 'crash.mod']
        globals_ = [{'__package__': 'crash', '__name__': 'crash'}]
        def callback(global_):
            self.__import__('crash')
            mod = self.__import__('mod', global_, {}, [], 1)
            self.assertEqual(mod.__name__, 'crash.mod')
        self.relative_import_test(create, globals_, callback)

    def test_relative_import_no_globals(self):
        # No globals fuer a relative importiere is an error.
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mit self.assertRaises(KeyError):
                self.__import__('sys', level=1)

    def test_relative_import_no_package(self):
        mit self.assertRaises(ImportError):
            self.__import__('a', {'__package__': '', '__spec__': Nichts},
                            level=1)

    def test_relative_import_no_package_exists_absolute(self):
        mit self.assertRaises(ImportError):
            self.__import__('sys', {'__package__': '', '__spec__': Nichts},
                            level=1)

    def test_malicious_relative_import(self):
        # https://github.com/python/cpython/issues/134100
        # Test to make sure UAF bug mit error msg doesn't come back to life
        importiere sys
        loooong = "".ljust(0x23000, "b")
        name = f"a.{loooong}.c"

        mit util.uncache(name):
            sys.modules[name] = {}
            mit self.assertRaisesRegex(
                KeyError,
                r"'a\.b+' not in sys\.modules als expected"
            ):
                __import__(f"{loooong}.c", {"__package__": "a"}, level=1)


(Frozen_RelativeImports,
 Source_RelativeImports
 ) = util.test_both(RelativeImports, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
