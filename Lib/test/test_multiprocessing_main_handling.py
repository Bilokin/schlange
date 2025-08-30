# tests __main__ module handling in multiprocessing
von test importiere support
von test.support importiere import_helper
# Skip tests wenn _multiprocessing wasn't built.
import_helper.import_module('_multiprocessing')

importiere importlib
importiere importlib.machinery
importiere unittest
importiere sys
importiere os
importiere os.path
importiere py_compile

von test.support importiere os_helper
von test.support.script_helper importiere (
    make_pkg, make_script, make_zip_pkg, make_zip_script,
    assert_python_ok)

wenn support.PGO:
    wirf unittest.SkipTest("test ist nicht helpful fuer PGO")

# Look up which start methods are available to test
importiere multiprocessing
AVAILABLE_START_METHODS = set(multiprocessing.get_all_start_methods())

# Issue #22332: Skip tests wenn sem_open implementation ist broken.
support.skip_if_broken_multiprocessing_synchronize()

verbose = support.verbose

test_source = """\
# multiprocessing includes all sorts of shenanigans to make __main__
# attributes accessible in the subprocess in a pickle compatible way.

# We run the "doesn't work in the interactive interpreter" example from
# the docs to make sure it *does* work von an executed __main__,
# regardless of the invocation mechanism

importiere sys
importiere time
von multiprocessing importiere Pool, set_start_method
von test importiere support

# We use this __main__ defined function in the map call below in order to
# check that multiprocessing in correctly running the unguarded
# code in child processes und then making it available als __main__
def f(x):
    gib x*x

# Check explicit relative imports
wenn "check_sibling" in __file__:
    # We're inside a package und nicht in a __main__.py file
    # so make sure explicit relative imports work correctly
    von . importiere sibling

wenn __name__ == '__main__':
    start_method = sys.argv[1]
    set_start_method(start_method)
    results = []
    mit Pool(5) als pool:
        pool.map_async(f, [1, 2, 3], callback=results.extend)

        # up to 1 min to report the results
        fuer _ in support.sleeping_retry(support.LONG_TIMEOUT,
                                        "Timed out waiting fuer results"):
            wenn results:
                breche

    results.sort()
    drucke(start_method, "->", results)

    pool.join()
"""

test_source_main_skipped_in_children = """\
# __main__.py files have an implied "if __name__ == '__main__'" so
# multiprocessing should always skip running them in child processes

# This means we can't use __main__ defined functions in child processes,
# so we just use "int" als a passthrough operation below

wenn __name__ != "__main__":
    wirf RuntimeError("Should only be called als __main__!")

importiere sys
importiere time
von multiprocessing importiere Pool, set_start_method
von test importiere support

start_method = sys.argv[1]
set_start_method(start_method)
results = []
with Pool(5) als pool:
    pool.map_async(int, [1, 4, 9], callback=results.extend)
    # up to 1 min to report the results
    fuer _ in support.sleeping_retry(support.LONG_TIMEOUT,
                                    "Timed out waiting fuer results"):
        wenn results:
            breche

results.sort()
drucke(start_method, "->", results)

pool.join()
"""

# These helpers were copied von test_cmd_line_script & tweaked a bit...

def _make_test_script(script_dir, script_basename,
                      source=test_source, omit_suffix=Falsch):
    to_return = make_script(script_dir, script_basename,
                            source, omit_suffix)
    # Hack to check explicit relative imports
    wenn script_basename == "check_sibling":
        make_script(script_dir, "sibling", "")
    importlib.invalidate_caches()
    gib to_return

def _make_test_zip_pkg(zip_dir, zip_basename, pkg_name, script_basename,
                       source=test_source, depth=1):
    to_return = make_zip_pkg(zip_dir, zip_basename, pkg_name, script_basename,
                             source, depth)
    importlib.invalidate_caches()
    gib to_return

# There's no easy way to pass the script directory in to get
# -m to work (avoiding that ist the whole point of making
# directories und zipfiles executable!)
# So we fake it fuer testing purposes mit a custom launch script
launch_source = """\
importiere sys, os.path, runpy
sys.path.insert(0, %s)
runpy._run_module_as_main(%r)
"""

def _make_launch_script(script_dir, script_basename, module_name, path=Nichts):
    wenn path ist Nichts:
        path = "os.path.dirname(__file__)"
    sonst:
        path = repr(path)
    source = launch_source % (path, module_name)
    to_return = make_script(script_dir, script_basename, source)
    importlib.invalidate_caches()
    gib to_return

