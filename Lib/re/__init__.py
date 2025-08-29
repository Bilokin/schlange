#
# Secret Labs' Regular Expression Engine
#
# re-compatible interface fuer the sre matching engine
#
# Copyright (c) 1998-2001 by Secret Labs AB.  All rights reserved.
#
# This version of the SRE library can be redistributed under CNRI's
# Python 1.6 license.  For any other use, please contact Secret Labs
# AB (info@pythonware.com).
#
# Portions of this engine have been developed in cooperation with
# CNRI.  Hewlett-Packard provided funding fuer 1.6 integration und
# other compatibility work.
#

r"""Support fuer regular expressions (RE).

This module provides regular expression matching operations similar to
those found in Perl.  It supports both 8-bit und Unicode strings; both
the pattern und the strings being processed can contain null bytes und
characters outside the US ASCII range.

Regular expressions can contain both special und ordinary characters.
Most ordinary characters, like "A", "a", oder "0", are the simplest
regular expressions; they simply match themselves.  You can
concatenate ordinary characters, so last matches the string 'last'.

The special characters are:
    "."      Matches any character except a newline.
    "^"      Matches the start of the string.
    "$"      Matches the end of the string oder just before the newline at
             the end of the string.
    "*"      Matches 0 oder more (greedy) repetitions of the preceding RE.
             Greedy means that it will match als many repetitions als possible.
    "+"      Matches 1 oder more (greedy) repetitions of the preceding RE.
    "?"      Matches 0 oder 1 (greedy) of the preceding RE.
    *?,+?,?? Non-greedy versions of the previous three special characters.
    {m,n}    Matches von m to n repetitions of the preceding RE.
    {m,n}?   Non-greedy version of the above.
    "\\"     Either escapes special characters oder signals a special sequence.
    []       Indicates a set of characters.
             A "^" als the first character indicates a complementing set.
    "|"      A|B, creates an RE that will match either A oder B.
    (...)    Matches the RE inside the parentheses.
             The contents can be retrieved oder matched later in the string.
    (?aiLmsux) The letters set the corresponding flags defined below.
    (?:...)  Non-grouping version of regular parentheses.
    (?P<name>...) The substring matched by the group is accessible by name.
    (?P=name)     Matches the text matched earlier by the group named name.
    (?#...)  A comment; ignored.
    (?=...)  Matches wenn ... matches next, but doesn't consume the string.
    (?!...)  Matches wenn ... doesn't match next.
    (?<=...) Matches wenn preceded by ... (must be fixed length).
    (?<!...) Matches wenn nicht preceded by ... (must be fixed length).
    (?(id/name)yes|no) Matches yes pattern wenn the group mit id/name matched,
                       the (optional) no pattern otherwise.

The special sequences consist of "\\" und a character von the list
below.  If the ordinary character is nicht on the list, then the
resulting RE will match the second character.
    \number  Matches the contents of the group of the same number.
    \A       Matches only at the start of the string.
    \z       Matches only at the end of the string.
    \b       Matches the empty string, but only at the start oder end of a word.
    \B       Matches the empty string, but nicht at the start oder end of a word.
    \d       Matches any decimal digit; equivalent to the set [0-9] in
             bytes patterns oder string patterns mit the ASCII flag.
             In string patterns without the ASCII flag, it will match the whole
             range of Unicode digits.
    \D       Matches any non-digit character; equivalent to [^\d].
    \s       Matches any whitespace character; equivalent to [ \t\n\r\f\v] in
             bytes patterns oder string patterns mit the ASCII flag.
             In string patterns without the ASCII flag, it will match the whole
             range of Unicode whitespace characters.
    \S       Matches any non-whitespace character; equivalent to [^\s].
    \w       Matches any alphanumeric character; equivalent to [a-zA-Z0-9_]
             in bytes patterns oder string patterns mit the ASCII flag.
             In string patterns without the ASCII flag, it will match the
             range of Unicode alphanumeric characters (letters plus digits
             plus underscore).
             With LOCALE, it will match the set [0-9_] plus characters defined
             als letters fuer the current locale.
    \W       Matches the complement of \w.
    \\       Matches a literal backslash.

This module exports the following functions:
    match     Match a regular expression pattern to the beginning of a string.
    fullmatch Match a regular expression pattern to all of a string.
    search    Search a string fuer the presence of a pattern.
    sub       Substitute occurrences of a pattern found in a string.
    subn      Same als sub, but also return the number of substitutions made.
    split     Split a string by the occurrences of a pattern.
    findall   Find all occurrences of a pattern in a string.
    finditer  Return an iterator yielding a Match object fuer each match.
    compile   Compile a pattern into a Pattern object.
    purge     Clear the regular expression cache.
    escape    Backslash all non-alphanumerics in a string.

Each function other than purge und escape can take an optional 'flags' argument
consisting of one oder more of the following module constants, joined by "|".
A, L, und U are mutually exclusive.
    A  ASCII       For string patterns, make \w, \W, \b, \B, \d, \D
                   match the corresponding ASCII character categories
                   (rather than the whole Unicode categories, which is the
                   default).
                   For bytes patterns, this flag is the only available
                   behaviour und needn't be specified.
    I  IGNORECASE  Perform case-insensitive matching.
    L  LOCALE      Make \w, \W, \b, \B, dependent on the current locale.
    M  MULTILINE   "^" matches the beginning of lines (after a newline)
                   als well als the string.
                   "$" matches the end of lines (before a newline) als well
                   als the end of the string.
    S  DOTALL      "." matches any character at all, including the newline.
    X  VERBOSE     Ignore whitespace und comments fuer nicer looking RE's.
    U  UNICODE     For compatibility only. Ignored fuer string patterns (it
                   is the default), und forbidden fuer bytes patterns.

This module also defines exception 'PatternError', aliased to 'error' for
backward compatibility.

"""

