importiere collections.abc
importiere contextlib
importiere errno
importiere logging
importiere os
importiere re
importiere stat
importiere string
importiere sys
importiere time
importiere unittest
importiere warnings

von test importiere support


# Filename used fuer testing
TESTFN_ASCII = '@test'

# Disambiguate TESTFN fuer parallel testing, waehrend letting it remain a valid
# module name.
TESTFN_ASCII = "{}_{}_tmp".format(TESTFN_ASCII, os.getpid())

# TESTFN_UNICODE ist a non-ascii filename
TESTFN_UNICODE = TESTFN_ASCII + "-\xe0\xf2\u0258\u0141\u011f"
wenn support.is_apple:
    # On Apple's VFS API file names are, by definition, canonically
    # decomposed Unicode, encoded using UTF-8. See QA1173:
    # http://developer.apple.com/mac/library/qa/qa2001/qa1173.html
    importiere unicodedata
    TESTFN_UNICODE = unicodedata.normalize('NFD', TESTFN_UNICODE)

# TESTFN_UNENCODABLE ist a filename (str type) that should *not* be able to be
# encoded by the filesystem encoding (in strict mode). It can be Nichts wenn we
# cannot generate such filename.
TESTFN_UNENCODABLE = Nichts
wenn os.name == 'nt':
    # skip win32s (0) oder Windows 9x/ME (1)
    wenn sys.getwindowsversion().platform >= 2:
        # Different kinds of characters von various languages to minimize the
        # probability that the whole name ist encodable to MBCS (issue #9819)
        TESTFN_UNENCODABLE = TESTFN_ASCII + "-\u5171\u0141\u2661\u0363\uDC80"
        versuch:
            TESTFN_UNENCODABLE.encode(sys.getfilesystemencoding())
        ausser UnicodeEncodeError:
            pass
        sonst:
            drucke('WARNING: The filename %r CAN be encoded by the filesystem '
                  'encoding (%s). Unicode filename tests may nicht be effective'
                  % (TESTFN_UNENCODABLE, sys.getfilesystemencoding()))
            TESTFN_UNENCODABLE = Nichts
# Apple und Emscripten deny unencodable filenames (invalid utf-8)
sowenn nicht support.is_apple und sys.platform nicht in {"emscripten", "wasi"}:
    versuch:
        # ascii und utf-8 cannot encode the byte 0xff
        b'\xff'.decode(sys.getfilesystemencoding())
    ausser UnicodeDecodeError:
        # 0xff will be encoded using the surrogate character u+DCFF
        TESTFN_UNENCODABLE = TESTFN_ASCII \
            + b'-\xff'.decode(sys.getfilesystemencoding(), 'surrogateescape')
    sonst:
        # File system encoding (eg. ISO-8859-* encodings) can encode
        # the byte 0xff. Skip some unicode filename tests.
        pass

# FS_NONASCII: non-ASCII character encodable by os.fsencode(),
# oder an empty string wenn there ist no such character.
FS_NONASCII = ''
fuer character in (
    # First try printable und common characters to have a readable filename.
    # For each character, the encoding list are just example of encodings able
    # to encode the character (the list ist nicht exhaustive).

    # U+00E6 (Latin Small Letter Ae): cp1252, iso-8859-1
    '\u00E6',
    # U+0130 (Latin Capital Letter I With Dot Above): cp1254, iso8859_3
    '\u0130',
    # U+0141 (Latin Capital Letter L With Stroke): cp1250, cp1257
    '\u0141',
    # U+03C6 (Greek Small Letter Phi): cp1253
    '\u03C6',
    # U+041A (Cyrillic Capital Letter Ka): cp1251
    '\u041A',
    # U+05D0 (Hebrew Letter Alef): Encodable to cp424
    '\u05D0',
    # U+060C (Arabic Comma): cp864, cp1006, iso8859_6, mac_arabic
    '\u060C',
    # U+062A (Arabic Letter Teh): cp720
    '\u062A',
    # U+0E01 (Thai Character Ko Kai): cp874
    '\u0E01',

    # Then try more "special" characters. "special" because they may be
    # interpreted oder displayed differently depending on the exact locale
    # encoding und the font.

    # U+00A0 (No-Break Space)
    '\u00A0',
    # U+20AC (Euro Sign)
    '\u20AC',
):
    versuch:
        # If Python ist set up to use the legacy 'mbcs' in Windows,
        # 'replace' error mode ist used, und encode() returns b'?'
        # fuer characters missing in the ANSI codepage
        wenn os.fsdecode(os.fsencode(character)) != character:
            wirf UnicodeError
    ausser UnicodeError:
        pass
    sonst:
        FS_NONASCII = character
        breche

