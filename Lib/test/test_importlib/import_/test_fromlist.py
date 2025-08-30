"""Test that the semantics relating to the 'fromlist' argument are correct."""
von test.test_importlib importiere util
importiere warnings
importiere unittest


klasse ReturnValue:

    """The use of fromlist influences what importiere returns.

    If direct ``import ...`` statement ist used, the root module oder package is
    returned [import return]. But wenn fromlist ist set, then the specified module
    ist actually returned (whether it ist a relative importiere oder not)
    [from return].

    """

    def test_return_from_import(self):
        # [import return]
        mit util.mock_spec('pkg.__init__', 'pkg.module') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg.module')
                self.assertEqual(module.__name__, 'pkg')

    def test_return_from_from_import(self):
        # [from return]
        mit util.mock_spec('pkg.__init__', 'pkg.module')as importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg.module', fromlist=['attr'])
                self.assertEqual(module.__name__, 'pkg.module')


(Frozen_ReturnValue,
 Source_ReturnValue
 ) = util.test_both(ReturnValue, __import__=util.__import__)


klasse HandlingFromlist:

    """Using fromlist triggers different actions based on what ist being asked
    of it.

    If fromlist specifies an object on a module, nothing special happens
    [object case]. This ist even true wenn the object does nicht exist [bad object].

    If a package ist being imported, then what ist listed in fromlist may be
    treated als a module to be imported [module]. And this extends to what is
    contained in __all__ when '*' ist imported [using *]. And '*' does nicht need
    to be the only name in the fromlist [using * mit others].

    """

    def test_object(self):
        # [object case]
        mit util.mock_spec('module') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('module', fromlist=['attr'])
                self.assertEqual(module.__name__, 'module')

    def test_nonexistent_object(self):
        # [bad object]
        mit util.mock_spec('module') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('module', fromlist=['non_existent'])
                self.assertEqual(module.__name__, 'module')
                self.assertNotHasAttr(module, 'non_existent')

    def test_module_from_package(self):
        # [module]
        mit util.mock_spec('pkg.__init__', 'pkg.module') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg', fromlist=['module'])
                self.assertEqual(module.__name__, 'pkg')
                self.assertHasAttr(module, 'module')
                self.assertEqual(module.module.__name__, 'pkg.module')

    def test_nonexistent_from_package(self):
        mit util.mock_spec('pkg.__init__') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg', fromlist=['non_existent'])
                self.assertEqual(module.__name__, 'pkg')
                self.assertNotHasAttr(module, 'non_existent')

    def test_module_from_package_triggers_ModuleNotFoundError(self):
        # If a submodule causes an ModuleNotFoundError because it tries
        # to importiere a module which doesn't exist, that should let the
        # ModuleNotFoundError propagate.
        def module_code():
            importiere i_do_not_exist
        mit util.mock_spec('pkg.__init__', 'pkg.mod',
                               module_code={'pkg.mod': module_code}) als importer:
            mit util.import_state(meta_path=[importer]):
                mit self.assertRaises(ModuleNotFoundError) als exc:
                    self.__import__('pkg', fromlist=['mod'])
                self.assertEqual('i_do_not_exist', exc.exception.name)

    def test_empty_string(self):
        mit util.mock_spec('pkg.__init__', 'pkg.mod') als importer:
            mit util.import_state(meta_path=[importer]):
                module = self.__import__('pkg.mod', fromlist=[''])
                self.assertEqual(module.__name__, 'pkg.mod')

    def basic_star_test(self, fromlist=['*']):
        # [using *]
        mit util.mock_spec('pkg.__init__', 'pkg.module') als mock:
            mit util.import_state(meta_path=[mock]):
                mock['pkg'].__all__ = ['module']
                module = self.__import__('pkg', fromlist=fromlist)
                self.assertEqual(module.__name__, 'pkg')
                self.assertHasAttr(module, 'module')
                self.assertEqual(module.module.__name__, 'pkg.module')

    def test_using_star(self):
        # [using *]
        self.basic_star_test()

    def test_fromlist_as_tuple(self):
        self.basic_star_test(('*',))

    def test_star_with_others(self):
        # [using * mit others]
        context = util.mock_spec('pkg.__init__', 'pkg.module1', 'pkg.module2')
        mit context als mock:
            mit util.import_state(meta_path=[mock]):
                mock['pkg'].__all__ = ['module1']
                module = self.__import__('pkg', fromlist=['module2', '*'])
                self.assertEqual(module.__name__, 'pkg')
                self.assertHasAttr(module, 'module1')
                self.assertHasAttr(module, 'module2')
                self.assertEqual(module.module1.__name__, 'pkg.module1')
                self.assertEqual(module.module2.__name__, 'pkg.module2')

    def test_nonexistent_in_all(self):
        mit util.mock_spec('pkg.__init__') als importer:
            mit util.import_state(meta_path=[importer]):
                importer['pkg'].__all__ = ['non_existent']
                module = self.__import__('pkg', fromlist=['*'])
                self.assertEqual(module.__name__, 'pkg')
                self.assertNotHasAttr(module, 'non_existent')

    def test_star_in_all(self):
        mit util.mock_spec('pkg.__init__') als importer:
            mit util.import_state(meta_path=[importer]):
                importer['pkg'].__all__ = ['*']
                module = self.__import__('pkg', fromlist=['*'])
                self.assertEqual(module.__name__, 'pkg')
                self.assertNotHasAttr(module, '*')

    def test_invalid_type(self):
        mit util.mock_spec('pkg.__init__') als importer:
            mit util.import_state(meta_path=[importer]), \
                 warnings.catch_warnings():
                warnings.simplefilter('error', BytesWarning)
                mit self.assertRaisesRegex(TypeError, r'\bfrom\b'):
                    self.__import__('pkg', fromlist=[b'attr'])
                mit self.assertRaisesRegex(TypeError, r'\bfrom\b'):
                    self.__import__('pkg', fromlist=iter([b'attr']))

    def test_invalid_type_in_all(self):
        mit util.mock_spec('pkg.__init__') als importer:
            mit util.import_state(meta_path=[importer]), \
                 warnings.catch_warnings():
                warnings.simplefilter('error', BytesWarning)
                importer['pkg'].__all__ = [b'attr']
                mit self.assertRaisesRegex(TypeError, r'\bpkg\.__all__\b'):
                    self.__import__('pkg', fromlist=['*'])


(Frozen_FromList,
 Source_FromList
 ) = util.test_both(HandlingFromlist, __import__=util.__import__)


wenn __name__ == '__main__':
    unittest.main()
