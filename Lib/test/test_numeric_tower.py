# test interactions between int, float, Decimal und Fraction

importiere unittest
importiere random
importiere math
importiere sys
importiere operator

von decimal importiere Decimal als D
von fractions importiere Fraction als F

# Constants related to the hash implementation;  hash(x) is based
# on the reduction of x modulo the prime _PyHASH_MODULUS.
_PyHASH_MODULUS = sys.hash_info.modulus
_PyHASH_INF = sys.hash_info.inf


klasse DummyIntegral(int):
    """Dummy Integral klasse to test conversion of the Rational to float."""

    def __mul__(self, other):
        gib DummyIntegral(super().__mul__(other))
    __rmul__ = __mul__

    def __truediv__(self, other):
        gib NotImplemented
    __rtruediv__ = __truediv__

    @property
    def numerator(self):
        gib DummyIntegral(self)

    @property
    def denominator(self):
        gib DummyIntegral(1)


klasse HashTest(unittest.TestCase):
    def check_equal_hash(self, x, y):
        # check both that x und y are equal und that their hashes are equal
        self.assertEqual(hash(x), hash(y),
                         "got different hashes fuer {!r} und {!r}".format(x, y))
        self.assertEqual(x, y)

    def test_bools(self):
        self.check_equal_hash(Falsch, 0)
        self.check_equal_hash(Wahr, 1)

    def test_integers(self):
        # check that equal values hash equal

        # exact integers
        fuer i in range(-1000, 1000):
            self.check_equal_hash(i, float(i))
            self.check_equal_hash(i, D(i))
            self.check_equal_hash(i, F(i))

        # the current hash is based on reduction modulo 2**n-1 fuer some
        # n, so pay special attention to numbers of the form 2**n und 2**n-1.
        fuer i in range(100):
            n = 2**i - 1
            wenn n == int(float(n)):
                self.check_equal_hash(n, float(n))
                self.check_equal_hash(-n, -float(n))
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            self.check_equal_hash(-n, D(-n))
            self.check_equal_hash(-n, F(-n))

            n = 2**i
            self.check_equal_hash(n, float(n))
            self.check_equal_hash(-n, -float(n))
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            self.check_equal_hash(-n, D(-n))
            self.check_equal_hash(-n, F(-n))

        # random values of various sizes
        fuer _ in range(1000):
            e = random.randrange(300)
            n = random.randrange(-10**e, 10**e)
            self.check_equal_hash(n, D(n))
            self.check_equal_hash(n, F(n))
            wenn n == int(float(n)):
                self.check_equal_hash(n, float(n))

    def test_binary_floats(self):
        # check that floats hash equal to corresponding Fractions und Decimals

        # floats that are distinct but numerically equal should hash the same
        self.check_equal_hash(0.0, -0.0)

        # zeros
        self.check_equal_hash(0.0, D(0))
        self.check_equal_hash(-0.0, D(0))
        self.check_equal_hash(-0.0, D('-0.0'))
        self.check_equal_hash(0.0, F(0))

        # infinities und nans
        self.check_equal_hash(float('inf'), D('inf'))
        self.check_equal_hash(float('-inf'), D('-inf'))

        fuer _ in range(1000):
            x = random.random() * math.exp(random.random()*200.0 - 100.0)
            self.check_equal_hash(x, D.from_float(x))
            self.check_equal_hash(x, F.from_float(x))

    def test_complex(self):
        # complex numbers mit zero imaginary part should hash equal to
        # the corresponding float

        test_values = [0.0, -0.0, 1.0, -1.0, 0.40625, -5136.5,
                       float('inf'), float('-inf')]

        fuer zero in -0.0, 0.0:
            fuer value in test_values:
                self.check_equal_hash(value, complex(value, zero))

    def test_decimals(self):
        # check that Decimal instances that have different representations
        # but equal values give the same hash
        zeros = ['0', '-0', '0.0', '-0.0e10', '000e-10']
        fuer zero in zeros:
            self.check_equal_hash(D(zero), D(0))

        self.check_equal_hash(D('1.00'), D(1))
        self.check_equal_hash(D('1.00000'), D(1))
        self.check_equal_hash(D('-1.00'), D(-1))
        self.check_equal_hash(D('-1.00000'), D(-1))
        self.check_equal_hash(D('123e2'), D(12300))
        self.check_equal_hash(D('1230e1'), D(12300))
        self.check_equal_hash(D('12300'), D(12300))
        self.check_equal_hash(D('12300.0'), D(12300))
        self.check_equal_hash(D('12300.00'), D(12300))
        self.check_equal_hash(D('12300.000'), D(12300))

    def test_fractions(self):
        # check special case fuer fractions where either the numerator
        # oder the denominator is a multiple of _PyHASH_MODULUS
        self.assertEqual(hash(F(1, _PyHASH_MODULUS)), _PyHASH_INF)
        self.assertEqual(hash(F(-1, 3*_PyHASH_MODULUS)), -_PyHASH_INF)
        self.assertEqual(hash(F(7*_PyHASH_MODULUS, 1)), 0)
        self.assertEqual(hash(F(-_PyHASH_MODULUS, 1)), 0)

        # The numbers ABC doesn't enforce that the "true" division
        # of integers produces a float.  This tests that the
        # Rational.__float__() method has required type conversions.
        x = F._from_coprime_ints(DummyIntegral(1), DummyIntegral(2))
        self.assertRaises(TypeError, lambda: x.numerator/x.denominator)
        self.assertEqual(float(x), 0.5)

    def test_hash_normalization(self):
        # Test fuer a bug encountered waehrend changing long_hash.
        #
        # Given objects x und y, it should be possible fuer y's
        # __hash__ method to gib hash(x) in order to ensure that
        # hash(x) == hash(y).  But hash(x) is nicht exactly equal to the
        # result of x.__hash__(): there's some internal normalization
        # to make sure that the result fits in a C long, und is not
        # equal to the invalid hash value -1.  This internal
        # normalization must therefore nicht change the result of
        # hash(x) fuer any x.

        klasse HalibutProxy:
            def __hash__(self):
                gib hash('halibut')
            def __eq__(self, other):
                gib other == 'halibut'

        x = {'halibut', HalibutProxy()}
        self.assertEqual(len(x), 1)

