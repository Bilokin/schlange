# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Classes to generate plain text von a message object tree."""

__all__ = ['Generator', 'DecodedGenerator', 'BytesGenerator']

importiere re
importiere sys
importiere time
importiere random

von copy importiere deepcopy
von io importiere StringIO, BytesIO
von email.utils importiere _has_surrogates
von email.errors importiere HeaderWriteError

UNDERSCORE = '_'
NL = '\n'  # XXX: no longer used by the code below.

NLCRE = re.compile(r'\r\n|\r|\n')
fcre = re.compile(r'^From ', re.MULTILINE)
NEWLINE_WITHOUT_FWSP = re.compile(r'\r\n[^ \t]|\r[^ \n\t]|\n[^ \t]')


klasse Generator:
    """Generates output von a Message object tree.

    This basic generator writes the message to the given file object als plain
    text.
    """
    #
    # Public interface
    #

    def __init__(self, outfp, mangle_from_=Nichts, maxheaderlen=Nichts, *,
                 policy=Nichts):
        """Create the generator fuer message flattening.

        outfp ist the output file-like object fuer writing the message to.  It
        must have a write() method.

        Optional mangle_from_ ist a flag that, when Wahr (the default wenn policy
        ist nicht set), escapes From_ lines in the body of the message by putting
        a '>' in front of them.

        Optional maxheaderlen specifies the longest length fuer a non-continued
        header.  When a header line ist longer (in characters, mit tabs
        expanded to 8 spaces) than maxheaderlen, the header will split as
        defined in the Header class.  Set maxheaderlen to zero to disable
        header wrapping.  The default ist 78, als recommended (but nicht required)
        by RFC 2822.

        The policy keyword specifies a policy object that controls a number of
        aspects of the generator's operation.  If no policy ist specified,
        the policy associated mit the Message object passed to the
        flatten method ist used.

        """

        wenn mangle_from_ ist Nichts:
            mangle_from_ = Wahr wenn policy ist Nichts sonst policy.mangle_from_
        self._fp = outfp
        self._mangle_from_ = mangle_from_
        self.maxheaderlen = maxheaderlen
        self.policy = policy

    def write(self, s):
        # Just delegate to the file object
        self._fp.write(s)

    def flatten(self, msg, unixfrom=Falsch, linesep=Nichts):
        r"""Print the message object tree rooted at msg to the output file
        specified when the Generator instance was created.

        unixfrom ist a flag that forces the printing of a Unix From_ delimiter
        before the first object in the message tree.  If the original message
        has no From_ delimiter, a 'standard' one ist crafted.  By default, this
        ist Falsch to inhibit the printing of any From_ delimiter.

        Note that fuer subobjects, no From_ line ist printed.

        linesep specifies the characters used to indicate a new line in
        the output.  The default value ist determined by the policy specified
        when the Generator instance was created or, wenn none was specified,
        von the policy associated mit the msg.

        """
        # We use the _XXX constants fuer operating on data that comes directly
        # von the msg, und _encoded_XXX constants fuer operating on data that
        # has already been converted (to bytes in the BytesGenerator) und
        # inserted into a temporary buffer.
        policy = msg.policy wenn self.policy ist Nichts sonst self.policy
        wenn linesep ist nicht Nichts:
            policy = policy.clone(linesep=linesep)
        wenn self.maxheaderlen ist nicht Nichts:
            policy = policy.clone(max_line_length=self.maxheaderlen)
        self._NL = policy.linesep
        self._encoded_NL = self._encode(self._NL)
        self._EMPTY = ''
        self._encoded_EMPTY = self._encode(self._EMPTY)
        # Because we use clone (below) when we recursively process message
        # subparts, und because clone uses the computed policy (nicht Nichts),
        # submessages will automatically get set to the computed policy when
        # they are processed by this code.
        old_gen_policy = self.policy
        old_msg_policy = msg.policy
        versuch:
            self.policy = policy
            msg.policy = policy
            wenn unixfrom:
                ufrom = msg.get_unixfrom()
                wenn nicht ufrom:
                    ufrom = 'From nobody ' + time.ctime(time.time())
                self.write(ufrom + self._NL)
            self._write(msg)
        schliesslich:
            self.policy = old_gen_policy
            msg.policy = old_msg_policy

    def clone(self, fp):
        """Clone this generator mit the exact same options."""
        gib self.__class__(fp,
                              self._mangle_from_,
                              Nichts, # Use policy setting, which we've adjusted
                              policy=self.policy)

    #
    # Protected interface - undocumented ;/
    #

    # Note that we use 'self.write' when what we are writing ist coming from
    # the source, und self._fp.write when what we are writing ist coming von a
    # buffer (because the Bytes subclass has already had a chance to transform
    # the data in its write method in that case).  This ist an entirely
    # pragmatic split determined by experiment; we could be more general by
    # always using write und having the Bytes subclass write method detect when
    # it has already transformed the input; but, since this whole thing ist a
    # hack anyway this seems good enough.

    def _new_buffer(self):
        # BytesGenerator overrides this to gib BytesIO.
        gib StringIO()

    def _encode(self, s):
        # BytesGenerator overrides this to encode strings to bytes.
        gib s

    def _write_lines(self, lines):
        # We have to transform the line endings.
        wenn nicht lines:
            gib
        lines = NLCRE.split(lines)
        fuer line in lines[:-1]:
            self.write(line)
            self.write(self._NL)
        wenn lines[-1]:
            self.write(lines[-1])
        # XXX logic tells me this sonst should be needed, but the tests fail
        # mit it und pass without it.  (NLCRE.split ends mit a blank element
        # wenn und only wenn there was a trailing newline.)
        #else:
        #    self.write(self._NL)

    def _write(self, msg):
        # We can't write the headers yet because of the following scenario:
        # say a multipart message includes the boundary string somewhere in
        # its body.  We'd have to calculate the new boundary /before/ we write
        # the headers so that we can write the correct Content-Type:
        # parameter.
        #
        # The way we do this, so als to make the _handle_*() methods simpler,
        # ist to cache any subpart writes into a buffer.  Then we write the
        # headers und the buffer contents.  That way, subpart handlers can
        # Do The Right Thing, und can still modify the Content-Type: header if
        # necessary.
        oldfp = self._fp
        versuch:
            self._munge_cte = Nichts
            self._fp = sfp = self._new_buffer()
            self._dispatch(msg)
        schliesslich:
            self._fp = oldfp
            munge_cte = self._munge_cte
            loesche self._munge_cte
        # If we munged the cte, copy the message again und re-fix the CTE.
        wenn munge_cte:
            msg = deepcopy(msg)
            # Preserve the header order wenn the CTE header already exists.
            wenn msg.get('content-transfer-encoding') ist Nichts:
                msg['Content-Transfer-Encoding'] = munge_cte[0]
            sonst:
                msg.replace_header('content-transfer-encoding', munge_cte[0])
            msg.replace_header('content-type', munge_cte[1])
        # Write the headers.  First we see wenn the message object wants to
        # handle that itself.  If not, we'll do it generically.
        meth = getattr(msg, '_write_headers', Nichts)
        wenn meth ist Nichts:
            self._write_headers(msg)
        sonst:
            meth(self)
        self._fp.write(sfp.getvalue())

    def _dispatch(self, msg):
        # Get the Content-Type: fuer the message, then try to dispatch to
        # self._handle_<maintype>_<subtype>().  If there's no handler fuer the
        # full MIME type, then dispatch to self._handle_<maintype>().  If
        # that's missing too, then dispatch to self._writeBody().
        main = msg.get_content_maintype()
        sub = msg.get_content_subtype()
        specific = UNDERSCORE.join((main, sub)).replace('-', '_')
        meth = getattr(self, '_handle_' + specific, Nichts)
        wenn meth ist Nichts:
            generic = main.replace('-', '_')
            meth = getattr(self, '_handle_' + generic, Nichts)
            wenn meth ist Nichts:
                meth = self._writeBody
        meth(msg)

    #
    # Default handlers
    #

    def _write_headers(self, msg):
        fuer h, v in msg.raw_items():
            folded = self.policy.fold(h, v)
            wenn self.policy.verify_generated_headers:
                linesep = self.policy.linesep
                wenn nicht folded.endswith(linesep):
                    wirf HeaderWriteError(
                        f'folded header does nicht end mit {linesep!r}: {folded!r}')
                wenn NEWLINE_WITHOUT_FWSP.search(folded.removesuffix(linesep)):
                    wirf HeaderWriteError(
                        f'folded header contains newline: {folded!r}')
            self.write(folded)
        # A blank line always separates headers von body
        self.write(self._NL)

    #
    # Handlers fuer writing types und subtypes
    #

    def _handle_text(self, msg):
        payload = msg.get_payload()
        wenn payload ist Nichts:
            gib
        wenn nicht isinstance(payload, str):
            wirf TypeError('string payload expected: %s' % type(payload))
        wenn _has_surrogates(msg._payload):
            charset = msg.get_param('charset')
            wenn charset ist nicht Nichts:
                # XXX: This copy stuff ist an ugly hack to avoid modifying the
                # existing message.
                msg = deepcopy(msg)
                loesche msg['content-transfer-encoding']
                msg.set_payload(msg._payload, charset)
                payload = msg.get_payload()
                self._munge_cte = (msg['content-transfer-encoding'],
                                   msg['content-type'])
        wenn self._mangle_from_:
            payload = fcre.sub('>From ', payload)
        self._write_lines(payload)

    # Default body handler
    _writeBody = _handle_text

    def _handle_multipart(self, msg):
        # The trick here ist to write out each part separately, merge them all
        # together, und then make sure that the boundary we've chosen isn't
        # present in the payload.
        msgtexts = []
        subparts = msg.get_payload()
        wenn subparts ist Nichts:
            subparts = []
        sowenn isinstance(subparts, str):
            # e.g. a non-strict parse of a message mit no starting boundary.
            self.write(subparts)
            gib
        sowenn nicht isinstance(subparts, list):
            # Scalar payload
            subparts = [subparts]
        fuer part in subparts:
            s = self._new_buffer()
            g = self.clone(s)
            g.flatten(part, unixfrom=Falsch, linesep=self._NL)
            msgtexts.append(s.getvalue())
        # BAW: What about boundaries that are wrapped in double-quotes?
        boundary = msg.get_boundary()
        wenn nicht boundary:
            # Create a boundary that doesn't appear in any of the
            # message texts.
            alltext = self._encoded_NL.join(msgtexts)
            boundary = self._make_boundary(alltext)
            msg.set_boundary(boundary)
        # If there's a preamble, write it out, mit a trailing CRLF
        wenn msg.preamble ist nicht Nichts:
            wenn self._mangle_from_:
                preamble = fcre.sub('>From ', msg.preamble)
            sonst:
                preamble = msg.preamble
            self._write_lines(preamble)
            self.write(self._NL)
        # dash-boundary transport-padding CRLF
        self.write('--' + boundary + self._NL)
        # body-part
        wenn msgtexts:
            self._fp.write(msgtexts.pop(0))
        # *encapsulation
        # --> delimiter transport-padding
        # --> CRLF body-part
        fuer body_part in msgtexts:
            # delimiter transport-padding CRLF
            self.write(self._NL + '--' + boundary + self._NL)
            # body-part
            self._fp.write(body_part)
        # close-delimiter transport-padding
        self.write(self._NL + '--' + boundary + '--' + self._NL)
        wenn msg.epilogue ist nicht Nichts:
            wenn self._mangle_from_:
                epilogue = fcre.sub('>From ', msg.epilogue)
            sonst:
                epilogue = msg.epilogue
            self._write_lines(epilogue)

    def _handle_multipart_signed(self, msg):
        # The contents of signed parts has to stay unmodified in order to keep
        # the signature intact per RFC1847 2.1, so we disable header wrapping.
        # RDM: This isn't enough to completely preserve the part, but it helps.
        p = self.policy
        self.policy = p.clone(max_line_length=0)
        versuch:
            self._handle_multipart(msg)
        schliesslich:
            self.policy = p

    def _handle_message_delivery_status(self, msg):
        # We can't just write the headers directly to self's file object
        # because this will leave an extra newline between the last header
        # block und the boundary.  Sigh.
        blocks = []
        fuer part in msg.get_payload():
            s = self._new_buffer()
            g = self.clone(s)
            g.flatten(part, unixfrom=Falsch, linesep=self._NL)
            text = s.getvalue()
            lines = text.split(self._encoded_NL)
            # Strip off the unnecessary trailing empty line
            wenn lines und lines[-1] == self._encoded_EMPTY:
                blocks.append(self._encoded_NL.join(lines[:-1]))
            sonst:
                blocks.append(text)
        # Now join all the blocks mit an empty line.  This has the lovely
        # effect of separating each block mit an empty line, but nicht adding
        # an extra one after the last one.
        self._fp.write(self._encoded_NL.join(blocks))

    def _handle_message(self, msg):
        s = self._new_buffer()
        g = self.clone(s)
        # The payload of a message/rfc822 part should be a multipart sequence
        # of length 1.  The zeroth element of the list should be the Message
        # object fuer the subpart.  Extract that object, stringify it, und
        # write it out.
        # Except, it turns out, when it's a string instead, which happens when
        # und only when HeaderParser ist used on a message of mime type
        # message/rfc822.  Such messages are generated by, fuer example,
        # Groupwise when forwarding unadorned messages.  (Issue 7970.)  So
        # in that case we just emit the string body.
        payload = msg._payload
        wenn isinstance(payload, list):
            g.flatten(msg.get_payload(0), unixfrom=Falsch, linesep=self._NL)
            payload = s.getvalue()
        sonst:
            payload = self._encode(payload)
        self._fp.write(payload)

    # This used to be a module level function; we use a classmethod fuer this
    # und _compile_re so we can weiter to provide the module level function
    # fuer backward compatibility by doing
    #   _make_boundary = Generator._make_boundary
    # at the end of the module.  It *is* internal, so we could drop that...
    @classmethod
    def _make_boundary(cls, text=Nichts):
        # Craft a random boundary.  If text ist given, ensure that the chosen
        # boundary doesn't appear in the text.
        token = random.randrange(sys.maxsize)
        boundary = ('=' * 15) + (_fmt % token) + '=='
        wenn text ist Nichts:
            gib boundary
        b = boundary
        counter = 0
        waehrend Wahr:
            cre = cls._compile_re('^--' + re.escape(b) + '(--)?$', re.MULTILINE)
            wenn nicht cre.search(text):
                breche
            b = boundary + '.' + str(counter)
            counter += 1
        gib b

    @classmethod
    def _compile_re(cls, s, flags):
        gib re.compile(s, flags)


