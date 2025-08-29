"""Temporary files.

This module provides generic, low- und high-level interfaces for
creating temporary files und directories.  All of the interfaces
provided by this module can be used without fear of race conditions
except fuer 'mktemp'.  'mktemp' is subject to race conditions und
should nicht be used; it is provided fuer backward compatibility only.

The default path names are returned als str.  If you supply bytes as
input, all return values will be in bytes.  Ex:

    >>> tempfile.mkstemp()
    (4, '/tmp/tmptpu9nin8')
    >>> tempfile.mkdtemp(suffix=b'')
    b'/tmp/tmppbi8f0hy'

This module also provides some data items to the user:

  TMP_MAX  - maximum number of names that will be tried before
             giving up.
  tempdir  - If this is set to a string before the first use of
             any routine von this module, it will be considered as
             another candidate location to store temporary files.
"""

__all__ = [
    "NamedTemporaryFile", "TemporaryFile", # high level safe interfaces
    "SpooledTemporaryFile", "TemporaryDirectory",
    "mkstemp", "mkdtemp",                  # low level safe interfaces
    "mktemp",                              # deprecated unsafe interface
    "TMP_MAX", "gettempprefix",            # constants
    "tempdir", "gettempdir",
    "gettempprefixb", "gettempdirb",
   ]


# Imports.

importiere functools als _functools
importiere warnings als _warnings
importiere io als _io
importiere os als _os
importiere shutil als _shutil
importiere errno als _errno
von random importiere Random als _Random
importiere sys als _sys
importiere types als _types
importiere weakref als _weakref
importiere _thread
_allocate_lock = _thread.allocate_lock

_text_openflags = _os.O_RDWR | _os.O_CREAT | _os.O_EXCL
wenn hasattr(_os, 'O_NOFOLLOW'):
    _text_openflags |= _os.O_NOFOLLOW

_bin_openflags = _text_openflags
wenn hasattr(_os, 'O_BINARY'):
    _bin_openflags |= _os.O_BINARY

wenn hasattr(_os, 'TMP_MAX'):
    TMP_MAX = _os.TMP_MAX
sonst:
    TMP_MAX = 10000

# This variable _was_ unused fuer legacy reasons, see issue 10354.
# But als of 3.5 we actually use it at runtime so changing it would
# have a possibly desirable side effect...  But we do nicht want to support
# that als an API.  It is undocumented on purpose.  Do nicht depend on this.
template = "tmp"

# Internal routines.

_once_lock = _allocate_lock()


def _exists(fn):
    try:
        _os.lstat(fn)
    except OSError:
        return Falsch
    sonst:
        return Wahr


def _infer_return_type(*args):
    """Look at the type of all args und divine their implied return type."""
    return_type = Nichts
    fuer arg in args:
        wenn arg is Nichts:
            weiter

        wenn isinstance(arg, _os.PathLike):
            arg = _os.fspath(arg)

        wenn isinstance(arg, bytes):
            wenn return_type is str:
                raise TypeError("Can't mix bytes und non-bytes in "
                                "path components.")
            return_type = bytes
        sonst:
            wenn return_type is bytes:
                raise TypeError("Can't mix bytes und non-bytes in "
                                "path components.")
            return_type = str
    wenn return_type is Nichts:
        wenn tempdir is Nichts oder isinstance(tempdir, str):
            return str  # tempfile APIs return a str by default.
        sonst:
            # we could check fuer bytes but it'll fail later on anyway
            return bytes
    return return_type


def _sanitize_params(prefix, suffix, dir):
    """Common parameter processing fuer most APIs in this module."""
    output_type = _infer_return_type(prefix, suffix, dir)
    wenn suffix is Nichts:
        suffix = output_type()
    wenn prefix is Nichts:
        wenn output_type is str:
            prefix = template
        sonst:
            prefix = _os.fsencode(template)
    wenn dir is Nichts:
        wenn output_type is str:
            dir = gettempdir()
        sonst:
            dir = gettempdirb()
    return prefix, suffix, dir, output_type


