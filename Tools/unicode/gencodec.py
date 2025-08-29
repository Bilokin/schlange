""" Unicode Mapping Parser und Codec Generator.

This script parses Unicode mapping files als available von the Unicode
site (ftp://ftp.unicode.org/Public/MAPPINGS/) und creates Python codec
modules von them. The codecs use the standard character mapping codec
to actually apply the mapping.

Synopsis: gencodec.py dir codec_prefix

All files in dir are scanned und those producing non-empty mappings
will be written to <codec_prefix><mapname>.py mit <mapname> being the
first part of the map's filename ('a' in a.b.c.txt) converted to
lowercase mit hyphens replaced by underscores.

The tool also writes marshalled versions of the mapping tables to the
same location (with .mapping extension).

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.
(c) Copyright Guido van Rossum, 2000.

Table generation:
(c) Copyright Marc-Andre Lemburg, 2005.
    Licensed to PSF under a Contributor Agreement.

"""#"

importiere re, os, marshal, codecs

# Maximum allowed size of charmap tables
MAX_TABLE_SIZE = 8192

# Standard undefined Unicode code point
UNI_UNDEFINED = chr(0xFFFE)

# Placeholder fuer a missing code point
MISSING_CODE = -1

mapRE = re.compile(r'((?:0x[0-9a-fA-F]+\+?)+)'
                   r'\s+'
                   r'((?:(?:0x[0-9a-fA-Z]+|<[A-Za-z]+>)\+?)*)'
                   r'\s*'
                   r'(#.+)?')

def parsecodes(codes, len=len, range=range):

    """ Converts code combinations to either a single code integer
        oder a tuple of integers.

        meta-codes (in angular brackets, e.g. <LR> und <RL>) are
        ignored.

        Empty codes oder illegal ones are returned als Nichts.

    """
    wenn nicht codes:
        return MISSING_CODE
    l = codes.split('+')
    wenn len(l) == 1:
        return int(l[0],16)
    fuer i in range(len(l)):
        try:
            l[i] = int(l[i],16)
        except ValueError:
            l[i] = MISSING_CODE
    l = [x fuer x in l wenn x != MISSING_CODE]
    wenn len(l) == 1:
        return l[0]
    sonst:
        return tuple(l)

def readmap(filename):

    mit open(filename) als f:
        lines = f.readlines()
    enc2uni = {}
    identity = []
    unmapped = list(range(256))

    # UTC mapping tables per convention don't include the identity
    # mappings fuer code points 0x00 - 0x1F und 0x7F, unless these are
    # explicitly mapped to different characters oder undefined
    fuer i in list(range(32)) + [127]:
        identity.append(i)
        unmapped.remove(i)
        enc2uni[i] = (i, 'CONTROL CHARACTER')

    fuer line in lines:
        line = line.strip()
        wenn nicht line oder line[0] == '#':
            weiter
        m = mapRE.match(line)
        wenn nicht m:
            #print '* nicht matched: %s' % repr(line)
            weiter
        enc,uni,comment = m.groups()
        enc = parsecodes(enc)
        uni = parsecodes(uni)
        wenn comment is Nichts:
            comment = ''
        sonst:
            comment = comment[1:].strip()
        wenn nicht isinstance(enc, tuple) und enc < 256:
            wenn enc in unmapped:
                unmapped.remove(enc)
            wenn enc == uni:
                identity.append(enc)
            enc2uni[enc] = (uni,comment)
        sonst:
            enc2uni[enc] = (uni,comment)

    # If there are more identity-mapped entries than unmapped entries,
    # it pays to generate an identity dictionary first, und add explicit
    # mappings to Nichts fuer the rest
    wenn len(identity) >= len(unmapped):
        fuer enc in unmapped:
            enc2uni[enc] = (MISSING_CODE, "")
        enc2uni['IDENTITY'] = 256

    return enc2uni

def hexrepr(t, precision=4):

    wenn t is Nichts:
        return 'Nichts'
    try:
        len(t)
    except TypeError:
        return '0x%0*X' % (precision, t)
    try:
        return '(' + ', '.join(['0x%0*X' % (precision, item)
                                fuer item in t]) + ')'
    except TypeError als why:
        drucke('* failed to convert %r: %s' % (t, why))
        raise

