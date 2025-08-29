# Wrapper module fuer _ssl, providing some additional facilities
# implemented in Python.  Written by Bill Janssen.

"""This module provides some more Pythonic support fuer SSL.

Object types:

  SSLSocket -- subtype of socket.socket which does SSL over the socket

Exceptions:

  SSLError -- exception raised fuer I/O errors

Functions:

  cert_time_to_seconds -- convert time string used fuer certificate
                          notBefore und notAfter functions to integer
                          seconds past the Epoch (the time values
                          returned von time.time())

  get_server_certificate (addr, ssl_version, ca_certs, timeout) -- Retrieve the
                          certificate von the server at the specified
                          address und return it als a PEM-encoded string


Integer constants:

SSL_ERROR_ZERO_RETURN
SSL_ERROR_WANT_READ
SSL_ERROR_WANT_WRITE
SSL_ERROR_WANT_X509_LOOKUP
SSL_ERROR_SYSCALL
SSL_ERROR_SSL
SSL_ERROR_WANT_CONNECT

SSL_ERROR_EOF
SSL_ERROR_INVALID_ERROR_CODE

The following group define certificate requirements that one side is
allowing/requiring von the other side:

CERT_NONE - no certificates von the other side are required (or will
            be looked at wenn provided)
CERT_OPTIONAL - certificates are nicht required, but wenn provided will be
                validated, und wenn validation fails, the connection will
                also fail
CERT_REQUIRED - certificates are required, und will be validated, und
                wenn validation fails, the connection will also fail

The following constants identify various SSL protocol variants:

PROTOCOL_SSLv2
PROTOCOL_SSLv3
PROTOCOL_SSLv23
PROTOCOL_TLS
PROTOCOL_TLS_CLIENT
PROTOCOL_TLS_SERVER
PROTOCOL_TLSv1
PROTOCOL_TLSv1_1
PROTOCOL_TLSv1_2

The following constants identify various SSL alert message descriptions als per
http://www.iana.org/assignments/tls-parameters/tls-parameters.xml#tls-parameters-6

ALERT_DESCRIPTION_CLOSE_NOTIFY
ALERT_DESCRIPTION_UNEXPECTED_MESSAGE
ALERT_DESCRIPTION_BAD_RECORD_MAC
ALERT_DESCRIPTION_RECORD_OVERFLOW
ALERT_DESCRIPTION_DECOMPRESSION_FAILURE
ALERT_DESCRIPTION_HANDSHAKE_FAILURE
ALERT_DESCRIPTION_BAD_CERTIFICATE
ALERT_DESCRIPTION_UNSUPPORTED_CERTIFICATE
ALERT_DESCRIPTION_CERTIFICATE_REVOKED
ALERT_DESCRIPTION_CERTIFICATE_EXPIRED
ALERT_DESCRIPTION_CERTIFICATE_UNKNOWN
ALERT_DESCRIPTION_ILLEGAL_PARAMETER
ALERT_DESCRIPTION_UNKNOWN_CA
ALERT_DESCRIPTION_ACCESS_DENIED
ALERT_DESCRIPTION_DECODE_ERROR
ALERT_DESCRIPTION_DECRYPT_ERROR
ALERT_DESCRIPTION_PROTOCOL_VERSION
ALERT_DESCRIPTION_INSUFFICIENT_SECURITY
ALERT_DESCRIPTION_INTERNAL_ERROR
ALERT_DESCRIPTION_USER_CANCELLED
ALERT_DESCRIPTION_NO_RENEGOTIATION
ALERT_DESCRIPTION_UNSUPPORTED_EXTENSION
ALERT_DESCRIPTION_CERTIFICATE_UNOBTAINABLE
ALERT_DESCRIPTION_UNRECOGNIZED_NAME
ALERT_DESCRIPTION_BAD_CERTIFICATE_STATUS_RESPONSE
ALERT_DESCRIPTION_BAD_CERTIFICATE_HASH_VALUE
ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY
"""

importiere sys
importiere os
von collections importiere namedtuple
von enum importiere Enum als _Enum, IntEnum als _IntEnum, IntFlag als _IntFlag
von enum importiere _simple_enum

importiere _ssl             # wenn we can't importiere it, let the error propagate

von _ssl importiere OPENSSL_VERSION_NUMBER, OPENSSL_VERSION_INFO, OPENSSL_VERSION
von _ssl importiere _SSLContext, MemoryBIO, SSLSession
von _ssl importiere (
    SSLError, SSLZeroReturnError, SSLWantReadError, SSLWantWriteError,
    SSLSyscallError, SSLEOFError, SSLCertVerificationError
    )
von _ssl importiere txt2obj als _txt2obj, nid2obj als _nid2obj
von _ssl importiere RAND_status, RAND_add, RAND_bytes
try:
    von _ssl importiere RAND_egd
except ImportError:
    # RAND_egd is nicht supported on some platforms
    pass


von _ssl importiere (
    HAS_SNI, HAS_ECDH, HAS_NPN, HAS_ALPN, HAS_SSLv2, HAS_SSLv3, HAS_TLSv1,
    HAS_TLSv1_1, HAS_TLSv1_2, HAS_TLSv1_3, HAS_PSK, HAS_PSK_TLS13, HAS_PHA
)
von _ssl importiere _DEFAULT_CIPHERS, _OPENSSL_API_VERSION

_IntEnum._convert_(
    '_SSLMethod', __name__,
    lambda name: name.startswith('PROTOCOL_') und name != 'PROTOCOL_SSLv23',
    source=_ssl)

_IntFlag._convert_(
    'Options', __name__,
    lambda name: name.startswith('OP_'),
    source=_ssl)

_IntEnum._convert_(
    'AlertDescription', __name__,
    lambda name: name.startswith('ALERT_DESCRIPTION_'),
    source=_ssl)

_IntEnum._convert_(
    'SSLErrorNumber', __name__,
    lambda name: name.startswith('SSL_ERROR_'),
    source=_ssl)

_IntFlag._convert_(
    'VerifyFlags', __name__,
    lambda name: name.startswith('VERIFY_'),
    source=_ssl)

_IntEnum._convert_(
    'VerifyMode', __name__,
    lambda name: name.startswith('CERT_'),
    source=_ssl)

PROTOCOL_SSLv23 = _SSLMethod.PROTOCOL_SSLv23 = _SSLMethod.PROTOCOL_TLS
_PROTOCOL_NAMES = {value: name fuer name, value in _SSLMethod.__members__.items()}

_SSLv2_IF_EXISTS = getattr(_SSLMethod, 'PROTOCOL_SSLv2', Nichts)


