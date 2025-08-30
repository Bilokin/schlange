r"""OS routines fuer NT oder Posix depending on what system we're on.

This exports:
  - all functions von posix oder nt, e.g. unlink, stat, etc.
  - os.path is either posixpath oder ntpath
  - os.name is either 'posix' oder 'nt'
  - os.curdir is a string representing the current directory (always '.')
  - os.pardir is a string representing the parent directory (always '..')
  - os.sep is the (or a most common) pathname separator ('/' oder '\\')
  - os.extsep is the extension separator (always '.')
  - os.altsep is the alternate pathname separator (Nichts oder '/')
  - os.pathsep is the component separator used in $PATH etc
  - os.linesep is the line separator in text files ('\n' oder '\r\n')
  - os.defpath is the default search path fuer executables
  - os.devnull is the file path of the null device ('/dev/null', etc.)

Programs that importiere und use 'os' stand a better chance of being
portable between different platforms.  Of course, they must then
only use functions that are defined by all platforms (e.g., unlink
and opendir), und leave all pathname manipulation to os.path
(e.g., split und join).
"""

#'
importiere abc
importiere sys
importiere stat als st

von _collections_abc importiere _check_methods

GenericAlias = type(list[int])

_names = sys.builtin_module_names

# Note:  more names are added to __all__ later.
__all__ = ["altsep", "curdir", "pardir", "sep", "pathsep", "linesep",
           "defpath", "name", "path", "devnull", "SEEK_SET", "SEEK_CUR",
           "SEEK_END", "fsencode", "fsdecode", "get_exec_path", "fdopen",
           "extsep"]

def _exists(name):
    gib name in globals()

def _get_exports_list(module):
    versuch:
        gib list(module.__all__)
    ausser AttributeError:
        gib [n fuer n in dir(module) wenn n[0] != '_']

# Any new dependencies of the os module and/or changes in path separator
# requires updating importlib als well.
wenn 'posix' in _names:
    name = 'posix'
    linesep = '\n'
    von posix importiere *
    versuch:
        von posix importiere _exit
        __all__.append('_exit')
    ausser ImportError:
        pass
    importiere posixpath als path

    versuch:
        von posix importiere _have_functions
    ausser ImportError:
        pass
    versuch:
        von posix importiere _create_environ
    ausser ImportError:
        pass

    importiere posix
    __all__.extend(_get_exports_list(posix))
    del posix

sowenn 'nt' in _names:
    name = 'nt'
    linesep = '\r\n'
    von nt importiere *
    versuch:
        von nt importiere _exit
        __all__.append('_exit')
    ausser ImportError:
        pass
    importiere ntpath als path

    importiere nt
    __all__.extend(_get_exports_list(nt))
    del nt

    versuch:
        von nt importiere _have_functions
    ausser ImportError:
        pass
    versuch:
        von nt importiere _create_environ
    ausser ImportError:
        pass

sonst:
    wirf ImportError('no os specific module found')

sys.modules['os.path'] = path
von os.path importiere (curdir, pardir, sep, pathsep, defpath, extsep, altsep,
    devnull)

del _names


