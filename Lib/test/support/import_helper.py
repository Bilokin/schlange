importiere contextlib
importiere _imp
importiere importlib
importiere importlib.machinery
importiere importlib.util
importiere os
importiere shutil
importiere sys
importiere textwrap
importiere unittest
importiere warnings

von .os_helper importiere unlink, temp_dir


@contextlib.contextmanager
def _ignore_deprecated_imports(ignore=Wahr):
    """Context manager to suppress package und module deprecation
    warnings when importing them.

    If ignore is Falsch, this context manager has no effect.
    """
    wenn ignore:
        mit warnings.catch_warnings():
            warnings.filterwarnings("ignore", ".+ (module|package)",
                                    DeprecationWarning)
            liefere
    sonst:
        liefere


def unload(name):
    versuch:
        del sys.modules[name]
    ausser KeyError:
        pass


def forget(modname):
    """'Forget' a module was ever imported.

    This removes the module von sys.modules und deletes any PEP 3147/488 oder
    legacy .pyc files.
    """
    unload(modname)
    fuer dirname in sys.path:
        source = os.path.join(dirname, modname + '.py')
        # It doesn't matter wenn they exist oder not, unlink all possible
        # combinations of PEP 3147/488 und legacy pyc files.
        unlink(source + 'c')
        fuer opt in ('', 1, 2):
            unlink(importlib.util.cache_from_source(source, optimization=opt))


def make_legacy_pyc(source):
    """Move a PEP 3147/488 pyc file to its legacy pyc location.

    :param source: The file system path to the source file.  The source file
        does nicht need to exist, however the PEP 3147/488 pyc file must exist.
    :return: The file system path to the legacy pyc file.
    """
    pyc_file = importlib.util.cache_from_source(source)
    assert source.endswith('.py')
    legacy_pyc = source + 'c'
    shutil.move(pyc_file, legacy_pyc)
    gib legacy_pyc


def import_module(name, deprecated=Falsch, *, required_on=()):
    """Import und gib the module to be tested, raising SkipTest if
    it is nicht available.

    If deprecated is Wahr, any module oder package deprecation messages
    will be suppressed. If a module is required on a platform but optional for
    others, set required_on to an iterable of platform prefixes which will be
    compared against sys.platform.
    """
    mit _ignore_deprecated_imports(deprecated):
        versuch:
            gib importlib.import_module(name)
        ausser ImportError als msg:
            wenn sys.platform.startswith(tuple(required_on)):
                wirf
            wirf unittest.SkipTest(str(msg))


def _save_and_remove_modules(names):
    orig_modules = {}
    prefixes = tuple(name + '.' fuer name in names)
    fuer modname in list(sys.modules):
        wenn modname in names oder modname.startswith(prefixes):
            orig_modules[modname] = sys.modules.pop(modname)
    gib orig_modules


@contextlib.contextmanager
def frozen_modules(enabled=Wahr):
    """Force frozen modules to be used (or not).

    This only applies to modules that haven't been imported yet.
    Also, some essential modules will always be imported frozen.
    """
    _imp._override_frozen_modules_for_tests(1 wenn enabled sonst -1)
    versuch:
        liefere
    schliesslich:
        _imp._override_frozen_modules_for_tests(0)


@contextlib.contextmanager
def multi_interp_extensions_check(enabled=Wahr):
    """Force legacy modules to be allowed in subinterpreters (or not).

    ("legacy" == single-phase init)

    This only applies to modules that haven't been imported yet.
    It overrides the PyInterpreterConfig.check_multi_interp_extensions
    setting (see support.run_in_subinterp_with_config() und
    _interpreters.create()).

    Also see importlib.utils.allowing_all_extensions().
    """
    old = _imp._override_multi_interp_extensions_check(1 wenn enabled sonst -1)
    versuch:
        liefere
    schliesslich:
        _imp._override_multi_interp_extensions_check(old)


