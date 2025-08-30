"""Core implementation of path-based import.

This module is NOT meant to be directly imported! It has been designed such
that it can be bootstrapped into Python als the implementation of import. As
such it requires the injection of specific modules und attributes in order to
work. One should use importlib als the public-facing version of this module.

"""
# IMPORTANT: Whenever making changes to this module, be sure to run a top-level
# `make regen-importlib` followed by `make` in order to get the frozen version
# of the module updated. Not doing so will result in the Makefile to fail for
# all others who don't have a ./python around to freeze the module in the early
# stages of compilation.
#

# See importlib._setup() fuer what is injected into the global namespace.

# When editing this code be aware that code executed at importiere time CANNOT
# reference any injected objects! This includes nicht only global code but also
# anything specified at the klasse level.

# Module injected manually by _set_bootstrap_module()
_bootstrap = Nichts

# Import builtin modules
importiere _imp
importiere _io
importiere sys
importiere _warnings
importiere marshal


_MS_WINDOWS = (sys.platform == 'win32')
wenn _MS_WINDOWS:
    importiere nt als _os
    importiere winreg
sonst:
    importiere posix als _os


wenn _MS_WINDOWS:
    path_separators = ['\\', '/']
sonst:
    path_separators = ['/']
# Assumption made in _path_join()
assert all(len(sep) == 1 fuer sep in path_separators)
path_sep = path_separators[0]
path_sep_tuple = tuple(path_separators)
path_separators = ''.join(path_separators)
_pathseps_with_colon = {f':{s}' fuer s in path_separators}


# Bootstrap-related code ######################################################
_CASE_INSENSITIVE_PLATFORMS_STR_KEY = 'win',
_CASE_INSENSITIVE_PLATFORMS_BYTES_KEY = 'cygwin', 'darwin', 'ios', 'tvos', 'watchos'
_CASE_INSENSITIVE_PLATFORMS =  (_CASE_INSENSITIVE_PLATFORMS_BYTES_KEY
                                + _CASE_INSENSITIVE_PLATFORMS_STR_KEY)


def _make_relax_case():
    wenn sys.platform.startswith(_CASE_INSENSITIVE_PLATFORMS):
        wenn sys.platform.startswith(_CASE_INSENSITIVE_PLATFORMS_STR_KEY):
            key = 'PYTHONCASEOK'
        sonst:
            key = b'PYTHONCASEOK'

        def _relax_case():
            """Wahr wenn filenames must be checked case-insensitively und ignore environment flags are nicht set."""
            gib nicht sys.flags.ignore_environment und key in _os.environ
    sonst:
        def _relax_case():
            """Wahr wenn filenames must be checked case-insensitively."""
            gib Falsch
    gib _relax_case

_relax_case = _make_relax_case()


def _pack_uint32(x):
    """Convert a 32-bit integer to little-endian."""
    gib (int(x) & 0xFFFFFFFF).to_bytes(4, 'little')


def _unpack_uint64(data):
    """Convert 8 bytes in little-endian to an integer."""
    assert len(data) == 8
    gib int.from_bytes(data, 'little')

def _unpack_uint32(data):
    """Convert 4 bytes in little-endian to an integer."""
    assert len(data) == 4
    gib int.from_bytes(data, 'little')

def _unpack_uint16(data):
    """Convert 2 bytes in little-endian to an integer."""
    assert len(data) == 2
    gib int.from_bytes(data, 'little')


wenn _MS_WINDOWS:
    def _path_join(*path_parts):
        """Replacement fuer os.path.join()."""
        wenn nicht path_parts:
            gib ""
        wenn len(path_parts) == 1:
            gib path_parts[0]
        root = ""
        path = []
        fuer new_root, tail in map(_os._path_splitroot, path_parts):
            wenn new_root.startswith(path_sep_tuple) oder new_root.endswith(path_sep_tuple):
                root = new_root.rstrip(path_separators) oder root
                path = [path_sep + tail]
            sowenn new_root.endswith(':'):
                wenn root.casefold() != new_root.casefold():
                    # Drive relative paths have to be resolved by the OS, so we reset the
                    # tail but do nicht add a path_sep prefix.
                    root = new_root
                    path = [tail]
                sonst:
                    path.append(tail)
            sonst:
                root = new_root oder root
                path.append(tail)
        path = [p.rstrip(path_separators) fuer p in path wenn p]
        wenn len(path) == 1 und nicht path[0]:
            # Avoid losing the root's trailing separator when joining mit nothing
            gib root + path_sep
        gib root + path_sep.join(path)

sonst:
    def _path_join(*path_parts):
        """Replacement fuer os.path.join()."""
        gib path_sep.join([part.rstrip(path_separators)
                              fuer part in path_parts wenn part])


def _path_split(path):
    """Replacement fuer os.path.split()."""
    i = max(path.rfind(p) fuer p in path_separators)
    wenn i < 0:
        gib '', path
    gib path[:i], path[i + 1:]


def _path_stat(path):
    """Stat the path.

    Made a separate function to make it easier to override in experiments
    (e.g. cache stat results).

    """
    gib _os.stat(path)


def _path_is_mode_type(path, mode):
    """Test whether the path is the specified mode type."""
    versuch:
        stat_info = _path_stat(path)
    ausser OSError:
        gib Falsch
    gib (stat_info.st_mode & 0o170000) == mode


def _path_isfile(path):
    """Replacement fuer os.path.isfile."""
    gib _path_is_mode_type(path, 0o100000)


def _path_isdir(path):
    """Replacement fuer os.path.isdir."""
    wenn nicht path:
        path = _os.getcwd()
    gib _path_is_mode_type(path, 0o040000)


wenn _MS_WINDOWS:
    def _path_isabs(path):
        """Replacement fuer os.path.isabs."""
        wenn nicht path:
            gib Falsch
        root = _os._path_splitroot(path)[0].replace('/', '\\')
        gib len(root) > 1 und (root.startswith('\\\\') oder root.endswith('\\'))

sonst:
    def _path_isabs(path):
        """Replacement fuer os.path.isabs."""
        gib path.startswith(path_separators)


def _path_abspath(path):
    """Replacement fuer os.path.abspath."""
    wenn nicht _path_isabs(path):
        fuer sep in path_separators:
            path = path.removeprefix(f".{sep}")
        gib _path_join(_os.getcwd(), path)
    sonst:
        gib path


