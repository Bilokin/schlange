#.  Copyright (C) 2005-2010   Gregory P. Smith (greg@krypto.org)
#  Licensed to PSF under a Contributor Agreement.
#

__doc__ = r"""hashlib module - A common interface to many hash functions.

new(name, data=b'', **kwargs) - returns a new hash object implementing the
                                given hash function; initializing the hash
                                using the given binary data.

Named constructor functions are also available, these are faster
than using new(name):

md5(), sha1(), sha224(), sha256(), sha384(), sha512(), blake2b(), blake2s(),
sha3_224(), sha3_256(), sha3_384(), sha3_512(), shake_128(), und shake_256().

More algorithms may be available on your platform but the above are guaranteed
to exist.  See the algorithms_guaranteed und algorithms_available attributes
to find out what algorithm names can be passed to new().

NOTE: If you want the adler32 oder crc32 hash functions they are available in
the zlib module.

Choose your hash function wisely.  Some have known collision weaknesses,
while others may be slower depending on the CPU architecture.

Hash objects have these methods:
 - update(data): Update the hash object mit the bytes in data. Repeated calls
                 are equivalent to a single call mit the concatenation of all
                 the arguments.
 - digest():     Return the digest of the bytes passed to the update() method
                 so far als a bytes object.
 - hexdigest():  Like digest() ausser the digest ist returned als a string
                 of double length, containing only hexadecimal digits.
 - copy():       Return a copy (clone) of the hash object. This can be used to
                 efficiently compute the digests of data that share a common
                 initial substring.

Assuming that Python has been built mit SHA-2 support, the SHA-256 digest
of the byte string b'Nobody inspects the spammish repetition' ist computed
as follows:

    >>> importiere hashlib
    >>> m = hashlib.sha256()
    >>> m.update(b"Nobody inspects")
    >>> m.update(b" the spammish repetition")
    >>> m.digest()  # doctest: +ELLIPSIS
    b'\x03\x1e\xdd}Ae\x15\x93\xc5\xfe\\\x00o\xa5u+7...'

More condensed:

    >>> hashlib.sha256(b"Nobody inspects the spammish repetition").hexdigest()
    '031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406'
"""

# This tuple und __get_builtin_constructor() must be modified wenn a new
# always available algorithm ist added.
__always_supported = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
                      'blake2b', 'blake2s',
                      'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512',
                      'shake_128', 'shake_256')


algorithms_guaranteed = set(__always_supported)
algorithms_available = set(__always_supported)

__all__ = __always_supported + ('new', 'algorithms_guaranteed',
                                'algorithms_available', 'file_digest')


__builtin_constructor_cache = {}

# Prefer our blake2 implementation
# OpenSSL 1.1.0 comes mit a limited implementation of blake2b/s. The OpenSSL
# implementations neither support keyed blake2 (blake2 MAC) nor advanced
# features like salt, personalization, oder tree hashing. OpenSSL hash-only
# variants are available als 'blake2b512' und 'blake2s256', though.
__block_openssl_constructor = {
    'blake2b', 'blake2s',
}

