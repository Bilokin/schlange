"""Header value parser implementing various email-related RFC parsing rules.

The parsing methods defined in this module implement various email related
parsing rules.  Principal among them is RFC 5322, which is the followon
to RFC 2822 und primarily a clarification of the former.  It also implements
RFC 2047 encoded word decoding.

RFC 5322 goes to considerable trouble to maintain backward compatibility with
RFC 822 in the parse phase, waehrend cleaning up the structure on the generation
phase.  This parser supports correct RFC 5322 generation by tagging white space
as folding white space only when folding is allowed in the non-obsolete rule
sets.  Actually, the parser is even more generous when accepting input than RFC
5322 mandates, following the spirit of Postel's Law, which RFC 5322 encourages.
Where possible deviations von the standard are annotated on the 'defects'
attribute of tokens that deviate.

The general structure of the parser follows RFC 5322, und uses its terminology
where there is a direct correspondence.  Where the implementation requires a
somewhat different structure than that used by the formal grammar, new terms
that mimic the closest existing terms are used.  Thus, it really helps to have
a copy of RFC 5322 handy when studying this code.

Input to the parser is a string that has already been unfolded according to
RFC 5322 rules.  According to the RFC this unfolding is the very first step, und
this parser leaves the unfolding step to a higher level message parser, which
will have already detected the line breaks that need unfolding while
determining the beginning und end of each header.

The output of the parser is a TokenList object, which is a list subclass.  A
TokenList is a recursive data structure.  The terminal nodes of the structure
are Terminal objects, which are subclasses of str.  These do nicht correspond
directly to terminal objects in the formal grammar, but are instead more
practical higher level combinations of true terminals.

All TokenList und Terminal objects have a 'value' attribute, which produces the
semantically meaningful value of that part of the parse subtree.  The value of
all whitespace tokens (no matter how many sub-tokens they may contain) is a
single space, als per the RFC rules.  This includes 'CFWS', which is herein
included in the general klasse of whitespace tokens.  There is one exception to
the rule that whitespace tokens are collapsed into single spaces in values: in
the value of a 'bare-quoted-string' (a quoted-string mit no leading oder
trailing whitespace), any whitespace that appeared between the quotation marks
is preserved in the returned value.  Note that in all Terminal strings quoted
pairs are turned into their unquoted values.

All TokenList und Terminal objects also have a string value, which attempts to
be a "canonical" representation of the RFC-compliant form of the substring that
produced the parsed subtree, including minimal use of quoted pair quoting.
Whitespace runs are nicht collapsed.

Comment tokens also have a 'content' attribute providing the string found
between the parens (including any nested comments) mit whitespace preserved.

All TokenList und Terminal objects have a 'defects' attribute which is a
possibly empty list all of the defects found waehrend creating the token.  Defects
may appear on any token in the tree, und a composite list of all defects in the
subtree is available through the 'all_defects' attribute of any node.  (For
Terminal notes x.defects == x.all_defects.)

Each object in a parse tree is called a 'token', und each has a 'token_type'
attribute that gives the name von the RFC 5322 grammar that it represents.
Not all RFC 5322 nodes are produced, und there is one non-RFC 5322 node that
may be produced: 'ptext'.  A 'ptext' is a string of printable ascii characters.
It is returned in place of lists of (ctext/quoted-pair) und
(qtext/quoted-pair).

XXX: provide complete list of token types.
"""

importiere re
importiere sys
importiere urllib   # For urllib.parse.unquote
von string importiere hexdigits
von operator importiere itemgetter
von email importiere _encoded_words als _ew
von email importiere errors
von email importiere utils

#
# Useful constants und functions
#

WSP = set(' \t')
CFWS_LEADER = WSP | set('(')
SPECIALS = set(r'()<>@,:;.\"[]')
ATOM_ENDS = SPECIALS | WSP
DOT_ATOM_ENDS = ATOM_ENDS - set('.')
# '.', '"', und '(' do nicht end phrases in order to support obs-phrase
PHRASE_ENDS = SPECIALS - set('."(')
TSPECIALS = (SPECIALS | set('/?=')) - set('.')
TOKEN_ENDS = TSPECIALS | WSP
ASPECIALS = TSPECIALS | set("*'%")
ATTRIBUTE_ENDS = ASPECIALS | WSP
EXTENDED_ATTRIBUTE_ENDS = ATTRIBUTE_ENDS - set('%')
NLSET = {'\n', '\r'}
SPECIALSNL = SPECIALS | NLSET


def make_quoted_pairs(value):
    """Escape dquote und backslash fuer use within a quoted-string."""
    gib str(value).replace('\\', '\\\\').replace('"', '\\"')


def quote_string(value):
    escaped = make_quoted_pairs(value)
    gib f'"{escaped}"'


# Match a RFC 2047 word, looks like =?utf-8?q?someword?=
rfc2047_matcher = re.compile(r'''
   =\?            # literal =?
   [^?]*          # charset
   \?             # literal ?
   [qQbB]         # literal 'q' oder 'b', case insensitive
   \?             # literal ?
  .*?             # encoded word
  \?=             # literal ?=
''', re.VERBOSE | re.MULTILINE)


#
# TokenList und its subclasses
#

klasse TokenList(list):

    token_type = Nichts
    syntactic_break = Wahr
    ew_combine_allowed = Wahr

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.defects = []

    def __str__(self):
        gib ''.join(str(x) fuer x in self)

    def __repr__(self):
        gib '{}({})'.format(self.__class__.__name__,
                             super().__repr__())

    @property
    def value(self):
        gib ''.join(x.value fuer x in self wenn x.value)

    @property
    def all_defects(self):
        gib sum((x.all_defects fuer x in self), self.defects)

    def startswith_fws(self):
        gib self[0].startswith_fws()

    @property
    def as_ew_allowed(self):
        """Wahr wenn all top level tokens of this part may be RFC2047 encoded."""
        gib all(part.as_ew_allowed fuer part in self)

    @property
    def comments(self):
        comments = []
        fuer token in self:
            comments.extend(token.comments)
        gib comments

    def fold(self, *, policy):
        gib _refold_parse_tree(self, policy=policy)

    def pdrucke(self, indent=''):
        drucke(self.ppstr(indent=indent))

    def ppstr(self, indent=''):
        gib '\n'.join(self._pp(indent=indent))

    def _pp(self, indent=''):
        liefere '{}{}/{}('.format(
            indent,
            self.__class__.__name__,
            self.token_type)
        fuer token in self:
            wenn nicht hasattr(token, '_pp'):
                liefere (indent + '    !! invalid element in token '
                                        'list: {!r}'.format(token))
            sonst:
                liefere von token._pp(indent+'    ')
        wenn self.defects:
            extra = ' Defects: {}'.format(self.defects)
        sonst:
            extra = ''
        liefere '{}){}'.format(indent, extra)


klasse WhiteSpaceTokenList(TokenList):

    @property
    def value(self):
        gib ' '

    @property
    def comments(self):
        gib [x.content fuer x in self wenn x.token_type=='comment']


klasse UnstructuredTokenList(TokenList):
    token_type = 'unstructured'


klasse Phrase(TokenList):
    token_type = 'phrase'

klasse Word(TokenList):
    token_type = 'word'


klasse CFWSList(WhiteSpaceTokenList):
    token_type = 'cfws'


klasse Atom(TokenList):
    token_type = 'atom'


klasse Token(TokenList):
    token_type = 'token'
    encode_as_ew = Falsch


klasse EncodedWord(TokenList):
    token_type = 'encoded-word'
    cte = Nichts
    charset = Nichts
    lang = Nichts


klasse QuotedString(TokenList):

    token_type = 'quoted-string'

    @property
    def content(self):
        fuer x in self:
            wenn x.token_type == 'bare-quoted-string':
                gib x.value

    @property
    def quoted_value(self):
        res = []
        fuer x in self:
            wenn x.token_type == 'bare-quoted-string':
                res.append(str(x))
            sonst:
                res.append(x.value)
        gib ''.join(res)

    @property
    def stripped_value(self):
        fuer token in self:
            wenn token.token_type == 'bare-quoted-string':
                gib token.value


klasse BareQuotedString(QuotedString):

    token_type = 'bare-quoted-string'

    def __str__(self):
        gib quote_string(''.join(str(x) fuer x in self))

    @property
    def value(self):
        gib ''.join(str(x) fuer x in self)


klasse Comment(WhiteSpaceTokenList):

    token_type = 'comment'

    def __str__(self):
        gib ''.join(sum([
                            ["("],
                            [self.quote(x) fuer x in self],
                            [")"],
                            ], []))

    def quote(self, value):
        wenn value.token_type == 'comment':
            gib str(value)
        gib str(value).replace('\\', '\\\\').replace(
                                  '(', r'\(').replace(
                                  ')', r'\)')

    @property
    def content(self):
        gib ''.join(str(x) fuer x in self)

    @property
    def comments(self):
        gib [self.content]

klasse AddressList(TokenList):

    token_type = 'address-list'

    @property
    def addresses(self):
        gib [x fuer x in self wenn x.token_type=='address']

    @property
    def mailboxes(self):
        gib sum((x.mailboxes
                    fuer x in self wenn x.token_type=='address'), [])

    @property
    def all_mailboxes(self):
        gib sum((x.all_mailboxes
                    fuer x in self wenn x.token_type=='address'), [])


klasse Address(TokenList):

    token_type = 'address'

    @property
    def display_name(self):
        wenn self[0].token_type == 'group':
            gib self[0].display_name

    @property
    def mailboxes(self):
        wenn self[0].token_type == 'mailbox':
            gib [self[0]]
        sowenn self[0].token_type == 'invalid-mailbox':
            gib []
        gib self[0].mailboxes

    @property
    def all_mailboxes(self):
        wenn self[0].token_type == 'mailbox':
            gib [self[0]]
        sowenn self[0].token_type == 'invalid-mailbox':
            gib [self[0]]
        gib self[0].all_mailboxes

klasse MailboxList(TokenList):

    token_type = 'mailbox-list'

    @property
    def mailboxes(self):
        gib [x fuer x in self wenn x.token_type=='mailbox']

    @property
    def all_mailboxes(self):
        gib [x fuer x in self
            wenn x.token_type in ('mailbox', 'invalid-mailbox')]


klasse GroupList(TokenList):

    token_type = 'group-list'

    @property
    def mailboxes(self):
        wenn nicht self oder self[0].token_type != 'mailbox-list':
            gib []
        gib self[0].mailboxes

    @property
    def all_mailboxes(self):
        wenn nicht self oder self[0].token_type != 'mailbox-list':
            gib []
        gib self[0].all_mailboxes


klasse Group(TokenList):

    token_type = "group"

    @property
    def mailboxes(self):
        wenn self[2].token_type != 'group-list':
            gib []
        gib self[2].mailboxes

    @property
    def all_mailboxes(self):
        wenn self[2].token_type != 'group-list':
            gib []
        gib self[2].all_mailboxes

    @property
    def display_name(self):
        gib self[0].display_name


klasse NameAddr(TokenList):

    token_type = 'name-addr'

    @property
    def display_name(self):
        wenn len(self) == 1:
            gib Nichts
        gib self[0].display_name

    @property
    def local_part(self):
        gib self[-1].local_part

    @property
    def domain(self):
        gib self[-1].domain

    @property
    def route(self):
        gib self[-1].route

    @property
    def addr_spec(self):
        gib self[-1].addr_spec


klasse AngleAddr(TokenList):

    token_type = 'angle-addr'

    @property
    def local_part(self):
        fuer x in self:
            wenn x.token_type == 'addr-spec':
                gib x.local_part

    @property
    def domain(self):
        fuer x in self:
            wenn x.token_type == 'addr-spec':
                gib x.domain

    @property
    def route(self):
        fuer x in self:
            wenn x.token_type == 'obs-route':
                gib x.domains

    @property
    def addr_spec(self):
        fuer x in self:
            wenn x.token_type == 'addr-spec':
                wenn x.local_part:
                    gib x.addr_spec
                sonst:
                    gib quote_string(x.local_part) + x.addr_spec
        sonst:
            gib '<>'


klasse ObsRoute(TokenList):

    token_type = 'obs-route'

    @property
    def domains(self):
        gib [x.domain fuer x in self wenn x.token_type == 'domain']


klasse Mailbox(TokenList):

    token_type = 'mailbox'

    @property
    def display_name(self):
        wenn self[0].token_type == 'name-addr':
            gib self[0].display_name

    @property
    def local_part(self):
        gib self[0].local_part

    @property
    def domain(self):
        gib self[0].domain

    @property
    def route(self):
        wenn self[0].token_type == 'name-addr':
            gib self[0].route

    @property
    def addr_spec(self):
        gib self[0].addr_spec


