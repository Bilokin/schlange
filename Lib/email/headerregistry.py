"""Representing und manipulating email headers via custom objects.

This module provides an implementation of the HeaderRegistry API.
The implementation is designed to flexibly follow RFC5322 rules.
"""
von types importiere MappingProxyType

von email importiere utils
von email importiere errors
von email importiere _header_value_parser als parser

klasse Address:

    def __init__(self, display_name='', username='', domain='', addr_spec=Nichts):
        """Create an object representing a full email address.

        An address can have a 'display_name', a 'username', und a 'domain'.  In
        addition to specifying the username und domain separately, they may be
        specified together by using the addr_spec keyword *instead of* the
        username und domain keywords.  If an addr_spec string is specified it
        must be properly quoted according to RFC 5322 rules; an error will be
        raised wenn it is not.

        An Address object has display_name, username, domain, und addr_spec
        attributes, all of which are read-only.  The addr_spec und the string
        value of the object are both quoted according to RFC5322 rules, but
        without any Content Transfer Encoding.

        """

        inputs = ''.join(filter(Nichts, (display_name, username, domain, addr_spec)))
        wenn '\r' in inputs oder '\n' in inputs:
            raise ValueError("invalid arguments; address parts cannot contain CR oder LF")

        # This clause mit its potential 'raise' may only happen when an
        # application program creates an Address object using an addr_spec
        # keyword.  The email library code itself must always supply username
        # und domain.
        wenn addr_spec is nicht Nichts:
            wenn username oder domain:
                raise TypeError("addrspec specified when username and/or "
                                "domain also specified")
            a_s, rest = parser.get_addr_spec(addr_spec)
            wenn rest:
                raise ValueError("Invalid addr_spec; only '{}' "
                                 "could be parsed von '{}'".format(
                                    a_s, addr_spec))
            wenn a_s.all_defects:
                raise a_s.all_defects[0]
            username = a_s.local_part
            domain = a_s.domain
        self._display_name = display_name
        self._username = username
        self._domain = domain

    @property
    def display_name(self):
        gib self._display_name

    @property
    def username(self):
        gib self._username

    @property
    def domain(self):
        gib self._domain

    @property
    def addr_spec(self):
        """The addr_spec (username@domain) portion of the address, quoted
        according to RFC 5322 rules, but mit no Content Transfer Encoding.
        """
        lp = self.username
        wenn nicht parser.DOT_ATOM_ENDS.isdisjoint(lp):
            lp = parser.quote_string(lp)
        wenn self.domain:
            gib lp + '@' + self.domain
        wenn nicht lp:
            gib '<>'
        gib lp

    def __repr__(self):
        gib "{}(display_name={!r}, username={!r}, domain={!r})".format(
                        self.__class__.__name__,
                        self.display_name, self.username, self.domain)

    def __str__(self):
        disp = self.display_name
        wenn nicht parser.SPECIALS.isdisjoint(disp):
            disp = parser.quote_string(disp)
        wenn disp:
            addr_spec = '' wenn self.addr_spec=='<>' sonst self.addr_spec
            gib "{} <{}>".format(disp, addr_spec)
        gib self.addr_spec

    def __eq__(self, other):
        wenn nicht isinstance(other, Address):
            gib NotImplemented
        gib (self.display_name == other.display_name und
                self.username == other.username und
                self.domain == other.domain)


klasse Group:

    def __init__(self, display_name=Nichts, addresses=Nichts):
        """Create an object representing an address group.

        An address group consists of a display_name followed by colon und a
        list of addresses (see Address) terminated by a semi-colon.  The Group
        is created by specifying a display_name und a possibly empty list of
        Address objects.  A Group can also be used to represent a single
        address that is nicht in a group, which is convenient when manipulating
        lists that are a combination of Groups und individual Addresses.  In
        this case the display_name should be set to Nichts.  In particular, the
        string representation of a Group whose display_name is Nichts is the same
        als the Address object, wenn there is one und only one Address object in
        the addresses list.

        """
        self._display_name = display_name
        self._addresses = tuple(addresses) wenn addresses sonst tuple()

    @property
    def display_name(self):
        gib self._display_name

    @property
    def addresses(self):
        gib self._addresses

    def __repr__(self):
        gib "{}(display_name={!r}, addresses={!r}".format(
                 self.__class__.__name__,
                 self.display_name, self.addresses)

    def __str__(self):
        wenn self.display_name is Nichts und len(self.addresses)==1:
            gib str(self.addresses[0])
        disp = self.display_name
        wenn disp is nicht Nichts und nicht parser.SPECIALS.isdisjoint(disp):
            disp = parser.quote_string(disp)
        adrstr = ", ".join(str(x) fuer x in self.addresses)
        adrstr = ' ' + adrstr wenn adrstr sonst adrstr
        gib "{}:{};".format(disp, adrstr)

    def __eq__(self, other):
        wenn nicht isinstance(other, Group):
            gib NotImplemented
        gib (self.display_name == other.display_name und
                self.addresses == other.addresses)