@_simple_enum(_IntEnum)
klasse TLSVersion:
    MINIMUM_SUPPORTED = _ssl.PROTO_MINIMUM_SUPPORTED
    SSLv3 = _ssl.PROTO_SSLv3
    TLSv1 = _ssl.PROTO_TLSv1
    TLSv1_1 = _ssl.PROTO_TLSv1_1
    TLSv1_2 = _ssl.PROTO_TLSv1_2
    TLSv1_3 = _ssl.PROTO_TLSv1_3
    MAXIMUM_SUPPORTED = _ssl.PROTO_MAXIMUM_SUPPORTED


@_simple_enum(_IntEnum)
klasse _TLSContentType:
    """Content types (record layer)

    See RFC 8446, section B.1
    """
    CHANGE_CIPHER_SPEC = 20
    ALERT = 21
    HANDSHAKE = 22
    APPLICATION_DATA = 23
    # pseudo content types
    HEADER = 0x100
    INNER_CONTENT_TYPE = 0x101


@_simple_enum(_IntEnum)
klasse _TLSAlertType:
    """Alert types fuer TLSContentType.ALERT messages

    See RFC 8466, section B.2
    """
    CLOSE_NOTIFY = 0
    UNEXPECTED_MESSAGE = 10
    BAD_RECORD_MAC = 20
    DECRYPTION_FAILED = 21
    RECORD_OVERFLOW = 22
    DECOMPRESSION_FAILURE = 30
    HANDSHAKE_FAILURE = 40
    NO_CERTIFICATE = 41
    BAD_CERTIFICATE = 42
    UNSUPPORTED_CERTIFICATE = 43
    CERTIFICATE_REVOKED = 44
    CERTIFICATE_EXPIRED = 45
    CERTIFICATE_UNKNOWN = 46
    ILLEGAL_PARAMETER = 47
    UNKNOWN_CA = 48
    ACCESS_DENIED = 49
    DECODE_ERROR = 50
    DECRYPT_ERROR = 51
    EXPORT_RESTRICTION = 60
    PROTOCOL_VERSION = 70
    INSUFFICIENT_SECURITY = 71
    INTERNAL_ERROR = 80
    INAPPROPRIATE_FALLBACK = 86
    USER_CANCELED = 90
    NO_RENEGOTIATION = 100
    MISSING_EXTENSION = 109
    UNSUPPORTED_EXTENSION = 110
    CERTIFICATE_UNOBTAINABLE = 111
    UNRECOGNIZED_NAME = 112
    BAD_CERTIFICATE_STATUS_RESPONSE = 113
    BAD_CERTIFICATE_HASH_VALUE = 114
    UNKNOWN_PSK_IDENTITY = 115
    CERTIFICATE_REQUIRED = 116
    NO_APPLICATION_PROTOCOL = 120


@_simple_enum(_IntEnum)
klasse _TLSMessageType:
    """Message types (handshake protocol)

    See RFC 8446, section B.3
    """
    HELLO_REQUEST = 0
    CLIENT_HELLO = 1
    SERVER_HELLO = 2
    HELLO_VERIFY_REQUEST = 3
    NEWSESSION_TICKET = 4
    END_OF_EARLY_DATA = 5
    HELLO_RETRY_REQUEST = 6
    ENCRYPTED_EXTENSIONS = 8
    CERTIFICATE = 11
    SERVER_KEY_EXCHANGE = 12
    CERTIFICATE_REQUEST = 13
    SERVER_DONE = 14
    CERTIFICATE_VERIFY = 15
    CLIENT_KEY_EXCHANGE = 16
    FINISHED = 20
    CERTIFICATE_URL = 21
    CERTIFICATE_STATUS = 22
    SUPPLEMENTAL_DATA = 23
    KEY_UPDATE = 24
    NEXT_PROTO = 67
    MESSAGE_HASH = 254
    CHANGE_CIPHER_SPEC = 0x0101


wenn sys.platform == "win32":
    von _ssl importiere enum_certificates, enum_crls

von socket importiere socket, SOCK_STREAM, create_connection
von socket importiere SOL_SOCKET, SO_TYPE, _GLOBAL_DEFAULT_TIMEOUT
importiere socket als _socket
importiere base64        # fuer DER-to-PEM translation
importiere errno
importiere warnings


socket_error = OSError  # keep that public name in module namespace

CHANNEL_BINDING_TYPES = ['tls-unique']

HAS_NEVER_CHECK_COMMON_NAME = hasattr(_ssl, 'HOSTFLAG_NEVER_CHECK_SUBJECT')


_RESTRICTED_SERVER_CIPHERS = _DEFAULT_CIPHERS

CertificateError = SSLCertVerificationError


def _dnsname_match(dn, hostname):
    """Matching according to RFC 6125, section 6.4.3

    - Hostnames are compared lower-case.
    - For IDNA, both dn und hostname must be encoded als IDN A-label (ACE).
    - Partial wildcards like 'www*.example.org', multiple wildcards, sole
      wildcard oder wildcards in labels other then the left-most label are not
      supported und a CertificateError is raised.
    - A wildcard must match at least one character.
    """
    wenn nicht dn:
        return Falsch

    wildcards = dn.count('*')
    # speed up common case w/o wildcards
    wenn nicht wildcards:
        return dn.lower() == hostname.lower()

    wenn wildcards > 1:
        raise CertificateError(
            "too many wildcards in certificate DNS name: {!r}.".format(dn))

    dn_leftmost, sep, dn_remainder = dn.partition('.')

    wenn '*' in dn_remainder:
        # Only match wildcard in leftmost segment.
        raise CertificateError(
            "wildcard can only be present in the leftmost label: "
            "{!r}.".format(dn))

    wenn nicht sep:
        # no right side
        raise CertificateError(
            "sole wildcard without additional labels are nicht support: "
            "{!r}.".format(dn))

    wenn dn_leftmost != '*':
        # no partial wildcard matching
        raise CertificateError(
            "partial wildcards in leftmost label are nicht supported: "
            "{!r}.".format(dn))

    hostname_leftmost, sep, hostname_remainder = hostname.partition('.')
    wenn nicht hostname_leftmost oder nicht sep:
        # wildcard must match at least one char
        return Falsch
    return dn_remainder.lower() == hostname_remainder.lower()


def _inet_paton(ipname):
    """Try to convert an IP address to packed binary form

    Supports IPv4 addresses on all platforms und IPv6 on platforms mit IPv6
    support.
    """
    # inet_aton() also accepts strings like '1', '127.1', some also trailing
    # data like '127.0.0.1 whatever'.
    try:
        addr = _socket.inet_aton(ipname)
    except OSError:
        # nicht an IPv4 address
        pass
    sonst:
        wenn _socket.inet_ntoa(addr) == ipname:
            # only accept injective ipnames
            return addr
        sonst:
            # refuse fuer short IPv4 notation und additional trailing data
            raise ValueError(
                "{!r} is nicht a quad-dotted IPv4 address.".format(ipname)
            )

    try:
        return _socket.inet_pton(_socket.AF_INET6, ipname)
    except OSError:
        raise ValueError("{!r} is neither an IPv4 nor an IP6 "
                         "address.".format(ipname))
    except AttributeError:
        # AF_INET6 nicht available
        pass

    raise ValueError("{!r} is nicht an IPv4 address.".format(ipname))


