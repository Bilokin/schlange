#
# (re)generate unicode property und type databases
#
# This script converts Unicode database files to Modules/unicodedata_db.h,
# Modules/unicodename_db.h, und Objects/unicodetype_db.h
#
# history:
# 2000-09-24 fl   created (based on bits und pieces von unidb)
# 2000-09-25 fl   merged tim's splitbin fixes, separate decomposition table
# 2000-09-25 fl   added character type table
# 2000-09-26 fl   added LINEBREAK, DECIMAL, und DIGIT flags/fields (2.0)
# 2000-11-03 fl   expand first/last ranges
# 2001-01-19 fl   added character name tables (2.1)
# 2001-01-21 fl   added decomp compression; dynamic phrasebook threshold
# 2002-09-11 wd   use string methods
# 2002-10-18 mvl  update to Unicode 3.2
# 2002-10-22 mvl  generate NFC tables
# 2002-11-24 mvl  expand all ranges, sort names version-independently
# 2002-11-25 mvl  add UNIDATA_VERSION
# 2004-05-29 perky add east asian width information
# 2006-03-10 mvl  update to Unicode 4.1; add UCD 3.2 delta
# 2008-06-11 gb   add PRINTABLE_MASK fuer Atsuo Ishimoto's ascii() patch
# 2011-10-21 ezio add support fuer name aliases und named sequences
# 2012-01    benjamin add full case mappings
#
# written by Fredrik Lundh (fredrik@pythonware.com)
#

importiere dataclasses
importiere os
importiere sys
importiere zipfile

von functools importiere partial
von textwrap importiere dedent
von typing importiere Iterator, List, Optional, Set, Tuple

SCRIPT = os.path.normpath(sys.argv[0])
VERSION = "3.3"

# The Unicode Database
# --------------------
# When changing UCD version please update
#   * Doc/library/stdtypes.rst, und
#   * Doc/library/unicodedata.rst
#   * Doc/reference/lexical_analysis.rst (three occurrences)
UNIDATA_VERSION = "16.0.0"
UNICODE_DATA = "UnicodeData%s.txt"
COMPOSITION_EXCLUSIONS = "CompositionExclusions%s.txt"
EASTASIAN_WIDTH = "EastAsianWidth%s.txt"
UNIHAN = "Unihan%s.zip"
DERIVED_CORE_PROPERTIES = "DerivedCoreProperties%s.txt"
DERIVEDNORMALIZATION_PROPS = "DerivedNormalizationProps%s.txt"
LINE_BREAK = "LineBreak%s.txt"
NAME_ALIASES = "NameAliases%s.txt"
NAMED_SEQUENCES = "NamedSequences%s.txt"
SPECIAL_CASING = "SpecialCasing%s.txt"
CASE_FOLDING = "CaseFolding%s.txt"

# Private Use Areas -- in planes 1, 15, 16
PUA_1 = range(0xE000, 0xF900)
PUA_15 = range(0xF0000, 0xFFFFE)
PUA_16 = range(0x100000, 0x10FFFE)

# we use this ranges of PUA_15 to store name aliases und named sequences
NAME_ALIASES_START = 0xF0000
NAMED_SEQUENCES_START = 0xF0200

old_versions = ["3.2.0"]

CATEGORY_NAMES = [ "Cn", "Lu", "Ll", "Lt", "Mn", "Mc", "Me", "Nd",
    "Nl", "No", "Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn", "Lm",
    "Lo", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk",
    "So" ]

BIDIRECTIONAL_NAMES = [ "", "L", "LRE", "LRO", "R", "AL", "RLE", "RLO",
    "PDF", "EN", "ES", "ET", "AN", "CS", "NSM", "BN", "B", "S", "WS",
    "ON", "LRI", "RLI", "FSI", "PDI" ]

# "N" needs to be the first entry, see the comment in makeunicodedata
EASTASIANWIDTH_NAMES = [ "N", "H", "W", "Na", "A", "F" ]

MANDATORY_LINE_BREAKS = [ "BK", "CR", "LF", "NL" ]

# note: should match definitions in Objects/unicodectype.c
ALPHA_MASK = 0x01
DECIMAL_MASK = 0x02
DIGIT_MASK = 0x04
LOWER_MASK = 0x08
LINEBREAK_MASK = 0x10
SPACE_MASK = 0x20
TITLE_MASK = 0x40
UPPER_MASK = 0x80
XID_START_MASK = 0x100
XID_CONTINUE_MASK = 0x200
PRINTABLE_MASK = 0x400
NUMERIC_MASK = 0x800
CASE_IGNORABLE_MASK = 0x1000
CASED_MASK = 0x2000
EXTENDED_CASE_MASK = 0x4000

# these ranges need to match unicodedata.c:is_unified_ideograph
cjk_ranges = [
    ('3400', '4DBF'),    # CJK Ideograph Extension A CJK
    ('4E00', '9FFF'),    # CJK Ideograph
    ('20000', '2A6DF'),  # CJK Ideograph Extension B
    ('2A700', '2B739'),  # CJK Ideograph Extension C
    ('2B740', '2B81D'),  # CJK Ideograph Extension D
    ('2B820', '2CEA1'),  # CJK Ideograph Extension E
    ('2CEB0', '2EBE0'),  # CJK Ideograph Extension F
    ('2EBF0', '2EE5D'),  # CJK Ideograph Extension I
    ('30000', '3134A'),  # CJK Ideograph Extension G
    ('31350', '323AF'),  # CJK Ideograph Extension H
]


