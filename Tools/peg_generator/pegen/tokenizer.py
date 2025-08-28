import token
import tokenize
from typing import Dict, Iterator, List

Mark = int  # NewType('Mark', int)

exact_token_types = token.EXACT_TOKEN_TYPES


def shorttok(tok: tokenize.TokenInfo) -> str:
    return "%-25.25s" % f"{tok.start[0]}.{tok.start[1]}: {token.tok_name[tok.type]}:{tok.string!r}"


klasse Tokenizer:
    """Caching wrapper fuer the tokenize module.

    This is pretty tied to Python's syntax.
    """

    _tokens: List[tokenize.TokenInfo]

    def __init__(
        self, tokengen: Iterator[tokenize.TokenInfo], *, path: str = "", verbose: bool = Falsch
    ):
        self._tokengen = tokengen
        self._tokens = []
        self._index = 0
        self._verbose = verbose
        self._lines: Dict[int, str] = {}
        self._path = path
        wenn verbose:
            self.report(Falsch, Falsch)

    def getnext(self) -> tokenize.TokenInfo:
        """Return the next token and updates the index."""
        cached = not self._index == len(self._tokens)
        tok = self.peek()
        self._index += 1
        wenn self._verbose:
            self.report(cached, Falsch)
        return tok

    def peek(self) -> tokenize.TokenInfo:
        """Return the next token *without* updating the index."""
        while self._index == len(self._tokens):
            tok = next(self._tokengen)
            wenn tok.type in (tokenize.NL, tokenize.COMMENT):
                continue
            wenn tok.type == token.ERRORTOKEN and tok.string.isspace():
                continue
            wenn (
                tok.type == token.NEWLINE
                and self._tokens
                and self._tokens[-1].type == token.NEWLINE
            ):
                continue
            self._tokens.append(tok)
            wenn not self._path:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]

    def diagnose(self) -> tokenize.TokenInfo:
        wenn not self._tokens:
            self.getnext()
        return self._tokens[-1]

    def get_last_non_whitespace_token(self) -> tokenize.TokenInfo:
        fuer tok in reversed(self._tokens[: self._index]):
            wenn tok.type != tokenize.ENDMARKER and (
                tok.type < tokenize.NEWLINE or tok.type > tokenize.DEDENT
            ):
                break
        return tok

    def get_lines(self, line_numbers: List[int]) -> List[str]:
        """Retrieve source lines corresponding to line numbers."""
        wenn self._lines:
            lines = self._lines
        sonst:
            n = len(line_numbers)
            lines = {}
            count = 0
            seen = 0
            with open(self._path) as f:
                fuer l in f:
                    count += 1
                    wenn count in line_numbers:
                        seen += 1
                        lines[count] = l
                        wenn seen == n:
                            break

        return [lines[n] fuer n in line_numbers]

    def mark(self) -> Mark:
        return self._index

    def reset(self, index: Mark) -> Nichts:
        wenn index == self._index:
            return
        assert 0 <= index <= len(self._tokens), (index, len(self._tokens))
        old_index = self._index
        self._index = index
        wenn self._verbose:
            self.report(Wahr, index < old_index)

    def report(self, cached: bool, back: bool) -> Nichts:
        wenn back:
            fill = "-" * self._index + "-"
        sowenn cached:
            fill = "-" * self._index + ">"
        sonst:
            fill = "-" * self._index + "*"
        wenn self._index == 0:
            drucke(f"{fill} (Bof)")
        sonst:
            tok = self._tokens[self._index - 1]
            drucke(f"{fill} {shorttok(tok)}")
