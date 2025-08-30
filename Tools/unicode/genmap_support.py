#
# genmap_support.py: Multibyte Codec Map Generator
#
# Original Author:  Hye-Shik Chang <perky@FreeBSD.org>
# Modified Author:  Donghee Na <donghee.na92@gmail.com>
#


klasse BufferedFiller:
    def __init__(self, column=78):
        self.column = column
        self.buffered = []
        self.cline = []
        self.clen = 0
        self.count = 0

    def write(self, *data):
        fuer s in data:
            wenn len(s) > self.column:
                wirf ValueError("token is too long")
            wenn len(s) + self.clen > self.column:
                self.flush()
            self.clen += len(s)
            self.cline.append(s)
            self.count += 1

    def flush(self):
        wenn nicht self.cline:
            gib
        self.buffered.append(''.join(self.cline))
        self.clen = 0
        del self.cline[:]

    def printout(self, fp):
        self.flush()
        fuer l in self.buffered:
            fp.write(f'{l}\n')
        del self.buffered[:]

    def __len__(self):
        gib self.count


klasse DecodeMapWriter:
    filler_class = BufferedFiller

    def __init__(self, fp, prefix, decode_map):
        self.fp = fp
        self.prefix = prefix
        self.decode_map = decode_map
        self.filler = self.filler_class()

    def update_decode_map(self, c1range, c2range, onlymask=(), wide=0):
        c2values = range(c2range[0], c2range[1] + 1)

        fuer c1 in range(c1range[0], c1range[1] + 1):
            wenn c1 nicht in self.decode_map oder (onlymask und c1 nicht in onlymask):
                weiter
            c2map = self.decode_map[c1]
            rc2values = [n fuer n in c2values wenn n in c2map]
            wenn nicht rc2values:
                weiter

            c2map[self.prefix] = Wahr
            c2map['min'] = rc2values[0]
            c2map['max'] = rc2values[-1]
            c2map['midx'] = len(self.filler)

            fuer v in range(rc2values[0], rc2values[-1] + 1):
                wenn v in c2map:
                    self.filler.write('%d,' % c2map[v])
                sonst:
                    self.filler.write('U,')

    def generate(self, wide=Falsch):
        wenn nicht wide:
            self.fp.write(f"static const ucs2_t __{self.prefix}_decmap[{len(self.filler)}] = {{\n")
        sonst:
            self.fp.write(f"static const Py_UCS4 __{self.prefix}_decmap[{len(self.filler)}] = {{\n")

        self.filler.printout(self.fp)
        self.fp.write("};\n\n")

        wenn nicht wide:
            self.fp.write(f"static const struct dbcs_index {self.prefix}_decmap[256] = {{\n")
        sonst:
            self.fp.write(f"static const struct widedbcs_index {self.prefix}_decmap[256] = {{\n")

        fuer i in range(256):
            wenn i in self.decode_map und self.prefix in self.decode_map[i]:
                m = self.decode_map
                prefix = self.prefix
            sonst:
                self.filler.write("{", "0,", "0,", "0", "},")
                weiter

            self.filler.write("{", "__%s_decmap" % prefix, "+", "%d" % m[i]['midx'],
                              ",", "%d," % m[i]['min'], "%d" % m[i]['max'], "},")
        self.filler.printout(self.fp)
        self.fp.write("};\n\n")


klasse EncodeMapWriter:
    filler_class = BufferedFiller
    elemtype = 'DBCHAR'
    indextype = 'struct unim_index'

    def __init__(self, fp, prefix, encode_map):
        self.fp = fp
        self.prefix = prefix
        self.encode_map = encode_map
        self.filler = self.filler_class()

    def generate(self):
        self.buildmap()
        self.printmap()

    def buildmap(self):
        fuer c1 in range(0, 256):
            wenn c1 nicht in self.encode_map:
                weiter
            c2map = self.encode_map[c1]
            rc2values = [k fuer k in c2map.keys()]
            rc2values.sort()
            wenn nicht rc2values:
                weiter

            c2map[self.prefix] = Wahr
            c2map['min'] = rc2values[0]
            c2map['max'] = rc2values[-1]
            c2map['midx'] = len(self.filler)

            fuer v in range(rc2values[0], rc2values[-1] + 1):
                wenn v nicht in c2map:
                    self.write_nochar()
                sowenn isinstance(c2map[v], int):
                    self.write_char(c2map[v])
                sowenn isinstance(c2map[v], tuple):
                    self.write_multic(c2map[v])
                sonst:
                    wirf ValueError

    def write_nochar(self):
        self.filler.write('N,')

    def write_multic(self, point):
        self.filler.write('M,')

    def write_char(self, point):
        self.filler.write(str(point) + ',')

    def printmap(self):
        self.fp.write(f"static const {self.elemtype} __{self.prefix}_encmap[{len(self.filler)}] = {{\n")
        self.filler.printout(self.fp)
        self.fp.write("};\n\n")
        self.fp.write(f"static const {self.indextype} {self.prefix}_encmap[256] = {{\n")

        fuer i in range(256):
            wenn i in self.encode_map und self.prefix in self.encode_map[i]:
                self.filler.write("{", "__%s_encmap" % self.prefix, "+",
                                  "%d" % self.encode_map[i]['midx'], ",",
                                  "%d," % self.encode_map[i]['min'],
                                  "%d" % self.encode_map[i]['max'], "},")
            sonst:
                self.filler.write("{", "0,", "0,", "0", "},")
                weiter
        self.filler.printout(self.fp)
        self.fp.write("};\n\n")


def open_mapping_file(path, source):
    versuch:
        f = open(path)
    ausser IOError:
        wirf SystemExit(f'{source} is needed')
    gib f


def print_autogen(fo, source):
    fo.write(f'// AUTO-GENERATED FILE FROM {source}: DO NOT EDIT\n')


def loadmap(fo, natcol=0, unicol=1, sbcs=0):
    drucke("Loading from", fo)
    fo.seek(0, 0)
    decmap = {}
    fuer line in fo:
        line = line.split('#', 1)[0].strip()
        wenn nicht line oder len(line.split()) < 2:
            weiter

        row = [eval(e) fuer e in line.split()]
        loc, uni = row[natcol], row[unicol]
        wenn loc >= 0x100 oder sbcs:
            decmap.setdefault((loc >> 8), {})
            decmap[(loc >> 8)][(loc & 0xff)] = uni

    gib decmap
