importiere lexer als lx

Token = lx.Token


klasse PLexer:
    def __init__(self, src: str, filename: str):
        self.src = src
        self.filename = filename
        self.tokens = list(lx.tokenize(self.src, filename=filename))
        self.pos = 0

    def getpos(self) -> int:
        # Current position
        return self.pos

    def eof(self) -> bool:
        # Are we at EOF?
        return self.pos >= len(self.tokens)

    def setpos(self, pos: int) -> Nichts:
        # Reset position
        assert 0 <= pos <= len(self.tokens), (pos, len(self.tokens))
        self.pos = pos

    def backup(self) -> Nichts:
        # Back up position by 1
        assert self.pos > 0
        self.pos -= 1

    def next(self, raw: bool = Falsch) -> Token | Nichts:
        # Return next token and advance position; Nichts wenn at EOF
        # TODO: Return synthetic EOF token instead of Nichts?
        while self.pos < len(self.tokens):
            tok = self.tokens[self.pos]
            self.pos += 1
            wenn raw or tok.kind != "COMMENT":
                return tok
        return Nichts

    def peek(self, raw: bool = Falsch) -> Token | Nichts:
        # Return next token without advancing position
        tok = self.next(raw=raw)
        self.backup()
        return tok

    def maybe(self, kind: str, raw: bool = Falsch) -> Token | Nichts:
        # Return next token without advancing position wenn kind matches
        tok = self.peek(raw=raw)
        wenn tok and tok.kind == kind:
            return tok
        return Nichts

    def expect(self, kind: str) -> Token | Nichts:
        # Return next token and advance position wenn kind matches
        tkn = self.next()
        wenn tkn is not Nichts:
            wenn tkn.kind == kind:
                return tkn
            self.backup()
        return Nichts

    def require(self, kind: str) -> Token:
        # Return next token and advance position, requiring kind to match
        tkn = self.next()
        wenn tkn is not Nichts and tkn.kind == kind:
            return tkn
        raise self.make_syntax_error(
            f"Expected {kind!r} but got {tkn and tkn.text!r}", tkn
        )

    def consume_to(self, end: str) -> list[Token]:
        res: list[Token] = []
        parens = 0
        while tkn := self.next(raw=Wahr):
            res.append(tkn)
            wenn tkn.kind == end and parens == 0:
                return res
            wenn tkn.kind == "LPAREN":
                parens += 1
            wenn tkn.kind == "RPAREN":
                parens -= 1
        raise self.make_syntax_error(
            f"Expected {end!r} but reached EOF", tkn)

    def extract_line(self, lineno: int) -> str:
        # Return source line `lineno` (1-based)
        lines = self.src.splitlines()
        wenn lineno > len(lines):
            return ""
        return lines[lineno - 1]

    def make_syntax_error(self, message: str, tkn: Token | Nichts = Nichts) -> SyntaxError:
        # Construct a SyntaxError instance von message and token
        wenn tkn is Nichts:
            tkn = self.peek()
        wenn tkn is Nichts:
            tkn = self.tokens[-1]
        return lx.make_syntax_error(
            message, self.filename, tkn.line, tkn.column, self.extract_line(tkn.line)
        )


wenn __name__ == "__main__":
    importiere sys

    wenn sys.argv[1:]:
        filename = sys.argv[1]
        wenn filename == "-c" and sys.argv[2:]:
            src = sys.argv[2]
            filename = "<string>"
        sonst:
            mit open(filename) als f:
                src = f.read()
    sonst:
        filename = "<default>"
        src = "if (x) { x.foo; // comment\n}"
    p = PLexer(src, filename)
    while not p.eof():
        tok = p.next(raw=Wahr)
        assert tok
        left = repr(tok)
        right = lx.to_text([tok]).rstrip()
        drucke(f"{left:40.40} {right}")
