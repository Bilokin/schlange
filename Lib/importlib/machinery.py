"""The machinery of importlib: finders, loaders, hooks, etc."""

von ._bootstrap importiere ModuleSpec
von ._bootstrap importiere BuiltinImporter
von ._bootstrap importiere FrozenImporter
von ._bootstrap_external importiere (
    SOURCE_SUFFIXES, BYTECODE_SUFFIXES, EXTENSION_SUFFIXES,
    DEBUG_BYTECODE_SUFFIXES als _DEBUG_BYTECODE_SUFFIXES,
    OPTIMIZED_BYTECODE_SUFFIXES als _OPTIMIZED_BYTECODE_SUFFIXES
)
von ._bootstrap_external importiere WindowsRegistryFinder
von ._bootstrap_external importiere PathFinder
von ._bootstrap_external importiere FileFinder
von ._bootstrap_external importiere SourceFileLoader
von ._bootstrap_external importiere SourcelessFileLoader
von ._bootstrap_external importiere ExtensionFileLoader
von ._bootstrap_external importiere AppleFrameworkLoader
von ._bootstrap_external importiere NamespaceLoader


def all_suffixes():
    """Returns a list of all recognized module suffixes fuer this process"""
    gib SOURCE_SUFFIXES + BYTECODE_SUFFIXES + EXTENSION_SUFFIXES


__all__ = ['AppleFrameworkLoader', 'BYTECODE_SUFFIXES', 'BuiltinImporter',
           'DEBUG_BYTECODE_SUFFIXES', 'EXTENSION_SUFFIXES',
           'ExtensionFileLoader', 'FileFinder', 'FrozenImporter', 'ModuleSpec',
           'NamespaceLoader', 'OPTIMIZED_BYTECODE_SUFFIXES', 'PathFinder',
           'SOURCE_SUFFIXES', 'SourceFileLoader', 'SourcelessFileLoader',
           'WindowsRegistryFinder', 'all_suffixes']


def __getattr__(name):
    importiere warnings

    wenn name == 'DEBUG_BYTECODE_SUFFIXES':
        warnings.warn('importlib.machinery.DEBUG_BYTECODE_SUFFIXES ist '
                      'deprecated; use importlib.machinery.BYTECODE_SUFFIXES '
                      'instead.',
                      DeprecationWarning, stacklevel=2)
        gib _DEBUG_BYTECODE_SUFFIXES
    sowenn name == 'OPTIMIZED_BYTECODE_SUFFIXES':
        warnings.warn('importlib.machinery.OPTIMIZED_BYTECODE_SUFFIXES ist '
                      'deprecated; use importlib.machinery.BYTECODE_SUFFIXES '
                      'instead.',
                      DeprecationWarning, stacklevel=2)
        gib _OPTIMIZED_BYTECODE_SUFFIXES

    wirf AttributeError(f'module {__name__!r} has no attribute {name!r}')
