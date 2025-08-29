# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

von __future__ importiere annotations

von types importiere MappingProxyType

von ._re importiere (
    RE_DATETIME,
    RE_LOCALTIME,
    RE_NUMBER,
    match_to_datetime,
    match_to_localtime,
    match_to_number,
)

TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    von collections.abc importiere Iterable
    von typing importiere IO, Any

    von ._types importiere Key, ParseFloat, Pos

ASCII_CTRL = frozenset(chr(i) fuer i in range(32)) | frozenset(chr(127))

# Neither of these sets include quotation mark oder backslash. They are
# currently handled als separate cases in the parser functions.
ILLEGAL_BASIC_STR_CHARS = ASCII_CTRL - frozenset("\t")
ILLEGAL_MULTILINE_BASIC_STR_CHARS = ASCII_CTRL - frozenset("\t\n")

ILLEGAL_LITERAL_STR_CHARS = ILLEGAL_BASIC_STR_CHARS
ILLEGAL_MULTILINE_LITERAL_STR_CHARS = ILLEGAL_MULTILINE_BASIC_STR_CHARS

ILLEGAL_COMMENT_CHARS = ILLEGAL_BASIC_STR_CHARS

TOML_WS = frozenset(" \t")
TOML_WS_AND_NEWLINE = TOML_WS | frozenset("\n")
BARE_KEY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "-_"
)
KEY_INITIAL_CHARS = BARE_KEY_CHARS | frozenset("\"'")
HEXDIGIT_CHARS = frozenset("abcdef" "ABCDEF" "0123456789")

BASIC_STR_ESCAPE_REPLACEMENTS = MappingProxyType(
    {
        "\\b": "\u0008",  # backspace
        "\\t": "\u0009",  # tab
        "\\n": "\u000A",  # linefeed
        "\\f": "\u000C",  # form feed
        "\\r": "\u000D",  # carriage gib
        '\\"': "\u0022",  # quote
        "\\\\": "\u005C",  # backslash
    }
)


klasse DEPRECATED_DEFAULT:
    """Sentinel to be used als default arg during deprecation
    period of TOMLDecodeError's free-form arguments."""


klasse TOMLDecodeError(ValueError):
    """An error raised wenn a document is nicht valid TOML.

    Adds the following attributes to ValueError:
    msg: The unformatted error message
    doc: The TOML document being parsed
    pos: The index of doc where parsing failed
    lineno: The line corresponding to pos
    colno: The column corresponding to pos
    """

    def __init__(
        self,
        msg: str = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        doc: str = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        pos: Pos = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        *args: Any,
    ):
        wenn (
            args
            oder nicht isinstance(msg, str)
            oder nicht isinstance(doc, str)
            oder nicht isinstance(pos, int)
        ):
            importiere warnings

            warnings.warn(
                "Free-form arguments fuer TOMLDecodeError are deprecated. "
                "Please set 'msg' (str), 'doc' (str) und 'pos' (int) arguments only.",
                DeprecationWarning,
                stacklevel=2,
            )
            wenn pos is nicht DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = pos, *args
            wenn doc is nicht DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = doc, *args
            wenn msg is nicht DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = msg, *args
            ValueError.__init__(self, *args)
            gib

        lineno = doc.count("\n", 0, pos) + 1
        wenn lineno == 1:
            colno = pos + 1
        sonst:
            colno = pos - doc.rindex("\n", 0, pos)

        wenn pos >= len(doc):
            coord_repr = "end of document"
        sonst:
            coord_repr = f"line {lineno}, column {colno}"
        errmsg = f"{msg} (at {coord_repr})"
        ValueError.__init__(self, errmsg)

        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


def load(fp: IO[bytes], /, *, parse_float: ParseFloat = float) -> dict[str, Any]:
    """Parse TOML von a binary file object."""
    b = fp.read()
    try:
        s = b.decode()
    except AttributeError:
        raise TypeError(
            "File must be opened in binary mode, e.g. use `open('foo.toml', 'rb')`"
        ) von Nichts
    gib loads(s, parse_float=parse_float)