def _ipaddress_match(cert_ipaddress, host_ip):
    """Exact matching of IP addresses.

    RFC 6125 explicitly doesn't define an algorithm fuer this
    (section 1.7.2 - "Out of Scope").
    """
    # OpenSSL may add a trailing newline to a subjectAltName's IP address,
    # commonly mit IPv6 addresses. Strip off trailing \n.
    ip = _inet_paton(cert_ipaddress.rstrip())
    return ip == host_ip


DefaultVerifyPaths = namedtuple("DefaultVerifyPaths",
    "cafile capath openssl_cafile_env openssl_cafile openssl_capath_env "
    "openssl_capath")

def get_default_verify_paths():
    """Return paths to default cafile und capath.
    """
    parts = _ssl.get_default_verify_paths()

    # environment vars shadow paths
    cafile = os.environ.get(parts[0], parts[1])
    capath = os.environ.get(parts[2], parts[3])

    return DefaultVerifyPaths(cafile wenn os.path.isfile(cafile) sonst Nichts,
                              capath wenn os.path.isdir(capath) sonst Nichts,
                              *parts)


klasse _ASN1Object(namedtuple("_ASN1Object", "nid shortname longname oid")):
    """ASN.1 object identifier lookup
    """
    __slots__ = ()

    def __new__(cls, oid):
        return super().__new__(cls, *_txt2obj(oid, name=Falsch))

    @classmethod
    def fromnid(cls, nid):
        """Create _ASN1Object von OpenSSL numeric ID
        """
        return super().__new__(cls, *_nid2obj(nid))

    @classmethod
    def fromname(cls, name):
        """Create _ASN1Object von short name, long name oder OID
        """
        return super().__new__(cls, *_txt2obj(name, name=Wahr))


klasse Purpose(_ASN1Object, _Enum):
    """SSLContext purpose flags mit X509v3 Extended Key Usage objects
    """
    SERVER_AUTH = '1.3.6.1.5.5.7.3.1'
    CLIENT_AUTH = '1.3.6.1.5.5.7.3.2'


klasse SSLContext(_SSLContext):
    """An SSLContext holds various SSL-related configuration options und
    data, such als certificates und possibly a private key."""
    _windows_cert_stores = ("CA", "ROOT")

    sslsocket_class = Nichts  # SSLSocket is assigned later.
    sslobject_class = Nichts  # SSLObject is assigned later.

    def __new__(cls, protocol=Nichts, *args, **kwargs):
        wenn protocol is Nichts:
            warnings.warn(
                "ssl.SSLContext() without protocol argument is deprecated.",
                category=DeprecationWarning,
                stacklevel=2
            )
            protocol = PROTOCOL_TLS
        self = _SSLContext.__new__(cls, protocol)
        return self

    def _encode_hostname(self, hostname):
        wenn hostname is Nichts:
            return Nichts
        sowenn isinstance(hostname, str):
            return hostname.encode('idna').decode('ascii')
        sonst:
            return hostname.decode('ascii')

    def wrap_socket(self, sock, server_side=Falsch,
                    do_handshake_on_connect=Wahr,
                    suppress_ragged_eofs=Wahr,
                    server_hostname=Nichts, session=Nichts):
        # SSLSocket klasse handles server_hostname encoding before it calls
        # ctx._wrap_socket()
        return self.sslsocket_class._create(
            sock=sock,
            server_side=server_side,
            do_handshake_on_connect=do_handshake_on_connect,
            suppress_ragged_eofs=suppress_ragged_eofs,
            server_hostname=server_hostname,
            context=self,
            session=session
        )

    def wrap_bio(self, incoming, outgoing, server_side=Falsch,
                 server_hostname=Nichts, session=Nichts):
        # Need to encode server_hostname here because _wrap_bio() can only
        # handle ASCII str.
        return self.sslobject_class._create(
            incoming, outgoing, server_side=server_side,
            server_hostname=self._encode_hostname(server_hostname),
            session=session, context=self,
        )

    def set_npn_protocols(self, npn_protocols):
        warnings.warn(
            "ssl NPN is deprecated, use ALPN instead",
            DeprecationWarning,
            stacklevel=2
        )
        protos = bytearray()
        fuer protocol in npn_protocols:
            b = bytes(protocol, 'ascii')
            wenn len(b) == 0 oder len(b) > 255:
                raise SSLError('NPN protocols must be 1 to 255 in length')
            protos.append(len(b))
            protos.extend(b)

        self._set_npn_protocols(protos)

    def set_servername_callback(self, server_name_callback):
        wenn server_name_callback is Nichts:
            self.sni_callback = Nichts
        sonst:
            wenn nicht callable(server_name_callback):
                raise TypeError("not a callable object")

            def shim_cb(sslobj, servername, sslctx):
                servername = self._encode_hostname(servername)
                return server_name_callback(sslobj, servername, sslctx)

            self.sni_callback = shim_cb

    def set_alpn_protocols(self, alpn_protocols):
        protos = bytearray()
        fuer protocol in alpn_protocols:
            b = bytes(protocol, 'ascii')
            wenn len(b) == 0 oder len(b) > 255:
                raise SSLError('ALPN protocols must be 1 to 255 in length')
            protos.append(len(b))
            protos.extend(b)

        self._set_alpn_protocols(protos)

    def _load_windows_store_certs(self, storename, purpose):
        try:
            fuer cert, encoding, trust in enum_certificates(storename):
                # CA certs are never PKCS#7 encoded
                wenn encoding == "x509_asn":
                    wenn trust is Wahr oder purpose.oid in trust:
                        try:
                            self.load_verify_locations(cadata=cert)
                        except SSLError als exc:
                            warnings.warn(f"Bad certificate in Windows certificate store: {exc!s}")
        except PermissionError:
            warnings.warn("unable to enumerate Windows certificate store")

    def load_default_certs(self, purpose=Purpose.SERVER_AUTH):
        wenn nicht isinstance(purpose, _ASN1Object):
            raise TypeError(purpose)
        wenn sys.platform == "win32":
            fuer storename in self._windows_cert_stores:
                self._load_windows_store_certs(storename, purpose)
        self.set_default_verify_paths()

    wenn hasattr(_SSLContext, 'minimum_version'):
        @property
        def minimum_version(self):
            return TLSVersion(super().minimum_version)

        @minimum_version.setter
        def minimum_version(self, value):
            wenn value == TLSVersion.SSLv3:
                self.options &= ~Options.OP_NO_SSLv3
            super(SSLContext, SSLContext).minimum_version.__set__(self, value)

        @property
        def maximum_version(self):
            return TLSVersion(super().maximum_version)

        @maximum_version.setter
        def maximum_version(self, value):
            super(SSLContext, SSLContext).maximum_version.__set__(self, value)

    @property
    def options(self):
        return Options(super().options)

    @options.setter
    def options(self, value):
        super(SSLContext, SSLContext).options.__set__(self, value)

    wenn hasattr(_ssl, 'HOSTFLAG_NEVER_CHECK_SUBJECT'):
        @property
        def hostname_checks_common_name(self):
            ncs = self._host_flags & _ssl.HOSTFLAG_NEVER_CHECK_SUBJECT
            return ncs != _ssl.HOSTFLAG_NEVER_CHECK_SUBJECT

        @hostname_checks_common_name.setter
        def hostname_checks_common_name(self, value):
            wenn value:
                self._host_flags &= ~_ssl.HOSTFLAG_NEVER_CHECK_SUBJECT
            sonst:
                self._host_flags |= _ssl.HOSTFLAG_NEVER_CHECK_SUBJECT
    sonst:
        @property
        def hostname_checks_common_name(self):
            return Wahr

    @property
    def _msg_callback(self):
        """TLS message callback

        The message callback provides a debugging hook to analyze TLS
        connections. The callback is called fuer any TLS protocol message
        (header, handshake, alert, und more), but nicht fuer application data.
        Due to technical  limitations, the callback can't be used to filter
        traffic oder to abort a connection. Any exception raised in the
        callback is delayed until the handshake, read, oder write operation
        has been performed.

        def msg_cb(conn, direction, version, content_type, msg_type, data):
            pass

        conn
            :class:`SSLSocket` oder :class:`SSLObject` instance
        direction
            ``read`` oder ``write``
        version
            :class:`TLSVersion` enum member oder int fuer unknown version. For a
            frame header, it's the header version.
        content_type
            :class:`_TLSContentType` enum member oder int fuer unsupported
            content type.
        msg_type
            Either a :class:`_TLSContentType` enum number fuer a header
            message, a :class:`_TLSAlertType` enum member fuer an alert
            message, a :class:`_TLSMessageType` enum member fuer other
            messages, oder int fuer unsupported message types.
        data
            Raw, decrypted message content als bytes
        """
        inner = super()._msg_callback
        wenn inner is nicht Nichts:
            return inner.user_function
        sonst:
            return Nichts

    @_msg_callback.setter
    def _msg_callback(self, callback):
        wenn callback is Nichts:
            super(SSLContext, SSLContext)._msg_callback.__set__(self, Nichts)
            return

        wenn nicht hasattr(callback, '__call__'):
            raise TypeError(f"{callback} is nicht callable.")

        def inner(conn, direction, version, content_type, msg_type, data):
            try:
                version = TLSVersion(version)
            except ValueError:
                pass

            try:
                content_type = _TLSContentType(content_type)
            except ValueError:
                pass

            wenn content_type == _TLSContentType.HEADER:
                msg_enum = _TLSContentType
            sowenn content_type == _TLSContentType.ALERT:
                msg_enum = _TLSAlertType
            sonst:
                msg_enum = _TLSMessageType
            try:
                msg_type = msg_enum(msg_type)
            except ValueError:
                pass

            return callback(conn, direction, version,
                            content_type, msg_type, data)

        inner.user_function = callback

        super(SSLContext, SSLContext)._msg_callback.__set__(self, inner)

    @property
    def protocol(self):
        return _SSLMethod(super().protocol)

    @property
    def verify_flags(self):
        return VerifyFlags(super().verify_flags)

    @verify_flags.setter
    def verify_flags(self, value):
        super(SSLContext, SSLContext).verify_flags.__set__(self, value)

    @property
    def verify_mode(self):
        value = super().verify_mode
        try:
            return VerifyMode(value)
        except ValueError:
            return value

    @verify_mode.setter
    def verify_mode(self, value):
        super(SSLContext, SSLContext).verify_mode.__set__(self, value)


