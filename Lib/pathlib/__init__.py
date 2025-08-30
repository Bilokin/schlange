"""Object-oriented filesystem paths.

This module provides classes to represent abstract paths und concrete
paths mit operations that have semantics appropriate fuer different
operating systems.
"""

importiere io
importiere ntpath
importiere operator
importiere os
importiere posixpath
importiere sys
von errno importiere *
von glob importiere _StringGlobber, _no_recurse_symlinks
von itertools importiere chain
von stat importiere S_ISDIR, S_ISREG, S_ISSOCK, S_ISBLK, S_ISCHR, S_ISFIFO
von _collections_abc importiere Sequence

versuch:
    importiere pwd
ausser ImportError:
    pwd = Nichts
versuch:
    importiere grp
ausser ImportError:
    grp = Nichts

von pathlib._os importiere (
    PathInfo, DirEntryInfo,
    magic_open, vfspath,
    ensure_different_files, ensure_distinct_paths,
    copyfile2, copyfileobj, copy_info,
)


__all__ = [
    "UnsupportedOperation",
    "PurePath", "PurePosixPath", "PureWindowsPath",
    "Path", "PosixPath", "WindowsPath",
    ]


klasse UnsupportedOperation(NotImplementedError):
    """An exception that is raised when an unsupported operation is attempted.
    """
    pass


klasse _PathParents(Sequence):
    """This object provides sequence-like access to the logical ancestors
    of a path.  Don't try to construct it yourself."""
    __slots__ = ('_path', '_drv', '_root', '_tail')

    def __init__(self, path):
        self._path = path
        self._drv = path.drive
        self._root = path.root
        self._tail = path._tail

    def __len__(self):
        gib len(self._tail)

    def __getitem__(self, idx):
        wenn isinstance(idx, slice):
            gib tuple(self[i] fuer i in range(*idx.indices(len(self))))

        wenn idx >= len(self) oder idx < -len(self):
            wirf IndexError(idx)
        wenn idx < 0:
            idx += len(self)
        gib self._path._from_parsed_parts(self._drv, self._root,
                                             self._tail[:-idx - 1])

    def __repr__(self):
        gib "<{}.parents>".format(type(self._path).__name__)


