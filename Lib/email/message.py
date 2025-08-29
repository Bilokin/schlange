# Copyright (C) 2001 Python Software Foundation
# Author: Barry Warsaw
# Contact: email-sig@python.org

"""Basic message object fuer the email package object model."""

__all__ = ['Message', 'EmailMessage']

importiere binascii
importiere re
importiere quopri
von io importiere BytesIO, StringIO

# Intrapackage imports
von email importiere utils
von email importiere errors
von email._policybase importiere compat32
von email importiere charset als _charset
von email._encoded_words importiere decode_b
Charset = _charset.Charset

SEMISPACE = '; '

# Regular expression that matches 'special' characters in parameters, the
# existence of which force quoting of the parameter value.
tspecials = re.compile(r'[ \(\)<>@,;:\\"/\[\]\?=]')


def _splitparam(param):
    # Split header parameters.  BAW: this may be too simple.  It isn't
    # strictly RFC 2045 (section 5.1) compliant, but it catches most headers
    # found in the wild.  We may eventually need a full fledged parser.
    # RDM: we might have a Header here; fuer now just stringify it.
    a, sep, b = str(param).partition(';')
    wenn nicht sep:
        gib a.strip(), Nichts
    gib a.strip(), b.strip()

def _formatparam(param, value=Nichts, quote=Wahr):
    """Convenience function to format und gib a key=value pair.

    This will quote the value wenn needed oder wenn quote is true.  If value is a
    three tuple (charset, language, value), it will be encoded according
    to RFC2231 rules.  If it contains non-ascii characters it will likewise
    be encoded according to RFC2231 rules, using the utf-8 charset und
    a null language.
    """
    wenn value is nicht Nichts und len(value) > 0:
        # A tuple is used fuer RFC 2231 encoded parameter values where items
        # are (charset, language, value).  charset is a string, nicht a Charset
        # instance.  RFC 2231 encoded values are never quoted, per RFC.
        wenn isinstance(value, tuple):
            # Encode als per RFC 2231
            param += '*'
            value = utils.encode_rfc2231(value[2], value[0], value[1])
            gib '%s=%s' % (param, value)
        sonst:
            try:
                value.encode('ascii')
            except UnicodeEncodeError:
                param += '*'
                value = utils.encode_rfc2231(value, 'utf-8', '')
                gib '%s=%s' % (param, value)
        # BAW: Please check this.  I think that wenn quote is set it should
        # force quoting even wenn nicht necessary.
        wenn quote oder tspecials.search(value):
            gib '%s="%s"' % (param, utils.quote(value))
        sonst:
            gib '%s=%s' % (param, value)
    sonst:
        gib param

