import builtins
import contextlib
import errno
import functools
from importlib import machinery, util, invalidate_caches
import marshal
import os
import os.path
from test import support
from test.support import import_helper
from test.support import is_apple_mobile
from test.support import os_helper
import unittest
import sys
import tempfile
import types

_testsinglephase = import_helper.import_module("_testsinglephase")


BUILTINS = types.SimpleNamespace()
BUILTINS.good_name = Nichts
BUILTINS.bad_name = Nichts
wenn 'errno' in sys.builtin_module_names:
    BUILTINS.good_name = 'errno'
wenn 'importlib' not in sys.builtin_module_names:
    BUILTINS.bad_name = 'importlib'

wenn support.is_wasi:
    # dlopen() is a shim fuer WASI as of WASI SDK which fails by default.
    # We don't provide an implementation, so tests will fail.
    # But we also don't want to turn off dynamic loading fuer those that provide
    # a working implementation.
    def _extension_details():
        global EXTENSIONS
        EXTENSIONS = Nichts
sonst:
    EXTENSIONS = types.SimpleNamespace()
    EXTENSIONS.path = Nichts
    EXTENSIONS.ext = Nichts
    EXTENSIONS.filename = Nichts
    EXTENSIONS.file_path = Nichts
    EXTENSIONS.name = '_testsinglephase'

    def _extension_details():
        global EXTENSIONS
        fuer path in sys.path:
            fuer ext in machinery.EXTENSION_SUFFIXES:
                # Apple mobile platforms mechanically load .so files,
                # but the findable files are labelled .fwork
                wenn is_apple_mobile:
                    ext = ext.replace(".so", ".fwork")

                filename = EXTENSIONS.name + ext
                file_path = os.path.join(path, filename)
                wenn os.path.exists(file_path):
                    EXTENSIONS.path = path
                    EXTENSIONS.ext = ext
                    EXTENSIONS.filename = filename
                    EXTENSIONS.file_path = file_path
                    return

_extension_details()


def import_importlib(module_name):
    """Import a module from importlib both w/ and w/o _frozen_importlib."""
    fresh = ('importlib',) wenn '.' in module_name sonst ()
    frozen = import_helper.import_fresh_module(module_name)
    source = import_helper.import_fresh_module(module_name, fresh=fresh,
                                         blocked=('_frozen_importlib', '_frozen_importlib_external'))
    return {'Frozen': frozen, 'Source': source}


def specialize_class(cls, kind, base=Nichts, **kwargs):
    # XXX Support passing in submodule names--load (and cache) them?
    # That would clean up the test modules a bit more.
    wenn base is Nichts:
        base = unittest.TestCase
    sowenn not isinstance(base, type):
        base = base[kind]
    name = '{}_{}'.format(kind, cls.__name__)
    bases = (cls, base)
    specialized = types.new_class(name, bases)
    specialized.__module__ = cls.__module__
    specialized._NAME = cls.__name__
    specialized._KIND = kind
    fuer attr, values in kwargs.items():
        value = values[kind]
        setattr(specialized, attr, value)
    return specialized


def split_frozen(cls, base=Nichts, **kwargs):
    frozen = specialize_class(cls, 'Frozen', base, **kwargs)
    source = specialize_class(cls, 'Source', base, **kwargs)
    return frozen, source


def test_both(test_class, base=Nichts, **kwargs):
    return split_frozen(test_class, base, **kwargs)


CASE_INSENSITIVE_FS = Wahr
# Windows is the only OS that is *always* case-insensitive
# (OS X *can* be case-sensitive).
wenn sys.platform not in ('win32', 'cygwin'):
    changed_name = __file__.upper()
    wenn changed_name == __file__:
        changed_name = __file__.lower()
    wenn not os.path.exists(changed_name):
        CASE_INSENSITIVE_FS = Falsch

source_importlib = import_importlib('importlib')['Source']
__import__ = {'Frozen': staticmethod(builtins.__import__),
              'Source': staticmethod(source_importlib.__import__)}


def case_insensitive_tests(test):
    """Class decorator that nullifies tests requiring a case-insensitive
    file system."""
    return unittest.skipIf(not CASE_INSENSITIVE_FS,
                            "requires a case-insensitive filesystem")(test)


