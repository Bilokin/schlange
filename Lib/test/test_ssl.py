# Test the support fuer SSL und sockets

importiere sys
importiere unittest
importiere unittest.mock
von ast importiere literal_eval
von threading importiere Thread
von test importiere support
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere socket_helper
von test.support importiere threading_helper
von test.support importiere warnings_helper
von test.support importiere asyncore
importiere array
importiere re
importiere socket
importiere select
importiere struct
importiere time
importiere enum
importiere gc
importiere http.client
importiere os
importiere errno
importiere pprint
importiere urllib.request
importiere threading
importiere traceback
importiere weakref
importiere platform
importiere sysconfig
importiere functools
von contextlib importiere nullcontext
versuch:
    importiere ctypes
ausser ImportError:
    ctypes = Nichts


ssl = import_helper.import_module("ssl")
importiere _ssl

von ssl importiere Purpose, TLSVersion, _TLSContentType, _TLSMessageType, _TLSAlertType

Py_DEBUG_WIN32 = support.Py_DEBUG und sys.platform == 'win32'

PROTOCOLS = sorted(ssl._PROTOCOL_NAMES)
HOST = socket_helper.HOST
IS_OPENSSL_3_0_0 = ssl.OPENSSL_VERSION_INFO >= (3, 0, 0)
CAN_GET_SELECTED_OPENSSL_GROUP = ssl.OPENSSL_VERSION_INFO >= (3, 2)
CAN_IGNORE_UNKNOWN_OPENSSL_GROUPS = ssl.OPENSSL_VERSION_INFO >= (3, 3)
CAN_GET_AVAILABLE_OPENSSL_GROUPS = ssl.OPENSSL_VERSION_INFO >= (3, 5)
PY_SSL_DEFAULT_CIPHERS = sysconfig.get_config_var('PY_SSL_DEFAULT_CIPHERS')

PROTOCOL_TO_TLS_VERSION = {}
fuer proto, ver in (
    ("PROTOCOL_SSLv3", "SSLv3"),
    ("PROTOCOL_TLSv1", "TLSv1"),
    ("PROTOCOL_TLSv1_1", "TLSv1_1"),
):
    versuch:
        proto = getattr(ssl, proto)
        ver = getattr(ssl.TLSVersion, ver)
    ausser AttributeError:
        weiter
    PROTOCOL_TO_TLS_VERSION[proto] = ver

def data_file(*name):
    gib os.path.join(os.path.dirname(__file__), "certdata", *name)

# The custom key und certificate files used in test_ssl are generated
# using Lib/test/certdata/make_ssl_certs.py.
# Other certificates are simply fetched von the internet servers they
# are meant to authenticate.

CERTFILE = data_file("keycert.pem")
BYTES_CERTFILE = os.fsencode(CERTFILE)
ONLYCERT = data_file("ssl_cert.pem")
ONLYKEY = data_file("ssl_key.pem")
BYTES_ONLYCERT = os.fsencode(ONLYCERT)
BYTES_ONLYKEY = os.fsencode(ONLYKEY)
CERTFILE_PROTECTED = data_file("keycert.passwd.pem")
ONLYKEY_PROTECTED = data_file("ssl_key.passwd.pem")
KEY_PASSWORD = "somepass"
CAPATH = data_file("capath")
BYTES_CAPATH = os.fsencode(CAPATH)
CAFILE_NEURONIO = data_file("capath", "4e1295a3.0")
CAFILE_CACERT = data_file("capath", "5ed36f99.0")

with open(data_file('keycert.pem.reference')) als file:
    CERTFILE_INFO = literal_eval(file.read())

# empty CRL
CRLFILE = data_file("revocation.crl")

# Two keys und certs signed by the same CA (for SNI tests)
SIGNED_CERTFILE = data_file("keycert3.pem")
SINGED_CERTFILE_ONLY = data_file("cert3.pem")
SIGNED_CERTFILE_HOSTNAME = 'localhost'

with open(data_file('keycert3.pem.reference')) als file:
    SIGNED_CERTFILE_INFO = literal_eval(file.read())

SIGNED_CERTFILE2 = data_file("keycert4.pem")
SIGNED_CERTFILE2_HOSTNAME = 'fakehostname'
SIGNED_CERTFILE_ECC = data_file("keycertecc.pem")
SIGNED_CERTFILE_ECC_HOSTNAME = 'localhost-ecc'

# A custom testcase, extracted von `rfc5280::aki::leaf-missing-aki` in x509-limbo:
# The leaf (server) certificate has no AKI, which ist forbidden under RFC 5280.
# See: https://x509-limbo.com/testcases/rfc5280/#rfc5280akileaf-missing-aki
LEAF_MISSING_AKI_CERTFILE = data_file("leaf-missing-aki.keycert.pem")
LEAF_MISSING_AKI_CERTFILE_HOSTNAME = "example.com"
LEAF_MISSING_AKI_CA = data_file("leaf-missing-aki.ca.pem")

# Same certificate als pycacert.pem, but without extra text in file
SIGNING_CA = data_file("capath", "ceff1710.0")
# cert mit all kinds of subject alt names
ALLSANFILE = data_file("allsans.pem")
IDNSANSFILE = data_file("idnsans.pem")
NOSANFILE = data_file("nosan.pem")
NOSAN_HOSTNAME = 'localhost'

REMOTE_HOST = "self-signed.pythontest.net"

EMPTYCERT = data_file("nullcert.pem")
BADCERT = data_file("badcert.pem")
NONEXISTINGCERT = data_file("XXXnonexisting.pem")
BADKEY = data_file("badkey.pem")
NOKIACERT = data_file("nokia.pem")
NULLBYTECERT = data_file("nullbytecert.pem")
TALOS_INVALID_CRLDP = data_file("talos-2019-0758.pem")

DHFILE = data_file("ffdh3072.pem")
BYTES_DHFILE = os.fsencode(DHFILE)

# Not defined in all versions of OpenSSL
OP_NO_COMPRESSION = getattr(ssl, "OP_NO_COMPRESSION", 0)
OP_SINGLE_DH_USE = getattr(ssl, "OP_SINGLE_DH_USE", 0)
OP_SINGLE_ECDH_USE = getattr(ssl, "OP_SINGLE_ECDH_USE", 0)
OP_CIPHER_SERVER_PREFERENCE = getattr(ssl, "OP_CIPHER_SERVER_PREFERENCE", 0)
OP_ENABLE_MIDDLEBOX_COMPAT = getattr(ssl, "OP_ENABLE_MIDDLEBOX_COMPAT", 0)

# Ubuntu has patched OpenSSL und changed behavior of security level 2
# see https://bugs.python.org/issue41561#msg389003
def is_ubuntu():
    versuch:
        # Assume that any references of "ubuntu" implies Ubuntu-like distro
        # The workaround ist nicht required fuer 18.04, but doesn't hurt either.
        mit open("/etc/os-release", encoding="utf-8") als f:
            gib "ubuntu" in f.read()
    ausser FileNotFoundError:
        gib Falsch

wenn is_ubuntu():
    def seclevel_workaround(*ctxs):
        """Lower security level to '1' und allow all ciphers fuer TLS 1.0/1"""
        fuer ctx in ctxs:
            wenn (
                hasattr(ctx, "minimum_version") und
                ctx.minimum_version <= ssl.TLSVersion.TLSv1_1 und
                ctx.security_level > 1
            ):
                ctx.set_ciphers("@SECLEVEL=1:ALL")
sonst:
    def seclevel_workaround(*ctxs):
        pass


def has_tls_protocol(protocol):
    """Check wenn a TLS protocol ist available und enabled

    :param protocol: enum ssl._SSLMethod member oder name
    :return: bool
    """
    wenn isinstance(protocol, str):
        assert protocol.startswith('PROTOCOL_')
        protocol = getattr(ssl, protocol, Nichts)
        wenn protocol ist Nichts:
            gib Falsch
    wenn protocol in {
        ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS_SERVER,
        ssl.PROTOCOL_TLS_CLIENT
    }:
        # auto-negotiate protocols are always available
        gib Wahr
    name = protocol.name
    gib has_tls_version(name[len('PROTOCOL_'):])


@functools.lru_cache
def has_tls_version(version):
    """Check wenn a TLS/SSL version ist enabled

    :param version: TLS version name oder ssl.TLSVersion member
    :return: bool
    """
    wenn isinstance(version, str):
        version = ssl.TLSVersion.__members__[version]

    # check compile time flags like ssl.HAS_TLSv1_2
    wenn nicht getattr(ssl, f'HAS_{version.name}'):
        gib Falsch

    wenn IS_OPENSSL_3_0_0 und version < ssl.TLSVersion.TLSv1_2:
        # bpo43791: 3.0.0-alpha14 fails mit TLSV1_ALERT_INTERNAL_ERROR
        gib Falsch

    # check runtime und dynamic crypto policy settings. A TLS version may
    # be compiled in but disabled by a policy oder config option.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    wenn (
            hasattr(ctx, 'minimum_version') und
            ctx.minimum_version != ssl.TLSVersion.MINIMUM_SUPPORTED und
            version < ctx.minimum_version
    ):
        gib Falsch
    wenn (
        hasattr(ctx, 'maximum_version') und
        ctx.maximum_version != ssl.TLSVersion.MAXIMUM_SUPPORTED und
        version > ctx.maximum_version
    ):
        gib Falsch

    gib Wahr


