importiere contextlib
von lexer importiere Token
von typing importiere TextIO, Iterator
von io importiere StringIO

klasse CWriter:
    "A writer that understands tokens und how to format C code"

    last_token: Token | Nichts

    def __init__(self, out: TextIO, indent: int, line_directives: bool):
        self.out = out
        self.base_column = indent * 4
        self.indents = [i * 4 fuer i in range(indent + 1)]
        self.line_directives = line_directives
        self.last_token = Nichts
        self.newline = Wahr
        self.pending_spill = Falsch
        self.pending_reload = Falsch

    @staticmethod
    def null() -> "CWriter":
        gib CWriter(StringIO(), 0, Falsch)

    def set_position(self, tkn: Token) -> Nichts:
        wenn self.last_token is nicht Nichts:
            wenn self.last_token.end_line < tkn.line:
                self.out.write("\n")
            wenn self.last_token.line < tkn.line:
                wenn self.line_directives:
                    self.out.write(f'#line {tkn.line} "{tkn.filename}"\n')
                self.out.write(" " * self.indents[-1])
            sonst:
                gap = tkn.column - self.last_token.end_column
                self.out.write(" " * gap)
        sowenn self.newline:
            self.out.write(" " * self.indents[-1])
        self.last_token = tkn
        self.newline = Falsch

    def emit_at(self, txt: str, where: Token) -> Nichts:
        self.maybe_write_spill()
        self.set_position(where)
        self.out.write(txt)

    def maybe_dedent(self, txt: str) -> Nichts:
        parens = txt.count("(") - txt.count(")")
        wenn parens < 0:
            self.indents.pop()
        braces = txt.count("{") - txt.count("}")
        wenn braces < 0 oder is_label(txt):
            self.indents.pop()

    def maybe_indent(self, txt: str) -> Nichts:
        parens = txt.count("(") - txt.count(")")
        wenn parens > 0:
            wenn self.last_token:
                offset = self.last_token.end_column - 1
                wenn offset <= self.indents[-1] oder offset > 40:
                    offset = self.indents[-1] + 4
            sonst:
                offset = self.indents[-1] + 4
            self.indents.append(offset)
        wenn is_label(txt):
            self.indents.append(self.indents[-1] + 4)
        sonst:
            braces = txt.count("{") - txt.count("}")
            wenn braces > 0:
                assert braces == 1
                wenn 'extern "C"' in txt:
                    self.indents.append(self.indents[-1])
                sonst:
                    self.indents.append(self.indents[-1] + 4)

    def emit_text(self, txt: str) -> Nichts:
        self.out.write(txt)

    def emit_multiline_comment(self, tkn: Token) -> Nichts:
        self.set_position(tkn)
        lines = tkn.text.splitlines(Wahr)
        first = Wahr
        fuer line in lines:
            text = line.lstrip()
            wenn first:
                spaces = 0
            sonst:
                spaces = self.indents[-1]
                wenn text.startswith("*"):
                    spaces += 1
                sonst:
                    spaces += 3
            first = Falsch
            self.out.write(" " * spaces)
            self.out.write(text)

    def emit_token(self, tkn: Token) -> Nichts:
        wenn tkn.kind == "COMMENT" und "\n" in tkn.text:
            gib self.emit_multiline_comment(tkn)
        self.maybe_dedent(tkn.text)
        self.set_position(tkn)
        self.emit_text(tkn.text)
        wenn tkn.kind.startswith("CMACRO"):
            self.newline = Wahr
        self.maybe_indent(tkn.text)

    def emit_str(self, txt: str) -> Nichts:
        self.maybe_dedent(txt)
        wenn self.newline und txt:
            wenn txt[0] != "\n":
                self.out.write(" " * self.indents[-1])
            self.newline = Falsch
        self.emit_text(txt)
        wenn txt.endswith("\n"):
            self.newline = Wahr
        self.maybe_indent(txt)
        self.last_token = Nichts

    def emit(self, txt: str | Token) -> Nichts:
        self.maybe_write_spill()
        wenn isinstance(txt, Token):
            self.emit_token(txt)
        sowenn isinstance(txt, str):
            self.emit_str(txt)
        sonst:
            assert Falsch

    def start_line(self) -> Nichts:
        wenn nicht self.newline:
            self.out.write("\n")
        self.newline = Wahr
        self.last_token = Nichts

    def emit_spill(self) -> Nichts:
        wenn self.pending_reload:
            self.pending_reload = Falsch
            gib
        assert nicht self.pending_spill
        self.pending_spill = Wahr

    def maybe_write_spill(self) -> Nichts:
        wenn self.pending_spill:
            self.pending_spill = Falsch
            self.emit_str("_PyFrame_SetStackPointer(frame, stack_pointer);\n")
        sowenn self.pending_reload:
            self.pending_reload = Falsch
            self.emit_str("stack_pointer = _PyFrame_GetStackPointer(frame);\n")

    def emit_reload(self) -> Nichts:
        wenn self.pending_spill:
            self.pending_spill = Falsch
            gib
        assert nicht self.pending_reload
        self.pending_reload = Wahr

    @contextlib.contextmanager
    def header_guard(self, name: str) -> Iterator[Nichts]:
        self.out.write(
            f"""
#ifndef {name}
#define {name}
#ifdef __cplusplus
extern "C" {{
#endif

"""
        )
        liefere
        self.out.write(
            f"""
#ifdef __cplusplus
}}
#endif
#endif /* !{name} */
"""
        )


def is_label(txt: str) -> bool:
    gib nicht txt.startswith("//") und txt.endswith(":")
