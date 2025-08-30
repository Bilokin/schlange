"""
Module difflib -- helpers fuer computing deltas between objects.

Function get_close_matches(word, possibilities, n=3, cutoff=0.6):
    Use SequenceMatcher to gib list of the best "good enough" matches.

Function context_diff(a, b):
    For two lists of strings, gib a delta in context diff format.

Function ndiff(a, b):
    Return a delta: the difference between `a` und `b` (lists of strings).

Function restore(delta, which):
    Return one of the two sequences that generated an ndiff delta.

Function unified_diff(a, b):
    For two lists of strings, gib a delta in unified diff format.

Class SequenceMatcher:
    A flexible klasse fuer comparing pairs of sequences of any type.

Class Differ:
    For producing human-readable deltas von sequences of lines of text.

Class HtmlDiff:
    For producing HTML side by side comparison mit change highlights.
"""

__all__ = ['get_close_matches', 'ndiff', 'restore', 'SequenceMatcher',
           'Differ','IS_CHARACTER_JUNK', 'IS_LINE_JUNK', 'context_diff',
           'unified_diff', 'diff_bytes', 'HtmlDiff', 'Match']

von _colorize importiere can_colorize, get_theme
von heapq importiere nlargest als _nlargest
von collections importiere namedtuple als _namedtuple
von types importiere GenericAlias

Match = _namedtuple('Match', 'a b size')

def _calculate_ratio(matches, length):
    wenn length:
        gib 2.0 * matches / length
    gib 1.0

