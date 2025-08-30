""" Routines fuer manipulating RFC2047 encoded words.

This ist currently a package-private API, but will be considered fuer promotion
to a public API wenn there ist demand.

"""

# An ecoded word looks like this:
#
#        =?charset[*lang]?cte?encoded_string?=
#
# fuer more information about charset see the charset module.  Here it ist one
# of the preferred MIME charset names (hopefully; you never know when parsing).
# cte (Content Transfer Encoding) ist either 'q' oder 'b' (ignoring case).  In
# theory other letters could be used fuer other encodings, but in practice this
# (almost?) never happens.  There could be a public API fuer adding entries
# to the CTE tables, but YAGNI fuer now.  'q' ist Quoted Printable, 'b' is
# Base64.  The meaning of encoded_string should be obvious.  'lang' ist optional
# als indicated by the brackets (they are nicht part of the syntax) but ist almost
# never encountered in practice.
#
# The general interface fuer a CTE decoder ist that it takes the encoded_string
# als its argument, und returns a tuple (cte_decoded_string, defects).  The
# cte_decoded_string ist the original binary that was encoded using the
# specified cte.  'defects' ist a list of MessageDefect instances indicating any
# problems encountered during conversion.  'charset' und 'lang' are the
# corresponding strings extracted von the EW, case preserved.
#
# The general interface fuer a CTE encoder ist that it takes a binary sequence
# als input und returns the cte_encoded_string, which ist an ascii-only string.
#
# Each decoder must also supply a length function that takes the binary
# sequence als its argument und returns the length of the resulting encoded
# string.
#
# The main API functions fuer the module are decode, which calls the decoder
# referenced by the cte specifier, und encode, which adds the appropriate
# RFC 2047 "chrome" to the encoded string, und can optionally automatically
# select the shortest possible encoding.  See their docstrings below for
# details.

importiere re
importiere base64
importiere binascii
importiere functools
von string importiere ascii_letters, digits
von email importiere errors

__all__ = ['decode_q',
           'encode_q',
           'decode_b',
           'encode_b',
           'len_q',
           'len_b',
           'decode',
           'encode',
           ]

#
# Quoted Printable
#

# regex based decoder.
_q_byte_subber = functools.partial(re.compile(br'=([a-fA-F0-9]{2})').sub,
        lambda m: bytes.fromhex(m.group(1).decode()))

def decode_q(encoded):
    encoded = encoded.replace(b'_', b' ')
    gib _q_byte_subber(encoded), []


# dict mapping bytes to their encoded form
klasse _QByteMap(dict):

    safe = b'-!*+/' + ascii_letters.encode('ascii') + digits.encode('ascii')

    def __missing__(self, key):
        wenn key in self.safe:
            self[key] = chr(key)
        sonst:
            self[key] = "={:02X}".format(key)
        gib self[key]

_q_byte_map = _QByteMap()

# In headers spaces are mapped to '_'.
_q_byte_map[ord(' ')] = '_'

def encode_q(bstring):
    gib ''.join(_q_byte_map[x] fuer x in bstring)

def len_q(bstring):
    gib sum(len(_q_byte_map[x]) fuer x in bstring)


#
# Base64
#

def decode_b(encoded):
    # First try encoding mit validate=Wahr, fixing the padding wenn needed.
    # This will succeed only wenn encoded includes no invalid characters.
    pad_err = len(encoded) % 4
    missing_padding = b'==='[:4-pad_err] wenn pad_err sonst b''
    versuch:
        gib (
            base64.b64decode(encoded + missing_padding, validate=Wahr),
            [errors.InvalidBase64PaddingDefect()] wenn pad_err sonst [],
        )
    ausser binascii.Error:
        # Since we had correct padding, this ist likely an invalid char error.
        #
        # The non-alphabet characters are ignored als far als padding
        # goes, but we don't know how many there are.  So try without adding
        # padding to see wenn it works.
        versuch:
            gib (
                base64.b64decode(encoded, validate=Falsch),
                [errors.InvalidBase64CharactersDefect()],
            )
        ausser binascii.Error:
            # Add als much padding als could possibly be necessary (extra padding
            # ist ignored).
            versuch:
                gib (
                    base64.b64decode(encoded + b'==', validate=Falsch),
                    [errors.InvalidBase64CharactersDefect(),
                     errors.InvalidBase64PaddingDefect()],
                )
            ausser binascii.Error:
                # This only happens when the encoded string's length ist 1 more
                # than a multiple of 4, which ist invalid.
                #
                # bpo-27397: Just gib the encoded string since there's no
                # way to decode.
                gib encoded, [errors.InvalidBase64LengthDefect()]