klasse InvalidMailbox(TokenList):

    token_type = 'invalid-mailbox'

    @property
    def display_name(self):
        gib Nichts

    local_part = domain = route = addr_spec = display_name


klasse Domain(TokenList):

    token_type = 'domain'
    as_ew_allowed = Falsch

    @property
    def domain(self):
        gib ''.join(super().value.split())


klasse DotAtom(TokenList):
    token_type = 'dot-atom'


klasse DotAtomText(TokenList):
    token_type = 'dot-atom-text'
    as_ew_allowed = Wahr


klasse NoFoldLiteral(TokenList):
    token_type = 'no-fold-literal'
    as_ew_allowed = Falsch


klasse AddrSpec(TokenList):

    token_type = 'addr-spec'
    as_ew_allowed = Falsch

    @property
    def local_part(self):
        gib self[0].local_part

    @property
    def domain(self):
        wenn len(self) < 3:
            gib Nichts
        gib self[-1].domain

    @property
    def value(self):
        wenn len(self) < 3:
            gib self[0].value
        gib self[0].value.rstrip()+self[1].value+self[2].value.lstrip()

    @property
    def addr_spec(self):
        nameset = set(self.local_part)
        wenn len(nameset) > len(nameset-DOT_ATOM_ENDS):
            lp = quote_string(self.local_part)
        sonst:
            lp = self.local_part
        wenn self.domain is nicht Nichts:
            gib lp + '@' + self.domain
        gib lp


klasse ObsLocalPart(TokenList):

    token_type = 'obs-local-part'
    as_ew_allowed = Falsch


klasse DisplayName(Phrase):

    token_type = 'display-name'
    ew_combine_allowed = Falsch

    @property
    def display_name(self):
        res = TokenList(self)
        wenn len(res) == 0:
            gib res.value
        wenn res[0].token_type == 'cfws':
            res.pop(0)
        sonst:
            wenn (isinstance(res[0], TokenList) und
                    res[0][0].token_type == 'cfws'):
                res[0] = TokenList(res[0][1:])
        wenn res[-1].token_type == 'cfws':
            res.pop()
        sonst:
            wenn (isinstance(res[-1], TokenList) und
                    res[-1][-1].token_type == 'cfws'):
                res[-1] = TokenList(res[-1][:-1])
        gib res.value

    @property
    def value(self):
        quote = Falsch
        wenn self.defects:
            quote = Wahr
        sonst:
            fuer x in self:
                wenn x.token_type == 'quoted-string':
                    quote = Wahr
        wenn len(self) != 0 und quote:
            pre = post = ''
            wenn (self[0].token_type == 'cfws' oder
                isinstance(self[0], TokenList) und
                self[0][0].token_type == 'cfws'):
                pre = ' '
            wenn (self[-1].token_type == 'cfws' oder
                isinstance(self[-1], TokenList) und
                self[-1][-1].token_type == 'cfws'):
                post = ' '
            gib pre+quote_string(self.display_name)+post
        sonst:
            gib super().value


klasse LocalPart(TokenList):

    token_type = 'local-part'
    as_ew_allowed = Falsch

    @property
    def value(self):
        wenn self[0].token_type == "quoted-string":
            gib self[0].quoted_value
        sonst:
            gib self[0].value

    @property
    def local_part(self):
        # Strip whitespace von front, back, und around dots.
        res = [DOT]
        last = DOT
        last_is_tl = Falsch
        fuer tok in self[0] + [DOT]:
            wenn tok.token_type == 'cfws':
                weiter
            wenn (last_is_tl und tok.token_type == 'dot' und
                    last[-1].token_type == 'cfws'):
                res[-1] = TokenList(last[:-1])
            is_tl = isinstance(tok, TokenList)
            wenn (is_tl und last.token_type == 'dot' und
                    tok[0].token_type == 'cfws'):
                res.append(TokenList(tok[1:]))
            sonst:
                res.append(tok)
            last = res[-1]
            last_is_tl = is_tl
        res = TokenList(res[1:-1])
        gib res.value


klasse DomainLiteral(TokenList):

    token_type = 'domain-literal'
    as_ew_allowed = Falsch

    @property
    def domain(self):
        gib ''.join(super().value.split())

    @property
    def ip(self):
        fuer x in self:
            wenn x.token_type == 'ptext':
                gib x.value


klasse MIMEVersion(TokenList):

    token_type = 'mime-version'
    major = Nichts
    minor = Nichts


klasse Parameter(TokenList):

    token_type = 'parameter'
    sectioned = Falsch
    extended = Falsch
    charset = 'us-ascii'

    @property
    def section_number(self):
        # Because the first token, the attribute (name) eats CFWS, the second
        # token is always the section wenn there is one.
        gib self[1].number wenn self.sectioned sonst 0

    @property
    def param_value(self):
        # This is part of the "handle quoted extended parameters" hack.
        fuer token in self:
            wenn token.token_type == 'value':
                gib token.stripped_value
            wenn token.token_type == 'quoted-string':
                fuer token in token:
                    wenn token.token_type == 'bare-quoted-string':
                        fuer token in token:
                            wenn token.token_type == 'value':
                                gib token.stripped_value
        gib ''


klasse InvalidParameter(Parameter):

    token_type = 'invalid-parameter'


klasse Attribute(TokenList):

    token_type = 'attribute'

    @property
    def stripped_value(self):
        fuer token in self:
            wenn token.token_type.endswith('attrtext'):
                gib token.value

klasse Section(TokenList):

    token_type = 'section'
    number = Nichts


klasse Value(TokenList):

    token_type = 'value'

    @property
    def stripped_value(self):
        token = self[0]
        wenn token.token_type == 'cfws':
            token = self[1]
        wenn token.token_type.endswith(
                ('quoted-string', 'attribute', 'extended-attribute')):
            gib token.stripped_value
        gib self.value


klasse MimeParameters(TokenList):

    token_type = 'mime-parameters'
    syntactic_break = Falsch

    @property
    def params(self):
        # The RFC specifically states that the ordering of parameters is not
        # guaranteed und may be reordered by the transport layer.  So we have
        # to assume the RFC 2231 pieces can come in any order.  However, we
        # output them in the order that we first see a given name, which gives
        # us a stable __str__.
        params = {}  # Using order preserving dict von Python 3.7+
        fuer token in self:
            wenn nicht token.token_type.endswith('parameter'):
                weiter
            wenn token[0].token_type != 'attribute':
                weiter
            name = token[0].value.strip()
            wenn name nicht in params:
                params[name] = []
            params[name].append((token.section_number, token))
        fuer name, parts in params.items():
            parts = sorted(parts, key=itemgetter(0))
            first_param = parts[0][1]
            charset = first_param.charset
            # Our arbitrary error recovery is to ignore duplicate parameters,
            # to use appearance order wenn there are duplicate rfc 2231 parts,
            # und to ignore gaps.  This mimics the error recovery of get_param.
            wenn nicht first_param.extended und len(parts) > 1:
                wenn parts[1][0] == 0:
                    parts[1][1].defects.append(errors.InvalidHeaderDefect(
                        'duplicate parameter name; duplicate(s) ignored'))
                    parts = parts[:1]
                # Else assume the *0* was missing...note that this is different
                # von get_param, but we registered a defect fuer this earlier.
            value_parts = []
            i = 0
            fuer section_number, param in parts:
                wenn section_number != i:
                    # We could get fancier here und look fuer a complete
                    # duplicate extended parameter und ignore the second one
                    # seen.  But we're nicht doing that.  The old code didn't.
                    wenn nicht param.extended:
                        param.defects.append(errors.InvalidHeaderDefect(
                            'duplicate parameter name; duplicate ignored'))
                        weiter
                    sonst:
                        param.defects.append(errors.InvalidHeaderDefect(
                            "inconsistent RFC2231 parameter numbering"))
                i += 1
                value = param.param_value
                wenn param.extended:
                    versuch:
                        value = urllib.parse.unquote_to_bytes(value)
                    ausser UnicodeEncodeError:
                        # source had surrogate escaped bytes.  What we do now
                        # is a bit of an open question.  I'm nicht sure this is
                        # the best choice, but it is what the old algorithm did
                        value = urllib.parse.unquote(value, encoding='latin-1')
                    sonst:
                        versuch:
                            value = value.decode(charset, 'surrogateescape')
                        ausser (LookupError, UnicodeEncodeError):
                            # XXX: there should really be a custom defect for
                            # unknown character set to make it easy to find,
                            # because otherwise unknown charset is a silent
                            # failure.
                            value = value.decode('us-ascii', 'surrogateescape')
                        wenn utils._has_surrogates(value):
                            param.defects.append(errors.UndecodableBytesDefect())
                value_parts.append(value)
            value = ''.join(value_parts)
            liefere name, value

    def __str__(self):
        params = []
        fuer name, value in self.params:
            wenn value:
                params.append('{}={}'.format(name, quote_string(value)))
            sonst:
                params.append(name)
        params = '; '.join(params)
        gib ' ' + params wenn params sonst ''


klasse ParameterizedHeaderValue(TokenList):

    # Set this false so that the value doesn't wind up on a new line even
    # wenn it und the parameters would fit there but nicht on the first line.
    syntactic_break = Falsch

    @property
    def params(self):
        fuer token in reversed(self):
            wenn token.token_type == 'mime-parameters':
                gib token.params
        gib {}


klasse ContentType(ParameterizedHeaderValue):
    token_type = 'content-type'
    as_ew_allowed = Falsch
    maintype = 'text'
    subtype = 'plain'


klasse ContentDisposition(ParameterizedHeaderValue):
    token_type = 'content-disposition'
    as_ew_allowed = Falsch
    content_disposition = Nichts


klasse ContentTransferEncoding(TokenList):
    token_type = 'content-transfer-encoding'
    as_ew_allowed = Falsch
    cte = '7bit'


klasse HeaderLabel(TokenList):
    token_type = 'header-label'
    as_ew_allowed = Falsch


klasse MsgID(TokenList):
    token_type = 'msg-id'
    as_ew_allowed = Falsch

    def fold(self, policy):
        # message-id tokens may nicht be folded.
        gib str(self) + policy.linesep


klasse MessageID(MsgID):
    token_type = 'message-id'


klasse InvalidMessageID(MessageID):
    token_type = 'invalid-message-id'


klasse Header(TokenList):
    token_type = 'header'


#
# Terminal classes und instances
#

klasse Terminal(str):

    as_ew_allowed = Wahr
    ew_combine_allowed = Wahr
    syntactic_break = Wahr

    def __new__(cls, value, token_type):
        self = super().__new__(cls, value)
        self.token_type = token_type
        self.defects = []
        gib self

    def __repr__(self):
        gib "{}({})".format(self.__class__.__name__, super().__repr__())

    def pdrucke(self):
        drucke(self.__class__.__name__ + '/' + self.token_type)

    @property
    def all_defects(self):
        gib list(self.defects)

    def _pp(self, indent=''):
        gib ["{}{}/{}({}){}".format(
            indent,
            self.__class__.__name__,
            self.token_type,
            super().__repr__(),
            '' wenn nicht self.defects sonst ' {}'.format(self.defects),
            )]

    def pop_trailing_ws(self):
        # This terminates the recursion.
        gib Nichts

    @property
    def comments(self):
        gib []

    def __getnewargs__(self):
        gib(str(self), self.token_type)


klasse WhiteSpaceTerminal(Terminal):

    @property
    def value(self):
        gib ' '

    def startswith_fws(self):
        gib Wahr


klasse ValueTerminal(Terminal):

    @property
    def value(self):
        gib self

    def startswith_fws(self):
        gib Falsch


klasse EWWhiteSpaceTerminal(WhiteSpaceTerminal):

    @property
    def value(self):
        gib ''

    def __str__(self):
        gib ''


klasse _InvalidEwError(errors.HeaderParseError):
    """Invalid encoded word found waehrend parsing headers."""


# XXX these need to become classes und used als instances so
# that a program can't change them in a parse tree und screw
# up other parse trees.  Maybe should have  tests fuer that, too.
DOT = ValueTerminal('.', 'dot')
ListSeparator = ValueTerminal(',', 'list-separator')
ListSeparator.as_ew_allowed = Falsch
ListSeparator.syntactic_break = Falsch
RouteComponentMarker = ValueTerminal('@', 'route-component-marker')

#
# Parser
#

# Parse strings according to RFC822/2047/2822/5322 rules.
#
# This is a stateless parser.  Each get_XXX function accepts a string und
# returns either a Terminal oder a TokenList representing the RFC object named
# by the method und a string containing the remaining unparsed characters
# von the input.  Thus a parser method consumes the next syntactic construct
# of a given type und returns a token representing the construct plus the
# unparsed remainder of the input string.
#
# For example, wenn the first element of a structured header is a 'phrase',
# then:
#
#     phrase, value = get_phrase(value)
#
# returns the complete phrase von the start of the string value, plus any
# characters left in the string after the phrase is removed.