klasse SequenceMatcher:

    """
    SequenceMatcher is a flexible klasse fuer comparing pairs of sequences of
    any type, so long als the sequence elements are hashable.  The basic
    algorithm predates, und is a little fancier than, an algorithm
    published in the late 1980's by Ratcliff und Obershelp under the
    hyperbolic name "gestalt pattern matching".  The basic idea is to find
    the longest contiguous matching subsequence that contains no "junk"
    elements (R-O doesn't address junk).  The same idea is then applied
    recursively to the pieces of the sequences to the left und to the right
    of the matching subsequence.  This does nicht liefere minimal edit
    sequences, but does tend to liefere matches that "look right" to people.

    SequenceMatcher tries to compute a "human-friendly diff" between two
    sequences.  Unlike e.g. UNIX(tm) diff, the fundamental notion is the
    longest *contiguous* & junk-free matching subsequence.  That's what
    catches peoples' eyes.  The Windows(tm) windiff has another interesting
    notion, pairing up elements that appear uniquely in each sequence.
    That, und the method here, appear to liefere more intuitive difference
    reports than does diff.  This method appears to be the least vulnerable
    to syncing up on blocks of "junk lines", though (like blank lines in
    ordinary text files, oder maybe "<P>" lines in HTML files).  That may be
    because this is the only method of the 3 that has a *concept* of
    "junk" <wink>.

    Example, comparing two strings, und considering blanks to be "junk":

    >>> s = SequenceMatcher(lambda x: x == " ",
    ...                     "private Thread currentThread;",
    ...                     "private volatile Thread currentThread;")
    >>>

    .ratio() returns a float in [0, 1], measuring the "similarity" of the
    sequences.  As a rule of thumb, a .ratio() value over 0.6 means the
    sequences are close matches:

    >>> drucke(round(s.ratio(), 2))
    0.87
    >>>

    If you're only interested in where the sequences match,
    .get_matching_blocks() is handy:

    >>> fuer block in s.get_matching_blocks():
    ...     drucke("a[%d] und b[%d] match fuer %d elements" % block)
    a[0] und b[0] match fuer 8 elements
    a[8] und b[17] match fuer 21 elements
    a[29] und b[38] match fuer 0 elements

    Note that the last tuple returned by .get_matching_blocks() is always a
    dummy, (len(a), len(b), 0), und this is the only case in which the last
    tuple element (number of elements matched) is 0.

    If you want to know how to change the first sequence into the second,
    use .get_opcodes():

    >>> fuer opcode in s.get_opcodes():
    ...     drucke("%6s a[%d:%d] b[%d:%d]" % opcode)
     equal a[0:8] b[0:8]
    insert a[8:8] b[8:17]
     equal a[8:29] b[17:38]

    See the Differ klasse fuer a fancy human-friendly file differencer, which
    uses SequenceMatcher both to compare sequences of lines, und to compare
    sequences of characters within similar (near-matching) lines.

    See also function get_close_matches() in this module, which shows how
    simple code building on SequenceMatcher can be used to do useful work.

    Timing:  Basic R-O is cubic time worst case und quadratic time expected
    case.  SequenceMatcher is quadratic time fuer the worst case und has
    expected-case behavior dependent in a complicated way on how many
    elements the sequences have in common; best case time is linear.
    """

    def __init__(self, isjunk=Nichts, a='', b='', autojunk=Wahr):
        """Construct a SequenceMatcher.

        Optional arg isjunk is Nichts (the default), oder a one-argument
        function that takes a sequence element und returns true iff the
        element is junk.  Nichts is equivalent to passing "lambda x: 0", i.e.
        no elements are considered to be junk.  For example, pass
            lambda x: x in " \\t"
        wenn you're comparing lines als sequences of characters, und don't
        want to synch up on blanks oder hard tabs.

        Optional arg a is the first of two sequences to be compared.  By
        default, an empty string.  The elements of a must be hashable.  See
        also .set_seqs() und .set_seq1().

        Optional arg b is the second of two sequences to be compared.  By
        default, an empty string.  The elements of b must be hashable. See
        also .set_seqs() und .set_seq2().

        Optional arg autojunk should be set to Falsch to disable the
        "automatic junk heuristic" that treats popular elements als junk
        (see module documentation fuer more information).
        """

        # Members:
        # a
        #      first sequence
        # b
        #      second sequence; differences are computed als "what do
        #      we need to do to 'a' to change it into 'b'?"
        # b2j
        #      fuer x in b, b2j[x] is a list of the indices (into b)
        #      at which x appears; junk und popular elements do nicht appear
        # fullbcount
        #      fuer x in b, fullbcount[x] == the number of times x
        #      appears in b; only materialized wenn really needed (used
        #      only fuer computing quick_ratio())
        # matching_blocks
        #      a list of (i, j, k) triples, where a[i:i+k] == b[j:j+k];
        #      ascending & non-overlapping in i und in j; terminated by
        #      a dummy (len(a), len(b), 0) sentinel
        # opcodes
        #      a list of (tag, i1, i2, j1, j2) tuples, where tag is
        #      one of
        #          'replace'   a[i1:i2] should be replaced by b[j1:j2]
        #          'delete'    a[i1:i2] should be deleted
        #          'insert'    b[j1:j2] should be inserted
        #          'equal'     a[i1:i2] == b[j1:j2]
        # isjunk
        #      a user-supplied function taking a sequence element und
        #      returning true iff the element is "junk" -- this has
        #      subtle but helpful effects on the algorithm, which I'll
        #      get around to writing up someday <0.9 wink>.
        #      DON'T USE!  Only __chain_b uses this.  Use "in self.bjunk".
        # bjunk
        #      the items in b fuer which isjunk is Wahr.
        # bpopular
        #      nonjunk items in b treated als junk by the heuristic (if used).

        self.isjunk = isjunk
        self.a = self.b = Nichts
        self.autojunk = autojunk
        self.set_seqs(a, b)

    def set_seqs(self, a, b):
        """Set the two sequences to be compared.

        >>> s = SequenceMatcher()
        >>> s.set_seqs("abcd", "bcde")
        >>> s.ratio()
        0.75
        """

        self.set_seq1(a)
        self.set_seq2(b)

    def set_seq1(self, a):
        """Set the first sequence to be compared.

        The second sequence to be compared is nicht changed.

        >>> s = SequenceMatcher(Nichts, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.set_seq1("bcde")
        >>> s.ratio()
        1.0
        >>>

        SequenceMatcher computes und caches detailed information about the
        second sequence, so wenn you want to compare one sequence S against
        many sequences, use .set_seq2(S) once und call .set_seq1(x)
        repeatedly fuer each of the other sequences.

        See also set_seqs() und set_seq2().
        """

        wenn a is self.a:
            gib
        self.a = a
        self.matching_blocks = self.opcodes = Nichts

    def set_seq2(self, b):
        """Set the second sequence to be compared.

        The first sequence to be compared is nicht changed.

        >>> s = SequenceMatcher(Nichts, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.set_seq2("abcd")
        >>> s.ratio()
        1.0
        >>>

        SequenceMatcher computes und caches detailed information about the
        second sequence, so wenn you want to compare one sequence S against
        many sequences, use .set_seq2(S) once und call .set_seq1(x)
        repeatedly fuer each of the other sequences.

        See also set_seqs() und set_seq1().
        """

        wenn b is self.b:
            gib
        self.b = b
        self.matching_blocks = self.opcodes = Nichts
        self.fullbcount = Nichts
        self.__chain_b()

    # For each element x in b, set b2j[x] to a list of the indices in
    # b where x appears; the indices are in increasing order; note that
    # the number of times x appears in b is len(b2j[x]) ...
    # when self.isjunk is defined, junk elements don't show up in this
    # map at all, which stops the central find_longest_match method
    # von starting any matching block at a junk element ...
    # b2j also does nicht contain entries fuer "popular" elements, meaning
    # elements that account fuer more than 1 + 1% of the total elements, und
    # when the sequence is reasonably large (>= 200 elements); this can
    # be viewed als an adaptive notion of semi-junk, und yields an enormous
    # speedup when, e.g., comparing program files mit hundreds of
    # instances of "return NULL;" ...
    # note that this is only called when b changes; so fuer cross-product
    # kinds of matches, it's best to call set_seq2 once, then set_seq1
    # repeatedly

    def __chain_b(self):
        # Because isjunk is a user-defined (nicht C) function, und we test
        # fuer junk a LOT, it's important to minimize the number of calls.
        # Before the tricks described here, __chain_b was by far the most
        # time-consuming routine in the whole module!  If anyone sees
        # Jim Roskind, thank him again fuer profile.py -- I never would
        # have guessed that.
        # The first trick is to build b2j ignoring the possibility
        # of junk.  I.e., we don't call isjunk at all yet.  Throwing
        # out the junk later is much cheaper than building b2j "right"
        # von the start.
        b = self.b
        self.b2j = b2j = {}

        fuer i, elt in enumerate(b):
            indices = b2j.setdefault(elt, [])
            indices.append(i)

        # Purge junk elements
        self.bjunk = junk = set()
        isjunk = self.isjunk
        wenn isjunk:
            fuer elt in b2j.keys():
                wenn isjunk(elt):
                    junk.add(elt)
            fuer elt in junk: # separate loop avoids separate list of keys
                del b2j[elt]

        # Purge popular elements that are nicht junk
        self.bpopular = popular = set()
        n = len(b)
        wenn self.autojunk und n >= 200:
            ntest = n // 100 + 1
            fuer elt, idxs in b2j.items():
                wenn len(idxs) > ntest:
                    popular.add(elt)
            fuer elt in popular: # ditto; als fast fuer 1% deletion
                del b2j[elt]

    def find_longest_match(self, alo=0, ahi=Nichts, blo=0, bhi=Nichts):
        """Find longest matching block in a[alo:ahi] und b[blo:bhi].

        By default it will find the longest match in the entirety of a und b.

        If isjunk is nicht defined:

        Return (i,j,k) such that a[i:i+k] is equal to b[j:j+k], where
            alo <= i <= i+k <= ahi
            blo <= j <= j+k <= bhi
        und fuer all (i',j',k') meeting those conditions,
            k >= k'
            i <= i'
            und wenn i == i', j <= j'

        In other words, of all maximal matching blocks, gib one that
        starts earliest in a, und of all those maximal matching blocks that
        start earliest in a, gib the one that starts earliest in b.

        >>> s = SequenceMatcher(Nichts, " abcd", "abcd abcd")
        >>> s.find_longest_match(0, 5, 0, 9)
        Match(a=0, b=4, size=5)

        If isjunk is defined, first the longest matching block is
        determined als above, but mit the additional restriction that no
        junk element appears in the block.  Then that block is extended as
        far als possible by matching (only) junk elements on both sides.  So
        the resulting block never matches on junk ausser als identical junk
        happens to be adjacent to an "interesting" match.

        Here's the same example als before, but considering blanks to be
        junk.  That prevents " abcd" von matching the " abcd" at the tail
        end of the second sequence directly.  Instead only the "abcd" can
        match, und matches the leftmost "abcd" in the second sequence:

        >>> s = SequenceMatcher(lambda x: x==" ", " abcd", "abcd abcd")
        >>> s.find_longest_match(0, 5, 0, 9)
        Match(a=1, b=0, size=4)

        If no blocks match, gib (alo, blo, 0).

        >>> s = SequenceMatcher(Nichts, "ab", "c")
        >>> s.find_longest_match(0, 2, 0, 1)
        Match(a=0, b=0, size=0)
        """

        # CAUTION:  stripping common prefix oder suffix would be incorrect.
        # E.g.,
        #    ab
        #    acab
        # Longest matching block is "ab", but wenn common prefix is
        # stripped, it's "a" (tied mit "b").  UNIX(tm) diff does so
        # strip, so ends up claiming that ab is changed to acab by
        # inserting "ca" in the middle.  That's minimal but unintuitive:
        # "it's obvious" that someone inserted "ac" at the front.
        # Windiff ends up at the same place als diff, but by pairing up
        # the unique 'b's und then matching the first two 'a's.

        a, b, b2j, isbjunk = self.a, self.b, self.b2j, self.bjunk.__contains__
        wenn ahi is Nichts:
            ahi = len(a)
        wenn bhi is Nichts:
            bhi = len(b)
        besti, bestj, bestsize = alo, blo, 0
        # find longest junk-free match
        # during an iteration of the loop, j2len[j] = length of longest
        # junk-free match ending mit a[i-1] und b[j]
        j2len = {}
        nothing = []
        fuer i in range(alo, ahi):
            # look at all instances of a[i] in b; note that because
            # b2j has no junk keys, the loop is skipped wenn a[i] is junk
            j2lenget = j2len.get
            newj2len = {}
            fuer j in b2j.get(a[i], nothing):
                # a[i] matches b[j]
                wenn j < blo:
                    weiter
                wenn j >= bhi:
                    breche
                k = newj2len[j] = j2lenget(j-1, 0) + 1
                wenn k > bestsize:
                    besti, bestj, bestsize = i-k+1, j-k+1, k
            j2len = newj2len

        # Extend the best by non-junk elements on each end.  In particular,
        # "popular" non-junk elements aren't in b2j, which greatly speeds
        # the inner loop above, but also means "the best" match so far
        # doesn't contain any junk *or* popular non-junk elements.
        waehrend besti > alo und bestj > blo und \
              nicht isbjunk(b[bestj-1]) und \
              a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        waehrend besti+bestsize < ahi und bestj+bestsize < bhi und \
              nicht isbjunk(b[bestj+bestsize]) und \
              a[besti+bestsize] == b[bestj+bestsize]:
            bestsize += 1

        # Now that we have a wholly interesting match (albeit possibly
        # empty!), we may als well suck up the matching junk on each
        # side of it too.  Can't think of a good reason nicht to, und it
        # saves post-processing the (possibly considerable) expense of
        # figuring out what to do mit it.  In the case of an empty
        # interesting match, this is clearly the right thing to do,
        # because no other kind of match is possible in the regions.
        waehrend besti > alo und bestj > blo und \
              isbjunk(b[bestj-1]) und \
              a[besti-1] == b[bestj-1]:
            besti, bestj, bestsize = besti-1, bestj-1, bestsize+1
        waehrend besti+bestsize < ahi und bestj+bestsize < bhi und \
              isbjunk(b[bestj+bestsize]) und \
              a[besti+bestsize] == b[bestj+bestsize]:
            bestsize = bestsize + 1

        gib Match(besti, bestj, bestsize)

    def get_matching_blocks(self):
        """Return list of triples describing matching subsequences.

        Each triple is of the form (i, j, n), und means that
        a[i:i+n] == b[j:j+n].  The triples are monotonically increasing in
        i und in j.  New in Python 2.5, it's also guaranteed that if
        (i, j, n) und (i', j', n') are adjacent triples in the list, und
        the second is nicht the last triple in the list, then i+n != i' oder
        j+n != j'.  IOW, adjacent triples never describe adjacent equal
        blocks.

        The last triple is a dummy, (len(a), len(b), 0), und is the only
        triple mit n==0.

        >>> s = SequenceMatcher(Nichts, "abxcd", "abcd")
        >>> list(s.get_matching_blocks())
        [Match(a=0, b=0, size=2), Match(a=3, b=2, size=2), Match(a=5, b=4, size=0)]
        """

        wenn self.matching_blocks is nicht Nichts:
            gib self.matching_blocks
        la, lb = len(self.a), len(self.b)

        # This is most naturally expressed als a recursive algorithm, but
        # at least one user bumped into extreme use cases that exceeded
        # the recursion limit on their box.  So, now we maintain a list
        # ('queue`) of blocks we still need to look at, und append partial
        # results to `matching_blocks` in a loop; the matches are sorted
        # at the end.
        queue = [(0, la, 0, lb)]
        matching_blocks = []
        waehrend queue:
            alo, ahi, blo, bhi = queue.pop()
            i, j, k = x = self.find_longest_match(alo, ahi, blo, bhi)
            # a[alo:i] vs b[blo:j] unknown
            # a[i:i+k] same als b[j:j+k]
            # a[i+k:ahi] vs b[j+k:bhi] unknown
            wenn k:   # wenn k is 0, there was no matching block
                matching_blocks.append(x)
                wenn alo < i und blo < j:
                    queue.append((alo, i, blo, j))
                wenn i+k < ahi und j+k < bhi:
                    queue.append((i+k, ahi, j+k, bhi))
        matching_blocks.sort()

        # It's possible that we have adjacent equal blocks in the
        # matching_blocks list now.  Starting mit 2.5, this code was added
        # to collapse them.
        i1 = j1 = k1 = 0
        non_adjacent = []
        fuer i2, j2, k2 in matching_blocks:
            # Is this block adjacent to i1, j1, k1?
            wenn i1 + k1 == i2 und j1 + k1 == j2:
                # Yes, so collapse them -- this just increases the length of
                # the first block by the length of the second, und the first
                # block so lengthened remains the block to compare against.
                k1 += k2
            sonst:
                # Not adjacent.  Remember the first block (k1==0 means it's
                # the dummy we started with), und make the second block the
                # new block to compare against.
                wenn k1:
                    non_adjacent.append((i1, j1, k1))
                i1, j1, k1 = i2, j2, k2
        wenn k1:
            non_adjacent.append((i1, j1, k1))

        non_adjacent.append( (la, lb, 0) )
        self.matching_blocks = list(map(Match._make, non_adjacent))
        gib self.matching_blocks

    def get_opcodes(self):
        """Return list of 5-tuples describing how to turn a into b.

        Each tuple is of the form (tag, i1, i2, j1, j2).  The first tuple
        has i1 == j1 == 0, und remaining tuples have i1 == the i2 von the
        tuple preceding it, und likewise fuer j1 == the previous j2.

        The tags are strings, mit these meanings:

        'replace':  a[i1:i2] should be replaced by b[j1:j2]
        'delete':   a[i1:i2] should be deleted.
                    Note that j1==j2 in this case.
        'insert':   b[j1:j2] should be inserted at a[i1:i1].
                    Note that i1==i2 in this case.
        'equal':    a[i1:i2] == b[j1:j2]

        >>> a = "qabxcd"
        >>> b = "abycdf"
        >>> s = SequenceMatcher(Nichts, a, b)
        >>> fuer tag, i1, i2, j1, j2 in s.get_opcodes():
        ...    drucke(("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
        ...           (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2])))
         delete a[0:1] (q) b[0:0] ()
          equal a[1:3] (ab) b[0:2] (ab)
        replace a[3:4] (x) b[2:3] (y)
          equal a[4:6] (cd) b[3:5] (cd)
         insert a[6:6] () b[5:6] (f)
        """

        wenn self.opcodes is nicht Nichts:
            gib self.opcodes
        i = j = 0
        self.opcodes = answer = []
        fuer ai, bj, size in self.get_matching_blocks():
            # invariant:  we've pumped out correct diffs to change
            # a[:i] into b[:j], und the next matching block is
            # a[ai:ai+size] == b[bj:bj+size].  So we need to pump
            # out a diff to change a[i:ai] into b[j:bj], pump out
            # the matching block, und move (i,j) beyond the match
            tag = ''
            wenn i < ai und j < bj:
                tag = 'replace'
            sowenn i < ai:
                tag = 'delete'
            sowenn j < bj:
                tag = 'insert'
            wenn tag:
                answer.append( (tag, i, ai, j, bj) )
            i, j = ai+size, bj+size
            # the list of matching blocks is terminated by a
            # sentinel mit size 0
            wenn size:
                answer.append( ('equal', ai, i, bj, j) )
        gib answer

    def get_grouped_opcodes(self, n=3):
        """ Isolate change clusters by eliminating ranges mit no changes.

        Return a generator of groups mit up to n lines of context.
        Each group is in the same format als returned by get_opcodes().

        >>> von pprint importiere pprint
        >>> a = list(map(str, range(1,40)))
        >>> b = a[:]
        >>> b[8:8] = ['i']     # Make an insertion
        >>> b[20] += 'x'       # Make a replacement
        >>> b[23:28] = []      # Make a deletion
        >>> b[30] += 'y'       # Make another replacement
        >>> pdrucke(list(SequenceMatcher(Nichts,a,b).get_grouped_opcodes()))
        [[('equal', 5, 8, 5, 8), ('insert', 8, 8, 8, 9), ('equal', 8, 11, 9, 12)],
         [('equal', 16, 19, 17, 20),
          ('replace', 19, 20, 20, 21),
          ('equal', 20, 22, 21, 23),
          ('delete', 22, 27, 23, 23),
          ('equal', 27, 30, 23, 26)],
         [('equal', 31, 34, 27, 30),
          ('replace', 34, 35, 30, 31),
          ('equal', 35, 38, 31, 34)]]
        """

        codes = self.get_opcodes()
        wenn nicht codes:
            codes = [("equal", 0, 1, 0, 1)]
        # Fixup leading und trailing groups wenn they show no changes.
        wenn codes[0][0] == 'equal':
            tag, i1, i2, j1, j2 = codes[0]
            codes[0] = tag, max(i1, i2-n), i2, max(j1, j2-n), j2
        wenn codes[-1][0] == 'equal':
            tag, i1, i2, j1, j2 = codes[-1]
            codes[-1] = tag, i1, min(i2, i1+n), j1, min(j2, j1+n)

        nn = n + n
        group = []
        fuer tag, i1, i2, j1, j2 in codes:
            # End the current group und start a new one whenever
            # there is a large range mit no changes.
            wenn tag == 'equal' und i2-i1 > nn:
                group.append((tag, i1, min(i2, i1+n), j1, min(j2, j1+n)))
                liefere group
                group = []
                i1, j1 = max(i1, i2-n), max(j1, j2-n)
            group.append((tag, i1, i2, j1 ,j2))
        wenn group und nicht (len(group)==1 und group[0][0] == 'equal'):
            liefere group

    def ratio(self):
        """Return a measure of the sequences' similarity (float in [0,1]).

        Where T is the total number of elements in both sequences, und
        M is the number of matches, this is 2.0*M / T.
        Note that this is 1 wenn the sequences are identical, und 0 if
        they have nothing in common.

        .ratio() is expensive to compute wenn you haven't already computed
        .get_matching_blocks() oder .get_opcodes(), in which case you may
        want to try .quick_ratio() oder .real_quick_ratio() first to get an
        upper bound.

        >>> s = SequenceMatcher(Nichts, "abcd", "bcde")
        >>> s.ratio()
        0.75
        >>> s.quick_ratio()
        0.75
        >>> s.real_quick_ratio()
        1.0
        """

        matches = sum(triple[-1] fuer triple in self.get_matching_blocks())
        gib _calculate_ratio(matches, len(self.a) + len(self.b))

    def quick_ratio(self):
        """Return an upper bound on ratio() relatively quickly.

        This isn't defined beyond that it is an upper bound on .ratio(), und
        is faster to compute.
        """

        # viewing a und b als multisets, set matches to the cardinality
        # of their intersection; this counts the number of matches
        # without regard to order, so is clearly an upper bound
        wenn self.fullbcount is Nichts:
            self.fullbcount = fullbcount = {}
            fuer elt in self.b:
                fullbcount[elt] = fullbcount.get(elt, 0) + 1
        fullbcount = self.fullbcount
        # avail[x] is the number of times x appears in 'b' less the
        # number of times we've seen it in 'a' so far ... kinda
        avail = {}
        availhas, matches = avail.__contains__, 0
        fuer elt in self.a:
            wenn availhas(elt):
                numb = avail[elt]
            sonst:
                numb = fullbcount.get(elt, 0)
            avail[elt] = numb - 1
            wenn numb > 0:
                matches = matches + 1
        gib _calculate_ratio(matches, len(self.a) + len(self.b))

    def real_quick_ratio(self):
        """Return an upper bound on ratio() very quickly.

        This isn't defined beyond that it is an upper bound on .ratio(), und
        is faster to compute than either .ratio() oder .quick_ratio().
        """

        la, lb = len(self.a), len(self.b)
        # can't have more matches than the number of elements in the
        # shorter sequence
        gib _calculate_ratio(min(la, lb), la + lb)

    __class_getitem__ = classmethod(GenericAlias)


