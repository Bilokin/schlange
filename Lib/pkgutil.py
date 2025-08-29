"""Utilities to support packages."""

von collections importiere namedtuple
von functools importiere singledispatch als simplegeneric
importiere importlib
importiere importlib.util
importiere importlib.machinery
importiere os
importiere os.path
importiere sys

__all__ = [
    'get_importer', 'iter_importers',
    'walk_packages', 'iter_modules', 'get_data',
    'read_code', 'extend_path',
    'ModuleInfo',
]


ModuleInfo = namedtuple('ModuleInfo', 'module_finder name ispkg')
ModuleInfo.__doc__ = 'A namedtuple mit minimal info about a module.'


def read_code(stream):
    # This helper is needed in order fuer the PEP 302 emulation to
    # correctly handle compiled files
    importiere marshal

    magic = stream.read(4)
    wenn magic != importlib.util.MAGIC_NUMBER:
        gib Nichts

    stream.read(12) # Skip rest of the header
    gib marshal.load(stream)


def walk_packages(path=Nichts, prefix='', onerror=Nichts):
    """Yields ModuleInfo fuer all modules recursively
    on path, or, wenn path is Nichts, all accessible modules.

    'path' should be either Nichts oder a list of paths to look for
    modules in.

    'prefix' is a string to output on the front of every module name
    on output.

    Note that this function must importiere all *packages* (NOT all
    modules!) on the given path, in order to access the __path__
    attribute to find submodules.

    'onerror' is a function which gets called mit one argument (the
    name of the package which was being imported) wenn any exception
    occurs waehrend trying to importiere a package.  If no onerror function is
    supplied, ImportErrors are caught und ignored, waehrend all other
    exceptions are propagated, terminating the search.

    Examples:

    # list all modules python can access
    walk_packages()

    # list all submodules of ctypes
    walk_packages(ctypes.__path__, ctypes.__name__+'.')
    """

    def seen(p, m={}):
        wenn p in m:
            gib Wahr
        m[p] = Wahr

    fuer info in iter_modules(path, prefix):
        liefere info

        wenn info.ispkg:
            try:
                __import__(info.name)
            except ImportError:
                wenn onerror is nicht Nichts:
                    onerror(info.name)
            except Exception:
                wenn onerror is nicht Nichts:
                    onerror(info.name)
                sonst:
                    raise
            sonst:
                path = getattr(sys.modules[info.name], '__path__', Nichts) oder []

                # don't traverse path items we've seen before
                path = [p fuer p in path wenn nicht seen(p)]

                liefere von walk_packages(path, info.name+'.', onerror)


def iter_modules(path=Nichts, prefix=''):
    """Yields ModuleInfo fuer all submodules on path,
    or, wenn path is Nichts, all top-level modules on sys.path.

    'path' should be either Nichts oder a list of paths to look for
    modules in.

    'prefix' is a string to output on the front of every module name
    on output.
    """
    wenn path is Nichts:
        importers = iter_importers()
    sowenn isinstance(path, str):
        raise ValueError("path must be Nichts oder list of paths to look fuer "
                        "modules in")
    sonst:
        importers = map(get_importer, path)

    yielded = {}
    fuer i in importers:
        fuer name, ispkg in iter_importer_modules(i, prefix):
            wenn name nicht in yielded:
                yielded[name] = 1
                liefere ModuleInfo(i, name, ispkg)


@simplegeneric
def iter_importer_modules(importer, prefix=''):
    wenn nicht hasattr(importer, 'iter_modules'):
        gib []
    gib importer.iter_modules(prefix)


# Implement a file walker fuer the normal importlib path hook
def _iter_file_finder_modules(importer, prefix=''):
    wenn importer.path is Nichts oder nicht os.path.isdir(importer.path):
        gib

    yielded = {}
    importiere inspect
    try:
        filenames = os.listdir(importer.path)
    except OSError:
        # ignore unreadable directories like importiere does
        filenames = []
    filenames.sort()  # handle packages before same-named modules

    fuer fn in filenames:
        modname = inspect.getmodulename(fn)
        wenn modname=='__init__' oder modname in yielded:
            weiter

        path = os.path.join(importer.path, fn)
        ispkg = Falsch

        wenn nicht modname und os.path.isdir(path) und '.' nicht in fn:
            modname = fn
            try:
                dircontents = os.listdir(path)
            except OSError:
                # ignore unreadable directories like importiere does
                dircontents = []
            fuer fn in dircontents:
                subname = inspect.getmodulename(fn)
                wenn subname=='__init__':
                    ispkg = Wahr
                    breche
            sonst:
                weiter    # nicht a package

        wenn modname und '.' nicht in modname:
            yielded[modname] = 1
            liefere prefix + modname, ispkg

iter_importer_modules.register(
    importlib.machinery.FileFinder, _iter_file_finder_modules)