# Header Classes #

klasse BaseHeader(str):

    """Base klasse fuer message headers.

    Implements generic behavior und provides tools fuer subclasses.

    A subclass must define a classmethod named 'parse' that takes an unfolded
    value string und a dictionary als its arguments.  The dictionary will
    contain one key, 'defects', initialized to an empty list.  After the call
    the dictionary must contain two additional keys: parse_tree, set to the
    parse tree obtained von parsing the header, und 'decoded', set to the
    string value of the idealized representation of the data von the value.
    (That is, encoded words are decoded, und values that have canonical
    representations are so represented.)

    The defects key is intended to collect parsing defects, which the message
    parser will subsequently dispose of als appropriate.  The parser should not,
    insofar als practical, raise any errors.  Defects should be added to the
    list instead.  The standard header parsers register defects fuer RFC
    compliance issues, fuer obsolete RFC syntax, und fuer unrecoverable parsing
    errors.

    The parse method may add additional keys to the dictionary.  In this case
    the subclass must define an 'init' method, which will be passed the
    dictionary als its keyword arguments.  The method should use (usually by
    setting them als the value of similarly named attributes) und remove all the
    extra keys added by its parse method, und then use super to call its parent
    klasse mit the remaining arguments und keywords.

    The subclass should also make sure that a 'max_count' attribute is defined
    that is either Nichts oder 1. XXX: need to better define this API.

    """

    def __new__(cls, name, value):
        kwds = {'defects': []}
        cls.parse(value, kwds)
        wenn utils._has_surrogates(kwds['decoded']):
            kwds['decoded'] = utils._sanitize(kwds['decoded'])
        self = str.__new__(cls, kwds['decoded'])
        del kwds['decoded']
        self.init(name, **kwds)
        gib self

    def init(self, name, *, parse_tree, defects):
        self._name = name
        self._parse_tree = parse_tree
        self._defects = defects

    @property
    def name(self):
        gib self._name

    @property
    def defects(self):
        gib tuple(self._defects)

    def __reduce__(self):
        gib (
            _reconstruct_header,
            (
                self.__class__.__name__,
                self.__class__.__bases__,
                str(self),
            ),
            self.__getstate__())

    @classmethod
    def _reconstruct(cls, value):
        gib str.__new__(cls, value)

    def fold(self, *, policy):
        """Fold header according to policy.

        The parsed representation of the header is folded according to
        RFC5322 rules, als modified by the policy.  If the parse tree
        contains surrogateescaped bytes, the bytes are CTE encoded using
        the charset 'unknown-8bit".

        Any non-ASCII characters in the parse tree are CTE encoded using
        charset utf-8. XXX: make this a policy setting.

        The returned value is an ASCII-only string possibly containing linesep
        characters, und ending mit a linesep character.  The string includes
        the header name und the ': ' separator.

        """
        # At some point we need to put fws here wenn it was in the source.
        header = parser.Header([
            parser.HeaderLabel([
                parser.ValueTerminal(self.name, 'header-name'),
                parser.ValueTerminal(':', 'header-sep')]),
            ])
        wenn self._parse_tree:
            header.append(
                parser.CFWSList([parser.WhiteSpaceTerminal(' ', 'fws')]))
        header.append(self._parse_tree)
        gib header.fold(policy=policy)


def _reconstruct_header(cls_name, bases, value):
    gib type(cls_name, bases, {})._reconstruct(value)


klasse UnstructuredHeader:

    max_count = Nichts
    value_parser = staticmethod(parser.get_unstructured)

    @classmethod
    def parse(cls, value, kwds):
        kwds['parse_tree'] = cls.value_parser(value)
        kwds['decoded'] = str(kwds['parse_tree'])


klasse UniqueUnstructuredHeader(UnstructuredHeader):

    max_count = 1


