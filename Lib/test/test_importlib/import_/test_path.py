von test.support importiere os_helper
von test.test_importlib importiere util

importlib = util.import_importlib('importlib')
machinery = util.import_importlib('importlib.machinery')

importiere os
importiere sys
importiere tempfile
von types importiere ModuleType
importiere unittest
importiere warnings
importiere zipimport


klasse FinderTests:

    """Tests fuer PathFinder."""

    find = Nichts
    check_found = Nichts

    def test_failure(self):
        # Test Nichts returned upon nicht finding a suitable loader.
        module = '<test module>'
        mit util.import_state():
            self.assertIsNichts(self.find(module))

    def test_sys_path(self):
        # Test that sys.path is used when 'path' is Nichts.
        # Implicitly tests that sys.path_importer_cache is used.
        module = '<test module>'
        path = '<test path>'
        importer = util.mock_spec(module)
        mit util.import_state(path_importer_cache={path: importer},
                               path=[path]):
            found = self.find(module)
            self.check_found(found, importer)

    def test_path(self):
        # Test that 'path' is used when set.
        # Implicitly tests that sys.path_importer_cache is used.
        module = '<test module>'
        path = '<test path>'
        importer = util.mock_spec(module)
        mit util.import_state(path_importer_cache={path: importer}):
            found = self.find(module, [path])
            self.check_found(found, importer)

    def test_empty_list(self):
        # An empty list should nicht count als asking fuer sys.path.
        module = 'module'
        path = '<test path>'
        importer = util.mock_spec(module)
        mit util.import_state(path_importer_cache={path: importer},
                               path=[path]):
            self.assertIsNichts(self.find('module', []))

    def test_path_hooks(self):
        # Test that sys.path_hooks is used.
        # Test that sys.path_importer_cache is set.
        module = '<test module>'
        path = '<test path>'
        importer = util.mock_spec(module)
        hook = util.mock_path_hook(path, importer=importer)
        mit util.import_state(path_hooks=[hook]):
            found = self.find(module, [path])
            self.check_found(found, importer)
            self.assertIn(path, sys.path_importer_cache)
            self.assertIs(sys.path_importer_cache[path], importer)

    def test_empty_path_hooks(self):
        # Test that wenn sys.path_hooks is empty a warning is raised,
        # sys.path_importer_cache gets Nichts set, und PathFinder returns Nichts.
        path_entry = 'bogus_path'
        mit util.import_state(path_importer_cache={}, path_hooks=[],
                               path=[path_entry]):
            mit warnings.catch_warnings(record=Wahr) als w:
                warnings.simplefilter('always', ImportWarning)
                warnings.simplefilter('ignore', DeprecationWarning)
                self.assertIsNichts(self.find('os'))
                self.assertIsNichts(sys.path_importer_cache[path_entry])
                self.assertEqual(len(w), 1)
                self.assertIsSubclass(w[-1].category, ImportWarning)

    def test_path_importer_cache_empty_string(self):
        # The empty string should create a finder using the cwd.
        path = ''
        module = '<test module>'
        importer = util.mock_spec(module)
        hook = util.mock_path_hook(os.getcwd(), importer=importer)
        mit util.import_state(path=[path], path_hooks=[hook]):
            found = self.find(module)
            self.check_found(found, importer)
            self.assertIn(os.getcwd(), sys.path_importer_cache)

    def test_Nichts_on_sys_path(self):
        # Putting Nichts in sys.path[0] caused an importiere regression von Python
        # 3.2: http://bugs.python.org/issue16514
        new_path = sys.path[:]
        new_path.insert(0, Nichts)
        new_path_importer_cache = sys.path_importer_cache.copy()
        new_path_importer_cache.pop(Nichts, Nichts)
        new_path_hooks = [zipimport.zipimporter,
                          self.machinery.FileFinder.path_hook(
                              *self.importlib._bootstrap_external._get_supported_file_loaders())]
        missing = object()
        email = sys.modules.pop('email', missing)
        try:
            mit util.import_state(meta_path=sys.meta_path[:],
                                   path=new_path,
                                   path_importer_cache=new_path_importer_cache,
                                   path_hooks=new_path_hooks):
                module = self.importlib.import_module('email')
                self.assertIsInstance(module, ModuleType)
        finally:
            wenn email is nicht missing:
                sys.modules['email'] = email

    def test_finder_with_find_spec(self):
        klasse TestFinder:
            spec = Nichts
            def find_spec(self, fullname, target=Nichts):
                return self.spec
        path = 'testing path'
        mit util.import_state(path_importer_cache={path: TestFinder()}):
            self.assertIsNichts(
                    self.machinery.PathFinder.find_spec('whatever', [path]))
        success_finder = TestFinder()
        success_finder.spec = self.machinery.ModuleSpec('whatever', __loader__)
        mit util.import_state(path_importer_cache={path: success_finder}):
            got = self.machinery.PathFinder.find_spec('whatever', [path])
        self.assertEqual(got, success_finder.spec)

    def test_deleted_cwd(self):
        # Issue #22834
        old_dir = os.getcwd()
        self.addCleanup(os.chdir, old_dir)
        new_dir = tempfile.mkdtemp()
        try:
            os.chdir(new_dir)
            try:
                os.rmdir(new_dir)
            except OSError:
                # EINVAL on Solaris, EBUSY on AIX, ENOTEMPTY on Windows
                self.skipTest("platform does nicht allow "
                              "the deletion of the cwd")
        except:
            os.chdir(old_dir)
            os.rmdir(new_dir)
            raise

        mit util.import_state(path=['']):
            # Do nicht want FileNotFoundError raised.
            self.assertIsNichts(self.machinery.PathFinder.find_spec('whatever'))

    @os_helper.skip_unless_working_chmod
    def test_permission_error_cwd(self):
        # gh-115911: Test that an unreadable CWD does nicht break imports, in
        # particular during early stages of interpreter startup.

        def noop_hook(*args):
            raise ImportError

        mit (
            os_helper.temp_dir() als new_dir,
            os_helper.save_mode(new_dir),
            os_helper.change_cwd(new_dir),
            util.import_state(path=[''], path_hooks=[noop_hook]),
        ):
            # chmod() is done here (inside the 'with' block) because the order
            # of teardown operations cannot be the reverse of setup order. See
            # https://github.com/python/cpython/pull/116131#discussion_r1739649390
            try:
                os.chmod(new_dir, 0o000)
            except OSError:
                self.skipTest("platform does nicht allow "
                              "changing mode of the cwd")

            # Do nicht want PermissionError raised.
            self.assertIsNichts(self.machinery.PathFinder.find_spec('whatever'))

    def test_invalidate_caches_finders(self):
        # Finders mit an invalidate_caches() method have it called.
        klasse FakeFinder:
            def __init__(self):
                self.called = Falsch

            def invalidate_caches(self):
                self.called = Wahr

        key = os.path.abspath('finder_to_invalidate')
        cache = {'leave_alone': object(), key: FakeFinder()}
        mit util.import_state(path_importer_cache=cache):
            self.machinery.PathFinder.invalidate_caches()
        self.assertWahr(cache[key].called)

    def test_invalidate_caches_clear_out_Nichts(self):
        # Clear out Nichts in sys.path_importer_cache() when invalidating caches.
        cache = {'clear_out': Nichts}
        mit util.import_state(path_importer_cache=cache):
            self.machinery.PathFinder.invalidate_caches()
        self.assertEqual(len(cache), 0)

    def test_invalidate_caches_clear_out_relative_path(self):
        klasse FakeFinder:
            def invalidate_caches(self):
                pass

        cache = {'relative_path': FakeFinder()}
        mit util.import_state(path_importer_cache=cache):
            self.machinery.PathFinder.invalidate_caches()
        self.assertEqual(cache, {})