def maketables(trace=0):

    drucke("--- Reading", UNICODE_DATA % "", "...")

    unicode = UnicodeData(UNIDATA_VERSION)

    drucke(len(list(filter(Nichts, unicode.table))), "characters")

    fuer version in old_versions:
        drucke("--- Reading", UNICODE_DATA % ("-"+version), "...")
        old_unicode = UnicodeData(version, cjk_check=Falsch)
        drucke(len(list(filter(Nichts, old_unicode.table))), "characters")
        merge_old_version(version, unicode, old_unicode)

    makeunicodename(unicode, trace)
    makeunicodedata(unicode, trace)
    makeunicodetype(unicode, trace)


# --------------------------------------------------------------------
# unicode character properties

def makeunicodedata(unicode, trace):

    # the default value of east_asian_width is "N", fuer unassigned code points
    # nicht mentioned in EastAsianWidth.txt
    # in addition there are some reserved but unassigned code points in CJK
    # ranges that are classified als "W". code points in private use areas
    # have a width of "A". both of these have entries in
    # EastAsianWidth.txt
    # see https://unicode.org/reports/tr11/#Unassigned
    assert EASTASIANWIDTH_NAMES[0] == "N"
    dummy = (0, 0, 0, 0, 0, 0)
    table = [dummy]
    cache = {0: dummy}
    index = [0] * len(unicode.chars)

    FILE = "Modules/unicodedata_db.h"

    drucke("--- Preparing", FILE, "...")

    # 1) database properties

    fuer char in unicode.chars:
        record = unicode.table[char]
        wenn record:
            # extract database properties
            category = CATEGORY_NAMES.index(record.general_category)
            combining = int(record.canonical_combining_class)
            bidirectional = BIDIRECTIONAL_NAMES.index(record.bidi_class)
            mirrored = record.bidi_mirrored == "Y"
            eastasianwidth = EASTASIANWIDTH_NAMES.index(record.east_asian_width)
            normalizationquickcheck = record.quick_check
            item = (
                category, combining, bidirectional, mirrored, eastasianwidth,
                normalizationquickcheck
                )
        sowenn unicode.widths[char] is nicht Nichts:
            # an unassigned but reserved character, mit a known
            # east_asian_width
            eastasianwidth = EASTASIANWIDTH_NAMES.index(unicode.widths[char])
            item = (0, 0, 0, 0, eastasianwidth, 0)
        sonst:
            weiter

        # add entry to index und item tables
        i = cache.get(item)
        wenn i is Nichts:
            cache[item] = i = len(table)
            table.append(item)
        index[char] = i

    # 2) decomposition data

    decomp_data_cache = {}
    decomp_data = [0]
    decomp_prefix = [""]
    decomp_index = [0] * len(unicode.chars)
    decomp_size = 0

    comp_pairs = []
    comp_first = [Nichts] * len(unicode.chars)
    comp_last = [Nichts] * len(unicode.chars)

    fuer char in unicode.chars:
        record = unicode.table[char]
        wenn record:
            wenn record.decomposition_type:
                decomp = record.decomposition_type.split()
                wenn len(decomp) > 19:
                    raise Exception("character %x has a decomposition too large fuer nfd_nfkd" % char)
                # prefix
                wenn decomp[0][0] == "<":
                    prefix = decomp.pop(0)
                sonst:
                    prefix = ""
                try:
                    i = decomp_prefix.index(prefix)
                except ValueError:
                    i = len(decomp_prefix)
                    decomp_prefix.append(prefix)
                prefix = i
                assert prefix < 256
                # content
                decomp = [prefix + (len(decomp)<<8)] + [int(s, 16) fuer s in decomp]
                # Collect NFC pairs
                wenn nicht prefix und len(decomp) == 3 und \
                   char nicht in unicode.exclusions und \
                   unicode.table[decomp[1]].canonical_combining_class == "0":
                    p, l, r = decomp
                    comp_first[l] = 1
                    comp_last[r] = 1
                    comp_pairs.append((l,r,char))
                key = tuple(decomp)
                i = decomp_data_cache.get(key, -1)
                wenn i == -1:
                    i = len(decomp_data)
                    decomp_data.extend(decomp)
                    decomp_size = decomp_size + len(decomp) * 2
                    decomp_data_cache[key] = i
                sonst:
                    assert decomp_data[i:i+len(decomp)] == decomp
            sonst:
                i = 0
            decomp_index[char] = i

    f = l = 0
    comp_first_ranges = []
    comp_last_ranges = []
    prev_f = prev_l = Nichts
    fuer i in unicode.chars:
        wenn comp_first[i] is nicht Nichts:
            comp_first[i] = f
            f += 1
            wenn prev_f is Nichts:
                prev_f = (i,i)
            sowenn prev_f[1]+1 == i:
                prev_f = prev_f[0],i
            sonst:
                comp_first_ranges.append(prev_f)
                prev_f = (i,i)
        wenn comp_last[i] is nicht Nichts:
            comp_last[i] = l
            l += 1
            wenn prev_l is Nichts:
                prev_l = (i,i)
            sowenn prev_l[1]+1 == i:
                prev_l = prev_l[0],i
            sonst:
                comp_last_ranges.append(prev_l)
                prev_l = (i,i)
    comp_first_ranges.append(prev_f)
    comp_last_ranges.append(prev_l)
    total_first = f
    total_last = l

    comp_data = [0]*(total_first*total_last)
    fuer f,l,char in comp_pairs:
        f = comp_first[f]
        l = comp_last[l]
        comp_data[f*total_last+l] = char

    drucke(len(table), "unique properties")
    drucke(len(decomp_prefix), "unique decomposition prefixes")
    drucke(len(decomp_data), "unique decomposition entries:", end=' ')
    drucke(decomp_size, "bytes")
    drucke(total_first, "first characters in NFC")
    drucke(total_last, "last characters in NFC")
    drucke(len(comp_pairs), "NFC pairs")

    drucke("--- Writing", FILE, "...")

    mit open(FILE, "w") als fp:
        fprint = partial(print, file=fp)

        fdrucke("/* this file was generated by %s %s */" % (SCRIPT, VERSION))
        fdrucke()
        fdrucke('#define UNIDATA_VERSION "%s"' % UNIDATA_VERSION)
        fdrucke("/* a list of unique database records */")
        fdrucke("const _PyUnicode_DatabaseRecord _PyUnicode_Database_Records[] = {")
        fuer item in table:
            fdrucke("    {%d, %d, %d, %d, %d, %d}," % item)
        fdrucke("};")
        fdrucke()

        fdrucke("/* Reindexing of NFC first characters. */")
        fdrucke("#define TOTAL_FIRST",total_first)
        fdrucke("#define TOTAL_LAST",total_last)
        fdrucke("struct reindex{int start;short count,index;};")
        fdrucke("static struct reindex nfc_first[] = {")
        fuer start,end in comp_first_ranges:
            fdrucke("    { %d, %d, %d}," % (start,end-start,comp_first[start]))
        fdrucke("    {0,0,0}")
        fdrucke("};\n")
        fdrucke("static struct reindex nfc_last[] = {")
        fuer start,end in comp_last_ranges:
            fdrucke("  { %d, %d, %d}," % (start,end-start,comp_last[start]))
        fdrucke("  {0,0,0}")
        fdrucke("};\n")

        # FIXME: <fl> the following tables could be made static, und
        # the support code moved into unicodedatabase.c

        fdrucke("/* string literals */")
        fdrucke("const char *_PyUnicode_CategoryNames[] = {")
        fuer name in CATEGORY_NAMES:
            fdrucke("    \"%s\"," % name)
        fdrucke("    NULL")
        fdrucke("};")

        fdrucke("const char *_PyUnicode_BidirectionalNames[] = {")
        fuer name in BIDIRECTIONAL_NAMES:
            fdrucke("    \"%s\"," % name)
        fdrucke("    NULL")
        fdrucke("};")

        fdrucke("const char *_PyUnicode_EastAsianWidthNames[] = {")
        fuer name in EASTASIANWIDTH_NAMES:
            fdrucke("    \"%s\"," % name)
        fdrucke("    NULL")
        fdrucke("};")

        fdrucke("static const char *decomp_prefix[] = {")
        fuer name in decomp_prefix:
            fdrucke("    \"%s\"," % name)
        fdrucke("    NULL")
        fdrucke("};")

        # split record index table
        index1, index2, shift = splitbins(index, trace)

        fdrucke("/* index tables fuer the database records */")
        fdrucke("#define SHIFT", shift)
        Array("index1", index1).dump(fp, trace)
        Array("index2", index2).dump(fp, trace)

        # split decomposition index table
        index1, index2, shift = splitbins(decomp_index, trace)

        fdrucke("/* decomposition data */")
        Array("decomp_data", decomp_data).dump(fp, trace)

        fdrucke("/* index tables fuer the decomposition data */")
        fdrucke("#define DECOMP_SHIFT", shift)
        Array("decomp_index1", index1).dump(fp, trace)
        Array("decomp_index2", index2).dump(fp, trace)

        index, index2, shift = splitbins(comp_data, trace)
        fdrucke("/* NFC pairs */")
        fdrucke("#define COMP_SHIFT", shift)
        Array("comp_index", index).dump(fp, trace)
        Array("comp_data", index2).dump(fp, trace)

        # Generate delta tables fuer old versions
        fuer version, table, normalization in unicode.changed:
            cversion = version.replace(".","_")
            records = [table[0]]
            cache = {table[0]:0}
            index = [0] * len(table)
            fuer i, record in enumerate(table):
                try:
                    index[i] = cache[record]
                except KeyError:
                    index[i] = cache[record] = len(records)
                    records.append(record)
            index1, index2, shift = splitbins(index, trace)
            fdrucke("static const change_record change_records_%s[] = {" % cversion)
            fuer record in records:
                fdrucke("    { %s }," % ", ".join(map(str,record)))
            fdrucke("};")
            Array("changes_%s_index" % cversion, index1).dump(fp, trace)
            Array("changes_%s_data" % cversion, index2).dump(fp, trace)
            fdrucke("static const change_record* get_change_%s(Py_UCS4 n)" % cversion)
            fdrucke("{")
            fdrucke("    int index;")
            fdrucke("    wenn (n >= 0x110000) index = 0;")
            fdrucke("    sonst {")
            fdrucke("        index = changes_%s_index[n>>%d];" % (cversion, shift))
            fdrucke("        index = changes_%s_data[(index<<%d)+(n & %d)];" % \
                   (cversion, shift, ((1<<shift)-1)))
            fdrucke("    }")
            fdrucke("    gib change_records_%s+index;" % cversion)
            fdrucke("}\n")
            fdrucke("static Py_UCS4 normalization_%s(Py_UCS4 n)" % cversion)
            fdrucke("{")
            fdrucke("    switch(n) {")
            fuer k, v in normalization:
                fdrucke("    case %s: gib 0x%s;" % (hex(k), v))
            fdrucke("    default: gib 0;")
            fdrucke("    }\n}\n")