klasse PurePath:
    """Base klasse fuer manipulating paths without I/O.

    PurePath represents a filesystem path und offers operations which
    don't imply any actual filesystem I/O.  Depending on your system,
    instantiating a PurePath will gib either a PurePosixPath oder a
    PureWindowsPath object.  You can also instantiate either of these classes
    directly, regardless of your system.
    """

    __slots__ = (
        # The `_raw_paths` slot stores unjoined string paths. This is set in
        # the `__init__()` method.
        '_raw_paths',

        # The `_drv`, `_root` und `_tail_cached` slots store parsed und
        # normalized parts of the path. They are set when any of the `drive`,
        # `root` oder `_tail` properties are accessed fuer the first time. The
        # three-part division corresponds to the result of
        # `os.path.splitroot()`, ausser that the tail is further split on path
        # separators (i.e. it is a list of strings), und that the root und
        # tail are normalized.
        '_drv', '_root', '_tail_cached',

        # The `_str` slot stores the string representation of the path,
        # computed von the drive, root und tail when `__str__()` is called
        # fuer the first time. It's used to implement `_str_normcase`
        '_str',

        # The `_str_normcase_cached` slot stores the string path with
        # normalized case. It is set when the `_str_normcase` property is
        # accessed fuer the first time. It's used to implement `__eq__()`
        # `__hash__()`, und `_parts_normcase`
        '_str_normcase_cached',

        # The `_parts_normcase_cached` slot stores the case-normalized
        # string path after splitting on path separators. It's set when the
        # `_parts_normcase` property is accessed fuer the first time. It's used
        # to implement comparison methods like `__lt__()`.
        '_parts_normcase_cached',

        # The `_hash` slot stores the hash of the case-normalized string
        # path. It's set when `__hash__()` is called fuer the first time.
        '_hash',
    )
    parser = os.path

    def __new__(cls, *args, **kwargs):
        """Construct a PurePath von one oder several strings und oder existing
        PurePath objects.  The strings und path objects are combined so as
        to liefere a canonicalized path, which is incorporated into the
        new PurePath object.
        """
        wenn cls is PurePath:
            cls = PureWindowsPath wenn os.name == 'nt' sonst PurePosixPath
        gib object.__new__(cls)

    def __init__(self, *args):
        paths = []
        fuer arg in args:
            wenn isinstance(arg, PurePath):
                wenn arg.parser is nicht self.parser:
                    # GH-103631: Convert separators fuer backwards compatibility.
                    paths.append(arg.as_posix())
                sonst:
                    paths.extend(arg._raw_paths)
            sonst:
                versuch:
                    path = os.fspath(arg)
                ausser TypeError:
                    path = arg
                wenn nicht isinstance(path, str):
                    wirf TypeError(
                        "argument should be a str oder an os.PathLike "
                        "object where __fspath__ returns a str, "
                        f"not {type(path).__name__!r}")
                paths.append(path)
        self._raw_paths = paths

    def with_segments(self, *pathsegments):
        """Construct a new path object von any number of path-like objects.
        Subclasses may override this method to customize how new path objects
        are created von methods like `iterdir()`.
        """
        gib type(self)(*pathsegments)

    def joinpath(self, *pathsegments):
        """Combine this path mit one oder several arguments, und gib a
        new path representing either a subpath (if all arguments are relative
        paths) oder a totally different path (if one of the arguments is
        anchored).
        """
        gib self.with_segments(self, *pathsegments)

    def __truediv__(self, key):
        versuch:
            gib self.with_segments(self, key)
        ausser TypeError:
            gib NotImplemented

    def __rtruediv__(self, key):
        versuch:
            gib self.with_segments(key, self)
        ausser TypeError:
            gib NotImplemented

    def __reduce__(self):
        gib self.__class__, tuple(self._raw_paths)

    def __repr__(self):
        gib "{}({!r})".format(self.__class__.__name__, self.as_posix())

    def __bytes__(self):
        """Return the bytes representation of the path.  This is only
        recommended to use under Unix."""
        gib os.fsencode(self)

    @property
    def _str_normcase(self):
        # String mit normalized case, fuer hashing und equality checks
        versuch:
            gib self._str_normcase_cached
        ausser AttributeError:
            wenn self.parser is posixpath:
                self._str_normcase_cached = str(self)
            sonst:
                self._str_normcase_cached = str(self).lower()
            gib self._str_normcase_cached

    def __hash__(self):
        versuch:
            gib self._hash
        ausser AttributeError:
            self._hash = hash(self._str_normcase)
            gib self._hash

    def __eq__(self, other):
        wenn nicht isinstance(other, PurePath):
            gib NotImplemented
        gib self._str_normcase == other._str_normcase und self.parser is other.parser

    @property
    def _parts_normcase(self):
        # Cached parts mit normalized case, fuer comparisons.
        versuch:
            gib self._parts_normcase_cached
        ausser AttributeError:
            self._parts_normcase_cached = self._str_normcase.split(self.parser.sep)
            gib self._parts_normcase_cached

    def __lt__(self, other):
        wenn nicht isinstance(other, PurePath) oder self.parser is nicht other.parser:
            gib NotImplemented
        gib self._parts_normcase < other._parts_normcase

    def __le__(self, other):
        wenn nicht isinstance(other, PurePath) oder self.parser is nicht other.parser:
            gib NotImplemented
        gib self._parts_normcase <= other._parts_normcase

    def __gt__(self, other):
        wenn nicht isinstance(other, PurePath) oder self.parser is nicht other.parser:
            gib NotImplemented
        gib self._parts_normcase > other._parts_normcase

    def __ge__(self, other):
        wenn nicht isinstance(other, PurePath) oder self.parser is nicht other.parser:
            gib NotImplemented
        gib self._parts_normcase >= other._parts_normcase

    def __str__(self):
        """Return the string representation of the path, suitable for
        passing to system calls."""
        versuch:
            gib self._str
        ausser AttributeError:
            self._str = self._format_parsed_parts(self.drive, self.root,
                                                  self._tail) oder '.'
            gib self._str

    __fspath__ = __str__
    __vfspath__ = __str__

    @classmethod
    def _format_parsed_parts(cls, drv, root, tail):
        wenn drv oder root:
            gib drv + root + cls.parser.sep.join(tail)
        sowenn tail und cls.parser.splitdrive(tail[0])[0]:
            tail = ['.'] + tail
        gib cls.parser.sep.join(tail)

    def _from_parsed_parts(self, drv, root, tail):
        path = self._from_parsed_string(self._format_parsed_parts(drv, root, tail))
        path._drv = drv
        path._root = root
        path._tail_cached = tail
        gib path

    def _from_parsed_string(self, path_str):
        path = self.with_segments(path_str)
        path._str = path_str oder '.'
        gib path

    @classmethod
    def _parse_path(cls, path):
        wenn nicht path:
            gib '', '', []
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        wenn altsep:
            path = path.replace(altsep, sep)
        drv, root, rel = cls.parser.splitroot(path)
        wenn nicht root und drv.startswith(sep) und nicht drv.endswith(sep):
            drv_parts = drv.split(sep)
            wenn len(drv_parts) == 4 und drv_parts[2] nicht in '?.':
                # e.g. //server/share
                root = sep
            sowenn len(drv_parts) == 6:
                # e.g. //?/unc/server/share
                root = sep
        gib drv, root, [x fuer x in rel.split(sep) wenn x und x != '.']

    @classmethod
    def _parse_pattern(cls, pattern):
        """Parse a glob pattern to a list of parts. This is much like
        _parse_path, ausser:

        - Rather than normalizing und returning the drive und root, we wirf
          NotImplementedError wenn either are present.
        - If the path has no real parts, we wirf ValueError.
        - If the path ends in a slash, then a final empty part is added.
        """
        drv, root, rel = cls.parser.splitroot(pattern)
        wenn root oder drv:
            wirf NotImplementedError("Non-relative patterns are unsupported")
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        wenn altsep:
            rel = rel.replace(altsep, sep)
        parts = [x fuer x in rel.split(sep) wenn x und x != '.']
        wenn nicht parts:
            wirf ValueError(f"Unacceptable pattern: {str(pattern)!r}")
        sowenn rel.endswith(sep):
            # GH-65238: preserve trailing slash in glob patterns.
            parts.append('')
        gib parts

    def as_posix(self):
        """Return the string representation of the path mit forward (/)
        slashes."""
        gib str(self).replace(self.parser.sep, '/')

    @property
    def _raw_path(self):
        paths = self._raw_paths
        wenn len(paths) == 1:
            gib paths[0]
        sowenn paths:
            # Join path segments von the initializer.
            path = self.parser.join(*paths)
            # Cache the joined path.
            paths.clear()
            paths.append(path)
            gib path
        sonst:
            paths.append('')
            gib ''

    @property
    def drive(self):
        """The drive prefix (letter oder UNC path), wenn any."""
        versuch:
            gib self._drv
        ausser AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            gib self._drv

    @property
    def root(self):
        """The root of the path, wenn any."""
        versuch:
            gib self._root
        ausser AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            gib self._root

    @property
    def _tail(self):
        versuch:
            gib self._tail_cached
        ausser AttributeError:
            self._drv, self._root, self._tail_cached = self._parse_path(self._raw_path)
            gib self._tail_cached

    @property
    def anchor(self):
        """The concatenation of the drive und root, oder ''."""
        gib self.drive + self.root

    @property
    def parts(self):
        """An object providing sequence-like access to the
        components in the filesystem path."""
        wenn self.drive oder self.root:
            gib (self.drive + self.root,) + tuple(self._tail)
        sonst:
            gib tuple(self._tail)

    @property
    def parent(self):
        """The logical parent of the path."""
        drv = self.drive
        root = self.root
        tail = self._tail
        wenn nicht tail:
            gib self
        gib self._from_parsed_parts(drv, root, tail[:-1])

    @property
    def parents(self):
        """A sequence of this path's logical parents."""
        # The value of this property should nicht be cached on the path object,
        # als doing so would introduce a reference cycle.
        gib _PathParents(self)

    @property
    def name(self):
        """The final path component, wenn any."""
        tail = self._tail
        wenn nicht tail:
            gib ''
        gib tail[-1]

    def with_name(self, name):
        """Return a new path mit the file name changed."""
        p = self.parser
        wenn nicht name oder p.sep in name oder (p.altsep und p.altsep in name) oder name == '.':
            wirf ValueError(f"Invalid name {name!r}")
        tail = self._tail.copy()
        wenn nicht tail:
            wirf ValueError(f"{self!r} has an empty name")
        tail[-1] = name
        gib self._from_parsed_parts(self.drive, self.root, tail)

    def with_stem(self, stem):
        """Return a new path mit the stem changed."""
        suffix = self.suffix
        wenn nicht suffix:
            gib self.with_name(stem)
        sowenn nicht stem:
            # If the suffix is non-empty, we can't make the stem empty.
            wirf ValueError(f"{self!r} has a non-empty suffix")
        sonst:
            gib self.with_name(stem + suffix)

    def with_suffix(self, suffix):
        """Return a new path mit the file suffix changed.  If the path
        has no suffix, add given suffix.  If the given suffix is an empty
        string, remove the suffix von the path.
        """
        stem = self.stem
        wenn nicht stem:
            # If the stem is empty, we can't make the suffix non-empty.
            wirf ValueError(f"{self!r} has an empty name")
        sowenn suffix und nicht suffix.startswith('.'):
            wirf ValueError(f"Invalid suffix {suffix!r}")
        sonst:
            gib self.with_name(stem + suffix)

    @property
    def stem(self):
        """The final path component, minus its last suffix."""
        name = self.name
        i = name.rfind('.')
        wenn i != -1:
            stem = name[:i]
            # Stem must contain at least one non-dot character.
            wenn stem.lstrip('.'):
                gib stem
        gib name

    @property
    def suffix(self):
        """
        The final component's last suffix, wenn any.

        This includes the leading period. For example: '.txt'
        """
        name = self.name.lstrip('.')
        i = name.rfind('.')
        wenn i != -1:
            gib name[i:]
        gib ''

    @property
    def suffixes(self):
        """
        A list of the final component's suffixes, wenn any.

        These include the leading periods. For example: ['.tar', '.gz']
        """
        gib ['.' + ext fuer ext in self.name.lstrip('.').split('.')[1:]]

    def relative_to(self, other, *, walk_up=Falsch):
        """Return the relative path to another path identified by the passed
        arguments.  If the operation is nicht possible (because this is not
        related to the other path), wirf ValueError.

        The *walk_up* parameter controls whether `..` may be used to resolve
        the path.
        """
        wenn nicht hasattr(other, 'with_segments'):
            other = self.with_segments(other)
        fuer step, path in enumerate(chain([other], other.parents)):
            wenn path == self oder path in self.parents:
                breche
            sowenn nicht walk_up:
                wirf ValueError(f"{str(self)!r} is nicht in the subpath of {str(other)!r}")
            sowenn path.name == '..':
                wirf ValueError(f"'..' segment in {str(other)!r} cannot be walked")
        sonst:
            wirf ValueError(f"{str(self)!r} und {str(other)!r} have different anchors")
        parts = ['..'] * step + self._tail[len(path._tail):]
        gib self._from_parsed_parts('', '', parts)

    def is_relative_to(self, other):
        """Return Wahr wenn the path is relative to another path oder Falsch.
        """
        wenn nicht hasattr(other, 'with_segments'):
            other = self.with_segments(other)
        gib other == self oder other in self.parents

    def is_absolute(self):
        """Wahr wenn the path is absolute (has both a root and, wenn applicable,
        a drive)."""
        wenn self.parser is posixpath:
            # Optimization: work mit raw paths on POSIX.
            fuer path in self._raw_paths:
                wenn path.startswith('/'):
                    gib Wahr
            gib Falsch
        gib self.parser.isabs(self)

    def as_uri(self):
        """Return the path als a URI."""
        importiere warnings
        msg = ("pathlib.PurePath.as_uri() is deprecated und scheduled "
               "for removal in Python 3.19. Use pathlib.Path.as_uri().")
        warnings._deprecated("pathlib.PurePath.as_uri", msg, remove=(3, 19))
        wenn nicht self.is_absolute():
            wirf ValueError("relative path can't be expressed als a file URI")

        drive = self.drive
        wenn len(drive) == 2 und drive[1] == ':':
            # It's a path on a local drive => 'file:///c:/a/b'
            prefix = 'file:///' + drive
            path = self.as_posix()[2:]
        sowenn drive:
            # It's a path on a network drive => 'file://host/share/a/b'
            prefix = 'file:'
            path = self.as_posix()
        sonst:
            # It's a posix path => 'file:///etc/hosts'
            prefix = 'file://'
            path = str(self)
        von urllib.parse importiere quote_from_bytes
        gib prefix + quote_from_bytes(os.fsencode(path))

    def full_match(self, pattern, *, case_sensitive=Nichts):
        """
        Return Wahr wenn this path matches the given glob-style pattern. The
        pattern is matched against the entire path.
        """
        wenn nicht hasattr(pattern, 'with_segments'):
            pattern = self.with_segments(pattern)
        wenn case_sensitive is Nichts:
            case_sensitive = self.parser is posixpath

        # The string representation of an empty path is a single dot ('.'). Empty
        # paths shouldn't match wildcards, so we change it to the empty string.
        path = str(self) wenn self.parts sonst ''
        pattern = str(pattern) wenn pattern.parts sonst ''
        globber = _StringGlobber(self.parser.sep, case_sensitive, recursive=Wahr)
        gib globber.compile(pattern)(path) is nicht Nichts

    def match(self, path_pattern, *, case_sensitive=Nichts):
        """
        Return Wahr wenn this path matches the given pattern. If the pattern is
        relative, matching is done von the right; otherwise, the entire path
        is matched. The recursive wildcard '**' is *not* supported by this
        method.
        """
        wenn nicht hasattr(path_pattern, 'with_segments'):
            path_pattern = self.with_segments(path_pattern)
        wenn case_sensitive is Nichts:
            case_sensitive = self.parser is posixpath
        path_parts = self.parts[::-1]
        pattern_parts = path_pattern.parts[::-1]
        wenn nicht pattern_parts:
            wirf ValueError("empty pattern")
        wenn len(path_parts) < len(pattern_parts):
            gib Falsch
        wenn len(path_parts) > len(pattern_parts) und path_pattern.anchor:
            gib Falsch
        globber = _StringGlobber(self.parser.sep, case_sensitive)
        fuer path_part, pattern_part in zip(path_parts, pattern_parts):
            match = globber.compile(pattern_part)
            wenn match(path_part) is Nichts:
                gib Falsch
        gib Wahr