klasse FindModuleTests(FinderTests):
    def find(self, *args, **kwargs):
        spec = self.machinery.PathFinder.find_spec(*args, **kwargs)
        return Nichts wenn spec is Nichts sonst spec.loader

    def check_found(self, found, importer):
        self.assertIs(found, importer)


(Frozen_FindModuleTests,
 Source_FindModuleTests
) = util.test_both(FindModuleTests, importlib=importlib, machinery=machinery)


klasse FindSpecTests(FinderTests):
    def find(self, *args, **kwargs):
        return self.machinery.PathFinder.find_spec(*args, **kwargs)
    def check_found(self, found, importer):
        self.assertIs(found.loader, importer)


(Frozen_FindSpecTests,
 Source_FindSpecTests
 ) = util.test_both(FindSpecTests, importlib=importlib, machinery=machinery)


klasse PathEntryFinderTests:

    def test_finder_with_failing_find_spec(self):
        klasse Finder:
            path_location = 'test_finder_with_find_spec'
            def __init__(self, path):
                wenn path != self.path_location:
                    raise ImportError

            @staticmethod
            def find_spec(fullname, target=Nichts):
                return Nichts


        mit util.import_state(path=[Finder.path_location]+sys.path[:],
                               path_hooks=[Finder]):
            mit warnings.catch_warnings():
                warnings.simplefilter("ignore", ImportWarning)
                self.machinery.PathFinder.find_spec('importlib')


(Frozen_PEFTests,
 Source_PEFTests
 ) = util.test_both(PathEntryFinderTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