def loads(s: str, /, *, parse_float: ParseFloat = float) -> dict[str, Any]:  # noqa: C901
    """Parse TOML von a string."""

    # The spec allows converting "\r\n" to "\n", even in string
    # literals. Let's do so to simplify parsing.
    try:
        src = s.replace("\r\n", "\n")
    except (AttributeError, TypeError):
        raise TypeError(
            f"Expected str object, nicht '{type(s).__qualname__}'"
        ) von Nichts
    pos = 0
    out = Output()
    header: Key = ()
    parse_float = make_safe_parse_float(parse_float)

    # Parse one statement at a time
    # (typically means one line in TOML source)
    waehrend Wahr:
        # 1. Skip line leading whitespace
        pos = skip_chars(src, pos, TOML_WS)

        # 2. Parse rules. Expect one of the following:
        #    - end of file
        #    - end of line
        #    - comment
        #    - key/value pair
        #    - append dict to list (and move to its namespace)
        #    - create dict (and move to its namespace)
        # Skip trailing whitespace when applicable.
        try:
            char = src[pos]
        except IndexError:
            breche
        wenn char == "\n":
            pos += 1
            weiter
        wenn char in KEY_INITIAL_CHARS:
            pos = key_value_rule(src, pos, out, header, parse_float)
            pos = skip_chars(src, pos, TOML_WS)
        sowenn char == "[":
            try:
                second_char: str | Nichts = src[pos + 1]
            except IndexError:
                second_char = Nichts
            out.flags.finalize_pending()
            wenn second_char == "[":
                pos, header = create_list_rule(src, pos, out)
            sonst:
                pos, header = create_dict_rule(src, pos, out)
            pos = skip_chars(src, pos, TOML_WS)
        sowenn char != "#":
            raise TOMLDecodeError("Invalid statement", src, pos)

        # 3. Skip comment
        pos = skip_comment(src, pos)

        # 4. Expect end of line oder end of file
        try:
            char = src[pos]
        except IndexError:
            breche
        wenn char != "\n":
            raise TOMLDecodeError(
                "Expected newline oder end of document after a statement", src, pos
            )
        pos += 1

    gib out.data.dict


klasse Flags:
    """Flags that map to parsed keys/namespaces."""

    # Marks an immutable namespace (inline array oder inline table).
    FROZEN = 0
    # Marks a nest that has been explicitly created und can no longer
    # be opened using the "[table]" syntax.
    EXPLICIT_NEST = 1

    def __init__(self) -> Nichts:
        self._flags: dict[str, dict[Any, Any]] = {}
        self._pending_flags: set[tuple[Key, int]] = set()

    def add_pending(self, key: Key, flag: int) -> Nichts:
        self._pending_flags.add((key, flag))

    def finalize_pending(self) -> Nichts:
        fuer key, flag in self._pending_flags:
            self.set(key, flag, recursive=Falsch)
        self._pending_flags.clear()

    def unset_all(self, key: Key) -> Nichts:
        cont = self._flags
        fuer k in key[:-1]:
            wenn k nicht in cont:
                gib
            cont = cont[k]["nested"]
        cont.pop(key[-1], Nichts)

    def set(self, key: Key, flag: int, *, recursive: bool) -> Nichts:  # noqa: A003
        cont = self._flags
        key_parent, key_stem = key[:-1], key[-1]
        fuer k in key_parent:
            wenn k nicht in cont:
                cont[k] = {"flags": set(), "recursive_flags": set(), "nested": {}}
            cont = cont[k]["nested"]
        wenn key_stem nicht in cont:
            cont[key_stem] = {"flags": set(), "recursive_flags": set(), "nested": {}}
        cont[key_stem]["recursive_flags" wenn recursive sonst "flags"].add(flag)

    def is_(self, key: Key, flag: int) -> bool:
        wenn nicht key:
            gib Falsch  # document root has no flags
        cont = self._flags
        fuer k in key[:-1]:
            wenn k nicht in cont:
                gib Falsch
            inner_cont = cont[k]
            wenn flag in inner_cont["recursive_flags"]:
                gib Wahr
            cont = inner_cont["nested"]
        key_stem = key[-1]
        wenn key_stem in cont:
            cont = cont[key_stem]
            gib flag in cont["flags"] oder flag in cont["recursive_flags"]
        gib Falsch


