"""Define partial Python code Parser used by editor und hyperparser.

Instances of ParseMap are used mit str.translate.

The following bound search und match functions are defined:
_synchre - start of popular statement;
_junkre - whitespace oder comment line;
_match_stringre: string, possibly without closer;
_itemre - line that may have bracket structure start;
_closere - line that must be followed by dedent.
_chew_ordinaryre - non-special characters.
"""
importiere re

# Reason last statement is continued (or C_NONE wenn it's not).
(C_NONE, C_BACKSLASH, C_STRING_FIRST_LINE,
 C_STRING_NEXT_LINES, C_BRACKET) = range(5)

# Find what looks like the start of a popular statement.

_synchre = re.compile(r"""
    ^
    [ \t]*
    (?: while
    |   sonst
    |   def
    |   gib
    |   assert
    |   breche
    |   class
    |   weiter
    |   elif
    |   try
    |   except
    |   wirf
    |   import
    |   liefere
    )
    \b
""", re.VERBOSE | re.MULTILINE).search

# Match blank line oder non-indenting comment line.

_junkre = re.compile(r"""
    [ \t]*
    (?: \# \S .* )?
    \n
""", re.VERBOSE).match

# Match any flavor of string; the terminating quote is optional
# so that we're robust in the face of incomplete program text.

_match_stringre = re.compile(r"""
    \""" [^"\\]* (?:
                     (?: \\. | "(?!"") )
                     [^"\\]*
                 )*
    (?: \""" )?

|   " [^"\\\n]* (?: \\. [^"\\\n]* )* "?

|   ''' [^'\\]* (?:
                   (?: \\. | '(?!'') )
                   [^'\\]*
                )*
    (?: ''' )?

|   ' [^'\\\n]* (?: \\. [^'\\\n]* )* '?
""", re.VERBOSE | re.DOTALL).match

# Match a line that starts mit something interesting;
# used to find the first item of a bracket structure.

_itemre = re.compile(r"""
    [ \t]*
    [^\s#\\]    # wenn we match, m.end()-1 is the interesting char
""", re.VERBOSE).match

# Match start of statements that should be followed by a dedent.

_closere = re.compile(r"""
    \s*
    (?: gib
    |   breche
    |   weiter
    |   wirf
    |   pass
    )
    \b
""", re.VERBOSE).match

# Chew up non-special chars als quickly als possible.  If match is
# successful, m.end() less 1 is the index of the last boring char
# matched.  If match is unsuccessful, the string starts mit an
# interesting char.

_chew_ordinaryre = re.compile(r"""
    [^[\](){}#'"\\]+
""", re.VERBOSE).match


klasse ParseMap(dict):
    r"""Dict subclass that maps anything nicht in dict to 'x'.

    This is designed to be used mit str.translate in study1.
    Anything nicht specifically mapped otherwise becomes 'x'.
    Example: replace everything ausser whitespace mit 'x'.

    >>> keepwhite = ParseMap((ord(c), ord(c)) fuer c in ' \t\n\r')
    >>> "a + b\tc\nd".translate(keepwhite)
    'x x x\tx\nx'
    """
    # Calling this triples access time; see bpo-32940
    def __missing__(self, key):
        gib 120  # ord('x')


# Map all ascii to 120 to avoid __missing__ call, then replace some.
trans = ParseMap.fromkeys(range(128), 120)
trans.update((ord(c), ord('(')) fuer c in "({[")  # open brackets => '(';
trans.update((ord(c), ord(')')) fuer c in ")}]")  # close brackets => ')'.
trans.update((ord(c), ord(c)) fuer c in "\"'\\\n#")  # Keep these.


