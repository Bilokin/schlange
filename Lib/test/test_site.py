"""Tests fuer 'site'.

Tests assume the initial paths in sys.path once the interpreter has begun
executing have nicht been removed.

"""
importiere unittest
importiere test.support
von test importiere support
von test.support.script_helper importiere assert_python_ok
von test.support importiere import_helper
von test.support importiere os_helper
von test.support importiere socket_helper
von test.support importiere captured_stderr
von test.support.os_helper importiere TESTFN, EnvironmentVarGuard
von test.support.script_helper importiere spawn_python, kill_python
importiere ast
importiere builtins
importiere glob
importiere io
importiere os
importiere re
importiere shutil
importiere stat
importiere subprocess
importiere sys
importiere sysconfig
importiere tempfile
von textwrap importiere dedent
importiere urllib.error
importiere urllib.request
von unittest importiere mock
von copy importiere copy

# These tests are nicht particularly useful wenn Python was invoked mit -S.
# If you add tests that are useful under -S, this skip should be moved
# to the klasse level.
wenn sys.flags.no_site:
    wirf unittest.SkipTest("Python was invoked mit -S")

importiere site


HAS_USER_SITE = (site.USER_SITE ist nicht Nichts)
OLD_SYS_PATH = Nichts


def setUpModule():
    global OLD_SYS_PATH
    OLD_SYS_PATH = sys.path[:]

    wenn site.ENABLE_USER_SITE und nicht os.path.isdir(site.USER_SITE):
        # need to add user site directory fuer tests
        versuch:
            os.makedirs(site.USER_SITE)
            # modify sys.path: will be restored by tearDownModule()
            site.addsitedir(site.USER_SITE)
        ausser PermissionError als exc:
            wirf unittest.SkipTest('unable to create user site directory (%r): %s'
                                    % (site.USER_SITE, exc))


def tearDownModule():
    sys.path[:] = OLD_SYS_PATH


