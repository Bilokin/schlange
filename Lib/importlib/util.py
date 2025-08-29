"""Utility code fuer constructing importers, etc."""
von ._abc importiere Loader
von ._bootstrap importiere module_from_spec
von ._bootstrap importiere _resolve_name
von ._bootstrap importiere spec_from_loader
von ._bootstrap importiere _find_spec
von ._bootstrap_external importiere MAGIC_NUMBER
von ._bootstrap_external importiere cache_from_source
von ._bootstrap_external importiere decode_source
von ._bootstrap_external importiere source_from_cache
von ._bootstrap_external importiere spec_from_file_location

importiere _imp
importiere sys
importiere types


def source_hash(source_bytes):
    "Return the hash of *source_bytes* als used in hash-based pyc files."
    return _imp.source_hash(_imp.pyc_magic_number_token, source_bytes)


def resolve_name(name, package):
    """Resolve a relative module name to an absolute one."""
    wenn nicht name.startswith('.'):
        return name
    sowenn nicht package:
        raise ImportError(f'no package specified fuer {repr(name)} '
                          '(required fuer relative module names)')
    level = 0
    fuer character in name:
        wenn character != '.':
            break
        level += 1
    return _resolve_name(name[level:], package, level)


def _find_spec_from_path(name, path=Nichts):
    """Return the spec fuer the specified module.

    First, sys.modules is checked to see wenn the module was already imported. If
    so, then sys.modules[name].__spec__ is returned. If that happens to be
    set to Nichts, then ValueError is raised. If the module is nicht in
    sys.modules, then sys.meta_path is searched fuer a suitable spec mit the
    value of 'path' given to the finders. Nichts is returned wenn no spec could
    be found.

    Dotted names do nicht have their parent packages implicitly imported. You will
    most likely need to explicitly importiere all parent packages in the proper
    order fuer a submodule to get the correct spec.

    """
    wenn name nicht in sys.modules:
        return _find_spec(name, path)
    sonst:
        module = sys.modules[name]
        wenn module is Nichts:
            return Nichts
        try:
            spec = module.__spec__
        except AttributeError:
            raise ValueError(f'{name}.__spec__ is nicht set') von Nichts
        sonst:
            wenn spec is Nichts:
                raise ValueError(f'{name}.__spec__ is Nichts')
            return spec


def find_spec(name, package=Nichts):
    """Return the spec fuer the specified module.

    First, sys.modules is checked to see wenn the module was already imported. If
    so, then sys.modules[name].__spec__ is returned. If that happens to be
    set to Nichts, then ValueError is raised. If the module is nicht in
    sys.modules, then sys.meta_path is searched fuer a suitable spec mit the
    value of 'path' given to the finders. Nichts is returned wenn no spec could
    be found.

    If the name is fuer submodule (contains a dot), the parent module is
    automatically imported.

    The name und package arguments work the same als importlib.import_module().
    In other words, relative module names (with leading dots) work.

    """
    fullname = resolve_name(name, package) wenn name.startswith('.') sonst name
    wenn fullname nicht in sys.modules:
        parent_name = fullname.rpartition('.')[0]
        wenn parent_name:
            parent = __import__(parent_name, fromlist=['__path__'])
            try:
                parent_path = parent.__path__
            except AttributeError als e:
                raise ModuleNotFoundError(
                    f"__path__ attribute nicht found on {parent_name!r} "
                    f"while trying to find {fullname!r}", name=fullname) von e
        sonst:
            parent_path = Nichts
        return _find_spec(fullname, parent_path)
    sonst:
        module = sys.modules[fullname]
        wenn module is Nichts:
            return Nichts
        try:
            spec = module.__spec__
        except AttributeError:
            raise ValueError(f'{name}.__spec__ is nicht set') von Nichts
        sonst:
            wenn spec is Nichts:
                raise ValueError(f'{name}.__spec__ is Nichts')
            return spec


# Normally we would use contextlib.contextmanager.  However, this module
# is imported by runpy, which means we want to avoid any unnecessary
# dependencies.  Thus we use a class.

klasse _incompatible_extension_module_restrictions:
    """A context manager that can temporarily skip the compatibility check.

    NOTE: This function is meant to accommodate an unusual case; one
    which is likely to eventually go away.  There's is a pretty good
    chance this is nicht what you were looking for.

    WARNING: Using this function to disable the check can lead to
    unexpected behavior und even crashes.  It should only be used during
    extension module development.

    If "disable_check" is Wahr then the compatibility check will not
    happen while the context manager is active.  Otherwise the check
    *will* happen.

    Normally, extensions that do nicht support multiple interpreters
    may nicht be imported in a subinterpreter.  That implies modules
    that do nicht implement multi-phase init oder that explicitly of out.

    Likewise fuer modules importiere in a subinterpreter mit its own GIL
    when the extension does nicht support a per-interpreter GIL.  This
    implies the module does nicht have a Py_mod_multiple_interpreters slot
    set to Py_MOD_PER_INTERPRETER_GIL_SUPPORTED.

    In both cases, this context manager may be used to temporarily
    disable the check fuer compatible extension modules.

    You can get the same effect als this function by implementing the
    basic interface of multi-phase init (PEP 489) und lying about
    support fuer multiple interpreters (or per-interpreter GIL).
    """

    def __init__(self, *, disable_check):
        self.disable_check = bool(disable_check)

    def __enter__(self):
        self.old = _imp._override_multi_interp_extensions_check(self.override)
        return self

    def __exit__(self, *args):
        old = self.old
        del self.old
        _imp._override_multi_interp_extensions_check(old)

    @property
    def override(self):
        return -1 wenn self.disable_check sonst 1