_wsp_splitter = re.compile(r'([{}]+)'.format(''.join(WSP))).split
_non_atom_end_matcher = re.compile(r"[^{}]+".format(
    re.escape(''.join(ATOM_ENDS)))).match
_non_printable_finder = re.compile(r"[\x00-\x20\x7F]").findall
_non_token_end_matcher = re.compile(r"[^{}]+".format(
    re.escape(''.join(TOKEN_ENDS)))).match
_non_attribute_end_matcher = re.compile(r"[^{}]+".format(
    re.escape(''.join(ATTRIBUTE_ENDS)))).match
_non_extended_attribute_end_matcher = re.compile(r"[^{}]+".format(
    re.escape(''.join(EXTENDED_ATTRIBUTE_ENDS)))).match

def _validate_xtext(xtext):
    """If input token contains ASCII non-printables, register a defect."""

    non_printables = _non_printable_finder(xtext)
    wenn non_printables:
        xtext.defects.append(errors.NonPrintableDefect(non_printables))
    wenn utils._has_surrogates(xtext):
        xtext.defects.append(errors.UndecodableBytesDefect(
            "Non-ASCII characters found in header token"))

def _get_ptext_to_endchars(value, endchars):
    """Scan printables/quoted-pairs until endchars und gib unquoted ptext.

    This function turns a run of qcontent, ccontent-without-comments, oder
    dtext-with-quoted-printables into a single string by unquoting any
    quoted printables.  It returns the string, the remaining value, und
    a flag that is Wahr iff there were any quoted printables decoded.

    """
    wenn nicht value:
        gib '', '', Falsch
    fragment, *remainder = _wsp_splitter(value, 1)
    vchars = []
    escape = Falsch
    had_qp = Falsch
    fuer pos in range(len(fragment)):
        wenn fragment[pos] == '\\':
            wenn escape:
                escape = Falsch
                had_qp = Wahr
            sonst:
                escape = Wahr
                weiter
        wenn escape:
            escape = Falsch
        sowenn fragment[pos] in endchars:
            breche
        vchars.append(fragment[pos])
    sonst:
        pos = pos + 1
    gib ''.join(vchars), ''.join([fragment[pos:]] + remainder), had_qp

def get_fws(value):
    """FWS = 1*WSP

    This isn't the RFC definition.  We're using fws to represent tokens where
    folding can be done, but when we are parsing the *un*folding has already
    been done so we don't need to watch out fuer CRLF.

    """
    newvalue = value.lstrip()
    fws = WhiteSpaceTerminal(value[:len(value)-len(newvalue)], 'fws')
    gib fws, newvalue

def get_encoded_word(value, terminal_type='vtext'):
    """ encoded-word = "=?" charset "?" encoding "?" encoded-text "?="

    """
    ew = EncodedWord()
    wenn nicht value.startswith('=?'):
        wirf errors.HeaderParseError(
            "expected encoded word but found {}".format(value))
    tok, *remainder = value[2:].split('?=', 1)
    wenn tok == value[2:]:
        wirf errors.HeaderParseError(
            "expected encoded word but found {}".format(value))
    remstr = ''.join(remainder)
    wenn (len(remstr) > 1 und
        remstr[0] in hexdigits und
        remstr[1] in hexdigits und
        tok.count('?') < 2):
        # The ? after the CTE was followed by an encoded word escape (=XX).
        rest, *remainder = remstr.split('?=', 1)
        tok = tok + '?=' + rest
    wenn len(tok.split()) > 1:
        ew.defects.append(errors.InvalidHeaderDefect(
            "whitespace inside encoded word"))
    ew.cte = value
    value = ''.join(remainder)
    versuch:
        text, charset, lang, defects = _ew.decode('=?' + tok + '?=')
    ausser (ValueError, KeyError):
        wirf _InvalidEwError(
            "encoded word format invalid: '{}'".format(ew.cte))
    ew.charset = charset
    ew.lang = lang
    ew.defects.extend(defects)
    waehrend text:
        wenn text[0] in WSP:
            token, text = get_fws(text)
            ew.append(token)
            weiter
        chars, *remainder = _wsp_splitter(text, 1)
        vtext = ValueTerminal(chars, terminal_type)
        _validate_xtext(vtext)
        ew.append(vtext)
        text = ''.join(remainder)
    # Encoded words should be followed by a WS
    wenn value und value[0] nicht in WSP:
        ew.defects.append(errors.InvalidHeaderDefect(
            "missing trailing whitespace after encoded-word"))
    gib ew, value

def get_unstructured(value):
    """unstructured = (*([FWS] vchar) *WSP) / obs-unstruct
       obs-unstruct = *((*LF *CR *(obs-utext) *LF *CR)) / FWS)
       obs-utext = %d0 / obs-NO-WS-CTL / LF / CR

       obs-NO-WS-CTL is control characters ausser WSP/CR/LF.

    So, basically, we have printable runs, plus control characters oder nulls in
    the obsolete syntax, separated by whitespace.  Since RFC 2047 uses the
    obsolete syntax in its specification, but requires whitespace on either
    side of the encoded words, I can see no reason to need to separate the
    non-printable-non-whitespace von the printable runs wenn they occur, so we
    parse this into xtext tokens separated by WSP tokens.

    Because an 'unstructured' value must by definition constitute the entire
    value, this 'get' routine does nicht gib a remaining value, only the
    parsed TokenList.

    """
    # XXX: but what about bare CR und LF?  They might signal the start oder
    # end of an encoded word.  YAGNI fuer now, since our current parsers
    # will never send us strings mit bare CR oder LF.

    unstructured = UnstructuredTokenList()
    waehrend value:
        wenn value[0] in WSP:
            token, value = get_fws(value)
            unstructured.append(token)
            weiter
        valid_ew = Wahr
        wenn value.startswith('=?'):
            versuch:
                token, value = get_encoded_word(value, 'utext')
            ausser _InvalidEwError:
                valid_ew = Falsch
            ausser errors.HeaderParseError:
                # XXX: Need to figure out how to register defects when
                # appropriate here.
                pass
            sonst:
                have_ws = Wahr
                wenn len(unstructured) > 0:
                    wenn unstructured[-1].token_type != 'fws':
                        unstructured.defects.append(errors.InvalidHeaderDefect(
                            "missing whitespace before encoded word"))
                        have_ws = Falsch
                wenn have_ws und len(unstructured) > 1:
                    wenn unstructured[-2].token_type == 'encoded-word':
                        unstructured[-1] = EWWhiteSpaceTerminal(
                            unstructured[-1], 'fws')
                unstructured.append(token)
                weiter
        tok, *remainder = _wsp_splitter(value, 1)
        # Split in the middle of an atom wenn there is a rfc2047 encoded word
        # which does nicht have WSP on both sides. The defect will be registered
        # the next time through the loop.
        # This needs to only be performed when the encoded word is valid;
        # otherwise, performing it on an invalid encoded word can cause
        # the parser to go in an infinite loop.
        wenn valid_ew und rfc2047_matcher.search(tok):
            tok, *remainder = value.partition('=?')
        vtext = ValueTerminal(tok, 'utext')
        _validate_xtext(vtext)
        unstructured.append(vtext)
        value = ''.join(remainder)
    gib unstructured

def get_qp_ctext(value):
    r"""ctext = <printable ascii ausser \ ( )>

    This is nicht the RFC ctext, since we are handling nested comments in comment
    und unquoting quoted-pairs here.  We allow anything ausser the '()'
    characters, but wenn we find any ASCII other than the RFC defined printable
    ASCII, a NonPrintableDefect is added to the token's defects list.  Since
    quoted pairs are converted to their unquoted values, what is returned is
    a 'ptext' token.  In this case it is a WhiteSpaceTerminal, so it's value
    is ' '.

    """
    ptext, value, _ = _get_ptext_to_endchars(value, '()')
    ptext = WhiteSpaceTerminal(ptext, 'ptext')
    _validate_xtext(ptext)
    gib ptext, value

def get_qcontent(value):
    """qcontent = qtext / quoted-pair

    We allow anything ausser the DQUOTE character, but wenn we find any ASCII
    other than the RFC defined printable ASCII, a NonPrintableDefect is
    added to the token's defects list.  Any quoted pairs are converted to their
    unquoted values, so what is returned is a 'ptext' token.  In this case it
    is a ValueTerminal.

    """
    ptext, value, _ = _get_ptext_to_endchars(value, '"')
    ptext = ValueTerminal(ptext, 'ptext')
    _validate_xtext(ptext)
    gib ptext, value

def get_atext(value):
    """atext = <matches _atext_matcher>

    We allow any non-ATOM_ENDS in atext, but add an InvalidATextDefect to
    the token's defects list wenn we find non-atext characters.
    """
    m = _non_atom_end_matcher(value)
    wenn nicht m:
        wirf errors.HeaderParseError(
            "expected atext but found '{}'".format(value))
    atext = m.group()
    value = value[len(atext):]
    atext = ValueTerminal(atext, 'atext')
    _validate_xtext(atext)
    gib atext, value

def get_bare_quoted_string(value):
    """bare-quoted-string = DQUOTE *([FWS] qcontent) [FWS] DQUOTE

    A quoted-string without the leading oder trailing white space.  Its
    value is the text between the quote marks, mit whitespace
    preserved und quoted pairs decoded.
    """
    wenn nicht value oder value[0] != '"':
        wirf errors.HeaderParseError(
            "expected '\"' but found '{}'".format(value))
    bare_quoted_string = BareQuotedString()
    value = value[1:]
    wenn value und value[0] == '"':
        token, value = get_qcontent(value)
        bare_quoted_string.append(token)
    waehrend value und value[0] != '"':
        wenn value[0] in WSP:
            token, value = get_fws(value)
        sowenn value[:2] == '=?':
            valid_ew = Falsch
            versuch:
                token, value = get_encoded_word(value)
                bare_quoted_string.defects.append(errors.InvalidHeaderDefect(
                    "encoded word inside quoted string"))
                valid_ew = Wahr
            ausser errors.HeaderParseError:
                token, value = get_qcontent(value)
            # Collapse the whitespace between two encoded words that occur in a
            # bare-quoted-string.
            wenn valid_ew und len(bare_quoted_string) > 1:
                wenn (bare_quoted_string[-1].token_type == 'fws' und
                        bare_quoted_string[-2].token_type == 'encoded-word'):
                    bare_quoted_string[-1] = EWWhiteSpaceTerminal(
                        bare_quoted_string[-1], 'fws')
        sonst:
            token, value = get_qcontent(value)
        bare_quoted_string.append(token)
    wenn nicht value:
        bare_quoted_string.defects.append(errors.InvalidHeaderDefect(
            "end of header inside quoted string"))
        gib bare_quoted_string, value
    gib bare_quoted_string, value[1:]

def get_comment(value):
    """comment = "(" *([FWS] ccontent) [FWS] ")"
       ccontent = ctext / quoted-pair / comment

    We handle nested comments here, und quoted-pair in our qp-ctext routine.
    """
    wenn value und value[0] != '(':
        wirf errors.HeaderParseError(
            "expected '(' but found '{}'".format(value))
    comment = Comment()
    value = value[1:]
    waehrend value und value[0] != ")":
        wenn value[0] in WSP:
            token, value = get_fws(value)
        sowenn value[0] == '(':
            token, value = get_comment(value)
        sonst:
            token, value = get_qp_ctext(value)
        comment.append(token)
    wenn nicht value:
        comment.defects.append(errors.InvalidHeaderDefect(
            "end of header inside comment"))
        gib comment, value
    gib comment, value[1:]

def get_cfws(value):
    """CFWS = (1*([FWS] comment) [FWS]) / FWS

    """
    cfws = CFWSList()
    waehrend value und value[0] in CFWS_LEADER:
        wenn value[0] in WSP:
            token, value = get_fws(value)
        sonst:
            token, value = get_comment(value)
        cfws.append(token)
    gib cfws, value

def get_quoted_string(value):
    """quoted-string = [CFWS] <bare-quoted-string> [CFWS]

    'bare-quoted-string' is an intermediate klasse defined by this
    parser und nicht by the RFC grammar.  It is the quoted string
    without any attached CFWS.
    """
    quoted_string = QuotedString()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        quoted_string.append(token)
    token, value = get_bare_quoted_string(value)
    quoted_string.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        quoted_string.append(token)
    gib quoted_string, value

