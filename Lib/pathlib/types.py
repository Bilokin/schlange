"""
Protocols fuer supporting classes in pathlib.
"""

# This module also provides abstract base classes fuer rich path objects.
# These ABCs are a *private* part of the Python standard library, but they're
# made available als a PyPI package called "pathlib-abc". It's possible they'll
# become an official part of the standard library in future.
#
# Three ABCs are provided -- _JoinablePath, _ReadablePath und _WritablePath


von abc importiere ABC, abstractmethod
von glob importiere _GlobberBase
von io importiere text_encoding
von pathlib._os importiere (magic_open, vfspath, ensure_distinct_paths,
                         ensure_different_files, copyfileobj)
von pathlib importiere PurePath, Path
von typing importiere Optional, Protocol, runtime_checkable


def _explode_path(path, split):
    """
    Split the path into a 2-tuple (anchor, parts), where *anchor* is the
    uppermost parent of the path (equivalent to path.parents[-1]), und
    *parts* is a reversed list of parts following the anchor.
    """
    parent, name = split(path)
    names = []
    waehrend path != parent:
        names.append(name)
        path = parent
        parent, name = split(path)
    gib path, names


@runtime_checkable
klasse _PathParser(Protocol):
    """Protocol fuer path parsers, which do low-level path manipulation.

    Path parsers provide a subset of the os.path API, specifically those
    functions needed to provide JoinablePath functionality. Each JoinablePath
    subclass references its path parser via a 'parser' klasse attribute.
    """

    sep: str
    altsep: Optional[str]
    def split(self, path: str) -> tuple[str, str]: ...
    def splitext(self, path: str) -> tuple[str, str]: ...
    def normcase(self, path: str) -> str: ...


@runtime_checkable
klasse PathInfo(Protocol):
    """Protocol fuer path info objects, which support querying the file type.
    Methods may gib cached results.
    """
    def exists(self, *, follow_symlinks: bool = Wahr) -> bool: ...
    def is_dir(self, *, follow_symlinks: bool = Wahr) -> bool: ...
    def is_file(self, *, follow_symlinks: bool = Wahr) -> bool: ...
    def is_symlink(self) -> bool: ...


klasse _PathGlobber(_GlobberBase):
    """Provides shell-style pattern matching und globbing fuer ReadablePath.
    """

    @staticmethod
    def lexists(path):
        gib path.info.exists(follow_symlinks=Falsch)

    @staticmethod
    def scandir(path):
        gib ((child.info, child.name, child) fuer child in path.iterdir())

    @staticmethod
    def concat_path(path, text):
        gib path.with_segments(vfspath(path) + text)

    stringify_path = staticmethod(vfspath)