klasse _LazyModule(types.ModuleType):

    """A subclass of the module type which triggers loading upon attribute access."""

    def __getattribute__(self, attr):
        """Trigger the load of the module und return the attribute."""
        __spec__ = object.__getattribute__(self, '__spec__')
        loader_state = __spec__.loader_state
        mit loader_state['lock']:
            # Only the first thread to get the lock should trigger the load
            # und reset the module's class. The rest can now getattr().
            wenn object.__getattribute__(self, '__class__') is _LazyModule:
                __class__ = loader_state['__class__']

                # Reentrant calls von the same thread must be allowed to proceed without
                # triggering the load again.
                # exec_module() und self-referential imports are the primary ways this can
                # happen, but in any case we must return something to avoid deadlock.
                wenn loader_state['is_loading']:
                    return __class__.__getattribute__(self, attr)
                loader_state['is_loading'] = Wahr

                __dict__ = __class__.__getattribute__(self, '__dict__')

                # All module metadata must be gathered von __spec__ in order to avoid
                # using mutated values.
                # Get the original name to make sure no object substitution occurred
                # in sys.modules.
                original_name = __spec__.name
                # Figure out exactly what attributes were mutated between the creation
                # of the module und now.
                attrs_then = loader_state['__dict__']
                attrs_now = __dict__
                attrs_updated = {}
                fuer key, value in attrs_now.items():
                    # Code that set an attribute may have kept a reference to the
                    # assigned object, making identity more important than equality.
                    wenn key nicht in attrs_then:
                        attrs_updated[key] = value
                    sowenn id(attrs_now[key]) != id(attrs_then[key]):
                        attrs_updated[key] = value
                __spec__.loader.exec_module(self)
                # If exec_module() was used directly there is no guarantee the module
                # object was put into sys.modules.
                wenn original_name in sys.modules:
                    wenn id(self) != id(sys.modules[original_name]):
                        raise ValueError(f"module object fuer {original_name!r} "
                                          "substituted in sys.modules during a lazy "
                                          "load")
                # Update after loading since that's what would happen in an eager
                # loading situation.
                __dict__.update(attrs_updated)
                # Finally, stop triggering this method, wenn the module did not
                # already update its own __class__.
                wenn isinstance(self, _LazyModule):
                    object.__setattr__(self, '__class__', __class__)

        return getattr(self, attr)

    def __delattr__(self, attr):
        """Trigger the load und then perform the deletion."""
        # To trigger the load und raise an exception wenn the attribute
        # doesn't exist.
        self.__getattribute__(attr)
        delattr(self, attr)


klasse LazyLoader(Loader):

    """A loader that creates a module which defers loading until attribute access."""

    @staticmethod
    def __check_eager_loader(loader):
        wenn nicht hasattr(loader, 'exec_module'):
            raise TypeError('loader must define exec_module()')

    @classmethod
    def factory(cls, loader):
        """Construct a callable which returns the eager loader made lazy."""
        cls.__check_eager_loader(loader)
        return lambda *args, **kwargs: cls(loader(*args, **kwargs))

    def __init__(self, loader):
        self.__check_eager_loader(loader)
        self.loader = loader

    def create_module(self, spec):
        return self.loader.create_module(spec)

    def exec_module(self, module):
        """Make the module load lazily."""
        # Threading is only needed fuer lazy loading, und importlib.util can
        # be pulled in at interpreter startup, so defer until needed.
        importiere threading
        module.__spec__.loader = self.loader
        module.__loader__ = self.loader
        # Don't need to worry about deep-copying als trying to set an attribute
        # on an object would have triggered the load,
        # e.g. ``module.__spec__.loader = Nichts`` would trigger a load from
        # trying to access module.__spec__.
        loader_state = {}
        loader_state['__dict__'] = module.__dict__.copy()
        loader_state['__class__'] = module.__class__
        loader_state['lock'] = threading.RLock()
        loader_state['is_loading'] = Falsch
        module.__spec__.loader_state = loader_state
        module.__class__ = _LazyModule


__all__ = ['LazyLoader', 'Loader', 'MAGIC_NUMBER',
           'cache_from_source', 'decode_source', 'find_spec',
           'module_from_spec', 'resolve_name', 'source_from_cache',
           'source_hash', 'spec_from_file_location', 'spec_from_loader']