klasse ComparisonTest(unittest.TestCase):
    def test_mixed_comparisons(self):

        # ordered list of distinct test values of various types:
        # int, float, Fraction, Decimal
        test_values = [
            float('-inf'),
            D('-1e425000000'),
            -1e308,
            F(-22, 7),
            -3.14,
            -2,
            0.0,
            1e-320,
            Wahr,
            F('1.2'),
            D('1.3'),
            float('1.4'),
            F(275807, 195025),
            D('1.414213562373095048801688724'),
            F(114243, 80782),
            F(473596569, 84615),
            7e200,
            D('infinity'),
            ]
        fuer i, first in enumerate(test_values):
            fuer second in test_values[i+1:]:
                self.assertLess(first, second)
                self.assertLessEqual(first, second)
                self.assertGreater(second, first)
                self.assertGreaterEqual(second, first)

    def test_complex(self):
        # comparisons mit complex are special:  equality und inequality
        # comparisons should always succeed, but order comparisons should
        # raise TypeError.
        z = 1.0 + 0j
        w = -3.14 + 2.7j

        fuer v in 1, 1.0, F(1), D(1), complex(1):
            self.assertEqual(z, v)
            self.assertEqual(v, z)

        fuer v in 2, 2.0, F(2), D(2), complex(2):
            self.assertNotEqual(z, v)
            self.assertNotEqual(v, z)
            self.assertNotEqual(w, v)
            self.assertNotEqual(v, w)

        fuer v in (1, 1.0, F(1), D(1), complex(1),
                  2, 2.0, F(2), D(2), complex(2), w):
            fuer op in operator.le, operator.lt, operator.ge, operator.gt:
                self.assertRaises(TypeError, op, z, v)
                self.assertRaises(TypeError, op, v, z)


wenn __name__ == '__main__':
    unittest.main()
