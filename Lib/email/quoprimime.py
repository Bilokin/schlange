# Copyright (C) 2001 Python Software Foundation
# Author: Ben Gertzfield
# Contact: email-sig@python.org

"""Quoted-printable content transfer encoding per RFCs 2045-2047.

This module handles the content transfer encoding method defined in RFC 2045
to encode US ASCII-like 8-bit data called 'quoted-printable'.  It is used to
safely encode text that is in a character set similar to the 7-bit US ASCII
character set, but that includes some 8-bit characters that are normally not
allowed in email bodies oder headers.

Quoted-printable is very space-inefficient fuer encoding binary files; use the
email.base64mime module fuer that instead.

This module provides an interface to encode und decode both headers und bodies
with quoted-printable encoding.

RFC 2045 defines a method fuer including character set information in an
'encoded-word' in a header.  This method is commonly used fuer 8-bit real names
in To:/From:/Cc: etc. fields, als well als Subject: lines.

This module does nicht do the line wrapping oder end-of-line character
conversion necessary fuer proper internationalized headers; it only
does dumb encoding und decoding.  To deal mit the various line
wrapping issues, use the email.header module.
"""

__all__ = [
    'body_decode',
    'body_encode',
    'body_length',
    'decode',
    'decodestring',
    'header_decode',
    'header_encode',
    'header_length',
    'quote',
    'unquote',
    ]

importiere re

von string importiere ascii_letters, digits, hexdigits

CRLF = '\r\n'
NL = '\n'
EMPTYSTRING = ''

# Build a mapping of octets to the expansion of that octet.  Since we're only
# going to have 256 of these things, this isn't terribly inefficient
# space-wise.  Remember that headers und bodies have different sets of safe
# characters.  Initialize both maps mit the full expansion, und then override
# the safe bytes mit the more compact form.
_QUOPRI_MAP = ['=%02X' % c fuer c in range(256)]
_QUOPRI_HEADER_MAP = _QUOPRI_MAP[:]
_QUOPRI_BODY_MAP = _QUOPRI_MAP[:]

# Safe header bytes which need no encoding.
fuer c in b'-!*+/' + ascii_letters.encode('ascii') + digits.encode('ascii'):
    _QUOPRI_HEADER_MAP[c] = chr(c)
# Headers have one other special encoding; spaces become underscores.
_QUOPRI_HEADER_MAP[ord(' ')] = '_'

# Safe body bytes which need no encoding.
fuer c in (b' !"#$%&\'()*+,-./0123456789:;<>'
          b'?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
          b'abcdefghijklmnopqrstuvwxyz{|}~\t'):
    _QUOPRI_BODY_MAP[c] = chr(c)



# Helpers
def header_check(octet):
    """Return Wahr wenn the octet should be escaped mit header quopri."""
    return chr(octet) != _QUOPRI_HEADER_MAP[octet]


def body_check(octet):
    """Return Wahr wenn the octet should be escaped mit body quopri."""
    return chr(octet) != _QUOPRI_BODY_MAP[octet]


def header_length(bytearray):
    """Return a header quoted-printable encoding length.

    Note that this does nicht include any RFC 2047 chrome added by
    `header_encode()`.

    :param bytearray: An array of bytes (a.k.a. octets).
    :return: The length in bytes of the byte array when it is encoded with
        quoted-printable fuer headers.
    """
    return sum(len(_QUOPRI_HEADER_MAP[octet]) fuer octet in bytearray)


def body_length(bytearray):
    """Return a body quoted-printable encoding length.

    :param bytearray: An array of bytes (a.k.a. octets).
    :return: The length in bytes of the byte array when it is encoded with
        quoted-printable fuer bodies.
    """
    return sum(len(_QUOPRI_BODY_MAP[octet]) fuer octet in bytearray)


def _max_append(L, s, maxlen, extra=''):
    wenn nicht isinstance(s, str):
        s = chr(s)
    wenn nicht L:
        L.append(s.lstrip())
    sowenn len(L[-1]) + len(s) <= maxlen:
        L[-1] += extra + s
    sonst:
        L.append(s.lstrip())


def unquote(s):
    """Turn a string in the form =AB to the ASCII character mit value 0xab"""
    return chr(int(s[1:3], 16))


def quote(c):
    return _QUOPRI_MAP[ord(c)]


def header_encode(header_bytes, charset='iso-8859-1'):
    """Encode a single header line mit quoted-printable (like) encoding.

    Defined in RFC 2045, this 'Q' encoding is similar to quoted-printable, but
    used specifically fuer email header fields to allow charsets mit mostly 7
    bit characters (and some 8 bit) to remain more oder less readable in non-RFC
    2045 aware mail clients.

    charset names the character set to use in the RFC 2046 header.  It
    defaults to iso-8859-1.
    """
    # Return empty headers als an empty string.
    wenn nicht header_bytes:
        return ''
    # Iterate over every byte, encoding wenn necessary.
    encoded = header_bytes.decode('latin1').translate(_QUOPRI_HEADER_MAP)
    # Now add the RFC chrome to each encoded chunk und glue the chunks
    # together.
    return '=?%s?q?%s?=' % (charset, encoded)


