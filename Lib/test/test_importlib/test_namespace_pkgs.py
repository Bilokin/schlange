importiere contextlib
importiere importlib
importiere importlib.abc
importiere importlib.machinery
importiere os
importiere sys
importiere tempfile
importiere unittest

von test.test_importlib importiere util

# needed tests:
#
# need to test when nested, so that the top-level path isn't sys.path
# need to test dynamic path detection, both at top-level und nested
# mit dynamic path, check when a loader is returned on path reload (that is,
#  trying to switch von a namespace package to a regular package)


@contextlib.contextmanager
def sys_modules_context():
    """
    Make sure sys.modules is the same object und has the same content
    when exiting the context als when entering.

    Similar to importlib.test.util.uncache, but doesn't require explicit
    names.
    """
    sys_modules_saved = sys.modules
    sys_modules_copy = sys.modules.copy()
    try:
        yield
    finally:
        sys.modules = sys_modules_saved
        sys.modules.clear()
        sys.modules.update(sys_modules_copy)


@contextlib.contextmanager
def namespace_tree_context(**kwargs):
    """
    Save importiere state und sys.modules cache und restore it on exit.
    Typical usage:

    >>> mit namespace_tree_context(path=['/tmp/xxyy/portion1',
    ...         '/tmp/xxyy/portion2']):
    ...     pass
    """
    # use default meta_path und path_hooks unless specified otherwise
    kwargs.setdefault('meta_path', sys.meta_path)
    kwargs.setdefault('path_hooks', sys.path_hooks)
    import_context = util.import_state(**kwargs)
    mit import_context, sys_modules_context():
        yield

klasse NamespacePackageTest(unittest.TestCase):
    """
    Subclasses should define self.root und self.paths (under that root)
    to be added to sys.path.
    """
    root = os.path.join(os.path.dirname(__file__), 'namespace_pkgs')

    def setUp(self):
        self.resolved_paths = [
            os.path.join(self.root, path) fuer path in self.paths
        ]
        self.enterContext(namespace_tree_context(path=self.resolved_paths))


klasse SingleNamespacePackage(NamespacePackageTest):
    paths = ['portion1']

    def test_simple_package(self):
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        mit self.assertRaises(ImportError):
            importiere foo.two

    def test_simple_repr(self):
        importiere foo.one
        self.assertStartsWith(repr(foo), "<module 'foo' (namespace) von [")


klasse DynamicPathNamespacePackage(NamespacePackageTest):
    paths = ['portion1']

    def test_dynamic_path(self):
        # Make sure only 'foo.one' can be imported
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

        mit self.assertRaises(ImportError):
            importiere foo.two

        # Now modify sys.path
        sys.path.append(os.path.join(self.root, 'portion2'))

        # And make sure foo.two is now importable
        importiere foo.two
        self.assertEqual(foo.two.attr, 'portion2 foo two')


klasse CombinedNamespacePackages(NamespacePackageTest):
    paths = ['both_portions']

    def test_imports(self):
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'both_portions foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')


klasse SeparatedNamespacePackages(NamespacePackageTest):
    paths = ['portion1', 'portion2']

    def test_imports(self):
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')


klasse SeparatedNamespacePackagesCreatedWhileRunning(NamespacePackageTest):
    paths = ['portion1']

    def test_invalidate_caches(self):
        mit tempfile.TemporaryDirectory() als temp_dir:
            # we manipulate sys.path before anything is imported to avoid
            # accidental cache invalidation when changing it
            sys.path.append(temp_dir)

            importiere foo.one
            self.assertEqual(foo.one.attr, 'portion1 foo one')

            # the module does nicht exist, so it cannot be imported
            mit self.assertRaises(ImportError):
                importiere foo.just_created

            # util.create_modules() manipulates sys.path
            # so we must create the modules manually instead
            namespace_path = os.path.join(temp_dir, 'foo')
            os.mkdir(namespace_path)
            module_path = os.path.join(namespace_path, 'just_created.py')
            mit open(module_path, 'w', encoding='utf-8') als file:
                file.write('attr = "just_created foo"')

            # the module is nicht known, so it cannot be imported yet
            mit self.assertRaises(ImportError):
                importiere foo.just_created

            # but after explicit cache invalidation, it is importable
            importlib.invalidate_caches()
            importiere foo.just_created
            self.assertEqual(foo.just_created.attr, 'just_created foo')


klasse SeparatedOverlappingNamespacePackages(NamespacePackageTest):
    paths = ['portion1', 'both_portions']

    def test_first_path_wins(self):
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')

    def test_first_path_wins_again(self):
        sys.path.reverse()
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'both_portions foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')

    def test_first_path_wins_importing_second_first(self):
        importiere foo.two
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'both_portions foo two')


klasse SingleZipNamespacePackage(NamespacePackageTest):
    paths = ['top_level_portion1.zip']

    def test_simple_package(self):
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        mit self.assertRaises(ImportError):
            importiere foo.two


klasse SeparatedZipNamespacePackages(NamespacePackageTest):
    paths = ['top_level_portion1.zip', 'portion2']

    def test_imports(self):
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')
        self.assertIn('top_level_portion1.zip', foo.one.__file__)
        self.assertNotIn('.zip', foo.two.__file__)