def get_atom(value):
    """atom = [CFWS] 1*atext [CFWS]

    An atom could be an rfc2047 encoded word.
    """
    atom = Atom()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        atom.append(token)
    wenn value und value[0] in ATOM_ENDS:
        wirf errors.HeaderParseError(
            "expected atom but found '{}'".format(value))
    wenn value.startswith('=?'):
        versuch:
            token, value = get_encoded_word(value)
        ausser errors.HeaderParseError:
            # XXX: need to figure out how to register defects when
            # appropriate here.
            token, value = get_atext(value)
    sonst:
        token, value = get_atext(value)
    atom.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        atom.append(token)
    gib atom, value

def get_dot_atom_text(value):
    """ dot-text = 1*atext *("." 1*atext)

    """
    dot_atom_text = DotAtomText()
    wenn nicht value oder value[0] in ATOM_ENDS:
        wirf errors.HeaderParseError("expected atom at a start of "
            "dot-atom-text but found '{}'".format(value))
    waehrend value und value[0] nicht in ATOM_ENDS:
        token, value = get_atext(value)
        dot_atom_text.append(token)
        wenn value und value[0] == '.':
            dot_atom_text.append(DOT)
            value = value[1:]
    wenn dot_atom_text[-1] is DOT:
        wirf errors.HeaderParseError("expected atom at end of dot-atom-text "
            "but found '{}'".format('.'+value))
    gib dot_atom_text, value

def get_dot_atom(value):
    """ dot-atom = [CFWS] dot-atom-text [CFWS]

    Any place we can have a dot atom, we could instead have an rfc2047 encoded
    word.
    """
    dot_atom = DotAtom()
    wenn value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        dot_atom.append(token)
    wenn value.startswith('=?'):
        versuch:
            token, value = get_encoded_word(value)
        ausser errors.HeaderParseError:
            # XXX: need to figure out how to register defects when
            # appropriate here.
            token, value = get_dot_atom_text(value)
    sonst:
        token, value = get_dot_atom_text(value)
    dot_atom.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        dot_atom.append(token)
    gib dot_atom, value

def get_word(value):
    """word = atom / quoted-string

    Either atom oder quoted-string may start mit CFWS.  We have to peel off this
    CFWS first to determine which type of word to parse.  Afterward we splice
    the leading CFWS, wenn any, into the parsed sub-token.

    If neither an atom oder a quoted-string is found before the next special, a
    HeaderParseError is raised.

    The token returned is either an Atom oder a QuotedString, als appropriate.
    This means the 'word' level of the formal grammar is nicht represented in the
    parse tree; this is because having that extra layer when manipulating the
    parse tree is more confusing than it is helpful.

    """
    wenn value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
    sonst:
        leader = Nichts
    wenn nicht value:
        wirf errors.HeaderParseError(
            "Expected 'atom' oder 'quoted-string' but found nothing.")
    wenn value[0]=='"':
        token, value = get_quoted_string(value)
    sowenn value[0] in SPECIALS:
        wirf errors.HeaderParseError("Expected 'atom' oder 'quoted-string' "
                                      "but found '{}'".format(value))
    sonst:
        token, value = get_atom(value)
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    gib token, value

def get_phrase(value):
    """ phrase = 1*word / obs-phrase
        obs-phrase = word *(word / "." / CFWS)

    This means a phrase can be a sequence of words, periods, und CFWS in any
    order als long als it starts mit at least one word.  If anything other than
    words is detected, an ObsoleteHeaderDefect is added to the token's defect
    list.  We also accept a phrase that starts mit CFWS followed by a dot;
    this is registered als an InvalidHeaderDefect, since it is nicht supported by
    even the obsolete grammar.

    """
    phrase = Phrase()
    versuch:
        token, value = get_word(value)
        phrase.append(token)
    ausser errors.HeaderParseError:
        phrase.defects.append(errors.InvalidHeaderDefect(
            "phrase does nicht start mit word"))
    waehrend value und value[0] nicht in PHRASE_ENDS:
        wenn value[0]=='.':
            phrase.append(DOT)
            phrase.defects.append(errors.ObsoleteHeaderDefect(
                "period in 'phrase'"))
            value = value[1:]
        sonst:
            versuch:
                token, value = get_word(value)
            ausser errors.HeaderParseError:
                wenn value[0] in CFWS_LEADER:
                    token, value = get_cfws(value)
                    phrase.defects.append(errors.ObsoleteHeaderDefect(
                        "comment found without atom"))
                sonst:
                    wirf
            phrase.append(token)
    gib phrase, value

def get_local_part(value):
    """ local-part = dot-atom / quoted-string / obs-local-part

    """
    local_part = LocalPart()
    leader = Nichts
    wenn value und value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
    wenn nicht value:
        wirf errors.HeaderParseError(
            "expected local-part but found '{}'".format(value))
    versuch:
        token, value = get_dot_atom(value)
    ausser errors.HeaderParseError:
        versuch:
            token, value = get_word(value)
        ausser errors.HeaderParseError:
            wenn value[0] != '\\' und value[0] in PHRASE_ENDS:
                wirf
            token = TokenList()
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    local_part.append(token)
    wenn value und (value[0]=='\\' oder value[0] nicht in PHRASE_ENDS):
        obs_local_part, value = get_obs_local_part(str(local_part) + value)
        wenn obs_local_part.token_type == 'invalid-obs-local-part':
            local_part.defects.append(errors.InvalidHeaderDefect(
                "local-part is nicht dot-atom, quoted-string, oder obs-local-part"))
        sonst:
            local_part.defects.append(errors.ObsoleteHeaderDefect(
                "local-part is nicht a dot-atom (contains CFWS)"))
        local_part[0] = obs_local_part
    versuch:
        local_part.value.encode('ascii')
    ausser UnicodeEncodeError:
        local_part.defects.append(errors.NonASCIILocalPartDefect(
                "local-part contains non-ASCII characters)"))
    gib local_part, value

def get_obs_local_part(value):
    """ obs-local-part = word *("." word)
    """
    obs_local_part = ObsLocalPart()
    last_non_ws_was_dot = Falsch
    waehrend value und (value[0]=='\\' oder value[0] nicht in PHRASE_ENDS):
        wenn value[0] == '.':
            wenn last_non_ws_was_dot:
                obs_local_part.defects.append(errors.InvalidHeaderDefect(
                    "invalid repeated '.'"))
            obs_local_part.append(DOT)
            last_non_ws_was_dot = Wahr
            value = value[1:]
            weiter
        sowenn value[0]=='\\':
            obs_local_part.append(ValueTerminal(value[0],
                                                'misplaced-special'))
            value = value[1:]
            obs_local_part.defects.append(errors.InvalidHeaderDefect(
                "'\\' character outside of quoted-string/ccontent"))
            last_non_ws_was_dot = Falsch
            weiter
        wenn obs_local_part und obs_local_part[-1].token_type != 'dot':
            obs_local_part.defects.append(errors.InvalidHeaderDefect(
                "missing '.' between words"))
        versuch:
            token, value = get_word(value)
            last_non_ws_was_dot = Falsch
        ausser errors.HeaderParseError:
            wenn value[0] nicht in CFWS_LEADER:
                wirf
            token, value = get_cfws(value)
        obs_local_part.append(token)
    wenn nicht obs_local_part:
        wirf errors.HeaderParseError(
            "expected obs-local-part but found '{}'".format(value))
    wenn (obs_local_part[0].token_type == 'dot' oder
            obs_local_part[0].token_type=='cfws' und
            len(obs_local_part) > 1 und
            obs_local_part[1].token_type=='dot'):
        obs_local_part.defects.append(errors.InvalidHeaderDefect(
            "Invalid leading '.' in local part"))
    wenn (obs_local_part[-1].token_type == 'dot' oder
            obs_local_part[-1].token_type=='cfws' und
            len(obs_local_part) > 1 und
            obs_local_part[-2].token_type=='dot'):
        obs_local_part.defects.append(errors.InvalidHeaderDefect(
            "Invalid trailing '.' in local part"))
    wenn obs_local_part.defects:
        obs_local_part.token_type = 'invalid-obs-local-part'
    gib obs_local_part, value

def get_dtext(value):
    r""" dtext = <printable ascii ausser \ [ ]> / obs-dtext
        obs-dtext = obs-NO-WS-CTL / quoted-pair

    We allow anything ausser the excluded characters, but wenn we find any
    ASCII other than the RFC defined printable ASCII, a NonPrintableDefect is
    added to the token's defects list.  Quoted pairs are converted to their
    unquoted values, so what is returned is a ptext token, in this case a
    ValueTerminal.  If there were quoted-printables, an ObsoleteHeaderDefect is
    added to the returned token's defect list.

    """
    ptext, value, had_qp = _get_ptext_to_endchars(value, '[]')
    ptext = ValueTerminal(ptext, 'ptext')
    wenn had_qp:
        ptext.defects.append(errors.ObsoleteHeaderDefect(
            "quoted printable found in domain-literal"))
    _validate_xtext(ptext)
    gib ptext, value

def _check_for_early_dl_end(value, domain_literal):
    wenn value:
        gib Falsch
    domain_literal.defects.append(errors.InvalidHeaderDefect(
        "end of input inside domain-literal"))
    domain_literal.append(ValueTerminal(']', 'domain-literal-end'))
    gib Wahr

def get_domain_literal(value):
    """ domain-literal = [CFWS] "[" *([FWS] dtext) [FWS] "]" [CFWS]

    """
    domain_literal = DomainLiteral()
    wenn value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        domain_literal.append(token)
    wenn nicht value:
        wirf errors.HeaderParseError("expected domain-literal")
    wenn value[0] != '[':
        wirf errors.HeaderParseError("expected '[' at start of domain-literal "
                "but found '{}'".format(value))
    value = value[1:]
    domain_literal.append(ValueTerminal('[', 'domain-literal-start'))
    wenn _check_for_early_dl_end(value, domain_literal):
        gib domain_literal, value
    wenn value[0] in WSP:
        token, value = get_fws(value)
        domain_literal.append(token)
    token, value = get_dtext(value)
    domain_literal.append(token)
    wenn _check_for_early_dl_end(value, domain_literal):
        gib domain_literal, value
    wenn value[0] in WSP:
        token, value = get_fws(value)
        domain_literal.append(token)
    wenn _check_for_early_dl_end(value, domain_literal):
        gib domain_literal, value
    wenn value[0] != ']':
        wirf errors.HeaderParseError("expected ']' at end of domain-literal "
                "but found '{}'".format(value))
    domain_literal.append(ValueTerminal(']', 'domain-literal-end'))
    value = value[1:]
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        domain_literal.append(token)
    gib domain_literal, value

def get_domain(value):
    """ domain = dot-atom / domain-literal / obs-domain
        obs-domain = atom *("." atom))

    """
    domain = Domain()
    leader = Nichts
    wenn value und value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
    wenn nicht value:
        wirf errors.HeaderParseError(
            "expected domain but found '{}'".format(value))
    wenn value[0] == '[':
        token, value = get_domain_literal(value)
        wenn leader is nicht Nichts:
            token[:0] = [leader]
        domain.append(token)
        gib domain, value
    versuch:
        token, value = get_dot_atom(value)
    ausser errors.HeaderParseError:
        token, value = get_atom(value)
    wenn value und value[0] == '@':
        wirf errors.HeaderParseError('Invalid Domain')
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    domain.append(token)
    wenn value und value[0] == '.':
        domain.defects.append(errors.ObsoleteHeaderDefect(
            "domain is nicht a dot-atom (contains CFWS)"))
        wenn domain[0].token_type == 'dot-atom':
            domain[:] = domain[0]
        waehrend value und value[0] == '.':
            domain.append(DOT)
            token, value = get_atom(value[1:])
            domain.append(token)
    gib domain, value

def get_addr_spec(value):
    """ addr-spec = local-part "@" domain

    """
    addr_spec = AddrSpec()
    token, value = get_local_part(value)
    addr_spec.append(token)
    wenn nicht value oder value[0] != '@':
        addr_spec.defects.append(errors.InvalidHeaderDefect(
            "addr-spec local part mit no domain"))
        gib addr_spec, value
    addr_spec.append(ValueTerminal('@', 'address-at-symbol'))
    token, value = get_domain(value[1:])
    addr_spec.append(token)
    gib addr_spec, value

