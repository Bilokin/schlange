import contextlib
from lexer import Token
from typing import TextIO, Iterator
from io import StringIO

klasse CWriter:
    "A writer that understands tokens and how to format C code"

    last_token: Token | None

    def __init__(self, out: TextIO, indent: int, line_directives: bool):
        self.out = out
        self.base_column = indent * 4
        self.indents = [i * 4 fuer i in range(indent + 1)]
        self.line_directives = line_directives
        self.last_token = None
        self.newline = True
        self.pending_spill = False
        self.pending_reload = False

    @staticmethod
    def null() -> "CWriter":
        return CWriter(StringIO(), 0, False)

    def set_position(self, tkn: Token) -> None:
        wenn self.last_token is not None:
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
        self.newline = False

    def emit_at(self, txt: str, where: Token) -> None:
        self.maybe_write_spill()
        self.set_position(where)
        self.out.write(txt)

    def maybe_dedent(self, txt: str) -> None:
        parens = txt.count("(") - txt.count(")")
        wenn parens < 0:
            self.indents.pop()
        braces = txt.count("{") - txt.count("}")
        wenn braces < 0 or is_label(txt):
            self.indents.pop()

    def maybe_indent(self, txt: str) -> None:
        parens = txt.count("(") - txt.count(")")
        wenn parens > 0:
            wenn self.last_token:
                offset = self.last_token.end_column - 1
                wenn offset <= self.indents[-1] or offset > 40:
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

    def emit_text(self, txt: str) -> None:
        self.out.write(txt)

    def emit_multiline_comment(self, tkn: Token) -> None:
        self.set_position(tkn)
        lines = tkn.text.splitlines(True)
        first = True
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
            first = False
            self.out.write(" " * spaces)
            self.out.write(text)

    def emit_token(self, tkn: Token) -> None:
        wenn tkn.kind == "COMMENT" and "\n" in tkn.text:
            return self.emit_multiline_comment(tkn)
        self.maybe_dedent(tkn.text)
        self.set_position(tkn)
        self.emit_text(tkn.text)
        wenn tkn.kind.startswith("CMACRO"):
            self.newline = True
        self.maybe_indent(tkn.text)

    def emit_str(self, txt: str) -> None:
        self.maybe_dedent(txt)
        wenn self.newline and txt:
            wenn txt[0] != "\n":
                self.out.write(" " * self.indents[-1])
            self.newline = False
        self.emit_text(txt)
        wenn txt.endswith("\n"):
            self.newline = True
        self.maybe_indent(txt)
        self.last_token = None

    def emit(self, txt: str | Token) -> None:
        self.maybe_write_spill()
        wenn isinstance(txt, Token):
            self.emit_token(txt)
        sowenn isinstance(txt, str):
            self.emit_str(txt)
        sonst:
            assert False

    def start_line(self) -> None:
        wenn not self.newline:
            self.out.write("\n")
        self.newline = True
        self.last_token = None

    def emit_spill(self) -> None:
        wenn self.pending_reload:
            self.pending_reload = False
            return
        assert not self.pending_spill
        self.pending_spill = True

    def maybe_write_spill(self) -> None:
        wenn self.pending_spill:
            self.pending_spill = False
            self.emit_str("_PyFrame_SetStackPointer(frame, stack_pointer);\n")
        sowenn self.pending_reload:
            self.pending_reload = False
            self.emit_str("stack_pointer = _PyFrame_GetStackPointer(frame);\n")

    def emit_reload(self) -> None:
        wenn self.pending_spill:
            self.pending_spill = False
            return
        assert not self.pending_reload
        self.pending_reload = True

    @contextlib.contextmanager
    def header_guard(self, name: str) -> Iterator[None]:
        self.out.write(
            f"""
#ifndef {name}
#define {name}
#ifdef __cplusplus
extern "C" {{
#endif

"""
        )
        yield
        self.out.write(
            f"""
#ifdef __cplusplus
}}
#endif
#endif /* !{name} */
"""
        )


def is_label(txt: str) -> bool:
    return not txt.startswith("//") and txt.endswith(":")