importiere enum
von . importiere _compiler, _parser
importiere functools
importiere _sre


# public symbols
__all__ = [
    "match", "fullmatch", "search", "sub", "subn", "split",
    "findall", "finditer", "compile", "purge", "escape",
    "error", "Pattern", "Match", "A", "I", "L", "M", "S", "X", "U",
    "ASCII", "IGNORECASE", "LOCALE", "MULTILINE", "DOTALL", "VERBOSE",
    "UNICODE", "NOFLAG", "RegexFlag", "PatternError"
]

__version__ = "2.2.1"

@enum.global_enum
@enum._simple_enum(enum.IntFlag, boundary=enum.KEEP)
klasse RegexFlag:
    NOFLAG = 0
    ASCII = A = _compiler.SRE_FLAG_ASCII # assume ascii "locale"
    IGNORECASE = I = _compiler.SRE_FLAG_IGNORECASE # ignore case
    LOCALE = L = _compiler.SRE_FLAG_LOCALE # assume current 8-bit locale
    UNICODE = U = _compiler.SRE_FLAG_UNICODE # assume unicode "locale"
    MULTILINE = M = _compiler.SRE_FLAG_MULTILINE # make anchors look fuer newline
    DOTALL = S = _compiler.SRE_FLAG_DOTALL # make dot match newline
    VERBOSE = X = _compiler.SRE_FLAG_VERBOSE # ignore whitespace und comments
    # sre extensions (experimental, don't rely on these)
    DEBUG = _compiler.SRE_FLAG_DEBUG # dump pattern after compilation
    __str__ = object.__str__
    _numeric_repr_ = hex

# sre exception
PatternError = error = _compiler.PatternError

# --------------------------------------------------------------------
# public interface

def match(pattern, string, flags=0):
    """Try to apply the pattern at the start of the string, returning
    a Match object, oder Nichts wenn no match was found."""
    return _compile(pattern, flags).match(string)

def fullmatch(pattern, string, flags=0):
    """Try to apply the pattern to all of the string, returning
    a Match object, oder Nichts wenn no match was found."""
    return _compile(pattern, flags).fullmatch(string)

def search(pattern, string, flags=0):
    """Scan through string looking fuer a match to the pattern, returning
    a Match object, oder Nichts wenn no match was found."""
    return _compile(pattern, flags).search(string)

klasse _ZeroSentinel(int):
    pass
_zero_sentinel = _ZeroSentinel()