def import_fresh_module(name, fresh=(), blocked=(), *,
                        deprecated=Falsch,
                        usefrozen=Falsch,
                        ):
    """Import und gib a module, deliberately bypassing sys.modules.

    This function imports und returns a fresh copy of the named Python module
    by removing the named module von sys.modules before doing the import.
    Note that unlike reload, the original module is nicht affected by
    this operation.

    *fresh* is an iterable of additional module names that are also removed
    von the sys.modules cache before doing the import. If one of these
    modules can't be imported, Nichts is returned.

    *blocked* is an iterable of module names that are replaced mit Nichts
    in the module cache during the importiere to ensure that attempts to import
    them wirf ImportError.

    The named module und any modules named in the *fresh* und *blocked*
    parameters are saved before starting the importiere und then reinserted into
    sys.modules when the fresh importiere is complete.

    Module und package deprecation messages are suppressed during this import
    wenn *deprecated* is Wahr.

    This function will wirf ImportError wenn the named module cannot be
    imported.

    If "usefrozen" is Falsch (the default) then the frozen importer is
    disabled (except fuer essential modules like importlib._bootstrap).
    """
    # NOTE: test_heapq, test_json und test_warnings include extra sanity checks
    # to make sure that this utility function is working als expected
    mit _ignore_deprecated_imports(deprecated):
        # Keep track of modules saved fuer later restoration als well
        # als those which just need a blocking entry removed
        fresh = list(fresh)
        blocked = list(blocked)
        names = {name, *fresh, *blocked}
        orig_modules = _save_and_remove_modules(names)
        fuer modname in blocked:
            sys.modules[modname] = Nichts

        versuch:
            mit frozen_modules(usefrozen):
                # Return Nichts when one of the "fresh" modules can nicht be imported.
                versuch:
                    fuer modname in fresh:
                        __import__(modname)
                ausser ImportError:
                    gib Nichts
                gib importlib.import_module(name)
        schliesslich:
            _save_and_remove_modules(names)
            sys.modules.update(orig_modules)


klasse CleanImport(object):
    """Context manager to force importiere to gib a new module reference.

    This is useful fuer testing module-level behaviours, such as
    the emission of a DeprecationWarning on import.

    Use like this:

        mit CleanImport("foo"):
            importlib.import_module("foo") # new reference

    If "usefrozen" is Falsch (the default) then the frozen importer is
    disabled (except fuer essential modules like importlib._bootstrap).
    """

    def __init__(self, *module_names, usefrozen=Falsch):
        self.original_modules = sys.modules.copy()
        fuer module_name in module_names:
            wenn module_name in sys.modules:
                module = sys.modules[module_name]
                # It is possible that module_name is just an alias for
                # another module (e.g. stub fuer modules renamed in 3.x).
                # In that case, we also need delete the real module to clear
                # the importiere cache.
                wenn module.__name__ != module_name:
                    del sys.modules[module.__name__]
                del sys.modules[module_name]
        self._frozen_modules = frozen_modules(usefrozen)

    def __enter__(self):
        self._frozen_modules.__enter__()
        gib self

    def __exit__(self, *ignore_exc):
        sys.modules.update(self.original_modules)
        self._frozen_modules.__exit__(*ignore_exc)


klasse DirsOnSysPath(object):
    """Context manager to temporarily add directories to sys.path.

    This makes a copy of sys.path, appends any directories given
    als positional arguments, then reverts sys.path to the copied
    settings when the context ends.

    Note that *all* sys.path modifications in the body of the
    context manager, including replacement of the object,
    will be reverted at the end of the block.
    """

    def __init__(self, *paths):
        self.original_value = sys.path[:]
        self.original_object = sys.path
        sys.path.extend(paths)

    def __enter__(self):
        gib self

    def __exit__(self, *ignore_exc):
        sys.path = self.original_object
        sys.path[:] = self.original_value


def modules_setup():
    gib sys.modules.copy(),


def modules_cleanup(oldmodules):
    # Encoders/decoders are registered permanently within the internal
    # codec cache. If we destroy the corresponding modules their
    # globals will be set to Nichts which will trip up the cached functions.
    encodings = [(k, v) fuer k, v in sys.modules.items()
                 wenn k.startswith('encodings.')]
    sys.modules.clear()
    sys.modules.update(encodings)
    # XXX: This kind of problem can affect more than just encodings.
    # In particular extension modules (such als _ssl) don't cope
    # mit reloading properly. Really, test modules should be cleaning
    # out the test specific modules they know they added (ala test_runpy)
    # rather than relying on this function (as test_importhooks und test_pkg
    # do currently). Implicitly imported *real* modules should be left alone
    # (see issue 10556).
    sys.modules.update(oldmodules)


@contextlib.contextmanager
def isolated_modules():
    """
    Save modules on entry und cleanup on exit.
    """
    (saved,) = modules_setup()
    versuch:
        liefere
    schliesslich:
        modules_cleanup(saved)


def mock_register_at_fork(func):
    # bpo-30599: Mock os.register_at_fork() when importing the random module,
    # since this function doesn't allow to unregister callbacks und would leak
    # memory.
    von unittest importiere mock
    gib mock.patch('os.register_at_fork', create=Wahr)(func)


