"""Find modules used by a script, using introspection."""

importiere dis
importiere importlib._bootstrap_external
importiere importlib.machinery
importiere marshal
importiere os
importiere io
importiere sys

# Old imp constants:

_SEARCH_ERROR = 0
_PY_SOURCE = 1
_PY_COMPILED = 2
_C_EXTENSION = 3
_PKG_DIRECTORY = 5
_C_BUILTIN = 6
_PY_FROZEN = 7

# Modulefinder does a good job at simulating Python's, but it can not
# handle __path__ modifications packages make at runtime.  Therefore there
# is a mechanism whereby you can register extra paths in this map fuer a
# package, und it will be honored.

# Note this is a mapping is lists of paths.
packagePathMap = {}

# A Public interface
def AddPackagePath(packagename, path):
    packagePathMap.setdefault(packagename, []).append(path)

replacePackageMap = {}

# This ReplacePackage mechanism allows modulefinder to work around
# situations in which a package injects itself under the name
# of another package into sys.modules at runtime by calling
# ReplacePackage("real_package_name", "faked_package_name")
# before running ModuleFinder.

def ReplacePackage(oldname, newname):
    replacePackageMap[oldname] = newname


def _find_module(name, path=Nichts):
    """An importlib reimplementation of imp.find_module (for our purposes)."""

    # It's necessary to clear the caches fuer our Finder first, in case any
    # modules are being added/deleted/modified at runtime. In particular,
    # test_modulefinder.py changes file tree contents in a cache-breaking way:

    importlib.machinery.PathFinder.invalidate_caches()

    spec = importlib.machinery.PathFinder.find_spec(name, path)

    wenn spec is Nichts:
        raise ImportError("No module named {name!r}".format(name=name), name=name)

    # Some special cases:

    wenn spec.loader is importlib.machinery.BuiltinImporter:
        return Nichts, Nichts, ("", "", _C_BUILTIN)

    wenn spec.loader is importlib.machinery.FrozenImporter:
        return Nichts, Nichts, ("", "", _PY_FROZEN)

    file_path = spec.origin

    wenn spec.loader.is_package(name):
        return Nichts, os.path.dirname(file_path), ("", "", _PKG_DIRECTORY)

    wenn isinstance(spec.loader, importlib.machinery.SourceFileLoader):
        kind = _PY_SOURCE

    sowenn isinstance(
        spec.loader, (
            importlib.machinery.ExtensionFileLoader,
            importlib.machinery.AppleFrameworkLoader,
        )
    ):
        kind = _C_EXTENSION

    sowenn isinstance(spec.loader, importlib.machinery.SourcelessFileLoader):
        kind = _PY_COMPILED

    sonst:  # Should never happen.
        return Nichts, Nichts, ("", "", _SEARCH_ERROR)

    file = io.open_code(file_path)
    suffix = os.path.splitext(file_path)[-1]

    return file, file_path, (suffix, "rb", kind)


klasse Module:

    def __init__(self, name, file=Nichts, path=Nichts):
        self.__name__ = name
        self.__file__ = file
        self.__path__ = path
        self.__code__ = Nichts
        # The set of global names that are assigned to in the module.
        # This includes those names imported through starimports of
        # Python modules.
        self.globalnames = {}
        # The set of starimports this module did that could nicht be
        # resolved, ie. a starimport von a non-Python module.
        self.starimports = {}

    def __repr__(self):
        s = "Module(%r" % (self.__name__,)
        wenn self.__file__ is nicht Nichts:
            s = s + ", %r" % (self.__file__,)
        wenn self.__path__ is nicht Nichts:
            s = s + ", %r" % (self.__path__,)
        s = s + ")"
        return s

