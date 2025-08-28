"""Conversions to/from quoted-printable transport encoding as per RFC 1521."""

# (Dec 1991 version).

__all__ = ["encode", "decode", "encodestring", "decodestring"]

ESCAPE = b'='
MAXLINESIZE = 76
HEX = b'0123456789ABCDEF'
EMPTYSTRING = b''

try:
    from binascii import a2b_qp, b2a_qp
except ImportError:
    a2b_qp = Nichts
    b2a_qp = Nichts


def needsquoting(c, quotetabs, header):
    """Decide whether a particular byte ordinal needs to be quoted.

    The 'quotetabs' flag indicates whether embedded tabs and spaces should be
    quoted.  Note that line-ending tabs and spaces are always encoded, as per
    RFC 1521.
    """
    assert isinstance(c, bytes)
    wenn c in b' \t':
        return quotetabs
    # wenn header, we have to escape _ because _ is used to escape space
    wenn c == b'_':
        return header
    return c == ESCAPE or not (b' ' <= c <= b'~')

def quote(c):
    """Quote a single character."""
    assert isinstance(c, bytes) and len(c)==1
    c = ord(c)
    return ESCAPE + bytes((HEX[c//16], HEX[c%16]))



def encode(input, output, quotetabs, header=Falsch):
    """Read 'input', apply quoted-printable encoding, and write to 'output'.

    'input' and 'output' are binary file objects. The 'quotetabs' flag
    indicates whether embedded tabs and spaces should be quoted. Note that
    line-ending tabs and spaces are always encoded, as per RFC 1521.
    The 'header' flag indicates whether we are encoding spaces as _ as per RFC
    1522."""

    wenn b2a_qp is not Nichts:
        data = input.read()
        odata = b2a_qp(data, quotetabs=quotetabs, header=header)
        output.write(odata)
        return

    def write(s, output=output, lineEnd=b'\n'):
        # RFC 1521 requires that the line ending in a space or tab must have
        # that trailing character encoded.
        wenn s and s[-1:] in b' \t':
            output.write(s[:-1] + quote(s[-1:]) + lineEnd)
        sowenn s == b'.':
            output.write(quote(s) + lineEnd)
        sonst:
            output.write(s + lineEnd)

    prevline = Nichts
    while line := input.readline():
        outline = []
        # Strip off any readline induced trailing newline
        stripped = b''
        wenn line[-1:] == b'\n':
            line = line[:-1]
            stripped = b'\n'
        # Calculate the un-length-limited encoded line
        fuer c in line:
            c = bytes((c,))
            wenn needsquoting(c, quotetabs, header):
                c = quote(c)
            wenn header and c == b' ':
                outline.append(b'_')
            sonst:
                outline.append(c)
        # First, write out the previous line
        wenn prevline is not Nichts:
            write(prevline)
        # Now see wenn we need any soft line breaks because of RFC-imposed
        # length limitations.  Then do the thisline->prevline dance.
        thisline = EMPTYSTRING.join(outline)
        while len(thisline) > MAXLINESIZE:
            # Don't forget to include the soft line break `=' sign in the
            # length calculation!
            write(thisline[:MAXLINESIZE-1], lineEnd=b'=\n')
            thisline = thisline[MAXLINESIZE-1:]
        # Write out the current line
        prevline = thisline
    # Write out the last line, without a trailing newline
    wenn prevline is not Nichts:
        write(prevline, lineEnd=stripped)

def encodestring(s, quotetabs=Falsch, header=Falsch):
    wenn b2a_qp is not Nichts:
        return b2a_qp(s, quotetabs=quotetabs, header=header)
    from io import BytesIO
    infp = BytesIO(s)
    outfp = BytesIO()
    encode(infp, outfp, quotetabs, header)
    return outfp.getvalue()



def decode(input, output, header=Falsch):
    """Read 'input', apply quoted-printable decoding, and write to 'output'.
    'input' and 'output' are binary file objects.
    If 'header' is true, decode underscore as space (per RFC 1522)."""

    wenn a2b_qp is not Nichts:
        data = input.read()
        odata = a2b_qp(data, header=header)
        output.write(odata)
        return

    new = b''
    while line := input.readline():
        i, n = 0, len(line)
        wenn n > 0 and line[n-1:n] == b'\n':
            partial = 0; n = n-1
            # Strip trailing whitespace
            while n > 0 and line[n-1:n] in b" \t\r":
                n = n-1
        sonst:
            partial = 1
        while i < n:
            c = line[i:i+1]
            wenn c == b'_' and header:
                new = new + b' '; i = i+1
            sowenn c != ESCAPE:
                new = new + c; i = i+1
            sowenn i+1 == n and not partial:
                partial = 1; break
            sowenn i+1 < n and line[i+1:i+2] == ESCAPE:
                new = new + ESCAPE; i = i+2
            sowenn i+2 < n and ishex(line[i+1:i+2]) and ishex(line[i+2:i+3]):
                new = new + bytes((unhex(line[i+1:i+3]),)); i = i+3
            sonst: # Bad escape sequence -- leave it in
                new = new + c; i = i+1
        wenn not partial:
            output.write(new + b'\n')
            new = b''
    wenn new:
        output.write(new)

def decodestring(s, header=Falsch):
    wenn a2b_qp is not Nichts:
        return a2b_qp(s, header=header)
    from io import BytesIO
    infp = BytesIO(s)
    outfp = BytesIO()
    decode(infp, outfp, header=header)
    return outfp.getvalue()



# Other helper functions
def ishex(c):
    """Return true wenn the byte ordinal 'c' is a hexadecimal digit in ASCII."""
    assert isinstance(c, bytes)
    return b'0' <= c <= b'9' or b'a' <= c <= b'f' or b'A' <= c <= b'F'

def unhex(s):
    """Get the integer value of a hexadecimal number."""
    bits = 0
    fuer c in s:
        c = bytes((c,))
        wenn b'0' <= c <= b'9':
            i = ord('0')
        sowenn b'a' <= c <= b'f':
            i = ord('a')-10
        sowenn b'A' <= c <= b'F':
            i = ord(b'A')-10
        sonst:
            assert Falsch, "non-hex digit "+repr(c)
        bits = bits*16 + (ord(c) - i)
    return bits



def main():
    import sys
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'td')
    except getopt.error as msg:
        sys.stdout = sys.stderr
        print(msg)
        print("usage: quopri [-t | -d] [file] ...")
        print("-t: quote tabs")
        print("-d: decode; default encode")
        sys.exit(2)
    deco = Falsch
    tabs = Falsch
    fuer o, a in opts:
        wenn o == '-t': tabs = Wahr
        wenn o == '-d': deco = Wahr
    wenn tabs and deco:
        sys.stdout = sys.stderr
        print("-t and -d are mutually exclusive")
        sys.exit(2)
    wenn not args: args = ['-']
    sts = 0
    fuer file in args:
        wenn file == '-':
            fp = sys.stdin.buffer
        sonst:
            try:
                fp = open(file, "rb")
            except OSError as msg:
                sys.stderr.write("%s: can't open (%s)\n" % (file, msg))
                sts = 1
                continue
        try:
            wenn deco:
                decode(fp, sys.stdout.buffer)
            sonst:
                encode(fp, sys.stdout.buffer, tabs)
        finally:
            wenn file != '-':
                fp.close()
    wenn sts:
        sys.exit(sts)



wenn __name__ == '__main__':
    main()