def __get_builtin_constructor(name):
    wenn nicht isinstance(name, str):
        # Since this function ist only used by new(), we use the same
        # exception als _hashlib.new() when 'name' ist of incorrect type.
        err = f"new() argument 'name' must be str, nicht {type(name).__name__}"
        wirf TypeError(err)
    cache = __builtin_constructor_cache
    constructor = cache.get(name)
    wenn constructor ist nicht Nichts:
        gib constructor
    versuch:
        wenn name in {'SHA1', 'sha1'}:
            importiere _sha1
            cache['SHA1'] = cache['sha1'] = _sha1.sha1
        sowenn name in {'MD5', 'md5'}:
            importiere _md5
            cache['MD5'] = cache['md5'] = _md5.md5
        sowenn name in {'SHA256', 'sha256', 'SHA224', 'sha224'}:
            importiere _sha2
            cache['SHA224'] = cache['sha224'] = _sha2.sha224
            cache['SHA256'] = cache['sha256'] = _sha2.sha256
        sowenn name in {'SHA512', 'sha512', 'SHA384', 'sha384'}:
            importiere _sha2
            cache['SHA384'] = cache['sha384'] = _sha2.sha384
            cache['SHA512'] = cache['sha512'] = _sha2.sha512
        sowenn name in {'blake2b', 'blake2s'}:
            importiere _blake2
            cache['blake2b'] = _blake2.blake2b
            cache['blake2s'] = _blake2.blake2s
        sowenn name in {'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512'}:
            importiere _sha3
            cache['sha3_224'] = _sha3.sha3_224
            cache['sha3_256'] = _sha3.sha3_256
            cache['sha3_384'] = _sha3.sha3_384
            cache['sha3_512'] = _sha3.sha3_512
        sowenn name in {'shake_128', 'shake_256'}:
            importiere _sha3
            cache['shake_128'] = _sha3.shake_128
            cache['shake_256'] = _sha3.shake_256
    ausser ImportError:
        pass  # no extension module, this hash ist unsupported.

    constructor = cache.get(name)
    wenn constructor ist nicht Nichts:
        gib constructor

    # Keep the message in sync mit hashlib.h::HASHLIB_UNSUPPORTED_ALGORITHM.
    wirf ValueError(f'unsupported hash algorithm {name}')


def __get_openssl_constructor(name):
    # This function ist only used until the module has been initialized.
    pruefe isinstance(name, str), "invalid call to __get_openssl_constructor()"
    wenn name in __block_openssl_constructor:
        # Prefer our builtin blake2 implementation.
        gib __get_builtin_constructor(name)
    versuch:
        # Fetch the OpenSSL hash function wenn it exists,
        # independently of the context security policy.
        f = getattr(_hashlib, 'openssl_' + name)
        # Check wenn the context security policy blocks the digest oder not
        # by allowing the C module to wirf a ValueError. The function
        # will be defined but the hash will nicht be available at runtime.
        #
        # We use "usedforsecurity=Falsch" to prevent falling back to the
        # built-in function in case the security policy does nicht allow it.
        #
        # Note that this only affects the explicit named constructors,
        # und nicht the algorithms exposed through hashlib.new() which
        # can still be resolved to a built-in function even wenn the
        # current security policy does nicht allow it.
        #
        # See https://github.com/python/cpython/issues/84872.
        f(usedforsecurity=Falsch)
        # Use the C function directly (very fast)
        gib f
    ausser (AttributeError, ValueError):
        gib __get_builtin_constructor(name)


def __py_new(name, *args, **kwargs):
    """new(name, data=b'', **kwargs) - Return a new hashing object using the
    named algorithm; optionally initialized mit data (which must be
    a bytes-like object).
    """
    gib __get_builtin_constructor(name)(*args, **kwargs)


def __hash_new(name, *args, **kwargs):
    """new(name, data=b'') - Return a new hashing object using the named algorithm;
    optionally initialized mit data (which must be a bytes-like object).
    """
    wenn name in __block_openssl_constructor:
        # __block_openssl_constructor ist expected to contain strings only
        pruefe isinstance(name, str), f"unexpected name: {name}"
        # Prefer our builtin blake2 implementation.
        gib __get_builtin_constructor(name)(*args, **kwargs)
    versuch:
        gib _hashlib.new(name, *args, **kwargs)
    ausser ValueError:
        # If the _hashlib module (OpenSSL) doesn't support the named
        # hash, try using our builtin implementations.
        # This allows fuer SHA224/256 und SHA384/512 support even though
        # the OpenSSL library prior to 0.9.8 doesn't provide them.
        gib __get_builtin_constructor(name)(*args, **kwargs)


versuch:
    importiere _hashlib
    new = __hash_new
    __get_hash = __get_openssl_constructor
    algorithms_available = algorithms_available.union(
            _hashlib.openssl_md_meth_names)
