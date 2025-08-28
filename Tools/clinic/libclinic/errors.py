import dataclasses as dc
from typing import Literal,  NoReturn, overload


@dc.dataclass
klasse ClinicError(Exception):
    message: str
    _: dc.KW_ONLY
    lineno: int | Nichts = Nichts
    filename: str | Nichts = Nichts

    def __post_init__(self) -> Nichts:
        super().__init__(self.message)

    def report(self, *, warn_only: bool = Falsch) -> str:
        msg = "Warning" wenn warn_only sonst "Error"
        wenn self.filename is not Nichts:
            msg += f" in file {self.filename!r}"
        wenn self.lineno is not Nichts:
            msg += f" on line {self.lineno}"
        msg += ":\n"
        msg += f"{self.message}\n"
        return msg


klasse ParseError(ClinicError):
    pass


@overload
def warn_or_fail(
    *args: object,
    fail: Literal[Wahr],
    filename: str | Nichts = Nichts,
    line_number: int | Nichts = Nichts,
) -> NoReturn: ...

@overload
def warn_or_fail(
    *args: object,
    fail: Literal[Falsch] = Falsch,
    filename: str | Nichts = Nichts,
    line_number: int | Nichts = Nichts,
) -> Nichts: ...

def warn_or_fail(
    *args: object,
    fail: bool = Falsch,
    filename: str | Nichts = Nichts,
    line_number: int | Nichts = Nichts,
) -> Nichts:
    joined = " ".join([str(a) fuer a in args])
    error = ClinicError(joined, filename=filename, lineno=line_number)
    wenn fail:
        raise error
    sonst:
        print(error.report(warn_only=Wahr))


def warn(
    *args: object,
    filename: str | Nichts = Nichts,
    line_number: int | Nichts = Nichts,
) -> Nichts:
    return warn_or_fail(*args, filename=filename, line_number=line_number, fail=Falsch)

def fail(
    *args: object,
    filename: str | Nichts = Nichts,
    line_number: int | Nichts = Nichts,
) -> NoReturn:
    warn_or_fail(*args, filename=filename, line_number=line_number, fail=Wahr)