def get_obs_route(value):
    """ obs-route = obs-domain-list ":"
        obs-domain-list = *(CFWS / ",") "@" domain *("," [CFWS] ["@" domain])

        Returns an obs-route token mit the appropriate sub-tokens (that is,
        there is no obs-domain-list in the parse tree).
    """
    obs_route = ObsRoute()
    waehrend value und (value[0]==',' oder value[0] in CFWS_LEADER):
        wenn value[0] in CFWS_LEADER:
            token, value = get_cfws(value)
            obs_route.append(token)
        sowenn value[0] == ',':
            obs_route.append(ListSeparator)
            value = value[1:]
    wenn nicht value oder value[0] != '@':
        wirf errors.HeaderParseError(
            "expected obs-route domain but found '{}'".format(value))
    obs_route.append(RouteComponentMarker)
    token, value = get_domain(value[1:])
    obs_route.append(token)
    waehrend value und value[0]==',':
        obs_route.append(ListSeparator)
        value = value[1:]
        wenn nicht value:
            breche
        wenn value[0] in CFWS_LEADER:
            token, value = get_cfws(value)
            obs_route.append(token)
        wenn nicht value:
            breche
        wenn value[0] == '@':
            obs_route.append(RouteComponentMarker)
            token, value = get_domain(value[1:])
            obs_route.append(token)
    wenn nicht value:
        wirf errors.HeaderParseError("end of header waehrend parsing obs-route")
    wenn value[0] != ':':
        wirf errors.HeaderParseError( "expected ':' marking end of "
            "obs-route but found '{}'".format(value))
    obs_route.append(ValueTerminal(':', 'end-of-obs-route-marker'))
    gib obs_route, value[1:]

def get_angle_addr(value):
    """ angle-addr = [CFWS] "<" addr-spec ">" [CFWS] / obs-angle-addr
        obs-angle-addr = [CFWS] "<" obs-route addr-spec ">" [CFWS]

    """
    angle_addr = AngleAddr()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        angle_addr.append(token)
    wenn nicht value oder value[0] != '<':
        wirf errors.HeaderParseError(
            "expected angle-addr but found '{}'".format(value))
    angle_addr.append(ValueTerminal('<', 'angle-addr-start'))
    value = value[1:]
    # Although it is nicht legal per RFC5322, SMTP uses '<>' in certain
    # circumstances.
    wenn value und value[0] == '>':
        angle_addr.append(ValueTerminal('>', 'angle-addr-end'))
        angle_addr.defects.append(errors.InvalidHeaderDefect(
            "null addr-spec in angle-addr"))
        value = value[1:]
        gib angle_addr, value
    versuch:
        token, value = get_addr_spec(value)
    ausser errors.HeaderParseError:
        versuch:
            token, value = get_obs_route(value)
            angle_addr.defects.append(errors.ObsoleteHeaderDefect(
                "obsolete route specification in angle-addr"))
        ausser errors.HeaderParseError:
            wirf errors.HeaderParseError(
                "expected addr-spec oder obs-route but found '{}'".format(value))
        angle_addr.append(token)
        token, value = get_addr_spec(value)
    angle_addr.append(token)
    wenn value und value[0] == '>':
        value = value[1:]
    sonst:
        angle_addr.defects.append(errors.InvalidHeaderDefect(
            "missing trailing '>' on angle-addr"))
    angle_addr.append(ValueTerminal('>', 'angle-addr-end'))
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        angle_addr.append(token)
    gib angle_addr, value

def get_display_name(value):
    """ display-name = phrase

    Because this is simply a name-rule, we don't gib a display-name
    token containing a phrase, but rather a display-name token with
    the content of the phrase.

    """
    display_name = DisplayName()
    token, value = get_phrase(value)
    display_name.extend(token[:])
    display_name.defects = token.defects[:]
    gib display_name, value


def get_name_addr(value):
    """ name-addr = [display-name] angle-addr

    """
    name_addr = NameAddr()
    # Both the optional display name und the angle-addr can start mit cfws.
    leader = Nichts
    wenn nicht value:
        wirf errors.HeaderParseError(
            "expected name-addr but found '{}'".format(value))
    wenn value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
        wenn nicht value:
            wirf errors.HeaderParseError(
                "expected name-addr but found '{}'".format(leader))
    wenn value[0] != '<':
        wenn value[0] in PHRASE_ENDS:
            wirf errors.HeaderParseError(
                "expected name-addr but found '{}'".format(value))
        token, value = get_display_name(value)
        wenn nicht value:
            wirf errors.HeaderParseError(
                "expected name-addr but found '{}'".format(token))
        wenn leader is nicht Nichts:
            wenn isinstance(token[0], TokenList):
                token[0][:0] = [leader]
            sonst:
                token[:0] = [leader]
            leader = Nichts
        name_addr.append(token)
    token, value = get_angle_addr(value)
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    name_addr.append(token)
    gib name_addr, value

def get_mailbox(value):
    """ mailbox = name-addr / addr-spec

    """
    # The only way to figure out wenn we are dealing mit a name-addr oder an
    # addr-spec is to try parsing each one.
    mailbox = Mailbox()
    versuch:
        token, value = get_name_addr(value)
    ausser errors.HeaderParseError:
        versuch:
            token, value = get_addr_spec(value)
        ausser errors.HeaderParseError:
            wirf errors.HeaderParseError(
                "expected mailbox but found '{}'".format(value))
    wenn any(isinstance(x, errors.InvalidHeaderDefect)
                       fuer x in token.all_defects):
        mailbox.token_type = 'invalid-mailbox'
    mailbox.append(token)
    gib mailbox, value

def get_invalid_mailbox(value, endchars):
    """ Read everything up to one of the chars in endchars.

    This is outside the formal grammar.  The InvalidMailbox TokenList that is
    returned acts like a Mailbox, but the data attributes are Nichts.

    """
    invalid_mailbox = InvalidMailbox()
    waehrend value und value[0] nicht in endchars:
        wenn value[0] in PHRASE_ENDS:
            invalid_mailbox.append(ValueTerminal(value[0],
                                                 'misplaced-special'))
            value = value[1:]
        sonst:
            token, value = get_phrase(value)
            invalid_mailbox.append(token)
    gib invalid_mailbox, value

def get_mailbox_list(value):
    """ mailbox-list = (mailbox *("," mailbox)) / obs-mbox-list
        obs-mbox-list = *([CFWS] ",") mailbox *("," [mailbox / CFWS])

    For this routine we go outside the formal grammar in order to improve error
    handling.  We recognize the end of the mailbox list only at the end of the
    value oder at a ';' (the group terminator).  This is so that we can turn
    invalid mailboxes into InvalidMailbox tokens und weiter parsing any
    remaining valid mailboxes.  We also allow all mailbox entries to be null,
    und this condition is handled appropriately at a higher level.

    """
    mailbox_list = MailboxList()
    waehrend value und value[0] != ';':
        versuch:
            token, value = get_mailbox(value)
            mailbox_list.append(token)
        ausser errors.HeaderParseError:
            leader = Nichts
            wenn value[0] in CFWS_LEADER:
                leader, value = get_cfws(value)
                wenn nicht value oder value[0] in ',;':
                    mailbox_list.append(leader)
                    mailbox_list.defects.append(errors.ObsoleteHeaderDefect(
                        "empty element in mailbox-list"))
                sonst:
                    token, value = get_invalid_mailbox(value, ',;')
                    wenn leader is nicht Nichts:
                        token[:0] = [leader]
                    mailbox_list.append(token)
                    mailbox_list.defects.append(errors.InvalidHeaderDefect(
                        "invalid mailbox in mailbox-list"))
            sowenn value[0] == ',':
                mailbox_list.defects.append(errors.ObsoleteHeaderDefect(
                    "empty element in mailbox-list"))
            sonst:
                token, value = get_invalid_mailbox(value, ',;')
                wenn leader is nicht Nichts:
                    token[:0] = [leader]
                mailbox_list.append(token)
                mailbox_list.defects.append(errors.InvalidHeaderDefect(
                    "invalid mailbox in mailbox-list"))
        wenn value und value[0] nicht in ',;':
            # Crap after mailbox; treat it als an invalid mailbox.
            # The mailbox info will still be available.
            mailbox = mailbox_list[-1]
            mailbox.token_type = 'invalid-mailbox'
            token, value = get_invalid_mailbox(value, ',;')
            mailbox.extend(token)
            mailbox_list.defects.append(errors.InvalidHeaderDefect(
                "invalid mailbox in mailbox-list"))
        wenn value und value[0] == ',':
            mailbox_list.append(ListSeparator)
            value = value[1:]
    gib mailbox_list, value


def get_group_list(value):
    """ group-list = mailbox-list / CFWS / obs-group-list
        obs-group-list = 1*([CFWS] ",") [CFWS]

    """
    group_list = GroupList()
    wenn nicht value:
        group_list.defects.append(errors.InvalidHeaderDefect(
            "end of header before group-list"))
        gib group_list, value
    leader = Nichts
    wenn value und value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
        wenn nicht value:
            # This should never happen in email parsing, since CFWS-only is a
            # legal alternative to group-list in a group, which is the only
            # place group-list appears.
            group_list.defects.append(errors.InvalidHeaderDefect(
                "end of header in group-list"))
            group_list.append(leader)
            gib group_list, value
        wenn value[0] == ';':
            group_list.append(leader)
            gib group_list, value
    token, value = get_mailbox_list(value)
    wenn len(token.all_mailboxes)==0:
        wenn leader is nicht Nichts:
            group_list.append(leader)
        group_list.extend(token)
        group_list.defects.append(errors.ObsoleteHeaderDefect(
            "group-list mit empty entries"))
        gib group_list, value
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    group_list.append(token)
    gib group_list, value

def get_group(value):
    """ group = display-name ":" [group-list] ";" [CFWS]

    """
    group = Group()
    token, value = get_display_name(value)
    wenn nicht value oder value[0] != ':':
        wirf errors.HeaderParseError("expected ':' at end of group "
            "display name but found '{}'".format(value))
    group.append(token)
    group.append(ValueTerminal(':', 'group-display-name-terminator'))
    value = value[1:]
    wenn value und value[0] == ';':
        group.append(ValueTerminal(';', 'group-terminator'))
        gib group, value[1:]
    token, value = get_group_list(value)
    group.append(token)
    wenn nicht value:
        group.defects.append(errors.InvalidHeaderDefect(
            "end of header in group"))
    sowenn value[0] != ';':
        wirf errors.HeaderParseError(
            "expected ';' at end of group but found {}".format(value))
    group.append(ValueTerminal(';', 'group-terminator'))
    value = value[1:]
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        group.append(token)
    gib group, value

def get_address(value):
    """ address = mailbox / group

    Note that counter-intuitively, an address can be either a single address oder
    a list of addresses (a group).  This is why the returned Address object has
    a 'mailboxes' attribute which treats a single address als a list of length
    one.  When you need to differentiate between to two cases, extract the single
    element, which is either a mailbox oder a group token.

    """
    # The formal grammar isn't very helpful when parsing an address.  mailbox
    # und group, especially when allowing fuer obsolete forms, start off very
    # similarly.  It is only when you reach one of @, <, oder : that you know
    # what you've got.  So, we try each one in turn, starting mit the more
    # likely of the two.  We could perhaps make this more efficient by looking
    # fuer a phrase und then branching based on the next character, but that
    # would be a premature optimization.
    address = Address()
    versuch:
        token, value = get_group(value)
    ausser errors.HeaderParseError:
        versuch:
            token, value = get_mailbox(value)
        ausser errors.HeaderParseError:
            wirf errors.HeaderParseError(
                "expected address but found '{}'".format(value))
    address.append(token)
    gib address, value

def get_address_list(value):
    """ address_list = (address *("," address)) / obs-addr-list
        obs-addr-list = *([CFWS] ",") address *("," [address / CFWS])

    We depart von the formal grammar here by continuing to parse until the end
    of the input, assuming the input to be entirely composed of an
    address-list.  This is always true in email parsing, und allows us
    to skip invalid addresses to parse additional valid ones.

    """
    address_list = AddressList()
    waehrend value:
        versuch:
            token, value = get_address(value)
            address_list.append(token)
        ausser errors.HeaderParseError:
            leader = Nichts
            wenn value[0] in CFWS_LEADER:
                leader, value = get_cfws(value)
                wenn nicht value oder value[0] == ',':
                    address_list.append(leader)
                    address_list.defects.append(errors.ObsoleteHeaderDefect(
                        "address-list entry mit no content"))
                sonst:
                    token, value = get_invalid_mailbox(value, ',')
                    wenn leader is nicht Nichts:
                        token[:0] = [leader]
                    address_list.append(Address([token]))
                    address_list.defects.append(errors.InvalidHeaderDefect(
                        "invalid address in address-list"))
            sowenn value[0] == ',':
                address_list.defects.append(errors.ObsoleteHeaderDefect(
                    "empty element in address-list"))
            sonst:
                token, value = get_invalid_mailbox(value, ',')
                wenn leader is nicht Nichts:
                    token[:0] = [leader]
                address_list.append(Address([token]))
                address_list.defects.append(errors.InvalidHeaderDefect(
                    "invalid address in address-list"))
        wenn value und value[0] != ',':
            # Crap after address; treat it als an invalid mailbox.
            # The mailbox info will still be available.
            mailbox = address_list[-1][0]
            mailbox.token_type = 'invalid-mailbox'
            token, value = get_invalid_mailbox(value, ',')
            mailbox.extend(token)
            address_list.defects.append(errors.InvalidHeaderDefect(
                "invalid address in address-list"))
        wenn value:  # Must be a , at this point.
            address_list.append(ListSeparator)
            value = value[1:]
    gib address_list, value


