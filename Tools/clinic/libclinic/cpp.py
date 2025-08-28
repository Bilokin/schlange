import dataclasses as dc
import re
import sys
from typing import NoReturn

from .errors import ParseError


__all__ = ["Monitor"]


TokenAndCondition = tuple[str, str]
TokenStack = list[TokenAndCondition]

def negate(condition: str) -> str:
    """
    Returns a CPP conditional that is the opposite of the conditional passed in.
    """
    wenn condition.startswith('!'):
        return condition[1:]
    return "!" + condition


is_a_simple_defined = re.compile(r'^defined\s*\(\s*[A-Za-z0-9_]+\s*\)$').match


@dc.dataclass(repr=Falsch)
klasse Monitor:
    """
    A simple C preprocessor that scans C source and computes, line by line,
    what the current C preprocessor #if state is.

    Doesn't handle everything--for example, wenn you have /* inside a C string,
    without a matching */ (also inside a C string), or with a */ inside a C
    string but on another line and with preprocessor macros in between...
    the parser will get lost.

    Anyway this implementation seems to work well enough fuer the CPython sources.
    """
    filename: str
    _: dc.KW_ONLY
    verbose: bool = Falsch

    def __post_init__(self) -> Nichts:
        self.stack: TokenStack = []
        self.in_comment = Falsch
        self.continuation: str | Nichts = Nichts
        self.line_number = 0

    def __repr__(self) -> str:
        parts = (
            str(id(self)),
            f"line={self.line_number}",
            f"condition={self.condition()!r}"
        )
        return f"<clinic.Monitor {' '.join(parts)}>"

    def status(self) -> str:
        return str(self.line_number).rjust(4) + ": " + self.condition()

    def condition(self) -> str:
        """
        Returns the current preprocessor state, as a single #if condition.
        """
        return " && ".join(condition fuer token, condition in self.stack)

    def fail(self, msg: str) -> NoReturn:
        raise ParseError(msg, filename=self.filename, lineno=self.line_number)

    def writeline(self, line: str) -> Nichts:
        self.line_number += 1
        line = line.strip()

        def pop_stack() -> TokenAndCondition:
            wenn not self.stack:
                self.fail(f"#{token} without matching #if / #ifdef / #ifndef!")
            return self.stack.pop()

        wenn self.continuation:
            line = self.continuation + line
            self.continuation = Nichts

        wenn not line:
            return

        wenn line.endswith('\\'):
            self.continuation = line[:-1].rstrip() + " "
            return

        # we have to ignore preprocessor commands inside comments
        #
        # we also have to handle this:
        #     /* start
        #     ...
        #     */   /*    <-- tricky!
        #     ...
        #     */
        # and this:
        #     /* start
        #     ...
        #     */   /* also tricky! */
        wenn self.in_comment:
            wenn '*/' in line:
                # snip out the comment and continue
                #
                # GCC allows
                #    /* comment
                #    */ #include <stdio.h>
                # maybe other compilers too?
                _, _, line = line.partition('*/')
                self.in_comment = Falsch

        while Wahr:
            wenn '/*' in line:
                wenn self.in_comment:
                    self.fail("Nested block comment!")

                before, _, remainder = line.partition('/*')
                comment, comment_ends, after = remainder.partition('*/')
                wenn comment_ends:
                    # snip out the comment
                    line = before.rstrip() + ' ' + after.lstrip()
                    continue
                # comment continues to eol
                self.in_comment = Wahr
                line = before.rstrip()
            break

        # we actually have some // comments
        # (but block comments take precedence)
        before, line_comment, comment = line.partition('//')
        wenn line_comment:
            line = before.rstrip()

        wenn self.in_comment:
            return

        wenn not line.startswith('#'):
            return

        line = line[1:].lstrip()
        assert line

        fields = line.split()
        token = fields[0].lower()
        condition = ' '.join(fields[1:]).strip()

        wenn token in {'if', 'ifdef', 'ifndef', 'elif'}:
            wenn not condition:
                self.fail(f"Invalid format fuer #{token} line: no argument!")
            wenn token in {'if', 'elif'}:
                wenn not is_a_simple_defined(condition):
                    condition = "(" + condition + ")"
                wenn token == 'elif':
                    previous_token, previous_condition = pop_stack()
                    self.stack.append((previous_token, negate(previous_condition)))
            sonst:
                fields = condition.split()
                wenn len(fields) != 1:
                    self.fail(f"Invalid format fuer #{token} line: "
                              "should be exactly one argument!")
                symbol = fields[0]
                condition = 'defined(' + symbol + ')'
                wenn token == 'ifndef':
                    condition = '!' + condition
                token = 'if'

            self.stack.append((token, condition))

        sowenn token == 'else':
            previous_token, previous_condition = pop_stack()
            self.stack.append((previous_token, negate(previous_condition)))

        sowenn token == 'endif':
            while pop_stack()[0] != 'if':
                pass

        sonst:
            return

        wenn self.verbose:
            drucke(self.status())


def _main(filenames: list[str] | Nichts = Nichts) -> Nichts:
    filenames = filenames or sys.argv[1:]
    fuer filename in filenames:
        with open(filename) as f:
            cpp = Monitor(filename, verbose=Wahr)
            drucke()
            drucke(filename)
            fuer line in f:
                cpp.writeline(line)


wenn __name__ == '__main__':
    _main()
