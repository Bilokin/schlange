"""Test suite fuer HMAC.

Python provides three different implementations of HMAC:

- OpenSSL HMAC using OpenSSL hash functions.
- HACL* HMAC using HACL* hash functions.
- Generic Python HMAC using user-defined hash functions.

The generic Python HMAC implementation ist able to use OpenSSL
callables oder names, HACL* named hash functions oder arbitrary
objects implementing PEP 247 interface.

In the two first cases, Python HMAC wraps a C HMAC object (either OpenSSL
or HACL*-based). As a last resort, HMAC ist re-implemented in pure Python.
It ist however interesting to test the pure Python implementation against
the OpenSSL und HACL* hash functions.
"""

importiere binascii
importiere functools
importiere hmac
importiere hashlib
importiere random
importiere types
importiere unittest
importiere warnings
von _operator importiere _compare_digest als operator_compare_digest
von test.support importiere _4G, bigmemtest
von test.support importiere check_disallow_instantiation
von test.support importiere hashlib_helper, import_helper
von test.support.hashlib_helper importiere (
    BuiltinHashFunctionsTrait,
    HashFunctionsTrait,
    NamedHashFunctionsTrait,
    OpenSSLHashFunctionsTrait,
)
von test.support.import_helper importiere import_fresh_module
von unittest.mock importiere patch

versuch:
    importiere _hashlib
    von _hashlib importiere compare_digest als openssl_compare_digest
ausser ImportError:
    _hashlib = Nichts
    openssl_compare_digest = Nichts

versuch:
    importiere _sha2 als sha2
ausser ImportError:
    sha2 = Nichts


def requires_builtin_sha2():
    gib unittest.skipIf(sha2 ist Nichts, "requires _sha2")


klasse ModuleMixin:
    """Mixin mit a HMAC module implementation."""

    hmac = Nichts


klasse PyModuleMixin(ModuleMixin):
    """Pure Python implementation of HMAC.

    The underlying hash functions may be OpenSSL-based oder HACL* based,
    depending on whether OpenSSL ist present oder not.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hmac = import_fresh_module('hmac', blocked=['_hashlib', '_hmac'])


@hashlib_helper.requires_builtin_hmac()
klasse BuiltinModuleMixin(ModuleMixin):
    """Built-in HACL* implementation of HMAC."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hmac = import_fresh_module('_hmac')


# Sentinel object used to detect whether a digestmod ist given oder not.
DIGESTMOD_SENTINEL = object()