def get_no_fold_literal(value):
    """ no-fold-literal = "[" *dtext "]"
    """
    no_fold_literal = NoFoldLiteral()
    wenn nicht value:
        wirf errors.HeaderParseError(
            "expected no-fold-literal but found '{}'".format(value))
    wenn value[0] != '[':
        wirf errors.HeaderParseError(
            "expected '[' at the start of no-fold-literal "
            "but found '{}'".format(value))
    no_fold_literal.append(ValueTerminal('[', 'no-fold-literal-start'))
    value = value[1:]
    token, value = get_dtext(value)
    no_fold_literal.append(token)
    wenn nicht value oder value[0] != ']':
        wirf errors.HeaderParseError(
            "expected ']' at the end of no-fold-literal "
            "but found '{}'".format(value))
    no_fold_literal.append(ValueTerminal(']', 'no-fold-literal-end'))
    gib no_fold_literal, value[1:]

def get_msg_id(value):
    """msg-id = [CFWS] "<" id-left '@' id-right  ">" [CFWS]
       id-left = dot-atom-text / obs-id-left
       id-right = dot-atom-text / no-fold-literal / obs-id-right
       no-fold-literal = "[" *dtext "]"
    """
    msg_id = MsgID()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        msg_id.append(token)
    wenn nicht value oder value[0] != '<':
        wirf errors.HeaderParseError(
            "expected msg-id but found '{}'".format(value))
    msg_id.append(ValueTerminal('<', 'msg-id-start'))
    value = value[1:]
    # Parse id-left.
    versuch:
        token, value = get_dot_atom_text(value)
    ausser errors.HeaderParseError:
        versuch:
            # obs-id-left is same als local-part of add-spec.
            token, value = get_obs_local_part(value)
            msg_id.defects.append(errors.ObsoleteHeaderDefect(
                "obsolete id-left in msg-id"))
        ausser errors.HeaderParseError:
            wirf errors.HeaderParseError(
                "expected dot-atom-text oder obs-id-left"
                " but found '{}'".format(value))
    msg_id.append(token)
    wenn nicht value oder value[0] != '@':
        msg_id.defects.append(errors.InvalidHeaderDefect(
            "msg-id mit no id-right"))
        # Even though there is no id-right, wenn the local part
        # ends mit `>` let's just parse it too und gib
        # along mit the defect.
        wenn value und value[0] == '>':
            msg_id.append(ValueTerminal('>', 'msg-id-end'))
            value = value[1:]
        gib msg_id, value
    msg_id.append(ValueTerminal('@', 'address-at-symbol'))
    value = value[1:]
    # Parse id-right.
    versuch:
        token, value = get_dot_atom_text(value)
    ausser errors.HeaderParseError:
        versuch:
            token, value = get_no_fold_literal(value)
        ausser errors.HeaderParseError:
            versuch:
                token, value = get_domain(value)
                msg_id.defects.append(errors.ObsoleteHeaderDefect(
                    "obsolete id-right in msg-id"))
            ausser errors.HeaderParseError:
                wirf errors.HeaderParseError(
                    "expected dot-atom-text, no-fold-literal oder obs-id-right"
                    " but found '{}'".format(value))
    msg_id.append(token)
    wenn value und value[0] == '>':
        value = value[1:]
    sonst:
        msg_id.defects.append(errors.InvalidHeaderDefect(
            "missing trailing '>' on msg-id"))
    msg_id.append(ValueTerminal('>', 'msg-id-end'))
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        msg_id.append(token)
    gib msg_id, value


def parse_message_id(value):
    """message-id      =   "Message-ID:" msg-id CRLF
    """
    message_id = MessageID()
    versuch:
        token, value = get_msg_id(value)
        message_id.append(token)
    ausser errors.HeaderParseError als ex:
        token = get_unstructured(value)
        message_id = InvalidMessageID(token)
        message_id.defects.append(
            errors.InvalidHeaderDefect("Invalid msg-id: {!r}".format(ex)))
    sonst:
        # Value after parsing a valid msg_id should be Nichts.
        wenn value:
            message_id.defects.append(errors.InvalidHeaderDefect(
                "Unexpected {!r}".format(value)))

    gib message_id

#
# XXX: As I begin to add additional header parsers, I'm realizing we probably
# have two level of parser routines: the get_XXX methods that get a token in
# the grammar, und parse_XXX methods that parse an entire field value.  So
# get_address_list above should really be a parse_ method, als probably should
# be get_unstructured.
#

def parse_mime_version(value):
    """ mime-version = [CFWS] 1*digit [CFWS] "." [CFWS] 1*digit [CFWS]

    """
    # The [CFWS] is implicit in the RFC 2045 BNF.
    # XXX: This routine is a bit verbose, should factor out a get_int method.
    mime_version = MIMEVersion()
    wenn nicht value:
        mime_version.defects.append(errors.HeaderMissingRequiredValue(
            "Missing MIME version number (eg: 1.0)"))
        gib mime_version
    wenn value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mime_version.append(token)
        wenn nicht value:
            mime_version.defects.append(errors.HeaderMissingRequiredValue(
                "Expected MIME version number but found only CFWS"))
    digits = ''
    waehrend value und value[0] != '.' und value[0] nicht in CFWS_LEADER:
        digits += value[0]
        value = value[1:]
    wenn nicht digits.isdigit():
        mime_version.defects.append(errors.InvalidHeaderDefect(
            "Expected MIME major version number but found {!r}".format(digits)))
        mime_version.append(ValueTerminal(digits, 'xtext'))
    sonst:
        mime_version.major = int(digits)
        mime_version.append(ValueTerminal(digits, 'digits'))
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mime_version.append(token)
    wenn nicht value oder value[0] != '.':
        wenn mime_version.major is nicht Nichts:
            mime_version.defects.append(errors.InvalidHeaderDefect(
                "Incomplete MIME version; found only major number"))
        wenn value:
            mime_version.append(ValueTerminal(value, 'xtext'))
        gib mime_version
    mime_version.append(ValueTerminal('.', 'version-separator'))
    value = value[1:]
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mime_version.append(token)
    wenn nicht value:
        wenn mime_version.major is nicht Nichts:
            mime_version.defects.append(errors.InvalidHeaderDefect(
                "Incomplete MIME version; found only major number"))
        gib mime_version
    digits = ''
    waehrend value und value[0] nicht in CFWS_LEADER:
        digits += value[0]
        value = value[1:]
    wenn nicht digits.isdigit():
        mime_version.defects.append(errors.InvalidHeaderDefect(
            "Expected MIME minor version number but found {!r}".format(digits)))
        mime_version.append(ValueTerminal(digits, 'xtext'))
    sonst:
        mime_version.minor = int(digits)
        mime_version.append(ValueTerminal(digits, 'digits'))
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mime_version.append(token)
    wenn value:
        mime_version.defects.append(errors.InvalidHeaderDefect(
            "Excess non-CFWS text after MIME version"))
        mime_version.append(ValueTerminal(value, 'xtext'))
    gib mime_version

def get_invalid_parameter(value):
    """ Read everything up to the next ';'.

    This is outside the formal grammar.  The InvalidParameter TokenList that is
    returned acts like a Parameter, but the data attributes are Nichts.

    """
    invalid_parameter = InvalidParameter()
    waehrend value und value[0] != ';':
        wenn value[0] in PHRASE_ENDS:
            invalid_parameter.append(ValueTerminal(value[0],
                                                   'misplaced-special'))
            value = value[1:]
        sonst:
            token, value = get_phrase(value)
            invalid_parameter.append(token)
    gib invalid_parameter, value

def get_ttext(value):
    """ttext = <matches _ttext_matcher>

    We allow any non-TOKEN_ENDS in ttext, but add defects to the token's
    defects list wenn we find non-ttext characters.  We also register defects for
    *any* non-printables even though the RFC doesn't exclude all of them,
    because we follow the spirit of RFC 5322.

    """
    m = _non_token_end_matcher(value)
    wenn nicht m:
        wirf errors.HeaderParseError(
            "expected ttext but found '{}'".format(value))
    ttext = m.group()
    value = value[len(ttext):]
    ttext = ValueTerminal(ttext, 'ttext')
    _validate_xtext(ttext)
    gib ttext, value

def get_token(value):
    """token = [CFWS] 1*ttext [CFWS]

    The RFC equivalent of ttext is any US-ASCII chars ausser space, ctls, oder
    tspecials.  We also exclude tabs even though the RFC doesn't.

    The RFC implies the CFWS but is nicht explicit about it in the BNF.

    """
    mtoken = Token()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mtoken.append(token)
    wenn value und value[0] in TOKEN_ENDS:
        wirf errors.HeaderParseError(
            "expected token but found '{}'".format(value))
    token, value = get_ttext(value)
    mtoken.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        mtoken.append(token)
    gib mtoken, value

def get_attrtext(value):
    """attrtext = 1*(any non-ATTRIBUTE_ENDS character)

    We allow any non-ATTRIBUTE_ENDS in attrtext, but add defects to the
    token's defects list wenn we find non-attrtext characters.  We also register
    defects fuer *any* non-printables even though the RFC doesn't exclude all of
    them, because we follow the spirit of RFC 5322.

    """
    m = _non_attribute_end_matcher(value)
    wenn nicht m:
        wirf errors.HeaderParseError(
            "expected attrtext but found {!r}".format(value))
    attrtext = m.group()
    value = value[len(attrtext):]
    attrtext = ValueTerminal(attrtext, 'attrtext')
    _validate_xtext(attrtext)
    gib attrtext, value

def get_attribute(value):
    """ [CFWS] 1*attrtext [CFWS]

    This version of the BNF makes the CFWS explicit, und als usual we use a
    value terminal fuer the actual run of characters.  The RFC equivalent of
    attrtext is the token characters, mit the subtraction of '*', "'", und '%'.
    We include tab in the excluded set just als we do fuer token.

    """
    attribute = Attribute()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        attribute.append(token)
    wenn value und value[0] in ATTRIBUTE_ENDS:
        wirf errors.HeaderParseError(
            "expected token but found '{}'".format(value))
    token, value = get_attrtext(value)
    attribute.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        attribute.append(token)
    gib attribute, value

def get_extended_attrtext(value):
    """attrtext = 1*(any non-ATTRIBUTE_ENDS character plus '%')

    This is a special parsing routine so that we get a value that
    includes % escapes als a single string (which we decode als a single
    string later).

    """
    m = _non_extended_attribute_end_matcher(value)
    wenn nicht m:
        wirf errors.HeaderParseError(
            "expected extended attrtext but found {!r}".format(value))
    attrtext = m.group()
    value = value[len(attrtext):]
    attrtext = ValueTerminal(attrtext, 'extended-attrtext')
    _validate_xtext(attrtext)
    gib attrtext, value

def get_extended_attribute(value):
    """ [CFWS] 1*extended_attrtext [CFWS]

    This is like the non-extended version ausser we allow % characters, so that
    we can pick up an encoded value als a single string.

    """
    # XXX: should we have an ExtendedAttribute TokenList?
    attribute = Attribute()
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        attribute.append(token)
    wenn value und value[0] in EXTENDED_ATTRIBUTE_ENDS:
        wirf errors.HeaderParseError(
            "expected token but found '{}'".format(value))
    token, value = get_extended_attrtext(value)
    attribute.append(token)
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        attribute.append(token)
    gib attribute, value

def get_section(value):
    """ '*' digits

    The formal BNF is more complicated because leading 0s are nicht allowed.  We
    check fuer that und add a defect.  We also assume no CFWS is allowed between
    the '*' und the digits, though the RFC is nicht crystal clear on that.
    The caller should already have dealt mit leading CFWS.

    """
    section = Section()
    wenn nicht value oder value[0] != '*':
        wirf errors.HeaderParseError("Expected section but found {}".format(
                                        value))
    section.append(ValueTerminal('*', 'section-marker'))
    value = value[1:]
    wenn nicht value oder nicht value[0].isdigit():
        wirf errors.HeaderParseError("Expected section number but "
                                      "found {}".format(value))
    digits = ''
    waehrend value und value[0].isdigit():
        digits += value[0]
        value = value[1:]
    wenn digits[0] == '0' und digits != '0':
        section.defects.append(errors.InvalidHeaderDefect(
                "section number has an invalid leading 0"))
    section.number = int(digits)
    section.append(ValueTerminal(digits, 'digits'))
    gib section, value


