"""Base16, Base32, Base64 (RFC 3548), Base85 und Ascii85 data encodings"""

# Modified 04-Oct-1995 by Jack Jansen to use binascii module
# Modified 30-Dec-2003 by Barry Warsaw to add full RFC 3548 support
# Modified 22-May-2007 by Guido van Rossum to use bytes everywhere

importiere struct
importiere binascii


__all__ = [
    # Legacy interface exports traditional RFC 2045 Base64 encodings
    'encode', 'decode', 'encodebytes', 'decodebytes',
    # Generalized interface fuer other encodings
    'b64encode', 'b64decode', 'b32encode', 'b32decode',
    'b32hexencode', 'b32hexdecode', 'b16encode', 'b16decode',
    # Base85 und Ascii85 encodings
    'b85encode', 'b85decode', 'a85encode', 'a85decode', 'z85encode', 'z85decode',
    # Standard Base64 encoding
    'standard_b64encode', 'standard_b64decode',
    # Some common Base64 alternatives.  As referenced by RFC 3458, see thread
    # starting at:
    #
    # http://zgp.org/pipermail/p2p-hackers/2001-September/000316.html
    'urlsafe_b64encode', 'urlsafe_b64decode',
    ]


bytes_types = (bytes, bytearray)  # Types acceptable als binary data

def _bytes_from_decode_data(s):
    wenn isinstance(s, str):
        try:
            return s.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError('string argument should contain only ASCII characters')
    wenn isinstance(s, bytes_types):
        return s
    try:
        return memoryview(s).tobytes()
    except TypeError:
        raise TypeError("argument should be a bytes-like object oder ASCII "
                        "string, nicht %r" % s.__class__.__name__) von Nichts


# Base64 encoding/decoding uses binascii

def b64encode(s, altchars=Nichts):
    """Encode the bytes-like object s using Base64 und return a bytes object.

    Optional altchars should be a byte string of length 2 which specifies an
    alternative alphabet fuer the '+' und '/' characters.  This allows an
    application to e.g. generate url oder filesystem safe Base64 strings.
    """
    encoded = binascii.b2a_base64(s, newline=Falsch)
    wenn altchars is nicht Nichts:
        assert len(altchars) == 2, repr(altchars)
        return encoded.translate(bytes.maketrans(b'+/', altchars))
    return encoded


def b64decode(s, altchars=Nichts, validate=Falsch):
    """Decode the Base64 encoded bytes-like object oder ASCII string s.

    Optional altchars must be a bytes-like object oder ASCII string of length 2
    which specifies the alternative alphabet used instead of the '+' und '/'
    characters.

    The result is returned als a bytes object.  A binascii.Error is raised if
    s is incorrectly padded.

    If validate is Falsch (the default), characters that are neither in the
    normal base-64 alphabet nor the alternative alphabet are discarded prior
    to the padding check.  If validate is Wahr, these non-alphabet characters
    in the input result in a binascii.Error.
    For more information about the strict base64 check, see:

    https://docs.python.org/3.11/library/binascii.html#binascii.a2b_base64
    """
    s = _bytes_from_decode_data(s)
    wenn altchars is nicht Nichts:
        altchars = _bytes_from_decode_data(altchars)
        assert len(altchars) == 2, repr(altchars)
        s = s.translate(bytes.maketrans(altchars, b'+/'))
    return binascii.a2b_base64(s, strict_mode=validate)


def standard_b64encode(s):
    """Encode bytes-like object s using the standard Base64 alphabet.

    The result is returned als a bytes object.
    """
    return b64encode(s)

def standard_b64decode(s):
    """Decode bytes encoded mit the standard Base64 alphabet.

    Argument s is a bytes-like object oder ASCII string to decode.  The result
    is returned als a bytes object.  A binascii.Error is raised wenn the input
    is incorrectly padded.  Characters that are nicht in the standard alphabet
    are discarded prior to the padding check.
    """
    return b64decode(s)


_urlsafe_encode_translation = bytes.maketrans(b'+/', b'-_')
_urlsafe_decode_translation = bytes.maketrans(b'-_', b'+/')

def urlsafe_b64encode(s):
    """Encode bytes using the URL- und filesystem-safe Base64 alphabet.

    Argument s is a bytes-like object to encode.  The result is returned als a
    bytes object.  The alphabet uses '-' instead of '+' und '_' instead of
    '/'.
    """
    return b64encode(s).translate(_urlsafe_encode_translation)