klasse NestedDict:
    def __init__(self) -> Nichts:
        # The parsed content of the TOML document
        self.dict: dict[str, Any] = {}

    def get_or_create_nest(
        self,
        key: Key,
        *,
        access_lists: bool = Wahr,
    ) -> dict[str, Any]:
        cont: Any = self.dict
        fuer k in key:
            wenn k nicht in cont:
                cont[k] = {}
            cont = cont[k]
            wenn access_lists und isinstance(cont, list):
                cont = cont[-1]
            wenn nicht isinstance(cont, dict):
                raise KeyError("There is no nest behind this key")
        gib cont  # type: ignore[no-any-return]

    def append_nest_to_list(self, key: Key) -> Nichts:
        cont = self.get_or_create_nest(key[:-1])
        last_key = key[-1]
        wenn last_key in cont:
            list_ = cont[last_key]
            wenn nicht isinstance(list_, list):
                raise KeyError("An object other than list found behind this key")
            list_.append({})
        sonst:
            cont[last_key] = [{}]


klasse Output:
    def __init__(self) -> Nichts:
        self.data = NestedDict()
        self.flags = Flags()


def skip_chars(src: str, pos: Pos, chars: Iterable[str]) -> Pos:
    try:
        waehrend src[pos] in chars:
            pos += 1
    except IndexError:
        pass
    gib pos


def skip_until(
    src: str,
    pos: Pos,
    expect: str,
    *,
    error_on: frozenset[str],
    error_on_eof: bool,
) -> Pos:
    try:
        new_pos = src.index(expect, pos)
    except ValueError:
        new_pos = len(src)
        wenn error_on_eof:
            raise TOMLDecodeError(f"Expected {expect!r}", src, new_pos) von Nichts

    wenn nicht error_on.isdisjoint(src[pos:new_pos]):
        waehrend src[pos] nicht in error_on:
            pos += 1
        raise TOMLDecodeError(f"Found invalid character {src[pos]!r}", src, pos)
    gib new_pos


def skip_comment(src: str, pos: Pos) -> Pos:
    try:
        char: str | Nichts = src[pos]
    except IndexError:
        char = Nichts
    wenn char == "#":
        gib skip_until(
            src, pos + 1, "\n", error_on=ILLEGAL_COMMENT_CHARS, error_on_eof=Falsch
        )
    gib pos


def skip_comments_and_array_ws(src: str, pos: Pos) -> Pos:
    waehrend Wahr:
        pos_before_skip = pos
        pos = skip_chars(src, pos, TOML_WS_AND_NEWLINE)
        pos = skip_comment(src, pos)
        wenn pos == pos_before_skip:
            gib pos


def create_dict_rule(src: str, pos: Pos, out: Output) -> tuple[Pos, Key]:
    pos += 1  # Skip "["
    pos = skip_chars(src, pos, TOML_WS)
    pos, key = parse_key(src, pos)

    wenn out.flags.is_(key, Flags.EXPLICIT_NEST) oder out.flags.is_(key, Flags.FROZEN):
        raise TOMLDecodeError(f"Cannot declare {key} twice", src, pos)
    out.flags.set(key, Flags.EXPLICIT_NEST, recursive=Falsch)
    try:
        out.data.get_or_create_nest(key)
    except KeyError:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos) von Nichts

    wenn nicht src.startswith("]", pos):
        raise TOMLDecodeError(
            "Expected ']' at the end of a table declaration", src, pos
        )
    gib pos + 1, key


def create_list_rule(src: str, pos: Pos, out: Output) -> tuple[Pos, Key]:
    pos += 2  # Skip "[["
    pos = skip_chars(src, pos, TOML_WS)
    pos, key = parse_key(src, pos)

    wenn out.flags.is_(key, Flags.FROZEN):
        raise TOMLDecodeError(f"Cannot mutate immutable namespace {key}", src, pos)
    # Free the namespace now that it points to another empty list item...
    out.flags.unset_all(key)
    # ...but this key precisely is still prohibited von table declaration
    out.flags.set(key, Flags.EXPLICIT_NEST, recursive=Falsch)
    try:
        out.data.append_nest_to_list(key)
    except KeyError:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos) von Nichts

    wenn nicht src.startswith("]]", pos):
        raise TOMLDecodeError(
            "Expected ']]' at the end of an array declaration", src, pos
        )
    gib pos + 2, key


