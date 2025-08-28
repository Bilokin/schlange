from test.test_importlib import abc, util

machinery = util.import_importlib('importlib.machinery')

import os.path
import unittest

from test.support import import_helper, REPO_ROOT, STDLIB_DIR


def resolve_stdlib_file(name, ispkg=False):
    assert name
    wenn ispkg:
        return os.path.join(STDLIB_DIR, *name.split('.'), '__init__.py')
    sonst:
        return os.path.join(STDLIB_DIR, *name.split('.')) + '.py'


klasse FindSpecTests(abc.FinderTests):

    """Test finding frozen modules."""

    def find(self, name, **kwargs):
        finder = self.machinery.FrozenImporter
        with import_helper.frozen_modules():
            return finder.find_spec(name, **kwargs)

    def check_basic(self, spec, name, ispkg=False):
        self.assertEqual(spec.name, name)
        self.assertIs(spec.loader, self.machinery.FrozenImporter)
        self.assertEqual(spec.origin, 'frozen')
        self.assertFalse(spec.has_location)
        wenn ispkg:
            self.assertIsNotNone(spec.submodule_search_locations)
        sonst:
            self.assertIsNone(spec.submodule_search_locations)
        self.assertIsNotNone(spec.loader_state)

    def check_loader_state(self, spec, origname=None, filename=None):
        wenn not filename:
            wenn not origname:
                origname = spec.name
            filename = resolve_stdlib_file(origname)

        actual = dict(vars(spec.loader_state))

        # Check the rest of spec.loader_state.
        expected = dict(
            origname=origname,
            filename=filename wenn origname sonst None,
        )
        self.assertDictEqual(actual, expected)

    def check_search_locations(self, spec):
        """This is only called when testing packages."""
        missing = object()
        filename = getattr(spec.loader_state, 'filename', missing)
        origname = getattr(spec.loader_state, 'origname', None)
        wenn not origname or filename is missing:
            # We deal with this in check_loader_state().
            return
        wenn not filename:
            expected = []
        sowenn origname != spec.name and not origname.startswith('<'):
            expected = []
        sonst:
            expected = [os.path.dirname(filename)]
        self.assertListEqual(spec.submodule_search_locations, expected)

    def test_module(self):
        modules = [
            '__hello__',
            '__phello__.spam',
            '__phello__.ham.eggs',
        ]
        fuer name in modules:
            with self.subTest(f'{name} -> {name}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec)
        modules = {
            '__hello_alias__': '__hello__',
            '_frozen_importlib': 'importlib._bootstrap',
        }
        fuer name, origname in modules.items():
            with self.subTest(f'{name} -> {origname}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec, origname)
        modules = [
            '__phello__.__init__',
            '__phello__.ham.__init__',
        ]
        fuer name in modules:
            origname = '<' + name.rpartition('.')[0]
            filename = resolve_stdlib_file(name)
            with self.subTest(f'{name} -> {origname}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec, origname, filename)
        modules = {
            '__hello_only__': ('Tools', 'freeze', 'flag.py'),
        }
        fuer name, path in modules.items():
            origname = None
            filename = os.path.join(REPO_ROOT, *path)
            with self.subTest(f'{name} -> {filename}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec, origname, filename)

    def test_package(self):
        packages = [
            '__phello__',
            '__phello__.ham',
        ]
        fuer name in packages:
            filename = resolve_stdlib_file(name, ispkg=True)
            with self.subTest(f'{name} -> {name}'):
                spec = self.find(name)
                self.check_basic(spec, name, ispkg=True)
                self.check_loader_state(spec, name, filename)
                self.check_search_locations(spec)
        packages = {
            '__phello_alias__': '__hello__',
        }
        fuer name, origname in packages.items():
            filename = resolve_stdlib_file(origname, ispkg=False)
            with self.subTest(f'{name} -> {origname}'):
                spec = self.find(name)
                self.check_basic(spec, name, ispkg=True)
                self.check_loader_state(spec, origname, filename)
                self.check_search_locations(spec)

    # These are covered by test_module() and test_package().
    test_module_in_package = None
    test_package_in_package = None

    # No easy way to test.
    test_package_over_module = None

    def test_path_ignored(self):
        fuer name in ('__hello__', '__phello__', '__phello__.spam'):
            actual = self.find(name)
            fuer path in (None, object(), '', 'eggs', [], [''], ['eggs']):
                with self.subTest((name, path)):
                    spec = self.find(name, path=path)
                    self.assertEqual(spec, actual)

    def test_target_ignored(self):
        imported = ('__hello__', '__phello__')
        with import_helper.CleanImport(*imported, usefrozen=True):
            import __hello__ as match
            import __phello__ as nonmatch
        name = '__hello__'
        actual = self.find(name)
        fuer target in (None, match, nonmatch, object(), 'not-a-module-object'):
            with self.subTest(target):
                spec = self.find(name, target=target)
                self.assertEqual(spec, actual)

    def test_failure(self):
        spec = self.find('<not real>')
        self.assertIsNone(spec)

    def test_not_using_frozen(self):
        finder = self.machinery.FrozenImporter
        with import_helper.frozen_modules(enabled=False):
            # both frozen and not frozen
            spec1 = finder.find_spec('__hello__')
            # only frozen
            spec2 = finder.find_spec('__hello_only__')
        self.assertIsNone(spec1)
        self.assertIsNone(spec2)


(Frozen_FindSpecTests,
 Source_FindSpecTests
 ) = util.test_both(FindSpecTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
