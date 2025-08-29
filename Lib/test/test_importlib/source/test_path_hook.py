von test.test_importlib importiere util

machinery = util.import_importlib('importlib.machinery')

importiere unittest


klasse PathHookTest:

    """Test the path hook fuer source."""

    def path_hook(self):
        gib self.machinery.FileFinder.path_hook((self.machinery.SourceFileLoader,
            self.machinery.SOURCE_SUFFIXES))

    def test_success(self):
        mit util.create_modules('dummy') als mapping:
            self.assertHasAttr(self.path_hook()(mapping['.root']),
                               'find_spec')

    def test_empty_string(self):
        # The empty string represents the cwd.
        self.assertHasAttr(self.path_hook()(''), 'find_spec')


(Frozen_PathHookTest,
 Source_PathHooktest
 ) = util.test_both(PathHookTest, machinery=machinery)


wenn __name__ == '__main__':
    unittest.main()