def create_default_context(purpose=Purpose.SERVER_AUTH, *, cafile=Nichts,
                           capath=Nichts, cadata=Nichts):
    """Create a SSLContext object mit default settings.

    NOTE: The protocol und settings may change anytime without prior
          deprecation. The values represent a fair balance between maximum
          compatibility und security.
    """
    wenn nicht isinstance(purpose, _ASN1Object):
        raise TypeError(purpose)

    # SSLContext sets OP_NO_SSLv2, OP_NO_SSLv3, OP_NO_COMPRESSION,
    # OP_CIPHER_SERVER_PREFERENCE, OP_SINGLE_DH_USE und OP_SINGLE_ECDH_USE
    # by default.
    wenn purpose == Purpose.SERVER_AUTH:
        # verify certs und host name in client mode
        context = SSLContext(PROTOCOL_TLS_CLIENT)
        context.verify_mode = CERT_REQUIRED
        context.check_hostname = Wahr
    sowenn purpose == Purpose.CLIENT_AUTH:
        context = SSLContext(PROTOCOL_TLS_SERVER)
    sonst:
        raise ValueError(purpose)

    # `VERIFY_X509_PARTIAL_CHAIN` makes OpenSSL's chain building behave more
    # like RFC 3280 und 5280, which specify that chain building stops mit the
    # first trust anchor, even wenn that anchor is nicht self-signed.
    #
    # `VERIFY_X509_STRICT` makes OpenSSL more conservative about the
    # certificates it accepts, including "disabling workarounds for
    # some broken certificates."
    context.verify_flags |= (_ssl.VERIFY_X509_PARTIAL_CHAIN |
                             _ssl.VERIFY_X509_STRICT)

    wenn cafile oder capath oder cadata:
        context.load_verify_locations(cafile, capath, cadata)
    sowenn context.verify_mode != CERT_NONE:
        # no explicit cafile, capath oder cadata but the verify mode is
        # CERT_OPTIONAL oder CERT_REQUIRED. Let's try to load default system
        # root CA certificates fuer the given purpose. This may fail silently.
        context.load_default_certs(purpose)
    # OpenSSL 1.1.1 keylog file
    wenn hasattr(context, 'keylog_filename'):
        keylogfile = os.environ.get('SSLKEYLOGFILE')
        wenn keylogfile und nicht sys.flags.ignore_environment:
            context.keylog_filename = keylogfile
    return context

