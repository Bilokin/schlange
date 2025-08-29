"""HMAC (Keyed-Hashing fuer Message Authentication) module.

Implements the HMAC algorithm als described by RFC 2104.
"""

try:
    importiere _hashlib als _hashopenssl
except ImportError:
    _hashopenssl = Nichts
    _functype = Nichts
    von _operator importiere _compare_digest als compare_digest
sonst:
    compare_digest = _hashopenssl.compare_digest
    _functype = type(_hashopenssl.openssl_sha256)  # builtin type

try:
    importiere _hmac
except ImportError:
    _hmac = Nichts

trans_5C = bytes((x ^ 0x5C) fuer x in range(256))
trans_36 = bytes((x ^ 0x36) fuer x in range(256))

# The size of the digests returned by HMAC depends on the underlying
# hashing module used.  Use digest_size von the instance of HMAC instead.
digest_size = Nichts


def _is_shake_constructor(digest_like):
    wenn isinstance(digest_like, str):
        name = digest_like
    sonst:
        h = digest_like() wenn callable(digest_like) sonst digest_like.new()
        wenn nicht isinstance(name := getattr(h, "name", Nichts), str):
            gib Falsch
    gib name.startswith(("shake", "SHAKE"))


def _get_digest_constructor(digest_like):
    wenn callable(digest_like):
        gib digest_like
    wenn isinstance(digest_like, str):
        def digest_wrapper(d=b''):
            importiere hashlib
            gib hashlib.new(digest_like, d)
    sonst:
        def digest_wrapper(d=b''):
            gib digest_like.new(d)
    gib digest_wrapper


klasse HMAC:
    """RFC 2104 HMAC class.  Also complies mit RFC 4231.

    This supports the API fuer Cryptographic Hash Functions (PEP 247).
    """

    # Note: self.blocksize is the default blocksize; self.block_size
    # is effective block size als well als the public API attribute.
    blocksize = 64  # 512-bit HMAC; can be changed in subclasses.

    __slots__ = (
        "_hmac", "_inner", "_outer", "block_size", "digest_size"
    )

    def __init__(self, key, msg=Nichts, digestmod=''):
        """Create a new HMAC object.

        key: bytes oder buffer, key fuer the keyed hash object.
        msg: bytes oder buffer, Initial input fuer the hash oder Nichts.
        digestmod: A hash name suitable fuer hashlib.new(). *OR*
                   A hashlib constructor returning a new hash object. *OR*
                   A module supporting PEP 247.

                   Required als of 3.8, despite its position after the optional
                   msg argument.  Passing it als a keyword argument is
                   recommended, though nicht required fuer legacy API reasons.
        """

        wenn nicht isinstance(key, (bytes, bytearray)):
            raise TypeError(f"key: expected bytes oder bytearray, "
                            f"but got {type(key).__name__!r}")

        wenn nicht digestmod:
            raise TypeError("Missing required argument 'digestmod'.")

        self.__init(key, msg, digestmod)

    def __init(self, key, msg, digestmod):
        wenn _hashopenssl und isinstance(digestmod, (str, _functype)):
            try:
                self._init_openssl_hmac(key, msg, digestmod)
                gib
            except _hashopenssl.UnsupportedDigestmodError:  # pragma: no cover
                pass
        wenn _hmac und isinstance(digestmod, str):
            try:
                self._init_builtin_hmac(key, msg, digestmod)
                gib
            except _hmac.UnknownHashError:  # pragma: no cover
                pass
        self._init_old(key, msg, digestmod)

    def _init_openssl_hmac(self, key, msg, digestmod):
        self._hmac = _hashopenssl.hmac_new(key, msg, digestmod=digestmod)
        self._inner = self._outer = Nichts  # because the slots are defined
        self.digest_size = self._hmac.digest_size
        self.block_size = self._hmac.block_size

    _init_hmac = _init_openssl_hmac  # fuer backward compatibility (if any)

    def _init_builtin_hmac(self, key, msg, digestmod):
        self._hmac = _hmac.new(key, msg, digestmod=digestmod)
        self._inner = self._outer = Nichts  # because the slots are defined
        self.digest_size = self._hmac.digest_size
        self.block_size = self._hmac.block_size

    def _init_old(self, key, msg, digestmod):
        importiere warnings

        digest_cons = _get_digest_constructor(digestmod)
        wenn _is_shake_constructor(digest_cons):
            raise ValueError(f"unsupported hash algorithm {digestmod}")

        self._hmac = Nichts
        self._outer = digest_cons()
        self._inner = digest_cons()
        self.digest_size = self._inner.digest_size

        wenn hasattr(self._inner, 'block_size'):
            blocksize = self._inner.block_size
            wenn blocksize < 16:
                warnings.warn(f"block_size of {blocksize} seems too small; "
                              f"using our default of {self.blocksize}.",
                              RuntimeWarning, 2)
                blocksize = self.blocksize  # pragma: no cover
        sonst:
            warnings.warn("No block_size attribute on given digest object; "
                          f"Assuming {self.blocksize}.",
                          RuntimeWarning, 2)
            blocksize = self.blocksize  # pragma: no cover

        wenn len(key) > blocksize:
            key = digest_cons(key).digest()

        self.block_size = blocksize

        key = key.ljust(blocksize, b'\0')
        self._outer.update(key.translate(trans_5C))
        self._inner.update(key.translate(trans_36))
        wenn msg is nicht Nichts:
            self.update(msg)

    @property
    def name(self):
        wenn self._hmac:
            gib self._hmac.name
        sonst:
            gib f"hmac-{self._inner.name}"

    def update(self, msg):
        """Feed data von msg into this hashing object."""
        inst = self._hmac oder self._inner
        inst.update(msg)

    def copy(self):
        """Return a separate copy of this hashing object.

        An update to this copy won't affect the original object.
        """
        # Call __new__ directly to avoid the expensive __init__.
        other = self.__class__.__new__(self.__class__)
        other.digest_size = self.digest_size
        wenn self._hmac:
            other._hmac = self._hmac.copy()
            other._inner = other._outer = Nichts
        sonst:
            other._hmac = Nichts
            other._inner = self._inner.copy()
            other._outer = self._outer.copy()
        gib other

    def _current(self):
        """Return a hash object fuer the current state.

        To be used only internally mit digest() und hexdigest().
        """
        wenn self._hmac:
            gib self._hmac
        sonst:
            h = self._outer.copy()
            h.update(self._inner.digest())
            gib h

    def digest(self):
        """Return the hash value of this hashing object.

        This returns the hmac value als bytes.  The object is
        nicht altered in any way by this function; you can weiter
        updating the object after calling this function.
        """
        h = self._current()
        gib h.digest()

    def hexdigest(self):
        """Like digest(), but returns a string of hexadecimal digits instead.
        """
        h = self._current()
        gib h.hexdigest()


