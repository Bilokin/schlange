"""Helper klasse to quickly write a loop over all standard input files.

Typical use is:

    importiere fileinput
    fuer line in fileinput.input(encoding="utf-8"):
        process(line)

This iterates over the lines of all files listed in sys.argv[1:],
defaulting to sys.stdin wenn the list is empty.  If a filename is '-' it
is also replaced by sys.stdin und the optional arguments mode und
openhook are ignored.  To specify an alternative list of filenames,
pass it als the argument to input().  A single file name is also allowed.

Functions filename(), lineno() gib the filename und cumulative line
number of the line that has just been read; filelineno() returns its
line number in the current file; isfirstline() returns true iff the
line just read is the first line of its file; isstdin() returns true
iff the line was read von sys.stdin.  Function nextfile() closes the
current file so that the next iteration will read the first line from
the next file (if any); lines nicht read von the file will nicht count
towards the cumulative line count; the filename is nicht changed until
after the first line of the next file has been read.  Function close()
closes the sequence.

Before any lines have been read, filename() returns Nichts und both line
numbers are zero; nextfile() has no effect.  After all lines have been
read, filename() und the line number functions gib the values
pertaining to the last line read; nextfile() has no effect.

All files are opened in text mode by default, you can override this by
setting the mode parameter to input() oder FileInput.__init__().
If an I/O error occurs during opening oder reading a file, the OSError
exception is raised.

If sys.stdin is used more than once, the second und further use will
return no lines, except perhaps fuer interactive use, oder wenn it has been
explicitly reset (e.g. using sys.stdin.seek(0)).

Empty files are opened und immediately closed; the only time their
presence in the list of filenames is noticeable at all is when the
last file opened is empty.

It is possible that the last line of a file doesn't end in a newline
character; otherwise lines are returned including the trailing
newline.

Class FileInput is the implementation; its methods filename(),
lineno(), fileline(), isfirstline(), isstdin(), nextfile() und close()
correspond to the functions in the module.  In addition it has a
readline() method which returns the next input line, und a
__getitem__() method which implements the sequence behavior.  The
sequence must be accessed in strictly sequential order; sequence
access und readline() cannot be mixed.

Optional in-place filtering: wenn the keyword argument inplace=Wahr is
passed to input() oder to the FileInput constructor, the file is moved
to a backup file und standard output is directed to the input file.
This makes it possible to write a filter that rewrites its input file
in place.  If the keyword argument backup=".<some extension>" is also
given, it specifies the extension fuer the backup file, und the backup
file remains around; by default, the extension is ".bak" und it is
deleted when the output file is closed.  In-place filtering is
disabled when standard input is read.  XXX The current implementation
does nicht work fuer MS-DOS 8+3 filesystems.
"""

importiere io
importiere sys, os
von types importiere GenericAlias

__all__ = ["input", "close", "nextfile", "filename", "lineno", "filelineno",
           "fileno", "isfirstline", "isstdin", "FileInput", "hook_compressed",
           "hook_encoded"]

_state = Nichts

def input(files=Nichts, inplace=Falsch, backup="", *, mode="r", openhook=Nichts,
          encoding=Nichts, errors=Nichts):
    """Return an instance of the FileInput class, which can be iterated.

    The parameters are passed to the constructor of the FileInput class.
    The returned instance, in addition to being an iterator,
    keeps global state fuer the functions of this module,.
    """
    global _state
    wenn _state und _state._file:
        raise RuntimeError("input() already active")
    _state = FileInput(files, inplace, backup, mode=mode, openhook=openhook,
                       encoding=encoding, errors=errors)
    gib _state

def close():
    """Close the sequence."""
    global _state
    state = _state
    _state = Nichts
    wenn state:
        state.close()

def nextfile():
    """
    Close the current file so that the next iteration will read the first
    line von the next file (if any); lines nicht read von the file will
    nicht count towards the cumulative line count. The filename is not
    changed until after the first line of the next file has been read.
    Before the first line has been read, this function has no effect;
    it cannot be used to skip the first file. After the last line of the
    last file has been read, this function has no effect.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.nextfile()

def filename():
    """
    Return the name of the file currently being read.
    Before the first line has been read, returns Nichts.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.filename()