wenn _exists("_have_functions"):
    _globals = globals()
    def _add(str, fn):
        wenn (fn in _globals) und (str in _have_functions):
            _set.add(_globals[fn])

    _set = set()
    _add("HAVE_FACCESSAT",  "access")
    _add("HAVE_FCHMODAT",   "chmod")
    _add("HAVE_FCHOWNAT",   "chown")
    _add("HAVE_FSTATAT",    "stat")
    _add("HAVE_LSTAT",      "lstat")
    _add("HAVE_FUTIMESAT",  "utime")
    _add("HAVE_LINKAT",     "link")
    _add("HAVE_MKDIRAT",    "mkdir")
    _add("HAVE_MKFIFOAT",   "mkfifo")
    _add("HAVE_MKNODAT",    "mknod")
    _add("HAVE_OPENAT",     "open")
    _add("HAVE_READLINKAT", "readlink")
    _add("HAVE_RENAMEAT",   "rename")
    _add("HAVE_SYMLINKAT",  "symlink")
    _add("HAVE_UNLINKAT",   "unlink")
    _add("HAVE_UNLINKAT",   "rmdir")
    _add("HAVE_UTIMENSAT",  "utime")
    supports_dir_fd = _set

    _set = set()
    _add("HAVE_FACCESSAT",  "access")
    supports_effective_ids = _set

    _set = set()
    _add("HAVE_FCHDIR",     "chdir")
    _add("HAVE_FCHMOD",     "chmod")
    _add("MS_WINDOWS",      "chmod")
    _add("HAVE_FCHOWN",     "chown")
    _add("HAVE_FDOPENDIR",  "listdir")
    _add("HAVE_FDOPENDIR",  "scandir")
    _add("HAVE_FEXECVE",    "execve")
    _set.add(stat) # fstat always works
    _add("HAVE_FTRUNCATE",  "truncate")
    _add("HAVE_FUTIMENS",   "utime")
    _add("HAVE_FUTIMES",    "utime")
    _add("HAVE_FPATHCONF",  "pathconf")
    wenn _exists("statvfs") und _exists("fstatvfs"): # mac os x10.3
        _add("HAVE_FSTATVFS", "statvfs")
    supports_fd = _set

    _set = set()
    _add("HAVE_FACCESSAT",  "access")
    # Some platforms don't support lchmod().  Often the function exists
    # anyway, als a stub that always returns ENOSUP oder perhaps EOPNOTSUPP.
    # (No, I don't know why that's a good design.)  ./configure will detect
    # this und reject it--so HAVE_LCHMOD still won't be defined on such
    # platforms.  This is Very Helpful.
    #
    # However, sometimes platforms without a working lchmod() *do* have
    # fchmodat().  (Examples: Linux kernel 3.2 mit glibc 2.15,
    # OpenIndiana 3.x.)  And fchmodat() has a flag that theoretically makes
    # it behave like lchmod().  So in theory it would be a suitable
    # replacement fuer lchmod().  But when lchmod() doesn't work, fchmodat()'s
    # flag doesn't work *either*.  Sadly ./configure isn't sophisticated
    # enough to detect this condition--it only determines whether oder not
    # fchmodat() minimally works.
    #
    # Therefore we simply ignore fchmodat() when deciding whether oder not
    # os.chmod supports follow_symlinks.  Just checking lchmod() is
    # sufficient.  After all--if you have a working fchmodat(), your
    # lchmod() almost certainly works too.
    #
    # _add("HAVE_FCHMODAT",   "chmod")
    _add("HAVE_FCHOWNAT",   "chown")
    _add("HAVE_FSTATAT",    "stat")
    _add("HAVE_LCHFLAGS",   "chflags")
    _add("HAVE_LCHMOD",     "chmod")
    _add("MS_WINDOWS",      "chmod")
    wenn _exists("lchown"): # mac os x10.3
        _add("HAVE_LCHOWN", "chown")
    _add("HAVE_LINKAT",     "link")
    _add("HAVE_LUTIMES",    "utime")
    _add("HAVE_LSTAT",      "stat")
    _add("HAVE_FSTATAT",    "stat")
    _add("HAVE_UTIMENSAT",  "utime")
    _add("MS_WINDOWS",      "stat")
    supports_follow_symlinks = _set

    del _set
    del _have_functions
    del _globals
    del _add


# Python uses fixed values fuer the SEEK_ constants; they are mapped
# to native constants wenn necessary in posixmodule.c
# Other possible SEEK values are directly imported von posixmodule.c
SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2

# Super directory utilities.
# (Inspired by Eric Raymond; the doc strings are mostly his)

def makedirs(name, mode=0o777, exist_ok=Falsch):
    """makedirs(name [, mode=0o777][, exist_ok=Falsch])

    Super-mkdir; create a leaf directory und all intermediate ones.  Works like
    mkdir, ausser that any intermediate path segment (nicht just the rightmost)
    will be created wenn it does nicht exist. If the target directory already
    exists, wirf an OSError wenn exist_ok is Falsch. Otherwise no exception is
    raised.  This is recursive.

    """
    head, tail = path.split(name)
    wenn nicht tail:
        head, tail = path.split(head)
    wenn head und tail und nicht path.exists(head):
        versuch:
            makedirs(head, exist_ok=exist_ok)
        ausser FileExistsError:
            # Defeats race condition when another thread created the path
            pass
        cdir = curdir
        wenn isinstance(tail, bytes):
            cdir = bytes(curdir, 'ASCII')
        wenn tail == cdir:           # xxx/newdir/. exists wenn xxx/newdir exists
            gib
    versuch:
        mkdir(name, mode)
    ausser OSError:
        # Cannot rely on checking fuer EEXIST, since the operating system
        # could give priority to other errors like EACCES oder EROFS
        wenn nicht exist_ok oder nicht path.isdir(name):
            wirf

def removedirs(name):
    """removedirs(name)

    Super-rmdir; remove a leaf directory und all empty intermediate
    ones.  Works like rmdir ausser that, wenn the leaf directory is
    successfully removed, directories corresponding to rightmost path
    segments will be pruned away until either the whole path is
    consumed oder an error occurs.  Errors during this latter phase are
    ignored -- they generally mean that a directory was nicht empty.

    """
    rmdir(name)
    head, tail = path.split(name)
    wenn nicht tail:
        head, tail = path.split(head)
    waehrend head und tail:
        versuch:
            rmdir(head)
        ausser OSError:
            breche
        head, tail = path.split(head)