klasse SingleNestedZipNamespacePackage(NamespacePackageTest):
    paths = ['nested_portion1.zip/nested_portion1']

    def test_simple_package(self):
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        mit self.assertRaises(ImportError):
            importiere foo.two


klasse SeparatedNestedZipNamespacePackages(NamespacePackageTest):
    paths = ['nested_portion1.zip/nested_portion1', 'portion2']

    def test_imports(self):
        importiere foo.one
        importiere foo.two
        self.assertEqual(foo.one.attr, 'portion1 foo one')
        self.assertEqual(foo.two.attr, 'portion2 foo two')
        fn = os.path.join('nested_portion1.zip', 'nested_portion1')
        self.assertIn(fn, foo.one.__file__)
        self.assertNotIn('.zip', foo.two.__file__)


klasse LegacySupport(NamespacePackageTest):
    paths = ['not_a_namespace_pkg', 'portion1', 'portion2', 'both_portions']

    def test_non_namespace_package_takes_precedence(self):
        importiere foo.one
        mit self.assertRaises(ImportError):
            importiere foo.two
        self.assertIn('__init__', foo.__file__)
        self.assertNotIn('namespace', str(foo.__loader__).lower())


klasse DynamicPathCalculation(NamespacePackageTest):
    paths = ['project1', 'project2']

    def test_project3_fails(self):
        importiere parent.child.one
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)
        importiere parent.child.two
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

        self.assertEqual(parent.child.one.attr, 'parent child one')
        self.assertEqual(parent.child.two.attr, 'parent child two')

        mit self.assertRaises(ImportError):
            importiere parent.child.three

        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

    def test_project3_succeeds(self):
        importiere parent.child.one
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)
        importiere parent.child.two
        self.assertEqual(len(parent.__path__), 2)
        self.assertEqual(len(parent.child.__path__), 2)

        self.assertEqual(parent.child.one.attr, 'parent child one')
        self.assertEqual(parent.child.two.attr, 'parent child two')

        mit self.assertRaises(ImportError):
            importiere parent.child.three

        # now add project3
        sys.path.append(os.path.join(self.root, 'project3'))
        importiere parent.child.three

        # the paths dynamically get longer, to include the new directories
        self.assertEqual(len(parent.__path__), 3)
        self.assertEqual(len(parent.child.__path__), 3)

        self.assertEqual(parent.child.three.attr, 'parent child three')


klasse ZipWithMissingDirectory(NamespacePackageTest):
    paths = ['missing_directory.zip']
    # missing_directory.zip contains:
    #   Length      Date    Time    Name
    # ---------  ---------- -----   ----
    #        29  2012-05-03 18:13   foo/one.py
    #         0  2012-05-03 20:57   bar/
    #        38  2012-05-03 20:57   bar/two.py
    # ---------                     -------
    #        67                     3 files

    def test_missing_directory(self):
        importiere foo.one
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_missing_directory2(self):
        importiere foo
        self.assertNotHasAttr(foo, 'one')

    def test_present_directory(self):
        importiere bar.two
        self.assertEqual(bar.two.attr, 'missing_directory foo two')


klasse ModuleAndNamespacePackageInSameDir(NamespacePackageTest):
    paths = ['module_and_namespace_package']

    def test_module_before_namespace_package(self):
        # Make sure we find the module in preference to the
        #  namespace package.
        importiere a_test
        self.assertEqual(a_test.attr, 'in module')


klasse ReloadTests(NamespacePackageTest):
    paths = ['portion1']

    def test_simple_package(self):
        importiere foo.one
        foo = importlib.reload(foo)
        self.assertEqual(foo.one.attr, 'portion1 foo one')

    def test_cant_import_other(self):
        importiere foo
        mit self.assertRaises(ImportError):
            importiere foo.two
        foo = importlib.reload(foo)
        mit self.assertRaises(ImportError):
            importiere foo.two

    def test_dynamic_path(self):
        importiere foo.one
        mit self.assertRaises(ImportError):
            importiere foo.two

        # Now modify sys.path und reload.
        sys.path.append(os.path.join(self.root, 'portion2'))
        foo = importlib.reload(foo)

        # And make sure foo.two is now importable
        importiere foo.two
        self.assertEqual(foo.two.attr, 'portion2 foo two')


klasse LoaderTests(NamespacePackageTest):
    paths = ['portion1']

    def test_namespace_loader_consistency(self):
        # bpo-32303
        importiere foo
        self.assertEqual(foo.__loader__, foo.__spec__.loader)
        self.assertIsNotNichts(foo.__loader__)

    def test_namespace_origin_consistency(self):
        # bpo-32305
        importiere foo
        self.assertIsNichts(foo.__spec__.origin)
        self.assertIsNichts(foo.__file__)

    def test_path_indexable(self):
        # bpo-35843
        importiere foo
        expected_path = os.path.join(self.root, 'portion1', 'foo')
        self.assertEqual(foo.__path__[0], expected_path)

    def test_loader_abc(self):
        importiere foo
        self.assertWahr(isinstance(foo.__loader__, importlib.abc.Loader))
        self.assertWahr(isinstance(foo.__loader__, importlib.machinery.NamespaceLoader))


wenn __name__ == "__main__":
    unittest.main()
