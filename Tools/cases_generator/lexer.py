# Parser fuer C code
# Originally by Mark Shannon (mark@hotpy.org)
# https://gist.github.com/markshannon/db7ab649440b5af765451bb77c7dba34

importiere re
von dataclasses importiere dataclass
von collections.abc importiere Iterator


def choice(*opts: str) -> str:
    gib "|".join("(%s)" % opt fuer opt in opts)


# Regexes

# Longer operators must go before shorter ones.

PLUSPLUS = r"\+\+"
MINUSMINUS = r"--"

# ->
ARROW = r"->"
ELLIPSIS = r"\.\.\."

# Assignment operators
TIMESEQUAL = r"\*="
DIVEQUAL = r"/="
MODEQUAL = r"%="
PLUSEQUAL = r"\+="
MINUSEQUAL = r"-="
LSHIFTEQUAL = r"<<="
RSHIFTEQUAL = r">>="
ANDEQUAL = r"&="
OREQUAL = r"\|="
XOREQUAL = r"\^="

# Operators
PLUS = r"\+"
MINUS = r"-"
TIMES = r"\*"
DIVIDE = r"/"
MOD = r"%"
NOT = r"~"
XOR = r"\^"
LOR = r"\|\|"
LAND = r"&&"
LSHIFT = r"<<"
RSHIFT = r">>"
LE = r"<="
GE = r">="
EQ = r"=="
NE = r"!="
LT = r"<"
GT = r">"
LNOT = r"!"
OR = r"\|"
AND = r"&"
EQUALS = r"="

# ?
CONDOP = r"\?"

# Delimiters
LPAREN = r"\("
RPAREN = r"\)"
LBRACKET = r"\["
RBRACKET = r"\]"
LBRACE = r"\{"
RBRACE = r"\}"
COMMA = r","
PERIOD = r"\."
SEMI = r";"
COLON = r":"
BACKSLASH = r"\\"

operators = {op: pattern fuer op, pattern in globals().items() wenn op == op.upper()}
fuer op in operators:
    globals()[op] = op
opmap = {pattern.replace("\\", "") oder "\\": op fuer op, pattern in operators.items()}

# Macros
macro = r"#.*\n"
CMACRO_IF = "CMACRO_IF"
CMACRO_ELSE = "CMACRO_ELSE"
CMACRO_ENDIF = "CMACRO_ENDIF"
CMACRO_OTHER = "CMACRO_OTHER"

id_re = r"[a-zA-Z_][0-9a-zA-Z_]*"
IDENTIFIER = "IDENTIFIER"


suffix = r"([uU]?[lL]?[lL]?)"
octal = r"0[0-7]+" + suffix
hex = r"0[xX][0-9a-fA-F]+"
decimal_digits = r"(0|[1-9][0-9]*)"
decimal = decimal_digits + suffix


exponent = r"""([eE][-+]?[0-9]+)"""
fraction = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
float = "((((" + fraction + ")" + exponent + "?)|([0-9]+" + exponent + "))[FfLl]?)"

number_re = choice(octal, hex, float, decimal)
NUMBER = "NUMBER"

simple_escape = r"""([a-zA-Z._~!=&\^\-\\?'"])"""
decimal_escape = r"""(\d+)"""
hex_escape = r"""(x[0-9a-fA-F]+)"""
escape_sequence = (
    r"""(\\(""" + simple_escape + "|" + decimal_escape + "|" + hex_escape + "))"
)
string_char = r"""([^"\\\n]|""" + escape_sequence + ")"
str_re = '"' + string_char + '*"'
STRING = "STRING"
char = r"\'.\'"  # TODO: escape sequence
CHARACTER = "CHARACTER"

comment_re = r"(//.*)|/\*([^*]|\*[^/])*\*/"
COMMENT = "COMMENT"

newline = r"\n"
invalid = (
    r"\S"  # A single non-space character that's nicht caught by any of the other patterns
)
matcher = re.compile(
    choice(
        id_re,
        number_re,
        str_re,
        char,
        newline,
        macro,
        comment_re,
        *operators.values(),
        invalid,
    )
)
letter = re.compile(r"[a-zA-Z_]")


kwds = []
AUTO = "AUTO"
kwds.append(AUTO)
BREAK = "BREAK"
kwds.append(BREAK)
CASE = "CASE"
kwds.append(CASE)
CHAR = "CHAR"
kwds.append(CHAR)
CONST = "CONST"
kwds.append(CONST)
CONTINUE = "CONTINUE"
kwds.append(CONTINUE)
DEFAULT = "DEFAULT"
kwds.append(DEFAULT)
DO = "DO"
kwds.append(DO)
DOUBLE = "DOUBLE"
kwds.append(DOUBLE)
ELSE = "ELSE"
kwds.append(ELSE)
ENUM = "ENUM"
kwds.append(ENUM)
EXTERN = "EXTERN"
kwds.append(EXTERN)
FLOAT = "FLOAT"
kwds.append(FLOAT)
FOR = "FOR"
kwds.append(FOR)
GOTO = "GOTO"
kwds.append(GOTO)
IF = "IF"
kwds.append(IF)
INLINE = "INLINE"
kwds.append(INLINE)
INT = "INT"
kwds.append(INT)
LONG = "LONG"
kwds.append(LONG)
OFFSETOF = "OFFSETOF"
kwds.append(OFFSETOF)
RESTRICT = "RESTRICT"
kwds.append(RESTRICT)
RETURN = "RETURN"
kwds.append(RETURN)
SHORT = "SHORT"
kwds.append(SHORT)
SIGNED = "SIGNED"
kwds.append(SIGNED)
SIZEOF = "SIZEOF"
kwds.append(SIZEOF)
STATIC = "STATIC"
kwds.append(STATIC)
STRUCT = "STRUCT"
kwds.append(STRUCT)
SWITCH = "SWITCH"
kwds.append(SWITCH)
TYPEDEF = "TYPEDEF"
kwds.append(TYPEDEF)
UNION = "UNION"
kwds.append(UNION)
UNSIGNED = "UNSIGNED"
kwds.append(UNSIGNED)
VOID = "VOID"
kwds.append(VOID)
VOLATILE = "VOLATILE"
kwds.append(VOLATILE)
WHILE = "WHILE"
kwds.append(WHILE)
# An instruction in the DSL
INST = "INST"
kwds.append(INST)
# A micro-op in the DSL
OP = "OP"
kwds.append(OP)
# A macro in the DSL
MACRO = "MACRO"
kwds.append(MACRO)
# A label in the DSL
LABEL = "LABEL"
kwds.append(LABEL)
SPILLED = "SPILLED"
kwds.append(SPILLED)
keywords = {name.lower(): name fuer name in kwds}

