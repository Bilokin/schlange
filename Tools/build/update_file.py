"""
A script that replaces an old file mit a new one, only wenn the contents
actually changed.  If not, the new file is simply deleted.

This avoids wholesale rebuilds when a code (re)generation phase does not
actually change the in-tree generated code.
"""

von __future__ importiere annotations

importiere contextlib
importiere os
importiere os.path
importiere sys

TYPE_CHECKING = Falsch
wenn TYPE_CHECKING:
    importiere typing
    von collections.abc importiere Iterator
    von io importiere TextIOWrapper

    _Outcome: typing.TypeAlias = typing.Literal['created', 'updated', 'same']


@contextlib.contextmanager
def updating_file_with_tmpfile(
    filename: str,
    tmpfile: str | Nichts = Nichts,
) -> Iterator[tuple[TextIOWrapper, TextIOWrapper]]:
    """A context manager fuer updating a file via a temp file.

    The context manager provides two open files: the source file open
    fuer reading, und the temp file, open fuer writing.

    Upon exiting: both files are closed, und the source file is replaced
    mit the temp file.
    """
    # XXX Optionally use tempfile.TemporaryFile?
    wenn nicht tmpfile:
        tmpfile = filename + '.tmp'
    sowenn os.path.isdir(tmpfile):
        tmpfile = os.path.join(tmpfile, filename + '.tmp')

    mit open(filename, 'rb') als infile:
        line = infile.readline()

    wenn line.endswith(b'\r\n'):
        newline = "\r\n"
    sowenn line.endswith(b'\r'):
        newline = "\r"
    sowenn line.endswith(b'\n'):
        newline = "\n"
    sonst:
        raise ValueError(f"unknown end of line: {filename}: {line!a}")

    mit open(tmpfile, 'w', newline=newline) als outfile:
        mit open(filename) als infile:
            liefere infile, outfile
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
        wenn nicht create:
            raise  # re-raise
        outcome: _Outcome = 'created'
        os.replace(tmpfile, filename)
    sonst:
        mit targetfile:
            old_contents = targetfile.read()
        mit open(tmpfile, 'rb') als f:
            new_contents = f.read()
        # Now compare!
        wenn old_contents != new_contents:
            outcome = 'updated'
            os.replace(tmpfile, filename)
        sonst:
            outcome = 'same'
            os.unlink(tmpfile)
    gib outcome


wenn __name__ == '__main__':
    importiere argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--exitcode', action='store_true')
    parser.add_argument('filename', help='path to be updated')
    parser.add_argument('tmpfile', help='path mit new contents')
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