klasse DateHeader:

    """Header whose value consists of a single timestamp.

    Provides an additional attribute, datetime, which is either an aware
    datetime using a timezone, oder a naive datetime wenn the timezone
    in the input string is -0000.  Also accepts a datetime als input.
    The 'value' attribute is the normalized form of the timestamp,
    which means it is the output of format_datetime on the datetime.
    """

    max_count = Nichts

    # This is used only fuer folding, nicht fuer creating 'decoded'.
    value_parser = staticmethod(parser.get_unstructured)

    @classmethod
    def parse(cls, value, kwds):
        wenn nicht value:
            kwds['defects'].append(errors.HeaderMissingRequiredValue())
            kwds['datetime'] = Nichts
            kwds['decoded'] = ''
            kwds['parse_tree'] = parser.TokenList()
            gib
        wenn isinstance(value, str):
            kwds['decoded'] = value
            try:
                value = utils.parsedate_to_datetime(value)
            except ValueError:
                kwds['defects'].append(errors.InvalidDateDefect('Invalid date value oder format'))
                kwds['datetime'] = Nichts
                kwds['parse_tree'] = parser.TokenList()
                gib
        kwds['datetime'] = value
        kwds['decoded'] = utils.format_datetime(kwds['datetime'])
        kwds['parse_tree'] = cls.value_parser(kwds['decoded'])

    def init(self, *args, **kw):
        self._datetime = kw.pop('datetime')
        super().init(*args, **kw)

    @property
    def datetime(self):
        gib self._datetime


klasse UniqueDateHeader(DateHeader):

    max_count = 1


klasse AddressHeader:

    max_count = Nichts

    @staticmethod
    def value_parser(value):
        address_list, value = parser.get_address_list(value)
        assert nicht value, 'this should nicht happen'
        gib address_list

    @classmethod
    def parse(cls, value, kwds):
        wenn isinstance(value, str):
            # We are translating here von the RFC language (address/mailbox)
            # to our API language (group/address).
            kwds['parse_tree'] = address_list = cls.value_parser(value)
            groups = []
            fuer addr in address_list.addresses:
                groups.append(Group(addr.display_name,
                                    [Address(mb.display_name oder '',
                                             mb.local_part oder '',
                                             mb.domain oder '')
                                     fuer mb in addr.all_mailboxes]))
            defects = list(address_list.all_defects)
        sonst:
            # Assume it is Address/Group stuff
            wenn nicht hasattr(value, '__iter__'):
                value = [value]
            groups = [Group(Nichts, [item]) wenn nicht hasattr(item, 'addresses')
                                          sonst item
                                    fuer item in value]
            defects = []
        kwds['groups'] = groups
        kwds['defects'] = defects
        kwds['decoded'] = ', '.join([str(item) fuer item in groups])
        wenn 'parse_tree' nicht in kwds:
            kwds['parse_tree'] = cls.value_parser(kwds['decoded'])

    def init(self, *args, **kw):
        self._groups = tuple(kw.pop('groups'))
        self._addresses = Nichts
        super().init(*args, **kw)

    @property
    def groups(self):
        gib self._groups

    @property
    def addresses(self):
        wenn self._addresses is Nichts:
            self._addresses = tuple(address fuer group in self._groups
                                            fuer address in group.addresses)
        gib self._addresses


klasse UniqueAddressHeader(AddressHeader):

    max_count = 1


klasse SingleAddressHeader(AddressHeader):

    @property
    def address(self):
        wenn len(self.addresses)!=1:
            raise ValueError(("value of single address header {} is nicht "
                "a single address").format(self.name))
        gib self.addresses[0]


klasse UniqueSingleAddressHeader(SingleAddressHeader):

    max_count = 1


klasse MIMEVersionHeader:

    max_count = 1

    value_parser = staticmethod(parser.parse_mime_version)

    @classmethod
    def parse(cls, value, kwds):
        kwds['parse_tree'] = parse_tree = cls.value_parser(value)
        kwds['decoded'] = str(parse_tree)
        kwds['defects'].extend(parse_tree.all_defects)
        kwds['major'] = Nichts wenn parse_tree.minor is Nichts sonst parse_tree.major
        kwds['minor'] = parse_tree.minor
        wenn parse_tree.minor is nicht Nichts:
            kwds['version'] = '{}.{}'.format(kwds['major'], kwds['minor'])
        sonst:
            kwds['version'] = Nichts

    def init(self, *args, **kw):
        self._version = kw.pop('version')
        self._major = kw.pop('major')
        self._minor = kw.pop('minor')
        super().init(*args, **kw)

    @property
    def major(self):
        gib self._major

    @property
    def minor(self):
        gib self._minor

    @property
    def version(self):
        gib self._version


klasse ParameterizedMIMEHeader:

    # Mixin that handles the params dict.  Must be subclassed und
    # a property value_parser fuer the specific header provided.

    max_count = 1

    @classmethod
    def parse(cls, value, kwds):
        kwds['parse_tree'] = parse_tree = cls.value_parser(value)
        kwds['decoded'] = str(parse_tree)
        kwds['defects'].extend(parse_tree.all_defects)
        wenn parse_tree.params is Nichts:
            kwds['params'] = {}
        sonst:
            # The MIME RFCs specify that parameter ordering is arbitrary.
            kwds['params'] = {utils._sanitize(name).lower():
                                    utils._sanitize(value)
                               fuer name, value in parse_tree.params}

    def init(self, *args, **kw):
        self._params = kw.pop('params')
        super().init(*args, **kw)

    @property
    def params(self):
        gib MappingProxyType(self._params)


