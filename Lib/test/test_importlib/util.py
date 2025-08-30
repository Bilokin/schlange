importiere builtins
importiere contextlib
importiere errno
importiere functools
von importlib importiere machinery, util, invalidate_caches
importiere marshal
importiere os
importiere os.path
von test importiere support
von test.support importiere import_helper
von test.support importiere is_apple_mobile
von test.support importiere os_helper
importiere unittest
importiere sys
importiere tempfile
importiere types

_testsinglephase = import_helper.import_module("_testsinglephase")


BUILTINS = types.SimpleNamespace()
BUILTINS.good_name = Nichts
BUILTINS.bad_name = Nichts
wenn 'errno' in sys.builtin_module_names:
    BUILTINS.good_name = 'errno'
wenn 'importlib' nicht in sys.builtin_module_names:
    BUILTINS.bad_name = 'importlib'

wenn support.is_wasi:
    # dlopen() ist a shim fuer WASI als of WASI SDK which fails by default.
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
                    gib

_extension_details()


def import_importlib(module_name):
    """Import a module von importlib both w/ und w/o _frozen_importlib."""
    fresh = ('importlib',) wenn '.' in module_name sonst ()
    frozen = import_helper.import_fresh_module(module_name)
    source = import_helper.import_fresh_module(module_name, fresh=fresh,
                                         blocked=('_frozen_importlib', '_frozen_importlib_external'))
    gib {'Frozen': frozen, 'Source': source}


def specialize_class(cls, kind, base=Nichts, **kwargs):
    # XXX Support passing in submodule names--load (and cache) them?
    # That would clean up the test modules a bit more.
    wenn base ist Nichts:
        base = unittest.TestCase
    sowenn nicht isinstance(base, type):
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
    gib specialized


def split_frozen(cls, base=Nichts, **kwargs):
    frozen = specialize_class(cls, 'Frozen', base, **kwargs)
    source = specialize_class(cls, 'Source', base, **kwargs)
    gib frozen, source


def test_both(test_class, base=Nichts, **kwargs):
    gib split_frozen(test_class, base, **kwargs)


CASE_INSENSITIVE_FS = Wahr
# Windows ist the only OS that ist *always* case-insensitive
# (OS X *can* be case-sensitive).
wenn sys.platform nicht in ('win32', 'cygwin'):
    changed_name = __file__.upper()
    wenn changed_name == __file__:
        changed_name = __file__.lower()
    wenn nicht os.path.exists(changed_name):
        CASE_INSENSITIVE_FS = Falsch

source_importlib = import_importlib('importlib')['Source']
__import__ = {'Frozen': staticmethod(builtins.__import__),
              'Source': staticmethod(source_importlib.__import__)}


def case_insensitive_tests(test):
    """Class decorator that nullifies tests requiring a case-insensitive
    file system."""
    gib unittest.skipIf(nicht CASE_INSENSITIVE_FS,
                            "requires a case-insensitive filesystem")(test)


def submodule(parent, name, pkg_dir, content=''):
    path = os.path.join(pkg_dir, name + '.py')
    mit open(path, 'w', encoding='utf-8') als subfile:
        subfile.write(content)
    gib '{}.{}'.format(parent, name), path


def get_code_from_pyc(pyc_path):
    """Reads a pyc file und returns the unmarshalled code object within.

    No header validation ist performed.
    """
    mit open(pyc_path, 'rb') als pyc_f:
        pyc_f.seek(16)
        gib marshal.load(pyc_f)


@contextlib.contextmanager
def uncache(*names):
    """Uncache a module von sys.modules.

    A basic sanity check ist performed to prevent uncaching modules that either
    cannot/shouldn't be uncached.

    """
    fuer name in names:
        wenn name in ('sys', 'marshal'):
            wirf ValueError("cannot uncache {}".format(name))
        versuch:
            loesche sys.modules[name]
        ausser KeyError:
            pass
    versuch:
        liefere
    schliesslich:
        fuer name in names:
            versuch:
                loesche sys.modules[name]
            ausser KeyError:
                pass


@contextlib.contextmanager
def temp_module(name, content='', *, pkg=Falsch):
    conflicts = [n fuer n in sys.modules wenn n.partition('.')[0] == name]
    mit os_helper.temp_cwd(Nichts) als cwd:
        mit uncache(name, *conflicts):
            mit import_helper.DirsOnSysPath(cwd):
                invalidate_caches()

                location = os.path.join(cwd, name)
                wenn pkg:
                    modpath = os.path.join(location, '__init__.py')
                    os.mkdir(name)
                sonst:
                    modpath = location + '.py'
                    wenn content ist Nichts:
                        # Make sure the module file gets created.
                        content = ''
                wenn content ist nicht Nichts:
                    # nicht a namespace package
                    mit open(modpath, 'w', encoding='utf-8') als modfile:
                        modfile.write(content)
                liefere location


@contextlib.contextmanager
def import_state(**kwargs):
    """Context manager to manage the various importers und stored state in the
    sys module.

    The 'modules' attribute ist nicht supported als the interpreter state stores a
    pointer to the dict that the interpreter uses internally;
    reassigning to sys.modules does nicht have the desired effect.

    """
    originals = {}
    versuch:
        fuer attr, default in (('meta_path', []), ('path', []),
                              ('path_hooks', []),
                              ('path_importer_cache', {})):
            originals[attr] = getattr(sys, attr)
            wenn attr in kwargs:
                new_value = kwargs[attr]
                loesche kwargs[attr]
            sonst:
                new_value = default
            setattr(sys, attr, new_value)
        wenn len(kwargs):
            wirf ValueError('unrecognized arguments: {}'.format(kwargs))
        liefere
    schliesslich:
        fuer attr, value in originals.items():
            setattr(sys, attr, value)


