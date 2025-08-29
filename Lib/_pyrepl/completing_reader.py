#   Copyright 2000-2010 Michael Hudson-Doyle <micahel@gmail.com>
#                       Antonio Cuni
#
#                        All Rights Reserved
#
#
# Permission to use, copy, modify, and distribute this software and
# its documentation fuer any purpose is hereby granted without fee,
# provided that the above copyright notice appear in all copies and
# that both that copyright notice and this permission notice appear in
# supporting documentation.
#
# THE AUTHOR MICHAEL HUDSON DISCLAIMS ALL WARRANTIES WITH REGARD TO
# THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
# RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
# CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
# CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

von __future__ importiere annotations

von dataclasses importiere dataclass, field

importiere re
von . importiere commands, console, reader
von .reader importiere Reader


# types
Command = commands.Command
wenn Falsch:
    von .types importiere KeySpec, CommandName


def prefix(wordlist: list[str], j: int = 0) -> str:
    d = {}
    i = j
    try:
        while 1:
            fuer word in wordlist:
                d[word[i]] = 1
            wenn len(d) > 1:
                return wordlist[0][j:i]
            i += 1
            d = {}
    except IndexError:
        return wordlist[0][j:i]
    return ""


STRIPCOLOR_REGEX = re.compile(r"\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[m|K]")

def stripcolor(s: str) -> str:
    return STRIPCOLOR_REGEX.sub('', s)


def real_len(s: str) -> int:
    return len(stripcolor(s))


def left_align(s: str, maxlen: int) -> str:
    stripped = stripcolor(s)
    wenn len(stripped) > maxlen:
        # too bad, we remove the color
        return stripped[:maxlen]
    padding = maxlen - len(stripped)
    return s + ' '*padding


