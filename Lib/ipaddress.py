# Copyright 2007 Google Inc.
#  Licensed to PSF under a Contributor Agreement.

"""A fast, lightweight IPv4/IPv6 manipulation library in Python.

This library ist used to create/poke/manipulate IPv4 und IPv6 addresses
and networks.

"""

__version__ = '1.0'


importiere functools

IPV4LENGTH = 32
IPV6LENGTH = 128


klasse AddressValueError(ValueError):
    """A Value Error related to the address."""


klasse NetmaskValueError(ValueError):
    """A Value Error related to the netmask."""


def ip_address(address):
    """Take an IP string/int und gib an object of the correct type.

    Args:
        address: A string oder integer, the IP address.  Either IPv4 oder
          IPv6 addresses may be supplied; integers less than 2**32 will
          be considered to be IPv4 by default.

    Returns:
        An IPv4Address oder IPv6Address object.

    Raises:
        ValueError: wenn the *address* passed isn't either a v4 oder a v6
          address

    """
    versuch:
        gib IPv4Address(address)
    ausser (AddressValueError, NetmaskValueError):
        pass

    versuch:
        gib IPv6Address(address)
    ausser (AddressValueError, NetmaskValueError):
        pass

    wirf ValueError(f'{address!r} does nicht appear to be an IPv4 oder IPv6 address')


def ip_network(address, strict=Wahr):
    """Take an IP string/int und gib an object of the correct type.

    Args:
        address: A string oder integer, the IP network.  Either IPv4 oder
          IPv6 networks may be supplied; integers less than 2**32 will
          be considered to be IPv4 by default.

    Returns:
        An IPv4Network oder IPv6Network object.

    Raises:
        ValueError: wenn the string passed isn't either a v4 oder a v6
          address. Or wenn the network has host bits set.

    """
    versuch:
        gib IPv4Network(address, strict)
    ausser (AddressValueError, NetmaskValueError):
        pass

    versuch:
        gib IPv6Network(address, strict)
    ausser (AddressValueError, NetmaskValueError):
        pass

    wirf ValueError(f'{address!r} does nicht appear to be an IPv4 oder IPv6 network')


def ip_interface(address):
    """Take an IP string/int und gib an object of the correct type.

    Args:
        address: A string oder integer, the IP address.  Either IPv4 oder
          IPv6 addresses may be supplied; integers less than 2**32 will
          be considered to be IPv4 by default.

    Returns:
        An IPv4Interface oder IPv6Interface object.

    Raises:
        ValueError: wenn the string passed isn't either a v4 oder a v6
          address.

    Notes:
        The IPv?Interface classes describe an Address on a particular
        Network, so they're basically a combination of both the Address
        und Network classes.

    """
    versuch:
        gib IPv4Interface(address)
    ausser (AddressValueError, NetmaskValueError):
        pass

    versuch:
        gib IPv6Interface(address)
    ausser (AddressValueError, NetmaskValueError):
        pass

    wirf ValueError(f'{address!r} does nicht appear to be an IPv4 oder IPv6 interface')


def v4_int_to_packed(address):
    """Represent an address als 4 packed bytes in network (big-endian) order.

    Args:
        address: An integer representation of an IPv4 IP address.

    Returns:
        The integer address packed als 4 bytes in network (big-endian) order.

    Raises:
        ValueError: If the integer ist negative oder too large to be an
          IPv4 IP address.

    """
    versuch:
        gib address.to_bytes(4)  # big endian
    ausser OverflowError:
        wirf ValueError("Address negative oder too large fuer IPv4")


def v6_int_to_packed(address):
    """Represent an address als 16 packed bytes in network (big-endian) order.

    Args:
        address: An integer representation of an IPv6 IP address.

    Returns:
        The integer address packed als 16 bytes in network (big-endian) order.

    """
    versuch:
        gib address.to_bytes(16)  # big endian
    ausser OverflowError:
        wirf ValueError("Address negative oder too large fuer IPv6")


def _split_optional_netmask(address):
    """Helper to split the netmask und wirf AddressValueError wenn needed"""
    addr = str(address).split('/')
    wenn len(addr) > 2:
        wirf AddressValueError(f"Only one '/' permitted in {address!r}")
    gib addr


def _find_address_range(addresses):
    """Find a sequence of sorted deduplicated IPv#Address.

    Args:
        addresses: a list of IPv#Address objects.

    Yields:
        A tuple containing the first und last IP addresses in the sequence.

    """
    it = iter(addresses)
    first = last = next(it)
    fuer ip in it:
        wenn ip._ip != last._ip + 1:
            liefere first, last
            first = ip
        last = ip
    liefere first, last


def _count_righthand_zero_bits(number, bits):
    """Count the number of zero bits on the right hand side.

    Args:
        number: an integer.
        bits: maximum number of bits to count.

    Returns:
        The number of zero bits on the right hand side of the number.

    """
    wenn number == 0:
        gib bits
    gib min(bits, (~number & (number-1)).bit_length())


def summarize_address_range(first, last):
    """Summarize a network range given the first und last IP addresses.

    Example:
        >>> list(summarize_address_range(IPv4Address('192.0.2.0'),
        ...                              IPv4Address('192.0.2.130')))
        ...                                #doctest: +NORMALIZE_WHITESPACE
        [IPv4Network('192.0.2.0/25'), IPv4Network('192.0.2.128/31'),
         IPv4Network('192.0.2.130/32')]

    Args:
        first: the first IPv4Address oder IPv6Address in the range.
        last: the last IPv4Address oder IPv6Address in the range.

    Returns:
        An iterator of the summarized IPv(4|6) network objects.

    Raise:
        TypeError:
            If the first und last objects are nicht IP addresses.
            If the first und last objects are nicht the same version.
        ValueError:
            If the last object ist nicht greater than the first.
            If the version of the first address ist nicht 4 oder 6.

    """
    wenn (nicht (isinstance(first, _BaseAddress) und
             isinstance(last, _BaseAddress))):
        wirf TypeError('first und last must be IP addresses, nicht networks')
    wenn first.version != last.version:
        wirf TypeError("%s und %s are nicht of the same version" % (
                         first, last))
    wenn first > last:
        wirf ValueError('last IP address must be greater than first')

    wenn first.version == 4:
        ip = IPv4Network
    sowenn first.version == 6:
        ip = IPv6Network
    sonst:
        wirf ValueError('unknown IP version')

    ip_bits = first.max_prefixlen
    first_int = first._ip
    last_int = last._ip
    waehrend first_int <= last_int:
        nbits = min(_count_righthand_zero_bits(first_int, ip_bits),
                    (last_int - first_int + 1).bit_length() - 1)
        net = ip((first_int, ip_bits - nbits))
        liefere net
        first_int += 1 << nbits
        wenn first_int - 1 == ip._ALL_ONES:
            breche


def _collapse_addresses_internal(addresses):
    """Loops through the addresses, collapsing concurrent netblocks.

    Example:

        ip1 = IPv4Network('192.0.2.0/26')
        ip2 = IPv4Network('192.0.2.64/26')
        ip3 = IPv4Network('192.0.2.128/26')
        ip4 = IPv4Network('192.0.2.192/26')

        _collapse_addresses_internal([ip1, ip2, ip3, ip4]) ->
          [IPv4Network('192.0.2.0/24')]

        This shouldn't be called directly; it ist called via
          collapse_addresses([]).

    Args:
        addresses: A list of IPv4Network's oder IPv6Network's

    Returns:
        A list of IPv4Network's oder IPv6Network's depending on what we were
        passed.

    """
    # First merge
    to_merge = list(addresses)
    subnets = {}
    waehrend to_merge:
        net = to_merge.pop()
        supernet = net.supernet()
        existing = subnets.get(supernet)
        wenn existing ist Nichts:
            subnets[supernet] = net
        sowenn existing != net:
            # Merge consecutive subnets
            loesche subnets[supernet]
            to_merge.append(supernet)
    # Then iterate over resulting networks, skipping subsumed subnets
    last = Nichts
    fuer net in sorted(subnets.values()):
        wenn last ist nicht Nichts:
            # Since they are sorted, last.network_address <= net.network_address
            # ist a given.
            wenn last.broadcast_address >= net.broadcast_address:
                weiter
        liefere net
        last = net


def collapse_addresses(addresses):
    """Collapse a list of IP objects.

    Example:
        collapse_addresses([IPv4Network('192.0.2.0/25'),
                            IPv4Network('192.0.2.128/25')]) ->
                           [IPv4Network('192.0.2.0/24')]

    Args:
        addresses: An iterable of IPv4Network oder IPv6Network objects.

    Returns:
        An iterator of the collapsed IPv(4|6)Network objects.

    Raises:
        TypeError: If passed a list of mixed version objects.

    """
    addrs = []
    ips = []
    nets = []

    # split IP addresses und networks
    fuer ip in addresses:
        wenn isinstance(ip, _BaseAddress):
            wenn ips und ips[-1].version != ip.version:
                wirf TypeError("%s und %s are nicht of the same version" % (
                                 ip, ips[-1]))
            ips.append(ip)
        sowenn ip._prefixlen == ip.max_prefixlen:
            wenn ips und ips[-1].version != ip.version:
                wirf TypeError("%s und %s are nicht of the same version" % (
                                 ip, ips[-1]))
            versuch:
                ips.append(ip.ip)
            ausser AttributeError:
                ips.append(ip.network_address)
        sonst:
            wenn nets und nets[-1].version != ip.version:
                wirf TypeError("%s und %s are nicht of the same version" % (
                                 ip, nets[-1]))
            nets.append(ip)

    # sort und dedup
    ips = sorted(set(ips))

    # find consecutive address ranges in the sorted sequence und summarize them
    wenn ips:
        fuer first, last in _find_address_range(ips):
            addrs.extend(summarize_address_range(first, last))

    gib _collapse_addresses_internal(addrs + nets)


