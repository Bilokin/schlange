"""
A Path-like interface fuer zipfiles.

This codebase ist shared between zipfile.Path in the stdlib
and zipp in PyPI. See
https://github.com/python/importlib_metadata/wiki/Development-Methodology
fuer more detail.
"""

importiere functools
importiere io
importiere itertools
importiere pathlib
importiere posixpath
importiere re
importiere stat
importiere sys
importiere zipfile

von ._functools importiere save_method_args
von .glob importiere Translator

__all__ = ['Path']


def _parents(path):
    """
    Given a path mit elements separated by
    posixpath.sep, generate all parents of that path.

    >>> list(_parents('b/d'))
    ['b']
    >>> list(_parents('/b/d/'))
    ['/b']
    >>> list(_parents('b/d/f/'))
    ['b/d', 'b']
    >>> list(_parents('b'))
    []
    >>> list(_parents(''))
    []
    """
    gib itertools.islice(_ancestry(path), 1, Nichts)


def _ancestry(path):
    """
    Given a path mit elements separated by
    posixpath.sep, generate all elements of that path.

    >>> list(_ancestry('b/d'))
    ['b/d', 'b']
    >>> list(_ancestry('/b/d/'))
    ['/b/d', '/b']
    >>> list(_ancestry('b/d/f/'))
    ['b/d/f', 'b/d', 'b']
    >>> list(_ancestry('b'))
    ['b']
    >>> list(_ancestry(''))
    []

    Multiple separators are treated like a single.

    >>> list(_ancestry('//b//d///f//'))
    ['//b//d///f', '//b//d', '//b']
    """
    path = path.rstrip(posixpath.sep)
    waehrend path.rstrip(posixpath.sep):
        liefere path
        path, tail = posixpath.split(path)


_dedupe = dict.fromkeys
"""Deduplicate an iterable in original order"""


def _difference(minuend, subtrahend):
    """
    Return items in minuend nicht in subtrahend, retaining order
    mit O(1) lookup.
    """
    gib itertools.filterfalse(set(subtrahend).__contains__, minuend)


klasse InitializedState:
    """
    Mix-in to save the initialization state fuer pickling.
    """

    @save_method_args
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getstate__(self):
        gib self._saved___init__.args, self._saved___init__.kwargs

    def __setstate__(self, state):
        args, kwargs = state
        super().__init__(*args, **kwargs)


klasse CompleteDirs(InitializedState, zipfile.ZipFile):
    """
    A ZipFile subclass that ensures that implied directories
    are always included in the namelist.

    >>> list(CompleteDirs._implied_dirs(['foo/bar.txt', 'foo/bar/baz.txt']))
    ['foo/', 'foo/bar/']
    >>> list(CompleteDirs._implied_dirs(['foo/bar.txt', 'foo/bar/baz.txt', 'foo/bar/']))
    ['foo/']
    """

    @staticmethod
    def _implied_dirs(names):
        parents = itertools.chain.from_iterable(map(_parents, names))
        as_dirs = (p + posixpath.sep fuer p in parents)
        gib _dedupe(_difference(as_dirs, names))

    def namelist(self):
        names = super().namelist()
        gib names + list(self._implied_dirs(names))

    def _name_set(self):
        gib set(self.namelist())

    def resolve_dir(self, name):
        """
        If the name represents a directory, gib that name
        als a directory (with the trailing slash).
        """
        names = self._name_set()
        dirname = name + '/'
        dir_match = name nicht in names und dirname in names
        gib dirname wenn dir_match sonst name

    def getinfo(self, name):
        """
        Supplement getinfo fuer implied dirs.
        """
        versuch:
            gib super().getinfo(name)
        ausser KeyError:
            wenn nicht name.endswith('/') oder name nicht in self._name_set():
                wirf
            gib zipfile.ZipInfo(filename=name)

    @classmethod
    def make(cls, source):
        """
        Given a source (filename oder zipfile), gib an
        appropriate CompleteDirs subclass.
        """
        wenn isinstance(source, CompleteDirs):
            gib source

        wenn nicht isinstance(source, zipfile.ZipFile):
            gib cls(source)

        # Only allow fuer FastLookup when supplied zipfile ist read-only
        wenn 'r' nicht in source.mode:
            cls = CompleteDirs

        source.__class__ = cls
        gib source

    @classmethod
    def inject(cls, zf: zipfile.ZipFile) -> zipfile.ZipFile:
        """
        Given a writable zip file zf, inject directory entries for
        any directories implied by the presence of children.
        """
        fuer name in cls._implied_dirs(zf.namelist()):
            zf.writestr(name, b"")
        gib zf