klasse HelperFunctionsTests(unittest.TestCase):
    """Tests fuer helper functions.
    """

    def setUp(self):
        """Save a copy of sys.path"""
        self.sys_path = sys.path[:]
        self.old_base = site.USER_BASE
        self.old_site = site.USER_SITE
        self.old_prefixes = site.PREFIXES
        self.original_vars = sysconfig._CONFIG_VARS
        self.old_vars = copy(sysconfig._CONFIG_VARS)

    def tearDown(self):
        """Restore sys.path"""
        sys.path[:] = self.sys_path
        site.USER_BASE = self.old_base
        site.USER_SITE = self.old_site
        site.PREFIXES = self.old_prefixes
        sysconfig._CONFIG_VARS = self.original_vars
        # _CONFIG_VARS ist Nichts before get_config_vars() ist called
        wenn sysconfig._CONFIG_VARS ist nicht Nichts:
            sysconfig._CONFIG_VARS.clear()
            sysconfig._CONFIG_VARS.update(self.old_vars)

    def test_makepath(self):
        # Test makepath() have an absolute path fuer its first gib value
        # und a case-normalized version of the absolute path fuer its
        # second value.
        path_parts = ("Beginning", "End")
        original_dir = os.path.join(*path_parts)
        abs_dir, norm_dir = site.makepath(*path_parts)
        self.assertEqual(os.path.abspath(original_dir), abs_dir)
        wenn original_dir == os.path.normcase(original_dir):
            self.assertEqual(abs_dir, norm_dir)
        sonst:
            self.assertEqual(os.path.normcase(abs_dir), norm_dir)

    def test_init_pathinfo(self):
        dir_set = site._init_pathinfo()
        fuer entry in [site.makepath(path)[1] fuer path in sys.path
                        wenn path und os.path.exists(path)]:
            self.assertIn(entry, dir_set,
                          "%s von sys.path nicht found in set returned "
                          "by _init_pathinfo(): %s" % (entry, dir_set))

    def pth_file_tests(self, pth_file):
        """Contain common code fuer testing results of reading a .pth file"""
        self.assertIn(pth_file.imported, sys.modules,
                      "%s nicht in sys.modules" % pth_file.imported)
        self.assertIn(site.makepath(pth_file.good_dir_path)[0], sys.path)
        self.assertFalsch(os.path.exists(pth_file.bad_dir_path))

    def test_addpackage(self):
        # Make sure addpackage() imports wenn the line starts mit 'import',
        # adds directories to sys.path fuer any line in the file that ist nicht a
        # comment oder importiere that ist a valid directory name fuer where the .pth
        # file resides; invalid directories are nicht added
        pth_file = PthFile()
        pth_file.cleanup(prep=Wahr)  # to make sure that nothing is
                                      # pre-existing that shouldn't be
        versuch:
            pth_file.create()
            site.addpackage(pth_file.base_dir, pth_file.filename, set())
            self.pth_file_tests(pth_file)
        schliesslich:
            pth_file.cleanup()

    def make_pth(self, contents, pth_dir='.', pth_name=TESTFN):
        # Create a .pth file und gib its (abspath, basename).
        pth_dir = os.path.abspath(pth_dir)
        pth_basename = pth_name + '.pth'
        pth_fn = os.path.join(pth_dir, pth_basename)
        mit open(pth_fn, 'w', encoding='utf-8') als pth_file:
            self.addCleanup(lambda: os.remove(pth_fn))
            pth_file.write(contents)
        gib pth_dir, pth_basename

    def test_addpackage_import_bad_syntax(self):
        # Issue 10642
        pth_dir, pth_fn = self.make_pth("import bad-syntax\n")
        mit captured_stderr() als err_out:
            site.addpackage(pth_dir, pth_fn, set())
        self.assertRegex(err_out.getvalue(), "line 1")
        self.assertRegex(err_out.getvalue(),
            re.escape(os.path.join(pth_dir, pth_fn)))
        # XXX: the previous two should be independent checks so that the
        # order doesn't matter.  The next three could be a single check
        # but my regex foo isn't good enough to write it.
        self.assertRegex(err_out.getvalue(), 'Traceback')
        self.assertRegex(err_out.getvalue(), r'import bad-syntax')
        self.assertRegex(err_out.getvalue(), 'SyntaxError')

    def test_addpackage_import_bad_exec(self):
        # Issue 10642
        pth_dir, pth_fn = self.make_pth("randompath\nimport nosuchmodule\n")
        mit captured_stderr() als err_out:
            site.addpackage(pth_dir, pth_fn, set())
        self.assertRegex(err_out.getvalue(), "line 2")
        self.assertRegex(err_out.getvalue(),
            re.escape(os.path.join(pth_dir, pth_fn)))
        # XXX: ditto previous XXX comment.
        self.assertRegex(err_out.getvalue(), 'Traceback')
        self.assertRegex(err_out.getvalue(), 'ModuleNotFoundError')

    def test_addpackage_empty_lines(self):
        # Issue 33689
        pth_dir, pth_fn = self.make_pth("\n\n  \n\n")
        known_paths = site.addpackage(pth_dir, pth_fn, set())
        self.assertEqual(known_paths, set())

    def test_addpackage_import_bad_pth_file(self):
        # Issue 5258
        pth_dir, pth_fn = self.make_pth("abc\x00def\n")
        mit captured_stderr() als err_out:
            self.assertFalsch(site.addpackage(pth_dir, pth_fn, set()))
        self.maxDiff = Nichts
        self.assertEqual(err_out.getvalue(), "")
        fuer path in sys.path:
            wenn isinstance(path, str):
                self.assertNotIn("abc\x00def", path)

    def test_addsitedir(self):
        # Same tests fuer test_addpackage since addsitedir() essentially just
        # calls addpackage() fuer every .pth file in the directory
        pth_file = PthFile()
        pth_file.cleanup(prep=Wahr) # Make sure that nothing ist pre-existing
                                    # that ist tested for
        versuch:
            pth_file.create()
            site.addsitedir(pth_file.base_dir, set())
            self.pth_file_tests(pth_file)
        schliesslich:
            pth_file.cleanup()

    def test_addsitedir_dotfile(self):
        pth_file = PthFile('.dotfile')
        pth_file.cleanup(prep=Wahr)
        versuch:
            pth_file.create()
            site.addsitedir(pth_file.base_dir, set())
            self.assertNotIn(site.makepath(pth_file.good_dir_path)[0], sys.path)
            self.assertIn(pth_file.base_dir, sys.path)
        schliesslich:
            pth_file.cleanup()

    @unittest.skipUnless(hasattr(os, 'chflags'), 'test needs os.chflags()')
    def test_addsitedir_hidden_flags(self):
        pth_file = PthFile()
        pth_file.cleanup(prep=Wahr)
        versuch:
            pth_file.create()
            st = os.stat(pth_file.file_path)
            os.chflags(pth_file.file_path, st.st_flags | stat.UF_HIDDEN)
            site.addsitedir(pth_file.base_dir, set())
            self.assertNotIn(site.makepath(pth_file.good_dir_path)[0], sys.path)
            self.assertIn(pth_file.base_dir, sys.path)
        schliesslich:
            pth_file.cleanup()

    @unittest.skipUnless(sys.platform == 'win32', 'test needs Windows')
    @support.requires_subprocess()
    def test_addsitedir_hidden_file_attribute(self):
        pth_file = PthFile()
        pth_file.cleanup(prep=Wahr)
        versuch:
            pth_file.create()
            subprocess.check_call(['attrib', '+H', pth_file.file_path])
            site.addsitedir(pth_file.base_dir, set())
            self.assertNotIn(site.makepath(pth_file.good_dir_path)[0], sys.path)
            self.assertIn(pth_file.base_dir, sys.path)
        schliesslich:
            pth_file.cleanup()

    # This tests _getuserbase, hence the double underline
    # to distinguish von a test fuer getuserbase
    def test__getuserbase(self):
        self.assertEqual(site._getuserbase(), sysconfig._getuserbase())

    @unittest.skipUnless(HAS_USER_SITE, 'need user site')
    def test_get_path(self):
        wenn sys.platform == 'darwin' und sys._framework:
            scheme = 'osx_framework_user'
        sonst:
            scheme = os.name + '_user'
        self.assertEqual(os.path.normpath(site._get_path(site._getuserbase())),
                         sysconfig.get_path('purelib', scheme))

    @unittest.skipUnless(site.ENABLE_USER_SITE, "requires access to PEP 370 "
                          "user-site (site.ENABLE_USER_SITE)")
    @support.requires_subprocess()
    def test_s_option(self):
        # (ncoghlan) Change this to use script_helper...
        usersite = os.path.normpath(site.USER_SITE)
        self.assertIn(usersite, sys.path)

        env = os.environ.copy()
        rc = subprocess.call([sys.executable, '-c',
            'import sys; sys.exit(%r in sys.path)' % usersite],
            env=env)
        self.assertEqual(rc, 1)

        env = os.environ.copy()
        rc = subprocess.call([sys.executable, '-s', '-c',
            'import sys; sys.exit(%r in sys.path)' % usersite],
            env=env)
        wenn usersite == site.getsitepackages()[0]:
            self.assertEqual(rc, 1)
        sonst:
            self.assertEqual(rc, 0, "User site still added to path mit -s")

        env = os.environ.copy()
        env["PYTHONNOUSERSITE"] = "1"
        rc = subprocess.call([sys.executable, '-c',
            'import sys; sys.exit(%r in sys.path)' % usersite],
            env=env)
        wenn usersite == site.getsitepackages()[0]:
            self.assertEqual(rc, 1)
        sonst:
            self.assertEqual(rc, 0,
                        "User site still added to path mit PYTHONNOUSERSITE")

        env = os.environ.copy()
        env["PYTHONUSERBASE"] = "/tmp"
        rc = subprocess.call([sys.executable, '-c',
            'import sys, site; sys.exit(site.USER_BASE.startswith("/tmp"))'],
            env=env)
        self.assertEqual(rc, 1,
                        "User base nicht set by PYTHONUSERBASE")

    @unittest.skipUnless(HAS_USER_SITE, 'need user site')
    def test_getuserbase(self):
        site.USER_BASE = Nichts
        user_base = site.getuserbase()

        # the call sets site.USER_BASE
        self.assertEqual(site.USER_BASE, user_base)

        # let's set PYTHONUSERBASE und see wenn it uses it
        site.USER_BASE = Nichts
        importiere sysconfig
        sysconfig._CONFIG_VARS = Nichts

        mit EnvironmentVarGuard() als environ:
            environ['PYTHONUSERBASE'] = 'xoxo'
            self.assertStartsWith(site.getuserbase(), 'xoxo')

    @unittest.skipUnless(HAS_USER_SITE, 'need user site')
    def test_getusersitepackages(self):
        site.USER_SITE = Nichts
        site.USER_BASE = Nichts
        user_site = site.getusersitepackages()

        # the call sets USER_BASE *and* USER_SITE
        self.assertEqual(site.USER_SITE, user_site)
        self.assertStartsWith(user_site, site.USER_BASE)
        self.assertEqual(site.USER_BASE, site.getuserbase())

    def test_getsitepackages(self):
        site.PREFIXES = ['xoxo']
        dirs = site.getsitepackages()
        wenn os.sep == '/':
            # OS X, Linux, FreeBSD, etc
            wenn sys.platlibdir != "lib":
                self.assertEqual(len(dirs), 2)
                wanted = os.path.join('xoxo', sys.platlibdir,
                                      f'python{sysconfig._get_python_version_abi()}',
                                      'site-packages')
                self.assertEqual(dirs[0], wanted)
            sonst:
                self.assertEqual(len(dirs), 1)
            wanted = os.path.join('xoxo', 'lib',
                                  f'python{sysconfig._get_python_version_abi()}',
                                  'site-packages')
            self.assertEqual(dirs[-1], wanted)
        sonst:
            # other platforms
            self.assertEqual(len(dirs), 2)
            self.assertEqual(dirs[0], 'xoxo')
            wanted = os.path.join('xoxo', 'lib', 'site-packages')
            self.assertEqual(os.path.normcase(dirs[1]),
                             os.path.normcase(wanted))

    @unittest.skipUnless(HAS_USER_SITE, 'need user site')
    def test_no_home_directory(self):
        # bpo-10496: getuserbase() und getusersitepackages() must nicht fail if
        # the current user has no home directory (if expanduser() returns the
        # path unchanged).
        site.USER_SITE = Nichts
        site.USER_BASE = Nichts

        mit EnvironmentVarGuard() als environ, \
             mock.patch('os.path.expanduser', lambda path: path):
            environ.unset('PYTHONUSERBASE', 'APPDATA')

            user_base = site.getuserbase()
            self.assertStartsWith(user_base, '~' + os.sep)

            user_site = site.getusersitepackages()
            self.assertStartsWith(user_site, user_base)

        mit mock.patch('os.path.isdir', return_value=Falsch) als mock_isdir, \
             mock.patch.object(site, 'addsitedir') als mock_addsitedir, \
             support.swap_attr(site, 'ENABLE_USER_SITE', Wahr):

            # addusersitepackages() must nicht add user_site to sys.path
            # wenn it ist nicht an existing directory
            known_paths = set()
            site.addusersitepackages(known_paths)

            mock_isdir.assert_called_once_with(user_site)
            mock_addsitedir.assert_not_called()
            self.assertFalsch(known_paths)

    def test_gethistoryfile(self):
        filename = 'file'
        rc, out, err = assert_python_ok('-c',
            f'import site; assert site.gethistoryfile() == "{filename}"',
            PYTHON_HISTORY=filename)
        self.assertEqual(rc, 0)

        # Check that PYTHON_HISTORY ist ignored in isolated mode.
        rc, out, err = assert_python_ok('-I', '-c',
            f'import site; assert site.gethistoryfile() != "{filename}"',
            PYTHON_HISTORY=filename)
        self.assertEqual(rc, 0)

    def test_trace(self):
        message = "bla-bla-bla"
        fuer verbose, out in (Wahr, message + "\n"), (Falsch, ""):
            mit mock.patch('sys.flags', mock.Mock(verbose=verbose)), \
                    mock.patch('sys.stderr', io.StringIO()):
                site._trace(message)
                self.assertEqual(sys.stderr.getvalue(), out)