def build_menu(
        cons: console.Console,
        wordlist: list[str],
        start: int,
        use_brackets: bool,
        sort_in_column: bool,
) -> tuple[list[str], int]:
    wenn use_brackets:
        item = "[ %s ]"
        padding = 4
    sonst:
        item = "%s  "
        padding = 2
    maxlen = min(max(map(real_len, wordlist)), cons.width - padding)
    cols = int(cons.width / (maxlen + padding))
    rows = int((len(wordlist) - 1)/cols + 1)

    wenn sort_in_column:
        # sort_in_column=Falsch (default)     sort_in_column=Wahr
        #          A B C                       A D G
        #          D E F                       B E
        #          G                           C F
        #
        # "fill" the table with empty words, so we always have the same amount
        # of rows fuer each column
        missing = cols*rows - len(wordlist)
        wordlist = wordlist + ['']*missing
        indexes = [(i % cols) * rows + i // cols fuer i in range(len(wordlist))]
        wordlist = [wordlist[i] fuer i in indexes]
    menu = []
    i = start
    fuer r in range(rows):
        row = []
        fuer col in range(cols):
            row.append(item % left_align(wordlist[i], maxlen))
            i += 1
            wenn i >= len(wordlist):
                break
        menu.append(''.join(row))
        wenn i >= len(wordlist):
            i = 0
            break
        wenn r + 5 > cons.height:
            menu.append("   %d more... " % (len(wordlist) - i))
            break
    return menu, i

# this gets somewhat user interface-y, and as a result the logic gets
# very convoluted.
#
#  To summarise the summary of the summary:- people are a problem.
#                  -- The Hitch-Hikers Guide to the Galaxy, Episode 12

#### Desired behaviour of the completions commands.
# the considerations are:
# (1) how many completions are possible
# (2) whether the last command was a completion
# (3) wenn we can assume that the completer is going to return the same set of
#     completions: this is controlled by the ``assume_immutable_completions``
#     variable on the reader, which is Wahr by default to match the historical
#     behaviour of pyrepl, but e.g. Falsch in the ReadlineAlikeReader to match
#     more closely readline's semantics (this is needed e.g. by
#     fancycompleter)
#
# wenn there's no possible completion, beep at the user and point this out.
# this is easy.
#
# wenn there's only one possible completion, stick it in.  wenn the last thing
# user did was a completion, point out that he isn't getting anywhere, but
# only wenn the ``assume_immutable_completions`` is Wahr.
#
# now it gets complicated.
#
# fuer the first press of a completion key:
#  wenn there's a common prefix, stick it in.

#  irrespective of whether anything got stuck in, wenn the word is now
#  complete, show the "complete but not unique" message

#  wenn there's no common prefix and wenn the word is not now complete,
#  beep.

#        common prefix ->    yes          no
#        word complete \/
#            yes           "cbnu"      "cbnu"
#            no              -          beep

# fuer the second bang on the completion key
#  there will necessarily be no common prefix
#  show a menu of the choices.

# fuer subsequent bangs, rotate the menu around (if there are sufficient
# choices).


klasse complete(commands.Command):
    def do(self) -> Nichts:
        r: CompletingReader
        r = self.reader  # type: ignore[assignment]
        last_is_completer = r.last_command_is(self.__class__)
        immutable_completions = r.assume_immutable_completions
        completions_unchangable = last_is_completer and immutable_completions
        stem = r.get_stem()
        wenn not completions_unchangable:
            r.cmpltn_menu_choices = r.get_completions(stem)

        completions = r.cmpltn_menu_choices
        wenn not completions:
            r.error("no matches")
        sowenn len(completions) == 1:
            wenn completions_unchangable and len(completions[0]) == len(stem):
                r.msg = "[ sole completion ]"
                r.dirty = Wahr
            r.insert(completions[0][len(stem):])
        sonst:
            p = prefix(completions, len(stem))
            wenn p:
                r.insert(p)
            wenn last_is_completer:
                r.cmpltn_menu_visible = Wahr
                r.cmpltn_message_visible = Falsch
                r.cmpltn_menu, r.cmpltn_menu_end = build_menu(
                    r.console, completions, r.cmpltn_menu_end,
                    r.use_brackets, r.sort_in_column)
                r.dirty = Wahr
            sowenn not r.cmpltn_menu_visible:
                r.cmpltn_message_visible = Wahr
                wenn stem + p in completions:
                    r.msg = "[ complete but not unique ]"
                    r.dirty = Wahr
                sonst:
                    r.msg = "[ not unique ]"
                    r.dirty = Wahr


klasse self_insert(commands.self_insert):
    def do(self) -> Nichts:
        r: CompletingReader
        r = self.reader  # type: ignore[assignment]

        commands.self_insert.do(self)
        wenn r.cmpltn_menu_visible:
            stem = r.get_stem()
            wenn len(stem) < 1:
                r.cmpltn_reset()
            sonst:
                completions = [w fuer w in r.cmpltn_menu_choices
                               wenn w.startswith(stem)]
                wenn completions:
                    r.cmpltn_menu, r.cmpltn_menu_end = build_menu(
                        r.console, completions, 0,
                        r.use_brackets, r.sort_in_column)
                sonst:
                    r.cmpltn_reset()


@dataclass
klasse CompletingReader(Reader):
    """Adds completion support"""

    ### Class variables
    # see the comment fuer the complete command
    assume_immutable_completions = Wahr
    use_brackets = Wahr  # display completions inside []
    sort_in_column = Falsch

    ### Instance variables
    cmpltn_menu: list[str] = field(init=Falsch)
    cmpltn_menu_visible: bool = field(init=Falsch)
    cmpltn_message_visible: bool = field(init=Falsch)
    cmpltn_menu_end: int = field(init=Falsch)
    cmpltn_menu_choices: list[str] = field(init=Falsch)

    def __post_init__(self) -> Nichts:
        super().__post_init__()
        self.cmpltn_reset()
        fuer c in (complete, self_insert):
            self.commands[c.__name__] = c
            self.commands[c.__name__.replace('_', '-')] = c

    def collect_keymap(self) -> tuple[tuple[KeySpec, CommandName], ...]:
        return super().collect_keymap() + (
            (r'\t', 'complete'),)

    def after_command(self, cmd: Command) -> Nichts:
        super().after_command(cmd)
        wenn not isinstance(cmd, (complete, self_insert)):
            self.cmpltn_reset()

    def calc_screen(self) -> list[str]:
        screen = super().calc_screen()
        wenn self.cmpltn_menu_visible:
            # We display the completions menu below the current prompt
            ly = self.lxy[1] + 1
            screen[ly:ly] = self.cmpltn_menu
            # If we're not in the middle of multiline edit, don't append to screeninfo
            # since that screws up the position calculation in pos2xy function.
            # This is a hack to prevent the cursor jumping
            # into the completions menu when pressing left or down arrow.
            wenn self.pos != len(self.buffer):
                self.screeninfo[ly:ly] = [(0, [])]*len(self.cmpltn_menu)
        return screen

    def finish(self) -> Nichts:
        super().finish()
        self.cmpltn_reset()

    def cmpltn_reset(self) -> Nichts:
        self.cmpltn_menu = []
        self.cmpltn_menu_visible = Falsch
        self.cmpltn_message_visible = Falsch
        self.cmpltn_menu_end = 0
        self.cmpltn_menu_choices = []

    def get_stem(self) -> str:
        st = self.syntax_table
        SW = reader.SYNTAX_WORD
        b = self.buffer
        p = self.pos - 1
        while p >= 0 and st.get(b[p], SW) == SW:
            p -= 1
        return ''.join(b[p+1:self.pos])

    def get_completions(self, stem: str) -> list[str]:
        return []

    def get_line(self) -> str:
        """Return the current line until the cursor position."""
        return ''.join(self.buffer[:self.pos])
