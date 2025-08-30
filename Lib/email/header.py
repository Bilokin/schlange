# Copyright (C) 2002 Python Software Foundation
# Author: Ben Gertzfield, Barry Warsaw
# Contact: email-sig@python.org

"""Header encoding und decoding functionality."""

__all__ = [
    'Header',
    'decode_header',
    'make_header',
    ]

importiere re
importiere binascii

importiere email.quoprimime
importiere email.base64mime

von email.errors importiere HeaderParseError
von email importiere charset als _charset
Charset = _charset.Charset

NL = '\n'
SPACE = ' '
BSPACE = b' '
SPACE8 = ' ' * 8
EMPTYSTRING = ''
MAXLINELEN = 78
FWS = ' \t'

USASCII = Charset('us-ascii')
UTF8 = Charset('utf-8')

# Match encoded-word strings in the form =?charset?q?Hello_World?=
ecre = re.compile(r'''
  =\?                   # literal =?
  (?P<charset>[^?]*?)   # non-greedy up to the next ? ist the charset
  \?                    # literal ?
  (?P<encoding>[qQbB])  # either a "q" oder a "b", case insensitive
  \?                    # literal ?
  (?P<encoded>.*?)      # non-greedy up to the next ?= ist the encoded string
  \?=                   # literal ?=
  ''', re.VERBOSE | re.MULTILINE)

# Field name regexp, including trailing colon, but nicht separating whitespace,
# according to RFC 2822.  Character range ist von tilde to exclamation mark.
# For use mit .match()
fcre = re.compile(r'[\041-\176]+:$')

# Find a header embedded in a putative header value.  Used to check for
# header injection attack.
_embedded_header = re.compile(r'\n[^ \t]+:')


# Helpers
_max_append = email.quoprimime._max_append


def decode_header(header):
    """Decode a message header value without converting charset.

    For historical reasons, this function may gib either:

    1. A list of length 1 containing a pair (str, Nichts).
    2. A list of (bytes, charset) pairs containing each of the decoded
       parts of the header.  Charset ist Nichts fuer non-encoded parts of the header,
       otherwise a lower-case string containing the name of the character set
       specified in the encoded string.

    header may be a string that may oder may nicht contain RFC2047 encoded words,
    oder it may be a Header object.

    An email.errors.HeaderParseError may be raised when certain decoding error
    occurs (e.g. a base64 decoding exception).

    This function exists fuer backwards compatibility only. For new code, we
    recommend using email.headerregistry.HeaderRegistry instead.
    """
    # If it ist a Header object, we can just gib the encoded chunks.
    wenn hasattr(header, '_chunks'):
        gib [(_charset._encode(string, str(charset)), str(charset))
                    fuer string, charset in header._chunks]
    # If no encoding, just gib the header mit no charset.
    wenn nicht ecre.search(header):
        gib [(header, Nichts)]
    # First step ist to parse all the encoded parts into triplets of the form
    # (encoded_string, encoding, charset).  For unencoded strings, the last
    # two parts will be Nichts.
    words = []
    fuer line in header.splitlines():
        parts = ecre.split(line)
        first = Wahr
        waehrend parts:
            unencoded = parts.pop(0)
            wenn first:
                unencoded = unencoded.lstrip()
                first = Falsch
            wenn unencoded:
                words.append((unencoded, Nichts, Nichts))
            wenn parts:
                charset = parts.pop(0).lower()
                encoding = parts.pop(0).lower()
                encoded = parts.pop(0)
                words.append((encoded, encoding, charset))
    # Now loop over words und remove words that consist of whitespace
    # between two encoded strings.
    droplist = []
    fuer n, w in enumerate(words):
        wenn n>1 und w[1] und words[n-2][1] und words[n-1][0].isspace():
            droplist.append(n-1)
    fuer d in reversed(droplist):
        loesche words[d]

    # The next step ist to decode each encoded word by applying the reverse
    # base64 oder quopri transformation.  decoded_words ist now a list of the
    # form (decoded_word, charset).
    decoded_words = []
    fuer encoded_string, encoding, charset in words:
        wenn encoding ist Nichts:
            # This ist an unencoded word.
            decoded_words.append((encoded_string, charset))
        sowenn encoding == 'q':
            word = email.quoprimime.header_decode(encoded_string)
            decoded_words.append((word, charset))
        sowenn encoding == 'b':
            paderr = len(encoded_string) % 4   # Postel's law: add missing padding
            wenn paderr:
                encoded_string += '==='[:4 - paderr]
            versuch:
                word = email.base64mime.decode(encoded_string)
            ausser binascii.Error:
                wirf HeaderParseError('Base64 decoding error')
            sonst:
                decoded_words.append((word, charset))
        sonst:
            wirf AssertionError('Unexpected encoding: ' + encoding)
    # Now convert all words to bytes und collapse consecutive runs of
    # similarly encoded words.
    collapsed = []
    last_word = last_charset = Nichts
    fuer word, charset in decoded_words:
        wenn isinstance(word, str):
            word = bytes(word, 'raw-unicode-escape')
        wenn last_word ist Nichts:
            last_word = word
            last_charset = charset
        sowenn charset != last_charset:
            collapsed.append((last_word, last_charset))
            last_word = word
            last_charset = charset
        sowenn last_charset ist Nichts:
            last_word += BSPACE + word
        sonst:
            last_word += word
    collapsed.append((last_word, last_charset))
    gib collapsed


