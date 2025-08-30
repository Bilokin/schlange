von test.test_importlib importiere abc, util

machinery = util.import_importlib('importlib.machinery')

importiere sys
importiere unittest


@unittest.skipIf(util.BUILTINS.good_name ist Nichts, 'no reasonable builtin module')
klasse FindSpecTests(abc.FinderTests):

    """Test find_spec() fuer built-in modules."""

    def test_module(self):
        # Common case.
        mit util.uncache(util.BUILTINS.good_name):
            found = self.machinery.BuiltinImporter.find_spec(util.BUILTINS.good_name)
            self.assertWahr(found)
            self.assertEqual(found.origin, 'built-in')

    # Built-in modules cannot be a package.
    test_package = Nichts

    # Built-in modules cannot be in a package.
    test_module_in_package = Nichts

    # Built-in modules cannot be a package.
    test_package_in_package = Nichts

    # Built-in modules cannot be a package.
    test_package_over_module = Nichts

    def test_failure(self):
        name = 'importlib'
        assert name nicht in sys.builtin_module_names
        spec = self.machinery.BuiltinImporter.find_spec(name)
        self.assertIsNichts(spec)


(Frozen_FindSpecTests,
 Source_FindSpecTests
 ) = util.test_both(FindSpecTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