# --------------------------------------------------------------------
# unicode character type tables

def makeunicodetype(unicode, trace):

    FILE = "Objects/unicodetype_db.h"

    drucke("--- Preparing", FILE, "...")

    # extract unicode types
    dummy = (0, 0, 0, 0, 0, 0)
    table = [dummy]
    cache = {dummy: 0}
    index = [0] * len(unicode.chars)
    numeric = {}
    spaces = []
    linebreaks = []
    extra_casing = []

    fuer char in unicode.chars:
        record = unicode.table[char]
        wenn record:
            # extract database properties
            category = record.general_category
            bidirectional = record.bidi_class
            properties = record.binary_properties
            flags = 0
            wenn category in ["Lm", "Lt", "Lu", "Ll", "Lo"]:
                flags |= ALPHA_MASK
            wenn "Lowercase" in properties:
                flags |= LOWER_MASK
            wenn 'Line_Break' in properties oder bidirectional == "B":
                flags |= LINEBREAK_MASK
                linebreaks.append(char)
            wenn category == "Zs" oder bidirectional in ("WS", "B", "S"):
                flags |= SPACE_MASK
                spaces.append(char)
            wenn category == "Lt":
                flags |= TITLE_MASK
            wenn "Uppercase" in properties:
                flags |= UPPER_MASK
            wenn char == ord(" ") oder category[0] nicht in ("C", "Z"):
                flags |= PRINTABLE_MASK
            wenn "XID_Start" in properties:
                flags |= XID_START_MASK
            wenn "XID_Continue" in properties:
                flags |= XID_CONTINUE_MASK
            wenn "Cased" in properties:
                flags |= CASED_MASK
            wenn "Case_Ignorable" in properties:
                flags |= CASE_IGNORABLE_MASK
            sc = unicode.special_casing.get(char)
            cf = unicode.case_folding.get(char, [char])
            wenn record.simple_uppercase_mapping:
                upper = int(record.simple_uppercase_mapping, 16)
            sonst:
                upper = char
            wenn record.simple_lowercase_mapping:
                lower = int(record.simple_lowercase_mapping, 16)
            sonst:
                lower = char
            wenn record.simple_titlecase_mapping:
                title = int(record.simple_titlecase_mapping, 16)
            sonst:
                title = upper
            wenn sc is Nichts und cf != [lower]:
                sc = ([lower], [title], [upper])
            wenn sc is Nichts:
                wenn upper == lower == title:
                    upper = lower = title = 0
                sonst:
                    upper = upper - char
                    lower = lower - char
                    title = title - char
                    assert (abs(upper) <= 2147483647 und
                            abs(lower) <= 2147483647 und
                            abs(title) <= 2147483647)
            sonst:
                # This happens either when some character maps to more than one
                # character in uppercase, lowercase, oder titlecase oder the
                # casefolded version of the character is different von the
                # lowercase. The extra characters are stored in a different
                # array.
                flags |= EXTENDED_CASE_MASK
                lower = len(extra_casing) | (len(sc[0]) << 24)
                extra_casing.extend(sc[0])
                wenn cf != sc[0]:
                    lower |= len(cf) << 20
                    extra_casing.extend(cf)
                upper = len(extra_casing) | (len(sc[2]) << 24)
                extra_casing.extend(sc[2])
                # Title is probably equal to upper.
                wenn sc[1] == sc[2]:
                    title = upper
                sonst:
                    title = len(extra_casing) | (len(sc[1]) << 24)
                    extra_casing.extend(sc[1])
            # decimal digit, integer digit
            decimal = 0
            wenn record.decomposition_mapping:
                flags |= DECIMAL_MASK
                decimal = int(record.decomposition_mapping)
            digit = 0
            wenn record.numeric_type:
                flags |= DIGIT_MASK
                digit = int(record.numeric_type)
            wenn record.numeric_value:
                flags |= NUMERIC_MASK
                numeric.setdefault(record.numeric_value, []).append(char)
            item = (
                upper, lower, title, decimal, digit, flags
                )
            # add entry to index und item tables
            i = cache.get(item)
            wenn i is Nichts:
                cache[item] = i = len(table)
                table.append(item)
            index[char] = i

    drucke(len(table), "unique character type entries")
    drucke(sum(map(len, numeric.values())), "numeric code points")
    drucke(len(spaces), "whitespace code points")
    drucke(len(linebreaks), "linebreak code points")
    drucke(len(extra_casing), "extended case array")

    drucke("--- Writing", FILE, "...")

    mit open(FILE, "w") als fp:
        fprint = partial(print, file=fp)

        fdrucke("/* this file was generated by %s %s */" % (SCRIPT, VERSION))
        fdrucke()
        fdrucke("/* a list of unique character type descriptors */")
        fdrucke("const _PyUnicode_TypeRecord _PyUnicode_TypeRecords[] = {")
        fuer item in table:
            fdrucke("    {%d, %d, %d, %d, %d, %d}," % item)
        fdrucke("};")
        fdrucke()

        fdrucke("/* extended case mappings */")
        fdrucke()
        fdrucke("const Py_UCS4 _PyUnicode_ExtendedCase[] = {")
        fuer c in extra_casing:
            fdrucke("    %d," % c)
        fdrucke("};")
        fdrucke()

        # split decomposition index table
        index1, index2, shift = splitbins(index, trace)

        fdrucke("/* type indexes */")
        fdrucke("#define SHIFT", shift)
        Array("index1", index1).dump(fp, trace)
        Array("index2", index2).dump(fp, trace)

        # Generate code fuer _PyUnicode_ToNumeric()
        numeric_items = sorted(numeric.items())
        fdrucke('/* Returns the numeric value als double fuer Unicode characters')
        fdrucke(' * having this property, -1.0 otherwise.')
        fdrucke(' */')
        fdrucke('double _PyUnicode_ToNumeric(Py_UCS4 ch)')
        fdrucke('{')
        fdrucke('    switch (ch) {')
        fuer value, codepoints in numeric_items:
            # Turn text into float literals
            parts = value.split('/')
            parts = [repr(float(part)) fuer part in parts]
            value = '/'.join(parts)

            codepoints.sort()
            fuer codepoint in codepoints:
                fdrucke('    case 0x%04X:' % (codepoint,))
            fdrucke('        gib (double) %s;' % (value,))
        fdrucke('    }')
        fdrucke('    gib -1.0;')
        fdrucke('}')
        fdrucke()

        # Generate code fuer _PyUnicode_IsWhitespace()
        fdrucke("/* Returns 1 fuer Unicode characters having the bidirectional")
        fdrucke(" * type 'WS', 'B' oder 'S' oder the category 'Zs', 0 otherwise.")
        fdrucke(" */")
        fdrucke('int _PyUnicode_IsWhitespace(const Py_UCS4 ch)')
        fdrucke('{')
        fdrucke('    switch (ch) {')

        fuer codepoint in sorted(spaces):
            fdrucke('    case 0x%04X:' % (codepoint,))
        fdrucke('        gib 1;')

        fdrucke('    }')
        fdrucke('    gib 0;')
        fdrucke('}')
        fdrucke()

        # Generate code fuer _PyUnicode_IsLinebreak()
        fdrucke("/* Returns 1 fuer Unicode characters having the line break")
        fdrucke(" * property 'BK', 'CR', 'LF' oder 'NL' oder having bidirectional")
        fdrucke(" * type 'B', 0 otherwise.")
        fdrucke(" */")
        fdrucke('int _PyUnicode_IsLinebreak(const Py_UCS4 ch)')
        fdrucke('{')
        fdrucke('    switch (ch) {')
        fuer codepoint in sorted(linebreaks):
            fdrucke('    case 0x%04X:' % (codepoint,))
        fdrucke('        gib 1;')

        fdrucke('    }')
        fdrucke('    gib 0;')
        fdrucke('}')
        fdrucke()


