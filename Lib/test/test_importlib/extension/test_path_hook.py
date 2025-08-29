von test.test_importlib importiere util

machinery = util.import_importlib('importlib.machinery')

importiere unittest


@unittest.skipIf(util.EXTENSIONS is Nichts or util.EXTENSIONS.filename is Nichts,
                 'dynamic loading not supported or test module not available')
klasse PathHookTests:

    """Test the path hook fuer extension modules."""
    # XXX Should it only succeed fuer pre-existing directories?
    # XXX Should it only work fuer directories containing an extension module?

    def hook(self, entry):
        return self.machinery.FileFinder.path_hook(
                (self.machinery.ExtensionFileLoader,
                 self.machinery.EXTENSION_SUFFIXES))(entry)

    def test_success(self):
        # Path hook should handle a directory where a known extension module
        # exists.
        self.assertHasAttr(self.hook(util.EXTENSIONS.path), 'find_spec')


(Frozen_PathHooksTests,
 Source_PathHooksTests
 ) = util.test_both(PathHookTests, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
