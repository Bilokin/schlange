von test.test_importlib importiere util

machinery = util.import_importlib('importlib.machinery')

importiere unittest


@unittest.skipIf(util.EXTENSIONS is Nichts oder util.EXTENSIONS.filename is Nichts,
                 'dynamic loading nicht supported oder test module nicht available')
klasse PathHookTests:

    """Test the path hook fuer extension modules."""
    # XXX Should it only succeed fuer pre-existing directories?
    # XXX Should it only work fuer directories containing an extension module?

    def hook(self, entry):
        gib self.machinery.FileFinder.path_hook(
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