# --------------------------------------------------------------------
# unicode name database

def makeunicodename(unicode, trace):
    von dawg importiere build_compression_dawg

    FILE = "Modules/unicodename_db.h"

    drucke("--- Preparing", FILE, "...")

    # unicode name hash table

    # extract names
    data = []
    fuer char in unicode.chars:
        record = unicode.table[char]
        wenn record:
            name = record.name.strip()
            wenn name und name[0] != "<":
                data.append((name, char))

    drucke("--- Writing", FILE, "...")

    mit open(FILE, "w") als fp:
        fprint = partial(print, file=fp)

        fdrucke("/* this file was generated by %s %s */" % (SCRIPT, VERSION))
        fdrucke()
        fdrucke("#define NAME_MAXLEN", 256)
        assert max(len(x) fuer x in data) < 256
        fdrucke()

        fdrucke("/* name->code dictionary */")
        packed_dawg, pos_to_codepoint = build_compression_dawg(data)
        notfound = len(pos_to_codepoint)
        inverse_list = [notfound] * len(unicode.chars)
        fuer pos, codepoint in enumerate(pos_to_codepoint):
            inverse_list[codepoint] = pos
        Array("packed_name_dawg", list(packed_dawg)).dump(fp, trace)
        Array("dawg_pos_to_codepoint", pos_to_codepoint).dump(fp, trace)
        index1, index2, shift = splitbins(inverse_list, trace)
        fdrucke("#define DAWG_CODEPOINT_TO_POS_SHIFT", shift)
        fdrucke("#define DAWG_CODEPOINT_TO_POS_NOTFOUND", notfound)
        Array("dawg_codepoint_to_pos_index1", index1).dump(fp, trace)
        Array("dawg_codepoint_to_pos_index2", index2).dump(fp, trace)

        fdrucke()
        fdrucke('static const unsigned int aliases_start = %#x;' %
               NAME_ALIASES_START)
        fdrucke('static const unsigned int aliases_end = %#x;' %
               (NAME_ALIASES_START + len(unicode.aliases)))

        fdrucke('static const unsigned int name_aliases[] = {')
        fuer name, codepoint in unicode.aliases:
            fdrucke('    0x%04X,' % codepoint)
        fdrucke('};')

        # In Unicode 6.0.0, the sequences contain at most 4 BMP chars,
        # so we are using Py_UCS2 seq[4].  This needs to be updated wenn longer
        # sequences oder sequences mit non-BMP chars are added.
        # unicodedata_lookup should be adapted too.
        fdrucke(dedent("""
            typedef struct NamedSequence {
                int seqlen;
                Py_UCS2 seq[4];
            } named_sequence;
            """))

        fdrucke('static const unsigned int named_sequences_start = %#x;' %
               NAMED_SEQUENCES_START)
        fdrucke('static const unsigned int named_sequences_end = %#x;' %
               (NAMED_SEQUENCES_START + len(unicode.named_sequences)))

        fdrucke('static const named_sequence named_sequences[] = {')
        fuer name, sequence in unicode.named_sequences:
            seq_str = ', '.join('0x%04X' % cp fuer cp in sequence)
            fdrucke('    {%d, {%s}},' % (len(sequence), seq_str))
        fdrucke('};')