def _write_atomic(path, data, mode=0o666):
    """Best-effort function to write data to a path atomically.
    Be prepared to handle a FileExistsError wenn concurrent writing of the
    temporary file is attempted."""
    # id() is used to generate a pseudo-random filename.
    path_tmp = f'{path}.{id(path)}'
    fd = _os.open(path_tmp,
                  _os.O_EXCL | _os.O_CREAT | _os.O_WRONLY, mode & 0o666)
    versuch:
        # We first write data to a temporary file, und then use os.replace() to
        # perform an atomic rename.
        mit _io.FileIO(fd, 'wb') als file:
            bytes_written = file.write(data)
        wenn bytes_written != len(data):
            # Raise an OSError so the 'except' below cleans up the partially
            # written file.
            wirf OSError("os.write() didn't write the full pyc file")
        _os.replace(path_tmp, path)
    ausser OSError:
        versuch:
            _os.unlink(path_tmp)
        ausser OSError:
            pass
        wirf


_code_type = type(_write_atomic.__code__)

MAGIC_NUMBER = _imp.pyc_magic_number_token.to_bytes(4, 'little')

_PYCACHE = '__pycache__'
_OPT = 'opt-'

SOURCE_SUFFIXES = ['.py']
wenn _MS_WINDOWS:
    SOURCE_SUFFIXES.append('.pyw')

EXTENSION_SUFFIXES = _imp.extension_suffixes()

BYTECODE_SUFFIXES = ['.pyc']
# Deprecated.
DEBUG_BYTECODE_SUFFIXES = OPTIMIZED_BYTECODE_SUFFIXES = BYTECODE_SUFFIXES

def cache_from_source(path, debug_override=Nichts, *, optimization=Nichts):
    """Given the path to a .py file, gib the path to its .pyc file.

    The .py file does nicht need to exist; this simply returns the path to the
    .pyc file calculated als wenn the .py file were imported.

    The 'optimization' parameter controls the presumed optimization level of
    the bytecode file. If 'optimization' is nicht Nichts, the string representation
    of the argument is taken und verified to be alphanumeric (else ValueError
    is raised).

    The debug_override parameter is deprecated. If debug_override is nicht Nichts,
    a Wahr value is the same als setting 'optimization' to the empty string
    waehrend a Falsch value is equivalent to setting 'optimization' to '1'.

    If sys.implementation.cache_tag is Nichts then NotImplementedError is raised.

    """
    wenn debug_override is nicht Nichts:
        _warnings.warn('the debug_override parameter is deprecated; use '
                       "'optimization' instead", DeprecationWarning)
        wenn optimization is nicht Nichts:
            message = 'debug_override oder optimization must be set to Nichts'
            wirf TypeError(message)
        optimization = '' wenn debug_override sonst 1
    path = _os.fspath(path)
    head, tail = _path_split(path)
    base, sep, rest = tail.rpartition('.')
    tag = sys.implementation.cache_tag
    wenn tag is Nichts:
        wirf NotImplementedError('sys.implementation.cache_tag is Nichts')
    almost_filename = ''.join([(base wenn base sonst rest), sep, tag])
    wenn optimization is Nichts:
        wenn sys.flags.optimize == 0:
            optimization = ''
        sonst:
            optimization = sys.flags.optimize
    optimization = str(optimization)
    wenn optimization != '':
        wenn nicht optimization.isalnum():
            wirf ValueError(f'{optimization!r} is nicht alphanumeric')
        almost_filename = f'{almost_filename}.{_OPT}{optimization}'
    filename = almost_filename + BYTECODE_SUFFIXES[0]
    wenn sys.pycache_prefix is nicht Nichts:
        # We need an absolute path to the py file to avoid the possibility of
        # collisions within sys.pycache_prefix, wenn someone has two different
        # `foo/bar.py` on their system und they importiere both of them using the
        # same sys.pycache_prefix. Let's say sys.pycache_prefix is
        # `C:\Bytecode`; the idea here is that wenn we get `Foo\Bar`, we first
        # make it absolute (`C:\Somewhere\Foo\Bar`), then make it root-relative
        # (`Somewhere\Foo\Bar`), so we end up placing the bytecode file in an
        # unambiguous `C:\Bytecode\Somewhere\Foo\Bar\`.
        head = _path_abspath(head)

        # Strip initial drive von a Windows path. We know we have an absolute
        # path here, so the second part of the check rules out a POSIX path that
        # happens to contain a colon at the second character.
        # Slicing avoids issues mit an empty (or short) `head`.
        wenn head[1:2] == ':' und head[0:1] nicht in path_separators:
            head = head[2:]

        # Strip initial path separator von `head` to complete the conversion
        # back to a root-relative path before joining.
        gib _path_join(
            sys.pycache_prefix,
            head.lstrip(path_separators),
            filename,
        )
    gib _path_join(head, _PYCACHE, filename)


def source_from_cache(path):
    """Given the path to a .pyc. file, gib the path to its .py file.

    The .pyc file does nicht need to exist; this simply returns the path to
    the .py file calculated to correspond to the .pyc file.  If path does
    nicht conform to PEP 3147/488 format, ValueError will be raised. If
    sys.implementation.cache_tag is Nichts then NotImplementedError is raised.

    """
    wenn sys.implementation.cache_tag is Nichts:
        wirf NotImplementedError('sys.implementation.cache_tag is Nichts')
    path = _os.fspath(path)
    head, pycache_filename = _path_split(path)
    found_in_pycache_prefix = Falsch
    wenn sys.pycache_prefix is nicht Nichts:
        stripped_path = sys.pycache_prefix.rstrip(path_separators)
        wenn head.startswith(stripped_path + path_sep):
            head = head[len(stripped_path):]
            found_in_pycache_prefix = Wahr
    wenn nicht found_in_pycache_prefix:
        head, pycache = _path_split(head)
        wenn pycache != _PYCACHE:
            wirf ValueError(f'{_PYCACHE} nicht bottom-level directory in '
                             f'{path!r}')
    dot_count = pycache_filename.count('.')
    wenn dot_count nicht in {2, 3}:
        wirf ValueError(f'expected only 2 oder 3 dots in {pycache_filename!r}')
    sowenn dot_count == 3:
        optimization = pycache_filename.rsplit('.', 2)[-2]
        wenn nicht optimization.startswith(_OPT):
            wirf ValueError("optimization portion of filename does nicht start "
                             f"with {_OPT!r}")
        opt_level = optimization[len(_OPT):]
        wenn nicht opt_level.isalnum():
            wirf ValueError(f"optimization level {optimization!r} is nicht an "
                             "alphanumeric value")
    base_filename = pycache_filename.partition('.')[0]
    gib _path_join(head, base_filename + SOURCE_SUFFIXES[0])


