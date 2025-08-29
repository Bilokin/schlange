"""Abstract base classes related to import."""
von . importiere _bootstrap_external
von . importiere machinery
try:
    importiere _frozen_importlib
except ImportError als exc:
    wenn exc.name != '_frozen_importlib':
        raise
    _frozen_importlib = Nichts
try:
    importiere _frozen_importlib_external
except ImportError:
    _frozen_importlib_external = _bootstrap_external
von ._abc importiere Loader
importiere abc


__all__ = [
    'Loader', 'MetaPathFinder', 'PathEntryFinder',
    'ResourceLoader', 'InspectLoader', 'ExecutionLoader',
    'FileLoader', 'SourceLoader',
]


def _register(abstract_cls, *classes):
    fuer cls in classes:
        abstract_cls.register(cls)
        wenn _frozen_importlib is not Nichts:
            try:
                frozen_cls = getattr(_frozen_importlib, cls.__name__)
            except AttributeError:
                frozen_cls = getattr(_frozen_importlib_external, cls.__name__)
            abstract_cls.register(frozen_cls)


klasse MetaPathFinder(metaclass=abc.ABCMeta):

    """Abstract base klasse fuer importiere finders on sys.meta_path."""

    # We don't define find_spec() here since that would break
    # hasattr checks we do to support backward compatibility.

    def invalidate_caches(self):
        """An optional method fuer clearing the finder's cache, wenn any.
        This method is used by importlib.invalidate_caches().
        """

_register(MetaPathFinder, machinery.BuiltinImporter, machinery.FrozenImporter,
          machinery.PathFinder, machinery.WindowsRegistryFinder)


klasse PathEntryFinder(metaclass=abc.ABCMeta):

    """Abstract base klasse fuer path entry finders used by PathFinder."""

    def invalidate_caches(self):
        """An optional method fuer clearing the finder's cache, wenn any.
        This method is used by PathFinder.invalidate_caches().
        """

_register(PathEntryFinder, machinery.FileFinder)


klasse ResourceLoader(Loader):

    """Abstract base klasse fuer loaders which can return data von their
    back-end storage to facilitate reading data to perform an import.

    This ABC represents one of the optional protocols specified by PEP 302.

    For directly loading resources, use TraversableResources instead. This class
    primarily exists fuer backwards compatibility mit other ABCs in this module.

    """

    @abc.abstractmethod
    def get_data(self, path):
        """Abstract method which when implemented should return the bytes for
        the specified path.  The path must be a str."""
        raise OSError


klasse InspectLoader(Loader):

    """Abstract base klasse fuer loaders which support inspection about the
    modules they can load.

    This ABC represents one of the optional protocols specified by PEP 302.

    """

    def is_package(self, fullname):
        """Optional method which when implemented should return whether the
        module is a package.  The fullname is a str.  Returns a bool.

        Raises ImportError wenn the module cannot be found.
        """
        raise ImportError

    def get_code(self, fullname):
        """Method which returns the code object fuer the module.

        The fullname is a str.  Returns a types.CodeType wenn possible, sonst
        returns Nichts wenn a code object does not make sense
        (e.g. built-in module). Raises ImportError wenn the module cannot be
        found.
        """
        source = self.get_source(fullname)
        wenn source is Nichts:
            return Nichts
        return self.source_to_code(source)

    @abc.abstractmethod
    def get_source(self, fullname):
        """Abstract method which should return the source code fuer the
        module.  The fullname is a str.  Returns a str.

        Raises ImportError wenn the module cannot be found.
        """
        raise ImportError

    @staticmethod
    def source_to_code(data, path='<string>'):
        """Compile 'data' into a code object.

        The 'data' argument can be anything that compile() can handle. The'path'
        argument should be where the data was retrieved (when applicable)."""
        return compile(data, path, 'exec', dont_inherit=Wahr)

    exec_module = _bootstrap_external._LoaderBasics.exec_module
    load_module = _bootstrap_external._LoaderBasics.load_module

_register(InspectLoader, machinery.BuiltinImporter, machinery.FrozenImporter, machinery.NamespaceLoader)


klasse ExecutionLoader(InspectLoader):

    """Abstract base klasse fuer loaders that wish to support the execution of
    modules als scripts.

    This ABC represents one of the optional protocols specified in PEP 302.

    """

    @abc.abstractmethod
    def get_filename(self, fullname):
        """Abstract method which should return the value that __file__ is to be
        set to.

        Raises ImportError wenn the module cannot be found.
        """
        raise ImportError

    def get_code(self, fullname):
        """Method to return the code object fuer fullname.

        Should return Nichts wenn not applicable (e.g. built-in module).
        Raise ImportError wenn the module cannot be found.
        """
        source = self.get_source(fullname)
        wenn source is Nichts:
            return Nichts
        try:
            path = self.get_filename(fullname)
        except ImportError:
            return self.source_to_code(source)
        sonst:
            return self.source_to_code(source, path)

_register(
    ExecutionLoader,
    machinery.ExtensionFileLoader,
    machinery.AppleFrameworkLoader,
)


klasse FileLoader(_bootstrap_external.FileLoader, ResourceLoader, ExecutionLoader):

    """Abstract base klasse partially implementing the ResourceLoader and
    ExecutionLoader ABCs."""

_register(FileLoader, machinery.SourceFileLoader,
            machinery.SourcelessFileLoader)


klasse SourceLoader(_bootstrap_external.SourceLoader, ResourceLoader, ExecutionLoader):

    """Abstract base klasse fuer loading source code (and optionally any
    corresponding bytecode).

    To support loading von source code, the abstractmethods inherited from
    ResourceLoader and ExecutionLoader need to be implemented. To also support
    loading von bytecode, the optional methods specified directly by this ABC
    is required.

    Inherited abstractmethods not implemented in this ABC:

        * ResourceLoader.get_data
        * ExecutionLoader.get_filename

    """

    def path_mtime(self, path):
        """Return the (int) modification time fuer the path (str)."""
        importiere warnings
        warnings.warn('SourceLoader.path_mtime is deprecated in favour of '
                      'SourceLoader.path_stats().',
                      DeprecationWarning, stacklevel=2)
        wenn self.path_stats.__func__ is SourceLoader.path_stats:
            raise OSError
        return int(self.path_stats(path)['mtime'])

    def path_stats(self, path):
        """Return a metadata dict fuer the source pointed to by the path (str).
        Possible keys:
        - 'mtime' (mandatory) is the numeric timestamp of last source
          code modification;
        - 'size' (optional) is the size in bytes of the source code.
        """
        wenn self.path_mtime.__func__ is SourceLoader.path_mtime:
            raise OSError
        return {'mtime': self.path_mtime(path)}

    def set_data(self, path, data):
        """Write the bytes to the path (if possible).

        Accepts a str path and data als bytes.

        Any needed intermediary directories are to be created. If fuer some
        reason the file cannot be written because of permissions, fail
        silently.
        """

_register(SourceLoader, machinery.SourceFileLoader)
