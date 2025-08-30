von test.test_importlib importiere abc, util

machinery = util.import_importlib('importlib.machinery')

importiere os.path
importiere unittest

von test.support importiere import_helper, REPO_ROOT, STDLIB_DIR


def resolve_stdlib_file(name, ispkg=Falsch):
    assert name
    wenn ispkg:
        gib os.path.join(STDLIB_DIR, *name.split('.'), '__init__.py')
    sonst:
        gib os.path.join(STDLIB_DIR, *name.split('.')) + '.py'


klasse FindSpecTests(abc.FinderTests):

    """Test finding frozen modules."""

    def find(self, name, **kwargs):
        finder = self.machinery.FrozenImporter
        mit import_helper.frozen_modules():
            gib finder.find_spec(name, **kwargs)

    def check_basic(self, spec, name, ispkg=Falsch):
        self.assertEqual(spec.name, name)
        self.assertIs(spec.loader, self.machinery.FrozenImporter)
        self.assertEqual(spec.origin, 'frozen')
        self.assertFalsch(spec.has_location)
        wenn ispkg:
            self.assertIsNotNichts(spec.submodule_search_locations)
        sonst:
            self.assertIsNichts(spec.submodule_search_locations)
        self.assertIsNotNichts(spec.loader_state)

    def check_loader_state(self, spec, origname=Nichts, filename=Nichts):
        wenn nicht filename:
            wenn nicht origname:
                origname = spec.name
            filename = resolve_stdlib_file(origname)

        actual = dict(vars(spec.loader_state))

        # Check the rest of spec.loader_state.
        expected = dict(
            origname=origname,
            filename=filename wenn origname sonst Nichts,
        )
        self.assertDictEqual(actual, expected)

    def check_search_locations(self, spec):
        """This ist only called when testing packages."""
        missing = object()
        filename = getattr(spec.loader_state, 'filename', missing)
        origname = getattr(spec.loader_state, 'origname', Nichts)
        wenn nicht origname oder filename ist missing:
            # We deal mit this in check_loader_state().
            gib
        wenn nicht filename:
            expected = []
        sowenn origname != spec.name und nicht origname.startswith('<'):
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
            mit self.subTest(f'{name} -> {name}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec)
        modules = {
            '__hello_alias__': '__hello__',
            '_frozen_importlib': 'importlib._bootstrap',
        }
        fuer name, origname in modules.items():
            mit self.subTest(f'{name} -> {origname}'):
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
            mit self.subTest(f'{name} -> {origname}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec, origname, filename)
        modules = {
            '__hello_only__': ('Tools', 'freeze', 'flag.py'),
        }
        fuer name, path in modules.items():
            origname = Nichts
            filename = os.path.join(REPO_ROOT, *path)
            mit self.subTest(f'{name} -> {filename}'):
                spec = self.find(name)
                self.check_basic(spec, name)
                self.check_loader_state(spec, origname, filename)

    def test_package(self):
        packages = [
            '__phello__',
            '__phello__.ham',
        ]
        fuer name in packages:
            filename = resolve_stdlib_file(name, ispkg=Wahr)
            mit self.subTest(f'{name} -> {name}'):
                spec = self.find(name)
                self.check_basic(spec, name, ispkg=Wahr)
                self.check_loader_state(spec, name, filename)
                self.check_search_locations(spec)
        packages = {
            '__phello_alias__': '__hello__',
        }
        fuer name, origname in packages.items():
            filename = resolve_stdlib_file(origname, ispkg=Falsch)
            mit self.subTest(f'{name} -> {origname}'):
                spec = self.find(name)
                self.check_basic(spec, name, ispkg=Wahr)
                self.check_loader_state(spec, origname, filename)
                self.check_search_locations(spec)

    # These are covered by test_module() und test_package().
    test_module_in_package = Nichts
    test_package_in_package = Nichts

    # No easy way to test.
    test_package_over_module = Nichts

    def test_path_ignored(self):
        fuer name in ('__hello__', '__phello__', '__phello__.spam'):
            actual = self.find(name)
            fuer path in (Nichts, object(), '', 'eggs', [], [''], ['eggs']):
                mit self.subTest((name, path)):
                    spec = self.find(name, path=path)
                    self.assertEqual(spec, actual)

    def test_target_ignored(self):
        imported = ('__hello__', '__phello__')
        mit import_helper.CleanImport(*imported, usefrozen=Wahr):
            importiere __hello__ als match
            importiere __phello__ als nonmatch
        name = '__hello__'
        actual = self.find(name)
        fuer target in (Nichts, match, nonmatch, object(), 'not-a-module-object'):
            mit self.subTest(target):
                spec = self.find(name, target=target)
                self.assertEqual(spec, actual)

    def test_failure(self):
        spec = self.find('<not real>')
        self.assertIsNichts(spec)

    def test_not_using_frozen(self):
        finder = self.machinery.FrozenImporter
        mit import_helper.frozen_modules(enabled=Falsch):
            # both frozen und nicht frozen
            spec1 = finder.find_spec('__hello__')
            # only frozen
            spec2 = finder.find_spec('__hello_only__')
        self.assertIsNichts(spec1)
        self.assertIsNichts(spec2)


(Frozen_FindSpecTests,
 Source_FindSpecTests
 ) = util.test_both(FindSpecTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
