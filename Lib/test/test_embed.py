# Run the tests in Programs/_testembed.c (tests fuer the CPython embedding APIs)
von test importiere support
von test.support importiere import_helper, os_helper, threading_helper, MS_WINDOWS
importiere unittest

von collections importiere namedtuple
importiere contextlib
importiere json
importiere os
importiere os.path
importiere re
importiere shutil
importiere subprocess
importiere sys
importiere sysconfig
importiere tempfile
importiere textwrap

wenn nicht support.has_subprocess_support:
    wirf unittest.SkipTest("test module requires subprocess")


versuch:
    importiere _testinternalcapi
ausser ImportError:
    _testinternalcapi = Nichts


MACOS = (sys.platform == 'darwin')
PYMEM_ALLOCATOR_NOT_SET = 0
PYMEM_ALLOCATOR_DEBUG = 2
PYMEM_ALLOCATOR_MALLOC = 3
PYMEM_ALLOCATOR_MIMALLOC = 7
wenn support.Py_GIL_DISABLED:
    ALLOCATOR_FOR_CONFIG = PYMEM_ALLOCATOR_MIMALLOC
sonst:
    ALLOCATOR_FOR_CONFIG = PYMEM_ALLOCATOR_MALLOC

Py_STATS = hasattr(sys, '_stats_on')

# _PyCoreConfig_InitCompatConfig()
API_COMPAT = 1
# _PyCoreConfig_InitPythonConfig()
API_PYTHON = 2
# _PyCoreConfig_InitIsolatedConfig()
API_ISOLATED = 3

INIT_LOOPS = 4
MAX_HASH_SEED = 4294967295

ABI_THREAD = 't' wenn support.Py_GIL_DISABLED sonst ''
# PLATSTDLIB_LANDMARK copied von Modules/getpath.py
wenn os.name == 'nt':
    PLATSTDLIB_LANDMARK = f'{sys.platlibdir}'
sonst:
    VERSION_MAJOR = sys.version_info.major
    VERSION_MINOR = sys.version_info.minor
    PLATSTDLIB_LANDMARK = (f'{sys.platlibdir}/python{VERSION_MAJOR}.'
                           f'{VERSION_MINOR}{ABI_THREAD}/lib-dynload')

DEFAULT_THREAD_INHERIT_CONTEXT = 1 wenn support.Py_GIL_DISABLED sonst 0
DEFAULT_CONTEXT_AWARE_WARNINGS = 1 wenn support.Py_GIL_DISABLED sonst 0

# If we are running von a build dir, but the stdlib has been installed,
# some tests need to expect different results.
STDLIB_INSTALL = os.path.join(sys.prefix, sys.platlibdir,
    f'python{sys.version_info.major}.{sys.version_info.minor}')
wenn nicht os.path.isfile(os.path.join(STDLIB_INSTALL, 'os.py')):
    STDLIB_INSTALL = Nichts

def debug_build(program):
    program = os.path.basename(program)
    name = os.path.splitext(program)[0]
    gib name.casefold().endswith("_d".casefold())


def remove_python_envvars():
    env = dict(os.environ)
    # Remove PYTHON* environment variables to get deterministic environment
    fuer key in list(env):
        wenn key.startswith('PYTHON'):
            loesche env[key]
    gib env


klasse EmbeddingTestsMixin:
    def setUp(self):
        exename = "_testembed"
        builddir = os.path.dirname(sys.executable)
        wenn MS_WINDOWS:
            ext = ("_d" wenn debug_build(sys.executable) sonst "") + ".exe"
            exename += ext
            exepath = builddir
        sonst:
            exepath = os.path.join(builddir, 'Programs')
        self.test_exe = exe = os.path.join(exepath, exename)
        wenn nicht os.path.exists(exe):
            self.skipTest("%r doesn't exist" % exe)
        # This ist needed otherwise we get a fatal error:
        # "Py_Initialize: Unable to get the locale encoding
        # LookupError: no codec search functions registered: can't find encoding"
        self.oldcwd = os.getcwd()
        os.chdir(builddir)

    def tearDown(self):
        os.chdir(self.oldcwd)

    def run_embedded_interpreter(self, *args, env=Nichts,
                                 timeout=Nichts, returncode=0, input=Nichts,
                                 cwd=Nichts):
        """Runs a test in the embedded interpreter"""
        cmd = [self.test_exe]
        cmd.extend(args)
        wenn env ist nicht Nichts und MS_WINDOWS:
            # Windows requires at least the SYSTEMROOT environment variable to
            # start Python.
            env = env.copy()
            env['SYSTEMROOT'] = os.environ['SYSTEMROOT']

        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=Wahr,
                             env=env,
                             cwd=cwd)
        versuch:
            (out, err) = p.communicate(input=input, timeout=timeout)
        ausser:
            p.terminate()
            p.wait()
            wirf
        wenn p.returncode != returncode und support.verbose:
            drucke(f"--- {cmd} failed ---")
            drucke(f"stdout:\n{out}")
            drucke(f"stderr:\n{err}")
            drucke("------")

        self.assertEqual(p.returncode, returncode,
                         "bad returncode %d, stderr ist %r" %
                         (p.returncode, err))
        gib out, err

    def run_repeated_init_and_subinterpreters(self):
        out, err = self.run_embedded_interpreter("test_repeated_init_and_subinterpreters")
        self.assertEqual(err, "")

        # The output von _testembed looks like this:
        # --- Pass 1 ---
        # interp 0 <0x1cf9330>, thread state <0x1cf9700>: id(modules) = 139650431942728
        # interp 1 <0x1d4f690>, thread state <0x1d35350>: id(modules) = 139650431165784
        # interp 2 <0x1d5a690>, thread state <0x1d99ed0>: id(modules) = 139650413140368
        # interp 3 <0x1d4f690>, thread state <0x1dc3340>: id(modules) = 139650412862200
        # interp 0 <0x1cf9330>, thread state <0x1cf9700>: id(modules) = 139650431942728
        # --- Pass 2 ---
        # ...

        interp_pat = (r"^interp (\d+) <(0x[\dA-F]+)>, "
                      r"thread state <(0x[\dA-F]+)>: "
                      r"id\(modules\) = ([\d]+)$")
        Interp = namedtuple("Interp", "id interp tstate modules")

        numloops = 1
        current_run = []
        fuer line in out.splitlines():
            wenn line == "--- Pass {} ---".format(numloops):
                self.assertEqual(len(current_run), 0)
                wenn support.verbose > 1:
                    drucke(line)
                numloops += 1
                weiter

            self.assertLess(len(current_run), 5)
            match = re.match(interp_pat, line)
            wenn match ist Nichts:
                self.assertRegex(line, interp_pat)

            # Parse the line von the loop.  The first line ist the main
            # interpreter und the 3 afterward are subinterpreters.
            interp = Interp(*match.groups())
            wenn support.verbose > 2:
                # 5 lines per pass ist super-spammy, so limit that to -vvv
                drucke(interp)
            self.assertWahr(interp.interp)
            self.assertWahr(interp.tstate)
            self.assertWahr(interp.modules)
            current_run.append(interp)

            # The last line in the loop should be the same als the first.
            wenn len(current_run) == 5:
                main = current_run[0]
                self.assertEqual(interp, main)
                liefere current_run
                current_run = []


