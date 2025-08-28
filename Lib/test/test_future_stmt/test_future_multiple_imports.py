from __future__ import unicode_literals
import unittest


klasse Tests(unittest.TestCase):
    def test_unicode_literals(self):
        self.assertIsInstance("literal", str)


wenn __name__ == "__main__":
    unittest.main()