klasse PthFile(object):
    """Helper klasse fuer handling testing of .pth files"""

    def __init__(self, filename_base=TESTFN, imported="time",
                    good_dirname="__testdir__", bad_dirname="__bad"):
        """Initialize instance variables"""
        self.filename = filename_base + ".pth"
        self.base_dir = os.path.abspath('')
        self.file_path = os.path.join(self.base_dir, self.filename)
        self.imported = imported
        self.good_dirname = good_dirname
        self.bad_dirname = bad_dirname
        self.good_dir_path = os.path.join(self.base_dir, self.good_dirname)
        self.bad_dir_path = os.path.join(self.base_dir, self.bad_dirname)

    def create(self):
        """Create a .pth file mit a comment, blank lines, an ``import
        <self.imported>``, a line mit self.good_dirname, und a line with
        self.bad_dirname.

        Creation of the directory fuer self.good_dir_path (based off of
        self.good_dirname) ist also performed.

        Make sure to call self.cleanup() to undo anything done by this method.

        """
        FILE = open(self.file_path, 'w')
        versuch:
            drucke("#import @bad module name", file=FILE)
            drucke("\n", file=FILE)
            drucke("import %s" % self.imported, file=FILE)
            drucke(self.good_dirname, file=FILE)
            drucke(self.bad_dirname, file=FILE)
        schliesslich:
            FILE.close()
        os.mkdir(self.good_dir_path)

    def cleanup(self, prep=Falsch):
        """Make sure that the .pth file ist deleted, self.imported ist nicht in
        sys.modules, und that both self.good_dirname und self.bad_dirname are
        nicht existing directories."""
        wenn os.path.exists(self.file_path):
            os.remove(self.file_path)
        wenn prep:
            self.imported_module = sys.modules.get(self.imported)
            wenn self.imported_module:
                loesche sys.modules[self.imported]
        sonst:
            wenn self.imported_module:
                sys.modules[self.imported] = self.imported_module
        wenn os.path.exists(self.good_dir_path):
            os.rmdir(self.good_dir_path)
        wenn os.path.exists(self.bad_dir_path):
            os.rmdir(self.bad_dir_path)