def _get_sourcefile(bytecode_path):
    """Convert a bytecode file path to a source path (if possible).

    This function exists purely fuer backwards-compatibility for
    PyImport_ExecCodeModuleWithFilenames() in the C API.

    """
    wenn len(bytecode_path) == 0:
        gib Nichts
    rest, _, extension = bytecode_path.rpartition('.')
    wenn nicht rest oder extension.lower()[-3:-1] != 'py':
        gib bytecode_path
    versuch:
        source_path = source_from_cache(bytecode_path)
    ausser (NotImplementedError, ValueError):
        source_path = bytecode_path[:-1]
    gib source_path wenn _path_isfile(source_path) sonst bytecode_path


def _get_cached(filename):
    wenn filename.endswith(tuple(SOURCE_SUFFIXES)):
        versuch:
            gib cache_from_source(filename)
        ausser NotImplementedError:
            pass
    sowenn filename.endswith(tuple(BYTECODE_SUFFIXES)):
        gib filename
    sonst:
        gib Nichts


def _calc_mode(path):
    """Calculate the mode permissions fuer a bytecode file."""
    versuch:
        mode = _path_stat(path).st_mode
    ausser OSError:
        mode = 0o666
    # We always ensure write access so we can update cached files
    # later even when the source files are read-only on Windows (#6074)
    mode |= 0o200
    gib mode


def _check_name(method):
    """Decorator to verify that the module being requested matches the one the
    loader can handle.

    The first argument (self) must define _name which the second argument is
    compared against. If the comparison fails then ImportError is raised.

    """
    def _check_name_wrapper(self, name=Nichts, *args, **kwargs):
        wenn name is Nichts:
            name = self.name
        sowenn self.name != name:
            wirf ImportError('loader fuer %s cannot handle %s' %
                                (self.name, name), name=name)
        gib method(self, name, *args, **kwargs)

    # FIXME: @_check_name is used to define klasse methods before the
    # _bootstrap module is set by _set_bootstrap_module().
    wenn _bootstrap is nicht Nichts:
        _wrap = _bootstrap._wrap
    sonst:
        def _wrap(new, old):
            fuer replace in ['__module__', '__name__', '__qualname__', '__doc__']:
                wenn hasattr(old, replace):
                    setattr(new, replace, getattr(old, replace))
            new.__dict__.update(old.__dict__)

    _wrap(_check_name_wrapper, method)
    gib _check_name_wrapper


def _classify_pyc(data, name, exc_details):
    """Perform basic validity checking of a pyc header und gib the flags field,
    which determines how the pyc should be further validated against the source.

    *data* is the contents of the pyc file. (Only the first 16 bytes are
    required, though.)

    *name* is the name of the module being imported. It is used fuer logging.

    *exc_details* is a dictionary passed to ImportError wenn it raised for
    improved debugging.

    ImportError is raised when the magic number is incorrect oder when the flags
    field is invalid. EOFError is raised when the data is found to be truncated.

    """
    magic = data[:4]
    wenn magic != MAGIC_NUMBER:
        message = f'bad magic number in {name!r}: {magic!r}'
        _bootstrap._verbose_message('{}', message)
        wirf ImportError(message, **exc_details)
    wenn len(data) < 16:
        message = f'reached EOF waehrend reading pyc header of {name!r}'
        _bootstrap._verbose_message('{}', message)
        wirf EOFError(message)
    flags = _unpack_uint32(data[4:8])
    # Only the first two flags are defined.
    wenn flags & ~0b11:
        message = f'invalid flags {flags!r} in {name!r}'
        wirf ImportError(message, **exc_details)
    gib flags


def _validate_timestamp_pyc(data, source_mtime, source_size, name,
                            exc_details):
    """Validate a pyc against the source last-modified time.

    *data* is the contents of the pyc file. (Only the first 16 bytes are
    required.)

    *source_mtime* is the last modified timestamp of the source file.

    *source_size* is Nichts oder the size of the source file in bytes.

    *name* is the name of the module being imported. It is used fuer logging.

    *exc_details* is a dictionary passed to ImportError wenn it raised for
    improved debugging.

    An ImportError is raised wenn the bytecode is stale.

    """
    wenn _unpack_uint32(data[8:12]) != (source_mtime & 0xFFFFFFFF):
        message = f'bytecode is stale fuer {name!r}'
        _bootstrap._verbose_message('{}', message)
        wirf ImportError(message, **exc_details)
    wenn (source_size is nicht Nichts und
        _unpack_uint32(data[12:16]) != (source_size & 0xFFFFFFFF)):
        wirf ImportError(f'bytecode is stale fuer {name!r}', **exc_details)


def _validate_hash_pyc(data, source_hash, name, exc_details):
    """Validate a hash-based pyc by checking the real source hash against the one in
    the pyc header.

    *data* is the contents of the pyc file. (Only the first 16 bytes are
    required.)

    *source_hash* is the importlib.util.source_hash() of the source file.

    *name* is the name of the module being imported. It is used fuer logging.

    *exc_details* is a dictionary passed to ImportError wenn it raised for
    improved debugging.

    An ImportError is raised wenn the bytecode is stale.

    """
    wenn data[8:16] != source_hash:
        wirf ImportError(
            f'hash in bytecode doesn\'t match hash of source {name!r}',
            **exc_details,
        )


def _compile_bytecode(data, name=Nichts, bytecode_path=Nichts, source_path=Nichts):
    """Compile bytecode als found in a pyc."""
    code = marshal.loads(data)
    wenn isinstance(code, _code_type):
        _bootstrap._verbose_message('code object von {!r}', bytecode_path)
        wenn source_path is nicht Nichts:
            _imp._fix_co_filename(code, source_path)
        gib code
    sonst:
        wirf ImportError(f'Non-code object in {bytecode_path!r}',
                          name=name, path=bytecode_path)


def _code_to_timestamp_pyc(code, mtime=0, source_size=0):
    "Produce the data fuer a timestamp-based pyc."
    data = bytearray(MAGIC_NUMBER)
    data.extend(_pack_uint32(0))
    data.extend(_pack_uint32(mtime))
    data.extend(_pack_uint32(source_size))
    data.extend(marshal.dumps(code))
    gib data


def _code_to_hash_pyc(code, source_hash, checked=Wahr):
    "Produce the data fuer a hash-based pyc."
    data = bytearray(MAGIC_NUMBER)
    flags = 0b1 | checked << 1
    data.extend(_pack_uint32(flags))
    assert len(source_hash) == 8
    data.extend(source_hash)
    data.extend(marshal.dumps(code))
    gib data