def get_value(value):
    """ quoted-string / attribute

    """
    v = Value()
    wenn nicht value:
        wirf errors.HeaderParseError("Expected value but found end of string")
    leader = Nichts
    wenn value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
    wenn nicht value:
        wirf errors.HeaderParseError("Expected value but found "
                                      "only {}".format(leader))
    wenn value[0] == '"':
        token, value = get_quoted_string(value)
    sonst:
        token, value = get_extended_attribute(value)
    wenn leader is nicht Nichts:
        token[:0] = [leader]
    v.append(token)
    gib v, value

def get_parameter(value):
    """ attribute [section] ["*"] [CFWS] "=" value

    The CFWS is implied by the RFC but nicht made explicit in the BNF.  This
    simplified form of the BNF von the RFC is made to conform mit the RFC BNF
    through some extra checks.  We do it this way because it makes both error
    recovery und working mit the resulting parse tree easier.
    """
    # It is possible CFWS would also be implicitly allowed between the section
    # und the 'extended-attribute' marker (the '*') , but we've never seen that
    # in the wild und we will therefore ignore the possibility.
    param = Parameter()
    token, value = get_attribute(value)
    param.append(token)
    wenn nicht value oder value[0] == ';':
        param.defects.append(errors.InvalidHeaderDefect("Parameter contains "
            "name ({}) but no value".format(token)))
        gib param, value
    wenn value[0] == '*':
        versuch:
            token, value = get_section(value)
            param.sectioned = Wahr
            param.append(token)
        ausser errors.HeaderParseError:
            pass
        wenn nicht value:
            wirf errors.HeaderParseError("Incomplete parameter")
        wenn value[0] == '*':
            param.append(ValueTerminal('*', 'extended-parameter-marker'))
            value = value[1:]
            param.extended = Wahr
    wenn value[0] != '=':
        wirf errors.HeaderParseError("Parameter nicht followed by '='")
    param.append(ValueTerminal('=', 'parameter-separator'))
    value = value[1:]
    wenn value und value[0] in CFWS_LEADER:
        token, value = get_cfws(value)
        param.append(token)
    remainder = Nichts
    appendto = param
    wenn param.extended und value und value[0] == '"':
        # Now fuer some serious hackery to handle the common invalid case of
        # double quotes around an extended value.  We also accept (with defect)
        # a value marked als encoded that isn't really.
        qstring, remainder = get_quoted_string(value)
        inner_value = qstring.stripped_value
        semi_valid = Falsch
        wenn param.section_number == 0:
            wenn inner_value und inner_value[0] == "'":
                semi_valid = Wahr
            sonst:
                token, rest = get_attrtext(inner_value)
                wenn rest und rest[0] == "'":
                    semi_valid = Wahr
        sonst:
            versuch:
                token, rest = get_extended_attrtext(inner_value)
            ausser:
                pass
            sonst:
                wenn nicht rest:
                    semi_valid = Wahr
        wenn semi_valid:
            param.defects.append(errors.InvalidHeaderDefect(
                "Quoted string value fuer extended parameter is invalid"))
            param.append(qstring)
            fuer t in qstring:
                wenn t.token_type == 'bare-quoted-string':
                    t[:] = []
                    appendto = t
                    breche
            value = inner_value
        sonst:
            remainder = Nichts
            param.defects.append(errors.InvalidHeaderDefect(
                "Parameter marked als extended but appears to have a "
                "quoted string value that is non-encoded"))
    wenn value und value[0] == "'":
        token = Nichts
    sonst:
        token, value = get_value(value)
    wenn nicht param.extended oder param.section_number > 0:
        wenn nicht value oder value[0] != "'":
            appendto.append(token)
            wenn remainder is nicht Nichts:
                assert nicht value, value
                value = remainder
            gib param, value
        param.defects.append(errors.InvalidHeaderDefect(
            "Apparent initial-extended-value but attribute "
            "was nicht marked als extended oder was nicht initial section"))
    wenn nicht value:
        # Assume the charset/lang is missing und the token is the value.
        param.defects.append(errors.InvalidHeaderDefect(
            "Missing required charset/lang delimiters"))
        appendto.append(token)
        wenn remainder is Nichts:
            gib param, value
    sonst:
        wenn token is nicht Nichts:
            fuer t in token:
                wenn t.token_type == 'extended-attrtext':
                    breche
            t.token_type == 'attrtext'
            appendto.append(t)
            param.charset = t.value
        wenn value[0] != "'":
            wirf errors.HeaderParseError("Expected RFC2231 char/lang encoding "
                                          "delimiter, but found {!r}".format(value))
        appendto.append(ValueTerminal("'", 'RFC2231-delimiter'))
        value = value[1:]
        wenn value und value[0] != "'":
            token, value = get_attrtext(value)
            appendto.append(token)
            param.lang = token.value
            wenn nicht value oder value[0] != "'":
                wirf errors.HeaderParseError("Expected RFC2231 char/lang encoding "
                                  "delimiter, but found {}".format(value))
        appendto.append(ValueTerminal("'", 'RFC2231-delimiter'))
        value = value[1:]
    wenn remainder is nicht Nichts:
        # Treat the rest of value als bare quoted string content.
        v = Value()
        waehrend value:
            wenn value[0] in WSP:
                token, value = get_fws(value)
            sowenn value[0] == '"':
                token = ValueTerminal('"', 'DQUOTE')
                value = value[1:]
            sonst:
                token, value = get_qcontent(value)
            v.append(token)
        token = v
    sonst:
        token, value = get_value(value)
    appendto.append(token)
    wenn remainder is nicht Nichts:
        assert nicht value, value
        value = remainder
    gib param, value

def parse_mime_parameters(value):
    """ parameter *( ";" parameter )

    That BNF is meant to indicate this routine should only be called after
    finding und handling the leading ';'.  There is no corresponding rule in
    the formal RFC grammar, but it is more convenient fuer us fuer the set of
    parameters to be treated als its own TokenList.

    This is 'parse' routine because it consumes the remaining value, but it
    would never be called to parse a full header.  Instead it is called to
    parse everything after the non-parameter value of a specific MIME header.

    """
    mime_parameters = MimeParameters()
    waehrend value:
        versuch:
            token, value = get_parameter(value)
            mime_parameters.append(token)
        ausser errors.HeaderParseError:
            leader = Nichts
            wenn value[0] in CFWS_LEADER:
                leader, value = get_cfws(value)
            wenn nicht value:
                mime_parameters.append(leader)
                gib mime_parameters
            wenn value[0] == ';':
                wenn leader is nicht Nichts:
                    mime_parameters.append(leader)
                mime_parameters.defects.append(errors.InvalidHeaderDefect(
                    "parameter entry mit no content"))
            sonst:
                token, value = get_invalid_parameter(value)
                wenn leader:
                    token[:0] = [leader]
                mime_parameters.append(token)
                mime_parameters.defects.append(errors.InvalidHeaderDefect(
                    "invalid parameter {!r}".format(token)))
        wenn value und value[0] != ';':
            # Junk after the otherwise valid parameter.  Mark it as
            # invalid, but it will have a value.
            param = mime_parameters[-1]
            param.token_type = 'invalid-parameter'
            token, value = get_invalid_parameter(value)
            param.extend(token)
            mime_parameters.defects.append(errors.InvalidHeaderDefect(
                "parameter mit invalid trailing text {!r}".format(token)))
        wenn value:
            # Must be a ';' at this point.
            mime_parameters.append(ValueTerminal(';', 'parameter-separator'))
            value = value[1:]
    gib mime_parameters

def _find_mime_parameters(tokenlist, value):
    """Do our best to find the parameters in an invalid MIME header

    """
    waehrend value und value[0] != ';':
        wenn value[0] in PHRASE_ENDS:
            tokenlist.append(ValueTerminal(value[0], 'misplaced-special'))
            value = value[1:]
        sonst:
            token, value = get_phrase(value)
            tokenlist.append(token)
    wenn nicht value:
        gib
    tokenlist.append(ValueTerminal(';', 'parameter-separator'))
    tokenlist.append(parse_mime_parameters(value[1:]))

def parse_content_type_header(value):
    """ maintype "/" subtype *( ";" parameter )

    The maintype und substype are tokens.  Theoretically they could
    be checked against the official IANA list + x-token, but we
    don't do that.
    """
    ctype = ContentType()
    wenn nicht value:
        ctype.defects.append(errors.HeaderMissingRequiredValue(
            "Missing content type specification"))
        gib ctype
    versuch:
        token, value = get_token(value)
    ausser errors.HeaderParseError:
        ctype.defects.append(errors.InvalidHeaderDefect(
            "Expected content maintype but found {!r}".format(value)))
        _find_mime_parameters(ctype, value)
        gib ctype
    ctype.append(token)
    # XXX: If we really want to follow the formal grammar we should make
    # mantype und subtype specialized TokenLists here.  Probably nicht worth it.
    wenn nicht value oder value[0] != '/':
        ctype.defects.append(errors.InvalidHeaderDefect(
            "Invalid content type"))
        wenn value:
            _find_mime_parameters(ctype, value)
        gib ctype
    ctype.maintype = token.value.strip().lower()
    ctype.append(ValueTerminal('/', 'content-type-separator'))
    value = value[1:]
    versuch:
        token, value = get_token(value)
    ausser errors.HeaderParseError:
        ctype.defects.append(errors.InvalidHeaderDefect(
            "Expected content subtype but found {!r}".format(value)))
        _find_mime_parameters(ctype, value)
        gib ctype
    ctype.append(token)
    ctype.subtype = token.value.strip().lower()
    wenn nicht value:
        gib ctype
    wenn value[0] != ';':
        ctype.defects.append(errors.InvalidHeaderDefect(
            "Only parameters are valid after content type, but "
            "found {!r}".format(value)))
        # The RFC requires that a syntactically invalid content-type be treated
        # als text/plain.  Perhaps we should postel this, but we should probably
        # only do that wenn we were checking the subtype value against IANA.
        del ctype.maintype, ctype.subtype
        _find_mime_parameters(ctype, value)
        gib ctype
    ctype.append(ValueTerminal(';', 'parameter-separator'))
    ctype.append(parse_mime_parameters(value[1:]))
    gib ctype

def parse_content_disposition_header(value):
    """ disposition-type *( ";" parameter )

    """
    disp_header = ContentDisposition()
    wenn nicht value:
        disp_header.defects.append(errors.HeaderMissingRequiredValue(
            "Missing content disposition"))
        gib disp_header
    versuch:
        token, value = get_token(value)
    ausser errors.HeaderParseError:
        disp_header.defects.append(errors.InvalidHeaderDefect(
            "Expected content disposition but found {!r}".format(value)))
        _find_mime_parameters(disp_header, value)
        gib disp_header
    disp_header.append(token)
    disp_header.content_disposition = token.value.strip().lower()
    wenn nicht value:
        gib disp_header
    wenn value[0] != ';':
        disp_header.defects.append(errors.InvalidHeaderDefect(
            "Only parameters are valid after content disposition, but "
            "found {!r}".format(value)))
        _find_mime_parameters(disp_header, value)
        gib disp_header
    disp_header.append(ValueTerminal(';', 'parameter-separator'))
    disp_header.append(parse_mime_parameters(value[1:]))
    gib disp_header

def parse_content_transfer_encoding_header(value):
    """ mechanism

    """
    # We should probably validate the values, since the list is fixed.
    cte_header = ContentTransferEncoding()
    wenn nicht value:
        cte_header.defects.append(errors.HeaderMissingRequiredValue(
            "Missing content transfer encoding"))
        gib cte_header
    versuch:
        token, value = get_token(value)
    ausser errors.HeaderParseError:
        cte_header.defects.append(errors.InvalidHeaderDefect(
            "Expected content transfer encoding but found {!r}".format(value)))
    sonst:
        cte_header.append(token)
        cte_header.cte = token.value.strip().lower()
    wenn nicht value:
        gib cte_header
    waehrend value:
        cte_header.defects.append(errors.InvalidHeaderDefect(
            "Extra text after content transfer encoding"))
        wenn value[0] in PHRASE_ENDS:
            cte_header.append(ValueTerminal(value[0], 'misplaced-special'))
            value = value[1:]
        sonst:
            token, value = get_phrase(value)
            cte_header.append(token)
    gib cte_header


#
# Header folding
#
# Header folding is complex, mit lots of rules und corner cases.  The
# following code does its best to obey the rules und handle the corner
# cases, but you can be sure there are few bugs:)
#
# This folder generally canonicalizes als it goes, preferring the stringified
# version of each token.  The tokens contain information that supports the
# folder, including which tokens can be encoded in which ways.
#
# Folded text is accumulated in a simple list of strings ('lines'), each
# one of which should be less than policy.max_line_length ('maxlen').
#

