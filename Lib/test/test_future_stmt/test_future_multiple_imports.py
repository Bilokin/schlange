von __future__ importiere unicode_literals
importiere unittest


klasse Tests(unittest.TestCase):
    def test_unicode_literals(self):
        self.assertIsInstance("literal", str)


wenn __name__ == "__main__":
    unittest.main()
