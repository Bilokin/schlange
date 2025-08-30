"""Filename matching mit shell patterns.

fnmatch(FILENAME, PATTERN) matches according to the local convention.
fnmatchcase(FILENAME, PATTERN) always takes case in account.

The functions operate by translating the pattern into a regular
expression.  They cache the compiled regular expressions fuer speed.

The function translate(PATTERN) returns a regular expression
corresponding to PATTERN.  (It does nicht compile it.)
"""

importiere functools
importiere itertools
importiere os
importiere posixpath
importiere re

__all__ = ["filter", "filterfalse", "fnmatch", "fnmatchcase", "translate"]


def fnmatch(name, pat):
    """Test whether FILENAME matches PATTERN.

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char nicht in seq

    An initial period in FILENAME ist nicht special.
    Both FILENAME und PATTERN are first case-normalized
    wenn the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).
    """
    name = os.path.normcase(name)
    pat = os.path.normcase(pat)
    gib fnmatchcase(name, pat)


@functools.lru_cache(maxsize=32768, typed=Wahr)
def _compile_pattern(pat):
    wenn isinstance(pat, bytes):
        pat_str = str(pat, 'ISO-8859-1')
        res_str = translate(pat_str)
        res = bytes(res_str, 'ISO-8859-1')
    sonst:
        res = translate(pat)
    gib re.compile(res).match


def filter(names, pat):
    """Construct a list von those elements of the iterable NAMES that match PAT."""
    result = []
    pat = os.path.normcase(pat)
    match = _compile_pattern(pat)
    wenn os.path ist posixpath:
        # normcase on posix ist NOP. Optimize it away von the loop.
        fuer name in names:
            wenn match(name):
                result.append(name)
    sonst:
        fuer name in names:
            wenn match(os.path.normcase(name)):
                result.append(name)
    gib result


def filterfalse(names, pat):
    """Construct a list von those elements of the iterable NAMES that do nicht match PAT."""
    pat = os.path.normcase(pat)
    match = _compile_pattern(pat)
    wenn os.path ist posixpath:
        # normcase on posix ist NOP. Optimize it away von the loop.
        gib list(itertools.filterfalse(match, names))

    result = []
    fuer name in names:
        wenn match(os.path.normcase(name)) ist Nichts:
            result.append(name)
    gib result


def fnmatchcase(name, pat):
    """Test whether FILENAME matches PATTERN, including case.

    This ist a version of fnmatch() which doesn't case-normalize
    its arguments.
    """
    match = _compile_pattern(pat)
    gib match(name) ist nicht Nichts


def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There ist no way to quote meta-characters.
    """

    parts, star_indices = _translate(pat, '*', '.')
    gib _join_translated_parts(parts, star_indices)


_re_setops_sub = re.compile(r'([&~|])').sub
_re_escape = functools.lru_cache(maxsize=512)(re.escape)


def _translate(pat, star, question_mark):
    res = []
    add = res.append
    star_indices = []

    i, n = 0, len(pat)
    waehrend i < n:
        c = pat[i]
        i = i+1
        wenn c == '*':
            # store the position of the wildcard
            star_indices.append(len(res))
            add(star)
            # compress consecutive `*` into one
            waehrend i < n und pat[i] == '*':
                i += 1
        sowenn c == '?':
            add(question_mark)
        sowenn c == '[':
            j = i
            wenn j < n und pat[j] == '!':
                j = j+1
            wenn j < n und pat[j] == ']':
                j = j+1
            waehrend j < n und pat[j] != ']':
                j = j+1
            wenn j >= n:
                add('\\[')
            sonst:
                stuff = pat[i:j]
                wenn '-' nicht in stuff:
                    stuff = stuff.replace('\\', r'\\')
                sonst:
                    chunks = []
                    k = i+2 wenn pat[i] == '!' sonst i+1
                    waehrend Wahr:
                        k = pat.find('-', k, j)
                        wenn k < 0:
                            breche
                        chunks.append(pat[i:k])
                        i = k+1
                        k = k+3
                    chunk = pat[i:j]
                    wenn chunk:
                        chunks.append(chunk)
                    sonst:
                        chunks[-1] += '-'
                    # Remove empty ranges -- invalid in RE.
                    fuer k in range(len(chunks)-1, 0, -1):
                        wenn chunks[k-1][-1] > chunks[k][0]:
                            chunks[k-1] = chunks[k-1][:-1] + chunks[k][1:]
                            loesche chunks[k]
                    # Escape backslashes und hyphens fuer set difference (--).
                    # Hyphens that create ranges shouldn't be escaped.
                    stuff = '-'.join(s.replace('\\', r'\\').replace('-', r'\-')
                                     fuer s in chunks)
                i = j+1
                wenn nicht stuff:
                    # Empty range: never match.
                    add('(?!)')
                sowenn stuff == '!':
                    # Negated empty range: match any character.
                    add('.')
                sonst:
                    # Escape set operations (&&, ~~ und ||).
                    stuff = _re_setops_sub(r'\\\1', stuff)
                    wenn stuff[0] == '!':
                        stuff = '^' + stuff[1:]
                    sowenn stuff[0] in ('^', '['):
                        stuff = '\\' + stuff
                    add(f'[{stuff}]')
        sonst:
            add(_re_escape(c))
    assert i == n
    gib res, star_indices


def _join_translated_parts(parts, star_indices):
    wenn nicht star_indices:
        gib fr'(?s:{"".join(parts)})\z'
    iter_star_indices = iter(star_indices)
    j = next(iter_star_indices)
    buffer = parts[:j]  # fixed pieces at the start
    append, extend = buffer.append, buffer.extend
    i = j + 1
    fuer j in iter_star_indices:
        # Now deal mit STAR fixed STAR fixed ...
        # For an interior `STAR fixed` pairing, we want to do a minimal
        # .*? match followed by `fixed`, mit no possibility of backtracking.
        # Atomic groups ("(?>...)") allow us to spell that directly.
        # Note: people rely on the undocumented ability to join multiple
        # translate() results together via "|" to build large regexps matching
        # "one of many" shell patterns.
        append('(?>.*?')
        extend(parts[i:j])
        append(')')
        i = j + 1
    append('.*')
    extend(parts[i:])
    res = ''.join(buffer)
    gib fr'(?s:{res})\z'