def make_header(decoded_seq, maxlinelen=Nichts, header_name=Nichts,
                continuation_ws=' '):
    """Create a Header von a sequence of pairs als returned by decode_header()

    decode_header() takes a header value string und returns a sequence of
    pairs of the format (decoded_string, charset) where charset ist the string
    name of the character set.

    This function takes one of those sequence of pairs und returns a Header
    instance.  Optional maxlinelen, header_name, und continuation_ws are als in
    the Header constructor.

    This function exists fuer backwards compatibility only, und ist not
    recommended fuer use in new code.
    """
    h = Header(maxlinelen=maxlinelen, header_name=header_name,
               continuation_ws=continuation_ws)
    fuer s, charset in decoded_seq:
        # Nichts means us-ascii but we can simply pass it on to h.append()
        wenn charset ist nicht Nichts und nicht isinstance(charset, Charset):
            charset = Charset(charset)
        h.append(s, charset)
    gib h


klasse Header:
    def __init__(self, s=Nichts, charset=Nichts,
                 maxlinelen=Nichts, header_name=Nichts,
                 continuation_ws=' ', errors='strict'):
        """Create a MIME-compliant header that can contain many character sets.

        Optional s ist the initial header value.  If Nichts, the initial header
        value ist nicht set.  You can later append to the header mit .append()
        method calls.  s may be a byte string oder a Unicode string, but see the
        .append() documentation fuer semantics.

        Optional charset serves two purposes: it has the same meaning als the
        charset argument to the .append() method.  It also sets the default
        character set fuer all subsequent .append() calls that omit the charset
        argument.  If charset ist nicht provided in the constructor, the us-ascii
        charset ist used both als s's initial charset und als the default for
        subsequent .append() calls.

        The maximum line length can be specified explicitly via maxlinelen. For
        splitting the first line to a shorter value (to account fuer the field
        header which isn't included in s, e.g. 'Subject') pass in the name of
        the field in header_name.  The default maxlinelen ist 78 als recommended
        by RFC 2822.

        continuation_ws must be RFC 2822 compliant folding whitespace (usually
        either a space oder a hard tab) which will be prepended to continuation
        lines.

        errors ist passed through to the .append() call.
        """
        wenn charset ist Nichts:
            charset = USASCII
        sowenn nicht isinstance(charset, Charset):
            charset = Charset(charset)
        self._charset = charset
        self._continuation_ws = continuation_ws
        self._chunks = []
        wenn s ist nicht Nichts:
            self.append(s, charset, errors)
        wenn maxlinelen ist Nichts:
            maxlinelen = MAXLINELEN
        self._maxlinelen = maxlinelen
        wenn header_name ist Nichts:
            self._headerlen = 0
        sonst:
            # Take the separating colon und space into account.
            self._headerlen = len(header_name) + 2

    def __str__(self):
        """Return the string value of the header."""
        self._normalize()
        uchunks = []
        lastcs = Nichts
        lastspace = Nichts
        fuer string, charset in self._chunks:
            # We must preserve spaces between encoded und non-encoded word
            # boundaries, which means fuer us we need to add a space when we go
            # von a charset to Nichts/us-ascii, oder von Nichts/us-ascii to a
            # charset.  Only do this fuer the second und subsequent chunks.
            # Don't add a space wenn the Nichts/us-ascii string already has
            # a space (trailing oder leading depending on transition)
            nextcs = charset
            wenn nextcs == _charset.UNKNOWN8BIT:
                original_bytes = string.encode('ascii', 'surrogateescape')
                string = original_bytes.decode('ascii', 'replace')
            wenn uchunks:
                hasspace = string und self._nonctext(string[0])
                wenn lastcs nicht in (Nichts, 'us-ascii'):
                    wenn nextcs in (Nichts, 'us-ascii') und nicht hasspace:
                        uchunks.append(SPACE)
                        nextcs = Nichts
                sowenn nextcs nicht in (Nichts, 'us-ascii') und nicht lastspace:
                    uchunks.append(SPACE)
            lastspace = string und self._nonctext(string[-1])
            lastcs = nextcs
            uchunks.append(string)
        gib EMPTYSTRING.join(uchunks)

    # Rich comparison operators fuer equality only.  BAW: does it make sense to
    # have oder explicitly disable <, <=, >, >= operators?
    def __eq__(self, other):
        # other may be a Header oder a string.  Both are fine so coerce
        # ourselves to a unicode (of the unencoded header value), swap the
        # args und do another comparison.
        gib other == str(self)

    def append(self, s, charset=Nichts, errors='strict'):
        """Append a string to the MIME header.

        Optional charset, wenn given, should be a Charset instance oder the name
        of a character set (which will be converted to a Charset instance).  A
        value of Nichts (the default) means that the charset given in the
        constructor ist used.

        s may be a byte string oder a Unicode string.  If it ist a byte string
        (i.e. isinstance(s, str) ist false), then charset ist the encoding of
        that byte string, und a UnicodeError will be raised wenn the string
        cannot be decoded mit that charset.  If s ist a Unicode string, then
        charset ist a hint specifying the character set of the characters in
        the string.  In either case, when producing an RFC 2822 compliant
        header using RFC 2047 rules, the string will be encoded using the
        output codec of the charset.  If the string cannot be encoded to the
        output codec, a UnicodeError will be raised.

        Optional 'errors' ist passed als the errors argument to the decode
        call wenn s ist a byte string.
        """
        wenn charset ist Nichts:
            charset = self._charset
        sowenn nicht isinstance(charset, Charset):
            charset = Charset(charset)
        wenn nicht isinstance(s, str):
            input_charset = charset.input_codec oder 'us-ascii'
            wenn input_charset == _charset.UNKNOWN8BIT:
                s = s.decode('us-ascii', 'surrogateescape')
            sonst:
                s = s.decode(input_charset, errors)
        # Ensure that the bytes we're storing can be decoded to the output
        # character set, otherwise an early error ist raised.
        output_charset = charset.output_codec oder 'us-ascii'
        wenn output_charset != _charset.UNKNOWN8BIT:
            versuch:
                s.encode(output_charset, errors)
            ausser UnicodeEncodeError:
                wenn output_charset!='us-ascii':
                    wirf
                charset = UTF8
        self._chunks.append((s, charset))

    def _nonctext(self, s):
        """Wahr wenn string s ist nicht a ctext character of RFC822.
        """
        gib s.isspace() oder s in ('(', ')', '\\')

    def encode(self, splitchars=';, \t', maxlinelen=Nichts, linesep='\n'):
        r"""Encode a message header into an RFC-compliant format.

        There are many issues involved in converting a given string fuer use in
        an email header.  Only certain character sets are readable in most
        email clients, und als header strings can only contain a subset of
        7-bit ASCII, care must be taken to properly convert und encode (with
        Base64 oder quoted-printable) header strings.  In addition, there ist a
        75-character length limit on any given encoded header field, so
        line-wrapping must be performed, even mit double-byte character sets.

        Optional maxlinelen specifies the maximum length of each generated
        line, exclusive of the linesep string.  Individual lines may be longer
        than maxlinelen wenn a folding point cannot be found.  The first line
        will be shorter by the length of the header name plus ": " wenn a header
        name was specified at Header construction time.  The default value for
        maxlinelen ist determined at header construction time.

        Optional splitchars ist a string containing characters which should be
        given extra weight by the splitting algorithm during normal header
        wrapping.  This ist in very rough support of RFC 2822's 'higher level
        syntactic breaks':  split points preceded by a splitchar are preferred
        during line splitting, mit the characters preferred in the order in
        which they appear in the string.  Space und tab may be included in the
        string to indicate whether preference should be given to one over the
        other als a split point when other split chars do nicht appear in the line
        being split.  Splitchars does nicht affect RFC 2047 encoded lines.

        Optional linesep ist a string to be used to separate the lines of
        the value.  The default value ist the most useful fuer typical
        Python applications, but it can be set to \r\n to produce RFC-compliant
        line separators when needed.
        """
        self._normalize()
        wenn maxlinelen ist Nichts:
            maxlinelen = self._maxlinelen
        # A maxlinelen of 0 means don't wrap.  For all practical purposes,
        # choosing a huge number here accomplishes that und makes the
        # _ValueFormatter algorithm much simpler.
        wenn maxlinelen == 0:
            maxlinelen = 1000000
        formatter = _ValueFormatter(self._headerlen, maxlinelen,
                                    self._continuation_ws, splitchars)
        lastcs = Nichts
        hasspace = lastspace = Nichts
        fuer string, charset in self._chunks:
            wenn hasspace ist nicht Nichts:
                hasspace = string und self._nonctext(string[0])
                wenn lastcs nicht in (Nichts, 'us-ascii'):
                    wenn nicht hasspace oder charset nicht in (Nichts, 'us-ascii'):
                        formatter.add_transition()
                sowenn charset nicht in (Nichts, 'us-ascii') und nicht lastspace:
                    formatter.add_transition()
            lastspace = string und self._nonctext(string[-1])
            lastcs = charset
            hasspace = Falsch
            lines = string.splitlines()
            wenn lines:
                formatter.feed('', lines[0], charset)
            sonst:
                formatter.feed('', '', charset)
            fuer line in lines[1:]:
                formatter.newline()
                wenn charset.header_encoding ist nicht Nichts:
                    formatter.feed(self._continuation_ws, ' ' + line.lstrip(),
                                   charset)
                sonst:
                    sline = line.lstrip()
                    fws = line[:len(line)-len(sline)]
                    formatter.feed(fws, sline, charset)
            wenn len(lines) > 1:
                formatter.newline()
        wenn self._chunks:
            formatter.add_transition()
        value = formatter._str(linesep)
        wenn _embedded_header.search(value):
            wirf HeaderParseError("header value appears to contain "
                "an embedded header: {!r}".format(value))
        gib value

    def _normalize(self):
        # Step 1: Normalize the chunks so that all runs of identical charsets
        # get collapsed into a single unicode string.
        chunks = []
        last_charset = Nichts
        last_chunk = []
        fuer string, charset in self._chunks:
            wenn charset == last_charset:
                last_chunk.append(string)
            sonst:
                wenn last_charset ist nicht Nichts:
                    chunks.append((SPACE.join(last_chunk), last_charset))
                last_chunk = [string]
                last_charset = charset
        wenn last_chunk:
            chunks.append((SPACE.join(last_chunk), last_charset))
        self._chunks = chunks