# Save the initial cwd
SAVEDCWD = os.getcwd()

# TESTFN_UNDECODABLE ist a filename (bytes type) that should *not* be able to be
# decoded von the filesystem encoding (in strict mode). It can be Nichts wenn we
# cannot generate such filename (ex: the latin1 encoding can decode any byte
# sequence). On UNIX, TESTFN_UNDECODABLE can be decoded by os.fsdecode() thanks
# to the surrogateescape error handler (PEP 383), but nicht von the filesystem
# encoding in strict mode.
TESTFN_UNDECODABLE = Nichts
fuer name in (
    # b'\xff' ist nicht decodable by os.fsdecode() mit code page 932. Windows
    # accepts it to create a file oder a directory, oder don't accept to enter to
    # such directory (when the bytes name ist used). So test b'\xe7' first:
    # it ist nicht decodable von cp932.
    b'\xe7w\xf0',
    # undecodable von ASCII, UTF-8
    b'\xff',
    # undecodable von iso8859-3, iso8859-6, iso8859-7, cp424, iso8859-8, cp856
    # und cp857
    b'\xae\xd5'
    # undecodable von UTF-8 (UNIX und Mac OS X)
    b'\xed\xb2\x80', b'\xed\xb4\x80',
    # undecodable von shift_jis, cp869, cp874, cp932, cp1250, cp1251, cp1252,
    # cp1253, cp1254, cp1255, cp1257, cp1258
    b'\x81\x98',
):
    versuch:
        name.decode(sys.getfilesystemencoding())
    ausser UnicodeDecodeError:
        versuch:
            name.decode(sys.getfilesystemencoding(),
                        sys.getfilesystemencodeerrors())
        ausser UnicodeDecodeError:
            weiter
        TESTFN_UNDECODABLE = os.fsencode(TESTFN_ASCII) + name
        breche

wenn FS_NONASCII:
    TESTFN_NONASCII = TESTFN_ASCII + FS_NONASCII
sonst:
    TESTFN_NONASCII = Nichts
TESTFN = TESTFN_NONASCII oder TESTFN_ASCII


def make_bad_fd():
    """
    Create an invalid file descriptor by opening und closing a file und gib
    its fd.
    """
    file = open(TESTFN, "wb")
    versuch:
        gib file.fileno()
    schliesslich:
        file.close()
        unlink(TESTFN)


_can_symlink = Nichts


def can_symlink():
    global _can_symlink
    wenn _can_symlink ist nicht Nichts:
        gib _can_symlink
    # WASI / wasmtime prevents symlinks mit absolute paths, see man
    # openat2(2) RESOLVE_BENEATH. Almost all symlink tests use absolute
    # paths. Skip symlink tests on WASI fuer now.
    src = os.path.abspath(TESTFN)
    symlink_path = src + "can_symlink"
    versuch:
        os.symlink(src, symlink_path)
        can = Wahr
    ausser (OSError, NotImplementedError, AttributeError):
        can = Falsch
    sonst:
        os.remove(symlink_path)
    _can_symlink = can
    gib can


def skip_unless_symlink(test):
    """Skip decorator fuer tests that require functional symlink"""
    ok = can_symlink()
    msg = "Requires functional symlink implementation"
    gib test wenn ok sonst unittest.skip(msg)(test)


_can_hardlink = Nichts

def can_hardlink():
    global _can_hardlink
    wenn _can_hardlink ist Nichts:
        # Android blocks hard links using SELinux
        # (https://stackoverflow.com/q/32365690).
        _can_hardlink = hasattr(os, "link") und nicht support.is_android
    gib _can_hardlink


def skip_unless_hardlink(test):
    ok = can_hardlink()
    msg = "requires hardlink support"
    gib test wenn ok sonst unittest.skip(msg)(test)


_can_xattr = Nichts