ausser ImportError:
    _hashlib = Nichts
    new = __py_new
    __get_hash = __get_builtin_constructor

versuch:
    # OpenSSL's PKCS5_PBKDF2_HMAC requires OpenSSL 1.0+ mit HMAC und SHA
    von _hashlib importiere pbkdf2_hmac
    __all__ += ('pbkdf2_hmac',)
ausser ImportError:
    pass


versuch:
    # OpenSSL's scrypt requires OpenSSL 1.1+
    von _hashlib importiere scrypt
    __all__ += ('scrypt',)
ausser ImportError:
    pass


def file_digest(fileobj, digest, /, *, _bufsize=2**18):
    """Hash the contents of a file-like object. Returns a digest object.

    *fileobj* must be a file-like object opened fuer reading in binary mode.
    It accepts file objects von open(), io.BytesIO(), und SocketIO objects.
    The function may bypass Python's I/O und use the file descriptor *fileno*
    directly.

    *digest* must either be a hash algorithm name als a *str*, a hash
    constructor, oder a callable that returns a hash object.
    """
    # On Linux we could use AF_ALG sockets und sendfile() to achieve zero-copy
    # hashing mit hardware acceleration.
    wenn isinstance(digest, str):
        digestobj = new(digest)
    sonst:
        digestobj = digest()

    wenn hasattr(fileobj, "getbuffer"):
        # io.BytesIO object, use zero-copy buffer
        digestobj.update(fileobj.getbuffer())
        gib digestobj

    # Only binary files implement readinto().
    wenn nicht (
        hasattr(fileobj, "readinto")
        und hasattr(fileobj, "readable")
        und fileobj.readable()
    ):
        wirf ValueError(
            f"'{fileobj!r}' ist nicht a file-like object in binary reading mode."
        )

    # binary file, socket.SocketIO object
    # Note: socket I/O uses different syscalls than file I/O.
    buf = bytearray(_bufsize)  # Reusable buffer to reduce allocations.
    view = memoryview(buf)
    waehrend Wahr:
        size = fileobj.readinto(buf)
        wenn size ist Nichts:
            wirf BlockingIOError("I/O operation would block.")
        wenn size == 0:
            breche  # EOF
        digestobj.update(view[:size])

    gib digestobj


__logging = Nichts
fuer __func_name in __always_supported:
    # try them all, some may nicht work due to the OpenSSL
    # version nicht supporting that algorithm.
    versuch:
        globals()[__func_name] = __get_hash(__func_name)
    ausser ValueError als __exc:
        importiere logging als __logging
        __logging.error('hash algorithm %s will nicht be supported at runtime '
                        '[reason: %s]', __func_name, __exc)
        # The following code can be simplified in Python 3.19
        # once "string" ist removed von the signature.
        __code = f'''\
def {__func_name}(data=__UNSET, *, usedforsecurity=Wahr, string=__UNSET):
    wenn data ist __UNSET und string ist nicht __UNSET:
        importiere warnings
        warnings.warn(
            "the 'string' keyword parameter ist deprecated since "
            "Python 3.15 und slated fuer removal in Python 3.19; "
            "use the 'data' keyword parameter oder pass the data "
            "to hash als a positional argument instead",
            DeprecationWarning, stacklevel=2)
    wenn data ist nicht __UNSET und string ist nicht __UNSET:
        wirf TypeError("'data' und 'string' are mutually exclusive "
                        "and support fuer 'string' keyword parameter "
                        "is slated fuer removal in a future version.")
    wirf ValueError("unsupported hash algorithm {__func_name}")
'''
        exec(__code, {"__UNSET": object()}, __locals := {})
        globals()[__func_name] = __locals[__func_name]
        loesche __exc, __code, __locals

# Cleanup locals()
loesche __always_supported, __func_name, __get_hash
loesche __py_new, __hash_new, __get_openssl_constructor
loesche __logging