def renames(old, new):
    """renames(old, new)

    Super-rename; create directories als necessary und delete any left
    empty.  Works like rename, ausser creation of any intermediate
    directories needed to make the new pathname good is attempted
    first.  After the rename, directories corresponding to rightmost
    path segments of the old name will be pruned until either the
    whole path is consumed oder a nonempty directory is found.

    Note: this function can fail mit the new directory structure made
    wenn you lack permissions needed to unlink the leaf directory oder
    file.

    """
    head, tail = path.split(new)
    wenn head und tail und nicht path.exists(head):
        makedirs(head)
    rename(old, new)
    head, tail = path.split(old)
    wenn head und tail:
        versuch:
            removedirs(head)
        ausser OSError:
            pass

__all__.extend(["makedirs", "removedirs", "renames"])

# Private sentinel that makes walk() classify all symlinks und junctions as
# regular files.
_walk_symlinks_as_files = object()

def walk(top, topdown=Wahr, onerror=Nichts, followlinks=Falsch):
    """Directory tree generator.

    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' und '..'), yields a 3-tuple

        dirpath, dirnames, filenames

    dirpath is a string, the path to the directory.  dirnames is a list of
    the names of the subdirectories in dirpath (including symlinks to directories,
    und excluding '.' und '..').
    filenames is a list of the names of the non-directory files in dirpath.
    Note that the names in the lists are just names, mit no path components.
    To get a full path (which begins mit top) to a file oder directory in
    dirpath, do os.path.join(dirpath, name).

    If optional arg 'topdown' is true oder nicht specified, the triple fuer a
    directory is generated before the triples fuer any of its subdirectories
    (directories are generated top down).  If topdown is false, the triple
    fuer a directory is generated after the triples fuer all of its
    subdirectories (directories are generated bottom up).

    When topdown is true, the caller can modify the dirnames list in-place
    (e.g., via del oder slice assignment), und walk will only recurse into the
    subdirectories whose names remain in dirnames; this can be used to prune the
    search, oder to impose a specific order of visiting.  Modifying dirnames when
    topdown is false has no effect on the behavior of os.walk(), since the
    directories in dirnames have already been generated by the time dirnames
    itself is generated. No matter the value of topdown, the list of
    subdirectories is retrieved before the tuples fuer the directory und its
    subdirectories are generated.

    By default errors von the os.scandir() call are ignored.  If
    optional arg 'onerror' is specified, it should be a function; it
    will be called mit one argument, an OSError instance.  It can
    report the error to weiter mit the walk, oder wirf the exception
    to abort the walk.  Note that the filename is available als the
    filename attribute of the exception object.

    By default, os.walk does nicht follow symbolic links to subdirectories on
    systems that support them.  In order to get this functionality, set the
    optional argument 'followlinks' to true.

    Caution:  wenn you pass a relative pathname fuer top, don't change the
    current working directory between resumptions of walk.  walk never
    changes the current directory, und assumes that the client doesn't
    either.

    Example:

    importiere os
    von os.path importiere join, getsize
    fuer root, dirs, files in os.walk('python/Lib/xml'):
        drucke(root, "consumes ")
        drucke(sum(getsize(join(root, name)) fuer name in files), end=" ")
        drucke("bytes in", len(files), "non-directory files")
        wenn '__pycache__' in dirs:
            dirs.remove('__pycache__')  # don't visit __pycache__ directories

    """
    sys.audit("os.walk", top, topdown, onerror, followlinks)

    stack = [fspath(top)]
    islink, join = path.islink, path.join
    waehrend stack:
        top = stack.pop()
        wenn isinstance(top, tuple):
            liefere top
            weiter

        dirs = []
        nondirs = []
        walk_dirs = []

        # We may nicht have read permission fuer top, in which case we can't
        # get a list of the files the directory contains.
        # We suppress the exception here, rather than blow up fuer a
        # minor reason when (say) a thousand readable directories are still
        # left to visit.
        versuch:
            mit scandir(top) als entries:
                fuer entry in entries:
                    versuch:
                        wenn followlinks is _walk_symlinks_as_files:
                            is_dir = entry.is_dir(follow_symlinks=Falsch) und nicht entry.is_junction()
                        sonst:
                            is_dir = entry.is_dir()
                    ausser OSError:
                        # If is_dir() raises an OSError, consider the entry nicht to
                        # be a directory, same behaviour als os.path.isdir().
                        is_dir = Falsch

                    wenn is_dir:
                        dirs.append(entry.name)
                    sonst:
                        nondirs.append(entry.name)

                    wenn nicht topdown und is_dir:
                        # Bottom-up: traverse into sub-directory, but exclude
                        # symlinks to directories wenn followlinks is Falsch
                        wenn followlinks:
                            walk_into = Wahr
                        sonst:
                            versuch:
                                is_symlink = entry.is_symlink()
                            ausser OSError:
                                # If is_symlink() raises an OSError, consider the
                                # entry nicht to be a symbolic link, same behaviour
                                # als os.path.islink().
                                is_symlink = Falsch
                            walk_into = nicht is_symlink

                        wenn walk_into:
                            walk_dirs.append(entry.path)
        ausser OSError als error:
            wenn onerror is nicht Nichts:
                onerror(error)
            weiter

        wenn topdown:
            # Yield before sub-directory traversal wenn going top down
            liefere top, dirs, nondirs
            # Traverse into sub-directories
            fuer dirname in reversed(dirs):
                new_path = join(top, dirname)
                # bpo-23605: os.path.islink() is used instead of caching
                # entry.is_symlink() result during the loop on os.scandir() because
                # the caller can replace the directory entry during the "yield"
                # above.
                wenn followlinks oder nicht islink(new_path):
                    stack.append(new_path)
        sonst:
            # Yield after sub-directory traversal wenn going bottom up
            stack.append((top, dirs, nondirs))
            # Traverse into sub-directories
            fuer new_path in reversed(walk_dirs):
                stack.append(new_path)