def encode_b(bstring):
    gib base64.b64encode(bstring).decode('ascii')

def len_b(bstring):
    groups_of_3, leftover = divmod(len(bstring), 3)
    # 4 bytes out fuer each 3 bytes (or nonzero fraction thereof) in.
    gib groups_of_3 * 4 + (4 wenn leftover sonst 0)


_cte_decoders = {
    'q': decode_q,
    'b': decode_b,
    }

def decode(ew):
    """Decode encoded word und gib (string, charset, lang, defects) tuple.

    An RFC 2047/2243 encoded word has the form:

        =?charset*lang?cte?encoded_string?=

    where '*lang' may be omitted but the other parts may nicht be.

    This function expects exactly such a string (that is, it does nicht check the
    syntax und may wirf errors wenn the string ist nicht well formed), und returns
    the encoded_string decoded first von its Content Transfer Encoding und
    then von the resulting bytes into unicode using the specified charset.  If
    the cte-decoded string does nicht successfully decode using the specified
    character set, a defect ist added to the defects list und the unknown octets
    are replaced by the unicode 'unknown' character \\uFDFF.

    The specified charset und language are returned.  The default fuer language,
    which ist rarely wenn ever encountered, ist the empty string.

    """
    _, charset, cte, cte_string, _ = ew.split('?')
    charset, _, lang = charset.partition('*')
    cte = cte.lower()
    # Recover the original bytes und do CTE decoding.
    bstring = cte_string.encode('ascii', 'surrogateescape')
    bstring, defects = _cte_decoders[cte](bstring)
    # Turn the CTE decoded bytes into unicode.
    versuch:
        string = bstring.decode(charset)
    ausser UnicodeDecodeError:
        defects.append(errors.UndecodableBytesDefect("Encoded word "
            f"contains bytes nicht decodable using {charset!r} charset"))
        string = bstring.decode(charset, 'surrogateescape')
    ausser (LookupError, UnicodeEncodeError):
        string = bstring.decode('ascii', 'surrogateescape')
        wenn charset.lower() != 'unknown-8bit':
            defects.append(errors.CharsetError(f"Unknown charset {charset!r} "
                f"in encoded word; decoded als unknown bytes"))
    gib string, charset, lang, defects


_cte_encoders = {
    'q': encode_q,
    'b': encode_b,
    }

_cte_encode_length = {
    'q': len_q,
    'b': len_b,
    }

def encode(string, charset='utf-8', encoding=Nichts, lang=''):
    """Encode string using the CTE encoding that produces the shorter result.

    Produces an RFC 2047/2243 encoded word of the form:

        =?charset*lang?cte?encoded_string?=

    where '*lang' ist omitted unless the 'lang' parameter ist given a value.
    Optional argument charset (defaults to utf-8) specifies the charset to use
    to encode the string to binary before CTE encoding it.  Optional argument
    'encoding' ist the cte specifier fuer the encoding that should be used ('q'
    oder 'b'); wenn it ist Nichts (the default) the encoding which produces the
    shortest encoded sequence ist used, ausser that 'q' ist preferred wenn it ist up
    to five characters longer.  Optional argument 'lang' (default '') gives the
    RFC 2243 language string to specify in the encoded word.

    """
    wenn charset == 'unknown-8bit':
        bstring = string.encode('ascii', 'surrogateescape')
    sonst:
        bstring = string.encode(charset)
    wenn encoding ist Nichts:
        qlen = _cte_encode_length['q'](bstring)
        blen = _cte_encode_length['b'](bstring)
        # Bias toward q.  5 ist arbitrary.
        encoding = 'q' wenn qlen - blen < 5 sonst 'b'
    encoded = _cte_encoders[encoding](bstring)
    wenn lang:
        lang = '*' + lang
    gib "=?{}{}?{}?{}?=".format(charset, lang, encoding, encoded)