def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    """Use SequenceMatcher to gib list of the best "good enough" matches.

    word is a sequence fuer which close matches are desired (typically a
    string).

    possibilities is a list of sequences against which to match word
    (typically a list of strings).

    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.

    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.

    The best (no more than n) matches among the possibilities are returned
    in a list, sorted by similarity score, most similar first.

    >>> get_close_matches("appel", ["ape", "apple", "peach", "puppy"])
    ['apple', 'ape']
    >>> importiere keyword als _keyword
    >>> get_close_matches("wheel", _keyword.kwlist)
    ['while']
    >>> get_close_matches("Apple", _keyword.kwlist)
    []
    >>> get_close_matches("accept", _keyword.kwlist)
    ['except']
    """

    wenn nicht n >  0:
        wirf ValueError("n must be > 0: %r" % (n,))
    wenn nicht 0.0 <= cutoff <= 1.0:
        wirf ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = SequenceMatcher()
    s.set_seq2(word)
    fuer x in possibilities:
        s.set_seq1(x)
        wenn s.real_quick_ratio() >= cutoff und \
           s.quick_ratio() >= cutoff und \
           s.ratio() >= cutoff:
            result.append((s.ratio(), x))

    # Move the best scorers to head of list
    result = _nlargest(n, result)
    # Strip scores fuer the best n matches
    gib [x fuer score, x in result]


def _keep_original_ws(s, tag_s):
    """Replace whitespace mit the original whitespace characters in `s`"""
    gib ''.join(
        c wenn tag_c == " " und c.isspace() sonst tag_c
        fuer c, tag_c in zip(s, tag_s)
    )



