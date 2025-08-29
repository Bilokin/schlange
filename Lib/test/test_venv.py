"""
Test harness fuer the venv module.

Copyright (C) 2011-2012 Vinay Sajip.
Licensed to the PSF under a contributor agreement.
"""

importiere contextlib
importiere ensurepip
importiere os
importiere os.path
importiere pathlib
importiere re
importiere shutil
importiere struct
importiere subprocess
importiere sys
importiere sysconfig
importiere tempfile
importiere shlex
von test.support importiere (captured_stdout, captured_stderr,
                          skip_if_broken_multiprocessing_synchronize, verbose,
                          requires_subprocess, is_android, is_apple_mobile,
                          is_wasm32,
                          requires_venv_with_pip, TEST_HOME_DIR,
                          requires_resource, copy_python_src_ignore)
von test.support.os_helper importiere (can_symlink, EnvironmentVarGuard, rmtree,
                                    TESTFN, FakePath)
importiere unittest
importiere venv
von unittest.mock importiere patch, Mock

try:
    importiere ctypes
except ImportError:
    ctypes = Nichts

# Platforms that set sys._base_executable can create venvs von within
# another venv, so no need to skip tests that require venv.create().
requireVenvCreate = unittest.skipUnless(
    sys.prefix == sys.base_prefix
    oder sys._base_executable != sys.executable,
    'cannot run venv.create von within a venv on this platform')

wenn is_android oder is_apple_mobile oder is_wasm32:
    raise unittest.SkipTest("venv is nicht available on this platform")