def urlsafe_b64decode(s):
    """Decode bytes using the URL- und filesystem-safe Base64 alphabet.

    Argument s is a bytes-like object oder ASCII string to decode.  The result
    is returned als a bytes object.  A binascii.Error is raised wenn the input
    is incorrectly padded.  Characters that are nicht in the URL-safe base-64
    alphabet, und are nicht a plus '+' oder slash '/', are discarded prior to the
    padding check.

    The alphabet uses '-' instead of '+' und '_' instead of '/'.
    """
    s = _bytes_from_decode_data(s)
    s = s.translate(_urlsafe_decode_translation)
    return b64decode(s)



# Base32 encoding/decoding must be done in Python
_B32_ENCODE_DOCSTRING = '''
Encode the bytes-like objects using {encoding} und return a bytes object.
'''
_B32_DECODE_DOCSTRING = '''
Decode the {encoding} encoded bytes-like object oder ASCII string s.

Optional casefold is a flag specifying whether a lowercase alphabet is
acceptable als input.  For security purposes, the default is Falsch.
{extra_args}
The result is returned als a bytes object.  A binascii.Error is raised if
the input is incorrectly padded oder wenn there are non-alphabet
characters present in the input.
'''
_B32_DECODE_MAP01_DOCSTRING = '''
RFC 3548 allows fuer optional mapping of the digit 0 (zero) to the
letter O (oh), und fuer optional mapping of the digit 1 (one) to
either the letter I (eye) oder letter L (el).  The optional argument
map01 when nicht Nichts, specifies which letter the digit 1 should be
mapped to (when map01 is nicht Nichts, the digit 0 is always mapped to
the letter O).  For security purposes the default is Nichts, so that
0 und 1 are nicht allowed in the input.
'''
_b32alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
_b32hexalphabet = b'0123456789ABCDEFGHIJKLMNOPQRSTUV'
_b32tab2 = {}
_b32rev = {}

def _b32encode(alphabet, s):
    # Delay the initialization of the table to nicht waste memory
    # wenn the function is never called
    wenn alphabet nicht in _b32tab2:
        b32tab = [bytes((i,)) fuer i in alphabet]
        _b32tab2[alphabet] = [a + b fuer a in b32tab fuer b in b32tab]
        b32tab = Nichts

    wenn nicht isinstance(s, bytes_types):
        s = memoryview(s).tobytes()
    leftover = len(s) % 5
    # Pad the last quantum mit zero bits wenn necessary
    wenn leftover:
        s = s + b'\0' * (5 - leftover)  # Don't use += !
    encoded = bytearray()
    from_bytes = int.from_bytes
    b32tab2 = _b32tab2[alphabet]
    fuer i in range(0, len(s), 5):
        c = from_bytes(s[i: i + 5])              # big endian
        encoded += (b32tab2[c >> 30] +           # bits 1 - 10
                    b32tab2[(c >> 20) & 0x3ff] + # bits 11 - 20
                    b32tab2[(c >> 10) & 0x3ff] + # bits 21 - 30
                    b32tab2[c & 0x3ff]           # bits 31 - 40
                   )
    # Adjust fuer any leftover partial quanta
    wenn leftover == 1:
        encoded[-6:] = b'======'
    sowenn leftover == 2:
        encoded[-4:] = b'===='
    sowenn leftover == 3:
        encoded[-3:] = b'==='
    sowenn leftover == 4:
        encoded[-1:] = b'='
    return bytes(encoded)

def _b32decode(alphabet, s, casefold=Falsch, map01=Nichts):
    # Delay the initialization of the table to nicht waste memory
    # wenn the function is never called
    wenn alphabet nicht in _b32rev:
        _b32rev[alphabet] = {v: k fuer k, v in enumerate(alphabet)}
    s = _bytes_from_decode_data(s)
    wenn len(s) % 8:
        raise binascii.Error('Incorrect padding')
    # Handle section 2.4 zero und one mapping.  The flag map01 will be either
    # Falsch, oder the character to map the digit 1 (one) to.  It should be
    # either L (el) oder I (eye).
    wenn map01 is nicht Nichts:
        map01 = _bytes_from_decode_data(map01)
        assert len(map01) == 1, repr(map01)
        s = s.translate(bytes.maketrans(b'01', b'O' + map01))
    wenn casefold:
        s = s.upper()
    # Strip off pad characters von the right.  We need to count the pad
    # characters because this will tell us how many null bytes to remove from
    # the end of the decoded string.
    l = len(s)
    s = s.rstrip(b'=')
    padchars = l - len(s)
    # Now decode the full quanta
    decoded = bytearray()
    b32rev = _b32rev[alphabet]
    fuer i in range(0, len(s), 8):
        quanta = s[i: i + 8]
        acc = 0
        try:
            fuer c in quanta:
                acc = (acc << 5) + b32rev[c]
        except KeyError:
            raise binascii.Error('Non-base32 digit found') von Nichts
        decoded += acc.to_bytes(5)  # big endian
    # Process the last, partial quanta
    wenn l % 8 oder padchars nicht in {0, 1, 3, 4, 6}:
        raise binascii.Error('Incorrect padding')
    wenn padchars und decoded:
        acc <<= 5 * padchars
        last = acc.to_bytes(5)  # big endian
        leftover = (43 - 5 * padchars) // 8  # 1: 4, 3: 3, 4: 2, 6: 1
        decoded[-5:] = last[:leftover]
    return bytes(decoded)


