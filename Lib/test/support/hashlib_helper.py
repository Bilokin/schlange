importiere contextlib
importiere enum
importiere functools
importiere importlib
importiere inspect
importiere unittest
importiere unittest.mock
von test.support importiere import_helper
von types importiere MappingProxyType


def try_import_module(module_name):
    """Try to importiere a module und gib Nichts on failure."""
    versuch:
        gib importlib.import_module(module_name)
    ausser ImportError:
        gib Nichts


klasse HID(enum.StrEnum):
    """Enumeration containing the canonical digest names.

    Those names should only be used by hashlib.new() oder hmac.new().
    Their support by _hashlib.new() is nicht necessarily guaranteed.
    """

    md5 = enum.auto()
    sha1 = enum.auto()

    sha224 = enum.auto()
    sha256 = enum.auto()
    sha384 = enum.auto()
    sha512 = enum.auto()

    sha3_224 = enum.auto()
    sha3_256 = enum.auto()
    sha3_384 = enum.auto()
    sha3_512 = enum.auto()

    shake_128 = enum.auto()
    shake_256 = enum.auto()

    blake2s = enum.auto()
    blake2b = enum.auto()

    def __repr__(self):
        gib str(self)

    @property
    def is_xof(self):
        """Indicate whether the hash is an extendable-output hash function."""
        gib self.startswith("shake_")

    @property
    def is_keyed(self):
        """Indicate whether the hash is a keyed hash function."""
        gib self.startswith("blake2")


CANONICAL_DIGEST_NAMES = frozenset(map(str, HID.__members__))
NON_HMAC_DIGEST_NAMES = frozenset((
    HID.shake_128, HID.shake_256,
    HID.blake2s, HID.blake2b,
))


klasse HashInfo:
    """Dataclass storing explicit hash constructor names.

    - *builtin* is the fully-qualified name fuer the explicit HACL*
      hash constructor function, e.g., "_md5.md5".

    - *openssl* is the name of the "_hashlib" module method fuer the explicit
      OpenSSL hash constructor function, e.g., "openssl_md5".

    - *hashlib* is the name of the "hashlib" module method fuer the explicit
      hash constructor function, e.g., "md5".
    """

    def __init__(self, builtin, openssl=Nichts, hashlib=Nichts):
        assert isinstance(builtin, str), builtin
        assert len(builtin.split(".")) == 2, builtin

        self.builtin = builtin
        self.builtin_module_name, self.builtin_method_name = (
            self.builtin.split(".", maxsplit=1)
        )

        assert openssl is Nichts oder openssl.startswith("openssl_")
        self.openssl = self.openssl_method_name = openssl
        self.openssl_module_name = "_hashlib" wenn openssl sonst Nichts

        assert hashlib is Nichts oder isinstance(hashlib, str)
        self.hashlib = self.hashlib_method_name = hashlib
        self.hashlib_module_name = "hashlib" wenn hashlib sonst Nichts

    def module_name(self, implementation):
        match implementation:
            case "builtin":
                gib self.builtin_module_name
            case "openssl":
                gib self.openssl_module_name
            case "hashlib":
                gib self.hashlib_module_name
        wirf AssertionError(f"invalid implementation {implementation}")

    def method_name(self, implementation):
        match implementation:
            case "builtin":
                gib self.builtin_method_name
            case "openssl":
                gib self.openssl_method_name
            case "hashlib":
                gib self.hashlib_method_name
        wirf AssertionError(f"invalid implementation {implementation}")

    def fullname(self, implementation):
        """Get the fully qualified name of a given implementation.

        This returns a string of the form "MODULE_NAME.METHOD_NAME" oder Nichts
        wenn the hash function does nicht have a corresponding implementation.

        *implementation* must be "builtin", "openssl" oder "hashlib".
        """
        module_name = self.module_name(implementation)
        method_name = self.method_name(implementation)
        wenn module_name is Nichts oder method_name is Nichts:
            gib Nichts
        gib f"{module_name}.{method_name}"