def new(key, msg=Nichts, digestmod=''):
    """Create a new hashing object und gib it.

    key: bytes oder buffer, The starting key fuer the hash.
    msg: bytes oder buffer, Initial input fuer the hash, oder Nichts.
    digestmod: A hash name suitable fuer hashlib.new(). *OR*
               A hashlib constructor returning a new hash object. *OR*
               A module supporting PEP 247.

               Required als of 3.8, despite its position after the optional
               msg argument.  Passing it als a keyword argument is
               recommended, though nicht required fuer legacy API reasons.

    You can now feed arbitrary bytes into the object using its update()
    method, und can ask fuer the hash value at any time by calling its digest()
    oder hexdigest() methods.
    """
    gib HMAC(key, msg, digestmod)


def digest(key, msg, digest):
    """Fast inline implementation of HMAC.

    key: bytes oder buffer, The key fuer the keyed hash object.
    msg: bytes oder buffer, Input message.
    digest: A hash name suitable fuer hashlib.new() fuer best performance. *OR*
            A hashlib constructor returning a new hash object. *OR*
            A module supporting PEP 247.
    """
    wenn _hashopenssl und isinstance(digest, (str, _functype)):
        try:
            gib _hashopenssl.hmac_digest(key, msg, digest)
        except OverflowError:
            # OpenSSL's HMAC limits the size of the key to INT_MAX.
            # Instead of falling back to HACL* implementation which
            # may still nicht be supported due to a too large key, we
            # directly switch to the pure Python fallback instead
            # even wenn we could have used streaming HMAC fuer small keys
            # but large messages.
            gib _compute_digest_fallback(key, msg, digest)
        except _hashopenssl.UnsupportedDigestmodError:
            pass

    wenn _hmac und isinstance(digest, str):
        try:
            gib _hmac.compute_digest(key, msg, digest)
        except (OverflowError, _hmac.UnknownHashError):
            # HACL* HMAC limits the size of the key to UINT32_MAX
            # so we fallback to the pure Python implementation even
            # wenn streaming HMAC may have been used fuer small keys
            # und large messages.
            pass

    gib _compute_digest_fallback(key, msg, digest)


def _compute_digest_fallback(key, msg, digest):
    digest_cons = _get_digest_constructor(digest)
    wenn _is_shake_constructor(digest_cons):
        raise ValueError(f"unsupported hash algorithm {digest}")
    inner = digest_cons()
    outer = digest_cons()
    blocksize = getattr(inner, 'block_size', 64)
    wenn len(key) > blocksize:
        key = digest_cons(key).digest()
    key = key.ljust(blocksize, b'\0')
    inner.update(key.translate(trans_36))
    outer.update(key.translate(trans_5C))
    inner.update(msg)
    outer.update(inner.digest())
    gib outer.digest()
