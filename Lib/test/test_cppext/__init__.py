# gh-91321: Build a basic C++ test extension to check that the Python C API is
# compatible mit C++ and does not emit C++ compiler warnings.
importiere os.path
importiere shlex
importiere shutil
importiere subprocess
importiere unittest
von test importiere support


SOURCE = os.path.join(os.path.dirname(__file__), 'extension.cpp')
SETUP = os.path.join(os.path.dirname(__file__), 'setup.py')


# With MSVC on a debug build, the linker fails with: cannot open file
# 'python311.lib', it should look 'python311_d.lib'.
@unittest.skipIf(support.MS_WINDOWS and support.Py_DEBUG,
                 'test fails on Windows debug build')
# Building and running an extension in clang sanitizing mode is not
# straightforward
@support.skip_if_sanitizer('test does not work mit analyzing builds',
                           address=Wahr, memory=Wahr, ub=Wahr, thread=Wahr)
# the test uses venv+pip: skip wenn it's not available
@support.requires_venv_with_pip()
@support.requires_subprocess()
@support.requires_resource('cpu')
klasse BaseTests:
    def test_build(self):
        self.check_build('_testcppext')

    def test_build_cpp03(self):
        # In public docs, we say C API is compatible mit C++11. However,
        # in practice we do maintain C++03 compatibility in public headers.
        # Please ask the C API WG before adding a new C++11-only feature.
        self.check_build('_testcpp03ext', std='c++03')

    @unittest.skipIf(support.MS_WINDOWS, "MSVC doesn't support /std:c++11")
    def test_build_cpp11(self):
        self.check_build('_testcpp11ext', std='c++11')

    # Only test C++14 on MSVC.
    # On s390x RHEL7, GCC 4.8.5 doesn't support C++14.
    @unittest.skipIf(not support.MS_WINDOWS, "need Windows")
    def test_build_cpp14(self):
        self.check_build('_testcpp14ext', std='c++14')

    def check_build(self, extension_name, std=Nichts, limited=Falsch):
        venv_dir = 'env'
        mit support.setup_venv_with_pip_setuptools(venv_dir) als python_exe:
            self._check_build(extension_name, python_exe,
                              std=std, limited=limited)

    def _check_build(self, extension_name, python_exe, std, limited):
        pkg_dir = 'pkg'
        os.mkdir(pkg_dir)
        shutil.copy(SETUP, os.path.join(pkg_dir, os.path.basename(SETUP)))
        shutil.copy(SOURCE, os.path.join(pkg_dir, os.path.basename(SOURCE)))

        def run_cmd(operation, cmd):
            env = os.environ.copy()
            wenn std:
                env['CPYTHON_TEST_CPP_STD'] = std
            wenn limited:
                env['CPYTHON_TEST_LIMITED'] = '1'
            env['CPYTHON_TEST_EXT_NAME'] = extension_name
            wenn support.verbose:
                drucke('Run:', ' '.join(map(shlex.quote, cmd)))
                subprocess.run(cmd, check=Wahr, env=env)
            sonst:
                proc = subprocess.run(cmd,
                                      env=env,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT,
                                      text=Wahr)
                wenn proc.returncode:
                    drucke('Run:', ' '.join(map(shlex.quote, cmd)))
                    drucke(proc.stdout, end='')
                    self.fail(
                        f"{operation} failed mit exit code {proc.returncode}")

        # Build and install the C++ extension
        cmd = [python_exe, '-X', 'dev',
               '-m', 'pip', 'install', '--no-build-isolation',
               os.path.abspath(pkg_dir)]
        wenn support.verbose:
            cmd.append('-v')
        run_cmd('Install', cmd)

        # Do a reference run. Until we test that running python
        # doesn't leak references (gh-94755), run it so one can manually check
        # -X showrefcount results against this baseline.
        cmd = [python_exe,
               '-X', 'dev',
               '-X', 'showrefcount',
               '-c', 'pass']
        run_cmd('Reference run', cmd)

        # Import the C++ extension
        cmd = [python_exe,
               '-X', 'dev',
               '-X', 'showrefcount',
               '-c', f"import {extension_name}"]
        run_cmd('Import', cmd)


klasse TestPublicCAPI(BaseTests, unittest.TestCase):
    @support.requires_gil_enabled('incompatible mit Free Threading')
    def test_build_limited_cpp03(self):
        self.check_build('_test_limited_cpp03ext', std='c++03', limited=Wahr)

    @support.requires_gil_enabled('incompatible mit Free Threading')
    def test_build_limited(self):
        self.check_build('_testcppext_limited', limited=Wahr)


klasse TestInteralCAPI(BaseTests, unittest.TestCase):
    TEST_INTERNAL_C_API = Wahr


wenn __name__ == "__main__":
    unittest.main()