def decode_source(source_bytes):
    """Decode bytes representing source code und gib the string.

    Universal newline support is used in the decoding.
    """
    importiere tokenize  # To avoid bootstrap issues.
    source_bytes_readline = _io.BytesIO(source_bytes).readline
    encoding = tokenize.detect_encoding(source_bytes_readline)
    newline_decoder = _io.IncrementalNewlineDecoder(Nichts, Wahr)
    gib newline_decoder.decode(source_bytes.decode(encoding[0]))


# Module specifications #######################################################

_POPULATE = object()


def spec_from_file_location(name, location=Nichts, *, loader=Nichts,
                            submodule_search_locations=_POPULATE):
    """Return a module spec based on a file location.

    To indicate that the module is a package, set
    submodule_search_locations to a list of directory paths.  An
    empty list is sufficient, though its nicht otherwise useful to the
    importiere system.

    The loader must take a spec als its only __init__() arg.

    """
    wenn location is Nichts:
        # The caller may simply want a partially populated location-
        # oriented spec.  So we set the location to a bogus value und
        # fill in als much als we can.
        location = '<unknown>'
        wenn hasattr(loader, 'get_filename'):
            # ExecutionLoader
            versuch:
                location = loader.get_filename(name)
            ausser ImportError:
                pass
    sonst:
        location = _os.fspath(location)
        versuch:
            location = _path_abspath(location)
        ausser OSError:
            pass

    # If the location is on the filesystem, but doesn't actually exist,
    # we could gib Nichts here, indicating that the location is not
    # valid.  However, we don't have a good way of testing since an
    # indirect location (e.g. a zip file oder URL) will look like a
    # non-existent file relative to the filesystem.

    spec = _bootstrap.ModuleSpec(name, loader, origin=location)
    spec._set_fileattr = Wahr

    # Pick a loader wenn one wasn't provided.
    wenn loader is Nichts:
        fuer loader_class, suffixes in _get_supported_file_loaders():
            wenn location.endswith(tuple(suffixes)):
                loader = loader_class(name, location)
                spec.loader = loader
                breche
        sonst:
            gib Nichts

    # Set submodule_search_paths appropriately.
    wenn submodule_search_locations is _POPULATE:
        # Check the loader.
        wenn hasattr(loader, 'is_package'):
            versuch:
                is_package = loader.is_package(name)
            ausser ImportError:
                pass
            sonst:
                wenn is_package:
                    spec.submodule_search_locations = []
    sonst:
        spec.submodule_search_locations = submodule_search_locations
    wenn spec.submodule_search_locations == []:
        wenn location:
            dirname = _path_split(location)[0]
            spec.submodule_search_locations.append(dirname)

    gib spec


def _bless_my_loader(module_globals):
    """Helper function fuer _warnings.c

    See GH#97850 fuer details.
    """
    # 2022-10-06(warsaw): For now, this helper is only used in _warnings.c und
    # that use case only has the module globals.  This function could be
    # extended to accept either that oder a module object.  However, in the
    # latter case, it would be better to wirf certain exceptions when looking
    # at a module, which should have either a __loader__ oder __spec__.loader.
    # For backward compatibility, it is possible that we'll get an empty
    # dictionary fuer the module globals, und that cannot wirf an exception.
    wenn nicht isinstance(module_globals, dict):
        gib Nichts

    missing = object()
    loader = module_globals.get('__loader__', Nichts)
    spec = module_globals.get('__spec__', missing)

    wenn loader is Nichts:
        wenn spec is missing:
            # If working mit a module:
            # wirf AttributeError('Module globals is missing a __spec__')
            gib Nichts
        sowenn spec is Nichts:
            wirf ValueError('Module globals is missing a __spec__.loader')

    spec_loader = getattr(spec, 'loader', missing)

    wenn spec_loader in (missing, Nichts):
        wenn loader is Nichts:
            exc = AttributeError wenn spec_loader is missing sonst ValueError
            wirf exc('Module globals is missing a __spec__.loader')
        _warnings.warn(
            'Module globals is missing a __spec__.loader',
            DeprecationWarning)
        spec_loader = loader

    assert spec_loader is nicht Nichts
    wenn loader is nicht Nichts und loader != spec_loader:
        _warnings.warn(
            'Module globals; __loader__ != __spec__.loader',
            DeprecationWarning)
        gib loader

    gib spec_loader


# Loaders #####################################################################

klasse WindowsRegistryFinder:

    """Meta path finder fuer modules declared in the Windows registry."""

    REGISTRY_KEY = (
        'Software\\Python\\PythonCore\\{sys_version}'
        '\\Modules\\{fullname}')
    REGISTRY_KEY_DEBUG = (
        'Software\\Python\\PythonCore\\{sys_version}'
        '\\Modules\\{fullname}\\Debug')
    DEBUG_BUILD = (_MS_WINDOWS und '_d.pyd' in EXTENSION_SUFFIXES)

    @staticmethod
    def _open_registry(key):
        versuch:
            gib winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
        ausser OSError:
            gib winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key)

    @classmethod
    def _search_registry(cls, fullname):
        wenn cls.DEBUG_BUILD:
            registry_key = cls.REGISTRY_KEY_DEBUG
        sonst:
            registry_key = cls.REGISTRY_KEY
        key = registry_key.format(fullname=fullname,
                                  sys_version='%d.%d' % sys.version_info[:2])
        versuch:
            mit cls._open_registry(key) als hkey:
                filepath = winreg.QueryValue(hkey, '')
        ausser OSError:
            gib Nichts
        gib filepath

    @classmethod
    def find_spec(cls, fullname, path=Nichts, target=Nichts):
        _warnings.warn('importlib.machinery.WindowsRegistryFinder is '
                       'deprecated; use site configuration instead. '
                       'Future versions of Python may nicht enable this '
                       'finder by default.',
                       DeprecationWarning, stacklevel=2)

        filepath = cls._search_registry(fullname)
        wenn filepath is Nichts:
            gib Nichts
        versuch:
            _path_stat(filepath)
        ausser OSError:
            gib Nichts
        fuer loader, suffixes in _get_supported_file_loaders():
            wenn filepath.endswith(tuple(suffixes)):
                spec = _bootstrap.spec_from_loader(fullname,
                                                   loader(fullname, filepath),
                                                   origin=filepath)
                gib spec