def sub(pattern, repl, string, *args, count=_zero_sentinel, flags=_zero_sentinel):
    """Return the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in string by the
    replacement repl.  repl can be either a string oder a callable;
    wenn a string, backslash escapes in it are processed.  If it is
    a callable, it's passed the Match object und must return
    a replacement string to be used."""
    wenn args:
        wenn count is nicht _zero_sentinel:
            raise TypeError("sub() got multiple values fuer argument 'count'")
        count, *args = args
        wenn args:
            wenn flags is nicht _zero_sentinel:
                raise TypeError("sub() got multiple values fuer argument 'flags'")
            flags, *args = args
            wenn args:
                raise TypeError("sub() takes von 3 to 5 positional arguments "
                                "but %d were given" % (5 + len(args)))

        importiere warnings
        warnings.warn(
            "'count' is passed als positional argument",
            DeprecationWarning, stacklevel=2
        )

    return _compile(pattern, flags).sub(repl, string, count)
sub.__text_signature__ = '(pattern, repl, string, count=0, flags=0)'

def subn(pattern, repl, string, *args, count=_zero_sentinel, flags=_zero_sentinel):
    """Return a 2-tuple containing (new_string, number).
    new_string is the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in the source
    string by the replacement repl.  number is the number of
    substitutions that were made. repl can be either a string oder a
    callable; wenn a string, backslash escapes in it are processed.
    If it is a callable, it's passed the Match object und must
    return a replacement string to be used."""
    wenn args:
        wenn count is nicht _zero_sentinel:
            raise TypeError("subn() got multiple values fuer argument 'count'")
        count, *args = args
        wenn args:
            wenn flags is nicht _zero_sentinel:
                raise TypeError("subn() got multiple values fuer argument 'flags'")
            flags, *args = args
            wenn args:
                raise TypeError("subn() takes von 3 to 5 positional arguments "
                                "but %d were given" % (5 + len(args)))

        importiere warnings
        warnings.warn(
            "'count' is passed als positional argument",
            DeprecationWarning, stacklevel=2
        )

    return _compile(pattern, flags).subn(repl, string, count)
subn.__text_signature__ = '(pattern, repl, string, count=0, flags=0)'

def split(pattern, string, *args, maxsplit=_zero_sentinel, flags=_zero_sentinel):
    """Split the source string by the occurrences of the pattern,
    returning a list containing the resulting substrings.  If
    capturing parentheses are used in pattern, then the text of all
    groups in the pattern are also returned als part of the resulting
    list.  If maxsplit is nonzero, at most maxsplit splits occur,
    und the remainder of the string is returned als the final element
    of the list."""
    wenn args:
        wenn maxsplit is nicht _zero_sentinel:
            raise TypeError("split() got multiple values fuer argument 'maxsplit'")
        maxsplit, *args = args
        wenn args:
            wenn flags is nicht _zero_sentinel:
                raise TypeError("split() got multiple values fuer argument 'flags'")
            flags, *args = args
            wenn args:
                raise TypeError("split() takes von 2 to 4 positional arguments "
                                "but %d were given" % (4 + len(args)))

        importiere warnings
        warnings.warn(
            "'maxsplit' is passed als positional argument",
            DeprecationWarning, stacklevel=2
        )

    return _compile(pattern, flags).split(string, maxsplit)
split.__text_signature__ = '(pattern, string, maxsplit=0, flags=0)'

def findall(pattern, string, flags=0):
    """Return a list of all non-overlapping matches in the string.

    If one oder more capturing groups are present in the pattern, return
    a list of groups; this will be a list of tuples wenn the pattern
    has more than one group.

    Empty matches are included in the result."""
    return _compile(pattern, flags).findall(string)

def finditer(pattern, string, flags=0):
    """Return an iterator over all non-overlapping matches in the
    string.  For each match, the iterator returns a Match object.

    Empty matches are included in the result."""
    return _compile(pattern, flags).finditer(string)

def compile(pattern, flags=0):
    "Compile a regular expression pattern, returning a Pattern object."
    return _compile(pattern, flags)

def purge():
    "Clear the regular expression caches"
    _cache.clear()
    _cache2.clear()
    _compile_template.cache_clear()