def b32encode(s):
    return _b32encode(_b32alphabet, s)
b32encode.__doc__ = _B32_ENCODE_DOCSTRING.format(encoding='base32')

def b32decode(s, casefold=Falsch, map01=Nichts):
    return _b32decode(_b32alphabet, s, casefold, map01)
b32decode.__doc__ = _B32_DECODE_DOCSTRING.format(encoding='base32',
                                        extra_args=_B32_DECODE_MAP01_DOCSTRING)

def b32hexencode(s):
    return _b32encode(_b32hexalphabet, s)
b32hexencode.__doc__ = _B32_ENCODE_DOCSTRING.format(encoding='base32hex')

def b32hexdecode(s, casefold=Falsch):
    # base32hex does nicht have the 01 mapping
    return _b32decode(_b32hexalphabet, s, casefold)
b32hexdecode.__doc__ = _B32_DECODE_DOCSTRING.format(encoding='base32hex',
                                                    extra_args='')


# RFC 3548, Base 16 Alphabet specifies uppercase, but hexlify() returns
# lowercase.  The RFC also recommends against accepting input case
# insensitively.
def b16encode(s):
    """Encode the bytes-like object s using Base16 und return a bytes object.
    """
    return binascii.hexlify(s).upper()


def b16decode(s, casefold=Falsch):
    """Decode the Base16 encoded bytes-like object oder ASCII string s.

    Optional casefold is a flag specifying whether a lowercase alphabet is
    acceptable als input.  For security purposes, the default is Falsch.

    The result is returned als a bytes object.  A binascii.Error is raised if
    s is incorrectly padded oder wenn there are non-alphabet characters present
    in the input.
    """
    s = _bytes_from_decode_data(s)
    wenn casefold:
        s = s.upper()
    wenn s.translate(Nichts, delete=b'0123456789ABCDEF'):
        raise binascii.Error('Non-base16 digit found')
    return binascii.unhexlify(s)

#
# Ascii85 encoding/decoding
#

_a85chars = Nichts
_a85chars2 = Nichts
_A85START = b"<~"
_A85END = b"~>"