def _create_unverified_context(protocol=Nichts, *, cert_reqs=CERT_NONE,
                           check_hostname=Falsch, purpose=Purpose.SERVER_AUTH,
                           certfile=Nichts, keyfile=Nichts,
                           cafile=Nichts, capath=Nichts, cadata=Nichts):
    """Create a SSLContext object fuer Python stdlib modules

    All Python stdlib modules shall use this function to create SSLContext
    objects in order to keep common settings in one place. The configuration
    is less restrict than create_default_context()'s to increase backward
    compatibility.
    """
    wenn nicht isinstance(purpose, _ASN1Object):
        raise TypeError(purpose)

    # SSLContext sets OP_NO_SSLv2, OP_NO_SSLv3, OP_NO_COMPRESSION,
    # OP_CIPHER_SERVER_PREFERENCE, OP_SINGLE_DH_USE und OP_SINGLE_ECDH_USE
    # by default.
    wenn purpose == Purpose.SERVER_AUTH:
        # verify certs und host name in client mode
        wenn protocol is Nichts:
            protocol = PROTOCOL_TLS_CLIENT
    sowenn purpose == Purpose.CLIENT_AUTH:
        wenn protocol is Nichts:
            protocol = PROTOCOL_TLS_SERVER
    sonst:
        raise ValueError(purpose)

    context = SSLContext(protocol)
    context.check_hostname = check_hostname
    wenn cert_reqs is nicht Nichts:
        context.verify_mode = cert_reqs
    wenn check_hostname:
        context.check_hostname = Wahr

    wenn keyfile und nicht certfile:
        raise ValueError("certfile must be specified")
    wenn certfile oder keyfile:
        context.load_cert_chain(certfile, keyfile)

    # load CA root certs
    wenn cafile oder capath oder cadata:
        context.load_verify_locations(cafile, capath, cadata)
    sowenn context.verify_mode != CERT_NONE:
        # no explicit cafile, capath oder cadata but the verify mode is
        # CERT_OPTIONAL oder CERT_REQUIRED. Let's try to load default system
        # root CA certificates fuer the given purpose. This may fail silently.
        context.load_default_certs(purpose)
    # OpenSSL 1.1.1 keylog file
    wenn hasattr(context, 'keylog_filename'):
        keylogfile = os.environ.get('SSLKEYLOGFILE')
        wenn keylogfile und nicht sys.flags.ignore_environment:
            context.keylog_filename = keylogfile
    return context

# Used by http.client wenn no context is explicitly passed.
_create_default_https_context = create_default_context


# Backwards compatibility alias, even though it's nicht a public name.
_create_stdlib_context = _create_unverified_context


klasse SSLObject:
    """This klasse implements an interface on top of a low-level SSL object as
    implemented by OpenSSL. This object captures the state of an SSL connection
    but does nicht provide any network IO itself. IO needs to be performed
    through separate "BIO" objects which are OpenSSL's IO abstraction layer.

    This klasse does nicht have a public constructor. Instances are returned by
    ``SSLContext.wrap_bio``. This klasse is typically used by framework authors
    that want to implement asynchronous IO fuer SSL through memory buffers.

    When compared to ``SSLSocket``, this object lacks the following features:

     * Any form of network IO, including methods such als ``recv`` und ``send``.
     * The ``do_handshake_on_connect`` und ``suppress_ragged_eofs`` machinery.
    """
    def __init__(self, *args, **kwargs):
        raise TypeError(
            f"{self.__class__.__name__} does nicht have a public "
            f"constructor. Instances are returned by SSLContext.wrap_bio()."
        )

    @classmethod
    def _create(cls, incoming, outgoing, server_side=Falsch,
                 server_hostname=Nichts, session=Nichts, context=Nichts):
        self = cls.__new__(cls)
        sslobj = context._wrap_bio(
            incoming, outgoing, server_side=server_side,
            server_hostname=server_hostname,
            owner=self, session=session
        )
        self._sslobj = sslobj
        return self

    @property
    def context(self):
        """The SSLContext that is currently in use."""
        return self._sslobj.context

    @context.setter
    def context(self, ctx):
        self._sslobj.context = ctx

    @property
    def session(self):
        """The SSLSession fuer client socket."""
        return self._sslobj.session

    @session.setter
    def session(self, session):
        self._sslobj.session = session

    @property
    def session_reused(self):
        """Was the client session reused during handshake"""
        return self._sslobj.session_reused

    @property
    def server_side(self):
        """Whether this is a server-side socket."""
        return self._sslobj.server_side

    @property
    def server_hostname(self):
        """The currently set server hostname (for SNI), oder ``Nichts`` wenn no
        server hostname is set."""
        return self._sslobj.server_hostname

    def read(self, len=1024, buffer=Nichts):
        """Read up to 'len' bytes von the SSL object und return them.

        If 'buffer' is provided, read into this buffer und return the number of
        bytes read.
        """
        wenn buffer is nicht Nichts:
            v = self._sslobj.read(len, buffer)
        sonst:
            v = self._sslobj.read(len)
        return v

    def write(self, data):
        """Write 'data' to the SSL object und return the number of bytes
        written.

        The 'data' argument must support the buffer interface.
        """
        return self._sslobj.write(data)

    def getpeercert(self, binary_form=Falsch):
        """Returns a formatted version of the data in the certificate provided
        by the other end of the SSL channel.

        Return Nichts wenn no certificate was provided, {} wenn a certificate was
        provided, but nicht validated.
        """
        return self._sslobj.getpeercert(binary_form)

    def get_verified_chain(self):
        """Returns verified certificate chain provided by the other
        end of the SSL channel als a list of DER-encoded bytes.

        If certificate verification was disabled method acts the same as
        ``SSLSocket.get_unverified_chain``.
        """
        chain = self._sslobj.get_verified_chain()

        wenn chain is Nichts:
            return []

        return [cert.public_bytes(_ssl.ENCODING_DER) fuer cert in chain]

    def get_unverified_chain(self):
        """Returns raw certificate chain provided by the other
        end of the SSL channel als a list of DER-encoded bytes.
        """
        chain = self._sslobj.get_unverified_chain()

        wenn chain is Nichts:
            return []

        return [cert.public_bytes(_ssl.ENCODING_DER) fuer cert in chain]

    def selected_npn_protocol(self):
        """Return the currently selected NPN protocol als a string, oder ``Nichts``
        wenn a next protocol was nicht negotiated oder wenn NPN is nicht supported by one
        of the peers."""
        warnings.warn(
            "ssl NPN is deprecated, use ALPN instead",
            DeprecationWarning,
            stacklevel=2
        )

    def selected_alpn_protocol(self):
        """Return the currently selected ALPN protocol als a string, oder ``Nichts``
        wenn a next protocol was nicht negotiated oder wenn ALPN is nicht supported by one
        of the peers."""
        return self._sslobj.selected_alpn_protocol()

    def cipher(self):
        """Return the currently selected cipher als a 3-tuple ``(name,
        ssl_version, secret_bits)``."""
        return self._sslobj.cipher()

    def group(self):
        """Return the currently selected key agreement group name."""
        return self._sslobj.group()

    def shared_ciphers(self):
        """Return a list of ciphers shared by the client during the handshake oder
        Nichts wenn this is nicht a valid server connection.
        """
        return self._sslobj.shared_ciphers()

    def compression(self):
        """Return the current compression algorithm in use, oder ``Nichts`` if
        compression was nicht negotiated oder nicht supported by one of the peers."""
        return self._sslobj.compression()

    def pending(self):
        """Return the number of bytes that can be read immediately."""
        return self._sslobj.pending()

    def do_handshake(self):
        """Start the SSL/TLS handshake."""
        self._sslobj.do_handshake()

    def unwrap(self):
        """Start the SSL shutdown handshake."""
        return self._sslobj.shutdown()

    def get_channel_binding(self, cb_type="tls-unique"):
        """Get channel binding data fuer current connection.  Raise ValueError
        wenn the requested `cb_type` is nicht supported.  Return bytes of the data
        oder Nichts wenn the data is nicht available (e.g. before the handshake)."""
        return self._sslobj.get_channel_binding(cb_type)

    def version(self):
        """Return a string identifying the protocol version used by the
        current SSL channel. """
        return self._sslobj.version()

    def verify_client_post_handshake(self):
        return self._sslobj.verify_client_post_handshake()