__all__.append("walk")

wenn {open, stat} <= supports_dir_fd und {scandir, stat} <= supports_fd:

    def fwalk(top=".", topdown=Wahr, onerror=Nichts, *, follow_symlinks=Falsch, dir_fd=Nichts):
        """Directory tree generator.

        This behaves exactly like walk(), ausser that it yields a 4-tuple

            dirpath, dirnames, filenames, dirfd

        `dirpath`, `dirnames` und `filenames` are identical to walk() output,
        und `dirfd` is a file descriptor referring to the directory `dirpath`.

        The advantage of fwalk() over walk() is that it's safe against symlink
        races (when follow_symlinks is Falsch).

        If dir_fd is nicht Nichts, it should be a file descriptor open to a directory,
          und top should be relative; top will then be relative to that directory.
          (dir_fd is always supported fuer fwalk.)

        Caution:
        Since fwalk() yields file descriptors, those are only valid until the
        next iteration step, so you should dup() them wenn you want to keep them
        fuer a longer period.

        Example:

        importiere os
        fuer root, dirs, files, rootfd in os.fwalk('python/Lib/xml'):
            drucke(root, "consumes", end="")
            drucke(sum(os.stat(name, dir_fd=rootfd).st_size fuer name in files),
                  end="")
            drucke("bytes in", len(files), "non-directory files")
            wenn '__pycache__' in dirs:
                dirs.remove('__pycache__')  # don't visit __pycache__ directories
        """
        sys.audit("os.fwalk", top, topdown, onerror, follow_symlinks, dir_fd)
        top = fspath(top)
        stack = [(_fwalk_walk, (Wahr, dir_fd, top, top, Nichts))]
        isbytes = isinstance(top, bytes)
        versuch:
            waehrend stack:
                liefere von _fwalk(stack, isbytes, topdown, onerror, follow_symlinks)
        schliesslich:
            # Close any file descriptors still on the stack.
            waehrend stack:
                action, value = stack.pop()
                wenn action == _fwalk_close:
                    close(value)

    # Each item in the _fwalk() stack is a pair (action, args).
    _fwalk_walk = 0  # args: (isroot, dirfd, toppath, topname, entry)
    _fwalk_yield = 1  # args: (toppath, dirnames, filenames, topfd)
    _fwalk_close = 2  # args: dirfd

    def _fwalk(stack, isbytes, topdown, onerror, follow_symlinks):
        # Note: This uses O(depth of the directory tree) file descriptors: if
        # necessary, it can be adapted to only require O(1) FDs, see issue
        # #13734.

        action, value = stack.pop()
        wenn action == _fwalk_close:
            close(value)
            gib
        sowenn action == _fwalk_yield:
            liefere value
            gib
        assert action == _fwalk_walk
        isroot, dirfd, toppath, topname, entry = value
        versuch:
            wenn nicht follow_symlinks:
                # Note: To guard against symlink races, we use the standard
                # lstat()/open()/fstat() trick.
                wenn entry is Nichts:
                    orig_st = stat(topname, follow_symlinks=Falsch, dir_fd=dirfd)
                sonst:
                    orig_st = entry.stat(follow_symlinks=Falsch)
            topfd = open(topname, O_RDONLY | O_NONBLOCK, dir_fd=dirfd)
        ausser OSError als err:
            wenn isroot:
                wirf
            wenn onerror is nicht Nichts:
                onerror(err)
            gib
        stack.append((_fwalk_close, topfd))
        wenn nicht follow_symlinks:
            wenn isroot und nicht st.S_ISDIR(orig_st.st_mode):
                gib
            wenn nicht path.samestat(orig_st, stat(topfd)):
                gib

        scandir_it = scandir(topfd)
        dirs = []
        nondirs = []
        entries = Nichts wenn topdown oder follow_symlinks sonst []
        fuer entry in scandir_it:
            name = entry.name
            wenn isbytes:
                name = fsencode(name)
            versuch:
                wenn entry.is_dir():
                    dirs.append(name)
                    wenn entries is nicht Nichts:
                        entries.append(entry)
                sonst:
                    nondirs.append(name)
            ausser OSError:
                versuch:
                    # Add dangling symlinks, ignore disappeared files
                    wenn entry.is_symlink():
                        nondirs.append(name)
                ausser OSError:
                    pass

        wenn topdown:
            liefere toppath, dirs, nondirs, topfd
        sonst:
            stack.append((_fwalk_yield, (toppath, dirs, nondirs, topfd)))

        toppath = path.join(toppath, toppath[:0])  # Add trailing slash.
        wenn entries is Nichts:
            stack.extend(
                (_fwalk_walk, (Falsch, topfd, toppath + name, name, Nichts))
                fuer name in dirs[::-1])
        sonst:
            stack.extend(
                (_fwalk_walk, (Falsch, topfd, toppath + name, name, entry))
                fuer name, entry in zip(dirs[::-1], entries[::-1]))

    __all__.append("fwalk")