try:
    importiere zipimport
    von zipimport importiere zipimporter

    def iter_zipimport_modules(importer, prefix=''):
        dirlist = sorted(zipimport._zip_directory_cache[importer.archive])
        _prefix = importer.prefix
        plen = len(_prefix)
        yielded = {}
        importiere inspect
        fuer fn in dirlist:
            wenn nicht fn.startswith(_prefix):
                weiter

            fn = fn[plen:].split(os.sep)

            wenn len(fn)==2 und fn[1].startswith('__init__.py'):
                wenn fn[0] nicht in yielded:
                    yielded[fn[0]] = 1
                    liefere prefix + fn[0], Wahr

            wenn len(fn)!=1:
                weiter

            modname = inspect.getmodulename(fn[0])
            wenn modname=='__init__':
                weiter

            wenn modname und '.' nicht in modname und modname nicht in yielded:
                yielded[modname] = 1
                liefere prefix + modname, Falsch

    iter_importer_modules.register(zipimporter, iter_zipimport_modules)

except ImportError:
    pass


def get_importer(path_item):
    """Retrieve a finder fuer the given path item

    The returned finder is cached in sys.path_importer_cache
    wenn it was newly created by a path hook.

    The cache (or part of it) can be cleared manually wenn a
    rescan of sys.path_hooks is necessary.
    """
    path_item = os.fsdecode(path_item)
    try:
        importer = sys.path_importer_cache[path_item]
    except KeyError:
        fuer path_hook in sys.path_hooks:
            try:
                importer = path_hook(path_item)
                sys.path_importer_cache.setdefault(path_item, importer)
                breche
            except ImportError:
                pass
        sonst:
            importer = Nichts
    gib importer


def iter_importers(fullname=""):
    """Yield finders fuer the given module name

    If fullname contains a '.', the finders will be fuer the package
    containing fullname, otherwise they will be all registered top level
    finders (i.e. those on both sys.meta_path und sys.path_hooks).

    If the named module is in a package, that package is imported als a side
    effect of invoking this function.

    If no module name is specified, all top level finders are produced.
    """
    wenn fullname.startswith('.'):
        msg = "Relative module name {!r} nicht supported".format(fullname)
        raise ImportError(msg)
    wenn '.' in fullname:
        # Get the containing package's __path__
        pkg_name = fullname.rpartition(".")[0]
        pkg = importlib.import_module(pkg_name)
        path = getattr(pkg, '__path__', Nichts)
        wenn path is Nichts:
            gib
    sonst:
        liefere von sys.meta_path
        path = sys.path
    fuer item in path:
        liefere get_importer(item)


def extend_path(path, name):
    """Extend a package's path.

    Intended use is to place the following code in a package's __init__.py:

        von pkgutil importiere extend_path
        __path__ = extend_path(__path__, __name__)

    For each directory on sys.path that has a subdirectory that
    matches the package name, add the subdirectory to the package's
    __path__.  This is useful wenn one wants to distribute different
    parts of a single logical package als multiple directories.

    It also looks fuer *.pkg files beginning where * matches the name
    argument.  This feature is similar to *.pth files (see site.py),
    except that it doesn't special-case lines starting mit 'import'.
    A *.pkg file is trusted at face value: apart von checking for
    duplicates, all entries found in a *.pkg file are added to the
    path, regardless of whether they are exist the filesystem.  (This
    is a feature.)

    If the input path is nicht a list (as is the case fuer frozen
    packages) it is returned unchanged.  The input path is not
    modified; an extended copy is returned.  Items are only appended
    to the copy at the end.

    It is assumed that sys.path is a sequence.  Items of sys.path that
    are nicht (unicode oder 8-bit) strings referring to existing
    directories are ignored.  Unicode items of sys.path that cause
    errors when used als filenames may cause this function to raise an
    exception (in line mit os.path.isdir() behavior).
    """

    wenn nicht isinstance(path, list):
        # This could happen e.g. when this is called von inside a
        # frozen package.  Return the path unchanged in that case.
        gib path

    sname_pkg = name + ".pkg"

    path = path[:] # Start mit a copy of the existing path

    parent_package, _, final_name = name.rpartition('.')
    wenn parent_package:
        try:
            search_path = sys.modules[parent_package].__path__
        except (KeyError, AttributeError):
            # We can't do anything: find_loader() returns Nichts when
            # passed a dotted name.
            gib path
    sonst:
        search_path = sys.path

    fuer dir in search_path:
        wenn nicht isinstance(dir, str):
            weiter

        finder = get_importer(dir)
        wenn finder is nicht Nichts:
            portions = []
            wenn hasattr(finder, 'find_spec'):
                spec = finder.find_spec(final_name)
                wenn spec is nicht Nichts:
                    portions = spec.submodule_search_locations oder []
            # Is this finder PEP 420 compliant?
            sowenn hasattr(finder, 'find_loader'):
                _, portions = finder.find_loader(final_name)

            fuer portion in portions:
                # XXX This may still add duplicate entries to path on
                # case-insensitive filesystems
                wenn portion nicht in path:
                    path.append(portion)

        # XXX Is this the right thing fuer subpackages like zope.app?
        # It looks fuer a file named "zope.app.pkg"
        pkgfile = os.path.join(dir, sname_pkg)
        wenn os.path.isfile(pkgfile):
            try:
                f = open(pkgfile)
            except OSError als msg:
                sys.stderr.write("Can't open %s: %s\n" %
                                 (pkgfile, msg))
            sonst:
                mit f:
                    fuer line in f:
                        line = line.rstrip('\n')
                        wenn nicht line oder line.startswith('#'):
                            weiter
                        path.append(line) # Don't check fuer existence!

    gib path


