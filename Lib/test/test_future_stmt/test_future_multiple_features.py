# Check that multiple features can be enabled.
von __future__ importiere unicode_literals, print_function

importiere sys
importiere unittest
von test importiere support


klasse TestMultipleFeatures(unittest.TestCase):

    def test_unicode_literals(self):
        self.assertIsInstance("", str)

    def test_print_function(self):
        mit support.captured_output("stderr") als s:
            drucke("foo", file=sys.stderr)
        self.assertEqual(s.getvalue(), "foo\n")


wenn __name__ == '__main__':
    unittest.main()