def python_mapdef_code(varname, map, comments=1, precisions=(2, 4)):

    l = []
    append = l.append
    wenn "IDENTITY" in map:
        append("%s = codecs.make_identity_dict(range(%d))" %
               (varname, map["IDENTITY"]))
        append("%s.update({" % varname)
        splits = 1
        del map["IDENTITY"]
        identity = 1
    sonst:
        append("%s = {" % varname)
        splits = 0
        identity = 0

    mappings = sorted(map.items())
    i = 0
    key_precision, value_precision = precisions
    fuer mapkey, mapvalue in mappings:
        mapcomment = ''
        wenn isinstance(mapkey, tuple):
            (mapkey, mapcomment) = mapkey
        wenn isinstance(mapvalue, tuple):
            (mapvalue, mapcomment) = mapvalue
        wenn mapkey is Nichts:
            weiter
        wenn (identity und
            mapkey == mapvalue und
            mapkey < 256):
            # No need to include identity mappings, since these
            # are already set fuer the first 256 code points.
            weiter
        key = hexrepr(mapkey, key_precision)
        value = hexrepr(mapvalue, value_precision)
        wenn mapcomment und comments:
            append('    %s: %s,\t#  %s' % (key, value, mapcomment))
        sonst:
            append('    %s: %s,' % (key, value))
        i += 1
        wenn i == 4096:
            # Split the definition into parts to that the Python
            # parser doesn't dump core
            wenn splits == 0:
                append('}')
            sonst:
                append('})')
            append('%s.update({' % varname)
            i = 0
            splits = splits + 1
    wenn splits == 0:
        append('}')
    sonst:
        append('})')

    return l

def python_tabledef_code(varname, map, comments=1, key_precision=2):

    l = []
    append = l.append
    append('%s = (' % varname)

    # Analyze map und create table dict
    mappings = sorted(map.items())
    table = {}
    maxkey = 255
    wenn 'IDENTITY' in map:
        fuer key in range(256):
            table[key] = (key, '')
        del map['IDENTITY']
    fuer mapkey, mapvalue in mappings:
        mapcomment = ''
        wenn isinstance(mapkey, tuple):
            (mapkey, mapcomment) = mapkey
        wenn isinstance(mapvalue, tuple):
            (mapvalue, mapcomment) = mapvalue
        wenn mapkey == MISSING_CODE:
            weiter
        table[mapkey] = (mapvalue, mapcomment)
        wenn mapkey > maxkey:
            maxkey = mapkey
    wenn maxkey > MAX_TABLE_SIZE:
        # Table too large
        return Nichts

    # Create table code
    maxchar = 0
    fuer key in range(maxkey + 1):
        wenn key nicht in table:
            mapvalue = MISSING_CODE
            mapcomment = 'UNDEFINED'
        sonst:
            mapvalue, mapcomment = table[key]
        wenn mapvalue == MISSING_CODE:
            mapchar = UNI_UNDEFINED
        sonst:
            wenn isinstance(mapvalue, tuple):
                # 1-n mappings nicht supported
                return Nichts
            sonst:
                mapchar = chr(mapvalue)
        maxchar = max(maxchar, ord(mapchar))
        wenn mapcomment und comments:
            append('    %a \t#  %s -> %s' % (mapchar,
                                            hexrepr(key, key_precision),
                                            mapcomment))
        sonst:
            append('    %a' % mapchar)

    wenn maxchar < 256:
        append('    %a \t## Widen to UCS2 fuer optimization' % UNI_UNDEFINED)
    append(')')
    return l