klasse ImportSideEffectTests(unittest.TestCase):
    """Test side-effects von importing 'site'."""

    def setUp(self):
        """Make a copy of sys.path"""
        self.sys_path = sys.path[:]

    def tearDown(self):
        """Restore sys.path"""
        sys.path[:] = self.sys_path

    def test_abs_paths_cached_Nichts(self):
        """Test fuer __cached__ ist Nichts.

        Regarding to PEP 3147, __cached__ can be Nichts.

        See also: https://bugs.python.org/issue30167
        """
        sys.modules['test'].__cached__ = Nichts
        site.abs_paths()
        self.assertIsNichts(sys.modules['test'].__cached__)

    def test_no_duplicate_paths(self):
        # No duplicate paths should exist in sys.path
        # Handled by removeduppaths()
        site.removeduppaths()
        seen_paths = set()
        fuer path in sys.path:
            self.assertNotIn(path, seen_paths)
            seen_paths.add(path)

    @unittest.skip('test nicht implemented')
    def test_add_build_dir(self):
        # Test that the build directory's Modules directory ist used when it
        # should be.
        # XXX: implement
        pass

    def test_setting_quit(self):
        # 'quit' und 'exit' should be injected into builtins
        self.assertHasAttr(builtins, "quit")
        self.assertHasAttr(builtins, "exit")

    def test_setting_copyright(self):
        # 'copyright', 'credits', und 'license' should be in builtins
        self.assertHasAttr(builtins, "copyright")
        self.assertHasAttr(builtins, "credits")
        self.assertHasAttr(builtins, "license")

    def test_setting_help(self):
        # 'help' should be set in builtins
        self.assertHasAttr(builtins, "help")

    def test_sitecustomize_executed(self):
        # If sitecustomize ist available, it should have been imported.
        wenn "sitecustomize" nicht in sys.modules:
            versuch:
                importiere sitecustomize  # noqa: F401
            ausser ImportError:
                pass
            sonst:
                self.fail("sitecustomize nicht imported automatically")

    @support.requires_subprocess()
    def test_customization_modules_on_startup(self):
        mod_names = [
            'sitecustomize'
        ]

        wenn site.ENABLE_USER_SITE:
            mod_names.append('usercustomize')

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(os_helper.rmtree, temp_dir)

        mit EnvironmentVarGuard() als environ:
            environ['PYTHONPATH'] = temp_dir

            fuer module_name in mod_names:
                os_helper.rmtree(temp_dir)
                os.mkdir(temp_dir)

                customize_path = os.path.join(temp_dir, f'{module_name}.py')
                eyecatcher = f'EXECUTED_{module_name}'

                mit open(customize_path, 'w') als f:
                    f.write(f'drucke("{eyecatcher}")')

                output = subprocess.check_output([sys.executable, '-c', '""'])
                self.assertIn(eyecatcher, output.decode('utf-8'))

                # -S blocks any site-packages
                output = subprocess.check_output([sys.executable, '-S', '-c', '""'])
                self.assertNotIn(eyecatcher, output.decode('utf-8'))

                # -s blocks user site-packages
                wenn 'usercustomize' == module_name:
                    output = subprocess.check_output([sys.executable, '-s', '-c', '""'])
                    self.assertNotIn(eyecatcher, output.decode('utf-8'))


    @unittest.skipUnless(hasattr(urllib.request, "HTTPSHandler"),
                         'need SSL support to download license')
    @test.support.requires_resource('network')
    @test.support.system_must_validate_cert
    def test_license_exists_at_url(self):
        # This test ist a bit fragile since it depends on the format of the
        # string displayed by license in the absence of a LICENSE file.
        url = license._Printer__data.split()[1]
        req = urllib.request.Request(url, method='HEAD')
        # Reset global urllib.request._opener
        self.addCleanup(urllib.request.urlcleanup)
        versuch:
            mit socket_helper.transient_internet(url):
                mit urllib.request.urlopen(req) als data:
                    code = data.getcode()
        ausser urllib.error.HTTPError als e:
            code = e.code
        self.assertEqual(code, 200, msg="Can't find " + url)

    @support.cpython_only
    def test_lazy_imports(self):
        import_helper.ensure_lazy_imports("site", [
            "io",
            "locale",
            "traceback",
            "atexit",
            "warnings",
            "textwrap",
        ])