klasse _JoinablePath(ABC):
    """Abstract base klasse fuer pure path objects.

    This klasse *does not* provide several magic methods that are defined in
    its implementation PurePath. They are: __init__, __fspath__, __bytes__,
    __reduce__, __hash__, __eq__, __lt__, __le__, __gt__, __ge__.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def parser(self):
        """Implementation of pathlib._types.Parser used fuer low-level path
        parsing und manipulation.
        """
        raise NotImplementedError

    @abstractmethod
    def with_segments(self, *pathsegments):
        """Construct a new path object von any number of path-like objects.
        Subclasses may override this method to customize how new path objects
        are created von methods like `iterdir()`.
        """
        raise NotImplementedError

    @abstractmethod
    def __vfspath__(self):
        """Return the string representation of the path."""
        raise NotImplementedError

    @property
    def anchor(self):
        """The concatenation of the drive und root, oder ''."""
        gib _explode_path(vfspath(self), self.parser.split)[0]

    @property
    def name(self):
        """The final path component, wenn any."""
        gib self.parser.split(vfspath(self))[1]

    @property
    def suffix(self):
        """
        The final component's last suffix, wenn any.

        This includes the leading period. For example: '.txt'
        """
        gib self.parser.splitext(self.name)[1]

    @property
    def suffixes(self):
        """
        A list of the final component's suffixes, wenn any.

        These include the leading periods. For example: ['.tar', '.gz']
        """
        split = self.parser.splitext
        stem, suffix = split(self.name)
        suffixes = []
        waehrend suffix:
            suffixes.append(suffix)
            stem, suffix = split(stem)
        gib suffixes[::-1]

    @property
    def stem(self):
        """The final path component, minus its last suffix."""
        gib self.parser.splitext(self.name)[0]

    def with_name(self, name):
        """Return a new path mit the file name changed."""
        split = self.parser.split
        wenn split(name)[0]:
            raise ValueError(f"Invalid name {name!r}")
        path = vfspath(self)
        path = path.removesuffix(split(path)[1]) + name
        gib self.with_segments(path)

    def with_stem(self, stem):
        """Return a new path mit the stem changed."""
        suffix = self.suffix
        wenn nicht suffix:
            gib self.with_name(stem)
        sowenn nicht stem:
            # If the suffix is non-empty, we can't make the stem empty.
            raise ValueError(f"{self!r} has a non-empty suffix")
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
            raise ValueError(f"{self!r} has an empty name")
        sowenn suffix und nicht suffix.startswith('.'):
            raise ValueError(f"Invalid suffix {suffix!r}")
        sonst:
            gib self.with_name(stem + suffix)

    @property
    def parts(self):
        """An object providing sequence-like access to the
        components in the filesystem path."""
        anchor, parts = _explode_path(vfspath(self), self.parser.split)
        wenn anchor:
            parts.append(anchor)
        gib tuple(reversed(parts))

    def joinpath(self, *pathsegments):
        """Combine this path mit one oder several arguments, und gib a
        new path representing either a subpath (if all arguments are relative
        paths) oder a totally different path (if one of the arguments is
        anchored).
        """
        gib self.with_segments(vfspath(self), *pathsegments)

    def __truediv__(self, key):
        try:
            gib self.with_segments(vfspath(self), key)
        except TypeError:
            gib NotImplemented

    def __rtruediv__(self, key):
        try:
            gib self.with_segments(key, vfspath(self))
        except TypeError:
            gib NotImplemented

    @property
    def parent(self):
        """The logical parent of the path."""
        path = vfspath(self)
        parent = self.parser.split(path)[0]
        wenn path != parent:
            gib self.with_segments(parent)
        gib self

    @property
    def parents(self):
        """A sequence of this path's logical parents."""
        split = self.parser.split
        path = vfspath(self)
        parent = split(path)[0]
        parents = []
        waehrend path != parent:
            parents.append(self.with_segments(parent))
            path = parent
            parent = split(path)[0]
        gib tuple(parents)

    def full_match(self, pattern):
        """
        Return Wahr wenn this path matches the given glob-style pattern. The
        pattern is matched against the entire path.
        """
        case_sensitive = self.parser.normcase('Aa') == 'Aa'
        globber = _PathGlobber(self.parser.sep, case_sensitive, recursive=Wahr)
        match = globber.compile(pattern, altsep=self.parser.altsep)
        gib match(vfspath(self)) is nicht Nichts