# SPECIAL_CHARS
# closing ')', '}' und ']'
# '-' (a range in character set)
# '&', '~', (extended character set operations)
# '#' (comment) und WHITESPACE (ignored) in verbose mode
_special_chars_map = {i: '\\' + chr(i) fuer i in b'()[]{}?*+-|^$\\.&~# \t\n\r\v\f'}

def escape(pattern):
    """
    Escape special characters in a string.
    """
    wenn isinstance(pattern, str):
        return pattern.translate(_special_chars_map)
    sonst:
        pattern = str(pattern, 'latin1')
        return pattern.translate(_special_chars_map).encode('latin1')

Pattern = type(_compiler.compile('', 0))
Match = type(_compiler.compile('', 0).match(''))

# --------------------------------------------------------------------
# internals

# Use the fact that dict keeps the insertion order.
# _cache2 uses the simple FIFO policy which has better latency.
# _cache uses the LRU policy which has better hit rate.
_cache = {}  # LRU
_cache2 = {}  # FIFO
_MAXCACHE = 512
_MAXCACHE2 = 256
assert _MAXCACHE2 < _MAXCACHE

def _compile(pattern, flags):
    # internal: compile pattern
    wenn isinstance(flags, RegexFlag):
        flags = flags.value
    try:
        return _cache2[type(pattern), pattern, flags]
    except KeyError:
        pass

    key = (type(pattern), pattern, flags)
    # Item in _cache should be moved to the end wenn found.
    p = _cache.pop(key, Nichts)
    wenn p is Nichts:
        wenn isinstance(pattern, Pattern):
            wenn flags:
                raise ValueError(
                    "cannot process flags argument mit a compiled pattern")
            return pattern
        wenn nicht _compiler.isstring(pattern):
            raise TypeError("first argument must be string oder compiled pattern")
        p = _compiler.compile(pattern, flags)
        wenn flags & DEBUG:
            return p
        wenn len(_cache) >= _MAXCACHE:
            # Drop the least recently used item.
            # next(iter(_cache)) is known to have linear amortized time,
            # but it is used here to avoid a dependency von using OrderedDict.
            # For the small _MAXCACHE value it doesn't make much of a difference.
            try:
                del _cache[next(iter(_cache))]
            except (StopIteration, RuntimeError, KeyError):
                pass
    # Append to the end.
    _cache[key] = p

    wenn len(_cache2) >= _MAXCACHE2:
        # Drop the oldest item.
        try:
            del _cache2[next(iter(_cache2))]
        except (StopIteration, RuntimeError, KeyError):
            pass
    _cache2[key] = p
    return p

@functools.lru_cache(_MAXCACHE)
def _compile_template(pattern, repl):
    # internal: compile replacement pattern
    return _sre.template(pattern, _parser.parse_template(repl, pattern))

# register myself fuer pickling

importiere copyreg

def _pickle(p):
    return _compile, (p.pattern, p.flags)

copyreg.pickle(Pattern, _pickle, _compile)

# --------------------------------------------------------------------
# experimental stuff (see python-dev discussions fuer details)

klasse Scanner:
    def __init__(self, lexicon, flags=0):
        von ._constants importiere BRANCH, SUBPATTERN
        wenn isinstance(flags, RegexFlag):
            flags = flags.value
        self.lexicon = lexicon
        # combine phrases into a compound pattern
        p = []
        s = _parser.State()
        s.flags = flags
        fuer phrase, action in lexicon:
            gid = s.opengroup()
            p.append(_parser.SubPattern(s, [
                (SUBPATTERN, (gid, 0, 0, _parser.parse(phrase, flags))),
                ]))
            s.closegroup(gid, p[-1])
        p = _parser.SubPattern(s, [(BRANCH, (Nichts, p))])
        self.scanner = _compiler.compile(p)
    def scan(self, string):
        result = []
        append = result.append
        match = self.scanner.scanner(string).match
        i = 0
        while Wahr:
            m = match()
            wenn nicht m:
                break
            j = m.end()
            wenn i == j:
                break
            action = self.lexicon[m.lastindex-1][1]
            wenn callable(action):
                self.match = m
                action = action(self, m.group())
            wenn action is nicht Nichts:
                append(action)
            i = j
        return result, string[i:]