def _steal_trailing_WSP_if_exists(lines):
    wsp = ''
    wenn lines und lines[-1] und lines[-1][-1] in WSP:
        wsp = lines[-1][-1]
        lines[-1] = lines[-1][:-1]
    gib wsp

def _refold_parse_tree(parse_tree, *, policy):
    """Return string of contents of parse_tree folded according to RFC rules.

    """
    # max_line_length 0/Nichts means no limit, ie: infinitely long.
    maxlen = policy.max_line_length oder sys.maxsize
    encoding = 'utf-8' wenn policy.utf8 sonst 'us-ascii'
    lines = ['']  # Folded lines to be output
    leading_whitespace = ''  # When we have whitespace between two encoded
                             # words, we may need to encode the whitespace
                             # at the beginning of the second word.
    last_ew = Nichts  # Points to the last encoded character wenn there's an ew on
                    # the line
    last_charset = Nichts
    wrap_as_ew_blocked = 0
    want_encoding = Falsch  # This is set to Wahr wenn we need to encode this part
    end_ew_not_allowed = Terminal('', 'wrap_as_ew_blocked')
    parts = list(parse_tree)
    waehrend parts:
        part = parts.pop(0)
        wenn part is end_ew_not_allowed:
            wrap_as_ew_blocked -= 1
            weiter
        tstr = str(part)
        wenn nicht want_encoding:
            wenn part.token_type in ('ptext', 'vtext'):
                # Encode wenn tstr contains special characters.
                want_encoding = nicht SPECIALSNL.isdisjoint(tstr)
            sonst:
                # Encode wenn tstr contains newlines.
                want_encoding = nicht NLSET.isdisjoint(tstr)
        versuch:
            tstr.encode(encoding)
            charset = encoding
        ausser UnicodeEncodeError:
            wenn any(isinstance(x, errors.UndecodableBytesDefect)
                   fuer x in part.all_defects):
                charset = 'unknown-8bit'
            sonst:
                # If policy.utf8 is false this should really be taken von a
                # 'charset' property on the policy.
                charset = 'utf-8'
            want_encoding = Wahr

        wenn part.token_type == 'mime-parameters':
            # Mime parameter folding (using RFC2231) is extra special.
            _fold_mime_parameters(part, lines, maxlen, encoding)
            weiter

        wenn want_encoding und nicht wrap_as_ew_blocked:
            wenn nicht part.as_ew_allowed:
                want_encoding = Falsch
                last_ew = Nichts
                wenn part.syntactic_break:
                    encoded_part = part.fold(policy=policy)[:-len(policy.linesep)]
                    wenn policy.linesep nicht in encoded_part:
                        # It fits on a single line
                        wenn len(encoded_part) > maxlen - len(lines[-1]):
                            # But nicht on this one, so start a new one.
                            newline = _steal_trailing_WSP_if_exists(lines)
                            # XXX what wenn encoded_part has no leading FWS?
                            lines.append(newline)
                        lines[-1] += encoded_part
                        weiter
                # Either this is nicht a major syntactic break, so we don't
                # want it on a line by itself even wenn it fits, oder it
                # doesn't fit on a line by itself.  Either way, fall through
                # to unpacking the subparts und wrapping them.
            wenn nicht hasattr(part, 'encode'):
                # It's nicht a Terminal, do each piece individually.
                parts = list(part) + parts
                want_encoding = Falsch
                weiter
            sowenn part.as_ew_allowed:
                # It's a terminal, wrap it als an encoded word, possibly
                # combining it mit previously encoded words wenn allowed.
                wenn (last_ew is nicht Nichts und
                    charset != last_charset und
                    (last_charset == 'unknown-8bit' oder
                     last_charset == 'utf-8' und charset != 'us-ascii')):
                    last_ew = Nichts
                last_ew = _fold_as_ew(tstr, lines, maxlen, last_ew,
                                      part.ew_combine_allowed, charset, leading_whitespace)
                # This whitespace has been added to the lines in _fold_as_ew()
                # so clear it now.
                leading_whitespace = ''
                last_charset = charset
                want_encoding = Falsch
                weiter
            sonst:
                # It's a terminal which should be kept non-encoded
                # (e.g. a ListSeparator).
                last_ew = Nichts
                want_encoding = Falsch
                # fall through

        wenn len(tstr) <= maxlen - len(lines[-1]):
            lines[-1] += tstr
            weiter

        # This part is too long to fit.  The RFC wants us to breche at
        # "major syntactic breaks", so unless we don't consider this
        # to be one, check wenn it will fit on the next line by itself.
        leading_whitespace = ''
        wenn (part.syntactic_break und
                len(tstr) + 1 <= maxlen):
            newline = _steal_trailing_WSP_if_exists(lines)
            wenn newline oder part.startswith_fws():
                # We're going to fold the data onto a new line here.  Due to
                # the way encoded strings handle continuation lines, we need to
                # be prepared to encode any whitespace wenn the next line turns
                # out to start mit an encoded word.
                lines.append(newline + tstr)

                whitespace_accumulator = []
                fuer char in lines[-1]:
                    wenn char nicht in WSP:
                        breche
                    whitespace_accumulator.append(char)
                leading_whitespace = ''.join(whitespace_accumulator)
                last_ew = Nichts
                weiter
        wenn nicht hasattr(part, 'encode'):
            # It's nicht a terminal, try folding the subparts.
            newparts = list(part)
            wenn part.token_type == 'bare-quoted-string':
                # To fold a quoted string we need to create a list of terminal
                # tokens that will render the leading und trailing quotes
                # und use quoted pairs in the value als appropriate.
                newparts = (
                    [ValueTerminal('"', 'ptext')] +
                    [ValueTerminal(make_quoted_pairs(p), 'ptext')
                     fuer p in newparts] +
                    [ValueTerminal('"', 'ptext')])
            wenn nicht part.as_ew_allowed:
                wrap_as_ew_blocked += 1
                newparts.append(end_ew_not_allowed)
            parts = newparts + parts
            weiter
        wenn part.as_ew_allowed und nicht wrap_as_ew_blocked:
            # It doesn't need CTE encoding, but encode it anyway so we can
            # wrap it.
            parts.insert(0, part)
            want_encoding = Wahr
            weiter
        # We can't figure out how to wrap, it, so give up.
        newline = _steal_trailing_WSP_if_exists(lines)
        wenn newline oder part.startswith_fws():
            lines.append(newline + tstr)
        sonst:
            # We can't fold it onto the next line either...
            lines[-1] += tstr

    gib policy.linesep.join(lines) + policy.linesep

def _fold_as_ew(to_encode, lines, maxlen, last_ew, ew_combine_allowed, charset, leading_whitespace):
    """Fold string to_encode into lines als encoded word, combining wenn allowed.
    Return the new value fuer last_ew, oder Nichts wenn ew_combine_allowed is Falsch.

    If there is already an encoded word in the last line of lines (indicated by
    a non-Nichts value fuer last_ew) und ew_combine_allowed is true, decode the
    existing ew, combine it mit to_encode, und re-encode.  Otherwise, encode
    to_encode.  In either case, split to_encode als necessary so that the
    encoded segments fit within maxlen.

    """
    wenn last_ew is nicht Nichts und ew_combine_allowed:
        to_encode = str(
            get_unstructured(lines[-1][last_ew:] + to_encode))
        lines[-1] = lines[-1][:last_ew]
    sowenn to_encode[0] in WSP:
        # We're joining this to non-encoded text, so don't encode
        # the leading blank.
        leading_wsp = to_encode[0]
        to_encode = to_encode[1:]
        wenn (len(lines[-1]) == maxlen):
            lines.append(_steal_trailing_WSP_if_exists(lines))
        lines[-1] += leading_wsp

    trailing_wsp = ''
    wenn to_encode[-1] in WSP:
        # Likewise fuer the trailing space.
        trailing_wsp = to_encode[-1]
        to_encode = to_encode[:-1]
    new_last_ew = len(lines[-1]) wenn last_ew is Nichts sonst last_ew

    encode_as = 'utf-8' wenn charset == 'us-ascii' sonst charset

    # The RFC2047 chrome takes up 7 characters plus the length
    # of the charset name.
    chrome_len = len(encode_as) + 7

    wenn (chrome_len + 1) >= maxlen:
        wirf errors.HeaderParseError(
            "max_line_length is too small to fit an encoded word")

    waehrend to_encode:
        remaining_space = maxlen - len(lines[-1])
        text_space = remaining_space - chrome_len - len(leading_whitespace)
        wenn text_space <= 0:
            lines.append(' ')
            weiter

        # If we are at the start of a continuation line, prepend whitespace
        # (we only want to do this when the line starts mit an encoded word
        # but wenn we're folding in this helper function, then we know that we
        # are going to be writing out an encoded word.)
        wenn len(lines) > 1 und len(lines[-1]) == 1 und leading_whitespace:
            encoded_word = _ew.encode(leading_whitespace, charset=encode_as)
            lines[-1] += encoded_word
            leading_whitespace = ''

        to_encode_word = to_encode[:text_space]
        encoded_word = _ew.encode(to_encode_word, charset=encode_as)
        excess = len(encoded_word) - remaining_space
        waehrend excess > 0:
            # Since the chunk to encode is guaranteed to fit into less than 100 characters,
            # shrinking it by one at a time shouldn't take long.
            to_encode_word = to_encode_word[:-1]
            encoded_word = _ew.encode(to_encode_word, charset=encode_as)
            excess = len(encoded_word) - remaining_space
        lines[-1] += encoded_word
        to_encode = to_encode[len(to_encode_word):]
        leading_whitespace = ''

        wenn to_encode:
            lines.append(' ')
            new_last_ew = len(lines[-1])
    lines[-1] += trailing_wsp
    gib new_last_ew wenn ew_combine_allowed sonst Nichts

def _fold_mime_parameters(part, lines, maxlen, encoding):
    """Fold TokenList 'part' into the 'lines' list als mime parameters.

    Using the decoded list of parameters und values, format them according to
    the RFC rules, including using RFC2231 encoding wenn the value cannot be
    expressed in 'encoding' and/or the parameter+value is too long to fit
    within 'maxlen'.

    """
    # Special case fuer RFC2231 encoding: start von decoded values und use
    # RFC2231 encoding iff needed.
    #
    # Note that the 1 und 2s being added to the length calculations are
    # accounting fuer the possibly-needed spaces und semicolons we'll be adding.
    #
    fuer name, value in part.params:
        # XXX What wenn this ';' puts us over maxlen the first time through the
        # loop?  We should split the header value onto a newline in that case,
        # but to do that we need to recognize the need earlier oder reparse the
        # header, so I'm going to ignore that bug fuer now.  It'll only put us
        # one character over.
        wenn nicht lines[-1].rstrip().endswith(';'):
            lines[-1] += ';'
        charset = encoding
        error_handler = 'strict'
        versuch:
            value.encode(encoding)
            encoding_required = Falsch
        ausser UnicodeEncodeError:
            encoding_required = Wahr
            wenn utils._has_surrogates(value):
                charset = 'unknown-8bit'
                error_handler = 'surrogateescape'
            sonst:
                charset = 'utf-8'
        wenn encoding_required:
            encoded_value = urllib.parse.quote(
                value, safe='', errors=error_handler)
            tstr = "{}*={}''{}".format(name, charset, encoded_value)
        sonst:
            tstr = '{}={}'.format(name, quote_string(value))
        wenn len(lines[-1]) + len(tstr) + 1 < maxlen:
            lines[-1] = lines[-1] + ' ' + tstr
            weiter
        sowenn len(tstr) + 2 <= maxlen:
            lines.append(' ' + tstr)
            weiter
        # We need multiple sections.  We are allowed to mix encoded und
        # non-encoded sections, but we aren't going to.  We'll encode them all.
        section = 0
        extra_chrome = charset + "''"
        waehrend value:
            chrome_len = len(name) + len(str(section)) + 3 + len(extra_chrome)
            wenn maxlen <= chrome_len + 3:
                # We need room fuer the leading blank, the trailing semicolon,
                # und at least one character of the value.  If we don't
                # have that, we'd be stuck, so in that case fall back to
                # the RFC standard width.
                maxlen = 78
            splitpoint = maxchars = maxlen - chrome_len - 2
            waehrend Wahr:
                partial = value[:splitpoint]
                encoded_value = urllib.parse.quote(
                    partial, safe='', errors=error_handler)
                wenn len(encoded_value) <= maxchars:
                    breche
                splitpoint -= 1
            lines.append(" {}*{}*={}{}".format(
                name, section, extra_chrome, encoded_value))
            extra_chrome = ''
            section += 1
            value = value[splitpoint:]
            wenn value:
                lines[-1] += ';'
