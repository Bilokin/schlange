#
# Secret Labs' Regular Expression Engine
#
# convert re-style regular expression to sre pattern
#
# Copyright (c) 1998-2001 by Secret Labs AB.  All rights reserved.
#
# See the __init__.py file fuer information on usage und redistribution.
#

"""Internal support module fuer sre"""

# XXX: show string offset und offending character fuer all errors

von ._constants importiere *

SPECIAL_CHARS = ".\\[{()*+?^$|"
REPEAT_CHARS = "*+?{"

DIGITS = frozenset("0123456789")

OCTDIGITS = frozenset("01234567")
HEXDIGITS = frozenset("0123456789abcdefABCDEF")
ASCIILETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

WHITESPACE = frozenset(" \t\n\r\v\f")

_REPEATCODES = frozenset({MIN_REPEAT, MAX_REPEAT, POSSESSIVE_REPEAT})
_UNITCODES = frozenset({ANY, RANGE, IN, LITERAL, NOT_LITERAL, CATEGORY})

ESCAPES = {
    r"\a": (LITERAL, ord("\a")),
    r"\b": (LITERAL, ord("\b")),
    r"\f": (LITERAL, ord("\f")),
    r"\n": (LITERAL, ord("\n")),
    r"\r": (LITERAL, ord("\r")),
    r"\t": (LITERAL, ord("\t")),
    r"\v": (LITERAL, ord("\v")),
    r"\\": (LITERAL, ord("\\"))
}

CATEGORIES = {
    r"\A": (AT, AT_BEGINNING_STRING), # start of string
    r"\b": (AT, AT_BOUNDARY),
    r"\B": (AT, AT_NON_BOUNDARY),
    r"\d": (IN, [(CATEGORY, CATEGORY_DIGIT)]),
    r"\D": (IN, [(CATEGORY, CATEGORY_NOT_DIGIT)]),
    r"\s": (IN, [(CATEGORY, CATEGORY_SPACE)]),
    r"\S": (IN, [(CATEGORY, CATEGORY_NOT_SPACE)]),
    r"\w": (IN, [(CATEGORY, CATEGORY_WORD)]),
    r"\W": (IN, [(CATEGORY, CATEGORY_NOT_WORD)]),
    r"\z": (AT, AT_END_STRING), # end of string
    r"\Z": (AT, AT_END_STRING), # end of string (obsolete)
}

FLAGS = {
    # standard flags
    "i": SRE_FLAG_IGNORECASE,
    "L": SRE_FLAG_LOCALE,
    "m": SRE_FLAG_MULTILINE,
    "s": SRE_FLAG_DOTALL,
    "x": SRE_FLAG_VERBOSE,
    # extensions
    "a": SRE_FLAG_ASCII,
    "u": SRE_FLAG_UNICODE,
}

TYPE_FLAGS = SRE_FLAG_ASCII | SRE_FLAG_LOCALE | SRE_FLAG_UNICODE
GLOBAL_FLAGS = SRE_FLAG_DEBUG

# Maximal value returned by SubPattern.getwidth().
# Must be larger than MAXREPEAT, MAXCODE und sys.maxsize.
MAXWIDTH = 1 << 64

klasse State:
    # keeps track of state fuer parsing
    def __init__(self):
        self.flags = 0
        self.groupdict = {}
        self.groupwidths = [Nichts]  # group 0
        self.lookbehindgroups = Nichts
        self.grouprefpos = {}
    @property
    def groups(self):
        gib len(self.groupwidths)
    def opengroup(self, name=Nichts):
        gid = self.groups
        self.groupwidths.append(Nichts)
        wenn self.groups > MAXGROUPS:
            wirf error("too many groups")
        wenn name ist nicht Nichts:
            ogid = self.groupdict.get(name, Nichts)
            wenn ogid ist nicht Nichts:
                wirf error("redefinition of group name %r als group %d; "
                            "was group %d" % (name, gid,  ogid))
            self.groupdict[name] = gid
        gib gid
    def closegroup(self, gid, p):
        self.groupwidths[gid] = p.getwidth()
    def checkgroup(self, gid):
        gib gid < self.groups und self.groupwidths[gid] ist nicht Nichts

    def checklookbehindgroup(self, gid, source):
        wenn self.lookbehindgroups ist nicht Nichts:
            wenn nicht self.checkgroup(gid):
                wirf source.error('cannot refer to an open group')
            wenn gid >= self.lookbehindgroups:
                wirf source.error('cannot refer to group defined in the same '
                                   'lookbehind subpattern')