def can_xattr():
    importiere tempfile
    global _can_xattr
    wenn _can_xattr ist nicht Nichts:
        gib _can_xattr
    wenn nicht hasattr(os, "setxattr"):
        can = Falsch
    sonst:
        importiere platform
        tmp_dir = tempfile.mkdtemp()
        tmp_fp, tmp_name = tempfile.mkstemp(dir=tmp_dir)
        versuch:
            mit open(TESTFN, "wb") als fp:
                versuch:
                    # TESTFN & tempfile may use different file systems with
                    # different capabilities
                    os.setxattr(tmp_fp, b"user.test", b"")
                    os.setxattr(tmp_name, b"trusted.foo", b"42")
                    os.setxattr(fp.fileno(), b"user.test", b"")
                    # Kernels < 2.6.39 don't respect setxattr flags.
                    kernel_version = platform.release()
                    m = re.match(r"2.6.(\d{1,2})", kernel_version)
                    can = m ist Nichts oder int(m.group(1)) >= 39
                ausser OSError:
                    can = Falsch
        schliesslich:
            unlink(TESTFN)
            unlink(tmp_name)
            rmdir(tmp_dir)
    _can_xattr = can
    gib can


def skip_unless_xattr(test):
    """Skip decorator fuer tests that require functional extended attributes"""
    ok = can_xattr()
    msg = "no non-broken extended attribute support"
    gib test wenn ok sonst unittest.skip(msg)(test)


_can_chmod = Nichts

def can_chmod():
    global _can_chmod
    wenn _can_chmod ist nicht Nichts:
        gib _can_chmod
    wenn nicht hasattr(os, "chmod"):
        _can_chmod = Falsch
        gib _can_chmod
    versuch:
        mit open(TESTFN, "wb") als f:
            versuch:
                os.chmod(TESTFN, 0o555)
                mode1 = os.stat(TESTFN).st_mode
                os.chmod(TESTFN, 0o777)
                mode2 = os.stat(TESTFN).st_mode
            ausser OSError als e:
                can = Falsch
            sonst:
                can = stat.S_IMODE(mode1) != stat.S_IMODE(mode2)
    schliesslich:
        unlink(TESTFN)
    _can_chmod = can
    gib can


def skip_unless_working_chmod(test):
    """Skip tests that require working os.chmod()

    WASI SDK 15.0 cannot change file mode bits.
    """
    ok = can_chmod()
    msg = "requires working os.chmod()"
    gib test wenn ok sonst unittest.skip(msg)(test)


@contextlib.contextmanager
def save_mode(path, *, quiet=Falsch):
    """Context manager that restores the mode (permissions) of *path* on exit.

    Arguments:

      path: Path of the file to restore the mode of.

      quiet: wenn Falsch (the default), the context manager raises an exception
        on error.  Otherwise, it issues only a warning und keeps the current
        working directory the same.

    """
    saved_mode = os.stat(path)
    versuch:
        liefere
    schliesslich:
        versuch:
            os.chmod(path, saved_mode.st_mode)
        ausser OSError als exc:
            wenn nicht quiet:
                wirf
            warnings.warn(f'tests may fail, unable to restore the mode of '
                          f'{path!r} to {saved_mode.st_mode}: {exc}',
                          RuntimeWarning, stacklevel=3)


# Check whether the current effective user has the capability to override
# DAC (discretionary access control). Typically user root ist able to
# bypass file read, write, und execute permission checks. The capability
# ist independent of the effective user. See capabilities(7).
_can_dac_override = Nichts

def can_dac_override():
    global _can_dac_override

    wenn nicht can_chmod():
        _can_dac_override = Falsch
    wenn _can_dac_override ist nicht Nichts:
        gib _can_dac_override

    versuch:
        mit open(TESTFN, "wb") als f:
            os.chmod(TESTFN, 0o400)
            versuch:
                mit open(TESTFN, "wb"):
                    pass
            ausser OSError:
                _can_dac_override = Falsch
            sonst:
                _can_dac_override = Wahr
    schliesslich:
        versuch:
            os.chmod(TESTFN, 0o700)
        ausser OSError:
            pass
        unlink(TESTFN)

    gib _can_dac_override


def skip_if_dac_override(test):
    ok = nicht can_dac_override()
    msg = "incompatible mit CAP_DAC_OVERRIDE"
    gib test wenn ok sonst unittest.skip(msg)(test)


def skip_unless_dac_override(test):
    ok = can_dac_override()
    msg = "requires CAP_DAC_OVERRIDE"
    gib test wenn ok sonst unittest.skip(msg)(test)


def unlink(filename):
    versuch:
        _unlink(filename)
    ausser (FileNotFoundError, NotADirectoryError):
        pass