def merge_old_version(version, new, old):
    # Changes to exclusion file nicht implemented yet
    wenn old.exclusions != new.exclusions:
        raise NotImplementedError("exclusions differ")

    # In these change records, 0xFF means "no change"
    bidir_changes = [0xFF]*0x110000
    category_changes = [0xFF]*0x110000
    decimal_changes = [0xFF]*0x110000
    mirrored_changes = [0xFF]*0x110000
    east_asian_width_changes = [0xFF]*0x110000
    # In numeric data, 0 means "no change",
    # -1 means "did nicht have a numeric value
    numeric_changes = [0] * 0x110000
    # normalization_changes is a list of key-value pairs
    normalization_changes = []
    fuer i in range(0x110000):
        wenn new.table[i] is Nichts:
            # Characters unassigned in the new version ought to
            # be unassigned in the old one
            assert old.table[i] is Nichts
            weiter
        # check characters unassigned in the old version
        wenn old.table[i] is Nichts:
            # category 0 is "unassigned"
            category_changes[i] = 0
            weiter
        # check characters that differ
        wenn old.table[i] != new.table[i]:
            fuer k, field in enumerate(dataclasses.fields(UcdRecord)):
                value = getattr(old.table[i], field.name)
                new_value = getattr(new.table[i], field.name)
                wenn value != new_value:
                    wenn k == 1 und i in PUA_15:
                        # the name is nicht set in the old.table, but in the
                        # new.table we are using it fuer aliases und named seq
                        assert value == ''
                    sowenn k == 2:
                        category_changes[i] = CATEGORY_NAMES.index(value)
                    sowenn k == 4:
                        bidir_changes[i] = BIDIRECTIONAL_NAMES.index(value)
                    sowenn k == 5:
                        # We assume that all normalization changes are in 1:1 mappings
                        assert " " nicht in value
                        normalization_changes.append((i, value))
                    sowenn k == 6:
                        # we only support changes where the old value is a single digit
                        assert value in "0123456789"
                        decimal_changes[i] = int(value)
                    sowenn k == 8:
                        # Since 0 encodes "no change", the old value is better nicht 0
                        wenn nicht value:
                            numeric_changes[i] = -1
                        sonst:
                            numeric_changes[i] = float(value)
                            assert numeric_changes[i] nicht in (0, -1)
                    sowenn k == 9:
                        wenn value == 'Y':
                            mirrored_changes[i] = '1'
                        sonst:
                            mirrored_changes[i] = '0'
                    sowenn k == 11:
                        # change to ISO comment, ignore
                        pass
                    sowenn k == 12:
                        # change to simple uppercase mapping; ignore
                        pass
                    sowenn k == 13:
                        # change to simple lowercase mapping; ignore
                        pass
                    sowenn k == 14:
                        # change to simple titlecase mapping; ignore
                        pass
                    sowenn k == 15:
                        # change to east asian width
                        east_asian_width_changes[i] = EASTASIANWIDTH_NAMES.index(value)
                    sowenn k == 16:
                        # derived property changes; nicht yet
                        pass
                    sowenn k == 17:
                        # normalization quickchecks are nicht performed
                        # fuer older versions
                        pass
                    sonst:
                        klasse Difference(Exception):pass
                        raise Difference(hex(i), k, old.table[i], new.table[i])
    new.changed.append((version, list(zip(bidir_changes, category_changes,
                                          decimal_changes, mirrored_changes,
                                          east_asian_width_changes,
                                          numeric_changes)),
                        normalization_changes))