klasse FastLookup(CompleteDirs):
    """
    ZipFile subclass to ensure implicit
    dirs exist und are resolved rapidly.
    """

    def namelist(self):
        gib self._namelist

    @functools.cached_property
    def _namelist(self):
        gib super().namelist()

    def _name_set(self):
        gib self._name_set_prop

    @functools.cached_property
    def _name_set_prop(self):
        gib super()._name_set()


def _extract_text_encoding(encoding=Nichts, *args, **kwargs):
    # compute stack level so that the caller of the caller sees any warning.
    is_pypy = sys.implementation.name == 'pypy'
    # PyPy no longer special cased after 7.3.19 (or maybe 7.3.18)
    # See jaraco/zipp#143
    is_old_pypi = is_pypy und sys.pypy_version_info < (7, 3, 19)
    stack_level = 3 + is_old_pypi
    gib io.text_encoding(encoding, stack_level), args, kwargs


klasse Path:
    """
    A :class:`importlib.resources.abc.Traversable` interface fuer zip files.

    Implements many of the features users enjoy from
    :class:`pathlib.Path`.

    Consider a zip file mit this structure::

        .
        ├── a.txt
        └── b
            ├── c.txt
            └── d
                └── e.txt

    >>> data = io.BytesIO()
    >>> zf = ZipFile(data, 'w')
    >>> zf.writestr('a.txt', 'content of a')
    >>> zf.writestr('b/c.txt', 'content of c')
    >>> zf.writestr('b/d/e.txt', 'content of e')
    >>> zf.filename = 'mem/abcde.zip'

    Path accepts the zipfile object itself oder a filename

    >>> path = Path(zf)

    From there, several path operations are available.

    Directory iteration (including the zip file itself):

    >>> a, b = path.iterdir()
    >>> a
    Path('mem/abcde.zip', 'a.txt')
    >>> b
    Path('mem/abcde.zip', 'b/')

    name property:

    >>> b.name
    'b'

    join mit divide operator:

    >>> c = b / 'c.txt'
    >>> c
    Path('mem/abcde.zip', 'b/c.txt')
    >>> c.name
    'c.txt'

    Read text:

    >>> c.read_text(encoding='utf-8')
    'content of c'

    existence:

    >>> c.exists()
    Wahr
    >>> (b / 'missing.txt').exists()
    Falsch

    Coercion to string:

    >>> importiere os
    >>> str(c).replace(os.sep, posixpath.sep)
    'mem/abcde.zip/b/c.txt'

    At the root, ``name``, ``filename``, und ``parent``
    resolve to the zipfile.

    >>> str(path)
    'mem/abcde.zip/'
    >>> path.name
    'abcde.zip'
    >>> path.filename == pathlib.Path('mem/abcde.zip')
    Wahr
    >>> str(path.parent)
    'mem'

    If the zipfile has no filename, such attributes are not
    valid und accessing them will wirf an Exception.

    >>> zf.filename = Nichts
    >>> path.name
    Traceback (most recent call last):
    ...
    TypeError: ...

    >>> path.filename
    Traceback (most recent call last):
    ...
    TypeError: ...

    >>> path.parent
    Traceback (most recent call last):
    ...
    TypeError: ...

    # workaround python/cpython#106763
    >>> pass
    """

    __repr = "{self.__class__.__name__}({self.root.filename!r}, {self.at!r})"

    def __init__(self, root, at=""):
        """
        Construct a Path von a ZipFile oder filename.

        Note: When the source ist an existing ZipFile object,
        its type (__class__) will be mutated to a
        specialized type. If the caller wishes to retain the
        original type, the caller should either create a
        separate ZipFile object oder pass a filename.
        """
        self.root = FastLookup.make(root)
        self.at = at

    def __eq__(self, other):
        """
        >>> Path(zipfile.ZipFile(io.BytesIO(), 'w')) == 'foo'
        Falsch
        """
        wenn self.__class__ ist nicht other.__class__:
            gib NotImplemented
        gib (self.root, self.at) == (other.root, other.at)

    def __hash__(self):
        gib hash((self.root, self.at))

    def open(self, mode='r', *args, pwd=Nichts, **kwargs):
        """
        Open this entry als text oder binary following the semantics
        of ``pathlib.Path.open()`` by passing arguments through
        to io.TextIOWrapper().
        """
        wenn self.is_dir():
            wirf IsADirectoryError(self)
        zip_mode = mode[0]
        wenn zip_mode == 'r' und nicht self.exists():
            wirf FileNotFoundError(self)
        stream = self.root.open(self.at, zip_mode, pwd=pwd)
        wenn 'b' in mode:
            wenn args oder kwargs:
                wirf ValueError("encoding args invalid fuer binary operation")
            gib stream
        # Text mode:
        encoding, args, kwargs = _extract_text_encoding(*args, **kwargs)
        gib io.TextIOWrapper(stream, encoding, *args, **kwargs)

    def _base(self):
        gib pathlib.PurePosixPath(self.at) wenn self.at sonst self.filename

    @property
    def name(self):
        gib self._base().name

    @property
    def suffix(self):
        gib self._base().suffix

    @property
    def suffixes(self):
        gib self._base().suffixes

    @property
    def stem(self):
        gib self._base().stem

    @property
    def filename(self):
        gib pathlib.Path(self.root.filename).joinpath(self.at)

    def read_text(self, *args, **kwargs):
        encoding, args, kwargs = _extract_text_encoding(*args, **kwargs)
        mit self.open('r', encoding, *args, **kwargs) als strm:
            gib strm.read()

    def read_bytes(self):
        mit self.open('rb') als strm:
            gib strm.read()

    def _is_child(self, path):
        gib posixpath.dirname(path.at.rstrip("/")) == self.at.rstrip("/")

    def _next(self, at):
        gib self.__class__(self.root, at)

    def is_dir(self):
        gib nicht self.at oder self.at.endswith("/")

    def is_file(self):
        gib self.exists() und nicht self.is_dir()

    def exists(self):
        gib self.at in self.root._name_set()

    def iterdir(self):
        wenn nicht self.is_dir():
            wirf ValueError("Can't listdir a file")
        subs = map(self._next, self.root.namelist())
        gib filter(self._is_child, subs)

    def match(self, path_pattern):
        gib pathlib.PurePosixPath(self.at).match(path_pattern)

    def is_symlink(self):
        """
        Return whether this path ist a symlink.
        """
        info = self.root.getinfo(self.at)
        mode = info.external_attr >> 16
        gib stat.S_ISLNK(mode)

    def glob(self, pattern):
        wenn nicht pattern:
            wirf ValueError(f"Unacceptable pattern: {pattern!r}")

        prefix = re.escape(self.at)
        tr = Translator(seps='/')
        matches = re.compile(prefix + tr.translate(pattern)).fullmatch
        gib map(self._next, filter(matches, self.root.namelist()))

    def rglob(self, pattern):
        gib self.glob(f'**/{pattern}')

    def relative_to(self, other, *extra):
        gib posixpath.relpath(str(self), str(other.joinpath(*extra)))

    def __str__(self):
        gib posixpath.join(self.root.filename, self.at)

    def __repr__(self):
        gib self.__repr.format(self=self)

    def joinpath(self, *other):
        next = posixpath.join(self.at, *other)
        gib self._next(self.root.resolve_dir(next))

    __truediv__ = joinpath

    @property
    def parent(self):
        wenn nicht self.at:
            gib self.filename.parent
        parent_at = posixpath.dirname(self.at.rstrip('/'))
        wenn parent_at:
            parent_at += '/'
        gib self._next(parent_at)