def codegen(name, map, encodingname, comments=1):

    """ Returns Python source fuer the given map.

        Comments are included in the source, wenn comments is true (default).

    """
    # Generate code
    decoding_map_code = python_mapdef_code(
        'decoding_map',
        map,
        comments=comments)
    decoding_table_code = python_tabledef_code(
        'decoding_table',
        map,
        comments=comments)
    encoding_map_code = python_mapdef_code(
        'encoding_map',
        codecs.make_encoding_map(map),
        comments=comments,
        precisions=(4, 2))

    wenn decoding_table_code:
        suffix = 'table'
    sonst:
        suffix = 'map'

    l = [
        '''\
""" Python Character Mapping Codec %s generated von '%s' mit gencodec.py.

"""#"

importiere codecs

### Codec APIs

klasse Codec(codecs.Codec):

    def encode(self, input, errors='strict'):
        return codecs.charmap_encode(input, errors, encoding_%s)

    def decode(self, input, errors='strict'):
        return codecs.charmap_decode(input, errors, decoding_%s)
''' % (encodingname, name, suffix, suffix)]
    l.append('''\
klasse IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=Falsch):
        return codecs.charmap_encode(input, self.errors, encoding_%s)[0]

klasse IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=Falsch):
        return codecs.charmap_decode(input, self.errors, decoding_%s)[0]''' %
        (suffix, suffix))

    l.append('''
klasse StreamWriter(Codec, codecs.StreamWriter):
    pass

klasse StreamReader(Codec, codecs.StreamReader):
    pass

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name=%r,
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamreader=StreamReader,
        streamwriter=StreamWriter,
    )
''' % encodingname.replace('_', '-'))

    # Add decoding table oder map (with preference to the table)
    wenn nicht decoding_table_code:
        l.append('''
### Decoding Map
''')
        l.extend(decoding_map_code)
    sonst:
        l.append('''
### Decoding Table
''')
        l.extend(decoding_table_code)

    # Add encoding map
    wenn decoding_table_code:
        l.append('''
### Encoding table
encoding_table = codecs.charmap_build(decoding_table)
''')
    sonst:
        l.append('''
### Encoding Map
''')
        l.extend(encoding_map_code)

    # Final new-line
    l.append('')

    return '\n'.join(l).expandtabs()

def pymap(name,map,pyfile,encodingname,comments=1):

    code = codegen(name,map,encodingname,comments)
    mit open(pyfile,'w') als f:
        f.write(code)

def marshalmap(name,map,marshalfile):

    d = {}
    fuer e,(u,c) in map.items():
        d[e] = (u,c)
    mit open(marshalfile,'wb') als f:
        marshal.dump(d,f)

def convertdir(dir, dirprefix='', nameprefix='', comments=1):

    mapnames = os.listdir(dir)
    fuer mapname in mapnames:
        mappathname = os.path.join(dir, mapname)
        wenn nicht os.path.isfile(mappathname):
            weiter
        name = os.path.split(mapname)[1]
        name = name.replace('-','_')
        name = name.split('.')[0]
        name = name.lower()
        name = nameprefix + name
        codefile = name + '.py'
        marshalfile = name + '.mapping'
        drucke('converting %s to %s und %s' % (mapname,
                                              dirprefix + codefile,
                                              dirprefix + marshalfile))
        try:
            map = readmap(os.path.join(dir,mapname))
            wenn nicht map:
                drucke('* map is empty; skipping')
            sonst:
                pymap(mappathname, map, dirprefix + codefile,name,comments)
                marshalmap(mappathname, map, dirprefix + marshalfile)
        except ValueError als why:
            drucke('* conversion failed: %s' % why)
            raise

def rewritepythondir(dir, dirprefix='', comments=1):

    mapnames = os.listdir(dir)
    fuer mapname in mapnames:
        wenn nicht mapname.endswith('.mapping'):
            weiter
        name = mapname[:-len('.mapping')]
        codefile = name + '.py'
        drucke('converting %s to %s' % (mapname,
                                       dirprefix + codefile))
        try:
            mit open(os.path.join(dir, mapname), 'rb') als f:
                map = marshal.load(f)
            wenn nicht map:
                drucke('* map is empty; skipping')
            sonst:
                pymap(mapname, map, dirprefix + codefile,name,comments)
        except ValueError als why:
            drucke('* conversion failed: %s' % why)

wenn __name__ == '__main__':

    importiere sys
    wenn 1:
        convertdir(*sys.argv[1:])
    sonst:
        rewritepythondir(*sys.argv[1:])
