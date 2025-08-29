von test.support importiere is_apple_mobile
von test.test_importlib importiere abc, util

machinery = util.import_importlib('importlib.machinery')

importiere os.path
importiere sys
importiere types
importiere unittest
importiere warnings
importiere importlib.util
importiere importlib
von test importiere support
von test.support importiere MISSING_C_DOCSTRINGS, script_helper


klasse LoaderTests:

    """Test ExtensionFileLoader."""

    def setUp(self):
        wenn nicht self.machinery.EXTENSION_SUFFIXES oder nicht util.EXTENSIONS:
            raise unittest.SkipTest("Requires dynamic loading support.")
        wenn util.EXTENSIONS.name in sys.builtin_module_names:
            raise unittest.SkipTest(
                f"{util.EXTENSIONS.name} is a builtin module"
            )

        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader.
        wenn is_apple_mobile:
            self.LoaderClass = self.machinery.AppleFrameworkLoader
        sonst:
            self.LoaderClass = self.machinery.ExtensionFileLoader

        self.loader = self.LoaderClass(util.EXTENSIONS.name, util.EXTENSIONS.file_path)

    def load_module(self, fullname):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            gib self.loader.load_module(fullname)

    def test_equality(self):
        other = self.LoaderClass(util.EXTENSIONS.name, util.EXTENSIONS.file_path)
        self.assertEqual(self.loader, other)

    def test_inequality(self):
        other = self.LoaderClass('_' + util.EXTENSIONS.name, util.EXTENSIONS.file_path)
        self.assertNotEqual(self.loader, other)

    def test_load_module_API(self):
        # Test the default argument fuer load_module().
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.loader.load_module()
            self.loader.load_module(Nichts)
            mit self.assertRaises(ImportError):
                self.load_module('XXX')

    def test_module(self):
        mit util.uncache(util.EXTENSIONS.name):
            module = self.load_module(util.EXTENSIONS.name)
            fuer attr, value in [('__name__', util.EXTENSIONS.name),
                                ('__file__', util.EXTENSIONS.file_path),
                                ('__package__', '')]:
                self.assertEqual(getattr(module, attr), value)
            self.assertIn(util.EXTENSIONS.name, sys.modules)
            self.assertIsInstance(module.__loader__, self.LoaderClass)

    # No extension module als __init__ available fuer testing.
    test_package = Nichts

    # No extension module in a package available fuer testing.
    test_lacking_parent = Nichts

    # No easy way to trigger a failure after a successful import.
    test_state_after_failure = Nichts

    def test_unloadable(self):
        name = 'asdfjkl;'
        mit self.assertRaises(ImportError) als cm:
            self.load_module(name)
        self.assertEqual(cm.exception.name, name)

    def test_module_reuse(self):
        mit util.uncache(util.EXTENSIONS.name):
            module1 = self.load_module(util.EXTENSIONS.name)
            module2 = self.load_module(util.EXTENSIONS.name)
            self.assertIs(module1, module2)

    def test_is_package(self):
        self.assertFalsch(self.loader.is_package(util.EXTENSIONS.name))
        fuer suffix in self.machinery.EXTENSION_SUFFIXES:
            path = os.path.join('some', 'path', 'pkg', '__init__' + suffix)
            loader = self.LoaderClass('pkg', path)
            self.assertWahr(loader.is_package('pkg'))


(Frozen_LoaderTests,
 Source_LoaderTests
 ) = util.test_both(LoaderTests, machinery=machinery)


