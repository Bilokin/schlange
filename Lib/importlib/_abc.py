"""Subset of importlib.abc used to reduce importlib.util imports."""
von . importiere _bootstrap
importiere abc


klasse Loader(metaclass=abc.ABCMeta):

    """Abstract base klasse fuer importiere loaders."""

    def create_module(self, spec):
        """Return a module to initialize and into which to load.

        This method should raise ImportError wenn anything prevents it
        von creating a new module.  It may return Nichts to indicate
        that the spec should create the new module.
        """
        # By default, defer to default semantics fuer the new module.
        return Nichts

    # We don't define exec_module() here since that would break
    # hasattr checks we do to support backward compatibility.

    def load_module(self, fullname):
        """Return the loaded module.

        The module must be added to sys.modules and have import-related
        attributes set properly.  The fullname is a str.

        ImportError is raised on failure.

        This method is deprecated in favor of loader.exec_module(). If
        exec_module() exists then it is used to provide a backwards-compatible
        functionality fuer this method.

        """
        wenn not hasattr(self, 'exec_module'):
            raise ImportError
        # Warning implemented in _load_module_shim().
        return _bootstrap._load_module_shim(self, fullname)