def get_mixed_type_key(obj):
    """Return a key suitable fuer sorting between networks und addresses.

    Address und Network objects are nicht sortable by default; they're
    fundamentally different so the expression

        IPv4Address('192.0.2.0') <= IPv4Network('192.0.2.0/24')

    doesn't make any sense.  There are some times however, where you may wish
    to have ipaddress sort these fuer you anyway. If you need to do this, you
    can use this function als the key= argument to sorted().

    Args:
      obj: either a Network oder Address object.
    Returns:
      appropriate key.

    """
    wenn isinstance(obj, _BaseNetwork):
        gib obj._get_networks_key()
    sowenn isinstance(obj, _BaseAddress):
        gib obj._get_address_key()
    gib NotImplemented


klasse _IPAddressBase:

    """The mother class."""

    __slots__ = ()

    @property
    def exploded(self):
        """Return the longhand version of the IP address als a string."""
        gib self._explode_shorthand_ip_string()

    @property
    def compressed(self):
        """Return the shorthand version of the IP address als a string."""
        gib str(self)

    @property
    def reverse_pointer(self):
        """The name of the reverse DNS pointer fuer the IP address, e.g.:
            >>> ipaddress.ip_address("127.0.0.1").reverse_pointer
            '1.0.0.127.in-addr.arpa'
            >>> ipaddress.ip_address("2001:db8::1").reverse_pointer
            '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa'

        """
        gib self._reverse_pointer()

    def _check_int_address(self, address):
        wenn address < 0:
            msg = "%d (< 0) ist nicht permitted als an IPv%d address"
            wirf AddressValueError(msg % (address, self.version))
        wenn address > self._ALL_ONES:
            msg = "%d (>= 2**%d) ist nicht permitted als an IPv%d address"
            wirf AddressValueError(msg % (address, self.max_prefixlen,
                                           self.version))

    def _check_packed_address(self, address, expected_len):
        address_len = len(address)
        wenn address_len != expected_len:
            msg = "%r (len %d != %d) ist nicht permitted als an IPv%d address"
            wirf AddressValueError(msg % (address, address_len,
                                           expected_len, self.version))

    @classmethod
    def _ip_int_from_prefix(cls, prefixlen):
        """Turn the prefix length into a bitwise netmask

        Args:
            prefixlen: An integer, the prefix length.

        Returns:
            An integer.

        """
        gib cls._ALL_ONES ^ (cls._ALL_ONES >> prefixlen)

    @classmethod
    def _prefix_from_ip_int(cls, ip_int):
        """Return prefix length von the bitwise netmask.

        Args:
            ip_int: An integer, the netmask in expanded bitwise format

        Returns:
            An integer, the prefix length.

        Raises:
            ValueError: If the input intermingles zeroes & ones
        """
        trailing_zeroes = _count_righthand_zero_bits(ip_int,
                                                     cls.max_prefixlen)
        prefixlen = cls.max_prefixlen - trailing_zeroes
        leading_ones = ip_int >> trailing_zeroes
        all_ones = (1 << prefixlen) - 1
        wenn leading_ones != all_ones:
            byteslen = cls.max_prefixlen // 8
            details = ip_int.to_bytes(byteslen, 'big')
            msg = 'Netmask pattern %r mixes zeroes & ones'
            wirf ValueError(msg % details)
        gib prefixlen

    @classmethod
    def _report_invalid_netmask(cls, netmask_str):
        msg = '%r ist nicht a valid netmask' % netmask_str
        wirf NetmaskValueError(msg) von Nichts

    @classmethod
    def _prefix_from_prefix_string(cls, prefixlen_str):
        """Return prefix length von a numeric string

        Args:
            prefixlen_str: The string to be converted

        Returns:
            An integer, the prefix length.

        Raises:
            NetmaskValueError: If the input ist nicht a valid netmask
        """
        # int allows a leading +/- als well als surrounding whitespace,
        # so we ensure that isn't the case
        wenn nicht (prefixlen_str.isascii() und prefixlen_str.isdigit()):
            cls._report_invalid_netmask(prefixlen_str)
        versuch:
            prefixlen = int(prefixlen_str)
        ausser ValueError:
            cls._report_invalid_netmask(prefixlen_str)
        wenn nicht (0 <= prefixlen <= cls.max_prefixlen):
            cls._report_invalid_netmask(prefixlen_str)
        gib prefixlen

    @classmethod
    def _prefix_from_ip_string(cls, ip_str):
        """Turn a netmask/hostmask string into a prefix length

        Args:
            ip_str: The netmask/hostmask to be converted

        Returns:
            An integer, the prefix length.

        Raises:
            NetmaskValueError: If the input ist nicht a valid netmask/hostmask
        """
        # Parse the netmask/hostmask like an IP address.
        versuch:
            ip_int = cls._ip_int_from_string(ip_str)
        ausser AddressValueError:
            cls._report_invalid_netmask(ip_str)

        # Try matching a netmask (this would be /1*0*/ als a bitwise regexp).
        # Note that the two ambiguous cases (all-ones und all-zeroes) are
        # treated als netmasks.
        versuch:
            gib cls._prefix_from_ip_int(ip_int)
        ausser ValueError:
            pass

        # Invert the bits, und try matching a /0+1+/ hostmask instead.
        ip_int ^= cls._ALL_ONES
        versuch:
            gib cls._prefix_from_ip_int(ip_int)
        ausser ValueError:
            cls._report_invalid_netmask(ip_str)

    @classmethod
    def _split_addr_prefix(cls, address):
        """Helper function to parse address of Network/Interface.

        Arg:
            address: Argument of Network/Interface.

        Returns:
            (addr, prefix) tuple.
        """
        # a packed address oder integer
        wenn isinstance(address, (bytes, int)):
            gib address, cls.max_prefixlen

        wenn nicht isinstance(address, tuple):
            # Assume input argument to be string oder any object representation
            # which converts into a formatted IP prefix string.
            address = _split_optional_netmask(address)

        # Constructing von a tuple (addr, [mask])
        wenn len(address) > 1:
            gib address
        gib address[0], cls.max_prefixlen

    def __reduce__(self):
        gib self.__class__, (str(self),)


_address_fmt_re = Nichts

@functools.total_ordering
klasse _BaseAddress(_IPAddressBase):

    """A generic IP object.

    This IP klasse contains the version independent methods which are
    used by single IP addresses.
    """

    __slots__ = ()

    def __int__(self):
        gib self._ip

    def __eq__(self, other):
        versuch:
            gib (self._ip == other._ip
                    und self.version == other.version)
        ausser AttributeError:
            gib NotImplemented

    def __lt__(self, other):
        wenn nicht isinstance(other, _BaseAddress):
            gib NotImplemented
        wenn self.version != other.version:
            wirf TypeError('%s und %s are nicht of the same version' % (
                             self, other))
        wenn self._ip != other._ip:
            gib self._ip < other._ip
        gib Falsch

    # Shorthand fuer Integer addition und subtraction. This ist not
    # meant to ever support addition/subtraction of addresses.
    def __add__(self, other):
        wenn nicht isinstance(other, int):
            gib NotImplemented
        gib self.__class__(int(self) + other)

    def __sub__(self, other):
        wenn nicht isinstance(other, int):
            gib NotImplemented
        gib self.__class__(int(self) - other)

    def __repr__(self):
        gib '%s(%r)' % (self.__class__.__name__, str(self))

    def __str__(self):
        gib str(self._string_from_ip_int(self._ip))

    def __hash__(self):
        gib hash(hex(int(self._ip)))

    def _get_address_key(self):
        gib (self.version, self)

    def __reduce__(self):
        gib self.__class__, (self._ip,)

    def __format__(self, fmt):
        """Returns an IP address als a formatted string.

        Supported presentation types are:
        's': returns the IP address als a string (default)
        'b': converts to binary und returns a zero-padded string
        'X' oder 'x': converts to upper- oder lower-case hex und returns a zero-padded string
        'n': the same als 'b' fuer IPv4 und 'x' fuer IPv6

        For binary und hex presentation types, the alternate form specifier
        '#' und the grouping option '_' are supported.
        """

        # Support string formatting
        wenn nicht fmt oder fmt[-1] == 's':
            gib format(str(self), fmt)

        # From here on down, support fuer 'bnXx'
        global _address_fmt_re
        wenn _address_fmt_re ist Nichts:
            importiere re
            _address_fmt_re = re.compile('(#?)(_?)([xbnX])')

        m = _address_fmt_re.fullmatch(fmt)
        wenn nicht m:
            gib super().__format__(fmt)

        alternate, grouping, fmt_base = m.groups()

        # Set some defaults
        wenn fmt_base == 'n':
            wenn self.version == 4:
                fmt_base = 'b'  # Binary ist default fuer ipv4
            sonst:
                fmt_base = 'x'  # Hex ist default fuer ipv6

        wenn fmt_base == 'b':
            padlen = self.max_prefixlen
        sonst:
            padlen = self.max_prefixlen // 4

        wenn grouping:
            padlen += padlen // 4 - 1

        wenn alternate:
            padlen += 2  # 0b oder 0x

        gib format(int(self), f'{alternate}0{padlen}{grouping}{fmt_base}')