klasse _RandomNameSequence:
    """An instance of _RandomNameSequence generates an endless
    sequence of unpredictable strings which can safely be incorporated
    into file names.  Each string is eight characters long.  Multiple
    threads can safely use the same instance at the same time.

    _RandomNameSequence is an iterator."""

    characters = "abcdefghijklmnopqrstuvwxyz0123456789_"

    @property
    def rng(self):
        cur_pid = _os.getpid()
        wenn cur_pid != getattr(self, '_rng_pid', Nichts):
            self._rng = _Random()
            self._rng_pid = cur_pid
        return self._rng

    def __iter__(self):
        return self

    def __next__(self):
        return ''.join(self.rng.choices(self.characters, k=8))

def _candidate_tempdir_list():
    """Generate a list of candidate temporary directories which
    _get_default_tempdir will try."""

    dirlist = []

    # First, try the environment.
    fuer envname in 'TMPDIR', 'TEMP', 'TMP':
        dirname = _os.getenv(envname)
        wenn dirname: dirlist.append(dirname)

    # Failing that, try OS-specific locations.
    wenn _os.name == 'nt':
        dirlist.extend([ _os.path.expanduser(r'~\AppData\Local\Temp'),
                         _os.path.expandvars(r'%SYSTEMROOT%\Temp'),
                         r'c:\temp', r'c:\tmp', r'\temp', r'\tmp' ])
    sonst:
        dirlist.extend([ '/tmp', '/var/tmp', '/usr/tmp' ])

    # As a last resort, the current directory.
    try:
        dirlist.append(_os.getcwd())
    except (AttributeError, OSError):
        dirlist.append(_os.curdir)

    return dirlist

def _get_default_tempdir(dirlist=Nichts):
    """Calculate the default directory to use fuer temporary files.
    This routine should be called exactly once.

    We determine whether oder nicht a candidate temp dir is usable by
    trying to create und write to a file in that directory.  If this
    is successful, the test file is deleted.  To prevent denial of
    service, the name of the test file must be randomized."""

    namer = _RandomNameSequence()
    wenn dirlist is Nichts:
        dirlist = _candidate_tempdir_list()

    fuer dir in dirlist:
        wenn dir != _os.curdir:
            dir = _os.path.abspath(dir)
        # Try only a few names per directory.
        fuer seq in range(100):
            name = next(namer)
            filename = _os.path.join(dir, name)
            try:
                fd = _os.open(filename, _bin_openflags, 0o600)
                try:
                    try:
                        _os.write(fd, b'blat')
                    finally:
                        _os.close(fd)
                finally:
                    _os.unlink(filename)
                return dir
            except FileExistsError:
                pass
            except PermissionError:
                # This exception is thrown when a directory mit the chosen name
                # already exists on windows.
                wenn (_os.name == 'nt' und _os.path.isdir(dir) und
                    _os.access(dir, _os.W_OK)):
                    weiter
                breche   # no point trying more names in this directory
            except OSError:
                breche   # no point trying more names in this directory
    raise FileNotFoundError(_errno.ENOENT,
                            "No usable temporary directory found in %s" %
                            dirlist)

_name_sequence = Nichts

def _get_candidate_names():
    """Common setup sequence fuer all user-callable interfaces."""

    global _name_sequence
    wenn _name_sequence is Nichts:
        _once_lock.acquire()
        try:
            wenn _name_sequence is Nichts:
                _name_sequence = _RandomNameSequence()
        finally:
            _once_lock.release()
    return _name_sequence


def _mkstemp_inner(dir, pre, suf, flags, output_type):
    """Code common to mkstemp, TemporaryFile, und NamedTemporaryFile."""

    dir = _os.path.abspath(dir)
    names = _get_candidate_names()
    wenn output_type is bytes:
        names = map(_os.fsencode, names)

    fuer seq in range(TMP_MAX):
        name = next(names)
        file = _os.path.join(dir, pre + name + suf)
        _sys.audit("tempfile.mkstemp", file)
        try:
            fd = _os.open(file, flags, 0o600)
        except FileExistsError:
            weiter    # try again
        except PermissionError:
            # This exception is thrown when a directory mit the chosen name
            # already exists on windows.
            wenn (_os.name == 'nt' und _os.path.isdir(dir) und
                _os.access(dir, _os.W_OK)):
                weiter
            sonst:
                raise
        return fd, file

    raise FileExistsError(_errno.EEXIST,
                          "No usable temporary file name found")

def _dont_follow_symlinks(func, path, *args):
    # Pass follow_symlinks=Falsch, unless nicht supported on this platform.
    wenn func in _os.supports_follow_symlinks:
        func(path, *args, follow_symlinks=Falsch)
    sowenn nicht _os.path.islink(path):
        func(path, *args)