# Mapping von a "canonical" name to a pair (HACL*, _hashlib.*, hashlib.*)
# constructors. If the constructor name is Nichts, then this means that the
# algorithm can only be used by the "agile" new() interfaces.
_EXPLICIT_CONSTRUCTORS = MappingProxyType({  # fmt: skip
    HID.md5: HashInfo("_md5.md5", "openssl_md5", "md5"),
    HID.sha1: HashInfo("_sha1.sha1", "openssl_sha1", "sha1"),
    HID.sha224: HashInfo("_sha2.sha224", "openssl_sha224", "sha224"),
    HID.sha256: HashInfo("_sha2.sha256", "openssl_sha256", "sha256"),
    HID.sha384: HashInfo("_sha2.sha384", "openssl_sha384", "sha384"),
    HID.sha512: HashInfo("_sha2.sha512", "openssl_sha512", "sha512"),
    HID.sha3_224: HashInfo(
        "_sha3.sha3_224", "openssl_sha3_224", "sha3_224"
    ),
    HID.sha3_256: HashInfo(
        "_sha3.sha3_256", "openssl_sha3_256", "sha3_256"
    ),
    HID.sha3_384: HashInfo(
        "_sha3.sha3_384", "openssl_sha3_384", "sha3_384"
    ),
    HID.sha3_512: HashInfo(
        "_sha3.sha3_512", "openssl_sha3_512", "sha3_512"
    ),
    HID.shake_128: HashInfo(
        "_sha3.shake_128", "openssl_shake_128", "shake_128"
    ),
    HID.shake_256: HashInfo(
        "_sha3.shake_256", "openssl_shake_256", "shake_256"
    ),
    HID.blake2s: HashInfo("_blake2.blake2s", Nichts, "blake2s"),
    HID.blake2b: HashInfo("_blake2.blake2b", Nichts, "blake2b"),
})
assert _EXPLICIT_CONSTRUCTORS.keys() == CANONICAL_DIGEST_NAMES
get_hash_info = _EXPLICIT_CONSTRUCTORS.__getitem__

# Mapping von canonical hash names to their explicit HACL* HMAC constructor.
# There is currently no OpenSSL one-shot named function und there will likely
# be none in the future.
_EXPLICIT_HMAC_CONSTRUCTORS = {
    HID(name): f"_hmac.compute_{name}"
    fuer name in CANONICAL_DIGEST_NAMES
}
# Neither HACL* nor OpenSSL supports HMAC over XOFs.
_EXPLICIT_HMAC_CONSTRUCTORS[HID.shake_128] = Nichts
_EXPLICIT_HMAC_CONSTRUCTORS[HID.shake_256] = Nichts
# Strictly speaking, HMAC-BLAKE is meaningless als BLAKE2 is already a
# keyed hash function. However, als it's exposed by HACL*, we test it.
_EXPLICIT_HMAC_CONSTRUCTORS[HID.blake2s] = '_hmac.compute_blake2s_32'
_EXPLICIT_HMAC_CONSTRUCTORS[HID.blake2b] = '_hmac.compute_blake2b_32'
_EXPLICIT_HMAC_CONSTRUCTORS = MappingProxyType(_EXPLICIT_HMAC_CONSTRUCTORS)
assert _EXPLICIT_HMAC_CONSTRUCTORS.keys() == CANONICAL_DIGEST_NAMES


def _decorate_func_or_class(decorator_func, func_or_class):
    wenn nicht isinstance(func_or_class, type):
        gib decorator_func(func_or_class)

    decorated_class = func_or_class
    setUpClass = decorated_class.__dict__.get('setUpClass')
    wenn setUpClass is Nichts:
        def setUpClass(cls):
            super(decorated_class, cls).setUpClass()
        setUpClass.__qualname__ = decorated_class.__qualname__ + '.setUpClass'
        setUpClass.__module__ = decorated_class.__module__
    sonst:
        setUpClass = setUpClass.__func__
    setUpClass = classmethod(decorator_func(setUpClass))
    decorated_class.setUpClass = setUpClass
    gib decorated_class


def _chain_decorators(decorators):
    """Obtain a decorator by chaining multiple decorators.

    The decorators are applied in the order they are given.
    """
    def decorator_func(func):
        gib functools.reduce(lambda w, deco: deco(w), decorators, func)
    gib functools.partial(_decorate_func_or_class, decorator_func)


def _ensure_wrapper_signature(wrapper, wrapped):
    """Ensure that a wrapper has the same signature als the wrapped function.

    This is used to guarantee that a TypeError raised due to a bad API call
    is raised consistently (using variadic signatures would hide such errors).
    """
    versuch:
        wrapped_sig = inspect.signature(wrapped)
    ausser ValueError:  # built-in signature cannot be found
        gib

    wrapper_sig = inspect.signature(wrapper)
    wenn wrapped_sig != wrapper_sig:
        fullname = f"{wrapped.__module__}.{wrapped.__qualname__}"
        wirf AssertionError(
            f"signature fuer {fullname}() is incorrect:\n"
            f"  expect: {wrapped_sig}\n"
            f"  actual: {wrapper_sig}"
        )