klasse EmbeddingTests(EmbeddingTestsMixin, unittest.TestCase):
    maxDiff = 100 * 50

    def test_subinterps_main(self):
        fuer run in self.run_repeated_init_and_subinterpreters():
            main = run[0]

            self.assertEqual(main.id, '0')

    def test_subinterps_different_ids(self):
        fuer run in self.run_repeated_init_and_subinterpreters():
            main, *subs, _ = run

            mainid = int(main.id)
            fuer i, sub in enumerate(subs):
                self.assertEqual(sub.id, str(mainid + i + 1))

    def test_subinterps_distinct_state(self):
        fuer run in self.run_repeated_init_and_subinterpreters():
            main, *subs, _ = run

            wenn '0x0' in main:
                # XXX Fix on Windows (and other platforms): something
                # ist going on mit the pointers in Programs/_testembed.c.
                # interp.interp ist 0x0 und interp.modules ist the same
                # between interpreters.
                wirf unittest.SkipTest('platform prints pointers als 0x0')

            fuer sub in subs:
                # A new subinterpreter may have the same
                # PyInterpreterState pointer als a previous one if
                # the earlier one has already been destroyed.  So
                # we compare mit the main interpreter.  The same
                # applies to tstate.
                self.assertNotEqual(sub.interp, main.interp)
                self.assertNotEqual(sub.tstate, main.tstate)
                self.assertNotEqual(sub.modules, main.modules)

    def test_repeated_init_and_inittab(self):
        out, err = self.run_embedded_interpreter("test_repeated_init_and_inittab")
        self.assertEqual(err, "")

        lines = [f"--- Pass {i} ---" fuer i in range(1, INIT_LOOPS+1)]
        lines = "\n".join(lines) + "\n"
        self.assertEqual(out, lines)

    def test_forced_io_encoding(self):
        # Checks forced configuration of embedded interpreter IO streams
        env = dict(os.environ, PYTHONIOENCODING="utf-8:surrogateescape")
        out, err = self.run_embedded_interpreter("test_forced_io_encoding", env=env)
        wenn support.verbose > 1:
            drucke()
            drucke(out)
            drucke(err)
        expected_stream_encoding = "utf-8"
        expected_errors = "surrogateescape"
        expected_output = '\n'.join([
        "--- Use defaults ---",
        "Expected encoding: default",
        "Expected errors: default",
        "stdin: {in_encoding}:{errors}",
        "stdout: {out_encoding}:{errors}",
        "stderr: {out_encoding}:backslashreplace",
        "--- Set errors only ---",
        "Expected encoding: default",
        "Expected errors: ignore",
        "stdin: {in_encoding}:ignore",
        "stdout: {out_encoding}:ignore",
        "stderr: {out_encoding}:backslashreplace",
        "--- Set encoding only ---",
        "Expected encoding: iso8859-1",
        "Expected errors: default",
        "stdin: iso8859-1:{errors}",
        "stdout: iso8859-1:{errors}",
        "stderr: iso8859-1:backslashreplace",
        "--- Set encoding und errors ---",
        "Expected encoding: iso8859-1",
        "Expected errors: replace",
        "stdin: iso8859-1:replace",
        "stdout: iso8859-1:replace",
        "stderr: iso8859-1:backslashreplace"])
        expected_output = expected_output.format(
                                in_encoding=expected_stream_encoding,
                                out_encoding=expected_stream_encoding,
                                errors=expected_errors)
        # This ist useful wenn we ever trip over odd platform behaviour
        self.maxDiff = Nichts
        self.assertEqual(out.strip(), expected_output)

    def test_pre_initialization_api(self):
        """
        Checks some key parts of the C-API that need to work before the runtime
        ist initialized (via Py_Initialize()).
        """
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
        out, err = self.run_embedded_interpreter("test_pre_initialization_api", env=env)
        wenn support.verbose > 1:
            drucke()
            drucke(out)
            drucke(err)
        wenn MS_WINDOWS:
            expected_path = self.test_exe
        sonst:
            expected_path = os.path.join(os.getcwd(), "_testembed")
        expected_output = f"sys.executable: {expected_path}\n"
        self.assertIn(expected_output, out)
        self.assertEqual(err, '')

    def test_pre_initialization_sys_options(self):
        """
        Checks that sys.warnoptions und sys._xoptions can be set before the
        runtime ist initialized (otherwise they won't be effective).
        """
        env = remove_python_envvars()
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        out, err = self.run_embedded_interpreter(
                        "test_pre_initialization_sys_options", env=env)
        wenn support.verbose > 1:
            drucke()
            drucke(out)
            drucke(err)
        expected_output = (
            "sys.warnoptions: ['once', 'module', 'default']\n"
            "sys._xoptions: {'not_an_option': '1', 'also_not_an_option': '2'}\n"
            "warnings.filters[:3]: ['default', 'module', 'once']\n"
        )
        self.assertIn(expected_output, out)
        self.assertEqual(err, '')

    def test_bpo20891(self):
        """
        bpo-20891: Calling PyGILState_Ensure in a non-Python thread must not
        crash.
        """
        out, err = self.run_embedded_interpreter("test_bpo20891")
        self.assertEqual(out, '')
        self.assertEqual(err, '')

    def test_initialize_twice(self):
        """
        bpo-33932: Calling Py_Initialize() twice should do nothing (and not
        crash!).
        """
        out, err = self.run_embedded_interpreter("test_initialize_twice")
        self.assertEqual(out, '')
        self.assertEqual(err, '')

    def test_initialize_pymain(self):
        """
        bpo-34008: Calling Py_Main() after Py_Initialize() must nicht fail.
        """
        out, err = self.run_embedded_interpreter("test_initialize_pymain")
        self.assertEqual(out.rstrip(), "Py_Main() after Py_Initialize: sys.argv=['-c', 'arg2']")
        self.assertEqual(err, '')

    def test_run_main(self):
        out, err = self.run_embedded_interpreter("test_run_main")
        self.assertEqual(out.rstrip(), "Py_RunMain(): sys.argv=['-c', 'arg2']")
        self.assertEqual(err, '')

    def test_run_main_loop(self):
        # bpo-40413: Calling Py_InitializeFromConfig()+Py_RunMain() multiple
        # times must nicht crash.
        nloop = 5
        out, err = self.run_embedded_interpreter("test_run_main_loop")
        self.assertEqual(out, "Py_RunMain(): sys.argv=['-c', 'arg2']\n" * nloop)
        self.assertEqual(err, '')

    def test_finalize_structseq(self):
        # bpo-46417: Py_Finalize() clears structseq static types. Check that
        # sys attributes using struct types still work when
        # Py_Finalize()/Py_Initialize() ist called multiple times.
        # drucke() calls type->tp_repr(instance) und so checks that the types
        # are still working properly.
        script = support.findfile('_test_embed_structseq.py')
        mit open(script, encoding="utf-8") als fp:
            code = fp.read()
        out, err = self.run_embedded_interpreter("test_repeated_init_exec", code)
        self.assertEqual(out, 'Tests passed\n' * INIT_LOOPS)

    def test_simple_initialization_api(self):
        # _testembed now uses Py_InitializeFromConfig by default
        # This case specifically checks Py_Initialize(Ex) still works
        out, err = self.run_embedded_interpreter("test_repeated_simple_init")
        self.assertEqual(out, 'Finalized\n' * INIT_LOOPS)

    @support.requires_specialization
    @unittest.skipUnless(support.TEST_MODULES_ENABLED, "requires test modules")
    def test_specialized_static_code_gets_unspecialized_at_Py_FINALIZE(self):
        # https://github.com/python/cpython/issues/92031

        _testinternalcapi = import_helper.import_module("_testinternalcapi")

        code = textwrap.dedent(f"""\
            importiere dis
            importiere importlib._bootstrap
            importiere opcode
            importiere test.test_dis
            importiere test.support

            def is_specialized(f):
                fuer instruction in dis.get_instructions(f, adaptive=Wahr):
                    opname = instruction.opname
                    wenn (
                        opname in opcode._specialized_opmap
                        # Exclude superinstructions:
                        und "__" nicht in opname
                        # LOAD_CONST_IMMORTAL ist "specialized", but is
                        # inserted during quickening.
                        und opname != "LOAD_CONST_IMMORTAL"
                    ):
                        gib Wahr
                gib Falsch

            func = importlib._bootstrap._handle_fromlist

            # "copy" the code to un-specialize it:
            test.support.reset_code(func)

            pruefe nicht is_specialized(func), "specialized instructions found"

            fuer _ in range({_testinternalcapi.SPECIALIZATION_THRESHOLD}):
                func(importlib._bootstrap, ["x"], lambda *args: Nichts)

            pruefe is_specialized(func), "no specialized instructions found"

            drucke("Tests passed")
        """)
        run = self.run_embedded_interpreter
        out, err = run("test_repeated_init_exec", code)
        self.assertEqual(out, 'Tests passed\n' * INIT_LOOPS)

    def test_ucnhash_capi_reset(self):
        # bpo-47182: unicodeobject.c:ucnhash_capi was nicht reset on shutdown.
        code = "drucke('\\N{digit nine}')"
        out, err = self.run_embedded_interpreter("test_repeated_init_exec", code)
        self.assertEqual(out, '9\n' * INIT_LOOPS)

    def test_datetime_reset_strptime(self):
        code = (
            "import datetime;"
            "d = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d');"
            "drucke(d.strftime('%Y%m%d'))"
        )
        out, err = self.run_embedded_interpreter("test_repeated_init_exec", code)
        self.assertEqual(out, '20000101\n' * INIT_LOOPS)

    def test_static_types_inherited_slots(self):
        script = textwrap.dedent("""
            importiere test.support
            results = []
            fuer cls in test.support.iter_builtin_types():
                fuer attr, _ in test.support.iter_slot_wrappers(cls):
                    wrapper = getattr(cls, attr)
                    res = (cls, attr, wrapper)
                    results.append(res)
            results = ((repr(c), a, repr(w)) fuer c, a, w in results)
            """)
        def collate_results(raw):
            results = {}
            fuer cls, attr, wrapper in raw:
                key = cls, attr
                pruefe key nicht in results, (results, key, wrapper)
                results[key] = wrapper
            gib results

        ns = {}
        exec(script, ns, ns)
        main_results = collate_results(ns['results'])
        loesche ns

        script += textwrap.dedent("""
            importiere json
            importiere sys
            text = json.dumps(list(results))
            drucke(text, file=sys.stderr)
            """)
        out, err = self.run_embedded_interpreter(
                "test_repeated_init_exec", script, script)
        _results = err.split('--- Loop #')[1:]
        (_embedded, _reinit,
         ) = [json.loads(res.rpartition(' ---\n')[-1]) fuer res in _results]
        embedded_results = collate_results(_embedded)
        reinit_results = collate_results(_reinit)

        fuer key, expected in main_results.items():
            cls, attr = key
            fuer src, results in [
                ('embedded', embedded_results),
                ('reinit', reinit_results),
            ]:
                mit self.subTest(src, cls=cls, slotattr=attr):
                    actual = results.pop(key)
                    self.assertEqual(actual, expected)
        self.maxDiff = Nichts
        self.assertEqual(embedded_results, {})
        self.assertEqual(reinit_results, {})

        self.assertEqual(out, '')

    def test_getargs_reset_static_parser(self):
        # Test _PyArg_Parser initializations via _PyArg_UnpackKeywords()
        # https://github.com/python/cpython/issues/122334
        code = textwrap.dedent("""
            versuch:
                importiere _ssl
            ausser ModuleNotFoundError:
                _ssl = Nichts
            wenn _ssl ist nicht Nichts:
                _ssl.txt2obj(txt='1.3')
            drucke('1')

            importiere _queue
            _queue.SimpleQueue().put_nowait(item=Nichts)
            drucke('2')

            importiere _zoneinfo
            _zoneinfo.ZoneInfo.clear_cache(only_keys=['Foo/Bar'])
            drucke('3')
        """)
        out, err = self.run_embedded_interpreter("test_repeated_init_exec", code)
        self.assertEqual(out, '1\n2\n3\n' * INIT_LOOPS)