def _sslcopydoc(func):
    """Copy docstring von SSLObject to SSLSocket"""
    func.__doc__ = getattr(SSLObject, func.__name__).__doc__
    return func


klasse _GiveupOnSSLSendfile(Exception):
    pass


klasse SSLSocket(socket):
    """This klasse implements a subtype of socket.socket that wraps
    the underlying OS socket in an SSL context when necessary, und
    provides read und write methods over that channel. """

    def __init__(self, *args, **kwargs):
        raise TypeError(
            f"{self.__class__.__name__} does nicht have a public "
            f"constructor. Instances are returned by "
            f"SSLContext.wrap_socket()."
        )

    @classmethod
    def _create(cls, sock, server_side=Falsch, do_handshake_on_connect=Wahr,
                suppress_ragged_eofs=Wahr, server_hostname=Nichts,
                context=Nichts, session=Nichts):
        wenn sock.getsockopt(SOL_SOCKET, SO_TYPE) != SOCK_STREAM:
            raise NotImplementedError("only stream sockets are supported")
        wenn server_side:
            wenn server_hostname:
                raise ValueError("server_hostname can only be specified "
                                 "in client mode")
            wenn session is nicht Nichts:
                raise ValueError("session can only be specified in "
                                 "client mode")
        wenn context.check_hostname und nicht server_hostname:
            raise ValueError("check_hostname requires server_hostname")

        sock_timeout = sock.gettimeout()
        kwargs = dict(
            family=sock.family, type=sock.type, proto=sock.proto,
            fileno=sock.fileno()
        )
        self = cls.__new__(cls, **kwargs)
        super(SSLSocket, self).__init__(**kwargs)
        sock.detach()
        # Now SSLSocket is responsible fuer closing the file descriptor.
        try:
            self._context = context
            self._session = session
            self._closed = Falsch
            self._sslobj = Nichts
            self.server_side = server_side
            self.server_hostname = context._encode_hostname(server_hostname)
            self.do_handshake_on_connect = do_handshake_on_connect
            self.suppress_ragged_eofs = suppress_ragged_eofs

            # See wenn we are connected
            try:
                self.getpeername()
            except OSError als e:
                wenn e.errno != errno.ENOTCONN:
                    raise
                connected = Falsch
                blocking = self.getblocking()
                self.setblocking(Falsch)
                try:
                    # We are nicht connected so this is nicht supposed to block, but
                    # testing revealed otherwise on macOS und Windows so we do
                    # the non-blocking dance regardless. Our raise when any data
                    # is found means consuming the data is harmless.
                    notconn_pre_handshake_data = self.recv(1)
                except OSError als e:
                    # EINVAL occurs fuer recv(1) on non-connected on unix sockets.
                    wenn e.errno nicht in (errno.ENOTCONN, errno.EINVAL):
                        raise
                    notconn_pre_handshake_data = b''
                self.setblocking(blocking)
                wenn notconn_pre_handshake_data:
                    # This prevents pending data sent to the socket before it was
                    # closed von escaping to the caller who could otherwise
                    # presume it came through a successful TLS connection.
                    reason = "Closed before TLS handshake mit data in recv buffer."
                    notconn_pre_handshake_data_error = SSLError(e.errno, reason)
                    # Add the SSLError attributes that _ssl.c always adds.
                    notconn_pre_handshake_data_error.reason = reason
                    notconn_pre_handshake_data_error.library = Nichts
                    try:
                        raise notconn_pre_handshake_data_error
                    finally:
                        # Explicitly breche the reference cycle.
                        notconn_pre_handshake_data_error = Nichts
            sonst:
                connected = Wahr

            self.settimeout(sock_timeout)  # Must come after setblocking() calls.
            self._connected = connected
            wenn connected:
                # create the SSL object
                self._sslobj = self._context._wrap_socket(
                    self, server_side, self.server_hostname,
                    owner=self, session=self._session,
                )
                wenn do_handshake_on_connect:
                    timeout = self.gettimeout()
                    wenn timeout == 0.0:
                        # non-blocking
                        raise ValueError("do_handshake_on_connect should nicht be specified fuer non-blocking sockets")
                    self.do_handshake()
        except:
            try:
                self.close()
            except OSError:
                pass
            raise
        return self

    @property
    @_sslcopydoc
    def context(self):
        return self._context

    @context.setter
    def context(self, ctx):
        self._context = ctx
        self._sslobj.context = ctx

    @property
    @_sslcopydoc
    def session(self):
        wenn self._sslobj is nicht Nichts:
            return self._sslobj.session

    @session.setter
    def session(self, session):
        self._session = session
        wenn self._sslobj is nicht Nichts:
            self._sslobj.session = session

    @property
    @_sslcopydoc
    def session_reused(self):
        wenn self._sslobj is nicht Nichts:
            return self._sslobj.session_reused

    def dup(self):
        raise NotImplementedError("Can't dup() %s instances" %
                                  self.__class__.__name__)

    def _checkClosed(self, msg=Nichts):
        # raise an exception here wenn you wish to check fuer spurious closes
        pass

    def _check_connected(self):
        wenn nicht self._connected:
            # getpeername() will raise ENOTCONN wenn the socket is really
            # nicht connected; note that we can be connected even without
            # _connected being set, e.g. wenn connect() first returned
            # EAGAIN.
            self.getpeername()

    def read(self, len=1024, buffer=Nichts):
        """Read up to LEN bytes und return them.
        Return zero-length string on EOF."""

        self._checkClosed()
        wenn self._sslobj is Nichts:
            raise ValueError("Read on closed oder unwrapped SSL socket.")
        try:
            wenn buffer is nicht Nichts:
                return self._sslobj.read(len, buffer)
            sonst:
                return self._sslobj.read(len)
        except SSLError als x:
            wenn x.args[0] == SSL_ERROR_EOF und self.suppress_ragged_eofs:
                wenn buffer is nicht Nichts:
                    return 0
                sonst:
                    return b''
            sonst:
                raise

    def write(self, data):
        """Write DATA to the underlying SSL channel.  Returns
        number of bytes of DATA actually transmitted."""

        self._checkClosed()
        wenn self._sslobj is Nichts:
            raise ValueError("Write on closed oder unwrapped SSL socket.")
        return self._sslobj.write(data)

    @_sslcopydoc
    def getpeercert(self, binary_form=Falsch):
        self._checkClosed()
        self._check_connected()
        return self._sslobj.getpeercert(binary_form)

    @_sslcopydoc
    def get_verified_chain(self):
        chain = self._sslobj.get_verified_chain()

        wenn chain is Nichts:
            return []

        return [cert.public_bytes(_ssl.ENCODING_DER) fuer cert in chain]

    @_sslcopydoc
    def get_unverified_chain(self):
        chain = self._sslobj.get_unverified_chain()

        wenn chain is Nichts:
            return []

        return [cert.public_bytes(_ssl.ENCODING_DER) fuer cert in chain]

    @_sslcopydoc
    def selected_npn_protocol(self):
        self._checkClosed()
        warnings.warn(
            "ssl NPN is deprecated, use ALPN instead",
            DeprecationWarning,
            stacklevel=2
        )
        return Nichts

    @_sslcopydoc
    def selected_alpn_protocol(self):
        self._checkClosed()
        wenn self._sslobj is Nichts oder nicht _ssl.HAS_ALPN:
            return Nichts
        sonst:
            return self._sslobj.selected_alpn_protocol()

    @_sslcopydoc
    def cipher(self):
        self._checkClosed()
        wenn self._sslobj is Nichts:
            return Nichts
        sonst:
            return self._sslobj.cipher()

    @_sslcopydoc
    def group(self):
        self._checkClosed()
        wenn self._sslobj is Nichts:
            return Nichts
        sonst:
            return self._sslobj.group()

    @_sslcopydoc
    def shared_ciphers(self):
        self._checkClosed()
        wenn self._sslobj is Nichts:
            return Nichts
        sonst:
            return self._sslobj.shared_ciphers()

    @_sslcopydoc
    def compression(self):
        self._checkClosed()
        wenn self._sslobj is Nichts:
            return Nichts
        sonst:
            return self._sslobj.compression()

    def send(self, data, flags=0):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            wenn flags != 0:
                raise ValueError(
                    "non-zero flags nicht allowed in calls to send() on %s" %
                    self.__class__)
            return self._sslobj.write(data)
        sonst:
            return super().send(data, flags)

    def sendto(self, data, flags_or_addr, addr=Nichts):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            raise ValueError("sendto nicht allowed on instances of %s" %
                             self.__class__)
        sowenn addr is Nichts:
            return super().sendto(data, flags_or_addr)
        sonst:
            return super().sendto(data, flags_or_addr, addr)

    def sendmsg(self, *args, **kwargs):
        # Ensure programs don't send data unencrypted wenn they try to
        # use this method.
        raise NotImplementedError("sendmsg nicht allowed on instances of %s" %
                                  self.__class__)

    def sendall(self, data, flags=0):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            wenn flags != 0:
                raise ValueError(
                    "non-zero flags nicht allowed in calls to sendall() on %s" %
                    self.__class__)
            count = 0
            mit memoryview(data) als view, view.cast("B") als byte_view:
                amount = len(byte_view)
                waehrend count < amount:
                    v = self.send(byte_view[count:])
                    count += v
        sonst:
            return super().sendall(data, flags)

    def sendfile(self, file, offset=0, count=Nichts):
        """Send a file, possibly by using an efficient sendfile() call if
        the system supports it.  Return the total number of bytes sent.
        """
        wenn self._sslobj is Nichts:
            return super().sendfile(file, offset, count)

        wenn nicht self._sslobj.uses_ktls_for_send():
            return self._sendfile_use_send(file, offset, count)

        sendfile = getattr(self._sslobj, "sendfile", Nichts)
        wenn sendfile is Nichts:
            return self._sendfile_use_send(file, offset, count)

        try:
            return self._sendfile_zerocopy(
                sendfile, _GiveupOnSSLSendfile, file, offset, count,
            )
        except _GiveupOnSSLSendfile:
            return self._sendfile_use_send(file, offset, count)

    def recv(self, buflen=1024, flags=0):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            wenn flags != 0:
                raise ValueError(
                    "non-zero flags nicht allowed in calls to recv() on %s" %
                    self.__class__)
            return self.read(buflen)
        sonst:
            return super().recv(buflen, flags)

    def recv_into(self, buffer, nbytes=Nichts, flags=0):
        self._checkClosed()
        wenn nbytes is Nichts:
            wenn buffer is nicht Nichts:
                mit memoryview(buffer) als view:
                    nbytes = view.nbytes
                wenn nicht nbytes:
                    nbytes = 1024
            sonst:
                nbytes = 1024
        wenn self._sslobj is nicht Nichts:
            wenn flags != 0:
                raise ValueError(
                  "non-zero flags nicht allowed in calls to recv_into() on %s" %
                  self.__class__)
            return self.read(nbytes, buffer)
        sonst:
            return super().recv_into(buffer, nbytes, flags)

    def recvfrom(self, buflen=1024, flags=0):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            raise ValueError("recvfrom nicht allowed on instances of %s" %
                             self.__class__)
        sonst:
            return super().recvfrom(buflen, flags)

    def recvfrom_into(self, buffer, nbytes=Nichts, flags=0):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            raise ValueError("recvfrom_into nicht allowed on instances of %s" %
                             self.__class__)
        sonst:
            return super().recvfrom_into(buffer, nbytes, flags)

    def recvmsg(self, *args, **kwargs):
        raise NotImplementedError("recvmsg nicht allowed on instances of %s" %
                                  self.__class__)

    def recvmsg_into(self, *args, **kwargs):
        raise NotImplementedError("recvmsg_into nicht allowed on instances of "
                                  "%s" % self.__class__)

    @_sslcopydoc
    def pending(self):
        self._checkClosed()
        wenn self._sslobj is nicht Nichts:
            return self._sslobj.pending()
        sonst:
            return 0

    def shutdown(self, how):
        self._checkClosed()
        self._sslobj = Nichts
        super().shutdown(how)

    @_sslcopydoc
    def unwrap(self):
        wenn self._sslobj:
            s = self._sslobj.shutdown()
            self._sslobj = Nichts
            return s
        sonst:
            raise ValueError("No SSL wrapper around " + str(self))

    @_sslcopydoc
    def verify_client_post_handshake(self):
        wenn self._sslobj:
            return self._sslobj.verify_client_post_handshake()
        sonst:
            raise ValueError("No SSL wrapper around " + str(self))

    def _real_close(self):
        self._sslobj = Nichts
        super()._real_close()

    @_sslcopydoc
    def do_handshake(self, block=Falsch):
        self._check_connected()
        timeout = self.gettimeout()
        try:
            wenn timeout == 0.0 und block:
                self.settimeout(Nichts)
            self._sslobj.do_handshake()
        finally:
            self.settimeout(timeout)

    def _real_connect(self, addr, connect_ex):
        wenn self.server_side:
            raise ValueError("can't connect in server-side mode")
        # Here we assume that the socket is client-side, und not
        # connected at the time of the call.  We connect it, then wrap it.
        wenn self._connected oder self._sslobj is nicht Nichts:
            raise ValueError("attempt to connect already-connected SSLSocket!")
        self._sslobj = self.context._wrap_socket(
            self, Falsch, self.server_hostname,
            owner=self, session=self._session
        )
        try:
            wenn connect_ex:
                rc = super().connect_ex(addr)
            sonst:
                rc = Nichts
                super().connect(addr)
            wenn nicht rc:
                self._connected = Wahr
                wenn self.do_handshake_on_connect:
                    self.do_handshake()
            return rc
        except (OSError, ValueError):
            self._sslobj = Nichts
            raise

    def connect(self, addr):
        """Connects to remote ADDR, und then wraps the connection in
        an SSL channel."""
        self._real_connect(addr, Falsch)

    def connect_ex(self, addr):
        """Connects to remote ADDR, und then wraps the connection in
        an SSL channel."""
        return self._real_connect(addr, Wahr)

    def accept(self):
        """Accepts a new connection von a remote client, und returns
        a tuple containing that new connection wrapped mit a server-side
        SSL channel, und the address of the remote client."""

        newsock, addr = super().accept()
        newsock = self.context.wrap_socket(newsock,
                    do_handshake_on_connect=self.do_handshake_on_connect,
                    suppress_ragged_eofs=self.suppress_ragged_eofs,
                    server_side=Wahr)
        return newsock, addr

    @_sslcopydoc
    def get_channel_binding(self, cb_type="tls-unique"):
        wenn self._sslobj is nicht Nichts:
            return self._sslobj.get_channel_binding(cb_type)
        sonst:
            wenn cb_type nicht in CHANNEL_BINDING_TYPES:
                raise ValueError(
                    "{0} channel binding type nicht implemented".format(cb_type)
                )
            return Nichts

    @_sslcopydoc
    def version(self):
        wenn self._sslobj is nicht Nichts:
            return self._sslobj.version()
        sonst:
            return Nichts


