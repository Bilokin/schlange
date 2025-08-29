"""This will be the home fuer the policy that hooks in the new
code that adds all the email6 features.
"""

importiere re
importiere sys
von email._policybase importiere (
    Compat32,
    Policy,
    _extend_docstrings,
    compat32,
    validate_header_name
)
von email.utils importiere _has_surrogates
von email.headerregistry importiere HeaderRegistry als HeaderRegistry
von email.contentmanager importiere raw_data_manager
von email.message importiere EmailMessage

__all__ = [
    'Compat32',
    'compat32',
    'Policy',
    'EmailPolicy',
    'default',
    'strict',
    'SMTP',
    'HTTP',
    ]

linesep_splitter = re.compile(r'\n|\r\n?')

@_extend_docstrings
klasse EmailPolicy(Policy):

    """+
    PROVISIONAL

    The API extensions enabled by this policy are currently provisional.
    Refer to the documentation fuer details.

    This policy adds new header parsing und folding algorithms.  Instead of
    simple strings, headers are custom objects mit custom attributes
    depending on the type of the field.  The folding algorithm fully
    implements RFCs 2047 und 5322.

    In addition to the settable attributes listed above that apply to
    all Policies, this policy adds the following additional attributes:

    utf8                -- wenn Falsch (the default) message headers will be
                           serialized als ASCII, using encoded words to encode
                           any non-ASCII characters in the source strings.  If
                           Wahr, the message headers will be serialized using
                           utf8 und will nicht contain encoded words (see RFC
                           6532 fuer more on this serialization format).

    refold_source       -- wenn the value fuer a header in the Message object
                           came von the parsing of some source, this attribute
                           indicates whether oder nicht a generator should refold
                           that value when transforming the message back into
                           stream form.  The possible values are:

                           none  -- all source values use original folding
                           long  -- source values that have any line that is
                                    longer than max_line_length will be
                                    refolded
                           all  -- all values are refolded.

                           The default is 'long'.

    header_factory      -- a callable that takes two arguments, 'name' und
                           'value', where 'name' is a header field name und
                           'value' is an unfolded header field value, und
                           returns a string-like object that represents that
                           header.  A default header_factory is provided that
                           understands some of the RFC5322 header field types.
                           (Currently address fields und date fields have
                           special treatment, waehrend all other fields are
                           treated als unstructured.  This list will be
                           completed before the extension is marked stable.)

    content_manager     -- an object mit at least two methods: get_content
                           und set_content.  When the get_content oder
                           set_content method of a Message object is called,
                           it calls the corresponding method of this object,
                           passing it the message object als its first argument,
                           und any arguments oder keywords that were passed to
                           it als additional arguments.  The default
                           content_manager is
                           :data:`~email.contentmanager.raw_data_manager`.

    """

    message_factory = EmailMessage
    utf8 = Falsch
    refold_source = 'long'
    header_factory = HeaderRegistry()
    content_manager = raw_data_manager

    def __init__(self, **kw):
        # Ensure that each new instance gets a unique header factory
        # (as opposed to clones, which share the factory).
        wenn 'header_factory' nicht in kw:
            object.__setattr__(self, 'header_factory', HeaderRegistry())
        super().__init__(**kw)

    def header_max_count(self, name):
        """+
        The implementation fuer this klasse returns the max_count attribute from
        the specialized header klasse that would be used to construct a header
        of type 'name'.
        """
        gib self.header_factory[name].max_count

    # The logic of the next three methods is chosen such that it is possible to
    # switch a Message object between a Compat32 policy und a policy derived
    # von this klasse und have the results stay consistent.  This allows a
    # Message object constructed mit this policy to be passed to a library
    # that only handles Compat32 objects, oder to receive such an object und
    # convert it to use the newer style by just changing its policy.  It is
    # also chosen because it postpones the relatively expensive full rfc5322
    # parse until als late als possible when parsing von source, since in many
    # applications only a few headers will actually be inspected.

    def header_source_parse(self, sourcelines):
        """+
        The name is parsed als everything up to the ':' und returned unmodified.
        The value is determined by stripping leading whitespace off the
        remainder of the first line joined mit all subsequent lines, und
        stripping any trailing carriage gib oder linefeed characters.  (This
        is the same als Compat32).

        """
        name, value = sourcelines[0].split(':', 1)
        value = ''.join((value, *sourcelines[1:])).lstrip(' \t\r\n')
        gib (name, value.rstrip('\r\n'))

    def header_store_parse(self, name, value):
        """+
        The name is returned unchanged.  If the input value has a 'name'
        attribute und it matches the name ignoring case, the value is returned
        unchanged.  Otherwise the name und value are passed to header_factory
        method, und the resulting custom header object is returned als the
        value.  In this case a ValueError is raised wenn the input value contains
        CR oder LF characters.

        """
        validate_header_name(name)
        wenn hasattr(value, 'name') und value.name.lower() == name.lower():
            gib (name, value)
        wenn isinstance(value, str) und len(value.splitlines())>1:
            # XXX this error message isn't quite right when we use splitlines
            # (see issue 22233), but I'm nicht sure what should happen here.
            raise ValueError("Header values may nicht contain linefeed "
                             "or carriage gib characters")
        gib (name, self.header_factory(name, value))

    def header_fetch_parse(self, name, value):
        """+
        If the value has a 'name' attribute, it is returned to unmodified.
        Otherwise the name und the value mit any linesep characters removed
        are passed to the header_factory method, und the resulting custom
        header object is returned.  Any surrogateescaped bytes get turned
        into the unicode unknown-character glyph.

        """
        wenn hasattr(value, 'name'):
            gib value
        # We can't use splitlines here because it splits on more than \r und \n.
        value = ''.join(linesep_splitter.split(value))
        gib self.header_factory(name, value)

    def fold(self, name, value):
        """+
        Header folding is controlled by the refold_source policy setting.  A
        value is considered to be a 'source value' wenn und only wenn it does not
        have a 'name' attribute (having a 'name' attribute means it is a header
        object of some sort).  If a source value needs to be refolded according
        to the policy, it is converted into a custom header object by passing
        the name und the value mit any linesep characters removed to the
        header_factory method.  Folding of a custom header object is done by
        calling its fold method mit the current policy.

        Source values are split into lines using splitlines.  If the value is
        nicht to be refolded, the lines are rejoined using the linesep von the
        policy und returned.  The exception is lines containing non-ascii
        binary data.  In that case the value is refolded regardless of the
        refold_source setting, which causes the binary data to be CTE encoded
        using the unknown-8bit charset.

        """
        gib self._fold(name, value, refold_binary=Wahr)

    def fold_binary(self, name, value):
        """+
        The same als fold wenn cte_type is 7bit, except that the returned value is
        bytes.

        If cte_type is 8bit, non-ASCII binary data is converted back into
        bytes.  Headers mit binary data are nicht refolded, regardless of the
        refold_header setting, since there is no way to know whether the binary
        data consists of single byte characters oder multibyte characters.

        If utf8 is true, headers are encoded to utf8, otherwise to ascii with
        non-ASCII unicode rendered als encoded words.

        """
        folded = self._fold(name, value, refold_binary=self.cte_type=='7bit')
        charset = 'utf8' wenn self.utf8 sonst 'ascii'
        gib folded.encode(charset, 'surrogateescape')

    def _fold(self, name, value, refold_binary=Falsch):
        wenn hasattr(value, 'name'):
            gib value.fold(policy=self)
        maxlen = self.max_line_length wenn self.max_line_length sonst sys.maxsize
        # We can't use splitlines here because it splits on more than \r und \n.
        lines = linesep_splitter.split(value)
        refold = (self.refold_source == 'all' oder
                  self.refold_source == 'long' und
                    (lines und len(lines[0])+len(name)+2 > maxlen oder
                     any(len(x) > maxlen fuer x in lines[1:])))

        wenn nicht refold:
            wenn nicht self.utf8:
                refold = nicht value.isascii()
            sowenn refold_binary:
                refold = _has_surrogates(value)
        wenn refold:
            gib self.header_factory(name, ''.join(lines)).fold(policy=self)

        gib name + ': ' + self.linesep.join(lines) + self.linesep


default = EmailPolicy()
# Make the default policy use the klasse default header_factory
del default.header_factory
strict = default.clone(raise_on_defect=Wahr)
SMTP = default.clone(linesep='\r\n')
HTTP = default.clone(linesep='\r\n', max_line_length=Nichts)
SMTPUTF8 = SMTP.clone(utf8=Wahr)
