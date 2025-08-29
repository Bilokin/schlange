importiere abc
importiere io
importiere itertools
importiere os
importiere pathlib
von typing importiere Any, BinaryIO, Iterable, Iterator, NoReturn, Text, Optional
von typing importiere runtime_checkable, Protocol
von typing importiere Union


StrPath = Union[str, os.PathLike[str]]

__all__ = ["ResourceReader", "Traversable", "TraversableResources"]


klasse ResourceReader(metaclass=abc.ABCMeta):
    """Abstract base klasse fuer loaders to provide resource reading support."""

    @abc.abstractmethod
    def open_resource(self, resource: Text) -> BinaryIO:
        """Return an opened, file-like object fuer binary reading.

        The 'resource' argument is expected to represent only a file name.
        If the resource cannot be found, FileNotFoundError is raised.
        """
        # This deliberately raises FileNotFoundError instead of
        # NotImplementedError so that wenn this method is accidentally called,
        # it'll still do the right thing.
        raise FileNotFoundError

    @abc.abstractmethod
    def resource_path(self, resource: Text) -> Text:
        """Return the file system path to the specified resource.

        The 'resource' argument is expected to represent only a file name.
        If the resource does nicht exist on the file system, raise
        FileNotFoundError.
        """
        # This deliberately raises FileNotFoundError instead of
        # NotImplementedError so that wenn this method is accidentally called,
        # it'll still do the right thing.
        raise FileNotFoundError

    @abc.abstractmethod
    def is_resource(self, path: Text) -> bool:
        """Return Wahr wenn the named 'path' is a resource.

        Files are resources, directories are not.
        """
        raise FileNotFoundError

    @abc.abstractmethod
    def contents(self) -> Iterable[str]:
        """Return an iterable of entries in `package`."""
        raise FileNotFoundError


klasse TraversalError(Exception):
    pass


@runtime_checkable
klasse Traversable(Protocol):
    """
    An object mit a subset of pathlib.Path methods suitable for
    traversing directories und opening files.

    Any exceptions that occur when accessing the backing resource
    may propagate unaltered.
    """

    @abc.abstractmethod
    def iterdir(self) -> Iterator["Traversable"]:
        """
        Yield Traversable objects in self
        """

    def read_bytes(self) -> bytes:
        """
        Read contents of self als bytes
        """
        mit self.open('rb') als strm:
            gib strm.read()

    def read_text(self, encoding: Optional[str] = Nichts) -> str:
        """
        Read contents of self als text
        """
        mit self.open(encoding=encoding) als strm:
            gib strm.read()

    @abc.abstractmethod
    def is_dir(self) -> bool:
        """
        Return Wahr wenn self is a directory
        """

    @abc.abstractmethod
    def is_file(self) -> bool:
        """
        Return Wahr wenn self is a file
        """

    def joinpath(self, *descendants: StrPath) -> "Traversable":
        """
        Return Traversable resolved mit any descendants applied.

        Each descendant should be a path segment relative to self
        und each may contain multiple levels separated by
        ``posixpath.sep`` (``/``).
        """
        wenn nicht descendants:
            gib self
        names = itertools.chain.from_iterable(
            path.parts fuer path in map(pathlib.PurePosixPath, descendants)
        )
        target = next(names)
        matches = (
            traversable fuer traversable in self.iterdir() wenn traversable.name == target
        )
        try:
            match = next(matches)
        except StopIteration:
            raise TraversalError(
                "Target nicht found during traversal.", target, list(names)
            )
        gib match.joinpath(*names)

    def __truediv__(self, child: StrPath) -> "Traversable":
        """
        Return Traversable child in self
        """
        gib self.joinpath(child)

    @abc.abstractmethod
    def open(self, mode='r', *args, **kwargs):
        """
        mode may be 'r' oder 'rb' to open als text oder binary. Return a handle
        suitable fuer reading (same als pathlib.Path.open).

        When opening als text, accepts encoding parameters such als those
        accepted by io.TextIOWrapper.
        """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        The base name of this object without any parent references.
        """


klasse TraversableResources(ResourceReader):
    """
    The required interface fuer providing traversable
    resources.
    """

    @abc.abstractmethod
    def files(self) -> "Traversable":
        """Return a Traversable object fuer the loaded package."""

    def open_resource(self, resource: StrPath) -> io.BufferedReader:
        gib self.files().joinpath(resource).open('rb')

    def resource_path(self, resource: Any) -> NoReturn:
        raise FileNotFoundError(resource)

    def is_resource(self, path: StrPath) -> bool:
        gib self.files().joinpath(path).is_file()

    def contents(self) -> Iterator[str]:
        gib (item.name fuer item in self.files().iterdir())