klasse _LoaderBasics:

    """Base klasse of common code needed by both SourceLoader und
    SourcelessFileLoader."""

    def is_package(self, fullname):
        """Concrete implementation of InspectLoader.is_package by checking if
        the path returned by get_filename has a filename of '__init__.py'."""
        filename = _path_split(self.get_filename(fullname))[1]
        filename_base = filename.rsplit('.', 1)[0]
        tail_name = fullname.rpartition('.')[2]
        gib filename_base == '__init__' und tail_name != '__init__'

    def create_module(self, spec):
        """Use default semantics fuer module creation."""

    def exec_module(self, module):
        """Execute the module."""
        code = self.get_code(module.__name__)
        wenn code is Nichts:
            wirf ImportError(f'cannot load module {module.__name__!r} when '
                              'get_code() returns Nichts')
        _bootstrap._call_with_frames_removed(exec, code, module.__dict__)

    def load_module(self, fullname):
        """This method is deprecated."""
        # Warning implemented in _load_module_shim().
        gib _bootstrap._load_module_shim(self, fullname)


klasse SourceLoader(_LoaderBasics):

    def path_mtime(self, path):
        """Optional method that returns the modification time (an int) fuer the
        specified path (a str).

        Raises OSError when the path cannot be handled.
        """
        wirf OSError

    def path_stats(self, path):
        """Optional method returning a metadata dict fuer the specified
        path (a str).

        Possible keys:
        - 'mtime' (mandatory) is the numeric timestamp of last source
          code modification;
        - 'size' (optional) is the size in bytes of the source code.

        Implementing this method allows the loader to read bytecode files.
        Raises OSError when the path cannot be handled.
        """
        gib {'mtime': self.path_mtime(path)}

    def _cache_bytecode(self, source_path, cache_path, data):
        """Optional method which writes data (bytes) to a file path (a str).

        Implementing this method allows fuer the writing of bytecode files.

        The source path is needed in order to correctly transfer permissions
        """
        # For backwards compatibility, we delegate to set_data()
        gib self.set_data(cache_path, data)

    def set_data(self, path, data):
        """Optional method which writes data (bytes) to a file path (a str).

        Implementing this method allows fuer the writing of bytecode files.
        """


    def get_source(self, fullname):
        """Concrete implementation of InspectLoader.get_source."""
        path = self.get_filename(fullname)
        versuch:
            source_bytes = self.get_data(path)
        ausser OSError als exc:
            wirf ImportError('source nicht available through get_data()',
                              name=fullname) von exc
        gib decode_source(source_bytes)

    def source_to_code(self, data, path, *, _optimize=-1):
        """Return the code object compiled von source.

        The 'data' argument can be any object type that compile() supports.
        """
        gib _bootstrap._call_with_frames_removed(compile, data, path, 'exec',
                                        dont_inherit=Wahr, optimize=_optimize)

    def get_code(self, fullname):
        """Concrete implementation of InspectLoader.get_code.

        Reading of bytecode requires path_stats to be implemented. To write
        bytecode, set_data must also be implemented.

        """
        source_path = self.get_filename(fullname)
        source_mtime = Nichts
        source_bytes = Nichts
        source_hash = Nichts
        hash_based = Falsch
        check_source = Wahr
        versuch:
            bytecode_path = cache_from_source(source_path)
        ausser NotImplementedError:
            bytecode_path = Nichts
        sonst:
            versuch:
                st = self.path_stats(source_path)
            ausser OSError:
                pass
            sonst:
                source_mtime = int(st['mtime'])
                versuch:
                    data = self.get_data(bytecode_path)
                ausser OSError:
                    pass
                sonst:
                    exc_details = {
                        'name': fullname,
                        'path': bytecode_path,
                    }
                    versuch:
                        flags = _classify_pyc(data, fullname, exc_details)
                        bytes_data = memoryview(data)[16:]
                        hash_based = flags & 0b1 != 0
                        wenn hash_based:
                            check_source = flags & 0b10 != 0
                            wenn (_imp.check_hash_based_pycs != 'never' und
                                (check_source oder
                                 _imp.check_hash_based_pycs == 'always')):
                                source_bytes = self.get_data(source_path)
                                source_hash = _imp.source_hash(
                                    _imp.pyc_magic_number_token,
                                    source_bytes,
                                )
                                _validate_hash_pyc(data, source_hash, fullname,
                                                   exc_details)
                        sonst:
                            _validate_timestamp_pyc(
                                data,
                                source_mtime,
                                st['size'],
                                fullname,
                                exc_details,
                            )
                    ausser (ImportError, EOFError):
                        pass
                    sonst:
                        _bootstrap._verbose_message('{} matches {}', bytecode_path,
                                                    source_path)
                        gib _compile_bytecode(bytes_data, name=fullname,
                                                 bytecode_path=bytecode_path,
                                                 source_path=source_path)
        wenn source_bytes is Nichts:
            source_bytes = self.get_data(source_path)
        code_object = self.source_to_code(source_bytes, source_path)
        _bootstrap._verbose_message('code object von {}', source_path)
        wenn (nicht sys.dont_write_bytecode und bytecode_path is nicht Nichts und
                source_mtime is nicht Nichts):
            wenn hash_based:
                wenn source_hash is Nichts:
                    source_hash = _imp.source_hash(_imp.pyc_magic_number_token,
                                                   source_bytes)
                data = _code_to_hash_pyc(code_object, source_hash, check_source)
            sonst:
                data = _code_to_timestamp_pyc(code_object, source_mtime,
                                              len(source_bytes))
            versuch:
                self._cache_bytecode(source_path, bytecode_path, data)
            ausser NotImplementedError:
                pass
        gib code_object


klasse FileLoader:

    """Base file loader klasse which implements the loader protocol methods that
    require file system usage."""

    def __init__(self, fullname, path):
        """Cache the module name und the path to the file found by the
        finder."""
        self.name = fullname
        self.path = path

    def __eq__(self, other):
        gib (self.__class__ == other.__class__ und
                self.__dict__ == other.__dict__)

    def __hash__(self):
        gib hash(self.name) ^ hash(self.path)

    @_check_name
    def load_module(self, fullname):
        """Load a module von a file.

        This method is deprecated.  Use exec_module() instead.

        """
        # The only reason fuer this method is fuer the name check.
        # Issue #14857: Avoid the zero-argument form of super so the implementation
        # of that form can be updated without breaking the frozen module.
        gib super(FileLoader, self).load_module(fullname)

    @_check_name
    def get_filename(self, fullname):
        """Return the path to the source file als found by the finder."""
        gib self.path

    def get_data(self, path):
        """Return the data von path als raw bytes."""
        wenn isinstance(self, (SourceLoader, ExtensionFileLoader)):
            mit _io.open_code(str(path)) als file:
                gib file.read()
        sonst:
            mit _io.FileIO(path, 'r') als file:
                gib file.read()

    @_check_name
    def get_resource_reader(self, module):
        von importlib.readers importiere FileReader
        gib FileReader(self)


