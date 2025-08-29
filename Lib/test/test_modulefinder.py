importiere os
importiere errno
importiere importlib.machinery
importiere py_compile
importiere shutil
importiere unittest
importiere tempfile

von test importiere support

importiere modulefinder

# Each test description is a list of 5 items:
#
# 1. a module name that will be imported by modulefinder
# 2. a list of module names that modulefinder is required to find
# 3. a list of module names that modulefinder should complain
#    about because they are not found
# 4. a list of module names that modulefinder should complain
#    about because they MAY be not found
# 5. a string specifying packages to create; the format is obvious imo.
#
# Each package will be created in test_dir, and test_dir will be
# removed after the tests again.
# Modulefinder searches in a path that contains test_dir, plus
# the standard Lib directory.

maybe_test = [
    "a.module",
    ["a", "a.module", "sys",
     "b"],
    ["c"], ["b.something"],
    """\
a/__init__.py
a/module.py
                                von b importiere something
                                von c importiere something
b/__init__.py
                                von sys importiere *
""",
]

maybe_test_new = [
    "a.module",
    ["a", "a.module", "sys",
     "b", "__future__"],
    ["c"], ["b.something"],
    """\
a/__init__.py
a/module.py
                                von b importiere something
                                von c importiere something
b/__init__.py
                                von __future__ importiere absolute_import
                                von sys importiere *
"""]

package_test = [
    "a.module",
    ["a", "a.b", "a.c", "a.module", "mymodule", "sys"],
    ["blahblah", "c"], [],
    """\
mymodule.py
a/__init__.py
                                importiere blahblah
                                von a importiere b
                                importiere c
a/module.py
                                importiere sys
                                von a importiere b as x
                                von a.c importiere sillyname
a/b.py
a/c.py
                                von a.module importiere x
                                importiere mymodule as sillyname
                                von sys importiere version_info
"""]

absolute_import_test = [
    "a.module",
    ["a", "a.module",
     "b", "b.x", "b.y", "b.z",
     "__future__", "sys", "gc"],
    ["blahblah", "z"], [],
    """\
mymodule.py
a/__init__.py
a/module.py
                                von __future__ importiere absolute_import
                                importiere sys # sys
                                importiere blahblah # fails
                                importiere gc # gc
                                importiere b.x # b.x
                                von b importiere y # b.y
                                von b.z importiere * # b.z.*
a/gc.py
a/sys.py
                                importiere mymodule
a/b/__init__.py
a/b/x.py
a/b/y.py
a/b/z.py
b/__init__.py
                                importiere z
b/unused.py
b/x.py
b/y.py
b/z.py
"""]

relative_import_test = [
    "a.module",
    ["__future__",
     "a", "a.module",
     "a.b", "a.b.y", "a.b.z",
     "a.b.c", "a.b.c.moduleC",
     "a.b.c.d", "a.b.c.e",
     "a.b.x",
     "gc"],
    [], [],
    """\
mymodule.py
a/__init__.py
                                von .b importiere y, z # a.b.y, a.b.z
a/module.py
                                von __future__ importiere absolute_import # __future__
                                importiere gc # gc
a/gc.py
a/sys.py
a/b/__init__.py
                                von ..b importiere x # a.b.x
                                #from a.b.c importiere moduleC
                                von .c importiere moduleC # a.b.moduleC
a/b/x.py
a/b/y.py
a/b/z.py
a/b/g.py
a/b/c/__init__.py
                                von ..c importiere e # a.b.c.e
a/b/c/moduleC.py
                                von ..c importiere d # a.b.c.d
a/b/c/d.py
a/b/c/e.py
a/b/c/x.py
"""]