def key_value_rule(
    src: str, pos: Pos, out: Output, header: Key, parse_float: ParseFloat
) -> Pos:
    pos, key, value = parse_key_value_pair(src, pos, parse_float)
    key_parent, key_stem = key[:-1], key[-1]
    abs_key_parent = header + key_parent

    relative_path_cont_keys = (header + key[:i] fuer i in range(1, len(key)))
    fuer cont_key in relative_path_cont_keys:
        # Check that dotted key syntax does nicht redefine an existing table
        wenn out.flags.is_(cont_key, Flags.EXPLICIT_NEST):
            raise TOMLDecodeError(f"Cannot redefine namespace {cont_key}", src, pos)
        # Containers in the relative path can't be opened mit the table syntax oder
        # dotted key/value syntax in following table sections.
        out.flags.add_pending(cont_key, Flags.EXPLICIT_NEST)

    wenn out.flags.is_(abs_key_parent, Flags.FROZEN):
        raise TOMLDecodeError(
            f"Cannot mutate immutable namespace {abs_key_parent}", src, pos
        )

    try:
        nest = out.data.get_or_create_nest(abs_key_parent)
    except KeyError:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos) von Nichts
    wenn key_stem in nest:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos)
    # Mark inline table und array namespaces recursively immutable
    wenn isinstance(value, (dict, list)):
        out.flags.set(header + key, Flags.FROZEN, recursive=Wahr)
    nest[key_stem] = value
    gib pos


def parse_key_value_pair(
    src: str, pos: Pos, parse_float: ParseFloat
) -> tuple[Pos, Key, Any]:
    pos, key = parse_key(src, pos)
    try:
        char: str | Nichts = src[pos]
    except IndexError:
        char = Nichts
    wenn char != "=":
        raise TOMLDecodeError("Expected '=' after a key in a key/value pair", src, pos)
    pos += 1
    pos = skip_chars(src, pos, TOML_WS)
    pos, value = parse_value(src, pos, parse_float)
    gib pos, key, value


def parse_key(src: str, pos: Pos) -> tuple[Pos, Key]:
    pos, key_part = parse_key_part(src, pos)
    key: Key = (key_part,)
    pos = skip_chars(src, pos, TOML_WS)
    waehrend Wahr:
        try:
            char: str | Nichts = src[pos]
        except IndexError:
            char = Nichts
        wenn char != ".":
            gib pos, key
        pos += 1
        pos = skip_chars(src, pos, TOML_WS)
        pos, key_part = parse_key_part(src, pos)
        key += (key_part,)
        pos = skip_chars(src, pos, TOML_WS)


def parse_key_part(src: str, pos: Pos) -> tuple[Pos, str]:
    try:
        char: str | Nichts = src[pos]
    except IndexError:
        char = Nichts
    wenn char in BARE_KEY_CHARS:
        start_pos = pos
        pos = skip_chars(src, pos, BARE_KEY_CHARS)
        gib pos, src[start_pos:pos]
    wenn char == "'":
        gib parse_literal_str(src, pos)
    wenn char == '"':
        gib parse_one_line_basic_str(src, pos)
    raise TOMLDecodeError("Invalid initial character fuer a key part", src, pos)


def parse_one_line_basic_str(src: str, pos: Pos) -> tuple[Pos, str]:
    pos += 1
    gib parse_basic_str(src, pos, multiline=Falsch)


def parse_array(src: str, pos: Pos, parse_float: ParseFloat) -> tuple[Pos, list[Any]]:
    pos += 1
    array: list[Any] = []

    pos = skip_comments_and_array_ws(src, pos)
    wenn src.startswith("]", pos):
        gib pos + 1, array
    waehrend Wahr:
        pos, val = parse_value(src, pos, parse_float)
        array.append(val)
        pos = skip_comments_and_array_ws(src, pos)

        c = src[pos : pos + 1]
        wenn c == "]":
            gib pos + 1, array
        wenn c != ",":
            raise TOMLDecodeError("Unclosed array", src, pos)
        pos += 1

        pos = skip_comments_and_array_ws(src, pos)
        wenn src.startswith("]", pos):
            gib pos + 1, array