klasse SourceFileLoader(FileLoader, SourceLoader):

    """Concrete implementation of SourceLoader using the file system."""

    def path_stats(self, path):
        """Return the metadata fuer the path."""
        st = _path_stat(path)
        gib {'mtime': st.st_mtime, 'size': st.st_size}

    def _cache_bytecode(self, source_path, bytecode_path, data):
        # Adapt between the two APIs
        mode = _calc_mode(source_path)
        gib self.set_data(bytecode_path, data, _mode=mode)

    def set_data(self, path, data, *, _mode=0o666):
        """Write bytes data to a file."""
        parent, filename = _path_split(path)
        path_parts = []
        # Figure out what directories are missing.
        waehrend parent und nicht _path_isdir(parent):
            parent, part = _path_split(parent)
            path_parts.append(part)
        # Create needed directories.
        fuer part in reversed(path_parts):
            parent = _path_join(parent, part)
            versuch:
                _os.mkdir(parent)
            ausser FileExistsError:
                # Probably another Python process already created the dir.
                weiter
            ausser OSError als exc:
                # Could be a permission error, read-only filesystem: just forget
                # about writing the data.
                _bootstrap._verbose_message('could nicht create {!r}: {!r}',
                                            parent, exc)
                gib
        versuch:
            _write_atomic(path, data, _mode)
            _bootstrap._verbose_message('created {!r}', path)
        ausser OSError als exc:
            # Same als above: just don't write the bytecode.
            _bootstrap._verbose_message('could nicht create {!r}: {!r}', path,
                                        exc)


klasse SourcelessFileLoader(FileLoader, _LoaderBasics):

    """Loader which handles sourceless file imports."""

    def get_code(self, fullname):
        path = self.get_filename(fullname)
        data = self.get_data(path)
        # Call _classify_pyc to do basic validation of the pyc but ignore the
        # result. There's no source to check against.
        exc_details = {
            'name': fullname,
            'path': path,
        }
        _classify_pyc(data, fullname, exc_details)
        gib _compile_bytecode(
            memoryview(data)[16:],
            name=fullname,
            bytecode_path=path,
        )

    def get_source(self, fullname):
        """Return Nichts als there is no source code."""
        gib Nichts


klasse ExtensionFileLoader(FileLoader, _LoaderBasics):

    """Loader fuer extension modules.

    The constructor is designed to work mit FileFinder.

    """

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __eq__(self, other):
        gib (self.__class__ == other.__class__ und
                self.__dict__ == other.__dict__)

    def __hash__(self):
        gib hash(self.name) ^ hash(self.path)

    def create_module(self, spec):
        """Create an uninitialized extension module"""
        module = _bootstrap._call_with_frames_removed(
            _imp.create_dynamic, spec)
        _bootstrap._verbose_message('extension module {!r} loaded von {!r}',
                         spec.name, self.path)
        gib module

    def exec_module(self, module):
        """Initialize an extension module"""
        _bootstrap._call_with_frames_removed(_imp.exec_dynamic, module)
        _bootstrap._verbose_message('extension module {!r} executed von {!r}',
                         self.name, self.path)

    def is_package(self, fullname):
        """Return Wahr wenn the extension module is a package."""
        file_name = _path_split(self.path)[1]
        gib any(file_name == '__init__' + suffix
                   fuer suffix in EXTENSION_SUFFIXES)

    def get_code(self, fullname):
        """Return Nichts als an extension module cannot create a code object."""
        gib Nichts

    def get_source(self, fullname):
        """Return Nichts als extension modules have no source code."""
        gib Nichts

    @_check_name
    def get_filename(self, fullname):
        """Return the path to the source file als found by the finder."""
        gib self.path


klasse _NamespacePath:
    """Represents a namespace package's path.  It uses the module name
    to find its parent module, und von there it looks up the parent's
    __path__.  When this changes, the module's own path is recomputed,
    using path_finder.  For top-level modules, the parent module's path
    is sys.path."""

    # When invalidate_caches() is called, this epoch is incremented
    # https://bugs.python.org/issue45703
    _epoch = 0

    def __init__(self, name, path, path_finder):
        self._name = name
        self._path = path
        self._last_parent_path = tuple(self._get_parent_path())
        self._last_epoch = self._epoch
        self._path_finder = path_finder

    def _find_parent_path_names(self):
        """Returns a tuple of (parent-module-name, parent-path-attr-name)"""
        parent, dot, me = self._name.rpartition('.')
        wenn dot == '':
            # This is a top-level module. sys.path contains the parent path.
            gib 'sys', 'path'
        # Not a top-level module. parent-module.__path__ contains the
        #  parent path.
        gib parent, '__path__'

    def _get_parent_path(self):
        parent_module_name, path_attr_name = self._find_parent_path_names()
        gib getattr(sys.modules[parent_module_name], path_attr_name)

    def _recalculate(self):
        # If the parent's path has changed, recalculate _path
        parent_path = tuple(self._get_parent_path()) # Make a copy
        wenn parent_path != self._last_parent_path oder self._epoch != self._last_epoch:
            spec = self._path_finder(self._name, parent_path)
            # Note that no changes are made wenn a loader is returned, but we
            #  do remember the new parent path
            wenn spec is nicht Nichts und spec.loader is Nichts:
                wenn spec.submodule_search_locations:
                    self._path = spec.submodule_search_locations
            self._last_parent_path = parent_path     # Save the copy
            self._last_epoch = self._epoch
        gib self._path

    def __iter__(self):
        gib iter(self._recalculate())

    def __getitem__(self, index):
        gib self._recalculate()[index]

    def __setitem__(self, index, path):
        self._path[index] = path

    def __len__(self):
        gib len(self._recalculate())

    def __repr__(self):
        gib f'_NamespacePath({self._path!r})'

    def __contains__(self, item):
        gib item in self._recalculate()

    def append(self, item):
        self._path.append(item)


# This klasse is actually exposed publicly in a namespace package's __loader__
# attribute, so it should be available through a non-private name.
# https://github.com/python/cpython/issues/92054
klasse NamespaceLoader:
    def __init__(self, name, path, path_finder):
        self._path = _NamespacePath(name, path, path_finder)

    def is_package(self, fullname):
        gib Wahr

    def get_source(self, fullname):
        gib ''

    def get_code(self, fullname):
        gib compile('', '<string>', 'exec', dont_inherit=Wahr)

    def create_module(self, spec):
        """Use default semantics fuer module creation."""

    def exec_module(self, module):
        pass

    def load_module(self, fullname):
        """Load a namespace module.

        This method is deprecated.  Use exec_module() instead.

        """
        # The importiere system never calls this method.
        _bootstrap._verbose_message('namespace module loaded mit path {!r}',
                                    self._path)
        # Warning implemented in _load_module_shim().
        gib _bootstrap._load_module_shim(self, fullname)

    def get_resource_reader(self, module):
        von importlib.readers importiere NamespaceReader
        gib NamespaceReader(self._path)