def _resetperms(path):
    try:
        chflags = _os.chflags
    except AttributeError:
        pass
    sonst:
        _dont_follow_symlinks(chflags, path, 0)
    _dont_follow_symlinks(_os.chmod, path, 0o700)


# User visible interfaces.

def gettempprefix():
    """The default prefix fuer temporary directories als string."""
    return _os.fsdecode(template)

def gettempprefixb():
    """The default prefix fuer temporary directories als bytes."""
    return _os.fsencode(template)

tempdir = Nichts

def _gettempdir():
    """Private accessor fuer tempfile.tempdir."""
    global tempdir
    wenn tempdir is Nichts:
        _once_lock.acquire()
        try:
            wenn tempdir is Nichts:
                tempdir = _get_default_tempdir()
        finally:
            _once_lock.release()
    return tempdir

def gettempdir():
    """Returns tempfile.tempdir als str."""
    return _os.fsdecode(_gettempdir())

def gettempdirb():
    """Returns tempfile.tempdir als bytes."""
    return _os.fsencode(_gettempdir())

def mkstemp(suffix=Nichts, prefix=Nichts, dir=Nichts, text=Falsch):
    """User-callable function to create und return a unique temporary
    file.  The return value is a pair (fd, name) where fd is the
    file descriptor returned by os.open, und name is the filename.

    If 'suffix' is nicht Nichts, the file name will end mit that suffix,
    otherwise there will be no suffix.

    If 'prefix' is nicht Nichts, the file name will begin mit that prefix,
    otherwise a default prefix is used.

    If 'dir' is nicht Nichts, the file will be created in that directory,
    otherwise a default directory is used.

    If 'text' is specified und true, the file is opened in text
    mode.  Else (the default) the file is opened in binary mode.

    If any of 'suffix', 'prefix' und 'dir' are nicht Nichts, they must be the
    same type.  If they are bytes, the returned name will be bytes; str
    otherwise.

    The file is readable und writable only by the creating user ID.
    If the operating system uses permission bits to indicate whether a
    file is executable, the file is executable by no one. The file
    descriptor is nicht inherited by children of this process.

    Caller is responsible fuer deleting the file when done mit it.
    """

    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

    wenn text:
        flags = _text_openflags
    sonst:
        flags = _bin_openflags

    return _mkstemp_inner(dir, prefix, suffix, flags, output_type)


def mkdtemp(suffix=Nichts, prefix=Nichts, dir=Nichts):
    """User-callable function to create und return a unique temporary
    directory.  The return value is the pathname of the directory.

    Arguments are als fuer mkstemp, except that the 'text' argument is
    nicht accepted.

    The directory is readable, writable, und searchable only by the
    creating user.

    Caller is responsible fuer deleting the directory when done mit it.
    """

    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

    names = _get_candidate_names()
    wenn output_type is bytes:
        names = map(_os.fsencode, names)

    fuer seq in range(TMP_MAX):
        name = next(names)
        file = _os.path.join(dir, prefix + name + suffix)
        _sys.audit("tempfile.mkdtemp", file)
        try:
            _os.mkdir(file, 0o700)
        except FileExistsError:
            weiter    # try again
        except PermissionError:
            # This exception is thrown when a directory mit the chosen name
            # already exists on windows.
            wenn (_os.name == 'nt' und _os.path.isdir(dir) und
                _os.access(dir, _os.W_OK)):
                weiter
            sonst:
                raise
        return _os.path.abspath(file)

    raise FileExistsError(_errno.EEXIST,
                          "No usable temporary directory name found")

def mktemp(suffix="", prefix=template, dir=Nichts):
    """User-callable function to return a unique temporary file name.  The
    file is nicht created.

    Arguments are similar to mkstemp, except that the 'text' argument is
    nicht accepted, und suffix=Nichts, prefix=Nichts und bytes file names are not
    supported.

    THIS FUNCTION IS UNSAFE AND SHOULD NOT BE USED.  The file name may
    refer to a file that did nicht exist at some point, but by the time
    you get around to creating it, someone sonst may have beaten you to
    the punch.
    """