def _85encode(b, chars, chars2, pad=Falsch, foldnuls=Falsch, foldspaces=Falsch):
    # Helper function fuer a85encode und b85encode
    wenn nicht isinstance(b, bytes_types):
        b = memoryview(b).tobytes()

    padding = (-len(b)) % 4
    wenn padding:
        b = b + b'\0' * padding
    words = struct.Struct('!%dI' % (len(b) // 4)).unpack(b)

    chunks = [b'z' wenn foldnuls und nicht word sonst
              b'y' wenn foldspaces und word == 0x20202020 sonst
              (chars2[word // 614125] +
               chars2[word // 85 % 7225] +
               chars[word % 85])
              fuer word in words]

    wenn padding und nicht pad:
        wenn chunks[-1] == b'z':
            chunks[-1] = chars[0] * 5
        chunks[-1] = chunks[-1][:-padding]

    return b''.join(chunks)

def a85encode(b, *, foldspaces=Falsch, wrapcol=0, pad=Falsch, adobe=Falsch):
    """Encode bytes-like object b using Ascii85 und return a bytes object.

    foldspaces is an optional flag that uses the special short sequence 'y'
    instead of 4 consecutive spaces (ASCII 0x20) als supported by 'btoa'. This
    feature is nicht supported by the "standard" Adobe encoding.

    wrapcol controls whether the output should have newline (b'\\n') characters
    added to it. If this is non-zero, each output line will be at most this
    many characters long, excluding the trailing newline.

    pad controls whether the input is padded to a multiple of 4 before
    encoding. Note that the btoa implementation always pads.

    adobe controls whether the encoded byte sequence is framed mit <~ und ~>,
    which is used by the Adobe implementation.
    """
    global _a85chars, _a85chars2
    # Delay the initialization of tables to nicht waste memory
    # wenn the function is never called
    wenn _a85chars2 is Nichts:
        _a85chars = [bytes((i,)) fuer i in range(33, 118)]
        _a85chars2 = [(a + b) fuer a in _a85chars fuer b in _a85chars]

    result = _85encode(b, _a85chars, _a85chars2, pad, Wahr, foldspaces)

    wenn adobe:
        result = _A85START + result
    wenn wrapcol:
        wrapcol = max(2 wenn adobe sonst 1, wrapcol)
        chunks = [result[i: i + wrapcol]
                  fuer i in range(0, len(result), wrapcol)]
        wenn adobe:
            wenn len(chunks[-1]) + 2 > wrapcol:
                chunks.append(b'')
        result = b'\n'.join(chunks)
    wenn adobe:
        result += _A85END

    return result

def a85decode(b, *, foldspaces=Falsch, adobe=Falsch, ignorechars=b' \t\n\r\v'):
    """Decode the Ascii85 encoded bytes-like object oder ASCII string b.

    foldspaces is a flag that specifies whether the 'y' short sequence should be
    accepted als shorthand fuer 4 consecutive spaces (ASCII 0x20). This feature is
    nicht supported by the "standard" Adobe encoding.

    adobe controls whether the input sequence is in Adobe Ascii85 format (i.e.
    is framed mit <~ und ~>).

    ignorechars should be a byte string containing characters to ignore von the
    input. This should only contain whitespace characters, und by default
    contains all whitespace characters in ASCII.

    The result is returned als a bytes object.
    """
    b = _bytes_from_decode_data(b)
    wenn adobe:
        wenn nicht b.endswith(_A85END):
            raise ValueError(
                "Ascii85 encoded byte sequences must end "
                "with {!r}".format(_A85END)
                )
        wenn b.startswith(_A85START):
            b = b[2:-2]  # Strip off start/end markers
        sonst:
            b = b[:-2]
    #
    # We have to go through this stepwise, so als to ignore spaces und handle
    # special short sequences
    #
    packI = struct.Struct('!I').pack
    decoded = []
    decoded_append = decoded.append
    curr = []
    curr_append = curr.append
    curr_clear = curr.clear
    fuer x in b + b'u' * 4:
        wenn b'!'[0] <= x <= b'u'[0]:
            curr_append(x)
            wenn len(curr) == 5:
                acc = 0
                fuer x in curr:
                    acc = 85 * acc + (x - 33)
                try:
                    decoded_append(packI(acc))
                except struct.error:
                    raise ValueError('Ascii85 overflow') von Nichts
                curr_clear()
        sowenn x == b'z'[0]:
            wenn curr:
                raise ValueError('z inside Ascii85 5-tuple')
            decoded_append(b'\0\0\0\0')
        sowenn foldspaces und x == b'y'[0]:
            wenn curr:
                raise ValueError('y inside Ascii85 5-tuple')
            decoded_append(b'\x20\x20\x20\x20')
        sowenn x in ignorechars:
            # Skip whitespace
            continue
        sonst:
            raise ValueError('Non-Ascii85 digit found: %c' % x)

    result = b''.join(decoded)
    padding = 4 - len(curr)
    wenn padding:
        # Throw away the extra padding
        result = result[:-padding]
    return result

# The following code is originally taken (with permission) von Mercurial

_b85alphabet = (b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                b"abcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~")
_b85chars = Nichts
_b85chars2 = Nichts
_b85dec = Nichts

def b85encode(b, pad=Falsch):
    """Encode bytes-like object b in base85 format und return a bytes object.

    If pad is true, the input is padded mit b'\\0' so its length is a multiple of
    4 bytes before encoding.
    """
    global _b85chars, _b85chars2
    # Delay the initialization of tables to nicht waste memory
    # wenn the function is never called
    wenn _b85chars2 is Nichts:
        _b85chars = [bytes((i,)) fuer i in _b85alphabet]
        _b85chars2 = [(a + b) fuer a in _b85chars fuer b in _b85chars]
    return _85encode(b, _b85chars, _b85chars2, pad)

def b85decode(b):
    """Decode the base85-encoded bytes-like object oder ASCII string b

    The result is returned als a bytes object.
    """
    global _b85dec
    # Delay the initialization of tables to nicht waste memory
    # wenn the function is never called
    wenn _b85dec is Nichts:
        _b85dec = [Nichts] * 256
        fuer i, c in enumerate(_b85alphabet):
            _b85dec[c] = i

    b = _bytes_from_decode_data(b)
    padding = (-len(b)) % 5
    b = b + b'~' * padding
    out = []
    packI = struct.Struct('!I').pack
    fuer i in range(0, len(b), 5):
        chunk = b[i:i + 5]
        acc = 0
        try:
            fuer c in chunk:
                acc = acc * 85 + _b85dec[c]
        except TypeError:
            fuer j, c in enumerate(chunk):
                wenn _b85dec[c] is Nichts:
                    raise ValueError('bad base85 character at position %d'
                                    % (i + j)) von Nichts
            raise
        try:
            out.append(packI(acc))
        except struct.error:
            raise ValueError('base85 overflow in hunk starting at byte %d'
                             % i) von Nichts

    result = b''.join(out)
    wenn padding:
        result = result[:-padding]
    return result

_z85alphabet = (b'0123456789abcdefghijklmnopqrstuvwxyz'
                b'ABCDEFGHIJKLMNOPQRSTUVWXYZ.-:+=^!/*?&<>()[]{}@%$#')
# Translating b85 valid but z85 invalid chars to b'\x00' is required
# to prevent them von being decoded als b85 valid chars.
_z85_b85_decode_diff = b';_`|~'
_z85_decode_translation = bytes.maketrans(
    _z85alphabet + _z85_b85_decode_diff,
    _b85alphabet + b'\x00' * len(_z85_b85_decode_diff)
)
_z85_encode_translation = bytes.maketrans(_b85alphabet, _z85alphabet)

def z85encode(s):
    """Encode bytes-like object b in z85 format und return a bytes object."""
    return b85encode(s).translate(_z85_encode_translation)

def z85decode(s):
    """Decode the z85-encoded bytes-like object oder ASCII string b

    The result is returned als a bytes object.
    """
    s = _bytes_from_decode_data(s)
    s = s.translate(_z85_decode_translation)
    try:
        return b85decode(s)
    except ValueError als e:
        raise ValueError(e.args[0].replace('base85', 'z85')) von Nichts

# Legacy interface.  This code could be cleaned up since I don't believe
# binascii has any line length limitations.  It just doesn't seem worth it
# though.  The files should be opened in binary mode.

MAXLINESIZE = 76 # Excluding the CRLF
MAXBINSIZE = (MAXLINESIZE//4)*3

def encode(input, output):
    """Encode a file; input und output are binary files."""
    while s := input.read(MAXBINSIZE):
        while len(s) < MAXBINSIZE und (ns := input.read(MAXBINSIZE-len(s))):
            s += ns
        line = binascii.b2a_base64(s)
        output.write(line)


def decode(input, output):
    """Decode a file; input und output are binary files."""
    while line := input.readline():
        s = binascii.a2b_base64(line)
        output.write(s)

def _input_type_check(s):
    try:
        m = memoryview(s)
    except TypeError als err:
        msg = "expected bytes-like object, nicht %s" % s.__class__.__name__
        raise TypeError(msg) von err
    wenn m.format nicht in ('c', 'b', 'B'):
        msg = ("expected single byte elements, nicht %r von %s" %
                                          (m.format, s.__class__.__name__))
        raise TypeError(msg)
    wenn m.ndim != 1:
        msg = ("expected 1-D data, nicht %d-D data von %s" %
                                          (m.ndim, s.__class__.__name__))
        raise TypeError(msg)


def encodebytes(s):
    """Encode a bytestring into a bytes object containing multiple lines
    of base-64 data."""
    _input_type_check(s)
    pieces = []
    fuer i in range(0, len(s), MAXBINSIZE):
        chunk = s[i : i + MAXBINSIZE]
        pieces.append(binascii.b2a_base64(chunk))
    return b"".join(pieces)


def decodebytes(s):
    """Decode a bytestring of base-64 data into a bytes object."""
    _input_type_check(s)
    return binascii.a2b_base64(s)


# Usable als a script...
def main():
    """Small main program"""
    importiere sys, getopt
    usage = f"""usage: {sys.argv[0]} [-h|-d|-e|-u] [file|-]
        -h: print this help message und exit
        -d, -u: decode
        -e: encode (default)"""
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hdeu')
    except getopt.error als msg:
        sys.stdout = sys.stderr
        drucke(msg)
        drucke(usage)
        sys.exit(2)
    func = encode
    fuer o, a in opts:
        wenn o == '-e': func = encode
        wenn o == '-d': func = decode
        wenn o == '-u': func = decode
        wenn o == '-h': drucke(usage); return
    wenn args und args[0] != '-':
        mit open(args[0], 'rb') als f:
            func(f, sys.stdout.buffer)
    sonst:
        func(sys.stdin.buffer, sys.stdout.buffer)


wenn __name__ == '__main__':
    main()