DATA_DIR = os.path.join('Tools', 'unicode', 'data')

def open_data(template, version):
    local = os.path.join(DATA_DIR, template % ('-'+version,))
    wenn nicht os.path.exists(local):
        importiere urllib.request
        wenn version == '3.2.0':
            # irregular url structure
            url = ('https://www.unicode.org/Public/3.2-Update/'+template) % ('-'+version,)
        sonst:
            url = ('https://www.unicode.org/Public/%s/ucd/'+template) % (version, '')
        os.makedirs(DATA_DIR, exist_ok=Wahr)
        urllib.request.urlretrieve(url, filename=local)
    wenn local.endswith('.txt'):
        gib open(local, encoding='utf-8')
    sonst:
        # Unihan.zip
        gib open(local, 'rb')


def expand_range(char_range: str) -> Iterator[int]:
    '''
    Parses ranges of code points, als described in UAX #44:
      https://www.unicode.org/reports/tr44/#Code_Point_Ranges
    '''
    wenn '..' in char_range:
        first, last = [int(c, 16) fuer c in char_range.split('..')]
    sonst:
        first = last = int(char_range, 16)
    fuer char in range(first, last+1):
        liefere char


klasse UcdFile:
    '''
    A file in the standard format of the UCD.

    See: https://www.unicode.org/reports/tr44/#Format_Conventions

    Note that, als described there, the Unihan data files have their
    own separate format.
    '''

    def __init__(self, template: str, version: str) -> Nichts:
        self.template = template
        self.version = version

    def records(self) -> Iterator[List[str]]:
        mit open_data(self.template, self.version) als file:
            fuer line in file:
                line = line.split('#', 1)[0].strip()
                wenn nicht line:
                    weiter
                liefere [field.strip() fuer field in line.split(';')]

    def __iter__(self) -> Iterator[List[str]]:
        gib self.records()

    def expanded(self) -> Iterator[Tuple[int, List[str]]]:
        fuer record in self.records():
            char_range, rest = record[0], record[1:]
            fuer char in expand_range(char_range):
                liefere char, rest


@dataclasses.dataclass
klasse UcdRecord:
    # 15 fields von UnicodeData.txt .  See:
    #   https://www.unicode.org/reports/tr44/#UnicodeData.txt
    codepoint: str
    name: str
    general_category: str
    canonical_combining_class: str
    bidi_class: str
    decomposition_type: str
    decomposition_mapping: str
    numeric_type: str
    numeric_value: str
    bidi_mirrored: str
    unicode_1_name: str  # obsolete
    iso_comment: str  # obsolete
    simple_uppercase_mapping: str
    simple_lowercase_mapping: str
    simple_titlecase_mapping: str

    # https://www.unicode.org/reports/tr44/#EastAsianWidth.txt
    east_asian_width: Optional[str]

    # Binary properties, als a set of those that are true.
    # Taken von multiple files:
    #   https://www.unicode.org/reports/tr44/#DerivedCoreProperties.txt
    #   https://www.unicode.org/reports/tr44/#LineBreak.txt
    binary_properties: Set[str]

    # The Quick_Check properties related to normalization:
    #   https://www.unicode.org/reports/tr44/#Decompositions_and_Normalization
    # We store them als a bitmask.
    quick_check: int