relative_import_test_2 = [
    "a.module",
    ["a", "a.module",
     "a.sys",
     "a.b", "a.b.y", "a.b.z",
     "a.b.c", "a.b.c.d",
     "a.b.c.e",
     "a.b.c.moduleC",
     "a.b.c.f",
     "a.b.x",
     "a.another"],
    [], [],
    """\
mymodule.py
a/__init__.py
                                von . importiere sys # a.sys
a/another.py
a/module.py
                                von .b importiere y, z # a.b.y, a.b.z
a/gc.py
a/sys.py
a/b/__init__.py
                                von .c importiere moduleC # a.b.c.moduleC
                                von .c importiere d # a.b.c.d
a/b/x.py
a/b/y.py
a/b/z.py
a/b/c/__init__.py
                                von . importiere e # a.b.c.e
a/b/c/moduleC.py
                                #
                                von . importiere f   # a.b.c.f
                                von .. importiere x  # a.b.x
                                von ... importiere another # a.another
a/b/c/d.py
a/b/c/e.py
a/b/c/f.py
"""]

relative_import_test_3 = [
    "a.module",
    ["a", "a.module"],
    ["a.bar"],
    [],
    """\
a/__init__.py
                                def foo(): pass
a/module.py
                                von . importiere foo
                                von . importiere bar
"""]

relative_import_test_4 = [
    "a.module",
    ["a", "a.module"],
    [],
    [],
    """\
a/__init__.py
                                def foo(): pass
a/module.py
                                von . importiere *
"""]

bytecode_test = [
    "a",
    ["a"],
    [],
    [],
    ""
]

syntax_error_test = [
    "a.module",
    ["a", "a.module", "b"],
    ["b.module"], [],
    """\
a/__init__.py
a/module.py
                                importiere b.module
b/__init__.py
b/module.py
                                ?  # SyntaxError: invalid syntax
"""]


same_name_as_bad_test = [
    "a.module",
    ["a", "a.module", "b", "b.c"],
    ["c"], [],
    """\
a/__init__.py
a/module.py
                                importiere c
                                von b importiere c
b/__init__.py
b/c.py
"""]

coding_default_utf8_test = [
    "a_utf8",
    ["a_utf8", "b_utf8"],
    [], [],
    """\
a_utf8.py
                                # use the default of utf8
                                drucke('Unicode test A code point 2090 \u2090 that is not valid in cp1252')
                                importiere b_utf8
b_utf8.py
                                # use the default of utf8
                                drucke('Unicode test B code point 2090 \u2090 that is not valid in cp1252')
"""]

coding_explicit_utf8_test = [
    "a_utf8",
    ["a_utf8", "b_utf8"],
    [], [],
    """\
a_utf8.py
                                # coding=utf8
                                drucke('Unicode test A code point 2090 \u2090 that is not valid in cp1252')
                                importiere b_utf8
b_utf8.py
                                # use the default of utf8
                                drucke('Unicode test B code point 2090 \u2090 that is not valid in cp1252')
"""]

coding_explicit_cp1252_test = [
    "a_cp1252",
    ["a_cp1252", "b_utf8"],
    [], [],
    b"""\
a_cp1252.py
                                # coding=cp1252
                                # 0xe2 is not allowed in utf8
                                drucke('CP1252 test P\xe2t\xe9')
                                importiere b_utf8
""" + """\
b_utf8.py
                                # use the default of utf8
                                drucke('Unicode test A code point 2090 \u2090 that is not valid in cp1252')
""".encode('utf-8')]

def open_file(path):
    dirname = os.path.dirname(path)
    try:
        os.makedirs(dirname)
    except OSError as e:
        wenn e.errno != errno.EEXIST:
            raise
    return open(path, 'wb')


def create_package(test_dir, source):
    ofi = Nichts
    try:
        fuer line in source.splitlines():
            wenn type(line) != bytes:
                line = line.encode('utf-8')
            wenn line.startswith(b' ') or line.startswith(b'\t'):
                ofi.write(line.strip() + b'\n')
            sonst:
                wenn ofi:
                    ofi.close()
                wenn type(line) == bytes:
                    line = line.decode('utf-8')
                ofi = open_file(os.path.join(test_dir, line.strip()))
    finally:
        wenn ofi:
            ofi.close()