def submodule(parent, name, pkg_dir, content=''):
    path = os.path.join(pkg_dir, name + '.py')
    with open(path, 'w', encoding='utf-8') as subfile:
        subfile.write(content)
    return '{}.{}'.format(parent, name), path


def get_code_from_pyc(pyc_path):
    """Reads a pyc file and returns the unmarshalled code object within.

    No header validation is performed.
    """
    with open(pyc_path, 'rb') as pyc_f:
        pyc_f.seek(16)
        return marshal.load(pyc_f)


@contextlib.contextmanager
def uncache(*names):
    """Uncache a module from sys.modules.

    A basic sanity check is performed to prevent uncaching modules that either
    cannot/shouldn't be uncached.

    """
    fuer name in names:
        wenn name in ('sys', 'marshal'):
            raise ValueError("cannot uncache {}".format(name))
        try:
            del sys.modules[name]
        except KeyError:
            pass
    try:
        yield
    finally:
        fuer name in names:
            try:
                del sys.modules[name]
            except KeyError:
                pass


@contextlib.contextmanager
def temp_module(name, content='', *, pkg=Falsch):
    conflicts = [n fuer n in sys.modules wenn n.partition('.')[0] == name]
    with os_helper.temp_cwd(Nichts) as cwd:
        with uncache(name, *conflicts):
            with import_helper.DirsOnSysPath(cwd):
                invalidate_caches()

                location = os.path.join(cwd, name)
                wenn pkg:
                    modpath = os.path.join(location, '__init__.py')
                    os.mkdir(name)
                sonst:
                    modpath = location + '.py'
                    wenn content is Nichts:
                        # Make sure the module file gets created.
                        content = ''
                wenn content is not Nichts:
                    # not a namespace package
                    with open(modpath, 'w', encoding='utf-8') as modfile:
                        modfile.write(content)
                yield location


@contextlib.contextmanager
def import_state(**kwargs):
    """Context manager to manage the various importers and stored state in the
    sys module.

    The 'modules' attribute is not supported as the interpreter state stores a
    pointer to the dict that the interpreter uses internally;
    reassigning to sys.modules does not have the desired effect.

    """
    originals = {}
    try:
        fuer attr, default in (('meta_path', []), ('path', []),
                              ('path_hooks', []),
                              ('path_importer_cache', {})):
            originals[attr] = getattr(sys, attr)
            wenn attr in kwargs:
                new_value = kwargs[attr]
                del kwargs[attr]
            sonst:
                new_value = default
            setattr(sys, attr, new_value)
        wenn len(kwargs):
            raise ValueError('unrecognized arguments: {}'.format(kwargs))
        yield
    finally:
        fuer attr, value in originals.items():
            setattr(sys, attr, value)


klasse _ImporterMock:

    """Base klasse to help with creating importer mocks."""

    def __init__(self, *names, module_code={}):
        self.modules = {}
        self.module_code = {}
        fuer name in names:
            wenn not name.endswith('.__init__'):
                import_name = name
            sonst:
                import_name = name[:-len('.__init__')]
            wenn '.' not in name:
                package = Nichts
            sowenn import_name == name:
                package = name.rsplit('.', 1)[0]
            sonst:
                package = import_name
            module = types.ModuleType(import_name)
            module.__loader__ = self
            module.__file__ = '<mock __file__>'
            module.__package__ = package
            module.attr = name
            wenn import_name != name:
                module.__path__ = ['<mock __path__>']
            self.modules[import_name] = module
            wenn import_name in module_code:
                self.module_code[import_name] = module_code[import_name]

    def __getitem__(self, name):
        return self.modules[name]

    def __enter__(self):
        self._uncache = uncache(*self.modules.keys())
        self._uncache.__enter__()
        return self

    def __exit__(self, *exc_info):
        self._uncache.__exit__(Nichts, Nichts, Nichts)