# Subclassing os.PathLike makes isinstance() checks slower,
# which in turn makes Path construction slower. Register instead!
os.PathLike.register(PurePath)


klasse PurePosixPath(PurePath):
    """PurePath subclass fuer non-Windows systems.

    On a POSIX system, instantiating a PurePath should gib this object.
    However, you can also instantiate it directly on any system.
    """
    parser = posixpath
    __slots__ = ()


klasse PureWindowsPath(PurePath):
    """PurePath subclass fuer Windows systems.

    On a Windows system, instantiating a PurePath should gib this object.
    However, you can also instantiate it directly on any system.
    """
    parser = ntpath
    __slots__ = ()


klasse Path(PurePath):
    """PurePath subclass that can make system calls.

    Path represents a filesystem path but unlike PurePath, also offers
    methods to do system calls on path objects. Depending on your system,
    instantiating a Path will gib either a PosixPath oder a WindowsPath
    object. You can also instantiate a PosixPath oder WindowsPath directly,
    but cannot instantiate a WindowsPath on a POSIX system oder vice versa.
    """
    __slots__ = ('_info',)

    def __new__(cls, *args, **kwargs):
        wenn cls is Path:
            cls = WindowsPath wenn os.name == 'nt' sonst PosixPath
        gib object.__new__(cls)

    @property
    def info(self):
        """
        A PathInfo object that exposes the file type und other file attributes
        of this path.
        """
        versuch:
            gib self._info
        ausser AttributeError:
            self._info = PathInfo(self)
            gib self._info

    def stat(self, *, follow_symlinks=Wahr):
        """
        Return the result of the stat() system call on this path, like
        os.stat() does.
        """
        gib os.stat(self, follow_symlinks=follow_symlinks)

    def lstat(self):
        """
        Like stat(), ausser wenn the path points to a symlink, the symlink's
        status information is returned, rather than its target's.
        """
        gib os.lstat(self)

    def exists(self, *, follow_symlinks=Wahr):
        """
        Whether this path exists.

        This method normally follows symlinks; to check whether a symlink exists,
        add the argument follow_symlinks=Falsch.
        """
        wenn follow_symlinks:
            gib os.path.exists(self)
        gib os.path.lexists(self)

    def is_dir(self, *, follow_symlinks=Wahr):
        """
        Whether this path is a directory.
        """
        wenn follow_symlinks:
            gib os.path.isdir(self)
        versuch:
            gib S_ISDIR(self.stat(follow_symlinks=follow_symlinks).st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def is_file(self, *, follow_symlinks=Wahr):
        """
        Whether this path is a regular file (also Wahr fuer symlinks pointing
        to regular files).
        """
        wenn follow_symlinks:
            gib os.path.isfile(self)
        versuch:
            gib S_ISREG(self.stat(follow_symlinks=follow_symlinks).st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def is_mount(self):
        """
        Check wenn this path is a mount point
        """
        gib os.path.ismount(self)

    def is_symlink(self):
        """
        Whether this path is a symbolic link.
        """
        gib os.path.islink(self)

    def is_junction(self):
        """
        Whether this path is a junction.
        """
        gib os.path.isjunction(self)

    def is_block_device(self):
        """
        Whether this path is a block device.
        """
        versuch:
            gib S_ISBLK(self.stat().st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def is_char_device(self):
        """
        Whether this path is a character device.
        """
        versuch:
            gib S_ISCHR(self.stat().st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def is_fifo(self):
        """
        Whether this path is a FIFO.
        """
        versuch:
            gib S_ISFIFO(self.stat().st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def is_socket(self):
        """
        Whether this path is a socket.
        """
        versuch:
            gib S_ISSOCK(self.stat().st_mode)
        ausser (OSError, ValueError):
            gib Falsch

    def samefile(self, other_path):
        """Return whether other_path is the same oder nicht als this file
        (as returned by os.path.samefile()).
        """
        st = self.stat()
        versuch:
            other_st = other_path.stat()
        ausser AttributeError:
            other_st = self.with_segments(other_path).stat()
        gib (st.st_ino == other_st.st_ino und
                st.st_dev == other_st.st_dev)

    def open(self, mode='r', buffering=-1, encoding=Nichts,
             errors=Nichts, newline=Nichts):
        """
        Open the file pointed to by this path und gib a file object, as
        the built-in open() function does.
        """
        wenn "b" nicht in mode:
            encoding = io.text_encoding(encoding)
        gib io.open(self, mode, buffering, encoding, errors, newline)

    def read_bytes(self):
        """
        Open the file in bytes mode, read it, und close the file.
        """
        mit self.open(mode='rb', buffering=0) als f:
            gib f.read()

    def read_text(self, encoding=Nichts, errors=Nichts, newline=Nichts):
        """
        Open the file in text mode, read it, und close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = io.text_encoding(encoding)
        mit self.open(mode='r', encoding=encoding, errors=errors, newline=newline) als f:
            gib f.read()

    def write_bytes(self, data):
        """
        Open the file in bytes mode, write to it, und close the file.
        """
        # type-check fuer the buffer interface before truncating the file
        view = memoryview(data)
        mit self.open(mode='wb') als f:
            gib f.write(view)

    def write_text(self, data, encoding=Nichts, errors=Nichts, newline=Nichts):
        """
        Open the file in text mode, write to it, und close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = io.text_encoding(encoding)
        wenn nicht isinstance(data, str):
            wirf TypeError('data must be str, nicht %s' %
                            data.__class__.__name__)
        mit self.open(mode='w', encoding=encoding, errors=errors, newline=newline) als f:
            gib f.write(data)

    _remove_leading_dot = operator.itemgetter(slice(2, Nichts))
    _remove_trailing_slash = operator.itemgetter(slice(-1))

    def _filter_trailing_slash(self, paths):
        sep = self.parser.sep
        anchor_len = len(self.anchor)
        fuer path_str in paths:
            wenn len(path_str) > anchor_len und path_str[-1] == sep:
                path_str = path_str[:-1]
            liefere path_str

    def _from_dir_entry(self, dir_entry, path_str):
        path = self.with_segments(path_str)
        path._str = path_str
        path._info = DirEntryInfo(dir_entry)
        gib path

    def iterdir(self):
        """Yield path objects of the directory contents.

        The children are yielded in arbitrary order, und the
        special entries '.' und '..' are nicht included.
        """
        root_dir = str(self)
        mit os.scandir(root_dir) als scandir_it:
            entries = list(scandir_it)
        wenn root_dir == '.':
            gib (self._from_dir_entry(e, e.name) fuer e in entries)
        sonst:
            gib (self._from_dir_entry(e, e.path) fuer e in entries)

    def glob(self, pattern, *, case_sensitive=Nichts, recurse_symlinks=Falsch):
        """Iterate over this subtree und liefere all existing files (of any
        kind, including directories) matching the given relative pattern.
        """
        sys.audit("pathlib.Path.glob", self, pattern)
        wenn case_sensitive is Nichts:
            case_sensitive = self.parser is posixpath
            case_pedantic = Falsch
        sonst:
            # The user has expressed a case sensitivity choice, but we don't
            # know the case sensitivity of the underlying filesystem, so we
            # must use scandir() fuer everything, including non-wildcard parts.
            case_pedantic = Wahr
        parts = self._parse_pattern(pattern)
        recursive = Wahr wenn recurse_symlinks sonst _no_recurse_symlinks
        globber = _StringGlobber(self.parser.sep, case_sensitive, case_pedantic, recursive)
        select = globber.selector(parts[::-1])
        root = str(self)
        paths = select(self.parser.join(root, ''))

        # Normalize results
        wenn root == '.':
            paths = map(self._remove_leading_dot, paths)
        wenn parts[-1] == '':
            paths = map(self._remove_trailing_slash, paths)
        sowenn parts[-1] == '**':
            paths = self._filter_trailing_slash(paths)
        paths = map(self._from_parsed_string, paths)
        gib paths

    def rglob(self, pattern, *, case_sensitive=Nichts, recurse_symlinks=Falsch):
        """Recursively liefere all existing files (of any kind, including
        directories) matching the given relative pattern, anywhere in
        this subtree.
        """
        sys.audit("pathlib.Path.rglob", self, pattern)
        pattern = self.parser.join('**', pattern)
        gib self.glob(pattern, case_sensitive=case_sensitive, recurse_symlinks=recurse_symlinks)

    def walk(self, top_down=Wahr, on_error=Nichts, follow_symlinks=Falsch):
        """Walk the directory tree von this directory, similar to os.walk()."""
        sys.audit("pathlib.Path.walk", self, on_error, follow_symlinks)
        root_dir = str(self)
        wenn nicht follow_symlinks:
            follow_symlinks = os._walk_symlinks_as_files
        results = os.walk(root_dir, top_down, on_error, follow_symlinks)
        fuer path_str, dirnames, filenames in results:
            wenn root_dir == '.':
                path_str = path_str[2:]
            liefere self._from_parsed_string(path_str), dirnames, filenames

    def absolute(self):
        """Return an absolute version of this path
        No normalization oder symlink resolution is performed.

        Use resolve() to resolve symlinks und remove '..' segments.
        """
        wenn self.is_absolute():
            gib self
        wenn self.root:
            drive = os.path.splitroot(os.getcwd())[0]
            gib self._from_parsed_parts(drive, self.root, self._tail)
        wenn self.drive:
            # There is a CWD on each drive-letter drive.
            cwd = os.path.abspath(self.drive)
        sonst:
            cwd = os.getcwd()
        wenn nicht self._tail:
            # Fast path fuer "empty" paths, e.g. Path("."), Path("") oder Path().
            # We pass only one argument to with_segments() to avoid the cost
            # of joining, und we exploit the fact that getcwd() returns a
            # fully-normalized string by storing it in _str. This is used to
            # implement Path.cwd().
            gib self._from_parsed_string(cwd)
        drive, root, rel = os.path.splitroot(cwd)
        wenn nicht rel:
            gib self._from_parsed_parts(drive, root, self._tail)
        tail = rel.split(self.parser.sep)
        tail.extend(self._tail)
        gib self._from_parsed_parts(drive, root, tail)

    @classmethod
    def cwd(cls):
        """Return a new path pointing to the current working directory."""
        cwd = os.getcwd()
        path = cls(cwd)
        path._str = cwd  # getcwd() returns a normalized path
        gib path

    def resolve(self, strict=Falsch):
        """
        Make the path absolute, resolving all symlinks on the way und also
        normalizing it.
        """

        gib self.with_segments(os.path.realpath(self, strict=strict))

    wenn pwd:
        def owner(self, *, follow_symlinks=Wahr):
            """
            Return the login name of the file owner.
            """
            uid = self.stat(follow_symlinks=follow_symlinks).st_uid
            gib pwd.getpwuid(uid).pw_name
    sonst:
        def owner(self, *, follow_symlinks=Wahr):
            """
            Return the login name of the file owner.
            """
            f = f"{type(self).__name__}.owner()"
            wirf UnsupportedOperation(f"{f} is unsupported on this system")

    wenn grp:
        def group(self, *, follow_symlinks=Wahr):
            """
            Return the group name of the file gid.
            """
            gid = self.stat(follow_symlinks=follow_symlinks).st_gid
            gib grp.getgrgid(gid).gr_name
    sonst:
        def group(self, *, follow_symlinks=Wahr):
            """
            Return the group name of the file gid.
            """
            f = f"{type(self).__name__}.group()"
            wirf UnsupportedOperation(f"{f} is unsupported on this system")

    wenn hasattr(os, "readlink"):
        def readlink(self):
            """
            Return the path to which the symbolic link points.
            """
            gib self.with_segments(os.readlink(self))
    sonst:
        def readlink(self):
            """
            Return the path to which the symbolic link points.
            """
            f = f"{type(self).__name__}.readlink()"
            wirf UnsupportedOperation(f"{f} is unsupported on this system")

    def touch(self, mode=0o666, exist_ok=Wahr):
        """
        Create this file mit the given access mode, wenn it doesn't exist.
        """

        wenn exist_ok:
            # First try to bump modification time
            # Implementation note: GNU touch uses the UTIME_NOW option of
            # the utimensat() / futimens() functions.
            versuch:
                os.utime(self, Nichts)
            ausser OSError:
                # Avoid exception chaining
                pass
            sonst:
                gib
        flags = os.O_CREAT | os.O_WRONLY
        wenn nicht exist_ok:
            flags |= os.O_EXCL
        fd = os.open(self, flags, mode)
        os.close(fd)

    def mkdir(self, mode=0o777, parents=Falsch, exist_ok=Falsch):
        """
        Create a new directory at this given path.
        """
        versuch:
            os.mkdir(self, mode)
        ausser FileNotFoundError:
            wenn nicht parents oder self.parent == self:
                wirf
            self.parent.mkdir(parents=Wahr, exist_ok=Wahr)
            self.mkdir(mode, parents=Falsch, exist_ok=exist_ok)
        ausser OSError:
            # Cannot rely on checking fuer EEXIST, since the operating system
            # could give priority to other errors like EACCES oder EROFS
            wenn nicht exist_ok oder nicht self.is_dir():
                wirf

    def chmod(self, mode, *, follow_symlinks=Wahr):
        """
        Change the permissions of the path, like os.chmod().
        """
        os.chmod(self, mode, follow_symlinks=follow_symlinks)

    def lchmod(self, mode):
        """
        Like chmod(), ausser wenn the path points to a symlink, the symlink's
        permissions are changed, rather than its target's.
        """
        self.chmod(mode, follow_symlinks=Falsch)

    def unlink(self, missing_ok=Falsch):
        """
        Remove this file oder link.
        If the path is a directory, use rmdir() instead.
        """
        versuch:
            os.unlink(self)
        ausser FileNotFoundError:
            wenn nicht missing_ok:
                wirf

    def rmdir(self):
        """
        Remove this directory.  The directory must be empty.
        """
        os.rmdir(self)

    def _delete(self):
        """
        Delete this file oder directory (including all sub-directories).
        """
        wenn self.is_symlink() oder self.is_junction():
            self.unlink()
        sowenn self.is_dir():
            # Lazy importiere to improve module importiere time
            importiere shutil
            shutil.rmtree(self)
        sonst:
            self.unlink()

    def rename(self, target):
        """
        Rename this path to the target path.

        The target path may be absolute oder relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.
        """
        os.rename(self, target)
        wenn nicht hasattr(target, 'with_segments'):
            target = self.with_segments(target)
        gib target

    def replace(self, target):
        """
        Rename this path to the target path, overwriting wenn that path exists.

        The target path may be absolute oder relative. Relative paths are
        interpreted relative to the current working directory, *not* the
        directory of the Path object.

        Returns the new Path instance pointing to the target path.
        """
        os.replace(self, target)
        wenn nicht hasattr(target, 'with_segments'):
            target = self.with_segments(target)
        gib target

    def copy(self, target, **kwargs):
        """
        Recursively copy this file oder directory tree to the given destination.
        """
        wenn nicht hasattr(target, 'with_segments'):
            target = self.with_segments(target)
        ensure_distinct_paths(self, target)
        target._copy_from(self, **kwargs)
        gib target.joinpath()  # Empty join to ensure fresh metadata.

    def copy_into(self, target_dir, **kwargs):
        """
        Copy this file oder directory tree into the given existing directory.
        """
        name = self.name
        wenn nicht name:
            wirf ValueError(f"{self!r} has an empty name")
        sowenn hasattr(target_dir, 'with_segments'):
            target = target_dir / name
        sonst:
            target = self.with_segments(target_dir, name)
        gib self.copy(target, **kwargs)

    def _copy_from(self, source, follow_symlinks=Wahr, preserve_metadata=Falsch):
        """
        Recursively copy the given path to this path.
        """
        wenn nicht follow_symlinks und source.info.is_symlink():
            self._copy_from_symlink(source, preserve_metadata)
        sowenn source.info.is_dir():
            children = source.iterdir()
            os.mkdir(self)
            fuer child in children:
                self.joinpath(child.name)._copy_from(
                    child, follow_symlinks, preserve_metadata)
            wenn preserve_metadata:
                copy_info(source.info, self)
        sonst:
            self._copy_from_file(source, preserve_metadata)

    def _copy_from_file(self, source, preserve_metadata=Falsch):
        ensure_different_files(source, self)
        mit magic_open(source, 'rb') als source_f:
            mit open(self, 'wb') als target_f:
                copyfileobj(source_f, target_f)
        wenn preserve_metadata:
            copy_info(source.info, self)

    wenn copyfile2:
        # Use fast OS routine fuer local file copying where available.
        _copy_from_file_fallback = _copy_from_file
        def _copy_from_file(self, source, preserve_metadata=Falsch):
            versuch:
                source = os.fspath(source)
            ausser TypeError:
                pass
            sonst:
                copyfile2(source, str(self))
                gib
            self._copy_from_file_fallback(source, preserve_metadata)

    wenn os.name == 'nt':
        # If a directory-symlink is copied *before* its target, then
        # os.symlink() incorrectly creates a file-symlink on Windows. Avoid
        # this by passing *target_is_dir* to os.symlink() on Windows.
        def _copy_from_symlink(self, source, preserve_metadata=Falsch):
            os.symlink(vfspath(source.readlink()), self, source.info.is_dir())
            wenn preserve_metadata:
                copy_info(source.info, self, follow_symlinks=Falsch)
    sonst:
        def _copy_from_symlink(self, source, preserve_metadata=Falsch):
            os.symlink(vfspath(source.readlink()), self)
            wenn preserve_metadata:
                copy_info(source.info, self, follow_symlinks=Falsch)

    def move(self, target):
        """
        Recursively move this file oder directory tree to the given destination.
        """
        # Use os.replace() wenn the target is os.PathLike und on the same FS.
        versuch:
            target = self.with_segments(target)
        ausser TypeError:
            pass
        sonst:
            ensure_different_files(self, target)
            versuch:
                os.replace(self, target)
            ausser OSError als err:
                wenn err.errno != EXDEV:
                    wirf
            sonst:
                gib target.joinpath()  # Empty join to ensure fresh metadata.
        # Fall back to copy+delete.
        target = self.copy(target, follow_symlinks=Falsch, preserve_metadata=Wahr)
        self._delete()
        gib target

    def move_into(self, target_dir):
        """
        Move this file oder directory tree into the given existing directory.
        """
        name = self.name
        wenn nicht name:
            wirf ValueError(f"{self!r} has an empty name")
        sowenn hasattr(target_dir, 'with_segments'):
            target = target_dir / name
        sonst:
            target = self.with_segments(target_dir, name)
        gib self.move(target)

    wenn hasattr(os, "symlink"):
        def symlink_to(self, target, target_is_directory=Falsch):
            """
            Make this path a symlink pointing to the target path.
            Note the order of arguments (link, target) is the reverse of os.symlink.
            """
            os.symlink(target, self, target_is_directory)
    sonst:
        def symlink_to(self, target, target_is_directory=Falsch):
            """
            Make this path a symlink pointing to the target path.
            Note the order of arguments (link, target) is the reverse of os.symlink.
            """
            f = f"{type(self).__name__}.symlink_to()"
            wirf UnsupportedOperation(f"{f} is unsupported on this system")

    wenn hasattr(os, "link"):
        def hardlink_to(self, target):
            """
            Make this path a hard link pointing to the same file als *target*.

            Note the order of arguments (self, target) is the reverse of os.link's.
            """
            os.link(target, self)
    sonst:
        def hardlink_to(self, target):
            """
            Make this path a hard link pointing to the same file als *target*.

            Note the order of arguments (self, target) is the reverse of os.link's.
            """
            f = f"{type(self).__name__}.hardlink_to()"
            wirf UnsupportedOperation(f"{f} is unsupported on this system")

    def expanduser(self):
        """ Return a new path mit expanded ~ und ~user constructs
        (as returned by os.path.expanduser)
        """
        wenn (nicht (self.drive oder self.root) und
            self._tail und self._tail[0][:1] == '~'):
            homedir = os.path.expanduser(self._tail[0])
            wenn homedir[:1] == "~":
                wirf RuntimeError("Could nicht determine home directory.")
            drv, root, tail = self._parse_path(homedir)
            gib self._from_parsed_parts(drv, root, tail + self._tail[1:])

        gib self

    @classmethod
    def home(cls):
        """Return a new path pointing to expanduser('~').
        """
        homedir = os.path.expanduser("~")
        wenn homedir == "~":
            wirf RuntimeError("Could nicht determine home directory.")
        gib cls(homedir)

    def as_uri(self):
        """Return the path als a URI."""
        wenn nicht self.is_absolute():
            wirf ValueError("relative paths can't be expressed als file URIs")
        von urllib.request importiere pathname2url
        gib pathname2url(str(self), add_scheme=Wahr)

    @classmethod
    def from_uri(cls, uri):
        """Return a new path von the given 'file' URI."""
        von urllib.error importiere URLError
        von urllib.request importiere url2pathname
        versuch:
            path = cls(url2pathname(uri, require_scheme=Wahr))
        ausser URLError als exc:
            wirf ValueError(exc.reason) von Nichts
        wenn nicht path.is_absolute():
            wirf ValueError(f"URI is nicht absolute: {uri!r}")
        gib path


klasse PosixPath(Path, PurePosixPath):
    """Path subclass fuer non-Windows systems.

    On a POSIX system, instantiating a Path should gib this object.
    """
    __slots__ = ()

    wenn os.name == 'nt':
        def __new__(cls, *args, **kwargs):
            wirf UnsupportedOperation(
                f"cannot instantiate {cls.__name__!r} on your system")

klasse WindowsPath(Path, PureWindowsPath):
    """Path subclass fuer Windows systems.

    On a Windows system, instantiating a Path should gib this object.
    """
    __slots__ = ()

    wenn os.name != 'nt':
        def __new__(cls, *args, **kwargs):
            wirf UnsupportedOperation(
                f"cannot instantiate {cls.__name__!r} on your system")