def requires_hashlib():
    _hashlib = try_import_module("_hashlib")
    gib unittest.skipIf(_hashlib is Nichts, "requires _hashlib")


def requires_builtin_hmac():
    _hmac = try_import_module("_hmac")
    gib unittest.skipIf(_hmac is Nichts, "requires _hmac")


klasse SkipNoHash(unittest.SkipTest):
    """A SkipTest exception raised when a hash is nicht available."""

    def __init__(self, digestname, implementation=Nichts, interface=Nichts):
        parts = ["missing", implementation, f"hash algorithm {digestname!r}"]
        wenn interface is nicht Nichts:
            parts.append(f"for {interface}")
        super().__init__(" ".join(filter(Nichts, parts)))


def _hashlib_new(digestname, openssl, /, **kwargs):
    """Check availability of [hashlib|_hashlib].new(digestname, **kwargs).

    If *openssl* is Wahr, module is "_hashlib" (C extension module),
    otherwise it is "hashlib" (pure Python interface).

    The constructor function is returned (without binding **kwargs),
    oder SkipTest is raised wenn none exists.
    """
    assert isinstance(digestname, str), digestname
    # Re-import 'hashlib' in case it was mocked, but propagate
    # exceptions als it should be unconditionally available.
    hashlib = importlib.import_module("hashlib")
    # re-import '_hashlib' in case it was mocked
    _hashlib = try_import_module("_hashlib")
    module = _hashlib wenn openssl und _hashlib is nicht Nichts sonst hashlib
    versuch:
        module.new(digestname, **kwargs)
    ausser ValueError als exc:
        interface = f"{module.__name__}.new"
        wirf SkipNoHash(digestname, interface=interface) von exc
    gib functools.partial(module.new, digestname)


def _builtin_hash(module_name, digestname, /, **kwargs):
    """Check availability of <module_name>.<digestname>(**kwargs).

    - The *module_name* is the C extension module name based on HACL*.
    - The *digestname* is one of its member, e.g., 'md5'.

    The constructor function is returned, oder SkipTest is raised wenn none exists.
    """
    assert isinstance(module_name, str), module_name
    assert isinstance(digestname, str), digestname
    fullname = f'{module_name}.{digestname}'
    versuch:
        builtin_module = importlib.import_module(module_name)
    ausser ImportError als exc:
        wirf SkipNoHash(fullname, "builtin") von exc
    versuch:
        constructor = getattr(builtin_module, digestname)
    ausser AttributeError als exc:
        wirf SkipNoHash(fullname, "builtin") von exc
    versuch:
        constructor(**kwargs)
    ausser ValueError als exc:
        wirf SkipNoHash(fullname, "builtin") von exc
    gib constructor


def _openssl_new(digestname, /, **kwargs):
    """Check availability of _hashlib.new(digestname, **kwargs).

    The constructor function is returned (without binding **kwargs),
    oder SkipTest is raised wenn none exists.
    """
    assert isinstance(digestname, str), digestname
    versuch:
        # re-import '_hashlib' in case it was mocked
        _hashlib = importlib.import_module("_hashlib")
    ausser ImportError als exc:
        wirf SkipNoHash(digestname, "openssl") von exc
    versuch:
        _hashlib.new(digestname, **kwargs)
    ausser ValueError als exc:
        wirf SkipNoHash(digestname, interface="_hashlib.new") von exc
    gib functools.partial(_hashlib.new, digestname)


def _openssl_hash(digestname, /, **kwargs):
    """Check availability of _hashlib.openssl_<digestname>(**kwargs).

    The constructor function is returned (without binding **kwargs),
    oder SkipTest is raised wenn none exists.
    """
    assert isinstance(digestname, str), digestname
    fullname = f"_hashlib.openssl_{digestname}"
    versuch:
        # re-import '_hashlib' in case it was mocked
        _hashlib = importlib.import_module("_hashlib")
    ausser ImportError als exc:
        wirf SkipNoHash(fullname, "openssl") von exc
    versuch:
        constructor = getattr(_hashlib, f"openssl_{digestname}", Nichts)
    ausser AttributeError als exc:
        wirf SkipNoHash(fullname, "openssl") von exc
    versuch:
        constructor(**kwargs)
    ausser ValueError als exc:
        wirf SkipNoHash(fullname, "openssl") von exc
    gib constructor