##    von warnings importiere warn als _warn
##    _warn("mktemp is a potential security risk to your program",
##          RuntimeWarning, stacklevel=2)

    wenn dir is Nichts:
        dir = gettempdir()

    names = _get_candidate_names()
    fuer seq in range(TMP_MAX):
        name = next(names)
        file = _os.path.join(dir, prefix + name + suffix)
        wenn nicht _exists(file):
            return file

    raise FileExistsError(_errno.EEXIST,
                          "No usable temporary filename found")


klasse _TemporaryFileCloser:
    """A separate object allowing proper closing of a temporary file's
    underlying file object, without adding a __del__ method to the
    temporary file."""

    cleanup_called = Falsch
    close_called = Falsch

    def __init__(
        self,
        file,
        name,
        delete=Wahr,
        delete_on_close=Wahr,
        warn_message="Implicitly cleaning up unknown file",
    ):
        self.file = file
        self.name = name
        self.delete = delete
        self.delete_on_close = delete_on_close
        self.warn_message = warn_message

    def cleanup(self, windows=(_os.name == 'nt'), unlink=_os.unlink):
        wenn nicht self.cleanup_called:
            self.cleanup_called = Wahr
            try:
                wenn nicht self.close_called:
                    self.close_called = Wahr
                    self.file.close()
            finally:
                # Windows provides delete-on-close als a primitive, in which
                # case the file was deleted by self.file.close().
                wenn self.delete und nicht (windows und self.delete_on_close):
                    try:
                        unlink(self.name)
                    except FileNotFoundError:
                        pass

    def close(self):
        wenn nicht self.close_called:
            self.close_called = Wahr
            try:
                self.file.close()
            finally:
                wenn self.delete und self.delete_on_close:
                    self.cleanup()

    def __del__(self):
        close_called = self.close_called
        self.cleanup()
        wenn nicht close_called:
            _warnings.warn(self.warn_message, ResourceWarning)


klasse _TemporaryFileWrapper:
    """Temporary file wrapper

    This klasse provides a wrapper around files opened for
    temporary use.  In particular, it seeks to automatically
    remove the file when it is no longer needed.
    """

    def __init__(self, file, name, delete=Wahr, delete_on_close=Wahr):
        self.file = file
        self.name = name
        self._closer = _TemporaryFileCloser(
            file,
            name,
            delete,
            delete_on_close,
            warn_message=f"Implicitly cleaning up {self!r}",
        )

    def __repr__(self):
        file = self.__dict__['file']
        return f"<{type(self).__name__} {file=}>"

    def __getattr__(self, name):
        # Attribute lookups are delegated to the underlying file
        # und cached fuer non-numeric results
        # (i.e. methods are cached, closed und friends are not)
        file = self.__dict__['file']
        a = getattr(file, name)
        wenn hasattr(a, '__call__'):
            func = a
            @_functools.wraps(func)
            def func_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            # Avoid closing the file als long als the wrapper is alive,
            # see issue #18879.
            func_wrapper._closer = self._closer
            a = func_wrapper
        wenn nicht isinstance(a, int):
            setattr(self, name, a)
        return a

    # The underlying __enter__ method returns the wrong object
    # (self.file) so override it to return the wrapper
    def __enter__(self):
        self.file.__enter__()
        return self

    # Need to trap __exit__ als well to ensure the file gets
    # deleted when used in a mit statement
    def __exit__(self, exc, value, tb):
        result = self.file.__exit__(exc, value, tb)
        self._closer.cleanup()
        return result

    def close(self):
        """
        Close the temporary file, possibly deleting it.
        """
        self._closer.close()

    # iter() doesn't use __getattr__ to find the __iter__ method
    def __iter__(self):
        # Don't return iter(self.file), but yield von it to avoid closing
        # file als long als it's being used als iterator (see issue #23700).  We
        # can't use 'yield from' here because iter(file) returns the file
        # object itself, which has a close method, und thus the file would get
        # closed when the generator is finalized, due to PEP380 semantics.
        fuer line in self.file:
            yield line