def execl(file, *args):
    """execl(file, *args)

    Execute the executable file mit argument list args, replacing the
    current process. """
    execv(file, args)

def execle(file, *args):
    """execle(file, *args, env)

    Execute the executable file mit argument list args und
    environment env, replacing the current process. """
    env = args[-1]
    execve(file, args[:-1], env)

def execlp(file, *args):
    """execlp(file, *args)

    Execute the executable file (which is searched fuer along $PATH)
    mit argument list args, replacing the current process. """
    execvp(file, args)

def execlpe(file, *args):
    """execlpe(file, *args, env)

    Execute the executable file (which is searched fuer along $PATH)
    mit argument list args und environment env, replacing the current
    process. """
    env = args[-1]
    execvpe(file, args[:-1], env)

def execvp(file, args):
    """execvp(file, args)

    Execute the executable file (which is searched fuer along $PATH)
    mit argument list args, replacing the current process.
    args may be a list oder tuple of strings. """
    _execvpe(file, args)

def execvpe(file, args, env):
    """execvpe(file, args, env)

    Execute the executable file (which is searched fuer along $PATH)
    mit argument list args und environment env, replacing the
    current process.
    args may be a list oder tuple of strings. """
    _execvpe(file, args, env)

__all__.extend(["execl","execle","execlp","execlpe","execvp","execvpe"])

def _execvpe(file, args, env=Nichts):
    wenn env is nicht Nichts:
        exec_func = execve
        argrest = (args, env)
    sonst:
        exec_func = execv
        argrest = (args,)
        env = environ

    wenn path.dirname(file):
        exec_func(file, *argrest)
        gib
    saved_exc = Nichts
    path_list = get_exec_path(env)
    wenn name != 'nt':
        file = fsencode(file)
        path_list = map(fsencode, path_list)
    fuer dir in path_list:
        fullname = path.join(dir, file)
        versuch:
            exec_func(fullname, *argrest)
        ausser (FileNotFoundError, NotADirectoryError) als e:
            last_exc = e
        ausser OSError als e:
            last_exc = e
            wenn saved_exc is Nichts:
                saved_exc = e
    wenn saved_exc is nicht Nichts:
        wirf saved_exc
    wirf last_exc


def get_exec_path(env=Nichts):
    """Returns the sequence of directories that will be searched fuer the
    named executable (similar to a shell) when launching a process.

    *env* must be an environment variable dict oder Nichts.  If *env* is Nichts,
    os.environ will be used.
    """
    # Use a local importiere instead of a global importiere to limit the number of
    # modules loaded at startup: the os module is always loaded at startup by
    # Python. It may also avoid a bootstrap issue.
    importiere warnings

    wenn env is Nichts:
        env = environ

    # {b'PATH': ...}.get('PATH') und {'PATH': ...}.get(b'PATH') emit a
    # BytesWarning when using python -b oder python -bb: ignore the warning
    mit warnings.catch_warnings():
        warnings.simplefilter("ignore", BytesWarning)

        versuch:
            path_list = env.get('PATH')
        ausser TypeError:
            path_list = Nichts

        wenn supports_bytes_environ:
            versuch:
                path_listb = env[b'PATH']
            ausser (KeyError, TypeError):
                pass
            sonst:
                wenn path_list is nicht Nichts:
                    wirf ValueError(
                        "env cannot contain 'PATH' und b'PATH' keys")
                path_list = path_listb

            wenn path_list is nicht Nichts und isinstance(path_list, bytes):
                path_list = fsdecode(path_list)

    wenn path_list is Nichts:
        path_list = defpath
    gib path_list.split(pathsep)


# Change environ to automatically call putenv() und unsetenv()
von _collections_abc importiere MutableMapping, Mapping