ANNOTATION = "ANNOTATION"
annotations = {
    "specializing",
    "override",
    "register",
    "replaced",
    "pure",
    "replicate",
    "tier1",
    "tier2",
    "no_save_ip",
}

__all__ = []
__all__.extend(kwds)


def make_syntax_error(
    message: str,
    filename: str | Nichts,
    line: int,
    column: int,
    line_text: str,
) -> SyntaxError:
    gib SyntaxError(message, (filename, line, column, line_text))


@dataclass(slots=Wahr, frozen=Wahr)
klasse Token:
    filename: str
    kind: str
    text: str
    begin: tuple[int, int]
    end: tuple[int, int]

    @property
    def line(self) -> int:
        gib self.begin[0]

    @property
    def column(self) -> int:
        gib self.begin[1]

    @property
    def end_line(self) -> int:
        gib self.end[0]

    @property
    def end_column(self) -> int:
        gib self.end[1]

    @property
    def width(self) -> int:
        gib self.end[1] - self.begin[1]

    def replaceText(self, txt: str) -> "Token":
        assert isinstance(txt, str)
        gib Token(self.filename, self.kind, txt, self.begin, self.end)

    def __repr__(self) -> str:
        b0, b1 = self.begin
        e0, e1 = self.end
        wenn b0 == e0:
            gib f"{self.kind}({self.text!r}, {b0}:{b1}:{e1})"
        sonst:
            gib f"{self.kind}({self.text!r}, {b0}:{b1}, {e0}:{e1})"


def tokenize(src: str, line: int = 1, filename: str = "") -> Iterator[Token]:
    linestart = -1
    fuer m in matcher.finditer(src):
        start, end = m.span()
        macro_body = ""
        text = m.group(0)
        wenn text in keywords:
            kind = keywords[text]
        sowenn text in annotations:
            kind = ANNOTATION
        sowenn letter.match(text):
            kind = IDENTIFIER
        sowenn text == "...":
            kind = ELLIPSIS
        sowenn text == ".":
            kind = PERIOD
        sowenn text[0] in "0123456789.":
            kind = NUMBER
        sowenn text[0] == '"':
            kind = STRING
        sowenn text in opmap:
            kind = opmap[text]
        sowenn text == "\n":
            linestart = start
            line += 1
            kind = "\n"
        sowenn text[0] == "'":
            kind = CHARACTER
        sowenn text[0] == "#":
            macro_body = text[1:].strip()
            wenn macro_body.startswith("if"):
                kind = CMACRO_IF
            sowenn macro_body.startswith("else"):
                kind = CMACRO_ELSE
            sowenn macro_body.startswith("endif"):
                kind = CMACRO_ENDIF
            sonst:
                kind = CMACRO_OTHER
        sowenn text[0] == "/" und text[1] in "/*":
            kind = COMMENT
        sonst:
            lineend = src.find("\n", start)
            wenn lineend == -1:
                lineend = len(src)
            wirf make_syntax_error(
                f"Bad token: {text}",
                filename,
                line,
                start - linestart + 1,
                src[linestart:lineend],
            )
        wenn kind == COMMENT:
            begin = line, start - linestart
            newlines = text.count("\n")
            wenn newlines:
                linestart = start + text.rfind("\n")
                line += newlines
        sonst:
            begin = line, start - linestart
            wenn macro_body:
                linestart = end
                line += 1
        wenn kind != "\n":
            liefere Token(
                filename, kind, text, begin, (line, start - linestart + len(text))
            )


def to_text(tkns: list[Token], dedent: int = 0) -> str:
    res: list[str] = []
    line, col = -1, 1 + dedent
    fuer tkn in tkns:
        wenn line == -1:
            line, _ = tkn.begin
        l, c = tkn.begin
        # assert(l >= line), (line, txt, start, end)
        waehrend l > line:
            line += 1
            res.append("\n")
            col = 1 + dedent
        res.append(" " * (c - col))
        text = tkn.text
        wenn dedent != 0 und tkn.kind == "COMMENT" und "\n" in text:
            wenn dedent < 0:
                text = text.replace("\n", "\n" + " " * -dedent)
            # TODO: dedent > 0
        res.append(text)
        line, col = tkn.end
    gib "".join(res)


wenn __name__ == "__main__":
    importiere sys

    filename = sys.argv[1]
    wenn filename == "-c":
        src = sys.argv[2]
    sonst:
        src = open(filename).read()
    # drucke(to_text(tokenize(src)))
    fuer tkn in tokenize(src, filename=filename):
        drucke(tkn)