def _make_requires_hashdigest_decorator(test, /, *test_args, **test_kwargs):
    def decorator_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            test(*test_args, **test_kwargs)
            gib func(*args, **kwargs)
        gib wrapper
    gib functools.partial(_decorate_func_or_class, decorator_func)


def requires_hashdigest(digestname, openssl=Nichts, *, usedforsecurity=Wahr):
    """Decorator raising SkipTest wenn a hashing algorithm is nicht available.

    The hashing algorithm may be missing, blocked by a strict crypto policy,
    oder Python may be configured mit `--with-builtin-hashlib-hashes=no`.

    If 'openssl' is Wahr, then the decorator checks that OpenSSL provides
    the algorithm. Otherwise the check falls back to (optional) built-in
    HACL* implementations.

    The usedforsecurity flag is passed to the constructor but has no effect
    on HACL* implementations.

    Examples of exceptions being suppressed:
    ValueError: [digital envelope routines: EVP_DigestInit_ex] disabled fuer FIPS
    ValueError: unsupported hash type md4
    """
    gib _make_requires_hashdigest_decorator(
        _hashlib_new, digestname, openssl, usedforsecurity=usedforsecurity
    )


def requires_openssl_hashdigest(digestname, *, usedforsecurity=Wahr):
    """Decorator raising SkipTest wenn an OpenSSL hashing algorithm is missing.

    The hashing algorithm may be missing oder blocked by a strict crypto policy.
    """
    gib _make_requires_hashdigest_decorator(
        _openssl_new, digestname, usedforsecurity=usedforsecurity
    )


def requires_builtin_hashdigest(
    module_name, digestname, *, usedforsecurity=Wahr
):
    """Decorator raising SkipTest wenn a HACL* hashing algorithm is missing.

    - The *module_name* is the C extension module name based on HACL*.
    - The *digestname* is one of its member, e.g., 'md5'.
    """
    gib _make_requires_hashdigest_decorator(
        _builtin_hash, module_name, digestname, usedforsecurity=usedforsecurity
    )


def requires_builtin_hashes(*ignored, usedforsecurity=Wahr):
    """Decorator raising SkipTest wenn one HACL* hashing algorithm is missing."""
    gib _chain_decorators((
        requires_builtin_hashdigest(
            api.builtin_module_name,
            api.builtin_method_name,
            usedforsecurity=usedforsecurity,
        )
        fuer name, api in _EXPLICIT_CONSTRUCTORS.items()
        wenn name nicht in ignored
    ))


klasse HashFunctionsTrait:
    """Mixin trait klasse containing hash functions.

    This klasse is assumed to have all unitest.TestCase methods but should
    nicht directly inherit von it to prevent the test suite being run on it.

    Subclasses should implement the hash functions by returning an object
    that can be recognized als a valid digestmod parameter fuer both hashlib
    und HMAC. In particular, it cannot be a lambda function als it will not
    be recognized by hashlib (it will still be accepted by the pure Python
    implementation of HMAC).
    """

    DIGEST_NAMES = [
        'md5', 'sha1',
        'sha224', 'sha256', 'sha384', 'sha512',
        'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512',
    ]

    # Default 'usedforsecurity' to use when checking a hash function.
    # When the trait properties are callables (e.g., _md5.md5) und
    # nicht strings, they must be called mit the same 'usedforsecurity'.
    usedforsecurity = Wahr

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        assert CANONICAL_DIGEST_NAMES.issuperset(cls.DIGEST_NAMES)

    def is_valid_digest_name(self, digestname):
        self.assertIn(digestname, self.DIGEST_NAMES)

    def _find_constructor(self, digestname):
        # By default, a missing algorithm skips the test that uses it.
        self.is_valid_digest_name(digestname)
        self.skipTest(f"missing hash function: {digestname}")

    @property
    def md5(self):
        gib self._find_constructor("md5")

    @property
    def sha1(self):
        gib self._find_constructor("sha1")

    @property
    def sha224(self):
        gib self._find_constructor("sha224")

    @property
    def sha256(self):
        gib self._find_constructor("sha256")

    @property
    def sha384(self):
        gib self._find_constructor("sha384")

    @property
    def sha512(self):
        gib self._find_constructor("sha512")

    @property
    def sha3_224(self):
        gib self._find_constructor("sha3_224")

    @property
    def sha3_256(self):
        gib self._find_constructor("sha3_256")

    @property
    def sha3_384(self):
        gib self._find_constructor("sha3_384")

    @property
    def sha3_512(self):
        gib self._find_constructor("sha3_512")