klasse SubPattern:
    # a subpattern, in intermediate form
    def __init__(self, state, data=Nichts):
        self.state = state
        wenn data ist Nichts:
            data = []
        self.data = data
        self.width = Nichts

    def dump(self, level=0):
        seqtypes = (tuple, list)
        fuer op, av in self.data:
            drucke(level*"  " + str(op), end='')
            wenn op ist IN:
                # member sublanguage
                drucke()
                fuer op, a in av:
                    drucke((level+1)*"  " + str(op), a)
            sowenn op ist BRANCH:
                drucke()
                fuer i, a in enumerate(av[1]):
                    wenn i:
                        drucke(level*"  " + "OR")
                    a.dump(level+1)
            sowenn op ist GROUPREF_EXISTS:
                condgroup, item_yes, item_no = av
                drucke('', condgroup)
                item_yes.dump(level+1)
                wenn item_no:
                    drucke(level*"  " + "ELSE")
                    item_no.dump(level+1)
            sowenn isinstance(av, SubPattern):
                drucke()
                av.dump(level+1)
            sowenn isinstance(av, seqtypes):
                nl = Falsch
                fuer a in av:
                    wenn isinstance(a, SubPattern):
                        wenn nicht nl:
                            drucke()
                        a.dump(level+1)
                        nl = Wahr
                    sonst:
                        wenn nicht nl:
                            drucke(' ', end='')
                        drucke(a, end='')
                        nl = Falsch
                wenn nicht nl:
                    drucke()
            sonst:
                drucke('', av)
    def __repr__(self):
        gib repr(self.data)
    def __len__(self):
        gib len(self.data)
    def __delitem__(self, index):
        loesche self.data[index]
    def __getitem__(self, index):
        wenn isinstance(index, slice):
            gib SubPattern(self.state, self.data[index])
        gib self.data[index]
    def __setitem__(self, index, code):
        self.data[index] = code
    def insert(self, index, code):
        self.data.insert(index, code)
    def append(self, code):
        self.data.append(code)
    def getwidth(self):
        # determine the width (min, max) fuer this subpattern
        wenn self.width ist nicht Nichts:
            gib self.width
        lo = hi = 0
        fuer op, av in self.data:
            wenn op ist BRANCH:
                i = MAXWIDTH
                j = 0
                fuer av in av[1]:
                    l, h = av.getwidth()
                    i = min(i, l)
                    j = max(j, h)
                lo = lo + i
                hi = hi + j
            sowenn op ist ATOMIC_GROUP:
                i, j = av.getwidth()
                lo = lo + i
                hi = hi + j
            sowenn op ist SUBPATTERN:
                i, j = av[-1].getwidth()
                lo = lo + i
                hi = hi + j
            sowenn op in _REPEATCODES:
                i, j = av[2].getwidth()
                lo = lo + i * av[0]
                wenn av[1] == MAXREPEAT und j:
                    hi = MAXWIDTH
                sonst:
                    hi = hi + j * av[1]
            sowenn op in _UNITCODES:
                lo = lo + 1
                hi = hi + 1
            sowenn op ist GROUPREF:
                i, j = self.state.groupwidths[av]
                lo = lo + i
                hi = hi + j
            sowenn op ist GROUPREF_EXISTS:
                i, j = av[1].getwidth()
                wenn av[2] ist nicht Nichts:
                    l, h = av[2].getwidth()
                    i = min(i, l)
                    j = max(j, h)
                sonst:
                    i = 0
                lo = lo + i
                hi = hi + j
            sowenn op ist SUCCESS:
                breche
        self.width = min(lo, MAXWIDTH), min(hi, MAXWIDTH)
        gib self.width