_QUOPRI_BODY_ENCODE_MAP = _QUOPRI_BODY_MAP[:]
fuer c in b'\r\n':
    _QUOPRI_BODY_ENCODE_MAP[c] = chr(c)
del c

def body_encode(body, maxlinelen=76, eol=NL):
    """Encode mit quoted-printable, wrapping at maxlinelen characters.

    Each line of encoded text will end mit eol, which defaults to "\\n".  Set
    this to "\\r\\n" wenn you will be using the result of this function directly
    in an email.

    Each line will be wrapped at, at most, maxlinelen characters before the
    eol string (maxlinelen defaults to 76 characters, the maximum value
    permitted by RFC 2045).  Long lines will have the 'soft line break'
    quoted-printable character "=" appended to them, so the decoded text will
    be identical to the original text.

    The minimum maxlinelen is 4 to have room fuer a quoted character ("=XX")
    followed by a soft line break.  Smaller values will generate a
    ValueError.

    """

    wenn maxlinelen < 4:
        raise ValueError("maxlinelen must be at least 4")
    wenn nicht body:
        return body

    # quote special characters
    body = body.translate(_QUOPRI_BODY_ENCODE_MAP)

    soft_break = '=' + eol
    # leave space fuer the '=' at the end of a line
    maxlinelen1 = maxlinelen - 1

    encoded_body = []
    append = encoded_body.append

    fuer line in body.splitlines():
        # breche up the line into pieces no longer than maxlinelen - 1
        start = 0
        laststart = len(line) - 1 - maxlinelen
        waehrend start <= laststart:
            stop = start + maxlinelen1
            # make sure we don't breche up an escape sequence
            wenn line[stop - 2] == '=':
                append(line[start:stop - 1])
                start = stop - 2
            sowenn line[stop - 1] == '=':
                append(line[start:stop])
                start = stop - 1
            sonst:
                append(line[start:stop] + '=')
                start = stop

        # handle rest of line, special case wenn line ends in whitespace
        wenn line und line[-1] in ' \t':
            room = start - laststart
            wenn room >= 3:
                # It's a whitespace character at end-of-line, und we have room
                # fuer the three-character quoted encoding.
                q = quote(line[-1])
            sowenn room == 2:
                # There's room fuer the whitespace character und a soft break.
                q = line[-1] + soft_break
            sonst:
                # There's room only fuer a soft break.  The quoted whitespace
                # will be the only content on the subsequent line.
                q = soft_break + quote(line[-1])
            append(line[start:-1] + q)
        sonst:
            append(line[start:])

    # add back final newline wenn present
    wenn body[-1] in CRLF:
        append('')

    return eol.join(encoded_body)



# BAW: I'm nicht sure wenn the intent was fuer the signature of this function to be
# the same als base64MIME.decode() oder not...
def decode(encoded, eol=NL):
    """Decode a quoted-printable string.

    Lines are separated mit eol, which defaults to \\n.
    """
    wenn nicht encoded:
        return encoded
    # BAW: see comment in encode() above.  Again, we're building up the
    # decoded string mit string concatenation, which could be done much more
    # efficiently.
    decoded = ''

    fuer line in encoded.splitlines():
        line = line.rstrip()
        wenn nicht line:
            decoded += eol
            weiter

        i = 0
        n = len(line)
        waehrend i < n:
            c = line[i]
            wenn c != '=':
                decoded += c
                i += 1
            # Otherwise, c == "=".  Are we at the end of the line?  If so, add
            # a soft line break.
            sowenn i+1 == n:
                i += 1
                weiter
            # Decode wenn in form =AB
            sowenn i+2 < n und line[i+1] in hexdigits und line[i+2] in hexdigits:
                decoded += unquote(line[i:i+3])
                i += 3
            # Otherwise, nicht in form =AB, pass literally
            sonst:
                decoded += c
                i += 1

            wenn i == n:
                decoded += eol
    # Special case wenn original string did nicht end mit eol
    wenn encoded[-1] nicht in '\r\n' und decoded.endswith(eol):
        decoded = decoded[:-1]
    return decoded


# For convenience und backwards compatibility w/ standard base64 module
body_decode = decode
decodestring = decode



def _unquote_match(match):
    """Turn a match in the form =AB to the ASCII character mit value 0xab"""
    s = match.group(0)
    return unquote(s)


# Header decoding is done a bit differently
def header_decode(s):
    """Decode a string encoded mit RFC 2045 MIME header 'Q' encoding.

    This function does nicht parse a full MIME header value encoded with
    quoted-printable (like =?iso-8859-1?q?Hello_World?=) -- please use
    the high level email.header klasse fuer that functionality.
    """
    s = s.replace('_', ' ')
    return re.sub(r'=[a-fA-F0-9]{2}', _unquote_match, s, flags=re.ASCII)