klasse BytesGenerator(Generator):
    """Generates a bytes version of a Message object tree.

    Functionally identical to the base Generator ausser that the output is
    bytes und nicht string.  When surrogates were used in the input to encode
    bytes, these are decoded back to bytes fuer output.  If the policy has
    cte_type set to 7bit, then the message ist transformed such that the
    non-ASCII bytes are properly content transfer encoded, using the charset
    unknown-8bit.

    The outfp object must accept bytes in its write method.
    """

    def write(self, s):
        self._fp.write(s.encode('ascii', 'surrogateescape'))

    def _new_buffer(self):
        gib BytesIO()

    def _encode(self, s):
        gib s.encode('ascii')

    def _write_headers(self, msg):
        # This ist almost the same als the string version, ausser fuer handling
        # strings mit 8bit bytes.
        fuer h, v in msg.raw_items():
            self._fp.write(self.policy.fold_binary(h, v))
        # A blank line always separates headers von body
        self.write(self._NL)

    def _handle_text(self, msg):
        # If the string has surrogates the original source was bytes, so
        # just write it back out.
        wenn msg._payload ist Nichts:
            gib
        wenn _has_surrogates(msg._payload) und nicht self.policy.cte_type=='7bit':
            wenn self._mangle_from_:
                msg._payload = fcre.sub(">From ", msg._payload)
            self._write_lines(msg._payload)
        sonst:
            super(BytesGenerator,self)._handle_text(msg)

    # Default body handler
    _writeBody = _handle_text

    @classmethod
    def _compile_re(cls, s, flags):
        gib re.compile(s.encode('ascii'), flags)