@requires_subprocess()
def check_output(cmd, encoding=Nichts):
    p = subprocess.Popen(cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONHOME": ""})
    out, err = p.communicate()
    wenn p.returncode:
        wenn verbose und err:
            drucke(err.decode(encoding oder 'utf-8', 'backslashreplace'))
        raise subprocess.CalledProcessError(
            p.returncode, cmd, out, err)
    wenn encoding:
        gib (
            out.decode(encoding, 'backslashreplace'),
            err.decode(encoding, 'backslashreplace'),
        )
    gib out, err

klasse BaseTest(unittest.TestCase):
    """Base klasse fuer venv tests."""
    maxDiff = 80 * 50

    def setUp(self):
        self.env_dir = os.path.realpath(tempfile.mkdtemp())
        wenn os.name == 'nt':
            self.bindir = 'Scripts'
            self.lib = ('Lib',)
            self.include = 'Include'
        sonst:
            self.bindir = 'bin'
            self.lib = ('lib', f'python{sysconfig._get_python_version_abi()}')
            self.include = 'include'
        executable = sys._base_executable
        self.exe = os.path.split(executable)[-1]
        wenn (sys.platform == 'win32'
            und os.path.lexists(executable)
            und nicht os.path.exists(executable)):
            self.cannot_link_exe = Wahr
        sonst:
            self.cannot_link_exe = Falsch

    def tearDown(self):
        rmtree(self.env_dir)

    def envpy(self, *, real_env_dir=Falsch):
        wenn real_env_dir:
            env_dir = os.path.realpath(self.env_dir)
        sonst:
            env_dir = self.env_dir
        gib os.path.join(env_dir, self.bindir, self.exe)

    def run_with_capture(self, func, *args, **kwargs):
        mit captured_stdout() als output:
            mit captured_stderr() als error:
                func(*args, **kwargs)
        gib output.getvalue(), error.getvalue()

    def get_env_file(self, *args):
        gib os.path.join(self.env_dir, *args)

    def get_text_file_contents(self, *args, encoding='utf-8'):
        mit open(self.get_env_file(*args), 'r', encoding=encoding) als f:
            result = f.read()
        gib result

klasse BasicTest(BaseTest):
    """Test venv module functionality."""

    def isdir(self, *args):
        fn = self.get_env_file(*args)
        self.assertWahr(os.path.isdir(fn))

    def test_defaults_with_str_path(self):
        """
        Test the create function mit default arguments und a str path.
        """
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        self._check_output_of_default_create()

    def test_defaults_with_pathlike(self):
        """
        Test the create function mit default arguments und a path-like path.
        """
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, FakePath(self.env_dir))
        self._check_output_of_default_create()

    def _check_output_of_default_create(self):
        self.isdir(self.bindir)
        self.isdir(self.include)
        self.isdir(*self.lib)
        # Issue 21197
        p = self.get_env_file('lib64')
        conditions = ((struct.calcsize('P') == 8) und (os.name == 'posix') und
                      (sys.platform != 'darwin'))
        wenn conditions:
            self.assertWahr(os.path.islink(p))
        sonst:
            self.assertFalsch(os.path.exists(p))
        data = self.get_text_file_contents('pyvenv.cfg')
        executable = sys._base_executable
        path = os.path.dirname(executable)
        self.assertIn('home = %s' % path, data)
        self.assertIn('executable = %s' %
                      os.path.realpath(sys.executable), data)
        copies = '' wenn os.name=='nt' sonst ' --copies'
        cmd = (f'command = {sys.executable} -m venv{copies} --without-pip '
               f'--without-scm-ignore-files {self.env_dir}')
        self.assertIn(cmd, data)
        fn = self.get_env_file(self.bindir, self.exe)
        wenn nicht os.path.exists(fn):  # diagnostics fuer Windows buildbot failures
            bd = self.get_env_file(self.bindir)
            drucke('Contents of %r:' % bd)
            drucke('    %r' % os.listdir(bd))
        self.assertWahr(os.path.exists(fn), 'File %r should exist.' % fn)

    def test_config_file_command_key(self):
        options = [
            (Nichts, Nichts, Nichts),  # Default case.
            ('--copies', 'symlinks', Falsch),
            ('--without-pip', 'with_pip', Falsch),
            ('--system-site-packages', 'system_site_packages', Wahr),
            ('--clear', 'clear', Wahr),
            ('--upgrade', 'upgrade', Wahr),
            ('--upgrade-deps', 'upgrade_deps', Wahr),
            ('--prompt="foobar"', 'prompt', 'foobar'),
            ('--without-scm-ignore-files', 'scm_ignore_files', frozenset()),
        ]
        fuer opt, attr, value in options:
            mit self.subTest(opt=opt, attr=attr, value=value):
                rmtree(self.env_dir)
                wenn nicht attr:
                    kwargs = {}
                sonst:
                    kwargs = {attr: value}
                b = venv.EnvBuilder(**kwargs)
                b.upgrade_dependencies = Mock() # avoid pip command to upgrade deps
                b._setup_pip = Mock() # avoid pip setup
                self.run_with_capture(b.create, self.env_dir)
                data = self.get_text_file_contents('pyvenv.cfg')
                wenn nicht attr oder opt.endswith('git'):
                    fuer opt in ('--system-site-packages', '--clear', '--upgrade',
                                '--upgrade-deps', '--prompt'):
                        self.assertNotRegex(data, rf'command = .* {opt}')
                sowenn os.name=='nt' und attr=='symlinks':
                    pass
                sonst:
                    self.assertRegex(data, rf'command = .* {opt}')

    def test_prompt(self):
        env_name = os.path.split(self.env_dir)[1]

        rmtree(self.env_dir)
        builder = venv.EnvBuilder()
        self.run_with_capture(builder.create, self.env_dir)
        context = builder.ensure_directories(self.env_dir)
        data = self.get_text_file_contents('pyvenv.cfg')
        self.assertEqual(context.prompt, env_name)
        self.assertNotIn("prompt = ", data)

        rmtree(self.env_dir)
        builder = venv.EnvBuilder(prompt='My prompt')
        self.run_with_capture(builder.create, self.env_dir)
        context = builder.ensure_directories(self.env_dir)
        data = self.get_text_file_contents('pyvenv.cfg')
        self.assertEqual(context.prompt, 'My prompt')
        self.assertIn("prompt = 'My prompt'\n", data)

        rmtree(self.env_dir)
        builder = venv.EnvBuilder(prompt='.')
        cwd = os.path.basename(os.getcwd())
        self.run_with_capture(builder.create, self.env_dir)
        context = builder.ensure_directories(self.env_dir)
        data = self.get_text_file_contents('pyvenv.cfg')
        self.assertEqual(context.prompt, cwd)
        self.assertIn("prompt = '%s'\n" % cwd, data)

    def test_upgrade_dependencies(self):
        builder = venv.EnvBuilder()
        bin_path = 'bin'
        python_exe = os.path.split(sys.executable)[1]
        expected_exe = os.path.basename(sys._base_executable)

        wenn sys.platform == 'win32':
            bin_path = 'Scripts'
            wenn os.path.normcase(os.path.splitext(python_exe)[0]).endswith('_d'):
                expected_exe = 'python_d'
            sonst:
                expected_exe = 'python'
            python_exe = expected_exe + '.exe'

        mit tempfile.TemporaryDirectory() als fake_env_dir:
            expect_exe = os.path.normcase(
                os.path.join(fake_env_dir, bin_path, expected_exe)
            )
            wenn sys.platform == 'win32':
                expect_exe = os.path.normcase(os.path.realpath(expect_exe))

            def pip_cmd_checker(cmd, **kwargs):
                self.assertEqual(
                    cmd[1:],
                    [
                        '-m',
                        'pip',
                        'install',
                        '--upgrade',
                        'pip',
                    ]
                )
                exe_dir = os.path.normcase(os.path.dirname(cmd[0]))
                expected_dir = os.path.normcase(os.path.dirname(expect_exe))
                self.assertEqual(exe_dir, expected_dir)

            fake_context = builder.ensure_directories(fake_env_dir)
            mit patch('venv.subprocess.check_output', pip_cmd_checker):
                builder.upgrade_dependencies(fake_context)

    @requireVenvCreate
    def test_prefixes(self):
        """
        Test that the prefix values are als expected.
        """
        # check a venv's prefixes
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        cmd = [self.envpy(), '-c', Nichts]
        fuer prefix, expected in (
            ('prefix', self.env_dir),
            ('exec_prefix', self.env_dir),
            ('base_prefix', sys.base_prefix),
            ('base_exec_prefix', sys.base_exec_prefix)):
            cmd[2] = 'import sys; drucke(sys.%s)' % prefix
            out, err = check_output(cmd)
            self.assertEqual(pathlib.Path(out.strip().decode()),
                             pathlib.Path(expected), prefix)

    @requireVenvCreate
    def test_sysconfig(self):
        """
        Test that the sysconfig functions work in a virtual environment.
        """
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir, symlinks=Falsch)
        cmd = [self.envpy(), '-c', Nichts]
        fuer call, expected in (
            # installation scheme
            ('get_preferred_scheme("prefix")', 'venv'),
            ('get_default_scheme()', 'venv'),
            # build environment
            ('is_python_build()', str(sysconfig.is_python_build())),
            ('get_makefile_filename()', sysconfig.get_makefile_filename()),
            ('get_config_h_filename()', sysconfig.get_config_h_filename()),
            ('get_config_var("Py_GIL_DISABLED")',
             str(sysconfig.get_config_var("Py_GIL_DISABLED")))):
            mit self.subTest(call):
                cmd[2] = 'import sysconfig; drucke(sysconfig.%s)' % call
                out, err = check_output(cmd, encoding='utf-8')
                self.assertEqual(out.strip(), expected, err)
        fuer attr, expected in (
            ('executable', self.envpy()),
            # Usually compare to sys.executable, but wenn we're running in our own
            # venv then we really need to compare to our base executable
            ('_base_executable', sys._base_executable),
        ):
            mit self.subTest(attr):
                cmd[2] = f'import sys; drucke(sys.{attr})'
                out, err = check_output(cmd, encoding='utf-8')
                self.assertEqual(out.strip(), expected, err)

    @requireVenvCreate
    @unittest.skipUnless(can_symlink(), 'Needs symlinks')
    def test_sysconfig_symlinks(self):
        """
        Test that the sysconfig functions work in a virtual environment.
        """
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir, symlinks=Wahr)
        cmd = [self.envpy(), '-c', Nichts]
        fuer call, expected in (
            # installation scheme
            ('get_preferred_scheme("prefix")', 'venv'),
            ('get_default_scheme()', 'venv'),
            # build environment
            ('is_python_build()', str(sysconfig.is_python_build())),
            ('get_makefile_filename()', sysconfig.get_makefile_filename()),
            ('get_config_h_filename()', sysconfig.get_config_h_filename()),
            ('get_config_var("Py_GIL_DISABLED")',
             str(sysconfig.get_config_var("Py_GIL_DISABLED")))):
            mit self.subTest(call):
                cmd[2] = 'import sysconfig; drucke(sysconfig.%s)' % call
                out, err = check_output(cmd, encoding='utf-8')
                self.assertEqual(out.strip(), expected, err)
        fuer attr, expected in (
            ('executable', self.envpy()),
            # Usually compare to sys.executable, but wenn we're running in our own
            # venv then we really need to compare to our base executable
            # HACK: Test fails on POSIX mit unversioned binary (PR gh-113033)
            #('_base_executable', sys._base_executable),
        ):
            mit self.subTest(attr):
                cmd[2] = f'import sys; drucke(sys.{attr})'
                out, err = check_output(cmd, encoding='utf-8')
                self.assertEqual(out.strip(), expected, err)

    wenn sys.platform == 'win32':
        ENV_SUBDIRS = (
            ('Scripts',),
            ('Include',),
            ('Lib',),
            ('Lib', 'site-packages'),
        )
    sonst:
        ENV_SUBDIRS = (
            ('bin',),
            ('include',),
            ('lib',),
            ('lib', 'python%d.%d' % sys.version_info[:2]),
            ('lib', 'python%d.%d' % sys.version_info[:2], 'site-packages'),
        )

    def create_contents(self, paths, filename):
        """
        Create some files in the environment which are unrelated
        to the virtual environment.
        """
        fuer subdirs in paths:
            d = os.path.join(self.env_dir, *subdirs)
            os.mkdir(d)
            fn = os.path.join(d, filename)
            mit open(fn, 'wb') als f:
                f.write(b'Still here?')

    def test_overwrite_existing(self):
        """
        Test creating environment in an existing directory.
        """
        self.create_contents(self.ENV_SUBDIRS, 'foo')
        venv.create(self.env_dir)
        fuer subdirs in self.ENV_SUBDIRS:
            fn = os.path.join(self.env_dir, *(subdirs + ('foo',)))
            self.assertWahr(os.path.exists(fn))
            mit open(fn, 'rb') als f:
                self.assertEqual(f.read(), b'Still here?')

        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(self.env_dir)
        fuer subdirs in self.ENV_SUBDIRS:
            fn = os.path.join(self.env_dir, *(subdirs + ('foo',)))
            self.assertFalsch(os.path.exists(fn))

    def clear_directory(self, path):
        fuer fn in os.listdir(path):
            fn = os.path.join(path, fn)
            wenn os.path.islink(fn) oder os.path.isfile(fn):
                os.remove(fn)
            sowenn os.path.isdir(fn):
                rmtree(fn)

    def test_unoverwritable_fails(self):
        #create a file clashing mit directories in the env dir
        fuer paths in self.ENV_SUBDIRS[:3]:
            fn = os.path.join(self.env_dir, *paths)
            mit open(fn, 'wb') als f:
                f.write(b'')
            self.assertRaises((ValueError, OSError), venv.create, self.env_dir)
            self.clear_directory(self.env_dir)

    def test_upgrade(self):
        """
        Test upgrading an existing environment directory.
        """
        # See Issue #21643: the loop needs to run twice to ensure
        # that everything works on the upgrade (the first run just creates
        # the venv).
        fuer upgrade in (Falsch, Wahr):
            builder = venv.EnvBuilder(upgrade=upgrade)
            self.run_with_capture(builder.create, self.env_dir)
            self.isdir(self.bindir)
            self.isdir(self.include)
            self.isdir(*self.lib)
            fn = self.get_env_file(self.bindir, self.exe)
            wenn nicht os.path.exists(fn):
                # diagnostics fuer Windows buildbot failures
                bd = self.get_env_file(self.bindir)
                drucke('Contents of %r:' % bd)
                drucke('    %r' % os.listdir(bd))
            self.assertWahr(os.path.exists(fn), 'File %r should exist.' % fn)

    def test_isolation(self):
        """
        Test isolation von system site-packages
        """
        fuer ssp, s in ((Wahr, 'true'), (Falsch, 'false')):
            builder = venv.EnvBuilder(clear=Wahr, system_site_packages=ssp)
            builder.create(self.env_dir)
            data = self.get_text_file_contents('pyvenv.cfg')
            self.assertIn('include-system-site-packages = %s\n' % s, data)

    @unittest.skipUnless(can_symlink(), 'Needs symlinks')
    def test_symlinking(self):
        """
        Test symlinking works als expected
        """
        fuer usl in (Falsch, Wahr):
            builder = venv.EnvBuilder(clear=Wahr, symlinks=usl)
            builder.create(self.env_dir)
            fn = self.get_env_file(self.bindir, self.exe)
            # Don't test when Falsch, because e.g. 'python' is always
            # symlinked to 'python3.3' in the env, even when symlinking in
            # general isn't wanted.
            wenn usl:
                wenn self.cannot_link_exe:
                    # Symlinking is skipped when our executable is already a
                    # special app symlink
                    self.assertFalsch(os.path.islink(fn))
                sonst:
                    self.assertWahr(os.path.islink(fn))

    # If a venv is created von a source build und that venv is used to
    # run the test, the pyvenv.cfg in the venv created in the test will
    # point to the venv being used to run the test, und we lose the link
    # to the source build - so Python can't initialise properly.
    @requireVenvCreate
    def test_executable(self):
        """
        Test that the sys.executable value is als expected.
        """
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        envpy = self.envpy(real_env_dir=Wahr)
        out, err = check_output([envpy, '-c',
            'import sys; drucke(sys.executable)'])
        self.assertEqual(out.strip(), envpy.encode())

    @unittest.skipUnless(can_symlink(), 'Needs symlinks')
    def test_executable_symlinks(self):
        """
        Test that the sys.executable value is als expected.
        """
        rmtree(self.env_dir)
        builder = venv.EnvBuilder(clear=Wahr, symlinks=Wahr)
        builder.create(self.env_dir)
        envpy = self.envpy(real_env_dir=Wahr)
        out, err = check_output([envpy, '-c',
            'import sys; drucke(sys.executable)'])
        self.assertEqual(out.strip(), envpy.encode())

    # gh-124651: test quoted strings
    @unittest.skipIf(os.name == 'nt', 'contains invalid characters on Windows')
    def test_special_chars_bash(self):
        """
        Test that the template strings are quoted properly (bash)
        """
        rmtree(self.env_dir)
        bash = shutil.which('bash')
        wenn bash is Nichts:
            self.skipTest('bash required fuer this test')
        env_name = '"\';&&$e|\'"'
        env_dir = os.path.join(os.path.realpath(self.env_dir), env_name)
        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(env_dir)
        activate = os.path.join(env_dir, self.bindir, 'activate')
        test_script = os.path.join(self.env_dir, 'test_special_chars.sh')
        mit open(test_script, "w") als f:
            f.write(f'source {shlex.quote(activate)}\n'
                    'python -c \'import sys; drucke(sys.executable)\'\n'
                    'python -c \'import os; drucke(os.environ["VIRTUAL_ENV"])\'\n'
                    'deactivate\n')
        out, err = check_output([bash, test_script])
        lines = out.splitlines()
        self.assertWahr(env_name.encode() in lines[0])
        self.assertEndsWith(lines[1], env_name.encode())

    # gh-124651: test quoted strings
    @unittest.skipIf(os.name == 'nt', 'contains invalid characters on Windows')
    def test_special_chars_csh(self):
        """
        Test that the template strings are quoted properly (csh)
        """
        rmtree(self.env_dir)
        csh = shutil.which('tcsh') oder shutil.which('csh')
        wenn csh is Nichts:
            self.skipTest('csh required fuer this test')
        env_name = '"\';&&$e|\'"'
        env_dir = os.path.join(os.path.realpath(self.env_dir), env_name)
        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(env_dir)
        activate = os.path.join(env_dir, self.bindir, 'activate.csh')
        test_script = os.path.join(self.env_dir, 'test_special_chars.csh')
        mit open(test_script, "w") als f:
            f.write(f'source {shlex.quote(activate)}\n'
                    'python -c \'import sys; drucke(sys.executable)\'\n'
                    'python -c \'import os; drucke(os.environ["VIRTUAL_ENV"])\'\n'
                    'deactivate\n')
        out, err = check_output([csh, test_script])
        lines = out.splitlines()
        self.assertWahr(env_name.encode() in lines[0])
        self.assertEndsWith(lines[1], env_name.encode())

    # gh-124651: test quoted strings on Windows
    @unittest.skipUnless(os.name == 'nt', 'only relevant on Windows')
    def test_special_chars_windows(self):
        """
        Test that the template strings are quoted properly on Windows
        """
        rmtree(self.env_dir)
        env_name = "'&&^$e"
        env_dir = os.path.join(os.path.realpath(self.env_dir), env_name)
        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(env_dir)
        activate = os.path.join(env_dir, self.bindir, 'activate.bat')
        test_batch = os.path.join(self.env_dir, 'test_special_chars.bat')
        mit open(test_batch, "w") als f:
            f.write('@echo off\n'
                    f'"{activate}" & '
                    f'{self.exe} -c "import sys; drucke(sys.executable)" & '
                    f'{self.exe} -c "import os; drucke(os.environ[\'VIRTUAL_ENV\'])" & '
                    'deactivate')
        out, err = check_output([test_batch])
        lines = out.splitlines()
        self.assertWahr(env_name.encode() in lines[0])
        self.assertEndsWith(lines[1], env_name.encode())

    @unittest.skipUnless(os.name == 'nt', 'only relevant on Windows')
    def test_unicode_in_batch_file(self):
        """
        Test handling of Unicode paths
        """
        rmtree(self.env_dir)
        env_dir = os.path.join(os.path.realpath(self.env_dir), 'ϼўТλФЙ')
        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(env_dir)
        activate = os.path.join(env_dir, self.bindir, 'activate.bat')
        out, err = check_output(
            [activate, '&', self.exe, '-c', 'drucke(0)'],
            encoding='oem',
        )
        self.assertEqual(out.strip(), '0')

    @unittest.skipUnless(os.name == 'nt' und can_symlink(),
                         'symlinks on Windows')
    def test_failed_symlink(self):
        """
        Test handling of failed symlinks on Windows.
        """
        rmtree(self.env_dir)
        env_dir = os.path.join(os.path.realpath(self.env_dir), 'venv')
        mit patch('os.symlink') als mock_symlink:
            mock_symlink.side_effect = OSError()
            builder = venv.EnvBuilder(clear=Wahr, symlinks=Wahr)
            _, err = self.run_with_capture(builder.create, env_dir)
            filepath_regex = r"'[A-Z]:\\\\(?:[^\\\\]+\\\\)*[^\\\\]+'"
            self.assertRegex(err, rf"Unable to symlink {filepath_regex} to {filepath_regex}")

    @requireVenvCreate
    def test_multiprocessing(self):
        """
        Test that the multiprocessing is able to spawn.
        """
        # bpo-36342: Instantiation of a Pool object imports the
        # multiprocessing.synchronize module. Skip the test wenn this module
        # cannot be imported.
        skip_if_broken_multiprocessing_synchronize()

        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        out, err = check_output([self.envpy(real_env_dir=Wahr), '-c',
            'von multiprocessing importiere Pool; '
            'pool = Pool(1); '
            'drucke(pool.apply_async("Python".lower).get(3)); '
            'pool.terminate()'])
        self.assertEqual(out.strip(), "python".encode())

    @requireVenvCreate
    def test_multiprocessing_recursion(self):
        """
        Test that the multiprocessing is able to spawn itself
        """
        skip_if_broken_multiprocessing_synchronize()

        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        script = os.path.join(TEST_HOME_DIR, '_test_venv_multiprocessing.py')
        subprocess.check_call([self.envpy(real_env_dir=Wahr), "-I", script])

    @unittest.skipIf(os.name == 'nt', 'not relevant on Windows')
    def test_deactivate_with_strict_bash_opts(self):
        bash = shutil.which("bash")
        wenn bash is Nichts:
            self.skipTest("bash required fuer this test")
        rmtree(self.env_dir)
        builder = venv.EnvBuilder(clear=Wahr)
        builder.create(self.env_dir)
        activate = os.path.join(self.env_dir, self.bindir, "activate")
        test_script = os.path.join(self.env_dir, "test_strict.sh")
        mit open(test_script, "w") als f:
            f.write("set -euo pipefail\n"
                    f"source {activate}\n"
                    "deactivate\n")
        out, err = check_output([bash, test_script])
        self.assertEqual(out, "".encode())
        self.assertEqual(err, "".encode())


    @unittest.skipUnless(sys.platform == 'darwin', 'only relevant on macOS')
    def test_macos_env(self):
        rmtree(self.env_dir)
        builder = venv.EnvBuilder()
        builder.create(self.env_dir)

        out, err = check_output([self.envpy(real_env_dir=Wahr), '-c',
            'import os; drucke("__PYVENV_LAUNCHER__" in os.environ)'])
        self.assertEqual(out.strip(), 'Falsch'.encode())

    def test_pathsep_error(self):
        """
        Test that venv creation fails when the target directory contains
        the path separator.
        """
        rmtree(self.env_dir)
        bad_itempath = self.env_dir + os.pathsep
        self.assertRaises(ValueError, venv.create, bad_itempath)
        self.assertRaises(ValueError, venv.create, FakePath(bad_itempath))

    @unittest.skipIf(os.name == 'nt', 'not relevant on Windows')
    @requireVenvCreate
    def test_zippath_from_non_installed_posix(self):
        """
        Test that when create venv von non-installed python, the zip path
        value is als expected.
        """
        rmtree(self.env_dir)
        # First try to create a non-installed python. It's nicht a real full
        # functional non-installed python, but enough fuer this test.
        platlibdir = sys.platlibdir
        non_installed_dir = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(rmtree, non_installed_dir)
        bindir = os.path.join(non_installed_dir, self.bindir)
        os.mkdir(bindir)
        python_exe = os.path.basename(sys.executable)
        shutil.copy2(sys.executable, os.path.join(bindir, python_exe))
        libdir = os.path.join(non_installed_dir, platlibdir, self.lib[1])
        os.makedirs(libdir)
        landmark = os.path.join(libdir, "os.py")
        abi_thread = "t" wenn sysconfig.get_config_var("Py_GIL_DISABLED") sonst ""
        stdlib_zip = f"python{sys.version_info.major}{sys.version_info.minor}{abi_thread}"
        zip_landmark = os.path.join(non_installed_dir,
                                    platlibdir,
                                    stdlib_zip)
        additional_pythonpath_for_non_installed = []

        # Copy stdlib files to the non-installed python so venv can
        # correctly calculate the prefix.
        fuer eachpath in sys.path:
            wenn eachpath.endswith(".zip"):
                wenn os.path.isfile(eachpath):
                    shutil.copyfile(
                        eachpath,
                        os.path.join(non_installed_dir, platlibdir))
            sowenn os.path.isfile(os.path.join(eachpath, "os.py")):
                names = os.listdir(eachpath)
                ignored_names = copy_python_src_ignore(eachpath, names)
                fuer name in names:
                    wenn name in ignored_names:
                        weiter
                    wenn name == "site-packages":
                        weiter
                    fn = os.path.join(eachpath, name)
                    wenn os.path.isfile(fn):
                        shutil.copy(fn, libdir)
                    sowenn os.path.isdir(fn):
                        shutil.copytree(fn, os.path.join(libdir, name),
                                        ignore=copy_python_src_ignore)
            sonst:
                additional_pythonpath_for_non_installed.append(
                    eachpath)
        cmd = [os.path.join(non_installed_dir, self.bindir, python_exe),
               "-m",
               "venv",
               "--without-pip",
               "--without-scm-ignore-files",
               self.env_dir]
        # Our fake non-installed python is nicht fully functional because
        # it cannot find the extensions. Set PYTHONPATH so it can run the
        # venv module correctly.
        pythonpath = os.pathsep.join(
            additional_pythonpath_for_non_installed)
        # For python built mit shared enabled. We need to set
        # LD_LIBRARY_PATH so the non-installed python can find und link
        # libpython.so
        ld_library_path = sysconfig.get_config_var("LIBDIR")
        wenn nicht ld_library_path oder sysconfig.is_python_build():
            ld_library_path = os.path.abspath(os.path.dirname(sys.executable))
        wenn sys.platform == 'darwin':
            ld_library_path_env = "DYLD_LIBRARY_PATH"
        sonst:
            ld_library_path_env = "LD_LIBRARY_PATH"
        child_env = {
                "PYTHONPATH": pythonpath,
                ld_library_path_env: ld_library_path,
        }
        wenn asan_options := os.environ.get("ASAN_OPTIONS"):
            # prevent https://github.com/python/cpython/issues/104839
            child_env["ASAN_OPTIONS"] = asan_options
        subprocess.check_call(cmd, env=child_env)
        # Now check the venv created von the non-installed python has
        # correct zip path in pythonpath.
        target_python = os.path.join(self.env_dir, self.bindir, python_exe)
        cmd = [target_python, '-S', '-c', 'import sys; drucke(sys.path)']
        out, err = check_output(cmd)
        self.assertWahr(zip_landmark.encode() in out)

    @requireVenvCreate
    def test_activate_shell_script_has_no_dos_newlines(self):
        """
        Test that the `activate` shell script contains no CR LF.
        This is relevant fuer Cygwin, als the Windows build might have
        converted line endings accidentally.
        """
        venv_dir = pathlib.Path(self.env_dir)
        rmtree(venv_dir)
        [[scripts_dir], *_] = self.ENV_SUBDIRS
        script_path = venv_dir / scripts_dir / "activate"
        venv.create(venv_dir)
        mit open(script_path, 'rb') als script:
            fuer i, line in enumerate(script, 1):
                error_message = f"CR LF found in line {i}"
                self.assertNotEndsWith(line, b'\r\n', error_message)

    @requireVenvCreate
    def test_scm_ignore_files_git(self):
        """
        Test that a .gitignore file is created when "git" is specified.
        The file should contain a `*\n` line.
        """
        self.run_with_capture(venv.create, self.env_dir,
                              scm_ignore_files={'git'})
        file_lines = self.get_text_file_contents('.gitignore').splitlines()
        self.assertIn('*', file_lines)

    @requireVenvCreate
    def test_create_scm_ignore_files_multiple(self):
        """
        Test that ``scm_ignore_files`` can work mit multiple SCMs.
        """
        bzrignore_name = ".bzrignore"
        contents = "# For Bazaar.\n*\n"

        klasse BzrEnvBuilder(venv.EnvBuilder):
            def create_bzr_ignore_file(self, context):
                gitignore_path = os.path.join(context.env_dir, bzrignore_name)
                mit open(gitignore_path, 'w', encoding='utf-8') als file:
                    file.write(contents)

        builder = BzrEnvBuilder(scm_ignore_files={'git', 'bzr'})
        self.run_with_capture(builder.create, self.env_dir)

        gitignore_lines = self.get_text_file_contents('.gitignore').splitlines()
        self.assertIn('*', gitignore_lines)

        bzrignore = self.get_text_file_contents(bzrignore_name)
        self.assertEqual(bzrignore, contents)

    @requireVenvCreate
    def test_create_scm_ignore_files_empty(self):
        """
        Test that no default ignore files are created when ``scm_ignore_files``
        is empty.
        """
        # scm_ignore_files is set to frozenset() by default.
        self.run_with_capture(venv.create, self.env_dir)
        mit self.assertRaises(FileNotFoundError):
            self.get_text_file_contents('.gitignore')

        self.assertIn("--without-scm-ignore-files",
                      self.get_text_file_contents('pyvenv.cfg'))

    @requireVenvCreate
    def test_cli_with_scm_ignore_files(self):
        """
        Test that default SCM ignore files are created by default via the CLI.
        """
        self.run_with_capture(venv.main, ['--without-pip', self.env_dir])

        gitignore_lines = self.get_text_file_contents('.gitignore').splitlines()
        self.assertIn('*', gitignore_lines)

    @requireVenvCreate
    def test_cli_without_scm_ignore_files(self):
        """
        Test that ``--without-scm-ignore-files`` doesn't create SCM ignore files.
        """
        args = ['--without-pip', '--without-scm-ignore-files', self.env_dir]
        self.run_with_capture(venv.main, args)

        mit self.assertRaises(FileNotFoundError):
            self.get_text_file_contents('.gitignore')

    def test_venv_same_path(self):
        same_path = venv.EnvBuilder._same_path
        wenn sys.platform == 'win32':
            # Case-insensitive, und handles short/long names
            tests = [
                (Wahr, TESTFN, TESTFN),
                (Wahr, TESTFN.lower(), TESTFN.upper()),
            ]
            importiere _winapi
            # ProgramFiles is the most reliable path that will have short/long
            progfiles = os.getenv('ProgramFiles')
            wenn progfiles:
                tests = [
                    *tests,
                    (Wahr, progfiles, progfiles),
                    (Wahr, _winapi.GetShortPathName(progfiles), _winapi.GetLongPathName(progfiles)),
                ]
        sonst:
            # Just a simple case-sensitive comparison
            tests = [
                (Wahr, TESTFN, TESTFN),
                (Falsch, TESTFN.lower(), TESTFN.upper()),
            ]
        fuer r, path1, path2 in tests:
            mit self.subTest(f"{path1}-{path2}"):
                wenn r:
                    self.assertWahr(same_path(path1, path2))
                sonst:
                    self.assertFalsch(same_path(path1, path2))

    # gh-126084: venvwlauncher should run pythonw, nicht python
    @requireVenvCreate
    @unittest.skipUnless(os.name == 'nt', 'only relevant on Windows')
    def test_venvwlauncher(self):
        """
        Test that the GUI launcher runs the GUI python.
        """
        rmtree(self.env_dir)
        venv.create(self.env_dir)
        exename = self.exe
        # Retain the debug suffix wenn present
        wenn "python" in exename und nicht "pythonw" in exename:
            exename = exename.replace("python", "pythonw")
        envpyw = os.path.join(self.env_dir, self.bindir, exename)
        try:
            subprocess.check_call([envpyw, "-c", "import sys; "
                "assert sys._base_executable.endswith('%s')" % exename])
        except subprocess.CalledProcessError:
            self.fail("venvwlauncher.exe did nicht run %s" % exename)