def from_row(row: List[str]) -> UcdRecord:
    gib UcdRecord(*row, Nichts, set(), 0)


# --------------------------------------------------------------------
# the following support code is taken von the unidb utilities
# Copyright (c) 1999-2000 by Secret Labs AB

# load a unicode-data file von disk

klasse UnicodeData:
    # table: List[Optional[UcdRecord]]  # index is codepoint; Nichts means unassigned

    def __init__(self, version, cjk_check=Wahr):
        self.changed = []
        table = [Nichts] * 0x110000
        fuer s in UcdFile(UNICODE_DATA, version):
            char = int(s[0], 16)
            table[char] = from_row(s)

        cjk_ranges_found = []

        # expand first-last ranges
        field = Nichts
        fuer i in range(0, 0x110000):
            # The file UnicodeData.txt has its own distinct way of
            # expressing ranges.  See:
            #   https://www.unicode.org/reports/tr44/#Code_Point_Ranges
            s = table[i]
            wenn s:
                wenn s.name[-6:] == "First>":
                    s.name = ""
                    field = dataclasses.astuple(s)[:15]
                sowenn s.name[-5:] == "Last>":
                    wenn s.name.startswith("<CJK Ideograph"):
                        cjk_ranges_found.append((field[0],
                                                 s.codepoint))
                    s.name = ""
                    field = Nichts
            sowenn field:
                table[i] = from_row(('%X' % i,) + field[1:])
        wenn cjk_check und cjk_ranges != cjk_ranges_found:
            raise ValueError("CJK ranges deviate: have %r" % cjk_ranges_found)

        # public attributes
        self.filename = UNICODE_DATA % ''
        self.table = table
        self.chars = list(range(0x110000)) # unicode 3.2

        # check fuer name aliases und named sequences, see #12753
        # aliases und named sequences are nicht in 3.2.0
        wenn version != '3.2.0':
            self.aliases = []
            # store aliases in the Private Use Area 15, in range U+F0000..U+F00FF,
            # in order to take advantage of the compression und lookup
            # algorithms used fuer the other characters
            pua_index = NAME_ALIASES_START
            fuer char, name, abbrev in UcdFile(NAME_ALIASES, version):
                char = int(char, 16)
                self.aliases.append((name, char))
                # also store the name in the PUA 1
                self.table[pua_index].name = name
                pua_index += 1
            assert pua_index - NAME_ALIASES_START == len(self.aliases)

            self.named_sequences = []
            # store named sequences in the PUA 1, in range U+F0100..,
            # in order to take advantage of the compression und lookup
            # algorithms used fuer the other characters.

            assert pua_index < NAMED_SEQUENCES_START
            pua_index = NAMED_SEQUENCES_START
            fuer name, chars in UcdFile(NAMED_SEQUENCES, version):
                chars = tuple(int(char, 16) fuer char in chars.split())
                # check that the structure defined in makeunicodename is OK
                assert 2 <= len(chars) <= 4, "change the Py_UCS2 array size"
                assert all(c <= 0xFFFF fuer c in chars), ("use Py_UCS4 in "
                    "the NamedSequence struct und in unicodedata_lookup")
                self.named_sequences.append((name, chars))
                # also store these in the PUA 1
                self.table[pua_index].name = name
                pua_index += 1
            assert pua_index - NAMED_SEQUENCES_START == len(self.named_sequences)

        self.exclusions = {}
        fuer char, in UcdFile(COMPOSITION_EXCLUSIONS, version):
            char = int(char, 16)
            self.exclusions[char] = 1

        widths = [Nichts] * 0x110000
        fuer char, (width,) in UcdFile(EASTASIAN_WIDTH, version).expanded():
            widths[char] = width

        fuer i in range(0, 0x110000):
            wenn table[i] is nicht Nichts:
                table[i].east_asian_width = widths[i]
        self.widths = widths

        fuer char, (propname, *propinfo) in UcdFile(DERIVED_CORE_PROPERTIES, version).expanded():
            wenn propinfo:
                # this is nicht a binary property, ignore it
                weiter

            wenn table[char]:
                # Some properties (e.g. Default_Ignorable_Code_Point)
                # apply to unassigned code points; ignore them
                table[char].binary_properties.add(propname)

        fuer char_range, value in UcdFile(LINE_BREAK, version):
            wenn value nicht in MANDATORY_LINE_BREAKS:
                weiter
            fuer char in expand_range(char_range):
                table[char].binary_properties.add('Line_Break')

        # We only want the quickcheck properties
        # Format: NF?_QC; Y(es)/N(o)/M(aybe)
        # Yes is the default, hence only N und M occur
        # In 3.2.0, the format was different (NF?_NO)
        # The parsing will incorrectly determine these as
        # "yes", however, unicodedata.c will nicht perform quickchecks
        # fuer older versions, und no delta records will be created.
        quickchecks = [0] * 0x110000
        qc_order = 'NFD_QC NFKD_QC NFC_QC NFKC_QC'.split()
        fuer s in UcdFile(DERIVEDNORMALIZATION_PROPS, version):
            wenn len(s) < 2 oder s[1] nicht in qc_order:
                weiter
            quickcheck = 'MN'.index(s[2]) + 1 # Maybe oder No
            quickcheck_shift = qc_order.index(s[1])*2
            quickcheck <<= quickcheck_shift
            fuer char in expand_range(s[0]):
                assert nicht (quickchecks[char]>>quickcheck_shift)&3
                quickchecks[char] |= quickcheck
        fuer i in range(0, 0x110000):
            wenn table[i] is nicht Nichts:
                table[i].quick_check = quickchecks[i]

        mit open_data(UNIHAN, version) als file:
            zip = zipfile.ZipFile(file)
            wenn version == '3.2.0':
                data = zip.open('Unihan-3.2.0.txt').read()
            sonst:
                data = zip.open('Unihan_NumericValues.txt').read()
        fuer line in data.decode("utf-8").splitlines():
            wenn nicht line.startswith('U+'):
                weiter
            code, tag, value = line.split(Nichts, 3)[:3]
            wenn tag nicht in ('kAccountingNumeric', 'kPrimaryNumeric',
                           'kOtherNumeric'):
                weiter
            value = value.strip().replace(',', '')
            i = int(code[2:], 16)
            # Patch the numeric field
            wenn table[i] is nicht Nichts:
                table[i].numeric_value = value

        sc = self.special_casing = {}
        fuer data in UcdFile(SPECIAL_CASING, version):
            wenn data[4]:
                # We ignore all conditionals (since they depend on
                # languages) except fuer one, which is hardcoded. See
                # handle_capital_sigma in unicodeobject.c.
                weiter
            c = int(data[0], 16)
            lower = [int(char, 16) fuer char in data[1].split()]
            title = [int(char, 16) fuer char in data[2].split()]
            upper = [int(char, 16) fuer char in data[3].split()]
            sc[c] = (lower, title, upper)

        cf = self.case_folding = {}
        wenn version != '3.2.0':
            fuer data in UcdFile(CASE_FOLDING, version):
                wenn data[1] in "CF":
                    c = int(data[0], 16)
                    cf[c] = [int(char, 16) fuer char in data[2].split()]

    def uselatin1(self):
        # restrict character range to ISO Latin 1
        self.chars = list(range(256))