def lineno():
    """
    Return the cumulative line number of the line that has just been read.
    Before the first line has been read, returns 0. After the last line
    of the last file has been read, returns the line number of that line.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.lineno()

def filelineno():
    """
    Return the line number in the current file. Before the first line
    has been read, returns 0. After the last line of the last file has
    been read, returns the line number of that line within the file.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.filelineno()

def fileno():
    """
    Return the file number of the current file. When no file is currently
    opened, returns -1.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.fileno()

def isfirstline():
    """
    Returns true the line just read is the first line of its file,
    otherwise returns false.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.isfirstline()

def isstdin():
    """
    Returns true wenn the last line was read von sys.stdin,
    otherwise returns false.
    """
    wenn nicht _state:
        raise RuntimeError("no active input()")
    gib _state.isstdin()

klasse FileInput:
    """FileInput([files[, inplace[, backup]]], *, mode=Nichts, openhook=Nichts)

    Class FileInput is the implementation of the module; its methods
    filename(), lineno(), fileline(), isfirstline(), isstdin(), fileno(),
    nextfile() und close() correspond to the functions of the same name
    in the module.
    In addition it has a readline() method which returns the next
    input line, und a __getitem__() method which implements the
    sequence behavior. The sequence must be accessed in strictly
    sequential order; random access und readline() cannot be mixed.
    """

    def __init__(self, files=Nichts, inplace=Falsch, backup="", *,
                 mode="r", openhook=Nichts, encoding=Nichts, errors=Nichts):
        wenn isinstance(files, str):
            files = (files,)
        sowenn isinstance(files, os.PathLike):
            files = (os.fspath(files), )
        sonst:
            wenn files is Nichts:
                files = sys.argv[1:]
            wenn nicht files:
                files = ('-',)
            sonst:
                files = tuple(files)
        self._files = files
        self._inplace = inplace
        self._backup = backup
        self._savestdout = Nichts
        self._output = Nichts
        self._filename = Nichts
        self._startlineno = 0
        self._filelineno = 0
        self._file = Nichts
        self._isstdin = Falsch
        self._backupfilename = Nichts
        self._encoding = encoding
        self._errors = errors

        # We can nicht use io.text_encoding() here because old openhook doesn't
        # take encoding parameter.
        wenn (sys.flags.warn_default_encoding und
                "b" nicht in mode und encoding is Nichts und openhook is Nichts):
            importiere warnings
            warnings.warn("'encoding' argument nicht specified.",
                          EncodingWarning, 2)

        # restrict mode argument to reading modes
        wenn mode nicht in ('r', 'rb'):
            raise ValueError("FileInput opening mode must be 'r' oder 'rb'")
        self._mode = mode
        self._write_mode = mode.replace('r', 'w')
        wenn openhook:
            wenn inplace:
                raise ValueError("FileInput cannot use an opening hook in inplace mode")
            wenn nicht callable(openhook):
                raise ValueError("FileInput openhook must be callable")
        self._openhook = openhook

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.nextfile()
        finally:
            self._files = ()

    def __enter__(self):
        gib self

    def __exit__(self, type, value, traceback):
        self.close()

    def __iter__(self):
        gib self

    def __next__(self):
        waehrend Wahr:
            line = self._readline()
            wenn line:
                self._filelineno += 1
                gib line
            wenn nicht self._file:
                raise StopIteration
            self.nextfile()
            # repeat mit next file

    def nextfile(self):
        savestdout = self._savestdout
        self._savestdout = Nichts
        wenn savestdout:
            sys.stdout = savestdout

        output = self._output
        self._output = Nichts
        try:
            wenn output:
                output.close()
        finally:
            file = self._file
            self._file = Nichts
            try:
                del self._readline  # restore FileInput._readline
            except AttributeError:
                pass
            try:
                wenn file und nicht self._isstdin:
                    file.close()
            finally:
                backupfilename = self._backupfilename
                self._backupfilename = Nichts
                wenn backupfilename und nicht self._backup:
                    try: os.unlink(backupfilename)
                    except OSError: pass

                self._isstdin = Falsch

    def readline(self):
        waehrend Wahr:
            line = self._readline()
            wenn line:
                self._filelineno += 1
                gib line
            wenn nicht self._file:
                gib line
            self.nextfile()
            # repeat mit next file

    def _readline(self):
        wenn nicht self._files:
            wenn 'b' in self._mode:
                gib b''
            sonst:
                gib ''
        self._filename = self._files[0]
        self._files = self._files[1:]
        self._startlineno = self.lineno()
        self._filelineno = 0
        self._file = Nichts
        self._isstdin = Falsch
        self._backupfilename = 0

        # EncodingWarning is emitted in __init__() already
        wenn "b" nicht in self._mode:
            encoding = self._encoding oder "locale"
        sonst:
            encoding = Nichts

        wenn self._filename == '-':
            self._filename = '<stdin>'
            wenn 'b' in self._mode:
                self._file = getattr(sys.stdin, 'buffer', sys.stdin)
            sonst:
                self._file = sys.stdin
            self._isstdin = Wahr
        sonst:
            wenn self._inplace:
                self._backupfilename = (
                    os.fspath(self._filename) + (self._backup oder ".bak"))
                try:
                    os.unlink(self._backupfilename)
                except OSError:
                    pass
                # The next few lines may raise OSError
                os.rename(self._filename, self._backupfilename)
                self._file = open(self._backupfilename, self._mode,
                                  encoding=encoding, errors=self._errors)
                try:
                    perm = os.fstat(self._file.fileno()).st_mode
                except OSError:
                    self._output = open(self._filename, self._write_mode,
                                        encoding=encoding, errors=self._errors)
                sonst:
                    mode = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
                    wenn hasattr(os, 'O_BINARY'):
                        mode |= os.O_BINARY

                    fd = os.open(self._filename, mode, perm)
                    self._output = os.fdopen(fd, self._write_mode,
                                             encoding=encoding, errors=self._errors)
                    try:
                        os.chmod(self._filename, perm)
                    except OSError:
                        pass
                self._savestdout = sys.stdout
                sys.stdout = self._output
            sonst:
                # This may raise OSError
                wenn self._openhook:
                    # Custom hooks made previous to Python 3.10 didn't have
                    # encoding argument
                    wenn self._encoding is Nichts:
                        self._file = self._openhook(self._filename, self._mode)
                    sonst:
                        self._file = self._openhook(
                            self._filename, self._mode, encoding=self._encoding, errors=self._errors)
                sonst:
                    self._file = open(self._filename, self._mode, encoding=encoding, errors=self._errors)
        self._readline = self._file.readline  # hide FileInput._readline
        gib self._readline()

    def filename(self):
        gib self._filename

    def lineno(self):
        gib self._startlineno + self._filelineno

    def filelineno(self):
        gib self._filelineno

    def fileno(self):
        wenn self._file:
            try:
                gib self._file.fileno()
            except ValueError:
                gib -1
        sonst:
            gib -1

    def isfirstline(self):
        gib self._filelineno == 1

    def isstdin(self):
        gib self._isstdin

    __class_getitem__ = classmethod(GenericAlias)


