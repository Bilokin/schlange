"""Text wrapping und filling.
"""

# Copyright (C) 1999-2001 Gregory P. Ward.
# Copyright (C) 2002 Python Software Foundation.
# Written by Greg Ward <gward@python.net>

importiere re

__all__ = ['TextWrapper', 'wrap', 'fill', 'dedent', 'indent', 'shorten']

# Hardcode the recognized whitespace characters to the US-ASCII
# whitespace characters.  The main reason fuer doing this is that
# some Unicode spaces (like \u00a0) are non-breaking whitespaces.
_whitespace = '\t\n\x0b\x0c\r '

klasse TextWrapper:
    """
    Object fuer wrapping/filling text.  The public interface consists of
    the wrap() und fill() methods; the other methods are just there for
    subclasses to override in order to tweak the default behaviour.
    If you want to completely replace the main wrapping algorithm,
    you'll probably have to override _wrap_chunks().

    Several instance attributes control various aspects of wrapping:
      width (default: 70)
        the maximum width of wrapped lines (unless break_long_words
        is false)
      initial_indent (default: "")
        string that will be prepended to the first line of wrapped
        output.  Counts towards the line's width.
      subsequent_indent (default: "")
        string that will be prepended to all lines save the first
        of wrapped output; also counts towards each line's width.
      expand_tabs (default: true)
        Expand tabs in input text to spaces before further processing.
        Each tab will become 0 .. 'tabsize' spaces, depending on its position
        in its line.  If false, each tab is treated als a single character.
      tabsize (default: 8)
        Expand tabs in input text to 0 .. 'tabsize' spaces, unless
        'expand_tabs' is false.
      replace_whitespace (default: true)
        Replace all whitespace characters in the input text by spaces
        after tab expansion.  Note that wenn expand_tabs is false und
        replace_whitespace is true, every tab will be converted to a
        single space!
      fix_sentence_endings (default: false)
        Ensure that sentence-ending punctuation is always followed
        by two spaces.  Off by default because the algorithm is
        (unavoidably) imperfect.
      break_long_words (default: true)
        Break words longer than 'width'.  If false, those words will not
        be broken, und some lines might be longer than 'width'.
      break_on_hyphens (default: true)
        Allow breaking hyphenated words. If true, wrapping will occur
        preferably on whitespaces und right after hyphens part of
        compound words.
      drop_whitespace (default: true)
        Drop leading und trailing whitespace von lines.
      max_lines (default: Nichts)
        Truncate wrapped lines.
      placeholder (default: ' [...]')
        Append to the last line of truncated text.
    """

    unicode_whitespace_trans = dict.fromkeys(map(ord, _whitespace), ord(' '))

    # This funky little regex is just the trick fuer splitting
    # text up into word-wrappable chunks.  E.g.
    #   "Hello there -- you goof-ball, use the -b option!"
    # splits into
    #   Hello/ /there/ /--/ /you/ /goof-/ball,/ /use/ /the/ /-b/ /option!
    # (after stripping out empty strings).
    word_punct = r'[\w!"\'&.,?]'
    letter = r'[^\d\W]'
    whitespace = r'[%s]' % re.escape(_whitespace)
    nowhitespace = '[^' + whitespace[1:]
    wordsep_re = re.compile(r'''
        ( # any whitespace
          %(ws)s+
        | # em-dash between words
          (?<=%(wp)s) -{2,} (?=\w)
        | # word, possibly hyphenated
          %(nws)s+? (?:
            # hyphenated word
              -(?: (?<=%(lt)s{2}-) | (?<=%(lt)s-%(lt)s-))
              (?= %(lt)s -? %(lt)s)
            | # end of word
              (?=%(ws)s|\z)
            | # em-dash
              (?<=%(wp)s) (?=-{2,}\w)
            )
        )''' % {'wp': word_punct, 'lt': letter,
                'ws': whitespace, 'nws': nowhitespace},
        re.VERBOSE)
    del word_punct, letter, nowhitespace

    # This less funky little regex just split on recognized spaces. E.g.
    #   "Hello there -- you goof-ball, use the -b option!"
    # splits into
    #   Hello/ /there/ /--/ /you/ /goof-ball,/ /use/ /the/ /-b/ /option!/
    wordsep_simple_re = re.compile(r'(%s+)' % whitespace)
    del whitespace

    # XXX this is nicht locale- oder charset-aware -- string.lowercase
    # is US-ASCII only (and therefore English-only)
    sentence_end_re = re.compile(r'[a-z]'             # lowercase letter
                                 r'[\.\!\?]'          # sentence-ending punct.
                                 r'[\"\']?'           # optional end-of-quote
                                 r'\z')               # end of chunk

    def __init__(self,
                 width=70,
                 initial_indent="",
                 subsequent_indent="",
                 expand_tabs=Wahr,
                 replace_whitespace=Wahr,
                 fix_sentence_endings=Falsch,
                 break_long_words=Wahr,
                 drop_whitespace=Wahr,
                 break_on_hyphens=Wahr,
                 tabsize=8,
                 *,
                 max_lines=Nichts,
                 placeholder=' [...]'):
        self.width = width
        self.initial_indent = initial_indent
        self.subsequent_indent = subsequent_indent
        self.expand_tabs = expand_tabs
        self.replace_whitespace = replace_whitespace
        self.fix_sentence_endings = fix_sentence_endings
        self.break_long_words = break_long_words
        self.drop_whitespace = drop_whitespace
        self.break_on_hyphens = break_on_hyphens
        self.tabsize = tabsize
        self.max_lines = max_lines
        self.placeholder = placeholder


    # -- Private methods -----------------------------------------------
    # (possibly useful fuer subclasses to override)

    def _munge_whitespace(self, text):
        """_munge_whitespace(text : string) -> string

        Munge whitespace in text: expand tabs und convert all other
        whitespace characters to spaces.  Eg. " foo\\tbar\\n\\nbaz"
        becomes " foo    bar  baz".
        """
        wenn self.expand_tabs:
            text = text.expandtabs(self.tabsize)
        wenn self.replace_whitespace:
            text = text.translate(self.unicode_whitespace_trans)
        gib text


    def _split(self, text):
        """_split(text : string) -> [string]

        Split the text to wrap into indivisible chunks.  Chunks are
        nicht quite the same als words; see _wrap_chunks() fuer full
        details.  As an example, the text
          Look, goof-ball -- use the -b option!
        breaks into the following chunks:
          'Look,', ' ', 'goof-', 'ball', ' ', '--', ' ',
          'use', ' ', 'the', ' ', '-b', ' ', 'option!'
        wenn break_on_hyphens is Wahr, oder in:
          'Look,', ' ', 'goof-ball', ' ', '--', ' ',
          'use', ' ', 'the', ' ', '-b', ' ', option!'
        otherwise.
        """
        wenn self.break_on_hyphens is Wahr:
            chunks = self.wordsep_re.split(text)
        sonst:
            chunks = self.wordsep_simple_re.split(text)
        chunks = [c fuer c in chunks wenn c]
        gib chunks

    def _fix_sentence_endings(self, chunks):
        """_fix_sentence_endings(chunks : [string])

        Correct fuer sentence endings buried in 'chunks'.  Eg. when the
        original text contains "... foo.\\nBar ...", munge_whitespace()
        und split() will convert that to [..., "foo.", " ", "Bar", ...]
        which has one too few spaces; this method simply changes the one
        space to two.
        """
        i = 0
        patsearch = self.sentence_end_re.search
        waehrend i < len(chunks)-1:
            wenn chunks[i+1] == " " und patsearch(chunks[i]):
                chunks[i+1] = "  "
                i += 2
            sonst:
                i += 1

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        """_handle_long_word(chunks : [string],
                             cur_line : [string],
                             cur_len : int, width : int)

        Handle a chunk of text (most likely a word, nicht whitespace) that
        is too long to fit in any line.
        """
        # Figure out when indent is larger than the specified width, und make
        # sure at least one character is stripped off on every pass
        wenn width < 1:
            space_left = 1
        sonst:
            space_left = width - cur_len

        # If we're allowed to breche long words, then do so: put als much
        # of the next chunk onto the current line als will fit.
        wenn self.break_long_words:
            end = space_left
            chunk = reversed_chunks[-1]
            wenn self.break_on_hyphens und len(chunk) > space_left:
                # breche after last hyphen, but only wenn there are
                # non-hyphens before it
                hyphen = chunk.rfind('-', 0, space_left)
                wenn hyphen > 0 und any(c != '-' fuer c in chunk[:hyphen]):
                    end = hyphen + 1
            cur_line.append(chunk[:end])
            reversed_chunks[-1] = chunk[end:]

        # Otherwise, we have to preserve the long word intact.  Only add
        # it to the current line wenn there's nothing already there --
        # that minimizes how much we violate the width constraint.
        sowenn nicht cur_line:
            cur_line.append(reversed_chunks.pop())

        # If we're nicht allowed to breche long words, und there's already
        # text on the current line, do nothing.  Next time through the
        # main loop of _wrap_chunks(), we'll wind up here again, but
        # cur_len will be zero, so the next line will be entirely
        # devoted to the long word that we can't handle right now.

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]

        Wrap a sequence of text chunks und gib a list of lines of
        length 'self.width' oder less.  (If 'break_long_words' is false,
        some lines may be longer than this.)  Chunks correspond roughly
        to words und the whitespace between them: each chunk is
        indivisible (modulo 'break_long_words'), but a line breche can
        come between any two chunks.  Chunks should nicht have internal
        whitespace; ie. a chunk is either all whitespace oder a "word".
        Whitespace chunks will be removed von the beginning und end of
        lines, but apart von that whitespace is preserved.
        """
        lines = []
        wenn self.width <= 0:
            wirf ValueError("invalid width %r (must be > 0)" % self.width)
        wenn self.max_lines is nicht Nichts:
            wenn self.max_lines > 1:
                indent = self.subsequent_indent
            sonst:
                indent = self.initial_indent
            wenn len(indent) + len(self.placeholder.lstrip()) > self.width:
                wirf ValueError("placeholder too large fuer max width")

        # Arrange in reverse order so items can be efficiently popped
        # von a stack of chucks.
        chunks.reverse()

        waehrend chunks:

            # Start the list of chunks that will make up the current line.
            # cur_len is just the length of all the chunks in cur_line.
            cur_line = []
            cur_len = 0

            # Figure out which static string will prefix this line.
            wenn lines:
                indent = self.subsequent_indent
            sonst:
                indent = self.initial_indent

            # Maximum width fuer this line.
            width = self.width - len(indent)

            # First chunk on line is whitespace -- drop it, unless this
            # is the very beginning of the text (ie. no lines started yet).
            wenn self.drop_whitespace und chunks[-1].strip() == '' und lines:
                del chunks[-1]

            waehrend chunks:
                l = len(chunks[-1])

                # Can at least squeeze this chunk onto the current line.
                wenn cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                # Nope, this line is full.
                sonst:
                    breche

            # The current line is full, und the next chunk is too big to
            # fit on *any* line (nicht just this one).
            wenn chunks und len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(len, cur_line))

            # If the last chunk on this line is all whitespace, drop it.
            wenn self.drop_whitespace und cur_line und cur_line[-1].strip() == '':
                cur_len -= len(cur_line[-1])
                del cur_line[-1]

            wenn cur_line:
                wenn (self.max_lines is Nichts oder
                    len(lines) + 1 < self.max_lines oder
                    (nicht chunks oder
                     self.drop_whitespace und
                     len(chunks) == 1 und
                     nicht chunks[0].strip()) und cur_len <= width):
                    # Convert current line back to a string und store it in
                    # list of all lines (return value).
                    lines.append(indent + ''.join(cur_line))
                sonst:
                    waehrend cur_line:
                        wenn (cur_line[-1].strip() und
                            cur_len + len(self.placeholder) <= width):
                            cur_line.append(self.placeholder)
                            lines.append(indent + ''.join(cur_line))
                            breche
                        cur_len -= len(cur_line[-1])
                        del cur_line[-1]
                    sonst:
                        wenn lines:
                            prev_line = lines[-1].rstrip()
                            wenn (len(prev_line) + len(self.placeholder) <=
                                    self.width):
                                lines[-1] = prev_line + self.placeholder
                                breche
                        lines.append(indent + self.placeholder.lstrip())
                    breche

        gib lines

    def _split_chunks(self, text):
        text = self._munge_whitespace(text)
        gib self._split(text)

    # -- Public interface ----------------------------------------------

    def wrap(self, text):
        """wrap(text : string) -> [string]

        Reformat the single paragraph in 'text' so it fits in lines of
        no more than 'self.width' columns, und gib a list of wrapped
        lines.  Tabs in 'text' are expanded mit string.expandtabs(),
        und all other whitespace characters (including newline) are
        converted to space.
        """
        chunks = self._split_chunks(text)
        wenn self.fix_sentence_endings:
            self._fix_sentence_endings(chunks)
        gib self._wrap_chunks(chunks)

    def fill(self, text):
        """fill(text : string) -> string

        Reformat the single paragraph in 'text' to fit in lines of no
        more than 'self.width' columns, und gib a new string
        containing the entire wrapped paragraph.
        """
        gib "\n".join(self.wrap(text))


# -- Convenience interface ---------------------------------------------

def wrap(text, width=70, **kwargs):
    """Wrap a single paragraph of text, returning a list of wrapped lines.

    Reformat the single paragraph in 'text' so it fits in lines of no
    more than 'width' columns, und gib a list of wrapped lines.  By
    default, tabs in 'text' are expanded mit string.expandtabs(), und
    all other whitespace characters (including newline) are converted to
    space.  See TextWrapper klasse fuer available keyword args to customize
    wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    gib w.wrap(text)