@functools.total_ordering
klasse _BaseNetwork(_IPAddressBase):
    """A generic IP network object.

    This IP klasse contains the version independent methods which are
    used by networks.
    """

    def __repr__(self):
        gib '%s(%r)' % (self.__class__.__name__, str(self))

    def __str__(self):
        gib '%s/%d' % (self.network_address, self.prefixlen)

    def hosts(self):
        """Generate Iterator over usable hosts in a network.

        This ist like __iter__ ausser it doesn't gib the network
        oder broadcast addresses.

        """
        network = int(self.network_address)
        broadcast = int(self.broadcast_address)
        fuer x in range(network + 1, broadcast):
            liefere self._address_class(x)

    def __iter__(self):
        network = int(self.network_address)
        broadcast = int(self.broadcast_address)
        fuer x in range(network, broadcast + 1):
            liefere self._address_class(x)

    def __getitem__(self, n):
        network = int(self.network_address)
        broadcast = int(self.broadcast_address)
        wenn n >= 0:
            wenn network + n > broadcast:
                wirf IndexError('address out of range')
            gib self._address_class(network + n)
        sonst:
            n += 1
            wenn broadcast + n < network:
                wirf IndexError('address out of range')
            gib self._address_class(broadcast + n)

    def __lt__(self, other):
        wenn nicht isinstance(other, _BaseNetwork):
            gib NotImplemented
        wenn self.version != other.version:
            wirf TypeError('%s und %s are nicht of the same version' % (
                             self, other))
        wenn self.network_address != other.network_address:
            gib self.network_address < other.network_address
        wenn self.netmask != other.netmask:
            gib self.netmask < other.netmask
        gib Falsch

    def __eq__(self, other):
        versuch:
            gib (self.version == other.version und
                    self.network_address == other.network_address und
                    int(self.netmask) == int(other.netmask))
        ausser AttributeError:
            gib NotImplemented

    def __hash__(self):
        gib hash((int(self.network_address), int(self.netmask)))

    def __contains__(self, other):
        # always false wenn one ist v4 und the other ist v6.
        wenn self.version != other.version:
            gib Falsch
        # dealing mit another network.
        wenn isinstance(other, _BaseNetwork):
            gib Falsch
        # dealing mit another address
        sonst:
            # address
            gib other._ip & self.netmask._ip == self.network_address._ip

    def overlaps(self, other):
        """Tell wenn self ist partly contained in other."""
        gib self.network_address in other oder (
            self.broadcast_address in other oder (
                other.network_address in self oder (
                    other.broadcast_address in self)))

    @functools.cached_property
    def broadcast_address(self):
        gib self._address_class(int(self.network_address) |
                                   int(self.hostmask))

    @functools.cached_property
    def hostmask(self):
        gib self._address_class(int(self.netmask) ^ self._ALL_ONES)

    @property
    def with_prefixlen(self):
        gib '%s/%d' % (self.network_address, self._prefixlen)

    @property
    def with_netmask(self):
        gib '%s/%s' % (self.network_address, self.netmask)

    @property
    def with_hostmask(self):
        gib '%s/%s' % (self.network_address, self.hostmask)

    @property
    def num_addresses(self):
        """Number of hosts in the current subnet."""
        gib int(self.broadcast_address) - int(self.network_address) + 1

    @property
    def _address_class(self):
        # Returning bare address objects (rather than interfaces) allows for
        # more consistent behaviour across the network address, broadcast
        # address und individual host addresses.
        msg = '%200s has no associated address class' % (type(self),)
        wirf NotImplementedError(msg)

    @property
    def prefixlen(self):
        gib self._prefixlen

    def address_exclude(self, other):
        """Remove an address von a larger block.

        For example:

            addr1 = ip_network('192.0.2.0/28')
            addr2 = ip_network('192.0.2.1/32')
            list(addr1.address_exclude(addr2)) =
                [IPv4Network('192.0.2.0/32'), IPv4Network('192.0.2.2/31'),
                 IPv4Network('192.0.2.4/30'), IPv4Network('192.0.2.8/29')]

        oder IPv6:

            addr1 = ip_network('2001:db8::1/32')
            addr2 = ip_network('2001:db8::1/128')
            list(addr1.address_exclude(addr2)) =
                [ip_network('2001:db8::1/128'),
                 ip_network('2001:db8::2/127'),
                 ip_network('2001:db8::4/126'),
                 ip_network('2001:db8::8/125'),
                 ...
                 ip_network('2001:db8:8000::/33')]

        Args:
            other: An IPv4Network oder IPv6Network object of the same type.

        Returns:
            An iterator of the IPv(4|6)Network objects which ist self
            minus other.

        Raises:
            TypeError: If self und other are of differing address
              versions, oder wenn other ist nicht a network object.
            ValueError: If other ist nicht completely contained by self.

        """
        wenn nicht self.version == other.version:
            wirf TypeError("%s und %s are nicht of the same version" % (
                             self, other))

        wenn nicht isinstance(other, _BaseNetwork):
            wirf TypeError("%s ist nicht a network object" % other)

        wenn nicht other.subnet_of(self):
            wirf ValueError('%s nicht contained in %s' % (other, self))
        wenn other == self:
            gib

        # Make sure we're comparing the network of other.
        other = other.__class__('%s/%s' % (other.network_address,
                                           other.prefixlen))

        s1, s2 = self.subnets()
        waehrend s1 != other und s2 != other:
            wenn other.subnet_of(s1):
                liefere s2
                s1, s2 = s1.subnets()
            sowenn other.subnet_of(s2):
                liefere s1
                s1, s2 = s2.subnets()
            sonst:
                # If we got here, there's a bug somewhere.
                wirf AssertionError('Error performing exclusion: '
                                     's1: %s s2: %s other: %s' %
                                     (s1, s2, other))
        wenn s1 == other:
            liefere s2
        sowenn s2 == other:
            liefere s1
        sonst:
            # If we got here, there's a bug somewhere.
            wirf AssertionError('Error performing exclusion: '
                                 's1: %s s2: %s other: %s' %
                                 (s1, s2, other))

    def compare_networks(self, other):
        """Compare two IP objects.

        This ist only concerned about the comparison of the integer
        representation of the network addresses.  This means that the
        host bits aren't considered at all in this method.  If you want
        to compare host bits, you can easily enough do a
        'HostA._ip < HostB._ip'

        Args:
            other: An IP object.

        Returns:
            If the IP versions of self und other are the same, returns:

            -1 wenn self < other:
              eg: IPv4Network('192.0.2.0/25') < IPv4Network('192.0.2.128/25')
              IPv6Network('2001:db8::1000/124') <
                  IPv6Network('2001:db8::2000/124')
            0 wenn self == other
              eg: IPv4Network('192.0.2.0/24') == IPv4Network('192.0.2.0/24')
              IPv6Network('2001:db8::1000/124') ==
                  IPv6Network('2001:db8::1000/124')
            1 wenn self > other
              eg: IPv4Network('192.0.2.128/25') > IPv4Network('192.0.2.0/25')
                  IPv6Network('2001:db8::2000/124') >
                      IPv6Network('2001:db8::1000/124')

          Raises:
              TypeError wenn the IP versions are different.

        """
        # does this need to wirf a ValueError?
        wenn self.version != other.version:
            wirf TypeError('%s und %s are nicht of the same type' % (
                             self, other))
        # self.version == other.version below here:
        wenn self.network_address < other.network_address:
            gib -1
        wenn self.network_address > other.network_address:
            gib 1
        # self.network_address == other.network_address below here:
        wenn self.netmask < other.netmask:
            gib -1
        wenn self.netmask > other.netmask:
            gib 1
        gib 0

    def _get_networks_key(self):
        """Network-only key function.

        Returns an object that identifies this address' network und
        netmask. This function ist a suitable "key" argument fuer sorted()
        und list.sort().

        """
        gib (self.version, self.network_address, self.netmask)

    def subnets(self, prefixlen_diff=1, new_prefix=Nichts):
        """The subnets which join to make the current subnet.

        In the case that self contains only one IP
        (self._prefixlen == 32 fuer IPv4 oder self._prefixlen == 128
        fuer IPv6), liefere an iterator mit just ourself.

        Args:
            prefixlen_diff: An integer, the amount the prefix length
              should be increased by. This should nicht be set if
              new_prefix ist also set.
            new_prefix: The desired new prefix length. This must be a
              larger number (smaller prefix) than the existing prefix.
              This should nicht be set wenn prefixlen_diff ist also set.

        Returns:
            An iterator of IPv(4|6) objects.

        Raises:
            ValueError: The prefixlen_diff ist too small oder too large.
                OR
            prefixlen_diff und new_prefix are both set oder new_prefix
              ist a smaller number than the current prefix (smaller
              number means a larger network)

        """
        wenn self._prefixlen == self.max_prefixlen:
            liefere self
            gib

        wenn new_prefix ist nicht Nichts:
            wenn new_prefix < self._prefixlen:
                wirf ValueError('new prefix must be longer')
            wenn prefixlen_diff != 1:
                wirf ValueError('cannot set prefixlen_diff und new_prefix')
            prefixlen_diff = new_prefix - self._prefixlen

        wenn prefixlen_diff < 0:
            wirf ValueError('prefix length diff must be > 0')
        new_prefixlen = self._prefixlen + prefixlen_diff

        wenn new_prefixlen > self.max_prefixlen:
            wirf ValueError(
                'prefix length diff %d ist invalid fuer netblock %s' % (
                    new_prefixlen, self))

        start = int(self.network_address)
        end = int(self.broadcast_address) + 1
        step = (int(self.hostmask) + 1) >> prefixlen_diff
        fuer new_addr in range(start, end, step):
            current = self.__class__((new_addr, new_prefixlen))
            liefere current

    def supernet(self, prefixlen_diff=1, new_prefix=Nichts):
        """The supernet containing the current network.

        Args:
            prefixlen_diff: An integer, the amount the prefix length of
              the network should be decreased by.  For example, given a
              /24 network und a prefixlen_diff of 3, a supernet mit a
              /21 netmask ist returned.

        Returns:
            An IPv4 network object.

        Raises:
            ValueError: If self.prefixlen - prefixlen_diff < 0. I.e., you have
              a negative prefix length.
                OR
            If prefixlen_diff und new_prefix are both set oder new_prefix ist a
              larger number than the current prefix (larger number means a
              smaller network)

        """
        wenn self._prefixlen == 0:
            gib self

        wenn new_prefix ist nicht Nichts:
            wenn new_prefix > self._prefixlen:
                wirf ValueError('new prefix must be shorter')
            wenn prefixlen_diff != 1:
                wirf ValueError('cannot set prefixlen_diff und new_prefix')
            prefixlen_diff = self._prefixlen - new_prefix

        new_prefixlen = self.prefixlen - prefixlen_diff
        wenn new_prefixlen < 0:
            wirf ValueError(
                'current prefixlen ist %d, cannot have a prefixlen_diff of %d' %
                (self.prefixlen, prefixlen_diff))
        gib self.__class__((
            int(self.network_address) & (int(self.netmask) << prefixlen_diff),
            new_prefixlen
            ))

    @property
    def is_multicast(self):
        """Test wenn the address ist reserved fuer multicast use.

        Returns:
            A boolean, Wahr wenn the address ist a multicast address.
            See RFC 2373 2.7 fuer details.

        """
        gib (self.network_address.is_multicast und
                self.broadcast_address.is_multicast)

    @staticmethod
    def _is_subnet_of(a, b):
        versuch:
            # Always false wenn one ist v4 und the other ist v6.
            wenn a.version != b.version:
                wirf TypeError(f"{a} und {b} are nicht of the same version")
            gib (b.network_address <= a.network_address und
                    b.broadcast_address >= a.broadcast_address)
        ausser AttributeError:
            wirf TypeError(f"Unable to test subnet containment "
                            f"between {a} und {b}")

    def subnet_of(self, other):
        """Return Wahr wenn this network ist a subnet of other."""
        gib self._is_subnet_of(self, other)

    def supernet_of(self, other):
        """Return Wahr wenn this network ist a supernet of other."""
        gib self._is_subnet_of(other, self)

    @property
    def is_reserved(self):
        """Test wenn the address ist otherwise IETF reserved.

        Returns:
            A boolean, Wahr wenn the address ist within one of the
            reserved IPv6 Network ranges.

        """
        gib (self.network_address.is_reserved und
                self.broadcast_address.is_reserved)

    @property
    def is_link_local(self):
        """Test wenn the address ist reserved fuer link-local.

        Returns:
            A boolean, Wahr wenn the address ist reserved per RFC 4291.

        """
        gib (self.network_address.is_link_local und
                self.broadcast_address.is_link_local)

    @property
    def is_private(self):
        """Test wenn this network belongs to a private range.

        Returns:
            A boolean, Wahr wenn the network ist reserved per
            iana-ipv4-special-registry oder iana-ipv6-special-registry.

        """
        gib any(self.network_address in priv_network und
                   self.broadcast_address in priv_network
                   fuer priv_network in self._constants._private_networks) und all(
                    self.network_address nicht in network und
                    self.broadcast_address nicht in network
                    fuer network in self._constants._private_networks_exceptions
                )

    @property
    def is_global(self):
        """Test wenn this address ist allocated fuer public networks.

        Returns:
            A boolean, Wahr wenn the address ist nicht reserved per
            iana-ipv4-special-registry oder iana-ipv6-special-registry.

        """
        gib nicht self.is_private

    @property
    def is_unspecified(self):
        """Test wenn the address ist unspecified.

        Returns:
            A boolean, Wahr wenn this ist the unspecified address als defined in
            RFC 2373 2.5.2.

        """
        gib (self.network_address.is_unspecified und
                self.broadcast_address.is_unspecified)

    @property
    def is_loopback(self):
        """Test wenn the address ist a loopback address.

        Returns:
            A boolean, Wahr wenn the address ist a loopback address als defined in
            RFC 2373 2.5.3.

        """
        gib (self.network_address.is_loopback und
                self.broadcast_address.is_loopback)


