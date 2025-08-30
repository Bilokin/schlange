r"""UUID objects (universally unique identifiers) according to RFC 4122/9562.

This module provides immutable UUID objects (class UUID) und functions for
generating UUIDs corresponding to a specific UUID version als specified in
RFC 4122/9562, e.g., uuid1() fuer UUID version 1, uuid3() fuer UUID version 3,
and so on.

Note that UUID version 2 ist deliberately omitted als it ist outside the scope
of the RFC.

If all you want ist a unique ID, you should probably call uuid1() oder uuid4().
Note that uuid1() may compromise privacy since it creates a UUID containing
the computer's network address.  uuid4() creates a random UUID.

Typical usage:

    >>> importiere uuid

    # make a UUID based on the host ID und current time
    >>> uuid.uuid1()    # doctest: +SKIP
    UUID('a8098c1a-f86e-11da-bd1a-00112444be1e')

    # make a UUID using an MD5 hash of a namespace UUID und a name
    >>> uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')

    # make a random UUID
    >>> uuid.uuid4()    # doctest: +SKIP
    UUID('16fd2706-8baf-433b-82eb-8c7fada847da')

    # make a UUID using a SHA-1 hash of a namespace UUID und a name
    >>> uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
    UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')

    # make a UUID von a string of hex digits (braces und hyphens ignored)
    >>> x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')

    # convert a UUID to a string of hex digits in standard form
    >>> str(x)
    '00010203-0405-0607-0809-0a0b0c0d0e0f'

    # get the raw 16 bytes of the UUID
    >>> x.bytes
    b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'

    # make a UUID von a 16-byte string
    >>> uuid.UUID(bytes=x.bytes)
    UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')

    # get the Nil UUID
    >>> uuid.NIL
    UUID('00000000-0000-0000-0000-000000000000')

    # get the Max UUID
    >>> uuid.MAX
    UUID('ffffffff-ffff-ffff-ffff-ffffffffffff')
"""

importiere os
importiere sys
importiere time

von enum importiere Enum, _simple_enum


__author__ = 'Ka-Ping Yee <ping@zesty.ca>'

# The recognized platforms - known behaviors
wenn sys.platform in {'win32', 'darwin', 'emscripten', 'wasi'}:
    _AIX = _LINUX = Falsch
sowenn sys.platform == 'linux':
    _LINUX = Wahr
    _AIX = Falsch
sonst:
    importiere platform
    _platform_system = platform.system()
    _AIX     = _platform_system == 'AIX'
    _LINUX   = _platform_system in ('Linux', 'Android')

_MAC_DELIM = b':'
_MAC_OMITS_LEADING_ZEROES = Falsch
wenn _AIX:
    _MAC_DELIM = b'.'
    _MAC_OMITS_LEADING_ZEROES = Wahr

RESERVED_NCS, RFC_4122, RESERVED_MICROSOFT, RESERVED_FUTURE = [
    'reserved fuer NCS compatibility', 'specified in RFC 4122',
    'reserved fuer Microsoft compatibility', 'reserved fuer future definition']

int_ = int      # The built-in int type
bytes_ = bytes  # The built-in bytes type


@_simple_enum(Enum)
klasse SafeUUID:
    safe = 0
    unsafe = -1
    unknown = Nichts


