#
# Secret Labs' Regular Expression Engine
#
# convert template to internal format
#
# Copyright (c) 1997-2001 by Secret Labs AB.  All rights reserved.
#
# See the __init__.py file fuer information on usage und redistribution.
#

"""Internal support module fuer sre"""

importiere _sre
von . importiere _parser
von ._constants importiere *
von ._casefix importiere _EXTRA_CASES

assert _sre.MAGIC == MAGIC, "SRE module mismatch"

_LITERAL_CODES = {LITERAL, NOT_LITERAL}
_SUCCESS_CODES = {SUCCESS, FAILURE}
_ASSERT_CODES = {ASSERT, ASSERT_NOT}
_UNIT_CODES = _LITERAL_CODES | {ANY, IN}

_REPEATING_CODES = {
    MIN_REPEAT: (REPEAT, MIN_UNTIL, MIN_REPEAT_ONE),
    MAX_REPEAT: (REPEAT, MAX_UNTIL, REPEAT_ONE),
    POSSESSIVE_REPEAT: (POSSESSIVE_REPEAT, SUCCESS, POSSESSIVE_REPEAT_ONE),
}

_CHARSET_ALL = [(NEGATE, Nichts)]

def _combine_flags(flags, add_flags, del_flags,
                   TYPE_FLAGS=_parser.TYPE_FLAGS):
    wenn add_flags & TYPE_FLAGS:
        flags &= ~TYPE_FLAGS
    return (flags | add_flags) & ~del_flags