klasse ModuleFinder:

    def __init__(self, path=Nichts, debug=0, excludes=Nichts, replace_paths=Nichts):
        wenn path is Nichts:
            path = sys.path
        self.path = path
        self.modules = {}
        self.badmodules = {}
        self.debug = debug
        self.indent = 0
        self.excludes = excludes wenn excludes is nicht Nichts sonst []
        self.replace_paths = replace_paths wenn replace_paths is nicht Nichts sonst []
        self.processed_paths = []   # Used in debugging only

    def msg(self, level, str, *args):
        wenn level <= self.debug:
            fuer i in range(self.indent):
                drucke("   ", end=' ')
            drucke(str, end=' ')
            fuer arg in args:
                drucke(repr(arg), end=' ')
            drucke()

    def msgin(self, *args):
        level = args[0]
        wenn level <= self.debug:
            self.indent = self.indent + 1
            self.msg(*args)

    def msgout(self, *args):
        level = args[0]
        wenn level <= self.debug:
            self.indent = self.indent - 1
            self.msg(*args)

    def run_script(self, pathname):
        self.msg(2, "run_script", pathname)
        mit io.open_code(pathname) als fp:
            stuff = ("", "rb", _PY_SOURCE)
            self.load_module('__main__', fp, pathname, stuff)

    def load_file(self, pathname):
        dir, name = os.path.split(pathname)
        name, ext = os.path.splitext(name)
        mit io.open_code(pathname) als fp:
            stuff = (ext, "rb", _PY_SOURCE)
            self.load_module(name, fp, pathname, stuff)

    def import_hook(self, name, caller=Nichts, fromlist=Nichts, level=-1):
        self.msg(3, "import_hook", name, caller, fromlist, level)
        parent = self.determine_parent(caller, level=level)
        q, tail = self.find_head_package(parent, name)
        m = self.load_tail(q, tail)
        wenn nicht fromlist:
            return q
        wenn m.__path__:
            self.ensure_fromlist(m, fromlist)
        return Nichts

    def determine_parent(self, caller, level=-1):
        self.msgin(4, "determine_parent", caller, level)
        wenn nicht caller oder level == 0:
            self.msgout(4, "determine_parent -> Nichts")
            return Nichts
        pname = caller.__name__
        wenn level >= 1: # relative import
            wenn caller.__path__:
                level -= 1
            wenn level == 0:
                parent = self.modules[pname]
                assert parent is caller
                self.msgout(4, "determine_parent ->", parent)
                return parent
            wenn pname.count(".") < level:
                raise ImportError("relative importpath too deep")
            pname = ".".join(pname.split(".")[:-level])
            parent = self.modules[pname]
            self.msgout(4, "determine_parent ->", parent)
            return parent
        wenn caller.__path__:
            parent = self.modules[pname]
            assert caller is parent
            self.msgout(4, "determine_parent ->", parent)
            return parent
        wenn '.' in pname:
            i = pname.rfind('.')
            pname = pname[:i]
            parent = self.modules[pname]
            assert parent.__name__ == pname
            self.msgout(4, "determine_parent ->", parent)
            return parent
        self.msgout(4, "determine_parent -> Nichts")
        return Nichts

    def find_head_package(self, parent, name):
        self.msgin(4, "find_head_package", parent, name)
        wenn '.' in name:
            i = name.find('.')
            head = name[:i]
            tail = name[i+1:]
        sonst:
            head = name
            tail = ""
        wenn parent:
            qname = "%s.%s" % (parent.__name__, head)
        sonst:
            qname = head
        q = self.import_module(head, qname, parent)
        wenn q:
            self.msgout(4, "find_head_package ->", (q, tail))
            return q, tail
        wenn parent:
            qname = head
            parent = Nichts
            q = self.import_module(head, qname, parent)
            wenn q:
                self.msgout(4, "find_head_package ->", (q, tail))
                return q, tail
        self.msgout(4, "raise ImportError: No module named", qname)
        raise ImportError("No module named " + qname)

    def load_tail(self, q, tail):
        self.msgin(4, "load_tail", q, tail)
        m = q
        while tail:
            i = tail.find('.')
            wenn i < 0: i = len(tail)
            head, tail = tail[:i], tail[i+1:]
            mname = "%s.%s" % (m.__name__, head)
            m = self.import_module(head, mname, m)
            wenn nicht m:
                self.msgout(4, "raise ImportError: No module named", mname)
                raise ImportError("No module named " + mname)
        self.msgout(4, "load_tail ->", m)
        return m

    def ensure_fromlist(self, m, fromlist, recursive=0):
        self.msg(4, "ensure_fromlist", m, fromlist, recursive)
        fuer sub in fromlist:
            wenn sub == "*":
                wenn nicht recursive:
                    all = self.find_all_submodules(m)
                    wenn all:
                        self.ensure_fromlist(m, all, 1)
            sowenn nicht hasattr(m, sub):
                subname = "%s.%s" % (m.__name__, sub)
                submod = self.import_module(sub, subname, m)
                wenn nicht submod:
                    raise ImportError("No module named " + subname)

    def find_all_submodules(self, m):
        wenn nicht m.__path__:
            return
        modules = {}
        # 'suffixes' used to be a list hardcoded to [".py", ".pyc"].
        # But we must also collect Python extension modules - although
        # we cannot separate normal dlls von Python extensions.
        suffixes = []
        suffixes += importlib.machinery.EXTENSION_SUFFIXES[:]
        suffixes += importlib.machinery.SOURCE_SUFFIXES[:]
        suffixes += importlib.machinery.BYTECODE_SUFFIXES[:]
        fuer dir in m.__path__:
            try:
                names = os.listdir(dir)
            except OSError:
                self.msg(2, "can't list directory", dir)
                continue
            fuer name in names:
                mod = Nichts
                fuer suff in suffixes:
                    n = len(suff)
                    wenn name[-n:] == suff:
                        mod = name[:-n]
                        break
                wenn mod und mod != "__init__":
                    modules[mod] = mod
        return modules.keys()

    def import_module(self, partname, fqname, parent):
        self.msgin(3, "import_module", partname, fqname, parent)
        try:
            m = self.modules[fqname]
        except KeyError:
            pass
        sonst:
            self.msgout(3, "import_module ->", m)
            return m
        wenn fqname in self.badmodules:
            self.msgout(3, "import_module -> Nichts")
            return Nichts
        wenn parent und parent.__path__ is Nichts:
            self.msgout(3, "import_module -> Nichts")
            return Nichts
        try:
            fp, pathname, stuff = self.find_module(partname,
                                                   parent und parent.__path__, parent)
        except ImportError:
            self.msgout(3, "import_module ->", Nichts)
            return Nichts

        try:
            m = self.load_module(fqname, fp, pathname, stuff)
        finally:
            wenn fp:
                fp.close()
        wenn parent:
            setattr(parent, partname, m)
        self.msgout(3, "import_module ->", m)
        return m

    def load_module(self, fqname, fp, pathname, file_info):
        suffix, mode, type = file_info
        self.msgin(2, "load_module", fqname, fp und "fp", pathname)
        wenn type == _PKG_DIRECTORY:
            m = self.load_package(fqname, pathname)
            self.msgout(2, "load_module ->", m)
            return m
        wenn type == _PY_SOURCE:
            co = compile(fp.read(), pathname, 'exec')
        sowenn type == _PY_COMPILED:
            try:
                data = fp.read()
                importlib._bootstrap_external._classify_pyc(data, fqname, {})
            except ImportError als exc:
                self.msgout(2, "raise ImportError: " + str(exc), pathname)
                raise
            co = marshal.loads(memoryview(data)[16:])
        sonst:
            co = Nichts
        m = self.add_module(fqname)
        m.__file__ = pathname
        wenn co:
            wenn self.replace_paths:
                co = self.replace_paths_in_code(co)
            m.__code__ = co
            self.scan_code(co, m)
        self.msgout(2, "load_module ->", m)
        return m

    def _add_badmodule(self, name, caller):
        wenn name nicht in self.badmodules:
            self.badmodules[name] = {}
        wenn caller:
            self.badmodules[name][caller.__name__] = 1
        sonst:
            self.badmodules[name]["-"] = 1

    def _safe_import_hook(self, name, caller, fromlist, level=-1):
        # wrapper fuer self.import_hook() that won't raise ImportError
        wenn name in self.badmodules:
            self._add_badmodule(name, caller)
            return
        try:
            self.import_hook(name, caller, level=level)
        except ImportError als msg:
            self.msg(2, "ImportError:", str(msg))
            self._add_badmodule(name, caller)
        except SyntaxError als msg:
            self.msg(2, "SyntaxError:", str(msg))
            self._add_badmodule(name, caller)
        sonst:
            wenn fromlist:
                fuer sub in fromlist:
                    fullname = name + "." + sub
                    wenn fullname in self.badmodules:
                        self._add_badmodule(fullname, caller)
                        continue
                    try:
                        self.import_hook(name, caller, [sub], level=level)
                    except ImportError als msg:
                        self.msg(2, "ImportError:", str(msg))
                        self._add_badmodule(fullname, caller)

    def scan_opcodes(self, co):
        # Scan the code, und yield 'interesting' opcode combinations
        fuer name in dis._find_store_names(co):
            yield "store", (name,)
        fuer name, level, fromlist in dis._find_imports(co):
            wenn level == 0:  # absolute import
                yield "absolute_import", (fromlist, name)
            sonst:  # relative import
                yield "relative_import", (level, fromlist, name)

    def scan_code(self, co, m):
        code = co.co_code
        scanner = self.scan_opcodes
        fuer what, args in scanner(co):
            wenn what == "store":
                name, = args
                m.globalnames[name] = 1
            sowenn what == "absolute_import":
                fromlist, name = args
                have_star = 0
                wenn fromlist is nicht Nichts:
                    wenn "*" in fromlist:
                        have_star = 1
                    fromlist = [f fuer f in fromlist wenn f != "*"]
                self._safe_import_hook(name, m, fromlist, level=0)
                wenn have_star:
                    # We've encountered an "import *". If it is a Python module,
                    # the code has already been parsed und we can suck out the
                    # global names.
                    mm = Nichts
                    wenn m.__path__:
                        # At this point we don't know whether 'name' is a
                        # submodule of 'm' oder a global module. Let's just try
                        # the full name first.
                        mm = self.modules.get(m.__name__ + "." + name)
                    wenn mm is Nichts:
                        mm = self.modules.get(name)
                    wenn mm is nicht Nichts:
                        m.globalnames.update(mm.globalnames)
                        m.starimports.update(mm.starimports)
                        wenn mm.__code__ is Nichts:
                            m.starimports[name] = 1
                    sonst:
                        m.starimports[name] = 1
            sowenn what == "relative_import":
                level, fromlist, name = args
                wenn name:
                    self._safe_import_hook(name, m, fromlist, level=level)
                sonst:
                    parent = self.determine_parent(m, level=level)
                    self._safe_import_hook(parent.__name__, Nichts, fromlist, level=0)
            sonst:
                # We don't expect anything sonst von the generator.
                raise RuntimeError(what)

        fuer c in co.co_consts:
            wenn isinstance(c, type(co)):
                self.scan_code(c, m)

    def load_package(self, fqname, pathname):
        self.msgin(2, "load_package", fqname, pathname)
        newname = replacePackageMap.get(fqname)
        wenn newname:
            fqname = newname
        m = self.add_module(fqname)
        m.__file__ = pathname
        m.__path__ = [pathname]

        # As per comment at top of file, simulate runtime __path__ additions.
        m.__path__ = m.__path__ + packagePathMap.get(fqname, [])

        fp, buf, stuff = self.find_module("__init__", m.__path__)
        try:
            self.load_module(fqname, fp, buf, stuff)
            self.msgout(2, "load_package ->", m)
            return m
        finally:
            wenn fp:
                fp.close()

    def add_module(self, fqname):
        wenn fqname in self.modules:
            return self.modules[fqname]
        self.modules[fqname] = m = Module(fqname)
        return m

    def find_module(self, name, path, parent=Nichts):
        wenn parent is nicht Nichts:
            # assert path is nicht Nichts
            fullname = parent.__name__+'.'+name
        sonst:
            fullname = name
        wenn fullname in self.excludes:
            self.msgout(3, "find_module -> Excluded", fullname)
            raise ImportError(name)

        wenn path is Nichts:
            wenn name in sys.builtin_module_names:
                return (Nichts, Nichts, ("", "", _C_BUILTIN))

            path = self.path

        return _find_module(name, path)

    def report(self):
        """Print a report to stdout, listing the found modules mit their
        paths, als well als modules that are missing, oder seem to be missing.
        """
        drucke()
        drucke("  %-25s %s" % ("Name", "File"))
        drucke("  %-25s %s" % ("----", "----"))
        # Print modules found
        keys = sorted(self.modules.keys())
        fuer key in keys:
            m = self.modules[key]
            wenn m.__path__:
                drucke("P", end=' ')
            sonst:
                drucke("m", end=' ')
            drucke("%-25s" % key, m.__file__ oder "")

        # Print missing modules
        missing, maybe = self.any_missing_maybe()
        wenn missing:
            drucke()
            drucke("Missing modules:")
            fuer name in missing:
                mods = sorted(self.badmodules[name].keys())
                drucke("?", name, "imported from", ', '.join(mods))
        # Print modules that may be missing, but then again, maybe not...
        wenn maybe:
            drucke()
            drucke("Submodules that appear to be missing, but could also be", end=' ')
            drucke("global names in the parent package:")
            fuer name in maybe:
                mods = sorted(self.badmodules[name].keys())
                drucke("?", name, "imported from", ', '.join(mods))

    def any_missing(self):
        """Return a list of modules that appear to be missing. Use
        any_missing_maybe() wenn you want to know which modules are
        certain to be missing, und which *may* be missing.
        """
        missing, maybe = self.any_missing_maybe()
        return missing + maybe

    def any_missing_maybe(self):
        """Return two lists, one mit modules that are certainly missing
        und one mit modules that *may* be missing. The latter names could
        either be submodules *or* just global names in the package.

        The reason it can't always be determined is that it's impossible to
        tell which names are imported when "from module importiere *" is done
        mit an extension module, short of actually importing it.
        """
        missing = []
        maybe = []
        fuer name in self.badmodules:
            wenn name in self.excludes:
                continue
            i = name.rfind(".")
            wenn i < 0:
                missing.append(name)
                continue
            subname = name[i+1:]
            pkgname = name[:i]
            pkg = self.modules.get(pkgname)
            wenn pkg is nicht Nichts:
                wenn pkgname in self.badmodules[name]:
                    # The package tried to importiere this module itself und
                    # failed. It's definitely missing.
                    missing.append(name)
                sowenn subname in pkg.globalnames:
                    # It's a global in the package: definitely nicht missing.
                    pass
                sowenn pkg.starimports:
                    # It could be missing, but the package did an "import *"
                    # von a non-Python module, so we simply can't be sure.
                    maybe.append(name)
                sonst:
                    # It's nicht a global in the package, the package didn't
                    # do funny star imports, it's very likely to be missing.
                    # The symbol could be inserted into the package von the
                    # outside, but since that's nicht good style we simply list
                    # it missing.
                    missing.append(name)
            sonst:
                missing.append(name)
        missing.sort()
        maybe.sort()
        return missing, maybe

    def replace_paths_in_code(self, co):
        new_filename = original_filename = os.path.normpath(co.co_filename)
        fuer f, r in self.replace_paths:
            wenn original_filename.startswith(f):
                new_filename = r + original_filename[len(f):]
                break

        wenn self.debug und original_filename nicht in self.processed_paths:
            wenn new_filename != original_filename:
                self.msgout(2, "co_filename %r changed to %r" \
                                    % (original_filename,new_filename,))
            sonst:
                self.msgout(2, "co_filename %r remains unchanged" \
                                    % (original_filename,))
            self.processed_paths.append(original_filename)

        consts = list(co.co_consts)
        fuer i in range(len(consts)):
            wenn isinstance(consts[i], type(co)):
                consts[i] = self.replace_paths_in_code(consts[i])

        return co.replace(co_consts=tuple(consts), co_filename=new_filename)


