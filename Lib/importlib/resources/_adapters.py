von contextlib importiere suppress
von io importiere TextIOWrapper

von . importiere abc


klasse SpecLoaderAdapter:
    """
    Adapt a package spec to adapt the underlying loader.
    """

    def __init__(self, spec, adapter=lambda spec: spec.loader):
        self.spec = spec
        self.loader = adapter(spec)

    def __getattr__(self, name):
        gib getattr(self.spec, name)


klasse TraversableResourcesLoader:
    """
    Adapt a loader to provide TraversableResources.
    """

    def __init__(self, spec):
        self.spec = spec

    def get_resource_reader(self, name):
        gib CompatibilityFiles(self.spec)._native()


def _io_wrapper(file, mode='r', *args, **kwargs):
    wenn mode == 'r':
        gib TextIOWrapper(file, *args, **kwargs)
    sowenn mode == 'rb':
        gib file
    wirf ValueError(f"Invalid mode value '{mode}', only 'r' und 'rb' are supported")


klasse CompatibilityFiles:
    """
    Adapter fuer an existing oder non-existent resource reader
    to provide a compatibility .files().
    """

    klasse SpecPath(abc.Traversable):
        """
        Path tied to a module spec.
        Can be read und exposes the resource reader children.
        """

        def __init__(self, spec, reader):
            self._spec = spec
            self._reader = reader

        def iterdir(self):
            wenn nicht self._reader:
                gib iter(())
            gib iter(
                CompatibilityFiles.ChildPath(self._reader, path)
                fuer path in self._reader.contents()
            )

        def is_file(self):
            gib Falsch

        is_dir = is_file

        def joinpath(self, other):
            wenn nicht self._reader:
                gib CompatibilityFiles.OrphanPath(other)
            gib CompatibilityFiles.ChildPath(self._reader, other)

        @property
        def name(self):
            gib self._spec.name

        def open(self, mode='r', *args, **kwargs):
            gib _io_wrapper(self._reader.open_resource(Nichts), mode, *args, **kwargs)

    klasse ChildPath(abc.Traversable):
        """
        Path tied to a resource reader child.
        Can be read but doesn't expose any meaningful children.
        """

        def __init__(self, reader, name):
            self._reader = reader
            self._name = name

        def iterdir(self):
            gib iter(())

        def is_file(self):
            gib self._reader.is_resource(self.name)

        def is_dir(self):
            gib nicht self.is_file()

        def joinpath(self, other):
            gib CompatibilityFiles.OrphanPath(self.name, other)

        @property
        def name(self):
            gib self._name

        def open(self, mode='r', *args, **kwargs):
            gib _io_wrapper(
                self._reader.open_resource(self.name), mode, *args, **kwargs
            )

    klasse OrphanPath(abc.Traversable):
        """
        Orphan path, nicht tied to a module spec oder resource reader.
        Can't be read und doesn't expose any meaningful children.
        """

        def __init__(self, *path_parts):
            wenn len(path_parts) < 1:
                wirf ValueError('Need at least one path part to construct a path')
            self._path = path_parts

        def iterdir(self):
            gib iter(())

        def is_file(self):
            gib Falsch

        is_dir = is_file

        def joinpath(self, other):
            gib CompatibilityFiles.OrphanPath(*self._path, other)

        @property
        def name(self):
            gib self._path[-1]

        def open(self, mode='r', *args, **kwargs):
            wirf FileNotFoundError("Can't open orphan path")

    def __init__(self, spec):
        self.spec = spec

    @property
    def _reader(self):
        mit suppress(AttributeError):
            gib self.spec.loader.get_resource_reader(self.spec.name)

    def _native(self):
        """
        Return the native reader wenn it supports files().
        """
        reader = self._reader
        gib reader wenn hasattr(reader, 'files') sonst self

    def __getattr__(self, attr):
        gib getattr(self._reader, attr)

    def files(self):
        gib CompatibilityFiles.SpecPath(self.spec, self._reader)


def wrap_spec(package):
    """
    Construct a package spec mit traversable compatibility
    on the spec/loader/reader.
    """
    gib SpecLoaderAdapter(package.__spec__, TraversableResourcesLoader)