def requires_tls_version(version):
    """Decorator to skip tests when a required TLS version ist nicht available

    :param version: TLS version name oder ssl.TLSVersion member
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            wenn nicht has_tls_version(version):
                wirf unittest.SkipTest(f"{version} ist nicht available.")
            sonst:
                gib func(*args, **kw)
        gib wrapper
    gib decorator


def handle_error(prefix):
    exc_format = ' '.join(traceback.format_exception(sys.exception()))
    wenn support.verbose:
        sys.stdout.write(prefix + exc_format)


def utc_offset(): #NOTE: ignore issues like #1647654
    # local time = utc time + utc offset
    wenn time.daylight und time.localtime().tm_isdst > 0:
        gib -time.altzone  # seconds
    gib -time.timezone


ignore_deprecation = warnings_helper.ignore_warnings(
    category=DeprecationWarning
)


def test_wrap_socket(sock, *,
                     cert_reqs=ssl.CERT_NONE, ca_certs=Nichts,
                     ciphers=Nichts, certfile=Nichts, keyfile=Nichts,
                     **kwargs):
    wenn nicht kwargs.get("server_side"):
        kwargs["server_hostname"] = SIGNED_CERTFILE_HOSTNAME
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sonst:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    wenn cert_reqs ist nicht Nichts:
        wenn cert_reqs == ssl.CERT_NONE:
            context.check_hostname = Falsch
        context.verify_mode = cert_reqs
    wenn ca_certs ist nicht Nichts:
        context.load_verify_locations(ca_certs)
    wenn certfile ist nicht Nichts oder keyfile ist nicht Nichts:
        context.load_cert_chain(certfile, keyfile)
    wenn ciphers ist nicht Nichts:
        context.set_ciphers(ciphers)
    gib context.wrap_socket(sock, **kwargs)


USE_SAME_TEST_CONTEXT = Falsch
_TEST_CONTEXT = Nichts

def testing_context(server_cert=SIGNED_CERTFILE, *, server_chain=Wahr):
    """Create context

    client_context, server_context, hostname = testing_context()
    """
    global _TEST_CONTEXT
    wenn USE_SAME_TEST_CONTEXT:
        wenn _TEST_CONTEXT ist nicht Nichts:
            gib _TEST_CONTEXT

    wenn server_cert == SIGNED_CERTFILE:
        hostname = SIGNED_CERTFILE_HOSTNAME
    sowenn server_cert == SIGNED_CERTFILE2:
        hostname = SIGNED_CERTFILE2_HOSTNAME
    sowenn server_cert == NOSANFILE:
        hostname = NOSAN_HOSTNAME
    sonst:
        wirf ValueError(server_cert)

    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_context.load_verify_locations(SIGNING_CA)

    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(server_cert)
    wenn server_chain:
        server_context.load_verify_locations(SIGNING_CA)

    wenn USE_SAME_TEST_CONTEXT:
        wenn _TEST_CONTEXT ist nicht Nichts:
            _TEST_CONTEXT = client_context, server_context, hostname

    gib client_context, server_context, hostname


klasse BasicSocketTests(unittest.TestCase):

    def test_constants(self):
        ssl.CERT_NONE
        ssl.CERT_OPTIONAL
        ssl.CERT_REQUIRED
        ssl.OP_CIPHER_SERVER_PREFERENCE
        ssl.OP_SINGLE_DH_USE
        ssl.OP_SINGLE_ECDH_USE
        ssl.OP_NO_COMPRESSION
        self.assertEqual(ssl.HAS_SNI, Wahr)
        self.assertEqual(ssl.HAS_ECDH, Wahr)
        self.assertEqual(ssl.HAS_TLSv1_2, Wahr)
        self.assertEqual(ssl.HAS_TLSv1_3, Wahr)
        ssl.OP_NO_SSLv2
        ssl.OP_NO_SSLv3
        ssl.OP_NO_TLSv1
        ssl.OP_NO_TLSv1_3
        ssl.OP_NO_TLSv1_1
        ssl.OP_NO_TLSv1_2
        self.assertEqual(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv23)

    def test_options(self):
        # gh-106687: SSL options values are unsigned integer (uint64_t)
        fuer name in dir(ssl):
            wenn nicht name.startswith('OP_'):
                weiter
            mit self.subTest(option=name):
                value = getattr(ssl, name)
                self.assertGreaterEqual(value, 0, f"ssl.{name}")

    def test_ssl_types(self):
        ssl_types = [
            _ssl._SSLContext,
            _ssl._SSLSocket,
            _ssl.MemoryBIO,
            _ssl.Certificate,
            _ssl.SSLSession,
            _ssl.SSLError,
        ]
        fuer ssl_type in ssl_types:
            mit self.subTest(ssl_type=ssl_type):
                mit self.assertRaisesRegex(TypeError, "immutable type"):
                    ssl_type.value = Nichts
        support.check_disallow_instantiation(self, _ssl.Certificate)

    def test_private_init(self):
        mit self.assertRaisesRegex(TypeError, "public constructor"):
            mit socket.socket() als s:
                ssl.SSLSocket(s)

    def test_str_for_enums(self):
        # Make sure that the PROTOCOL_* constants have enum-like string
        # reprs.
        proto = ssl.PROTOCOL_TLS_CLIENT
        self.assertEqual(repr(proto), '<_SSLMethod.PROTOCOL_TLS_CLIENT: %r>' % proto.value)
        self.assertEqual(str(proto), str(proto.value))
        ctx = ssl.SSLContext(proto)
        self.assertIs(ctx.protocol, proto)

    def test_random(self):
        v = ssl.RAND_status()
        wenn support.verbose:
            sys.stdout.write("\n RAND_status ist %d (%s)\n"
                             % (v, (v und "sufficient randomness") oder
                                "insufficient randomness"))

        wenn v:
            data = ssl.RAND_bytes(16)
            self.assertEqual(len(data), 16)
        sonst:
            self.assertRaises(ssl.SSLError, ssl.RAND_bytes, 16)

        # negative num ist invalid
        self.assertRaises(ValueError, ssl.RAND_bytes, -5)

        ssl.RAND_add("this ist a random string", 75.0)
        ssl.RAND_add(b"this ist a random bytes object", 75.0)
        ssl.RAND_add(bytearray(b"this ist a random bytearray object"), 75.0)

    def test_parse_cert(self):
        self.maxDiff = Nichts
        # note that this uses an 'unofficial' function in _ssl.c,
        # provided solely fuer this test, to exercise the certificate
        # parsing code
        self.assertEqual(
            ssl._ssl._test_decode_cert(CERTFILE),
            CERTFILE_INFO
        )
        self.assertEqual(
            ssl._ssl._test_decode_cert(SIGNED_CERTFILE),
            SIGNED_CERTFILE_INFO
        )

        # Issue #13034: the subjectAltName in some certificates
        # (notably projects.developer.nokia.com:443) wasn't parsed
        p = ssl._ssl._test_decode_cert(NOKIACERT)
        wenn support.verbose:
            sys.stdout.write("\n" + pprint.pformat(p) + "\n")
        self.assertEqual(p['subjectAltName'],
                         (('DNS', 'projects.developer.nokia.com'),
                          ('DNS', 'projects.forum.nokia.com'))
                        )
        # extra OCSP und AIA fields
        self.assertEqual(p['OCSP'], ('http://ocsp.verisign.com',))
        self.assertEqual(p['caIssuers'],
                         ('http://SVRIntl-G3-aia.verisign.com/SVRIntlG3.cer',))
        self.assertEqual(p['crlDistributionPoints'],
                         ('http://SVRIntl-G3-crl.verisign.com/SVRIntlG3.crl',))

    def test_parse_cert_CVE_2019_5010(self):
        p = ssl._ssl._test_decode_cert(TALOS_INVALID_CRLDP)
        wenn support.verbose:
            sys.stdout.write("\n" + pprint.pformat(p) + "\n")
        self.assertEqual(
            p,
            {
                'issuer': (
                    (('countryName', 'UK'),), (('commonName', 'cody-ca'),)),
                'notAfter': 'Jun 14 18:00:58 2028 GMT',
                'notBefore': 'Jun 18 18:00:58 2018 GMT',
                'serialNumber': '02',
                'subject': ((('countryName', 'UK'),),
                            (('commonName',
                              'codenomicon-vm-2.test.lal.cisco.com'),)),
                'subjectAltName': (
                    ('DNS', 'codenomicon-vm-2.test.lal.cisco.com'),),
                'version': 3
            }
        )

    def test_parse_cert_CVE_2013_4238(self):
        p = ssl._ssl._test_decode_cert(NULLBYTECERT)
        wenn support.verbose:
            sys.stdout.write("\n" + pprint.pformat(p) + "\n")
        subject = ((('countryName', 'US'),),
                   (('stateOrProvinceName', 'Oregon'),),
                   (('localityName', 'Beaverton'),),
                   (('organizationName', 'Python Software Foundation'),),
                   (('organizationalUnitName', 'Python Core Development'),),
                   (('commonName', 'null.python.org\x00example.org'),),
                   (('emailAddress', 'python-dev@python.org'),))
        self.assertEqual(p['subject'], subject)
        self.assertEqual(p['issuer'], subject)
        wenn ssl._OPENSSL_API_VERSION >= (0, 9, 8):
            san = (('DNS', 'altnull.python.org\x00example.com'),
                   ('email', 'null@python.org\x00user@example.org'),
                   ('URI', 'http://null.python.org\x00http://example.org'),
                   ('IP Address', '192.0.2.1'),
                   ('IP Address', '2001:DB8:0:0:0:0:0:1'))
        sonst:
            # OpenSSL 0.9.7 doesn't support IPv6 addresses in subjectAltName
            san = (('DNS', 'altnull.python.org\x00example.com'),
                   ('email', 'null@python.org\x00user@example.org'),
                   ('URI', 'http://null.python.org\x00http://example.org'),
                   ('IP Address', '192.0.2.1'),
                   ('IP Address', '<invalid>'))

        self.assertEqual(p['subjectAltName'], san)

    def test_parse_all_sans(self):
        p = ssl._ssl._test_decode_cert(ALLSANFILE)
        self.assertEqual(p['subjectAltName'],
            (
                ('DNS', 'allsans'),
                ('othername', '<unsupported>'),
                ('othername', '<unsupported>'),
                ('email', 'user@example.org'),
                ('DNS', 'www.example.org'),
                ('DirName',
                    ((('countryName', 'XY'),),
                    (('localityName', 'Castle Anthrax'),),
                    (('organizationName', 'Python Software Foundation'),),
                    (('commonName', 'dirname example'),))),
                ('URI', 'https://www.python.org/'),
                ('IP Address', '127.0.0.1'),
                ('IP Address', '0:0:0:0:0:0:0:1'),
                ('Registered ID', '1.2.3.4.5')
            )
        )

    def test_DER_to_PEM(self):
        mit open(CAFILE_CACERT, 'r') als f:
            pem = f.read()
        d1 = ssl.PEM_cert_to_DER_cert(pem)
        p2 = ssl.DER_cert_to_PEM_cert(d1)
        d2 = ssl.PEM_cert_to_DER_cert(p2)
        self.assertEqual(d1, d2)
        wenn nicht p2.startswith(ssl.PEM_HEADER + '\n'):
            self.fail("DER-to-PEM didn't include correct header:\n%r\n" % p2)
        wenn nicht p2.endswith('\n' + ssl.PEM_FOOTER + '\n'):
            self.fail("DER-to-PEM didn't include correct footer:\n%r\n" % p2)

    def test_openssl_version(self):
        n = ssl.OPENSSL_VERSION_NUMBER
        t = ssl.OPENSSL_VERSION_INFO
        s = ssl.OPENSSL_VERSION
        self.assertIsInstance(n, int)
        self.assertIsInstance(t, tuple)
        self.assertIsInstance(s, str)
        # Some sanity checks follow
        # >= 1.1.1
        self.assertGreaterEqual(n, 0x10101000)
        # < 4.0
        self.assertLess(n, 0x40000000)
        major, minor, fix, patch, status = t
        self.assertGreaterEqual(major, 1)
        self.assertLess(major, 4)
        self.assertGreaterEqual(minor, 0)
        self.assertLess(minor, 256)
        self.assertGreaterEqual(fix, 0)
        self.assertLess(fix, 256)
        self.assertGreaterEqual(patch, 0)
        self.assertLessEqual(patch, 63)
        self.assertGreaterEqual(status, 0)
        self.assertLessEqual(status, 15)

        libressl_ver = f"LibreSSL {major:d}"
        wenn major >= 3:
            # 3.x uses 0xMNN00PP0L
            openssl_ver = f"OpenSSL {major:d}.{minor:d}.{patch:d}"
        sonst:
            openssl_ver = f"OpenSSL {major:d}.{minor:d}.{fix:d}"
        self.assertStartsWith(
            s, (openssl_ver, libressl_ver, "AWS-LC"),
            (t, hex(n))
        )

    @support.cpython_only
    def test_refcycle(self):
        # Issue #7943: an SSL object doesn't create reference cycles with
        # itself.
        s = socket.socket(socket.AF_INET)
        ss = test_wrap_socket(s)
        wr = weakref.ref(ss)
        mit warnings_helper.check_warnings(("", ResourceWarning)):
            loesche ss
        self.assertEqual(wr(), Nichts)

    def test_wrapped_unconnected(self):
        # Methods on an unconnected SSLSocket propagate the original
        # OSError wirf by the underlying socket object.
        s = socket.socket(socket.AF_INET)
        mit test_wrap_socket(s) als ss:
            self.assertRaises(OSError, ss.recv, 1)
            self.assertRaises(OSError, ss.recv_into, bytearray(b'x'))
            self.assertRaises(OSError, ss.recvfrom, 1)
            self.assertRaises(OSError, ss.recvfrom_into, bytearray(b'x'), 1)
            self.assertRaises(OSError, ss.send, b'x')
            self.assertRaises(OSError, ss.sendto, b'x', ('0.0.0.0', 0))
            self.assertRaises(NotImplementedError, ss.dup)
            self.assertRaises(NotImplementedError, ss.sendmsg,
                              [b'x'], (), 0, ('0.0.0.0', 0))
            self.assertRaises(NotImplementedError, ss.recvmsg, 100)
            self.assertRaises(NotImplementedError, ss.recvmsg_into,
                              [bytearray(100)])

    def test_timeout(self):
        # Issue #8524: when creating an SSL socket, the timeout of the
        # original socket should be retained.
        fuer timeout in (Nichts, 0.0, 5.0):
            s = socket.socket(socket.AF_INET)
            s.settimeout(timeout)
            mit test_wrap_socket(s) als ss:
                self.assertEqual(timeout, ss.gettimeout())

    def test_openssl111_deprecations(self):
        options = [
            ssl.OP_NO_TLSv1,
            ssl.OP_NO_TLSv1_1,
            ssl.OP_NO_TLSv1_2,
            ssl.OP_NO_TLSv1_3
        ]
        protocols = [
            ssl.PROTOCOL_TLSv1,
            ssl.PROTOCOL_TLSv1_1,
            ssl.PROTOCOL_TLSv1_2,
            ssl.PROTOCOL_TLS
        ]
        versions = [
            ssl.TLSVersion.SSLv3,
            ssl.TLSVersion.TLSv1,
            ssl.TLSVersion.TLSv1_1,
        ]

        fuer option in options:
            mit self.subTest(option=option):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                mit self.assertWarns(DeprecationWarning) als cm:
                    ctx.options |= option
                self.assertEqual(
                    'ssl.OP_NO_SSL*/ssl.OP_NO_TLS* options are deprecated',
                    str(cm.warning)
                )

        fuer protocol in protocols:
            wenn nicht has_tls_protocol(protocol):
                weiter
            mit self.subTest(protocol=protocol):
                mit self.assertWarns(DeprecationWarning) als cm:
                    ssl.SSLContext(protocol)
                self.assertEqual(
                    f'ssl.{protocol.name} ist deprecated',
                    str(cm.warning)
                )

        fuer version in versions:
            wenn nicht has_tls_version(version):
                weiter
            mit self.subTest(version=version):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                mit self.assertWarns(DeprecationWarning) als cm:
                    ctx.minimum_version = version
                version_text = '%s.%s' % (version.__class__.__name__, version.name)
                self.assertEqual(
                    f'ssl.{version_text} ist deprecated',
                    str(cm.warning)
                )

    def bad_cert_test(self, certfile):
        """Check that trying to use the given client certificate fails"""
        certfile = os.path.join(os.path.dirname(__file__) oder os.curdir,
                                "certdata", certfile)
        sock = socket.socket()
        self.addCleanup(sock.close)
        mit self.assertRaises(ssl.SSLError):
            test_wrap_socket(sock,
                             certfile=certfile)

    def test_empty_cert(self):
        """Wrapping mit an empty cert file"""
        self.bad_cert_test("nullcert.pem")

    def test_malformed_cert(self):
        """Wrapping mit a badly formatted certificate (syntax error)"""
        self.bad_cert_test("badcert.pem")

    def test_malformed_key(self):
        """Wrapping mit a badly formatted key (syntax error)"""
        self.bad_cert_test("badkey.pem")

    def test_server_side(self):
        # server_hostname doesn't work fuer server sockets
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        mit socket.socket() als sock:
            self.assertRaises(ValueError, ctx.wrap_socket, sock, Wahr,
                              server_hostname="some.hostname")

    def test_unknown_channel_binding(self):
        # should wirf ValueError fuer unknown type
        s = socket.create_server(('127.0.0.1', 0))
        c = socket.socket(socket.AF_INET)
        c.connect(s.getsockname())
        mit test_wrap_socket(c, do_handshake_on_connect=Falsch) als ss:
            mit self.assertRaises(ValueError):
                ss.get_channel_binding("unknown-type")
        s.close()

    @unittest.skipUnless("tls-unique" in ssl.CHANNEL_BINDING_TYPES,
                         "'tls-unique' channel binding nicht available")
    def test_tls_unique_channel_binding(self):
        # unconnected should gib Nichts fuer known type
        s = socket.socket(socket.AF_INET)
        mit test_wrap_socket(s) als ss:
            self.assertIsNichts(ss.get_channel_binding("tls-unique"))
        # the same fuer server-side
        s = socket.socket(socket.AF_INET)
        mit test_wrap_socket(s, server_side=Wahr, certfile=CERTFILE) als ss:
            self.assertIsNichts(ss.get_channel_binding("tls-unique"))

    def test_dealloc_warn(self):
        ss = test_wrap_socket(socket.socket(socket.AF_INET))
        r = repr(ss)
        mit self.assertWarns(ResourceWarning) als cm:
            ss = Nichts
            support.gc_collect()
        self.assertIn(r, str(cm.warning.args[0]))

    def test_get_default_verify_paths(self):
        paths = ssl.get_default_verify_paths()
        self.assertEqual(len(paths), 6)
        self.assertIsInstance(paths, ssl.DefaultVerifyPaths)

        mit os_helper.EnvironmentVarGuard() als env:
            env["SSL_CERT_DIR"] = CAPATH
            env["SSL_CERT_FILE"] = CERTFILE
            paths = ssl.get_default_verify_paths()
            self.assertEqual(paths.cafile, CERTFILE)
            self.assertEqual(paths.capath, CAPATH)

    @unittest.skipUnless(sys.platform == "win32", "Windows specific")
    def test_enum_certificates(self):
        self.assertWahr(ssl.enum_certificates("CA"))
        self.assertWahr(ssl.enum_certificates("ROOT"))

        self.assertRaises(TypeError, ssl.enum_certificates)
        self.assertRaises(WindowsError, ssl.enum_certificates, "")

        trust_oids = set()
        fuer storename in ("CA", "ROOT"):
            store = ssl.enum_certificates(storename)
            self.assertIsInstance(store, list)
            fuer element in store:
                self.assertIsInstance(element, tuple)
                self.assertEqual(len(element), 3)
                cert, enc, trust = element
                self.assertIsInstance(cert, bytes)
                self.assertIn(enc, {"x509_asn", "pkcs_7_asn"})
                self.assertIsInstance(trust, (frozenset, set, bool))
                wenn isinstance(trust, (frozenset, set)):
                    trust_oids.update(trust)

        serverAuth = "1.3.6.1.5.5.7.3.1"
        self.assertIn(serverAuth, trust_oids)

    @unittest.skipUnless(sys.platform == "win32", "Windows specific")
    def test_enum_crls(self):
        self.assertWahr(ssl.enum_crls("CA"))
        self.assertRaises(TypeError, ssl.enum_crls)
        self.assertRaises(WindowsError, ssl.enum_crls, "")

        crls = ssl.enum_crls("CA")
        self.assertIsInstance(crls, list)
        fuer element in crls:
            self.assertIsInstance(element, tuple)
            self.assertEqual(len(element), 2)
            self.assertIsInstance(element[0], bytes)
            self.assertIn(element[1], {"x509_asn", "pkcs_7_asn"})


    def test_asn1object(self):
        expected = (129, 'serverAuth', 'TLS Web Server Authentication',
                    '1.3.6.1.5.5.7.3.1')

        val = ssl._ASN1Object('1.3.6.1.5.5.7.3.1')
        self.assertEqual(val, expected)
        self.assertEqual(val.nid, 129)
        self.assertEqual(val.shortname, 'serverAuth')
        self.assertEqual(val.longname, 'TLS Web Server Authentication')
        self.assertEqual(val.oid, '1.3.6.1.5.5.7.3.1')
        self.assertIsInstance(val, ssl._ASN1Object)
        self.assertRaises(ValueError, ssl._ASN1Object, 'serverAuth')

        val = ssl._ASN1Object.fromnid(129)
        self.assertEqual(val, expected)
        self.assertIsInstance(val, ssl._ASN1Object)
        self.assertRaises(ValueError, ssl._ASN1Object.fromnid, -1)
        mit self.assertRaisesRegex(ValueError, "unknown NID 100000"):
            ssl._ASN1Object.fromnid(100000)
        fuer i in range(1000):
            versuch:
                obj = ssl._ASN1Object.fromnid(i)
            ausser ValueError:
                pass
            sonst:
                self.assertIsInstance(obj.nid, int)
                self.assertIsInstance(obj.shortname, str)
                self.assertIsInstance(obj.longname, str)
                self.assertIsInstance(obj.oid, (str, type(Nichts)))

        val = ssl._ASN1Object.fromname('TLS Web Server Authentication')
        self.assertEqual(val, expected)
        self.assertIsInstance(val, ssl._ASN1Object)
        self.assertEqual(ssl._ASN1Object.fromname('serverAuth'), expected)
        self.assertEqual(ssl._ASN1Object.fromname('1.3.6.1.5.5.7.3.1'),
                         expected)
        mit self.assertRaisesRegex(ValueError, "unknown object 'serverauth'"):
            ssl._ASN1Object.fromname('serverauth')

    def test_purpose_enum(self):
        val = ssl._ASN1Object('1.3.6.1.5.5.7.3.1')
        self.assertIsInstance(ssl.Purpose.SERVER_AUTH, ssl._ASN1Object)
        self.assertEqual(ssl.Purpose.SERVER_AUTH, val)
        self.assertEqual(ssl.Purpose.SERVER_AUTH.nid, 129)
        self.assertEqual(ssl.Purpose.SERVER_AUTH.shortname, 'serverAuth')
        self.assertEqual(ssl.Purpose.SERVER_AUTH.oid,
                              '1.3.6.1.5.5.7.3.1')

        val = ssl._ASN1Object('1.3.6.1.5.5.7.3.2')
        self.assertIsInstance(ssl.Purpose.CLIENT_AUTH, ssl._ASN1Object)
        self.assertEqual(ssl.Purpose.CLIENT_AUTH, val)
        self.assertEqual(ssl.Purpose.CLIENT_AUTH.nid, 130)
        self.assertEqual(ssl.Purpose.CLIENT_AUTH.shortname, 'clientAuth')
        self.assertEqual(ssl.Purpose.CLIENT_AUTH.oid,
                              '1.3.6.1.5.5.7.3.2')

    def test_unsupported_dtls(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(s.close)
        mit self.assertRaises(NotImplementedError) als cx:
            test_wrap_socket(s, cert_reqs=ssl.CERT_NONE)
        self.assertEqual(str(cx.exception), "only stream sockets are supported")
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        mit self.assertRaises(NotImplementedError) als cx:
            ctx.wrap_socket(s)
        self.assertEqual(str(cx.exception), "only stream sockets are supported")

    def cert_time_ok(self, timestring, timestamp):
        self.assertEqual(ssl.cert_time_to_seconds(timestring), timestamp)

    def cert_time_fail(self, timestring):
        mit self.assertRaises(ValueError):
            ssl.cert_time_to_seconds(timestring)

    @unittest.skipUnless(utc_offset(),
                         'local time needs to be different von UTC')
    def test_cert_time_to_seconds_timezone(self):
        # Issue #19940: ssl.cert_time_to_seconds() returns wrong
        #               results wenn local timezone ist nicht UTC
        self.cert_time_ok("May  9 00:00:00 2007 GMT", 1178668800.0)
        self.cert_time_ok("Jan  5 09:34:43 2018 GMT", 1515144883.0)

    def test_cert_time_to_seconds(self):
        timestring = "Jan  5 09:34:43 2018 GMT"
        ts = 1515144883.0
        self.cert_time_ok(timestring, ts)
        # accept keyword parameter, assert its name
        self.assertEqual(ssl.cert_time_to_seconds(cert_time=timestring), ts)
        # accept both %e und %d (space oder zero generated by strftime)
        self.cert_time_ok("Jan 05 09:34:43 2018 GMT", ts)
        # case-insensitive
        self.cert_time_ok("JaN  5 09:34:43 2018 GmT", ts)
        self.cert_time_fail("Jan  5 09:34 2018 GMT")     # no seconds
        self.cert_time_fail("Jan  5 09:34:43 2018")      # no GMT
        self.cert_time_fail("Jan  5 09:34:43 2018 UTC")  # nicht GMT timezone
        self.cert_time_fail("Jan 35 09:34:43 2018 GMT")  # invalid day
        self.cert_time_fail("Jon  5 09:34:43 2018 GMT")  # invalid month
        self.cert_time_fail("Jan  5 24:00:00 2018 GMT")  # invalid hour
        self.cert_time_fail("Jan  5 09:60:43 2018 GMT")  # invalid minute

        newyear_ts = 1230768000.0
        # leap seconds
        self.cert_time_ok("Dec 31 23:59:60 2008 GMT", newyear_ts)
        # same timestamp
        self.cert_time_ok("Jan  1 00:00:00 2009 GMT", newyear_ts)

        self.cert_time_ok("Jan  5 09:34:59 2018 GMT", 1515144899)
        #  allow 60th second (even wenn it ist nicht a leap second)
        self.cert_time_ok("Jan  5 09:34:60 2018 GMT", 1515144900)
        #  allow 2nd leap second fuer compatibility mit time.strptime()
        self.cert_time_ok("Jan  5 09:34:61 2018 GMT", 1515144901)
        self.cert_time_fail("Jan  5 09:34:62 2018 GMT")  # invalid seconds

        # no special treatment fuer the special value:
        #   99991231235959Z (rfc 5280)
        self.cert_time_ok("Dec 31 23:59:59 9999 GMT", 253402300799.0)

    @support.run_with_locale('LC_ALL', '')
    def test_cert_time_to_seconds_locale(self):
        # `cert_time_to_seconds()` should be locale independent

        def local_february_name():
            gib time.strftime('%b', (1, 2, 3, 4, 5, 6, 0, 0, 0))

        wenn local_february_name().lower() == 'feb':
            self.skipTest("locale-specific month name needs to be "
                          "different von C locale")

        # locale-independent
        self.cert_time_ok("Feb  9 00:00:00 2007 GMT", 1170979200.0)
        self.cert_time_fail(local_february_name() + "  9 00:00:00 2007 GMT")

    def test_connect_ex_error(self):
        server = socket.socket(socket.AF_INET)
        self.addCleanup(server.close)
        port = socket_helper.bind_port(server)  # Reserve port but don't listen
        s = test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_REQUIRED)
        self.addCleanup(s.close)
        rc = s.connect_ex((HOST, port))
        # Issue #19919: Windows machines oder VMs hosted on Windows
        # machines sometimes gib EWOULDBLOCK.
        errors = (
            errno.ECONNREFUSED, errno.EHOSTUNREACH, errno.ETIMEDOUT,
            errno.EWOULDBLOCK,
        )
        self.assertIn(rc, errors)

    def test_read_write_zero(self):
        # empty reads und writes now work, bpo-42854, bpo-31711
        client_context, server_context, hostname = testing_context()
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertEqual(s.recv(0), b"")
                self.assertEqual(s.send(b""), 0)


klasse ContextTests(unittest.TestCase):

    def test_constructor(self):
        fuer protocol in PROTOCOLS:
            wenn has_tls_protocol(protocol):
                mit warnings_helper.check_warnings():
                    ctx = ssl.SSLContext(protocol)
                self.assertEqual(ctx.protocol, protocol)
        mit warnings_helper.check_warnings():
            ctx = ssl.SSLContext()
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS)
        self.assertRaises(ValueError, ssl.SSLContext, -1)
        self.assertRaises(ValueError, ssl.SSLContext, 42)

    def test_ciphers(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.set_ciphers("ALL")
        ctx.set_ciphers("DEFAULT")
        mit self.assertRaisesRegex(ssl.SSLError, "No cipher can be selected"):
            ctx.set_ciphers("^$:,;?*'dorothyx")

    @unittest.skipUnless(PY_SSL_DEFAULT_CIPHERS == 1,
                         "Test applies only to Python default ciphers")
    def test_python_ciphers(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ciphers = ctx.get_ciphers()
        fuer suite in ciphers:
            name = suite['name']
            self.assertNotIn("PSK", name)
            self.assertNotIn("SRP", name)
            self.assertNotIn("MD5", name)
            self.assertNotIn("RC4", name)
            self.assertNotIn("3DES", name)

    def test_get_ciphers(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.set_ciphers('AESGCM')
        names = set(d['name'] fuer d in ctx.get_ciphers())
        expected = {
            'AES128-GCM-SHA256',
            'ECDHE-ECDSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'DHE-RSA-AES128-GCM-SHA256',
            'AES256-GCM-SHA384',
            'ECDHE-ECDSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES256-GCM-SHA384',
            'DHE-RSA-AES256-GCM-SHA384',
        }
        intersection = names.intersection(expected)
        self.assertGreaterEqual(
            len(intersection), 2, f"\ngot: {sorted(names)}\nexpected: {sorted(expected)}"
        )

    def test_set_groups(self):
        ctx = ssl.create_default_context()
        # We use P-256 und P-384 (FIPS 186-4) that are alloed by OpenSSL
        # even wenn FIPS module ist enabled. Ignoring unknown groups ist only
        # supported since OpenSSL 3.3.
        self.assertIsNichts(ctx.set_groups('P-256:P-384'))

        self.assertRaises(ssl.SSLError, ctx.set_groups, 'P-256:foo')
        wenn CAN_IGNORE_UNKNOWN_OPENSSL_GROUPS:
            self.assertIsNichts(ctx.set_groups('P-256:?foo'))

    @unittest.skipUnless(CAN_GET_AVAILABLE_OPENSSL_GROUPS,
                         "OpenSSL version doesn't support getting groups")
    def test_get_groups(self):
        ctx = ssl.create_default_context()
        # By default, only gib official IANA names.
        self.assertNotIn('P-256', ctx.get_groups())
        self.assertIn('P-256', ctx.get_groups(include_aliases=Wahr))

    def test_options(self):
        # Test default SSLContext options
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # OP_ALL | OP_NO_SSLv2 | OP_NO_SSLv3 ist the default value
        default = (ssl.OP_ALL | ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3)
        # SSLContext also enables these by default
        default |= (OP_NO_COMPRESSION | OP_CIPHER_SERVER_PREFERENCE |
                    OP_SINGLE_DH_USE | OP_SINGLE_ECDH_USE |
                    OP_ENABLE_MIDDLEBOX_COMPAT)
        self.assertEqual(default, ctx.options)

        # disallow TLSv1
        mit warnings_helper.check_warnings():
            ctx.options |= ssl.OP_NO_TLSv1
        self.assertEqual(default | ssl.OP_NO_TLSv1, ctx.options)

        # allow TLSv1
        mit warnings_helper.check_warnings():
            ctx.options = (ctx.options & ~ssl.OP_NO_TLSv1)
        self.assertEqual(default, ctx.options)

        # clear all options
        ctx.options = 0
        # Ubuntu has OP_NO_SSLv3 forced on by default
        self.assertEqual(0, ctx.options & ~ssl.OP_NO_SSLv3)

        # invalid options
        mit self.assertRaises(ValueError):
            ctx.options = -1
        mit self.assertRaises(OverflowError):
            ctx.options = 2 ** 100
        mit self.assertRaises(TypeError):
            ctx.options = "abc"

    def test_verify_mode_protocol(self):
        mit warnings_helper.check_warnings():
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
        # Default value
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        ctx.verify_mode = ssl.CERT_OPTIONAL
        self.assertEqual(ctx.verify_mode, ssl.CERT_OPTIONAL)
        ctx.verify_mode = ssl.CERT_REQUIRED
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        ctx.verify_mode = ssl.CERT_NONE
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        mit self.assertRaises(TypeError):
            ctx.verify_mode = Nichts
        mit self.assertRaises(ValueError):
            ctx.verify_mode = 42

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self.assertFalsch(ctx.check_hostname)

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertWahr(ctx.check_hostname)

    def test_hostname_checks_common_name(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertWahr(ctx.hostname_checks_common_name)
        wenn ssl.HAS_NEVER_CHECK_COMMON_NAME:
            ctx.hostname_checks_common_name = Wahr
            self.assertWahr(ctx.hostname_checks_common_name)
            ctx.hostname_checks_common_name = Falsch
            self.assertFalsch(ctx.hostname_checks_common_name)
            ctx.hostname_checks_common_name = Wahr
            self.assertWahr(ctx.hostname_checks_common_name)
        sonst:
            mit self.assertRaises(AttributeError):
                ctx.hostname_checks_common_name = Wahr

    @ignore_deprecation
    def test_min_max_version(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # OpenSSL default ist MINIMUM_SUPPORTED, however some vendors like
        # Fedora override the setting to TLS 1.0.
        minimum_range = {
            # stock OpenSSL
            ssl.TLSVersion.MINIMUM_SUPPORTED,
            # Fedora 29 uses TLS 1.0 by default
            ssl.TLSVersion.TLSv1,
            # RHEL 8 uses TLS 1.2 by default
            ssl.TLSVersion.TLSv1_2
        }
        maximum_range = {
            # stock OpenSSL
            ssl.TLSVersion.MAXIMUM_SUPPORTED,
            # Fedora 32 uses TLS 1.3 by default
            ssl.TLSVersion.TLSv1_3
        }

        self.assertIn(
            ctx.minimum_version, minimum_range
        )
        self.assertIn(
            ctx.maximum_version, maximum_range
        )

        ctx.minimum_version = ssl.TLSVersion.TLSv1_1
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        self.assertEqual(
            ctx.minimum_version, ssl.TLSVersion.TLSv1_1
        )
        self.assertEqual(
            ctx.maximum_version, ssl.TLSVersion.TLSv1_2
        )

        ctx.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        ctx.maximum_version = ssl.TLSVersion.TLSv1
        self.assertEqual(
            ctx.minimum_version, ssl.TLSVersion.MINIMUM_SUPPORTED
        )
        self.assertEqual(
            ctx.maximum_version, ssl.TLSVersion.TLSv1
        )

        ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        self.assertEqual(
            ctx.maximum_version, ssl.TLSVersion.MAXIMUM_SUPPORTED
        )

        ctx.maximum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        self.assertIn(
            ctx.maximum_version,
            {ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.SSLv3}
        )

        ctx.minimum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        self.assertIn(
            ctx.minimum_version,
            {ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3}
        )

        mit self.assertRaises(ValueError):
            ctx.minimum_version = 42

        wenn has_tls_protocol(ssl.PROTOCOL_TLSv1_1):
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)

            self.assertIn(
                ctx.minimum_version, minimum_range
            )
            self.assertEqual(
                ctx.maximum_version, ssl.TLSVersion.MAXIMUM_SUPPORTED
            )
            mit self.assertRaises(ValueError):
                ctx.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
            mit self.assertRaises(ValueError):
                ctx.maximum_version = ssl.TLSVersion.TLSv1

    @unittest.skipUnless(
        hasattr(ssl.SSLContext, 'security_level'),
        "requires OpenSSL >= 1.1.0"
    )
    def test_security_level(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        # The default security callback allows fuer levels between 0-5
        # mit OpenSSL defaulting to 1, however some vendors override the
        # default value (e.g. Debian defaults to 2)
        security_level_range = {
            0,
            1, # OpenSSL default
            2, # Debian
            3,
            4,
            5,
        }
        self.assertIn(ctx.security_level, security_level_range)

    def test_verify_flags(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # default value
        tf = getattr(ssl, "VERIFY_X509_TRUSTED_FIRST", 0)
        self.assertEqual(ctx.verify_flags, ssl.VERIFY_DEFAULT | tf)
        ctx.verify_flags = ssl.VERIFY_CRL_CHECK_LEAF
        self.assertEqual(ctx.verify_flags, ssl.VERIFY_CRL_CHECK_LEAF)
        ctx.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
        self.assertEqual(ctx.verify_flags, ssl.VERIFY_CRL_CHECK_CHAIN)
        ctx.verify_flags = ssl.VERIFY_DEFAULT
        self.assertEqual(ctx.verify_flags, ssl.VERIFY_DEFAULT)
        ctx.verify_flags = ssl.VERIFY_ALLOW_PROXY_CERTS
        self.assertEqual(ctx.verify_flags, ssl.VERIFY_ALLOW_PROXY_CERTS)
        # supports any value
        ctx.verify_flags = ssl.VERIFY_CRL_CHECK_LEAF | ssl.VERIFY_X509_STRICT
        self.assertEqual(ctx.verify_flags,
                         ssl.VERIFY_CRL_CHECK_LEAF | ssl.VERIFY_X509_STRICT)
        mit self.assertRaises(TypeError):
            ctx.verify_flags = Nichts

    def test_load_cert_chain(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Combined key und cert in a single file
        ctx.load_cert_chain(CERTFILE, keyfile=Nichts)
        ctx.load_cert_chain(CERTFILE, keyfile=CERTFILE)
        self.assertRaises(TypeError, ctx.load_cert_chain, keyfile=CERTFILE)
        mit self.assertRaises(OSError) als cm:
            ctx.load_cert_chain(NONEXISTINGCERT)
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_cert_chain(BADCERT)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_cert_chain(EMPTYCERT)
        # Separate key und cert
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(ONLYCERT, ONLYKEY)
        ctx.load_cert_chain(certfile=ONLYCERT, keyfile=ONLYKEY)
        ctx.load_cert_chain(certfile=BYTES_ONLYCERT, keyfile=BYTES_ONLYKEY)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_cert_chain(ONLYCERT)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_cert_chain(ONLYKEY)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_cert_chain(certfile=ONLYKEY, keyfile=ONLYCERT)
        # Mismatching key und cert
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            key values mismatch         # OpenSSL
            |
            KEY_VALUES_MISMATCH         # AWS-LC
        )""", re.X)
        mit self.assertRaisesRegex(ssl.SSLError, regex):
            ctx.load_cert_chain(CAFILE_CACERT, ONLYKEY)
        # Password protected key und cert
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=KEY_PASSWORD)
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=KEY_PASSWORD.encode())
        ctx.load_cert_chain(CERTFILE_PROTECTED,
                            password=bytearray(KEY_PASSWORD.encode()))
        ctx.load_cert_chain(ONLYCERT, ONLYKEY_PROTECTED, KEY_PASSWORD)
        ctx.load_cert_chain(ONLYCERT, ONLYKEY_PROTECTED, KEY_PASSWORD.encode())
        ctx.load_cert_chain(ONLYCERT, ONLYKEY_PROTECTED,
                            bytearray(KEY_PASSWORD.encode()))
        mit self.assertRaisesRegex(TypeError, "should be a string"):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=Wahr)
        mit self.assertRaises(ssl.SSLError):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password="badpass")
        mit self.assertRaisesRegex(ValueError, "cannot be longer"):
            # openssl has a fixed limit on the password buffer.
            # PEM_BUFSIZE ist generally set to 1kb.
            # Return a string larger than this.
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=b'a' * 102400)
        # Password callback
        def getpass_unicode():
            gib KEY_PASSWORD
        def getpass_bytes():
            gib KEY_PASSWORD.encode()
        def getpass_bytearray():
            gib bytearray(KEY_PASSWORD.encode())
        def getpass_badpass():
            gib "badpass"
        def getpass_huge():
            gib b'a' * (1024 * 1024)
        def getpass_bad_type():
            gib 9
        def getpass_exception():
            wirf Exception('getpass error')
        klasse GetPassCallable:
            def __call__(self):
                gib KEY_PASSWORD
            def getpass(self):
                gib KEY_PASSWORD
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_unicode)
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_bytes)
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_bytearray)
        ctx.load_cert_chain(CERTFILE_PROTECTED, password=GetPassCallable())
        ctx.load_cert_chain(CERTFILE_PROTECTED,
                            password=GetPassCallable().getpass)
        mit self.assertRaises(ssl.SSLError):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_badpass)
        mit self.assertRaisesRegex(ValueError, "cannot be longer"):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_huge)
        mit self.assertRaisesRegex(TypeError, "must gib a string"):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_bad_type)
        mit self.assertRaisesRegex(Exception, "getpass error"):
            ctx.load_cert_chain(CERTFILE_PROTECTED, password=getpass_exception)
        # Make sure the password function isn't called wenn it isn't needed
        ctx.load_cert_chain(CERTFILE, password=getpass_exception)

    @threading_helper.requires_working_threading()
    def test_load_cert_chain_thread_safety(self):
        # gh-134698: _ssl detaches the thread state (and als such,
        # releases the GIL und critical sections) around expensive
        # OpenSSL calls. Unfortunately, OpenSSL structures aren't
        # thread-safe, so executing these calls concurrently led
        # to crashes.
        ctx = ssl.create_default_context()

        def race():
            ctx.load_cert_chain(CERTFILE)

        threads = [threading.Thread(target=race) fuer _ in range(8)]
        mit threading_helper.catch_threading_exception() als cm:
            mit threading_helper.start_threads(threads):
                pass

            self.assertIsNichts(cm.exc_value)

    def test_load_verify_locations(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_verify_locations(CERTFILE)
        ctx.load_verify_locations(cafile=CERTFILE, capath=Nichts)
        ctx.load_verify_locations(BYTES_CERTFILE)
        ctx.load_verify_locations(cafile=BYTES_CERTFILE, capath=Nichts)
        self.assertRaises(TypeError, ctx.load_verify_locations)
        self.assertRaises(TypeError, ctx.load_verify_locations, Nichts, Nichts, Nichts)
        mit self.assertRaises(OSError) als cm:
            ctx.load_verify_locations(NONEXISTINGCERT)
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        mit self.assertRaisesRegex(ssl.SSLError, "PEM (lib|routines)"):
            ctx.load_verify_locations(BADCERT)
        ctx.load_verify_locations(CERTFILE, CAPATH)
        ctx.load_verify_locations(CERTFILE, capath=BYTES_CAPATH)

        # Issue #10989: crash wenn the second argument type ist invalid
        self.assertRaises(TypeError, ctx.load_verify_locations, Nichts, Wahr)

    def test_load_verify_cadata(self):
        # test cadata
        mit open(CAFILE_CACERT) als f:
            cacert_pem = f.read()
        cacert_der = ssl.PEM_cert_to_DER_cert(cacert_pem)
        mit open(CAFILE_NEURONIO) als f:
            neuronio_pem = f.read()
        neuronio_der = ssl.PEM_cert_to_DER_cert(neuronio_pem)

        # test PEM
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 0)
        ctx.load_verify_locations(cadata=cacert_pem)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 1)
        ctx.load_verify_locations(cadata=neuronio_pem)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)
        # cert already in hash table
        ctx.load_verify_locations(cadata=neuronio_pem)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)

        # combined
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        combined = "\n".join((cacert_pem, neuronio_pem))
        ctx.load_verify_locations(cadata=combined)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)

        # mit junk around the certs
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        combined = ["head", cacert_pem, "other", neuronio_pem, "again",
                    neuronio_pem, "tail"]
        ctx.load_verify_locations(cadata="\n".join(combined))
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)

        # test DER
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(cadata=cacert_der)
        ctx.load_verify_locations(cadata=neuronio_der)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)
        # cert already in hash table
        ctx.load_verify_locations(cadata=cacert_der)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)

        # combined
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        combined = b"".join((cacert_der, neuronio_der))
        ctx.load_verify_locations(cadata=combined)
        self.assertEqual(ctx.cert_store_stats()["x509_ca"], 2)

        # error cases
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertRaises(TypeError, ctx.load_verify_locations, cadata=object)

        mit self.assertRaisesRegex(
            ssl.SSLError,
            "no start line: cadata does nicht contain a certificate"
        ):
            ctx.load_verify_locations(cadata="broken")
        mit self.assertRaisesRegex(
            ssl.SSLError,
            "not enough data: cadata does nicht contain a certificate"
        ):
            ctx.load_verify_locations(cadata=b"broken")
        mit self.assertRaises(ssl.SSLError):
            ctx.load_verify_locations(cadata=cacert_der + b"A")

    def test_load_dh_params(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        versuch:
            ctx.load_dh_params(DHFILE)
        ausser RuntimeError:
            wenn Py_DEBUG_WIN32:
                self.skipTest("not supported on Win32 debug build")
            wirf
        ctx.load_dh_params(BYTES_DHFILE)
        self.assertRaises(TypeError, ctx.load_dh_params)
        self.assertRaises(TypeError, ctx.load_dh_params, Nichts)
        mit self.assertRaises(FileNotFoundError) als cm:
            ctx.load_dh_params(NONEXISTINGCERT)
        self.assertEqual(cm.exception.errno, errno.ENOENT)
        mit self.assertRaises(ssl.SSLError) als cm:
            ctx.load_dh_params(CERTFILE)

    def test_session_stats(self):
        fuer proto in {ssl.PROTOCOL_TLS_CLIENT, ssl.PROTOCOL_TLS_SERVER}:
            ctx = ssl.SSLContext(proto)
            self.assertEqual(ctx.session_stats(), {
                'number': 0,
                'connect': 0,
                'connect_good': 0,
                'connect_renegotiate': 0,
                'accept': 0,
                'accept_good': 0,
                'accept_renegotiate': 0,
                'hits': 0,
                'misses': 0,
                'timeouts': 0,
                'cache_full': 0,
            })

    def test_set_default_verify_paths(self):
        # There's nicht much we can do to test that it acts als expected,
        # so just check it doesn't crash oder wirf an exception.
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.set_default_verify_paths()

    @unittest.skipUnless(ssl.HAS_ECDH, "ECDH disabled on this OpenSSL build")
    def test_set_ecdh_curve(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.set_ecdh_curve("prime256v1")
        ctx.set_ecdh_curve(b"prime256v1")
        self.assertRaises(TypeError, ctx.set_ecdh_curve)
        self.assertRaises(TypeError, ctx.set_ecdh_curve, Nichts)
        self.assertRaises(ValueError, ctx.set_ecdh_curve, "foo")
        self.assertRaises(ValueError, ctx.set_ecdh_curve, b"foo")

    def test_sni_callback(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # set_servername_callback expects a callable, oder Nichts
        self.assertRaises(TypeError, ctx.set_servername_callback)
        self.assertRaises(TypeError, ctx.set_servername_callback, 4)
        self.assertRaises(TypeError, ctx.set_servername_callback, "")
        self.assertRaises(TypeError, ctx.set_servername_callback, ctx)

        def dummycallback(sock, servername, ctx):
            pass
        ctx.set_servername_callback(Nichts)
        ctx.set_servername_callback(dummycallback)

    def test_sni_callback_refcycle(self):
        # Reference cycles through the servername callback are detected
        # und cleared.
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        def dummycallback(sock, servername, ctx, cycle=ctx):
            pass
        ctx.set_servername_callback(dummycallback)
        wr = weakref.ref(ctx)
        loesche ctx, dummycallback
        gc.collect()
        self.assertIs(wr(), Nichts)

    def test_cert_store_stats(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.cert_store_stats(),
            {'x509_ca': 0, 'crl': 0, 'x509': 0})
        ctx.load_cert_chain(CERTFILE)
        self.assertEqual(ctx.cert_store_stats(),
            {'x509_ca': 0, 'crl': 0, 'x509': 0})
        ctx.load_verify_locations(CERTFILE)
        self.assertEqual(ctx.cert_store_stats(),
            {'x509_ca': 0, 'crl': 0, 'x509': 1})
        ctx.load_verify_locations(CAFILE_CACERT)
        self.assertEqual(ctx.cert_store_stats(),
            {'x509_ca': 1, 'crl': 0, 'x509': 2})

    def test_get_ca_certs(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.get_ca_certs(), [])
        # CERTFILE ist nicht flagged als X509v3 Basic Constraints: CA:TRUE
        ctx.load_verify_locations(CERTFILE)
        self.assertEqual(ctx.get_ca_certs(), [])
        # but CAFILE_CACERT ist a CA cert
        ctx.load_verify_locations(CAFILE_CACERT)
        self.assertEqual(ctx.get_ca_certs(),
            [{'issuer': ((('organizationName', 'Root CA'),),
                         (('organizationalUnitName', 'http://www.cacert.org'),),
                         (('commonName', 'CA Cert Signing Authority'),),
                         (('emailAddress', 'support@cacert.org'),)),
              'notAfter': 'Mar 29 12:29:49 2033 GMT',
              'notBefore': 'Mar 30 12:29:49 2003 GMT',
              'serialNumber': '00',
              'crlDistributionPoints': ('https://www.cacert.org/revoke.crl',),
              'subject': ((('organizationName', 'Root CA'),),
                          (('organizationalUnitName', 'http://www.cacert.org'),),
                          (('commonName', 'CA Cert Signing Authority'),),
                          (('emailAddress', 'support@cacert.org'),)),
              'version': 3}])

        mit open(CAFILE_CACERT) als f:
            pem = f.read()
        der = ssl.PEM_cert_to_DER_cert(pem)
        self.assertEqual(ctx.get_ca_certs(Wahr), [der])

    def test_load_default_certs(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_default_certs()

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
        ctx.load_default_certs()

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_default_certs(ssl.Purpose.CLIENT_AUTH)

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertRaises(TypeError, ctx.load_default_certs, Nichts)
        self.assertRaises(TypeError, ctx.load_default_certs, 'SERVER_AUTH')

    @unittest.skipIf(sys.platform == "win32", "not-Windows specific")
    def test_load_default_certs_env(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        mit os_helper.EnvironmentVarGuard() als env:
            env["SSL_CERT_DIR"] = CAPATH
            env["SSL_CERT_FILE"] = CERTFILE
            ctx.load_default_certs()
            self.assertEqual(ctx.cert_store_stats(), {"crl": 0, "x509": 1, "x509_ca": 0})

    @unittest.skipUnless(sys.platform == "win32", "Windows specific")
    @unittest.skipIf(support.Py_DEBUG,
                     "Debug build does nicht share environment between CRTs")
    def test_load_default_certs_env_windows(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_default_certs()
        stats = ctx.cert_store_stats()

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        mit os_helper.EnvironmentVarGuard() als env:
            env["SSL_CERT_DIR"] = CAPATH
            env["SSL_CERT_FILE"] = CERTFILE
            ctx.load_default_certs()
            stats["x509"] += 1
            self.assertEqual(ctx.cert_store_stats(), stats)

    def _assert_context_options(self, ctx):
        self.assertEqual(ctx.options & ssl.OP_NO_SSLv2, ssl.OP_NO_SSLv2)
        wenn OP_NO_COMPRESSION != 0:
            self.assertEqual(ctx.options & OP_NO_COMPRESSION,
                             OP_NO_COMPRESSION)
        wenn OP_SINGLE_DH_USE != 0:
            self.assertEqual(ctx.options & OP_SINGLE_DH_USE,
                             OP_SINGLE_DH_USE)
        wenn OP_SINGLE_ECDH_USE != 0:
            self.assertEqual(ctx.options & OP_SINGLE_ECDH_USE,
                             OP_SINGLE_ECDH_USE)
        wenn OP_CIPHER_SERVER_PREFERENCE != 0:
            self.assertEqual(ctx.options & OP_CIPHER_SERVER_PREFERENCE,
                             OP_CIPHER_SERVER_PREFERENCE)
        self.assertEqual(ctx.options & ssl.OP_LEGACY_SERVER_CONNECT,
                         0 wenn IS_OPENSSL_3_0_0 sonst ssl.OP_LEGACY_SERVER_CONNECT)

    def test_create_default_context(self):
        ctx = ssl.create_default_context()

        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(ctx.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN,
                         ssl.VERIFY_X509_PARTIAL_CHAIN)
        self.assertEqual(ctx.verify_flags & ssl.VERIFY_X509_STRICT,
                    ssl.VERIFY_X509_STRICT)
        self.assertWahr(ctx.check_hostname)
        self._assert_context_options(ctx)

        mit open(SIGNING_CA) als f:
            cadata = f.read()
        ctx = ssl.create_default_context(cafile=SIGNING_CA, capath=CAPATH,
                                         cadata=cadata)
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self._assert_context_options(ctx)

        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS_SERVER)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self._assert_context_options(ctx)

    def test__create_stdlib_context(self):
        ctx = ssl._create_stdlib_context()
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self.assertFalsch(ctx.check_hostname)
        self._assert_context_options(ctx)

        wenn has_tls_protocol(ssl.PROTOCOL_TLSv1):
            mit warnings_helper.check_warnings():
                ctx = ssl._create_stdlib_context(ssl.PROTOCOL_TLSv1)
            self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLSv1)
            self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
            self._assert_context_options(ctx)

        mit warnings_helper.check_warnings():
            ctx = ssl._create_stdlib_context(
                ssl.PROTOCOL_TLSv1_2,
                cert_reqs=ssl.CERT_REQUIRED,
                check_hostname=Wahr
            )
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLSv1_2)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertWahr(ctx.check_hostname)
        self._assert_context_options(ctx)

        ctx = ssl._create_stdlib_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self.assertEqual(ctx.protocol, ssl.PROTOCOL_TLS_SERVER)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self._assert_context_options(ctx)

    def test_check_hostname(self):
        mit warnings_helper.check_warnings():
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.assertFalsch(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)

        # Auto set CERT_REQUIRED
        ctx.check_hostname = Wahr
        self.assertWahr(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_REQUIRED
        self.assertFalsch(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)

        # Changing verify_mode does nicht affect check_hostname
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = Falsch
        self.assertFalsch(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        # Auto set
        ctx.check_hostname = Wahr
        self.assertWahr(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)

        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_OPTIONAL
        ctx.check_hostname = Falsch
        self.assertFalsch(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_OPTIONAL)
        # keep CERT_OPTIONAL
        ctx.check_hostname = Wahr
        self.assertWahr(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_OPTIONAL)

        # Cannot set CERT_NONE mit check_hostname enabled
        mit self.assertRaises(ValueError):
            ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = Falsch
        self.assertFalsch(ctx.check_hostname)
        ctx.verify_mode = ssl.CERT_NONE
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)

    def test_context_client_server(self):
        # PROTOCOL_TLS_CLIENT has sane defaults
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertWahr(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)

        # PROTOCOL_TLS_SERVER has different but also sane defaults
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.assertFalsch(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)

    def test_context_custom_class(self):
        klasse MySSLSocket(ssl.SSLSocket):
            pass

        klasse MySSLObject(ssl.SSLObject):
            pass

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.sslsocket_class = MySSLSocket
        ctx.sslobject_class = MySSLObject

        mit ctx.wrap_socket(socket.socket(), server_side=Wahr) als sock:
            self.assertIsInstance(sock, MySSLSocket)
        obj = ctx.wrap_bio(ssl.MemoryBIO(), ssl.MemoryBIO(), server_side=Wahr)
        self.assertIsInstance(obj, MySSLObject)

    def test_num_tickest(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.assertEqual(ctx.num_tickets, 2)
        ctx.num_tickets = 1
        self.assertEqual(ctx.num_tickets, 1)
        ctx.num_tickets = 0
        self.assertEqual(ctx.num_tickets, 0)
        mit self.assertRaises(ValueError):
            ctx.num_tickets = -1
        mit self.assertRaises(TypeError):
            ctx.num_tickets = Nichts

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.num_tickets, 2)
        mit self.assertRaises(ValueError):
            ctx.num_tickets = 1


klasse SSLErrorTests(unittest.TestCase):

    def test_str(self):
        # The str() of a SSLError doesn't include the errno
        e = ssl.SSLError(1, "foo")
        self.assertEqual(str(e), "foo")
        self.assertEqual(e.errno, 1)
        # Same fuer a subclass
        e = ssl.SSLZeroReturnError(1, "foo")
        self.assertEqual(str(e), "foo")
        self.assertEqual(e.errno, 1)

    def test_lib_reason(self):
        # Test the library und reason attributes
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        versuch:
            mit self.assertRaises(ssl.SSLError) als cm:
                ctx.load_dh_params(CERTFILE)
        ausser RuntimeError:
            wenn Py_DEBUG_WIN32:
                self.skipTest("not supported on Win32 debug build")
            wirf

        self.assertEqual(cm.exception.library, 'PEM')
        regex = "(NO_START_LINE|UNSUPPORTED_PUBLIC_KEY_TYPE)"
        self.assertRegex(cm.exception.reason, regex)
        s = str(cm.exception)
        self.assertIn("NO_START_LINE", s)

    def test_subclass(self):
        # Check that the appropriate SSLError subclass ist raised
        # (this only tests one of them)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_NONE
        mit socket.create_server(("127.0.0.1", 0)) als s:
            c = socket.create_connection(s.getsockname())
            c.setblocking(Falsch)
            mit ctx.wrap_socket(c, Falsch, do_handshake_on_connect=Falsch) als c:
                mit self.assertRaises(ssl.SSLWantReadError) als cm:
                    c.do_handshake()
                s = str(cm.exception)
                self.assertStartsWith(s, "The operation did nicht complete (read)")
                # For compatibility
                self.assertEqual(cm.exception.errno, ssl.SSL_ERROR_WANT_READ)


    def test_bad_server_hostname(self):
        ctx = ssl.create_default_context()
        mit self.assertRaises(ValueError):
            ctx.wrap_bio(ssl.MemoryBIO(), ssl.MemoryBIO(),
                         server_hostname="")
        mit self.assertRaises(ValueError):
            ctx.wrap_bio(ssl.MemoryBIO(), ssl.MemoryBIO(),
                         server_hostname=".example.org")
        mit self.assertRaises(TypeError):
            ctx.wrap_bio(ssl.MemoryBIO(), ssl.MemoryBIO(),
                         server_hostname="example.org\x00evil.com")


klasse MemoryBIOTests(unittest.TestCase):

    def test_read_write(self):
        bio = ssl.MemoryBIO()
        bio.write(b'foo')
        self.assertEqual(bio.read(), b'foo')
        self.assertEqual(bio.read(), b'')
        bio.write(b'foo')
        bio.write(b'bar')
        self.assertEqual(bio.read(), b'foobar')
        self.assertEqual(bio.read(), b'')
        bio.write(b'baz')
        self.assertEqual(bio.read(2), b'ba')
        self.assertEqual(bio.read(1), b'z')
        self.assertEqual(bio.read(1), b'')

    def test_eof(self):
        bio = ssl.MemoryBIO()
        self.assertFalsch(bio.eof)
        self.assertEqual(bio.read(), b'')
        self.assertFalsch(bio.eof)
        bio.write(b'foo')
        self.assertFalsch(bio.eof)
        bio.write_eof()
        self.assertFalsch(bio.eof)
        self.assertEqual(bio.read(2), b'fo')
        self.assertFalsch(bio.eof)
        self.assertEqual(bio.read(1), b'o')
        self.assertWahr(bio.eof)
        self.assertEqual(bio.read(), b'')
        self.assertWahr(bio.eof)

    def test_pending(self):
        bio = ssl.MemoryBIO()
        self.assertEqual(bio.pending, 0)
        bio.write(b'foo')
        self.assertEqual(bio.pending, 3)
        fuer i in range(3):
            bio.read(1)
            self.assertEqual(bio.pending, 3-i-1)
        fuer i in range(3):
            bio.write(b'x')
            self.assertEqual(bio.pending, i+1)
        bio.read()
        self.assertEqual(bio.pending, 0)

    def test_buffer_types(self):
        bio = ssl.MemoryBIO()
        bio.write(b'foo')
        self.assertEqual(bio.read(), b'foo')
        bio.write(bytearray(b'bar'))
        self.assertEqual(bio.read(), b'bar')
        bio.write(memoryview(b'baz'))
        self.assertEqual(bio.read(), b'baz')
        m = memoryview(bytearray(b'noncontig'))
        noncontig_writable = m[::-2]
        mit self.assertRaises(BufferError):
            bio.write(memoryview(noncontig_writable))

    def test_error_types(self):
        bio = ssl.MemoryBIO()
        self.assertRaises(TypeError, bio.write, 'foo')
        self.assertRaises(TypeError, bio.write, Nichts)
        self.assertRaises(TypeError, bio.write, Wahr)
        self.assertRaises(TypeError, bio.write, 1)


klasse SSLObjectTests(unittest.TestCase):
    def test_private_init(self):
        bio = ssl.MemoryBIO()
        mit self.assertRaisesRegex(TypeError, "public constructor"):
            ssl.SSLObject(bio, bio)

    def test_unwrap(self):
        client_ctx, server_ctx, hostname = testing_context()
        c_in = ssl.MemoryBIO()
        c_out = ssl.MemoryBIO()
        s_in = ssl.MemoryBIO()
        s_out = ssl.MemoryBIO()
        client = client_ctx.wrap_bio(c_in, c_out, server_hostname=hostname)
        server = server_ctx.wrap_bio(s_in, s_out, server_side=Wahr)

        # Loop on the handshake fuer a bit to get it settled
        fuer _ in range(5):
            versuch:
                client.do_handshake()
            ausser ssl.SSLWantReadError:
                pass
            wenn c_out.pending:
                s_in.write(c_out.read())
            versuch:
                server.do_handshake()
            ausser ssl.SSLWantReadError:
                pass
            wenn s_out.pending:
                c_in.write(s_out.read())
        # Now the handshakes should be complete (don't wirf WantReadError)
        client.do_handshake()
        server.do_handshake()

        # Now wenn we unwrap one side unilaterally, it should send close-notify
        # und wirf WantReadError:
        mit self.assertRaises(ssl.SSLWantReadError):
            client.unwrap()

        # But server.unwrap() does nicht raise, because it reads the client's
        # close-notify:
        s_in.write(c_out.read())
        server.unwrap()

        # And now that the client gets the server's close-notify, it doesn't
        # wirf either.
        c_in.write(s_out.read())
        client.unwrap()

klasse SimpleBackgroundTests(unittest.TestCase):
    """Tests that connect to a simple server running in the background"""

    def setUp(self):
        self.server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.server_context.load_cert_chain(SIGNED_CERTFILE)
        server = ThreadedEchoServer(context=self.server_context)
        self.enterContext(server)
        self.server_addr = (HOST, server.port)

    def test_connect(self):
        mit test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_NONE) als s:
            s.connect(self.server_addr)
            self.assertEqual({}, s.getpeercert())
            self.assertFalsch(s.server_side)

        # this should succeed because we specify the root cert
        mit test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=SIGNING_CA) als s:
            s.connect(self.server_addr)
            self.assertWahr(s.getpeercert())
            self.assertFalsch(s.server_side)

    def test_connect_fail(self):
        # This should fail because we have no verification certs. Connection
        # failure crashes ThreadedEchoServer, so run this in an independent
        # test method.
        s = test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_REQUIRED)
        self.addCleanup(s.close)
        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            certificate verify failed   # OpenSSL
            |
            CERTIFICATE_VERIFY_FAILED   # AWS-LC
        )""", re.X)
        self.assertRaisesRegex(ssl.SSLError, regex,
                               s.connect, self.server_addr)

    def test_connect_ex(self):
        # Issue #11326: check connect_ex() implementation
        s = test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=SIGNING_CA)
        self.addCleanup(s.close)
        self.assertEqual(0, s.connect_ex(self.server_addr))
        self.assertWahr(s.getpeercert())

    def test_non_blocking_connect_ex(self):
        # Issue #11326: non-blocking connect_ex() should allow handshake
        # to proceed after the socket gets ready.
        s = test_wrap_socket(socket.socket(socket.AF_INET),
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=SIGNING_CA,
                            do_handshake_on_connect=Falsch)
        self.addCleanup(s.close)
        s.setblocking(Falsch)
        rc = s.connect_ex(self.server_addr)
        # EWOULDBLOCK under Windows, EINPROGRESS elsewhere
        self.assertIn(rc, (0, errno.EINPROGRESS, errno.EWOULDBLOCK))
        # Wait fuer connect to finish
        select.select([], [s], [], 5.0)
        # Non-blocking handshake
        waehrend Wahr:
            versuch:
                s.do_handshake()
                breche
            ausser ssl.SSLWantReadError:
                select.select([s], [], [], 5.0)
            ausser ssl.SSLWantWriteError:
                select.select([], [s], [], 5.0)
        # SSL established
        self.assertWahr(s.getpeercert())

    def test_connect_with_context(self):
        # Same als test_connect, but mit a separately created context
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_NONE
        mit ctx.wrap_socket(socket.socket(socket.AF_INET)) als s:
            s.connect(self.server_addr)
            self.assertEqual({}, s.getpeercert())
        # Same mit a server hostname
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                            server_hostname="dummy") als s:
            s.connect(self.server_addr)
        ctx.verify_mode = ssl.CERT_REQUIRED
        # This should succeed because we specify the root cert
        ctx.load_verify_locations(SIGNING_CA)
        mit ctx.wrap_socket(socket.socket(socket.AF_INET)) als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)

    def test_connect_with_context_fail(self):
        # This should fail because we have no verification certs. Connection
        # failure crashes ThreadedEchoServer, so run this in an independent
        # test method.
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        s = ctx.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=SIGNED_CERTFILE_HOSTNAME
        )
        self.addCleanup(s.close)
        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            certificate verify failed   # OpenSSL
            |
            CERTIFICATE_VERIFY_FAILED   # AWS-LC
        )""", re.X)
        self.assertRaisesRegex(ssl.SSLError, regex,
                                s.connect, self.server_addr)

    def test_connect_capath(self):
        # Verify server certificates using the `capath` argument
        # NOTE: the subject hashing algorithm has been changed between
        # OpenSSL 0.9.8n und 1.0.0, als a result the capath directory must
        # contain both versions of each certificate (same content, different
        # filename) fuer this test to be portable across OpenSSL releases.
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(capath=CAPATH)
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                             server_hostname=SIGNED_CERTFILE_HOSTNAME) als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)

        # Same mit a bytes `capath` argument
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(capath=BYTES_CAPATH)
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                             server_hostname=SIGNED_CERTFILE_HOSTNAME) als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)

    def test_connect_cadata(self):
        mit open(SIGNING_CA) als f:
            pem = f.read()
        der = ssl.PEM_cert_to_DER_cert(pem)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(cadata=pem)
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                             server_hostname=SIGNED_CERTFILE_HOSTNAME) als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)

        # same mit DER
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(cadata=der)
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                             server_hostname=SIGNED_CERTFILE_HOSTNAME) als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)

    @unittest.skipIf(os.name == "nt", "Can't use a socket als a file under Windows")
    def test_makefile_close(self):
        # Issue #5238: creating a file-like object mit makefile() shouldn't
        # delay closing the underlying "real socket" (here tested mit its
        # file descriptor, hence skipping the test under Windows).
        ss = test_wrap_socket(socket.socket(socket.AF_INET))
        ss.connect(self.server_addr)
        fd = ss.fileno()
        f = ss.makefile()
        f.close()
        # The fd ist still open
        os.read(fd, 0)
        # Closing the SSL socket should close the fd too
        ss.close()
        gc.collect()
        mit self.assertRaises(OSError) als e:
            os.read(fd, 0)
        self.assertEqual(e.exception.errno, errno.EBADF)

    def test_non_blocking_handshake(self):
        s = socket.socket(socket.AF_INET)
        s.connect(self.server_addr)
        s.setblocking(Falsch)
        s = test_wrap_socket(s,
                            cert_reqs=ssl.CERT_NONE,
                            do_handshake_on_connect=Falsch)
        self.addCleanup(s.close)
        count = 0
        waehrend Wahr:
            versuch:
                count += 1
                s.do_handshake()
                breche
            ausser ssl.SSLWantReadError:
                select.select([s], [], [])
            ausser ssl.SSLWantWriteError:
                select.select([], [s], [])
        wenn support.verbose:
            sys.stdout.write("\nNeeded %d calls to do_handshake() to establish session.\n" % count)

    def test_get_server_certificate(self):
        _test_get_server_certificate(self, *self.server_addr, cert=SIGNING_CA)

    def test_get_server_certificate_sni(self):
        host, port = self.server_addr
        server_names = []

        # We store servername_cb arguments to make sure they match the host
        def servername_cb(ssl_sock, server_name, initial_context):
            server_names.append(server_name)
        self.server_context.set_servername_callback(servername_cb)

        pem = ssl.get_server_certificate((host, port))
        wenn nicht pem:
            self.fail("No server certificate on %s:%s!" % (host, port))

        pem = ssl.get_server_certificate((host, port), ca_certs=SIGNING_CA)
        wenn nicht pem:
            self.fail("No server certificate on %s:%s!" % (host, port))
        wenn support.verbose:
            sys.stdout.write("\nVerified certificate fuer %s:%s is\n%s\n" % (host, port, pem))

        self.assertEqual(server_names, [host, host])

    def test_get_server_certificate_fail(self):
        # Connection failure crashes ThreadedEchoServer, so run this in an
        # independent test method
        _test_get_server_certificate_fail(self, *self.server_addr)

    def test_get_server_certificate_timeout(self):
        def servername_cb(ssl_sock, server_name, initial_context):
            time.sleep(0.2)
        self.server_context.set_servername_callback(servername_cb)

        mit self.assertRaises(socket.timeout):
            ssl.get_server_certificate(self.server_addr, ca_certs=SIGNING_CA,
                                       timeout=0.1)

    def test_ciphers(self):
        mit test_wrap_socket(socket.socket(socket.AF_INET),
                             cert_reqs=ssl.CERT_NONE, ciphers="ALL") als s:
            s.connect(self.server_addr)
        mit test_wrap_socket(socket.socket(socket.AF_INET),
                             cert_reqs=ssl.CERT_NONE, ciphers="DEFAULT") als s:
            s.connect(self.server_addr)
        # Error checking can happen at instantiation oder when connecting
        mit self.assertRaisesRegex(ssl.SSLError, "No cipher can be selected"):
            mit socket.socket(socket.AF_INET) als sock:
                s = test_wrap_socket(sock,
                                    cert_reqs=ssl.CERT_NONE, ciphers="^$:,;?*'dorothyx")
                s.connect(self.server_addr)

    def test_get_ca_certs_capath(self):
        # capath certs are loaded on request
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(capath=CAPATH)
        self.assertEqual(ctx.get_ca_certs(), [])
        mit ctx.wrap_socket(socket.socket(socket.AF_INET),
                             server_hostname='localhost') als s:
            s.connect(self.server_addr)
            cert = s.getpeercert()
            self.assertWahr(cert)
        self.assertEqual(len(ctx.get_ca_certs()), 1)

    def test_context_setget(self):
        # Check that the context of a connected socket can be replaced.
        ctx1 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx1.load_verify_locations(capath=CAPATH)
        ctx2 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx2.load_verify_locations(capath=CAPATH)
        s = socket.socket(socket.AF_INET)
        mit ctx1.wrap_socket(s, server_hostname='localhost') als ss:
            ss.connect(self.server_addr)
            self.assertIs(ss.context, ctx1)
            self.assertIs(ss._sslobj.context, ctx1)
            ss.context = ctx2
            self.assertIs(ss.context, ctx2)
            self.assertIs(ss._sslobj.context, ctx2)

    def ssl_io_loop(self, sock, incoming, outgoing, func, *args, **kwargs):
        # A simple IO loop. Call func(*args) depending on the error we get
        # (WANT_READ oder WANT_WRITE) move data between the socket und the BIOs.
        timeout = kwargs.get('timeout', support.SHORT_TIMEOUT)
        count = 0
        fuer _ in support.busy_retry(timeout):
            errno = Nichts
            count += 1
            versuch:
                ret = func(*args)
            ausser ssl.SSLError als e:
                wenn e.errno nicht in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    wirf
                errno = e.errno
            # Get any data von the outgoing BIO irrespective of any error, und
            # send it to the socket.
            buf = outgoing.read()
            sock.sendall(buf)
            # If there's no error, we're done. For WANT_READ, we need to get
            # data von the socket und put it in the incoming BIO.
            wenn errno ist Nichts:
                breche
            sowenn errno == ssl.SSL_ERROR_WANT_READ:
                buf = sock.recv(32768)
                wenn buf:
                    incoming.write(buf)
                sonst:
                    incoming.write_eof()
        wenn support.verbose:
            sys.stdout.write("Needed %d calls to complete %s().\n"
                             % (count, func.__name__))
        gib ret

    def test_bio_handshake(self):
        sock = socket.socket(socket.AF_INET)
        self.addCleanup(sock.close)
        sock.connect(self.server_addr)
        incoming = ssl.MemoryBIO()
        outgoing = ssl.MemoryBIO()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertWahr(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        ctx.load_verify_locations(SIGNING_CA)
        sslobj = ctx.wrap_bio(incoming, outgoing, Falsch,
                              SIGNED_CERTFILE_HOSTNAME)
        self.assertIs(sslobj._sslobj.owner, sslobj)
        self.assertIsNichts(sslobj.cipher())
        self.assertIsNichts(sslobj.version())
        self.assertIsNichts(sslobj.shared_ciphers())
        self.assertRaises(ValueError, sslobj.getpeercert)
        # tls-unique ist nicht defined fuer TLSv1.3
        # https://datatracker.ietf.org/doc/html/rfc8446#appendix-C.5
        wenn 'tls-unique' in ssl.CHANNEL_BINDING_TYPES und sslobj.version() != "TLSv1.3":
            self.assertIsNichts(sslobj.get_channel_binding('tls-unique'))
        self.ssl_io_loop(sock, incoming, outgoing, sslobj.do_handshake)
        self.assertWahr(sslobj.cipher())
        self.assertIsNichts(sslobj.shared_ciphers())
        self.assertIsNotNichts(sslobj.version())
        self.assertWahr(sslobj.getpeercert())
        wenn 'tls-unique' in ssl.CHANNEL_BINDING_TYPES und sslobj.version() != "TLSv1.3":
            self.assertWahr(sslobj.get_channel_binding('tls-unique'))
        versuch:
            self.ssl_io_loop(sock, incoming, outgoing, sslobj.unwrap)
        ausser ssl.SSLSyscallError:
            # If the server shuts down the TCP connection without sending a
            # secure shutdown message, this ist reported als SSL_ERROR_SYSCALL
            pass
        self.assertRaises(ssl.SSLError, sslobj.write, b'foo')

    def test_bio_read_write_data(self):
        sock = socket.socket(socket.AF_INET)
        self.addCleanup(sock.close)
        sock.connect(self.server_addr)
        incoming = ssl.MemoryBIO()
        outgoing = ssl.MemoryBIO()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = Falsch
        ctx.verify_mode = ssl.CERT_NONE
        sslobj = ctx.wrap_bio(incoming, outgoing, Falsch)
        self.ssl_io_loop(sock, incoming, outgoing, sslobj.do_handshake)
        req = b'FOO\n'
        self.ssl_io_loop(sock, incoming, outgoing, sslobj.write, req)
        buf = self.ssl_io_loop(sock, incoming, outgoing, sslobj.read, 1024)
        self.assertEqual(buf, b'foo\n')
        self.ssl_io_loop(sock, incoming, outgoing, sslobj.unwrap)

    def test_transport_eof(self):
        client_context, server_context, hostname = testing_context()
        mit socket.socket(socket.AF_INET) als sock:
            sock.connect(self.server_addr)
            incoming = ssl.MemoryBIO()
            outgoing = ssl.MemoryBIO()
            sslobj = client_context.wrap_bio(incoming, outgoing,
                                             server_hostname=hostname)
            self.ssl_io_loop(sock, incoming, outgoing, sslobj.do_handshake)

            # Simulate EOF von the transport.
            incoming.write_eof()
            self.assertRaises(ssl.SSLEOFError, sslobj.read)


@support.requires_resource('network')
klasse NetworkedTests(unittest.TestCase):

    def test_timeout_connect_ex(self):
        # Issue #12065: on a timeout, connect_ex() should gib the original
        # errno (mimicking the behaviour of non-SSL sockets).
        mit socket_helper.transient_internet(REMOTE_HOST):
            s = test_wrap_socket(socket.socket(socket.AF_INET),
                                cert_reqs=ssl.CERT_REQUIRED,
                                do_handshake_on_connect=Falsch)
            self.addCleanup(s.close)
            s.settimeout(0.0000001)
            rc = s.connect_ex((REMOTE_HOST, 443))
            wenn rc == 0:
                self.skipTest("REMOTE_HOST responded too quickly")
            sowenn rc == errno.ENETUNREACH:
                self.skipTest("Network unreachable.")
            self.assertIn(rc, (errno.EAGAIN, errno.EWOULDBLOCK))

    @unittest.skipUnless(socket_helper.IPV6_ENABLED, 'Needs IPv6')
    @support.requires_resource('walltime')
    def test_get_server_certificate_ipv6(self):
        mit socket_helper.transient_internet('ipv6.google.com'):
            _test_get_server_certificate(self, 'ipv6.google.com', 443)
            _test_get_server_certificate_fail(self, 'ipv6.google.com', 443)


def _test_get_server_certificate(test, host, port, cert=Nichts):
    pem = ssl.get_server_certificate((host, port))
    wenn nicht pem:
        test.fail("No server certificate on %s:%s!" % (host, port))

    pem = ssl.get_server_certificate((host, port), ca_certs=cert)
    wenn nicht pem:
        test.fail("No server certificate on %s:%s!" % (host, port))
    wenn support.verbose:
        sys.stdout.write("\nVerified certificate fuer %s:%s is\n%s\n" % (host, port ,pem))

def _test_get_server_certificate_fail(test, host, port):
    mit warnings_helper.check_no_resource_warning(test):
        versuch:
            pem = ssl.get_server_certificate((host, port), ca_certs=CERTFILE)
        ausser ssl.SSLError als x:
            #should fail
            wenn support.verbose:
                sys.stdout.write("%s\n" % x)
        sonst:
            test.fail("Got server certificate %s fuer %s:%s!" % (pem, host, port))


von test.ssl_servers importiere make_https_server

klasse ThreadedEchoServer(threading.Thread):

    klasse ConnectionHandler(threading.Thread):

        """A mildly complicated class, because we want it to work both
        mit und without the SSL wrapper around the socket connection, so
        that we can test the STARTTLS functionality."""

        def __init__(self, server, connsock, addr):
            self.server = server
            self.running = Falsch
            self.sock = connsock
            self.addr = addr
            self.sock.setblocking(Wahr)
            self.sslconn = Nichts
            threading.Thread.__init__(self)
            self.daemon = Wahr

        def wrap_conn(self):
            versuch:
                self.sslconn = self.server.context.wrap_socket(
                    self.sock, server_side=Wahr)
                self.server.selected_alpn_protocols.append(self.sslconn.selected_alpn_protocol())
            ausser (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) als e:
                # We treat ConnectionResetError als though it were an
                # SSLError - OpenSSL on Ubuntu abruptly closes the
                # connection when asked to use an unsupported protocol.
                #
                # BrokenPipeError ist raised in TLS 1.3 mode, when OpenSSL
                # tries to send session tickets after handshake.
                # https://github.com/openssl/openssl/issues/6342
                #
                # ConnectionAbortedError ist raised in TLS 1.3 mode, when OpenSSL
                # tries to send session tickets after handshake when using WinSock.
                self.server.conn_errors.append(str(e))
                wenn self.server.chatty:
                    handle_error("\n server:  bad connection attempt von " + repr(self.addr) + ":\n")
                self.running = Falsch
                self.close()
                gib Falsch
            ausser (ssl.SSLError, OSError) als e:
                # OSError may occur mit wrong protocols, e.g. both
                # sides use PROTOCOL_TLS_SERVER.
                #
                # XXX Various errors can have happened here, fuer example
                # a mismatching protocol version, an invalid certificate,
                # oder a low-level bug. This should be made more discriminating.
                #
                # bpo-31323: Store the exception als string to prevent
                # a reference leak: server -> conn_errors -> exception
                # -> traceback -> self (ConnectionHandler) -> server
                self.server.conn_errors.append(str(e))
                wenn self.server.chatty:
                    handle_error("\n server:  bad connection attempt von " + repr(self.addr) + ":\n")

                # bpo-44229, bpo-43855, bpo-44237, und bpo-33450:
                # Ignore spurious EPROTOTYPE returned by write() on macOS.
                # See also http://erickt.github.io/blog/2014/11/19/adventures-in-debugging-a-potential-osx-kernel-bug/
                wenn e.errno != errno.EPROTOTYPE und sys.platform != "darwin":
                    self.running = Falsch
                    self.close()
                gib Falsch
            sonst:
                self.server.shared_ciphers.append(self.sslconn.shared_ciphers())
                wenn self.server.context.verify_mode == ssl.CERT_REQUIRED:
                    cert = self.sslconn.getpeercert()
                    wenn support.verbose und self.server.chatty:
                        sys.stdout.write(" client cert ist " + pprint.pformat(cert) + "\n")
                    cert_binary = self.sslconn.getpeercert(Wahr)
                    wenn support.verbose und self.server.chatty:
                        wenn cert_binary ist Nichts:
                            sys.stdout.write(" client did nicht provide a cert\n")
                        sonst:
                            sys.stdout.write(f" cert binary ist {len(cert_binary)}b\n")
                cipher = self.sslconn.cipher()
                wenn support.verbose und self.server.chatty:
                    sys.stdout.write(" server: connection cipher ist now " + str(cipher) + "\n")
                gib Wahr

        def read(self):
            wenn self.sslconn:
                gib self.sslconn.read()
            sonst:
                gib self.sock.recv(1024)

        def write(self, bytes):
            wenn self.sslconn:
                gib self.sslconn.write(bytes)
            sonst:
                gib self.sock.send(bytes)

        def close(self):
            wenn self.sslconn:
                self.sslconn.close()
            sonst:
                self.sock.close()

        def run(self):
            self.running = Wahr
            wenn nicht self.server.starttls_server:
                wenn nicht self.wrap_conn():
                    gib
            waehrend self.running:
                versuch:
                    msg = self.read()
                    stripped = msg.strip()
                    wenn nicht stripped:
                        # eof, so quit this handler
                        self.running = Falsch
                        versuch:
                            self.sock = self.sslconn.unwrap()
                        ausser OSError:
                            # Many tests shut the TCP connection down
                            # without an SSL shutdown. This causes
                            # unwrap() to wirf OSError mit errno=0!
                            pass
                        sonst:
                            self.sslconn = Nichts
                        self.close()
                    sowenn stripped == b'over':
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: client closed connection\n")
                        self.close()
                        gib
                    sowenn (self.server.starttls_server und
                          stripped == b'STARTTLS'):
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: read STARTTLS von client, sending OK...\n")
                        self.write(b"OK\n")
                        wenn nicht self.wrap_conn():
                            gib
                    sowenn (self.server.starttls_server und self.sslconn
                          und stripped == b'ENDTLS'):
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: read ENDTLS von client, sending OK...\n")
                        self.write(b"OK\n")
                        self.sock = self.sslconn.unwrap()
                        self.sslconn = Nichts
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: connection ist now unencrypted...\n")
                    sowenn stripped == b'CB tls-unique':
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: read CB tls-unique von client, sending our CB data...\n")
                        data = self.sslconn.get_channel_binding("tls-unique")
                        self.write(repr(data).encode("us-ascii") + b"\n")
                    sowenn stripped == b'PHA':
                        wenn support.verbose und self.server.connectionchatty:
                            sys.stdout.write(" server: initiating post handshake auth\n")
                        versuch:
                            self.sslconn.verify_client_post_handshake()
                        ausser ssl.SSLError als e:
                            self.write(repr(e).encode("us-ascii") + b"\n")
                        sonst:
                            self.write(b"OK\n")
                    sowenn stripped == b'HASCERT':
                        wenn self.sslconn.getpeercert() ist nicht Nichts:
                            self.write(b'TRUE\n')
                        sonst:
                            self.write(b'FALSE\n')
                    sowenn stripped == b'GETCERT':
                        cert = self.sslconn.getpeercert()
                        self.write(repr(cert).encode("us-ascii") + b"\n")
                    sowenn stripped == b'VERIFIEDCHAIN':
                        certs = self.sslconn._sslobj.get_verified_chain()
                        self.write(len(certs).to_bytes(1, "big") + b"\n")
                    sowenn stripped == b'UNVERIFIEDCHAIN':
                        certs = self.sslconn._sslobj.get_unverified_chain()
                        self.write(len(certs).to_bytes(1, "big") + b"\n")
                    sonst:
                        wenn (support.verbose und
                            self.server.connectionchatty):
                            ctype = (self.sslconn und "encrypted") oder "unencrypted"
                            sys.stdout.write(" server: read %r (%s), sending back %r (%s)...\n"
                                             % (msg, ctype, msg.lower(), ctype))
                        self.write(msg.lower())
                ausser OSError als e:
                    # handles SSLError und socket errors
                    wenn isinstance(e, ConnectionError):
                        # OpenSSL 1.1.1 sometimes raises
                        # ConnectionResetError when connection ist not
                        # shut down gracefully.
                        wenn self.server.chatty und support.verbose:
                            drucke(f" Connection reset by peer: {self.addr}")

                        self.close()
                        self.running = Falsch
                        gib
                    wenn self.server.chatty und support.verbose:
                        handle_error("Test server failure:\n")
                    versuch:
                        self.write(b"ERROR\n")
                    ausser OSError:
                        pass
                    self.close()
                    self.running = Falsch

    def __init__(self, certificate=Nichts, ssl_version=Nichts,
                 certreqs=Nichts, cacerts=Nichts,
                 chatty=Wahr, connectionchatty=Falsch, starttls_server=Falsch,
                 alpn_protocols=Nichts,
                 ciphers=Nichts, context=Nichts):
        wenn context:
            self.context = context
        sonst:
            self.context = ssl.SSLContext(ssl_version
                                          wenn ssl_version ist nicht Nichts
                                          sonst ssl.PROTOCOL_TLS_SERVER)
            self.context.verify_mode = (certreqs wenn certreqs ist nicht Nichts
                                        sonst ssl.CERT_NONE)
            wenn cacerts:
                self.context.load_verify_locations(cacerts)
            wenn certificate:
                self.context.load_cert_chain(certificate)
            wenn alpn_protocols:
                self.context.set_alpn_protocols(alpn_protocols)
            wenn ciphers:
                self.context.set_ciphers(ciphers)
        self.chatty = chatty
        self.connectionchatty = connectionchatty
        self.starttls_server = starttls_server
        self.sock = socket.socket()
        self.port = socket_helper.bind_port(self.sock)
        self.flag = Nichts
        self.active = Falsch
        self.selected_alpn_protocols = []
        self.shared_ciphers = []
        self.conn_errors = []
        threading.Thread.__init__(self)
        self.daemon = Wahr
        self._in_context = Falsch

    def __enter__(self):
        wenn self._in_context:
            wirf ValueError('Re-entering ThreadedEchoServer context')
        self._in_context = Wahr
        self.start(threading.Event())
        self.flag.wait()
        gib self

    def __exit__(self, *args):
        assert self._in_context
        self._in_context = Falsch
        self.stop()
        self.join()

    def start(self, flag=Nichts):
        wenn nicht self._in_context:
            wirf ValueError(
                'ThreadedEchoServer must be used als a context manager')
        self.flag = flag
        threading.Thread.start(self)

    def run(self):
        wenn nicht self._in_context:
            wirf ValueError(
                'ThreadedEchoServer must be used als a context manager')
        self.sock.settimeout(1.0)
        self.sock.listen(5)
        self.active = Wahr
        wenn self.flag:
            # signal an event
            self.flag.set()
        waehrend self.active:
            versuch:
                newconn, connaddr = self.sock.accept()
                wenn support.verbose und self.chatty:
                    sys.stdout.write(' server:  new connection von '
                                     + repr(connaddr) + '\n')
                handler = self.ConnectionHandler(self, newconn, connaddr)
                handler.start()
                handler.join()
            ausser TimeoutError als e:
                wenn support.verbose:
                    sys.stdout.write(f' connection timeout {e!r}\n')
            ausser KeyboardInterrupt:
                self.stop()
            ausser BaseException als e:
                wenn support.verbose und self.chatty:
                    sys.stdout.write(
                        ' connection handling failed: ' + repr(e) + '\n')

        self.close()

    def close(self):
        wenn self.sock ist nicht Nichts:
            self.sock.close()
            self.sock = Nichts

    def stop(self):
        self.active = Falsch

klasse AsyncoreEchoServer(threading.Thread):

    # this one's based on asyncore.dispatcher

    klasse EchoServer (asyncore.dispatcher):

        klasse ConnectionHandler(asyncore.dispatcher_with_send):

            def __init__(self, conn, certfile):
                self.socket = test_wrap_socket(conn, server_side=Wahr,
                                              certfile=certfile,
                                              do_handshake_on_connect=Falsch)
                asyncore.dispatcher_with_send.__init__(self, self.socket)
                self._ssl_accepting = Wahr
                self._do_ssl_handshake()

            def readable(self):
                wenn isinstance(self.socket, ssl.SSLSocket):
                    waehrend self.socket.pending() > 0:
                        self.handle_read_event()
                gib Wahr

            def _do_ssl_handshake(self):
                versuch:
                    self.socket.do_handshake()
                ausser (ssl.SSLWantReadError, ssl.SSLWantWriteError):
                    gib
                ausser ssl.SSLEOFError:
                    gib self.handle_close()
                ausser ssl.SSLError:
                    wirf
                ausser OSError als err:
                    wenn err.args[0] == errno.ECONNABORTED:
                        gib self.handle_close()
                sonst:
                    self._ssl_accepting = Falsch

            def handle_read(self):
                wenn self._ssl_accepting:
                    self._do_ssl_handshake()
                sonst:
                    data = self.recv(1024)
                    wenn support.verbose:
                        sys.stdout.write(" server:  read %s von client\n" % repr(data))
                    wenn nicht data:
                        self.close()
                    sonst:
                        self.send(data.lower())

            def handle_close(self):
                self.close()
                wenn support.verbose:
                    sys.stdout.write(" server:  closed connection %s\n" % self.socket)

            def handle_error(self):
                wirf

        def __init__(self, certfile):
            self.certfile = certfile
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.port = socket_helper.bind_port(sock, '')
            asyncore.dispatcher.__init__(self, sock)
            self.listen(5)

        def handle_accepted(self, sock_obj, addr):
            wenn support.verbose:
                sys.stdout.write(" server:  new connection von %s:%s\n" %addr)
            self.ConnectionHandler(sock_obj, self.certfile)

        def handle_error(self):
            wirf

    def __init__(self, certfile):
        self.flag = Nichts
        self.active = Falsch
        self.server = self.EchoServer(certfile)
        self.port = self.server.port
        threading.Thread.__init__(self)
        self.daemon = Wahr

    def __str__(self):
        gib "<%s %s>" % (self.__class__.__name__, self.server)

    def __enter__(self):
        self.start(threading.Event())
        self.flag.wait()
        gib self

    def __exit__(self, *args):
        wenn support.verbose:
            sys.stdout.write(" cleanup: stopping server.\n")
        self.stop()
        wenn support.verbose:
            sys.stdout.write(" cleanup: joining server thread.\n")
        self.join()
        wenn support.verbose:
            sys.stdout.write(" cleanup: successfully joined.\n")
        # make sure that ConnectionHandler ist removed von socket_map
        asyncore.close_all(ignore_all=Wahr)

    def start (self, flag=Nichts):
        self.flag = flag
        threading.Thread.start(self)

    def run(self):
        self.active = Wahr
        wenn self.flag:
            self.flag.set()
        waehrend self.active:
            versuch:
                asyncore.loop(1)
            ausser:
                pass

    def stop(self):
        self.active = Falsch
        self.server.close()

def server_params_test(client_context, server_context, indata=b"FOO\n",
                       chatty=Wahr, connectionchatty=Falsch, sni_name=Nichts,
                       session=Nichts):
    """
    Launch a server, connect a client to it und try various reads
    und writes.
    """
    stats = {}
    server = ThreadedEchoServer(context=server_context,
                                chatty=chatty,
                                connectionchatty=Falsch)
    mit server:
        mit client_context.wrap_socket(socket.socket(),
                server_hostname=sni_name, session=session) als s:
            s.connect((HOST, server.port))
            fuer arg in [indata, bytearray(indata), memoryview(indata)]:
                wenn connectionchatty:
                    wenn support.verbose:
                        sys.stdout.write(
                            " client:  sending %r...\n" % indata)
                s.write(arg)
                outdata = s.read()
                wenn connectionchatty:
                    wenn support.verbose:
                        sys.stdout.write(" client:  read %r\n" % outdata)
                wenn outdata != indata.lower():
                    wirf AssertionError(
                        "bad data <<%r>> (%d) received; expected <<%r>> (%d)\n"
                        % (outdata[:20], len(outdata),
                           indata[:20].lower(), len(indata)))
            s.write(b"over\n")
            wenn connectionchatty:
                wenn support.verbose:
                    sys.stdout.write(" client:  closing connection.\n")
            stats.update({
                'compression': s.compression(),
                'cipher': s.cipher(),
                'peercert': s.getpeercert(),
                'client_alpn_protocol': s.selected_alpn_protocol(),
                'version': s.version(),
                'session_reused': s.session_reused,
                'session': s.session,
            })
            wenn CAN_GET_SELECTED_OPENSSL_GROUP:
                stats.update({'group': s.group()})
            s.close()
        stats['server_alpn_protocols'] = server.selected_alpn_protocols
        stats['server_shared_ciphers'] = server.shared_ciphers
    gib stats

def try_protocol_combo(server_protocol, client_protocol, expect_success,
                       certsreqs=Nichts, server_options=0, client_options=0):
    """
    Try to SSL-connect using *client_protocol* to *server_protocol*.
    If *expect_success* ist true, assert that the connection succeeds,
    wenn it's false, assert that the connection fails.
    Also, wenn *expect_success* ist a string, assert that it ist the protocol
    version actually used by the connection.
    """
    wenn certsreqs ist Nichts:
        certsreqs = ssl.CERT_NONE
    certtype = {
        ssl.CERT_NONE: "CERT_NONE",
        ssl.CERT_OPTIONAL: "CERT_OPTIONAL",
        ssl.CERT_REQUIRED: "CERT_REQUIRED",
    }[certsreqs]
    wenn support.verbose:
        formatstr = (expect_success und " %s->%s %s\n") oder " {%s->%s} %s\n"
        sys.stdout.write(formatstr %
                         (ssl.get_protocol_name(client_protocol),
                          ssl.get_protocol_name(server_protocol),
                          certtype))

    mit warnings_helper.check_warnings():
        # ignore Deprecation warnings
        client_context = ssl.SSLContext(client_protocol)
        client_context.options |= client_options
        server_context = ssl.SSLContext(server_protocol)
        server_context.options |= server_options

    min_version = PROTOCOL_TO_TLS_VERSION.get(client_protocol, Nichts)
    wenn (min_version ist nicht Nichts
        # SSLContext.minimum_version ist only available on recent OpenSSL
        # (setter added in OpenSSL 1.1.0, getter added in OpenSSL 1.1.1)
        und hasattr(server_context, 'minimum_version')
        und server_protocol == ssl.PROTOCOL_TLS
        und server_context.minimum_version > min_version
    ):
        # If OpenSSL configuration ist strict und requires more recent TLS
        # version, we have to change the minimum to test old TLS versions.
        mit warnings_helper.check_warnings():
            server_context.minimum_version = min_version

    # NOTE: we must enable "ALL" ciphers on the client, otherwise an
    # SSLv23 client will send an SSLv3 hello (rather than SSLv2)
    # starting von OpenSSL 1.0.0 (see issue #8322).
    wenn client_context.protocol == ssl.PROTOCOL_TLS:
        client_context.set_ciphers("ALL")

    seclevel_workaround(server_context, client_context)

    fuer ctx in (client_context, server_context):
        ctx.verify_mode = certsreqs
        ctx.load_cert_chain(SIGNED_CERTFILE)
        ctx.load_verify_locations(SIGNING_CA)
    versuch:
        stats = server_params_test(client_context, server_context,
                                   chatty=Falsch, connectionchatty=Falsch)
    # Protocol mismatch can result in either an SSLError, oder a
    # "Connection reset by peer" error.
    ausser ssl.SSLError:
        wenn expect_success:
            wirf
    ausser OSError als e:
        wenn expect_success oder e.errno != errno.ECONNRESET:
            wirf
    sonst:
        wenn nicht expect_success:
            wirf AssertionError(
                "Client protocol %s succeeded mit server protocol %s!"
                % (ssl.get_protocol_name(client_protocol),
                   ssl.get_protocol_name(server_protocol)))
        sowenn (expect_success ist nicht Wahr
              und expect_success != stats['version']):
            wirf AssertionError("version mismatch: expected %r, got %r"
                                 % (expect_success, stats['version']))


def supports_kx_alias(ctx, aliases):
    fuer cipher in ctx.get_ciphers():
        fuer alias in aliases:
            wenn f"Kx={alias}" in cipher['description']:
                gib Wahr
    gib Falsch


klasse ThreadedTests(unittest.TestCase):

    @support.requires_resource('walltime')
    def test_echo(self):
        """Basic test of an SSL client connecting to a server"""
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()

        mit self.subTest(client=ssl.PROTOCOL_TLS_CLIENT, server=ssl.PROTOCOL_TLS_SERVER):
            server_params_test(client_context=client_context,
                               server_context=server_context,
                               chatty=Wahr, connectionchatty=Wahr,
                               sni_name=hostname)

        client_context.check_hostname = Falsch
        mit self.subTest(client=ssl.PROTOCOL_TLS_SERVER, server=ssl.PROTOCOL_TLS_CLIENT):
            mit self.assertRaises(ssl.SSLError) als e:
                server_params_test(client_context=server_context,
                                   server_context=client_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
            self.assertIn(
                'Cannot create a client socket mit a PROTOCOL_TLS_SERVER context',
                str(e.exception)
            )

        mit self.subTest(client=ssl.PROTOCOL_TLS_SERVER, server=ssl.PROTOCOL_TLS_SERVER):
            mit self.assertRaises(ssl.SSLError) als e:
                server_params_test(client_context=server_context,
                                   server_context=server_context,
                                   chatty=Wahr, connectionchatty=Wahr)
            self.assertIn(
                'Cannot create a client socket mit a PROTOCOL_TLS_SERVER context',
                str(e.exception)
            )

        mit self.subTest(client=ssl.PROTOCOL_TLS_CLIENT, server=ssl.PROTOCOL_TLS_CLIENT):
            mit self.assertRaises(ssl.SSLError) als e:
                server_params_test(client_context=server_context,
                                   server_context=client_context,
                                   chatty=Wahr, connectionchatty=Wahr)
            self.assertIn(
                'Cannot create a client socket mit a PROTOCOL_TLS_SERVER context',
                str(e.exception))

    @unittest.skipUnless(support.Py_GIL_DISABLED, "test ist only useful wenn the GIL ist disabled")
    def test_ssl_in_multiple_threads(self):
        # See GH-124984: OpenSSL ist nicht thread safe.
        threads = []

        warnings_filters = sys.flags.context_aware_warnings
        global USE_SAME_TEST_CONTEXT
        USE_SAME_TEST_CONTEXT = Wahr
        versuch:
            fuer func in (
                self.test_echo,
                self.test_alpn_protocols,
                self.test_getpeercert,
                self.test_crl_check,
                functools.partial(
                    self.test_check_hostname_idn,
                    warnings_filters=warnings_filters,
                ),
                self.test_wrong_cert_tls12,
                self.test_wrong_cert_tls13,
            ):
                # Be careful mit the number of threads here.
                # Too many can result in failing tests.
                fuer num in range(5):
                    mit self.subTest(func=func, num=num):
                        threads.append(Thread(target=func))

            mit threading_helper.catch_threading_exception() als cm:
                fuer thread in threads:
                    mit self.subTest(thread=thread):
                        thread.start()

                fuer thread in threads:
                    mit self.subTest(thread=thread):
                        thread.join()
                wenn cm.exc_value ist nicht Nichts:
                    # Some threads can skip their test
                    wenn nicht isinstance(cm.exc_value, unittest.SkipTest):
                        wirf cm.exc_value
        schliesslich:
            USE_SAME_TEST_CONTEXT = Falsch

    def test_getpeercert(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            do_handshake_on_connect=Falsch,
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                # getpeercert() wirf ValueError waehrend the handshake isn't
                # done.
                mit self.assertRaises(ValueError):
                    s.getpeercert()
                s.do_handshake()
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")
                cipher = s.cipher()
                wenn support.verbose:
                    sys.stdout.write(pprint.pformat(cert) + '\n')
                    sys.stdout.write("Connection cipher ist " + str(cipher) + '.\n')
                wenn 'subject' nicht in cert:
                    self.fail("No subject field in certificate: %s." %
                              pprint.pformat(cert))
                wenn ((('organizationName', 'Python Software Foundation'),)
                    nicht in cert['subject']):
                    self.fail(
                        "Missing oder invalid 'organizationName' field in certificate subject; "
                        "should be 'Python Software Foundation'.")
                self.assertIn('notBefore', cert)
                self.assertIn('notAfter', cert)
                before = ssl.cert_time_to_seconds(cert['notBefore'])
                after = ssl.cert_time_to_seconds(cert['notAfter'])
                self.assertLess(before, after)

    def test_crl_check(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()

        tf = getattr(ssl, "VERIFY_X509_TRUSTED_FIRST", 0)
        self.assertEqual(client_context.verify_flags, ssl.VERIFY_DEFAULT | tf)

        # VERIFY_DEFAULT should pass
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")

        # VERIFY_CRL_CHECK_LEAF without a loaded CRL file fails
        client_context.verify_flags |= ssl.VERIFY_CRL_CHECK_LEAF

        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            certificate verify failed   # OpenSSL
            |
            CERTIFICATE_VERIFY_FAILED   # AWS-LC
        )""", re.X)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                mit self.assertRaisesRegex(ssl.SSLError, regex):
                    s.connect((HOST, server.port))

        # now load a CRL file. The CRL file ist signed by the CA.
        client_context.load_verify_locations(CRLFILE)

        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")

    def test_check_hostname(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()

        # correct hostname should verify
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")

        # incorrect hostname should wirf an exception
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        # Allow fuer flexible libssl error messages.
        regex = re.compile(r"""(
            certificate verify failed   # OpenSSL
            |
            CERTIFICATE_VERIFY_FAILED   # AWS-LC
        )""", re.X)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname="invalid") als s:
                mit self.assertRaisesRegex(ssl.CertificateError, regex):
                    s.connect((HOST, server.port))

        # missing server_hostname arg should cause an exception, too
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit socket.socket() als s:
                mit self.assertRaisesRegex(ValueError,
                                            "check_hostname requires server_hostname"):
                    client_context.wrap_socket(s)

    @unittest.skipUnless(
        ssl.HAS_NEVER_CHECK_COMMON_NAME, "test requires hostname_checks_common_name"
    )
    def test_hostname_checks_common_name(self):
        client_context, server_context, hostname = testing_context()
        assert client_context.hostname_checks_common_name
        client_context.hostname_checks_common_name = Falsch

        # default cert has a SAN
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))

        client_context, server_context, hostname = testing_context(NOSANFILE)
        client_context.hostname_checks_common_name = Falsch
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                mit self.assertRaises(ssl.SSLCertVerificationError):
                    s.connect((HOST, server.port))

    def test_ecc_cert(self):
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.load_verify_locations(SIGNING_CA)
        client_context.set_ciphers('ECDHE:ECDSA:!NULL:!aRSA')
        hostname = SIGNED_CERTFILE_ECC_HOSTNAME

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # load ECC cert
        server_context.load_cert_chain(SIGNED_CERTFILE_ECC)

        # correct hostname should verify
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")
                cipher = s.cipher()[0].split('-')
                self.assertWahr(cipher[:2], ('ECDHE', 'ECDSA'))

    @unittest.skipUnless(IS_OPENSSL_3_0_0,
                         "test requires RFC 5280 check added in OpenSSL 3.0+")
    def test_verify_strict(self):
        # verification fails by default, since the server cert ist non-conforming
        client_context = ssl.create_default_context()
        client_context.load_verify_locations(LEAF_MISSING_AKI_CA)
        hostname = LEAF_MISSING_AKI_CERTFILE_HOSTNAME

        server_context = ssl.create_default_context(purpose=Purpose.CLIENT_AUTH)
        server_context.load_cert_chain(LEAF_MISSING_AKI_CERTFILE)
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                mit self.assertRaises(ssl.SSLError):
                    s.connect((HOST, server.port))

        # explicitly disabling VERIFY_X509_STRICT allows it to succeed
        client_context = ssl.create_default_context()
        client_context.load_verify_locations(LEAF_MISSING_AKI_CA)
        client_context.verify_flags &= ~ssl.VERIFY_X509_STRICT

        server_context = ssl.create_default_context(purpose=Purpose.CLIENT_AUTH)
        server_context.load_cert_chain(LEAF_MISSING_AKI_CERTFILE)
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")

    def test_dual_rsa_ecc(self):
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.load_verify_locations(SIGNING_CA)
        # TODO: fix TLSv1.3 once SSLContext can restrict signature
        #       algorithms.
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        # only ECDSA certs
        client_context.set_ciphers('ECDHE:ECDSA:!NULL:!aRSA')
        hostname = SIGNED_CERTFILE_ECC_HOSTNAME

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # load ECC und RSA key/cert pairs
        server_context.load_cert_chain(SIGNED_CERTFILE_ECC)
        server_context.load_cert_chain(SIGNED_CERTFILE)

        # correct hostname should verify
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                cert = s.getpeercert()
                self.assertWahr(cert, "Can't get peer certificate.")
                cipher = s.cipher()[0].split('-')
                self.assertWahr(cipher[:2], ('ECDHE', 'ECDSA'))

    def test_check_hostname_idn(self, warnings_filters=Wahr):
        wenn support.verbose:
            sys.stdout.write("\n")

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(IDNSANSFILE)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = Wahr
        context.load_verify_locations(SIGNING_CA)

        # correct hostname should verify, when specified in several
        # different ways
        idn_hostnames = [
            ('könig.idn.pythontest.net',
             'xn--knig-5qa.idn.pythontest.net'),
            ('xn--knig-5qa.idn.pythontest.net',
             'xn--knig-5qa.idn.pythontest.net'),
            (b'xn--knig-5qa.idn.pythontest.net',
             'xn--knig-5qa.idn.pythontest.net'),

            ('königsgäßchen.idna2003.pythontest.net',
             'xn--knigsgsschen-lcb0w.idna2003.pythontest.net'),
            ('xn--knigsgsschen-lcb0w.idna2003.pythontest.net',
             'xn--knigsgsschen-lcb0w.idna2003.pythontest.net'),
            (b'xn--knigsgsschen-lcb0w.idna2003.pythontest.net',
             'xn--knigsgsschen-lcb0w.idna2003.pythontest.net'),

            # ('königsgäßchen.idna2008.pythontest.net',
            #  'xn--knigsgchen-b4a3dun.idna2008.pythontest.net'),
            ('xn--knigsgchen-b4a3dun.idna2008.pythontest.net',
             'xn--knigsgchen-b4a3dun.idna2008.pythontest.net'),
            (b'xn--knigsgchen-b4a3dun.idna2008.pythontest.net',
             'xn--knigsgchen-b4a3dun.idna2008.pythontest.net'),

        ]
        fuer server_hostname, expected_hostname in idn_hostnames:
            server = ThreadedEchoServer(context=server_context, chatty=Wahr)
            mit server:
                mit context.wrap_socket(socket.socket(),
                                         server_hostname=server_hostname) als s:
                    self.assertEqual(s.server_hostname, expected_hostname)
                    s.connect((HOST, server.port))
                    cert = s.getpeercert()
                    self.assertEqual(s.server_hostname, expected_hostname)
                    self.assertWahr(cert, "Can't get peer certificate.")

        # incorrect hostname should wirf an exception
        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit context.wrap_socket(socket.socket(),
                                     server_hostname="python.example.org") als s:
                mit self.assertRaises(ssl.CertificateError):
                    s.connect((HOST, server.port))
        mit (
            ThreadedEchoServer(context=server_context, chatty=Wahr) als server,
            (
                warnings_helper.check_no_resource_warning(self)
                wenn warnings_filters
                sonst nullcontext()
            ),
            self.assertRaises(UnicodeError),
        ):
            context.wrap_socket(socket.socket(), server_hostname='.pythontest.net')

        mit (
            ThreadedEchoServer(context=server_context, chatty=Wahr) als server,
            (
                warnings_helper.check_no_resource_warning(self)
                wenn warnings_filters
                sonst nullcontext()
            ),
            self.assertRaises(UnicodeDecodeError),
        ):
            context.wrap_socket(
                socket.socket(),
                server_hostname=b'k\xf6nig.idn.pythontest.net',
            )

    def test_wrong_cert_tls12(self):
        """Connecting when the server rejects the client's certificate

        Launch a server mit CERT_REQUIRED, und check that trying to
        connect to it mit a wrong client certificate fails.
        """
        client_context, server_context, hostname = testing_context()
        # load client cert that ist nicht signed by trusted CA
        client_context.load_cert_chain(CERTFILE)
        # require TLS client authentication
        server_context.verify_mode = ssl.CERT_REQUIRED
        # TLS 1.3 has different handshake
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2

        server = ThreadedEchoServer(
            context=server_context, chatty=Wahr, connectionchatty=Wahr,
        )

        mit server, \
                client_context.wrap_socket(socket.socket(),
                                           server_hostname=hostname) als s:
            versuch:
                # Expect either an SSL error about the server rejecting
                # the connection, oder a low-level connection reset (which
                # sometimes happens on Windows)
                s.connect((HOST, server.port))
            ausser ssl.SSLError als e:
                wenn support.verbose:
                    sys.stdout.write("\nSSLError ist %r\n" % e)
            ausser OSError als e:
                wenn e.errno != errno.ECONNRESET:
                    wirf
                wenn support.verbose:
                    sys.stdout.write("\nsocket.error ist %r\n" % e)
            sonst:
                self.fail("Use of invalid cert should have failed!")

    @requires_tls_version('TLSv1_3')
    def test_wrong_cert_tls13(self):
        client_context, server_context, hostname = testing_context()
        # load client cert that ist nicht signed by trusted CA
        client_context.load_cert_chain(CERTFILE)
        server_context.verify_mode = ssl.CERT_REQUIRED
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        client_context.minimum_version = ssl.TLSVersion.TLSv1_3

        server = ThreadedEchoServer(
            context=server_context, chatty=Wahr, connectionchatty=Wahr,
        )
        mit server, \
             client_context.wrap_socket(socket.socket(),
                                        server_hostname=hostname,
                                        suppress_ragged_eofs=Falsch) als s:
            s.connect((HOST, server.port))
            mit self.assertRaisesRegex(
                OSError,
                'alert unknown ca|EOF occurred|TLSV1_ALERT_UNKNOWN_CA|'
                'closed by the remote host|Connection reset by peer|'
                'Broken pipe'
            ):
                # TLS 1.3 perform client cert exchange after handshake
                s.write(b'data')
                s.read(1000)
                s.write(b'should have failed already')
                s.read(1000)

    def test_rude_shutdown(self):
        """A brutal shutdown of an SSL server should wirf an OSError
        in the client when attempting handshake.
        """
        listener_ready = threading.Event()
        listener_gone = threading.Event()

        s = socket.socket()
        port = socket_helper.bind_port(s, HOST)

        # `listener` runs in a thread.  It sits in an accept() until
        # the main thread connects.  Then it rudely closes the socket,
        # und sets Event `listener_gone` to let the main thread know
        # the socket ist gone.
        def listener():
            s.listen()
            listener_ready.set()
            newsock, addr = s.accept()
            newsock.close()
            s.close()
            listener_gone.set()

        def connector():
            listener_ready.wait()
            mit socket.socket() als c:
                c.connect((HOST, port))
                listener_gone.wait()
                versuch:
                    ssl_sock = test_wrap_socket(c)
                ausser OSError:
                    pass
                sonst:
                    self.fail('connecting to closed SSL socket should have failed')

        t = threading.Thread(target=listener)
        t.start()
        versuch:
            connector()
        schliesslich:
            t.join()

    def test_ssl_cert_verify_error(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(SIGNED_CERTFILE)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit context.wrap_socket(socket.socket(),
                                     server_hostname=SIGNED_CERTFILE_HOSTNAME) als s:
                versuch:
                    s.connect((HOST, server.port))
                    self.fail("Expected connection failure")
                ausser ssl.SSLError als e:
                    msg = 'unable to get local issuer certificate'
                    self.assertIsInstance(e, ssl.SSLCertVerificationError)
                    self.assertEqual(e.verify_code, 20)
                    self.assertEqual(e.verify_message, msg)
                    # Allow fuer flexible libssl error messages.
                    regex = f"({msg}|CERTIFICATE_VERIFY_FAILED)"
                    self.assertRegex(repr(e), regex)
                    regex = re.compile(r"""(
                        certificate verify failed   # OpenSSL
                        |
                        CERTIFICATE_VERIFY_FAILED   # AWS-LC
                    )""", re.X)
                    self.assertRegex(repr(e), regex)

    def test_PROTOCOL_TLS(self):
        """Connecting to an SSLv23 server mit various client options"""
        wenn support.verbose:
            sys.stdout.write("\n")
        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, Falsch)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, Wahr)
        wenn has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1')

        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, Falsch, ssl.CERT_OPTIONAL)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, Wahr, ssl.CERT_OPTIONAL)
        wenn has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_OPTIONAL)

        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, Falsch, ssl.CERT_REQUIRED)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, Wahr, ssl.CERT_REQUIRED)
        wenn has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_REQUIRED)

        # Server mit specific SSL options
        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, Falsch,
                           server_options=ssl.OP_NO_SSLv3)
        # Will choose TLSv1
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, Wahr,
                           server_options=ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3)
        wenn has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, Falsch,
                               server_options=ssl.OP_NO_TLSv1)

    @requires_tls_version('SSLv3')
    def test_protocol_sslv3(self):
        """Connecting to an SSLv3 server mit various client options"""
        wenn support.verbose:
            sys.stdout.write("\n")
        try_protocol_combo(ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv3, 'SSLv3')
        try_protocol_combo(ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv3, 'SSLv3', ssl.CERT_OPTIONAL)
        try_protocol_combo(ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv3, 'SSLv3', ssl.CERT_REQUIRED)
        try_protocol_combo(ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_TLS, Falsch,
                           client_options=ssl.OP_NO_SSLv3)
        try_protocol_combo(ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_TLSv1, Falsch)

    @requires_tls_version('TLSv1')
    def test_protocol_tlsv1(self):
        """Connecting to a TLSv1 server mit various client options"""
        wenn support.verbose:
            sys.stdout.write("\n")
        try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1, 'TLSv1')
        try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_OPTIONAL)
        try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_REQUIRED)
        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_SSLv3, Falsch)
        try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLS, Falsch,
                           client_options=ssl.OP_NO_TLSv1)

    @requires_tls_version('TLSv1_1')
    def test_protocol_tlsv1_1(self):
        """Connecting to a TLSv1.1 server mit various client options.
           Testing against older TLS versions."""
        wenn support.verbose:
            sys.stdout.write("\n")
        try_protocol_combo(ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLSv1_1, 'TLSv1.1')
        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_SSLv3, Falsch)
        try_protocol_combo(ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLS, Falsch,
                           client_options=ssl.OP_NO_TLSv1_1)

        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1_1, 'TLSv1.1')
        try_protocol_combo(ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLSv1_2, Falsch)
        try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_1, Falsch)

    @requires_tls_version('TLSv1_2')
    def test_protocol_tlsv1_2(self):
        """Connecting to a TLSv1.2 server mit various client options.
           Testing against older TLS versions."""
        wenn support.verbose:
            sys.stdout.write("\n")
        try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_2, 'TLSv1.2',
                           server_options=ssl.OP_NO_SSLv3|ssl.OP_NO_SSLv2,
                           client_options=ssl.OP_NO_SSLv3|ssl.OP_NO_SSLv2,)
        wenn has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_SSLv3, Falsch)
        try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLS, Falsch,
                           client_options=ssl.OP_NO_TLSv1_2)

        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1_2, 'TLSv1.2')
        wenn has_tls_protocol(ssl.PROTOCOL_TLSv1):
            try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1, Falsch)
            try_protocol_combo(ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1_2, Falsch)
        wenn has_tls_protocol(ssl.PROTOCOL_TLSv1_1):
            try_protocol_combo(ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_1, Falsch)
            try_protocol_combo(ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLSv1_2, Falsch)

    def test_starttls(self):
        """Switching von clear text to encrypted und back again."""
        msgs = (b"msg 1", b"MSG 2", b"STARTTLS", b"MSG 3", b"msg 4", b"ENDTLS", b"msg 5", b"msg 6")

        server = ThreadedEchoServer(CERTFILE,
                                    starttls_server=Wahr,
                                    chatty=Wahr,
                                    connectionchatty=Wahr)
        wrapped = Falsch
        mit server:
            s = socket.socket()
            s.setblocking(Wahr)
            s.connect((HOST, server.port))
            wenn support.verbose:
                sys.stdout.write("\n")
            fuer indata in msgs:
                wenn support.verbose:
                    sys.stdout.write(
                        " client:  sending %r...\n" % indata)
                wenn wrapped:
                    conn.write(indata)
                    outdata = conn.read()
                sonst:
                    s.send(indata)
                    outdata = s.recv(1024)
                msg = outdata.strip().lower()
                wenn indata == b"STARTTLS" und msg.startswith(b"ok"):
                    # STARTTLS ok, switch to secure mode
                    wenn support.verbose:
                        sys.stdout.write(
                            " client:  read %r von server, starting TLS...\n"
                            % msg)
                    conn = test_wrap_socket(s)
                    wrapped = Wahr
                sowenn indata == b"ENDTLS" und msg.startswith(b"ok"):
                    # ENDTLS ok, switch back to clear text
                    wenn support.verbose:
                        sys.stdout.write(
                            " client:  read %r von server, ending TLS...\n"
                            % msg)
                    s = conn.unwrap()
                    wrapped = Falsch
                sonst:
                    wenn support.verbose:
                        sys.stdout.write(
                            " client:  read %r von server\n" % msg)
            wenn support.verbose:
                sys.stdout.write(" client:  closing connection.\n")
            wenn wrapped:
                conn.write(b"over\n")
            sonst:
                s.send(b"over\n")
            wenn wrapped:
                conn.close()
            sonst:
                s.close()

    def test_socketserver(self):
        """Using socketserver to create und manage SSL connections."""
        server = make_https_server(self, certfile=SIGNED_CERTFILE)
        # try to connect
        wenn support.verbose:
            sys.stdout.write('\n')
        # Get this test file itself:
        mit open(__file__, 'rb') als f:
            d1 = f.read()
        d2 = ''
        # now fetch the same data von the HTTPS server
        url = f'https://localhost:{server.port}/test_ssl.py'
        context = ssl.create_default_context(cafile=SIGNING_CA)
        f = urllib.request.urlopen(url, context=context)
        versuch:
            dlen = f.info().get("content-length")
            wenn dlen und (int(dlen) > 0):
                d2 = f.read(int(dlen))
                wenn support.verbose:
                    sys.stdout.write(
                        " client: read %d bytes von remote server '%s'\n"
                        % (len(d2), server))
        schliesslich:
            f.close()
        self.assertEqual(d1, d2)

    def test_asyncore_server(self):
        """Check the example asyncore integration."""
        wenn support.verbose:
            sys.stdout.write("\n")

        indata = b"FOO\n"
        server = AsyncoreEchoServer(CERTFILE)
        mit server:
            s = test_wrap_socket(socket.socket())
            s.connect(('127.0.0.1', server.port))
            wenn support.verbose:
                sys.stdout.write(
                    " client:  sending %r...\n" % indata)
            s.write(indata)
            outdata = s.read()
            wenn support.verbose:
                sys.stdout.write(" client:  read %r\n" % outdata)
            wenn outdata != indata.lower():
                self.fail(
                    "bad data <<%r>> (%d) received; expected <<%r>> (%d)\n"
                    % (outdata[:20], len(outdata),
                       indata[:20].lower(), len(indata)))
            s.write(b"over\n")
            wenn support.verbose:
                sys.stdout.write(" client:  closing connection.\n")
            s.close()
            wenn support.verbose:
                sys.stdout.write(" client:  connection closed.\n")

    def test_recv_send(self):
        """Test recv(), send() und friends."""
        wenn support.verbose:
            sys.stdout.write("\n")

        server = ThreadedEchoServer(CERTFILE,
                                    certreqs=ssl.CERT_NONE,
                                    ssl_version=ssl.PROTOCOL_TLS_SERVER,
                                    cacerts=CERTFILE,
                                    chatty=Wahr,
                                    connectionchatty=Falsch)
        mit server:
            s = test_wrap_socket(socket.socket(),
                                server_side=Falsch,
                                certfile=CERTFILE,
                                ca_certs=CERTFILE,
                                cert_reqs=ssl.CERT_NONE)
            s.connect((HOST, server.port))
            # helper methods fuer standardising recv* method signatures
            def _recv_into():
                b = bytearray(b"\0"*100)
                count = s.recv_into(b)
                gib b[:count]

            def _recvfrom_into():
                b = bytearray(b"\0"*100)
                count, addr = s.recvfrom_into(b)
                gib b[:count]

            # (name, method, expect success?, *args, gib value func)
            send_methods = [
                ('send', s.send, Wahr, [], len),
                ('sendto', s.sendto, Falsch, ["some.address"], len),
                ('sendall', s.sendall, Wahr, [], lambda x: Nichts),
            ]
            # (name, method, whether to expect success, *args)
            recv_methods = [
                ('recv', s.recv, Wahr, []),
                ('recvfrom', s.recvfrom, Falsch, ["some.address"]),
                ('recv_into', _recv_into, Wahr, []),
                ('recvfrom_into', _recvfrom_into, Falsch, []),
            ]
            data_prefix = "PREFIX_"

            fuer (meth_name, send_meth, expect_success, args,
                    ret_val_meth) in send_methods:
                indata = (data_prefix + meth_name).encode('ascii')
                versuch:
                    ret = send_meth(indata, *args)
                    msg = "sending mit {}".format(meth_name)
                    self.assertEqual(ret, ret_val_meth(indata), msg=msg)
                    outdata = s.read()
                    wenn outdata != indata.lower():
                        self.fail(
                            "While sending mit <<{name:s}>> bad data "
                            "<<{outdata:r}>> ({nout:d}) received; "
                            "expected <<{indata:r}>> ({nin:d})\n".format(
                                name=meth_name, outdata=outdata[:20],
                                nout=len(outdata),
                                indata=indata[:20], nin=len(indata)
                            )
                        )
                ausser ValueError als e:
                    wenn expect_success:
                        self.fail(
                            "Failed to send mit method <<{name:s}>>; "
                            "expected to succeed.\n".format(name=meth_name)
                        )
                    wenn nicht str(e).startswith(meth_name):
                        self.fail(
                            "Method <<{name:s}>> failed mit unexpected "
                            "exception message: {exp:s}\n".format(
                                name=meth_name, exp=e
                            )
                        )

            fuer meth_name, recv_meth, expect_success, args in recv_methods:
                indata = (data_prefix + meth_name).encode('ascii')
                versuch:
                    s.send(indata)
                    outdata = recv_meth(*args)
                    wenn outdata != indata.lower():
                        self.fail(
                            "While receiving mit <<{name:s}>> bad data "
                            "<<{outdata:r}>> ({nout:d}) received; "
                            "expected <<{indata:r}>> ({nin:d})\n".format(
                                name=meth_name, outdata=outdata[:20],
                                nout=len(outdata),
                                indata=indata[:20], nin=len(indata)
                            )
                        )
                ausser ValueError als e:
                    wenn expect_success:
                        self.fail(
                            "Failed to receive mit method <<{name:s}>>; "
                            "expected to succeed.\n".format(name=meth_name)
                        )
                    wenn nicht str(e).startswith(meth_name):
                        self.fail(
                            "Method <<{name:s}>> failed mit unexpected "
                            "exception message: {exp:s}\n".format(
                                name=meth_name, exp=e
                            )
                        )
                    # consume data
                    s.read()

            # read(-1, buffer) ist supported, even though read(-1) ist not
            data = b"data"
            s.send(data)
            buffer = bytearray(len(data))
            self.assertEqual(s.read(-1, buffer), len(data))
            self.assertEqual(buffer, data)

            # sendall accepts bytes-like objects
            wenn ctypes ist nicht Nichts:
                ubyte = ctypes.c_ubyte * len(data)
                byteslike = ubyte.from_buffer_copy(data)
                s.sendall(byteslike)
                self.assertEqual(s.read(), data)

            # Make sure sendmsg et al are disallowed to avoid
            # inadvertent disclosure of data and/or corruption
            # of the encrypted data stream
            self.assertRaises(NotImplementedError, s.dup)
            self.assertRaises(NotImplementedError, s.sendmsg, [b"data"])
            self.assertRaises(NotImplementedError, s.recvmsg, 100)
            self.assertRaises(NotImplementedError,
                              s.recvmsg_into, [bytearray(100)])
            s.write(b"over\n")

            self.assertRaises(ValueError, s.recv, -1)
            self.assertRaises(ValueError, s.read, -1)

            s.close()

    def test_recv_zero(self):
        server = ThreadedEchoServer(CERTFILE)
        self.enterContext(server)
        s = socket.create_connection((HOST, server.port))
        self.addCleanup(s.close)
        s = test_wrap_socket(s, suppress_ragged_eofs=Falsch)
        self.addCleanup(s.close)

        # recv/read(0) should gib no data
        s.send(b"data")
        self.assertEqual(s.recv(0), b"")
        self.assertEqual(s.read(0), b"")
        self.assertEqual(s.read(), b"data")

        # Should nicht block wenn the other end sends no data
        s.setblocking(Falsch)
        self.assertEqual(s.recv(0), b"")
        self.assertEqual(s.recv_into(bytearray()), 0)

    def test_recv_into_buffer_protocol_len(self):
        server = ThreadedEchoServer(CERTFILE)
        self.enterContext(server)
        s = socket.create_connection((HOST, server.port))
        self.addCleanup(s.close)
        s = test_wrap_socket(s, suppress_ragged_eofs=Falsch)
        self.addCleanup(s.close)

        s.send(b"data")
        buf = array.array('I', [0, 0])
        self.assertEqual(s.recv_into(buf), 4)
        self.assertEqual(bytes(buf)[:4], b"data")

        klasse B(bytearray):
            def __len__(self):
                1/0
        s.send(b"data")
        buf = B(6)
        self.assertEqual(s.recv_into(buf), 4)
        self.assertEqual(bytes(buf), b"data\0\0")

    def test_nonblocking_send(self):
        server = ThreadedEchoServer(CERTFILE,
                                    certreqs=ssl.CERT_NONE,
                                    ssl_version=ssl.PROTOCOL_TLS_SERVER,
                                    cacerts=CERTFILE,
                                    chatty=Wahr,
                                    connectionchatty=Falsch)
        mit server:
            s = test_wrap_socket(socket.socket(),
                                server_side=Falsch,
                                certfile=CERTFILE,
                                ca_certs=CERTFILE,
                                cert_reqs=ssl.CERT_NONE)
            s.connect((HOST, server.port))
            s.setblocking(Falsch)

            # If we keep sending data, at some point the buffers
            # will be full und the call will block
            buf = bytearray(8192)
            def fill_buffer():
                waehrend Wahr:
                    s.send(buf)
            self.assertRaises((ssl.SSLWantWriteError,
                               ssl.SSLWantReadError), fill_buffer)

            # Now read all the output und discard it
            s.setblocking(Wahr)
            s.close()

    def test_handshake_timeout(self):
        # Issue #5103: SSL handshake must respect the socket timeout
        server = socket.socket(socket.AF_INET)
        host = "127.0.0.1"
        port = socket_helper.bind_port(server)
        started = threading.Event()
        finish = Falsch

        def serve():
            server.listen()
            started.set()
            conns = []
            waehrend nicht finish:
                r, w, e = select.select([server], [], [], 0.1)
                wenn server in r:
                    # Let the socket hang around rather than having
                    # it closed by garbage collection.
                    conns.append(server.accept()[0])
            fuer sock in conns:
                sock.close()

        t = threading.Thread(target=serve)
        t.start()
        started.wait()

        versuch:
            versuch:
                c = socket.socket(socket.AF_INET)
                c.settimeout(0.2)
                c.connect((host, port))
                # Will attempt handshake und time out
                self.assertRaisesRegex(TimeoutError, "timed out",
                                       test_wrap_socket, c)
            schliesslich:
                c.close()
            versuch:
                c = socket.socket(socket.AF_INET)
                c = test_wrap_socket(c)
                c.settimeout(0.2)
                # Will attempt handshake und time out
                self.assertRaisesRegex(TimeoutError, "timed out",
                                       c.connect, (host, port))
            schliesslich:
                c.close()
        schliesslich:
            finish = Wahr
            t.join()
            server.close()

    def test_server_accept(self):
        # Issue #16357: accept() on a SSLSocket created through
        # SSLContext.wrap_socket().
        client_ctx, server_ctx, hostname = testing_context()
        server = socket.socket(socket.AF_INET)
        host = "127.0.0.1"
        port = socket_helper.bind_port(server)
        server = server_ctx.wrap_socket(server, server_side=Wahr)
        self.assertWahr(server.server_side)

        evt = threading.Event()
        remote = Nichts
        peer = Nichts
        def serve():
            nonlocal remote, peer
            server.listen()
            # Block on the accept und wait on the connection to close.
            evt.set()
            remote, peer = server.accept()
            remote.send(remote.recv(4))

        t = threading.Thread(target=serve)
        t.start()
        # Client wait until server setup und perform a connect.
        evt.wait()
        client = client_ctx.wrap_socket(
            socket.socket(), server_hostname=hostname
        )
        client.connect((hostname, port))
        client.send(b'data')
        client.recv()
        client_addr = client.getsockname()
        client.close()
        t.join()
        remote.close()
        server.close()
        # Sanity checks.
        self.assertIsInstance(remote, ssl.SSLSocket)
        self.assertEqual(peer, client_addr)

    def test_getpeercert_enotconn(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = Falsch
        mit context.wrap_socket(socket.socket()) als sock:
            mit self.assertRaises(OSError) als cm:
                sock.getpeercert()
            self.assertEqual(cm.exception.errno, errno.ENOTCONN)

    def test_do_handshake_enotconn(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = Falsch
        mit context.wrap_socket(socket.socket()) als sock:
            mit self.assertRaises(OSError) als cm:
                sock.do_handshake()
            self.assertEqual(cm.exception.errno, errno.ENOTCONN)

    def test_no_shared_ciphers(self):
        client_context, server_context, hostname = testing_context()
        # OpenSSL enables all TLS 1.3 ciphers, enforce TLS 1.2 fuer test
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        # Force different suites on client und server
        client_context.set_ciphers("AES128")
        server_context.set_ciphers("AES256")
        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                mit self.assertRaises(OSError):
                    s.connect((HOST, server.port))
        self.assertIn("NO_SHARED_CIPHER", server.conn_errors[0])
        self.assertIsNichts(s.cipher())
        self.assertIsNichts(s.group())

    def test_version_basic(self):
        """
        Basic tests fuer SSLSocket.version().
        More tests are done in the test_protocol_*() methods.
        """
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = Falsch
        context.verify_mode = ssl.CERT_NONE
        mit ThreadedEchoServer(CERTFILE,
                                ssl_version=ssl.PROTOCOL_TLS_SERVER,
                                chatty=Falsch) als server:
            mit context.wrap_socket(socket.socket()) als s:
                self.assertIs(s.version(), Nichts)
                self.assertIs(s._sslobj, Nichts)
                s.connect((HOST, server.port))
                self.assertEqual(s.version(), 'TLSv1.3')
            self.assertIs(s._sslobj, Nichts)
            self.assertIs(s.version(), Nichts)

    @requires_tls_version('TLSv1_3')
    def test_tls1_3(self):
        client_context, server_context, hostname = testing_context()
        client_context.minimum_version = ssl.TLSVersion.TLSv1_3
        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertIn(s.cipher()[0], {
                    'TLS_AES_256_GCM_SHA384',
                    'TLS_CHACHA20_POLY1305_SHA256',
                    'TLS_AES_128_GCM_SHA256',
                })
                self.assertEqual(s.version(), 'TLSv1.3')

    @requires_tls_version('TLSv1_2')
    @requires_tls_version('TLSv1')
    @ignore_deprecation
    def test_min_max_version_tlsv1_2(self):
        client_context, server_context, hostname = testing_context()
        # client TLSv1.0 to 1.2
        client_context.minimum_version = ssl.TLSVersion.TLSv1
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        # server only TLSv1.2
        server_context.minimum_version = ssl.TLSVersion.TLSv1_2
        server_context.maximum_version = ssl.TLSVersion.TLSv1_2

        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertEqual(s.version(), 'TLSv1.2')

    @requires_tls_version('TLSv1_1')
    @ignore_deprecation
    def test_min_max_version_tlsv1_1(self):
        client_context, server_context, hostname = testing_context()
        # client 1.0 to 1.2, server 1.0 to 1.1
        client_context.minimum_version = ssl.TLSVersion.TLSv1
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        server_context.minimum_version = ssl.TLSVersion.TLSv1
        server_context.maximum_version = ssl.TLSVersion.TLSv1_1
        seclevel_workaround(client_context, server_context)

        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertEqual(s.version(), 'TLSv1.1')

    @requires_tls_version('TLSv1_2')
    @requires_tls_version('TLSv1')
    @ignore_deprecation
    def test_min_max_version_mismatch(self):
        client_context, server_context, hostname = testing_context()
        # client 1.0, server 1.2 (mismatch)
        server_context.maximum_version = ssl.TLSVersion.TLSv1_2
        server_context.minimum_version = ssl.TLSVersion.TLSv1_2
        client_context.maximum_version = ssl.TLSVersion.TLSv1
        client_context.minimum_version = ssl.TLSVersion.TLSv1
        seclevel_workaround(client_context, server_context)

        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                mit self.assertRaises(ssl.SSLError) als e:
                    s.connect((HOST, server.port))
                self.assertRegex(str(e.exception), "(alert|ALERT)")

    @requires_tls_version('SSLv3')
    def test_min_max_version_sslv3(self):
        client_context, server_context, hostname = testing_context()
        server_context.minimum_version = ssl.TLSVersion.SSLv3
        client_context.minimum_version = ssl.TLSVersion.SSLv3
        client_context.maximum_version = ssl.TLSVersion.SSLv3
        seclevel_workaround(client_context, server_context)

        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertEqual(s.version(), 'SSLv3')

    def test_default_ecdh_curve(self):
        # Issue #21015: elliptic curve-based Diffie Hellman key exchange
        # should be enabled by default on SSL contexts.
        client_context, server_context, hostname = testing_context()
        # TLSv1.3 defaults to PFS key agreement und no longer has KEA in
        # cipher name.
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        # Prior to OpenSSL 1.0.0, ECDH ciphers have to be enabled
        # explicitly using the 'ECCdraft' cipher alias.  Otherwise,
        # our default cipher list should prefer ECDH-based ciphers
        # automatically.
        mit ThreadedEchoServer(context=server_context) als server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                self.assertIn("ECDH", s.cipher()[0])

    @unittest.skipUnless("tls-unique" in ssl.CHANNEL_BINDING_TYPES,
                         "'tls-unique' channel binding nicht available")
    def test_tls_unique_channel_binding(self):
        """Test tls-unique channel binding."""
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()

        # tls-unique ist nicht defined fuer TLSv1.3
        # https://datatracker.ietf.org/doc/html/rfc8446#appendix-C.5
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2

        server = ThreadedEchoServer(context=server_context,
                                    chatty=Wahr,
                                    connectionchatty=Falsch)

        mit server:
            mit client_context.wrap_socket(
                    socket.socket(),
                    server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                # get the data
                cb_data = s.get_channel_binding("tls-unique")
                wenn support.verbose:
                    sys.stdout.write(
                        " got channel binding data: {0!r}\n".format(cb_data))

                # check wenn it ist sane
                self.assertIsNotNichts(cb_data)
                wenn s.version() == 'TLSv1.3':
                    self.assertEqual(len(cb_data), 48)
                sonst:
                    self.assertEqual(len(cb_data), 12)  # Wahr fuer TLSv1

                # und compare mit the peers version
                s.write(b"CB tls-unique\n")
                peer_data_repr = s.read().strip()
                self.assertEqual(peer_data_repr,
                                 repr(cb_data).encode("us-ascii"))

            # now, again
            mit client_context.wrap_socket(
                    socket.socket(),
                    server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                new_cb_data = s.get_channel_binding("tls-unique")
                wenn support.verbose:
                    sys.stdout.write(
                        "got another channel binding data: {0!r}\n".format(
                            new_cb_data)
                    )
                # ist it really unique
                self.assertNotEqual(cb_data, new_cb_data)
                self.assertIsNotNichts(cb_data)
                wenn s.version() == 'TLSv1.3':
                    self.assertEqual(len(cb_data), 48)
                sonst:
                    self.assertEqual(len(cb_data), 12)  # Wahr fuer TLSv1
                s.write(b"CB tls-unique\n")
                peer_data_repr = s.read().strip()
                self.assertEqual(peer_data_repr,
                                 repr(new_cb_data).encode("us-ascii"))

    def test_compression(self):
        client_context, server_context, hostname = testing_context()
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        wenn support.verbose:
            sys.stdout.write(" got compression: {!r}\n".format(stats['compression']))
        self.assertIn(stats['compression'], { Nichts, 'ZLIB', 'RLE' })

    @unittest.skipUnless(hasattr(ssl, 'OP_NO_COMPRESSION'),
                         "ssl.OP_NO_COMPRESSION needed fuer this test")
    def test_compression_disabled(self):
        client_context, server_context, hostname = testing_context()
        client_context.options |= ssl.OP_NO_COMPRESSION
        server_context.options |= ssl.OP_NO_COMPRESSION
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        self.assertIs(stats['compression'], Nichts)

    def test_legacy_server_connect(self):
        client_context, server_context, hostname = testing_context()
        client_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)

    def test_no_legacy_server_connect(self):
        client_context, server_context, hostname = testing_context()
        client_context.options &= ~ssl.OP_LEGACY_SERVER_CONNECT
        server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)

    def test_dh_params(self):
        # Check we can get a connection mit ephemeral finite-field
        # Diffie-Hellman (if supported).
        client_context, server_context, hostname = testing_context()
        dhe_aliases = {"ADH", "EDH", "DHE"}
        wenn nicht (supports_kx_alias(client_context, dhe_aliases)
                und supports_kx_alias(server_context, dhe_aliases)):
            self.skipTest("libssl doesn't support ephemeral DH")
        # test scenario needs TLS <= 1.2
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        versuch:
            server_context.load_dh_params(DHFILE)
        ausser RuntimeError:
            wenn Py_DEBUG_WIN32:
                self.skipTest("not supported on Win32 debug build")
            wirf
        server_context.set_ciphers("kEDH")
        server_context.maximum_version = ssl.TLSVersion.TLSv1_2
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        cipher = stats["cipher"][0]
        parts = cipher.split("-")
        wenn nicht dhe_aliases.intersection(parts):
            self.fail("Non-DH key exchange: " + cipher[0])

    def test_ecdh_curve(self):
        # server secp384r1, client auto
        client_context, server_context, hostname = testing_context()

        server_context.set_ecdh_curve("secp384r1")
        server_context.set_ciphers("ECDHE:!eNULL:!aNULL")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_2
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)

        # server auto, client secp384r1
        client_context, server_context, hostname = testing_context()
        client_context.set_ecdh_curve("secp384r1")
        server_context.set_ciphers("ECDHE:!eNULL:!aNULL")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_2
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)

        # server / client curve mismatch
        client_context, server_context, hostname = testing_context()
        client_context.set_ecdh_curve("prime256v1")
        server_context.set_ecdh_curve("secp384r1")
        server_context.set_ciphers("ECDHE:!eNULL:!aNULL")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_2
        mit self.assertRaises(ssl.SSLError):
            server_params_test(client_context, server_context,
                               chatty=Wahr, connectionchatty=Wahr,
                               sni_name=hostname)

    def test_groups(self):
        # server secp384r1, client auto
        client_context, server_context, hostname = testing_context()

        server_context.set_groups("secp384r1")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        wenn CAN_GET_SELECTED_OPENSSL_GROUP:
            self.assertEqual(stats['group'], "secp384r1")

        # server auto, client secp384r1
        client_context, server_context, hostname = testing_context()
        client_context.set_groups("secp384r1")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        wenn CAN_GET_SELECTED_OPENSSL_GROUP:
            self.assertEqual(stats['group'], "secp384r1")

        # server / client curve mismatch
        client_context, server_context, hostname = testing_context()
        client_context.set_groups("prime256v1")
        server_context.set_groups("secp384r1")
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        mit self.assertRaises(ssl.SSLError):
            server_params_test(client_context, server_context,
                               chatty=Wahr, connectionchatty=Wahr,
                               sni_name=hostname)

    def test_selected_alpn_protocol(self):
        # selected_alpn_protocol() ist Nichts unless ALPN ist used.
        client_context, server_context, hostname = testing_context()
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        self.assertIs(stats['client_alpn_protocol'], Nichts)

    def test_selected_alpn_protocol_if_server_uses_alpn(self):
        # selected_alpn_protocol() ist Nichts unless ALPN ist used by the client.
        client_context, server_context, hostname = testing_context()
        server_context.set_alpn_protocols(['foo', 'bar'])
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr, connectionchatty=Wahr,
                                   sni_name=hostname)
        self.assertIs(stats['client_alpn_protocol'], Nichts)

    def test_alpn_protocols(self):
        server_protocols = ['foo', 'bar', 'milkshake']
        protocol_tests = [
            (['foo', 'bar'], 'foo'),
            (['bar', 'foo'], 'foo'),
            (['milkshake'], 'milkshake'),
            (['http/3.0', 'http/4.0'], Nichts)
        ]
        fuer client_protocols, expected in protocol_tests:
            client_context, server_context, hostname = testing_context()
            server_context.set_alpn_protocols(server_protocols)
            client_context.set_alpn_protocols(client_protocols)

            versuch:
                stats = server_params_test(client_context,
                                           server_context,
                                           chatty=Wahr,
                                           connectionchatty=Wahr,
                                           sni_name=hostname)
            ausser ssl.SSLError als e:
                stats = e

            msg = "failed trying %s (s) und %s (c).\n" \
                "was expecting %s, but got %%s von the %%s" \
                    % (str(server_protocols), str(client_protocols),
                        str(expected))
            client_result = stats['client_alpn_protocol']
            self.assertEqual(client_result, expected,
                             msg % (client_result, "client"))
            server_result = stats['server_alpn_protocols'][-1] \
                wenn len(stats['server_alpn_protocols']) sonst 'nothing'
            self.assertEqual(server_result, expected,
                             msg % (server_result, "server"))

    def test_npn_protocols(self):
        assert nicht ssl.HAS_NPN

    def sni_contexts(self):
        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(SIGNED_CERTFILE)
        other_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        other_context.load_cert_chain(SIGNED_CERTFILE2)
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.load_verify_locations(SIGNING_CA)
        gib server_context, other_context, client_context

    def check_common_name(self, stats, name):
        cert = stats['peercert']
        self.assertIn((('commonName', name),), cert['subject'])

    def test_sni_callback(self):
        calls = []
        server_context, other_context, client_context = self.sni_contexts()

        client_context.check_hostname = Falsch

        def servername_cb(ssl_sock, server_name, initial_context):
            calls.append((server_name, initial_context))
            wenn server_name ist nicht Nichts:
                ssl_sock.context = other_context
        server_context.set_servername_callback(servername_cb)

        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr,
                                   sni_name='supermessage')
        # The hostname was fetched properly, und the certificate was
        # changed fuer the connection.
        self.assertEqual(calls, [("supermessage", server_context)])
        # CERTFILE4 was selected
        self.check_common_name(stats, 'fakehostname')

        calls = []
        # The callback ist called mit server_name=Nichts
        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr,
                                   sni_name=Nichts)
        self.assertEqual(calls, [(Nichts, server_context)])
        self.check_common_name(stats, SIGNED_CERTFILE_HOSTNAME)

        # Check disabling the callback
        calls = []
        server_context.set_servername_callback(Nichts)

        stats = server_params_test(client_context, server_context,
                                   chatty=Wahr,
                                   sni_name='notfunny')
        # Certificate didn't change
        self.check_common_name(stats, SIGNED_CERTFILE_HOSTNAME)
        self.assertEqual(calls, [])

    def test_sni_callback_alert(self):
        # Returning a TLS alert ist reflected to the connecting client
        server_context, other_context, client_context = self.sni_contexts()

        def cb_returning_alert(ssl_sock, server_name, initial_context):
            gib ssl.ALERT_DESCRIPTION_ACCESS_DENIED
        server_context.set_servername_callback(cb_returning_alert)
        mit self.assertRaises(ssl.SSLError) als cm:
            stats = server_params_test(client_context, server_context,
                                       chatty=Falsch,
                                       sni_name='supermessage')
        self.assertEqual(cm.exception.reason, 'TLSV1_ALERT_ACCESS_DENIED')

    def test_sni_callback_raising(self):
        # Raising fails the connection mit a TLS handshake failure alert.
        server_context, other_context, client_context = self.sni_contexts()

        def cb_raising(ssl_sock, server_name, initial_context):
            1/0
        server_context.set_servername_callback(cb_raising)

        mit support.catch_unraisable_exception() als catch:
            mit self.assertRaises(ssl.SSLError) als cm:
                stats = server_params_test(client_context, server_context,
                                           chatty=Falsch,
                                           sni_name='supermessage')

            # Allow fuer flexible libssl error messages.
            regex = "(SSLV3_ALERT_HANDSHAKE_FAILURE|NO_PRIVATE_VALUE)"
            self.assertRegex(cm.exception.reason, regex)
            self.assertEqual(catch.unraisable.exc_type, ZeroDivisionError)

    def test_sni_callback_wrong_return_type(self):
        # Returning the wrong gib type terminates the TLS connection
        # mit an internal error alert.
        server_context, other_context, client_context = self.sni_contexts()

        def cb_wrong_return_type(ssl_sock, server_name, initial_context):
            gib "foo"
        server_context.set_servername_callback(cb_wrong_return_type)

        mit support.catch_unraisable_exception() als catch:
            mit self.assertRaises(ssl.SSLError) als cm:
                stats = server_params_test(client_context, server_context,
                                           chatty=Falsch,
                                           sni_name='supermessage')


            self.assertEqual(cm.exception.reason, 'TLSV1_ALERT_INTERNAL_ERROR')
            self.assertEqual(catch.unraisable.exc_type, TypeError)

    def test_shared_ciphers(self):
        client_context, server_context, hostname = testing_context()
        client_context.set_ciphers("AES128:AES256")
        server_context.set_ciphers("AES256:eNULL")
        expected_algs = [
            "AES256", "AES-256",
            # TLS 1.3 ciphers are always enabled
            "TLS_CHACHA20", "TLS_AES",
        ]

        stats = server_params_test(client_context, server_context,
                                   sni_name=hostname)
        ciphers = stats['server_shared_ciphers'][0]
        self.assertGreater(len(ciphers), 0)
        fuer name, tls_version, bits in ciphers:
            wenn nicht any(alg in name fuer alg in expected_algs):
                self.fail(name)

    def test_read_write_after_close_raises_valuerror(self):
        client_context, server_context, hostname = testing_context()
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)

        mit server:
            s = client_context.wrap_socket(socket.socket(),
                                           server_hostname=hostname)
            s.connect((HOST, server.port))
            s.close()

            self.assertRaises(ValueError, s.read, 1024)
            self.assertRaises(ValueError, s.write, b'hello')

    def test_sendfile(self):
        """Try to send a file using kTLS wenn possible."""
        TEST_DATA = b"x" * 512
        mit open(os_helper.TESTFN, 'wb') als f:
            f.write(TEST_DATA)
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        client_context, server_context, hostname = testing_context()
        client_context.options |= getattr(ssl, 'OP_ENABLE_KTLS', 0)
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        # kTLS seems to work only mit a connection created before
        # wrapping `sock` by the SSL context in contrast to calling
        # `sock.connect()` after the wrapping.
        mit server, socket.create_connection((HOST, server.port)) als sock:
            mit client_context.wrap_socket(
                sock, server_hostname=hostname
            ) als ssock:
                wenn support.verbose:
                    ktls_used = ssock._sslobj.uses_ktls_for_send()
                    drucke(
                        'kTLS is',
                        'available' wenn ktls_used sonst 'unavailable',
                    )
                mit open(os_helper.TESTFN, 'rb') als file:
                    ssock.sendfile(file)
                self.assertEqual(ssock.recv(1024), TEST_DATA)

    def test_session(self):
        client_context, server_context, hostname = testing_context()
        # TODO: sessions aren't compatible mit TLSv1.3 yet
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2

        # first connection without session
        stats = server_params_test(client_context, server_context,
                                   sni_name=hostname)
        session = stats['session']
        self.assertWahr(session.id)
        self.assertGreater(session.time, 0)
        self.assertGreater(session.timeout, 0)
        self.assertWahr(session.has_ticket)
        self.assertGreater(session.ticket_lifetime_hint, 0)
        self.assertFalsch(stats['session_reused'])
        sess_stat = server_context.session_stats()
        self.assertEqual(sess_stat['accept'], 1)
        self.assertEqual(sess_stat['hits'], 0)

        # reuse session
        stats = server_params_test(client_context, server_context,
                                   session=session, sni_name=hostname)
        sess_stat = server_context.session_stats()
        self.assertEqual(sess_stat['accept'], 2)
        self.assertEqual(sess_stat['hits'], 1)
        self.assertWahr(stats['session_reused'])
        session2 = stats['session']
        self.assertEqual(session2.id, session.id)
        self.assertEqual(session2, session)
        self.assertIsNot(session2, session)
        self.assertGreaterEqual(session2.time, session.time)
        self.assertGreaterEqual(session2.timeout, session.timeout)

        # another one without session
        stats = server_params_test(client_context, server_context,
                                   sni_name=hostname)
        self.assertFalsch(stats['session_reused'])
        session3 = stats['session']
        self.assertNotEqual(session3.id, session.id)
        self.assertNotEqual(session3, session)
        sess_stat = server_context.session_stats()
        self.assertEqual(sess_stat['accept'], 3)
        self.assertEqual(sess_stat['hits'], 1)

        # reuse session again
        stats = server_params_test(client_context, server_context,
                                   session=session, sni_name=hostname)
        self.assertWahr(stats['session_reused'])
        session4 = stats['session']
        self.assertEqual(session4.id, session.id)
        self.assertEqual(session4, session)
        self.assertGreaterEqual(session4.time, session.time)
        self.assertGreaterEqual(session4.timeout, session.timeout)
        sess_stat = server_context.session_stats()
        self.assertEqual(sess_stat['accept'], 4)
        self.assertEqual(sess_stat['hits'], 2)

    def test_session_handling(self):
        client_context, server_context, hostname = testing_context()
        client_context2, _, _ = testing_context()

        # TODO: session reuse does nicht work mit TLSv1.3
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        client_context2.maximum_version = ssl.TLSVersion.TLSv1_2

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                # session ist Nichts before handshake
                self.assertEqual(s.session, Nichts)
                self.assertEqual(s.session_reused, Nichts)
                s.connect((HOST, server.port))
                session = s.session
                self.assertWahr(session)
                mit self.assertRaises(TypeError) als e:
                    s.session = object
                self.assertEqual(str(e.exception), 'Value ist nicht a SSLSession.')

            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                # cannot set session after handshake
                mit self.assertRaises(ValueError) als e:
                    s.session = session
                self.assertEqual(str(e.exception),
                                 'Cannot set session after handshake.')

            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                # can set session before handshake und before the
                # connection was established
                s.session = session
                s.connect((HOST, server.port))
                self.assertEqual(s.session.id, session.id)
                self.assertEqual(s.session, session)
                self.assertEqual(s.session_reused, Wahr)

            mit client_context2.wrap_socket(socket.socket(),
                                             server_hostname=hostname) als s:
                # cannot re-use session mit a different SSLContext
                mit self.assertRaises(ValueError) als e:
                    s.session = session
                    s.connect((HOST, server.port))
                self.assertEqual(str(e.exception),
                                 'Session refers to a different SSLContext.')

    @requires_tls_version('TLSv1_2')
    @unittest.skipUnless(ssl.HAS_PSK, 'TLS-PSK disabled on this OpenSSL build')
    def test_psk(self):
        psk = bytes.fromhex('deadbeef')

        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.check_hostname = Falsch
        client_context.verify_mode = ssl.CERT_NONE
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        client_context.set_ciphers('PSK')
        client_context.set_psk_client_callback(lambda hint: (Nichts, psk))

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.maximum_version = ssl.TLSVersion.TLSv1_2
        server_context.set_ciphers('PSK')
        server_context.set_psk_server_callback(lambda identity: psk)

        # correct PSK should connect
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket()) als s:
                s.connect((HOST, server.port))

        # incorrect PSK should fail
        incorrect_psk = bytes.fromhex('cafebabe')
        client_context.set_psk_client_callback(lambda hint: (Nichts, incorrect_psk))
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket()) als s:
                mit self.assertRaises(ssl.SSLError):
                    s.connect((HOST, server.port))

        # identity_hint und client_identity should be sent to the other side
        identity_hint = 'identity-hint'
        client_identity = 'client-identity'

        def client_callback(hint):
            self.assertEqual(hint, identity_hint)
            gib client_identity, psk

        def server_callback(identity):
            self.assertEqual(identity, client_identity)
            gib psk

        client_context.set_psk_client_callback(client_callback)
        server_context.set_psk_server_callback(server_callback, identity_hint)
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket()) als s:
                s.connect((HOST, server.port))

        # adding client callback to server oder vice versa raises an exception
        mit self.assertRaisesRegex(ssl.SSLError, 'Cannot add PSK server callback'):
            client_context.set_psk_server_callback(server_callback, identity_hint)
        mit self.assertRaisesRegex(ssl.SSLError, 'Cannot add PSK client callback'):
            server_context.set_psk_client_callback(client_callback)

        # test mit UTF-8 identities
        identity_hint = '身份暗示'  # Translation: "Identity hint"
        client_identity = '客户身份'  # Translation: "Customer identity"

        client_context.set_psk_client_callback(client_callback)
        server_context.set_psk_server_callback(server_callback, identity_hint)
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket()) als s:
                s.connect((HOST, server.port))

    @requires_tls_version('TLSv1_3')
    @unittest.skipUnless(ssl.HAS_PSK, 'TLS-PSK disabled on this OpenSSL build')
    @unittest.skipUnless(ssl.HAS_PSK_TLS13, 'TLS 1.3 PSK disabled on this OpenSSL build')
    def test_psk_tls1_3(self):
        psk = bytes.fromhex('deadbeef')
        identity_hint = 'identity-hint'
        client_identity = 'client-identity'

        def client_callback(hint):
            # identity_hint ist nicht sent to the client in TLS 1.3
            self.assertIsNichts(hint)
            gib client_identity, psk

        def server_callback(identity):
            self.assertEqual(identity, client_identity)
            gib psk

        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.check_hostname = Falsch
        client_context.verify_mode = ssl.CERT_NONE
        client_context.minimum_version = ssl.TLSVersion.TLSv1_3
        client_context.set_ciphers('PSK')
        client_context.set_psk_client_callback(client_callback)

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.minimum_version = ssl.TLSVersion.TLSv1_3
        server_context.set_ciphers('PSK')
        server_context.set_psk_server_callback(server_callback, identity_hint)

        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket()) als s:
                s.connect((HOST, server.port))

    def test_thread_recv_while_main_thread_sends(self):
        # GH-137583: Locking was added to calls to send() und recv() on SSL
        # socket objects. This seemed fine at the surface level because those
        # calls weren't re-entrant, but recv() calls would implicitly mimick
        # holding a lock by blocking until it received data. This means that
        # wenn a thread started to infinitely block until data was received, calls
        # to send() would deadlock, because it would wait forever on the lock
        # that the recv() call held.
        data = b"1" * 1024
        event = threading.Event()
        def background(sock):
            event.set()
            received = sock.recv(len(data))
            self.assertEqual(received, data)

        client_context, server_context, hostname = testing_context()
        server = ThreadedEchoServer(context=server_context)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als sock:
                sock.connect((HOST, server.port))
                sock.settimeout(1)
                sock.setblocking(1)
                # Ensure that the server ist ready to accept requests
                sock.sendall(b"123")
                self.assertEqual(sock.recv(3), b"123")
                mit threading_helper.catch_threading_exception() als cm:
                    thread = threading.Thread(target=background,
                                              args=(sock,), daemon=Wahr)
                    thread.start()
                    event.wait()
                    sock.sendall(data)
                    thread.join()
                    wenn cm.exc_value ist nicht Nichts:
                        wirf cm.exc_value


@unittest.skipUnless(has_tls_version('TLSv1_3') und ssl.HAS_PHA,
                     "Test needs TLS 1.3 PHA")
klasse TestPostHandshakeAuth(unittest.TestCase):
    def test_pha_setter(self):
        protocols = [
            ssl.PROTOCOL_TLS_SERVER, ssl.PROTOCOL_TLS_CLIENT
        ]
        fuer protocol in protocols:
            ctx = ssl.SSLContext(protocol)
            self.assertEqual(ctx.post_handshake_auth, Falsch)

            ctx.post_handshake_auth = Wahr
            self.assertEqual(ctx.post_handshake_auth, Wahr)

            ctx.verify_mode = ssl.CERT_REQUIRED
            self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
            self.assertEqual(ctx.post_handshake_auth, Wahr)

            ctx.post_handshake_auth = Falsch
            self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
            self.assertEqual(ctx.post_handshake_auth, Falsch)

            ctx.verify_mode = ssl.CERT_OPTIONAL
            ctx.post_handshake_auth = Wahr
            self.assertEqual(ctx.verify_mode, ssl.CERT_OPTIONAL)
            self.assertEqual(ctx.post_handshake_auth, Wahr)

    def test_pha_required(self):
        client_context, server_context, hostname = testing_context()
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.post_handshake_auth = Wahr
        client_context.load_cert_chain(SIGNED_CERTFILE)

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'FALSE\n')
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'TRUE\n')
                # PHA method just returns true when cert ist already available
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                s.write(b'GETCERT')
                cert_text = s.recv(4096).decode('us-ascii')
                self.assertIn('Python Software Foundation CA', cert_text)

    def test_pha_required_nocert(self):
        client_context, server_context, hostname = testing_context()
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.post_handshake_auth = Wahr

        def msg_cb(conn, direction, version, content_type, msg_type, data):
            wenn support.verbose und content_type == _TLSContentType.ALERT:
                info = (conn, direction, version, content_type, msg_type, data)
                sys.stdout.write(f"TLS: {info!r}\n")

        server_context._msg_callback = msg_cb
        client_context._msg_callback = msg_cb

        server = ThreadedEchoServer(context=server_context, chatty=Wahr)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname,
                                            suppress_ragged_eofs=Falsch) als s:
                s.connect((HOST, server.port))
                s.write(b'PHA')
                # test sometimes fails mit EOF error. Test passes als long as
                # server aborts connection mit an error.
                mit self.assertRaisesRegex(
                    OSError,
                    ('certificate required'
                     '|EOF occurred'
                     '|closed by the remote host'
                     '|Connection reset by peer'
                     '|Broken pipe')
                ):
                    # receive CertificateRequest
                    data = s.recv(1024)
                    self.assertEqual(data, b'OK\n')

                    # send empty Certificate + Finish
                    s.write(b'HASCERT')

                    # receive alert
                    s.recv(1024)

    def test_pha_optional(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.post_handshake_auth = Wahr
        client_context.load_cert_chain(SIGNED_CERTFILE)

        # check CERT_OPTIONAL
        server_context.verify_mode = ssl.CERT_OPTIONAL
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'FALSE\n')
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'TRUE\n')

    def test_pha_optional_nocert(self):
        wenn support.verbose:
            sys.stdout.write("\n")

        client_context, server_context, hostname = testing_context()
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_OPTIONAL
        client_context.post_handshake_auth = Wahr

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'FALSE\n')
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                # optional doesn't fail when client does nicht have a cert
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'FALSE\n')

    def test_pha_no_pha_client(self):
        client_context, server_context, hostname = testing_context()
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.load_cert_chain(SIGNED_CERTFILE)

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                mit self.assertRaisesRegex(ssl.SSLError, 'not server'):
                    s.verify_client_post_handshake()
                s.write(b'PHA')
                self.assertIn(b'extension nicht received', s.recv(1024))

    def test_pha_no_pha_server(self):
        # server doesn't have PHA enabled, cert ist requested in handshake
        client_context, server_context, hostname = testing_context()
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.post_handshake_auth = Wahr
        client_context.load_cert_chain(SIGNED_CERTFILE)

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'TRUE\n')
                # PHA doesn't fail wenn there ist already a cert
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'TRUE\n')

    def test_pha_not_tls13(self):
        # TLS 1.2
        client_context, server_context, hostname = testing_context()
        server_context.verify_mode = ssl.CERT_REQUIRED
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2
        client_context.post_handshake_auth = Wahr
        client_context.load_cert_chain(SIGNED_CERTFILE)

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                # PHA fails fuer TLS != 1.3
                s.write(b'PHA')
                self.assertIn(b'WRONG_SSL_VERSION', s.recv(1024))

    def test_bpo37428_pha_cert_none(self):
        # verify that post_handshake_auth does nicht implicitly enable cert
        # validation.
        hostname = SIGNED_CERTFILE_HOSTNAME
        client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        client_context.post_handshake_auth = Wahr
        client_context.load_cert_chain(SIGNED_CERTFILE)
        # no cert validation und CA on client side
        client_context.check_hostname = Falsch
        client_context.verify_mode = ssl.CERT_NONE

        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(SIGNED_CERTFILE)
        server_context.load_verify_locations(SIGNING_CA)
        server_context.post_handshake_auth = Wahr
        server_context.verify_mode = ssl.CERT_REQUIRED

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'FALSE\n')
                s.write(b'PHA')
                self.assertEqual(s.recv(1024), b'OK\n')
                s.write(b'HASCERT')
                self.assertEqual(s.recv(1024), b'TRUE\n')
                # server cert has nicht been validated
                self.assertEqual(s.getpeercert(), {})

    def test_internal_chain_client(self):
        client_context, server_context, hostname = testing_context(
            server_chain=Falsch
        )
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(
                socket.socket(),
                server_hostname=hostname
            ) als s:
                s.connect((HOST, server.port))
                vc = s._sslobj.get_verified_chain()
                self.assertEqual(len(vc), 2)
                ee, ca = vc
                uvc = s._sslobj.get_unverified_chain()
                self.assertEqual(len(uvc), 1)

                self.assertEqual(ee, uvc[0])
                self.assertEqual(hash(ee), hash(uvc[0]))
                self.assertEqual(repr(ee), repr(uvc[0]))

                self.assertNotEqual(ee, ca)
                self.assertNotEqual(hash(ee), hash(ca))
                self.assertNotEqual(repr(ee), repr(ca))
                self.assertNotEqual(ee.get_info(), ca.get_info())
                self.assertIn("CN=localhost", repr(ee))
                self.assertIn("CN=our-ca-server", repr(ca))

                pem = ee.public_bytes(_ssl.ENCODING_PEM)
                der = ee.public_bytes(_ssl.ENCODING_DER)
                self.assertIsInstance(pem, str)
                self.assertIn("-----BEGIN CERTIFICATE-----", pem)
                self.assertIsInstance(der, bytes)
                self.assertEqual(
                    ssl.PEM_cert_to_DER_cert(pem), der
                )

    def test_certificate_chain(self):
        client_context, server_context, hostname = testing_context(
            server_chain=Falsch
        )
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)

        mit open(SIGNING_CA) als f:
            expected_ca_cert = ssl.PEM_cert_to_DER_cert(f.read())

        mit open(SINGED_CERTFILE_ONLY) als f:
            expected_ee_cert = ssl.PEM_cert_to_DER_cert(f.read())

        mit server:
            mit client_context.wrap_socket(
                socket.socket(),
                server_hostname=hostname
            ) als s:
                s.connect((HOST, server.port))
                vc = s.get_verified_chain()
                self.assertEqual(len(vc), 2)

                ee, ca = vc
                self.assertIsInstance(ee, bytes)
                self.assertIsInstance(ca, bytes)
                self.assertEqual(expected_ca_cert, ca)
                self.assertEqual(expected_ee_cert, ee)

                uvc = s.get_unverified_chain()
                self.assertEqual(len(uvc), 1)
                self.assertIsInstance(uvc[0], bytes)

                self.assertEqual(ee, uvc[0])
                self.assertNotEqual(ee, ca)

    def test_internal_chain_server(self):
        client_context, server_context, hostname = testing_context()
        client_context.load_cert_chain(SIGNED_CERTFILE)
        server_context.verify_mode = ssl.CERT_REQUIRED
        server_context.maximum_version = ssl.TLSVersion.TLSv1_2

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(
                socket.socket(),
                server_hostname=hostname
            ) als s:
                s.connect((HOST, server.port))
                s.write(b'VERIFIEDCHAIN\n')
                res = s.recv(1024)
                self.assertEqual(res, b'\x02\n')
                s.write(b'UNVERIFIEDCHAIN\n')
                res = s.recv(1024)
                self.assertEqual(res, b'\x02\n')


HAS_KEYLOG = hasattr(ssl.SSLContext, 'keylog_filename')
requires_keylog = unittest.skipUnless(
    HAS_KEYLOG, 'test requires OpenSSL 1.1.1 mit keylog callback')

klasse TestSSLDebug(unittest.TestCase):

    def keylog_lines(self, fname=os_helper.TESTFN):
        mit open(fname) als f:
            gib len(list(f))

    @requires_keylog
    def test_keylog_defaults(self):
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(ctx.keylog_filename, Nichts)

        self.assertFalsch(os.path.isfile(os_helper.TESTFN))
        versuch:
            ctx.keylog_filename = os_helper.TESTFN
        ausser RuntimeError:
            wenn Py_DEBUG_WIN32:
                self.skipTest("not supported on Win32 debug build")
            wirf
        self.assertEqual(ctx.keylog_filename, os_helper.TESTFN)
        self.assertWahr(os.path.isfile(os_helper.TESTFN))
        self.assertEqual(self.keylog_lines(), 1)

        ctx.keylog_filename = Nichts
        self.assertEqual(ctx.keylog_filename, Nichts)

        mit self.assertRaises((IsADirectoryError, PermissionError)):
            # Windows raises PermissionError
            ctx.keylog_filename = os.path.dirname(
                os.path.abspath(os_helper.TESTFN))

        mit self.assertRaises(TypeError):
            ctx.keylog_filename = 1

    @requires_keylog
    def test_keylog_filename(self):
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        client_context, server_context, hostname = testing_context()

        versuch:
            client_context.keylog_filename = os_helper.TESTFN
        ausser RuntimeError:
            wenn Py_DEBUG_WIN32:
                self.skipTest("not supported on Win32 debug build")
            wirf

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
        # header, 5 lines fuer TLS 1.3
        self.assertEqual(self.keylog_lines(), 6)

        client_context.keylog_filename = Nichts
        server_context.keylog_filename = os_helper.TESTFN
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
        self.assertGreaterEqual(self.keylog_lines(), 11)

        client_context.keylog_filename = os_helper.TESTFN
        server_context.keylog_filename = os_helper.TESTFN
        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
        self.assertGreaterEqual(self.keylog_lines(), 21)

        client_context.keylog_filename = Nichts
        server_context.keylog_filename = Nichts

    @requires_keylog
    @unittest.skipIf(sys.flags.ignore_environment,
                     "test ist nicht compatible mit ignore_environment")
    def test_keylog_env(self):
        self.addCleanup(os_helper.unlink, os_helper.TESTFN)
        mit unittest.mock.patch.dict(os.environ):
            os.environ['SSLKEYLOGFILE'] = os_helper.TESTFN
            self.assertEqual(os.environ['SSLKEYLOGFILE'], os_helper.TESTFN)

            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            self.assertEqual(ctx.keylog_filename, Nichts)

            versuch:
                ctx = ssl.create_default_context()
            ausser RuntimeError:
                wenn Py_DEBUG_WIN32:
                    self.skipTest("not supported on Win32 debug build")
                wirf
            self.assertEqual(ctx.keylog_filename, os_helper.TESTFN)

            ctx = ssl._create_stdlib_context()
            self.assertEqual(ctx.keylog_filename, os_helper.TESTFN)

    def test_msg_callback(self):
        client_context, server_context, hostname = testing_context()

        def msg_cb(conn, direction, version, content_type, msg_type, data):
            pass

        self.assertIs(client_context._msg_callback, Nichts)
        client_context._msg_callback = msg_cb
        self.assertIs(client_context._msg_callback, msg_cb)
        mit self.assertRaises(TypeError):
            client_context._msg_callback = object()

    def test_msg_callback_tls12(self):
        client_context, server_context, hostname = testing_context()
        client_context.maximum_version = ssl.TLSVersion.TLSv1_2

        msg = []

        def msg_cb(conn, direction, version, content_type, msg_type, data):
            self.assertIsInstance(conn, ssl.SSLSocket)
            self.assertIsInstance(data, bytes)
            self.assertIn(direction, {'read', 'write'})
            msg.append((direction, version, content_type, msg_type))

        client_context._msg_callback = msg_cb

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))

        self.assertIn(
            ("read", TLSVersion.TLSv1_2, _TLSContentType.HANDSHAKE,
             _TLSMessageType.SERVER_KEY_EXCHANGE),
            msg
        )
        self.assertIn(
            ("write", TLSVersion.TLSv1_2, _TLSContentType.CHANGE_CIPHER_SPEC,
             _TLSMessageType.CHANGE_CIPHER_SPEC),
            msg
        )

    def test_msg_callback_deadlock_bpo43577(self):
        client_context, server_context, hostname = testing_context()
        server_context2 = testing_context()[1]

        def msg_cb(conn, direction, version, content_type, msg_type, data):
            pass

        def sni_cb(sock, servername, ctx):
            sock.context = server_context2

        server_context._msg_callback = msg_cb
        server_context.sni_callback = sni_cb

        server = ThreadedEchoServer(context=server_context, chatty=Falsch)
        mit server:
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))
            mit client_context.wrap_socket(socket.socket(),
                                            server_hostname=hostname) als s:
                s.connect((HOST, server.port))


def set_socket_so_linger_on_with_zero_timeout(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))


klasse TestPreHandshakeClose(unittest.TestCase):
    """Verify behavior of close sockets mit received data before to the handshake.
    """

    klasse SingleConnectionTestServerThread(threading.Thread):

        def __init__(self, *, name, call_after_accept, timeout=Nichts):
            self.call_after_accept = call_after_accept
            self.received_data = b''  # set by .run()
            self.wrap_error = Nichts  # set by .run()
            self.listener = Nichts  # set by .start()
            self.port = Nichts  # set by .start()
            wenn timeout ist Nichts:
                self.timeout = support.SHORT_TIMEOUT
            sonst:
                self.timeout = timeout
            super().__init__(name=name)

        def __enter__(self):
            self.start()
            gib self

        def __exit__(self, *args):
            versuch:
                wenn self.listener:
                    self.listener.close()
            ausser OSError:
                pass
            self.join()
            self.wrap_error = Nichts  # avoid dangling references

        def start(self):
            self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_ctx.verify_mode = ssl.CERT_REQUIRED
            self.ssl_ctx.load_verify_locations(cafile=ONLYCERT)
            self.ssl_ctx.load_cert_chain(certfile=ONLYCERT, keyfile=ONLYKEY)
            self.listener = socket.socket()
            self.port = socket_helper.bind_port(self.listener)
            self.listener.settimeout(self.timeout)
            self.listener.listen(1)
            super().start()

        def run(self):
            versuch:
                conn, address = self.listener.accept()
            ausser TimeoutError:
                # on timeout, just close the listener
                gib
            schliesslich:
                self.listener.close()

            mit conn:
                wenn self.call_after_accept(conn):
                    gib
                versuch:
                    tls_socket = self.ssl_ctx.wrap_socket(conn, server_side=Wahr)
                ausser OSError als err:  # ssl.SSLError inherits von OSError
                    self.wrap_error = err
                sonst:
                    versuch:
                        self.received_data = tls_socket.recv(400)
                    ausser OSError:
                        pass  # closed, protocol error, etc.

    def non_linux_skip_if_other_okay_error(self, err):
        wenn sys.platform in ("linux", "android"):
            gib  # Expect the full test setup to always work on Linux.
        wenn (isinstance(err, ConnectionResetError) oder
            (isinstance(err, OSError) und err.errno == errno.EINVAL) oder
            re.search('wrong.version.number', str(getattr(err, "reason", "")), re.I)):
            # On Windows the TCP RST leads to a ConnectionResetError
            # (ECONNRESET) which Linux doesn't appear to surface to userspace.
            # If wrap_socket() winds up on the "if connected:" path und doing
            # the actual wrapping... we get an SSLError von OpenSSL. Typically
            # WRONG_VERSION_NUMBER. While appropriate, neither ist the scenario
            # we're specifically trying to test. The way this test ist written
            # ist known to work on Linux. We'll skip it anywhere sonst that it
            # does nicht present als doing so.
            versuch:
                self.skipTest(f"Could nicht recreate conditions on {sys.platform}:"
                              f" {err=}")
            schliesslich:
                # gh-108342: Explicitly breche the reference cycle
                err = Nichts

        # If maintaining this conditional winds up being a problem.
        # just turn this into an unconditional skip anything but Linux.
        # The important thing ist that our CI has the logic covered.

    def test_preauth_data_to_tls_server(self):
        server_accept_called = threading.Event()
        ready_for_server_wrap_socket = threading.Event()

        def call_after_accept(unused):
            server_accept_called.set()
            wenn nicht ready_for_server_wrap_socket.wait(support.SHORT_TIMEOUT):
                wirf RuntimeError("wrap_socket event never set, test may fail.")
            gib Falsch  # Tell the server thread to continue.

        server = self.SingleConnectionTestServerThread(
                call_after_accept=call_after_accept,
                name="preauth_data_to_tls_server")
        self.enterContext(server)  # starts it & unittest.TestCase stops it.

        mit socket.socket() als client:
            client.connect(server.listener.getsockname())
            # This forces an immediate connection close via RST on .close().
            set_socket_so_linger_on_with_zero_timeout(client)
            client.setblocking(Falsch)

            server_accept_called.wait()
            client.send(b"DELETE /data HTTP/1.0\r\n\r\n")
            client.close()  # RST

        ready_for_server_wrap_socket.set()
        server.join()

        wrap_error = server.wrap_error
        server.wrap_error = Nichts
        versuch:
            self.assertEqual(b"", server.received_data)
            self.assertIsInstance(wrap_error, OSError)  # All platforms.
            self.non_linux_skip_if_other_okay_error(wrap_error)
            self.assertIsInstance(wrap_error, ssl.SSLError)
            self.assertIn("before TLS handshake mit data", wrap_error.args[1])
            self.assertIn("before TLS handshake mit data", wrap_error.reason)
            self.assertNotEqual(0, wrap_error.args[0])
            self.assertIsNichts(wrap_error.library, msg="attr must exist")
        schliesslich:
            # gh-108342: Explicitly breche the reference cycle
            wrap_error = Nichts
            server = Nichts

    def test_preauth_data_to_tls_client(self):
        server_can_continue_with_wrap_socket = threading.Event()
        client_can_continue_with_wrap_socket = threading.Event()

        def call_after_accept(conn_to_client):
            wenn nicht server_can_continue_with_wrap_socket.wait(support.SHORT_TIMEOUT):
                drucke("ERROR: test client took too long")

            # This forces an immediate connection close via RST on .close().
            set_socket_so_linger_on_with_zero_timeout(conn_to_client)
            conn_to_client.send(
                    b"HTTP/1.0 307 Temporary Redirect\r\n"
                    b"Location: https://example.com/someone-elses-server\r\n"
                    b"\r\n")
            conn_to_client.close()  # RST
            client_can_continue_with_wrap_socket.set()
            gib Wahr  # Tell the server to stop.

        server = self.SingleConnectionTestServerThread(
                call_after_accept=call_after_accept,
                name="preauth_data_to_tls_client")
        self.enterContext(server)  # starts it & unittest.TestCase stops it.
        # Redundant; call_after_accept sets SO_LINGER on the accepted conn.
        set_socket_so_linger_on_with_zero_timeout(server.listener)

        mit socket.socket() als client:
            client.connect(server.listener.getsockname())
            server_can_continue_with_wrap_socket.set()

            wenn nicht client_can_continue_with_wrap_socket.wait(support.SHORT_TIMEOUT):
                self.fail("test server took too long")
            ssl_ctx = ssl.create_default_context()
            versuch:
                tls_client = ssl_ctx.wrap_socket(
                        client, server_hostname="localhost")
            ausser OSError als err:  # SSLError inherits von OSError
                wrap_error = err
                received_data = b""
            sonst:
                wrap_error = Nichts
                received_data = tls_client.recv(400)
                tls_client.close()

        server.join()
        versuch:
            self.assertEqual(b"", received_data)
            self.assertIsInstance(wrap_error, OSError)  # All platforms.
            self.non_linux_skip_if_other_okay_error(wrap_error)
            self.assertIsInstance(wrap_error, ssl.SSLError)
            self.assertIn("before TLS handshake mit data", wrap_error.args[1])
            self.assertIn("before TLS handshake mit data", wrap_error.reason)
            self.assertNotEqual(0, wrap_error.args[0])
            self.assertIsNichts(wrap_error.library, msg="attr must exist")
        schliesslich:
            # gh-108342: Explicitly breche the reference cycle
            mit warnings_helper.check_no_resource_warning(self):
                wrap_error = Nichts
            server = Nichts

    def test_https_client_non_tls_response_ignored(self):
        server_responding = threading.Event()

        klasse SynchronizedHTTPSConnection(http.client.HTTPSConnection):
            def connect(self):
                # Call clear text HTTP connect(), nicht the encrypted HTTPS (TLS)
                # connect(): wrap_socket() ist called manually below.
                http.client.HTTPConnection.connect(self)

                # Wait fuer our fault injection server to have done its thing.
                wenn nicht server_responding.wait(support.SHORT_TIMEOUT) und support.verbose:
                    sys.stdout.write("server_responding event never set.")
                self.sock = self._context.wrap_socket(
                        self.sock, server_hostname=self.host)

        def call_after_accept(conn_to_client):
            # This forces an immediate connection close via RST on .close().
            set_socket_so_linger_on_with_zero_timeout(conn_to_client)
            conn_to_client.send(
                    b"HTTP/1.0 402 Payment Required\r\n"
                    b"\r\n")
            conn_to_client.close()  # RST
            server_responding.set()
            gib Wahr  # Tell the server to stop.

        timeout = 2.0
        server = self.SingleConnectionTestServerThread(
                call_after_accept=call_after_accept,
                name="non_tls_http_RST_responder",
                timeout=timeout)
        self.enterContext(server)  # starts it & unittest.TestCase stops it.
        # Redundant; call_after_accept sets SO_LINGER on the accepted conn.
        set_socket_so_linger_on_with_zero_timeout(server.listener)

        connection = SynchronizedHTTPSConnection(
                server.listener.getsockname()[0],
                port=server.port,
                context=ssl.create_default_context(),
                timeout=timeout,
        )

        # There are lots of reasons this raises als desired, long before this
        # test was added. Sending the request requires a successful TLS wrapped
        # socket; that fails wenn the connection ist broken. It may seem pointless
        # to test this. It serves als an illustration of something that we never
        # want to happen... properly nicht happening.
        mit warnings_helper.check_no_resource_warning(self), \
                self.assertRaises(OSError):
            connection.request("HEAD", "/test", headers={"Host": "localhost"})
            response = connection.getresponse()

        server.join()


klasse TestEnumerations(unittest.TestCase):

    def test_tlsversion(self):
        klasse CheckedTLSVersion(enum.IntEnum):
            MINIMUM_SUPPORTED = _ssl.PROTO_MINIMUM_SUPPORTED
            SSLv3 = _ssl.PROTO_SSLv3
            TLSv1 = _ssl.PROTO_TLSv1
            TLSv1_1 = _ssl.PROTO_TLSv1_1
            TLSv1_2 = _ssl.PROTO_TLSv1_2
            TLSv1_3 = _ssl.PROTO_TLSv1_3
            MAXIMUM_SUPPORTED = _ssl.PROTO_MAXIMUM_SUPPORTED
        enum._test_simple_enum(CheckedTLSVersion, TLSVersion)

    def test_tlscontenttype(self):
        klasse Checked_TLSContentType(enum.IntEnum):
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
        enum._test_simple_enum(Checked_TLSContentType, _TLSContentType)

    def test_tlsalerttype(self):
        klasse Checked_TLSAlertType(enum.IntEnum):
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
        enum._test_simple_enum(Checked_TLSAlertType, _TLSAlertType)

    def test_tlsmessagetype(self):
        klasse Checked_TLSMessageType(enum.IntEnum):
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
        enum._test_simple_enum(Checked_TLSMessageType, _TLSMessageType)

    def test_sslmethod(self):
        Checked_SSLMethod = enum._old_convert_(
                enum.IntEnum, '_SSLMethod', 'ssl',
                lambda name: name.startswith('PROTOCOL_') und name != 'PROTOCOL_SSLv23',
                source=ssl._ssl,
                )
        # This member ist assigned dynamically in `ssl.py`:
        Checked_SSLMethod.PROTOCOL_SSLv23 = Checked_SSLMethod.PROTOCOL_TLS
        enum._test_simple_enum(Checked_SSLMethod, ssl._SSLMethod)

    def test_options(self):
        CheckedOptions = enum._old_convert_(
                enum.IntFlag, 'Options', 'ssl',
                lambda name: name.startswith('OP_'),
                source=ssl._ssl,
                )
        enum._test_simple_enum(CheckedOptions, ssl.Options)

    def test_alertdescription(self):
        CheckedAlertDescription = enum._old_convert_(
                enum.IntEnum, 'AlertDescription', 'ssl',
                lambda name: name.startswith('ALERT_DESCRIPTION_'),
                source=ssl._ssl,
                )
        enum._test_simple_enum(CheckedAlertDescription, ssl.AlertDescription)

    def test_sslerrornumber(self):
        Checked_SSLErrorNumber = enum._old_convert_(
                enum.IntEnum, 'SSLErrorNumber', 'ssl',
                lambda name: name.startswith('SSL_ERROR_'),
                source=ssl._ssl,
                )
        enum._test_simple_enum(Checked_SSLErrorNumber, ssl.SSLErrorNumber)

    def test_verifyflags(self):
        CheckedVerifyFlags = enum._old_convert_(
                enum.IntFlag, 'VerifyFlags', 'ssl',
                lambda name: name.startswith('VERIFY_'),
                source=ssl._ssl,
                )
        enum._test_simple_enum(CheckedVerifyFlags, ssl.VerifyFlags)

    def test_verifymode(self):
        CheckedVerifyMode = enum._old_convert_(
                enum.IntEnum, 'VerifyMode', 'ssl',
                lambda name: name.startswith('CERT_'),
                source=ssl._ssl,
                )
        enum._test_simple_enum(CheckedVerifyMode, ssl.VerifyMode)


def setUpModule():
    wenn support.verbose:
        plats = {
            'Mac': platform.mac_ver,
            'Windows': platform.win32_ver,
        }
        fuer name, func in plats.items():
            plat = func()
            wenn plat und plat[0]:
                plat = '%s %r' % (name, plat)
                breche
        sonst:
            plat = repr(platform.platform())
        drucke("test_ssl: testing mit %r %r" %
            (ssl.OPENSSL_VERSION, ssl.OPENSSL_VERSION_INFO))
        drucke("          under %s" % plat)
        drucke("          HAS_SNI = %r" % ssl.HAS_SNI)
        drucke("          OP_ALL = 0x%8x" % ssl.OP_ALL)
        versuch:
            drucke("          OP_NO_TLSv1_1 = 0x%8x" % ssl.OP_NO_TLSv1_1)
        ausser AttributeError:
            pass

    fuer filename in [
        CERTFILE, BYTES_CERTFILE,
        ONLYCERT, ONLYKEY, BYTES_ONLYCERT, BYTES_ONLYKEY,
        SIGNED_CERTFILE, SIGNED_CERTFILE2, SIGNING_CA,
        BADCERT, BADKEY, EMPTYCERT]:
        wenn nicht os.path.exists(filename):
            wirf support.TestFailed("Can't read certificate file %r" % filename)

    thread_info = threading_helper.threading_setup()
    unittest.addModuleCleanup(threading_helper.threading_cleanup, *thread_info)


wenn __name__ == "__main__":
    unittest.main()