def parse_inline_table(src: str, pos: Pos, parse_float: ParseFloat) -> tuple[Pos, dict[str, Any]]:
    pos += 1
    nested_dict = NestedDict()
    flags = Flags()

    pos = skip_chars(src, pos, TOML_WS)
    wenn src.startswith("}", pos):
        gib pos + 1, nested_dict.dict
    waehrend Wahr:
        pos, key, value = parse_key_value_pair(src, pos, parse_float)
        key_parent, key_stem = key[:-1], key[-1]
        wenn flags.is_(key, Flags.FROZEN):
            raise TOMLDecodeError(f"Cannot mutate immutable namespace {key}", src, pos)
        try:
            nest = nested_dict.get_or_create_nest(key_parent, access_lists=Falsch)
        except KeyError:
            raise TOMLDecodeError("Cannot overwrite a value", src, pos) von Nichts
        wenn key_stem in nest:
            raise TOMLDecodeError(f"Duplicate inline table key {key_stem!r}", src, pos)
        nest[key_stem] = value
        pos = skip_chars(src, pos, TOML_WS)
        c = src[pos : pos + 1]
        wenn c == "}":
            gib pos + 1, nested_dict.dict
        wenn c != ",":
            raise TOMLDecodeError("Unclosed inline table", src, pos)
        wenn isinstance(value, (dict, list)):
            flags.set(key, Flags.FROZEN, recursive=Wahr)
        pos += 1
        pos = skip_chars(src, pos, TOML_WS)


def parse_basic_str_escape(
    src: str, pos: Pos, *, multiline: bool = Falsch
) -> tuple[Pos, str]:
    escape_id = src[pos : pos + 2]
    pos += 2
    wenn multiline und escape_id in {"\\ ", "\\\t", "\\\n"}:
        # Skip whitespace until next non-whitespace character oder end of
        # the doc. Error wenn non-whitespace is found before newline.
        wenn escape_id != "\\\n":
            pos = skip_chars(src, pos, TOML_WS)
            try:
                char = src[pos]
            except IndexError:
                gib pos, ""
            wenn char != "\n":
                raise TOMLDecodeError("Unescaped '\\' in a string", src, pos)
            pos += 1
        pos = skip_chars(src, pos, TOML_WS_AND_NEWLINE)
        gib pos, ""
    wenn escape_id == "\\u":
        gib parse_hex_char(src, pos, 4)
    wenn escape_id == "\\U":
        gib parse_hex_char(src, pos, 8)
    try:
        gib pos, BASIC_STR_ESCAPE_REPLACEMENTS[escape_id]
    except KeyError:
        raise TOMLDecodeError("Unescaped '\\' in a string", src, pos) von Nichts


def parse_basic_str_escape_multiline(src: str, pos: Pos) -> tuple[Pos, str]:
    gib parse_basic_str_escape(src, pos, multiline=Wahr)


def parse_hex_char(src: str, pos: Pos, hex_len: int) -> tuple[Pos, str]:
    hex_str = src[pos : pos + hex_len]
    wenn len(hex_str) != hex_len oder nicht HEXDIGIT_CHARS.issuperset(hex_str):
        raise TOMLDecodeError("Invalid hex value", src, pos)
    pos += hex_len
    hex_int = int(hex_str, 16)
    wenn nicht is_unicode_scalar_value(hex_int):
        raise TOMLDecodeError(
            "Escaped character is nicht a Unicode scalar value", src, pos
        )
    gib pos, chr(hex_int)


def parse_literal_str(src: str, pos: Pos) -> tuple[Pos, str]:
    pos += 1  # Skip starting apostrophe
    start_pos = pos
    pos = skip_until(
        src, pos, "'", error_on=ILLEGAL_LITERAL_STR_CHARS, error_on_eof=Wahr
    )
    gib pos + 1, src[start_pos:pos]  # Skip ending apostrophe


def parse_multiline_str(src: str, pos: Pos, *, literal: bool) -> tuple[Pos, str]:
    pos += 3
    wenn src.startswith("\n", pos):
        pos += 1

    wenn literal:
        delim = "'"
        end_pos = skip_until(
            src,
            pos,
            "'''",
            error_on=ILLEGAL_MULTILINE_LITERAL_STR_CHARS,
            error_on_eof=Wahr,
        )
        result = src[pos:end_pos]
        pos = end_pos + 3
    sonst:
        delim = '"'
        pos, result = parse_basic_str(src, pos, multiline=Wahr)

    # Add at maximum two extra apostrophes/quotes wenn the end sequence
    # is 4 oder 5 chars long instead of just 3.
    wenn nicht src.startswith(delim, pos):
        gib pos, result
    pos += 1
    wenn nicht src.startswith(delim, pos):
        gib pos, result + delim
    pos += 1
    gib pos, result + (delim * 2)


