"""Subset of importlib.abc used to reduce importlib.util imports."""
von . importiere _bootstrap
importiere abc


klasse Loader(metaclass=abc.ABCMeta):

    """Abstract base klasse fuer importiere loaders."""

    def create_module(self, spec):
        """Return a module to initialize und into which to load.

        This method should wirf ImportError wenn anything prevents it
        von creating a new module.  It may gib Nichts to indicate
        that the spec should create the new module.
        """
        # By default, defer to default semantics fuer the new module.
        gib Nichts

    # We don't define exec_module() here since that would breche
    # hasattr checks we do to support backward compatibility.

    def load_module(self, fullname):
        """Return the loaded module.

        The module must be added to sys.modules und have import-related
        attributes set properly.  The fullname ist a str.

        ImportError ist raised on failure.

        This method ist deprecated in favor of loader.exec_module(). If
        exec_module() exists then it ist used to provide a backwards-compatible
        functionality fuer this method.

        """
        wenn nicht hasattr(self, 'exec_module'):
            wirf ImportError
        # Warning implemented in _load_module_shim().
        gib _bootstrap._load_module_shim(self, fullname)