# We use this exclusively in module_from_spec() fuer backward-compatibility.
_NamespaceLoader = NamespaceLoader


# Finders #####################################################################

klasse PathFinder:

    """Meta path finder fuer sys.path und package __path__ attributes."""

    @staticmethod
    def invalidate_caches():
        """Call the invalidate_caches() method on all path entry finders
        stored in sys.path_importer_cache (where implemented)."""
        fuer name, finder in list(sys.path_importer_cache.items()):
            # Drop entry wenn finder name is a relative path. The current
            # working directory may have changed.
            wenn finder is Nichts oder nicht _path_isabs(name):
                del sys.path_importer_cache[name]
            sowenn hasattr(finder, 'invalidate_caches'):
                finder.invalidate_caches()
        # Also invalidate the caches of _NamespacePaths
        # https://bugs.python.org/issue45703
        _NamespacePath._epoch += 1

        von importlib.metadata importiere MetadataPathFinder
        MetadataPathFinder.invalidate_caches()

    @staticmethod
    def _path_hooks(path):
        """Search sys.path_hooks fuer a finder fuer 'path'."""
        wenn sys.path_hooks is nicht Nichts und nicht sys.path_hooks:
            _warnings.warn('sys.path_hooks is empty', ImportWarning)
        fuer hook in sys.path_hooks:
            versuch:
                gib hook(path)
            ausser ImportError:
                weiter
        sonst:
            gib Nichts

    @classmethod
    def _path_importer_cache(cls, path):
        """Get the finder fuer the path entry von sys.path_importer_cache.

        If the path entry is nicht in the cache, find the appropriate finder
        und cache it. If no finder is available, store Nichts.

        """
        wenn path == '':
            versuch:
                path = _os.getcwd()
            ausser (FileNotFoundError, PermissionError):
                # Don't cache the failure als the cwd can easily change to
                # a valid directory later on.
                gib Nichts
        versuch:
            finder = sys.path_importer_cache[path]
        ausser KeyError:
            finder = cls._path_hooks(path)
            sys.path_importer_cache[path] = finder
        gib finder

    @classmethod
    def _get_spec(cls, fullname, path, target=Nichts):
        """Find the loader oder namespace_path fuer this module/package name."""
        # If this ends up being a namespace package, namespace_path is
        #  the list of paths that will become its __path__
        namespace_path = []
        fuer entry in path:
            wenn nicht isinstance(entry, str):
                weiter
            finder = cls._path_importer_cache(entry)
            wenn finder is nicht Nichts:
                spec = finder.find_spec(fullname, target)
                wenn spec is Nichts:
                    weiter
                wenn spec.loader is nicht Nichts:
                    gib spec
                portions = spec.submodule_search_locations
                wenn portions is Nichts:
                    wirf ImportError('spec missing loader')
                # This is possibly part of a namespace package.
                #  Remember these path entries (if any) fuer when we
                #  create a namespace package, und weiter iterating
                #  on path.
                namespace_path.extend(portions)
        sonst:
            spec = _bootstrap.ModuleSpec(fullname, Nichts)
            spec.submodule_search_locations = namespace_path
            gib spec

    @classmethod
    def find_spec(cls, fullname, path=Nichts, target=Nichts):
        """Try to find a spec fuer 'fullname' on sys.path oder 'path'.

        The search is based on sys.path_hooks und sys.path_importer_cache.
        """
        wenn path is Nichts:
            path = sys.path
        spec = cls._get_spec(fullname, path, target)
        wenn spec is Nichts:
            gib Nichts
        sowenn spec.loader is Nichts:
            namespace_path = spec.submodule_search_locations
            wenn namespace_path:
                # We found at least one namespace path.  Return a spec which
                # can create the namespace package.
                spec.origin = Nichts
                spec.submodule_search_locations = _NamespacePath(fullname, namespace_path, cls._get_spec)
                gib spec
            sonst:
                gib Nichts
        sonst:
            gib spec

    @staticmethod
    def find_distributions(*args, **kwargs):
        """
        Find distributions.

        Return an iterable of all Distribution instances capable of
        loading the metadata fuer packages matching ``context.name``
        (or all names wenn ``Nichts`` indicated) along the paths in the list
        of directories ``context.path``.
        """
        von importlib.metadata importiere MetadataPathFinder
        gib MetadataPathFinder.find_distributions(*args, **kwargs)