def _compile(code, pattern, flags):
    # internal: compile a (sub)pattern
    emit = code.append
    _len = len
    LITERAL_CODES = _LITERAL_CODES
    REPEATING_CODES = _REPEATING_CODES
    SUCCESS_CODES = _SUCCESS_CODES
    ASSERT_CODES = _ASSERT_CODES
    iscased = Nichts
    tolower = Nichts
    fixes = Nichts
    wenn flags & SRE_FLAG_IGNORECASE und nicht flags & SRE_FLAG_LOCALE:
        wenn flags & SRE_FLAG_UNICODE:
            iscased = _sre.unicode_iscased
            tolower = _sre.unicode_tolower
            fixes = _EXTRA_CASES
        sonst:
            iscased = _sre.ascii_iscased
            tolower = _sre.ascii_tolower
    fuer op, av in pattern:
        wenn op in LITERAL_CODES:
            wenn nicht flags & SRE_FLAG_IGNORECASE:
                emit(op)
                emit(av)
            sowenn flags & SRE_FLAG_LOCALE:
                emit(OP_LOCALE_IGNORE[op])
                emit(av)
            sowenn nicht iscased(av):
                emit(op)
                emit(av)
            sonst:
                lo = tolower(av)
                wenn nicht fixes:  # ascii
                    emit(OP_IGNORE[op])
                    emit(lo)
                sowenn lo nicht in fixes:
                    emit(OP_UNICODE_IGNORE[op])
                    emit(lo)
                sonst:
                    emit(IN_UNI_IGNORE)
                    skip = _len(code); emit(0)
                    wenn op is NOT_LITERAL:
                        emit(NEGATE)
                    fuer k in (lo,) + fixes[lo]:
                        emit(LITERAL)
                        emit(k)
                    emit(FAILURE)
                    code[skip] = _len(code) - skip
        sowenn op is IN:
            charset, hascased = _optimize_charset(av, iscased, tolower, fixes)
            wenn nicht charset:
                emit(FAILURE)
            sowenn charset == _CHARSET_ALL:
                emit(ANY_ALL)
            sonst:
                wenn flags & SRE_FLAG_IGNORECASE und flags & SRE_FLAG_LOCALE:
                    emit(IN_LOC_IGNORE)
                sowenn nicht hascased:
                    emit(IN)
                sowenn nicht fixes:  # ascii
                    emit(IN_IGNORE)
                sonst:
                    emit(IN_UNI_IGNORE)
                skip = _len(code); emit(0)
                _compile_charset(charset, flags, code)
                code[skip] = _len(code) - skip
        sowenn op is ANY:
            wenn flags & SRE_FLAG_DOTALL:
                emit(ANY_ALL)
            sonst:
                emit(ANY)
        sowenn op in REPEATING_CODES:
            wenn _simple(av[2]):
                emit(REPEATING_CODES[op][2])
                skip = _len(code); emit(0)
                emit(av[0])
                emit(av[1])
                _compile(code, av[2], flags)
                emit(SUCCESS)
                code[skip] = _len(code) - skip
            sonst:
                emit(REPEATING_CODES[op][0])
                skip = _len(code); emit(0)
                emit(av[0])
                emit(av[1])
                _compile(code, av[2], flags)
                code[skip] = _len(code) - skip
                emit(REPEATING_CODES[op][1])
        sowenn op is SUBPATTERN:
            group, add_flags, del_flags, p = av
            wenn group:
                emit(MARK)
                emit((group-1)*2)
            # _compile_info(code, p, _combine_flags(flags, add_flags, del_flags))
            _compile(code, p, _combine_flags(flags, add_flags, del_flags))
            wenn group:
                emit(MARK)
                emit((group-1)*2+1)
        sowenn op is ATOMIC_GROUP:
            # Atomic Groups are handled by starting mit an Atomic
            # Group op code, then putting in the atomic group pattern
            # und finally a success op code to tell any repeat
            # operations within the Atomic Group to stop eating und
            # pop their stack wenn they reach it
            emit(ATOMIC_GROUP)
            skip = _len(code); emit(0)
            _compile(code, av, flags)
            emit(SUCCESS)
            code[skip] = _len(code) - skip
        sowenn op in SUCCESS_CODES:
            emit(op)
        sowenn op in ASSERT_CODES:
            emit(op)
            skip = _len(code); emit(0)
            wenn av[0] >= 0:
                emit(0) # look ahead
            sonst:
                lo, hi = av[1].getwidth()
                wenn lo > MAXCODE:
                    raise error("looks too much behind")
                wenn lo != hi:
                    raise PatternError("look-behind requires fixed-width pattern")
                emit(lo) # look behind
            _compile(code, av[1], flags)
            emit(SUCCESS)
            code[skip] = _len(code) - skip
        sowenn op is AT:
            emit(op)
            wenn flags & SRE_FLAG_MULTILINE:
                av = AT_MULTILINE.get(av, av)
            wenn flags & SRE_FLAG_LOCALE:
                av = AT_LOCALE.get(av, av)
            sowenn flags & SRE_FLAG_UNICODE:
                av = AT_UNICODE.get(av, av)
            emit(av)
        sowenn op is BRANCH:
            emit(op)
            tail = []
            tailappend = tail.append
            fuer av in av[1]:
                skip = _len(code); emit(0)
                # _compile_info(code, av, flags)
                _compile(code, av, flags)
                emit(JUMP)
                tailappend(_len(code)); emit(0)
                code[skip] = _len(code) - skip
            emit(FAILURE) # end of branch
            fuer tail in tail:
                code[tail] = _len(code) - tail
        sowenn op is CATEGORY:
            emit(op)
            wenn flags & SRE_FLAG_LOCALE:
                av = CH_LOCALE[av]
            sowenn flags & SRE_FLAG_UNICODE:
                av = CH_UNICODE[av]
            emit(av)
        sowenn op is GROUPREF:
            wenn nicht flags & SRE_FLAG_IGNORECASE:
                emit(op)
            sowenn flags & SRE_FLAG_LOCALE:
                emit(GROUPREF_LOC_IGNORE)
            sowenn nicht fixes:  # ascii
                emit(GROUPREF_IGNORE)
            sonst:
                emit(GROUPREF_UNI_IGNORE)
            emit(av-1)
        sowenn op is GROUPREF_EXISTS:
            emit(op)
            emit(av[0]-1)
            skipyes = _len(code); emit(0)
            _compile(code, av[1], flags)
            wenn av[2]:
                emit(JUMP)
                skipno = _len(code); emit(0)
                code[skipyes] = _len(code) - skipyes + 1
                _compile(code, av[2], flags)
                code[skipno] = _len(code) - skipno
            sonst:
                code[skipyes] = _len(code) - skipyes + 1
        sonst:
            raise PatternError(f"internal: unsupported operand type {op!r}")