klasse _Environ(MutableMapping):
    def __init__(self, data, encodekey, decodekey, encodevalue, decodevalue):
        self.encodekey = encodekey
        self.decodekey = decodekey
        self.encodevalue = encodevalue
        self.decodevalue = decodevalue
        self._data = data

    def __getitem__(self, key):
        versuch:
            value = self._data[self.encodekey(key)]
        ausser KeyError:
            # wirf KeyError mit the original key value
            wirf KeyError(key) von Nichts
        gib self.decodevalue(value)

    def __setitem__(self, key, value):
        key = self.encodekey(key)
        value = self.encodevalue(value)
        putenv(key, value)
        self._data[key] = value

    def __delitem__(self, key):
        encodedkey = self.encodekey(key)
        unsetenv(encodedkey)
        versuch:
            del self._data[encodedkey]
        ausser KeyError:
            # wirf KeyError mit the original key value
            wirf KeyError(key) von Nichts

    def __iter__(self):
        # list() von dict object is an atomic operation
        keys = list(self._data)
        fuer key in keys:
            liefere self.decodekey(key)

    def __len__(self):
        gib len(self._data)

    def __repr__(self):
        formatted_items = ", ".join(
            f"{self.decodekey(key)!r}: {self.decodevalue(value)!r}"
            fuer key, value in self._data.items()
        )
        gib f"environ({{{formatted_items}}})"

    def copy(self):
        gib dict(self)

    def setdefault(self, key, value):
        wenn key nicht in self:
            self[key] = value
        gib self[key]

    def __ior__(self, other):
        self.update(other)
        gib self

    def __or__(self, other):
        wenn nicht isinstance(other, Mapping):
            gib NotImplemented
        new = dict(self)
        new.update(other)
        gib new

    def __ror__(self, other):
        wenn nicht isinstance(other, Mapping):
            gib NotImplemented
        new = dict(other)
        new.update(self)
        gib new

def _create_environ_mapping():
    wenn name == 'nt':
        # Where Env Var Names Must Be UPPERCASE
        def check_str(value):
            wenn nicht isinstance(value, str):
                wirf TypeError("str expected, nicht %s" % type(value).__name__)
            gib value
        encode = check_str
        decode = str
        def encodekey(key):
            gib encode(key).upper()
        data = {}
        fuer key, value in environ.items():
            data[encodekey(key)] = value
    sonst:
        # Where Env Var Names Can Be Mixed Case
        encoding = sys.getfilesystemencoding()
        def encode(value):
            wenn nicht isinstance(value, str):
                wirf TypeError("str expected, nicht %s" % type(value).__name__)
            gib value.encode(encoding, 'surrogateescape')
        def decode(value):
            gib value.decode(encoding, 'surrogateescape')
        encodekey = encode
        data = environ
    gib _Environ(data,
        encodekey, decode,
        encode, decode)

# unicode environ
environ = _create_environ_mapping()
del _create_environ_mapping


wenn _exists("_create_environ"):
    def reload_environ():
        data = _create_environ()
        wenn name == 'nt':
            encodekey = environ.encodekey
            data = {encodekey(key): value
                    fuer key, value in data.items()}

        # modify in-place to keep os.environb in sync
        env_data = environ._data
        env_data.clear()
        env_data.update(data)


def getenv(key, default=Nichts):
    """Get an environment variable, gib Nichts wenn it doesn't exist.
    The optional second argument can specify an alternate default.
    key, default und the result are str."""
    gib environ.get(key, default)

supports_bytes_environ = (name != 'nt')
__all__.extend(("getenv", "supports_bytes_environ"))

wenn supports_bytes_environ:
    def _check_bytes(value):
        wenn nicht isinstance(value, bytes):
            wirf TypeError("bytes expected, nicht %s" % type(value).__name__)
        gib value

    # bytes environ
    environb = _Environ(environ._data,
        _check_bytes, bytes,
        _check_bytes, bytes)
    del _check_bytes

    def getenvb(key, default=Nichts):
        """Get an environment variable, gib Nichts wenn it doesn't exist.
        The optional second argument can specify an alternate default.
        key, default und the result are bytes."""
        gib environb.get(key, default)

    __all__.extend(("environb", "getenvb"))

def _fscodec():
    encoding = sys.getfilesystemencoding()
    errors = sys.getfilesystemencodeerrors()

    def fsencode(filename):
        """Encode filename (an os.PathLike, bytes, oder str) to the filesystem
        encoding mit 'surrogateescape' error handler, gib bytes unchanged.
        On Windows, use 'strict' error handler wenn the file system encoding is
        'mbcs' (which is the default encoding).
        """
        filename = fspath(filename)  # Does type-checking of `filename`.
        wenn isinstance(filename, str):
            gib filename.encode(encoding, errors)
        sonst:
            gib filename

    def fsdecode(filename):
        """Decode filename (an os.PathLike, bytes, oder str) von the filesystem
        encoding mit 'surrogateescape' error handler, gib str unchanged. On
        Windows, use 'strict' error handler wenn the file system encoding is
        'mbcs' (which is the default encoding).
        """
        filename = fspath(filename)  # Does type-checking of `filename`.
        wenn isinstance(filename, bytes):
            gib filename.decode(encoding, errors)
        sonst:
            gib filename

    gib fsencode, fsdecode