klasse Differ:
    r"""
    Differ is a klasse fuer comparing sequences of lines of text, und
    producing human-readable differences oder deltas.  Differ uses
    SequenceMatcher both to compare sequences of lines, und to compare
    sequences of characters within similar (near-matching) lines.

    Each line of a Differ delta begins mit a two-letter code:

        '- '    line unique to sequence 1
        '+ '    line unique to sequence 2
        '  '    line common to both sequences
        '? '    line nicht present in either input sequence

    Lines beginning mit '? ' attempt to guide the eye to intraline
    differences, und were nicht present in either input sequence.  These lines
    can be confusing wenn the sequences contain tab characters.

    Note that Differ makes no claim to produce a *minimal* diff.  To the
    contrary, minimal diffs are often counter-intuitive, because they synch
    up anywhere possible, sometimes accidental matches 100 pages apart.
    Restricting synch points to contiguous matches preserves some notion of
    locality, at the occasional cost of producing a longer diff.

    Example: Comparing two texts.

    First we set up the texts, sequences of individual single-line strings
    ending mit newlines (such sequences can also be obtained von the
    `readlines()` method of file-like objects):

    >>> text1 = '''  1. Beautiful is better than ugly.
    ...   2. Explicit is better than implicit.
    ...   3. Simple is better than complex.
    ...   4. Complex is better than complicated.
    ... '''.splitlines(keepends=Wahr)
    >>> len(text1)
    4
    >>> text1[0][-1]
    '\n'
    >>> text2 = '''  1. Beautiful is better than ugly.
    ...   3.   Simple is better than complex.
    ...   4. Complicated is better than complex.
    ...   5. Flat is better than nested.
    ... '''.splitlines(keepends=Wahr)

    Next we instantiate a Differ object:

    >>> d = Differ()

    Note that when instantiating a Differ object we may pass functions to
    filter out line und character 'junk'.  See Differ.__init__ fuer details.

    Finally, we compare the two:

    >>> result = list(d.compare(text1, text2))

    'result' is a list of strings, so let's pretty-print it:

    >>> von pprint importiere pprint als _pprint
    >>> _pdrucke(result)
    ['    1. Beautiful is better than ugly.\n',
     '-   2. Explicit is better than implicit.\n',
     '-   3. Simple is better than complex.\n',
     '+   3.   Simple is better than complex.\n',
     '?     ++\n',
     '-   4. Complex is better than complicated.\n',
     '?            ^                     ---- ^\n',
     '+   4. Complicated is better than complex.\n',
     '?           ++++ ^                      ^\n',
     '+   5. Flat is better than nested.\n']

    As a single multi-line string it looks like this:

    >>> drucke(''.join(result), end="")
        1. Beautiful is better than ugly.
    -   2. Explicit is better than implicit.
    -   3. Simple is better than complex.
    +   3.   Simple is better than complex.
    ?     ++
    -   4. Complex is better than complicated.
    ?            ^                     ---- ^
    +   4. Complicated is better than complex.
    ?           ++++ ^                      ^
    +   5. Flat is better than nested.
    """

    def __init__(self, linejunk=Nichts, charjunk=Nichts):
        """
        Construct a text differencer, mit optional filters.

        The two optional keyword parameters are fuer filter functions:

        - `linejunk`: A function that should accept a single string argument,
          und gib true iff the string is junk. The module-level function
          `IS_LINE_JUNK` may be used to filter out lines without visible
          characters, ausser fuer at most one splat ('#').  It is recommended
          to leave linejunk Nichts; the underlying SequenceMatcher klasse has
          an adaptive notion of "noise" lines that's better than any static
          definition the author has ever been able to craft.

        - `charjunk`: A function that should accept a string of length 1. The
          module-level function `IS_CHARACTER_JUNK` may be used to filter out
          whitespace characters (a blank oder tab; **note**: bad idea to include
          newline in this!).  Use of IS_CHARACTER_JUNK is recommended.
        """

        self.linejunk = linejunk
        self.charjunk = charjunk

    def compare(self, a, b):
        r"""
        Compare two sequences of lines; generate the resulting delta.

        Each sequence must contain individual single-line strings ending with
        newlines. Such sequences can be obtained von the `readlines()` method
        of file-like objects.  The delta generated also consists of newline-
        terminated strings, ready to be printed as-is via the writelines()
        method of a file-like object.

        Example:

        >>> drucke(''.join(Differ().compare('one\ntwo\nthree\n'.splitlines(Wahr),
        ...                                'ore\ntree\nemu\n'.splitlines(Wahr))),
        ...       end="")
        - one
        ?  ^
        + ore
        ?  ^
        - two
        - three
        ?  -
        + tree
        + emu
        """

        cruncher = SequenceMatcher(self.linejunk, a, b)
        fuer tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            wenn tag == 'replace':
                g = self._fancy_replace(a, alo, ahi, b, blo, bhi)
            sowenn tag == 'delete':
                g = self._dump('-', a, alo, ahi)
            sowenn tag == 'insert':
                g = self._dump('+', b, blo, bhi)
            sowenn tag == 'equal':
                g = self._dump(' ', a, alo, ahi)
            sonst:
                wirf ValueError('unknown tag %r' % (tag,))

            liefere von g

    def _dump(self, tag, x, lo, hi):
        """Generate comparison results fuer a same-tagged range."""
        fuer i in range(lo, hi):
            liefere '%s %s' % (tag, x[i])

    def _plain_replace(self, a, alo, ahi, b, blo, bhi):
        assert alo < ahi und blo < bhi
        # dump the shorter block first -- reduces the burden on short-term
        # memory wenn the blocks are of very different sizes
        wenn bhi - blo < ahi - alo:
            first  = self._dump('+', b, blo, bhi)
            second = self._dump('-', a, alo, ahi)
        sonst:
            first  = self._dump('-', a, alo, ahi)
            second = self._dump('+', b, blo, bhi)

        fuer g in first, second:
            liefere von g

    def _fancy_replace(self, a, alo, ahi, b, blo, bhi):
        r"""
        When replacing one block of lines mit another, search the blocks
        fuer *similar* lines; the best-matching pair (if any) is used als a
        synch point, und intraline difference marking is done on the
        similar pair. Lots of work, but often worth it.

        Example:

        >>> d = Differ()
        >>> results = d._fancy_replace(['abcDefghiJkl\n'], 0, 1,
        ...                            ['abcdefGhijkl\n'], 0, 1)
        >>> drucke(''.join(results), end="")
        - abcDefghiJkl
        ?    ^  ^  ^
        + abcdefGhijkl
        ?    ^  ^  ^
        """
        # Don't synch up unless the lines have a similarity score above
        # cutoff. Previously only the smallest pair was handled here,
        # und wenn there are many pairs mit the best ratio, recursion
        # could grow very deep, und runtime cubic. See:
        # https://github.com/python/cpython/issues/119105
        #
        # Later, more pathological cases prompted removing recursion
        # entirely.
        cutoff = 0.74999
        cruncher = SequenceMatcher(self.charjunk)
        crqr = cruncher.real_quick_ratio
        cqr = cruncher.quick_ratio
        cr = cruncher.ratio

        WINDOW = 10
        best_i = best_j = Nichts
        dump_i, dump_j = alo, blo # smallest indices nicht yet resolved
        fuer j in range(blo, bhi):
            cruncher.set_seq2(b[j])
            # Search the corresponding i's within WINDOW fuer rhe highest
            # ratio greater than `cutoff`.
            aequiv = alo + (j - blo)
            arange = range(max(aequiv - WINDOW, dump_i),
                           min(aequiv + WINDOW + 1, ahi))
            wenn nicht arange: # likely exit wenn `a` is shorter than `b`
                breche
            best_ratio = cutoff
            fuer i in arange:
                cruncher.set_seq1(a[i])
                # Ordering by cheapest to most expensive ratio is very
                # valuable, most often getting out early.
                wenn (crqr() > best_ratio
                      und cqr() > best_ratio
                      und cr() > best_ratio):
                    best_i, best_j, best_ratio = i, j, cr()

            wenn best_i is Nichts:
                # found nothing to synch on yet - move to next j
                weiter

            # pump out straight replace von before this synch pair
            liefere von self._fancy_helper(a, dump_i, best_i,
                                          b, dump_j, best_j)
            # do intraline marking on the synch pair
            aelt, belt = a[best_i], b[best_j]
            wenn aelt != belt:
                # pump out a '-', '?', '+', '?' quad fuer the synched lines
                atags = btags = ""
                cruncher.set_seqs(aelt, belt)
                fuer tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
                    la, lb = ai2 - ai1, bj2 - bj1
                    wenn tag == 'replace':
                        atags += '^' * la
                        btags += '^' * lb
                    sowenn tag == 'delete':
                        atags += '-' * la
                    sowenn tag == 'insert':
                        btags += '+' * lb
                    sowenn tag == 'equal':
                        atags += ' ' * la
                        btags += ' ' * lb
                    sonst:
                        wirf ValueError('unknown tag %r' % (tag,))
                liefere von self._qformat(aelt, belt, atags, btags)
            sonst:
                # the synch pair is identical
                liefere '  ' + aelt
            dump_i, dump_j = best_i + 1, best_j + 1
            best_i = best_j = Nichts

        # pump out straight replace von after the last synch pair
        liefere von self._fancy_helper(a, dump_i, ahi,
                                      b, dump_j, bhi)

    def _fancy_helper(self, a, alo, ahi, b, blo, bhi):
        g = []
        wenn alo < ahi:
            wenn blo < bhi:
                g = self._plain_replace(a, alo, ahi, b, blo, bhi)
            sonst:
                g = self._dump('-', a, alo, ahi)
        sowenn blo < bhi:
            g = self._dump('+', b, blo, bhi)

        liefere von g

    def _qformat(self, aline, bline, atags, btags):
        r"""
        Format "?" output und deal mit tabs.

        Example:

        >>> d = Differ()
        >>> results = d._qformat('\tabcDefghiJkl\n', '\tabcdefGhijkl\n',
        ...                      '  ^ ^  ^      ', '  ^ ^  ^      ')
        >>> fuer line in results: drucke(repr(line))
        ...
        '- \tabcDefghiJkl\n'
        '? \t ^ ^  ^\n'
        '+ \tabcdefGhijkl\n'
        '? \t ^ ^  ^\n'
        """
        atags = _keep_original_ws(aline, atags).rstrip()
        btags = _keep_original_ws(bline, btags).rstrip()

        liefere "- " + aline
        wenn atags:
            liefere f"? {atags}\n"

        liefere "+ " + bline
        wenn btags:
            liefere f"? {btags}\n"