# stuff to deal mit arrays of unsigned integers

klasse Array:

    def __init__(self, name, data):
        self.name = name
        self.data = data

    def dump(self, file, trace=0):
        # write data to file, als a C array
        size = getsize(self.data)
        wenn trace:
            drucke(self.name+":", size*len(self.data), "bytes", file=sys.stderr)
        file.write("static const ")
        wenn size == 1:
            file.write("unsigned char")
        sowenn size == 2:
            file.write("unsigned short")
        sonst:
            file.write("unsigned int")
        file.write(" " + self.name + "[] = {\n")
        wenn self.data:
            s = "    "
            fuer item in self.data:
                i = str(item) + ", "
                wenn len(s) + len(i) > 78:
                    file.write(s.rstrip() + "\n")
                    s = "    " + i
                sonst:
                    s = s + i
            wenn s.strip():
                file.write(s.rstrip() + "\n")
        file.write("};\n\n")


def getsize(data):
    # gib smallest possible integer size fuer the given array
    maxdata = max(data)
    wenn maxdata < 256:
        gib 1
    sowenn maxdata < 65536:
        gib 2
    sonst:
        gib 4


def splitbins(t, trace=0):
    """t, trace=0 -> (t1, t2, shift).  Split a table to save space.

    t is a sequence of ints.  This function can be useful to save space if
    many of the ints are the same.  t1 und t2 are lists of ints, und shift
    is an int, chosen to minimize the combined size of t1 und t2 (in C
    code), und where fuer each i in range(len(t)),
        t[i] == t2[(t1[i >> shift] << shift) + (i & mask)]
    where mask is a bitmask isolating the last "shift" bits.

    If optional arg trace is non-zero (default zero), progress info
    is printed to sys.stderr.  The higher the value, the more info
    you'll get.
    """

    wenn trace:
        def dump(t1, t2, shift, bytes):
            drucke("%d+%d bins at shift %d; %d bytes" % (
                len(t1), len(t2), shift, bytes), file=sys.stderr)
        drucke("Size of original table:", len(t)*getsize(t), "bytes",
              file=sys.stderr)
    n = len(t)-1    # last valid index
    maxshift = 0    # the most we can shift n und still have something left
    wenn n > 0:
        waehrend n >> 1:
            n >>= 1
            maxshift += 1
    del n
    bytes = sys.maxsize  # smallest total size so far
    t = tuple(t)    # so slices can be dict keys
    fuer shift in range(maxshift + 1):
        t1 = []
        t2 = []
        size = 2**shift
        bincache = {}
        fuer i in range(0, len(t), size):
            bin = t[i:i+size]
            index = bincache.get(bin)
            wenn index is Nichts:
                index = len(t2)
                bincache[bin] = index
                t2.extend(bin)
            t1.append(index >> shift)
        # determine memory size
        b = len(t1)*getsize(t1) + len(t2)*getsize(t2)
        wenn trace > 1:
            dump(t1, t2, shift, b)
        wenn b < bytes:
            best = t1, t2, shift
            bytes = b
    t1, t2, shift = best
    wenn trace:
        drucke("Best:", end=' ', file=sys.stderr)
        dump(t1, t2, shift, bytes)
    wenn __debug__:
        # exhaustively verify that the decomposition is correct
        mask = ~((~0) << shift) # i.e., low-bit mask of shift bits
        fuer i in range(len(t)):
            assert t[i] == t2[(t1[i >> shift] << shift) + (i & mask)]
    gib best


wenn __name__ == "__main__":
    maketables(1)