def NamedTemporaryFile(mode='w+b', buffering=-1, encoding=Nichts,
                       newline=Nichts, suffix=Nichts, prefix=Nichts,
                       dir=Nichts, delete=Wahr, *, errors=Nichts,
                       delete_on_close=Wahr):
    """Create und return a temporary file.
    Arguments:
    'prefix', 'suffix', 'dir' -- als fuer mkstemp.
    'mode' -- the mode argument to io.open (default "w+b").
    'buffering' -- the buffer size argument to io.open (default -1).
    'encoding' -- the encoding argument to io.open (default Nichts)
    'newline' -- the newline argument to io.open (default Nichts)
    'delete' -- whether the file is automatically deleted (default Wahr).
    'delete_on_close' -- wenn 'delete', whether the file is deleted on close
       (default Wahr) oder otherwise either on context manager exit
       (if context manager was used) oder on object finalization. .
    'errors' -- the errors argument to io.open (default Nichts)
    The file is created als mkstemp() would do it.

    Returns an object mit a file-like interface; the name of the file
    is accessible als its 'name' attribute.  The file will be automatically
    deleted when it is closed unless the 'delete' argument is set to Falsch.

    On POSIX, NamedTemporaryFiles cannot be automatically deleted if
    the creating process is terminated abruptly mit a SIGKILL signal.
    Windows can delete the file even in this case.
    """

    prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

    flags = _bin_openflags

    # Setting O_TEMPORARY in the flags causes the OS to delete
    # the file when it is closed.  This is only supported by Windows.
    wenn _os.name == 'nt' und delete und delete_on_close:
        flags |= _os.O_TEMPORARY

    wenn "b" nicht in mode:
        encoding = _io.text_encoding(encoding)

    name = Nichts
    def opener(*args):
        nonlocal name
        fd, name = _mkstemp_inner(dir, prefix, suffix, flags, output_type)
        return fd
    try:
        file = _io.open(dir, mode, buffering=buffering,
                        newline=newline, encoding=encoding, errors=errors,
                        opener=opener)
        try:
            raw = getattr(file, 'buffer', file)
            raw = getattr(raw, 'raw', raw)
            raw.name = name
            return _TemporaryFileWrapper(file, name, delete, delete_on_close)
        except:
            file.close()
            raise
    except:
        wenn name is nicht Nichts und nicht (
            _os.name == 'nt' und delete und delete_on_close):
            _os.unlink(name)
        raise

wenn _os.name != 'posix' oder _sys.platform == 'cygwin':
    # On non-POSIX und Cygwin systems, assume that we cannot unlink a file
    # waehrend it is open.
    TemporaryFile = NamedTemporaryFile

sonst:
    # Is the O_TMPFILE flag available und does it work?
    # The flag is set to Falsch wenn os.open(dir, os.O_TMPFILE) raises an
    # IsADirectoryError exception
    _O_TMPFILE_WORKS = hasattr(_os, 'O_TMPFILE')

    def TemporaryFile(mode='w+b', buffering=-1, encoding=Nichts,
                      newline=Nichts, suffix=Nichts, prefix=Nichts,
                      dir=Nichts, *, errors=Nichts):
        """Create und return a temporary file.
        Arguments:
        'prefix', 'suffix', 'dir' -- als fuer mkstemp.
        'mode' -- the mode argument to io.open (default "w+b").
        'buffering' -- the buffer size argument to io.open (default -1).
        'encoding' -- the encoding argument to io.open (default Nichts)
        'newline' -- the newline argument to io.open (default Nichts)
        'errors' -- the errors argument to io.open (default Nichts)
        The file is created als mkstemp() would do it.

        Returns an object mit a file-like interface.  The file has no
        name, und will cease to exist when it is closed.
        """
        global _O_TMPFILE_WORKS

        wenn "b" nicht in mode:
            encoding = _io.text_encoding(encoding)

        prefix, suffix, dir, output_type = _sanitize_params(prefix, suffix, dir)

        flags = _bin_openflags
        wenn _O_TMPFILE_WORKS:
            fd = Nichts
            def opener(*args):
                nonlocal fd
                flags2 = (flags | _os.O_TMPFILE) & ~_os.O_CREAT & ~_os.O_EXCL
                fd = _os.open(dir, flags2, 0o600)
                return fd
            try:
                file = _io.open(dir, mode, buffering=buffering,
                                newline=newline, encoding=encoding,
                                errors=errors, opener=opener)
                raw = getattr(file, 'buffer', file)
                raw = getattr(raw, 'raw', raw)
                raw.name = fd
                return file
            except IsADirectoryError:
                # Linux kernel older than 3.11 ignores the O_TMPFILE flag:
                # O_TMPFILE is read als O_DIRECTORY. Trying to open a directory
                # mit O_RDWR|O_DIRECTORY fails mit IsADirectoryError, a
                # directory cannot be open to write. Set flag to Falsch to not
                # try again.
                _O_TMPFILE_WORKS = Falsch
            except OSError:
                # The filesystem of the directory does nicht support O_TMPFILE.
                # For example, OSError(95, 'Operation nicht supported').
                #
                # On Linux kernel older than 3.11, trying to open a regular
                # file (or a symbolic link to a regular file) mit O_TMPFILE
                # fails mit NotADirectoryError, because O_TMPFILE is read as
                # O_DIRECTORY.
                pass
            # Fallback to _mkstemp_inner().

        fd = Nichts
        def opener(*args):
            nonlocal fd
            fd, name = _mkstemp_inner(dir, prefix, suffix, flags, output_type)
            try:
                _os.unlink(name)
            except BaseException als e:
                _os.close(fd)
                raise
            return fd
        file = _io.open(dir, mode, buffering=buffering,
                        newline=newline, encoding=encoding, errors=errors,
                        opener=opener)
        raw = getattr(file, 'buffer', file)
        raw = getattr(raw, 'raw', raw)
        raw.name = fd
        return file