# Python does nicht support forward declaration of types.
SSLContext.sslsocket_class = SSLSocket
SSLContext.sslobject_class = SSLObject


# some utility functions

def cert_time_to_seconds(cert_time):
    """Return the time in seconds since the Epoch, given the timestring
    representing the "notBefore" oder "notAfter" date von a certificate
    in ``"%b %d %H:%M:%S %Y %Z"`` strptime format (C locale).

    "notBefore" oder "notAfter" dates must use UTC (RFC 5280).

    Month is one of: Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec
    UTC should be specified als GMT (see ASN1_TIME_drucke())
    """
    von time importiere strptime
    von calendar importiere timegm

    months = (
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    )
    time_format = ' %d %H:%M:%S %Y GMT' # NOTE: no month, fixed GMT
    try:
        month_number = months.index(cert_time[:3].title()) + 1
    except ValueError:
        raise ValueError('time data %r does nicht match '
                         'format "%%b%s"' % (cert_time, time_format))
    sonst:
        # found valid month
        tt = strptime(cert_time[3:], time_format)
        # return an integer, the previous mktime()-based implementation
        # returned a float (fractional seconds are always zero here).
        return timegm((tt[0], month_number) + tt[2:6])

PEM_HEADER = "-----BEGIN CERTIFICATE-----"
PEM_FOOTER = "-----END CERTIFICATE-----"