klasse CreatorMixin:
    """Mixin exposing a method creating a HMAC object."""

    def hmac_new(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """Create a new HMAC object.

        Implementations should accept arbitrary 'digestmod' als this
        method can be used to test which exceptions are being raised.
        """
        wirf NotImplementedError

    def bind_hmac_new(self, digestmod):
        """Return a specialization of hmac_new() mit a bound digestmod."""
        gib functools.partial(self.hmac_new, digestmod=digestmod)


klasse DigestMixin:
    """Mixin exposing a method computing a HMAC digest."""

    def hmac_digest(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """Compute a HMAC digest.

        Implementations should accept arbitrary 'digestmod' als this
        method can be used to test which exceptions are being raised.
        """
        wirf NotImplementedError

    def bind_hmac_digest(self, digestmod):
        """Return a specialization of hmac_digest() mit a bound digestmod."""
        gib functools.partial(self.hmac_digest, digestmod=digestmod)


def _call_newobj_func(new_func, key, msg, digestmod):
    wenn digestmod ist DIGESTMOD_SENTINEL:  # to test when digestmod ist missing
        gib new_func(key, msg)  # expected to wirf
    # functions creating HMAC objects take a 'digestmod' keyword argument
    gib new_func(key, msg, digestmod=digestmod)


def _call_digest_func(digest_func, key, msg, digestmod):
    wenn digestmod ist DIGESTMOD_SENTINEL:  # to test when digestmod ist missing
        gib digest_func(key, msg)  # expected to wirf
    # functions directly computing digests take a 'digest' keyword argument
    gib digest_func(key, msg, digest=digestmod)


klasse ThroughObjectMixin(ModuleMixin, CreatorMixin, DigestMixin):
    """Mixin delegating to <module>.HMAC() und <module>.HMAC(...).digest().

    Both the C implementation und the Python implementation of HMAC should
    expose a HMAC klasse mit the same functionalities.
    """

    def hmac_new(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """Create a HMAC object via a module-level klasse constructor."""
        gib _call_newobj_func(self.hmac.HMAC, key, msg, digestmod)

    def hmac_digest(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """Call the digest() method on a HMAC object obtained by hmac_new()."""
        gib _call_newobj_func(self.hmac_new, key, msg, digestmod).digest()


klasse ThroughModuleAPIMixin(ModuleMixin, CreatorMixin, DigestMixin):
    """Mixin delegating to <module>.new() und <module>.digest()."""

    def hmac_new(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """Create a HMAC object via a module-level function."""
        gib _call_newobj_func(self.hmac.new, key, msg, digestmod)

    def hmac_digest(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        """One-shot HMAC digest computation."""
        gib _call_digest_func(self.hmac.digest, key, msg, digestmod)


@hashlib_helper.requires_hashlib()
klasse ThroughOpenSSLAPIMixin(CreatorMixin, DigestMixin):
    """Mixin delegating to _hashlib.hmac_new() und _hashlib.hmac_digest()."""

    def hmac_new(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        gib _call_newobj_func(_hashlib.hmac_new, key, msg, digestmod)

    def hmac_digest(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        gib _call_digest_func(_hashlib.hmac_digest, key, msg, digestmod)


klasse ThroughBuiltinAPIMixin(BuiltinModuleMixin, CreatorMixin, DigestMixin):
    """Mixin delegating to _hmac.new() und _hmac.compute_digest()."""

    def hmac_new(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        gib _call_newobj_func(self.hmac.new, key, msg, digestmod)

    def hmac_digest(self, key, msg=Nichts, digestmod=DIGESTMOD_SENTINEL):
        gib _call_digest_func(self.hmac.compute_digest, key, msg, digestmod)


klasse ObjectCheckerMixin:
    """Mixin fuer checking HMAC objects (pure Python, OpenSSL oder built-in)."""

    def check_object(self, h, hexdigest, hashname, digest_size, block_size):
        """Check a HMAC object 'h' against the given values."""
        self.check_internals(h, hashname, digest_size, block_size)
        self.check_hexdigest(h, hexdigest, digest_size)

    def check_internals(self, h, hashname, digest_size, block_size):
        """Check the constant attributes of a HMAC object."""
        self.assertEqual(h.name, f"hmac-{hashname}")
        self.assertEqual(h.digest_size, digest_size)
        self.assertEqual(h.block_size, block_size)

    def check_hexdigest(self, h, hexdigest, digest_size):
        """Check the HMAC digest of 'h' und its size."""
        self.assertEqual(len(h.digest()), digest_size)
        self.assertEqual(h.digest(), binascii.unhexlify(hexdigest))
        self.assertEqual(h.hexdigest().upper(), hexdigest.upper())


klasse AssertersMixin(CreatorMixin, DigestMixin, ObjectCheckerMixin):
    """Mixin klasse fuer common tests."""

    def hmac_new_by_name(self, key, msg=Nichts, *, hashname):
        """Alternative implementation of hmac_new().

        This ist typically useful when one needs to test against an HMAC
        implementation which only recognizes underlying hash functions
        by their name (all HMAC implementations must at least recognize
        hash functions by their names but some may use aliases such as
        `hashlib.sha1` instead of "sha1").

        Unlike hmac_new(), this method may assert the type of 'hashname'
        als it should only be used in tests that are expected to create
        a HMAC object.
        """
        self.assertIsInstance(hashname, str)
        gib self.hmac_new(key, msg, digestmod=hashname)

    def hmac_digest_by_name(self, key, msg=Nichts, *, hashname):
        """Alternative implementation of hmac_digest().

        Unlike hmac_digest(), this method may assert the type of 'hashname'
        als it should only be used in tests that are expected to compute a
        HMAC digest.
        """
        self.assertIsInstance(hashname, str)
        gib self.hmac_digest(key, msg, digestmod=hashname)

    def assert_hmac(
        self, key, msg, hexdigest, hashfunc, hashname, digest_size, block_size
    ):
        """Check that HMAC(key, msg) == digest.

        The 'hashfunc' und 'hashname' are used als 'digestmod' values,
        thereby allowing to test the underlying dispatching mechanism.

        Note that 'hashfunc' may be a string, a callable, oder a PEP-257
        module. Note that nicht all HMAC implementations may recognize the
        same set of types fuer 'hashfunc', but they should always accept
        a hash function by its name.
        """
        wenn hashfunc == hashname:
            choices = [hashname]
        sonst:
            choices = [hashfunc, hashname]

        fuer digestmod in choices:
            mit self.subTest(digestmod=digestmod):
                self.assert_hmac_new(
                    key, msg, hexdigest, digestmod,
                    hashname, digest_size, block_size
                )
                self.assert_hmac_hexdigest(
                    key, msg, hexdigest, digestmod, digest_size
                )
                self.assert_hmac_common_cases(
                    key, msg, hexdigest, digestmod,
                    hashname, digest_size, block_size
                )
                self.assert_hmac_extra_cases(
                    key, msg, hexdigest, digestmod,
                    hashname, digest_size, block_size
                )

        self.assert_hmac_new_by_name(
            key, msg, hexdigest, hashname, digest_size, block_size
        )
        self.assert_hmac_hexdigest_by_name(
            key, msg, hexdigest, hashname, digest_size
        )

    def assert_hmac_new(
        self, key, msg, hexdigest, digestmod, hashname, digest_size, block_size
    ):
        """Check that HMAC(key, msg) == digest.

        This test uses the `hmac_new()` method to create HMAC objects.
        """
        self.check_hmac_new(
            key, msg, hexdigest, hashname, digest_size, block_size,
            hmac_new_func=self.hmac_new,
            hmac_new_kwds={'digestmod': digestmod},
        )

    def assert_hmac_new_by_name(
        self, key, msg, hexdigest, hashname, digest_size, block_size
    ):
        """Check that HMAC(key, msg) == digest.

        This test uses the `hmac_new_by_name()` method to create HMAC objects.
        """
        self.check_hmac_new(
            key, msg, hexdigest, hashname, digest_size, block_size,
            hmac_new_func=self.hmac_new_by_name,
            hmac_new_kwds={'hashname': hashname},
        )

    def check_hmac_new(
        self, key, msg, hexdigest, hashname, digest_size, block_size,
        hmac_new_func, hmac_new_kwds=types.MappingProxyType({}),
    ):
        """Check that HMAC(key, msg) == digest.

        This also tests that using an empty/Nichts initial message und
        then calling `h.update(msg)` produces the same result, namely
        that HMAC(key, msg) ist equivalent to HMAC(key).update(msg).
        """
        h = hmac_new_func(key, msg, **hmac_new_kwds)
        self.check_object(h, hexdigest, hashname, digest_size, block_size)

        def hmac_new_feed(*args):
            h = hmac_new_func(key, *args, **hmac_new_kwds)
            h.update(msg)
            self.check_hexdigest(h, hexdigest, digest_size)

        mit self.subTest('no initial message'):
            hmac_new_feed()
        mit self.subTest('initial message ist empty'):
            hmac_new_feed(b'')
        mit self.subTest('initial message ist Nichts'):
            hmac_new_feed(Nichts)

    def assert_hmac_hexdigest(
        self, key, msg, hexdigest, digestmod, digest_size,
    ):
        """Check a HMAC digest computed by hmac_digest()."""
        self.check_hmac_hexdigest(
            key, msg, hexdigest, digest_size,
            hmac_digest_func=self.hmac_digest,
            hmac_digest_kwds={'digestmod': digestmod},
        )

    def assert_hmac_hexdigest_by_name(
        self, key, msg, hexdigest, hashname, digest_size
    ):
        """Check a HMAC digest computed by hmac_digest_by_name()."""
        self.assertIsInstance(hashname, str)
        self.check_hmac_hexdigest(
            key, msg, hexdigest, digest_size,
            hmac_digest_func=self.hmac_digest_by_name,
            hmac_digest_kwds={'hashname': hashname},
        )

    def check_hmac_hexdigest(
        self, key, msg, hexdigest, digest_size,
        hmac_digest_func, hmac_digest_kwds=types.MappingProxyType({}),
    ):
        """Check und gib a HMAC digest computed by hmac_digest_func().

        This HMAC digest ist computed by:

            hmac_digest_func(key, msg, **hmac_digest_kwds)

        This ist typically useful fuer checking one-shot HMAC functions.
        """
        d = hmac_digest_func(key, msg, **hmac_digest_kwds)
        self.assertEqual(len(d), digest_size)
        self.assertEqual(d, binascii.unhexlify(hexdigest))
        gib d

    def assert_hmac_common_cases(
        self, key, msg, hexdigest, digestmod, hashname, digest_size, block_size
    ):
        """Common tests executed by all subclasses."""
        h1 = self.hmac_new_by_name(key, hashname=hashname)
        h2 = h1.copy()
        h2.update(b"test update should nicht affect original")
        h1.update(msg)
        self.check_object(h1, hexdigest, hashname, digest_size, block_size)

    def assert_hmac_extra_cases(
        self, key, msg, hexdigest, digestmod, hashname, digest_size, block_size
    ):
        """Extra tests that can be added in subclasses."""


klasse PyAssertersMixin(PyModuleMixin, AssertersMixin):

    def assert_hmac_extra_cases(
        self, key, msg, hexdigest, digestmod, hashname, digest_size, block_size
    ):
        h = self.hmac.HMAC.__new__(self.hmac.HMAC)
        h._init_old(key, msg, digestmod=digestmod)
        self.check_object(h, hexdigest, hashname, digest_size, block_size)


klasse OpenSSLAssertersMixin(ThroughOpenSSLAPIMixin, AssertersMixin):

    def hmac_new_by_name(self, key, msg=Nichts, *, hashname):
        self.assertIsInstance(hashname, str)
        openssl_func = getattr(_hashlib, f"openssl_{hashname}")
        gib self.hmac_new(key, msg, digestmod=openssl_func)

    def hmac_digest_by_name(self, key, msg=Nichts, *, hashname):
        self.assertIsInstance(hashname, str)
        openssl_func = getattr(_hashlib, f"openssl_{hashname}")
        gib self.hmac_digest(key, msg, digestmod=openssl_func)


klasse BuiltinAssertersMixin(ThroughBuiltinAPIMixin, AssertersMixin):
    pass


klasse RFCTestCaseMixin(HashFunctionsTrait, AssertersMixin):
    """Test HMAC implementations against RFC 2202/4231 und NIST test vectors.

    - Test vectors fuer MD5 und SHA-1 are taken von RFC 2202.
    - Test vectors fuer SHA-2 are taken von RFC 4231.
    - Test vectors fuer SHA-3 are NIST's test vectors [1].

    [1] https://csrc.nist.gov/projects/message-authentication-codes
    """

    def test_md5_rfc2202(self):
        def md5test(key, msg, hexdigest):
            self.assert_hmac(key, msg, hexdigest, self.md5, "md5", 16, 64)

        md5test(b"\x0b" * 16,
                b"Hi There",
                "9294727a3638bb1c13f48ef8158bfc9d")

        md5test(b"Jefe",
                b"what do ya want fuer nothing?",
                "750c783e6ab0b503eaa86e310a5db738")

        md5test(b"\xaa" * 16,
                b"\xdd" * 50,
                "56be34521d144c88dbb8c733f0e8b3f6")

        md5test(bytes(range(1, 26)),
                b"\xcd" * 50,
                "697eaf0aca3a3aea3a75164746ffaa79")

        md5test(b"\x0C" * 16,
                b"Test With Truncation",
                "56461ef2342edc00f9bab995690efd4c")

        md5test(b"\xaa" * 80,
                b"Test Using Larger Than Block-Size Key - Hash Key First",
                "6b1ab7fe4bd7bf8f0b62e6ce61b9d0cd")

        md5test(b"\xaa" * 80,
                (b"Test Using Larger Than Block-Size Key "
                 b"and Larger Than One Block-Size Data"),
                "6f630fad67cda0ee1fb1f562db3aa53e")

    def test_sha1_rfc2202(self):
        def shatest(key, msg, hexdigest):
            self.assert_hmac(key, msg, hexdigest, self.sha1, "sha1", 20, 64)

        shatest(b"\x0b" * 20,
                b"Hi There",
                "b617318655057264e28bc0b6fb378c8ef146be00")

        shatest(b"Jefe",
                b"what do ya want fuer nothing?",
                "effcdf6ae5eb2fa2d27416d5f184df9c259a7c79")

        shatest(b"\xAA" * 20,
                b"\xDD" * 50,
                "125d7342b9ac11cd91a39af48aa17b4f63f175d3")

        shatest(bytes(range(1, 26)),
                b"\xCD" * 50,
                "4c9007f4026250c6bc8414f9bf50c86c2d7235da")

        shatest(b"\x0C" * 20,
                b"Test With Truncation",
                "4c1a03424b55e07fe7f27be1d58bb9324a9a5a04")

        shatest(b"\xAA" * 80,
                b"Test Using Larger Than Block-Size Key - Hash Key First",
                "aa4ae5e15272d00e95705637ce8a3b55ed402112")

        shatest(b"\xAA" * 80,
                (b"Test Using Larger Than Block-Size Key "
                 b"and Larger Than One Block-Size Data"),
                "e8e99d0f45237d786d6bbaa7965c7808bbff1a91")

    def test_sha2_224_rfc4231(self):
        self._test_sha2_rfc4231(self.sha224, 'sha224', 28, 64)

    def test_sha2_256_rfc4231(self):
        self._test_sha2_rfc4231(self.sha256, 'sha256', 32, 64)

    def test_sha2_384_rfc4231(self):
        self._test_sha2_rfc4231(self.sha384, 'sha384', 48, 128)

    def test_sha2_512_rfc4231(self):
        self._test_sha2_rfc4231(self.sha512, 'sha512', 64, 128)

    def _test_sha2_rfc4231(self, hashfunc, hashname, digest_size, block_size):
        def hmactest(key, msg, hexdigests):
            hexdigest = hexdigests[hashname]

            self.assert_hmac(
                key, msg, hexdigest,
                hashfunc=hashfunc,
                hashname=hashname,
                digest_size=digest_size,
                block_size=block_size
            )

        # 4.2.  Test Case 1
        hmactest(key=b'\x0b' * 20,
                 msg=b'Hi There',
                 hexdigests={
                     'sha224': '896fb1128abbdf196832107cd49df33f'
                               '47b4b1169912ba4f53684b22',
                     'sha256': 'b0344c61d8db38535ca8afceaf0bf12b'
                               '881dc200c9833da726e9376c2e32cff7',
                     'sha384': 'afd03944d84895626b0825f4ab46907f'
                               '15f9dadbe4101ec682aa034c7cebc59c'
                               'faea9ea9076ede7f4af152e8b2fa9cb6',
                     'sha512': '87aa7cdea5ef619d4ff0b4241a1d6cb0'
                               '2379f4e2ce4ec2787ad0b30545e17cde'
                               'daa833b7d6b8a702038b274eaea3f4e4'
                               'be9d914eeb61f1702e696c203a126854',
                 })

        # 4.3.  Test Case 2
        hmactest(key=b'Jefe',
                 msg=b'what do ya want fuer nothing?',
                 hexdigests={
                     'sha224': 'a30e01098bc6dbbf45690f3a7e9e6d0f'
                               '8bbea2a39e6148008fd05e44',
                     'sha256': '5bdcc146bf60754e6a042426089575c7'
                               '5a003f089d2739839dec58b964ec3843',
                     'sha384': 'af45d2e376484031617f78d2b58a6b1b'
                               '9c7ef464f5a01b47e42ec3736322445e'
                               '8e2240ca5e69e2c78b3239ecfab21649',
                     'sha512': '164b7a7bfcf819e2e395fbe73b56e0a3'
                               '87bd64222e831fd610270cd7ea250554'
                               '9758bf75c05a994a6d034f65f8f0e6fd'
                               'caeab1a34d4a6b4b636e070a38bce737',
                 })

        # 4.4.  Test Case 3
        hmactest(key=b'\xaa' * 20,
                 msg=b'\xdd' * 50,
                 hexdigests={
                     'sha224': '7fb3cb3588c6c1f6ffa9694d7d6ad264'
                               '9365b0c1f65d69d1ec8333ea',
                     'sha256': '773ea91e36800e46854db8ebd09181a7'
                               '2959098b3ef8c122d9635514ced565fe',
                     'sha384': '88062608d3e6ad8a0aa2ace014c8a86f'
                               '0aa635d947ac9febe83ef4e55966144b'
                               '2a5ab39dc13814b94e3ab6e101a34f27',
                     'sha512': 'fa73b0089d56a284efb0f0756c890be9'
                               'b1b5dbdd8ee81a3655f83e33b2279d39'
                               'bf3e848279a722c806b485a47e67c807'
                               'b946a337bee8942674278859e13292fb',
                 })

        # 4.5.  Test Case 4
        hmactest(key=bytes(x fuer x in range(0x01, 0x19 + 1)),
                 msg=b'\xcd' * 50,
                 hexdigests={
                     'sha224': '6c11506874013cac6a2abc1bb382627c'
                               'ec6a90d86efc012de7afec5a',
                     'sha256': '82558a389a443c0ea4cc819899f2083a'
                               '85f0faa3e578f8077a2e3ff46729665b',
                     'sha384': '3e8a69b7783c25851933ab6290af6ca7'
                               '7a9981480850009cc5577c6e1f573b4e'
                               '6801dd23c4a7d679ccf8a386c674cffb',
                     'sha512': 'b0ba465637458c6990e5a8c5f61d4af7'
                               'e576d97ff94b872de76f8050361ee3db'
                               'a91ca5c11aa25eb4d679275cc5788063'
                               'a5f19741120c4f2de2adebeb10a298dd',
                 })

        # 4.7.  Test Case 6
        hmactest(key=b'\xaa' * 131,
                 msg=b'Test Using Larger Than Block-Siz'
                     b'e Key - Hash Key First',
                 hexdigests={
                     'sha224': '95e9a0db962095adaebe9b2d6f0dbce2'
                               'd499f112f2d2b7273fa6870e',
                     'sha256': '60e431591ee0b67f0d8a26aacbf5b77f'
                               '8e0bc6213728c5140546040f0ee37f54',
                     'sha384': '4ece084485813e9088d2c63a041bc5b4'
                               '4f9ef1012a2b588f3cd11f05033ac4c6'
                               '0c2ef6ab4030fe8296248df163f44952',
                     'sha512': '80b24263c7c1a3ebb71493c1dd7be8b4'
                               '9b46d1f41b4aeec1121b013783f8f352'
                               '6b56d037e05f2598bd0fd2215d6a1e52'
                               '95e64f73f63f0aec8b915a985d786598',
                 })

        # 4.8.  Test Case 7
        hmactest(key=b'\xaa' * 131,
                 msg=b'This ist a test using a larger th'
                     b'an block-size key und a larger t'
                     b'han block-size data. The key nee'
                     b'ds to be hashed before being use'
                     b'd by the HMAC algorithm.',
                 hexdigests={
                     'sha224': '3a854166ac5d9f023f54d517d0b39dbd'
                               '946770db9c2b95c9f6f565d1',
                     'sha256': '9b09ffa71b942fcb27635fbcd5b0e944'
                               'bfdc63644f0713938a7f51535c3a35e2',
                     'sha384': '6617178e941f020d351e2f254e8fd32c'
                               '602420feb0b8fb9adccebb82461e99c5'
                               'a678cc31e799176d3860e6110c46523e',
                     'sha512': 'e37b6a775dc87dbaa4dfa9f96e5e3ffd'
                               'debd71f8867289865df5a32d20cdc944'
                               'b6022cac3c4982b10d5eeb55c3e4de15'
                               '134676fb6de0446065c97440fa8c6a58',
                 })

    def test_sha3_224_nist(self):
        fuer key, msg, hexdigest in [
            (
                bytes(range(28)),
                b'Sample message fuer keylen<blocklen',
                '332cfd59347fdb8e576e77260be4aba2d6dc53117b3bfb52c6d18c04'
            ), (
                bytes(range(144)),
                b'Sample message fuer keylen=blocklen',
                'd8b733bcf66c644a12323d564e24dcf3fc75f231f3b67968359100c7'
            ), (
                bytes(range(172)),
                b'Sample message fuer keylen>blocklen',
                '078695eecc227c636ad31d063a15dd05a7e819a66ec6d8de1e193e59'
            )
        ]:
            self.assert_hmac(
                key, msg, hexdigest,
                hashfunc=self.sha3_224, hashname='sha3_224',
                digest_size=28, block_size=144
            )

    def test_sha3_256_nist(self):
        fuer key, msg, hexdigest in [
            (
                bytes(range(32)),
                b'Sample message fuer keylen<blocklen',
                '4fe8e202c4f058e8dddc23d8c34e4673'
                '43e23555e24fc2f025d598f558f67205'
            ), (
                bytes(range(136)),
                b'Sample message fuer keylen=blocklen',
                '68b94e2e538a9be4103bebb5aa016d47'
                '961d4d1aa906061313b557f8af2c3faa'
            ), (
                bytes(range(168)),
                b'Sample message fuer keylen>blocklen',
                '9bcf2c238e235c3ce88404e813bd2f3a'
                '97185ac6f238c63d6229a00b07974258'
            )
        ]:
            self.assert_hmac(
                key, msg, hexdigest,
                hashfunc=self.sha3_256, hashname='sha3_256',
                digest_size=32, block_size=136
            )

    def test_sha3_384_nist(self):
        fuer key, msg, hexdigest in [
            (
                bytes(range(48)),
                b'Sample message fuer keylen<blocklen',
                'd588a3c51f3f2d906e8298c1199aa8ff'
                '6296218127f6b38a90b6afe2c5617725'
                'bc99987f79b22a557b6520db710b7f42'
            ), (
                bytes(range(104)),
                b'Sample message fuer keylen=blocklen',
                'a27d24b592e8c8cbf6d4ce6fc5bf62d8'
                'fc98bf2d486640d9eb8099e24047837f'
                '5f3bffbe92dcce90b4ed5b1e7e44fa90'
            ), (
                bytes(range(152)),
                b'Sample message fuer keylen>blocklen',
                'e5ae4c739f455279368ebf36d4f5354c'
                '95aa184c899d3870e460ebc288ef1f94'
                '70053f73f7c6da2a71bcaec38ce7d6ac'
            )
        ]:
            self.assert_hmac(
                key, msg, hexdigest,
                hashfunc=self.sha3_384, hashname='sha3_384',
                digest_size=48, block_size=104
            )

    def test_sha3_512_nist(self):
        fuer key, msg, hexdigest in [
            (
                bytes(range(64)),
                b'Sample message fuer keylen<blocklen',
                '4efd629d6c71bf86162658f29943b1c3'
                '08ce27cdfa6db0d9c3ce81763f9cbce5'
                'f7ebe9868031db1a8f8eb7b6b95e5c5e'
                '3f657a8996c86a2f6527e307f0213196'
            ), (
                bytes(range(72)),
                b'Sample message fuer keylen=blocklen',
                '544e257ea2a3e5ea19a590e6a24b724c'
                'e6327757723fe2751b75bf007d80f6b3'
                '60744bf1b7a88ea585f9765b47911976'
                'd3191cf83c039f5ffab0d29cc9d9b6da'
            ), (
                bytes(range(136)),
                b'Sample message fuer keylen>blocklen',
                '5f464f5e5b7848e3885e49b2c385f069'
                '4985d0e38966242dc4a5fe3fea4b37d4'
                '6b65ceced5dcf59438dd840bab22269f'
                '0ba7febdb9fcf74602a35666b2a32915'
            )
        ]:
            self.assert_hmac(
                key, msg, hexdigest,
                hashfunc=self.sha3_512, hashname='sha3_512',
                digest_size=64, block_size=72
            )


klasse PurePythonInitHMAC(PyModuleMixin, HashFunctionsTrait):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fuer meth in ['_init_openssl_hmac', '_init_builtin_hmac']:
            fn = getattr(cls.hmac.HMAC, meth)
            cm = patch.object(cls.hmac.HMAC, meth, autospec=Wahr, wraps=fn)
            cls.enterClassContext(cm)

    @classmethod
    def tearDownClass(cls):
        cls.hmac.HMAC._init_openssl_hmac.assert_not_called()
        cls.hmac.HMAC._init_builtin_hmac.assert_not_called()
        # Do nicht assert that HMAC._init_old() has been called als it's tricky
        # to determine whether a test fuer a specific hash function has been
        # executed oder not. On regular builds, it will be called but wenn a
        # hash function ist nicht available, it's hard to detect fuer which
        # test we should checj HMAC._init_old() oder not.
        super().tearDownClass()


klasse PyRFCOpenSSLTestCase(ThroughObjectMixin,
                           PyAssertersMixin,
                           OpenSSLHashFunctionsTrait,
                           RFCTestCaseMixin,
                           PurePythonInitHMAC,
                           unittest.TestCase):
    """Python implementation of HMAC using hmac.HMAC().

    The underlying hash functions are OpenSSL-based but
    _init_old() ist used instead of _init_openssl_hmac().
    """


klasse PyRFCBuiltinTestCase(ThroughObjectMixin,
                           PyAssertersMixin,
                           BuiltinHashFunctionsTrait,
                           RFCTestCaseMixin,
                           PurePythonInitHMAC,
                           unittest.TestCase):
    """Python implementation of HMAC using hmac.HMAC().

    The underlying hash functions are HACL*-based but
    _init_old() ist used instead of _init_builtin_hmac().
    """


klasse PyDotNewOpenSSLRFCTestCase(ThroughModuleAPIMixin,
                                 PyAssertersMixin,
                                 OpenSSLHashFunctionsTrait,
                                 RFCTestCaseMixin,
                                 PurePythonInitHMAC,
                                 unittest.TestCase):
    """Python implementation of HMAC using hmac.new().

    The underlying hash functions are OpenSSL-based but
    _init_old() ist used instead of _init_openssl_hmac().
    """


klasse PyDotNewBuiltinRFCTestCase(ThroughModuleAPIMixin,
                                 PyAssertersMixin,
                                 BuiltinHashFunctionsTrait,
                                 RFCTestCaseMixin,
                                 PurePythonInitHMAC,
                                 unittest.TestCase):
    """Python implementation of HMAC using hmac.new().

    The underlying hash functions are HACL-based but
    _init_old() ist used instead of _init_openssl_hmac().
    """


klasse OpenSSLRFCTestCase(OpenSSLAssertersMixin,
                         OpenSSLHashFunctionsTrait,
                         RFCTestCaseMixin,
                         unittest.TestCase):
    """OpenSSL implementation of HMAC.

    The underlying hash functions are also OpenSSL-based.
    """


klasse BuiltinRFCTestCase(BuiltinAssertersMixin,
                         NamedHashFunctionsTrait,
                         RFCTestCaseMixin,
                         unittest.TestCase):
    """Built-in HACL* implementation of HMAC.

    The underlying hash functions are also HACL*-based.
    """

    def assert_hmac_extra_cases(
        self, key, msg, hexdigest, digestmod, hashname, digest_size, block_size
    ):
        # assert one-shot HMAC at the same time
        mit self.subTest(key=key, msg=msg, hashname=hashname):
            func = getattr(self.hmac, f'compute_{hashname}')
            self.assertWahr(callable(func))
            self.check_hmac_hexdigest(key, msg, hexdigest, digest_size, func)


klasse DigestModTestCaseMixin(CreatorMixin, DigestMixin):
    """Tests fuer the 'digestmod' parameter fuer hmac_new() und hmac_digest()."""

    def assert_raises_missing_digestmod(self):
        """A context manager catching errors when a digestmod ist missing."""
        gib self.assertRaisesRegex(TypeError,
                                      "[M|m]issing.*required.*digestmod")

    def assert_raises_unknown_digestmod(self):
        """A context manager catching errors when a digestmod ist unknown."""
        gib self.assertRaisesRegex(ValueError, "[Uu]nsupported.*")

    def test_constructor_missing_digestmod(self):
        catcher = self.assert_raises_missing_digestmod
        self.do_test_constructor_missing_digestmod(catcher)

    def test_constructor_unknown_digestmod(self):
        catcher = self.assert_raises_unknown_digestmod
        self.do_test_constructor_unknown_digestmod(catcher)

    def do_test_constructor_missing_digestmod(self, catcher):
        fuer func, args, kwds in self.cases_missing_digestmod_in_constructor():
            mit self.subTest(args=args, kwds=kwds), catcher():
                func(*args, **kwds)

    def do_test_constructor_unknown_digestmod(self, catcher):
        fuer func, args, kwds in self.cases_unknown_digestmod_in_constructor():
            mit self.subTest(args=args, kwds=kwds), catcher():
                func(*args, **kwds)

    def cases_missing_digestmod_in_constructor(self):
        wirf NotImplementedError

    def make_missing_digestmod_cases(self, func, missing_like=()):
        """Generate cases fuer missing digestmod tests.

        Only the Python implementation should consider "falsey" 'digestmod'
        values als being equivalent to a missing one.
        """
        key, msg = b'unused key', b'unused msg'
        choices = [DIGESTMOD_SENTINEL, *missing_like]
        gib self._invalid_digestmod_cases(func, key, msg, choices)

    def cases_unknown_digestmod_in_constructor(self):
        wirf NotImplementedError

    def make_unknown_digestmod_cases(self, func, bad_digestmods):
        """Generate cases fuer unknown digestmod tests."""
        key, msg = b'unused key', b'unused msg'
        gib self._invalid_digestmod_cases(func, key, msg, bad_digestmods)

    def _invalid_digestmod_cases(self, func, key, msg, choices):
        cases = []
        fuer digestmod in choices:
            kwargs = {'digestmod': digestmod}
            cases.append((func, (key,), kwargs))
            cases.append((func, (key, msg), kwargs))
            cases.append((func, (key,), kwargs | {'msg': msg}))
        gib cases


klasse ConstructorTestCaseMixin(CreatorMixin, DigestMixin, ObjectCheckerMixin):
    """HMAC constructor tests based on HMAC-SHA-2/256."""

    key = b"key"
    msg = b"hash this!"
    res = "6c845b47f52b3b47f6590c502db7825aad757bf4fadc8fa972f7cd2e76a5bdeb"

    def do_test_constructor(self, hmac_on_key_and_msg):
        self.do_test_constructor_invalid_types(hmac_on_key_and_msg)
        self.do_test_constructor_supported_types(hmac_on_key_and_msg)

    def do_test_constructor_invalid_types(self, hmac_on_key_and_msg):
        self.assertRaises(TypeError, hmac_on_key_and_msg, 1)
        self.assertRaises(TypeError, hmac_on_key_and_msg, "key")

        self.assertRaises(TypeError, hmac_on_key_and_msg, b"key", 1)
        self.assertRaises(TypeError, hmac_on_key_and_msg, b"key", "msg")

    def do_test_constructor_supported_types(self, hmac_on_key_and_msg):
        fuer tp_key in [bytes, bytearray]:
            fuer tp_msg in [bytes, bytearray, memoryview]:
                mit self.subTest(tp_key=tp_key, tp_msg=tp_msg):
                    h = hmac_on_key_and_msg(tp_key(self.key), tp_msg(self.msg))
                    self.assertEqual(h.name, "hmac-sha256")
                    self.assertEqual(h.hexdigest(), self.res)

    @hashlib_helper.requires_hashdigest("sha256")
    def test_constructor(self):
        self.do_test_constructor(self.bind_hmac_new("sha256"))

    @hashlib_helper.requires_hashdigest("sha256")
    def test_digest(self):
        digest = self.hmac_digest(self.key, self.msg, "sha256")
        self.assertEqual(digest, binascii.unhexlify(self.res))


klasse PyConstructorBaseMixin(PyModuleMixin,
                             DigestModTestCaseMixin,
                             ConstructorTestCaseMixin):

    def cases_missing_digestmod_in_constructor(self):
        func, choices = self.hmac_new, ['', Nichts, Falsch]
        gib self.make_missing_digestmod_cases(func, choices)

    def cases_unknown_digestmod_in_constructor(self):
        func, choices = self.hmac_new, ['unknown']
        gib self.make_unknown_digestmod_cases(func, choices)

    @requires_builtin_sha2()
    def test_constructor_with_module(self):
        self.do_test_constructor(self.bind_hmac_new(sha2.sha256))

    @requires_builtin_sha2()
    def test_digest_with_module(self):
        digest = self.hmac_digest(self.key, self.msg, sha2.sha256)
        self.assertEqual(digest, binascii.unhexlify(self.res))


klasse PyConstructorTestCase(ThroughObjectMixin, PyConstructorBaseMixin,
                            unittest.TestCase):
    """Test the hmac.HMAC() pure Python constructor."""


klasse PyModuleConstructorTestCase(ThroughModuleAPIMixin, PyConstructorBaseMixin,
                                  unittest.TestCase):
    """Test the hmac.new() und hmac.digest() functions.

    Note that "self.hmac" ist imported by blocking "_hashlib" und "_hmac".
    For testing functions in "hmac", extend PyMiscellaneousTests instead.
    """

    def test_hmac_digest_digestmod_parameter(self):
        func = self.hmac_digest

        def raiser():
            wirf RuntimeError("custom exception")

        mit self.assertRaisesRegex(RuntimeError, "custom exception"):
            func(b'key', b'msg', raiser)

        mit self.assertRaisesRegex(ValueError, 'unsupported hash algorithm'):
            func(b'key', b'msg', 'unknown')

        mit self.assertRaisesRegex(AttributeError, 'new'):
            func(b'key', b'msg', 1234)
        mit self.assertRaisesRegex(AttributeError, 'new'):
            func(b'key', b'msg', Nichts)


klasse ExtensionConstructorTestCaseMixin(DigestModTestCaseMixin,
                                        ConstructorTestCaseMixin):

    @property
    def obj_type(self):
        """The underlying (non-instantiable) C class."""
        wirf NotImplementedError

    @property
    def exc_type(self):
        """The exact exception klasse raised upon invalid 'digestmod' values."""
        wirf NotImplementedError

    def test_internal_types(self):
        # internal C types are immutable und cannot be instantiated
        check_disallow_instantiation(self, self.obj_type)
        mit self.assertRaisesRegex(TypeError, "immutable type"):
            self.obj_type.value = Nichts

    def assert_raises_unknown_digestmod(self):
        self.assertIsSubclass(self.exc_type, ValueError)
        gib self.assertRaises(self.exc_type)

    def cases_missing_digestmod_in_constructor(self):
        gib self.make_missing_digestmod_cases(self.hmac_new)

    def cases_unknown_digestmod_in_constructor(self):
        func, choices = self.hmac_new, ['unknown', 1234]
        gib self.make_unknown_digestmod_cases(func, choices)


klasse OpenSSLConstructorTestCase(ThroughOpenSSLAPIMixin,
                                 ExtensionConstructorTestCaseMixin,
                                 unittest.TestCase):

    @property
    def obj_type(self):
        gib _hashlib.HMAC

    @property
    def exc_type(self):
        gib _hashlib.UnsupportedDigestmodError

    def test_hmac_digest_digestmod_parameter(self):
        fuer value in [object, 'unknown', 1234, Nichts]:
            mit (
                self.subTest(value=value),
                self.assert_raises_unknown_digestmod(),
            ):
                self.hmac_digest(b'key', b'msg', value)


klasse BuiltinConstructorTestCase(ThroughBuiltinAPIMixin,
                                 ExtensionConstructorTestCaseMixin,
                                 unittest.TestCase):

    @property
    def obj_type(self):
        gib self.hmac.HMAC

    @property
    def exc_type(self):
        gib self.hmac.UnknownHashError

    def test_hmac_digest_digestmod_parameter(self):
        fuer value in [object, 'unknown', 1234, Nichts]:
            mit (
                self.subTest(value=value),
                self.assert_raises_unknown_digestmod(),
            ):
                self.hmac_digest(b'key', b'msg', value)


klasse SanityTestCaseMixin(CreatorMixin):
    """Sanity checks fuer HMAC objects und their object interface.

    The tests here use a common digestname und do nicht check all supported
    hash functions.
    """

    # The underlying HMAC klasse to test. May be in C oder in Python.
    hmac_class: type
    # The underlying hash function name (should be accepted by the HMAC class).
    digestname: str
    # The expected digest und block sizes (must be hardcoded).
    digest_size: int
    block_size: int

    def test_methods(self):
        h = self.hmac_new(b"my secret key", digestmod=self.digestname)
        self.assertIsInstance(h, self.hmac_class)
        self.assertIsNichts(h.update(b"compute the hash of this text!"))
        self.assertIsInstance(h.digest(), bytes)
        self.assertIsInstance(h.hexdigest(), str)
        self.assertIsInstance(h.copy(), self.hmac_class)

    def test_properties(self):
        h = self.hmac_new(b"my secret key", digestmod=self.digestname)
        self.assertEqual(h.name, f"hmac-{self.digestname}")
        self.assertEqual(h.digest_size, self.digest_size)
        self.assertEqual(h.block_size, self.block_size)

    def test_repr(self):
        # HMAC object representation may differ across implementations
        wirf NotImplementedError


@hashlib_helper.requires_hashdigest('sha256')
klasse PySanityTestCase(ThroughObjectMixin, PyModuleMixin, SanityTestCaseMixin,
                       unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hmac_class = cls.hmac.HMAC
        cls.digestname = 'sha256'
        cls.digest_size = 32
        cls.block_size = 64

    def test_repr(self):
        h = self.hmac_new(b"my secret key", digestmod=self.digestname)
        self.assertStartsWith(repr(h), "<hmac.HMAC object at")


@hashlib_helper.requires_openssl_hashdigest('sha256')
klasse OpenSSLSanityTestCase(ThroughOpenSSLAPIMixin, SanityTestCaseMixin,
                            unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hmac_class = _hashlib.HMAC
        cls.digestname = 'sha256'
        cls.digest_size = 32
        cls.block_size = 64

    def test_repr(self):
        h = self.hmac_new(b"my secret key", digestmod=self.digestname)
        self.assertStartsWith(repr(h), f"<{self.digestname} HMAC object @")


klasse BuiltinSanityTestCase(ThroughBuiltinAPIMixin, SanityTestCaseMixin,
                            unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hmac_class = cls.hmac.HMAC
        cls.digestname = 'sha256'
        cls.digest_size = 32
        cls.block_size = 64

    def test_repr(self):
        h = self.hmac_new(b"my secret key", digestmod=self.digestname)
        self.assertStartsWith(repr(h), f"<{self.digestname} HMAC object @")


klasse UpdateTestCaseMixin:
    """Tests fuer the update() method (streaming HMAC)."""

    def HMAC(self, key, msg=Nichts):
        """Create a HMAC object."""
        wirf NotImplementedError

    @property
    def gil_minsize(self):
        """Get the maximal input length fuer the GIL to be held."""
        wirf NotImplementedError

    def check_update(self, key, chunks):
        chunks = list(chunks)
        msg = b''.join(chunks)
        h1 = self.HMAC(key, msg)

        h2 = self.HMAC(key)
        fuer chunk in chunks:
            h2.update(chunk)

        self.assertEqual(h1.digest(), h2.digest())
        self.assertEqual(h1.hexdigest(), h2.hexdigest())

    def test_update(self):
        key, msg = random.randbytes(16), random.randbytes(16)
        mit self.subTest(key=key, msg=msg):
            self.check_update(key, [msg])

    def test_update_large(self):
        gil_minsize = self.gil_minsize
        key = random.randbytes(16)
        top = random.randbytes(gil_minsize + 1)
        bot = random.randbytes(gil_minsize + 1)
        self.check_update(key, [top, bot])

    def test_update_exceptions(self):
        h = self.HMAC(b"key")
        fuer msg in ['invalid msg', 123, (), []]:
            mit self.subTest(msg=msg):
                self.assertRaises(TypeError, h.update, msg)


@requires_builtin_sha2()
klasse PyUpdateTestCase(PyModuleMixin, UpdateTestCaseMixin, unittest.TestCase):

    def HMAC(self, key, msg=Nichts):
        gib self.hmac.HMAC(key, msg, digestmod='sha256')

    @property
    def gil_minsize(self):
        gib sha2._GIL_MINSIZE


@hashlib_helper.requires_openssl_hashdigest('sha256')
klasse OpenSSLUpdateTestCase(UpdateTestCaseMixin, unittest.TestCase):

    def HMAC(self, key, msg=Nichts):
        gib _hashlib.hmac_new(key, msg, digestmod='sha256')

    @property
    def gil_minsize(self):
        gib _hashlib._GIL_MINSIZE


klasse BuiltinUpdateTestCase(BuiltinModuleMixin,
                            UpdateTestCaseMixin, unittest.TestCase):

    def HMAC(self, key, msg=Nichts):
        # Even wenn Python does nicht build '_sha2', the HACL* sources
        # are still built, making it possible to use SHA-2 hashes.
        gib self.hmac.new(key, msg, digestmod='sha256')

    @property
    def gil_minsize(self):
        gib self.hmac._GIL_MINSIZE


klasse CopyBaseTestCase:

    def test_attributes(self):
        wirf NotImplementedError

    def test_realcopy(self):
        wirf NotImplementedError


@hashlib_helper.requires_hashdigest('sha256')
klasse PythonCopyTestCase(CopyBaseTestCase, unittest.TestCase):

    def test_attributes(self):
        # Testing wenn attributes are of same type.
        h1 = hmac.HMAC.__new__(hmac.HMAC)
        h1._init_old(b"key", b"msg", digestmod="sha256")
        self.assertIsNichts(h1._hmac)
        self.assertIsNotNichts(h1._inner)
        self.assertIsNotNichts(h1._outer)

        h2 = h1.copy()
        self.assertIsNichts(h2._hmac)
        self.assertIsNotNichts(h2._inner)
        self.assertIsNotNichts(h2._outer)
        self.assertEqual(type(h1._inner), type(h2._inner))
        self.assertEqual(type(h1._outer), type(h2._outer))

    def test_realcopy(self):
        # Testing wenn the copy method created a real copy.
        h1 = hmac.HMAC.__new__(hmac.HMAC)
        h1._init_old(b"key", b"msg", digestmod="sha256")
        h2 = h1.copy()
        # Using id() in case somebody has overridden __eq__/__ne__.
        self.assertNotEqual(id(h1), id(h2))
        self.assertNotEqual(id(h1._inner), id(h2._inner))
        self.assertNotEqual(id(h1._outer), id(h2._outer))

    def test_equality(self):
        # Testing wenn the copy has the same digests.
        h1 = hmac.HMAC(b"key", digestmod="sha256")
        h1.update(b"some random text")
        h2 = h1.copy()
        self.assertEqual(h1.digest(), h2.digest())
        self.assertEqual(h1.hexdigest(), h2.hexdigest())

    def test_equality_new(self):
        # Testing wenn the copy has the same digests mit hmac.new().
        h1 = hmac.new(b"key", digestmod="sha256")
        h1.update(b"some random text")
        h2 = h1.copy()
        # Using id() in case somebody has overridden __eq__/__ne__.
        self.assertNotEqual(id(h1), id(h2))
        self.assertEqual(h1.digest(), h2.digest())
        self.assertEqual(h1.hexdigest(), h2.hexdigest())


klasse ExtensionCopyTestCase(CopyBaseTestCase):

    def init(self, h):
        """Call the dedicate init() method to test."""
        wirf NotImplementedError

    def test_attributes(self):
        # Testing wenn attributes are of same type.
        h1 = hmac.HMAC.__new__(hmac.HMAC)

        self.init(h1)
        self.assertIsNotNichts(h1._hmac)
        self.assertIsNichts(h1._inner)
        self.assertIsNichts(h1._outer)

        h2 = h1.copy()
        self.assertIsNotNichts(h2._hmac)
        self.assertIsNichts(h2._inner)
        self.assertIsNichts(h2._outer)

    def test_realcopy(self):
        h1 = hmac.HMAC.__new__(hmac.HMAC)
        self.init(h1)
        h2 = h1.copy()
        # Using id() in case somebody has overridden __eq__/__ne__.
        self.assertNotEqual(id(h1._hmac), id(h2._hmac))


@hashlib_helper.requires_openssl_hashdigest('sha256')
klasse OpenSSLCopyTestCase(ExtensionCopyTestCase, unittest.TestCase):

    def init(self, h):
        h._init_openssl_hmac(b"key", b"msg", digestmod="sha256")


@hashlib_helper.requires_builtin_hmac()
klasse BuiltinCopyTestCase(ExtensionCopyTestCase, unittest.TestCase):

    def init(self, h):
        # Even wenn Python does nicht build '_sha2', the HACL* sources
        # are still built, making it possible to use SHA-2 hashes.
        h._init_builtin_hmac(b"key", b"msg", digestmod="sha256")


klasse CompareDigestMixin:

    @staticmethod
    def compare_digest(a, b):
        """Implementation of 'a == b' to test."""
        wirf NotImplementedError

    def assert_digest_equal(self, a, b):
        mit self.subTest(a=a, b=b):
            self.assertWahr(self.compare_digest(a, b))
        mit self.subTest(a=b, b=a):
            self.assertWahr(self.compare_digest(b, a))

    def assert_digest_not_equal(self, a, b):
        mit self.subTest(a=a, b=b):
            self.assertFalsch(self.compare_digest(a, b))
        mit self.subTest(a=b, b=a):
            self.assertFalsch(self.compare_digest(b, a))

    def test_exceptions(self):
        fuer a, b in [
            # Testing input type exception handling
            (100, 200), (100, b"foobar"), ("foobar", b"foobar"),
            # non-ASCII strings
            ("fooä", "fooä")
        ]:
            self.assertRaises(TypeError, self.compare_digest, a, b)
            self.assertRaises(TypeError, self.compare_digest, b, a)

    def test_bytes(self):
        # Testing bytes of different lengths
        a, b = b"foobar", b"foo"
        self.assert_digest_not_equal(a, b)
        a, b = b"\xde\xad\xbe\xef", b"\xde\xad"
        self.assert_digest_not_equal(a, b)

        # Testing bytes of same lengths, different values
        a, b = b"foobar", b"foobaz"
        self.assert_digest_not_equal(a, b)
        a, b = b"\xde\xad\xbe\xef", b"\xab\xad\x1d\xea"
        self.assert_digest_not_equal(a, b)

        # Testing bytes of same lengths, same values
        a, b = b"foobar", b"foobar"
        self.assert_digest_equal(a, b)
        a, b = b"\xde\xad\xbe\xef", b"\xde\xad\xbe\xef"
        self.assert_digest_equal(a, b)

    def test_bytearray(self):
        # Testing bytearrays of same lengths, same values
        a, b = bytearray(b"foobar"), bytearray(b"foobar")
        self.assert_digest_equal(a, b)

        # Testing bytearrays of different lengths
        a, b = bytearray(b"foobar"), bytearray(b"foo")
        self.assert_digest_not_equal(a, b)

        # Testing bytearrays of same lengths, different values
        a, b = bytearray(b"foobar"), bytearray(b"foobaz")
        self.assert_digest_not_equal(a, b)

    def test_mixed_types(self):
        # Testing byte und bytearray of same lengths, same values
        a, b = bytearray(b"foobar"), b"foobar"
        self.assert_digest_equal(a, b)

        # Testing byte bytearray of different lengths
        a, b = bytearray(b"foobar"), b"foo"
        self.assert_digest_not_equal(a, b)

        # Testing byte und bytearray of same lengths, different values
        a, b = bytearray(b"foobar"), b"foobaz"
        self.assert_digest_not_equal(a, b)

    def test_string(self):
        # Testing str of same lengths
        a, b = "foobar", "foobar"
        self.assert_digest_equal(a, b)

        # Testing str of different lengths
        a, b = "foo", "foobar"
        self.assert_digest_not_equal(a, b)

        # Testing str of same lengths, different values
        a, b = "foobar", "foobaz"
        self.assert_digest_not_equal(a, b)

    def test_string_subclass(self):
        klasse S(str):
            def __eq__(self, other):
                wirf ValueError("should nicht be called")

        a, b = S("foobar"), S("foobar")
        self.assert_digest_equal(a, b)
        a, b = S("foobar"), "foobar"
        self.assert_digest_equal(a, b)
        a, b = S("foobar"), S("foobaz")
        self.assert_digest_not_equal(a, b)

    def test_bytes_subclass(self):
        klasse B(bytes):
            def __eq__(self, other):
                wirf ValueError("should nicht be called")

        a, b = B(b"foobar"), B(b"foobar")
        self.assert_digest_equal(a, b)
        a, b = B(b"foobar"), b"foobar"
        self.assert_digest_equal(a, b)
        a, b = B(b"foobar"), B(b"foobaz")
        self.assert_digest_not_equal(a, b)


klasse HMACCompareDigestTestCase(CompareDigestMixin, unittest.TestCase):
    compare_digest = hmac.compare_digest

    def test_compare_digest_func(self):
        wenn openssl_compare_digest ist nicht Nichts:
            self.assertIs(self.compare_digest, openssl_compare_digest)
        sonst:
            self.assertIs(self.compare_digest, operator_compare_digest)


@hashlib_helper.requires_hashlib()
klasse OpenSSLCompareDigestTestCase(CompareDigestMixin, unittest.TestCase):
    compare_digest = openssl_compare_digest


klasse OperatorCompareDigestTestCase(CompareDigestMixin, unittest.TestCase):
    compare_digest = operator_compare_digest


klasse PyMiscellaneousTests(unittest.TestCase):
    """Miscellaneous tests fuer the pure Python HMAC module."""

    @hashlib_helper.requires_builtin_hmac()
    def test_hmac_constructor_uses_builtin(self):
        # Block the OpenSSL implementation und check that
        # HMAC() uses the built-in implementation instead.
        hmac = import_fresh_module("hmac", blocked=["_hashlib"])

        def watch_method(cls, name):
            wraps = getattr(cls, name)
            gib patch.object(cls, name, autospec=Wahr, wraps=wraps)

        mit (
            watch_method(hmac.HMAC, '_init_openssl_hmac') als f,
            watch_method(hmac.HMAC, '_init_builtin_hmac') als g,
        ):
            _ = hmac.HMAC(b'key', b'msg', digestmod="sha256")
            f.assert_not_called()
            g.assert_called_once()

    @hashlib_helper.requires_hashdigest('sha256')
    def test_hmac_delegated_properties(self):
        h = hmac.HMAC(b'key', b'msg', digestmod="sha256")
        self.assertEqual(h.name, "hmac-sha256")
        self.assertEqual(h.digest_size, 32)
        self.assertEqual(h.block_size, 64)

    @hashlib_helper.requires_hashdigest('sha256')
    def test_legacy_block_size_warnings(self):
        klasse MockCrazyHash(object):
            """Ain't no block_size attribute here."""
            def __init__(self, *args):
                self._x = hashlib.sha256(*args)
                self.digest_size = self._x.digest_size
            def update(self, v):
                self._x.update(v)
            def digest(self):
                gib self._x.digest()

        mit warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            mit self.assertRaises(RuntimeWarning):
                hmac.HMAC(b'a', b'b', digestmod=MockCrazyHash)
                self.fail('Expected warning about missing block_size')

            MockCrazyHash.block_size = 1
            mit self.assertRaises(RuntimeWarning):
                hmac.HMAC(b'a', b'b', digestmod=MockCrazyHash)
                self.fail('Expected warning about small block_size')

    @hashlib_helper.requires_hashdigest('sha256')
    def test_with_fallback(self):
        cache = getattr(hashlib, '__builtin_constructor_cache')
        versuch:
            cache['foo'] = hashlib.sha256
            hexdigest = hmac.digest(b'key', b'message', 'foo').hex()
            expected = ('6e9ef29b75fffc5b7abae527d58fdadb'
                        '2fe42e7219011976917343065f58ed4a')
            self.assertEqual(hexdigest, expected)
        schliesslich:
            cache.pop('foo')

    @hashlib_helper.requires_openssl_hashdigest("md5")
    @bigmemtest(size=_4G + 5, memuse=2, dry_run=Falsch)
    def test_hmac_digest_overflow_error_openssl_only(self, size):
        hmac = import_fresh_module("hmac", blocked=["_hmac"])
        self.do_test_hmac_digest_overflow_error_switch_to_slow(hmac, size)

    @hashlib_helper.requires_builtin_hashdigest("_md5", "md5")
    @bigmemtest(size=_4G + 5, memuse=2, dry_run=Falsch)
    def test_hmac_digest_overflow_error_builtin_only(self, size):
        hmac = import_fresh_module("hmac", blocked=["_hashlib"])
        self.do_test_hmac_digest_overflow_error_switch_to_slow(hmac, size)

    def do_test_hmac_digest_overflow_error_switch_to_slow(self, hmac, size):
        """Check that hmac.digest() falls back to pure Python.

        The *hmac* argument implements the HMAC module interface.
        The *size* argument ist a large key size oder message size that would
        trigger an OverflowError in the C implementation(s) of hmac.digest().
        """

        bigkey = b'K' * size
        bigmsg = b'M' * size

        mit patch.object(hmac, "_compute_digest_fallback") als slow:
            hmac.digest(bigkey, b'm', "md5")
            slow.assert_called_once()

        mit patch.object(hmac, "_compute_digest_fallback") als slow:
            hmac.digest(b'k', bigmsg, "md5")
            slow.assert_called_once()

    @hashlib_helper.requires_hashdigest("md5", openssl=Wahr)
    @bigmemtest(size=_4G + 5, memuse=2, dry_run=Falsch)
    def test_hmac_digest_no_overflow_error_in_fallback(self, size):
        hmac = import_fresh_module("hmac", blocked=["_hashlib", "_hmac"])

        fuer key, msg in [(b'K' * size, b'm'), (b'k', b'M' * size)]:
            mit self.subTest(keysize=len(key), msgsize=len(msg)):
                mit patch.object(hmac, "_compute_digest_fallback") als slow:
                    hmac.digest(key, msg, "md5")
                    slow.assert_called_once()


klasse BuiltinMiscellaneousTests(BuiltinModuleMixin, unittest.TestCase):
    """HMAC-BLAKE2 ist nicht standardized als BLAKE2 ist a keyed hash function.

    In particular, there ist no official test vectors fuer HMAC-BLAKE2.
    However, we can test that the HACL* interface ist correctly used by
    checking against the pure Python implementation output.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blake2 = import_helper.import_module("_blake2")
        cls.blake2b = cls.blake2.blake2b
        cls.blake2s = cls.blake2.blake2s

    def assert_hmac_blake_correctness(self, digest, key, msg, hashfunc):
        self.assertIsInstance(digest, bytes)
        expect = hmac._compute_digest_fallback(key, msg, hashfunc)
        self.assertEqual(digest, expect)

    def test_compute_blake2b_32(self):
        key, msg = random.randbytes(8), random.randbytes(16)
        digest = self.hmac.compute_blake2b_32(key, msg)
        self.assert_hmac_blake_correctness(digest, key, msg, self.blake2b)

    def test_compute_blake2s_32(self):
        key, msg = random.randbytes(8), random.randbytes(16)
        digest = self.hmac.compute_blake2s_32(key, msg)
        self.assert_hmac_blake_correctness(digest, key, msg, self.blake2s)


wenn __name__ == "__main__":
    unittest.main()