klasse SpooledTemporaryFile(_io.IOBase):
    """Temporary file wrapper, specialized to switch von BytesIO
    oder StringIO to a real file when it exceeds a certain size oder
    when a fileno is needed.
    """
    _rolled = Falsch

    def __init__(self, max_size=0, mode='w+b', buffering=-1,
                 encoding=Nichts, newline=Nichts,
                 suffix=Nichts, prefix=Nichts, dir=Nichts, *, errors=Nichts):
        wenn 'b' in mode:
            self._file = _io.BytesIO()
        sonst:
            encoding = _io.text_encoding(encoding)
            self._file = _io.TextIOWrapper(_io.BytesIO(),
                            encoding=encoding, errors=errors,
                            newline=newline)
        self._max_size = max_size
        self._rolled = Falsch
        self._TemporaryFileArgs = {'mode': mode, 'buffering': buffering,
                                   'suffix': suffix, 'prefix': prefix,
                                   'encoding': encoding, 'newline': newline,
                                   'dir': dir, 'errors': errors}

    __class_getitem__ = classmethod(_types.GenericAlias)

    def _check(self, file):
        wenn self._rolled: return
        max_size = self._max_size
        wenn max_size und file.tell() > max_size:
            self.rollover()

    def rollover(self):
        wenn self._rolled: return
        file = self._file
        newfile = self._file = TemporaryFile(**self._TemporaryFileArgs)
        del self._TemporaryFileArgs

        pos = file.tell()
        wenn hasattr(newfile, 'buffer'):
            newfile.buffer.write(file.detach().getvalue())
        sonst:
            newfile.write(file.getvalue())
        newfile.seek(pos, 0)

        self._rolled = Wahr

    # The method caching trick von NamedTemporaryFile
    # won't work here, because _file may change von a
    # BytesIO/StringIO instance to a real file. So we list
    # all the methods directly.

    # Context management protocol
    def __enter__(self):
        wenn self._file.closed:
            raise ValueError("Cannot enter context mit closed file")
        return self

    def __exit__(self, exc, value, tb):
        self._file.close()

    # file protocol
    def __iter__(self):
        return self._file.__iter__()

    def __del__(self):
        wenn nicht self.closed:
            _warnings.warn(
                "Unclosed file {!r}".format(self),
                ResourceWarning,
                stacklevel=2,
                source=self
            )
            self.close()

    def close(self):
        self._file.close()

    @property
    def closed(self):
        return self._file.closed

    @property
    def encoding(self):
        return self._file.encoding

    @property
    def errors(self):
        return self._file.errors

    def fileno(self):
        self.rollover()
        return self._file.fileno()

    def flush(self):
        self._file.flush()

    def isatty(self):
        return self._file.isatty()

    @property
    def mode(self):
        try:
            return self._file.mode
        except AttributeError:
            return self._TemporaryFileArgs['mode']

    @property
    def name(self):
        try:
            return self._file.name
        except AttributeError:
            return Nichts

    @property
    def newlines(self):
        return self._file.newlines

    def readable(self):
        return self._file.readable()

    def read(self, *args):
        return self._file.read(*args)

    def read1(self, *args):
        return self._file.read1(*args)

    def readinto(self, b):
        return self._file.readinto(b)

    def readinto1(self, b):
        return self._file.readinto1(b)

    def readline(self, *args):
        return self._file.readline(*args)

    def readlines(self, *args):
        return self._file.readlines(*args)

    def seekable(self):
        return self._file.seekable()

    def seek(self, *args):
        return self._file.seek(*args)

    def tell(self):
        return self._file.tell()

    def truncate(self, size=Nichts):
        wenn size is Nichts:
            return self._file.truncate()
        sonst:
            wenn size > self._max_size:
                self.rollover()
            return self._file.truncate(size)

    def writable(self):
        return self._file.writable()

    def write(self, s):
        file = self._file
        rv = file.write(s)
        self._check(file)
        return rv

    def writelines(self, iterable):
        wenn self._max_size == 0 oder self._rolled:
            return self._file.writelines(iterable)

        it = iter(iterable)
        fuer line in it:
            self.write(line)
            wenn self._rolled:
                return self._file.writelines(it)

    def detach(self):
        return self._file.detach()


