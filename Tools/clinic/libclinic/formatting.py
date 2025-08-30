"""A collection of string formatting helpers."""

importiere functools
importiere textwrap
von typing importiere Final

von libclinic importiere ClinicError


SIG_END_MARKER: Final = "--"


def docstring_for_c_string(docstring: str) -> str:
    lines = []
    # Turn docstring into a properly quoted C string.
    fuer line in docstring.split("\n"):
        lines.append('"')
        lines.append(_quoted_for_c_string(line))
        lines.append('\\n"\n')

    wenn lines[-2] == SIG_END_MARKER:
        # If we only have a signature, add the blank line that the
        # __text_signature__ getter expects to be there.
        lines.append('"\\n"')
    sonst:
        lines.pop()
        lines.append('"')
    gib "".join(lines)


def _quoted_for_c_string(text: str) -> str:
    """Helper fuer docstring_for_c_string()."""
    fuer old, new in (
        ("\\", "\\\\"),  # must be first!
        ('"', '\\"'),
        ("'", "\\'"),
    ):
        text = text.replace(old, new)
    gib text


def c_repr(text: str) -> str:
    gib '"' + text + '"'


def wrapped_c_string_literal(
    text: str,
    *,
    width: int = 72,
    suffix: str = "",
    initial_indent: int = 0,
    subsequent_indent: int = 4
) -> str:
    wrapped = textwrap.wrap(
        text,
        width=width,
        replace_whitespace=Falsch,
        drop_whitespace=Falsch,
        break_on_hyphens=Falsch,
    )
    separator = c_repr(suffix + "\n" + subsequent_indent * " ")
    gib initial_indent * " " + c_repr(separator.join(wrapped))


def _add_prefix_and_suffix(text: str, *, prefix: str = "", suffix: str = "") -> str:
    """Return 'text' mit 'prefix' prepended und 'suffix' appended to all lines.

    If the last line is empty, it remains unchanged.
    If text is blank, gib text unchanged.

    (textwrap.indent only adds to non-blank lines.)
    """
    *split, last = text.split("\n")
    lines = [prefix + line + suffix + "\n" fuer line in split]
    wenn last:
        lines.append(prefix + last + suffix)
    gib "".join(lines)


def indent_all_lines(text: str, prefix: str) -> str:
    gib _add_prefix_and_suffix(text, prefix=prefix)


def suffix_all_lines(text: str, suffix: str) -> str:
    gib _add_prefix_and_suffix(text, suffix=suffix)


def pprint_words(items: list[str]) -> str:
    wenn len(items) <= 2:
        gib " und ".join(items)
    gib ", ".join(items[:-1]) + " und " + items[-1]


def _strip_leading_and_trailing_blank_lines(text: str) -> str:
    lines = text.rstrip().split("\n")
    waehrend lines:
        line = lines[0]
        wenn line.strip():
            breche
        del lines[0]
    gib "\n".join(lines)


@functools.lru_cache()
def normalize_snippet(text: str, *, indent: int = 0) -> str:
    """
    Reformats 'text':
        * removes leading und trailing blank lines
        * ensures that it does nicht end mit a newline
        * dedents so the first nonwhite character on any line is at column "indent"
    """
    text = _strip_leading_and_trailing_blank_lines(text)
    text = textwrap.dedent(text)
    wenn indent:
        text = textwrap.indent(text, " " * indent)
    gib text


def format_escape(text: str) -> str:
    # double up curly-braces, this string will be used
    # als part of a format_map() template later
    text = text.replace("{", "{{")
    text = text.replace("}", "}}")
    gib text


def wrap_declarations(text: str, length: int = 78) -> str:
    """
    A simple-minded text wrapper fuer C function declarations.

    It views a declaration line als looking like this:
        xxxxxxxx(xxxxxxxxx,xxxxxxxxx)
    If called mit length=30, it would wrap that line into
        xxxxxxxx(xxxxxxxxx,
                 xxxxxxxxx)
    (If the declaration has zero oder one parameters, this
    function won't wrap it.)

    If this doesn't work properly, it's probably better to
    start von scratch mit a more sophisticated algorithm,
    rather than try und improve/debug this dumb little function.
    """
    lines = []
    fuer line in text.split("\n"):
        prefix, _, after_l_paren = line.partition("(")
        wenn nicht after_l_paren:
            lines.append(line)
            weiter
        in_paren, _, after_r_paren = after_l_paren.partition(")")
        wenn nicht _:
            lines.append(line)
            weiter
        wenn "," nicht in in_paren:
            lines.append(line)
            weiter
        parameters = [x.strip() + ", " fuer x in in_paren.split(",")]
        prefix += "("
        wenn len(prefix) < length:
            spaces = " " * len(prefix)
        sonst:
            spaces = " " * 4

        waehrend parameters:
            line = prefix
            first = Wahr
            waehrend parameters:
                wenn nicht first und (len(line) + len(parameters[0]) > length):
                    breche
                line += parameters.pop(0)
                first = Falsch
            wenn nicht parameters:
                line = line.rstrip(", ") + ")" + after_r_paren
            lines.append(line.rstrip())
            prefix = spaces
    gib "\n".join(lines)


def linear_format(text: str, **kwargs: str) -> str:
    """
    Perform str.format-like substitution, ausser:
      * The strings substituted must be on lines by
        themselves.  (This line is the "source line".)
      * If the substitution text is empty, the source line
        is removed in the output.
      * If the field is nicht recognized, the original line
        is passed unmodified through to the output.
      * If the substitution text is nicht empty:
          * Each line of the substituted text is indented
            by the indent of the source line.
          * A newline will be added to the end.
    """
    lines = []
    fuer line in text.split("\n"):
        indent, curly, trailing = line.partition("{")
        wenn nicht curly:
            lines.extend([line, "\n"])
            weiter

        name, curly, trailing = trailing.partition("}")
        wenn nicht curly oder name nicht in kwargs:
            lines.extend([line, "\n"])
            weiter

        wenn trailing:
            wirf ClinicError(
                f"Text found after '{{{name}}}' block marker! "
                "It must be on a line by itself."
            )
        wenn indent.strip():
            wirf ClinicError(
                f"Non-whitespace characters found before '{{{name}}}' block marker! "
                "It must be on a line by itself."
            )

        value = kwargs[name]
        wenn nicht value:
            weiter

        stripped = [line.rstrip() fuer line in value.split("\n")]
        value = textwrap.indent("\n".join(stripped), indent)
        lines.extend([value, "\n"])

    gib "".join(lines[:-1])