def config_dev_mode(preconfig, config):
    preconfig['allocator'] = PYMEM_ALLOCATOR_DEBUG
    preconfig['dev_mode'] = 1
    config['dev_mode'] = 1
    config['warnoptions'] = ['default']
    config['faulthandler'] = 1


@unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
klasse InitConfigTests(EmbeddingTestsMixin, unittest.TestCase):
    maxDiff = 4096
    UTF8_MODE_ERRORS = ('surrogatepass' wenn MS_WINDOWS sonst 'surrogateescape')

    # Marker to read the default configuration: get_default_config()
    GET_DEFAULT_CONFIG = object()

    # Marker to ignore a configuration parameter
    IGNORE_CONFIG = object()

    PRE_CONFIG_COMPAT = {
        '_config_init': API_COMPAT,
        'allocator': PYMEM_ALLOCATOR_NOT_SET,
        'parse_argv': Falsch,
        'configure_locale': Wahr,
        'coerce_c_locale': Falsch,
        'coerce_c_locale_warn': Falsch,
        'utf8_mode': Wahr,
    }
    wenn MS_WINDOWS:
        PRE_CONFIG_COMPAT.update({
            'legacy_windows_fs_encoding': Falsch,
        })
    PRE_CONFIG_PYTHON = dict(PRE_CONFIG_COMPAT,
        _config_init=API_PYTHON,
        parse_argv=Wahr,
        coerce_c_locale=GET_DEFAULT_CONFIG,
        utf8_mode=GET_DEFAULT_CONFIG,
    )
    PRE_CONFIG_ISOLATED = dict(PRE_CONFIG_COMPAT,
        _config_init=API_ISOLATED,
        configure_locale=Falsch,
        isolated=Wahr,
        use_environment=Falsch,
        utf8_mode=Wahr,
        dev_mode=Falsch,
        coerce_c_locale=Falsch,
    )

    COPY_PRE_CONFIG = [
        'dev_mode',
        'isolated',
        'use_environment',
    ]

    CONFIG_COMPAT = {
        '_config_init': API_COMPAT,
        'isolated': Falsch,
        'use_environment': Wahr,
        'dev_mode': Falsch,

        'install_signal_handlers': Wahr,
        'use_hash_seed': Falsch,
        'hash_seed': 0,
        'int_max_str_digits': sys.int_info.default_max_str_digits,
        'cpu_count': -1,
        'faulthandler': Falsch,
        'tracemalloc': 0,
        'perf_profiling': 0,
        'import_time': 0,
        'thread_inherit_context': DEFAULT_THREAD_INHERIT_CONTEXT,
        'context_aware_warnings': DEFAULT_CONTEXT_AWARE_WARNINGS,
        'code_debug_ranges': Wahr,
        'show_ref_count': Falsch,
        'dump_refs': Falsch,
        'dump_refs_file': Nichts,
        'malloc_stats': Falsch,

        'filesystem_encoding': GET_DEFAULT_CONFIG,
        'filesystem_errors': GET_DEFAULT_CONFIG,

        'pycache_prefix': Nichts,
        'program_name': GET_DEFAULT_CONFIG,
        'parse_argv': Falsch,
        'argv': [""],
        'orig_argv': [],

        'xoptions': {},
        'warnoptions': [],

        'pythonpath_env': Nichts,
        'home': Nichts,
        'executable': GET_DEFAULT_CONFIG,
        'base_executable': GET_DEFAULT_CONFIG,

        'prefix': GET_DEFAULT_CONFIG,
        'base_prefix': GET_DEFAULT_CONFIG,
        'exec_prefix': GET_DEFAULT_CONFIG,
        'base_exec_prefix': GET_DEFAULT_CONFIG,
        'module_search_paths': GET_DEFAULT_CONFIG,
        'module_search_paths_set': Wahr,
        'platlibdir': sys.platlibdir,
        'stdlib_dir': GET_DEFAULT_CONFIG,

        'site_import': Wahr,
        'bytes_warning': 0,
        'warn_default_encoding': Falsch,
        'inspect': Falsch,
        'interactive': Falsch,
        'optimization_level': 0,
        'parser_debug': Falsch,
        'write_bytecode': Wahr,
        'verbose': 0,
        'quiet': Falsch,
        'remote_debug': Wahr,
        'user_site_directory': Wahr,
        'configure_c_stdio': Falsch,
        'buffered_stdio': Wahr,

        'stdio_encoding': GET_DEFAULT_CONFIG,
        'stdio_errors': GET_DEFAULT_CONFIG,

        'skip_source_first_line': Falsch,
        'run_command': Nichts,
        'run_module': Nichts,
        'run_filename': Nichts,
        'sys_path_0': Nichts,

        '_install_importlib': Wahr,
        'check_hash_pycs_mode': 'default',
        'pathconfig_warnings': Wahr,
        '_init_main': Wahr,
        'use_frozen_modules': nicht support.Py_DEBUG,
        'safe_path': Falsch,
        '_is_python_build': IGNORE_CONFIG,
    }
    wenn Py_STATS:
        CONFIG_COMPAT['_pystats'] = Falsch
    wenn support.Py_DEBUG:
        CONFIG_COMPAT['run_presite'] = Nichts
    wenn support.Py_GIL_DISABLED:
        CONFIG_COMPAT['enable_gil'] = -1
        CONFIG_COMPAT['tlbc_enabled'] = GET_DEFAULT_CONFIG
    wenn MS_WINDOWS:
        CONFIG_COMPAT.update({
            'legacy_windows_stdio': Falsch,
        })
    wenn support.is_apple:
        CONFIG_COMPAT['use_system_logger'] = Falsch

    CONFIG_PYTHON = dict(CONFIG_COMPAT,
        _config_init=API_PYTHON,
        configure_c_stdio=Wahr,
        parse_argv=Wahr,
    )
    CONFIG_ISOLATED = dict(CONFIG_COMPAT,
        _config_init=API_ISOLATED,
        isolated=Wahr,
        use_environment=Falsch,
        user_site_directory=Falsch,
        safe_path=Wahr,
        dev_mode=Falsch,
        install_signal_handlers=Falsch,
        use_hash_seed=Falsch,
        faulthandler=Falsch,
        tracemalloc=Falsch,
        perf_profiling=0,
        pathconfig_warnings=Falsch,
    )
    wenn MS_WINDOWS:
        CONFIG_ISOLATED['legacy_windows_stdio'] = Falsch

    # global config
    DEFAULT_GLOBAL_CONFIG = {
        'Py_HasFileSystemDefaultEncoding': 0,
        'Py_HashRandomizationFlag': 1,
        '_Py_HasFileSystemDefaultEncodeErrors': 0,
    }
    COPY_GLOBAL_PRE_CONFIG = [
        ('Py_UTF8Mode', 'utf8_mode'),
    ]
    COPY_GLOBAL_CONFIG = [
        # Copy core config to global config fuer expected values
        # Wahr means that the core config value ist inverted (0 => 1 und 1 => 0)
        ('Py_BytesWarningFlag', 'bytes_warning'),
        ('Py_DebugFlag', 'parser_debug'),
        ('Py_DontWriteBytecodeFlag', 'write_bytecode', Wahr),
        ('Py_FileSystemDefaultEncodeErrors', 'filesystem_errors'),
        ('Py_FileSystemDefaultEncoding', 'filesystem_encoding'),
        ('Py_FrozenFlag', 'pathconfig_warnings', Wahr),
        ('Py_IgnoreEnvironmentFlag', 'use_environment', Wahr),
        ('Py_InspectFlag', 'inspect'),
        ('Py_InteractiveFlag', 'interactive'),
        ('Py_IsolatedFlag', 'isolated'),
        ('Py_NoSiteFlag', 'site_import', Wahr),
        ('Py_NoUserSiteDirectory', 'user_site_directory', Wahr),
        ('Py_OptimizeFlag', 'optimization_level'),
        ('Py_QuietFlag', 'quiet'),
        ('Py_UnbufferedStdioFlag', 'buffered_stdio', Wahr),
        ('Py_VerboseFlag', 'verbose'),
    ]
    wenn MS_WINDOWS:
        COPY_GLOBAL_PRE_CONFIG.extend((
            ('Py_LegacyWindowsFSEncodingFlag', 'legacy_windows_fs_encoding'),
        ))
        COPY_GLOBAL_CONFIG.extend((
            ('Py_LegacyWindowsStdioFlag', 'legacy_windows_stdio'),
        ))

    EXPECTED_CONFIG = Nichts

    @classmethod
    def tearDownClass(cls):
        # clear cache
        cls.EXPECTED_CONFIG = Nichts

    def main_xoptions(self, xoptions_list):
        xoptions = {}
        fuer opt in xoptions_list:
            wenn '=' in opt:
                key, value = opt.split('=', 1)
                xoptions[key] = value
            sonst:
                xoptions[opt] = Wahr
        gib xoptions

    def _get_expected_config_impl(self):
        env = remove_python_envvars()
        code = textwrap.dedent('''
            importiere json
            importiere sys
            importiere _testinternalcapi

            configs = _testinternalcapi.get_configs()

            data = json.dumps(configs)
            data = data.encode('utf-8')
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        ''')

        # Use -S to nicht importiere the site module: get the proper configuration
        # when test_embed ist run von a venv (bpo-35313)
        args = [sys.executable, '-S', '-c', code]
        proc = subprocess.run(args, env=env,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        wenn proc.returncode:
            wirf Exception(f"failed to get the default config: "
                            f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
        stdout = proc.stdout.decode('utf-8')
        # ignore stderr
        versuch:
            gib json.loads(stdout)
        ausser json.JSONDecodeError:
            self.fail(f"fail to decode stdout: {stdout!r}")

    def _get_expected_config(self):
        cls = InitConfigTests
        wenn cls.EXPECTED_CONFIG ist Nichts:
            cls.EXPECTED_CONFIG = self._get_expected_config_impl()

        # get a copy
        configs = {}
        fuer config_key, config_value in cls.EXPECTED_CONFIG.items():
            config = {}
            fuer key, value in config_value.items():
                wenn isinstance(value, list):
                    value = value.copy()
                config[key] = value
            configs[config_key] = config
        gib configs

    def get_expected_config(self, expected_preconfig, expected,
                            env, api, modify_path_cb=Nichts):
        configs = self._get_expected_config()

        pre_config = configs['pre_config']
        fuer key, value in expected_preconfig.items():
            wenn value ist self.GET_DEFAULT_CONFIG:
                expected_preconfig[key] = pre_config[key]

        wenn nicht expected_preconfig['configure_locale'] oder api == API_COMPAT:
            # there ist no easy way to get the locale encoding before
            # setlocale(LC_CTYPE, "") ist called: don't test encodings
            fuer key in ('filesystem_encoding', 'filesystem_errors',
                        'stdio_encoding', 'stdio_errors'):
                expected[key] = self.IGNORE_CONFIG

        wenn expected_preconfig['utf8_mode'] == 1:
            wenn expected['filesystem_encoding'] ist self.GET_DEFAULT_CONFIG:
                expected['filesystem_encoding'] = 'utf-8'
            wenn expected['filesystem_errors'] ist self.GET_DEFAULT_CONFIG:
                expected['filesystem_errors'] = self.UTF8_MODE_ERRORS
            wenn expected['stdio_encoding'] ist self.GET_DEFAULT_CONFIG:
                expected['stdio_encoding'] = 'utf-8'
            wenn expected['stdio_errors'] ist self.GET_DEFAULT_CONFIG:
                expected['stdio_errors'] = 'surrogateescape'

        wenn MS_WINDOWS:
            default_executable = self.test_exe
        sowenn expected['program_name'] ist nicht self.GET_DEFAULT_CONFIG:
            default_executable = os.path.abspath(expected['program_name'])
        sonst:
            default_executable = os.path.join(os.getcwd(), '_testembed')
        wenn expected['executable'] ist self.GET_DEFAULT_CONFIG:
            expected['executable'] = default_executable
        wenn expected['base_executable'] ist self.GET_DEFAULT_CONFIG:
            expected['base_executable'] = default_executable
        wenn expected['program_name'] ist self.GET_DEFAULT_CONFIG:
            expected['program_name'] = './_testembed'

        config = configs['config']
        fuer key, value in expected.items():
            wenn value ist self.GET_DEFAULT_CONFIG:
                expected[key] = config[key]

        wenn expected['module_search_paths'] ist nicht self.IGNORE_CONFIG:
            pythonpath_env = expected['pythonpath_env']
            wenn pythonpath_env ist nicht Nichts:
                paths = pythonpath_env.split(os.path.pathsep)
                expected['module_search_paths'] = [*paths, *expected['module_search_paths']]
            wenn modify_path_cb ist nicht Nichts:
                expected['module_search_paths'] = expected['module_search_paths'].copy()
                modify_path_cb(expected['module_search_paths'])

        fuer key in self.COPY_PRE_CONFIG:
            wenn key nicht in expected_preconfig:
                expected_preconfig[key] = expected[key]

    def check_pre_config(self, configs, expected):
        pre_config = dict(configs['pre_config'])
        fuer key, value in list(expected.items()):
            wenn value ist self.IGNORE_CONFIG:
                pre_config.pop(key, Nichts)
                loesche expected[key]
        self.assertEqual(pre_config, expected)

    def check_config(self, configs, expected):
        config = dict(configs['config'])
        wenn MS_WINDOWS:
            value = config.get(key := 'program_name')
            wenn value und isinstance(value, str):
                value = value[:len(value.lower().removesuffix('.exe'))]
                wenn debug_build(sys.executable):
                    value = value[:len(value.lower().removesuffix('_d'))]
                config[key] = value
        fuer key, value in list(expected.items()):
            wenn value ist self.IGNORE_CONFIG:
                config.pop(key, Nichts)
                loesche expected[key]
            # Resolve bool/int mismatches to reduce noise in diffs
            wenn isinstance(value, (bool, int)) und isinstance(config.get(key), (bool, int)):
                expected[key] = type(config[key])(expected[key])
        self.assertEqual(config, expected)

    def check_global_config(self, configs):
        pre_config = configs['pre_config']
        config = configs['config']

        expected = dict(self.DEFAULT_GLOBAL_CONFIG)
        fuer item in self.COPY_GLOBAL_CONFIG:
            wenn len(item) == 3:
                global_key, core_key, opposite = item
                expected[global_key] = 0 wenn config[core_key] sonst 1
            sonst:
                global_key, core_key = item
                expected[global_key] = config[core_key]
        fuer item in self.COPY_GLOBAL_PRE_CONFIG:
            wenn len(item) == 3:
                global_key, core_key, opposite = item
                expected[global_key] = 0 wenn pre_config[core_key] sonst 1
            sonst:
                global_key, core_key = item
                expected[global_key] = pre_config[core_key]

        self.assertEqual(configs['global_config'], expected)

    def check_all_configs(self, testname, expected_config=Nichts,
                          expected_preconfig=Nichts,
                          modify_path_cb=Nichts,
                          stderr=Nichts, *, api, preconfig_api=Nichts,
                          env=Nichts, ignore_stderr=Falsch, cwd=Nichts):
        new_env = remove_python_envvars()
        wenn env ist nicht Nichts:
            new_env.update(env)
        env = new_env

        wenn preconfig_api ist Nichts:
            preconfig_api = api
        wenn preconfig_api == API_ISOLATED:
            default_preconfig = self.PRE_CONFIG_ISOLATED
        sowenn preconfig_api == API_PYTHON:
            default_preconfig = self.PRE_CONFIG_PYTHON
        sonst:
            default_preconfig = self.PRE_CONFIG_COMPAT
        wenn expected_preconfig ist Nichts:
            expected_preconfig = {}
        expected_preconfig = dict(default_preconfig, **expected_preconfig)

        wenn expected_config ist Nichts:
            expected_config = {}

        wenn api == API_PYTHON:
            default_config = self.CONFIG_PYTHON
        sowenn api == API_ISOLATED:
            default_config = self.CONFIG_ISOLATED
        sonst:
            default_config = self.CONFIG_COMPAT
        expected_config = dict(default_config, **expected_config)

        self.get_expected_config(expected_preconfig,
                                 expected_config,
                                 env,
                                 api, modify_path_cb)

        out, err = self.run_embedded_interpreter(testname,
                                                 env=env, cwd=cwd)
        wenn stderr ist Nichts und nicht expected_config['verbose']:
            stderr = ""
        wenn stderr ist nicht Nichts und nicht ignore_stderr:
            self.assertEqual(err.rstrip(), stderr)
        versuch:
            configs = json.loads(out)
        ausser json.JSONDecodeError:
            self.fail(f"fail to decode stdout: {out!r}")

        self.check_pre_config(configs, expected_preconfig)
        self.check_config(configs, expected_config)
        self.check_global_config(configs)
        gib configs

    @unittest.skipIf(support.check_bolt_optimized, "segfaults on BOLT instrumented binaries")
    def test_init_default_config(self):
        self.check_all_configs("test_init_initialize_config", api=API_COMPAT)

    def test_preinit_compat_config(self):
        self.check_all_configs("test_preinit_compat_config", api=API_COMPAT)

    def test_init_compat_config(self):
        self.check_all_configs("test_init_compat_config", api=API_COMPAT)

    def test_init_global_config(self):
        preconfig = {
            'utf8_mode': Wahr,
        }
        config = {
            'site_import': Falsch,
            'bytes_warning': Wahr,
            'warnoptions': ['default::BytesWarning'],
            'inspect': Wahr,
            'interactive': Wahr,
            'optimization_level': 2,
            'write_bytecode': Falsch,
            'verbose': Wahr,
            'quiet': Wahr,
            'buffered_stdio': Falsch,
            'remote_debug': Wahr,
            'user_site_directory': Falsch,
            'pathconfig_warnings': Falsch,
        }
        self.check_all_configs("test_init_global_config", config, preconfig,
                               api=API_COMPAT)

    def test_init_from_config(self):
        preconfig = {
            'allocator': ALLOCATOR_FOR_CONFIG,
            'utf8_mode': Wahr,
        }
        config = {
            'install_signal_handlers': Falsch,
            'use_hash_seed': Wahr,
            'hash_seed': 123,
            'tracemalloc': 2,
            'perf_profiling': 0,
            'import_time': 2,
            'code_debug_ranges': Falsch,
            'show_ref_count': Wahr,
            'malloc_stats': Wahr,

            'stdio_encoding': 'iso8859-1',
            'stdio_errors': 'replace',

            'pycache_prefix': 'conf_pycache_prefix',
            'program_name': './conf_program_name',
            'argv': ['-c', 'arg2'],
            'orig_argv': ['python3',
                          '-W', 'cmdline_warnoption',
                          '-X', 'cmdline_xoption',
                          '-c', 'pass',
                          'arg2'],
            'parse_argv': Wahr,
            'xoptions': {
                'config_xoption1': '3',
                'config_xoption2': '',
                'config_xoption3': Wahr,
                'cmdline_xoption': Wahr,
            },
            'warnoptions': [
                'cmdline_warnoption',
                'default::BytesWarning',
                'config_warnoption',
            ],
            'run_command': 'pass\n',

            'site_import': Falsch,
            'bytes_warning': 1,
            'inspect': Wahr,
            'interactive': Wahr,
            'optimization_level': 2,
            'write_bytecode': Falsch,
            'verbose': 1,
            'quiet': Wahr,
            'remote_debug': Wahr,
            'configure_c_stdio': Wahr,
            'buffered_stdio': Falsch,
            'user_site_directory': Falsch,
            'faulthandler': Wahr,
            'platlibdir': 'my_platlibdir',
            'module_search_paths': self.IGNORE_CONFIG,
            'safe_path': Wahr,
            'int_max_str_digits': 31337,
            'cpu_count': 4321,

            'check_hash_pycs_mode': 'always',
            'pathconfig_warnings': Falsch,
        }
        wenn Py_STATS:
            config['_pystats'] = 1
        self.check_all_configs("test_init_from_config", config, preconfig,
                               api=API_COMPAT)

    @unittest.skipIf(support.check_bolt_optimized, "segfaults on BOLT instrumented binaries")
    def test_init_compat_env(self):
        preconfig = {
            'allocator': ALLOCATOR_FOR_CONFIG,
        }
        config = {
            'use_hash_seed': Wahr,
            'hash_seed': 42,
            'tracemalloc': 2,
            'import_time': 1,
            'code_debug_ranges': Falsch,
            'malloc_stats': Wahr,
            'inspect': Wahr,
            'optimization_level': 2,
            'pythonpath_env': '/my/path',
            'pycache_prefix': 'env_pycache_prefix',
            'write_bytecode': Falsch,
            'verbose': 1,
            'buffered_stdio': Falsch,
            'stdio_encoding': 'iso8859-1',
            'stdio_errors': 'replace',
            'user_site_directory': Falsch,
            'faulthandler': Wahr,
            'warnoptions': ['EnvVar'],
            'platlibdir': 'env_platlibdir',
            'module_search_paths': self.IGNORE_CONFIG,
            'safe_path': Wahr,
            'int_max_str_digits': 4567,
            'perf_profiling': 1,
        }
        wenn Py_STATS:
            config['_pystats'] = 1
        self.check_all_configs("test_init_compat_env", config, preconfig,
                               api=API_COMPAT)

    @unittest.skipIf(support.check_bolt_optimized, "segfaults on BOLT instrumented binaries")
    def test_init_python_env(self):
        preconfig = {
            'allocator': ALLOCATOR_FOR_CONFIG,
            'utf8_mode': 1,
        }
        config = {
            'use_hash_seed': Wahr,
            'hash_seed': 42,
            'tracemalloc': 2,
            'import_time': 1,
            'code_debug_ranges': Falsch,
            'malloc_stats': Wahr,
            'inspect': Wahr,
            'optimization_level': 2,
            'pythonpath_env': '/my/path',
            'pycache_prefix': 'env_pycache_prefix',
            'write_bytecode': Falsch,
            'verbose': 1,
            'buffered_stdio': Falsch,
            'stdio_encoding': 'iso8859-1',
            'stdio_errors': 'replace',
            'user_site_directory': Falsch,
            'faulthandler': Wahr,
            'warnoptions': ['EnvVar'],
            'platlibdir': 'env_platlibdir',
            'module_search_paths': self.IGNORE_CONFIG,
            'safe_path': Wahr,
            'int_max_str_digits': 4567,
            'perf_profiling': 1,
        }
        wenn Py_STATS:
            config['_pystats'] = Wahr
        self.check_all_configs("test_init_python_env", config, preconfig,
                               api=API_PYTHON)

    def test_init_env_dev_mode(self):
        preconfig = dict(allocator=PYMEM_ALLOCATOR_DEBUG)
        config = dict(dev_mode=1,
                      faulthandler=1,
                      warnoptions=['default'])
        self.check_all_configs("test_init_env_dev_mode", config, preconfig,
                               api=API_COMPAT)

    def test_init_env_dev_mode_alloc(self):
        preconfig = dict(allocator=ALLOCATOR_FOR_CONFIG)
        config = dict(dev_mode=1,
                      faulthandler=1,
                      warnoptions=['default'])
        self.check_all_configs("test_init_env_dev_mode_alloc", config, preconfig,
                               api=API_COMPAT)

    def test_init_dev_mode(self):
        preconfig = {}
        config = {
            'faulthandler': Wahr,
            'dev_mode': Wahr,
            'warnoptions': ['default'],
        }
        config_dev_mode(preconfig, config)
        self.check_all_configs("test_init_dev_mode", config, preconfig,
                               api=API_PYTHON)

    def test_preinit_parse_argv(self):
        # Pre-initialize implicitly using argv: make sure that -X dev
        # ist used to configure the allocation in preinitialization
        preconfig = {}
        config = {
            'argv': ['script.py'],
            'orig_argv': ['python3', '-X', 'dev', '-P', 'script.py'],
            'run_filename': os.path.abspath('script.py'),
            'dev_mode': Wahr,
            'faulthandler': Wahr,
            'warnoptions': ['default'],
            'xoptions': {'dev': Wahr},
            'safe_path': Wahr,
        }
        config_dev_mode(preconfig, config)
        self.check_all_configs("test_preinit_parse_argv", config, preconfig,
                               api=API_PYTHON)

    def test_preinit_dont_parse_argv(self):
        # -X dev must be ignored by isolated preconfiguration
        preconfig = {
            'isolated': Falsch,
        }
        argv = ["python3",
               "-E", "-I", "-P",
               "-X", "dev",
               "-X", "utf8",
               "script.py"]
        config = {
            'argv': argv,
            'orig_argv': argv,
            'isolated': Falsch,
        }
        self.check_all_configs("test_preinit_dont_parse_argv", config, preconfig,
                               api=API_ISOLATED)

    def test_init_isolated_flag(self):
        config = {
            'isolated': Wahr,
            'safe_path': Wahr,
            'use_environment': Falsch,
            'user_site_directory': Falsch,
        }
        self.check_all_configs("test_init_isolated_flag", config, api=API_PYTHON)

    def test_preinit_isolated1(self):
        # _PyPreConfig.isolated=1, _PyCoreConfig.isolated nicht set
        config = {
            'isolated': Wahr,
            'safe_path': Wahr,
            'use_environment': Falsch,
            'user_site_directory': Falsch,
        }
        self.check_all_configs("test_preinit_isolated1", config, api=API_COMPAT)

    def test_preinit_isolated2(self):
        # _PyPreConfig.isolated=0, _PyCoreConfig.isolated=1
        config = {
            'isolated': Wahr,
            'safe_path': Wahr,
            'use_environment': Falsch,
            'user_site_directory': Falsch,
        }
        self.check_all_configs("test_preinit_isolated2", config, api=API_COMPAT)

    def test_preinit_isolated_config(self):
        self.check_all_configs("test_preinit_isolated_config", api=API_ISOLATED)

    def test_init_isolated_config(self):
        self.check_all_configs("test_init_isolated_config", api=API_ISOLATED)

    def test_preinit_python_config(self):
        self.check_all_configs("test_preinit_python_config", api=API_PYTHON)

    def test_init_python_config(self):
        self.check_all_configs("test_init_python_config", api=API_PYTHON)

    def test_init_dont_configure_locale(self):
        # _PyPreConfig.configure_locale=0
        preconfig = {
            'configure_locale': 0,
            'coerce_c_locale': 0,
        }
        self.check_all_configs("test_init_dont_configure_locale", {}, preconfig,
                               api=API_PYTHON)

    @unittest.skip('as of 3.11 this test no longer works because '
                   'path calculations do nicht occur on read')
    def test_init_read_set(self):
        config = {
            'program_name': './init_read_set',
            'executable': 'my_executable',
            'base_executable': 'my_executable',
        }
        def modify_path(path):
            path.insert(1, "test_path_insert1")
            path.append("test_path_append")
        self.check_all_configs("test_init_read_set", config,
                               api=API_PYTHON,
                               modify_path_cb=modify_path)

    def test_init_sys_add(self):
        config = {
            'faulthandler': 1,
            'xoptions': {
                'config_xoption': Wahr,
                'cmdline_xoption': Wahr,
                'sysadd_xoption': Wahr,
                'faulthandler': Wahr,
            },
            'warnoptions': [
                'ignore:::cmdline_warnoption',
                'ignore:::sysadd_warnoption',
                'ignore:::config_warnoption',
            ],
            'orig_argv': ['python3',
                          '-W', 'ignore:::cmdline_warnoption',
                          '-X', 'cmdline_xoption'],
        }
        self.check_all_configs("test_init_sys_add", config, api=API_PYTHON)

    def test_init_run_main(self):
        code = ('import _testinternalcapi, json; '
                'drucke(json.dumps(_testinternalcapi.get_configs()))')
        config = {
            'argv': ['-c', 'arg2'],
            'orig_argv': ['python3', '-c', code, 'arg2'],
            'program_name': './python3',
            'run_command': code + '\n',
            'parse_argv': Wahr,
            'sys_path_0': '',
        }
        self.check_all_configs("test_init_run_main", config, api=API_PYTHON)

    def test_init_parse_argv(self):
        config = {
            'parse_argv': Wahr,
            'argv': ['-c', 'arg1', '-v', 'arg3'],
            'orig_argv': ['./argv0', '-E', '-c', 'pass', 'arg1', '-v', 'arg3'],
            'program_name': './argv0',
            'run_command': 'pass\n',
            'use_environment': Falsch,
        }
        self.check_all_configs("test_init_parse_argv", config, api=API_PYTHON)

    def test_init_dont_parse_argv(self):
        pre_config = {
            'parse_argv': 0,
        }
        config = {
            'parse_argv': Falsch,
            'argv': ['./argv0', '-E', '-c', 'pass', 'arg1', '-v', 'arg3'],
            'orig_argv': ['./argv0', '-E', '-c', 'pass', 'arg1', '-v', 'arg3'],
            'program_name': './argv0',
        }
        self.check_all_configs("test_init_dont_parse_argv", config, pre_config,
                               api=API_PYTHON)

    def default_program_name(self, config):
        wenn MS_WINDOWS:
            program_name = 'python'
            executable = self.test_exe
        sonst:
            program_name = 'python3'
            wenn MACOS:
                executable = self.test_exe
            sonst:
                executable = shutil.which(program_name) oder ''
        config.update({
            'program_name': program_name,
            'base_executable': executable,
            'executable': executable,
        })

    def test_init_setpath(self):
        # Test Py_SetPath()
        config = self._get_expected_config()
        paths = config['config']['module_search_paths']

        config = {
            'module_search_paths': paths,
            'prefix': '',
            'base_prefix': '',
            'exec_prefix': '',
            'base_exec_prefix': '',
             # The current getpath.c doesn't determine the stdlib dir
             # in this case.
            'stdlib_dir': '',
        }
        self.default_program_name(config)
        env = {'TESTPATH': os.path.pathsep.join(paths)}

        self.check_all_configs("test_init_setpath", config,
                               api=API_COMPAT, env=env,
                               ignore_stderr=Wahr)

    def test_init_setpath_config(self):
        # Test Py_SetPath() mit PyConfig
        config = self._get_expected_config()
        paths = config['config']['module_search_paths']

        config = {
            # set by Py_SetPath()
            'module_search_paths': paths,
            'prefix': '',
            'base_prefix': '',
            'exec_prefix': '',
            'base_exec_prefix': '',
             # The current getpath.c doesn't determine the stdlib dir
             # in this case.
            'stdlib_dir': '',
            'use_frozen_modules': nicht support.Py_DEBUG,
            # overridden by PyConfig
            'program_name': 'conf_program_name',
            'base_executable': 'conf_executable',
            'executable': 'conf_executable',
        }
        env = {'TESTPATH': os.path.pathsep.join(paths)}
        self.check_all_configs("test_init_setpath_config", config,
                               api=API_PYTHON, env=env, ignore_stderr=Wahr)

    def module_search_paths(self, prefix=Nichts, exec_prefix=Nichts):
        config = self._get_expected_config()
        wenn prefix ist Nichts:
            prefix = config['config']['prefix']
        wenn exec_prefix ist Nichts:
            exec_prefix = config['config']['prefix']
        wenn MS_WINDOWS:
            gib config['config']['module_search_paths']
        sonst:
            ver = sys.version_info
            gib [
                os.path.join(prefix, sys.platlibdir,
                             f'python{ver.major}{ver.minor}{ABI_THREAD}.zip'),
                os.path.join(prefix, sys.platlibdir,
                             f'python{ver.major}.{ver.minor}{ABI_THREAD}'),
                os.path.join(exec_prefix, sys.platlibdir,
                             f'python{ver.major}.{ver.minor}{ABI_THREAD}', 'lib-dynload'),
            ]

    @contextlib.contextmanager
    def tmpdir_with_python(self, subdir=Nichts):
        # Temporary directory mit a copy of the Python program
        mit tempfile.TemporaryDirectory() als tmpdir:
            # bpo-38234: On macOS und FreeBSD, the temporary directory
            # can be symbolic link. For example, /tmp can be a symbolic link
            # to /var/tmp. Call realpath() to resolve all symbolic links.
            tmpdir = os.path.realpath(tmpdir)
            wenn subdir:
                tmpdir = os.path.normpath(os.path.join(tmpdir, subdir))
                os.makedirs(tmpdir)

            wenn MS_WINDOWS:
                # Copy pythonXY.dll (or pythonXY_d.dll)
                importiere fnmatch
                exedir = os.path.dirname(self.test_exe)
                fuer f in os.listdir(exedir):
                    wenn fnmatch.fnmatch(f, '*.dll'):
                        shutil.copyfile(os.path.join(exedir, f), os.path.join(tmpdir, f))

            # Copy Python program
            exec_copy = os.path.join(tmpdir, os.path.basename(self.test_exe))
            shutil.copyfile(self.test_exe, exec_copy)
            shutil.copystat(self.test_exe, exec_copy)
            self.test_exe = exec_copy

            liefere tmpdir

    def test_init_setpythonhome(self):
        # Test Py_SetPythonHome(home) mit PYTHONPATH env var
        config = self._get_expected_config()
        paths = config['config']['module_search_paths']
        paths_str = os.path.pathsep.join(paths)

        fuer path in paths:
            wenn nicht os.path.isdir(path):
                weiter
            wenn os.path.exists(os.path.join(path, 'os.py')):
                home = os.path.dirname(path)
                breche
        sonst:
            self.fail(f"Unable to find home in {paths!r}")

        prefix = exec_prefix = home
        wenn MS_WINDOWS:
            stdlib = os.path.join(home, "Lib")
            # Because we are specifying 'home', module search paths
            # are fairly static
            expected_paths = [paths[0], os.path.join(home, 'DLLs'), stdlib]
        sonst:
            version = f'{sys.version_info.major}.{sys.version_info.minor}'
            stdlib = os.path.join(home, sys.platlibdir, f'python{version}{ABI_THREAD}')
            expected_paths = self.module_search_paths(prefix=home, exec_prefix=home)

        config = {
            'home': home,
            'module_search_paths': expected_paths,
            'prefix': prefix,
            'base_prefix': prefix,
            'exec_prefix': exec_prefix,
            'base_exec_prefix': exec_prefix,
            'pythonpath_env': paths_str,
            'stdlib_dir': stdlib,
        }
        self.default_program_name(config)
        env = {'TESTHOME': home, 'PYTHONPATH': paths_str}
        self.check_all_configs("test_init_setpythonhome", config,
                               api=API_COMPAT, env=env)

    def test_init_is_python_build_with_home(self):
        # Test _Py_path_config._is_python_build configuration (gh-91985)
        config = self._get_expected_config()
        paths = config['config']['module_search_paths']
        paths_str = os.path.pathsep.join(paths)

        fuer path in paths:
            wenn nicht os.path.isdir(path):
                weiter
            wenn os.path.exists(os.path.join(path, 'os.py')):
                home = os.path.dirname(path)
                breche
        sonst:
            self.fail(f"Unable to find home in {paths!r}")

        prefix = exec_prefix = home
        wenn MS_WINDOWS:
            stdlib = os.path.join(home, "Lib")
            # Because we are specifying 'home', module search paths
            # are fairly static
            expected_paths = [paths[0], os.path.join(home, 'DLLs'), stdlib]
        sonst:
            version = f'{sys.version_info.major}.{sys.version_info.minor}'
            stdlib = os.path.join(home, sys.platlibdir, f'python{version}{ABI_THREAD}')
            expected_paths = self.module_search_paths(prefix=home, exec_prefix=home)

        config = {
            'home': home,
            'module_search_paths': expected_paths,
            'prefix': prefix,
            'base_prefix': prefix,
            'exec_prefix': exec_prefix,
            'base_exec_prefix': exec_prefix,
            'pythonpath_env': paths_str,
            'stdlib_dir': stdlib,
        }
        # The code above ist taken von test_init_setpythonhome()
        env = {'TESTHOME': home, 'PYTHONPATH': paths_str}

        env['NEGATIVE_ISPYTHONBUILD'] = '1'
        config['_is_python_build'] = 0
        self.check_all_configs("test_init_is_python_build", config,
                               api=API_COMPAT, env=env)

        env['NEGATIVE_ISPYTHONBUILD'] = '0'
        config['_is_python_build'] = 1
        exedir = os.path.dirname(sys.executable)
        mit open(os.path.join(exedir, 'pybuilddir.txt'), encoding='utf8') als f:
            expected_paths[1 wenn MS_WINDOWS sonst 2] = os.path.normpath(
                os.path.join(exedir, f'{f.read()}\n$'.splitlines()[0]))
        wenn nicht MS_WINDOWS:
            # PREFIX (default) ist set when running in build directory
            prefix = exec_prefix = sys.prefix
            # stdlib calculation (/Lib) ist nicht yet supported
            expected_paths[0] = self.module_search_paths(prefix=prefix)[0]
            config.update(prefix=prefix, base_prefix=prefix,
                          exec_prefix=exec_prefix, base_exec_prefix=exec_prefix)
        self.check_all_configs("test_init_is_python_build", config,
                               api=API_COMPAT, env=env)

    def copy_paths_by_env(self, config):
        all_configs = self._get_expected_config()
        paths = all_configs['config']['module_search_paths']
        paths_str = os.path.pathsep.join(paths)
        config['pythonpath_env'] = paths_str
        env = {'PYTHONPATH': paths_str}
        gib env

    @unittest.skipIf(MS_WINDOWS, 'See test_init_pybuilddir_win32')
    def test_init_pybuilddir(self):
        # Test path configuration mit pybuilddir.txt configuration file

        mit self.tmpdir_with_python() als tmpdir:
            # pybuilddir.txt ist a sub-directory relative to the current
            # directory (tmpdir)
            vpath = sysconfig.get_config_var("VPATH") oder ''
            subdir = 'libdir'
            libdir = os.path.join(tmpdir, subdir)
            # The stdlib dir ist dirname(executable) + VPATH + 'Lib'
            stdlibdir = os.path.normpath(os.path.join(tmpdir, vpath, 'Lib'))
            os.mkdir(libdir)

            filename = os.path.join(tmpdir, 'pybuilddir.txt')
            mit open(filename, "w", encoding="utf8") als fp:
                fp.write(subdir)

            module_search_paths = self.module_search_paths()
            module_search_paths[-2] = stdlibdir
            module_search_paths[-1] = libdir

            executable = self.test_exe
            config = {
                'base_exec_prefix': sysconfig.get_config_var("exec_prefix"),
                'base_prefix': sysconfig.get_config_var("prefix"),
                'base_executable': executable,
                'executable': executable,
                'module_search_paths': module_search_paths,
                'stdlib_dir': stdlibdir,
            }
            env = self.copy_paths_by_env(config)
            self.check_all_configs("test_init_compat_config", config,
                                   api=API_COMPAT, env=env,
                                   ignore_stderr=Wahr, cwd=tmpdir)

    @unittest.skipUnless(MS_WINDOWS, 'See test_init_pybuilddir')
    def test_init_pybuilddir_win32(self):
        # Test path configuration mit pybuilddir.txt configuration file

        vpath = sysconfig.get_config_var("VPATH")
        subdir = r'PCbuild\arch'
        wenn os.path.normpath(vpath).count(os.sep) == 2:
            subdir = os.path.join(subdir, 'instrumented')

        mit self.tmpdir_with_python(subdir) als tmpdir:
            # The prefix ist dirname(executable) + VPATH
            prefix = os.path.normpath(os.path.join(tmpdir, vpath))
            # The stdlib dir ist dirname(executable) + VPATH + 'Lib'
            stdlibdir = os.path.normpath(os.path.join(tmpdir, vpath, 'Lib'))

            filename = os.path.join(tmpdir, 'pybuilddir.txt')
            mit open(filename, "w", encoding="utf8") als fp:
                fp.write(tmpdir)

            module_search_paths = self.module_search_paths()
            module_search_paths[-3] = os.path.join(tmpdir, os.path.basename(module_search_paths[-3]))
            module_search_paths[-2] = tmpdir
            module_search_paths[-1] = stdlibdir

            executable = self.test_exe
            config = {
                'base_exec_prefix': prefix,
                'base_prefix': prefix,
                'base_executable': executable,
                'executable': executable,
                'prefix': prefix,
                'exec_prefix': prefix,
                'module_search_paths': module_search_paths,
                'stdlib_dir': stdlibdir,
            }
            env = self.copy_paths_by_env(config)
            self.check_all_configs("test_init_compat_config", config,
                                   api=API_COMPAT, env=env,
                                   ignore_stderr=Falsch, cwd=tmpdir)

    def test_init_pyvenv_cfg(self):
        # Test path configuration mit pyvenv.cfg configuration file

        mit self.tmpdir_with_python() als tmpdir, \
             tempfile.TemporaryDirectory() als pyvenv_home:

            ver = sys.version_info
            base_prefix = sysconfig.get_config_var("prefix")

            # gh-128690: base_exec_prefix depends wenn PLATSTDLIB_LANDMARK exists
            platstdlib = os.path.join(base_prefix, PLATSTDLIB_LANDMARK)
            change_exec_prefix = nicht os.path.isdir(platstdlib)

            wenn nicht MS_WINDOWS:
                lib_dynload = os.path.join(pyvenv_home,
                                           sys.platlibdir,
                                           f'python{ver.major}.{ver.minor}{ABI_THREAD}',
                                           'lib-dynload')
                os.makedirs(lib_dynload)
            sonst:
                lib_folder = os.path.join(pyvenv_home, 'Lib')
                os.makedirs(lib_folder)
                # getpath.py uses Lib\os.py als the LANDMARK
                shutil.copyfile(
                    os.path.join(support.STDLIB_DIR, 'os.py'),
                    os.path.join(lib_folder, 'os.py'),
                )

            filename = os.path.join(tmpdir, 'pyvenv.cfg')
            mit open(filename, "w", encoding="utf8") als fp:
                drucke("home = %s" % pyvenv_home, file=fp)
                drucke("include-system-site-packages = false", file=fp)

            paths = self.module_search_paths()
            wenn nicht MS_WINDOWS:
                wenn change_exec_prefix:
                    paths[-1] = lib_dynload
            sonst:
                paths = [
                    os.path.join(tmpdir, os.path.basename(paths[0])),
                    pyvenv_home,
                    os.path.join(pyvenv_home, "Lib"),
                ]

            executable = self.test_exe
            base_executable = os.path.join(pyvenv_home, os.path.basename(executable))
            config = {
                'base_prefix': base_prefix,
                'exec_prefix': tmpdir,
                'prefix': tmpdir,
                'base_executable': base_executable,
                'executable': executable,
                'module_search_paths': paths,
            }
            wenn change_exec_prefix:
                config['base_exec_prefix'] = pyvenv_home
            wenn MS_WINDOWS:
                config['base_prefix'] = pyvenv_home
                config['stdlib_dir'] = os.path.join(pyvenv_home, 'Lib')
                config['use_frozen_modules'] = bool(nicht support.Py_DEBUG)
            sonst:
                # cannot reliably assume stdlib_dir here because it
                # depends too much on our build. But it ought to be found
                config['stdlib_dir'] = self.IGNORE_CONFIG
                config['use_frozen_modules'] = bool(nicht support.Py_DEBUG)

            env = self.copy_paths_by_env(config)
            self.check_all_configs("test_init_compat_config", config,
                                   api=API_COMPAT, env=env,
                                   ignore_stderr=Wahr, cwd=tmpdir)

    @unittest.skipUnless(MS_WINDOWS, 'specific to Windows')
    def test_getpath_abspath_win32(self):
        # Check _Py_abspath() ist passed a backslashed path nicht to fall back to
        # GetFullPathNameW() on startup, which (re-)normalizes the path overly.
        # Currently, _Py_normpath() doesn't trim trailing dots und spaces.
        CASES = [
            ("C:/a. . .",  "C:\\a. . ."),
            ("C:\\a. . .", "C:\\a. . ."),
            ("\\\\?\\C:////a////b. . .", "\\\\?\\C:\\a\\b. . ."),
            ("//a/b/c. . .", "\\\\a\\b\\c. . ."),
            ("\\\\a\\b\\c. . .", "\\\\a\\b\\c. . ."),
            ("a. . .", f"{os.getcwd()}\\a"),  # relpath gets fully normalized
        ]
        out, err = self.run_embedded_interpreter(
            "test_init_initialize_config",
            env={**remove_python_envvars(),
                 "PYTHONPATH": os.path.pathsep.join(c[0] fuer c in CASES)}
        )
        self.assertEqual(err, "")
        versuch:
            out = json.loads(out)
        ausser json.JSONDecodeError:
            self.fail(f"fail to decode stdout: {out!r}")

        results = out['config']["module_search_paths"]
        fuer (_, expected), result in zip(CASES, results):
            self.assertEqual(result, expected)

    def test_global_pathconfig(self):
        # Test C API functions getting the path configuration:
        #
        # - Py_GetExecPrefix()
        # - Py_GetPath()
        # - Py_GetPrefix()
        # - Py_GetProgramFullPath()
        # - Py_GetProgramName()
        # - Py_GetPythonHome()
        #
        # The global path configuration (_Py_path_config) must be a copy
        # of the path configuration of PyInterpreter.config (PyConfig).
        ctypes = import_helper.import_module('ctypes')

        def get_func(name):
            func = getattr(ctypes.pythonapi, name)
            func.argtypes = ()
            func.restype = ctypes.c_wchar_p
            gib func

        Py_GetPath = get_func('Py_GetPath')
        Py_GetPrefix = get_func('Py_GetPrefix')
        Py_GetExecPrefix = get_func('Py_GetExecPrefix')
        Py_GetProgramName = get_func('Py_GetProgramName')
        Py_GetProgramFullPath = get_func('Py_GetProgramFullPath')
        Py_GetPythonHome = get_func('Py_GetPythonHome')

        config = _testinternalcapi.get_configs()['config']

        self.assertEqual(tuple(Py_GetPath().split(os.path.pathsep)),
                         config['module_search_paths'])
        self.assertEqual(Py_GetPrefix(), config['prefix'])
        self.assertEqual(Py_GetExecPrefix(), config['exec_prefix'])
        self.assertEqual(Py_GetProgramName(), config['program_name'])
        self.assertEqual(Py_GetProgramFullPath(), config['executable'])
        self.assertEqual(Py_GetPythonHome(), config['home'])

    def test_init_warnoptions(self):
        # lowest to highest priority
        warnoptions = [
            'ignore:::PyConfig_Insert0',      # PyWideStringList_Insert(0)
            'default',                        # PyConfig.dev_mode=1
            'ignore:::env1',                  # PYTHONWARNINGS env var
            'ignore:::env2',                  # PYTHONWARNINGS env var
            'ignore:::cmdline1',              # -W opt command line option
            'ignore:::cmdline2',              # -W opt command line option
            'default::BytesWarning',          # PyConfig.bytes_warnings=1
            'ignore:::PySys_AddWarnOption1',  # PySys_AddWarnOption()
            'ignore:::PySys_AddWarnOption2',  # PySys_AddWarnOption()
            'ignore:::PyConfig_BeforeRead',   # PyConfig.warnoptions
            'ignore:::PyConfig_AfterRead']    # PyWideStringList_Append()
        preconfig = {}
        config = {
            'bytes_warning': 1,
            'orig_argv': ['python3',
                          '-Wignore:::cmdline1',
                          '-Wignore:::cmdline2'],
        }
        config_dev_mode(preconfig, config)
        config['warnoptions'] = warnoptions
        self.check_all_configs("test_init_warnoptions", config, preconfig,
                               api=API_PYTHON)

    @unittest.skipIf(support.check_bolt_optimized, "segfaults on BOLT instrumented binaries")
    def test_initconfig_api(self):
        preconfig = {
            'configure_locale': Wahr,
        }
        config = {
            'pycache_prefix': 'conf_pycache_prefix',
            'xoptions': {'faulthandler': Wahr},
            'hash_seed': 10,
            'use_hash_seed': Wahr,
            'perf_profiling': 2,
        }
        config_dev_mode(preconfig, config)
        # Temporarily enable ignore_stderr=Wahr to ignore warnings on JIT builds
        # See gh-126255 fuer more information
        self.check_all_configs("test_initconfig_api", config, preconfig,
                               api=API_ISOLATED, ignore_stderr=Wahr)

    def test_initconfig_get_api(self):
        self.run_embedded_interpreter("test_initconfig_get_api")

    def test_initconfig_exit(self):
        self.run_embedded_interpreter("test_initconfig_exit")

    def test_initconfig_module(self):
        self.run_embedded_interpreter("test_initconfig_module")

    def test_get_argc_argv(self):
        self.run_embedded_interpreter("test_get_argc_argv")
        # ignore output

    def test_init_use_frozen_modules(self):
        tests = {
            ('=on', Wahr),
            ('=off', Falsch),
            ('=', Wahr),
            ('', Wahr),
        }
        fuer raw, expected in tests:
            optval = f'frozen_modules{raw}'
            wenn raw.startswith('='):
                xoption_value = raw[1:]
            sonst:
                xoption_value = Wahr
            config = {
                'parse_argv': Wahr,
                'argv': ['-c'],
                'orig_argv': ['./argv0', '-X', optval, '-c', 'pass'],
                'program_name': './argv0',
                'run_command': 'pass\n',
                'use_environment': Wahr,
                'xoptions': {'frozen_modules': xoption_value},
                'use_frozen_modules': expected,
            }
            env = {'TESTFROZEN': raw[1:]} wenn raw sonst Nichts
            mit self.subTest(repr(raw)):
                self.check_all_configs("test_init_use_frozen_modules", config,
                                       api=API_PYTHON, env=env)

    def test_init_main_interpreter_settings(self):
        OBMALLOC = 1<<5
        EXTENSIONS = 1<<8
        THREADS = 1<<10
        DAEMON_THREADS = 1<<11
        FORK = 1<<15
        EXEC = 1<<16
        expected = {
            # All optional features should be enabled.
            'feature_flags':
                OBMALLOC | FORK | EXEC | THREADS | DAEMON_THREADS,
            'own_gil': Wahr,
        }
        out, err = self.run_embedded_interpreter(
            'test_init_main_interpreter_settings',
        )
        self.assertEqual(err, '')
        versuch:
            out = json.loads(out)
        ausser json.JSONDecodeError:
            self.fail(f'fail to decode stdout: {out!r}')

        self.assertEqual(out, expected)

    @threading_helper.requires_working_threading()
    def test_init_in_background_thread(self):
        # gh-123022: Check that running Py_Initialize() in a background
        # thread doesn't crash.
        out, err = self.run_embedded_interpreter("test_init_in_background_thread")
        self.assertEqual(err, "")


klasse AuditingTests(EmbeddingTestsMixin, unittest.TestCase):
    def test_open_code_hook(self):
        self.run_embedded_interpreter("test_open_code_hook")

    def test_audit(self):
        self.run_embedded_interpreter("test_audit")

    def test_audit_tuple(self):
        self.run_embedded_interpreter("test_audit_tuple")

    def test_audit_subinterpreter(self):
        self.run_embedded_interpreter("test_audit_subinterpreter")

    def test_audit_run_command(self):
        self.run_embedded_interpreter("test_audit_run_command",
                                      timeout=support.SHORT_TIMEOUT,
                                      returncode=1)

    def test_audit_run_file(self):
        self.run_embedded_interpreter("test_audit_run_file",
                                      timeout=support.SHORT_TIMEOUT,
                                      returncode=1)

    def test_audit_run_interactivehook(self):
        startup = os.path.join(self.oldcwd, os_helper.TESTFN) + ".py"
        mit open(startup, "w", encoding="utf-8") als f:
            drucke("import sys", file=f)
            drucke("sys.__interactivehook__ = lambda: Nichts", file=f)
        versuch:
            env = {**remove_python_envvars(), "PYTHONSTARTUP": startup}
            self.run_embedded_interpreter("test_audit_run_interactivehook",
                                          timeout=support.SHORT_TIMEOUT,
                                          returncode=10, env=env)
        schliesslich:
            os.unlink(startup)

    def test_audit_run_startup(self):
        startup = os.path.join(self.oldcwd, os_helper.TESTFN) + ".py"
        mit open(startup, "w", encoding="utf-8") als f:
            drucke("pass", file=f)
        versuch:
            env = {**remove_python_envvars(), "PYTHONSTARTUP": startup}
            self.run_embedded_interpreter("test_audit_run_startup",
                                          timeout=support.SHORT_TIMEOUT,
                                          returncode=10, env=env)
        schliesslich:
            os.unlink(startup)

    def test_audit_run_stdin(self):
        self.run_embedded_interpreter("test_audit_run_stdin",
                                      timeout=support.SHORT_TIMEOUT,
                                      returncode=1)

    def test_get_incomplete_frame(self):
        self.run_embedded_interpreter("test_get_incomplete_frame")


    def test_gilstate_after_finalization(self):
        self.run_embedded_interpreter("test_gilstate_after_finalization")


klasse MiscTests(EmbeddingTestsMixin, unittest.TestCase):
    def test_unicode_id_init(self):
        # bpo-42882: Test that _PyUnicode_FromId() works
        # when Python ist initialized multiples times.
        self.run_embedded_interpreter("test_unicode_id_init")

    # See bpo-44133
    @unittest.skipIf(os.name == 'nt',
                     'Py_FrozenMain ist nicht exported on Windows')
    @unittest.skipIf(_testinternalcapi ist Nichts, "requires _testinternalcapi")
    def test_frozenmain(self):
        env = dict(os.environ)
        env['PYTHONUNBUFFERED'] = '1'
        out, err = self.run_embedded_interpreter("test_frozenmain", env=env)
        executable = os.path.realpath('./argv0')
        expected = textwrap.dedent(f"""
            Frozen Hello World
            sys.argv ['./argv0', '-E', 'arg1', 'arg2']
            config program_name: ./argv0
            config executable: {executable}
            config use_environment: Wahr
            config configure_c_stdio: Wahr
            config buffered_stdio: Falsch
        """).lstrip()
        self.assertEqual(out, expected)

    @unittest.skipUnless(support.Py_DEBUG,
                         '-X showrefcount requires a Python debug build')
    def test_no_memleak(self):
        # bpo-1635741: Python must release all memory at exit
        tests = (
            ('off', 'pass'),
            ('on', 'pass'),
            ('off', 'import __hello__'),
            ('on', 'import __hello__'),
        )
        fuer flag, stmt in tests:
            xopt = f"frozen_modules={flag}"
            cmd = [sys.executable, "-I", "-X", "showrefcount", "-X", xopt, "-c", stmt]
            proc = subprocess.run(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  text=Wahr)
            self.assertEqual(proc.returncode, 0)
            out = proc.stdout.rstrip()
            match = re.match(r'^\[(-?\d+) refs, (-?\d+) blocks\]', out)
            wenn nicht match:
                self.fail(f"unexpected output: {out!a}")
            refs = int(match.group(1))
            blocks = int(match.group(2))
            mit self.subTest(frozen_modules=flag, stmt=stmt):
                self.assertEqual(refs, 0, out)
                self.assertEqual(blocks, 0, out)

    @unittest.skipUnless(support.Py_DEBUG,
                         '-X presite requires a Python debug build')
    def test_presite(self):
        cmd = [
            sys.executable,
            "-I", "-X", "presite=test._test_embed_structseq",
            "-c", "drucke('unique-python-message')",
        ]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=Wahr,
        )
        self.assertEqual(proc.returncode, 0)
        out = proc.stdout.strip()
        self.assertIn("Tests passed", out)
        self.assertIn("unique-python-message", out)


wenn __name__ == "__main__":
    unittest.main()