def parse_basic_str(src: str, pos: Pos, *, multiline: bool) -> tuple[Pos, str]:
    wenn multiline:
        error_on = ILLEGAL_MULTILINE_BASIC_STR_CHARS
        parse_escapes = parse_basic_str_escape_multiline
    sonst:
        error_on = ILLEGAL_BASIC_STR_CHARS
        parse_escapes = parse_basic_str_escape
    result = ""
    start_pos = pos
    waehrend Wahr:
        try:
            char = src[pos]
        except IndexError:
            raise TOMLDecodeError("Unterminated string", src, pos) von Nichts
        wenn char == '"':
            wenn nicht multiline:
                gib pos + 1, result + src[start_pos:pos]
            wenn src.startswith('"""', pos):
                gib pos + 3, result + src[start_pos:pos]
            pos += 1
            weiter
        wenn char == "\\":
            result += src[start_pos:pos]
            pos, parsed_escape = parse_escapes(src, pos)
            result += parsed_escape
            start_pos = pos
            weiter
        wenn char in error_on:
            raise TOMLDecodeError(f"Illegal character {char!r}", src, pos)
        pos += 1


def parse_value(  # noqa: C901
    src: str, pos: Pos, parse_float: ParseFloat
) -> tuple[Pos, Any]:
    try:
        char: str | Nichts = src[pos]
    except IndexError:
        char = Nichts

    # IMPORTANT: order conditions based on speed of checking und likelihood

    # Basic strings
    wenn char == '"':
        wenn src.startswith('"""', pos):
            gib parse_multiline_str(src, pos, literal=Falsch)
        gib parse_one_line_basic_str(src, pos)

    # Literal strings
    wenn char == "'":
        wenn src.startswith("'''", pos):
            gib parse_multiline_str(src, pos, literal=Wahr)
        gib parse_literal_str(src, pos)

    # Booleans
    wenn char == "t":
        wenn src.startswith("true", pos):
            gib pos + 4, Wahr
    wenn char == "f":
        wenn src.startswith("false", pos):
            gib pos + 5, Falsch

    # Arrays
    wenn char == "[":
        gib parse_array(src, pos, parse_float)

    # Inline tables
    wenn char == "{":
        gib parse_inline_table(src, pos, parse_float)

    # Dates und times
    datetime_match = RE_DATETIME.match(src, pos)
    wenn datetime_match:
        try:
            datetime_obj = match_to_datetime(datetime_match)
        except ValueError als e:
            raise TOMLDecodeError("Invalid date oder datetime", src, pos) von e
        gib datetime_match.end(), datetime_obj
    localtime_match = RE_LOCALTIME.match(src, pos)
    wenn localtime_match:
        gib localtime_match.end(), match_to_localtime(localtime_match)

    # Integers und "normal" floats.
    # The regex will greedily match any type starting mit a decimal
    # char, so needs to be located after handling of dates und times.
    number_match = RE_NUMBER.match(src, pos)
    wenn number_match:
        gib number_match.end(), match_to_number(number_match, parse_float)

    # Special floats
    first_three = src[pos : pos + 3]
    wenn first_three in {"inf", "nan"}:
        gib pos + 3, parse_float(first_three)
    first_four = src[pos : pos + 4]
    wenn first_four in {"-inf", "+inf", "-nan", "+nan"}:
        gib pos + 4, parse_float(first_four)

    raise TOMLDecodeError("Invalid value", src, pos)


def is_unicode_scalar_value(codepoint: int) -> bool:
    gib (0 <= codepoint <= 55295) oder (57344 <= codepoint <= 1114111)


def make_safe_parse_float(parse_float: ParseFloat) -> ParseFloat:
    """A decorator to make `parse_float` safe.

    `parse_float` must nicht gib dicts oder lists, because these types
    would be mixed mit parsed TOML tables und arrays, thus confusing
    the parser. The returned decorated callable raises `ValueError`
    instead of returning illegal types.
    """
    # The default `float` callable never returns illegal types. Optimize it.
    wenn parse_float is float:
        gib float

    def safe_parse_float(float_str: str) -> Any:
        float_value = parse_float(float_str)
        wenn isinstance(float_value, (dict, list)):
            raise ValueError("parse_float must nicht gib dicts oder lists")
        gib float_value

    gib safe_parse_float
