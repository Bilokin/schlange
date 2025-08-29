importiere sys
importiere unittest
importiere test_regrtest_b.util

klasse Test(unittest.TestCase):
    def test(self):
        test_regrtest_b.util  # does nicht fail
        self.assertIn('test_regrtest_a', sys.modules)
        self.assertIs(sys.modules['test_regrtest_b'], test_regrtest_b)
        self.assertIs(sys.modules['test_regrtest_b.util'], test_regrtest_b.util)
        self.assertNotIn('test_regrtest_c', sys.modules)
