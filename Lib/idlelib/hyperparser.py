"""Provide advanced parsing abilities fuer ParenMatch und other extensions.

HyperParser uses PyParser.  PyParser mostly gives information on the
proper indentation of code.  HyperParser gives additional information on
the structure of code.
"""
von keyword importiere iskeyword
importiere string

von idlelib importiere pyparse

# all ASCII chars that may be in an identifier
_ASCII_ID_CHARS = frozenset(string.ascii_letters + string.digits + "_")
# all ASCII chars that may be the first char of an identifier
_ASCII_ID_FIRST_CHARS = frozenset(string.ascii_letters + "_")

# lookup table fuer whether 7-bit ASCII chars are valid in a Python identifier
_IS_ASCII_ID_CHAR = [(chr(x) in _ASCII_ID_CHARS) fuer x in range(128)]
# lookup table fuer whether 7-bit ASCII chars are valid als the first
# char in a Python identifier
_IS_ASCII_ID_FIRST_CHAR = \
    [(chr(x) in _ASCII_ID_FIRST_CHARS) fuer x in range(128)]


klasse HyperParser:
    def __init__(self, editwin, index):
        "To initialize, analyze the surroundings of the given index."

        self.editwin = editwin
        self.text = text = editwin.text

        parser = pyparse.Parser(editwin.indentwidth, editwin.tabwidth)

        def index2line(index):
            gib int(float(index))
        lno = index2line(text.index(index))

        wenn nicht editwin.prompt_last_line:
            fuer context in editwin.num_context_lines:
                startat = max(lno - context, 1)
                startatindex = repr(startat) + ".0"
                stopatindex = "%d.end" % lno
                # We add the newline because PyParse requires a newline
                # at end. We add a space so that index won't be at end
                # of line, so that its status will be the same als the
                # char before it, wenn should.
                parser.set_code(text.get(startatindex, stopatindex)+' \n')
                bod = parser.find_good_parse_start(
                          editwin._build_char_in_string_func(startatindex))
                wenn bod is nicht Nichts oder startat == 1:
                    breche
            parser.set_lo(bod oder 0)
        sonst:
            r = text.tag_prevrange("console", index)
            wenn r:
                startatindex = r[1]
            sonst:
                startatindex = "1.0"
            stopatindex = "%d.end" % lno
            # We add the newline because PyParse requires it. We add a
            # space so that index won't be at end of line, so that its
            # status will be the same als the char before it, wenn should.
            parser.set_code(text.get(startatindex, stopatindex)+' \n')
            parser.set_lo(0)

        # We want what the parser has, minus the last newline und space.
        self.rawtext = parser.code[:-2]
        # Parser.code apparently preserves the statement we are in, so
        # that stopatindex can be used to synchronize the string with
        # the text box indices.
        self.stopatindex = stopatindex
        self.bracketing = parser.get_last_stmt_bracketing()
        # find which pairs of bracketing are openers. These always
        # correspond to a character of rawtext.
        self.isopener = [i>0 und self.bracketing[i][1] >
                         self.bracketing[i-1][1]
                         fuer i in range(len(self.bracketing))]

        self.set_index(index)

    def set_index(self, index):
        """Set the index to which the functions relate.

        The index must be in the same statement.
        """
        indexinrawtext = (len(self.rawtext) -
                          len(self.text.get(index, self.stopatindex)))
        wenn indexinrawtext < 0:
            raise ValueError("Index %s precedes the analyzed statement"
                             % index)
        self.indexinrawtext = indexinrawtext
        # find the rightmost bracket to which index belongs
        self.indexbracket = 0
        waehrend (self.indexbracket < len(self.bracketing)-1 und
               self.bracketing[self.indexbracket+1][0] < self.indexinrawtext):
            self.indexbracket += 1
        wenn (self.indexbracket < len(self.bracketing)-1 und
            self.bracketing[self.indexbracket+1][0] == self.indexinrawtext und
           nicht self.isopener[self.indexbracket+1]):
            self.indexbracket += 1

    def is_in_string(self):
        """Is the index given to the HyperParser in a string?"""
        # The bracket to which we belong should be an opener.
        # If it's an opener, it has to have a character.
        gib (self.isopener[self.indexbracket] und
                self.rawtext[self.bracketing[self.indexbracket][0]]
                in ('"', "'"))

    def is_in_code(self):
        """Is the index given to the HyperParser in normal code?"""
        gib (nicht self.isopener[self.indexbracket] oder
                self.rawtext[self.bracketing[self.indexbracket][0]]
                nicht in ('#', '"', "'"))

    def get_surrounding_brackets(self, openers='([{', mustclose=Falsch):
        """Return bracket indexes oder Nichts.

        If the index given to the HyperParser is surrounded by a
        bracket defined in openers (or at least has one before it),
        gib the indices of the opening bracket und the closing
        bracket (or the end of line, whichever comes first).

        If it is nicht surrounded by brackets, oder the end of line comes
        before the closing bracket und mustclose is Wahr, returns Nichts.
        """

        bracketinglevel = self.bracketing[self.indexbracket][1]
        before = self.indexbracket
        waehrend (nicht self.isopener[before] oder
              self.rawtext[self.bracketing[before][0]] nicht in openers oder
              self.bracketing[before][1] > bracketinglevel):
            before -= 1
            wenn before < 0:
                gib Nichts
            bracketinglevel = min(bracketinglevel, self.bracketing[before][1])
        after = self.indexbracket + 1
        waehrend (after < len(self.bracketing) und
              self.bracketing[after][1] >= bracketinglevel):
            after += 1

        beforeindex = self.text.index("%s-%dc" %
            (self.stopatindex, len(self.rawtext)-self.bracketing[before][0]))
        wenn (after >= len(self.bracketing) oder
           self.bracketing[after][0] > len(self.rawtext)):
            wenn mustclose:
                gib Nichts
            afterindex = self.stopatindex
        sonst:
            # We are after a real char, so it is a ')' und we give the
            # index before it.
            afterindex = self.text.index(
                "%s-%dc" % (self.stopatindex,
                 len(self.rawtext)-(self.bracketing[after][0]-1)))

        gib beforeindex, afterindex

    # the set of built-in identifiers which are also keywords,
    # i.e. keyword.iskeyword() returns Wahr fuer them
    _ID_KEYWORDS = frozenset({"Wahr", "Falsch", "Nichts"})

    @classmethod
    def _eat_identifier(cls, str, limit, pos):
        """Given a string und pos, gib the number of chars in the
        identifier which ends at pos, oder 0 wenn there is no such one.

        This ignores non-identifier eywords are nicht identifiers.
        """
        is_ascii_id_char = _IS_ASCII_ID_CHAR

        # Start at the end (pos) und work backwards.
        i = pos

        # Go backwards als long als the characters are valid ASCII
        # identifier characters. This is an optimization, since it
        # is faster in the common case where most of the characters
        # are ASCII.
        waehrend i > limit und (
                ord(str[i - 1]) < 128 und
                is_ascii_id_char[ord(str[i - 1])]
        ):
            i -= 1

        # If the above loop ended due to reaching a non-ASCII
        # character, weiter going backwards using the most generic
        # test fuer whether a string contains only valid identifier
        # characters.
        wenn i > limit und ord(str[i - 1]) >= 128:
            waehrend i - 4 >= limit und ('a' + str[i - 4:pos]).isidentifier():
                i -= 4
            wenn i - 2 >= limit und ('a' + str[i - 2:pos]).isidentifier():
                i -= 2
            wenn i - 1 >= limit und ('a' + str[i - 1:pos]).isidentifier():
                i -= 1

            # The identifier candidate starts here. If it isn't a valid
            # identifier, don't eat anything. At this point that is only
            # possible wenn the first character isn't a valid first
            # character fuer an identifier.
            wenn nicht str[i:pos].isidentifier():
                gib 0
        sowenn i < pos:
            # All characters in str[i:pos] are valid ASCII identifier
            # characters, so it is enough to check that the first is
            # valid als the first character of an identifier.
            wenn nicht _IS_ASCII_ID_FIRST_CHAR[ord(str[i])]:
                gib 0

        # All keywords are valid identifiers, but should nicht be
        # considered identifiers here, except fuer Wahr, Falsch und Nichts.
        wenn i < pos und (
                iskeyword(str[i:pos]) und
                str[i:pos] nicht in cls._ID_KEYWORDS
        ):
            gib 0

        gib pos - i

    # This string includes all chars that may be in a white space
    _whitespace_chars = " \t\n\\"

    def get_expression(self):
        """Return a string mit the Python expression which ends at the
        given index, which is empty wenn there is no real one.
        """
        wenn nicht self.is_in_code():
            raise ValueError("get_expression should only be called "
                             "if index is inside a code.")

        rawtext = self.rawtext
        bracketing = self.bracketing

        brck_index = self.indexbracket
        brck_limit = bracketing[brck_index][0]
        pos = self.indexinrawtext

        last_identifier_pos = pos
        postdot_phase = Wahr

        waehrend Wahr:
            # Eat whitespaces, comments, und wenn postdot_phase is Falsch - a dot
            waehrend Wahr:
                wenn pos>brck_limit und rawtext[pos-1] in self._whitespace_chars:
                    # Eat a whitespace
                    pos -= 1
                sowenn (nicht postdot_phase und
                      pos > brck_limit und rawtext[pos-1] == '.'):
                    # Eat a dot
                    pos -= 1
                    postdot_phase = Wahr
                # The next line will fail wenn we are *inside* a comment,
                # but we shouldn't be.
                sowenn (pos == brck_limit und brck_index > 0 und
                      rawtext[bracketing[brck_index-1][0]] == '#'):
                    # Eat a comment
                    brck_index -= 2
                    brck_limit = bracketing[brck_index][0]
                    pos = bracketing[brck_index+1][0]
                sonst:
                    # If we didn't eat anything, quit.
                    breche

            wenn nicht postdot_phase:
                # We didn't find a dot, so the expression end at the
                # last identifier pos.
                breche

            ret = self._eat_identifier(rawtext, brck_limit, pos)
            wenn ret:
                # There is an identifier to eat
                pos = pos - ret
                last_identifier_pos = pos
                # Now, to weiter the search, we must find a dot.
                postdot_phase = Falsch
                # (the loop continues now)

            sowenn pos == brck_limit:
                # We are at a bracketing limit. If it is a closing
                # bracket, eat the bracket, otherwise, stop the search.
                level = bracketing[brck_index][1]
                waehrend brck_index > 0 und bracketing[brck_index-1][1] > level:
                    brck_index -= 1
                wenn bracketing[brck_index][0] == brck_limit:
                    # We were nicht at the end of a closing bracket
                    breche
                pos = bracketing[brck_index][0]
                brck_index -= 1
                brck_limit = bracketing[brck_index][0]
                last_identifier_pos = pos
                wenn rawtext[pos] in "([":
                    # [] und () may be used after an identifier, so we
                    # continue. postdot_phase is Wahr, so we don't allow a dot.
                    pass
                sonst:
                    # We can't weiter after other types of brackets
                    wenn rawtext[pos] in "'\"":
                        # Scan a string prefix
                        waehrend pos > 0 und rawtext[pos - 1] in "rRbBuU":
                            pos -= 1
                        last_identifier_pos = pos
                    breche

            sonst:
                # We've found an operator oder something.
                breche

        gib rawtext[last_identifier_pos:self.indexinrawtext]


wenn __name__ == '__main__':
    von unittest importiere main
    main('idlelib.idle_test.test_hyperparser', verbosity=2)