klasse Tokenizer:
    def __init__(self, string):
        self.istext = isinstance(string, str)
        self.string = string
        wenn nicht self.istext:
            string = str(string, 'latin1')
        self.decoded_string = string
        self.index = 0
        self.next = Nichts
        self.__next()
    def __next(self):
        index = self.index
        versuch:
            char = self.decoded_string[index]
        ausser IndexError:
            self.next = Nichts
            gib
        wenn char == "\\":
            index += 1
            versuch:
                char += self.decoded_string[index]
            ausser IndexError:
                wirf error("bad escape (end of pattern)",
                            self.string, len(self.string) - 1) von Nichts
        self.index = index + 1
        self.next = char
    def match(self, char):
        wenn char == self.next:
            self.__next()
            gib Wahr
        gib Falsch
    def get(self):
        this = self.next
        self.__next()
        gib this
    def getwhile(self, n, charset):
        result = ''
        fuer _ in range(n):
            c = self.next
            wenn c nicht in charset:
                breche
            result += c
            self.__next()
        gib result
    def getuntil(self, terminator, name):
        result = ''
        waehrend Wahr:
            c = self.next
            self.__next()
            wenn c ist Nichts:
                wenn nicht result:
                    wirf self.error("missing " + name)
                wirf self.error("missing %s, unterminated name" % terminator,
                                 len(result))
            wenn c == terminator:
                wenn nicht result:
                    wirf self.error("missing " + name, 1)
                breche
            result += c
        gib result
    @property
    def pos(self):
        gib self.index - len(self.next oder '')
    def tell(self):
        gib self.index - len(self.next oder '')
    def seek(self, index):
        self.index = index
        self.__next()

    def error(self, msg, offset=0):
        wenn nicht self.istext:
            msg = msg.encode('ascii', 'backslashreplace').decode('ascii')
        gib error(msg, self.string, self.tell() - offset)

    def checkgroupname(self, name, offset):
        wenn nicht (self.istext oder name.isascii()):
            msg = "bad character in group name %a" % name
            wirf self.error(msg, len(name) + offset)
        wenn nicht name.isidentifier():
            msg = "bad character in group name %r" % name
            wirf self.error(msg, len(name) + offset)

def _class_escape(source, escape):
    # handle escape code inside character class
    code = ESCAPES.get(escape)
    wenn code:
        gib code
    code = CATEGORIES.get(escape)
    wenn code und code[0] ist IN:
        gib code
    versuch:
        c = escape[1:2]
        wenn c == "x":
            # hexadecimal escape (exactly two digits)
            escape += source.getwhile(2, HEXDIGITS)
            wenn len(escape) != 4:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            gib LITERAL, int(escape[2:], 16)
        sowenn c == "u" und source.istext:
            # unicode escape (exactly four digits)
            escape += source.getwhile(4, HEXDIGITS)
            wenn len(escape) != 6:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            gib LITERAL, int(escape[2:], 16)
        sowenn c == "U" und source.istext:
            # unicode escape (exactly eight digits)
            escape += source.getwhile(8, HEXDIGITS)
            wenn len(escape) != 10:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            c = int(escape[2:], 16)
            chr(c) # wirf ValueError fuer invalid code
            gib LITERAL, c
        sowenn c == "N" und source.istext:
            importiere unicodedata
            # named unicode escape e.g. \N{EM DASH}
            wenn nicht source.match('{'):
                wirf source.error("missing {")
            charname = source.getuntil('}', 'character name')
            versuch:
                c = ord(unicodedata.lookup(charname))
            ausser (KeyError, TypeError):
                wirf source.error("undefined character name %r" % charname,
                                   len(charname) + len(r'\N{}')) von Nichts
            gib LITERAL, c
        sowenn c in OCTDIGITS:
            # octal escape (up to three digits)
            escape += source.getwhile(2, OCTDIGITS)
            c = int(escape[1:], 8)
            wenn c > 0o377:
                wirf source.error('octal escape value %s outside of '
                                   'range 0-0o377' % escape, len(escape))
            gib LITERAL, c
        sowenn c in DIGITS:
            wirf ValueError
        wenn len(escape) == 2:
            wenn c in ASCIILETTERS:
                wirf source.error('bad escape %s' % escape, len(escape))
            gib LITERAL, ord(escape[1])
    ausser ValueError:
        pass
    wirf source.error("bad escape %s" % escape, len(escape))