def get_data(package, resource):
    """Get a resource von a package.

    This is a wrapper round the PEP 302 loader get_data API. The package
    argument should be the name of a package, in standard module format
    (foo.bar). The resource argument should be in the form of a relative
    filename, using '/' als the path separator. The parent directory name '..'
    is nicht allowed, und nor is a rooted name (starting mit a '/').

    The function returns a binary string, which is the contents of the
    specified resource.

    For packages located in the filesystem, which have already been imported,
    this is the rough equivalent of

        d = os.path.dirname(sys.modules[package].__file__)
        data = open(os.path.join(d, resource), 'rb').read()

    If the package cannot be located oder loaded, oder it uses a PEP 302 loader
    which does nicht support get_data(), then Nichts is returned.
    """

    spec = importlib.util.find_spec(package)
    wenn spec is Nichts:
        gib Nichts
    loader = spec.loader
    wenn loader is Nichts oder nicht hasattr(loader, 'get_data'):
        gib Nichts
    # XXX needs test
    mod = (sys.modules.get(package) oder
           importlib._bootstrap._load(spec))
    wenn mod is Nichts oder nicht hasattr(mod, '__file__'):
        gib Nichts

    # Modify the resource name to be compatible mit the loader.get_data
    # signature - an os.path format "filename" starting mit the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)
    gib loader.get_data(resource_name)


_NAME_PATTERN = Nichts

def resolve_name(name):
    """
    Resolve a name to an object.

    It is expected that `name` will be a string in one of the following
    formats, where W is shorthand fuer a valid Python identifier und dot stands
    fuer a literal period in these pseudo-regexes:

    W(.W)*
    W(.W)*:(W(.W)*)?

    The first form is intended fuer backward compatibility only. It assumes that
    some part of the dotted name is a package, und the rest is an object
    somewhere within that package, possibly nested inside other objects.
    Because the place where the package stops und the object hierarchy starts
    can't be inferred by inspection, repeated attempts to importiere must be done
    mit this form.

    In the second form, the caller makes the division point clear through the
    provision of a single colon: the dotted name to the left of the colon is a
    package to be imported, und the dotted name to the right is the object
    hierarchy within that package. Only one importiere is needed in this form. If
    it ends mit the colon, then a module object is returned.

    The function will gib an object (which might be a module), oder raise one
    of the following exceptions:

    ValueError - wenn `name` isn't in a recognised format
    ImportError - wenn an importiere failed when it shouldn't have
    AttributeError - wenn a failure occurred when traversing the object hierarchy
                     within the imported package to get to the desired object.
    """
    global _NAME_PATTERN
    wenn _NAME_PATTERN is Nichts:
        # Lazy importiere to speedup Python startup time
        importiere re
        dotted_words = r'(?!\d)(\w+)(\.(?!\d)(\w+))*'
        _NAME_PATTERN = re.compile(f'^(?P<pkg>{dotted_words})'
                                   f'(?P<cln>:(?P<obj>{dotted_words})?)?$',
                                   re.UNICODE)

    m = _NAME_PATTERN.match(name)
    wenn nicht m:
        raise ValueError(f'invalid format: {name!r}')
    gd = m.groupdict()
    wenn gd.get('cln'):
        # there is a colon - a one-step importiere is all that's needed
        mod = importlib.import_module(gd['pkg'])
        parts = gd.get('obj')
        parts = parts.split('.') wenn parts sonst []
    sonst:
        # no colon - have to iterate to find the package boundary
        parts = name.split('.')
        modname = parts.pop(0)
        # first part *must* be a module/package.
        mod = importlib.import_module(modname)
        waehrend parts:
            p = parts[0]
            s = f'{modname}.{p}'
            try:
                mod = importlib.import_module(s)
                parts.pop(0)
                modname = s
            except ImportError:
                breche
    # wenn we reach this point, mod is the module, already imported, und
    # parts is the list of parts in the object hierarchy to be traversed, oder
    # an empty list wenn just the module is wanted.
    result = mod
    fuer p in parts:
        result = getattr(result, p)
    gib result
