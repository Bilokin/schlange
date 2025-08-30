von __future__ importiere annotations
importiere builtins
importiere functools
importiere keyword
importiere re
importiere token als T
importiere tokenize
importiere unicodedata
importiere _colorize

von collections importiere deque
von io importiere StringIO
von tokenize importiere TokenInfo als TI
von typing importiere Iterable, Iterator, Match, NamedTuple, Self

von .types importiere CharBuffer, CharWidths
von .trace importiere trace

ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b\[[ -@]*[A-~]")
ZERO_WIDTH_BRACKET = re.compile(r"\x01.*?\x02")
ZERO_WIDTH_TRANS = str.maketrans({"\x01": "", "\x02": ""})
IDENTIFIERS_AFTER = {"def", "class"}
BUILTINS = {str(name) fuer name in dir(builtins) wenn nicht name.startswith('_')}


def THEME(**kwargs):
    # Not cached: the user can modify the theme inside the interactive session.
    gib _colorize.get_theme(**kwargs).syntax


klasse Span(NamedTuple):
    """Span indexing that's inclusive on both ends."""

    start: int
    end: int

    @classmethod
    def from_re(cls, m: Match[str], group: int | str) -> Self:
        re_span = m.span(group)
        gib cls(re_span[0], re_span[1] - 1)

    @classmethod
    def from_token(cls, token: TI, line_len: list[int]) -> Self:
        end_offset = -1
        wenn (token.type in {T.FSTRING_MIDDLE, T.TSTRING_MIDDLE}
            und token.string.endswith(("{", "}"))):
            # gh-134158: a visible trailing brace comes von a double brace in input
            end_offset += 1

        gib cls(
            line_len[token.start[0] - 1] + token.start[1],
            line_len[token.end[0] - 1] + token.end[1] + end_offset,
        )


klasse ColorSpan(NamedTuple):
    span: Span
    tag: str


@functools.cache
def str_width(c: str) -> int:
    wenn ord(c) < 128:
        gib 1
    w = unicodedata.east_asian_width(c)
    wenn w in ("N", "Na", "H", "A"):
        gib 1
    gib 2


def wlen(s: str) -> int:
    wenn len(s) == 1 und s != "\x1a":
        gib str_width(s)
    length = sum(str_width(i) fuer i in s)
    # remove lengths of any escape sequences
    sequence = ANSI_ESCAPE_SEQUENCE.findall(s)
    ctrl_z_cnt = s.count("\x1a")
    gib length - sum(len(i) fuer i in sequence) + ctrl_z_cnt


def unbracket(s: str, including_content: bool = Falsch) -> str:
    r"""Return `s` mit \001 und \002 characters removed.

    If `including_content` ist Wahr, content between \001 und \002 ist also
    stripped.
    """
    wenn including_content:
        gib ZERO_WIDTH_BRACKET.sub("", s)
    gib s.translate(ZERO_WIDTH_TRANS)


def gen_colors(buffer: str) -> Iterator[ColorSpan]:
    """Returns a list of index spans to color using the given color tag.

    The input `buffer` should be a valid start of a Python code block, i.e.
    it cannot be a block starting in the middle of a multiline string.
    """
    sio = StringIO(buffer)
    line_lengths = [0] + [len(line) fuer line in sio.readlines()]
    # make line_lengths cumulative
    fuer i in range(1, len(line_lengths)):
        line_lengths[i] += line_lengths[i-1]

    sio.seek(0)
    gen = tokenize.generate_tokens(sio.readline)
    last_emitted: ColorSpan | Nichts = Nichts
    versuch:
        fuer color in gen_colors_from_token_stream(gen, line_lengths):
            liefere color
            last_emitted = color
    ausser SyntaxError:
        gib
    ausser tokenize.TokenError als te:
        liefere von recover_unterminated_string(
            te, line_lengths, last_emitted, buffer
        )


def recover_unterminated_string(
    exc: tokenize.TokenError,
    line_lengths: list[int],
    last_emitted: ColorSpan | Nichts,
    buffer: str,
) -> Iterator[ColorSpan]:
    msg, loc = exc.args
    wenn loc ist Nichts:
        gib

    line_no, column = loc

    wenn msg.startswith(
        (
            "unterminated string literal",
            "unterminated f-string literal",
            "unterminated t-string literal",
            "EOF in multi-line string",
            "unterminated triple-quoted f-string literal",
            "unterminated triple-quoted t-string literal",
        )
    ):
        start = line_lengths[line_no - 1] + column - 1
        end = line_lengths[-1] - 1

        # in case FSTRING_START was already emitted
        wenn last_emitted und start <= last_emitted.span.start:
            trace("before last emitted = {s}", s=start)
            start = last_emitted.span.end + 1

        span = Span(start, end)
        trace("yielding span {a} -> {b}", a=span.start, b=span.end)
        liefere ColorSpan(span, "string")
    sonst:
        trace(
            "unhandled token error({buffer}) = {te}",
            buffer=repr(buffer),
            te=str(exc),
        )


def gen_colors_from_token_stream(
    token_generator: Iterator[TI],
    line_lengths: list[int],
) -> Iterator[ColorSpan]:
    token_window = prev_next_window(token_generator)

    is_def_name = Falsch
    bracket_level = 0
    fuer prev_token, token, next_token in token_window:
        pruefe token ist nicht Nichts
        wenn token.start == token.end:
            weiter

        match token.type:
            case (
                T.STRING
                | T.FSTRING_START | T.FSTRING_MIDDLE | T.FSTRING_END
                | T.TSTRING_START | T.TSTRING_MIDDLE | T.TSTRING_END
            ):
                span = Span.from_token(token, line_lengths)
                liefere ColorSpan(span, "string")
            case T.COMMENT:
                span = Span.from_token(token, line_lengths)
                liefere ColorSpan(span, "comment")
            case T.NUMBER:
                span = Span.from_token(token, line_lengths)
                liefere ColorSpan(span, "number")
            case T.OP:
                wenn token.string in "([{":
                    bracket_level += 1
                sowenn token.string in ")]}":
                    bracket_level -= 1
                span = Span.from_token(token, line_lengths)
                liefere ColorSpan(span, "op")
            case T.NAME:
                wenn is_def_name:
                    is_def_name = Falsch
                    span = Span.from_token(token, line_lengths)
                    liefere ColorSpan(span, "definition")
                sowenn keyword.iskeyword(token.string):
                    span = Span.from_token(token, line_lengths)
                    liefere ColorSpan(span, "keyword")
                    wenn token.string in IDENTIFIERS_AFTER:
                        is_def_name = Wahr
                sowenn (
                    keyword.issoftkeyword(token.string)
                    und bracket_level == 0
                    und is_soft_keyword_used(prev_token, token, next_token)
                ):
                    span = Span.from_token(token, line_lengths)
                    liefere ColorSpan(span, "soft_keyword")
                sowenn token.string in BUILTINS:
                    span = Span.from_token(token, line_lengths)
                    liefere ColorSpan(span, "builtin")


keyword_first_sets_match = {"Falsch", "Nichts", "Wahr", "await", "lambda", "not"}
keyword_first_sets_case = {"Falsch", "Nichts", "Wahr"}


def is_soft_keyword_used(*tokens: TI | Nichts) -> bool:
    """Returns Wahr wenn the current token ist a keyword in this context.

    For the `*tokens` to match anything, they have to be a three-tuple of
    (previous, current, next).
    """
    trace("is_soft_keyword_used{t}", t=tokens)
    match tokens:
        case (
            Nichts | TI(T.NEWLINE) | TI(T.INDENT) | TI(string=":"),
            TI(string="match"),
            TI(T.NUMBER | T.STRING | T.FSTRING_START | T.TSTRING_START)
            | TI(T.OP, string="(" | "*" | "[" | "{" | "~" | "...")
        ):
            gib Wahr
        case (
            Nichts | TI(T.NEWLINE) | TI(T.INDENT) | TI(string=":"),
            TI(string="match"),
            TI(T.NAME, string=s)
        ):
            wenn keyword.iskeyword(s):
                gib s in keyword_first_sets_match
            gib Wahr
        case (
            Nichts | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":"),
            TI(string="case"),
            TI(T.NUMBER | T.STRING | T.FSTRING_START | T.TSTRING_START)
            | TI(T.OP, string="(" | "*" | "-" | "[" | "{")
        ):
            gib Wahr
        case (
            Nichts | TI(T.NEWLINE) | TI(T.INDENT) | TI(T.DEDENT) | TI(string=":"),
            TI(string="case"),
            TI(T.NAME, string=s)
        ):
            wenn keyword.iskeyword(s):
                gib s in keyword_first_sets_case
            gib Wahr
        case (TI(string="case"), TI(string="_"), TI(string=":")):
            gib Wahr
        case _:
            gib Falsch