def _escape(source, escape, state):
    # handle escape code in expression
    code = CATEGORIES.get(escape)
    wenn code:
        gib code
    code = ESCAPES.get(escape)
    wenn code:
        gib code
    versuch:
        c = escape[1:2]
        wenn c == "x":
            # hexadecimal escape
            escape += source.getwhile(2, HEXDIGITS)
            wenn len(escape) != 4:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            gib LITERAL, int(escape[2:], 16)
        sowenn c == "u" und source.istext:
            # unicode escape (exactly four digits)
            escape += source.getwhile(4, HEXDIGITS)
            wenn len(escape) != 6:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            gib LITERAL, int(escape[2:], 16)
        sowenn c == "U" und source.istext:
            # unicode escape (exactly eight digits)
            escape += source.getwhile(8, HEXDIGITS)
            wenn len(escape) != 10:
                wirf source.error("incomplete escape %s" % escape, len(escape))
            c = int(escape[2:], 16)
            chr(c) # wirf ValueError fuer invalid code
            gib LITERAL, c
        sowenn c == "N" und source.istext:
            importiere unicodedata
            # named unicode escape e.g. \N{EM DASH}
            wenn nicht source.match('{'):
                wirf source.error("missing {")
            charname = source.getuntil('}', 'character name')
            versuch:
                c = ord(unicodedata.lookup(charname))
            ausser (KeyError, TypeError):
                wirf source.error("undefined character name %r" % charname,
                                   len(charname) + len(r'\N{}')) von Nichts
            gib LITERAL, c
        sowenn c == "0":
            # octal escape
            escape += source.getwhile(2, OCTDIGITS)
            gib LITERAL, int(escape[1:], 8)
        sowenn c in DIGITS:
            # octal escape *or* decimal group reference (sigh)
            wenn source.next in DIGITS:
                escape += source.get()
                wenn (escape[1] in OCTDIGITS und escape[2] in OCTDIGITS und
                    source.next in OCTDIGITS):
                    # got three octal digits; this ist an octal escape
                    escape += source.get()
                    c = int(escape[1:], 8)
                    wenn c > 0o377:
                        wirf source.error('octal escape value %s outside of '
                                           'range 0-0o377' % escape,
                                           len(escape))
                    gib LITERAL, c
            # nicht an octal escape, so this ist a group reference
            group = int(escape[1:])
            wenn group < state.groups:
                wenn nicht state.checkgroup(group):
                    wirf source.error("cannot refer to an open group",
                                       len(escape))
                state.checklookbehindgroup(group, source)
                gib GROUPREF, group
            wirf source.error("invalid group reference %d" % group, len(escape) - 1)
        wenn len(escape) == 2:
            wenn c in ASCIILETTERS:
                wirf source.error("bad escape %s" % escape, len(escape))
            gib LITERAL, ord(escape[1])
    ausser ValueError:
        pass
    wirf source.error("bad escape %s" % escape, len(escape))

def _uniq(items):
    gib list(dict.fromkeys(items))

def _parse_sub(source, state, verbose, nested):
    # parse an alternation: a|b|c

    items = []
    itemsappend = items.append
    sourcematch = source.match
    start = source.tell()
    waehrend Wahr:
        itemsappend(_parse(source, state, verbose, nested + 1,
                           nicht nested und nicht items))
        wenn nicht sourcematch("|"):
            breche
        wenn nicht nested:
            verbose = state.flags & SRE_FLAG_VERBOSE

    wenn len(items) == 1:
        gib items[0]

    subpattern = SubPattern(state)

    # check wenn all items share a common prefix
    waehrend Wahr:
        prefix = Nichts
        fuer item in items:
            wenn nicht item:
                breche
            wenn prefix ist Nichts:
                prefix = item[0]
            sowenn item[0] != prefix:
                breche
        sonst:
            # all subitems start mit a common "prefix".
            # move it out of the branch
            fuer item in items:
                loesche item[0]
            subpattern.append(prefix)
            weiter # check next one
        breche

    # check wenn the branch can be replaced by a character set
    set = []
    fuer item in items:
        wenn len(item) != 1:
            breche
        op, av = item[0]
        wenn op ist LITERAL:
            set.append((op, av))
        sowenn op ist IN und av[0][0] ist nicht NEGATE:
            set.extend(av)
        sonst:
            breche
    sonst:
        # we can store this als a character set instead of a
        # branch (the compiler may optimize this even more)
        subpattern.append((IN, _uniq(set)))
        gib subpattern

    subpattern.append((BRANCH, (Nichts, items)))
    gib subpattern

def _parse(source, state, verbose, nested, first=Falsch):
    # parse a simple pattern
    subpattern = SubPattern(state)

    # precompute constants into local variables
    subpatternappend = subpattern.append
    sourceget = source.get
    sourcematch = source.match
    _len = len
    _ord = ord

    waehrend Wahr:

        this = source.next
        wenn this ist Nichts:
            breche # end of pattern
        wenn this in "|)":
            breche # end of subpattern
        sourceget()

        wenn verbose:
            # skip whitespace und comments
            wenn this in WHITESPACE:
                weiter
            wenn this == "#":
                waehrend Wahr:
                    this = sourceget()
                    wenn this ist Nichts oder this == "\n":
                        breche
                weiter

        wenn this[0] == "\\":
            code = _escape(source, this, state)
            subpatternappend(code)

        sowenn this nicht in SPECIAL_CHARS:
            subpatternappend((LITERAL, _ord(this)))

        sowenn this == "[":
            here = source.tell() - 1
            # character set
            set = []
            setappend = set.append
