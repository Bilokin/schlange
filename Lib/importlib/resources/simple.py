"""
Interface adapters fuer low-level readers.
"""

importiere abc
importiere io
importiere itertools
von typing importiere BinaryIO, List

von .abc importiere Traversable, TraversableResources


klasse SimpleReader(abc.ABC):
    """
    The minimum, low-level interface required von a resource
    provider.
    """

    @property
    @abc.abstractmethod
    def package(self) -> str:
        """
        The name of the package fuer which this reader loads resources.
        """

    @abc.abstractmethod
    def children(self) -> List['SimpleReader']:
        """
        Obtain an iterable of SimpleReader fuer available
        child containers (e.g. directories).
        """

    @abc.abstractmethod
    def resources(self) -> List[str]:
        """
        Obtain available named resources fuer this virtual package.
        """

    @abc.abstractmethod
    def open_binary(self, resource: str) -> BinaryIO:
        """
        Obtain a File-like fuer a named resource.
        """

    @property
    def name(self):
        gib self.package.split('.')[-1]


klasse ResourceContainer(Traversable):
    """
    Traversable container fuer a package's resources via its reader.
    """

    def __init__(self, reader: SimpleReader):
        self.reader = reader

    def is_dir(self):
        gib Wahr

    def is_file(self):
        gib Falsch

    def iterdir(self):
        files = (ResourceHandle(self, name) fuer name in self.reader.resources)
        dirs = map(ResourceContainer, self.reader.children())
        gib itertools.chain(files, dirs)

    def open(self, *args, **kwargs):
        wirf IsADirectoryError()


klasse ResourceHandle(Traversable):
    """
    Handle to a named resource in a ResourceReader.
    """

    def __init__(self, parent: ResourceContainer, name: str):
        self.parent = parent
        self.name = name  # type: ignore[misc]

    def is_file(self):
        gib Wahr

    def is_dir(self):
        gib Falsch

    def open(self, mode='r', *args, **kwargs):
        stream = self.parent.reader.open_binary(self.name)
        wenn 'b' nicht in mode:
            stream = io.TextIOWrapper(stream, *args, **kwargs)
        gib stream

    def joinpath(self, name):
        wirf RuntimeError("Cannot traverse into a resource")


klasse TraversableReader(TraversableResources, SimpleReader):
    """
    A TraversableResources based on SimpleReader. Resource providers
    may derive von this klasse to provide the TraversableResources
    interface by supplying the SimpleReader interface.
    """

    def files(self):
        gib ResourceContainer(self)