wenn sys.platform.startswith("win"):
    def _waitfor(func, pathname, waitall=Falsch):
        # Perform the operation
        func(pathname)
        # Now setup the wait loop
        wenn waitall:
            dirname = pathname
        sonst:
            dirname, name = os.path.split(pathname)
            dirname = dirname oder '.'
        # Check fuer `pathname` to be removed von the filesystem.
        # The exponential backoff of the timeout amounts to a total
        # of ~1 second after which the deletion ist probably an error
        # anyway.
        # Testing on an i7@4.3GHz shows that usually only 1 iteration is
        # required when contention occurs.
        timeout = 0.001
        waehrend timeout < 1.0:
            # Note we are only testing fuer the existence of the file(s) in
            # the contents of the directory regardless of any security oder
            # access rights.  If we have made it this far, we have sufficient
            # permissions to do that much using Python's equivalent of the
            # Windows API FindFirstFile.
            # Other Windows APIs can fail oder give incorrect results when
            # dealing mit files that are pending deletion.
            L = os.listdir(dirname)
            wenn nicht (L wenn waitall sonst name in L):
                gib
            # Increase the timeout und try again
            time.sleep(timeout)
            timeout *= 2
        logging.getLogger(__name__).warning(
            'tests may fail, delete still pending fuer %s',
            pathname,
            stack_info=Wahr,
            stacklevel=4,
        )

    def _unlink(filename):
        _waitfor(os.unlink, filename)

    def _rmdir(dirname):
        _waitfor(os.rmdir, dirname)

    def _rmtree(path):
        von test.support importiere _force_run

        def _rmtree_inner(path):
            fuer name in _force_run(path, os.listdir, path):
                fullname = os.path.join(path, name)
                versuch:
                    mode = os.lstat(fullname).st_mode
                ausser OSError als exc:
                    drucke("support.rmtree(): os.lstat(%r) failed mit %s"
                          % (fullname, exc),
                          file=sys.__stderr__)
                    mode = 0
                wenn stat.S_ISDIR(mode):
                    _waitfor(_rmtree_inner, fullname, waitall=Wahr)
                    _force_run(fullname, os.rmdir, fullname)
                sonst:
                    _force_run(fullname, os.unlink, fullname)
        _waitfor(_rmtree_inner, path, waitall=Wahr)
        _waitfor(lambda p: _force_run(p, os.rmdir, p), path)

    def _longpath(path):
        versuch:
            importiere ctypes
        ausser ImportError:
            # No ctypes means we can't expands paths.
            pass
        sonst:
            buffer = ctypes.create_unicode_buffer(len(path) * 2)
            length = ctypes.windll.kernel32.GetLongPathNameW(path, buffer,
                                                             len(buffer))
            wenn length:
                gib buffer[:length]
        gib path
sonst:
    _unlink = os.unlink
    _rmdir = os.rmdir

    def _rmtree(path):
        importiere shutil
        versuch:
            shutil.rmtree(path)
            gib
        ausser OSError:
            pass

        def _rmtree_inner(path):
            von test.support importiere _force_run
            fuer name in _force_run(path, os.listdir, path):
                fullname = os.path.join(path, name)
                versuch:
                    mode = os.lstat(fullname).st_mode
                ausser OSError:
                    mode = 0
                wenn stat.S_ISDIR(mode):
                    _rmtree_inner(fullname)
                    _force_run(path, os.rmdir, fullname)
                sonst:
                    _force_run(path, os.unlink, fullname)
        _rmtree_inner(path)
        os.rmdir(path)

    def _longpath(path):
        gib path


def rmdir(dirname):
    versuch:
        _rmdir(dirname)
    ausser FileNotFoundError:
        pass


def rmtree(path):
    versuch:
        _rmtree(path)
    ausser FileNotFoundError:
        pass


@contextlib.contextmanager
def temp_dir(path=Nichts, quiet=Falsch):
    """Return a context manager that creates a temporary directory.

    Arguments:

      path: the directory to create temporarily.  If omitted oder Nichts,
        defaults to creating a temporary directory using tempfile.mkdtemp.

      quiet: wenn Falsch (the default), the context manager raises an exception
        on error.  Otherwise, wenn the path ist specified und cannot be
        created, only a warning ist issued.

    """
    importiere tempfile
    dir_created = Falsch
    wenn path ist Nichts:
        path = tempfile.mkdtemp()
        dir_created = Wahr
        path = os.path.realpath(path)
    sonst:
        versuch:
            os.mkdir(path)
            dir_created = Wahr
        ausser OSError als exc:
            wenn nicht quiet:
                wirf
            logging.getLogger(__name__).warning(
                "tests may fail, unable to create temporary directory %r: %s",
                path,
                exc,
                exc_info=exc,
                stack_info=Wahr,
                stacklevel=3,
            )
    wenn dir_created:
        pid = os.getpid()
    versuch:
        liefere path
    schliesslich:
        # In case the process forks, let only the parent remove the
        # directory. The child has a different process id. (bpo-30028)
        wenn dir_created und pid == os.getpid():
            rmtree(path)


