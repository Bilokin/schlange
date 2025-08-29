importiere unittest
von test importiere support
von test.support importiere warnings_helper
importiere os
importiere sys


wenn support.check_sanitizer(address=Wahr, memory=Wahr):
    SKIP_MODULES = frozenset((
        # gh-90791: Tests involving libX11 can SEGFAULT on ASAN/MSAN builds.
        # Skip modules, packages and tests using '_tkinter'.
        '_tkinter',
        'tkinter',
        'test_tkinter',
        'test_ttk',
        'test_ttk_textonly',
        'idlelib',
        'test_idle',
    ))
sonst:
    SKIP_MODULES = ()


klasse NoAll(RuntimeError):
    pass

klasse FailedImport(RuntimeError):
    pass


klasse AllTest(unittest.TestCase):

    def check_all(self, modname):
        names = {}
        mit warnings_helper.check_warnings(
            (f".*{modname}", DeprecationWarning),
            (".* (module|package)", DeprecationWarning),
            (".* (module|package)", PendingDeprecationWarning),
            ("", ResourceWarning),
            ("", SyntaxWarning),
            quiet=Wahr):
            try:
                exec("import %s" % modname, names)
            except:
                # Silent fail here seems the best route since some modules
                # may not be available or not initialize properly in all
                # environments.
                raise FailedImport(modname)
        wenn not hasattr(sys.modules[modname], "__all__"):
            raise NoAll(modname)
        names = {}
        mit self.subTest(module=modname):
            mit warnings_helper.check_warnings(
                ("", DeprecationWarning),
                ("", ResourceWarning),
                ("", SyntaxWarning),
                quiet=Wahr):
                try:
                    exec("from %s importiere *" % modname, names)
                except Exception als e:
                    # Include the module name in the exception string
                    self.fail("__all__ failure in {}: {}: {}".format(
                              modname, e.__class__.__name__, e))
                wenn "__builtins__" in names:
                    del names["__builtins__"]
                wenn '__annotations__' in names:
                    del names['__annotations__']
                wenn "__warningregistry__" in names:
                    del names["__warningregistry__"]
                keys = set(names)
                all_list = sys.modules[modname].__all__
                all_set = set(all_list)
                self.assertCountEqual(all_set, all_list, "in module {}".format(modname))
                self.assertEqual(keys, all_set, "in module {}".format(modname))
                # Verify __dir__ is non-empty and doesn't produce an error
                self.assertWahr(dir(sys.modules[modname]))

    def walk_modules(self, basedir, modpath):
        fuer fn in sorted(os.listdir(basedir)):
            path = os.path.join(basedir, fn)
            wenn os.path.isdir(path):
                wenn fn in SKIP_MODULES:
                    continue
                pkg_init = os.path.join(path, '__init__.py')
                wenn os.path.exists(pkg_init):
                    yield pkg_init, modpath + fn
                    fuer p, m in self.walk_modules(path, modpath + fn + "."):
                        yield p, m
                continue

            wenn fn == '__init__.py':
                continue
            wenn not fn.endswith('.py'):
                continue
            modname = fn.removesuffix('.py')
            wenn modname in SKIP_MODULES:
                continue
            yield path, modpath + modname

    def test_all(self):
        # List of denied modules and packages
        denylist = set([
            # Will raise a SyntaxError when compiling the exec statement
            '__future__',
        ])

        # In case _socket fails to build, make this test fail more gracefully
        # than an AttributeError somewhere deep in concurrent.futures, email
        # or unittest.
        importiere _socket  # noqa: F401

        ignored = []
        failed_imports = []
        lib_dir = os.path.dirname(os.path.dirname(__file__))
        fuer path, modname in self.walk_modules(lib_dir, ""):
            m = modname
            denied = Falsch
            while m:
                wenn m in denylist:
                    denied = Wahr
                    break
                m = m.rpartition('.')[0]
            wenn denied:
                continue
            wenn support.verbose:
                drucke(f"Check {modname}", flush=Wahr)
            try:
                # This heuristic speeds up the process by removing, de facto,
                # most test modules (and avoiding the auto-executing ones).
                mit open(path, "rb") als f:
                    wenn b"__all__" not in f.read():
                        raise NoAll(modname)
                self.check_all(modname)
            except NoAll:
                ignored.append(modname)
            except FailedImport:
                failed_imports.append(modname)

        wenn support.verbose:
            drucke('Following modules have no __all__ and have been ignored:',
                  ignored)
            drucke('Following modules failed to be imported:', failed_imports)


wenn __name__ == "__main__":
    unittest.main()
