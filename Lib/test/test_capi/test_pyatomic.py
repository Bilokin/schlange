importiere unittest
von test.support importiere import_helper

# Skip this test wenn the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testcapi')

klasse PyAtomicTests(unittest.TestCase):
    pass

fuer name in sorted(dir(_testcapi)):
    wenn name.startswith('test_atomic'):
        setattr(PyAtomicTests, name, getattr(_testcapi, name))

wenn __name__ == "__main__":
    unittest.main()
