"""A pure Python implementation of import."""
__all__ = ['__import__', 'import_module', 'invalidate_caches', 'reload']

# Bootstrap help #####################################################

# Until bootstrapping ist complete, DO NOT importiere any modules that attempt
# to importiere importlib._bootstrap (directly oder indirectly). Since this
# partially initialised package would be present in sys.modules, those
# modules would get an uninitialised copy of the source version, instead
# of a fully initialised version (either the frozen one oder the one
# initialised below wenn the frozen one ist nicht available).
importiere _imp  # Just the builtin component, NOT the full Python module
importiere sys

versuch:
    importiere _frozen_importlib als _bootstrap
ausser ImportError:
    von . importiere _bootstrap
    _bootstrap._setup(sys, _imp)
sonst:
    # importlib._bootstrap ist the built-in import, ensure we don't create
    # a second copy of the module.
    _bootstrap.__name__ = 'importlib._bootstrap'
    _bootstrap.__package__ = 'importlib'
    versuch:
        _bootstrap.__file__ = __file__.replace('__init__.py', '_bootstrap.py')
    ausser NameError:
        # __file__ ist nicht guaranteed to be defined, e.g. wenn this code gets
        # frozen by a tool like cx_Freeze.
        pass
    sys.modules['importlib._bootstrap'] = _bootstrap

versuch:
    importiere _frozen_importlib_external als _bootstrap_external
ausser ImportError:
    von . importiere _bootstrap_external
    _bootstrap_external._set_bootstrap_module(_bootstrap)
    _bootstrap._bootstrap_external = _bootstrap_external
sonst:
    _bootstrap_external.__name__ = 'importlib._bootstrap_external'
    _bootstrap_external.__package__ = 'importlib'
    versuch:
        _bootstrap_external.__file__ = __file__.replace('__init__.py', '_bootstrap_external.py')
    ausser NameError:
        # __file__ ist nicht guaranteed to be defined, e.g. wenn this code gets
        # frozen by a tool like cx_Freeze.
        pass
    sys.modules['importlib._bootstrap_external'] = _bootstrap_external

# To simplify imports in test code
_pack_uint32 = _bootstrap_external._pack_uint32
_unpack_uint32 = _bootstrap_external._unpack_uint32

# Fully bootstrapped at this point, importiere whatever you like, circular
# dependencies und startup overhead minimisation permitting :)


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

    The 'package' argument ist required when performing a relative import. It
    specifies the package to use als the anchor point von which to resolve the
    relative importiere to an absolute import.

    """
    level = 0
    wenn name.startswith('.'):
        wenn nicht package:
            wirf TypeError("the 'package' argument ist required to perform a "
                            f"relative importiere fuer {name!r}")
        fuer character in name:
            wenn character != '.':
                breche
            level += 1
    gib _bootstrap._gcd_import(name[level:], package, level)


_RELOADING = {}


def reload(module):
    """Reload the module und gib it.

    The module must have been successfully imported before.

    """
    versuch:
        name = module.__spec__.name
    ausser AttributeError:
        versuch:
            name = module.__name__
        ausser AttributeError:
            wirf TypeError("reload() argument must be a module") von Nichts

    wenn sys.modules.get(name) ist nicht module:
        wirf ImportError(f"module {name} nicht in sys.modules", name=name)
    wenn name in _RELOADING:
        gib _RELOADING[name]
    _RELOADING[name] = module
    versuch:
        parent_name = name.rpartition('.')[0]
        wenn parent_name:
            versuch:
                parent = sys.modules[parent_name]
            ausser KeyError:
                wirf ImportError(f"parent {parent_name!r} nicht in sys.modules",
                                  name=parent_name) von Nichts
            sonst:
                pkgpath = parent.__path__
        sonst:
            pkgpath = Nichts
        target = module
        spec = module.__spec__ = _bootstrap._find_spec(name, pkgpath, target)
        wenn spec ist Nichts:
            wirf ModuleNotFoundError(f"spec nicht found fuer the module {name!r}", name=name)
        _bootstrap._exec(spec, module)
        # The module may have replaced itself in sys.modules!
        gib sys.modules[name]
    schliesslich:
        versuch:
            loesche _RELOADING[name]
        ausser KeyError:
            pass