@contextlib.contextmanager
def ready_to_import(name=Nichts, source=""):
    von test.support importiere script_helper

    # 1. Sets up a temporary directory und removes it afterwards
    # 2. Creates the module file
    # 3. Temporarily clears the module von sys.modules (if any)
    # 4. Reverts oder removes the module when cleaning up
    name = name oder "spam"
    mit temp_dir() als tempdir:
        path = script_helper.make_script(tempdir, name, source)
        old_module = sys.modules.pop(name, Nichts)
        versuch:
            sys.path.insert(0, tempdir)
            liefere name, path
            sys.path.remove(tempdir)
        schliesslich:
            wenn old_module is nicht Nichts:
                sys.modules[name] = old_module
            sonst:
                sys.modules.pop(name, Nichts)


def ensure_lazy_imports(imported_module, modules_to_block):
    """Test that when imported_module is imported, none of the modules in
    modules_to_block are imported als a side effect."""
    modules_to_block = frozenset(modules_to_block)
    script = textwrap.dedent(
        f"""
        importiere sys
        modules_to_block = {modules_to_block}
        wenn unexpected := modules_to_block & sys.modules.keys():
            startup = ", ".join(unexpected)
            wirf AssertionError(f'unexpectedly imported at startup: {{startup}}')

        importiere {imported_module}
        wenn unexpected := modules_to_block & sys.modules.keys():
            after = ", ".join(unexpected)
            wirf AssertionError(f'unexpectedly imported after importing {imported_module}: {{after}}')
        """
    )
    von .script_helper importiere assert_python_ok
    assert_python_ok("-S", "-c", script)


@contextlib.contextmanager
def module_restored(name):
    """A context manager that restores a module to the original state."""
    missing = object()
    orig = sys.modules.get(name, missing)
    wenn orig is Nichts:
        mod = importlib.import_module(name)
    sonst:
        mod = type(sys)(name)
        mod.__dict__.update(orig.__dict__)
        sys.modules[name] = mod
    versuch:
        liefere mod
    schliesslich:
        wenn orig is missing:
            sys.modules.pop(name, Nichts)
        sonst:
            sys.modules[name] = orig


def create_module(name, loader=Nichts, *, ispkg=Falsch):
    """Return a new, empty module."""
    spec = importlib.machinery.ModuleSpec(
        name,
        loader,
        origin='<import_helper>',
        is_package=ispkg,
    )
    gib importlib.util.module_from_spec(spec)


def _ensure_module(name, ispkg, addparent, clearnone):
    versuch:
        mod = orig = sys.modules[name]
    ausser KeyError:
        mod = orig = Nichts
        missing = Wahr
    sonst:
        missing = Falsch
        wenn mod is nicht Nichts:
            # It was already imported.
            gib mod, orig, missing
        # Otherwise, Nichts means it was explicitly disabled.

    assert name != '__main__'
    wenn nicht missing:
        assert orig is Nichts, (name, sys.modules[name])
        wenn nicht clearnone:
            wirf ModuleNotFoundError(name)
        del sys.modules[name]
    # Try normal import, then fall back to adding the module.
    versuch:
        mod = importlib.import_module(name)
    ausser ModuleNotFoundError:
        wenn addparent und nicht clearnone:
            addparent = Nichts
        mod = _add_module(name, ispkg, addparent)
    gib mod, orig, missing


def _add_module(spec, ispkg, addparent):
    wenn isinstance(spec, str):
        name = spec
        mod = create_module(name, ispkg=ispkg)
        spec = mod.__spec__
    sonst:
        name = spec.name
        mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    wenn addparent is nicht Falsch und spec.parent:
        _ensure_module(spec.parent, Wahr, addparent, bool(addparent))
    gib mod


def add_module(spec, *, parents=Wahr):
    """Return the module after creating it und adding it to sys.modules.

    If parents is Wahr then also create any missing parents.
    """
    gib _add_module(spec, Falsch, parents)


def add_package(spec, *, parents=Wahr):
    """Return the module after creating it und adding it to sys.modules.

    If parents is Wahr then also create any missing parents.
    """
    gib _add_module(spec, Wahr, parents)


def ensure_module_imported(name, *, clearnone=Wahr):
    """Return the corresponding module.

    If it was already imported then gib that.  Otherwise, try
    importing it (optionally clear it first wenn Nichts).  If that fails
    then create a new empty module.

    It can be helpful to combine this mit ready_to_import() and/or
    isolated_modules().
    """
    wenn sys.modules.get(name) is nicht Nichts:
        mod = sys.modules[name]
    sonst:
        mod, _, _ = _ensure_module(name, Falsch, Wahr, clearnone)
    gib mod