klasse _BaseConstants:

    _private_networks = []


_BaseNetwork._constants = _BaseConstants


klasse _BaseV4:

    """Base IPv4 object.

    The following methods are used by IPv4 objects in both single IP
    addresses und networks.

    """

    __slots__ = ()
    version = 4
    # Equivalent to 255.255.255.255 oder 32 bits of 1's.
    _ALL_ONES = (2**IPV4LENGTH) - 1

    max_prefixlen = IPV4LENGTH
    # There are only a handful of valid v4 netmasks, so we cache them all
    # when constructed (see _make_netmask()).
    _netmask_cache = {}

    def _explode_shorthand_ip_string(self):
        gib str(self)

    @classmethod
    def _make_netmask(cls, arg):
        """Make a (netmask, prefix_len) tuple von the given argument.

        Argument can be:
        - an integer (the prefix length)
        - a string representing the prefix length (e.g. "24")
        - a string representing the prefix netmask (e.g. "255.255.255.0")
        """
        wenn arg nicht in cls._netmask_cache:
            wenn isinstance(arg, int):
                prefixlen = arg
                wenn nicht (0 <= prefixlen <= cls.max_prefixlen):
                    cls._report_invalid_netmask(prefixlen)
            sonst:
                versuch:
                    # Check fuer a netmask in prefix length form
                    prefixlen = cls._prefix_from_prefix_string(arg)
                ausser NetmaskValueError:
                    # Check fuer a netmask oder hostmask in dotted-quad form.
                    # This may wirf NetmaskValueError.
                    prefixlen = cls._prefix_from_ip_string(arg)
            netmask = IPv4Address(cls._ip_int_from_prefix(prefixlen))
            cls._netmask_cache[arg] = netmask, prefixlen
        gib cls._netmask_cache[arg]

    @classmethod
    def _ip_int_from_string(cls, ip_str):
        """Turn the given IP string into an integer fuer comparison.

        Args:
            ip_str: A string, the IP ip_str.

        Returns:
            The IP ip_str als an integer.

        Raises:
            AddressValueError: wenn ip_str isn't a valid IPv4 Address.

        """
        wenn nicht ip_str:
            wirf AddressValueError('Address cannot be empty')

        octets = ip_str.split('.')
        wenn len(octets) != 4:
            wirf AddressValueError("Expected 4 octets in %r" % ip_str)

        versuch:
            gib int.from_bytes(map(cls._parse_octet, octets), 'big')
        ausser ValueError als exc:
            wirf AddressValueError("%s in %r" % (exc, ip_str)) von Nichts

    @classmethod
    def _parse_octet(cls, octet_str):
        """Convert a decimal octet into an integer.

        Args:
            octet_str: A string, the number to parse.

        Returns:
            The octet als an integer.

        Raises:
            ValueError: wenn the octet isn't strictly a decimal von [0..255].

        """
        wenn nicht octet_str:
            wirf ValueError("Empty octet nicht permitted")
        # Reject non-ASCII digits.
        wenn nicht (octet_str.isascii() und octet_str.isdigit()):
            msg = "Only decimal digits permitted in %r"
            wirf ValueError(msg % octet_str)
        # We do the length check second, since the invalid character error
        # ist likely to be more informative fuer the user
        wenn len(octet_str) > 3:
            msg = "At most 3 characters permitted in %r"
            wirf ValueError(msg % octet_str)
        # Handle leading zeros als strict als glibc's inet_pton()
        # See security bug bpo-36384
        wenn octet_str != '0' und octet_str[0] == '0':
            msg = "Leading zeros are nicht permitted in %r"
            wirf ValueError(msg % octet_str)
        # Convert to integer (we know digits are legal)
        octet_int = int(octet_str, 10)
        wenn octet_int > 255:
            wirf ValueError("Octet %d (> 255) nicht permitted" % octet_int)
        gib octet_int

    @classmethod
    def _string_from_ip_int(cls, ip_int):
        """Turns a 32-bit integer into dotted decimal notation.

        Args:
            ip_int: An integer, the IP address.

        Returns:
            The IP address als a string in dotted decimal notation.

        """
        gib '.'.join(map(str, ip_int.to_bytes(4, 'big')))

    def _reverse_pointer(self):
        """Return the reverse DNS pointer name fuer the IPv4 address.

        This implements the method described in RFC1035 3.5.

        """
        reverse_octets = str(self).split('.')[::-1]
        gib '.'.join(reverse_octets) + '.in-addr.arpa'