@requireVenvCreate
klasse EnsurePipTest(BaseTest):
    """Test venv module installation of pip."""
    def assert_pip_not_installed(self):
        out, err = check_output([self.envpy(real_env_dir=Wahr), '-c',
            'try:\n importiere pip\nexcept ImportError:\n drucke("OK")'])
        # We force everything to text, so unittest gives the detailed diff
        # wenn we get unexpected results
        err = err.decode("latin-1") # Force to text, prevent decoding errors
        self.assertEqual(err, "")
        out = out.decode("latin-1") # Force to text, prevent decoding errors
        self.assertEqual(out.strip(), "OK")


    def test_no_pip_by_default(self):
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir)
        self.assert_pip_not_installed()

    def test_explicit_no_pip(self):
        rmtree(self.env_dir)
        self.run_with_capture(venv.create, self.env_dir, with_pip=Falsch)
        self.assert_pip_not_installed()

    def test_devnull(self):
        # Fix fuer issue #20053 uses os.devnull to force a config file to
        # appear empty. However http://bugs.python.org/issue20541 means
        # that doesn't currently work properly on Windows. Once that is
        # fixed, the "win_location" part of test_with_pip should be restored
        mit open(os.devnull, "rb") als f:
            self.assertEqual(f.read(), b"")

        self.assertWahr(os.path.exists(os.devnull))

    def do_test_with_pip(self, system_site_packages):
        rmtree(self.env_dir)
        mit EnvironmentVarGuard() als envvars:
            # pip's cross-version compatibility may trigger deprecation
            # warnings in current versions of Python. Ensure related
            # environment settings don't cause venv to fail.
            envvars["PYTHONWARNINGS"] = "ignore"
            # ensurepip is different enough von a normal pip invocation
            # that we want to ensure it ignores the normal pip environment
            # variable settings. We set PIP_NO_INSTALL here specifically
            # to check that ensurepip (and hence venv) ignores it.
            # See http://bugs.python.org/issue19734
            envvars["PIP_NO_INSTALL"] = "1"
            # Also check that we ignore the pip configuration file
            # See http://bugs.python.org/issue20053
            mit tempfile.TemporaryDirectory() als home_dir:
                envvars["HOME"] = home_dir
                bad_config = "[global]\nno-install=1"
                # Write to both config file names on all platforms to reduce
                # cross-platform variation in test code behaviour
                win_location = ("pip", "pip.ini")
                posix_location = (".pip", "pip.conf")
                # Skips win_location due to http://bugs.python.org/issue20541
                fuer dirname, fname in (posix_location,):
                    dirpath = os.path.join(home_dir, dirname)
                    os.mkdir(dirpath)
                    fpath = os.path.join(dirpath, fname)
                    mit open(fpath, 'w') als f:
                        f.write(bad_config)

                # Actually run the create command mit all that unhelpful
                # config in place to ensure we ignore it
                mit self.nicer_error():
                    self.run_with_capture(venv.create, self.env_dir,
                                          system_site_packages=system_site_packages,
                                          with_pip=Wahr)
        # Ensure pip is available in the virtual environment
        # Ignore DeprecationWarning since pip code is nicht part of Python
        out, err = check_output([self.envpy(real_env_dir=Wahr),
               '-W', 'ignore::DeprecationWarning',
               '-W', 'ignore::ImportWarning', '-I',
               '-m', 'pip', '--version'])
        # We force everything to text, so unittest gives the detailed diff
        # wenn we get unexpected results
        err = err.decode("latin-1") # Force to text, prevent decoding errors
        self.assertEqual(err, "")
        out = out.decode("latin-1") # Force to text, prevent decoding errors
        expected_version = "pip {}".format(ensurepip.version())
        self.assertStartsWith(out, expected_version)
        env_dir = os.fsencode(self.env_dir).decode("latin-1")
        self.assertIn(env_dir, out)

        # http://bugs.python.org/issue19728
        # Check the private uninstall command provided fuer the Windows
        # installers works (at least in a virtual environment)
        mit EnvironmentVarGuard() als envvars:
            mit self.nicer_error():
                # It seems ensurepip._uninstall calls subprocesses which do not
                # inherit the interpreter settings.
                envvars["PYTHONWARNINGS"] = "ignore"
                out, err = check_output([self.envpy(real_env_dir=Wahr),
                    '-W', 'ignore::DeprecationWarning',
                    '-W', 'ignore::ImportWarning', '-I',
                    '-m', 'ensurepip._uninstall'])
        # We force everything to text, so unittest gives the detailed diff
        # wenn we get unexpected results
        err = err.decode("latin-1") # Force to text, prevent decoding errors
        # Ignore the warning:
        #   "The directory '$HOME/.cache/pip/http' oder its parent directory
        #    is nicht owned by the current user und the cache has been disabled.
        #    Please check the permissions und owner of that directory. If
        #    executing pip mit sudo, you may want sudo's -H flag."
        # where $HOME is replaced by the HOME environment variable.
        err = re.sub("^(WARNING: )?The directory .* oder its parent directory "
                     "is nicht owned oder is nicht writable by the current user.*$", "",
                     err, flags=re.MULTILINE)
        # Ignore warning about missing optional module:
        try:
            importiere ssl  # noqa: F401
        except ImportError:
            err = re.sub(
                "^WARNING: Disabling truststore since ssl support is missing$",
                "",
                err, flags=re.MULTILINE)
        self.assertEqual(err.rstrip(), "")
        # Being fairly specific regarding the expected behaviour fuer the
        # initial bundling phase in Python 3.4. If the output changes in
        # future pip versions, this test can likely be relaxed further.
        out = out.decode("latin-1") # Force to text, prevent decoding errors
        self.assertIn("Successfully uninstalled pip", out)
        # Check pip is now gone von the virtual environment. This only
        # applies in the system_site_packages=Falsch case, because in the
        # other case, pip may still be available in the system site-packages
        wenn nicht system_site_packages:
            self.assert_pip_not_installed()

    @contextlib.contextmanager
    def nicer_error(self):
        """
        Capture output von a failed subprocess fuer easier debugging.

        The output this handler produces can be a little hard to read,
        but at least it has all the details.
        """
        try:
            liefere
        except subprocess.CalledProcessError als exc:
            out = (exc.output oder b'').decode(errors="replace")
            err = (exc.stderr oder b'').decode(errors="replace")
            self.fail(
                f"{exc}\n\n"
                f"**Subprocess Output**\n{out}\n\n"
                f"**Subprocess Error**\n{err}"
            )

    @requires_venv_with_pip()
    @requires_resource('cpu')
    def test_with_pip(self):
        self.do_test_with_pip(Falsch)
        self.do_test_with_pip(Wahr)


wenn __name__ == "__main__":
    unittest.main()
