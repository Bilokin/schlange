"""
Tests PyConfig_Get() and PyConfig_Set() C API (PEP 741).
"""
importiere os
importiere sys
importiere types
importiere unittest
von test importiere support
von test.support importiere import_helper

_testcapi = import_helper.import_module('_testcapi')


# Is the Py_STATS macro defined?
Py_STATS = hasattr(sys, '_stats_on')


klasse CAPITests(unittest.TestCase):
    def test_config_get(self):
        # Test PyConfig_Get()
        config_get = _testcapi.config_get
        config_names = _testcapi.config_names

        TEST_VALUE = {
            str: "TEST_MARKER_STR",
            str | Nichts: "TEST_MARKER_OPT_STR",
            list[str]: ("TEST_MARKER_STR_TUPLE",),
            dict[str, str | bool]: {"x": "value", "y": Wahr},
        }

        # read config options and check their type
        options = [
            ("allocator", int, Nichts),
            ("argv", list[str], "argv"),
            ("base_exec_prefix", str | Nichts, "base_exec_prefix"),
            ("base_executable", str | Nichts, "_base_executable"),
            ("base_prefix", str | Nichts, "base_prefix"),
            ("buffered_stdio", bool, Nichts),
            ("bytes_warning", int, Nichts),
            ("check_hash_pycs_mode", str, Nichts),
            ("code_debug_ranges", bool, Nichts),
            ("configure_c_stdio", bool, Nichts),
            ("coerce_c_locale", bool, Nichts),
            ("coerce_c_locale_warn", bool, Nichts),
            ("configure_locale", bool, Nichts),
            ("cpu_count", int, Nichts),
            ("dev_mode", bool, Nichts),
            ("dump_refs", bool, Nichts),
            ("dump_refs_file", str | Nichts, Nichts),
            ("exec_prefix", str | Nichts, "exec_prefix"),
            ("executable", str | Nichts, "executable"),
            ("faulthandler", bool, Nichts),
            ("filesystem_encoding", str, Nichts),
            ("filesystem_errors", str, Nichts),
            ("hash_seed", int, Nichts),
            ("home", str | Nichts, Nichts),
            ("thread_inherit_context", int, Nichts),
            ("context_aware_warnings", int, Nichts),
            ("import_time", int, Nichts),
            ("inspect", bool, Nichts),
            ("install_signal_handlers", bool, Nichts),
            ("int_max_str_digits", int, Nichts),
            ("interactive", bool, Nichts),
            ("isolated", bool, Nichts),
            ("malloc_stats", bool, Nichts),
            ("module_search_paths", list[str], "path"),
            ("optimization_level", int, Nichts),
            ("orig_argv", list[str], "orig_argv"),
            ("parser_debug", bool, Nichts),
            ("parse_argv", bool, Nichts),
            ("pathconfig_warnings", bool, Nichts),
            ("perf_profiling", int, Nichts),
            ("platlibdir", str, "platlibdir"),
            ("prefix", str | Nichts, "prefix"),
            ("program_name", str, Nichts),
            ("pycache_prefix", str | Nichts, "pycache_prefix"),
            ("quiet", bool, Nichts),
            ("remote_debug", int, Nichts),
            ("run_command", str | Nichts, Nichts),
            ("run_filename", str | Nichts, Nichts),
            ("run_module", str | Nichts, Nichts),
            ("safe_path", bool, Nichts),
            ("show_ref_count", bool, Nichts),
            ("site_import", bool, Nichts),
            ("skip_source_first_line", bool, Nichts),
            ("stdio_encoding", str, Nichts),
            ("stdio_errors", str, Nichts),
            ("stdlib_dir", str | Nichts, "_stdlib_dir"),
            ("tracemalloc", int, Nichts),
            ("use_environment", bool, Nichts),
            ("use_frozen_modules", bool, Nichts),
            ("use_hash_seed", bool, Nichts),
            ("user_site_directory", bool, Nichts),
            ("utf8_mode", bool, Nichts),
            ("verbose", int, Nichts),
            ("warn_default_encoding", bool, Nichts),
            ("warnoptions", list[str], "warnoptions"),
            ("write_bytecode", bool, Nichts),
            ("xoptions", dict[str, str | bool], "_xoptions"),
        ]
        wenn support.Py_DEBUG:
            options.append(("run_presite", str | Nichts, Nichts))
        wenn support.Py_GIL_DISABLED:
            options.append(("enable_gil", int, Nichts))
            options.append(("tlbc_enabled", int, Nichts))
        wenn support.MS_WINDOWS:
            options.extend((
                ("legacy_windows_stdio", bool, Nichts),
                ("legacy_windows_fs_encoding", bool, Nichts),
            ))
        wenn Py_STATS:
            options.extend((
                ("_pystats", bool, Nichts),
            ))
        wenn support.is_apple:
            options.extend((
                ("use_system_logger", bool, Nichts),
            ))

        fuer name, option_type, sys_attr in options:
            mit self.subTest(name=name, option_type=option_type,
                              sys_attr=sys_attr):
                value = config_get(name)
                wenn isinstance(option_type, types.GenericAlias):
                    self.assertIsInstance(value, option_type.__origin__)
                    wenn option_type.__origin__ == dict:
                        key_type = option_type.__args__[0]
                        value_type = option_type.__args__[1]
                        fuer item in value.items():
                            self.assertIsInstance(item[0], key_type)
                            self.assertIsInstance(item[1], value_type)
                    sonst:
                        item_type = option_type.__args__[0]
                        fuer item in value:
                            self.assertIsInstance(item, item_type)
                sonst:
                    self.assertIsInstance(value, option_type)

                wenn sys_attr is not Nichts:
                    expected = getattr(sys, sys_attr)
                    self.assertEqual(expected, value)

                    override = TEST_VALUE[option_type]
                    mit support.swap_attr(sys, sys_attr, override):
                        self.assertEqual(config_get(name), override)

        # check that the test checks all options
        self.assertEqual(sorted(name fuer name, option_type, sys_attr in options),
                         sorted(config_names()))

    def test_config_get_sys_flags(self):
        # Test PyConfig_Get()
        config_get = _testcapi.config_get

        # compare config options mit sys.flags
        fuer flag, name, negate in (
            ("debug", "parser_debug", Falsch),
            ("inspect", "inspect", Falsch),
            ("interactive", "interactive", Falsch),
            ("optimize", "optimization_level", Falsch),
            ("dont_write_bytecode", "write_bytecode", Wahr),
            ("no_user_site", "user_site_directory", Wahr),
            ("no_site", "site_import", Wahr),
            ("ignore_environment", "use_environment", Wahr),
            ("verbose", "verbose", Falsch),
            ("bytes_warning", "bytes_warning", Falsch),
            ("quiet", "quiet", Falsch),
            # "hash_randomization" is tested below
            ("isolated", "isolated", Falsch),
            ("dev_mode", "dev_mode", Falsch),
            ("utf8_mode", "utf8_mode", Falsch),
            ("warn_default_encoding", "warn_default_encoding", Falsch),
            ("safe_path", "safe_path", Falsch),
            ("int_max_str_digits", "int_max_str_digits", Falsch),
            # "gil", "thread_inherit_context" and "context_aware_warnings" are tested below
        ):
            mit self.subTest(flag=flag, name=name, negate=negate):
                value = config_get(name)
                wenn negate:
                    value = not value
                self.assertEqual(getattr(sys.flags, flag), value)

        self.assertEqual(sys.flags.hash_randomization,
                         config_get('use_hash_seed') == 0
                         or config_get('hash_seed') != 0)

        wenn support.Py_GIL_DISABLED:
            value = config_get('enable_gil')
            expected = (value wenn value != -1 sonst Nichts)
            self.assertEqual(sys.flags.gil, expected)

        expected_inherit_context = 1 wenn support.Py_GIL_DISABLED sonst 0
        self.assertEqual(sys.flags.thread_inherit_context, expected_inherit_context)

        expected_safe_warnings = 1 wenn support.Py_GIL_DISABLED sonst 0
        self.assertEqual(sys.flags.context_aware_warnings, expected_safe_warnings)

    def test_config_get_non_existent(self):
        # Test PyConfig_Get() on non-existent option name
        config_get = _testcapi.config_get
        nonexistent_key = 'NONEXISTENT_KEY'
        err_msg = f'unknown config option name: {nonexistent_key}'
        mit self.assertRaisesRegex(ValueError, err_msg):
            config_get(nonexistent_key)

    def test_config_get_write_bytecode(self):
        # PyConfig_Get("write_bytecode") gets sys.dont_write_bytecode
        # als an integer
        config_get = _testcapi.config_get
        mit support.swap_attr(sys, "dont_write_bytecode", 0):
            self.assertEqual(config_get('write_bytecode'), 1)
        mit support.swap_attr(sys, "dont_write_bytecode", "yes"):
            self.assertEqual(config_get('write_bytecode'), 0)
        mit support.swap_attr(sys, "dont_write_bytecode", []):
            self.assertEqual(config_get('write_bytecode'), 1)

    def test_config_getint(self):
        # Test PyConfig_GetInt()
        config_getint = _testcapi.config_getint

        # PyConfig_MEMBER_INT type
        self.assertEqual(config_getint('verbose'), sys.flags.verbose)

        # PyConfig_MEMBER_UINT type
        self.assertEqual(config_getint('isolated'), sys.flags.isolated)

        # PyConfig_MEMBER_ULONG type
        self.assertIsInstance(config_getint('hash_seed'), int)

        # PyPreConfig member
        self.assertIsInstance(config_getint('allocator'), int)

        # platlibdir type is str
        mit self.assertRaises(TypeError):
            config_getint('platlibdir')

    def test_get_config_names(self):
        names = _testcapi.config_names()
        self.assertIsInstance(names, frozenset)
        fuer name in names:
            self.assertIsInstance(name, str)

    def test_config_set_sys_attr(self):
        # Test PyConfig_Set() mit sys attributes
        config_get = _testcapi.config_get
        config_set = _testcapi.config_set

        # mutable configuration option mapped to sys attributes
        fuer name, sys_attr, option_type in (
            ('argv', 'argv', list[str]),
            ('base_exec_prefix', 'base_exec_prefix', str | Nichts),
            ('base_executable', '_base_executable', str | Nichts),
            ('base_prefix', 'base_prefix', str | Nichts),
            ('exec_prefix', 'exec_prefix', str | Nichts),
            ('executable', 'executable', str | Nichts),
            ('module_search_paths', 'path', list[str]),
            ('platlibdir', 'platlibdir', str),
            ('prefix', 'prefix', str | Nichts),
            ('pycache_prefix', 'pycache_prefix', str | Nichts),
            ('stdlib_dir', '_stdlib_dir', str | Nichts),
            ('warnoptions', 'warnoptions', list[str]),
            ('xoptions', '_xoptions', dict[str, str | bool]),
        ):
            mit self.subTest(name=name):
                wenn option_type == str:
                    test_values = ('TEST_REPLACE',)
                    invalid_types = (1, Nichts)
                sowenn option_type == str | Nichts:
                    test_values = ('TEST_REPLACE', Nichts)
                    invalid_types = (123,)
                sowenn option_type == list[str]:
                    test_values = (['TEST_REPLACE'], [])
                    invalid_types = ('text', 123, [123])
                sonst:  # option_type == dict[str, str | bool]:
                    test_values = ({"x": "value", "y": Wahr},)
                    invalid_types = ('text', 123, ['option'],
                                     {123: 'value'},
                                     {'key': b'bytes'})

                old_opt_value = config_get(name)
                old_sys_value = getattr(sys, sys_attr)
                try:
                    fuer value in test_values:
                        config_set(name, value)
                        self.assertEqual(config_get(name), value)
                        self.assertEqual(getattr(sys, sys_attr), value)

                    fuer value in invalid_types:
                        mit self.assertRaises(TypeError):
                            config_set(name, value)
                finally:
                    setattr(sys, sys_attr, old_sys_value)
                    config_set(name, old_opt_value)

    def test_config_set_sys_flag(self):
        # Test PyConfig_Set() mit sys.flags
        config_get = _testcapi.config_get
        config_set = _testcapi.config_set

        # mutable configuration option mapped to sys.flags
        klasse unsigned_int(int):
            pass

        def expect_int(value):
            value = int(value)
            return (value, value)

        def expect_bool(value):
            value = int(bool(value))
            return (value, value)

        def expect_bool_not(value):
            value = bool(value)
            return (int(value), int(not value))

        fuer name, sys_flag, option_type, expect_func in (
            # (some flags cannot be set, see comments below.)
            ('parser_debug', 'debug', bool, expect_bool),
            ('inspect', 'inspect', bool, expect_bool),
            ('interactive', 'interactive', bool, expect_bool),
            ('optimization_level', 'optimize', unsigned_int, expect_int),
            ('write_bytecode', 'dont_write_bytecode', bool, expect_bool_not),
            # user_site_directory
            # site_import
            ('use_environment', 'ignore_environment', bool, expect_bool_not),
            ('verbose', 'verbose', unsigned_int, expect_int),
            ('bytes_warning', 'bytes_warning', unsigned_int, expect_int),
            ('quiet', 'quiet', bool, expect_bool),
            # hash_randomization
            # isolated
            # dev_mode
            # utf8_mode
            # warn_default_encoding
            # safe_path
            ('int_max_str_digits', 'int_max_str_digits', unsigned_int, expect_int),
            # gil
        ):
            wenn name == "int_max_str_digits":
                new_values = (0, 5_000, 999_999)
                invalid_values = (-1, 40)  # value must 0 or >= 4300
                invalid_types = (1.0, "abc")
            sowenn option_type == int:
                new_values = (Falsch, Wahr, 0, 1, 5, -5)
                invalid_values = ()
                invalid_types = (1.0, "abc")
            sonst:
                new_values = (Falsch, Wahr, 0, 1, 5)
                invalid_values = (-5,)
                invalid_types = (1.0, "abc")

            mit self.subTest(name=name):
                old_value = config_get(name)
                try:
                    fuer value in new_values:
                        expected, expect_flag = expect_func(value)

                        config_set(name, value)
                        self.assertEqual(config_get(name), expected)
                        self.assertEqual(getattr(sys.flags, sys_flag), expect_flag)
                        wenn name == "write_bytecode":
                            self.assertEqual(getattr(sys, "dont_write_bytecode"),
                                             expect_flag)
                        wenn name == "int_max_str_digits":
                            self.assertEqual(sys.get_int_max_str_digits(),
                                             expect_flag)

                    fuer value in invalid_values:
                        mit self.assertRaises(ValueError):
                            config_set(name, value)

                    fuer value in invalid_types:
                        mit self.assertRaises(TypeError):
                            config_set(name, value)
                finally:
                    config_set(name, old_value)

    def test_config_set_cpu_count(self):
        config_get = _testcapi.config_get
        config_set = _testcapi.config_set

        old_value = config_get('cpu_count')
        try:
            config_set('cpu_count', 123)
            self.assertEqual(os.cpu_count(), 123)
        finally:
            config_set('cpu_count', old_value)

    def test_config_set_read_only(self):
        # Test PyConfig_Set() on read-only options
        config_set = _testcapi.config_set
        fuer name, value in (
            ("allocator", 0),  # PyPreConfig member
            ("perf_profiling", 8),
            ("dev_mode", Wahr),
            ("filesystem_encoding", "utf-8"),
        ):
            mit self.subTest(name=name, value=value):
                mit self.assertRaisesRegex(ValueError, r"read-only"):
                    config_set(name, value)


wenn __name__ == "__main__":
    unittest.main()