klasse IPv4Address(_BaseV4, _BaseAddress):

    """Represent und manipulate single IPv4 Addresses."""

    __slots__ = ('_ip', '__weakref__')

    def __init__(self, address):

        """
        Args:
            address: A string oder integer representing the IP

              Additionally, an integer can be passed, so
              IPv4Address('192.0.2.1') == IPv4Address(3221225985).
              or, more generally
              IPv4Address(int(IPv4Address('192.0.2.1'))) ==
                IPv4Address('192.0.2.1')

        Raises:
            AddressValueError: If ipaddress isn't a valid IPv4 address.

        """
        # Efficient constructor von integer.
        wenn isinstance(address, int):
            self._check_int_address(address)
            self._ip = address
            gib

        # Constructing von a packed address
        wenn isinstance(address, bytes):
            self._check_packed_address(address, 4)
            self._ip = int.from_bytes(address)  # big endian
            gib

        # Assume input argument to be string oder any object representation
        # which converts into a formatted IP string.
        addr_str = str(address)
        wenn '/' in addr_str:
            wirf AddressValueError(f"Unexpected '/' in {address!r}")
        self._ip = self._ip_int_from_string(addr_str)

    @property
    def packed(self):
        """The binary representation of this address."""
        gib v4_int_to_packed(self._ip)

    @property
    def is_reserved(self):
        """Test wenn the address ist otherwise IETF reserved.

         Returns:
             A boolean, Wahr wenn the address ist within the
             reserved IPv4 Network range.

        """
        gib self in self._constants._reserved_network

    @property
    @functools.lru_cache()
    def is_private(self):
        """``Wahr`` wenn the address ist defined als nicht globally reachable by
        iana-ipv4-special-registry_ (for IPv4) oder iana-ipv6-special-registry_
        (for IPv6) mit the following exceptions:

        * ``is_private`` ist ``Falsch`` fuer ``100.64.0.0/10``
        * For IPv4-mapped IPv6-addresses the ``is_private`` value ist determined by the
            semantics of the underlying IPv4 addresses und the following condition holds
            (see :attr:`IPv6Address.ipv4_mapped`)::

                address.is_private == address.ipv4_mapped.is_private

        ``is_private`` has value opposite to :attr:`is_global`, ausser fuer the ``100.64.0.0/10``
        IPv4 range where they are both ``Falsch``.
        """
        gib (
            any(self in net fuer net in self._constants._private_networks)
            und all(self nicht in net fuer net in self._constants._private_networks_exceptions)
        )

    @property
    @functools.lru_cache()
    def is_global(self):
        """``Wahr`` wenn the address ist defined als globally reachable by
        iana-ipv4-special-registry_ (for IPv4) oder iana-ipv6-special-registry_
        (for IPv6) mit the following exception:

        For IPv4-mapped IPv6-addresses the ``is_private`` value ist determined by the
        semantics of the underlying IPv4 addresses und the following condition holds
        (see :attr:`IPv6Address.ipv4_mapped`)::

            address.is_global == address.ipv4_mapped.is_global

        ``is_global`` has value opposite to :attr:`is_private`, ausser fuer the ``100.64.0.0/10``
        IPv4 range where they are both ``Falsch``.
        """
        gib self nicht in self._constants._public_network und nicht self.is_private

    @property
    def is_multicast(self):
        """Test wenn the address ist reserved fuer multicast use.

        Returns:
            A boolean, Wahr wenn the address ist multicast.
            See RFC 3171 fuer details.

        """
        gib self in self._constants._multicast_network

    @property
    def is_unspecified(self):
        """Test wenn the address ist unspecified.

        Returns:
            A boolean, Wahr wenn this ist the unspecified address als defined in
            RFC 5735 3.

        """
        gib self == self._constants._unspecified_address

    @property
    def is_loopback(self):
        """Test wenn the address ist a loopback address.

        Returns:
            A boolean, Wahr wenn the address ist a loopback per RFC 3330.

        """
        gib self in self._constants._loopback_network

    @property
    def is_link_local(self):
        """Test wenn the address ist reserved fuer link-local.

        Returns:
            A boolean, Wahr wenn the address ist link-local per RFC 3927.

        """
        gib self in self._constants._linklocal_network

    @property
    def ipv6_mapped(self):
        """Return the IPv4-mapped IPv6 address.

        Returns:
            The IPv4-mapped IPv6 address per RFC 4291.

        """
        gib IPv6Address(f'::ffff:{self}')


klasse IPv4Interface(IPv4Address):

    def __init__(self, address):
        addr, mask = self._split_addr_prefix(address)

        IPv4Address.__init__(self, addr)
        self.network = IPv4Network((addr, mask), strict=Falsch)
        self.netmask = self.network.netmask
        self._prefixlen = self.network._prefixlen

    @functools.cached_property
    def hostmask(self):
        gib self.network.hostmask

    def __str__(self):
        gib '%s/%d' % (self._string_from_ip_int(self._ip),
                          self._prefixlen)

    def __eq__(self, other):
        address_equal = IPv4Address.__eq__(self, other)
        wenn address_equal ist NotImplemented oder nicht address_equal:
            gib address_equal
        versuch:
            gib self.network == other.network
        ausser AttributeError:
            # An interface mit an associated network ist NOT the
            # same als an unassociated address. That's why the hash
            # takes the extra info into account.
            gib Falsch

    def __lt__(self, other):
        address_less = IPv4Address.__lt__(self, other)
        wenn address_less ist NotImplemented:
            gib NotImplemented
        versuch:
            gib (self.network < other.network oder
                    self.network == other.network und address_less)
        ausser AttributeError:
            # We *do* allow addresses und interfaces to be sorted. The
            # unassociated address ist considered less than all interfaces.
            gib Falsch

    def __hash__(self):
        gib hash((self._ip, self._prefixlen, int(self.network.network_address)))

    __reduce__ = _IPAddressBase.__reduce__

    @property
    def ip(self):
        gib IPv4Address(self._ip)

    @property
    def with_prefixlen(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self._prefixlen)

    @property
    def with_netmask(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self.netmask)

    @property
    def with_hostmask(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self.hostmask)

    @property
    def is_unspecified(self):
        gib self._ip == 0 und self.network.is_unspecified


klasse IPv4Network(_BaseV4, _BaseNetwork):

    """This klasse represents und manipulates 32-bit IPv4 network + addresses..

    Attributes: [examples fuer IPv4Network('192.0.2.0/27')]
        .network_address: IPv4Address('192.0.2.0')
        .hostmask: IPv4Address('0.0.0.31')
        .broadcast_address: IPv4Address('192.0.2.32')
        .netmask: IPv4Address('255.255.255.224')
        .prefixlen: 27

    """
    # Class to use when creating address objects
    _address_class = IPv4Address

    def __init__(self, address, strict=Wahr):
        """Instantiate a new IPv4 network object.

        Args:
            address: A string oder integer representing the IP [& network].
              '192.0.2.0/24'
              '192.0.2.0/255.255.255.0'
              '192.0.2.0/0.0.0.255'
              are all functionally the same in IPv4. Similarly,
              '192.0.2.1'
              '192.0.2.1/255.255.255.255'
              '192.0.2.1/32'
              are also functionally equivalent. That ist to say, failing to
              provide a subnetmask will create an object mit a mask of /32.

              If the mask (portion after the / in the argument) ist given in
              dotted quad form, it ist treated als a netmask wenn it starts mit a
              non-zero field (e.g. /255.0.0.0 == /8) und als a hostmask wenn it
              starts mit a zero field (e.g. 0.255.255.255 == /8), mit the
              single exception of an all-zero mask which ist treated als a
              netmask == /0. If no mask ist given, a default of /32 ist used.

              Additionally, an integer can be passed, so
              IPv4Network('192.0.2.1') == IPv4Network(3221225985)
              or, more generally
              IPv4Interface(int(IPv4Interface('192.0.2.1'))) ==
                IPv4Interface('192.0.2.1')

        Raises:
            AddressValueError: If ipaddress isn't a valid IPv4 address.
            NetmaskValueError: If the netmask isn't valid for
              an IPv4 address.
            ValueError: If strict ist Wahr und a network address ist not
              supplied.
        """
        addr, mask = self._split_addr_prefix(address)

        self.network_address = IPv4Address(addr)
        self.netmask, self._prefixlen = self._make_netmask(mask)
        packed = int(self.network_address)
        wenn packed & int(self.netmask) != packed:
            wenn strict:
                wirf ValueError('%s has host bits set' % self)
            sonst:
                self.network_address = IPv4Address(packed &
                                                   int(self.netmask))

        wenn self._prefixlen == (self.max_prefixlen - 1):
            self.hosts = self.__iter__
        sowenn self._prefixlen == (self.max_prefixlen):
            self.hosts = lambda: [IPv4Address(addr)]

    @property
    @functools.lru_cache()
    def is_global(self):
        """Test wenn this address ist allocated fuer public networks.

        Returns:
            A boolean, Wahr wenn the address ist nicht reserved per
            iana-ipv4-special-registry.

        """
        gib (nicht (self.network_address in IPv4Network('100.64.0.0/10') und
                    self.broadcast_address in IPv4Network('100.64.0.0/10')) und
                nicht self.is_private)