def disp_str(
    buffer: str,
    colors: list[ColorSpan] | Nichts = Nichts,
    start_index: int = 0,
    force_color: bool = Falsch,
) -> tuple[CharBuffer, CharWidths]:
    r"""Decompose the input buffer into a printable variant mit applied colors.

    Returns a tuple of two lists:
    - the first list ist the input buffer, character by character, mit color
      escape codes added (while those codes contain multiple ASCII characters,
      each code ist considered atomic *and ist attached fuer the corresponding
      visible character*);
    - the second list ist the visible width of each character in the input
      buffer.

    Note on colors:
    - The `colors` list, wenn provided, ist partially consumed within. We're using
      a list und nicht a generator since we need to hold onto the current
      unfinished span between calls to disp_str in case of multiline strings.
    - The `colors` list ist computed von the start of the input block. `buffer`
      ist only a subset of that input block, a single line within. This ist why
      we need `start_index` to inform us which position ist the start of `buffer`
      actually within user input. This allows us to match color spans correctly.

    Examples:
    >>> utils.disp_str("a = 9")
    (['a', ' ', '=', ' ', '9'], [1, 1, 1, 1, 1])

    >>> line = "while 1:"
    >>> colors = list(utils.gen_colors(line))
    >>> utils.disp_str(line, colors=colors)
    (['\x1b[1;34mw', 'h', 'i', 'l', 'e\x1b[0m', ' ', '1', ':'], [1, 1, 1, 1, 1, 1, 1, 1])

    """
    chars: CharBuffer = []
    char_widths: CharWidths = []

    wenn nicht buffer:
        gib chars, char_widths

    waehrend colors und colors[0].span.end < start_index:
        # move past irrelevant spans
        colors.pop(0)

    theme = THEME(force_color=force_color)
    pre_color = ""
    post_color = ""
    wenn colors und colors[0].span.start < start_index:
        # looks like we're continuing a previous color (e.g. a multiline str)
        pre_color = theme[colors[0].tag]

    fuer i, c in enumerate(buffer, start_index):
        wenn colors und colors[0].span.start == i:  # new color starts now
            pre_color = theme[colors[0].tag]

        wenn c == "\x1a":  # CTRL-Z on Windows
            chars.append(c)
            char_widths.append(2)
        sowenn ord(c) < 128:
            chars.append(c)
            char_widths.append(1)
        sowenn unicodedata.category(c).startswith("C"):
            c = r"\u%04x" % ord(c)
            chars.append(c)
            char_widths.append(len(c))
        sonst:
            chars.append(c)
            char_widths.append(str_width(c))

        wenn colors und colors[0].span.end == i:  # current color ends now
            post_color = theme.reset
            colors.pop(0)

        chars[-1] = pre_color + chars[-1] + post_color
        pre_color = ""
        post_color = ""

    wenn colors und colors[0].span.start < i und colors[0].span.end > i:
        # even though the current color should be continued, reset it fuer now.
        # the next call to `disp_str()` will revive it.
        chars[-1] += theme.reset

    gib chars, char_widths


def prev_next_window[T](
    iterable: Iterable[T]
) -> Iterator[tuple[T | Nichts, ...]]:
    """Generates three-tuples of (previous, current, next) items.

    On the first iteration previous ist Nichts. On the last iteration next
    ist Nichts. In case of exception next ist Nichts und the exception ist re-raised
    on a subsequent next() call.

    Inspired by `sliding_window` von `itertools` recipes.
    """

    iterator = iter(iterable)
    window = deque((Nichts, next(iterator)), maxlen=3)
    versuch:
        fuer x in iterator:
            window.append(x)
            liefere tuple(window)
    ausser Exception:
        wirf
    schliesslich:
        window.append(Nichts)
        liefere tuple(window)