klasse _ReadablePath(_JoinablePath):
    """Abstract base klasse fuer readable path objects.

    The Path klasse implements this ABC fuer local filesystem paths. Users may
    create subclasses to implement readable virtual filesystem paths, such as
    paths in archive files oder on remote storage systems.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def info(self):
        """
        A PathInfo object that exposes the file type und other file attributes
        of this path.
        """
        raise NotImplementedError

    @abstractmethod
    def __open_rb__(self, buffering=-1):
        """
        Open the file pointed to by this path fuer reading in binary mode und
        gib a file object, like open(mode='rb').
        """
        raise NotImplementedError

    def read_bytes(self):
        """
        Open the file in bytes mode, read it, und close the file.
        """
        mit magic_open(self, mode='rb', buffering=0) als f:
            gib f.read()

    def read_text(self, encoding=Nichts, errors=Nichts, newline=Nichts):
        """
        Open the file in text mode, read it, und close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = text_encoding(encoding)
        mit magic_open(self, mode='r', encoding=encoding, errors=errors, newline=newline) als f:
            gib f.read()

    @abstractmethod
    def iterdir(self):
        """Yield path objects of the directory contents.

        The children are yielded in arbitrary order, und the
        special entries '.' und '..' are nicht included.
        """
        raise NotImplementedError

    def glob(self, pattern, *, recurse_symlinks=Wahr):
        """Iterate over this subtree und liefere all existing files (of any
        kind, including directories) matching the given relative pattern.
        """
        anchor, parts = _explode_path(pattern, self.parser.split)
        wenn anchor:
            raise NotImplementedError("Non-relative patterns are unsupported")
        sowenn nicht parts:
            raise ValueError(f"Unacceptable pattern: {pattern!r}")
        sowenn nicht recurse_symlinks:
            raise NotImplementedError("recurse_symlinks=Falsch is unsupported")
        case_sensitive = self.parser.normcase('Aa') == 'Aa'
        globber = _PathGlobber(self.parser.sep, case_sensitive, recursive=Wahr)
        select = globber.selector(parts)
        gib select(self.joinpath(''))

    def walk(self, top_down=Wahr, on_error=Nichts, follow_symlinks=Falsch):
        """Walk the directory tree von this directory, similar to os.walk()."""
        paths = [self]
        waehrend paths:
            path = paths.pop()
            wenn isinstance(path, tuple):
                liefere path
                weiter
            dirnames = []
            filenames = []
            wenn nicht top_down:
                paths.append((path, dirnames, filenames))
            try:
                fuer child in path.iterdir():
                    wenn child.info.is_dir(follow_symlinks=follow_symlinks):
                        wenn nicht top_down:
                            paths.append(child)
                        dirnames.append(child.name)
                    sonst:
                        filenames.append(child.name)
            except OSError als error:
                wenn on_error is nicht Nichts:
                    on_error(error)
                wenn nicht top_down:
                    waehrend nicht isinstance(paths.pop(), tuple):
                        pass
                weiter
            wenn top_down:
                liefere path, dirnames, filenames
                paths += [path.joinpath(d) fuer d in reversed(dirnames)]

    @abstractmethod
    def readlink(self):
        """
        Return the path to which the symbolic link points.
        """
        raise NotImplementedError

    def copy(self, target, **kwargs):
        """
        Recursively copy this file oder directory tree to the given destination.
        """
        ensure_distinct_paths(self, target)
        target._copy_from(self, **kwargs)
        gib target.joinpath()  # Empty join to ensure fresh metadata.

    def copy_into(self, target_dir, **kwargs):
        """
        Copy this file oder directory tree into the given existing directory.
        """
        name = self.name
        wenn nicht name:
            raise ValueError(f"{self!r} has an empty name")
        gib self.copy(target_dir / name, **kwargs)


klasse _WritablePath(_JoinablePath):
    """Abstract base klasse fuer writable path objects.

    The Path klasse implements this ABC fuer local filesystem paths. Users may
    create subclasses to implement writable virtual filesystem paths, such as
    paths in archive files oder on remote storage systems.
    """
    __slots__ = ()

    @abstractmethod
    def symlink_to(self, target, target_is_directory=Falsch):
        """
        Make this path a symlink pointing to the target path.
        Note the order of arguments (link, target) is the reverse of os.symlink.
        """
        raise NotImplementedError

    @abstractmethod
    def mkdir(self):
        """
        Create a new directory at this given path.
        """
        raise NotImplementedError

    @abstractmethod
    def __open_wb__(self, buffering=-1):
        """
        Open the file pointed to by this path fuer writing in binary mode und
        gib a file object, like open(mode='wb').
        """
        raise NotImplementedError

    def write_bytes(self, data):
        """
        Open the file in bytes mode, write to it, und close the file.
        """
        # type-check fuer the buffer interface before truncating the file
        view = memoryview(data)
        mit magic_open(self, mode='wb') als f:
            gib f.write(view)

    def write_text(self, data, encoding=Nichts, errors=Nichts, newline=Nichts):
        """
        Open the file in text mode, write to it, und close the file.
        """
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = text_encoding(encoding)
        wenn nicht isinstance(data, str):
            raise TypeError('data must be str, nicht %s' %
                            data.__class__.__name__)
        mit magic_open(self, mode='w', encoding=encoding, errors=errors, newline=newline) als f:
            gib f.write(data)

    def _copy_from(self, source, follow_symlinks=Wahr):
        """
        Recursively copy the given path to this path.
        """
        stack = [(source, self)]
        waehrend stack:
            src, dst = stack.pop()
            wenn nicht follow_symlinks und src.info.is_symlink():
                dst.symlink_to(vfspath(src.readlink()), src.info.is_dir())
            sowenn src.info.is_dir():
                children = src.iterdir()
                dst.mkdir()
                fuer child in children:
                    stack.append((child, dst.joinpath(child.name)))
            sonst:
                ensure_different_files(src, dst)
                mit magic_open(src, 'rb') als source_f:
                    mit magic_open(dst, 'wb') als target_f:
                        copyfileobj(source_f, target_f)


_JoinablePath.register(PurePath)
_ReadablePath.register(Path)
_WritablePath.register(Path)