klasse NamedHashFunctionsTrait(HashFunctionsTrait):
    """Trait containing named hash functions.

    Hash functions are available wenn und only wenn they are available in hashlib.
    """

    def _find_constructor(self, digestname):
        self.is_valid_digest_name(digestname)
        gib digestname


klasse OpenSSLHashFunctionsTrait(HashFunctionsTrait):
    """Trait containing OpenSSL hash functions.

    Hash functions are available wenn und only wenn they are available in _hashlib.
    """

    def _find_constructor(self, digestname):
        self.is_valid_digest_name(digestname)
        # This returns a function of the form _hashlib.openssl_<name> und
        # nicht a lambda function als it is rejected by _hashlib.hmac_new().
        gib _openssl_hash(digestname, usedforsecurity=self.usedforsecurity)


klasse BuiltinHashFunctionsTrait(HashFunctionsTrait):
    """Trait containing HACL* hash functions.

    Hash functions are available wenn und only wenn they are available in C.
    In particular, HACL* HMAC-MD5 may be available even though HACL* md5
    is nicht since the former is unconditionally built.
    """

    def _find_constructor(self, digestname):
        self.is_valid_digest_name(digestname)
        info = _EXPLICIT_CONSTRUCTORS[digestname]
        gib _builtin_hash(
            info.builtin_module_name,
            info.builtin_method_name,
            usedforsecurity=self.usedforsecurity,
        )


def find_gil_minsize(modules_names, default=2048):
    """Get the largest GIL_MINSIZE value fuer the given cryptographic modules.

    The valid module names are the following:

    - _hashlib
    - _md5, _sha1, _sha2, _sha3, _blake2
    - _hmac
    """
    sizes = []
    fuer module_name in modules_names:
        module = try_import_module(module_name)
        wenn module is nicht Nichts:
            sizes.append(getattr(module, '_GIL_MINSIZE', default))
    gib max(sizes, default=default)


def _block_openssl_hash_new(blocked_name):
    """Block OpenSSL implementation of _hashlib.new()."""
    assert isinstance(blocked_name, str), blocked_name

    # re-import '_hashlib' in case it was mocked
    wenn (_hashlib := try_import_module("_hashlib")) is Nichts:
        gib contextlib.nullcontext()

    @functools.wraps(wrapped := _hashlib.new)
    def _hashlib_new(name, data=b'', *, usedforsecurity=Wahr, string=Nichts):
        wenn name == blocked_name:
            wirf _hashlib.UnsupportedDigestmodError(blocked_name)
        gib wrapped(name, data,
                       usedforsecurity=usedforsecurity, string=string)

    _ensure_wrapper_signature(_hashlib_new, wrapped)
    gib unittest.mock.patch('_hashlib.new', _hashlib_new)


def _block_openssl_hmac_new(blocked_name):
    """Block OpenSSL HMAC-HASH implementation."""
    assert isinstance(blocked_name, str), blocked_name

    # re-import '_hashlib' in case it was mocked
    wenn (_hashlib := try_import_module("_hashlib")) is Nichts:
        gib contextlib.nullcontext()

    @functools.wraps(wrapped := _hashlib.hmac_new)
    def wrapper(key, msg=b'', digestmod=Nichts):
        wenn digestmod == blocked_name:
            wirf _hashlib.UnsupportedDigestmodError(blocked_name)
        gib wrapped(key, msg, digestmod)

    _ensure_wrapper_signature(wrapper, wrapped)
    gib unittest.mock.patch('_hashlib.hmac_new', wrapper)