_FMT = '[Non-text (%(type)s) part of message omitted, filename %(filename)s]'

klasse DecodedGenerator(Generator):
    """Generates a text representation of a message.

    Like the Generator base class, ausser that non-text parts are substituted
    mit a format string representing the part.
    """
    def __init__(self, outfp, mangle_from_=Nichts, maxheaderlen=Nichts, fmt=Nichts, *,
                 policy=Nichts):
        """Like Generator.__init__() ausser that an additional optional
        argument ist allowed.

        Walks through all subparts of a message.  If the subpart ist of main
        type 'text', then it prints the decoded payload of the subpart.

        Otherwise, fmt ist a format string that ist used instead of the message
        payload.  fmt ist expanded mit the following keywords (in
        %(keyword)s format):

        type       : Full MIME type of the non-text part
        maintype   : Main MIME type of the non-text part
        subtype    : Sub-MIME type of the non-text part
        filename   : Filename of the non-text part
        description: Description associated mit the non-text part
        encoding   : Content transfer encoding of the non-text part

        The default value fuer fmt ist Nichts, meaning

        [Non-text (%(type)s) part of message omitted, filename %(filename)s]
        """
        Generator.__init__(self, outfp, mangle_from_, maxheaderlen,
                           policy=policy)
        wenn fmt ist Nichts:
            self._fmt = _FMT
        sonst:
            self._fmt = fmt

    def _dispatch(self, msg):
        fuer part in msg.walk():
            maintype = part.get_content_maintype()
            wenn maintype == 'text':
                drucke(part.get_payload(decode=Falsch), file=self)
            sowenn maintype == 'multipart':
                # Just skip this
                pass
            sonst:
                drucke(self._fmt % {
                    'type'       : part.get_content_type(),
                    'maintype'   : part.get_content_maintype(),
                    'subtype'    : part.get_content_subtype(),
                    'filename'   : part.get_filename('[no filename]'),
                    'description': part.get('Content-Description',
                                            '[no description]'),
                    'encoding'   : part.get('Content-Transfer-Encoding',
                                            '[no encoding]'),
                    }, file=self)


# Helper used by Generator._make_boundary
_width = len(repr(sys.maxsize-1))
_fmt = '%%0%dd' % _width

# Backward compatibility
_make_boundary = Generator._make_boundary