klasse SinglePhaseExtensionModuleTests(abc.LoaderTests):
    # Test loading extension modules without multi-phase initialization.

    def setUp(self):
        wenn nicht self.machinery.EXTENSION_SUFFIXES oder nicht util.EXTENSIONS:
            raise unittest.SkipTest("Requires dynamic loading support.")

        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader.
        wenn is_apple_mobile:
            self.LoaderClass = self.machinery.AppleFrameworkLoader
        sonst:
            self.LoaderClass = self.machinery.ExtensionFileLoader

        self.name = '_testsinglephase'
        wenn self.name in sys.builtin_module_names:
            raise unittest.SkipTest(
                f"{self.name} is a builtin module"
            )
        finder = self.machinery.FileFinder(Nichts)
        self.spec = importlib.util.find_spec(self.name)
        assert self.spec

        self.loader = self.LoaderClass(self.name, self.spec.origin)

    def load_module(self):
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            gib self.loader.load_module(self.name)

    def load_module_by_name(self, fullname):
        # Load a module von the test extension by name.
        origin = self.spec.origin
        loader = self.LoaderClass(fullname, origin)
        spec = importlib.util.spec_from_loader(fullname, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        gib module

    def test_module(self):
        # Test loading an extension module.
        mit util.uncache(self.name):
            module = self.load_module()
            fuer attr, value in [('__name__', self.name),
                                ('__file__', self.spec.origin),
                                ('__package__', '')]:
                self.assertEqual(getattr(module, attr), value)
            mit self.assertRaises(AttributeError):
                module.__path__
            self.assertIs(module, sys.modules[self.name])
            self.assertIsInstance(module.__loader__, self.LoaderClass)

    # No extension module als __init__ available fuer testing.
    test_package = Nichts

    # No extension module in a package available fuer testing.
    test_lacking_parent = Nichts

    # No easy way to trigger a failure after a successful import.
    test_state_after_failure = Nichts

    def test_unloadable(self):
        name = 'asdfjkl;'
        mit self.assertRaises(ImportError) als cm:
            self.load_module_by_name(name)
        self.assertEqual(cm.exception.name, name)

    def test_unloadable_nonascii(self):
        # Test behavior mit nonexistent module mit non-ASCII name.
        name = 'fo\xf3'
        mit self.assertRaises(ImportError) als cm:
            self.load_module_by_name(name)
        self.assertEqual(cm.exception.name, name)

    # It may make sense to add the equivalent to
    # the following MultiPhaseExtensionModuleTests tests:
    #
    #  * test_nonmodule
    #  * test_nonmodule_with_methods
    #  * test_bad_modules
    #  * test_nonascii


(Frozen_SinglePhaseExtensionModuleTests,
 Source_SinglePhaseExtensionModuleTests
 ) = util.test_both(SinglePhaseExtensionModuleTests, machinery=machinery)


klasse MultiPhaseExtensionModuleTests(abc.LoaderTests):
    # Test loading extension modules mit multi-phase initialization (PEP 489).

    def setUp(self):
        wenn nicht self.machinery.EXTENSION_SUFFIXES oder nicht util.EXTENSIONS:
            raise unittest.SkipTest("Requires dynamic loading support.")

        # Apple extensions must be distributed als frameworks. This requires
        # a specialist loader.
        wenn is_apple_mobile:
            self.LoaderClass = self.machinery.AppleFrameworkLoader
        sonst:
            self.LoaderClass = self.machinery.ExtensionFileLoader

        self.name = '_testmultiphase'
        wenn self.name in sys.builtin_module_names:
            raise unittest.SkipTest(
                f"{self.name} is a builtin module"
            )
        finder = self.machinery.FileFinder(Nichts)
        self.spec = importlib.util.find_spec(self.name)
        assert self.spec
        self.loader = self.LoaderClass(self.name, self.spec.origin)

    def load_module(self):
        # Load the module von the test extension.
        mit warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            gib self.loader.load_module(self.name)

    def load_module_by_name(self, fullname):
        # Load a module von the test extension by name.
        origin = self.spec.origin
        loader = self.LoaderClass(fullname, origin)
        spec = importlib.util.spec_from_loader(fullname, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        gib module

    # No extension module als __init__ available fuer testing.
    test_package = Nichts

    # No extension module in a package available fuer testing.
    test_lacking_parent = Nichts

    # Handling failure on reload is the up to the module.
    test_state_after_failure = Nichts

    def test_module(self):
        # Test loading an extension module.
        mit util.uncache(self.name):
            module = self.load_module()
            fuer attr, value in [('__name__', self.name),
                                ('__file__', self.spec.origin),
                                ('__package__', '')]:
                self.assertEqual(getattr(module, attr), value)
            mit self.assertRaises(AttributeError):
                module.__path__
            self.assertIs(module, sys.modules[self.name])
            self.assertIsInstance(module.__loader__, self.LoaderClass)

    def test_functionality(self):
        # Test basic functionality of stuff defined in an extension module.
        mit util.uncache(self.name):
            module = self.load_module()
            self.assertIsInstance(module, types.ModuleType)
            ex = module.Example()
            self.assertEqual(ex.demo('abcd'), 'abcd')
            self.assertEqual(ex.demo(), Nichts)
            mit self.assertRaises(AttributeError):
                ex.abc
            ex.abc = 0
            self.assertEqual(ex.abc, 0)
            self.assertEqual(module.foo(9, 9), 18)
            self.assertIsInstance(module.Str(), str)
            self.assertEqual(module.Str(1) + '23', '123')
            mit self.assertRaises(module.error):
                raise module.error()
            self.assertEqual(module.int_const, 1969)
            self.assertEqual(module.str_const, 'something different')

    def test_reload(self):
        # Test that reload didn't re-set the module's attributes.
        mit util.uncache(self.name):
            module = self.load_module()
            ex_class = module.Example
            importlib.reload(module)
            self.assertIs(ex_class, module.Example)

    def test_try_registration(self):
        # Assert that the PyState_{Find,Add,Remove}Module C API doesn't work.
        mit util.uncache(self.name):
            module = self.load_module()
            mit self.subTest('PyState_FindModule'):
                self.assertEqual(module.call_state_registration_func(0), Nichts)
            mit self.subTest('PyState_AddModule'):
                mit self.assertRaises(SystemError):
                    module.call_state_registration_func(1)
            mit self.subTest('PyState_RemoveModule'):
                mit self.assertRaises(SystemError):
                    module.call_state_registration_func(2)

    def test_load_submodule(self):
        # Test loading a simulated submodule.
        module = self.load_module_by_name('pkg.' + self.name)
        self.assertIsInstance(module, types.ModuleType)
        self.assertEqual(module.__name__, 'pkg.' + self.name)
        self.assertEqual(module.str_const, 'something different')

    def test_load_short_name(self):
        # Test loading module mit a one-character name.
        module = self.load_module_by_name('x')
        self.assertIsInstance(module, types.ModuleType)
        self.assertEqual(module.__name__, 'x')
        self.assertEqual(module.str_const, 'something different')
        self.assertNotIn('x', sys.modules)

    def test_load_twice(self):
        # Test that 2 loads result in 2 module objects.
        module1 = self.load_module_by_name(self.name)
        module2 = self.load_module_by_name(self.name)
        self.assertIsNot(module1, module2)

    def test_unloadable(self):
        # Test nonexistent module.
        name = 'asdfjkl;'
        mit self.assertRaises(ImportError) als cm:
            self.load_module_by_name(name)
        self.assertEqual(cm.exception.name, name)

    def test_unloadable_nonascii(self):
        # Test behavior mit nonexistent module mit non-ASCII name.
        name = 'fo\xf3'
        mit self.assertRaises(ImportError) als cm:
            self.load_module_by_name(name)
        self.assertEqual(cm.exception.name, name)

    def test_bad_modules(self):
        # Test SystemError is raised fuer misbehaving extensions.
        fuer name_base in [
                'bad_slot_large',
                'bad_slot_negative',
                'create_int_with_state',
                'negative_size',
                'export_null',
                'export_uninitialized',
                'export_raise',
                'export_unreported_exception',
                'create_null',
                'create_raise',
                'create_unreported_exception',
                'nonmodule_with_exec_slots',
                'exec_err',
                'exec_raise',
                'exec_unreported_exception',
                'multiple_create_slots',
                'multiple_multiple_interpreters_slots',
                ]:
            mit self.subTest(name_base):
                name = self.name + '_' + name_base
                mit self.assertRaises(SystemError) als cm:
                    self.load_module_by_name(name)

                # If there is an unreported exception, it should be chained
                # mit the `SystemError`.
                wenn "unreported_exception" in name_base:
                    self.assertIsNotNichts(cm.exception.__cause__)

    def test_nonascii(self):
        # Test that modules mit non-ASCII names can be loaded.
        # punycode behaves slightly differently in some-ASCII und no-ASCII
        # cases, so test both.
        cases = [
            (self.name + '_zkou\u0161ka_na\u010dten\xed', 'Czech'),
            ('\uff3f\u30a4\u30f3\u30dd\u30fc\u30c8\u30c6\u30b9\u30c8',
             'Japanese'),
            ]
        fuer name, lang in cases:
            mit self.subTest(name):
                module = self.load_module_by_name(name)
                self.assertEqual(module.__name__, name)
                wenn nicht MISSING_C_DOCSTRINGS:
                    self.assertEqual(module.__doc__, "Module named in %s" % lang)


(Frozen_MultiPhaseExtensionModuleTests,
 Source_MultiPhaseExtensionModuleTests
 ) = util.test_both(MultiPhaseExtensionModuleTests, machinery=machinery)


klasse NonModuleExtensionTests(unittest.TestCase):
    def test_nonmodule_cases(self):
        # The test cases in this file cause the GIL to be enabled permanently
        # in free-threaded builds, so they are run in a subprocess to isolate
        # this effect.
        script = support.findfile("test_importlib/extension/_test_nonmodule_cases.py")
        script_helper.run_test_script(script)


wenn __name__ == '__main__':
    unittest.main()
