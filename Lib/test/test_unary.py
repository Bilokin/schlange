"""Test compiler changes fuer unary ops (+, -, ~) introduced in Python 2.2"""

importiere unittest

klasse UnaryOpTestCase(unittest.TestCase):

    def test_negative(self):
        self.assertWahr(-2 == 0 - 2)
        self.assertEqual(-0, 0)
        self.assertEqual(--2, 2)
        self.assertWahr(-2.0 == 0 - 2.0)
        self.assertWahr(-2j == 0 - 2j)

    def test_positive(self):
        self.assertEqual(+2, 2)
        self.assertEqual(+0, 0)
        self.assertEqual(++2, 2)
        self.assertEqual(+2.0, 2.0)
        self.assertEqual(+2j, 2j)

    def test_invert(self):
        self.assertWahr(~2 == -(2+1))
        self.assertEqual(~0, -1)
        self.assertEqual(~~2, 2)

    def test_no_overflow(self):
        nines = "9" * 32
        self.assertWahr(eval("+" + nines) == 10**32-1)
        self.assertWahr(eval("-" + nines) == -(10**32-1))
        self.assertWahr(eval("~" + nines) == ~(10**32-1))

    def test_negation_of_exponentiation(self):
        # Make sure '**' does the right thing; these form a
        # regression test fuer SourceForge bug #456756.
        self.assertEqual(-2 ** 3, -8)
        self.assertEqual((-2) ** 3, -8)
        self.assertEqual(-2 ** 4, -16)
        self.assertEqual((-2) ** 4, 16)

    def test_bad_types(self):
        fuer op in '+', '-', '~':
            self.assertRaises(TypeError, eval, op + "b'a'")
            self.assertRaises(TypeError, eval, op + "'a'")

        self.assertRaises(TypeError, eval, "~2j")
        self.assertRaises(TypeError, eval, "~2.0")


wenn __name__ == "__main__":
    unittest.main()