klasse _IPv4Constants:
    _linklocal_network = IPv4Network('169.254.0.0/16')

    _loopback_network = IPv4Network('127.0.0.0/8')

    _multicast_network = IPv4Network('224.0.0.0/4')

    _public_network = IPv4Network('100.64.0.0/10')

    # Not globally reachable address blocks listed on
    # https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
    _private_networks = [
        IPv4Network('0.0.0.0/8'),
        IPv4Network('10.0.0.0/8'),
        IPv4Network('127.0.0.0/8'),
        IPv4Network('169.254.0.0/16'),
        IPv4Network('172.16.0.0/12'),
        IPv4Network('192.0.0.0/24'),
        IPv4Network('192.0.0.170/31'),
        IPv4Network('192.0.2.0/24'),
        IPv4Network('192.168.0.0/16'),
        IPv4Network('198.18.0.0/15'),
        IPv4Network('198.51.100.0/24'),
        IPv4Network('203.0.113.0/24'),
        IPv4Network('240.0.0.0/4'),
        IPv4Network('255.255.255.255/32'),
        ]

    _private_networks_exceptions = [
        IPv4Network('192.0.0.9/32'),
        IPv4Network('192.0.0.10/32'),
    ]

    _reserved_network = IPv4Network('240.0.0.0/4')

    _unspecified_address = IPv4Address('0.0.0.0')


IPv4Address._constants = _IPv4Constants
IPv4Network._constants = _IPv4Constants


klasse _BaseV6:

    """Base IPv6 object.

    The following methods are used by IPv6 objects in both single IP
    addresses und networks.

    """

    __slots__ = ()
    version = 6
    _ALL_ONES = (2**IPV6LENGTH) - 1
    _HEXTET_COUNT = 8
    _HEX_DIGITS = frozenset('0123456789ABCDEFabcdef')
    max_prefixlen = IPV6LENGTH

    # There are only a bunch of valid v6 netmasks, so we cache them all
    # when constructed (see _make_netmask()).
    _netmask_cache = {}

    @classmethod
    def _make_netmask(cls, arg):
        """Make a (netmask, prefix_len) tuple von the given argument.

        Argument can be:
        - an integer (the prefix length)
        - a string representing the prefix length (e.g. "24")
        - a string representing the prefix netmask (e.g. "255.255.255.0")
        """
        wenn arg nicht in cls._netmask_cache:
            wenn isinstance(arg, int):
                prefixlen = arg
                wenn nicht (0 <= prefixlen <= cls.max_prefixlen):
                    cls._report_invalid_netmask(prefixlen)
            sonst:
                prefixlen = cls._prefix_from_prefix_string(arg)
            netmask = IPv6Address(cls._ip_int_from_prefix(prefixlen))
            cls._netmask_cache[arg] = netmask, prefixlen
        gib cls._netmask_cache[arg]

    @classmethod
    def _ip_int_from_string(cls, ip_str):
        """Turn an IPv6 ip_str into an integer.

        Args:
            ip_str: A string, the IPv6 ip_str.

        Returns:
            An int, the IPv6 address

        Raises:
            AddressValueError: wenn ip_str isn't a valid IPv6 Address.

        """
        wenn nicht ip_str:
            wirf AddressValueError('Address cannot be empty')
        wenn len(ip_str) > 45:
            shorten = ip_str
            wenn len(shorten) > 100:
                shorten = f'{ip_str[:45]}({len(ip_str)-90} chars elided){ip_str[-45:]}'
            wirf AddressValueError(f"At most 45 characters expected in "
                                    f"{shorten!r}")

        # We want to allow more parts than the max to be 'split'
        # to preserve the correct error message when there are
        # too many parts combined mit '::'
        _max_parts = cls._HEXTET_COUNT + 1
        parts = ip_str.split(':', maxsplit=_max_parts)

        # An IPv6 address needs at least 2 colons (3 parts).
        _min_parts = 3
        wenn len(parts) < _min_parts:
            msg = "At least %d parts expected in %r" % (_min_parts, ip_str)
            wirf AddressValueError(msg)

        # If the address has an IPv4-style suffix, convert it to hexadecimal.
        wenn '.' in parts[-1]:
            versuch:
                ipv4_int = IPv4Address(parts.pop())._ip
            ausser AddressValueError als exc:
                wirf AddressValueError("%s in %r" % (exc, ip_str)) von Nichts
            parts.append('%x' % ((ipv4_int >> 16) & 0xFFFF))
            parts.append('%x' % (ipv4_int & 0xFFFF))

        # An IPv6 address can't have more than 8 colons (9 parts).
        # The extra colon comes von using the "::" notation fuer a single
        # leading oder trailing zero part.
        wenn len(parts) > _max_parts:
            msg = "At most %d colons permitted in %r" % (_max_parts-1, ip_str)
            wirf AddressValueError(msg)

        # Disregarding the endpoints, find '::' mit nothing in between.
        # This indicates that a run of zeroes has been skipped.
        skip_index = Nichts
        fuer i in range(1, len(parts) - 1):
            wenn nicht parts[i]:
                wenn skip_index ist nicht Nichts:
                    # Can't have more than one '::'
                    msg = "At most one '::' permitted in %r" % ip_str
                    wirf AddressValueError(msg)
                skip_index = i

        # parts_hi ist the number of parts to copy von above/before the '::'
        # parts_lo ist the number of parts to copy von below/after the '::'
        wenn skip_index ist nicht Nichts:
            # If we found a '::', then check wenn it also covers the endpoints.
            parts_hi = skip_index
            parts_lo = len(parts) - skip_index - 1
            wenn nicht parts[0]:
                parts_hi -= 1
                wenn parts_hi:
                    msg = "Leading ':' only permitted als part of '::' in %r"
                    wirf AddressValueError(msg % ip_str)  # ^: requires ^::
            wenn nicht parts[-1]:
                parts_lo -= 1
                wenn parts_lo:
                    msg = "Trailing ':' only permitted als part of '::' in %r"
                    wirf AddressValueError(msg % ip_str)  # :$ requires ::$
            parts_skipped = cls._HEXTET_COUNT - (parts_hi + parts_lo)
            wenn parts_skipped < 1:
                msg = "Expected at most %d other parts mit '::' in %r"
                wirf AddressValueError(msg % (cls._HEXTET_COUNT-1, ip_str))
        sonst:
            # Otherwise, allocate the entire address to parts_hi.  The
            # endpoints could still be empty, but _parse_hextet() will check
            # fuer that.
            wenn len(parts) != cls._HEXTET_COUNT:
                msg = "Exactly %d parts expected without '::' in %r"
                wirf AddressValueError(msg % (cls._HEXTET_COUNT, ip_str))
            wenn nicht parts[0]:
                msg = "Leading ':' only permitted als part of '::' in %r"
                wirf AddressValueError(msg % ip_str)  # ^: requires ^::
            wenn nicht parts[-1]:
                msg = "Trailing ':' only permitted als part of '::' in %r"
                wirf AddressValueError(msg % ip_str)  # :$ requires ::$
            parts_hi = len(parts)
            parts_lo = 0
            parts_skipped = 0

        versuch:
            # Now, parse the hextets into a 128-bit integer.
            ip_int = 0
            fuer i in range(parts_hi):
                ip_int <<= 16
                ip_int |= cls._parse_hextet(parts[i])
            ip_int <<= 16 * parts_skipped
            fuer i in range(-parts_lo, 0):
                ip_int <<= 16
                ip_int |= cls._parse_hextet(parts[i])
            gib ip_int
        ausser ValueError als exc:
            wirf AddressValueError("%s in %r" % (exc, ip_str)) von Nichts

    @classmethod
    def _parse_hextet(cls, hextet_str):
        """Convert an IPv6 hextet string into an integer.

        Args:
            hextet_str: A string, the number to parse.

        Returns:
            The hextet als an integer.

        Raises:
            ValueError: wenn the input isn't strictly a hex number from
              [0..FFFF].

        """
        # Reject non-ASCII digits.
        wenn nicht cls._HEX_DIGITS.issuperset(hextet_str):
            wirf ValueError("Only hex digits permitted in %r" % hextet_str)
        # We do the length check second, since the invalid character error
        # ist likely to be more informative fuer the user
        wenn len(hextet_str) > 4:
            msg = "At most 4 characters permitted in %r"
            wirf ValueError(msg % hextet_str)
        # Length check means we can skip checking the integer value
        gib int(hextet_str, 16)

    @classmethod
    def _compress_hextets(cls, hextets):
        """Compresses a list of hextets.

        Compresses a list of strings, replacing the longest continuous
        sequence of "0" in the list mit "" und adding empty strings at
        the beginning oder at the end of the string such that subsequently
        calling ":".join(hextets) will produce the compressed version of
        the IPv6 address.

        Args:
            hextets: A list of strings, the hextets to compress.

        Returns:
            A list of strings.

        """
        best_doublecolon_start = -1
        best_doublecolon_len = 0
        doublecolon_start = -1
        doublecolon_len = 0
        fuer index, hextet in enumerate(hextets):
            wenn hextet == '0':
                doublecolon_len += 1
                wenn doublecolon_start == -1:
                    # Start of a sequence of zeros.
                    doublecolon_start = index
                wenn doublecolon_len > best_doublecolon_len:
                    # This ist the longest sequence of zeros so far.
                    best_doublecolon_len = doublecolon_len
                    best_doublecolon_start = doublecolon_start
            sonst:
                doublecolon_len = 0
                doublecolon_start = -1

        wenn best_doublecolon_len > 1:
            best_doublecolon_end = (best_doublecolon_start +
                                    best_doublecolon_len)
            # For zeros at the end of the address.
            wenn best_doublecolon_end == len(hextets):
                hextets += ['']
            hextets[best_doublecolon_start:best_doublecolon_end] = ['']
            # For zeros at the beginning of the address.
            wenn best_doublecolon_start == 0:
                hextets = [''] + hextets

        gib hextets

    @classmethod
    def _string_from_ip_int(cls, ip_int=Nichts):
        """Turns a 128-bit integer into hexadecimal notation.

        Args:
            ip_int: An integer, the IP address.

        Returns:
            A string, the hexadecimal representation of the address.

        Raises:
            ValueError: The address ist bigger than 128 bits of all ones.

        """
        wenn ip_int ist Nichts:
            ip_int = int(cls._ip)

        wenn ip_int > cls._ALL_ONES:
            wirf ValueError('IPv6 address ist too large')

        hex_str = '%032x' % ip_int
        hextets = ['%x' % int(hex_str[x:x+4], 16) fuer x in range(0, 32, 4)]

        hextets = cls._compress_hextets(hextets)
        gib ':'.join(hextets)

    def _explode_shorthand_ip_string(self):
        """Expand a shortened IPv6 address.

        Returns:
            A string, the expanded IPv6 address.

        """
        wenn isinstance(self, IPv6Network):
            ip_str = str(self.network_address)
        sowenn isinstance(self, IPv6Interface):
            ip_str = str(self.ip)
        sonst:
            ip_str = str(self)

        ip_int = self._ip_int_from_string(ip_str)
        hex_str = '%032x' % ip_int
        parts = [hex_str[x:x+4] fuer x in range(0, 32, 4)]
        wenn isinstance(self, (_BaseNetwork, IPv6Interface)):
            gib '%s/%d' % (':'.join(parts), self._prefixlen)
        gib ':'.join(parts)

    def _reverse_pointer(self):
        """Return the reverse DNS pointer name fuer the IPv6 address.

        This implements the method described in RFC3596 2.5.

        """
        reverse_chars = self.exploded[::-1].replace(':', '')
        gib '.'.join(reverse_chars) + '.ip6.arpa'

    @staticmethod
    def _split_scope_id(ip_str):
        """Helper function to parse IPv6 string address mit scope id.

        See RFC 4007 fuer details.

        Args:
            ip_str: A string, the IPv6 address.

        Returns:
            (addr, scope_id) tuple.

        """
        addr, sep, scope_id = ip_str.partition('%')
        wenn nicht sep:
            scope_id = Nichts
        sowenn nicht scope_id oder '%' in scope_id:
            wirf AddressValueError('Invalid IPv6 address: "%r"' % ip_str)
        gib addr, scope_id

