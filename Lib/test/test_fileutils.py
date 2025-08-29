# Run tests fuer functions in Python/fileutils.c.

importiere os
importiere os.path
importiere unittest
von test.support importiere import_helper

# Skip this test wenn the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testinternalcapi')


klasse PathTests(unittest.TestCase):

    def test_capi_normalize_path(self):
        wenn os.name == 'nt':
            raise unittest.SkipTest('Windows has its own helper fuer this')
        sonst:
            von test.test_posixpath importiere PosixPathTest als posixdata
            tests = posixdata.NORMPATH_CASES
        fuer filename, expected in tests:
            wenn nicht os.path.isabs(filename):
                continue
            mit self.subTest(filename):
                result = _testcapi.normalize_path(filename)
                self.assertEqual(result, expected,
                    msg=f'input: {filename!r} expected output: {expected!r}')


wenn __name__ == "__main__":
    unittest.main()