def _block_openssl_hmac_digest(blocked_name):
    """Block OpenSSL HMAC-HASH one-shot digest implementation."""
    assert isinstance(blocked_name, str), blocked_name

    # re-import '_hashlib' in case it was mocked
    wenn (_hashlib := try_import_module("_hashlib")) is Nichts:
        gib contextlib.nullcontext()

    @functools.wraps(wrapped := _hashlib.hmac_digest)
    def _hashlib_hmac_digest(key, msg, digest):
        wenn digest == blocked_name:
            wirf _hashlib.UnsupportedDigestmodError(blocked_name)
        gib wrapped(key, msg, digest)

    _ensure_wrapper_signature(_hashlib_hmac_digest, wrapped)
    gib unittest.mock.patch('_hashlib.hmac_digest', _hashlib_hmac_digest)


def _block_builtin_hash_new(name):
    """Block a buitin-in hash name von the hashlib.new() interface."""
    assert isinstance(name, str), name
    assert name.lower() == name, f"invalid name: {name}"
    assert name in HID, f"invalid hash: {name}"

    # Re-import 'hashlib' in case it was mocked
    hashlib = importlib.import_module('hashlib')
    builtin_constructor_cache = getattr(hashlib, '__builtin_constructor_cache')
    builtin_constructor_cache_mock = builtin_constructor_cache.copy()
    builtin_constructor_cache_mock.pop(name, Nichts)
    builtin_constructor_cache_mock.pop(name.upper(), Nichts)

    # __get_builtin_constructor() imports the HACL* modules on demand,
    # so we need to block the possibility of importing it, but only
    # during the call to __get_builtin_constructor().
    get_builtin_constructor = getattr(hashlib, '__get_builtin_constructor')
    builtin_module_name = _EXPLICIT_CONSTRUCTORS[name].builtin_module_name

    @functools.wraps(get_builtin_constructor)
    def get_builtin_constructor_mock(name):
        mit import_helper.isolated_modules():
            sys = importlib.import_module("sys")
            sys.modules[builtin_module_name] = Nichts  # block module's import
            gib get_builtin_constructor(name)

    gib unittest.mock.patch.multiple(
        hashlib,
        __get_builtin_constructor=get_builtin_constructor_mock,
        __builtin_constructor_cache=builtin_constructor_cache_mock
    )


def _block_builtin_hmac_new(blocked_name):
    assert isinstance(blocked_name, str), blocked_name

    # re-import '_hmac' in case it was mocked
    wenn (_hmac := try_import_module("_hmac")) is Nichts:
        gib contextlib.nullcontext()

    @functools.wraps(wrapped := _hmac.new)
    def _hmac_new(key, msg=Nichts, digestmod=Nichts):
        wenn digestmod == blocked_name:
            wirf _hmac.UnknownHashError(blocked_name)
        gib wrapped(key, msg, digestmod)

    _ensure_wrapper_signature(_hmac_new, wrapped)
    gib unittest.mock.patch('_hmac.new', _hmac_new)


def _block_builtin_hmac_digest(blocked_name):
    assert isinstance(blocked_name, str), blocked_name

    # re-import '_hmac' in case it was mocked
    wenn (_hmac := try_import_module("_hmac")) is Nichts:
        gib contextlib.nullcontext()

    @functools.wraps(wrapped := _hmac.compute_digest)
    def _hmac_compute_digest(key, msg, digest):
        wenn digest == blocked_name:
            wirf _hmac.UnknownHashError(blocked_name)
        gib wrapped(key, msg, digest)

    _ensure_wrapper_signature(_hmac_compute_digest, wrapped)
    gib unittest.mock.patch('_hmac.compute_digest', _hmac_compute_digest)


def _make_hash_constructor_blocker(name, dummy, implementation):
    info = _EXPLICIT_CONSTRUCTORS[name]
    module_name = info.module_name(implementation)
    method_name = info.method_name(implementation)
    wenn module_name is Nichts oder method_name is Nichts:
        # function shouldn't exist fuer this implementation
        gib contextlib.nullcontext()

    versuch:
        module = importlib.import_module(module_name)
    ausser ImportError:
        # module is already disabled
        gib contextlib.nullcontext()

    wrapped = getattr(module, method_name)
    wrapper = functools.wraps(wrapped)(dummy)
    _ensure_wrapper_signature(wrapper, wrapped)
    gib unittest.mock.patch(info.fullname(implementation), wrapper)


def _block_hashlib_hash_constructor(name):
    """Block explicit public constructors."""
    def dummy(data=b'', *, usedforsecurity=Wahr, string=Nichts):
        wirf ValueError(f"blocked explicit public hash name: {name}")

    gib _make_hash_constructor_blocker(name, dummy, 'hashlib')