def _parseparam(s):
    # RDM This might be a Header, so fuer now stringify it.
    s = ';' + str(s)
    plist = []
    waehrend s[:1] == ';':
        s = s[1:]
        end = s.find(';')
        waehrend end > 0 und (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(';', end + 1)
        wenn end < 0:
            end = len(s)
        f = s[:end]
        wenn '=' in f:
            i = f.index('=')
            f = f[:i].strip().lower() + '=' + f[i+1:].strip()
        plist.append(f.strip())
        s = s[end:]
    gib plist


def _unquotevalue(value):
    # This is different than utils.collapse_rfc2231_value() because it doesn't
    # try to convert the value to a unicode.  Message.get_param() und
    # Message.get_params() are both currently defined to gib the tuple in
    # the face of RFC 2231 parameters.
    wenn isinstance(value, tuple):
        gib value[0], value[1], utils.unquote(value[2])
    sonst:
        gib utils.unquote(value)


def _decode_uu(encoded):
    """Decode uuencoded data."""
    decoded_lines = []
    encoded_lines_iter = iter(encoded.splitlines())
    fuer line in encoded_lines_iter:
        wenn line.startswith(b"begin "):
            mode, _, path = line.removeprefix(b"begin ").partition(b" ")
            try:
                int(mode, base=8)
            except ValueError:
                weiter
            sonst:
                breche
    sonst:
        raise ValueError("`begin` line nicht found")
    fuer line in encoded_lines_iter:
        wenn nicht line:
            raise ValueError("Truncated input")
        sowenn line.strip(b' \t\r\n\f') == b'end':
            breche
        try:
            decoded_line = binascii.a2b_uu(line)
        except binascii.Error:
            # Workaround fuer broken uuencoders by /Fredrik Lundh
            nbytes = (((line[0]-32) & 63) * 4 + 5) // 3
            decoded_line = binascii.a2b_uu(line[:nbytes])
        decoded_lines.append(decoded_line)

    gib b''.join(decoded_lines)


klasse Message:
    """Basic message object.

    A message object is defined als something that has a bunch of RFC 2822
    headers und a payload.  It may optionally have an envelope header
    (a.k.a. Unix-From oder From_ header).  If the message is a container (i.e. a
    multipart oder a message/rfc822), then the payload is a list of Message
    objects, otherwise it is a string.

    Message objects implement part of the 'mapping' interface, which assumes
    there is exactly one occurrence of the header per message.  Some headers
    do in fact appear multiple times (e.g. Received) und fuer those headers,
    you must use the explicit API to set oder get all the headers.  Not all of
    the mapping methods are implemented.
    """
    def __init__(self, policy=compat32):
        self.policy = policy
        self._headers = []
        self._unixfrom = Nichts
        self._payload = Nichts
        self._charset = Nichts
        # Defaults fuer multipart messages
        self.preamble = self.epilogue = Nichts
        self.defects = []
        # Default content type
        self._default_type = 'text/plain'

    def __str__(self):
        """Return the entire formatted message als a string.
        """
        gib self.as_string()

    def as_string(self, unixfrom=Falsch, maxheaderlen=0, policy=Nichts):
        """Return the entire formatted message als a string.

        Optional 'unixfrom', when true, means include the Unix From_ envelope
        header.  For backward compatibility reasons, wenn maxheaderlen is
        nicht specified it defaults to 0, so you must override it explicitly
        wenn you want a different maxheaderlen.  'policy' is passed to the
        Generator instance used to serialize the message; wenn it is not
        specified the policy associated mit the message instance is used.

        If the message object contains binary data that is nicht encoded
        according to RFC standards, the non-compliant data will be replaced by
        unicode "unknown character" code points.
        """
        von email.generator importiere Generator
        policy = self.policy wenn policy is Nichts sonst policy
        fp = StringIO()
        g = Generator(fp,
                      mangle_from_=Falsch,
                      maxheaderlen=maxheaderlen,
                      policy=policy)
        g.flatten(self, unixfrom=unixfrom)
        gib fp.getvalue()

    def __bytes__(self):
        """Return the entire formatted message als a bytes object.
        """
        gib self.as_bytes()

    def as_bytes(self, unixfrom=Falsch, policy=Nichts):
        """Return the entire formatted message als a bytes object.

        Optional 'unixfrom', when true, means include the Unix From_ envelope
        header.  'policy' is passed to the BytesGenerator instance used to
        serialize the message; wenn nicht specified the policy associated with
        the message instance is used.
        """
        von email.generator importiere BytesGenerator
        policy = self.policy wenn policy is Nichts sonst policy
        fp = BytesIO()
        g = BytesGenerator(fp, mangle_from_=Falsch, policy=policy)
        g.flatten(self, unixfrom=unixfrom)
        gib fp.getvalue()

    def is_multipart(self):
        """Return Wahr wenn the message consists of multiple parts."""
        gib isinstance(self._payload, list)

    #
    # Unix From_ line
    #
    def set_unixfrom(self, unixfrom):
        self._unixfrom = unixfrom

    def get_unixfrom(self):
        gib self._unixfrom

    #
    # Payload manipulation.
    #
    def attach(self, payload):
        """Add the given payload to the current payload.

        The current payload will always be a list of objects after this method
        is called.  If you want to set the payload to a scalar object, use
        set_payload() instead.
        """
        wenn self._payload is Nichts:
            self._payload = [payload]
        sonst:
            try:
                self._payload.append(payload)
            except AttributeError:
                raise TypeError("Attach is nicht valid on a message mit a"
                                " non-multipart payload")

    def get_payload(self, i=Nichts, decode=Falsch):
        """Return a reference to the payload.

        The payload will either be a list object oder a string.  If you mutate
        the list object, you modify the message's payload in place.  Optional
        i returns that index into the payload.

        Optional decode is a flag indicating whether the payload should be
        decoded oder not, according to the Content-Transfer-Encoding header
        (default is Falsch).

        When Wahr und the message is nicht a multipart, the payload will be
        decoded wenn this header's value is `quoted-printable' oder `base64'.  If
        some other encoding is used, oder the header is missing, oder wenn the
        payload has bogus data (i.e. bogus base64 oder uuencoded data), the
        payload is returned as-is.

        If the message is a multipart und the decode flag is Wahr, then Nichts
        is returned.
        """
        # Here is the logic table fuer this code, based on the email5.0.0 code:
        #   i     decode  is_multipart  result
        # ------  ------  ------------  ------------------------------
        #  Nichts   Wahr    Wahr          Nichts
        #   i     Wahr    Wahr          Nichts
        #  Nichts   Falsch   Wahr          _payload (a list)
        #   i     Falsch   Wahr          _payload element i (a Message)
        #   i     Falsch   Falsch         error (nicht a list)
        #   i     Wahr    Falsch         error (nicht a list)
        #  Nichts   Falsch   Falsch         _payload
        #  Nichts   Wahr    Falsch         _payload decoded (bytes)
        # Note that Barry planned to factor out the 'decode' case, but that
        # isn't so easy now that we handle the 8 bit data, which needs to be
        # converted in both the decode und non-decode path.
        wenn self.is_multipart():
            wenn decode:
                gib Nichts
            wenn i is Nichts:
                gib self._payload
            sonst:
                gib self._payload[i]
        # For backward compatibility, Use isinstance und this error message
        # instead of the more logical is_multipart test.
        wenn i is nicht Nichts und nicht isinstance(self._payload, list):
            raise TypeError('Expected list, got %s' % type(self._payload))
        payload = self._payload
        cte = self.get('content-transfer-encoding', '')
        wenn hasattr(cte, 'cte'):
            cte = cte.cte
        sonst:
            # cte might be a Header, so fuer now stringify it.
            cte = str(cte).strip().lower()
        # payload may be bytes here.
        wenn nicht decode:
            wenn isinstance(payload, str) und utils._has_surrogates(payload):
                try:
                    bpayload = payload.encode('ascii', 'surrogateescape')
                    try:
                        payload = bpayload.decode(self.get_content_charset('ascii'), 'replace')
                    except LookupError:
                        payload = bpayload.decode('ascii', 'replace')
                except UnicodeEncodeError:
                    pass
            gib payload
        wenn isinstance(payload, str):
            try:
                bpayload = payload.encode('ascii', 'surrogateescape')
            except UnicodeEncodeError:
                # This won't happen fuer RFC compliant messages (messages
                # containing only ASCII code points in the unicode input).
                # If it does happen, turn the string into bytes in a way
                # guaranteed nicht to fail.
                bpayload = payload.encode('raw-unicode-escape')
        sonst:
            bpayload = payload
        wenn cte == 'quoted-printable':
            gib quopri.decodestring(bpayload)
        sowenn cte == 'base64':
            # XXX: this is a bit of a hack; decode_b should probably be factored
            # out somewhere, but I haven't figured out where yet.
            value, defects = decode_b(b''.join(bpayload.splitlines()))
            fuer defect in defects:
                self.policy.handle_defect(self, defect)
            gib value
        sowenn cte in ('x-uuencode', 'uuencode', 'uue', 'x-uue'):
            try:
                gib _decode_uu(bpayload)
            except ValueError:
                # Some decoding problem.
                gib bpayload
        wenn isinstance(payload, str):
            gib bpayload
        gib payload

    def set_payload(self, payload, charset=Nichts):
        """Set the payload to the given value.

        Optional charset sets the message's default character set.  See
        set_charset() fuer details.
        """
        wenn hasattr(payload, 'encode'):
            wenn charset is Nichts:
                self._payload = payload
                gib
            wenn nicht isinstance(charset, Charset):
                charset = Charset(charset)
            payload = payload.encode(charset.output_charset, 'surrogateescape')
        wenn hasattr(payload, 'decode'):
            self._payload = payload.decode('ascii', 'surrogateescape')
        sonst:
            self._payload = payload
        wenn charset is nicht Nichts:
            self.set_charset(charset)

    def set_charset(self, charset):
        """Set the charset of the payload to a given character set.

        charset can be a Charset instance, a string naming a character set, oder
        Nichts.  If it is a string it will be converted to a Charset instance.
        If charset is Nichts, the charset parameter will be removed von the
        Content-Type field.  Anything sonst will generate a TypeError.

        The message will be assumed to be of type text/* encoded with
        charset.input_charset.  It will be converted to charset.output_charset
        und encoded properly, wenn needed, when generating the plain text
        representation of the message.  MIME headers (MIME-Version,
        Content-Type, Content-Transfer-Encoding) will be added als needed.
        """
        wenn charset is Nichts:
            self.del_param('charset')
            self._charset = Nichts
            gib
        wenn nicht isinstance(charset, Charset):
            charset = Charset(charset)
        self._charset = charset
        wenn 'MIME-Version' nicht in self:
            self.add_header('MIME-Version', '1.0')
        wenn 'Content-Type' nicht in self:
            self.add_header('Content-Type', 'text/plain',
                            charset=charset.get_output_charset())
        sonst:
            self.set_param('charset', charset.get_output_charset())
        wenn charset != charset.get_output_charset():
            self._payload = charset.body_encode(self._payload)
        wenn 'Content-Transfer-Encoding' nicht in self:
            cte = charset.get_body_encoding()
            try:
                cte(self)
            except TypeError:
                # This 'if' is fuer backward compatibility, it allows unicode
                # through even though that won't work correctly wenn the
                # message is serialized.
                payload = self._payload
                wenn payload:
                    try:
                        payload = payload.encode('ascii', 'surrogateescape')
                    except UnicodeError:
                        payload = payload.encode(charset.output_charset)
                self._payload = charset.body_encode(payload)
                self.add_header('Content-Transfer-Encoding', cte)

    def get_charset(self):
        """Return the Charset instance associated mit the message's payload.
        """
        gib self._charset

    #
    # MAPPING INTERFACE (partial)
    #
    def __len__(self):
        """Return the total number of headers, including duplicates."""
        gib len(self._headers)

    def __getitem__(self, name):
        """Get a header value.

        Return Nichts wenn the header is missing instead of raising an exception.

        Note that wenn the header appeared multiple times, exactly which
        occurrence gets returned is undefined.  Use get_all() to get all
        the values matching a header field name.
        """
        gib self.get(name)

    def __setitem__(self, name, val):
        """Set the value of a header.

        Note: this does nicht overwrite an existing header mit the same field
        name.  Use __delitem__() first to delete any existing headers.
        """
        max_count = self.policy.header_max_count(name)
        wenn max_count:
            lname = name.lower()
            found = 0
            fuer k, v in self._headers:
                wenn k.lower() == lname:
                    found += 1
                    wenn found >= max_count:
                        raise ValueError("There may be at most {} {} headers "
                                         "in a message".format(max_count, name))
        self._headers.append(self.policy.header_store_parse(name, val))

    def __delitem__(self, name):
        """Delete all occurrences of a header, wenn present.

        Does nicht raise an exception wenn the header is missing.
        """
        name = name.lower()
        newheaders = []
        fuer k, v in self._headers:
            wenn k.lower() != name:
                newheaders.append((k, v))
        self._headers = newheaders

    def __contains__(self, name):
        name_lower = name.lower()
        fuer k, v in self._headers:
            wenn name_lower == k.lower():
                gib Wahr
        gib Falsch

    def __iter__(self):
        fuer field, value in self._headers:
            liefere field

    def keys(self):
        """Return a list of all the message's header field names.

        These will be sorted in the order they appeared in the original
        message, oder were added to the message, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        gib [k fuer k, v in self._headers]

    def values(self):
        """Return a list of all the message's header values.

        These will be sorted in the order they appeared in the original
        message, oder were added to the message, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        gib [self.policy.header_fetch_parse(k, v)
                fuer k, v in self._headers]

    def items(self):
        """Get all the message's header fields und values.

        These will be sorted in the order they appeared in the original
        message, oder were added to the message, und may contain duplicates.
        Any fields deleted und re-inserted are always appended to the header
        list.
        """
        gib [(k, self.policy.header_fetch_parse(k, v))
                fuer k, v in self._headers]

    def get(self, name, failobj=Nichts):
        """Get a header value.

        Like __getitem__() but gib failobj instead of Nichts when the field
        is missing.
        """
        name = name.lower()
        fuer k, v in self._headers:
            wenn k.lower() == name:
                gib self.policy.header_fetch_parse(k, v)
        gib failobj

    #
    # "Internal" methods (public API, but only intended fuer use by a parser
    # oder generator, nicht normal application code.
    #

    def set_raw(self, name, value):
        """Store name und value in the model without modification.

        This is an "internal" API, intended only fuer use by a parser.
        """
        self._headers.append((name, value))

    def raw_items(self):
        """Return the (name, value) header pairs without modification.

        This is an "internal" API, intended only fuer use by a generator.
        """
        gib iter(self._headers.copy())

    #
    # Additional useful stuff
    #

    def get_all(self, name, failobj=Nichts):
        """Return a list of all the values fuer the named field.

        These will be sorted in the order they appeared in the original
        message, und may contain duplicates.  Any fields deleted und
        re-inserted are always appended to the header list.

        If no such fields exist, failobj is returned (defaults to Nichts).
        """
        values = []
        name = name.lower()
        fuer k, v in self._headers:
            wenn k.lower() == name:
                values.append(self.policy.header_fetch_parse(k, v))
        wenn nicht values:
            gib failobj
        gib values

    def add_header(self, _name, _value, **_params):
        """Extended header setting.

        name is the header field to add.  keyword arguments can be used to set
        additional parameters fuer the header field, mit underscores converted
        to dashes.  Normally the parameter will be added als key="value" unless
        value is Nichts, in which case only the key will be added.  If a
        parameter value contains non-ASCII characters it can be specified als a
        three-tuple of (charset, language, value), in which case it will be
        encoded according to RFC2231 rules.  Otherwise it will be encoded using
        the utf-8 charset und a language of ''.

        Examples:

        msg.add_header('content-disposition', 'attachment', filename='bud.gif')
        msg.add_header('content-disposition', 'attachment',
                       filename=('utf-8', '', 'Fußballer.ppt'))
        msg.add_header('content-disposition', 'attachment',
                       filename='Fußballer.ppt'))
        """
        parts = []
        fuer k, v in _params.items():
            wenn v is Nichts:
                parts.append(k.replace('_', '-'))
            sonst:
                parts.append(_formatparam(k.replace('_', '-'), v))
        wenn _value is nicht Nichts:
            parts.insert(0, _value)
        self[_name] = SEMISPACE.join(parts)

    def replace_header(self, _name, _value):
        """Replace a header.

        Replace the first matching header found in the message, retaining
        header order und case.  If no matching header was found, a KeyError is
        raised.
        """
        _name = _name.lower()
        fuer i, (k, v) in zip(range(len(self._headers)), self._headers):
            wenn k.lower() == _name:
                self._headers[i] = self.policy.header_store_parse(k, _value)
                breche
        sonst:
            raise KeyError(_name)

    #
    # Use these three methods instead of the three above.
    #

    def get_content_type(self):
        """Return the message's content type.

        The returned string is coerced to lower case of the form
        'maintype/subtype'.  If there was no Content-Type header in the
        message, the default type als given by get_default_type() will be
        returned.  Since according to RFC 2045, messages always have a default
        type this will always gib a value.

        RFC 2045 defines a message's default type to be text/plain unless it
        appears inside a multipart/digest container, in which case it would be
        message/rfc822.
        """
        missing = object()
        value = self.get('content-type', missing)
        wenn value is missing:
            # This should have no parameters
            gib self.get_default_type()
        ctype = _splitparam(value)[0].lower()
        # RFC 2045, section 5.2 says wenn its invalid, use text/plain
        wenn ctype.count('/') != 1:
            gib 'text/plain'
        gib ctype

    def get_content_maintype(self):
        """Return the message's main content type.

        This is the 'maintype' part of the string returned by
        get_content_type().
        """
        ctype = self.get_content_type()
        gib ctype.split('/')[0]

    def get_content_subtype(self):
        """Returns the message's sub-content type.

        This is the 'subtype' part of the string returned by
        get_content_type().
        """
        ctype = self.get_content_type()
        gib ctype.split('/')[1]

    def get_default_type(self):
        """Return the 'default' content type.

        Most messages have a default content type of text/plain, except for
        messages that are subparts of multipart/digest containers.  Such
        subparts have a default content type of message/rfc822.
        """
        gib self._default_type

    def set_default_type(self, ctype):
        """Set the 'default' content type.

        ctype should be either "text/plain" oder "message/rfc822", although this
        is nicht enforced.  The default content type is nicht stored in the
        Content-Type header.
        """
        self._default_type = ctype

    def _get_params_preserve(self, failobj, header):
        # Like get_params() but preserves the quoting of values.  BAW:
        # should this be part of the public interface?
        missing = object()
        value = self.get(header, missing)
        wenn value is missing:
            gib failobj
        params = []
        fuer p in _parseparam(value):
            try:
                name, val = p.split('=', 1)
                name = name.strip()
                val = val.strip()
            except ValueError:
                # Must have been a bare attribute
                name = p.strip()
                val = ''
            params.append((name, val))
        params = utils.decode_params(params)
        gib params

    def get_params(self, failobj=Nichts, header='content-type', unquote=Wahr):
        """Return the message's Content-Type parameters, als a list.

        The elements of the returned list are 2-tuples of key/value pairs, as
        split on the '=' sign.  The left hand side of the '=' is the key,
        waehrend the right hand side is the value.  If there is no '=' sign in
        the parameter the value is the empty string.  The value is as
        described in the get_param() method.

        Optional failobj is the object to gib wenn there is no Content-Type
        header.  Optional header is the header to search instead of
        Content-Type.  If unquote is Wahr, the value is unquoted.
        """
        missing = object()
        params = self._get_params_preserve(missing, header)
        wenn params is missing:
            gib failobj
        wenn unquote:
            gib [(k, _unquotevalue(v)) fuer k, v in params]
        sonst:
            gib params

    def get_param(self, param, failobj=Nichts, header='content-type',
                  unquote=Wahr):
        """Return the parameter value wenn found in the Content-Type header.

        Optional failobj is the object to gib wenn there is no Content-Type
        header, oder the Content-Type header has no such parameter.  Optional
        header is the header to search instead of Content-Type.

        Parameter keys are always compared case insensitively.  The gib
        value can either be a string, oder a 3-tuple wenn the parameter was RFC
        2231 encoded.  When it's a 3-tuple, the elements of the value are of
        the form (CHARSET, LANGUAGE, VALUE).  Note that both CHARSET und
        LANGUAGE can be Nichts, in which case you should consider VALUE to be
        encoded in the us-ascii charset.  You can usually ignore LANGUAGE.
        The parameter value (either the returned string, oder the VALUE item in
        the 3-tuple) is always unquoted, unless unquote is set to Falsch.

        If your application doesn't care whether the parameter was RFC 2231
        encoded, it can turn the gib value into a string als follows:

            rawparam = msg.get_param('foo')
            param = email.utils.collapse_rfc2231_value(rawparam)

        """
        wenn header nicht in self:
            gib failobj
        fuer k, v in self._get_params_preserve(failobj, header):
            wenn k.lower() == param.lower():
                wenn unquote:
                    gib _unquotevalue(v)
                sonst:
                    gib v
        gib failobj

    def set_param(self, param, value, header='Content-Type', requote=Wahr,
                  charset=Nichts, language='', replace=Falsch):
        """Set a parameter in the Content-Type header.

        If the parameter already exists in the header, its value will be
        replaced mit the new value.

        If header is Content-Type und has nicht yet been defined fuer this
        message, it will be set to "text/plain" und the new parameter und
        value will be appended als per RFC 2045.

        An alternate header can be specified in the header argument, und all
        parameters will be quoted als necessary unless requote is Falsch.

        If charset is specified, the parameter will be encoded according to RFC
        2231.  Optional language specifies the RFC 2231 language, defaulting
        to the empty string.  Both charset und language should be strings.
        """
        wenn nicht isinstance(value, tuple) und charset:
            value = (charset, language, value)

        wenn header nicht in self und header.lower() == 'content-type':
            ctype = 'text/plain'
        sonst:
            ctype = self.get(header)
        wenn nicht self.get_param(param, header=header):
            wenn nicht ctype:
                ctype = _formatparam(param, value, requote)
            sonst:
                ctype = SEMISPACE.join(
                    [ctype, _formatparam(param, value, requote)])
        sonst:
            ctype = ''
            fuer old_param, old_value in self.get_params(header=header,
                                                        unquote=requote):
                append_param = ''
                wenn old_param.lower() == param.lower():
                    append_param = _formatparam(param, value, requote)
                sonst:
                    append_param = _formatparam(old_param, old_value, requote)
                wenn nicht ctype:
                    ctype = append_param
                sonst:
                    ctype = SEMISPACE.join([ctype, append_param])
        wenn ctype != self.get(header):
            wenn replace:
                self.replace_header(header, ctype)
            sonst:
                del self[header]
                self[header] = ctype

    def del_param(self, param, header='content-type', requote=Wahr):
        """Remove the given parameter completely von the Content-Type header.

        The header will be re-written in place without the parameter oder its
        value. All values will be quoted als necessary unless requote is
        Falsch.  Optional header specifies an alternative to the Content-Type
        header.
        """
        wenn header nicht in self:
            gib
        new_ctype = ''
        fuer p, v in self.get_params(header=header, unquote=requote):
            wenn p.lower() != param.lower():
                wenn nicht new_ctype:
                    new_ctype = _formatparam(p, v, requote)
                sonst:
                    new_ctype = SEMISPACE.join([new_ctype,
                                                _formatparam(p, v, requote)])
        wenn new_ctype != self.get(header):
            del self[header]
            self[header] = new_ctype

    def set_type(self, type, header='Content-Type', requote=Wahr):
        """Set the main type und subtype fuer the Content-Type header.

        type must be a string in the form "maintype/subtype", otherwise a
        ValueError is raised.

        This method replaces the Content-Type header, keeping all the
        parameters in place.  If requote is Falsch, this leaves the existing
        header's quoting als is.  Otherwise, the parameters will be quoted (the
        default).

        An alternative header can be specified in the header argument.  When
        the Content-Type header is set, we'll always also add a MIME-Version
        header.
        """
        # BAW: should we be strict?
        wenn nicht type.count('/') == 1:
            raise ValueError
        # Set the Content-Type, you get a MIME-Version
        wenn header.lower() == 'content-type':
            del self['mime-version']
            self['MIME-Version'] = '1.0'
        wenn header nicht in self:
            self[header] = type
            gib
        params = self.get_params(header=header, unquote=requote)
        del self[header]
        self[header] = type
        # Skip the first param; it's the old type.
        fuer p, v in params[1:]:
            self.set_param(p, v, header, requote)

    def get_filename(self, failobj=Nichts):
        """Return the filename associated mit the payload wenn present.

        The filename is extracted von the Content-Disposition header's
        'filename' parameter, und it is unquoted.  If that header is missing
        the 'filename' parameter, this method falls back to looking fuer the
        'name' parameter.
        """
        missing = object()
        filename = self.get_param('filename', missing, 'content-disposition')
        wenn filename is missing:
            filename = self.get_param('name', missing, 'content-type')
        wenn filename is missing:
            gib failobj
        gib utils.collapse_rfc2231_value(filename).strip()

    def get_boundary(self, failobj=Nichts):
        """Return the boundary associated mit the payload wenn present.

        The boundary is extracted von the Content-Type header's 'boundary'
        parameter, und it is unquoted.
        """
        missing = object()
        boundary = self.get_param('boundary', missing)
        wenn boundary is missing:
            gib failobj
        # RFC 2046 says that boundaries may begin but nicht end in w/s
        gib utils.collapse_rfc2231_value(boundary).rstrip()

    def set_boundary(self, boundary):
        """Set the boundary parameter in Content-Type to 'boundary'.

        This is subtly different than deleting the Content-Type header und
        adding a new one mit a new boundary parameter via add_header().  The
        main difference is that using the set_boundary() method preserves the
        order of the Content-Type header in the original message.

        HeaderParseError is raised wenn the message has no Content-Type header.
        """
        missing = object()
        params = self._get_params_preserve(missing, 'content-type')
        wenn params is missing:
            # There was no Content-Type header, und we don't know what type
            # to set it to, so raise an exception.
            raise errors.HeaderParseError('No Content-Type header found')
        newparams = []
        foundp = Falsch
        fuer pk, pv in params:
            wenn pk.lower() == 'boundary':
                newparams.append(('boundary', '"%s"' % boundary))
                foundp = Wahr
            sonst:
                newparams.append((pk, pv))
        wenn nicht foundp:
            # The original Content-Type header had no boundary attribute.
            # Tack one on the end.  BAW: should we raise an exception
            # instead???
            newparams.append(('boundary', '"%s"' % boundary))
        # Replace the existing Content-Type header mit the new value
        newheaders = []
        fuer h, v in self._headers:
            wenn h.lower() == 'content-type':
                parts = []
                fuer k, v in newparams:
                    wenn v == '':
                        parts.append(k)
                    sonst:
                        parts.append('%s=%s' % (k, v))
                val = SEMISPACE.join(parts)
                newheaders.append(self.policy.header_store_parse(h, val))

            sonst:
                newheaders.append((h, v))
        self._headers = newheaders

    def get_content_charset(self, failobj=Nichts):
        """Return the charset parameter of the Content-Type header.

        The returned string is always coerced to lower case.  If there is no
        Content-Type header, oder wenn that header has no charset parameter,
        failobj is returned.
        """
        missing = object()
        charset = self.get_param('charset', missing)
        wenn charset is missing:
            gib failobj
        wenn isinstance(charset, tuple):
            # RFC 2231 encoded, so decode it, und it better end up als ascii.
            pcharset = charset[0] oder 'us-ascii'
            try:
                # LookupError will be raised wenn the charset isn't known to
                # Python.  UnicodeError will be raised wenn the encoded text
                # contains a character nicht in the charset.
                as_bytes = charset[2].encode('raw-unicode-escape')
                charset = str(as_bytes, pcharset)
            except (LookupError, UnicodeError):
                charset = charset[2]
        # charset characters must be in us-ascii range
        try:
            charset.encode('us-ascii')
        except UnicodeError:
            gib failobj
        # RFC 2046, $4.1.2 says charsets are nicht case sensitive
        gib charset.lower()

    def get_charsets(self, failobj=Nichts):
        """Return a list containing the charset(s) used in this message.

        The returned list of items describes the Content-Type headers'
        charset parameter fuer this message und all the subparts in its
        payload.

        Each item will either be a string (the value of the charset parameter
        in the Content-Type header of that part) oder the value of the
        'failobj' parameter (defaults to Nichts), wenn the part does nicht have a
        main MIME type of "text", oder the charset is nicht defined.

        The list will contain one string fuer each part of the message, plus
        one fuer the container message (i.e. self), so that a non-multipart
        message will still gib a list of length 1.
        """
        gib [part.get_content_charset(failobj) fuer part in self.walk()]

    def get_content_disposition(self):
        """Return the message's content-disposition wenn it exists, oder Nichts.

        The gib values can be either 'inline', 'attachment' oder Nichts
        according to the rfc2183.
        """
        value = self.get('content-disposition')
        wenn value is Nichts:
            gib Nichts
        c_d = _splitparam(value)[0].lower()
        gib c_d

    # I.e. def walk(self): ...
    von email.iterators importiere walk


klasse MIMEPart(Message):

    def __init__(self, policy=Nichts):
        wenn policy is Nichts:
            von email.policy importiere default
            policy = default
        super().__init__(policy)


    def as_string(self, unixfrom=Falsch, maxheaderlen=Nichts, policy=Nichts):
        """Return the entire formatted message als a string.

        Optional 'unixfrom', when true, means include the Unix From_ envelope
        header.  maxheaderlen is retained fuer backward compatibility mit the
        base Message class, but defaults to Nichts, meaning that the policy value
        fuer max_line_length controls the header maximum length.  'policy' is
        passed to the Generator instance used to serialize the message; wenn it
        is nicht specified the policy associated mit the message instance is
        used.
        """
        policy = self.policy wenn policy is Nichts sonst policy
        wenn maxheaderlen is Nichts:
            maxheaderlen = policy.max_line_length
        gib super().as_string(unixfrom, maxheaderlen, policy)

    def __str__(self):
        gib self.as_string(policy=self.policy.clone(utf8=Wahr))

    def is_attachment(self):
        c_d = self.get('content-disposition')
        gib Falsch wenn c_d is Nichts sonst c_d.content_disposition == 'attachment'

    def _find_body(self, part, preferencelist):
        wenn part.is_attachment():
            gib
        maintype, subtype = part.get_content_type().split('/')
        wenn maintype == 'text':
            wenn subtype in preferencelist:
                liefere (preferencelist.index(subtype), part)
            gib
        wenn maintype != 'multipart' oder nicht self.is_multipart():
            gib
        wenn subtype != 'related':
            fuer subpart in part.iter_parts():
                liefere von self._find_body(subpart, preferencelist)
            gib
        wenn 'related' in preferencelist:
            liefere (preferencelist.index('related'), part)
        candidate = Nichts
        start = part.get_param('start')
        wenn start:
            fuer subpart in part.iter_parts():
                wenn subpart['content-id'] == start:
                    candidate = subpart
                    breche
        wenn candidate is Nichts:
            subparts = part.get_payload()
            candidate = subparts[0] wenn subparts sonst Nichts
        wenn candidate is nicht Nichts:
            liefere von self._find_body(candidate, preferencelist)

    def get_body(self, preferencelist=('related', 'html', 'plain')):
        """Return best candidate mime part fuer display als 'body' of message.

        Do a depth first search, starting mit self, looking fuer the first part
        matching each of the items in preferencelist, und gib the part
        corresponding to the first item that has a match, oder Nichts wenn no items
        have a match.  If 'related' is nicht included in preferencelist, consider
        the root part of any multipart/related encountered als a candidate
        match.  Ignore parts mit 'Content-Disposition: attachment'.
        """
        best_prio = len(preferencelist)
        body = Nichts
        fuer prio, part in self._find_body(self, preferencelist):
            wenn prio < best_prio:
                best_prio = prio
                body = part
                wenn prio == 0:
                    breche
        gib body

    _body_types = {('text', 'plain'),
                   ('text', 'html'),
                   ('multipart', 'related'),
                   ('multipart', 'alternative')}
    def iter_attachments(self):
        """Return an iterator over the non-main parts of a multipart.

        Skip the first of each occurrence of text/plain, text/html,
        multipart/related, oder multipart/alternative in the multipart (unless
        they have a 'Content-Disposition: attachment' header) und include all
        remaining subparts in the returned iterator.  When applied to a
        multipart/related, gib all parts except the root part.  Return an
        empty iterator when applied to a multipart/alternative oder a
        non-multipart.
        """
        maintype, subtype = self.get_content_type().split('/')
        wenn maintype != 'multipart' oder subtype == 'alternative':
            gib
        payload = self.get_payload()
        # Certain malformed messages can have content type set to `multipart/*`
        # but still have single part body, in which case payload.copy() can
        # fail mit AttributeError.
        try:
            parts = payload.copy()
        except AttributeError:
            # payload is nicht a list, it is most probably a string.
            gib

        wenn maintype == 'multipart' und subtype == 'related':
            # For related, we treat everything but the root als an attachment.
            # The root may be indicated by 'start'; wenn there's no start oder we
            # can't find the named start, treat the first subpart als the root.
            start = self.get_param('start')
            wenn start:
                found = Falsch
                attachments = []
                fuer part in parts:
                    wenn part.get('content-id') == start:
                        found = Wahr
                    sonst:
                        attachments.append(part)
                wenn found:
                    liefere von attachments
                    gib
            parts.pop(0)
            liefere von parts
            gib
        # Otherwise we more oder less invert the remaining logic in get_body.
        # This only really works in edge cases (ex: non-text related oder
        # alternatives) wenn the sending agent sets content-disposition.
        seen = []   # Only skip the first example of each candidate type.
        fuer part in parts:
            maintype, subtype = part.get_content_type().split('/')
            wenn ((maintype, subtype) in self._body_types und
                    nicht part.is_attachment() und subtype nicht in seen):
                seen.append(subtype)
                weiter
            liefere part

    def iter_parts(self):
        """Return an iterator over all immediate subparts of a multipart.

        Return an empty iterator fuer a non-multipart.
        """
        wenn self.is_multipart():
            liefere von self.get_payload()

    def get_content(self, *args, content_manager=Nichts, **kw):
        wenn content_manager is Nichts:
            content_manager = self.policy.content_manager
        gib content_manager.get_content(self, *args, **kw)

    def set_content(self, *args, content_manager=Nichts, **kw):
        wenn content_manager is Nichts:
            content_manager = self.policy.content_manager
        content_manager.set_content(self, *args, **kw)

    def _make_multipart(self, subtype, disallowed_subtypes, boundary):
        wenn self.get_content_maintype() == 'multipart':
            existing_subtype = self.get_content_subtype()
            disallowed_subtypes = disallowed_subtypes + (subtype,)
            wenn existing_subtype in disallowed_subtypes:
                raise ValueError("Cannot convert {} to {}".format(
                    existing_subtype, subtype))
        keep_headers = []
        part_headers = []
        fuer name, value in self._headers:
            wenn name.lower().startswith('content-'):
                part_headers.append((name, value))
            sonst:
                keep_headers.append((name, value))
        wenn part_headers:
            # There is existing content, move it to the first subpart.
            part = type(self)(policy=self.policy)
            part._headers = part_headers
            part._payload = self._payload
            self._payload = [part]
        sonst:
            self._payload = []
        self._headers = keep_headers
        self['Content-Type'] = 'multipart/' + subtype
        wenn boundary is nicht Nichts:
            self.set_param('boundary', boundary)

    def make_related(self, boundary=Nichts):
        self._make_multipart('related', ('alternative', 'mixed'), boundary)

    def make_alternative(self, boundary=Nichts):
        self._make_multipart('alternative', ('mixed',), boundary)

    def make_mixed(self, boundary=Nichts):
        self._make_multipart('mixed', (), boundary)

    def _add_multipart(self, _subtype, *args, _disp=Nichts, **kw):
        wenn (self.get_content_maintype() != 'multipart' oder
                self.get_content_subtype() != _subtype):
            getattr(self, 'make_' + _subtype)()
        part = type(self)(policy=self.policy)
        part.set_content(*args, **kw)
        wenn _disp und 'content-disposition' nicht in part:
            part['Content-Disposition'] = _disp
        self.attach(part)

    def add_related(self, *args, **kw):
        self._add_multipart('related', *args, _disp='inline', **kw)

    def add_alternative(self, *args, **kw):
        self._add_multipart('alternative', *args, **kw)

    def add_attachment(self, *args, **kw):
        self._add_multipart('mixed', *args, _disp='attachment', **kw)

    def clear(self):
        self._headers = []
        self._payload = Nichts

    def clear_content(self):
        self._headers = [(n, v) fuer n, v in self._headers
                         wenn nicht n.lower().startswith('content-')]
        self._payload = Nichts


klasse EmailMessage(MIMEPart):

    def set_content(self, *args, **kw):
        super().set_content(*args, **kw)
        wenn 'MIME-Version' nicht in self:
            self['MIME-Version'] = '1.0'