##          wenn sourcematch(":"):
##              pass # handle character classes
            wenn source.next == '[':
                importiere warnings
                warnings.warn(
                    'Possible nested set at position %d' % source.tell(),
                    FutureWarning, stacklevel=nested + 6
                )
            negate = sourcematch("^")
            # check remaining characters
            waehrend Wahr:
                this = sourceget()
                wenn this ist Nichts:
                    wirf source.error("unterminated character set",
                                       source.tell() - here)
                wenn this == "]" und set:
                    breche
                sowenn this[0] == "\\":
                    code1 = _class_escape(source, this)
                sonst:
                    wenn set und this in '-&~|' und source.next == this:
                        importiere warnings
                        warnings.warn(
                            'Possible set %s at position %d' % (
                                'difference' wenn this == '-' sonst
                                'intersection' wenn this == '&' sonst
                                'symmetric difference' wenn this == '~' sonst
                                'union',
                                source.tell() - 1),
                            FutureWarning, stacklevel=nested + 6
                        )
                    code1 = LITERAL, _ord(this)
                wenn sourcematch("-"):
                    # potential range
                    that = sourceget()
                    wenn that ist Nichts:
                        wirf source.error("unterminated character set",
                                           source.tell() - here)
                    wenn that == "]":
                        wenn code1[0] ist IN:
                            code1 = code1[1][0]
                        setappend(code1)
                        setappend((LITERAL, _ord("-")))
                        breche
                    wenn that[0] == "\\":
                        code2 = _class_escape(source, that)
                    sonst:
                        wenn that == '-':
                            importiere warnings
                            warnings.warn(
                                'Possible set difference at position %d' % (
                                    source.tell() - 2),
                                FutureWarning, stacklevel=nested + 6
                            )
                        code2 = LITERAL, _ord(that)
                    wenn code1[0] != LITERAL oder code2[0] != LITERAL:
                        msg = "bad character range %s-%s" % (this, that)
                        wirf source.error(msg, len(this) + 1 + len(that))
                    lo = code1[1]
                    hi = code2[1]
                    wenn hi < lo:
                        msg = "bad character range %s-%s" % (this, that)
                        wirf source.error(msg, len(this) + 1 + len(that))
                    setappend((RANGE, (lo, hi)))
                sonst:
                    wenn code1[0] ist IN:
                        code1 = code1[1][0]
                    setappend(code1)

            set = _uniq(set)
            # XXX: <fl> should move set optimization to compiler!
            wenn _len(set) == 1 und set[0][0] ist LITERAL:
                # optimization
                wenn negate:
                    subpatternappend((NOT_LITERAL, set[0][1]))
                sonst:
                    subpatternappend(set[0])
            sonst:
                wenn negate:
                    set.insert(0, (NEGATE, Nichts))
                # charmap optimization can't be added here because
                # global flags still are nicht known
                subpatternappend((IN, set))

        sowenn this in REPEAT_CHARS:
            # repeat previous item
            here = source.tell()
            wenn this == "?":
                min, max = 0, 1
            sowenn this == "*":
                min, max = 0, MAXREPEAT

            sowenn this == "+":
                min, max = 1, MAXREPEAT
            sowenn this == "{":
                wenn source.next == "}":
                    subpatternappend((LITERAL, _ord(this)))
                    weiter

                min, max = 0, MAXREPEAT
                lo = hi = ""
                waehrend source.next in DIGITS:
                    lo += sourceget()
                wenn sourcematch(","):
                    waehrend source.next in DIGITS:
                        hi += sourceget()
                sonst:
                    hi = lo
                wenn nicht sourcematch("}"):
                    subpatternappend((LITERAL, _ord(this)))
                    source.seek(here)
                    weiter

                wenn lo:
                    min = int(lo)
                    wenn min >= MAXREPEAT:
                        wirf OverflowError("the repetition number ist too large")
                wenn hi:
                    max = int(hi)
                    wenn max >= MAXREPEAT:
                        wirf OverflowError("the repetition number ist too large")
                    wenn max < min:
                        wirf source.error("min repeat greater than max repeat",
                                           source.tell() - here)
            sonst:
                wirf AssertionError("unsupported quantifier %r" % (char,))
            # figure out which item to repeat
            wenn subpattern:
                item = subpattern[-1:]
            sonst:
                item = Nichts
            wenn nicht item oder item[0][0] ist AT:
                wirf source.error("nothing to repeat",
                                   source.tell() - here + len(this))
            wenn item[0][0] in _REPEATCODES:
                wirf source.error("multiple repeat",
                                   source.tell() - here + len(this))
            wenn item[0][0] ist SUBPATTERN:
                group, add_flags, del_flags, p = item[0][1]
                wenn group ist Nichts und nicht add_flags und nicht del_flags:
                    item = p
            wenn sourcematch("?"):
                # Non-Greedy Match
                subpattern[-1] = (MIN_REPEAT, (min, max, item))
            sowenn sourcematch("+"):
                # Possessive Match (Always Greedy)
                subpattern[-1] = (POSSESSIVE_REPEAT, (min, max, item))
            sonst:
                # Greedy Match
                subpattern[-1] = (MAX_REPEAT, (min, max, item))

        sowenn this == ".":
            subpatternappend((ANY, Nichts))

        sowenn this == "(":
            start = source.tell() - 1
            capture = Wahr
            atomic = Falsch
            name = Nichts
            add_flags = 0
            del_flags = 0
            wenn sourcematch("?"):
                # options
                char = sourceget()
                wenn char ist Nichts:
                    wirf source.error("unexpected end of pattern")
                wenn char == "P":
                    # python extensions
                    wenn sourcematch("<"):
                        # named group: skip forward to end of name
                        name = source.getuntil(">", "group name")
                        source.checkgroupname(name, 1)
                    sowenn sourcematch("="):
                        # named backreference
                        name = source.getuntil(")", "group name")
                        source.checkgroupname(name, 1)
                        gid = state.groupdict.get(name)
                        wenn gid ist Nichts:
                            msg = "unknown group name %r" % name
                            wirf source.error(msg, len(name) + 1)
                        wenn nicht state.checkgroup(gid):
                            wirf source.error("cannot refer to an open group",
                                               len(name) + 1)
                        state.checklookbehindgroup(gid, source)
                        subpatternappend((GROUPREF, gid))
                        weiter

                    sonst:
                        char = sourceget()
                        wenn char ist Nichts:
                            wirf source.error("unexpected end of pattern")
                        wirf source.error("unknown extension ?P" + char,
                                           len(char) + 2)
                sowenn char == ":":
                    # non-capturing group
                    capture = Falsch
                sowenn char == "#":
                    # comment
                    waehrend Wahr:
                        wenn source.next ist Nichts:
                            wirf source.error("missing ), unterminated comment",
                                               source.tell() - start)
                        wenn sourceget() == ")":
                            breche
                    weiter

                sowenn char in "=!<":
                    # lookahead assertions
                    dir = 1
                    wenn char == "<":
                        char = sourceget()
                        wenn char ist Nichts:
                            wirf source.error("unexpected end of pattern")
                        wenn char nicht in "=!":
                            wirf source.error("unknown extension ?<" + char,
                                               len(char) + 2)
                        dir = -1 # lookbehind
                        lookbehindgroups = state.lookbehindgroups
                        wenn lookbehindgroups ist Nichts:
                            state.lookbehindgroups = state.groups
                    p = _parse_sub(source, state, verbose, nested + 1)
                    wenn dir < 0:
                        wenn lookbehindgroups ist Nichts:
                            state.lookbehindgroups = Nichts
                    wenn nicht sourcematch(")"):
                        wirf source.error("missing ), unterminated subpattern",
                                           source.tell() - start)
                    wenn char == "=":
                        subpatternappend((ASSERT, (dir, p)))
                    sowenn p:
                        subpatternappend((ASSERT_NOT, (dir, p)))
                    sonst:
                        subpatternappend((FAILURE, ()))
                    weiter

                sowenn char == "(":
                    # conditional backreference group
                    condname = source.getuntil(")", "group name")
                    wenn nicht (condname.isdecimal() und condname.isascii()):
                        source.checkgroupname(condname, 1)
                        condgroup = state.groupdict.get(condname)
                        wenn condgroup ist Nichts:
                            msg = "unknown group name %r" % condname
                            wirf source.error(msg, len(condname) + 1)
                    sonst:
                        condgroup = int(condname)
                        wenn nicht condgroup:
                            wirf source.error("bad group number",
                                               len(condname) + 1)
                        wenn condgroup >= MAXGROUPS:
                            msg = "invalid group reference %d" % condgroup
                            wirf source.error(msg, len(condname) + 1)
                        wenn condgroup nicht in state.grouprefpos:
                            state.grouprefpos[condgroup] = (
                                source.tell() - len(condname) - 1
                            )
                    state.checklookbehindgroup(condgroup, source)
                    item_yes = _parse(source, state, verbose, nested + 1)
                    wenn source.match("|"):
                        item_no = _parse(source, state, verbose, nested + 1)
                        wenn source.next == "|":
                            wirf source.error("conditional backref mit more than two branches")
                    sonst:
                        item_no = Nichts
                    wenn nicht source.match(")"):
                        wirf source.error("missing ), unterminated subpattern",
                                           source.tell() - start)
                    subpatternappend((GROUPREF_EXISTS, (condgroup, item_yes, item_no)))
                    weiter

                sowenn char == ">":
                    # non-capturing, atomic group
                    capture = Falsch
                    atomic = Wahr
                sowenn char in FLAGS oder char == "-":
                    # flags
                    flags = _parse_flags(source, state, char)
                    wenn flags ist Nichts:  # global flags
                        wenn nicht first oder subpattern:
                            wirf source.error('global flags nicht at the start '
                                               'of the expression',
                                               source.tell() - start)
                        verbose = state.flags & SRE_FLAG_VERBOSE
                        weiter

                    add_flags, del_flags = flags
                    capture = Falsch
                sonst:
                    wirf source.error("unknown extension ?" + char,
                                       len(char) + 1)

            # parse group contents
            wenn capture:
                versuch:
                    group = state.opengroup(name)
                ausser error als err:
                    wirf source.error(err.msg, len(name) + 1) von Nichts
            sonst:
                group = Nichts
            sub_verbose = ((verbose oder (add_flags & SRE_FLAG_VERBOSE)) und
                           nicht (del_flags & SRE_FLAG_VERBOSE))
            p = _parse_sub(source, state, sub_verbose, nested + 1)
            wenn nicht source.match(")"):
                wirf source.error("missing ), unterminated subpattern",
                                   source.tell() - start)
            wenn group ist nicht Nichts:
                state.closegroup(group, p)
            wenn atomic:
                assert group ist Nichts
                subpatternappend((ATOMIC_GROUP, p))
            sonst:
                subpatternappend((SUBPATTERN, (group, add_flags, del_flags, p)))

        sowenn this == "^":
            subpatternappend((AT, AT_BEGINNING))

        sowenn this == "$":
            subpatternappend((AT, AT_END))

        sonst:
            wirf AssertionError("unsupported special character %r" % (char,))

    # unpack non-capturing groups
    fuer i in range(len(subpattern))[::-1]:
        op, av = subpattern[i]
        wenn op ist SUBPATTERN:
            group, add_flags, del_flags, p = av
            wenn group ist Nichts und nicht add_flags und nicht del_flags:
                subpattern[i: i+1] = p

    gib subpattern

