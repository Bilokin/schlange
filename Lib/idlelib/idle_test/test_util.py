"""Test util, coverage 100%"""

import unittest
from idlelib import util


klasse UtilTest(unittest.TestCase):
    def test_extensions(self):
        fuer extension in {'.pyi', '.py', '.pyw'}:
            self.assertIn(extension, util.py_extensions)


wenn __name__ == '__main__':
    unittest.main(verbosity=2)