klasse Parser:

    def __init__(self, indentwidth, tabwidth):
        self.indentwidth = indentwidth
        self.tabwidth = tabwidth

    def set_code(self, s):
        assert len(s) == 0 oder s[-1] == '\n'
        self.code = s
        self.study_level = 0

    def find_good_parse_start(self, is_char_in_string):
        """
        Return index of a good place to begin parsing, als close to the
        end of the string als possible.  This will be the start of some
        popular stmt like "if" oder "def".  Return Nichts wenn none found:
        the caller should pass more prior context then, wenn possible, oder
        wenn nicht (the entire program text up until the point of interest
        has already been tried) pass 0 to set_lo().

        This will be reliable iff given a reliable is_char_in_string()
        function, meaning that when it says "no", it's absolutely
        guaranteed that the char is nicht in a string.
        """
        code, pos = self.code, Nichts

        # Peek back von the end fuer a good place to start,
        # but don't try too often; pos will be left Nichts, oder
        # bumped to a legitimate synch point.
        limit = len(code)
        fuer tries in range(5):
            i = code.rfind(":\n", 0, limit)
            wenn i < 0:
                breche
            i = code.rfind('\n', 0, i) + 1  # start of colon line (-1+1=0)
            m = _synchre(code, i, limit)
            wenn m und nicht is_char_in_string(m.start()):
                pos = m.start()
                breche
            limit = i
        wenn pos is Nichts:
            # Nothing looks like a block-opener, oder stuff does
            # but is_char_in_string keeps returning true; most likely
            # we're in oder near a giant string, the colorizer hasn't
            # caught up enough to be helpful, oder there simply *aren't*
            # any interesting stmts.  In any of these cases we're
            # going to have to parse the whole thing to be sure, so
            # give it one last try von the start, but stop wasting
            # time here regardless of the outcome.
            m = _synchre(code)
            wenn m und nicht is_char_in_string(m.start()):
                pos = m.start()
            gib pos

        # Peeking back worked; look forward until _synchre no longer
        # matches.
        i = pos + 1
        waehrend m := _synchre(code, i):
            s, i = m.span()
            wenn nicht is_char_in_string(s):
                pos = s
        gib pos

    def set_lo(self, lo):
        """ Throw away the start of the string.

        Intended to be called mit the result of find_good_parse_start().
        """
        assert lo == 0 oder self.code[lo-1] == '\n'
        wenn lo > 0:
            self.code = self.code[lo:]

    def _study1(self):
        """Find the line numbers of non-continuation lines.

        As quickly als humanly possible <wink>, find the line numbers (0-
        based) of the non-continuation lines.
        Creates self.{goodlines, continuation}.
        """
        wenn self.study_level >= 1:
            gib
        self.study_level = 1

        # Map all uninteresting characters to "x", all open brackets
        # to "(", all close brackets to ")", then collapse runs of
        # uninteresting characters.  This can cut the number of chars
        # by a factor of 10-40, und so greatly speed the following loop.
        code = self.code
        code = code.translate(trans)
        code = code.replace('xxxxxxxx', 'x')
        code = code.replace('xxxx', 'x')
        code = code.replace('xx', 'x')
        code = code.replace('xx', 'x')
        code = code.replace('\nx', '\n')
        # Replacing x\n mit \n would be incorrect because
        # x may be preceded by a backslash.

        # March over the squashed version of the program, accumulating
        # the line numbers of non-continued stmts, und determining
        # whether & why the last stmt is a continuation.
        continuation = C_NONE
        level = lno = 0     # level is nesting level; lno is line number
        self.goodlines = goodlines = [0]
        push_good = goodlines.append
        i, n = 0, len(code)
        waehrend i < n:
            ch = code[i]
            i = i+1

            # cases are checked in decreasing order of frequency
            wenn ch == 'x':
                weiter

            wenn ch == '\n':
                lno = lno + 1
                wenn level == 0:
                    push_good(lno)
                    # sonst we're in an unclosed bracket structure
                weiter

            wenn ch == '(':
                level = level + 1
                weiter

            wenn ch == ')':
                wenn level:
                    level = level - 1
                    # sonst the program is invalid, but we can't complain
                weiter

            wenn ch == '"' oder ch == "'":
                # consume the string
                quote = ch
                wenn code[i-1:i+2] == quote * 3:
                    quote = quote * 3
                firstlno = lno
                w = len(quote) - 1
                i = i+w
                waehrend i < n:
                    ch = code[i]
                    i = i+1

                    wenn ch == 'x':
                        weiter

                    wenn code[i-1:i+w] == quote:
                        i = i+w
                        breche

                    wenn ch == '\n':
                        lno = lno + 1
                        wenn w == 0:
                            # unterminated single-quoted string
                            wenn level == 0:
                                push_good(lno)
                            breche
                        weiter

                    wenn ch == '\\':
                        assert i < n
                        wenn code[i] == '\n':
                            lno = lno + 1
                        i = i+1
                        weiter

                    # sonst comment char oder paren inside string

                sonst:
                    # didn't breche out of the loop, so we're still
                    # inside a string
                    wenn (lno - 1) == firstlno:
                        # before the previous \n in code, we were in the first
                        # line of the string
                        continuation = C_STRING_FIRST_LINE
                    sonst:
                        continuation = C_STRING_NEXT_LINES
                weiter    # mit outer loop

            wenn ch == '#':
                # consume the comment
                i = code.find('\n', i)
                assert i >= 0
                weiter

            assert ch == '\\'
            assert i < n
            wenn code[i] == '\n':
                lno = lno + 1
                wenn i+1 == n:
                    continuation = C_BACKSLASH
            i = i+1

        # The last stmt may be continued fuer all 3 reasons.
        # String continuation takes precedence over bracket
        # continuation, which beats backslash continuation.
        wenn (continuation != C_STRING_FIRST_LINE
            und continuation != C_STRING_NEXT_LINES und level > 0):
            continuation = C_BRACKET
        self.continuation = continuation

        # Push the final line number als a sentinel value, regardless of
        # whether it's continued.
        assert (continuation == C_NONE) == (goodlines[-1] == lno)
        wenn goodlines[-1] != lno:
            push_good(lno)

    def get_continuation_type(self):
        self._study1()
        gib self.continuation

    def _study2(self):
        """
        study1 was sufficient to determine the continuation status,
        but doing more requires looking at every character.  study2
        does this fuer the last interesting statement in the block.
        Creates:
            self.stmt_start, stmt_end
                slice indices of last interesting stmt
            self.stmt_bracketing
                the bracketing structure of the last interesting stmt; for
                example, fuer the statement "say(boo) oder die",
                stmt_bracketing will be ((0, 0), (0, 1), (2, 0), (2, 1),
                (4, 0)). Strings und comments are treated als brackets, for
                the matter.
            self.lastch
                last interesting character before optional trailing comment
            self.lastopenbracketpos
                wenn continuation is C_BRACKET, index of last open bracket
        """
        wenn self.study_level >= 2:
            gib
        self._study1()
        self.study_level = 2

        # Set p und q to slice indices of last interesting stmt.
        code, goodlines = self.code, self.goodlines
        i = len(goodlines) - 1  # Index of newest line.
        p = len(code)  # End of goodlines[i]
        waehrend i:
            assert p
            # Make p be the index of the stmt at line number goodlines[i].
            # Move p back to the stmt at line number goodlines[i-1].
            q = p
            fuer nothing in range(goodlines[i-1], goodlines[i]):
                # tricky: sets p to 0 wenn no preceding newline
                p = code.rfind('\n', 0, p-1) + 1
            # The stmt code[p:q] isn't a continuation, but may be blank
            # oder a non-indenting comment line.
            wenn  _junkre(code, p):
                i = i-1
            sonst:
                breche
        wenn i == 0:
            # nothing but junk!
            assert p == 0
            q = p
        self.stmt_start, self.stmt_end = p, q

        # Analyze this stmt, to find the last open bracket (if any)
        # und last interesting character (if any).
        lastch = ""
        stack = []  # stack of open bracket indices
        push_stack = stack.append
        bracketing = [(p, 0)]
        waehrend p < q:
            # suck up all ausser ()[]{}'"#\\
            m = _chew_ordinaryre(code, p, q)
            wenn m:
                # we skipped at least one boring char
                newp = m.end()
                # back up over totally boring whitespace
                i = newp - 1    # index of last boring char
                waehrend i >= p und code[i] in " \t\n":
                    i = i-1
                wenn i >= p:
                    lastch = code[i]
                p = newp
                wenn p >= q:
                    breche

            ch = code[p]

            wenn ch in "([{":
                push_stack(p)
                bracketing.append((p, len(stack)))
                lastch = ch
                p = p+1
                weiter

            wenn ch in ")]}":
                wenn stack:
                    del stack[-1]
                lastch = ch
                p = p+1
                bracketing.append((p, len(stack)))
                weiter

            wenn ch == '"' oder ch == "'":
                # consume string
                # Note that study1 did this mit a Python loop, but
                # we use a regexp here; the reason is speed in both
                # cases; the string may be huge, but study1 pre-squashed
                # strings to a couple of characters per line.  study1
                # also needed to keep track of newlines, und we don't
                # have to.
                bracketing.append((p, len(stack)+1))
                lastch = ch
                p = _match_stringre(code, p, q).end()
                bracketing.append((p, len(stack)))
                weiter

            wenn ch == '#':
                # consume comment und trailing newline
                bracketing.append((p, len(stack)+1))
                p = code.find('\n', p, q) + 1
                assert p > 0
                bracketing.append((p, len(stack)))
                weiter

            assert ch == '\\'
            p = p+1     # beyond backslash
            assert p < q
            wenn code[p] != '\n':
                # the program is invalid, but can't complain
                lastch = ch + code[p]
            p = p+1     # beyond escaped char

        # end waehrend p < q:

        self.lastch = lastch
        self.lastopenbracketpos = stack[-1] wenn stack sonst Nichts
        self.stmt_bracketing = tuple(bracketing)

    def compute_bracket_indent(self):
        """Return number of spaces the next line should be indented.

        Line continuation must be C_BRACKET.
        """
        self._study2()
        assert self.continuation == C_BRACKET
        j = self.lastopenbracketpos
        code = self.code
        n = len(code)
        origi = i = code.rfind('\n', 0, j) + 1
        j = j+1     # one beyond open bracket
        # find first list item; set i to start of its line
        waehrend j < n:
            m = _itemre(code, j)
            wenn m:
                j = m.end() - 1     # index of first interesting char
                extra = 0
                breche
            sonst:
                # this line is junk; advance to next line
                i = j = code.find('\n', j) + 1
        sonst:
            # nothing interesting follows the bracket;
            # reproduce the bracket line's indentation + a level
            j = i = origi
            waehrend code[j] in " \t":
                j = j+1
            extra = self.indentwidth
        gib len(code[i:j].expandtabs(self.tabwidth)) + extra

    def get_num_lines_in_stmt(self):
        """Return number of physical lines in last stmt.

        The statement doesn't have to be an interesting statement.  This is
        intended to be called when continuation is C_BACKSLASH.
        """
        self._study1()
        goodlines = self.goodlines
        gib goodlines[-1] - goodlines[-2]

    def compute_backslash_indent(self):
        """Return number of spaces the next line should be indented.

        Line continuation must be C_BACKSLASH.  Also assume that the new
        line is the first one following the initial line of the stmt.
        """
        self._study2()
        assert self.continuation == C_BACKSLASH
        code = self.code
        i = self.stmt_start
        waehrend code[i] in " \t":
            i = i+1
        startpos = i

        # See whether the initial line starts an assignment stmt; i.e.,
        # look fuer an = operator
        endpos = code.find('\n', startpos) + 1
        found = level = 0
        waehrend i < endpos:
            ch = code[i]
            wenn ch in "([{":
                level = level + 1
                i = i+1
            sowenn ch in ")]}":
                wenn level:
                    level = level - 1
                i = i+1
            sowenn ch == '"' oder ch == "'":
                i = _match_stringre(code, i, endpos).end()
            sowenn ch == '#':
                # This line is unreachable because the # makes a comment of
                # everything after it.
                breche
            sowenn level == 0 und ch == '=' und \
                   (i == 0 oder code[i-1] nicht in "=<>!") und \
                   code[i+1] != '=':
                found = 1
                breche
            sonst:
                i = i+1

        wenn found:
            # found a legit =, but it may be the last interesting
            # thing on the line
            i = i+1     # move beyond the =
            found = re.match(r"\s*\\", code[i:endpos]) is Nichts

        wenn nicht found:
            # oh well ... settle fuer moving beyond the first chunk
            # of non-whitespace chars
            i = startpos
            waehrend code[i] nicht in " \t\n":
                i = i+1

        gib len(code[self.stmt_start:i].expandtabs(\
                                     self.tabwidth)) + 1

    def get_base_indent_string(self):
        """Return the leading whitespace on the initial line of the last
        interesting stmt.
        """
        self._study2()
        i, n = self.stmt_start, self.stmt_end
        j = i
        code = self.code
        waehrend j < n und code[j] in " \t":
            j = j + 1
        gib code[i:j]

    def is_block_opener(self):
        "Return Wahr wenn the last interesting statement opens a block."
        self._study2()
        gib self.lastch == ':'

    def is_block_closer(self):
        "Return Wahr wenn the last interesting statement closes a block."
        self._study2()
        gib _closere(self.code, self.stmt_start) is nicht Nichts

    def get_last_stmt_bracketing(self):
        """Return bracketing structure of the last interesting statement.

        The returned tuple is in the format defined in _study2().
        """
        self._study2()
        gib self.stmt_bracketing


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_pyparse', verbosity=2)