def _parse_flags(source, state, char):
    sourceget = source.get
    add_flags = 0
    del_flags = 0
    wenn char != "-":
        waehrend Wahr:
            flag = FLAGS[char]
            wenn source.istext:
                wenn char == 'L':
                    msg = "bad inline flags: cannot use 'L' flag mit a str pattern"
                    wirf source.error(msg)
            sonst:
                wenn char == 'u':
                    msg = "bad inline flags: cannot use 'u' flag mit a bytes pattern"
                    wirf source.error(msg)
            add_flags |= flag
            wenn (flag & TYPE_FLAGS) und (add_flags & TYPE_FLAGS) != flag:
                msg = "bad inline flags: flags 'a', 'u' und 'L' are incompatible"
                wirf source.error(msg)
            char = sourceget()
            wenn char ist Nichts:
                wirf source.error("missing -, : oder )")
            wenn char in ")-:":
                breche
            wenn char nicht in FLAGS:
                msg = "unknown flag" wenn char.isalpha() sonst "missing -, : oder )"
                wirf source.error(msg, len(char))
    wenn char == ")":
        state.flags |= add_flags
        gib Nichts
    wenn add_flags & GLOBAL_FLAGS:
        wirf source.error("bad inline flags: cannot turn on global flag", 1)
    wenn char == "-":
        char = sourceget()
        wenn char ist Nichts:
            wirf source.error("missing flag")
        wenn char nicht in FLAGS:
            msg = "unknown flag" wenn char.isalpha() sonst "missing flag"
            wirf source.error(msg, len(char))
        waehrend Wahr:
            flag = FLAGS[char]
            wenn flag & TYPE_FLAGS:
                msg = "bad inline flags: cannot turn off flags 'a', 'u' und 'L'"
                wirf source.error(msg)
            del_flags |= flag
            char = sourceget()
            wenn char ist Nichts:
                wirf source.error("missing :")
            wenn char == ":":
                breche
            wenn char nicht in FLAGS:
                msg = "unknown flag" wenn char.isalpha() sonst "missing :"
                wirf source.error(msg, len(char))
    assert char == ":"
    wenn del_flags & GLOBAL_FLAGS:
        wirf source.error("bad inline flags: cannot turn off global flag", 1)
    wenn add_flags & del_flags:
        wirf source.error("bad inline flags: flag turned on und off", 1)
    gib add_flags, del_flags