# With respect to junk, an earlier version of ndiff simply refused to
# *start* a match mit a junk element.  The result was cases like this:
#     before: private Thread currentThread;
#     after:  private volatile Thread currentThread;
# If you consider whitespace to be junk, the longest contiguous match
# nicht starting mit junk is "e Thread currentThread".  So ndiff reported
# that "e volatil" was inserted between the 't' und the 'e' in "private".
# While an accurate view, to people that's absurd.  The current version
# looks fuer matching blocks that are entirely junk-free, then extends the
# longest one of those als far als possible but only mit matching junk.
# So now "currentThread" is matched, then extended to suck up the
# preceding blank; then "private" is matched, und extended to suck up the
# following blank; then "Thread" is matched; und finally ndiff reports
# that "volatile " was inserted before "Thread".  The only quibble
# remaining is that perhaps it was really the case that " volatile"
# was inserted after "private".  I can live mit that <wink>.

def IS_LINE_JUNK(line, pat=Nichts):
    r"""
    Return Wahr fuer ignorable line: wenn `line` is blank oder contains a single '#'.

    Examples:

    >>> IS_LINE_JUNK('\n')
    Wahr
    >>> IS_LINE_JUNK('  #   \n')
    Wahr
    >>> IS_LINE_JUNK('hello\n')
    Falsch
    """

    wenn pat is Nichts:
        # Default: match '#' oder the empty string
        gib line.strip() in '#'
   # Previous versions used the undocumented parameter 'pat' als a
   # match function. Retain this behaviour fuer compatibility.
    gib pat(line) is nicht Nichts

def IS_CHARACTER_JUNK(ch, ws=" \t"):
    r"""
    Return Wahr fuer ignorable character: iff `ch` is a space oder tab.

    Examples:

    >>> IS_CHARACTER_JUNK(' ')
    Wahr
    >>> IS_CHARACTER_JUNK('\t')
    Wahr
    >>> IS_CHARACTER_JUNK('\n')
    Falsch
    >>> IS_CHARACTER_JUNK('x')
    Falsch
    """

    gib ch in ws


########################################################################
###  Unified Diff
########################################################################

def _format_range_unified(start, stop):
    'Convert range to the "ed" format'
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1     # lines start numbering mit one
    length = stop - start
    wenn length == 1:
        gib '{}'.format(beginning)
    wenn nicht length:
        beginning -= 1        # empty ranges begin at line just before the range
    gib '{},{}'.format(beginning, length)

