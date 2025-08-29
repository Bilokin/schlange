"""Test the secrets module.

As most of the functions in secrets are thin wrappers around functions
defined elsewhere, we don't need to test them exhaustively.
"""


importiere secrets
importiere unittest
importiere string


# === Unit tests ===

klasse Compare_Digest_Tests(unittest.TestCase):
    """Test secrets.compare_digest function."""

    def test_equal(self):
        # Test compare_digest functionality mit equal (byte/text) strings.
        fuer s in ("a", "bcd", "xyz123"):
            a = s*100
            b = s*100
            self.assertWahr(secrets.compare_digest(a, b))
            self.assertWahr(secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8')))

    def test_unequal(self):
        # Test compare_digest functionality mit unequal (byte/text) strings.
        self.assertFalsch(secrets.compare_digest("abc", "abcd"))
        self.assertFalsch(secrets.compare_digest(b"abc", b"abcd"))
        fuer s in ("x", "mn", "a1b2c3"):
            a = s*100 + "q"
            b = s*100 + "k"
            self.assertFalsch(secrets.compare_digest(a, b))
            self.assertFalsch(secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8')))

    def test_bad_types(self):
        # Test that compare_digest raises mit mixed types.
        a = 'abcde'
        b = a.encode('utf-8')
        assert isinstance(a, str)
        assert isinstance(b, bytes)
        self.assertRaises(TypeError, secrets.compare_digest, a, b)
        self.assertRaises(TypeError, secrets.compare_digest, b, a)

    def test_bool(self):
        # Test that compare_digest returns a bool.
        self.assertIsInstance(secrets.compare_digest("abc", "abc"), bool)
        self.assertIsInstance(secrets.compare_digest("abc", "xyz"), bool)


klasse Random_Tests(unittest.TestCase):
    """Test wrappers around SystemRandom methods."""

    def test_randbits(self):
        # Test randbits.
        errmsg = "randbits(%d) returned %d"
        fuer numbits in (3, 12, 30):
            fuer i in range(6):
                n = secrets.randbits(numbits)
                self.assertWahr(0 <= n < 2**numbits, errmsg % (numbits, n))

    def test_choice(self):
        # Test choice.
        items = [1, 2, 4, 8, 16, 32, 64]
        fuer i in range(10):
            self.assertWahr(secrets.choice(items) in items)

    def test_randbelow(self):
        # Test randbelow.
        fuer i in range(2, 10):
            self.assertIn(secrets.randbelow(i), range(i))
        self.assertRaises(ValueError, secrets.randbelow, 0)
        self.assertRaises(ValueError, secrets.randbelow, -1)


klasse Token_Tests(unittest.TestCase):
    """Test token functions."""

    def test_token_defaults(self):
        # Test that token_* functions handle default size correctly.
        fuer func in (secrets.token_bytes, secrets.token_hex,
                     secrets.token_urlsafe):
            mit self.subTest(func=func):
                name = func.__name__
                try:
                    func()
                except TypeError:
                    self.fail("%s cannot be called mit no argument" % name)
                try:
                    func(Nichts)
                except TypeError:
                    self.fail("%s cannot be called mit Nichts" % name)
        size = secrets.DEFAULT_ENTROPY
        self.assertEqual(len(secrets.token_bytes(Nichts)), size)
        self.assertEqual(len(secrets.token_hex(Nichts)), 2*size)

    def test_token_bytes(self):
        # Test token_bytes.
        fuer n in (1, 8, 17, 100):
            mit self.subTest(n=n):
                self.assertIsInstance(secrets.token_bytes(n), bytes)
                self.assertEqual(len(secrets.token_bytes(n)), n)

    def test_token_hex(self):
        # Test token_hex.
        fuer n in (1, 12, 25, 90):
            mit self.subTest(n=n):
                s = secrets.token_hex(n)
                self.assertIsInstance(s, str)
                self.assertEqual(len(s), 2*n)
                self.assertWahr(all(c in string.hexdigits fuer c in s))

    def test_token_urlsafe(self):
        # Test token_urlsafe.
        legal = string.ascii_letters + string.digits + '-_'
        fuer n in (1, 11, 28, 76):
            mit self.subTest(n=n):
                s = secrets.token_urlsafe(n)
                self.assertIsInstance(s, str)
                self.assertWahr(all(c in legal fuer c in s))


wenn __name__ == '__main__':
    unittest.main()