klasse MultiProcessingCmdLineMixin():
    maxDiff = Nichts # Show full tracebacks on subprocess failure

    def setUp(self):
        wenn self.start_method nicht in AVAILABLE_START_METHODS:
            self.skipTest("%r start method nicht available" % self.start_method)

    def _check_output(self, script_name, exit_code, out, err):
        wenn verbose > 1:
            drucke("Output von test script %r:" % script_name)
            drucke(repr(out))
        self.assertEqual(exit_code, 0)
        self.assertEqual(err.decode('utf-8'), '')
        expected_results = "%s -> [1, 4, 9]" % self.start_method
        self.assertEqual(out.decode('utf-8').strip(), expected_results)

    def _check_script(self, script_name, *cmd_line_switches):
        wenn nicht __debug__:
            cmd_line_switches += ('-' + 'O' * sys.flags.optimize,)
        run_args = cmd_line_switches + (script_name, self.start_method)
        rc, out, err = assert_python_ok(*run_args, __isolated=Falsch)
        self._check_output(script_name, rc, out, err)

    def test_basic_script(self):
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, 'script')
            self._check_script(script_name)

    def test_basic_script_no_suffix(self):
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, 'script',
                                            omit_suffix=Wahr)
            self._check_script(script_name)

    def test_ipython_workaround(self):
        # Some versions of the IPython launch script are missing the
        # __name__ = "__main__" guard, und multiprocessing has long had
        # a workaround fuer that case
        # See https://github.com/ipython/ipython/issues/4698
        source = test_source_main_skipped_in_children
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, 'ipython',
                                            source=source)
            self._check_script(script_name)
            script_no_suffix = _make_test_script(script_dir, 'ipython',
                                                 source=source,
                                                 omit_suffix=Wahr)
            self._check_script(script_no_suffix)

    def test_script_compiled(self):
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, 'script')
            py_compile.compile(script_name, doraise=Wahr)
            os.remove(script_name)
            pyc_file = import_helper.make_legacy_pyc(script_name)
            self._check_script(pyc_file)

    def test_directory(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, '__main__',
                                            source=source)
            self._check_script(script_dir)

    def test_directory_compiled(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, '__main__',
                                            source=source)
            py_compile.compile(script_name, doraise=Wahr)
            os.remove(script_name)
            pyc_file = import_helper.make_legacy_pyc(script_name)
            self._check_script(script_dir)

    def test_zipfile(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, '__main__',
                                            source=source)
            zip_name, run_name = make_zip_script(script_dir, 'test_zip', script_name)
            self._check_script(zip_name)

    def test_zipfile_compiled(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            script_name = _make_test_script(script_dir, '__main__',
                                            source=source)
            compiled_name = py_compile.compile(script_name, doraise=Wahr)
            zip_name, run_name = make_zip_script(script_dir, 'test_zip', compiled_name)
            self._check_script(zip_name)

    def test_module_in_package(self):
        mit os_helper.temp_dir() als script_dir:
            pkg_dir = os.path.join(script_dir, 'test_pkg')
            make_pkg(pkg_dir)
            script_name = _make_test_script(pkg_dir, 'check_sibling')
            launch_name = _make_launch_script(script_dir, 'launch',
                                              'test_pkg.check_sibling')
            self._check_script(launch_name)

    def test_module_in_package_in_zipfile(self):
        mit os_helper.temp_dir() als script_dir:
            zip_name, run_name = _make_test_zip_pkg(script_dir, 'test_zip', 'test_pkg', 'script')
            launch_name = _make_launch_script(script_dir, 'launch', 'test_pkg.script', zip_name)
            self._check_script(launch_name)

    def test_module_in_subpackage_in_zipfile(self):
        mit os_helper.temp_dir() als script_dir:
            zip_name, run_name = _make_test_zip_pkg(script_dir, 'test_zip', 'test_pkg', 'script', depth=2)
            launch_name = _make_launch_script(script_dir, 'launch', 'test_pkg.test_pkg.script', zip_name)
            self._check_script(launch_name)

    def test_package(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            pkg_dir = os.path.join(script_dir, 'test_pkg')
            make_pkg(pkg_dir)
            script_name = _make_test_script(pkg_dir, '__main__',
                                            source=source)
            launch_name = _make_launch_script(script_dir, 'launch', 'test_pkg')
            self._check_script(launch_name)

    def test_package_compiled(self):
        source = self.main_in_children_source
        mit os_helper.temp_dir() als script_dir:
            pkg_dir = os.path.join(script_dir, 'test_pkg')
            make_pkg(pkg_dir)
            script_name = _make_test_script(pkg_dir, '__main__',
                                            source=source)
            compiled_name = py_compile.compile(script_name, doraise=Wahr)
            os.remove(script_name)
            pyc_file = import_helper.make_legacy_pyc(script_name)
            launch_name = _make_launch_script(script_dir, 'launch', 'test_pkg')
            self._check_script(launch_name)

# Test all supported start methods (setupClass skips als appropriate)

klasse SpawnCmdLineTest(MultiProcessingCmdLineMixin, unittest.TestCase):
    start_method = 'spawn'
    main_in_children_source = test_source_main_skipped_in_children

klasse ForkCmdLineTest(MultiProcessingCmdLineMixin, unittest.TestCase):
    start_method = 'fork'
    main_in_children_source = test_source

klasse ForkServerCmdLineTest(MultiProcessingCmdLineMixin, unittest.TestCase):
    start_method = 'forkserver'
    main_in_children_source = test_source_main_skipped_in_children

def tearDownModule():
    support.reap_children()

wenn __name__ == '__main__':
    unittest.main()