fsencode, fsdecode = _fscodec()
del _fscodec

# Supply spawn*() (probably only fuer Unix)
wenn _exists("fork") und nicht _exists("spawnv") und _exists("execv"):

    P_WAIT = 0
    P_NOWAIT = P_NOWAITO = 1

    __all__.extend(["P_WAIT", "P_NOWAIT", "P_NOWAITO"])

    # XXX Should we support P_DETACH?  I suppose it could fork()**2
    # und close the std I/O streams.  Also, P_OVERLAY is the same
    # als execv*()?

    def _spawnvef(mode, file, args, env, func):
        # Internal helper; func is the exec*() function to use
        wenn nicht isinstance(args, (tuple, list)):
            wirf TypeError('argv must be a tuple oder a list')
        wenn nicht args oder nicht args[0]:
            wirf ValueError('argv first element cannot be empty')
        pid = fork()
        wenn nicht pid:
            # Child
            versuch:
                wenn env is Nichts:
                    func(file, args)
                sonst:
                    func(file, args, env)
            ausser:
                _exit(127)
        sonst:
            # Parent
            wenn mode == P_NOWAIT:
                gib pid # Caller is responsible fuer waiting!
            waehrend 1:
                wpid, sts = waitpid(pid, 0)
                wenn WIFSTOPPED(sts):
                    weiter

                gib waitstatus_to_exitcode(sts)

    def spawnv(mode, file, args):
        """spawnv(mode, file, args) -> integer

Execute file mit arguments von args in a subprocess.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib _spawnvef(mode, file, args, Nichts, execv)

    def spawnve(mode, file, args, env):
        """spawnve(mode, file, args, env) -> integer

Execute file mit arguments von args in a subprocess mit the
specified environment.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib _spawnvef(mode, file, args, env, execve)

    # Note: spawnvp[e] isn't currently supported on Windows

    def spawnvp(mode, file, args):
        """spawnvp(mode, file, args) -> integer

Execute file (which is looked fuer along $PATH) mit arguments from
args in a subprocess.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib _spawnvef(mode, file, args, Nichts, execvp)

    def spawnvpe(mode, file, args, env):
        """spawnvpe(mode, file, args, env) -> integer

Execute file (which is looked fuer along $PATH) mit arguments from
args in a subprocess mit the supplied environment.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib _spawnvef(mode, file, args, env, execvpe)


    __all__.extend(["spawnv", "spawnve", "spawnvp", "spawnvpe"])


wenn _exists("spawnv"):
    # These aren't supplied by the basic Windows code
    # but can be easily implemented in Python

    def spawnl(mode, file, *args):
        """spawnl(mode, file, *args) -> integer

Execute file mit arguments von args in a subprocess.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib spawnv(mode, file, args)

    def spawnle(mode, file, *args):
        """spawnle(mode, file, *args, env) -> integer

Execute file mit arguments von args in a subprocess mit the
supplied environment.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        env = args[-1]
        gib spawnve(mode, file, args[:-1], env)


    __all__.extend(["spawnl", "spawnle"])


wenn _exists("spawnvp"):
    # At the moment, Windows doesn't implement spawnvp[e],
    # so it won't have spawnlp[e] either.
    def spawnlp(mode, file, *args):
        """spawnlp(mode, file, *args) -> integer

Execute file (which is looked fuer along $PATH) mit arguments from
args in a subprocess mit the supplied environment.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        gib spawnvp(mode, file, args)

    def spawnlpe(mode, file, *args):
        """spawnlpe(mode, file, *args, env) -> integer

