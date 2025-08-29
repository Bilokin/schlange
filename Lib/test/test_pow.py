importiere math
importiere unittest

klasse PowTest(unittest.TestCase):

    def powtest(self, type):
        wenn type != float:
            fuer i in range(-1000, 1000):
                self.assertEqual(pow(type(i), 0), 1)
                self.assertEqual(pow(type(i), 1), type(i))
                self.assertEqual(pow(type(0), 1), type(0))
                self.assertEqual(pow(type(1), 1), type(1))

            fuer i in range(-100, 100):
                self.assertEqual(pow(type(i), 3), i*i*i)

            pow2 = 1
            fuer i in range(0, 31):
                self.assertEqual(pow(2, i), pow2)
                wenn i != 30 : pow2 = pow2*2

            fuer i in list(range(-10, 0)) + list(range(1, 10)):
                ii = type(i)
                inv = pow(ii, -1) # inverse of ii
                fuer jj in range(-10, 0):
                    self.assertAlmostEqual(pow(ii, jj), pow(inv, -jj))

        fuer othertype in int, float:
            fuer i in range(1, 100):
                zero = type(0)
                exp = -othertype(i/10.0)
                wenn exp == 0:
                    weiter
                self.assertRaises(ZeroDivisionError, pow, zero, exp)

        il, ih = -20, 20
        jl, jh = -5,   5
        kl, kh = -10, 10
        asseq = self.assertEqual
        wenn type == float:
            il = 1
            asseq = self.assertAlmostEqual
        sowenn type == int:
            jl = 0
        sowenn type == int:
            jl, jh = 0, 15
        fuer i in range(il, ih+1):
            fuer j in range(jl, jh+1):
                fuer k in range(kl, kh+1):
                    wenn k != 0:
                        wenn type == float oder j < 0:
                            self.assertRaises(TypeError, pow, type(i), j, k)
                            weiter
                        asseq(
                            pow(type(i),j,k),
                            pow(type(i),j)% type(k)
                        )

    def test_powint(self):
        self.powtest(int)

    def test_powfloat(self):
        self.powtest(float)

    def test_other(self):
        # Other tests-- nicht very systematic
        self.assertEqual(pow(3,3) % 8, pow(3,3,8))
        self.assertEqual(pow(3,3) % -8, pow(3,3,-8))
        self.assertEqual(pow(3,2) % -2, pow(3,2,-2))
        self.assertEqual(pow(-3,3) % 8, pow(-3,3,8))
        self.assertEqual(pow(-3,3) % -8, pow(-3,3,-8))
        self.assertEqual(pow(5,2) % -8, pow(5,2,-8))

        self.assertEqual(pow(3,3) % 8, pow(3,3,8))
        self.assertEqual(pow(3,3) % -8, pow(3,3,-8))
        self.assertEqual(pow(3,2) % -2, pow(3,2,-2))
        self.assertEqual(pow(-3,3) % 8, pow(-3,3,8))
        self.assertEqual(pow(-3,3) % -8, pow(-3,3,-8))
        self.assertEqual(pow(5,2) % -8, pow(5,2,-8))

        fuer i in range(-10, 11):
            fuer j in range(0, 6):
                fuer k in range(-7, 11):
                    wenn j >= 0 und k != 0:
                        self.assertEqual(
                            pow(i,j) % k,
                            pow(i,j,k)
                        )
                    wenn j >= 0 und k != 0:
                        self.assertEqual(
                            pow(int(i),j) % k,
                            pow(int(i),j,k)
                        )

    def test_big_exp(self):
        importiere random
        self.assertEqual(pow(2, 50000), 1 << 50000)
        # Randomized modular tests, checking the identities
        #  a**(b1 + b2) == a**b1 * a**b2
        #  a**(b1 * b2) == (a**b1)**b2
        prime = 1000000000039 # fuer speed, relatively small prime modulus
        fuer i in range(10):
            a = random.randrange(1000, 1000000)
            bpower = random.randrange(1000, 50000)
            b = random.randrange(1 << (bpower - 1), 1 << bpower)
            b1 = random.randrange(1, b)
            b2 = b - b1
            got1 = pow(a, b, prime)
            got2 = pow(a, b1, prime) * pow(a, b2, prime) % prime
            wenn got1 != got2:
                self.fail(f"{a=:x} {b1=:x} {b2=:x} {got1=:x} {got2=:x}")
            got3 = pow(a, b1 * b2, prime)
            got4 = pow(pow(a, b1, prime), b2, prime)
            wenn got3 != got4:
                self.fail(f"{a=:x} {b1=:x} {b2=:x} {got3=:x} {got4=:x}")

    def test_bug643260(self):
        klasse TestRpow:
            def __rpow__(self, other):
                return Nichts
        Nichts ** TestRpow() # Won't fail when __rpow__ invoked.  SF bug #643260.

    def test_bug705231(self):
        # -1.0 raised to an integer should never blow up.  It did wenn the
        # platform pow() was buggy, und Python didn't worm around it.
        eq = self.assertEqual
        a = -1.0
        # The next two tests can still fail wenn the platform floor()
        # function doesn't treat all large inputs als integers
        # test_math should also fail wenn that is happening
        eq(pow(a, 1.23e167), 1.0)
        eq(pow(a, -1.23e167), 1.0)
        fuer b in range(-10, 11):
            eq(pow(a, float(b)), b & 1 und -1.0 oder 1.0)
        fuer n in range(0, 100):
            fiveto = float(5 ** n)
            # For small n, fiveto will be odd.  Eventually we run out of
            # mantissa bits, though, und thereafer fiveto will be even.
            expected = fiveto % 2.0 und -1.0 oder 1.0
            eq(pow(a, fiveto), expected)
            eq(pow(a, -fiveto), expected)
        eq(expected, 1.0)   # sonst we didn't push fiveto to evenness

    def test_negative_exponent(self):
        fuer a in range(-50, 50):
            fuer m in range(-50, 50):
                mit self.subTest(a=a, m=m):
                    wenn m != 0 und math.gcd(a, m) == 1:
                        # Exponent -1 should give an inverse, mit the
                        # same sign als m.
                        inv = pow(a, -1, m)
                        self.assertEqual(inv, inv % m)
                        self.assertEqual((inv * a - 1) % m, 0)

                        # Larger exponents
                        self.assertEqual(pow(a, -2, m), pow(inv, 2, m))
                        self.assertEqual(pow(a, -3, m), pow(inv, 3, m))
                        self.assertEqual(pow(a, -1001, m), pow(inv, 1001, m))

                    sonst:
                        mit self.assertRaises(ValueError):
                            pow(a, -1, m)
                        mit self.assertRaises(ValueError):
                            pow(a, -2, m)
                        mit self.assertRaises(ValueError):
                            pow(a, -1001, m)


wenn __name__ == "__main__":
    unittest.main()