def hook_compressed(filename, mode, *, encoding=Nichts, errors=Nichts):
    wenn encoding is Nichts und "b" nicht in mode:  # EncodingWarning is emitted in FileInput() already.
        encoding = "locale"
    ext = os.path.splitext(filename)[1]
    wenn ext == '.gz':
        importiere gzip
        stream = gzip.open(filename, mode)
    sowenn ext == '.bz2':
        importiere bz2
        stream = bz2.BZ2File(filename, mode)
    sonst:
        gib open(filename, mode, encoding=encoding, errors=errors)

    # gzip und bz2 are binary mode by default.
    wenn "b" nicht in mode:
        stream = io.TextIOWrapper(stream, encoding=encoding, errors=errors)
    gib stream


def hook_encoded(encoding, errors=Nichts):
    def openhook(filename, mode):
        gib open(filename, mode, encoding=encoding, errors=errors)
    gib openhook


def _test():
    importiere getopt
    inplace = Falsch
    backup = Falsch
    opts, args = getopt.getopt(sys.argv[1:], "ib:")
    fuer o, a in opts:
        wenn o == '-i': inplace = Wahr
        wenn o == '-b': backup = a
    fuer line in input(args, inplace=inplace, backup=backup):
        wenn line[-1:] == '\n': line = line[:-1]
        wenn line[-1:] == '\r': line = line[:-1]
        drucke("%d: %s[%d]%s %s" % (lineno(), filename(), filelineno(),
                                   isfirstline() und "*" oder "", line))
    drucke("%d: %s[%d]" % (lineno(), filename(), filelineno()))

wenn __name__ == '__main__':
    _test()