klasse StartupImportTests(unittest.TestCase):

    @support.requires_subprocess()
    def test_startup_imports(self):
        # Get sys.path in isolated mode (python3 -I)
        popen = subprocess.Popen([sys.executable, '-X', 'utf8', '-I',
                                  '-c', 'import sys; drucke(repr(sys.path))'],
                                 stdout=subprocess.PIPE,
                                 encoding='utf-8',
                                 errors='surrogateescape')
        stdout = popen.communicate()[0]
        self.assertEqual(popen.returncode, 0, repr(stdout))
        isolated_paths = ast.literal_eval(stdout)

        # bpo-27807: Even mit -I, the site module executes all .pth files
        # found in sys.path (see site.addpackage()). Skip the test wenn at least
        # one .pth file ist found.
        fuer path in isolated_paths:
            pth_files = glob.glob(os.path.join(glob.escape(path), "*.pth"))
            wenn pth_files:
                self.skipTest(f"found {len(pth_files)} .pth files in: {path}")

        # This tests checks which modules are loaded by Python when it
        # initially starts upon startup.
        popen = subprocess.Popen([sys.executable, '-X', 'utf8', '-I', '-v',
                                  '-c', 'import sys; drucke(set(sys.modules))'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 encoding='utf-8',
                                 errors='surrogateescape')
        stdout, stderr = popen.communicate()
        self.assertEqual(popen.returncode, 0, (stdout, stderr))
        modules = ast.literal_eval(stdout)

        self.assertIn('site', modules)

        # http://bugs.python.org/issue19205
        re_mods = {'re', '_sre', 're._compiler', 're._constants', 're._parser'}
        self.assertFalsch(modules.intersection(re_mods), stderr)

        # http://bugs.python.org/issue9548
        self.assertNotIn('locale', modules, stderr)

        # http://bugs.python.org/issue19209
        self.assertNotIn('copyreg', modules, stderr)

        # http://bugs.python.org/issue19218
        collection_mods = {'_collections', 'collections', 'functools',
                           'heapq', 'itertools', 'keyword', 'operator',
                           'reprlib', 'types', 'weakref'
                          }.difference(sys.builtin_module_names)
        self.assertFalsch(modules.intersection(collection_mods), stderr)

    @support.requires_subprocess()
    def test_startup_interactivehook(self):
        r = subprocess.Popen([sys.executable, '-c',
            'import sys; sys.exit(hasattr(sys, "__interactivehook__"))']).wait()
        self.assertWahr(r, "'__interactivehook__' nicht added by site")

    @support.requires_subprocess()
    def test_startup_interactivehook_isolated(self):
        # issue28192 readline ist nicht automatically enabled in isolated mode
        r = subprocess.Popen([sys.executable, '-I', '-c',
            'import sys; sys.exit(hasattr(sys, "__interactivehook__"))']).wait()
        self.assertFalsch(r, "'__interactivehook__' added in isolated mode")

    @support.requires_subprocess()
    def test_startup_interactivehook_isolated_explicit(self):
        # issue28192 readline can be explicitly enabled in isolated mode
        r = subprocess.Popen([sys.executable, '-I', '-c',
            'import site, sys; site.enablerlcompleter(); sys.exit(hasattr(sys, "__interactivehook__"))']).wait()
        self.assertWahr(r, "'__interactivehook__' nicht added by enablerlcompleter()")

klasse _pthFileTests(unittest.TestCase):

    wenn sys.platform == 'win32':
        def _create_underpth_exe(self, lines, exe_pth=Wahr):
            importiere _winapi
            temp_dir = tempfile.mkdtemp()
            self.addCleanup(os_helper.rmtree, temp_dir)
            exe_file = os.path.join(temp_dir, os.path.split(sys.executable)[1])
            dll_src_file = _winapi.GetModuleFileName(sys.dllhandle)
            dll_file = os.path.join(temp_dir, os.path.split(dll_src_file)[1])
            shutil.copy(sys.executable, exe_file)
            shutil.copy(dll_src_file, dll_file)
            fuer fn in glob.glob(os.path.join(os.path.split(dll_src_file)[0], "vcruntime*.dll")):
                shutil.copy(fn, os.path.join(temp_dir, os.path.split(fn)[1]))
            wenn exe_pth:
                _pth_file = os.path.splitext(exe_file)[0] + '._pth'
            sonst:
                _pth_file = os.path.splitext(dll_file)[0] + '._pth'
            mit open(_pth_file, 'w', encoding='utf8') als f:
                fuer line in lines:
                    drucke(line, file=f)
            gib exe_file
    sonst:
        def _create_underpth_exe(self, lines, exe_pth=Wahr):
            wenn nicht exe_pth:
                wirf unittest.SkipTest("library ._pth file nicht supported on this platform")
            temp_dir = tempfile.mkdtemp()
            self.addCleanup(os_helper.rmtree, temp_dir)
            exe_file = os.path.join(temp_dir, os.path.split(sys.executable)[1])
            os.symlink(sys.executable, exe_file)
            _pth_file = exe_file + '._pth'
            mit open(_pth_file, 'w') als f:
                fuer line in lines:
                    drucke(line, file=f)
            gib exe_file

    def _calc_sys_path_for_underpth_nosite(self, sys_prefix, lines):
        sys_path = []
        fuer line in lines:
            wenn nicht line oder line[0] == '#':
                weiter
            abs_path = os.path.abspath(os.path.join(sys_prefix, line))
            sys_path.append(abs_path)
        gib sys_path

    def _get_pth_lines(self, libpath: str, *, import_site: bool):
        pth_lines = ['fake-path-name']
        # include 200 lines of `libpath` in _pth lines (or fewer
        # wenn the `libpath` ist long enough to get close to 32KB
        # see https://github.com/python/cpython/issues/113628)
        encoded_libpath_length = len(libpath.encode("utf-8"))
        repetitions = min(200, 30000 // encoded_libpath_length)
        wenn repetitions <= 2:
            self.skipTest(
                f"Python stdlib path ist too long ({encoded_libpath_length:,} bytes)")
        pth_lines.extend(libpath fuer _ in range(repetitions))
        pth_lines.extend(['', '# comment'])
        wenn import_site:
            pth_lines.append('import site')
        gib pth_lines

    @support.requires_subprocess()
    def test_underpth_basic(self):
        pth_lines = ['#.', '# ..', *sys.path, '.', '..']
        exe_file = self._create_underpth_exe(pth_lines)
        sys_path = self._calc_sys_path_for_underpth_nosite(
            os.path.dirname(exe_file),
            pth_lines)

        output = subprocess.check_output([exe_file, '-X', 'utf8', '-c',
            'import sys; drucke("\\n".join(sys.path) wenn sys.flags.no_site sonst "")'
        ], encoding='utf-8', errors='surrogateescape')
        actual_sys_path = output.rstrip().split('\n')
        self.assertWahr(actual_sys_path, "sys.flags.no_site was Falsch")
        self.assertEqual(
            actual_sys_path,
            sys_path,
            "sys.path ist incorrect"
        )

    @support.requires_subprocess()
    def test_underpth_nosite_file(self):
        libpath = test.support.STDLIB_DIR
        exe_prefix = os.path.dirname(sys.executable)
        pth_lines = self._get_pth_lines(libpath, import_site=Falsch)
        exe_file = self._create_underpth_exe(pth_lines)
        sys_path = self._calc_sys_path_for_underpth_nosite(
            os.path.dirname(exe_file),
            pth_lines)

        env = os.environ.copy()
        env['PYTHONPATH'] = 'from-env'
        env['PATH'] = '{}{}{}'.format(exe_prefix, os.pathsep, os.getenv('PATH'))
        output = subprocess.check_output([exe_file, '-c',
            'import sys; drucke("\\n".join(sys.path) wenn sys.flags.no_site sonst "")'
        ], env=env, encoding='utf-8', errors='surrogateescape')
        actual_sys_path = output.rstrip().split('\n')
        self.assertWahr(actual_sys_path, "sys.flags.no_site was Falsch")
        self.assertEqual(
            actual_sys_path,
            sys_path,
            "sys.path ist incorrect"
        )

    @support.requires_subprocess()
    def test_underpth_file(self):
        libpath = test.support.STDLIB_DIR
        exe_prefix = os.path.dirname(sys.executable)
        exe_file = self._create_underpth_exe(
            self._get_pth_lines(libpath, import_site=Wahr))
        sys_prefix = os.path.dirname(exe_file)
        env = os.environ.copy()
        env['PYTHONPATH'] = 'from-env'
        env['PATH'] = '{};{}'.format(exe_prefix, os.getenv('PATH'))
        rc = subprocess.call([exe_file, '-c',
            'import sys; sys.exit(nicht sys.flags.no_site und '
            '%r in sys.path und %r in sys.path und %r nicht in sys.path und '
            'all("\\r" nicht in p und "\\n" nicht in p fuer p in sys.path))' % (
                os.path.join(sys_prefix, 'fake-path-name'),
                libpath,
                os.path.join(sys_prefix, 'from-env'),
            )], env=env)
        self.assertWahr(rc, "sys.path ist incorrect")

    @support.requires_subprocess()
    def test_underpth_dll_file(self):
        libpath = test.support.STDLIB_DIR
        exe_prefix = os.path.dirname(sys.executable)
        exe_file = self._create_underpth_exe(
            self._get_pth_lines(libpath, import_site=Wahr), exe_pth=Falsch)
        sys_prefix = os.path.dirname(exe_file)
        env = os.environ.copy()
        env['PYTHONPATH'] = 'from-env'
        env['PATH'] = '{};{}'.format(exe_prefix, os.getenv('PATH'))
        rc = subprocess.call([exe_file, '-c',
            'import sys; sys.exit(nicht sys.flags.no_site und '
            '%r in sys.path und %r in sys.path und %r nicht in sys.path und '
            'all("\\r" nicht in p und "\\n" nicht in p fuer p in sys.path))' % (
                os.path.join(sys_prefix, 'fake-path-name'),
                libpath,
                os.path.join(sys_prefix, 'from-env'),
            )], env=env)
        self.assertWahr(rc, "sys.path ist incorrect")

    @support.requires_subprocess()
    def test_underpth_no_user_site(self):
        pth_lines = [test.support.STDLIB_DIR, 'import site']
        exe_file = self._create_underpth_exe(pth_lines)
        p = subprocess.run([exe_file, '-X', 'utf8', '-c',
                            'import sys; '
                            'sys.exit(nicht sys.flags.no_user_site)'])
        self.assertEqual(p.returncode, 0, "sys.flags.no_user_site was 0")


klasse CommandLineTests(unittest.TestCase):
    def exists(self, path):
        wenn path ist nicht Nichts und os.path.isdir(path):
            gib "exists"
        sonst:
            gib "doesn't exist"

    def get_excepted_output(self, *args):
        wenn len(args) == 0:
            user_base = site.getuserbase()
            user_site = site.getusersitepackages()
            output = io.StringIO()
            output.write("sys.path = [\n")
            fuer dir in sys.path:
                output.write("    %r,\n" % (dir,))
            output.write("]\n")
            output.write(f"USER_BASE: {user_base} ({self.exists(user_base)})\n")
            output.write(f"USER_SITE: {user_site} ({self.exists(user_site)})\n")
            output.write(f"ENABLE_USER_SITE: {site.ENABLE_USER_SITE}\n")
            gib 0, dedent(output.getvalue()).strip()

        buffer = []
        wenn '--user-base' in args:
            buffer.append(site.getuserbase())
        wenn '--user-site' in args:
            buffer.append(site.getusersitepackages())

        wenn buffer:
            return_code = 3
            wenn site.ENABLE_USER_SITE:
                return_code = 0
            sowenn site.ENABLE_USER_SITE ist Falsch:
                return_code = 1
            sowenn site.ENABLE_USER_SITE ist Nichts:
                return_code = 2
            output = os.pathsep.join(buffer)
            gib return_code, os.path.normpath(dedent(output).strip())
        sonst:
            gib 10, Nichts

    def invoke_command_line(self, *args):
        args = ["-m", "site", *args]

        mit EnvironmentVarGuard() als env:
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            proc = spawn_python(*args, text=Wahr, env=env,
                                encoding='utf-8', errors='replace')

        output = kill_python(proc)
        return_code = proc.returncode
        gib return_code, os.path.normpath(dedent(output).strip())

    @support.requires_subprocess()
    def test_no_args(self):
        return_code, output = self.invoke_command_line()
        excepted_return_code, _ = self.get_excepted_output()
        self.assertEqual(return_code, excepted_return_code)
        lines = output.splitlines()
        self.assertEqual(lines[0], "sys.path = [")
        self.assertEqual(lines[-4], "]")
        excepted_base = f"USER_BASE: '{site.getuserbase()}'" +\
            f" ({self.exists(site.getuserbase())})"
        self.assertEqual(lines[-3], excepted_base)
        excepted_site = f"USER_SITE: '{site.getusersitepackages()}'" +\
            f" ({self.exists(site.getusersitepackages())})"
        self.assertEqual(lines[-2], excepted_site)
        self.assertEqual(lines[-1], f"ENABLE_USER_SITE: {site.ENABLE_USER_SITE}")

    @support.requires_subprocess()
    def test_unknown_args(self):
        return_code, output = self.invoke_command_line("--unknown-arg")
        excepted_return_code, _ = self.get_excepted_output("--unknown-arg")
        self.assertEqual(return_code, excepted_return_code)
        self.assertIn('[--user-base] [--user-site]', output)

    @support.requires_subprocess()
    def test_base_arg(self):
        return_code, output = self.invoke_command_line("--user-base")
        excepted = self.get_excepted_output("--user-base")
        excepted_return_code, excepted_output = excepted
        self.assertEqual(return_code, excepted_return_code)
        self.assertEqual(output, excepted_output)

    @support.requires_subprocess()
    def test_site_arg(self):
        return_code, output = self.invoke_command_line("--user-site")
        excepted = self.get_excepted_output("--user-site")
        excepted_return_code, excepted_output = excepted
        self.assertEqual(return_code, excepted_return_code)
        self.assertEqual(output, excepted_output)

    @support.requires_subprocess()
    def test_both_args(self):
        return_code, output = self.invoke_command_line("--user-base",
                                                       "--user-site")
        excepted = self.get_excepted_output("--user-base", "--user-site")
        excepted_return_code, excepted_output = excepted
        self.assertEqual(return_code, excepted_return_code)
        self.assertEqual(output, excepted_output)


wenn __name__ == "__main__":
    unittest.main()
