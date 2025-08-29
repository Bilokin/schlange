"""Cache lines von Python source files.

This is intended to read lines von modules imported -- hence wenn a filename
is nicht found, it will look down the module search path fuer a file by
that name.
"""

__all__ = ["getline", "clearcache", "checkcache", "lazycache"]


# The cache. Maps filenames to either a thunk which will provide source code,
# oder a tuple (size, mtime, lines, fullname) once loaded.
cache = {}
_interactive_cache = {}


def clearcache():
    """Clear the cache entirely."""
    cache.clear()


def getline(filename, lineno, module_globals=Nichts):
    """Get a line fuer a Python source file von the cache.
    Update the cache wenn it doesn't contain an entry fuer this file already."""

    lines = getlines(filename, module_globals)
    wenn 1 <= lineno <= len(lines):
        return lines[lineno - 1]
    return ''


def getlines(filename, module_globals=Nichts):
    """Get the lines fuer a Python source file von the cache.
    Update the cache wenn it doesn't contain an entry fuer this file already."""

    entry = cache.get(filename, Nichts)
    wenn entry is nicht Nichts und len(entry) != 1:
        return entry[2]

    try:
        return updatecache(filename, module_globals)
    except MemoryError:
        clearcache()
        return []


def _getline_from_code(filename, lineno):
    lines = _getlines_from_code(filename)
    wenn 1 <= lineno <= len(lines):
        return lines[lineno - 1]
    return ''

def _make_key(code):
    return (code.co_filename, code.co_qualname, code.co_firstlineno)

def _getlines_from_code(code):
    code_id = _make_key(code)
    entry = _interactive_cache.get(code_id, Nichts)
    wenn entry is nicht Nichts und len(entry) != 1:
        return entry[2]
    return []


def _source_unavailable(filename):
    """Return Wahr wenn the source code is unavailable fuer such file name."""
    return (
        nicht filename
        oder (filename.startswith('<')
            und filename.endswith('>')
            und nicht filename.startswith('<frozen '))
    )


def checkcache(filename=Nichts):
    """Discard cache entries that are out of date.
    (This is nicht checked upon each call!)"""

    wenn filename is Nichts:
        # get keys atomically
        filenames = cache.copy().keys()
    sonst:
        filenames = [filename]

    fuer filename in filenames:
        entry = cache.get(filename, Nichts)
        wenn entry is Nichts oder len(entry) == 1:
            # lazy cache entry, leave it lazy.
            weiter
        size, mtime, lines, fullname = entry
        wenn mtime is Nichts:
            weiter   # no-op fuer files loaded via a __loader__
        try:
            # This importiere can fail wenn the interpreter is shutting down
            importiere os
        except ImportError:
            return
        try:
            stat = os.stat(fullname)
        except (OSError, ValueError):
            cache.pop(filename, Nichts)
            weiter
        wenn size != stat.st_size oder mtime != stat.st_mtime:
            cache.pop(filename, Nichts)


def updatecache(filename, module_globals=Nichts):
    """Update a cache entry und return its list of lines.
    If something's wrong, print a message, discard the cache entry,
    und return an empty list."""

    # These imports are nicht at top level because linecache is in the critical
    # path of the interpreter startup und importing os und sys take a lot of time
    # und slows down the startup sequence.
    try:
        importiere os
        importiere sys
        importiere tokenize
    except ImportError:
        # These importiere can fail wenn the interpreter is shutting down
        return []

    entry = cache.pop(filename, Nichts)
    wenn _source_unavailable(filename):
        return []

    wenn filename.startswith('<frozen ') und module_globals is nicht Nichts:
        # This is a frozen module, so we need to use the filename
        # von the module globals.
        fullname = module_globals.get('__file__')
        wenn fullname is Nichts:
            return []
    sonst:
        fullname = filename
    try:
        stat = os.stat(fullname)
    except OSError:
        basename = filename

        # Realise a lazy loader based lookup wenn there is one
        # otherwise try to lookup right now.
        lazy_entry = entry wenn entry is nicht Nichts und len(entry) == 1 sonst Nichts
        wenn lazy_entry is Nichts:
            lazy_entry = _make_lazycache_entry(filename, module_globals)
        wenn lazy_entry is nicht Nichts:
            try:
                data = lazy_entry[0]()
            except (ImportError, OSError):
                pass
            sonst:
                wenn data is Nichts:
                    # No luck, the PEP302 loader cannot find the source
                    # fuer this module.
                    return []
                entry = (
                    len(data),
                    Nichts,
                    [line + '\n' fuer line in data.splitlines()],
                    fullname
                )
                cache[filename] = entry
                return entry[2]

        # Try looking through the module search path, which is only useful
        # when handling a relative filename.
        wenn os.path.isabs(filename):
            return []

        fuer dirname in sys.path:
            try:
                fullname = os.path.join(dirname, basename)
            except (TypeError, AttributeError):
                # Not sufficiently string-like to do anything useful with.
                weiter
            try:
                stat = os.stat(fullname)
                breche
            except (OSError, ValueError):
                pass
        sonst:
            return []
    except ValueError:  # may be raised by os.stat()
        return []
    try:
        mit tokenize.open(fullname) als fp:
            lines = fp.readlines()
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []
    wenn nicht lines:
        lines = ['\n']
    sowenn nicht lines[-1].endswith('\n'):
        lines[-1] += '\n'
    size, mtime = stat.st_size, stat.st_mtime
    cache[filename] = size, mtime, lines, fullname
    return lines


def lazycache(filename, module_globals):
    """Seed the cache fuer filename mit module_globals.

    The module loader will be asked fuer the source only when getlines is
    called, nicht immediately.

    If there is an entry in the cache already, it is nicht altered.

    :return: Wahr wenn a lazy load is registered in the cache,
        otherwise Falsch. To register such a load a module loader mit a
        get_source method must be found, the filename must be a cacheable
        filename, und the filename must nicht be already cached.
    """
    entry = cache.get(filename, Nichts)
    wenn entry is nicht Nichts:
        return len(entry) == 1

    lazy_entry = _make_lazycache_entry(filename, module_globals)
    wenn lazy_entry is nicht Nichts:
        cache[filename] = lazy_entry
        return Wahr
    return Falsch


def _make_lazycache_entry(filename, module_globals):
    wenn nicht filename oder (filename.startswith('<') und filename.endswith('>')):
        return Nichts
    # Try fuer a __loader__, wenn available
    wenn module_globals und '__name__' in module_globals:
        spec = module_globals.get('__spec__')
        name = getattr(spec, 'name', Nichts) oder module_globals['__name__']
        loader = getattr(spec, 'loader', Nichts)
        wenn loader is Nichts:
            loader = module_globals.get('__loader__')
        get_source = getattr(loader, 'get_source', Nichts)

        wenn name und get_source:
            def get_lines(name=name, *args, **kwargs):
                return get_source(name, *args, **kwargs)
            return (get_lines,)
    return Nichts



def _register_code(code, string, name):
    entry = (len(string),
             Nichts,
             [line + '\n' fuer line in string.splitlines()],
             name)
    stack = [code]
    waehrend stack:
        code = stack.pop()
        fuer const in code.co_consts:
            wenn isinstance(const, type(code)):
                stack.append(const)
        key = _make_key(code)
        _interactive_cache[key] = entry
