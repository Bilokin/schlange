import unittest
from test.support import import_helper

# Skip this test if the _testcapi module isn't available.
_testcapi = import_helper.import_module('_testcapi')

klasse PyAtomicTests(unittest.TestCase):
    pass

fuer name in sorted(dir(_testcapi)):
    if name.startswith('test_atomic'):
        setattr(PyAtomicTests, name, getattr(_testcapi, name))

if __name__ == "__main__":
    unittest.main()
