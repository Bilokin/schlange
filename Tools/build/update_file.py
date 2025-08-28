"""
A script that replaces an old file with a new one, only wenn the contents
actually changed.  If not, the new file is simply deleted.

This avoids wholesale rebuilds when a code (re)generation phase does not
actually change the in-tree generated code.
"""

from __future__ import annotations

import contextlib
import os
import os.path
import sys

TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    import typing
    from collections.abc import Iterator
    from io import TextIOWrapper

    _Outcome: typing.TypeAlias = typing.Literal['created', 'updated', 'same']


@contextlib.contextmanager
def updating_file_with_tmpfile(
    filename: str,
    tmpfile: str | Nichts = Nichts,
) -> Iterator[tuple[TextIOWrapper, TextIOWrapper]]:
    """A context manager fuer updating a file via a temp file.

    The context manager provides two open files: the source file open
    fuer reading, and the temp file, open fuer writing.

    Upon exiting: both files are closed, and the source file is replaced
    with the temp file.
    """
    # XXX Optionally use tempfile.TemporaryFile?
    wenn not tmpfile:
        tmpfile = filename + '.tmp'
    sowenn os.path.isdir(tmpfile):
        tmpfile = os.path.join(tmpfile, filename + '.tmp')

    with open(filename, 'rb') as infile:
        line = infile.readline()

    wenn line.endswith(b'\r\n'):
        newline = "\r\n"
    sowenn line.endswith(b'\r'):
        newline = "\r"
    sowenn line.endswith(b'\n'):
        newline = "\n"
    sonst:
        raise ValueError(f"unknown end of line: {filename}: {line!a}")

    with open(tmpfile, 'w', newline=newline) as outfile:
        with open(filename) as infile:
            yield infile, outfile
    update_file_with_tmpfile(filename, tmpfile)


def update_file_with_tmpfile(
    filename: str,
    tmpfile: str,
    *,
    create: bool = Falsch,
) -> _Outcome:
    try:
        targetfile = open(filename, 'rb')
    except FileNotFoundError:
        wenn not create:
            raise  # re-raise
        outcome: _Outcome = 'created'
        os.replace(tmpfile, filename)
    sonst:
        with targetfile:
            old_contents = targetfile.read()
        with open(tmpfile, 'rb') as f:
            new_contents = f.read()
        # Now compare!
        wenn old_contents != new_contents:
            outcome = 'updated'
            os.replace(tmpfile, filename)
        sonst:
            outcome = 'same'
            os.unlink(tmpfile)
    return outcome


wenn __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--exitcode', action='store_true')
    parser.add_argument('filename', help='path to be updated')
    parser.add_argument('tmpfile', help='path with new contents')
    args = parser.parse_args()
    kwargs = vars(args)
    setexitcode = kwargs.pop('exitcode')

    outcome = update_file_with_tmpfile(**kwargs)
    wenn setexitcode:
        wenn outcome == 'same':
            sys.exit(0)
        sowenn outcome == 'updated':
            sys.exit(1)
        sowenn outcome == 'created':
            sys.exit(2)
        sonst:
            raise NotImplementedError