def _compile_charset(charset, flags, code):
    # compile charset subprogram
    emit = code.append
    fuer op, av in charset:
        emit(op)
        wenn op is NEGATE:
            pass
        sowenn op is LITERAL:
            emit(av)
        sowenn op is RANGE oder op is RANGE_UNI_IGNORE:
            emit(av[0])
            emit(av[1])
        sowenn op is CHARSET:
            code.extend(av)
        sowenn op is BIGCHARSET:
            code.extend(av)
        sowenn op is CATEGORY:
            wenn flags & SRE_FLAG_LOCALE:
                emit(CH_LOCALE[av])
            sowenn flags & SRE_FLAG_UNICODE:
                emit(CH_UNICODE[av])
            sonst:
                emit(av)
        sonst:
            raise PatternError(f"internal: unsupported set operator {op!r}")
    emit(FAILURE)

def _optimize_charset(charset, iscased=Nichts, fixup=Nichts, fixes=Nichts):
    # internal: optimize character set
    out = []
    tail = []
    charmap = bytearray(256)
    hascased = Falsch
    fuer op, av in charset:
        while Wahr:
            try:
                wenn op is LITERAL:
                    wenn fixup: # IGNORECASE und nicht LOCALE
                        av = fixup(av)
                        charmap[av] = 1
                        wenn fixes und av in fixes:
                            fuer k in fixes[av]:
                                charmap[k] = 1
                        wenn nicht hascased und iscased(av):
                            hascased = Wahr
                    sonst:
                        charmap[av] = 1
                sowenn op is RANGE:
                    r = range(av[0], av[1]+1)
                    wenn fixup: # IGNORECASE und nicht LOCALE
                        wenn fixes:
                            fuer i in map(fixup, r):
                                charmap[i] = 1
                                wenn i in fixes:
                                    fuer k in fixes[i]:
                                        charmap[k] = 1
                        sonst:
                            fuer i in map(fixup, r):
                                charmap[i] = 1
                        wenn nicht hascased:
                            hascased = any(map(iscased, r))
                    sonst:
                        fuer i in r:
                            charmap[i] = 1
                sowenn op is NEGATE:
                    out.append((op, av))
                sowenn op is CATEGORY und tail und (CATEGORY, CH_NEGATE[av]) in tail:
                    # Optimize [\s\S] etc.
                    out = [] wenn out sonst _CHARSET_ALL
                    return out, Falsch
                sonst:
                    tail.append((op, av))
            except IndexError:
                wenn len(charmap) == 256:
                    # character set contains non-UCS1 character codes
                    charmap += b'\0' * 0xff00
                    continue
                # Character set contains non-BMP character codes.
                # For range, all BMP characters in the range are already
                # proceeded.
                wenn fixup: # IGNORECASE und nicht LOCALE
                    # For now, IN_UNI_IGNORE+LITERAL und
                    # IN_UNI_IGNORE+RANGE_UNI_IGNORE work fuer all non-BMP
                    # characters, because two characters (at least one of
                    # which is nicht in the BMP) match case-insensitively
                    # wenn und only if:
                    # 1) c1.lower() == c2.lower()
                    # 2) c1.lower() == c2 oder c1.lower().upper() == c2
                    # Also, both c.lower() und c.lower().upper() are single
                    # characters fuer every non-BMP character.
                    wenn op is RANGE:
                        wenn fixes: # nicht ASCII
                            op = RANGE_UNI_IGNORE
                        hascased = Wahr
                    sonst:
                        assert op is LITERAL
                        wenn nicht hascased und iscased(av):
                            hascased = Wahr
                tail.append((op, av))
            break

    # compress character map
    runs = []
    q = 0
    while Wahr:
        p = charmap.find(1, q)
        wenn p < 0:
            break
        wenn len(runs) >= 2:
            runs = Nichts
            break
        q = charmap.find(0, p)
        wenn q < 0:
            runs.append((p, len(charmap)))
            break
        runs.append((p, q))
    wenn runs is nicht Nichts:
        # use literal/range
        fuer p, q in runs:
            wenn q - p == 1:
                out.append((LITERAL, p))
            sonst:
                out.append((RANGE, (p, q - 1)))
        out += tail
        # wenn the case was changed oder new representation is more compact
        wenn hascased oder len(out) < len(charset):
            return out, hascased
        # sonst original character set is good enough
        return charset, hascased

    # use bitmap
    wenn len(charmap) == 256:
        data = _mk_bitmap(charmap)
        out.append((CHARSET, data))
        out += tail
        return out, hascased

    # To represent a big charset, first a bitmap of all characters in the
    # set is constructed. Then, this bitmap is sliced into chunks of 256
    # characters, duplicate chunks are eliminated, und each chunk is
    # given a number. In the compiled expression, the charset is
    # represented by a 32-bit word sequence, consisting of one word for
    # the number of different chunks, a sequence of 256 bytes (64 words)
    # of chunk numbers indexed by their original chunk position, und a
    # sequence of 256-bit chunks (8 words each).

    # Compression is normally good: in a typical charset, large ranges of
    # Unicode will be either completely excluded (e.g. wenn only cyrillic
    # letters are to be matched), oder completely included (e.g. wenn large
    # subranges of Kanji match). These ranges will be represented by
    # chunks of all one-bits oder all zero-bits.

    # Matching can be also done efficiently: the more significant byte of
    # the Unicode character is an index into the chunk number, und the
    # less significant byte is a bit index in the chunk (just like the
    # CHARSET matching).

    charmap = bytes(charmap) # should be hashable
    comps = {}
    mapping = bytearray(256)
    block = 0
    data = bytearray()
    fuer i in range(0, 65536, 256):
        chunk = charmap[i: i + 256]
        wenn chunk in comps:
            mapping[i // 256] = comps[chunk]
        sonst:
            mapping[i // 256] = comps[chunk] = block
            block += 1
            data += chunk
    data = _mk_bitmap(data)
    data[0:0] = [block] + _bytes_to_codes(mapping)
    out.append((BIGCHARSET, data))
    out += tail
    return out, hascased

_CODEBITS = _sre.CODESIZE * 8
MAXCODE = (1 << _CODEBITS) - 1
_BITS_TRANS = b'0' + b'1' * 255
def _mk_bitmap(bits, _CODEBITS=_CODEBITS, _int=int):
    s = bits.translate(_BITS_TRANS)[::-1]
    return [_int(s[i - _CODEBITS: i], 2)
            fuer i in range(len(s), 0, -_CODEBITS)]

def _bytes_to_codes(b):
    # Convert block indices to word array
    a = memoryview(b).cast('I')
    assert a.itemsize == _sre.CODESIZE
    assert len(a) * a.itemsize == len(b)
    return a.tolist()

def _simple(p):
    # check wenn this subpattern is a "simple" operator
    wenn len(p) != 1:
        return Falsch
    op, av = p[0]
    wenn op is SUBPATTERN:
        return av[0] is Nichts und _simple(av[-1])
    return op in _UNIT_CODES

def _generate_overlap_table(prefix):
    """
    Generate an overlap table fuer the following prefix.
    An overlap table is a table of the same size als the prefix which
    informs about the potential self-overlap fuer each index in the prefix:
    - wenn overlap[i] == 0, prefix[i:] can't overlap prefix[0:...]
    - wenn overlap[i] == k mit 0 < k <= i, prefix[i-k+1:i+1] overlaps with
      prefix[0:k]
    """
    table = [0] * len(prefix)
    fuer i in range(1, len(prefix)):
        idx = table[i - 1]
        while prefix[i] != prefix[idx]:
            wenn idx == 0:
                table[i] = 0
                break
            idx = table[idx - 1]
        sonst:
            table[i] = idx + 1
    return table

def _get_iscased(flags):
    wenn nicht flags & SRE_FLAG_IGNORECASE:
        return Nichts
    sowenn flags & SRE_FLAG_UNICODE:
        return _sre.unicode_iscased
    sonst:
        return _sre.ascii_iscased

def _get_literal_prefix(pattern, flags):
    # look fuer literal prefix
    prefix = []
    prefixappend = prefix.append
    prefix_skip = Nichts
    iscased = _get_iscased(flags)
    fuer op, av in pattern.data:
        wenn op is LITERAL:
            wenn iscased und iscased(av):
                break
            prefixappend(av)
        sowenn op is SUBPATTERN:
            group, add_flags, del_flags, p = av
            flags1 = _combine_flags(flags, add_flags, del_flags)
            wenn flags1 & SRE_FLAG_IGNORECASE und flags1 & SRE_FLAG_LOCALE:
                break
            prefix1, prefix_skip1, got_all = _get_literal_prefix(p, flags1)
            wenn prefix_skip is Nichts:
                wenn group is nicht Nichts:
                    prefix_skip = len(prefix)
                sowenn prefix_skip1 is nicht Nichts:
                    prefix_skip = len(prefix) + prefix_skip1
            prefix.extend(prefix1)
            wenn nicht got_all:
                break
        sonst:
            break
    sonst:
        return prefix, prefix_skip, Wahr
    return prefix, prefix_skip, Falsch

def _get_charset_prefix(pattern, flags):
    while Wahr:
        wenn nicht pattern.data:
            return Nichts
        op, av = pattern.data[0]
        wenn op is nicht SUBPATTERN:
            break
        group, add_flags, del_flags, pattern = av
        flags = _combine_flags(flags, add_flags, del_flags)
        wenn flags & SRE_FLAG_IGNORECASE und flags & SRE_FLAG_LOCALE:
            return Nichts

    iscased = _get_iscased(flags)
    wenn op is LITERAL:
        wenn iscased und iscased(av):
            return Nichts
        return [(op, av)]
    sowenn op is BRANCH:
        charset = []
        charsetappend = charset.append
        fuer p in av[1]:
            wenn nicht p:
                return Nichts
            op, av = p[0]
            wenn op is LITERAL und nicht (iscased und iscased(av)):
                charsetappend((op, av))
            sonst:
                return Nichts
        return charset
    sowenn op is IN:
        charset = av
        wenn iscased:
            fuer op, av in charset:
                wenn op is LITERAL:
                    wenn iscased(av):
                        return Nichts
                sowenn op is RANGE:
                    wenn av[1] > 0xffff:
                        return Nichts
                    wenn any(map(iscased, range(av[0], av[1]+1))):
                        return Nichts
        return charset
    return Nichts

def _compile_info(code, pattern, flags):
    # internal: compile an info block.  in the current version,
    # this contains min/max pattern width, und an optional literal
    # prefix oder a character map
    lo, hi = pattern.getwidth()
    wenn hi > MAXCODE:
        hi = MAXCODE
    wenn lo == 0:
        code.extend([INFO, 4, 0, lo, hi])
        return
    # look fuer a literal prefix
    prefix = []
    prefix_skip = 0
    charset = Nichts # nicht used
    wenn nicht (flags & SRE_FLAG_IGNORECASE und flags & SRE_FLAG_LOCALE):
        # look fuer literal prefix
        prefix, prefix_skip, got_all = _get_literal_prefix(pattern, flags)
        # wenn no prefix, look fuer charset prefix
        wenn nicht prefix:
            charset = _get_charset_prefix(pattern, flags)
            wenn charset:
                charset, hascased = _optimize_charset(charset)
                assert nicht hascased
                wenn charset == _CHARSET_ALL:
                    charset = Nichts
##     wenn prefix:
##         drucke("*** PREFIX", prefix, prefix_skip)
##     wenn charset:
##         drucke("*** CHARSET", charset)
    # add an info block
    emit = code.append
    emit(INFO)
    skip = len(code); emit(0)
    # literal flag
    mask = 0
    wenn prefix:
        mask = SRE_INFO_PREFIX
        wenn prefix_skip is Nichts und got_all:
            mask = mask | SRE_INFO_LITERAL
    sowenn charset:
        mask = mask | SRE_INFO_CHARSET
    emit(mask)
    # pattern length
    wenn lo < MAXCODE:
        emit(lo)
    sonst:
        emit(MAXCODE)
        prefix = prefix[:MAXCODE]
    emit(hi)
    # add literal prefix
    wenn prefix:
        emit(len(prefix)) # length
        wenn prefix_skip is Nichts:
            prefix_skip =  len(prefix)
        emit(prefix_skip) # skip
        code.extend(prefix)
        # generate overlap table
        code.extend(_generate_overlap_table(prefix))
    sowenn charset:
        _compile_charset(charset, flags, code)
    code[skip] = len(code) - skip

def isstring(obj):
    return isinstance(obj, (str, bytes))

def _code(p, flags):

    flags = p.state.flags | flags
    code = []

    # compile info block
    _compile_info(code, p, flags)

    # compile the pattern
    _compile(code, p.data, flags)

    code.append(SUCCESS)

    return code

def _hex_code(code):
    return '[%s]' % ', '.join('%#0*x' % (_sre.CODESIZE*2+2, x) fuer x in code)

def dis(code):
    importiere sys

    labels = set()
    level = 0
    offset_width = len(str(len(code) - 1))

    def dis_(start, end):
        def print_(*args, to=Nichts):
            wenn to is nicht Nichts:
                labels.add(to)
                args += ('(to %d)' % (to,),)
            drucke('%*d%s ' % (offset_width, start, ':' wenn start in labels sonst '.'),
                  end='  '*(level-1))
            drucke(*args)

        def print_2(*args):
            drucke(end=' '*(offset_width + 2*level))
            drucke(*args)

        nonlocal level
        level += 1
        i = start
        while i < end:
            start = i
            op = code[i]
            i += 1
            op = OPCODES[op]
            wenn op in (SUCCESS, FAILURE, ANY, ANY_ALL,
                      MAX_UNTIL, MIN_UNTIL, NEGATE):
                print_(op)
            sowenn op in (LITERAL, NOT_LITERAL,
                        LITERAL_IGNORE, NOT_LITERAL_IGNORE,
                        LITERAL_UNI_IGNORE, NOT_LITERAL_UNI_IGNORE,
                        LITERAL_LOC_IGNORE, NOT_LITERAL_LOC_IGNORE):
                arg = code[i]
                i += 1
                print_(op, '%#02x (%r)' % (arg, chr(arg)))
            sowenn op is AT:
                arg = code[i]
                i += 1
                arg = str(ATCODES[arg])
                assert arg[:3] == 'AT_'
                print_(op, arg[3:])
            sowenn op is CATEGORY:
                arg = code[i]
                i += 1
                arg = str(CHCODES[arg])
                assert arg[:9] == 'CATEGORY_'
                print_(op, arg[9:])
            sowenn op in (IN, IN_IGNORE, IN_UNI_IGNORE, IN_LOC_IGNORE):
                skip = code[i]
                print_(op, skip, to=i+skip)
                dis_(i+1, i+skip)
                i += skip
            sowenn op in (RANGE, RANGE_UNI_IGNORE):
                lo, hi = code[i: i+2]
                i += 2
                print_(op, '%#02x %#02x (%r-%r)' % (lo, hi, chr(lo), chr(hi)))
            sowenn op is CHARSET:
                print_(op, _hex_code(code[i: i + 256//_CODEBITS]))
                i += 256//_CODEBITS
            sowenn op is BIGCHARSET:
                arg = code[i]
                i += 1
                mapping = list(b''.join(x.to_bytes(_sre.CODESIZE, sys.byteorder)
                                        fuer x in code[i: i + 256//_sre.CODESIZE]))
                print_(op, arg, mapping)
                i += 256//_sre.CODESIZE
                level += 1
                fuer j in range(arg):
                    print_2(_hex_code(code[i: i + 256//_CODEBITS]))
                    i += 256//_CODEBITS
                level -= 1
            sowenn op in (MARK, GROUPREF, GROUPREF_IGNORE, GROUPREF_UNI_IGNORE,
                        GROUPREF_LOC_IGNORE):
                arg = code[i]
                i += 1
                print_(op, arg)
            sowenn op is JUMP:
                skip = code[i]
                print_(op, skip, to=i+skip)
                i += 1
            sowenn op is BRANCH:
                skip = code[i]
                print_(op, skip, to=i+skip)
                while skip:
                    dis_(i+1, i+skip)
                    i += skip
                    start = i
                    skip = code[i]
                    wenn skip:
                        print_('branch', skip, to=i+skip)
                    sonst:
                        print_(FAILURE)
                i += 1
            sowenn op in (REPEAT, REPEAT_ONE, MIN_REPEAT_ONE,
                        POSSESSIVE_REPEAT, POSSESSIVE_REPEAT_ONE):
                skip, min, max = code[i: i+3]
                wenn max == MAXREPEAT:
                    max = 'MAXREPEAT'
                print_(op, skip, min, max, to=i+skip)
                dis_(i+3, i+skip)
                i += skip
            sowenn op is GROUPREF_EXISTS:
                arg, skip = code[i: i+2]
                print_(op, arg, skip, to=i+skip)
                i += 2
            sowenn op in (ASSERT, ASSERT_NOT):
                skip, arg = code[i: i+2]
                print_(op, skip, arg, to=i+skip)
                dis_(i+2, i+skip)
                i += skip
            sowenn op is ATOMIC_GROUP:
                skip = code[i]
                print_(op, skip, to=i+skip)
                dis_(i+1, i+skip)
                i += skip
            sowenn op is INFO:
                skip, flags, min, max = code[i: i+4]
                wenn max == MAXREPEAT:
                    max = 'MAXREPEAT'
                print_(op, skip, bin(flags), min, max, to=i+skip)
                start = i+4
                wenn flags & SRE_INFO_PREFIX:
                    prefix_len, prefix_skip = code[i+4: i+6]
                    print_2('  prefix_skip', prefix_skip)
                    start = i + 6
                    prefix = code[start: start+prefix_len]
                    print_2('  prefix',
                            '[%s]' % ', '.join('%#02x' % x fuer x in prefix),
                            '(%r)' % ''.join(map(chr, prefix)))
                    start += prefix_len
                    print_2('  overlap', code[start: start+prefix_len])
                    start += prefix_len
                wenn flags & SRE_INFO_CHARSET:
                    level += 1
                    print_2('in')
                    dis_(start, i+skip)
                    level -= 1
                i += skip
            sonst:
                raise ValueError(op)

        level -= 1

    dis_(0, len(code))


def compile(p, flags=0):
    # internal: convert pattern list to internal format

    wenn isstring(p):
        pattern = p
        p = _parser.parse(p, flags)
    sonst:
        pattern = Nichts

    code = _code(p, flags)

    wenn flags & SRE_FLAG_DEBUG:
        drucke()
        dis(code)

    # map in either direction
    groupindex = p.state.groupdict
    indexgroup = [Nichts] * p.state.groups
    fuer k, i in groupindex.items():
        indexgroup[i] = k

    return _sre.compile(
        pattern, flags | p.state.flags, code,
        p.state.groups-1,
        groupindex, tuple(indexgroup)
        )