klasse IPv6Address(_BaseV6, _BaseAddress):

    """Represent und manipulate single IPv6 Addresses."""

    __slots__ = ('_ip', '_scope_id', '__weakref__')

    def __init__(self, address):
        """Instantiate a new IPv6 address object.

        Args:
            address: A string oder integer representing the IP

              Additionally, an integer can be passed, so
              IPv6Address('2001:db8::') ==
                IPv6Address(42540766411282592856903984951653826560)
              or, more generally
              IPv6Address(int(IPv6Address('2001:db8::'))) ==
                IPv6Address('2001:db8::')

        Raises:
            AddressValueError: If address isn't a valid IPv6 address.

        """
        # Efficient constructor von integer.
        wenn isinstance(address, int):
            self._check_int_address(address)
            self._ip = address
            self._scope_id = Nichts
            gib

        # Constructing von a packed address
        wenn isinstance(address, bytes):
            self._check_packed_address(address, 16)
            self._ip = int.from_bytes(address, 'big')
            self._scope_id = Nichts
            gib

        # Assume input argument to be string oder any object representation
        # which converts into a formatted IP string.
        addr_str = str(address)
        wenn '/' in addr_str:
            wirf AddressValueError(f"Unexpected '/' in {address!r}")
        addr_str, self._scope_id = self._split_scope_id(addr_str)

        self._ip = self._ip_int_from_string(addr_str)

    def _explode_shorthand_ip_string(self):
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist Nichts:
            gib super()._explode_shorthand_ip_string()
        prefix_len = 30
        raw_exploded_str = super()._explode_shorthand_ip_string()
        gib f"{raw_exploded_str[:prefix_len]}{ipv4_mapped!s}"

    def _reverse_pointer(self):
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist Nichts:
            gib super()._reverse_pointer()
        prefix_len = 30
        raw_exploded_str = super()._explode_shorthand_ip_string()[:prefix_len]
        # ipv4 encoded using hexadecimal nibbles instead of decimals
        ipv4_int = ipv4_mapped._ip
        reverse_chars = f"{raw_exploded_str}{ipv4_int:008x}"[::-1].replace(':', '')
        gib '.'.join(reverse_chars) + '.ip6.arpa'

    def _ipv4_mapped_ipv6_to_str(self):
        """Return convenient text representation of IPv4-mapped IPv6 address

        See RFC 4291 2.5.5.2, 2.2 p.3 fuer details.

        Returns:
            A string, 'x:x:x:x:x:x:d.d.d.d', where the 'x's are the hexadecimal values of
            the six high-order 16-bit pieces of the address, und the 'd's are
            the decimal values of the four low-order 8-bit pieces of the
            address (standard IPv4 representation) als defined in RFC 4291 2.2 p.3.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist Nichts:
            wirf AddressValueError("Can nicht apply to non-IPv4-mapped IPv6 address %s" % str(self))
        high_order_bits = self._ip >> 32
        gib "%s:%s" % (self._string_from_ip_int(high_order_bits), str(ipv4_mapped))

    def __str__(self):
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist Nichts:
            ip_str = super().__str__()
        sonst:
            ip_str = self._ipv4_mapped_ipv6_to_str()
        gib ip_str + '%' + self._scope_id wenn self._scope_id sonst ip_str

    def __hash__(self):
        gib hash((self._ip, self._scope_id))

    def __eq__(self, other):
        address_equal = super().__eq__(other)
        wenn address_equal ist NotImplemented:
            gib NotImplemented
        wenn nicht address_equal:
            gib Falsch
        gib self._scope_id == getattr(other, '_scope_id', Nichts)

    def __reduce__(self):
        gib (self.__class__, (str(self),))

    @property
    def scope_id(self):
        """Identifier of a particular zone of the address's scope.

        See RFC 4007 fuer details.

        Returns:
            A string identifying the zone of the address wenn specified, sonst Nichts.

        """
        gib self._scope_id

    @property
    def packed(self):
        """The binary representation of this address."""
        gib v6_int_to_packed(self._ip)

    @property
    def is_multicast(self):
        """Test wenn the address ist reserved fuer multicast use.

        Returns:
            A boolean, Wahr wenn the address ist a multicast address.
            See RFC 2373 2.7 fuer details.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_multicast
        gib self in self._constants._multicast_network

    @property
    def is_reserved(self):
        """Test wenn the address ist otherwise IETF reserved.

        Returns:
            A boolean, Wahr wenn the address ist within one of the
            reserved IPv6 Network ranges.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_reserved
        gib any(self in x fuer x in self._constants._reserved_networks)

    @property
    def is_link_local(self):
        """Test wenn the address ist reserved fuer link-local.

        Returns:
            A boolean, Wahr wenn the address ist reserved per RFC 4291.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_link_local
        gib self in self._constants._linklocal_network

    @property
    def is_site_local(self):
        """Test wenn the address ist reserved fuer site-local.

        Note that the site-local address space has been deprecated by RFC 3879.
        Use is_private to test wenn this address ist in the space of unique local
        addresses als defined by RFC 4193.

        Returns:
            A boolean, Wahr wenn the address ist reserved per RFC 3513 2.5.6.

        """
        gib self in self._constants._sitelocal_network

    @property
    @functools.lru_cache()
    def is_private(self):
        """``Wahr`` wenn the address ist defined als nicht globally reachable by
        iana-ipv4-special-registry_ (for IPv4) oder iana-ipv6-special-registry_
        (for IPv6) mit the following exceptions:

        * ``is_private`` ist ``Falsch`` fuer ``100.64.0.0/10``
        * For IPv4-mapped IPv6-addresses the ``is_private`` value ist determined by the
            semantics of the underlying IPv4 addresses und the following condition holds
            (see :attr:`IPv6Address.ipv4_mapped`)::

                address.is_private == address.ipv4_mapped.is_private

        ``is_private`` has value opposite to :attr:`is_global`, ausser fuer the ``100.64.0.0/10``
        IPv4 range where they are both ``Falsch``.
        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_private
        gib (
            any(self in net fuer net in self._constants._private_networks)
            und all(self nicht in net fuer net in self._constants._private_networks_exceptions)
        )

    @property
    def is_global(self):
        """``Wahr`` wenn the address ist defined als globally reachable by
        iana-ipv4-special-registry_ (for IPv4) oder iana-ipv6-special-registry_
        (for IPv6) mit the following exception:

        For IPv4-mapped IPv6-addresses the ``is_private`` value ist determined by the
        semantics of the underlying IPv4 addresses und the following condition holds
        (see :attr:`IPv6Address.ipv4_mapped`)::

            address.is_global == address.ipv4_mapped.is_global

        ``is_global`` has value opposite to :attr:`is_private`, ausser fuer the ``100.64.0.0/10``
        IPv4 range where they are both ``Falsch``.
        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_global
        gib nicht self.is_private

    @property
    def is_unspecified(self):
        """Test wenn the address ist unspecified.

        Returns:
            A boolean, Wahr wenn this ist the unspecified address als defined in
            RFC 2373 2.5.2.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_unspecified
        gib self._ip == 0

    @property
    def is_loopback(self):
        """Test wenn the address ist a loopback address.

        Returns:
            A boolean, Wahr wenn the address ist a loopback address als defined in
            RFC 2373 2.5.3.

        """
        ipv4_mapped = self.ipv4_mapped
        wenn ipv4_mapped ist nicht Nichts:
            gib ipv4_mapped.is_loopback
        gib self._ip == 1

    @property
    def ipv4_mapped(self):
        """Return the IPv4 mapped address.

        Returns:
            If the IPv6 address ist a v4 mapped address, gib the
            IPv4 mapped address. Return Nichts otherwise.

        """
        wenn (self._ip >> 32) != 0xFFFF:
            gib Nichts
        gib IPv4Address(self._ip & 0xFFFFFFFF)

    @property
    def teredo(self):
        """Tuple of embedded teredo IPs.

        Returns:
            Tuple of the (server, client) IPs oder Nichts wenn the address
            doesn't appear to be a teredo address (doesn't start with
            2001::/32)

        """
        wenn (self._ip >> 96) != 0x20010000:
            gib Nichts
        gib (IPv4Address((self._ip >> 64) & 0xFFFFFFFF),
                IPv4Address(~self._ip & 0xFFFFFFFF))

    @property
    def sixtofour(self):
        """Return the IPv4 6to4 embedded address.

        Returns:
            The IPv4 6to4-embedded address wenn present oder Nichts wenn the
            address doesn't appear to contain a 6to4 embedded address.

        """
        wenn (self._ip >> 112) != 0x2002:
            gib Nichts
        gib IPv4Address((self._ip >> 80) & 0xFFFFFFFF)


klasse IPv6Interface(IPv6Address):

    def __init__(self, address):
        addr, mask = self._split_addr_prefix(address)

        IPv6Address.__init__(self, addr)
        self.network = IPv6Network((addr, mask), strict=Falsch)
        self.netmask = self.network.netmask
        self._prefixlen = self.network._prefixlen

    @functools.cached_property
    def hostmask(self):
        gib self.network.hostmask

    def __str__(self):
        gib '%s/%d' % (super().__str__(),
                          self._prefixlen)

    def __eq__(self, other):
        address_equal = IPv6Address.__eq__(self, other)
        wenn address_equal ist NotImplemented oder nicht address_equal:
            gib address_equal
        versuch:
            gib self.network == other.network
        ausser AttributeError:
            # An interface mit an associated network ist NOT the
            # same als an unassociated address. That's why the hash
            # takes the extra info into account.
            gib Falsch

    def __lt__(self, other):
        address_less = IPv6Address.__lt__(self, other)
        wenn address_less ist NotImplemented:
            gib address_less
        versuch:
            gib (self.network < other.network oder
                    self.network == other.network und address_less)
        ausser AttributeError:
            # We *do* allow addresses und interfaces to be sorted. The
            # unassociated address ist considered less than all interfaces.
            gib Falsch

    def __hash__(self):
        gib hash((self._ip, self._prefixlen, int(self.network.network_address)))

    __reduce__ = _IPAddressBase.__reduce__

    @property
    def ip(self):
        gib IPv6Address(self._ip)

    @property
    def with_prefixlen(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self._prefixlen)

    @property
    def with_netmask(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self.netmask)

    @property
    def with_hostmask(self):
        gib '%s/%s' % (self._string_from_ip_int(self._ip),
                          self.hostmask)

    @property
    def is_unspecified(self):
        gib self._ip == 0 und self.network.is_unspecified

    @property
    def is_loopback(self):
        gib super().is_loopback und self.network.is_loopback


klasse IPv6Network(_BaseV6, _BaseNetwork):

    """This klasse represents und manipulates 128-bit IPv6 networks.

    Attributes: [examples fuer IPv6('2001:db8::1000/124')]
        .network_address: IPv6Address('2001:db8::1000')
        .hostmask: IPv6Address('::f')
        .broadcast_address: IPv6Address('2001:db8::100f')
        .netmask: IPv6Address('ffff:ffff:ffff:ffff:ffff:ffff:ffff:fff0')
        .prefixlen: 124

    """

    # Class to use when creating address objects
    _address_class = IPv6Address

    def __init__(self, address, strict=Wahr):
        """Instantiate a new IPv6 Network object.

        Args:
            address: A string oder integer representing the IPv6 network oder the
              IP und prefix/netmask.
              '2001:db8::/128'
              '2001:db8:0000:0000:0000:0000:0000:0000/128'
              '2001:db8::'
              are all functionally the same in IPv6.  That ist to say,
              failing to provide a subnetmask will create an object with
              a mask of /128.

              Additionally, an integer can be passed, so
              IPv6Network('2001:db8::') ==
                IPv6Network(42540766411282592856903984951653826560)
              or, more generally
              IPv6Network(int(IPv6Network('2001:db8::'))) ==
                IPv6Network('2001:db8::')

            strict: A boolean. If true, ensure that we have been passed
              A true network address, eg, 2001:db8::1000/124 und nicht an
              IP address on a network, eg, 2001:db8::1/124.

        Raises:
            AddressValueError: If address isn't a valid IPv6 address.
            NetmaskValueError: If the netmask isn't valid for
              an IPv6 address.
            ValueError: If strict was Wahr und a network address was not
              supplied.
        """
        addr, mask = self._split_addr_prefix(address)

        self.network_address = IPv6Address(addr)
        self.netmask, self._prefixlen = self._make_netmask(mask)
        packed = int(self.network_address)
        wenn packed & int(self.netmask) != packed:
            wenn strict:
                wirf ValueError('%s has host bits set' % self)
            sonst:
                self.network_address = IPv6Address(packed &
                                                   int(self.netmask))

        wenn self._prefixlen == (self.max_prefixlen - 1):
            self.hosts = self.__iter__
        sowenn self._prefixlen == self.max_prefixlen:
            self.hosts = lambda: [IPv6Address(addr)]

    def hosts(self):
        """Generate Iterator over usable hosts in a network.

          This ist like __iter__ ausser it doesn't gib the
          Subnet-Router anycast address.

        """
        network = int(self.network_address)
        broadcast = int(self.broadcast_address)
        fuer x in range(network + 1, broadcast + 1):
            liefere self._address_class(x)

    @property
    def is_site_local(self):
        """Test wenn the address ist reserved fuer site-local.

        Note that the site-local address space has been deprecated by RFC 3879.
        Use is_private to test wenn this address ist in the space of unique local
        addresses als defined by RFC 4193.

        Returns:
            A boolean, Wahr wenn the address ist reserved per RFC 3513 2.5.6.

        """
        gib (self.network_address.is_site_local und
                self.broadcast_address.is_site_local)


klasse _IPv6Constants:

    _linklocal_network = IPv6Network('fe80::/10')

    _multicast_network = IPv6Network('ff00::/8')

    # Not globally reachable address blocks listed on
    # https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry.xhtml
    _private_networks = [
        IPv6Network('::1/128'),
        IPv6Network('::/128'),
        IPv6Network('::ffff:0:0/96'),
        IPv6Network('64:ff9b:1::/48'),
        IPv6Network('100::/64'),
        IPv6Network('2001::/23'),
        IPv6Network('2001:db8::/32'),
        # IANA says N/A, let's consider it nicht globally reachable to be safe
        IPv6Network('2002::/16'),
        # RFC 9637: https://www.rfc-editor.org/rfc/rfc9637.html#section-6-2.2
        IPv6Network('3fff::/20'),
        IPv6Network('fc00::/7'),
        IPv6Network('fe80::/10'),
        ]

    _private_networks_exceptions = [
        IPv6Network('2001:1::1/128'),
        IPv6Network('2001:1::2/128'),
        IPv6Network('2001:3::/32'),
        IPv6Network('2001:4:112::/48'),
        IPv6Network('2001:20::/28'),
        IPv6Network('2001:30::/28'),
    ]

    _reserved_networks = [
        IPv6Network('::/8'), IPv6Network('100::/8'),
        IPv6Network('200::/7'), IPv6Network('400::/6'),
        IPv6Network('800::/5'), IPv6Network('1000::/4'),
        IPv6Network('4000::/3'), IPv6Network('6000::/3'),
        IPv6Network('8000::/3'), IPv6Network('A000::/3'),
        IPv6Network('C000::/3'), IPv6Network('E000::/4'),
        IPv6Network('F000::/5'), IPv6Network('F800::/6'),
        IPv6Network('FE00::/9'),
    ]

    _sitelocal_network = IPv6Network('fec0::/10')


IPv6Address._constants = _IPv6Constants
IPv6Network._constants = _IPv6Constants