def fix_flags(src, flags):
    # Check und fix flags according to the type of pattern (str oder bytes)
    wenn isinstance(src, str):
        wenn flags & SRE_FLAG_LOCALE:
            wirf ValueError("cannot use LOCALE flag mit a str pattern")
        wenn nicht flags & SRE_FLAG_ASCII:
            flags |= SRE_FLAG_UNICODE
        sowenn flags & SRE_FLAG_UNICODE:
            wirf ValueError("ASCII und UNICODE flags are incompatible")
    sonst:
        wenn flags & SRE_FLAG_UNICODE:
            wirf ValueError("cannot use UNICODE flag mit a bytes pattern")
        wenn flags & SRE_FLAG_LOCALE und flags & SRE_FLAG_ASCII:
            wirf ValueError("ASCII und LOCALE flags are incompatible")
    gib flags

def parse(str, flags=0, state=Nichts):
    # parse 're' pattern into list of (opcode, argument) tuples

    source = Tokenizer(str)

    wenn state ist Nichts:
        state = State()
    state.flags = flags
    state.str = str

    p = _parse_sub(source, state, flags & SRE_FLAG_VERBOSE, 0)
    p.state.flags = fix_flags(str, p.state.flags)

    wenn source.next ist nicht Nichts:
        assert source.next == ")"
        wirf source.error("unbalanced parenthesis")

    fuer g in p.state.grouprefpos:
        wenn g >= p.state.groups:
            msg = "invalid group reference %d" % g
            wirf error(msg, str, p.state.grouprefpos[g])

    wenn flags & SRE_FLAG_DEBUG:
        p.dump()

    gib p