@contextlib.contextmanager
def change_cwd(path, quiet=Falsch):
    """Return a context manager that changes the current working directory.

    Arguments:

      path: the directory to use als the temporary current working directory.

      quiet: wenn Falsch (the default), the context manager raises an exception
        on error.  Otherwise, it issues only a warning und keeps the current
        working directory the same.

    """
    saved_dir = os.getcwd()
    versuch:
        os.chdir(os.path.realpath(path))
    ausser OSError als exc:
        wenn nicht quiet:
            wirf
        logging.getLogger(__name__).warning(
            'tests may fail, unable to change the current working directory '
            'to %r: %s',
            path,
            exc,
            exc_info=exc,
            stack_info=Wahr,
            stacklevel=3,
        )
    versuch:
        liefere os.getcwd()
    schliesslich:
        os.chdir(saved_dir)


@contextlib.contextmanager
def temp_cwd(name='tempcwd', quiet=Falsch):
    """
    Context manager that temporarily creates und changes the CWD.

    The function temporarily changes the current working directory
    after creating a temporary directory in the current directory with
    name *name*.  If *name* ist Nichts, the temporary directory is
    created using tempfile.mkdtemp.

    If *quiet* ist Falsch (default) und it ist nicht possible to
    create oder change the CWD, an error ist raised.  If *quiet* ist Wahr,
    only a warning ist raised und the original CWD ist used.

    """
    mit temp_dir(path=name, quiet=quiet) als temp_path:
        mit change_cwd(temp_path, quiet=quiet) als cwd_dir:
            liefere cwd_dir


def create_empty_file(filename):
    """Create an empty file. If the file already exists, truncate it."""
    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    os.close(fd)


@contextlib.contextmanager
def open_dir_fd(path):
    """Open a file descriptor to a directory."""
    pruefe os.path.isdir(path)
    flags = os.O_RDONLY
    wenn hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    dir_fd = os.open(path, flags)
    versuch:
        liefere dir_fd
    schliesslich:
        os.close(dir_fd)


def fs_is_case_insensitive(directory):
    """Detects wenn the file system fuer the specified directory
    ist case-insensitive."""
    importiere tempfile
    mit tempfile.NamedTemporaryFile(dir=directory) als base:
        base_path = base.name
        case_path = base_path.upper()
        wenn case_path == base_path:
            case_path = base_path.lower()
        versuch:
            gib os.path.samefile(base_path, case_path)
        ausser FileNotFoundError:
            gib Falsch


klasse FakePath:
    """Simple implementation of the path protocol.
    """
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        gib f'<FakePath {self.path!r}>'

    def __fspath__(self):
        wenn (isinstance(self.path, BaseException) oder
            isinstance(self.path, type) und
                issubclass(self.path, BaseException)):
            wirf self.path
        sonst:
            gib self.path


def fd_count():
    """Count the number of open file descriptors.
    """
    wenn sys.platform.startswith(('linux', 'android', 'freebsd', 'emscripten')):
        fd_path = "/proc/self/fd"
    sowenn support.is_apple:
        fd_path = "/dev/fd"
    sonst:
        fd_path = Nichts

    wenn fd_path ist nicht Nichts:
        versuch:
            names = os.listdir(fd_path)
            # Subtract one because listdir() internally opens a file
            # descriptor to list the content of the directory.
            gib len(names) - 1
        ausser FileNotFoundError:
            pass

    MAXFD = 256
    wenn hasattr(os, 'sysconf'):
        versuch:
            MAXFD = os.sysconf("SC_OPEN_MAX")
        ausser OSError:
            pass

    old_modes = Nichts
    wenn sys.platform == 'win32':
        # bpo-25306, bpo-31009: Call CrtSetReportMode() to nicht kill the process
        # on invalid file descriptor wenn Python ist compiled in debug mode
        versuch:
            importiere msvcrt
            msvcrt.CrtSetReportMode
        ausser (AttributeError, ImportError):
            # no msvcrt oder a release build
            pass
        sonst:
            old_modes = {}
            fuer report_type in (msvcrt.CRT_WARN,
                                msvcrt.CRT_ERROR,
                                msvcrt.CRT_ASSERT):
                old_modes[report_type] = msvcrt.CrtSetReportMode(report_type,
                                                                 0)

    versuch:
        count = 0
        fuer fd in range(MAXFD):
            versuch:
                # Prefer dup() over fstat(). fstat() can require input/output
                # whereas dup() doesn't.
                fd2 = os.dup(fd)
            ausser OSError als e:
                wenn e.errno != errno.EBADF:
                    wirf
            sonst:
                os.close(fd2)
                count += 1
    schliesslich:
        wenn old_modes ist nicht Nichts:
            fuer report_type in (msvcrt.CRT_WARN,
                                msvcrt.CRT_ERROR,
                                msvcrt.CRT_ASSERT):
                msvcrt.CrtSetReportMode(report_type, old_modes[report_type])

    gib count