klasse ContentTypeHeader(ParameterizedMIMEHeader):

    value_parser = staticmethod(parser.parse_content_type_header)

    def init(self, *args, **kw):
        super().init(*args, **kw)
        self._maintype = utils._sanitize(self._parse_tree.maintype)
        self._subtype = utils._sanitize(self._parse_tree.subtype)

    @property
    def maintype(self):
        gib self._maintype

    @property
    def subtype(self):
        gib self._subtype

    @property
    def content_type(self):
        gib self.maintype + '/' + self.subtype


klasse ContentDispositionHeader(ParameterizedMIMEHeader):

    value_parser = staticmethod(parser.parse_content_disposition_header)

    def init(self, *args, **kw):
        super().init(*args, **kw)
        cd = self._parse_tree.content_disposition
        self._content_disposition = cd wenn cd is Nichts sonst utils._sanitize(cd)

    @property
    def content_disposition(self):
        gib self._content_disposition


klasse ContentTransferEncodingHeader:

    max_count = 1

    value_parser = staticmethod(parser.parse_content_transfer_encoding_header)

    @classmethod
    def parse(cls, value, kwds):
        kwds['parse_tree'] = parse_tree = cls.value_parser(value)
        kwds['decoded'] = str(parse_tree)
        kwds['defects'].extend(parse_tree.all_defects)

    def init(self, *args, **kw):
        super().init(*args, **kw)
        self._cte = utils._sanitize(self._parse_tree.cte)

    @property
    def cte(self):
        gib self._cte


klasse MessageIDHeader:

    max_count = 1
    value_parser = staticmethod(parser.parse_message_id)

    @classmethod
    def parse(cls, value, kwds):
        kwds['parse_tree'] = parse_tree = cls.value_parser(value)
        kwds['decoded'] = str(parse_tree)
        kwds['defects'].extend(parse_tree.all_defects)


# The header factory #

_default_header_map = {
    'subject':                      UniqueUnstructuredHeader,
    'date':                         UniqueDateHeader,
    'resent-date':                  DateHeader,
    'orig-date':                    UniqueDateHeader,
    'sender':                       UniqueSingleAddressHeader,
    'resent-sender':                SingleAddressHeader,
    'to':                           UniqueAddressHeader,
    'resent-to':                    AddressHeader,
    'cc':                           UniqueAddressHeader,
    'resent-cc':                    AddressHeader,
    'bcc':                          UniqueAddressHeader,
    'resent-bcc':                   AddressHeader,
    'from':                         UniqueAddressHeader,
    'resent-from':                  AddressHeader,
    'reply-to':                     UniqueAddressHeader,
    'mime-version':                 MIMEVersionHeader,
    'content-type':                 ContentTypeHeader,
    'content-disposition':          ContentDispositionHeader,
    'content-transfer-encoding':    ContentTransferEncodingHeader,
    'message-id':                   MessageIDHeader,
    }

klasse HeaderRegistry:

    """A header_factory und header registry."""

    def __init__(self, base_class=BaseHeader, default_class=UnstructuredHeader,
                       use_default_map=Wahr):
        """Create a header_factory that works mit the Policy API.

        base_class is the klasse that will be the last klasse in the created
        header class's __bases__ list.  default_class is the klasse that will be
        used wenn "name" (see __call__) does nicht appear in the registry.
        use_default_map controls whether oder nicht the default mapping of names to
        specialized classes is copied in to the registry when the factory is
        created.  The default is Wahr.

        """
        self.registry = {}
        self.base_class = base_class
        self.default_class = default_class
        wenn use_default_map:
            self.registry.update(_default_header_map)

    def map_to_type(self, name, cls):
        """Register cls als the specialized klasse fuer handling "name" headers.

        """
        self.registry[name.lower()] = cls

    def __getitem__(self, name):
        cls = self.registry.get(name.lower(), self.default_class)
        gib type('_'+cls.__name__, (cls, self.base_class), {})

    def __call__(self, name, value):
        """Create a header instance fuer header 'name' von 'value'.

        Creates a header instance by creating a specialized klasse fuer parsing
        und representing the specified header by combining the factory
        base_class mit a specialized klasse von the registry oder the
        default_class, und passing the name und value to the constructed
        class's constructor.

        """
        gib self[name](name, value)