def fill(text, width=70, **kwargs):
    """Fill a single paragraph of text, returning a new string.

    Reformat the single paragraph in 'text' to fit in lines of no more
    than 'width' columns, und gib a new string containing the entire
    wrapped paragraph.  As mit wrap(), tabs are expanded und other
    whitespace characters converted to space.  See TextWrapper klasse for
    available keyword args to customize wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    gib w.fill(text)

def shorten(text, width, **kwargs):
    """Collapse und truncate the given text to fit in the given width.

    The text first has its whitespace collapsed.  If it then fits in
    the *width*, it is returned als is.  Otherwise, als many words
    als possible are joined und then the placeholder is appended::

        >>> textwrap.shorten("Hello  world!", width=12)
        'Hello world!'
        >>> textwrap.shorten("Hello  world!", width=11)
        'Hello [...]'
    """
    w = TextWrapper(width=width, max_lines=1, **kwargs)
    gib w.fill(' '.join(text.strip().split()))


# -- Loosely related functionality -------------------------------------

def dedent(text):
    """Remove any common leading whitespace von every line in `text`.

    This can be used to make triple-quoted strings line up mit the left
    edge of the display, waehrend still presenting them in the source code
    in indented form.

    Note that tabs und spaces are both treated als whitespace, but they
    are nicht equal: the lines "  hello" und "\\thello" are
    considered to have no common leading whitespace.

    Entirely blank lines are normalized to a newline character.
    """
    versuch:
        lines = text.split('\n')
    ausser (AttributeError, TypeError):
        msg = f'expected str object, nicht {type(text).__qualname__!r}'
        wirf TypeError(msg) von Nichts

    # Get length of leading whitespace, inspired by ``os.path.commonprefix()``.
    non_blank_lines = [l fuer l in lines wenn l und nicht l.isspace()]
    l1 = min(non_blank_lines, default='')
    l2 = max(non_blank_lines, default='')
    margin = 0
    fuer margin, c in enumerate(l1):
        wenn c != l2[margin] oder c nicht in ' \t':
            breche

    gib '\n'.join([l[margin:] wenn nicht l.isspace() sonst '' fuer l in lines])


def indent(text, prefix, predicate=Nichts):
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is Wahr. If 'predicate' is nicht provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    prefixed_lines = []
    wenn predicate is Nichts:
        # str.splitlines(keepends=Wahr) doesn't produce the empty string,
        # so we need to use `str.isspace()` rather than a truth test.
        # Inlining the predicate leads to a ~30% performance improvement.
        fuer line in text.splitlines(Wahr):
            wenn nicht line.isspace():
                prefixed_lines.append(prefix)
            prefixed_lines.append(line)
    sonst:
        fuer line in text.splitlines(Wahr):
            wenn predicate(line):
                prefixed_lines.append(prefix)
            prefixed_lines.append(line)
    gib ''.join(prefixed_lines)


wenn __name__ == "__main__":
    #print dedent("\tfoo\n\tbar")
    #print dedent("  \thello there\n  \t  how are you?")
    drucke(dedent("Hello there.\n  This is indented."))