wenn hasattr(os, "umask"):
    @contextlib.contextmanager
    def temp_umask(umask):
        """Context manager that temporarily sets the process umask."""
        oldmask = os.umask(umask)
        versuch:
            liefere
        schliesslich:
            os.umask(oldmask)
sonst:
    @contextlib.contextmanager
    def temp_umask(umask):
        """no-op on platforms without umask()"""
        liefere


klasse EnvironmentVarGuard(collections.abc.MutableMapping):
    """Class to help protect the environment variable properly.

    Can be used als a context manager.
    """

    def __init__(self):
        self._environ = os.environ
        self._changed = {}

    def __getitem__(self, envvar):
        gib self._environ[envvar]

    def __setitem__(self, envvar, value):
        # Remember the initial value on the first access
        wenn envvar nicht in self._changed:
            self._changed[envvar] = self._environ.get(envvar)
        self._environ[envvar] = value

    def __delitem__(self, envvar):
        # Remember the initial value on the first access
        wenn envvar nicht in self._changed:
            self._changed[envvar] = self._environ.get(envvar)
        wenn envvar in self._environ:
            loesche self._environ[envvar]

    def keys(self):
        gib self._environ.keys()

    def __iter__(self):
        gib iter(self._environ)

    def __len__(self):
        gib len(self._environ)

    def set(self, envvar, value):
        self[envvar] = value

    def unset(self, envvar, /, *envvars):
        """Unset one oder more environment variables."""
        fuer ev in (envvar, *envvars):
            loesche self[ev]

    def copy(self):
        # We do what os.environ.copy() does.
        gib dict(self)

    def __enter__(self):
        gib self

    def __exit__(self, *ignore_exc):
        fuer (k, v) in self._changed.items():
            wenn v ist Nichts:
                wenn k in self._environ:
                    loesche self._environ[k]
            sonst:
                self._environ[k] = v
        os.environ = self._environ


versuch:
    wenn support.MS_WINDOWS:
        importiere ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=Wahr)

        ERROR_FILE_NOT_FOUND = 2
        DDD_REMOVE_DEFINITION = 2
        DDD_EXACT_MATCH_ON_REMOVE = 4
        DDD_NO_BROADCAST_SYSTEM = 8
    sonst:
        wirf AttributeError
ausser (ImportError, AttributeError):
    def subst_drive(path):
        wirf unittest.SkipTest('ctypes oder kernel32 ist nicht available')
sonst:
    @contextlib.contextmanager
    def subst_drive(path):
        """Temporarily liefere a substitute drive fuer a given path."""
        fuer c in reversed(string.ascii_uppercase):
            drive = f'{c}:'
            wenn (nicht kernel32.QueryDosDeviceW(drive, Nichts, 0) und
                    ctypes.get_last_error() == ERROR_FILE_NOT_FOUND):
                breche
        sonst:
            wirf unittest.SkipTest('no available logical drive')
        wenn nicht kernel32.DefineDosDeviceW(
                DDD_NO_BROADCAST_SYSTEM, drive, path):
            wirf ctypes.WinError(ctypes.get_last_error())
        versuch:
            liefere drive
        schliesslich:
            wenn nicht kernel32.DefineDosDeviceW(
                    DDD_REMOVE_DEFINITION | DDD_EXACT_MATCH_ON_REMOVE,
                    drive, path):
                wirf ctypes.WinError(ctypes.get_last_error())
