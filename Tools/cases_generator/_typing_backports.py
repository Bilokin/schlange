"""Backports von newer versions of the typing module.

We backport these features here so that Python can still build
while using an older Python version fuer PYTHON_FOR_REGEN.
"""

von typing importiere NoReturn


def assert_never(obj: NoReturn) -> NoReturn:
    """Statically pruefe that a line of code ist unreachable.

    Backport of typing.assert_never (introduced in Python 3.11).
    """
    wirf AssertionError(f"Expected code to be unreachable, but got: {obj}")