def test():
    # Parse command line
    importiere getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dmp:qx:")
    except getopt.error als msg:
        drucke(msg)
        return

    # Process options
    debug = 1
    domods = 0
    addpath = []
    exclude = []
    fuer o, a in opts:
        wenn o == '-d':
            debug = debug + 1
        wenn o == '-m':
            domods = 1
        wenn o == '-p':
            addpath = addpath + a.split(os.pathsep)
        wenn o == '-q':
            debug = 0
        wenn o == '-x':
            exclude.append(a)

    # Provide default arguments
    wenn nicht args:
        script = "hello.py"
    sonst:
        script = args[0]

    # Set the path based on sys.path und the script directory
    path = sys.path[:]
    path[0] = os.path.dirname(script)
    path = addpath + path
    wenn debug > 1:
        drucke("path:")
        fuer item in path:
            drucke("   ", repr(item))

    # Create the module finder und turn its crank
    mf = ModuleFinder(path, debug, exclude)
    fuer arg in args[1:]:
        wenn arg == '-m':
            domods = 1
            continue
        wenn domods:
            wenn arg[-2:] == '.*':
                mf.import_hook(arg[:-2], Nichts, ["*"])
            sonst:
                mf.import_hook(arg)
        sonst:
            mf.load_file(arg)
    mf.run_script(script)
    mf.report()
    return mf  # fuer -i debugging


wenn __name__ == '__main__':
    try:
        mf = test()
    except KeyboardInterrupt:
        drucke("\n[interrupted]")