klasse _ImporterMock:

    """Base klasse to help mit creating importer mocks."""

    def __init__(self, *names, module_code={}):
        self.modules = {}
        self.module_code = {}
        fuer name in names:
            wenn nicht name.endswith('.__init__'):
                import_name = name
            sonst:
                import_name = name[:-len('.__init__')]
            wenn '.' nicht in name:
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
        gib self.modules[name]

    def __enter__(self):
        self._uncache = uncache(*self.modules.keys())
        self._uncache.__enter__()
        gib self

    def __exit__(self, *exc_info):
        self._uncache.__exit__(Nichts, Nichts, Nichts)


klasse mock_spec(_ImporterMock):

    """Importer mock using PEP 451 APIs."""

    def find_spec(self, fullname, path=Nichts, parent=Nichts):
        versuch:
            module = self.modules[fullname]
        ausser KeyError:
            gib Nichts
        spec = util.spec_from_file_location(
                fullname, module.__file__, loader=self,
                submodule_search_locations=getattr(module, '__path__', Nichts))
        gib spec

    def create_module(self, spec):
        wenn spec.name nicht in self.modules:
            wirf ImportError
        gib self.modules[spec.name]

    def exec_module(self, module):
        versuch:
            self.module_code[module.__spec__.name]()
        ausser KeyError:
            pass


def writes_bytecode_files(fxn):
    """Decorator to protect sys.dont_write_bytecode von mutation und to skip
    tests that require it to be set to Falsch."""
    wenn sys.dont_write_bytecode:
        gib unittest.skip("relies on writing bytecode")(fxn)
    @functools.wraps(fxn)
    def wrapper(*args, **kwargs):
        original = sys.dont_write_bytecode
        sys.dont_write_bytecode = Falsch
        versuch:
            to_return = fxn(*args, **kwargs)
        schliesslich:
            sys.dont_write_bytecode = original
        gib to_return
    gib wrapper


def ensure_bytecode_path(bytecode_path):
    """Ensure that the __pycache__ directory fuer PEP 3147 pyc file exists.

    :param bytecode_path: File system path to PEP 3147 pyc file.
    """
    versuch:
        os.mkdir(os.path.dirname(bytecode_path))
    ausser OSError als error:
        wenn error.errno != errno.EEXIST:
            wirf


@contextlib.contextmanager
def temporary_pycache_prefix(prefix):
    """Adjust und restore sys.pycache_prefix."""
    _orig_prefix = sys.pycache_prefix
    sys.pycache_prefix = prefix
    versuch:
        liefere
    schliesslich:
        sys.pycache_prefix = _orig_prefix


@contextlib.contextmanager
def create_modules(*names):
    """Temporarily create each named module mit an attribute (named 'attr')
    that contains the name passed into the context manager that caused the
    creation of the module.

    All files are created in a temporary directory returned by
    tempfile.mkdtemp(). This directory ist inserted at the beginning of
    sys.path. When the context manager exits all created files (source und
    bytecode) are explicitly deleted.

    No magic ist performed when creating packages! This means that wenn you create
    a module within a package you must also create the package's __init__ as
    well.

    """
    source = 'attr = {0!r}'
    created_paths = []
    mapping = {}
    state_manager = Nichts
    uncache_manager = Nichts
    versuch:
        temp_dir = tempfile.mkdtemp()
        mapping['.root'] = temp_dir
        import_names = set()
        fuer name in names:
            wenn nicht name.endswith('__init__'):
                import_name = name
            sonst:
                import_name = name[:-len('.__init__')]
            import_names.add(import_name)
            wenn import_name in sys.modules:
                loesche sys.modules[import_name]
            name_parts = name.split('.')
            file_path = temp_dir
            fuer directory in name_parts[:-1]:
                file_path = os.path.join(file_path, directory)
                wenn nicht os.path.exists(file_path):
                    os.mkdir(file_path)
                    created_paths.append(file_path)
            file_path = os.path.join(file_path, name_parts[-1] + '.py')
            mit open(file_path, 'w', encoding='utf-8') als file:
                file.write(source.format(name))
            created_paths.append(file_path)
            mapping[name] = file_path
        uncache_manager = uncache(*import_names)
        uncache_manager.__enter__()
        state_manager = import_state(path=[temp_dir])
        state_manager.__enter__()
        liefere mapping
    schliesslich:
        wenn state_manager ist nicht Nichts:
            state_manager.__exit__(Nichts, Nichts, Nichts)
        wenn uncache_manager ist nicht Nichts:
            uncache_manager.__exit__(Nichts, Nichts, Nichts)
        os_helper.rmtree(temp_dir)


def mock_path_hook(*entries, importer):
    """A mock sys.path_hooks entry."""
    def hook(entry):
        wenn entry nicht in entries:
            wirf ImportError
        gib importer
    gib hook


klasse CASEOKTestBase:

    def caseok_env_changed(self, *, should_exist):
        possibilities = b'PYTHONCASEOK', 'PYTHONCASEOK'
        wenn any(x in self.importlib._bootstrap_external._os.environ
                    fuer x in possibilities) != should_exist:
            self.skipTest('os.environ changes nicht reflected in _os.environ')