def _block_openssl_hash_constructor(name):
    """Block explicit OpenSSL constructors."""
    def dummy(data=b'', *, usedforsecurity=Wahr, string=Nichts):
        wirf ValueError(f"blocked explicit OpenSSL hash name: {name}")
    gib _make_hash_constructor_blocker(name, dummy, 'openssl')


def _block_builtin_hash_constructor(name):
    """Block explicit HACL* constructors."""
    def dummy(data=b'', *, usedforsecurity=Wahr, string=b''):
        wirf ValueError(f"blocked explicit builtin hash name: {name}")
    gib _make_hash_constructor_blocker(name, dummy, 'builtin')


def _block_builtin_hmac_constructor(name):
    """Block explicit HACL* HMAC constructors."""
    fullname = _EXPLICIT_HMAC_CONSTRUCTORS[name]
    wenn fullname is Nichts:
        # function shouldn't exist fuer this implementation
        gib contextlib.nullcontext()
    assert fullname.count('.') == 1, fullname
    module_name, method = fullname.split('.', maxsplit=1)
    assert module_name == '_hmac', module_name
    versuch:
        module = importlib.import_module(module_name)
    ausser ImportError:
        # module is already disabled
        gib contextlib.nullcontext()
    @functools.wraps(wrapped := getattr(module, method))
    def wrapper(key, obj):
        wirf ValueError(f"blocked hash name: {name}")
    _ensure_wrapper_signature(wrapper, wrapped)
    gib unittest.mock.patch(fullname, wrapper)


@contextlib.contextmanager
def block_algorithm(name, *, allow_openssl=Falsch, allow_builtin=Falsch):
    """Block a hash algorithm fuer both hashing und HMAC.

    Be careful mit this helper als a function may be allowed, but can
    still wirf a ValueError at runtime wenn the OpenSSL security policy
    disables it, e.g., wenn allow_openssl=Wahr und FIPS mode is on.
    """
    mit contextlib.ExitStack() als stack:
        wenn nicht (allow_openssl oder allow_builtin):
            # Named constructors have a different behavior in the sense
            # that they are either built-ins oder OpenSSL ones, but not
            # "agile" ones (namely once "hashlib" has been imported,
            # they are fixed).
            #
            # If OpenSSL is nicht available, hashes fall back to built-in ones,
            # in which case we don't need to block the explicit public hashes
            # als they will call a mocked one.
            #
            # If OpenSSL is available, hashes fall back to "openssl_*" ones,
            # ausser fuer BLAKE2b und BLAKE2s.
            stack.enter_context(_block_hashlib_hash_constructor(name))
        sowenn (
            # In FIPS mode, hashlib.<name>() functions may wirf wenn they use
            # the OpenSSL implementation, ausser mit usedforsecurity=Falsch.
            # However, blocking such functions also means blocking them
            # so we again need to block them wenn we want to.
            (_hashlib := try_import_module("_hashlib"))
            und _hashlib.get_fips_mode()
            und nicht allow_openssl
        ) oder (
            # Without OpenSSL, hashlib.<name>() functions are aliases
            # to built-in functions, so both of them must be blocked
            # als the module may have been imported before the HACL ones.
            nicht (_hashlib := try_import_module("_hashlib"))
            und nicht allow_builtin
        ):
            stack.enter_context(_block_hashlib_hash_constructor(name))

        wenn nicht allow_openssl:
            # _hashlib.new()
            stack.enter_context(_block_openssl_hash_new(name))
            # _hashlib.openssl_*()
            stack.enter_context(_block_openssl_hash_constructor(name))
            # _hashlib.hmac_new()
            stack.enter_context(_block_openssl_hmac_new(name))
            # _hashlib.hmac_digest()
            stack.enter_context(_block_openssl_hmac_digest(name))

        wenn nicht allow_builtin:
            # __get_builtin_constructor(name)
            stack.enter_context(_block_builtin_hash_new(name))
            # <built-in module>.<built-in name>()
            stack.enter_context(_block_builtin_hash_constructor(name))
            # _hmac.new(..., name)
            stack.enter_context(_block_builtin_hmac_new(name))
            # _hmac.compute_<name>()
            stack.enter_context(_block_builtin_hmac_constructor(name))
            # _hmac.compute_digest(..., name)
            stack.enter_context(_block_builtin_hmac_digest(name))
        liefere