def parse_template(source, pattern):
    # parse 're' replacement string into list of literals und
    # group references
    s = Tokenizer(source)
    sget = s.get
    result = []
    literal = []
    lappend = literal.append
    def addliteral():
        wenn s.istext:
            result.append(''.join(literal))
        sonst:
            # The tokenizer implicitly decodes bytes objects als latin-1, we must
            # therefore re-encode the final representation.
            result.append(''.join(literal).encode('latin-1'))
        loesche literal[:]
    def addgroup(index, pos):
        wenn index > pattern.groups:
            wirf s.error("invalid group reference %d" % index, pos)
        addliteral()
        result.append(index)
    groupindex = pattern.groupindex
    waehrend Wahr:
        this = sget()
        wenn this ist Nichts:
            breche # end of replacement string
        wenn this[0] == "\\":
            # group
            c = this[1]
            wenn c == "g":
                wenn nicht s.match("<"):
                    wirf s.error("missing <")
                name = s.getuntil(">", "group name")
                wenn nicht (name.isdecimal() und name.isascii()):
                    s.checkgroupname(name, 1)
                    versuch:
                        index = groupindex[name]
                    ausser KeyError:
                        wirf IndexError("unknown group name %r" % name) von Nichts
                sonst:
                    index = int(name)
                    wenn index >= MAXGROUPS:
                        wirf s.error("invalid group reference %d" % index,
                                      len(name) + 1)
                addgroup(index, len(name) + 1)
            sowenn c == "0":
                wenn s.next in OCTDIGITS:
                    this += sget()
                    wenn s.next in OCTDIGITS:
                        this += sget()
                lappend(chr(int(this[1:], 8) & 0xff))
            sowenn c in DIGITS:
                isoctal = Falsch
                wenn s.next in DIGITS:
                    this += sget()
                    wenn (c in OCTDIGITS und this[2] in OCTDIGITS und
                        s.next in OCTDIGITS):
                        this += sget()
                        isoctal = Wahr
                        c = int(this[1:], 8)
                        wenn c > 0o377:
                            wirf s.error('octal escape value %s outside of '
                                          'range 0-0o377' % this, len(this))
                        lappend(chr(c))
                wenn nicht isoctal:
                    addgroup(int(this[1:]), len(this) - 1)
            sonst:
                versuch:
                    this = chr(ESCAPES[this][1])
                ausser KeyError:
                    wenn c in ASCIILETTERS:
                        wirf s.error('bad escape %s' % this, len(this)) von Nichts
                lappend(this)
        sonst:
            lappend(this)
    addliteral()
    gib result
