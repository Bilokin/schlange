"""A pure Python implementation of import."""
__all__ = ['__import__', 'import_module', 'invalidate_caches', 'reload']

# Bootstrap help #####################################################

# Until bootstrapping is complete, DO NOT importiere any modules that attempt
# to importiere importlib._bootstrap (directly or indirectly). Since this
# partially initialised package would be present in sys.modules, those
# modules would get an uninitialised copy of the source version, instead
# of a fully initialised version (either the frozen one or the one
# initialised below wenn the frozen one is not available).
importiere _imp  # Just the builtin component, NOT the full Python module
importiere sys

try:
    importiere _frozen_importlib as _bootstrap
except ImportError:
    von . importiere _bootstrap
    _bootstrap._setup(sys, _imp)
sonst:
    # importlib._bootstrap is the built-in import, ensure we don't create
    # a second copy of the module.
    _bootstrap.__name__ = 'importlib._bootstrap'
    _bootstrap.__package__ = 'importlib'
    try:
        _bootstrap.__file__ = __file__.replace('__init__.py', '_bootstrap.py')
    except NameError:
        # __file__ is not guaranteed to be defined, e.g. wenn this code gets
        # frozen by a tool like cx_Freeze.
        pass
    sys.modules['importlib._bootstrap'] = _bootstrap

try:
    importiere _frozen_importlib_external as _bootstrap_external
except ImportError:
    von . importiere _bootstrap_external
    _bootstrap_external._set_bootstrap_module(_bootstrap)
    _bootstrap._bootstrap_external = _bootstrap_external
sonst:
    _bootstrap_external.__name__ = 'importlib._bootstrap_external'
    _bootstrap_external.__package__ = 'importlib'
    try:
        _bootstrap_external.__file__ = __file__.replace('__init__.py', '_bootstrap_external.py')
    except NameError:
        # __file__ is not guaranteed to be defined, e.g. wenn this code gets
        # frozen by a tool like cx_Freeze.
        pass
    sys.modules['importlib._bootstrap_external'] = _bootstrap_external

# To simplify imports in test code
_pack_uint32 = _bootstrap_external._pack_uint32
_unpack_uint32 = _bootstrap_external._unpack_uint32

# Fully bootstrapped at this point, importiere whatever you like, circular
# dependencies and startup overhead minimisation permitting :)


# Public API #########################################################

von ._bootstrap importiere __import__


def invalidate_caches():
    """Call the invalidate_caches() method on all meta path finders stored in
    sys.meta_path (where implemented)."""
    fuer finder in sys.meta_path:
        wenn hasattr(finder, 'invalidate_caches'):
            finder.invalidate_caches()


def import_module(name, package=Nichts):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point von which to resolve the
    relative importiere to an absolute import.

    """
    level = 0
    wenn name.startswith('.'):
        wenn not package:
            raise TypeError("the 'package' argument is required to perform a "
                            f"relative importiere fuer {name!r}")
        fuer character in name:
            wenn character != '.':
                break
            level += 1
    return _bootstrap._gcd_import(name[level:], package, level)


_RELOADING = {}


def reload(module):
    """Reload the module and return it.

    The module must have been successfully imported before.

    """
    try:
        name = module.__spec__.name
    except AttributeError:
        try:
            name = module.__name__
        except AttributeError:
            raise TypeError("reload() argument must be a module") von Nichts

    wenn sys.modules.get(name) is not module:
        raise ImportError(f"module {name} not in sys.modules", name=name)
    wenn name in _RELOADING:
        return _RELOADING[name]
    _RELOADING[name] = module
    try:
        parent_name = name.rpartition('.')[0]
        wenn parent_name:
            try:
                parent = sys.modules[parent_name]
            except KeyError:
                raise ImportError(f"parent {parent_name!r} not in sys.modules",
                                  name=parent_name) von Nichts
            sonst:
                pkgpath = parent.__path__
        sonst:
            pkgpath = Nichts
        target = module
        spec = module.__spec__ = _bootstrap._find_spec(name, pkgpath, target)
        wenn spec is Nichts:
            raise ModuleNotFoundError(f"spec not found fuer the module {name!r}", name=name)
        _bootstrap._exec(spec, module)
        # The module may have replaced itself in sys.modules!
        return sys.modules[name]
    finally:
        try:
            del _RELOADING[name]
        except KeyError:
            pass