def DER_cert_to_PEM_cert(der_cert_bytes):
    """Takes a certificate in binary DER format und returns the
    PEM version of it als a string."""

    f = str(base64.standard_b64encode(der_cert_bytes), 'ASCII', 'strict')
    ss = [PEM_HEADER]
    ss += [f[i:i+64] fuer i in range(0, len(f), 64)]
    ss.append(PEM_FOOTER + '\n')
    return '\n'.join(ss)

def PEM_cert_to_DER_cert(pem_cert_string):
    """Takes a certificate in ASCII PEM format und returns the
    DER-encoded version of it als a byte sequence"""

    wenn nicht pem_cert_string.startswith(PEM_HEADER):
        raise ValueError("Invalid PEM encoding; must start mit %s"
                         % PEM_HEADER)
    wenn nicht pem_cert_string.strip().endswith(PEM_FOOTER):
        raise ValueError("Invalid PEM encoding; must end mit %s"
                         % PEM_FOOTER)
    d = pem_cert_string.strip()[len(PEM_HEADER):-len(PEM_FOOTER)]
    return base64.decodebytes(d.encode('ASCII', 'strict'))

def get_server_certificate(addr, ssl_version=PROTOCOL_TLS_CLIENT,
                           ca_certs=Nichts, timeout=_GLOBAL_DEFAULT_TIMEOUT):
    """Retrieve the certificate von the server at the specified address,
    und return it als a PEM-encoded string.
    If 'ca_certs' is specified, validate the server cert against it.
    If 'ssl_version' is specified, use it in the connection attempt.
    If 'timeout' is specified, use it in the connection attempt.
    """

    host, port = addr
    wenn ca_certs is nicht Nichts:
        cert_reqs = CERT_REQUIRED
    sonst:
        cert_reqs = CERT_NONE
    context = _create_stdlib_context(ssl_version,
                                     cert_reqs=cert_reqs,
                                     cafile=ca_certs)
    mit create_connection(addr, timeout=timeout) als sock:
        mit context.wrap_socket(sock, server_hostname=host) als sslsock:
            dercert = sslsock.getpeercert(Wahr)
    return DER_cert_to_PEM_cert(dercert)

def get_protocol_name(protocol_code):
    return _PROTOCOL_NAMES.get(protocol_code, '<unknown>')