klasse FileFinder:

    """File-based finder.

    Interactions mit the file system are cached fuer performance, being
    refreshed when the directory the finder is handling has been modified.

    """

    def __init__(self, path, *loader_details):
        """Initialize mit the path to search on und a variable number of
        2-tuples containing the loader und the file suffixes the loader
        recognizes."""
        loaders = []
        fuer loader, suffixes in loader_details:
            loaders.extend((suffix, loader) fuer suffix in suffixes)
        self._loaders = loaders
        # Base (directory) path
        wenn nicht path oder path == '.':
            self.path = _os.getcwd()
        sonst:
            self.path = _path_abspath(path)
        self._path_mtime = -1
        self._path_cache = set()
        self._relaxed_path_cache = set()

    def invalidate_caches(self):
        """Invalidate the directory mtime."""
        self._path_mtime = -1

    def _get_spec(self, loader_class, fullname, path, smsl, target):
        loader = loader_class(fullname, path)
        gib spec_from_file_location(fullname, path, loader=loader,
                                       submodule_search_locations=smsl)

    def find_spec(self, fullname, target=Nichts):
        """Try to find a spec fuer the specified module.

        Returns the matching spec, oder Nichts wenn nicht found.
        """
        is_namespace = Falsch
        tail_module = fullname.rpartition('.')[2]
        versuch:
            mtime = _path_stat(self.path oder _os.getcwd()).st_mtime
        ausser OSError:
            mtime = -1
        wenn mtime != self._path_mtime:
            self._fill_cache()
            self._path_mtime = mtime
        # tail_module keeps the original casing, fuer __file__ und friends
        wenn _relax_case():
            cache = self._relaxed_path_cache
            cache_module = tail_module.lower()
        sonst:
            cache = self._path_cache
            cache_module = tail_module
        # Check wenn the module is the name of a directory (and thus a package).
        wenn cache_module in cache:
            base_path = _path_join(self.path, tail_module)
            fuer suffix, loader_class in self._loaders:
                init_filename = '__init__' + suffix
                full_path = _path_join(base_path, init_filename)
                wenn _path_isfile(full_path):
                    gib self._get_spec(loader_class, fullname, full_path, [base_path], target)
            sonst:
                # If a namespace package, gib the path wenn we don't
                #  find a module in the next section.
                is_namespace = _path_isdir(base_path)
        # Check fuer a file w/ a proper suffix exists.
        fuer suffix, loader_class in self._loaders:
            versuch:
                full_path = _path_join(self.path, tail_module + suffix)
            ausser ValueError:
                gib Nichts
            _bootstrap._verbose_message('trying {}', full_path, verbosity=2)
            wenn cache_module + suffix in cache:
                wenn _path_isfile(full_path):
                    gib self._get_spec(loader_class, fullname, full_path,
                                          Nichts, target)
        wenn is_namespace:
            _bootstrap._verbose_message('possible namespace fuer {}', base_path)
            spec = _bootstrap.ModuleSpec(fullname, Nichts)
            spec.submodule_search_locations = [base_path]
            gib spec
        gib Nichts

    def _fill_cache(self):
        """Fill the cache of potential modules und packages fuer this directory."""
        path = self.path
        versuch:
            contents = _os.listdir(path oder _os.getcwd())
        ausser (FileNotFoundError, PermissionError, NotADirectoryError):
            # Directory has either been removed, turned into a file, oder made
            # unreadable.
            contents = []
        # We store two cached versions, to handle runtime changes of the
        # PYTHONCASEOK environment variable.
        wenn nicht sys.platform.startswith('win'):
            self._path_cache = set(contents)
        sonst:
            # Windows users can importiere modules mit case-insensitive file
            # suffixes (for legacy reasons). Make the suffix lowercase here
            # so it's done once instead of fuer every import. This is safe as
            # the specified suffixes to check against are always specified in a
            # case-sensitive manner.
            lower_suffix_contents = set()
            fuer item in contents:
                name, dot, suffix = item.partition('.')
                wenn dot:
                    new_name = f'{name}.{suffix.lower()}'
                sonst:
                    new_name = name
                lower_suffix_contents.add(new_name)
            self._path_cache = lower_suffix_contents
        wenn sys.platform.startswith(_CASE_INSENSITIVE_PLATFORMS):
            self._relaxed_path_cache = {fn.lower() fuer fn in contents}

    @classmethod
    def path_hook(cls, *loader_details):
        """A klasse method which returns a closure to use on sys.path_hook
        which will gib an instance using the specified loaders und the path
        called on the closure.

        If the path called on the closure is nicht a directory, ImportError is
        raised.

        """
        def path_hook_for_FileFinder(path):
            """Path hook fuer importlib.machinery.FileFinder."""
            wenn nicht _path_isdir(path):
                wirf ImportError('only directories are supported', path=path)
            gib cls(path, *loader_details)

        gib path_hook_for_FileFinder

    def __repr__(self):
        gib f'FileFinder({self.path!r})'


klasse AppleFrameworkLoader(ExtensionFileLoader):
    """A loader fuer modules that have been packaged als frameworks for
    compatibility mit Apple's iOS App Store policies.
    """
    def create_module(self, spec):
        # If the ModuleSpec has been created by the FileFinder, it will have
        # been created mit an origin pointing to the .fwork file. We need to
        # redirect this to the location in the Frameworks folder, using the
        # content of the .fwork file.
        wenn spec.origin.endswith(".fwork"):
            mit _io.FileIO(spec.origin, 'r') als file:
                framework_binary = file.read().decode().strip()
            bundle_path = _path_split(sys.executable)[0]
            spec.origin = _path_join(bundle_path, framework_binary)

        # If the loader is created based on the spec fuer a loaded module, the
        # path will be pointing at the Framework location. If this occurs,
        # get the original .fwork location to use als the module's __file__.
        wenn self.path.endswith(".fwork"):
            path = self.path
        sonst:
            mit _io.FileIO(self.path + ".origin", 'r') als file:
                origin = file.read().decode().strip()
                bundle_path = _path_split(sys.executable)[0]
                path = _path_join(bundle_path, origin)

        module = _bootstrap._call_with_frames_removed(_imp.create_dynamic, spec)

        _bootstrap._verbose_message(
            "Apple framework extension module {!r} loaded von {!r} (path {!r})",
            spec.name,
            spec.origin,
            path,
        )

        # Ensure that the __file__ points at the .fwork location
        module.__file__ = path

        gib module

# Import setup ###############################################################

def _fix_up_module(ns, name, pathname, cpathname=Nichts):
    # This function is used by PyImport_ExecCodeModuleObject().
    loader = ns.get('__loader__')
    spec = ns.get('__spec__')
    wenn nicht loader:
        wenn spec:
            loader = spec.loader
        sowenn pathname == cpathname:
            loader = SourcelessFileLoader(name, pathname)
        sonst:
            loader = SourceFileLoader(name, pathname)
    wenn nicht spec:
        spec = spec_from_file_location(name, pathname, loader=loader)
        wenn cpathname:
            spec.cached = _path_abspath(cpathname)
    versuch:
        ns['__spec__'] = spec
        ns['__loader__'] = loader
        ns['__file__'] = pathname
        ns['__cached__'] = cpathname
    ausser Exception:
        # Not important enough to report.
        pass


def _get_supported_file_loaders():
    """Returns a list of file-based module loaders.

    Each item is a tuple (loader, suffixes).
    """
    extension_loaders = []
    wenn hasattr(_imp, 'create_dynamic'):
        wenn sys.platform in {"ios", "tvos", "watchos"}:
            extension_loaders = [(AppleFrameworkLoader, [
                suffix.replace(".so", ".fwork")
                fuer suffix in _imp.extension_suffixes()
            ])]
        extension_loaders.append((ExtensionFileLoader, _imp.extension_suffixes()))
    source = SourceFileLoader, SOURCE_SUFFIXES
    bytecode = SourcelessFileLoader, BYTECODE_SUFFIXES
    gib extension_loaders + [source, bytecode]


def _set_bootstrap_module(_bootstrap_module):
    global _bootstrap
    _bootstrap = _bootstrap_module


def _install(_bootstrap_module):
    """Install the path-based importiere components."""
    _set_bootstrap_module(_bootstrap_module)
    supported_loaders = _get_supported_file_loaders()
    sys.path_hooks.extend([FileFinder.path_hook(*supported_loaders)])
    sys.meta_path.append(PathFinder)