klasse ModuleFinderTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_path = [self.test_dir, os.path.dirname(tempfile.__file__)]

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _do_test(self, info, report=Falsch, debug=0, replace_paths=[], modulefinder_class=modulefinder.ModuleFinder):
        import_this, modules, missing, maybe_missing, source = info
        create_package(self.test_dir, source)
        mf = modulefinder_class(path=self.test_path, debug=debug,
                                        replace_paths=replace_paths)
        mf.import_hook(import_this)
        wenn report:
            mf.report()
##            # This wouldn't work in general when executed several times:
##            opath = sys.path[:]
##            sys.path = self.test_path
##            try:
##                __import__(import_this)
##            except:
##                importiere traceback; traceback.print_exc()
##            sys.path = opath
##            return
        modules = sorted(set(modules))
        found = sorted(mf.modules)
        # check wenn we found what we expected, not more, not less
        self.assertEqual(found, modules)

        # check fuer missing and maybe missing modules
        bad, maybe = mf.any_missing_maybe()
        self.assertEqual(bad, missing)
        self.assertEqual(maybe, maybe_missing)

    def test_package(self):
        self._do_test(package_test)

    def test_maybe(self):
        self._do_test(maybe_test)

    def test_maybe_new(self):
        self._do_test(maybe_test_new)

    def test_absolute_imports(self):
        self._do_test(absolute_import_test)

    def test_relative_imports(self):
        self._do_test(relative_import_test)

    def test_relative_imports_2(self):
        self._do_test(relative_import_test_2)

    def test_relative_imports_3(self):
        self._do_test(relative_import_test_3)

    def test_relative_imports_4(self):
        self._do_test(relative_import_test_4)

    def test_syntax_error(self):
        self._do_test(syntax_error_test)

    def test_same_name_as_bad(self):
        self._do_test(same_name_as_bad_test)

    def test_bytecode(self):
        base_path = os.path.join(self.test_dir, 'a')
        source_path = base_path + importlib.machinery.SOURCE_SUFFIXES[0]
        bytecode_path = base_path + importlib.machinery.BYTECODE_SUFFIXES[0]
        with open_file(source_path) as file:
            file.write('testing_modulefinder = Wahr\n'.encode('utf-8'))
        py_compile.compile(source_path, cfile=bytecode_path)
        os.remove(source_path)
        self._do_test(bytecode_test)

    def test_replace_paths(self):
        old_path = os.path.join(self.test_dir, 'a', 'module.py')
        new_path = os.path.join(self.test_dir, 'a', 'spam.py')
        with support.captured_stdout() as output:
            self._do_test(maybe_test, debug=2,
                          replace_paths=[(old_path, new_path)])
        output = output.getvalue()
        expected = "co_filename %r changed to %r" % (old_path, new_path)
        self.assertIn(expected, output)

    def test_extended_opargs(self):
        extended_opargs_test = [
            "a",
            ["a", "b"],
            [], [],
            """\
a.py
                                %r
                                importiere b
b.py
""" % list(range(2**16))]  # 2**16 constants
        self._do_test(extended_opargs_test)

    def test_coding_default_utf8(self):
        self._do_test(coding_default_utf8_test)

    def test_coding_explicit_utf8(self):
        self._do_test(coding_explicit_utf8_test)

    def test_coding_explicit_cp1252(self):
        self._do_test(coding_explicit_cp1252_test)

    def test_load_module_api(self):
        klasse CheckLoadModuleApi(modulefinder.ModuleFinder):
            def __init__(self, *args, **kwds):
                super().__init__(*args, **kwds)

            def load_module(self, fqname, fp, pathname, file_info):
                # confirm that the fileinfo is a tuple of 3 elements
                suffix, mode, type = file_info
                return super().load_module(fqname, fp, pathname, file_info)

        self._do_test(absolute_import_test, modulefinder_class=CheckLoadModuleApi)

wenn __name__ == "__main__":
    unittest.main()