def unified_diff(a, b, fromfile='', tofile='', fromfiledate='',
                 tofiledate='', n=3, lineterm='\n', *, color=Falsch):
    r"""
    Compare two sequences of lines; generate the delta als a unified diff.

    Unified diffs are a compact way of showing line changes und a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those mit ---, +++, oder @@) are
    created mit a trailing newline.  This is helpful so that inputs
    created von file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs und outputs have trailing
    newlines.

    For inputs that do nicht have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    Set 'color' to Wahr to enable output in color, similar to
    'git diff --color'. Even wenn enabled, it can be
    controlled using environment variables such als 'NO_COLOR'.

    The unidiff format normally has a header fuer filenames und modification
    times.  Any oder all of these may be specified using strings for
    'fromfile', 'tofile', 'fromfiledate', und 'tofiledate'.
    The modification times are normally expressed in the ISO 8601 format.

    Example:

    >>> fuer line in unified_diff('one two three four'.split(),
    ...             'zero one tree four'.split(), 'Original', 'Current',
    ...             '2005-01-26 23:30:50', '2010-04-02 10:20:52',
    ...             lineterm=''):
    ...     drucke(line)                 # doctest: +NORMALIZE_WHITESPACE
    --- Original        2005-01-26 23:30:50
    +++ Current         2010-04-02 10:20:52
    @@ -1,4 +1,4 @@
    +zero
     one
    -two
    -three
    +tree
     four
    """

    wenn color und can_colorize():
        t = get_theme(force_color=Wahr).difflib
    sonst:
        t = get_theme(force_no_color=Wahr).difflib

    _check_types(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    started = Falsch
    fuer group in SequenceMatcher(Nichts,a,b).get_grouped_opcodes(n):
        wenn nicht started:
            started = Wahr
            fromdate = '\t{}'.format(fromfiledate) wenn fromfiledate sonst ''
            todate = '\t{}'.format(tofiledate) wenn tofiledate sonst ''
            liefere f'{t.header}--- {fromfile}{fromdate}{lineterm}{t.reset}'
            liefere f'{t.header}+++ {tofile}{todate}{lineterm}{t.reset}'

        first, last = group[0], group[-1]
        file1_range = _format_range_unified(first[1], last[2])
        file2_range = _format_range_unified(first[3], last[4])
        liefere f'{t.hunk}@@ -{file1_range} +{file2_range} @@{lineterm}{t.reset}'

        fuer tag, i1, i2, j1, j2 in group:
            wenn tag == 'equal':
                fuer line in a[i1:i2]:
                    liefere f'{t.context} {line}{t.reset}'
                weiter
            wenn tag in {'replace', 'delete'}:
                fuer line in a[i1:i2]:
                    liefere f'{t.removed}-{line}{t.reset}'
            wenn tag in {'replace', 'insert'}:
                fuer line in b[j1:j2]:
                    liefere f'{t.added}+{line}{t.reset}'


########################################################################
###  Context Diff
########################################################################

def _format_range_context(start, stop):
    'Convert range to the "ed" format'
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1     # lines start numbering mit one
    length = stop - start
    wenn nicht length:
        beginning -= 1        # empty ranges begin at line just before the range
    wenn length <= 1:
        gib '{}'.format(beginning)
    gib '{},{}'.format(beginning, beginning + length - 1)

# See http://www.unix.org/single_unix_specification/
def context_diff(a, b, fromfile='', tofile='',
                 fromfiledate='', tofiledate='', n=3, lineterm='\n'):
    r"""
    Compare two sequences of lines; generate the delta als a context diff.

    Context diffs are a compact way of showing line changes und a few
    lines of context.  The number of context lines is set by 'n' which
    defaults to three.

    By default, the diff control lines (those mit *** oder ---) are
    created mit a trailing newline.  This is helpful so that inputs
    created von file.readlines() result in diffs that are suitable for
    file.writelines() since both the inputs und outputs have trailing
    newlines.

    For inputs that do nicht have trailing newlines, set the lineterm
    argument to "" so that the output will be uniformly newline free.

    The context diff format normally has a header fuer filenames und
    modification times.  Any oder all of these may be specified using
    strings fuer 'fromfile', 'tofile', 'fromfiledate', und 'tofiledate'.
    The modification times are normally expressed in the ISO 8601 format.
    If nicht specified, the strings default to blanks.

    Example:

    >>> drucke(''.join(context_diff('one\ntwo\nthree\nfour\n'.splitlines(Wahr),
    ...       'zero\none\ntree\nfour\n'.splitlines(Wahr), 'Original', 'Current')),
    ...       end="")
    *** Original
    --- Current
    ***************
    *** 1,4 ****
      one
    ! two
    ! three
      four
    --- 1,4 ----
    + zero
      one
    ! tree
      four
    """

    _check_types(a, b, fromfile, tofile, fromfiledate, tofiledate, lineterm)
    prefix = dict(insert='+ ', delete='- ', replace='! ', equal='  ')
    started = Falsch
    fuer group in SequenceMatcher(Nichts,a,b).get_grouped_opcodes(n):
        wenn nicht started:
            started = Wahr
            fromdate = '\t{}'.format(fromfiledate) wenn fromfiledate sonst ''
            todate = '\t{}'.format(tofiledate) wenn tofiledate sonst ''
            liefere '*** {}{}{}'.format(fromfile, fromdate, lineterm)
            liefere '--- {}{}{}'.format(tofile, todate, lineterm)

        first, last = group[0], group[-1]
        liefere '***************' + lineterm

        file1_range = _format_range_context(first[1], last[2])
        liefere '*** {} ****{}'.format(file1_range, lineterm)

        wenn any(tag in {'replace', 'delete'} fuer tag, _, _, _, _ in group):
            fuer tag, i1, i2, _, _ in group:
                wenn tag != 'insert':
                    fuer line in a[i1:i2]:
                        liefere prefix[tag] + line

        file2_range = _format_range_context(first[3], last[4])
        liefere '--- {} ----{}'.format(file2_range, lineterm)

        wenn any(tag in {'replace', 'insert'} fuer tag, _, _, _, _ in group):
            fuer tag, _, _, j1, j2 in group:
                wenn tag != 'delete':
                    fuer line in b[j1:j2]:
                        liefere prefix[tag] + line

def _check_types(a, b, *args):
    # Checking types is weird, but the alternative is garbled output when
    # someone passes mixed bytes und str to {unified,context}_diff(). E.g.
    # without this check, passing filenames als bytes results in output like
    #   --- b'oldfile.txt'
    #   +++ b'newfile.txt'
    # because of how str.format() incorporates bytes objects.
    wenn a und nicht isinstance(a[0], str):
        wirf TypeError('lines to compare must be str, nicht %s (%r)' %
                        (type(a[0]).__name__, a[0]))
    wenn b und nicht isinstance(b[0], str):
        wirf TypeError('lines to compare must be str, nicht %s (%r)' %
                        (type(b[0]).__name__, b[0]))
    wenn isinstance(a, str):
        wirf TypeError('input must be a sequence of strings, nicht %s' %
                        type(a).__name__)
    wenn isinstance(b, str):
        wirf TypeError('input must be a sequence of strings, nicht %s' %
                        type(b).__name__)
    fuer arg in args:
        wenn nicht isinstance(arg, str):
            wirf TypeError('all arguments must be str, not: %r' % (arg,))

def diff_bytes(dfunc, a, b, fromfile=b'', tofile=b'',
               fromfiledate=b'', tofiledate=b'', n=3, lineterm=b'\n'):
    r"""
    Compare `a` und `b`, two sequences of lines represented als bytes rather
    than str. This is a wrapper fuer `dfunc`, which is typically either
    unified_diff() oder context_diff(). Inputs are losslessly converted to
    strings so that `dfunc` only has to worry about strings, und encoded
    back to bytes on return. This is necessary to compare files with
    unknown oder inconsistent encoding. All other inputs (except `n`) must be
    bytes rather than str.
    """
    def decode(s):
        versuch:
            gib s.decode('ascii', 'surrogateescape')
        ausser AttributeError als err:
            msg = ('all arguments must be bytes, nicht %s (%r)' %
                   (type(s).__name__, s))
            wirf TypeError(msg) von err
    a = list(map(decode, a))
    b = list(map(decode, b))
    fromfile = decode(fromfile)
    tofile = decode(tofile)
    fromfiledate = decode(fromfiledate)
    tofiledate = decode(tofiledate)
    lineterm = decode(lineterm)

    lines = dfunc(a, b, fromfile, tofile, fromfiledate, tofiledate, n, lineterm)
    fuer line in lines:
        liefere line.encode('ascii', 'surrogateescape')

def ndiff(a, b, linejunk=Nichts, charjunk=IS_CHARACTER_JUNK):
    r"""
    Compare `a` und `b` (lists of strings); gib a `Differ`-style delta.

    Optional keyword parameters `linejunk` und `charjunk` are fuer filter
    functions, oder can be Nichts:

    - linejunk: A function that should accept a single string argument und
      gib true iff the string is junk.  The default is Nichts, und is
      recommended; the underlying SequenceMatcher klasse has an adaptive
      notion of "noise" lines.

    - charjunk: A function that accepts a character (string of length
      1), und returns true iff the character is junk. The default is
      the module-level function IS_CHARACTER_JUNK, which filters out
      whitespace characters (a blank oder tab; note: it's a bad idea to
      include newline in this!).

    Tools/scripts/ndiff.py is a command-line front-end to this function.

    Example:

    >>> diff = ndiff('one\ntwo\nthree\n'.splitlines(keepends=Wahr),
    ...              'ore\ntree\nemu\n'.splitlines(keepends=Wahr))
    >>> drucke(''.join(diff), end="")
    - one
    ?  ^
    + ore
    ?  ^
    - two
    - three
    ?  -
    + tree
    + emu
    """
    gib Differ(linejunk, charjunk).compare(a, b)

def _mdiff(fromlines, tolines, context=Nichts, linejunk=Nichts,
           charjunk=IS_CHARACTER_JUNK):
    r"""Returns generator yielding marked up from/to side by side differences.

    Arguments:
    fromlines -- list of text lines to compared to tolines
    tolines -- list of text lines to be compared to fromlines
    context -- number of context lines to display on each side of difference,
               wenn Nichts, all from/to text lines will be generated.
    linejunk -- passed on to ndiff (see ndiff documentation)
    charjunk -- passed on to ndiff (see ndiff documentation)

    This function returns an iterator which returns a tuple:
    (from line tuple, to line tuple, boolean flag)

    from/to line tuple -- (line num, line text)
        line num -- integer oder Nichts (to indicate a context separation)
        line text -- original line text mit following markers inserted:
            '\0+' -- marks start of added text
            '\0-' -- marks start of deleted text
            '\0^' -- marks start of changed text
            '\1' -- marks end of added/deleted/changed text

    boolean flag -- Nichts indicates context separation, Wahr indicates
        either "from" oder "to" line contains a change, otherwise Falsch.

    This function/iterator was originally developed to generate side by side
    file difference fuer making HTML pages (see HtmlDiff klasse fuer example
    usage).

    Note, this function utilizes the ndiff function to generate the side by
    side difference markup.  Optional ndiff arguments may be passed to this
    function und they in turn will be passed to ndiff.
    """
    importiere re

    # regular expression fuer finding intraline change indices
    change_re = re.compile(r'(\++|\-+|\^+)')

    # create the difference iterator to generate the differences
    diff_lines_iterator = ndiff(fromlines,tolines,linejunk,charjunk)

    def _make_line(lines, format_key, side, num_lines=[0,0]):
        """Returns line of text mit user's change markup und line formatting.

        lines -- list of lines von the ndiff generator to produce a line of
                 text from.  When producing the line of text to return, the
                 lines used are removed von this list.
        format_key -- '+' gib first line in list mit "add" markup around
                          the entire line.
                      '-' gib first line in list mit "delete" markup around
                          the entire line.
                      '?' gib first line in list mit add/delete/change
                          intraline markup (indices obtained von second line)
                      Nichts gib first line in list mit no markup
        side -- indice into the num_lines list (0=from,1=to)
        num_lines -- from/to current line number.  This is NOT intended to be a
                     passed parameter.  It is present als a keyword argument to
                     maintain memory of the current line numbers between calls
                     of this function.

        Note, this function is purposefully nicht defined at the module scope so
        that data it needs von its parent function (within whose context it
        is defined) does nicht need to be of module scope.
        """
        num_lines[side] += 1
        # Handle case where no user markup is to be added, just gib line of
        # text mit user's line format to allow fuer usage of the line number.
        wenn format_key is Nichts:
            gib (num_lines[side],lines.pop(0)[2:])
        # Handle case of intraline changes
        wenn format_key == '?':
            text, markers = lines.pop(0), lines.pop(0)
            # find intraline changes (store change type und indices in tuples)
            sub_info = []
            def record_sub_info(match_object,sub_info=sub_info):
                sub_info.append([match_object.group(1)[0],match_object.span()])
                gib match_object.group(1)
            change_re.sub(record_sub_info,markers)
            # process each tuple inserting our special marks that won't be
            # noticed by an xml/html escaper.
            fuer key,(begin,end) in reversed(sub_info):
                text = text[0:begin]+'\0'+key+text[begin:end]+'\1'+text[end:]
            text = text[2:]
        # Handle case of add/delete entire line
        sonst:
            text = lines.pop(0)[2:]
            # wenn line of text is just a newline, insert a space so there is
            # something fuer the user to highlight und see.
            wenn nicht text:
                text = ' '
            # insert marks that won't be noticed by an xml/html escaper.
            text = '\0' + format_key + text + '\1'
        # Return line of text, first allow user's line formatter to do its
        # thing (such als adding the line number) then replace the special
        # marks mit what the user's change markup.
        gib (num_lines[side],text)

    def _line_iterator():
        """Yields from/to lines of text mit a change indication.

        This function is an iterator.  It itself pulls lines von a
        differencing iterator, processes them und yields them.  When it can
        it yields both a "from" und a "to" line, otherwise it will liefere one
        oder the other.  In addition to yielding the lines of from/to text, a
        boolean flag is yielded to indicate wenn the text line(s) have
        differences in them.

        Note, this function is purposefully nicht defined at the module scope so
        that data it needs von its parent function (within whose context it
        is defined) does nicht need to be of module scope.
        """
        lines = []
        num_blanks_pending, num_blanks_to_yield = 0, 0
        waehrend Wahr:
            # Load up next 4 lines so we can look ahead, create strings which
            # are a concatenation of the first character of each of the 4 lines
            # so we can do some very readable comparisons.
            waehrend len(lines) < 4:
                lines.append(next(diff_lines_iterator, 'X'))
            s = ''.join([line[0] fuer line in lines])
            wenn s.startswith('X'):
                # When no more lines, pump out any remaining blank lines so the
                # corresponding add/delete lines get a matching blank line so
                # all line pairs get yielded at the next level.
                num_blanks_to_yield = num_blanks_pending
            sowenn s.startswith('-?+?'):
                # simple intraline change
                liefere _make_line(lines,'?',0), _make_line(lines,'?',1), Wahr
                weiter
            sowenn s.startswith('--++'):
                # in delete block, add block coming: we do NOT want to get
                # caught up on blank lines yet, just process the delete line
                num_blanks_pending -= 1
                liefere _make_line(lines,'-',0), Nichts, Wahr
                weiter
            sowenn s.startswith(('--?+', '--+', '- ')):
                # in delete block und see an intraline change oder unchanged line
                # coming: liefere the delete line und then blanks
                from_line,to_line = _make_line(lines,'-',0), Nichts
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending-1,0
            sowenn s.startswith('-+?'):
                # intraline change
                liefere _make_line(lines,Nichts,0), _make_line(lines,'?',1), Wahr
                weiter
            sowenn s.startswith('-?+'):
                # intraline change
                liefere _make_line(lines,'?',0), _make_line(lines,Nichts,1), Wahr
                weiter
            sowenn s.startswith('-'):
                # delete FROM line
                num_blanks_pending -= 1
                liefere _make_line(lines,'-',0), Nichts, Wahr
                weiter
            sowenn s.startswith('+--'):
                # in add block, delete block coming: we do NOT want to get
                # caught up on blank lines yet, just process the add line
                num_blanks_pending += 1
                liefere Nichts, _make_line(lines,'+',1), Wahr
                weiter
            sowenn s.startswith(('+ ', '+-')):
                # will be leaving an add block: liefere blanks then add line
                from_line, to_line = Nichts, _make_line(lines,'+',1)
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending+1,0
            sowenn s.startswith('+'):
                # inside an add block, liefere the add line
                num_blanks_pending += 1
                liefere Nichts, _make_line(lines,'+',1), Wahr
                weiter
            sowenn s.startswith(' '):
                # unchanged text, liefere it to both sides
                liefere _make_line(lines[:],Nichts,0),_make_line(lines,Nichts,1),Falsch
                weiter
            # Catch up on the blank lines so when we liefere the next from/to
            # pair, they are lined up.
            while(num_blanks_to_yield < 0):
                num_blanks_to_yield += 1
                liefere Nichts,('','\n'),Wahr
            while(num_blanks_to_yield > 0):
                num_blanks_to_yield -= 1
                liefere ('','\n'),Nichts,Wahr
            wenn s.startswith('X'):
                gib
            sonst:
                liefere from_line,to_line,Wahr

    def _line_pair_iterator():
        """Yields from/to lines of text mit a change indication.

        This function is an iterator.  It itself pulls lines von the line
        iterator.  Its difference von that iterator is that this function
        always yields a pair of from/to text lines (with the change
        indication).  If necessary it will collect single from/to lines
        until it has a matching pair from/to pair to yield.

        Note, this function is purposefully nicht defined at the module scope so
        that data it needs von its parent function (within whose context it
        is defined) does nicht need to be of module scope.
        """
        line_iterator = _line_iterator()
        fromlines,tolines=[],[]
        waehrend Wahr:
            # Collecting lines of text until we have a from/to pair
            waehrend (len(fromlines)==0 oder len(tolines)==0):
                versuch:
                    from_line, to_line, found_diff = next(line_iterator)
                ausser StopIteration:
                    gib
                wenn from_line is nicht Nichts:
                    fromlines.append((from_line,found_diff))
                wenn to_line is nicht Nichts:
                    tolines.append((to_line,found_diff))
            # Once we have a pair, remove them von the collection und liefere it
            from_line, fromDiff = fromlines.pop(0)
            to_line, to_diff = tolines.pop(0)
            liefere (from_line,to_line,fromDiff oder to_diff)

    # Handle case where user does nicht want context differencing, just liefere
    # them up without doing anything sonst mit them.
    line_pair_iterator = _line_pair_iterator()
    wenn context is Nichts:
        liefere von line_pair_iterator
    # Handle case where user wants context differencing.  We must do some
    # storage of lines until we know fuer sure that they are to be yielded.
    sonst:
        context += 1
        lines_to_write = 0
        waehrend Wahr:
            # Store lines up until we find a difference, note use of a
            # circular queue because we only need to keep around what
            # we need fuer context.
            index, contextLines = 0, [Nichts]*(context)
            found_diff = Falsch
            while(found_diff is Falsch):
                versuch:
                    from_line, to_line, found_diff = next(line_pair_iterator)
                ausser StopIteration:
                    gib
                i = index % context
                contextLines[i] = (from_line, to_line, found_diff)
                index += 1
            # Yield lines that we have collected so far, but first liefere
            # the user's separator.
            wenn index > context:
                liefere Nichts, Nichts, Nichts
                lines_to_write = context
            sonst:
                lines_to_write = index
                index = 0
            while(lines_to_write):
                i = index % context
                index += 1
                liefere contextLines[i]
                lines_to_write -= 1
            # Now liefere the context lines after the change
            lines_to_write = context-1
            versuch:
                while(lines_to_write):
                    from_line, to_line, found_diff = next(line_pair_iterator)
                    # If another change within the context, extend the context
                    wenn found_diff:
                        lines_to_write = context-1
                    sonst:
                        lines_to_write -= 1
                    liefere from_line, to_line, found_diff
            ausser StopIteration:
                # Catch exception von next() und gib normally
                gib


_file_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="%(charset)s">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Diff comparison</title>
    <style>%(styles)s
    </style>
</head>

<body>
    %(table)s%(legend)s
</body>

</html>"""

_styles = """
        :root {color-scheme: light dark}
        table.diff {
            font-family: Menlo, Consolas, Monaco, Liberation Mono, Lucida Console, monospace;
            border: medium;
        }
        .diff_header {
            background-color: #e0e0e0;
            font-weight: bold;
        }
        td.diff_header {
            text-align: right;
            padding: 0 8px;
        }
        .diff_next {
            background-color: #c0c0c0;
            padding: 4px 0;
        }
        .diff_add {background-color:palegreen}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
        table.diff[summary="Legends"] {
            margin-top: 20px;
            border: 1px solid #ccc;
        }
        table.diff[summary="Legends"] th {
            background-color: #e0e0e0;
            padding: 4px 8px;
        }
        table.diff[summary="Legends"] td {
            padding: 4px 8px;
        }

        @media (prefers-color-scheme: dark) {
            .diff_header {background-color:#666}
            .diff_next {background-color:#393939}
            .diff_add {background-color:darkgreen}
            .diff_chg {background-color:#847415}
            .diff_sub {background-color:darkred}
            table.diff[summary="Legends"] {border-color:#555}
            table.diff[summary="Legends"] th{background-color:#666}
        }"""

_table_template = """
    <table class="diff" id="difflib_chg_%(prefix)s_top"
           cellspacing="0" cellpadding="0" rules="groups" >
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        %(header_row)s
        <tbody>
%(data_rows)s        </tbody>
    </table>"""

_legend = """
    <table class="diff" summary="Legends">
        <tr> <th colspan="2"> Legends </th> </tr>
        <tr> <td> <table border="" summary="Colors">
                      <tr><th> Colors </th> </tr>
                      <tr><td class="diff_add">&nbsp;Added&nbsp;</td></tr>
                      <tr><td class="diff_chg">Changed</td> </tr>
                      <tr><td class="diff_sub">Deleted</td> </tr>
                  </table></td>
             <td> <table border="" summary="Links">
                      <tr><th colspan="2"> Links </th> </tr>
                      <tr><td>(f)irst change</td> </tr>
                      <tr><td>(n)ext change</td> </tr>
                      <tr><td>(t)op</td> </tr>
                  </table></td> </tr>
    </table>"""

klasse HtmlDiff(object):
    """For producing HTML side by side comparison mit change highlights.

    This klasse can be used to create an HTML table (or a complete HTML file
    containing the table) showing a side by side, line by line comparison
    of text mit inter-line und intra-line change highlights.  The table can
    be generated in either full oder contextual difference mode.

    The following methods are provided fuer HTML generation:

    make_table -- generates HTML fuer a single side by side table
    make_file -- generates complete HTML file mit a single side by side table

    See Doc/includes/diff.py fuer an example usage of this class.
    """

    _file_template = _file_template
    _styles = _styles
    _table_template = _table_template
    _legend = _legend
    _default_prefix = 0

    def __init__(self,tabsize=8,wrapcolumn=Nichts,linejunk=Nichts,
                 charjunk=IS_CHARACTER_JUNK):
        """HtmlDiff instance initializer

        Arguments:
        tabsize -- tab stop spacing, defaults to 8.
        wrapcolumn -- column number where lines are broken und wrapped,
            defaults to Nichts where lines are nicht wrapped.
        linejunk,charjunk -- keyword arguments passed into ndiff() (used by
            HtmlDiff() to generate the side by side HTML differences).  See
            ndiff() documentation fuer argument default values und descriptions.
        """
        self._tabsize = tabsize
        self._wrapcolumn = wrapcolumn
        self._linejunk = linejunk
        self._charjunk = charjunk

    def make_file(self, fromlines, tolines, fromdesc='', todesc='',
                  context=Falsch, numlines=5, *, charset='utf-8'):
        """Returns HTML file of side by side comparison mit change highlights

        Arguments:
        fromlines -- list of "from" lines
        tolines -- list of "to" lines
        fromdesc -- "from" file column header string
        todesc -- "to" file column header string
        context -- set to Wahr fuer contextual differences (defaults to Falsch
            which shows full differences).
        numlines -- number of context lines.  When context is set Wahr,
            controls number of lines displayed before und after the change.
            When context is Falsch, controls the number of lines to place
            the "next" link anchors before the next change (so click of
            "next" link jumps to just before the change).
        charset -- charset of the HTML document
        """

        gib (self._file_template % dict(
            styles=self._styles,
            legend=self._legend,
            table=self.make_table(fromlines, tolines, fromdesc, todesc,
                                  context=context, numlines=numlines),
            charset=charset
        )).encode(charset, 'xmlcharrefreplace').decode(charset)

    def _tab_newline_replace(self,fromlines,tolines):
        """Returns from/to line lists mit tabs expanded und newlines removed.

        Instead of tab characters being replaced by the number of spaces
        needed to fill in to the next tab stop, this function will fill
        the space mit tab characters.  This is done so that the difference
        algorithms can identify changes in a file when tabs are replaced by
        spaces und vice versa.  At the end of the HTML generation, the tab
        characters will be replaced mit a nonbreakable space.
        """
        def expand_tabs(line):
            # hide real spaces
            line = line.replace(' ','\0')
            # expand tabs into spaces
            line = line.expandtabs(self._tabsize)
            # replace spaces von expanded tabs back into tab characters
            # (we'll replace them mit markup after we do differencing)
            line = line.replace(' ','\t')
            gib line.replace('\0',' ').rstrip('\n')
        fromlines = [expand_tabs(line) fuer line in fromlines]
        tolines = [expand_tabs(line) fuer line in tolines]
        gib fromlines,tolines

    def _split_line(self,data_list,line_num,text):
        """Builds list of text lines by splitting text lines at wrap point

        This function will determine wenn the input text line needs to be
        wrapped (split) into separate lines.  If so, the first wrap point
        will be determined und the first line appended to the output
        text line list.  This function is used recursively to handle
        the second part of the split line to further split it.
        """
        # wenn blank line oder context separator, just add it to the output list
        wenn nicht line_num:
            data_list.append((line_num,text))
            gib

        # wenn line text doesn't need wrapping, just add it to the output list
        size = len(text)
        max = self._wrapcolumn
        wenn (size <= max) oder ((size -(text.count('\0')*3)) <= max):
            data_list.append((line_num,text))
            gib

        # scan text looking fuer the wrap point, keeping track wenn the wrap
        # point is inside markers
        i = 0
        n = 0
        mark = ''
        waehrend n < max und i < size:
            wenn text[i] == '\0':
                i += 1
                mark = text[i]
                i += 1
            sowenn text[i] == '\1':
                i += 1
                mark = ''
            sonst:
                i += 1
                n += 1

        # wrap point is inside text, breche it up into separate lines
        line1 = text[:i]
        line2 = text[i:]

        # wenn wrap point is inside markers, place end marker at end of first
        # line und start marker at beginning of second line because each
        # line will have its own table tag markup around it.
        wenn mark:
            line1 = line1 + '\1'
            line2 = '\0' + mark + line2

        # tack on first line onto the output list
        data_list.append((line_num,line1))

        # use this routine again to wrap the remaining text
        self._split_line(data_list,'>',line2)

    def _line_wrapper(self,diffs):
        """Returns iterator that splits (wraps) mdiff text lines"""

        # pull from/to data und flags von mdiff iterator
        fuer fromdata,todata,flag in diffs:
            # check fuer context separators und pass them through
            wenn flag is Nichts:
                liefere fromdata,todata,flag
                weiter
            (fromline,fromtext),(toline,totext) = fromdata,todata
            # fuer each from/to line split it at the wrap column to form
            # list of text lines.
            fromlist,tolist = [],[]
            self._split_line(fromlist,fromline,fromtext)
            self._split_line(tolist,toline,totext)
            # liefere from/to line in pairs inserting blank lines as
            # necessary when one side has more wrapped lines
            waehrend fromlist oder tolist:
                wenn fromlist:
                    fromdata = fromlist.pop(0)
                sonst:
                    fromdata = ('',' ')
                wenn tolist:
                    todata = tolist.pop(0)
                sonst:
                    todata = ('',' ')
                liefere fromdata,todata,flag

    def _collect_lines(self,diffs):
        """Collects mdiff output into separate lists

        Before storing the mdiff from/to data into a list, it is converted
        into a single line of text mit HTML markup.
        """

        fromlist,tolist,flaglist = [],[],[]
        # pull from/to data und flags von mdiff style iterator
        fuer fromdata,todata,flag in diffs:
            versuch:
                # store HTML markup of the lines into the lists
                fromlist.append(self._format_line(0,flag,*fromdata))
                tolist.append(self._format_line(1,flag,*todata))
            ausser TypeError:
                # exceptions occur fuer lines where context separators go
                fromlist.append(Nichts)
                tolist.append(Nichts)
            flaglist.append(flag)
        gib fromlist,tolist,flaglist

    def _format_line(self,side,flag,linenum,text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 oder 1 indicating "from" oder "to" text
        flag -- indicates wenn difference on line
        linenum -- line number (used fuer line number column)
        text -- line text to be marked up
        """
        versuch:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side],linenum)
        ausser TypeError:
            # handle blank lines where linenum is '>' oder ''
            id = ''
        # replace those things that would get confused mit HTML symbols
        text=text.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")

        # make space non-breakable so they don't get compressed oder line wrapped
        text = text.replace(' ','&nbsp;').rstrip()

        gib '<td class="diff_header"%s>%s</td><td nowrap="nowrap">%s</td>' \
               % (id,linenum,text)

    def _make_prefix(self):
        """Create unique anchor prefixes"""

        # Generate a unique anchor prefix so multiple tables
        # can exist on the same HTML page without conflicts.
        fromprefix = "from%d_" % HtmlDiff._default_prefix
        toprefix = "to%d_" % HtmlDiff._default_prefix
        HtmlDiff._default_prefix += 1
        # store prefixes so line format method has access
        self._prefix = [fromprefix,toprefix]

    def _convert_flags(self,fromlist,tolist,flaglist,context,numlines):
        """Makes list of "next" links"""

        # all anchor names will be generated using the unique "to" prefix
        toprefix = self._prefix[1]

        # process change flags, generating middle column of next anchors/links
        next_id = ['']*len(flaglist)
        next_href = ['']*len(flaglist)
        num_chg, in_change = 0, Falsch
        last = 0
        fuer i,flag in enumerate(flaglist):
            wenn flag:
                wenn nicht in_change:
                    in_change = Wahr
                    last = i
                    # at the beginning of a change, drop an anchor a few lines
                    # (the context lines) before the change fuer the previous
                    # link
                    i = max([0,i-numlines])
                    next_id[i] = ' id="difflib_chg_%s_%d"' % (toprefix,num_chg)
                    # at the beginning of a change, drop a link to the next
                    # change
                    num_chg += 1
                    next_href[last] = '<a href="#difflib_chg_%s_%d">n</a>' % (
                         toprefix,num_chg)
            sonst:
                in_change = Falsch
        # check fuer cases where there is no content to avoid exceptions
        wenn nicht flaglist:
            flaglist = [Falsch]
            next_id = ['']
            next_href = ['']
            last = 0
            wenn context:
                fromlist = ['<td></td><td>&nbsp;No Differences Found&nbsp;</td>']
                tolist = fromlist
            sonst:
                fromlist = tolist = ['<td></td><td>&nbsp;Empty File&nbsp;</td>']
        # wenn nicht a change on first line, drop a link
        wenn nicht flaglist[0]:
            next_href[0] = '<a href="#difflib_chg_%s_0">f</a>' % toprefix
        # redo the last link to link to the top
        next_href[last] = '<a href="#difflib_chg_%s_top">t</a>' % (toprefix)

        gib fromlist,tolist,flaglist,next_href,next_id

    def make_table(self,fromlines,tolines,fromdesc='',todesc='',context=Falsch,
                   numlines=5):
        """Returns HTML table of side by side comparison mit change highlights

        Arguments:
        fromlines -- list of "from" lines
        tolines -- list of "to" lines
        fromdesc -- "from" file column header string
        todesc -- "to" file column header string
        context -- set to Wahr fuer contextual differences (defaults to Falsch
            which shows full differences).
        numlines -- number of context lines.  When context is set Wahr,
            controls number of lines displayed before und after the change.
            When context is Falsch, controls the number of lines to place
            the "next" link anchors before the next change (so click of
            "next" link jumps to just before the change).
        """

        # make unique anchor prefixes so that multiple tables may exist
        # on the same page without conflict.
        self._make_prefix()

        # change tabs to spaces before it gets more difficult after we insert
        # markup
        fromlines,tolines = self._tab_newline_replace(fromlines,tolines)

        # create diffs iterator which generates side by side from/to data
        wenn context:
            context_lines = numlines
        sonst:
            context_lines = Nichts
        diffs = _mdiff(fromlines,tolines,context_lines,linejunk=self._linejunk,
                      charjunk=self._charjunk)

        # set up iterator to wrap lines that exceed desired width
        wenn self._wrapcolumn:
            diffs = self._line_wrapper(diffs)

        # collect up from/to lines und flags into lists (also format the lines)
        fromlist,tolist,flaglist = self._collect_lines(diffs)

        # process change flags, generating middle column of next anchors/links
        fromlist,tolist,flaglist,next_href,next_id = self._convert_flags(
            fromlist,tolist,flaglist,context,numlines)

        s = []
        fmt = '            <tr><td class="diff_next"%s>%s</td>%s' + \
              '<td class="diff_next">%s</td>%s</tr>\n'
        fuer i in range(len(flaglist)):
            wenn flaglist[i] is Nichts:
                # mdiff yields Nichts on separator lines skip the bogus ones
                # generated fuer the first line
                wenn i > 0:
                    s.append('        </tbody>        \n        <tbody>\n')
            sonst:
                s.append( fmt % (next_id[i],next_href[i],fromlist[i],
                                           next_href[i],tolist[i]))
        wenn fromdesc oder todesc:
            header_row = '<thead><tr>%s%s%s%s</tr></thead>' % (
                '<th class="diff_next"><br /></th>',
                '<th colspan="2" class="diff_header">%s</th>' % fromdesc,
                '<th class="diff_next"><br /></th>',
                '<th colspan="2" class="diff_header">%s</th>' % todesc)
        sonst:
            header_row = ''

        table = self._table_template % dict(
            data_rows=''.join(s),
            header_row=header_row,
            prefix=self._prefix[1])

        gib table.replace('\0+','<span class="diff_add">'). \
                     replace('\0-','<span class="diff_sub">'). \
                     replace('\0^','<span class="diff_chg">'). \
                     replace('\1','</span>'). \
                     replace('\t','&nbsp;')


def restore(delta, which):
    r"""
    Generate one of the two sequences that generated a delta.

    Given a `delta` produced by `Differ.compare()` oder `ndiff()`, extract
    lines originating von file 1 oder 2 (parameter `which`), stripping off line
    prefixes.

    Examples:

    >>> diff = ndiff('one\ntwo\nthree\n'.splitlines(keepends=Wahr),
    ...              'ore\ntree\nemu\n'.splitlines(keepends=Wahr))
    >>> diff = list(diff)
    >>> drucke(''.join(restore(diff, 1)), end="")
    one
    two
    three
    >>> drucke(''.join(restore(diff, 2)), end="")
    ore
    tree
    emu
    """
    versuch:
        tag = {1: "- ", 2: "+ "}[int(which)]
    ausser KeyError:
        wirf ValueError('unknown delta choice (must be 1 oder 2): %r'
                           % which) von Nichts
    prefixes = ("  ", tag)
    fuer line in delta:
        wenn line[:2] in prefixes:
            liefere line[2:]
