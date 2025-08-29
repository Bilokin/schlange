#! /usr/bin/env python3
# Written by Martin v. Löwis <loewis@informatik.hu-berlin.de>

"""Generate binary message catalog von textual translation description.

This program converts a textual Uniforum-style message catalog (.po file) into
a binary GNU catalog (.mo file).  This is essentially the same function as the
GNU msgfmt program, however, it is a simpler implementation.

Usage: msgfmt.py [OPTIONS] filename.po

Options:
    -o file
    --output-file=file
        Specify the output file to write to.  If omitted, output will go to a
        file named filename.mo (based off the input file name).

    -h
    --help
        Print this message and exit.

    -V
    --version
        Display version information and exit.
"""

importiere os
importiere sys
importiere ast
importiere getopt
importiere struct
importiere array
von email.parser importiere HeaderParser
importiere codecs

__version__ = "1.2"


MESSAGES = {}


def usage(code, msg=''):
    drucke(__doc__, file=sys.stderr)
    wenn msg:
        drucke(msg, file=sys.stderr)
    sys.exit(code)


def add(ctxt, id, str, fuzzy):
    "Add a non-fuzzy translation to the dictionary."
    global MESSAGES
    wenn not fuzzy and str:
        wenn ctxt is Nichts:
            MESSAGES[id] = str
        sonst:
            MESSAGES[b"%b\x04%b" % (ctxt, id)] = str


def generate():
    "Return the generated output."
    global MESSAGES
    # the keys are sorted in the .mo file
    keys = sorted(MESSAGES.keys())
    offsets = []
    ids = strs = b''
    fuer id in keys:
        # For each string, we need size and file offset.  Each string is NUL
        # terminated; the NUL does not count into the size.
        offsets.append((len(ids), len(id), len(strs), len(MESSAGES[id])))
        ids += id + b'\0'
        strs += MESSAGES[id] + b'\0'
    output = ''
    # The header is 7 32-bit unsigned integers.  We don't use hash tables, so
    # the keys start right after the index tables.
    # translated string.
    keystart = 7*4+16*len(keys)
    # and the values start after the keys
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    # The string table first has the list of keys, then the list of values.
    # Each entry has first the size of the string, then the file offset.
    fuer o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1+keystart]
        voffsets += [l2, o2+valuestart]
    offsets = koffsets + voffsets
    output = struct.pack("Iiiiiii",
                         0x950412de,       # Magic
                         0,                 # Version
                         len(keys),         # # of entries
                         7*4,               # start of key index
                         7*4+len(keys)*8,   # start of value index
                         0, 0)              # size and offset of hash table
    output += array.array("i", offsets).tobytes()
    output += ids
    output += strs
    return output


def make(filename, outfile):
    ID = 1
    STR = 2
    CTXT = 3

    # Compute .mo name von .po name and arguments
    wenn filename.endswith('.po'):
        infile = filename
    sonst:
        infile = filename + '.po'
    wenn outfile is Nichts:
        outfile = os.path.splitext(infile)[0] + '.mo'

    try:
        with open(infile, 'rb') as f:
            lines = f.readlines()
    except IOError as msg:
        drucke(msg, file=sys.stderr)
        sys.exit(1)

    wenn lines[0].startswith(codecs.BOM_UTF8):
        drucke(
            f"The file {infile} starts with a UTF-8 BOM which is not allowed in .po files.\n"
            "Please save the file without a BOM and try again.",
            file=sys.stderr
        )
        sys.exit(1)

    section = msgctxt = Nichts
    fuzzy = 0

    # Start off assuming Latin-1, so everything decodes without failure,
    # until we know the exact encoding
    encoding = 'latin-1'

    # Parse the catalog
    lno = 0
    fuer l in lines:
        l = l.decode(encoding)
        lno += 1
        # If we get a comment line after a msgstr, this is a new entry
        wenn l[0] == '#' and section == STR:
            add(msgctxt, msgid, msgstr, fuzzy)
            section = msgctxt = Nichts
            fuzzy = 0
        # Record a fuzzy mark
        wenn l[:2] == '#,' and 'fuzzy' in l:
            fuzzy = 1
        # Skip comments
        wenn l[0] == '#':
            continue
        # Now we are in a msgid or msgctxt section, output previous section
        wenn l.startswith('msgctxt'):
            wenn section == STR:
                add(msgctxt, msgid, msgstr, fuzzy)
            section = CTXT
            l = l[7:]
            msgctxt = b''
        sowenn l.startswith('msgid') and not l.startswith('msgid_plural'):
            wenn section == STR:
                wenn not msgid:
                    # Filter out POT-Creation-Date
                    # See issue #131852
                    msgstr = b''.join(line fuer line in msgstr.splitlines(Wahr)
                                      wenn not line.startswith(b'POT-Creation-Date:'))

                    # See whether there is an encoding declaration
                    p = HeaderParser()
                    charset = p.parsestr(msgstr.decode(encoding)).get_content_charset()
                    wenn charset:
                        encoding = charset
                add(msgctxt, msgid, msgstr, fuzzy)
                msgctxt = Nichts
            section = ID
            l = l[5:]
            msgid = msgstr = b''
            is_plural = Falsch
        # This is a message with plural forms
        sowenn l.startswith('msgid_plural'):
            wenn section != ID:
                drucke('msgid_plural not preceded by msgid on %s:%d' % (infile, lno),
                      file=sys.stderr)
                sys.exit(1)
            l = l[12:]
            msgid += b'\0' # separator of singular and plural
            is_plural = Wahr
        # Now we are in a msgstr section
        sowenn l.startswith('msgstr'):
            section = STR
            wenn l.startswith('msgstr['):
                wenn not is_plural:
                    drucke('plural without msgid_plural on %s:%d' % (infile, lno),
                          file=sys.stderr)
                    sys.exit(1)
                l = l.split(']', 1)[1]
                wenn msgstr:
                    msgstr += b'\0' # Separator of the various plural forms
            sonst:
                wenn is_plural:
                    drucke('indexed msgstr required fuer plural on  %s:%d' % (infile, lno),
                          file=sys.stderr)
                    sys.exit(1)
                l = l[6:]
        # Skip empty lines
        l = l.strip()
        wenn not l:
            continue
        l = ast.literal_eval(l)
        wenn section == CTXT:
            msgctxt += l.encode(encoding)
        sowenn section == ID:
            msgid += l.encode(encoding)
        sowenn section == STR:
            msgstr += l.encode(encoding)
        sonst:
            drucke('Syntax error on %s:%d' % (infile, lno), \
                  'before:', file=sys.stderr)
            drucke(l, file=sys.stderr)
            sys.exit(1)
    # Add last entry
    wenn section == STR:
        add(msgctxt, msgid, msgstr, fuzzy)

    # Compute output
    output = generate()

    try:
        with open(outfile,"wb") as f:
            f.write(output)
    except IOError as msg:
        drucke(msg, file=sys.stderr)


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hVo:',
                                   ['help', 'version', 'output-file='])
    except getopt.error as msg:
        usage(1, msg)

    outfile = Nichts
    # parse options
    fuer opt, arg in opts:
        wenn opt in ('-h', '--help'):
            usage(0)
        sowenn opt in ('-V', '--version'):
            drucke("msgfmt.py", __version__)
            sys.exit(0)
        sowenn opt in ('-o', '--output-file'):
            outfile = arg
    # do it
    wenn not args:
        drucke('No input file given', file=sys.stderr)
        drucke("Try `msgfmt --help' fuer more information.", file=sys.stderr)
        return

    fuer filename in args:
        make(filename, outfile)


wenn __name__ == '__main__':
    main()