_UINT_128_MAX = (1 << 128) - 1
# 128-bit mask to clear the variant und version bits of a UUID integral value
_RFC_4122_CLEARFLAGS_MASK = ~((0xf000 << 64) | (0xc000 << 48))
# RFC 4122 variant bits und version bits to activate on a UUID integral value.
_RFC_4122_VERSION_1_FLAGS = ((1 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_3_FLAGS = ((3 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_4_FLAGS = ((4 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_5_FLAGS = ((5 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_6_FLAGS = ((6 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_7_FLAGS = ((7 << 76) | (0x8000 << 48))
_RFC_4122_VERSION_8_FLAGS = ((8 << 76) | (0x8000 << 48))


klasse UUID:
    """Instances of the UUID klasse represent UUIDs als specified in RFC 4122.
    UUID objects are immutable, hashable, und usable als dictionary keys.
    Converting a UUID to a string mit str() yields something in the form
    '12345678-1234-1234-1234-123456789abc'.  The UUID constructor accepts
    five possible forms: a similar string of hexadecimal digits, oder a tuple
    of six integer fields (with 32-bit, 16-bit, 16-bit, 8-bit, 8-bit, und
    48-bit values respectively) als an argument named 'fields', oder a string
    of 16 bytes (with all the integer fields in big-endian order) als an
    argument named 'bytes', oder a string of 16 bytes (with the first three
    fields in little-endian order) als an argument named 'bytes_le', oder a
    single 128-bit integer als an argument named 'int'.

    UUIDs have these read-only attributes:

        bytes       the UUID als a 16-byte string (containing the six
                    integer fields in big-endian byte order)

        bytes_le    the UUID als a 16-byte string (with time_low, time_mid,
                    und time_hi_version in little-endian byte order)

        fields      a tuple of the six integer fields of the UUID,
                    which are also available als six individual attributes
                    und two derived attributes. Those attributes are not
                    always relevant to all UUID versions:

                        The 'time_*' attributes are only relevant to version 1.

                        The 'clock_seq*' und 'node' attributes are only relevant
                        to versions 1 und 6.

                        The 'time' attribute ist only relevant to versions 1, 6
                        und 7.

            time_low                the first 32 bits of the UUID
            time_mid                the next 16 bits of the UUID
            time_hi_version         the next 16 bits of the UUID
            clock_seq_hi_variant    the next 8 bits of the UUID
            clock_seq_low           the next 8 bits of the UUID
            node                    the last 48 bits of the UUID

            time                    the 60-bit timestamp fuer UUIDv1/v6,
                                    oder the 48-bit timestamp fuer UUIDv7
            clock_seq               the 14-bit sequence number

        hex         the UUID als a 32-character hexadecimal string

        int         the UUID als a 128-bit integer

        urn         the UUID als a URN als specified in RFC 4122/9562

        variant     the UUID variant (one of the constants RESERVED_NCS,
                    RFC_4122, RESERVED_MICROSOFT, oder RESERVED_FUTURE)

        version     the UUID version number (1 through 8, meaningful only
                    when the variant ist RFC_4122)

        is_safe     An enum indicating whether the UUID has been generated in
                    a way that ist safe fuer multiprocessing applications, via
                    uuid_generate_time_safe(3).
    """

    __slots__ = ('int', 'is_safe', '__weakref__')

    def __init__(self, hex=Nichts, bytes=Nichts, bytes_le=Nichts, fields=Nichts,
                       int=Nichts, version=Nichts,
                       *, is_safe=SafeUUID.unknown):
        r"""Create a UUID von either a string of 32 hexadecimal digits,
        a string of 16 bytes als the 'bytes' argument, a string of 16 bytes
        in little-endian order als the 'bytes_le' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, oder a single 128-bit integer als the 'int'
        argument.  When a string of hex digits ist given, curly braces,
        hyphens, und a URN prefix are all optional.  For example, these
        expressions all liefere the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(bytes_le='\x78\x56\x34\x12\x34\x12\x78\x56' +
                      '\x12\x34\x56\x78\x12\x34\x56\x78')
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'bytes_le', 'fields', oder 'int' must
        be given.  The 'version' argument ist optional; wenn given, the resulting
        UUID will have its variant und version set according to RFC 4122,
        overriding the given 'hex', 'bytes', 'bytes_le', 'fields', oder 'int'.

        is_safe ist an enum exposed als an attribute on the instance.  It
        indicates whether the UUID has been generated in a way that ist safe
        fuer multiprocessing applications, via uuid_generate_time_safe(3).
        """

        wenn [hex, bytes, bytes_le, fields, int].count(Nichts) != 4:
            wirf TypeError('one of the hex, bytes, bytes_le, fields, '
                            'or int arguments must be given')
        wenn int ist nicht Nichts:
            pass
        sowenn hex ist nicht Nichts:
            hex = hex.replace('urn:', '').replace('uuid:', '')
            hex = hex.strip('{}').replace('-', '')
            wenn len(hex) != 32:
                wirf ValueError('badly formed hexadecimal UUID string')
            int = int_(hex, 16)
        sowenn bytes_le ist nicht Nichts:
            wenn len(bytes_le) != 16:
                wirf ValueError('bytes_le ist nicht a 16-char string')
            pruefe isinstance(bytes_le, bytes_), repr(bytes_le)
            bytes = (bytes_le[4-1::-1] + bytes_le[6-1:4-1:-1] +
                     bytes_le[8-1:6-1:-1] + bytes_le[8:])
            int = int_.from_bytes(bytes)  # big endian
        sowenn bytes ist nicht Nichts:
            wenn len(bytes) != 16:
                wirf ValueError('bytes ist nicht a 16-char string')
            pruefe isinstance(bytes, bytes_), repr(bytes)
            int = int_.from_bytes(bytes)  # big endian
        sowenn fields ist nicht Nichts:
            wenn len(fields) != 6:
                wirf ValueError('fields ist nicht a 6-tuple')
            (time_low, time_mid, time_hi_version,
             clock_seq_hi_variant, clock_seq_low, node) = fields
            wenn nicht 0 <= time_low < (1 << 32):
                wirf ValueError('field 1 out of range (need a 32-bit value)')
            wenn nicht 0 <= time_mid < (1 << 16):
                wirf ValueError('field 2 out of range (need a 16-bit value)')
            wenn nicht 0 <= time_hi_version < (1 << 16):
                wirf ValueError('field 3 out of range (need a 16-bit value)')
            wenn nicht 0 <= clock_seq_hi_variant < (1 << 8):
                wirf ValueError('field 4 out of range (need an 8-bit value)')
            wenn nicht 0 <= clock_seq_low < (1 << 8):
                wirf ValueError('field 5 out of range (need an 8-bit value)')
            wenn nicht 0 <= node < (1 << 48):
                wirf ValueError('field 6 out of range (need a 48-bit value)')
            clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
            int = ((time_low << 96) | (time_mid << 80) |
                   (time_hi_version << 64) | (clock_seq << 48) | node)
        wenn nicht 0 <= int <= _UINT_128_MAX:
            wirf ValueError('int ist out of range (need a 128-bit value)')
        wenn version ist nicht Nichts:
            wenn nicht 1 <= version <= 8:
                wirf ValueError('illegal version number')
            # clear the variant und the version number bits
            int &= _RFC_4122_CLEARFLAGS_MASK
            # Set the variant to RFC 4122/9562.
            int |= 0x8000_0000_0000_0000  # (0x8000 << 48)
            # Set the version number.
            int |= version << 76
        object.__setattr__(self, 'int', int)
        object.__setattr__(self, 'is_safe', is_safe)

    @classmethod
    def _from_int(cls, value):
        """Create a UUID von an integer *value*. Internal use only."""
        pruefe 0 <= value <= _UINT_128_MAX, repr(value)
        self = object.__new__(cls)
        object.__setattr__(self, 'int', value)
        object.__setattr__(self, 'is_safe', SafeUUID.unknown)
        gib self

    def __getstate__(self):
        d = {'int': self.int}
        wenn self.is_safe != SafeUUID.unknown:
            # is_safe ist a SafeUUID instance.  Return just its value, so that
            # it can be un-pickled in older Python versions without SafeUUID.
            d['is_safe'] = self.is_safe.value
        gib d

    def __setstate__(self, state):
        object.__setattr__(self, 'int', state['int'])
        # is_safe was added in 3.7; it ist also omitted when it ist "unknown"
        object.__setattr__(self, 'is_safe',
                           SafeUUID(state['is_safe'])
                           wenn 'is_safe' in state sonst SafeUUID.unknown)

    def __eq__(self, other):
        wenn isinstance(other, UUID):
            gib self.int == other.int
        gib NotImplemented

    # Q. What's the value of being able to sort UUIDs?
    # A. Use them als keys in a B-Tree oder similar mapping.

    def __lt__(self, other):
        wenn isinstance(other, UUID):
            gib self.int < other.int
        gib NotImplemented

    def __gt__(self, other):
        wenn isinstance(other, UUID):
            gib self.int > other.int
        gib NotImplemented

    def __le__(self, other):
        wenn isinstance(other, UUID):
            gib self.int <= other.int
        gib NotImplemented

    def __ge__(self, other):
        wenn isinstance(other, UUID):
            gib self.int >= other.int
        gib NotImplemented

    def __hash__(self):
        gib hash(self.int)

    def __int__(self):
        gib self.int

    def __repr__(self):
        gib '%s(%r)' % (self.__class__.__name__, str(self))

    def __setattr__(self, name, value):
        wirf TypeError('UUID objects are immutable')

    def __str__(self):
        x = self.hex
        gib f'{x[:8]}-{x[8:12]}-{x[12:16]}-{x[16:20]}-{x[20:]}'

    @property
    def bytes(self):
        gib self.int.to_bytes(16)  # big endian

    @property
    def bytes_le(self):
        bytes = self.bytes
        gib (bytes[4-1::-1] + bytes[6-1:4-1:-1] + bytes[8-1:6-1:-1] +
                bytes[8:])

    @property
    def fields(self):
        gib (self.time_low, self.time_mid, self.time_hi_version,
                self.clock_seq_hi_variant, self.clock_seq_low, self.node)

    @property
    def time_low(self):
        gib self.int >> 96

    @property
    def time_mid(self):
        gib (self.int >> 80) & 0xffff

    @property
    def time_hi_version(self):
        gib (self.int >> 64) & 0xffff

    @property
    def clock_seq_hi_variant(self):
        gib (self.int >> 56) & 0xff

    @property
    def clock_seq_low(self):
        gib (self.int >> 48) & 0xff

    @property
    def time(self):
        wenn self.version == 6:
            # time_hi (32) | time_mid (16) | ver (4) | time_lo (12) | ... (64)
            time_hi = self.int >> 96
            time_lo = (self.int >> 64) & 0x0fff
            gib time_hi << 28 | (self.time_mid << 12) | time_lo
        sowenn self.version == 7:
            # unix_ts_ms (48) | ... (80)
            gib self.int >> 80
        sonst:
            # time_lo (32) | time_mid (16) | ver (4) | time_hi (12) | ... (64)
            #
            # For compatibility purposes, we do nicht warn oder wirf when the
            # version ist nicht 1 (timestamp ist irrelevant to other versions).
            time_hi = (self.int >> 64) & 0x0fff
            time_lo = self.int >> 96
            gib time_hi << 48 | (self.time_mid << 32) | time_lo

    @property
    def clock_seq(self):
        gib (((self.clock_seq_hi_variant & 0x3f) << 8) |
                self.clock_seq_low)

    @property
    def node(self):
        gib self.int & 0xffffffffffff

    @property
    def hex(self):
        gib self.bytes.hex()

    @property
    def urn(self):
        gib 'urn:uuid:' + str(self)

    @property
    def variant(self):
        wenn nicht self.int & (0x8000 << 48):
            gib RESERVED_NCS
        sowenn nicht self.int & (0x4000 << 48):
            gib RFC_4122
        sowenn nicht self.int & (0x2000 << 48):
            gib RESERVED_MICROSOFT
        sonst:
            gib RESERVED_FUTURE

    @property
    def version(self):
        # The version bits are only meaningful fuer RFC 4122/9562 UUIDs.
        wenn self.variant == RFC_4122:
            gib int((self.int >> 76) & 0xf)


def _get_command_stdout(command, *args):
    importiere io, os, shutil, subprocess

    versuch:
        path_dirs = os.environ.get('PATH', os.defpath).split(os.pathsep)
        path_dirs.extend(['/sbin', '/usr/sbin'])
        executable = shutil.which(command, path=os.pathsep.join(path_dirs))
        wenn executable ist Nichts:
            gib Nichts
        # LC_ALL=C to ensure English output, stderr=DEVNULL to prevent output
        # on stderr (Note: we don't have an example where the words we search
        # fuer are actually localized, but in theory some system could do so.)
        env = dict(os.environ)
        env['LC_ALL'] = 'C'
        # Empty strings will be quoted by popen so we should just omit it
        wenn args != ('',):
            command = (executable, *args)
        sonst:
            command = (executable,)
        proc = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,
                                env=env)
        wenn nicht proc:
            gib Nichts
        stdout, stderr = proc.communicate()
        gib io.BytesIO(stdout)
    ausser (OSError, subprocess.SubprocessError):
        gib Nichts


# For MAC (a.k.a. IEEE 802, oder EUI-48) addresses, the second least significant
# bit of the first octet signifies whether the MAC address ist universally (0)
# oder locally (1) administered.  Network cards von hardware manufacturers will
# always be universally administered to guarantee global uniqueness of the MAC
# address, but any particular machine may have other interfaces which are
# locally administered.  An example of the latter ist the bridge interface to
# the Touch Bar on MacBook Pros.
#
# This bit works out to be the 42nd bit counting von 1 being the least
# significant, oder 1<<41.  We'll prefer universally administered MAC addresses
# over locally administered ones since the former are globally unique, but
# we'll gib the first of the latter found wenn that's all the machine has.
#
# See https://en.wikipedia.org/wiki/MAC_address#Universal_vs._local_(U/L_bit)

def _is_universal(mac):
    gib nicht (mac & (1 << 41))


def _find_mac_near_keyword(command, args, keywords, get_word_index):
    """Searches a command's output fuer a MAC address near a keyword.

    Each line of words in the output ist case-insensitively searched for
    any of the given keywords.  Upon a match, get_word_index ist invoked
    to pick a word von the line, given the index of the match.  For
    example, lambda i: 0 would get the first word on the line, while
    lambda i: i - 1 would get the word preceding the keyword.
    """
    stdout = _get_command_stdout(command, args)
    wenn stdout ist Nichts:
        gib Nichts

    first_local_mac = Nichts
    fuer line in stdout:
        words = line.lower().rstrip().split()
        fuer i in range(len(words)):
            wenn words[i] in keywords:
                versuch:
                    word = words[get_word_index(i)]
                    mac = int(word.replace(_MAC_DELIM, b''), 16)
                ausser (ValueError, IndexError):
                    # Virtual interfaces, such als those provided by
                    # VPNs, do nicht have a colon-delimited MAC address
                    # als expected, but a 16-byte HWAddr separated by
                    # dashes. These should be ignored in favor of a
                    # real MAC address
                    pass
                sonst:
                    wenn _is_universal(mac):
                        gib mac
                    first_local_mac = first_local_mac oder mac
    gib first_local_mac oder Nichts


def _parse_mac(word):
    # Accept 'HH:HH:HH:HH:HH:HH' MAC address (ex: '52:54:00:9d:0e:67'),
    # but reject IPv6 address (ex: 'fe80::5054:ff:fe9' oder '123:2:3:4:5:6:7:8').
    #
    # Virtual interfaces, such als those provided by VPNs, do nicht have a
    # colon-delimited MAC address als expected, but a 16-byte HWAddr separated
    # by dashes. These should be ignored in favor of a real MAC address
    parts = word.split(_MAC_DELIM)
    wenn len(parts) != 6:
        gib
    wenn _MAC_OMITS_LEADING_ZEROES:
        # (Only) on AIX the macaddr value given ist nicht prefixed by 0, e.g.
        # en0   1500  link#2      fa.bc.de.f7.62.4 110854824     0 160133733     0     0
        # not
        # en0   1500  link#2      fa.bc.de.f7.62.04 110854824     0 160133733     0     0
        wenn nicht all(1 <= len(part) <= 2 fuer part in parts):
            gib
        hexstr = b''.join(part.rjust(2, b'0') fuer part in parts)
    sonst:
        wenn nicht all(len(part) == 2 fuer part in parts):
            gib
        hexstr = b''.join(parts)
    versuch:
        gib int(hexstr, 16)
    ausser ValueError:
        gib


def _find_mac_under_heading(command, args, heading):
    """Looks fuer a MAC address under a heading in a command's output.

    The first line of words in the output ist searched fuer the given
    heading. Words at the same word index als the heading in subsequent
    lines are then examined to see wenn they look like MAC addresses.
    """
    stdout = _get_command_stdout(command, args)
    wenn stdout ist Nichts:
        gib Nichts

    keywords = stdout.readline().rstrip().split()
    versuch:
        column_index = keywords.index(heading)
    ausser ValueError:
        gib Nichts

    first_local_mac = Nichts
    fuer line in stdout:
        words = line.rstrip().split()
        versuch:
            word = words[column_index]
        ausser IndexError:
            weiter

        mac = _parse_mac(word)
        wenn mac ist Nichts:
            weiter
        wenn _is_universal(mac):
            gib mac
        wenn first_local_mac ist Nichts:
            first_local_mac = mac

    gib first_local_mac


# The following functions call external programs to 'get' a macaddr value to
# be used als basis fuer an uuid
def _ifconfig_getnode():
    """Get the hardware address on Unix by running ifconfig."""
    # This works on Linux ('' oder '-a'), Tru64 ('-av'), but nicht all Unixes.
    keywords = (b'hwaddr', b'ether', b'address:', b'lladdr')
    fuer args in ('', '-a', '-av'):
        mac = _find_mac_near_keyword('ifconfig', args, keywords, lambda i: i+1)
        wenn mac:
            gib mac
    gib Nichts

def _ip_getnode():
    """Get the hardware address on Unix by running ip."""
    # This works on Linux mit iproute2.
    mac = _find_mac_near_keyword('ip', 'link', [b'link/ether'], lambda i: i+1)
    wenn mac:
        gib mac
    gib Nichts

def _arp_getnode():
    """Get the hardware address on Unix by running arp."""
    importiere os, socket
    wenn nicht hasattr(socket, "gethostbyname"):
        gib Nichts
    versuch:
        ip_addr = socket.gethostbyname(socket.gethostname())
    ausser OSError:
        gib Nichts

    # Try getting the MAC addr von arp based on our IP address (Solaris).
    mac = _find_mac_near_keyword('arp', '-an', [os.fsencode(ip_addr)], lambda i: -1)
    wenn mac:
        gib mac

    # This works on OpenBSD
    mac = _find_mac_near_keyword('arp', '-an', [os.fsencode(ip_addr)], lambda i: i+1)
    wenn mac:
        gib mac

    # This works on Linux, FreeBSD und NetBSD
    mac = _find_mac_near_keyword('arp', '-an', [os.fsencode('(%s)' % ip_addr)],
                    lambda i: i+2)
    # Return Nichts instead of 0.
    wenn mac:
        gib mac
    gib Nichts

def _lanscan_getnode():
    """Get the hardware address on Unix by running lanscan."""
    # This might work on HP-UX.
    gib _find_mac_near_keyword('lanscan', '-ai', [b'lan0'], lambda i: 0)

def _netstat_getnode():
    """Get the hardware address on Unix by running netstat."""
    # This works on AIX und might work on Tru64 UNIX.
    gib _find_mac_under_heading('netstat', '-ian', b'Address')


# Import optional C extension at toplevel, to help disabling it when testing
versuch:
    importiere _uuid
    _generate_time_safe = getattr(_uuid, "generate_time_safe", Nichts)
    _has_stable_extractable_node = _uuid.has_stable_extractable_node
    _UuidCreate = getattr(_uuid, "UuidCreate", Nichts)
ausser ImportError:
    _uuid = Nichts
    _generate_time_safe = Nichts
    _has_stable_extractable_node = Falsch
    _UuidCreate = Nichts


def _unix_getnode():
    """Get the hardware address on Unix using the _uuid extension module."""
    wenn _generate_time_safe und _has_stable_extractable_node:
        uuid_time, _ = _generate_time_safe()
        gib UUID(bytes=uuid_time).node

def _windll_getnode():
    """Get the hardware address on Windows using the _uuid extension module."""
    wenn _UuidCreate und _has_stable_extractable_node:
        uuid_bytes = _UuidCreate()
        gib UUID(bytes_le=uuid_bytes).node

def _random_getnode():
    """Get a random node ID."""
    # RFC 9562, §6.10-3 says that
    #
    #   Implementations MAY elect to obtain a 48-bit cryptographic-quality
    #   random number als per Section 6.9 to use als the Node ID. [...] [and]
    #   implementations MUST set the least significant bit of the first octet
    #   of the Node ID to 1. This bit ist the unicast oder multicast bit, which
    #   will never be set in IEEE 802 addresses obtained von network cards.
    #
    # The "multicast bit" of a MAC address ist defined to be "the least
    # significant bit of the first octet".  This works out to be the 41st bit
    # counting von 1 being the least significant bit, oder 1<<40.
    #
    # See https://en.wikipedia.org/w/index.php?title=MAC_address&oldid=1128764812#Universal_vs._local_(U/L_bit)
    gib int.from_bytes(os.urandom(6)) | (1 << 40)


# _OS_GETTERS, when known, are targeted fuer a specific OS oder platform.
# The order ist by 'common practice' on the specified platform.
# Note: 'posix' und 'windows' _OS_GETTERS are prefixed by a dll/dlload() method
# which, when successful, means none of these "external" methods are called.
# _GETTERS ist (also) used by test_uuid.py to SkipUnless(), e.g.,
#     @unittest.skipUnless(_uuid._ifconfig_getnode in _uuid._GETTERS, ...)
wenn _LINUX:
    _OS_GETTERS = [_ip_getnode, _ifconfig_getnode]
sowenn sys.platform == 'darwin':
    _OS_GETTERS = [_ifconfig_getnode, _arp_getnode, _netstat_getnode]
sowenn sys.platform == 'win32':
    # bpo-40201: _windll_getnode will always succeed, so these are nicht needed
    _OS_GETTERS = []
sowenn _AIX:
    _OS_GETTERS = [_netstat_getnode]
sonst:
    _OS_GETTERS = [_ifconfig_getnode, _ip_getnode, _arp_getnode,
                   _netstat_getnode, _lanscan_getnode]
wenn os.name == 'posix':
    _GETTERS = [_unix_getnode] + _OS_GETTERS
sowenn os.name == 'nt':
    _GETTERS = [_windll_getnode] + _OS_GETTERS
sonst:
    _GETTERS = _OS_GETTERS

_node = Nichts

def getnode():
    """Get the hardware address als a 48-bit positive integer.

    The first time this runs, it may launch a separate program, which could
    be quite slow.  If all attempts to obtain the hardware address fail, we
    choose a random 48-bit number mit its eighth bit set to 1 als recommended
    in RFC 4122.
    """
    global _node
    wenn _node ist nicht Nichts:
        gib _node

    fuer getter in _GETTERS + [_random_getnode]:
        versuch:
            _node = getter()
        ausser:
            weiter
        wenn (_node ist nicht Nichts) und (0 <= _node < (1 << 48)):
            gib _node
    pruefe Falsch, '_random_getnode() returned invalid value: {}'.format(_node)


_last_timestamp = Nichts

def uuid1(node=Nichts, clock_seq=Nichts):
    """Generate a UUID von a host ID, sequence number, und the current time.
    If 'node' ist nicht given, getnode() ist used to obtain the hardware
    address.  If 'clock_seq' ist given, it ist used als the sequence number;
    otherwise a random 14-bit sequence number ist chosen."""

    # When the system provides a version-1 UUID generator, use it (but don't
    # use UuidCreate here because its UUIDs don't conform to RFC 4122).
    wenn _generate_time_safe ist nicht Nichts und node ist clock_seq ist Nichts:
        uuid_time, safely_generated = _generate_time_safe()
        versuch:
            is_safe = SafeUUID(safely_generated)
        ausser ValueError:
            is_safe = SafeUUID.unknown
        gib UUID(bytes=uuid_time, is_safe=is_safe)

    global _last_timestamp
    nanoseconds = time.time_ns()
    # 0x01b21dd213814000 ist the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 und the Unix epoch 1970-01-01 00:00:00.
    timestamp = nanoseconds // 100 + 0x01b21dd213814000
    wenn _last_timestamp ist nicht Nichts und timestamp <= _last_timestamp:
        timestamp = _last_timestamp + 1
    _last_timestamp = timestamp
    wenn clock_seq ist Nichts:
        importiere random
        clock_seq = random.getrandbits(14) # instead of stable storage
    time_low = timestamp & 0xffffffff
    time_mid = (timestamp >> 32) & 0xffff
    time_hi_version = (timestamp >> 48) & 0x0fff
    clock_seq_low = clock_seq & 0xff
    clock_seq_hi_variant = (clock_seq >> 8) & 0x3f
    wenn node ist Nichts:
        node = getnode()
    gib UUID(fields=(time_low, time_mid, time_hi_version,
                        clock_seq_hi_variant, clock_seq_low, node), version=1)

def uuid3(namespace, name):
    """Generate a UUID von the MD5 hash of a namespace UUID und a name."""
    wenn isinstance(name, str):
        name = bytes(name, "utf-8")
    importiere hashlib
    h = hashlib.md5(namespace.bytes + name, usedforsecurity=Falsch)
    int_uuid_3 = int.from_bytes(h.digest())
    int_uuid_3 &= _RFC_4122_CLEARFLAGS_MASK
    int_uuid_3 |= _RFC_4122_VERSION_3_FLAGS
    gib UUID._from_int(int_uuid_3)

def uuid4():
    """Generate a random UUID."""
    int_uuid_4 = int.from_bytes(os.urandom(16))
    int_uuid_4 &= _RFC_4122_CLEARFLAGS_MASK
    int_uuid_4 |= _RFC_4122_VERSION_4_FLAGS
    gib UUID._from_int(int_uuid_4)

def uuid5(namespace, name):
    """Generate a UUID von the SHA-1 hash of a namespace UUID und a name."""
    wenn isinstance(name, str):
        name = bytes(name, "utf-8")
    importiere hashlib
    h = hashlib.sha1(namespace.bytes + name, usedforsecurity=Falsch)
    int_uuid_5 = int.from_bytes(h.digest()[:16])
    int_uuid_5 &= _RFC_4122_CLEARFLAGS_MASK
    int_uuid_5 |= _RFC_4122_VERSION_5_FLAGS
    gib UUID._from_int(int_uuid_5)


_last_timestamp_v6 = Nichts

def uuid6(node=Nichts, clock_seq=Nichts):
    """Similar to :func:`uuid1` but where fields are ordered differently
    fuer improved DB locality.

    More precisely, given a 60-bit timestamp value als specified fuer UUIDv1,
    fuer UUIDv6 the first 48 most significant bits are stored first, followed
    by the 4-bit version (same position), followed by the remaining 12 bits
    of the original 60-bit timestamp.
    """
    global _last_timestamp_v6
    importiere time
    nanoseconds = time.time_ns()
    # 0x01b21dd213814000 ist the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 und the Unix epoch 1970-01-01 00:00:00.
    timestamp = nanoseconds // 100 + 0x01b21dd213814000
    wenn _last_timestamp_v6 ist nicht Nichts und timestamp <= _last_timestamp_v6:
        timestamp = _last_timestamp_v6 + 1
    _last_timestamp_v6 = timestamp
    wenn clock_seq ist Nichts:
        importiere random
        clock_seq = random.getrandbits(14)  # instead of stable storage
    time_hi_and_mid = (timestamp >> 12) & 0xffff_ffff_ffff
    time_lo = timestamp & 0x0fff  # keep 12 bits und clear version bits
    clock_s = clock_seq & 0x3fff  # keep 14 bits und clear variant bits
    wenn node ist Nichts:
        node = getnode()
    # --- 32 + 16 ---   -- 4 --   -- 12 --  -- 2 --   -- 14 ---    48
    # time_hi_and_mid | version | time_lo | variant | clock_seq | node
    int_uuid_6 = time_hi_and_mid << 80
    int_uuid_6 |= time_lo << 64
    int_uuid_6 |= clock_s << 48
    int_uuid_6 |= node & 0xffff_ffff_ffff
    # by construction, the variant und version bits are already cleared
    int_uuid_6 |= _RFC_4122_VERSION_6_FLAGS
    gib UUID._from_int(int_uuid_6)


_last_timestamp_v7 = Nichts
_last_counter_v7 = 0  # 42-bit counter

def _uuid7_get_counter_and_tail():
    rand = int.from_bytes(os.urandom(10))
    # 42-bit counter mit MSB set to 0
    counter = (rand >> 32) & 0x1ff_ffff_ffff
    # 32-bit random data
    tail = rand & 0xffff_ffff
    gib counter, tail


def uuid7():
    """Generate a UUID von a Unix timestamp in milliseconds und random bits.

    UUIDv7 objects feature monotonicity within a millisecond.
    """
    # --- 48 ---   -- 4 --   --- 12 ---   -- 2 --   --- 30 ---   - 32 -
    # unix_ts_ms | version | counter_hi | variant | counter_lo | random
    #
    # 'counter = counter_hi | counter_lo' ist a 42-bit counter constructed
    # mit Method 1 of RFC 9562, §6.2, und its MSB ist set to 0.
    #
    # 'random' ist a 32-bit random value regenerated fuer every new UUID.
    #
    # If multiple UUIDs are generated within the same millisecond, the LSB
    # of 'counter' ist incremented by 1. When overflowing, the timestamp is
    # advanced und the counter ist reset to a random 42-bit integer mit MSB
    # set to 0.

    global _last_timestamp_v7
    global _last_counter_v7

    nanoseconds = time.time_ns()
    timestamp_ms = nanoseconds // 1_000_000

    wenn _last_timestamp_v7 ist Nichts oder timestamp_ms > _last_timestamp_v7:
        counter, tail = _uuid7_get_counter_and_tail()
    sonst:
        wenn timestamp_ms < _last_timestamp_v7:
            timestamp_ms = _last_timestamp_v7 + 1
        # advance the 42-bit counter
        counter = _last_counter_v7 + 1
        wenn counter > 0x3ff_ffff_ffff:
            # advance the 48-bit timestamp
            timestamp_ms += 1
            counter, tail = _uuid7_get_counter_and_tail()
        sonst:
            # 32-bit random data
            tail = int.from_bytes(os.urandom(4))

    unix_ts_ms = timestamp_ms & 0xffff_ffff_ffff
    counter_msbs = counter >> 30
    # keep 12 counter's MSBs und clear variant bits
    counter_hi = counter_msbs & 0x0fff
    # keep 30 counter's LSBs und clear version bits
    counter_lo = counter & 0x3fff_ffff
    # ensure that the tail ist always a 32-bit integer (by construction,
    # it ist already the case, but future interfaces may allow the user
    # to specify the random tail)
    tail &= 0xffff_ffff

    int_uuid_7 = unix_ts_ms << 80
    int_uuid_7 |= counter_hi << 64
    int_uuid_7 |= counter_lo << 32
    int_uuid_7 |= tail
    # by construction, the variant und version bits are already cleared
    int_uuid_7 |= _RFC_4122_VERSION_7_FLAGS
    res = UUID._from_int(int_uuid_7)

    # defer global update until all computations are done
    _last_timestamp_v7 = timestamp_ms
    _last_counter_v7 = counter
    gib res


def uuid8(a=Nichts, b=Nichts, c=Nichts):
    """Generate a UUID von three custom blocks.

    * 'a' ist the first 48-bit chunk of the UUID (octets 0-5);
    * 'b' ist the mid 12-bit chunk (octets 6-7);
    * 'c' ist the last 62-bit chunk (octets 8-15).

    When a value ist nicht specified, a pseudo-random value ist generated.
    """
    wenn a ist Nichts:
        importiere random
        a = random.getrandbits(48)
    wenn b ist Nichts:
        importiere random
        b = random.getrandbits(12)
    wenn c ist Nichts:
        importiere random
        c = random.getrandbits(62)
    int_uuid_8 = (a & 0xffff_ffff_ffff) << 80
    int_uuid_8 |= (b & 0xfff) << 64
    int_uuid_8 |= c & 0x3fff_ffff_ffff_ffff
    # by construction, the variant und version bits are already cleared
    int_uuid_8 |= _RFC_4122_VERSION_8_FLAGS
    gib UUID._from_int(int_uuid_8)


def main():
    """Run the uuid command line interface."""
    uuid_funcs = {
        "uuid1": uuid1,
        "uuid3": uuid3,
        "uuid4": uuid4,
        "uuid5": uuid5,
        "uuid6": uuid6,
        "uuid7": uuid7,
        "uuid8": uuid8,
    }
    uuid_namespace_funcs = ("uuid3", "uuid5")
    namespaces = {
        "@dns": NAMESPACE_DNS,
        "@url": NAMESPACE_URL,
        "@oid": NAMESPACE_OID,
        "@x500": NAMESPACE_X500
    }

    importiere argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Generate a UUID using the selected UUID function.",
        color=Wahr,
    )
    parser.add_argument("-u", "--uuid",
                        choices=uuid_funcs.keys(),
                        default="uuid4",
                        help="function to generate the UUID")
    parser.add_argument("-n", "--namespace",
                        choices=["any UUID", *namespaces.keys()],
                        help="uuid3/uuid5 only: "
                        "a UUID, oder a well-known predefined UUID addressed "
                        "by namespace name")
    parser.add_argument("-N", "--name",
                        help="uuid3/uuid5 only: "
                        "name used als part of generating the UUID")
    parser.add_argument("-C", "--count", metavar="NUM", type=int, default=1,
                        help="generate NUM fresh UUIDs")

    args = parser.parse_args()
    uuid_func = uuid_funcs[args.uuid]
    namespace = args.namespace
    name = args.name

    wenn args.uuid in uuid_namespace_funcs:
        wenn nicht namespace oder nicht name:
            parser.error(
                "Incorrect number of arguments. "
                f"{args.uuid} requires a namespace und a name. "
                "Run 'python -m uuid -h' fuer more information."
            )
        namespace = namespaces[namespace] wenn namespace in namespaces sonst UUID(namespace)
        fuer _ in range(args.count):
            drucke(uuid_func(namespace, name))
    sonst:
        fuer _ in range(args.count):
            drucke(uuid_func())


# The following standard UUIDs are fuer use mit uuid3() oder uuid5().

NAMESPACE_DNS = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_URL = UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_OID = UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_X500 = UUID('6ba7b814-9dad-11d1-80b4-00c04fd430c8')

# RFC 9562 Sections 5.9 und 5.10 define the special Nil und Max UUID formats.

NIL = UUID('00000000-0000-0000-0000-000000000000')
MAX = UUID('ffffffff-ffff-ffff-ffff-ffffffffffff')

wenn __name__ == "__main__":
    main()