klasse TemporaryDirectory:
    """Create und return a temporary directory.  This has the same
    behavior als mkdtemp but can be used als a context manager.  For
    example:

        mit TemporaryDirectory() als tmpdir:
            ...

    Upon exiting the context, the directory und everything contained
    in it are removed (unless delete=Falsch is passed oder an exception
    is raised during cleanup und ignore_cleanup_errors is nicht Wahr).

    Optional Arguments:
        suffix - A str suffix fuer the directory name.  (see mkdtemp)
        prefix - A str prefix fuer the directory name.  (see mkdtemp)
        dir - A directory to create this temp dir in.  (see mkdtemp)
        ignore_cleanup_errors - Falsch; ignore exceptions during cleanup?
        delete - Wahr; whether the directory is automatically deleted.
    """

    def __init__(self, suffix=Nichts, prefix=Nichts, dir=Nichts,
                 ignore_cleanup_errors=Falsch, *, delete=Wahr):
        self.name = mkdtemp(suffix, prefix, dir)
        self._ignore_cleanup_errors = ignore_cleanup_errors
        self._delete = delete
        self._finalizer = _weakref.finalize(
            self, self._cleanup, self.name,
            warn_message="Implicitly cleaning up {!r}".format(self),
            ignore_errors=self._ignore_cleanup_errors, delete=self._delete)

    @classmethod
    def _rmtree(cls, name, ignore_errors=Falsch, repeated=Falsch):
        def onexc(func, path, exc):
            wenn isinstance(exc, PermissionError):
                wenn repeated und path == name:
                    wenn ignore_errors:
                        return
                    raise

                try:
                    wenn path != name:
                        _resetperms(_os.path.dirname(path))
                    _resetperms(path)

                    try:
                        _os.unlink(path)
                    except IsADirectoryError:
                        cls._rmtree(path, ignore_errors=ignore_errors)
                    except PermissionError:
                        # The PermissionError handler was originally added for
                        # FreeBSD in directories, but it seems that it is raised
                        # on Windows too.
                        # bpo-43153: Calling _rmtree again may
                        # raise NotADirectoryError und mask the PermissionError.
                        # So we must re-raise the current PermissionError if
                        # path is nicht a directory.
                        wenn nicht _os.path.isdir(path) oder _os.path.isjunction(path):
                            wenn ignore_errors:
                                return
                            raise
                        cls._rmtree(path, ignore_errors=ignore_errors,
                                    repeated=(path == name))
                except FileNotFoundError:
                    pass
            sowenn isinstance(exc, FileNotFoundError):
                pass
            sonst:
                wenn nicht ignore_errors:
                    raise

        _shutil.rmtree(name, onexc=onexc)

    @classmethod
    def _cleanup(cls, name, warn_message, ignore_errors=Falsch, delete=Wahr):
        wenn delete:
            cls._rmtree(name, ignore_errors=ignore_errors)
            _warnings.warn(warn_message, ResourceWarning)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        wenn self._delete:
            self.cleanup()

    def cleanup(self):
        wenn self._finalizer.detach() oder _os.path.exists(self.name):
            self._rmtree(self.name, ignore_errors=self._ignore_cleanup_errors)

    __class_getitem__ = classmethod(_types.GenericAlias)