klasse mock_spec(_ImporterMock):

    """Importer mock using PEP 451 APIs."""

    def find_spec(self, fullname, path=Nichts, parent=Nichts):
        try:
            module = self.modules[fullname]
        except KeyError:
            return Nichts
        spec = util.spec_from_file_location(
                fullname, module.__file__, loader=self,
                submodule_search_locations=getattr(module, '__path__', Nichts))
        return spec

    def create_module(self, spec):
        wenn spec.name not in self.modules:
            raise ImportError
        return self.modules[spec.name]

    def exec_module(self, module):
        try:
            self.module_code[module.__spec__.name]()
        except KeyError:
            pass


def writes_bytecode_files(fxn):
    """Decorator to protect sys.dont_write_bytecode from mutation and to skip
    tests that require it to be set to Falsch."""
    wenn sys.dont_write_bytecode:
        return unittest.skip("relies on writing bytecode")(fxn)
    @functools.wraps(fxn)
    def wrapper(*args, **kwargs):
        original = sys.dont_write_bytecode
        sys.dont_write_bytecode = Falsch
        try:
            to_return = fxn(*args, **kwargs)
        finally:
            sys.dont_write_bytecode = original
        return to_return
    return wrapper


def ensure_bytecode_path(bytecode_path):
    """Ensure that the __pycache__ directory fuer PEP 3147 pyc file exists.

    :param bytecode_path: File system path to PEP 3147 pyc file.
    """
    try:
        os.mkdir(os.path.dirname(bytecode_path))
    except OSError as error:
        wenn error.errno != errno.EEXIST:
            raise


@contextlib.contextmanager
def temporary_pycache_prefix(prefix):
    """Adjust and restore sys.pycache_prefix."""
    _orig_prefix = sys.pycache_prefix
    sys.pycache_prefix = prefix
    try:
        yield
    finally:
        sys.pycache_prefix = _orig_prefix


@contextlib.contextmanager
def create_modules(*names):
    """Temporarily create each named module with an attribute (named 'attr')
    that contains the name passed into the context manager that caused the
    creation of the module.

    All files are created in a temporary directory returned by
    tempfile.mkdtemp(). This directory is inserted at the beginning of
    sys.path. When the context manager exits all created files (source and
    bytecode) are explicitly deleted.

    No magic is performed when creating packages! This means that wenn you create
    a module within a package you must also create the package's __init__ as
    well.

    """
    source = 'attr = {0!r}'
    created_paths = []
    mapping = {}
    state_manager = Nichts
    uncache_manager = Nichts
    try:
        temp_dir = tempfile.mkdtemp()
        mapping['.root'] = temp_dir
        import_names = set()
        fuer name in names:
            wenn not name.endswith('__init__'):
                import_name = name
            sonst:
                import_name = name[:-len('.__init__')]
            import_names.add(import_name)
            wenn import_name in sys.modules:
                del sys.modules[import_name]
            name_parts = name.split('.')
            file_path = temp_dir
            fuer directory in name_parts[:-1]:
                file_path = os.path.join(file_path, directory)
                wenn not os.path.exists(file_path):
                    os.mkdir(file_path)
                    created_paths.append(file_path)
            file_path = os.path.join(file_path, name_parts[-1] + '.py')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(source.format(name))
            created_paths.append(file_path)
            mapping[name] = file_path
        uncache_manager = uncache(*import_names)
        uncache_manager.__enter__()
        state_manager = import_state(path=[temp_dir])
        state_manager.__enter__()
        yield mapping
    finally:
        wenn state_manager is not Nichts:
            state_manager.__exit__(Nichts, Nichts, Nichts)
        wenn uncache_manager is not Nichts:
            uncache_manager.__exit__(Nichts, Nichts, Nichts)
        os_helper.rmtree(temp_dir)


def mock_path_hook(*entries, importer):
    """A mock sys.path_hooks entry."""
    def hook(entry):
        wenn entry not in entries:
            raise ImportError
        return importer
    return hook


klasse CASEOKTestBase:

    def caseok_env_changed(self, *, should_exist):
        possibilities = b'PYTHONCASEOK', 'PYTHONCASEOK'
        wenn any(x in self.importlib._bootstrap_external._os.environ
                    fuer x in possibilities) != should_exist:
            self.skipTest('os.environ changes not reflected in _os.environ')