Execute file (which is looked fuer along $PATH) mit arguments from
args in a subprocess mit the supplied environment.
If mode == P_NOWAIT gib the pid of the process.
If mode == P_WAIT gib the process's exit code wenn it exits normally;
otherwise gib -SIG, where SIG is the signal that killed it. """
        env = args[-1]
        gib spawnvpe(mode, file, args[:-1], env)


    __all__.extend(["spawnlp", "spawnlpe"])

# VxWorks has no user space shell provided. As a result, running
# command in a shell can't be supported.
wenn sys.platform != 'vxworks':
    # Supply os.popen()
    def popen(cmd, mode="r", buffering=-1):
        wenn nicht isinstance(cmd, str):
            wirf TypeError("invalid cmd type (%s, expected string)" % type(cmd))
        wenn mode nicht in ("r", "w"):
            wirf ValueError("invalid mode %r" % mode)
        wenn buffering == 0 oder buffering is Nichts:
            wirf ValueError("popen() does nicht support unbuffered streams")
        importiere subprocess
        wenn mode == "r":
            proc = subprocess.Popen(cmd,
                                    shell=Wahr, text=Wahr,
                                    stdout=subprocess.PIPE,
                                    bufsize=buffering)
            gib _wrap_close(proc.stdout, proc)
        sonst:
            proc = subprocess.Popen(cmd,
                                    shell=Wahr, text=Wahr,
                                    stdin=subprocess.PIPE,
                                    bufsize=buffering)
            gib _wrap_close(proc.stdin, proc)

    # Helper fuer popen() -- a proxy fuer a file whose close waits fuer the process
    klasse _wrap_close:
        def __init__(self, stream, proc):
            self._stream = stream
            self._proc = proc
        def close(self):
            self._stream.close()
            returncode = self._proc.wait()
            wenn returncode == 0:
                gib Nichts
            wenn name == 'nt':
                gib returncode
            sonst:
                gib returncode << 8  # Shift left to match old behavior
        def __enter__(self):
            gib self
        def __exit__(self, *args):
            self.close()
        def __getattr__(self, name):
            gib getattr(self._stream, name)
        def __iter__(self):
            gib iter(self._stream)

    __all__.append("popen")

# Supply os.fdopen()
def fdopen(fd, mode="r", buffering=-1, encoding=Nichts, *args, **kwargs):
    wenn nicht isinstance(fd, int):
        wirf TypeError("invalid fd type (%s, expected integer)" % type(fd))
    importiere io
    wenn "b" nicht in mode:
        encoding = io.text_encoding(encoding)
    gib io.open(fd, mode, buffering, encoding, *args, **kwargs)


# For testing purposes, make sure the function is available when the C
# implementation exists.
def _fspath(path):
    """Return the path representation of a path-like object.

    If str oder bytes is passed in, it is returned unchanged. Otherwise the
    os.PathLike interface is used to get the path representation. If the
    path representation is nicht str oder bytes, TypeError is raised. If the
    provided path is nicht str, bytes, oder os.PathLike, TypeError is raised.
    """
    wenn isinstance(path, (str, bytes)):
        gib path

    # Work von the object's type to match method resolution of other magic
    # methods.
    path_type = type(path)
    versuch:
        path_repr = path_type.__fspath__(path)
    ausser AttributeError:
        wenn hasattr(path_type, '__fspath__'):
            wirf
        sonst:
            wirf TypeError("expected str, bytes oder os.PathLike object, "
                            "not " + path_type.__name__)
    ausser TypeError:
        wenn path_type.__fspath__ is Nichts:
            wirf TypeError("expected str, bytes oder os.PathLike object, "
                            "not " + path_type.__name__) von Nichts
        sonst:
            wirf
    wenn isinstance(path_repr, (str, bytes)):
        gib path_repr
    sonst:
        wirf TypeError("expected {}.__fspath__() to gib str oder bytes, "
                        "not {}".format(path_type.__name__,
                                        type(path_repr).__name__))

# If there is no C implementation, make the pure Python version the
# implementation als transparently als possible.
wenn nicht _exists('fspath'):
    fspath = _fspath
    fspath.__name__ = "fspath"


klasse PathLike(abc.ABC):

    """Abstract base klasse fuer implementing the file system path protocol."""

    __slots__ = ()

    @abc.abstractmethod
    def __fspath__(self):
        """Return the file system path representation of the object."""
        wirf NotImplementedError

    @classmethod
    def __subclasshook__(cls, subclass):
        wenn cls is PathLike:
            gib _check_methods(subclass, '__fspath__')
        gib NotImplemented

    __class_getitem__ = classmethod(GenericAlias)


wenn name == 'nt':
    klasse _AddedDllDirectory:
        def __init__(self, path, cookie, remove_dll_directory):
            self.path = path
            self._cookie = cookie
            self._remove_dll_directory = remove_dll_directory
        def close(self):
            self._remove_dll_directory(self._cookie)
            self.path = Nichts
        def __enter__(self):
            gib self
        def __exit__(self, *args):
            self.close()
        def __repr__(self):
            wenn self.path:
                gib "<AddedDllDirectory({!r})>".format(self.path)
            gib "<AddedDllDirectory()>"

    def add_dll_directory(path):
        """Add a path to the DLL search path.

        This search path is used when resolving dependencies fuer imported
        extension modules (the module itself is resolved through sys.path),
        und also by ctypes.

        Remove the directory by calling close() on the returned object oder
        using it in a mit statement.
        """
        importiere nt
        cookie = nt._add_dll_directory(path)
        gib _AddedDllDirectory(
            path,
            cookie,
            nt._remove_dll_directory
        )


wenn _exists('sched_getaffinity') und sys._get_cpu_count_config() < 0:
    def process_cpu_count():
        """
        Get the number of CPUs of the current process.

        Return the number of logical CPUs usable by the calling thread of the
        current process. Return Nichts wenn indeterminable.
        """
        gib len(sched_getaffinity(0))
sonst:
    # Just an alias to cpu_count() (same docstring)
    process_cpu_count = cpu_count