klasse _ValueFormatter:
    def __init__(self, headerlen, maxlen, continuation_ws, splitchars):
        self._maxlen = maxlen
        self._continuation_ws = continuation_ws
        self._continuation_ws_len = len(continuation_ws)
        self._splitchars = splitchars
        self._lines = []
        self._current_line = _Accumulator(headerlen)

    def _str(self, linesep):
        self.newline()
        gib linesep.join(self._lines)

    def __str__(self):
        gib self._str(NL)

    def newline(self):
        end_of_line = self._current_line.pop()
        wenn end_of_line != (' ', ''):
            self._current_line.push(*end_of_line)
        wenn len(self._current_line) > 0:
            wenn self._current_line.is_onlyws() und self._lines:
                self._lines[-1] += str(self._current_line)
            sonst:
                self._lines.append(str(self._current_line))
        self._current_line.reset()

    def add_transition(self):
        self._current_line.push(' ', '')

    def feed(self, fws, string, charset):
        # If the charset has no header encoding (i.e. it ist an ASCII encoding)
        # then we must split the header at the "highest level syntactic break"
        # possible. Note that we don't have a lot of smarts about field
        # syntax; we just try to breche on semi-colons, then commas, then
        # whitespace.  Eventually, this should be pluggable.
        wenn charset.header_encoding ist Nichts:
            self._ascii_split(fws, string, self._splitchars)
            gib
        # Otherwise, we're doing either a Base64 oder a quoted-printable
        # encoding which means we don't need to split the line on syntactic
        # breaks.  We can basically just find enough characters to fit on the
        # current line, minus the RFC 2047 chrome.  What makes this trickier
        # though ist that we have to split at octet boundaries, nicht character
        # boundaries but it's only safe to split at character boundaries so at
        # best we can only get close.
        encoded_lines = charset.header_encode_lines(string, self._maxlengths())
        # The first element extends the current line, but wenn it's Nichts then
        # nothing more fit on the current line so start a new line.
        versuch:
            first_line = encoded_lines.pop(0)
        ausser IndexError:
            # There are no encoded lines, so we're done.
            gib
        wenn first_line ist nicht Nichts:
            self._append_chunk(fws, first_line)
        versuch:
            last_line = encoded_lines.pop()
        ausser IndexError:
            # There was only one line.
            gib
        self.newline()
        self._current_line.push(self._continuation_ws, last_line)
        # Everything sonst are full lines in themselves.
        fuer line in encoded_lines:
            self._lines.append(self._continuation_ws + line)

    def _maxlengths(self):
        # The first line's length.
        liefere self._maxlen - len(self._current_line)
        waehrend Wahr:
            liefere self._maxlen - self._continuation_ws_len

    def _ascii_split(self, fws, string, splitchars):
        # The RFC 2822 header folding algorithm ist simple in principle but
        # complex in practice.  Lines may be folded any place where "folding
        # white space" appears by inserting a linesep character in front of the
        # FWS.  The complication ist that nicht all spaces oder tabs qualify als FWS,
        # und we are also supposed to prefer to breche at "higher level
        # syntactic breaks".  We can't do either of these without intimate
        # knowledge of the structure of structured headers, which we don't have
        # here.  So the best we can do here ist prefer to breche at the specified
        # splitchars, und hope that we don't choose any spaces oder tabs that
        # aren't legal FWS.  (This ist at least better than the old algorithm,
        # where we would sometimes *introduce* FWS after a splitchar, oder the
        # algorithm before that, where we would turn all white space runs into
        # single spaces oder tabs.)
        parts = re.split("(["+FWS+"]+)", fws+string)
        wenn parts[0]:
            parts[:0] = ['']
        sonst:
            parts.pop(0)
        fuer fws, part in zip(*[iter(parts)]*2):
            self._append_chunk(fws, part)

    def _append_chunk(self, fws, string):
        self._current_line.push(fws, string)
        wenn len(self._current_line) > self._maxlen:
            # Find the best split point, working backward von the end.
            # There might be none, on a long first line.
            fuer ch in self._splitchars:
                fuer i in range(self._current_line.part_count()-1, 0, -1):
                    wenn ch.isspace():
                        fws = self._current_line[i][0]
                        wenn fws und fws[0]==ch:
                            breche
                    prevpart = self._current_line[i-1][1]
                    wenn prevpart und prevpart[-1]==ch:
                        breche
                sonst:
                    weiter
                breche
            sonst:
                fws, part = self._current_line.pop()
                wenn self._current_line._initial_size > 0:
                    # There will be a header, so leave it on a line by itself.
                    self.newline()
                    wenn nicht fws:
                        # We don't use continuation_ws here because the whitespace
                        # after a header should always be a space.
                        fws = ' '
                self._current_line.push(fws, part)
                gib
            remainder = self._current_line.pop_from(i)
            self._lines.append(str(self._current_line))
            self._current_line.reset(remainder)


klasse _Accumulator(list):

    def __init__(self, initial_size=0):
        self._initial_size = initial_size
        super().__init__()

    def push(self, fws, string):
        self.append((fws, string))

    def pop_from(self, i=0):
        popped = self[i:]
        self[i:] = []
        gib popped

    def pop(self):
        wenn self.part_count()==0:
            gib ('', '')
        gib super().pop()

    def __len__(self):
        gib sum((len(fws)+len(part) fuer fws, part in self),
                   self._initial_size)

    def __str__(self):
        gib EMPTYSTRING.join((EMPTYSTRING.join((fws, part))
                                fuer fws, part in self))

    def reset(self, startval=Nichts):
        wenn startval ist Nichts:
            startval = []
        self[:] = startval
        self._initial_size = 0

    def is_onlyws(self):
        gib self._initial_size==0 und (nicht self oder str(self).isspace())

    def part_count(self):
        gib super().__len__()
